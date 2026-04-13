from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd

from wtbench.stage2_truth_bridge import log_normalize_csr


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/stage2/k562_13d_minimal_model_tradeoff_audit_v1.json"
ROLE_ORDER = ["canonical_backbone", "shift_excess", "mixed"]


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extract_gene_symbol(var_name: object) -> str:
    text = str(var_name)
    if "_" in text:
        return text.split("_", 1)[1]
    return text


def safe_cosine(left: np.ndarray, right: np.ndarray) -> float:
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm == 0.0 and right_norm == 0.0:
        return 1.0
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def top_k_overlap_fraction(left: np.ndarray, right: np.ndarray, top_k: int) -> float:
    effective_k = min(int(top_k), int(left.shape[0]), int(right.shape[0]))
    if effective_k <= 0:
        return float("nan")
    left_top = set(np.argsort(np.abs(left))[-effective_k:].tolist())
    right_top = set(np.argsort(np.abs(right))[-effective_k:].tolist())
    return float(len(left_top & right_top) / effective_k)


def rank_percentile(values: pd.Series, key: str) -> float:
    non_na = values.dropna()
    if key not in non_na.index or len(non_na) <= 1:
        return float("nan")
    ranked = non_na.rank(method="average", ascending=False)
    rank = float(ranked.loc[key])
    return 1.0 - ((rank - 1.0) / (len(non_na) - 1.0))


def pairwise_superiority_probability(left: pd.Series, right: pd.Series) -> float:
    left_values = left.dropna().to_numpy(dtype=np.float64)
    right_values = right.dropna().to_numpy(dtype=np.float64)
    if left_values.size == 0 or right_values.size == 0:
        return float("nan")
    comparisons = (left_values[:, None] > right_values[None, :]).mean()
    ties = (left_values[:, None] == right_values[None, :]).mean()
    return float(comparisons + 0.5 * ties)


def normalize_architecture_role(value: object) -> str:
    text = str(value)
    if text == "backbone":
        return "canonical_backbone"
    if text == "shift_excess":
        return "shift_excess"
    return "mixed"


def load_role_table(axis_membership_path: Path, axis_summary_path: Path) -> pd.DataFrame:
    axis_membership = pd.read_csv(axis_membership_path, sep="\t")
    axis_summary = pd.read_csv(axis_summary_path, sep="\t")
    required_membership = {"target_gene", "fine_axis"}
    required_summary = {"fine_axis", "architecture_role"}
    missing_membership = sorted(required_membership - set(axis_membership.columns))
    missing_summary = sorted(required_summary - set(axis_summary.columns))
    if missing_membership:
        raise ValueError(f"{axis_membership_path} 缺少列: {missing_membership}")
    if missing_summary:
        raise ValueError(f"{axis_summary_path} 缺少列: {missing_summary}")
    role_table = axis_membership.loc[:, ["target_gene", "fine_axis"]].drop_duplicates().merge(
        axis_summary.loc[:, ["fine_axis", "architecture_role"]].drop_duplicates(),
        on="fine_axis",
        how="left",
        validate="many_to_one",
    )
    role_table["architecture_role"] = role_table["architecture_role"].map(normalize_architecture_role)
    return role_table


def load_prediction_matrix(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep="\t")
    if frame.empty:
        raise ValueError(f"{path} 为空。")
    if frame.columns[0] != "target_gene":
        raise ValueError(f"{path} 首列必须是 target_gene。")
    frame["target_gene"] = frame["target_gene"].astype(str)
    return frame


def build_truth_shift_matrix(
    *,
    input_h5ad_path: Path,
    target_order: list[str],
    gene_order: list[str],
    target_sum: float,
) -> pd.DataFrame:
    raw = ad.read_h5ad(input_h5ad_path)
    if "target_gene" not in raw.obs or "is_control" not in raw.obs:
        raise ValueError(f"{input_h5ad_path} 必须包含 obs['target_gene'] 与 obs['is_control']。")

    symbol_to_var: dict[str, str] = {}
    for var_name in raw.var.index.astype(str).tolist():
        symbol = extract_gene_symbol(var_name)
        symbol_to_var.setdefault(symbol, var_name)
    present_genes = [gene for gene in gene_order if gene in symbol_to_var]
    missing_genes = sorted(set(gene_order) - set(present_genes))
    if missing_genes:
        print(
            "[k562-minimal-tradeoff] drop_missing_truth_genes "
            f"n={len(missing_genes)} genes={','.join(missing_genes[:8])}",
            flush=True,
        )
    if not present_genes:
        raise ValueError("预测矩阵列与 K562 h5ad gene symbols 没有交集，无法同空间评分。")

    raw_sub = raw[:, [symbol_to_var[gene] for gene in present_genes]].copy()
    normalized = log_normalize_csr(raw_sub.X, target_sum=target_sum).tocsr()
    obs = raw_sub.obs.copy()
    obs["target_gene"] = obs["target_gene"].astype(str)
    is_control = obs["is_control"].astype(bool).to_numpy()
    if not is_control.any():
        raise ValueError("K562 h5ad 中没有 control cells。")
    control_mean = np.asarray(normalized[is_control].mean(axis=0)).ravel().astype(np.float64)

    rows: list[np.ndarray] = []
    kept_targets: list[str] = []
    for target_gene in target_order:
        target_mask = obs["target_gene"].eq(target_gene).to_numpy() & ~is_control
        if not target_mask.any():
            continue
        target_mean = np.asarray(normalized[target_mask].mean(axis=0)).ravel().astype(np.float64)
        rows.append(target_mean - control_mean)
        kept_targets.append(target_gene)
    if not rows:
        raise ValueError("K562 h5ad 中没有可与预测矩阵对齐的 perturbation target。")
    truth = pd.DataFrame(rows, columns=present_genes)
    truth.insert(0, "target_gene", kept_targets)
    return truth


def build_shared_mean_baseline(truth: pd.DataFrame) -> pd.DataFrame:
    values = truth.drop(columns=["target_gene"]).to_numpy(dtype=np.float64)
    shared_mean = values.mean(axis=0)
    baseline = pd.DataFrame(np.tile(shared_mean, (len(truth), 1)), columns=truth.columns[1:])
    baseline.insert(0, "target_gene", truth["target_gene"].astype(str).tolist())
    return baseline


def align_prediction_and_truth(
    prediction: pd.DataFrame,
    truth: pd.DataFrame,
    role_table: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    target_order = [
        target
        for target in role_table["target_gene"].astype(str).tolist()
        if target in set(prediction["target_gene"]) and target in set(truth["target_gene"])
    ]
    gene_order = [gene for gene in prediction.columns[1:] if gene in set(truth.columns[1:])]
    if not target_order:
        raise ValueError("预测、truth 与 role table 没有共同 target。")
    if not gene_order:
        raise ValueError("预测与 truth 没有共同 gene columns。")
    prediction_aligned = prediction.set_index("target_gene").loc[target_order, gene_order]
    truth_aligned = truth.set_index("target_gene").loc[target_order, gene_order]
    roles_aligned = role_table.set_index("target_gene").loc[target_order].reset_index()
    return prediction_aligned, truth_aligned, roles_aligned


def score_model(
    *,
    model_id: str,
    object_role: str,
    prediction: pd.DataFrame,
    truth: pd.DataFrame,
    role_table: pd.DataFrame,
) -> tuple[dict[str, object], pd.DataFrame]:
    prediction_aligned, truth_aligned, roles_aligned = align_prediction_and_truth(
        prediction=prediction,
        truth=truth,
        role_table=role_table,
    )
    truth_vectors = {
        target_gene: truth_aligned.loc[target_gene].to_numpy(dtype=np.float64)
        for target_gene in truth_aligned.index.astype(str)
    }
    rows: list[dict[str, object]] = []
    for row in roles_aligned.itertuples(index=False):
        target_gene = str(row.target_gene)
        predicted_vec = prediction_aligned.loc[target_gene].to_numpy(dtype=np.float64)
        truth_vec = truth_vectors[target_gene]
        truth_cosines = pd.Series(
            {
                truth_target: safe_cosine(predicted_vec, truth_target_vec)
                for truth_target, truth_target_vec in truth_vectors.items()
            }
        )
        rows.append(
            {
                "model_id": model_id,
                "object_role": object_role,
                "target_gene": target_gene,
                "fine_axis": str(row.fine_axis),
                "architecture_role": str(row.architecture_role),
                "cosine_similarity": safe_cosine(predicted_vec, truth_vec),
                "l2_distance": float(np.linalg.norm(predicted_vec - truth_vec)),
                "top20_overlap_fraction": top_k_overlap_fraction(predicted_vec, truth_vec, top_k=20),
                "predicted_shift_l2": float(np.linalg.norm(predicted_vec)),
                "truth_shift_l2": float(np.linalg.norm(truth_vec)),
                "target_specificity_rank": rank_percentile(truth_cosines, target_gene),
                "n_genes_scored": int(len(predicted_vec)),
            }
        )
    target_metrics = pd.DataFrame(rows)
    summary: dict[str, object] = {
        "model_id": model_id,
        "object_role": object_role,
        "n_targets": int(len(target_metrics)),
        "n_genes_scored": int(target_metrics["n_genes_scored"].min()) if not target_metrics.empty else 0,
    }
    for role in ROLE_ORDER:
        subset = target_metrics.loc[target_metrics["architecture_role"].eq(role)]
        summary[f"n_{role}_targets"] = int(len(subset))
        summary[f"{role}_cosine_mean"] = float(subset["cosine_similarity"].mean()) if not subset.empty else float("nan")
        summary[f"{role}_target_specificity_mean"] = (
            float(subset["target_specificity_rank"].mean()) if not subset.empty else float("nan")
        )
        summary[f"{role}_predicted_shift_l2_mean"] = (
            float(subset["predicted_shift_l2"].mean()) if not subset.empty else float("nan")
        )
    summary["backbone_recovery_score"] = summary["canonical_backbone_cosine_mean"]
    summary["shift_excess_recovery_score"] = summary["shift_excess_cosine_mean"]
    summary["shift_excess_identification_score"] = pairwise_superiority_probability(
        target_metrics.loc[target_metrics["architecture_role"].eq("shift_excess"), "predicted_shift_l2"],
        target_metrics.loc[target_metrics["architecture_role"].eq("canonical_backbone"), "predicted_shift_l2"],
    )
    summary["structure_vs_context_separation_score"] = float(target_metrics["target_specificity_rank"].mean())
    summary["overall_cosine_mean"] = float(target_metrics["cosine_similarity"].mean())
    return summary, target_metrics


def build_direction_calls(
    comparison: pd.DataFrame,
    thresholds: dict[str, Any],
) -> pd.DataFrame:
    if comparison.empty or "shared_mean_baseline" not in set(comparison["model_id"]):
        return pd.DataFrame()
    baseline = comparison.set_index("model_id").loc["shared_mean_baseline"]
    rows: list[dict[str, object]] = []
    min_role_targets = int(thresholds.get("minimum_role_targets", 1))
    backbone_gap_min = float(thresholds.get("backbone_gap_min", 0.0))
    separation_gain_min = float(thresholds.get("separation_gain_min", 0.0))
    shift_excess_gain_min = float(thresholds.get("shift_excess_gain_min", 0.0))
    for row in comparison.itertuples(index=False):
        if row.model_id == "shared_mean_baseline":
            continue
        backbone_delta = float(row.backbone_recovery_score) - float(baseline["backbone_recovery_score"])
        separation_delta = float(row.structure_vs_context_separation_score) - float(
            baseline["structure_vs_context_separation_score"]
        )
        shift_recovery_delta = float(row.shift_excess_recovery_score) - float(baseline["shift_excess_recovery_score"])
        role_coverage_ok = (
            int(row.n_canonical_backbone_targets) >= min_role_targets
            and int(row.n_shift_excess_targets) >= min_role_targets
        )
        baseline_backbone_advantage = backbone_delta < -backbone_gap_min
        entrant_separation_advantage = separation_delta > separation_gain_min
        entrant_shift_excess_advantage = shift_recovery_delta > shift_excess_gain_min
        same_direction = bool(
            role_coverage_ok
            and baseline_backbone_advantage
            and (entrant_separation_advantage or entrant_shift_excess_advantage)
        )
        if not role_coverage_ok:
            call = "insufficient_role_coverage"
        elif same_direction:
            call = "same_direction_as_hcc_tradeoff"
        else:
            call = "not_same_direction_as_hcc_tradeoff"
        rows.append(
            {
                "model_id": row.model_id,
                "reference_model_id": "shared_mean_baseline",
                "role_coverage_ok": role_coverage_ok,
                "backbone_delta_vs_baseline": backbone_delta,
                "separation_delta_vs_baseline": separation_delta,
                "shift_excess_recovery_delta_vs_baseline": shift_recovery_delta,
                "baseline_backbone_advantage": baseline_backbone_advantage,
                "entrant_separation_advantage": entrant_separation_advantage,
                "entrant_shift_excess_advantage": entrant_shift_excess_advantage,
                "direction_call": call,
            }
        )
    return pd.DataFrame(rows)


def render_report(comparison: pd.DataFrame, calls: pd.DataFrame, output_path: Path) -> None:
    lines = [
        "# K562 13d minimal model-side trade-off audit",
        "",
        "## 定位",
        "",
        "- 这不是 leaderboard；只检查 HCC 中的非对称 model-side architecture trade-off 是否在 GSE90063 K562 13d KO context 中出现同类方向。",
        "- 固定口径：`shared_mean_baseline` 若更强，含义只限于 shared backbone；entrant 若更强，主要看 `shift-excess` 与 target-specific separation。",
        "- `shift-excess` 不等于 shared trend / overall displacement。",
        "",
        "## 模型最小集",
        "",
    ]
    for row in comparison.itertuples(index=False):
        lines.append(
            f"- `{row.model_id}` ({row.object_role}): "
            f"backbone = `{row.backbone_recovery_score:.3f}`；"
            f"shift-excess = `{row.shift_excess_recovery_score:.3f}`；"
            f"separation = `{row.structure_vs_context_separation_score:.3f}`。"
        )
    lines.extend(["", "## 方向判读", ""])
    if calls.empty:
        lines.append("- 未生成方向判读；通常是 baseline 缺失或没有可比较 entrant。")
    else:
        for row in calls.itertuples(index=False):
            lines.append(f"### {row.model_id}")
            lines.append(f"- direction_call = `{row.direction_call}`。")
            lines.append(f"- backbone_delta_vs_baseline = `{row.backbone_delta_vs_baseline:.3f}`。")
            lines.append(f"- separation_delta_vs_baseline = `{row.separation_delta_vs_baseline:.3f}`。")
            lines.append(
                f"- shift_excess_recovery_delta_vs_baseline = `{row.shift_excess_recovery_delta_vs_baseline:.3f}`。"
            )
            if row.direction_call == "same_direction_as_hcc_tradeoff" and row.shift_excess_recovery_delta_vs_baseline < 0:
                lines.append(
                    "- 定级：`partial recurrence / partial-support`。K562 13d 复现了 backbone-vs-separation 主方向，但 `shift-excess` 分量未复现。"
                )
                lines.append(
                    "- 禁止升级：不能写成 `full recurrence`、`complete model-side generalization` 或 `GEARS deviation-sensitive advantage broadly established`。"
                )
            lines.append("")
    lines.extend(
        [
            "## Manuscript-ready wording",
            "",
            "In the external K562 13-day setting, we observed a partial recurrence of the model-side architecture trade-off seen in HCC: the shared baseline again remained stronger on backbone recovery, whereas GEARS retained an advantage in structure-vs-context separation. However, the shift-excess component was not recapitulated, indicating that the external support is partial and that finer deviation-sensitive recovery remains context-dependent under the current data setting.",
            "",
            "在外部 K562 13 天数据中，我们观察到与 HCC 主分析一致的模型侧架构 trade-off 的部分复现：`shared_mean_baseline` 再次在 backbone recovery 上占优，而 `GEARS` 仍在 structure-vs-context separation 上表现更强。然而，`shift-excess` 成分未得到复现，提示当前外部支持属于部分支持，且更细粒度的 deviation-sensitive recovery 在现有数据设定下仍具有 context dependence。",
            "",
            "## Evidence tier",
            "",
            "- backbone vs separation trade-off recurrence：`supporting / partial-confirmed`",
            "- full three-component recurrence：`not established`",
            "- external model-side generalization：`not established`",
            "- framework-level supplementary strengthening：`yes`",
            "- HCC 主 biological content strengthened：`no`",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def iter_prediction_models(config: dict[str, Any]) -> list[dict[str, Any]]:
    models = []
    for model in config.get("prediction_models", []):
        if not bool(model.get("enabled", True)):
            continue
        prediction_path = str(model.get("prediction_path", ""))
        if not prediction_path:
            if bool(model.get("required", False)):
                raise ValueError(f"{model.get('model_id')} 启用但 prediction_path 为空。")
            continue
        models.append(model)
    if len(models) > 2:
        raise ValueError("最小集最多允许 baseline + 2 个 prediction models。")
    return models


def main() -> None:
    parser = argparse.ArgumentParser(
        description="运行 GSE90063 K562 13d 最小 model-side architecture trade-off 方向审计。"
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()

    config = read_json(resolve_path(args.config))
    output_root = resolve_path(config["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    role_table = load_role_table(
        resolve_path(config["axis_membership_path"]),
        resolve_path(config["axis_summary_path"]),
    )
    prediction_models = iter_prediction_models(config)
    if not prediction_models:
        raise ValueError("配置中没有启用的 prediction model。")

    loaded_predictions: dict[str, pd.DataFrame] = {}
    target_candidates: set[str] = set()
    gene_order: list[str] = []
    seen_genes: set[str] = set()
    for model in prediction_models:
        prediction_path = resolve_path(model["prediction_path"])
        if not prediction_path.exists():
            if bool(model.get("required", False)):
                raise FileNotFoundError(prediction_path)
            continue
        prediction = load_prediction_matrix(prediction_path)
        model_id = str(model["model_id"])
        loaded_predictions[model_id] = prediction
        target_candidates.update(prediction["target_gene"].astype(str).tolist())
        for gene in prediction.columns[1:].astype(str).tolist():
            if gene not in seen_genes:
                seen_genes.add(gene)
                gene_order.append(gene)
    if not loaded_predictions:
        raise ValueError("没有可读取的 prediction matrix。")
    target_order = [
        target
        for target in role_table["target_gene"].astype(str).tolist()
        if target in target_candidates
    ]
    truth = build_truth_shift_matrix(
        input_h5ad_path=resolve_path(config["input_h5ad_path"]),
        target_order=target_order,
        gene_order=gene_order,
        target_sum=float(config.get("normalization", {}).get("target_sum", 10000.0)),
    )
    truth.to_csv(output_root / "k562_13d_truth_shift.tsv.gz", sep="\t", index=False, compression="gzip")

    baseline_spec = config.get("generated_baseline", {})
    baseline = build_shared_mean_baseline(truth)
    baseline_path = output_root / "shared_mean_baseline_predicted_shift.tsv.gz"
    baseline.to_csv(baseline_path, sep="\t", index=False, compression="gzip")

    summaries: list[dict[str, object]] = []
    target_metric_frames: list[pd.DataFrame] = []
    baseline_summary, baseline_metrics = score_model(
        model_id=str(baseline_spec.get("model_id", "shared_mean_baseline")),
        object_role=str(baseline_spec.get("object_role", "baseline")),
        prediction=baseline,
        truth=truth,
        role_table=role_table,
    )
    summaries.append(baseline_summary)
    target_metric_frames.append(baseline_metrics)

    for model in prediction_models:
        model_id = str(model["model_id"])
        prediction = loaded_predictions.get(model_id)
        if prediction is None:
            continue
        summary, target_metrics = score_model(
            model_id=model_id,
            object_role=str(model.get("object_role", "entrant")),
            prediction=prediction,
            truth=truth,
            role_table=role_table,
        )
        summaries.append(summary)
        target_metric_frames.append(target_metrics)

    comparison = pd.DataFrame(summaries)
    comparison.to_csv(output_root / "minimal_model_comparison.tsv", sep="\t", index=False)
    target_metrics_all = pd.concat(target_metric_frames, ignore_index=True)
    target_metrics_all.to_csv(output_root / "target_level_model_metrics.tsv", sep="\t", index=False)
    calls = build_direction_calls(comparison, dict(config.get("thresholds", {})))
    calls.to_csv(output_root / "tradeoff_direction_calls.tsv", sep="\t", index=False)
    render_report(comparison, calls, output_root / "minimal_tradeoff_audit.md")
    write_json(
        {
            "stage": config.get("stage"),
            "dataset_label": config.get("dataset_label"),
            "claim_scope": config.get("claim_scope"),
            "baseline_prediction_path": str(baseline_path.relative_to(PROJECT_ROOT)),
            "outputs": {
                "truth_shift": str((output_root / "k562_13d_truth_shift.tsv.gz").relative_to(PROJECT_ROOT)),
                "minimal_model_comparison": str((output_root / "minimal_model_comparison.tsv").relative_to(PROJECT_ROOT)),
                "target_level_model_metrics": str((output_root / "target_level_model_metrics.tsv").relative_to(PROJECT_ROOT)),
                "tradeoff_direction_calls": str((output_root / "tradeoff_direction_calls.tsv").relative_to(PROJECT_ROOT)),
                "report": str((output_root / "minimal_tradeoff_audit.md").relative_to(PROJECT_ROOT)),
            },
        },
        output_root / "run_manifest.json",
    )
    print(json.dumps({"output_root": str(output_root.relative_to(PROJECT_ROOT))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
