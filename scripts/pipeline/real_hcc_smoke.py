from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from wtbench.model_expression_scorer import score_prediction_against_truth_expression
from wtbench.model_structure_scorer import score_prediction_against_frozen_architecture


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = PROJECT_ROOT / "data/predictions/hcc_scorer_ready"
VALIDATION_ROOT = PROJECT_ROOT / "reports/stage2_hcc_prediction_validation"
MANIFEST_ROOT = PROJECT_ROOT / "reports/stage2_hcc_prediction_contract"
OUTPUT_ROOT = PROJECT_ROOT / "reports/real_hcc_smoke"
DETAIL_ROOT = OUTPUT_ROOT / "details"

SMOKE_OBJECTS = [
    ("null_model", "null"),
    ("shared_mean_baseline", "baseline"),
]
CELL_LINES = ["HCC38", "HCC1143"]
ROLE_PREFIXES = {
    "canonical_backbone": "backbone",
    "shift_excess": "shift_excess",
    "context_deviation": "context_deviation",
}
ROLE_DISPLAY = [
    ("A", "canonical_backbone", "backbone"),
    ("B", "shift_excess", "shift_excess"),
    ("C", "context_deviation", "context_deviation"),
]
BACKBONE_DIAGNOSIS_PATH = OUTPUT_ROOT / "backbone_diagnosis.tsv"
BACKBONE_DIAGNOSIS_REPORT_PATH = OUTPUT_ROOT / "backbone_diagnosis.md"

BACKBONE_COSINE_GAP_THRESHOLD = 0.10
BACKBONE_L2_GAP_THRESHOLD = 0.10
BACKBONE_TOP20_GAP_THRESHOLD = 0.08
BACKBONE_RECOVERY_GAP_THRESHOLD = 0.08
SEPARATION_GAIN_THRESHOLD = 0.05


def detect_status(model_id: str, cell_line: str) -> tuple[str, Path | None]:
    prediction_path = INPUT_ROOT / model_id / cell_line / "predicted_shift.tsv.gz"
    validation_path = VALIDATION_ROOT / model_id / cell_line / "validation_summary.json"
    manifest_path = MANIFEST_ROOT / model_id / cell_line / "prediction_manifest.json"
    if not prediction_path.exists():
        return "missing_raw_output", None
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_status = str(manifest.get("export_status", ""))
        if manifest_status in {"alignment_failed", "space_mismatch", "export_ready"}:
            return manifest_status, prediction_path
    if not validation_path.exists():
        return "alignment_failed", prediction_path
    payload = json.loads(validation_path.read_text(encoding="utf-8"))
    if not payload.get("contract_pass"):
        return "space_mismatch", prediction_path
    return "contract_validated", prediction_path


def discover_smoke_objects() -> list[tuple[str, str]]:
    objects = list(SMOKE_OBJECTS)
    if not MANIFEST_ROOT.exists():
        return objects
    for model_dir in sorted(MANIFEST_ROOT.iterdir()):
        if not model_dir.is_dir():
            continue
        manifest_paths = [model_dir / cell_line / "prediction_manifest.json" for cell_line in CELL_LINES]
        if not all(path.exists() for path in manifest_paths):
            continue
        manifests = [json.loads(path.read_text(encoding="utf-8")) for path in manifest_paths]
        object_role = str(manifests[0].get("object_role", ""))
        if object_role != "entrant":
            continue
        if any(str(manifest.get("object_role", "")) != "entrant" for manifest in manifests):
            continue
        objects.append((model_dir.name, "entrant"))
    return objects


def _format_metric(value: object) -> str:
    if pd.isna(value):
        return "nan"
    return f"{float(value):.3f}"


def write_detail_outputs(
    *,
    model_id: str,
    cell_line: str,
    projected: pd.DataFrame,
    structure_scores: pd.DataFrame,
    target_metrics: pd.DataFrame,
    expression_summary: pd.DataFrame,
) -> None:
    detail_dir = DETAIL_ROOT / model_id / cell_line
    detail_dir.mkdir(parents=True, exist_ok=True)
    projected.to_csv(detail_dir / "axis_projection.tsv", sep="\t", index=False)
    structure_scores.to_csv(detail_dir / "structure_scores.tsv", sep="\t", index=False)
    target_metrics.to_csv(detail_dir / "target_expression_metrics.tsv", sep="\t", index=False)
    expression_summary.to_csv(detail_dir / "expression_summary.tsv", sep="\t", index=False)


def append_expression_summary_to_row(
    row: dict[str, object],
    expression_summary: pd.DataFrame,
) -> None:
    if expression_summary.empty:
        return
    summary_map = expression_summary.set_index("group_key").to_dict(orient="index")
    overall = summary_map.get("all_targets")
    if overall is not None:
        row.update(
            {
                "cosine_similarity_mean": float(overall["cosine_similarity_mean"]),
                "l2_distance_mean": float(overall["l2_distance_mean"]),
                "top20_overlap_mean": float(overall["top20_overlap_mean"]),
            }
        )
    for role_name, prefix in ROLE_PREFIXES.items():
        payload = summary_map.get(role_name)
        if payload is None:
            continue
        row.update(
            {
                f"{prefix}_cosine_similarity_mean": float(payload["cosine_similarity_mean"]),
                f"{prefix}_l2_distance_mean": float(payload["l2_distance_mean"]),
                f"{prefix}_top20_overlap_mean": float(payload["top20_overlap_mean"]),
                f"{prefix}_target_count": int(payload["target_count"]),
            }
        )


def render_report(summary: pd.DataFrame, output_path: Path) -> None:
    lines = [
        "# Stage 2 Real HCC Smoke",
        "",
        "## 定位",
        "",
        "- 本报告只覆盖真实 HCC 输入桥的 smoke adjudication。",
        "- 当前检查 `null_model`、`shared_mean_baseline` 与所有已冻结 entrant 是否成功导出、通过 contract、并可进入 scorer。",
        "- 这仍是 smoke adjudication，不直接上升为 architecture recovery 正式结论。",
        "",
        "## 状态",
        "",
        "- A/B/C 三层在本报告中固定映射到：`A=canonical_backbone`，`B=shift_excess`，`C=context_deviation`。",
        "- `cosine`、`L2`、`top-20 overlap` 只作为辅助裁决层，用于解释为什么赢/输，不替代 architecture-level 主裁决。",
        "",
    ]
    for row in summary.itertuples(index=False):
        lines.append(f"### {row.model_id} / {row.cell_line}")
        lines.append(f"- export_status = `{row.export_status}`。")
        if row.export_status == "contract_validated":
            lines.append(
                f"- backbone recovery = `{row.backbone_recovery_score:.3f}`；"
                f"shift-excess identification = `{row.shift_excess_identification_score:.3f}`；"
                f"structure-vs-context separation = `{row.structure_vs_context_separation_score:.3f}`。"
            )
            lines.append(
                f"- 辅助数值层（全 targets）：cosine = `{_format_metric(row.cosine_similarity_mean)}`；"
                f"L2 = `{_format_metric(row.l2_distance_mean)}`；"
                f"top-20 overlap = `{_format_metric(row.top20_overlap_mean)}`。"
            )
            for layer_key, role_name, prefix in ROLE_DISPLAY:
                lines.append(
                    f"- {layer_key} 层 `{role_name}`：cosine = `{_format_metric(getattr(row, f'{prefix}_cosine_similarity_mean'))}`；"
                    f"L2 = `{_format_metric(getattr(row, f'{prefix}_l2_distance_mean'))}`；"
                    f"top-20 overlap = `{_format_metric(getattr(row, f'{prefix}_top20_overlap_mean'))}`。"
                )
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _safe_float(value: object) -> float:
    if pd.isna(value):
        return float("nan")
    return float(value)


def classify_backbone_failure(
    *,
    backbone_cosine_gap: float,
    backbone_l2_gap: float,
    backbone_top20_gap: float,
    backbone_recovery_gap: float,
    separation_gain: float,
) -> str:
    direction_flag = (
        backbone_cosine_gap >= BACKBONE_COSINE_GAP_THRESHOLD
        and backbone_top20_gap < BACKBONE_TOP20_GAP_THRESHOLD
    )
    amplitude_flag = (
        backbone_l2_gap >= BACKBONE_L2_GAP_THRESHOLD
        and backbone_cosine_gap < BACKBONE_COSINE_GAP_THRESHOLD
    )
    tradeoff_flag = (
        backbone_recovery_gap >= BACKBONE_RECOVERY_GAP_THRESHOLD
        and separation_gain >= SEPARATION_GAIN_THRESHOLD
    )
    active = [direction_flag, amplitude_flag, tradeoff_flag]
    if sum(active) != 1:
        return "mixed"
    if direction_flag:
        return "direction"
    if amplitude_flag:
        return "amplitude"
    return "tradeoff"


def build_backbone_diagnosis(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()
    validated = summary.loc[summary["export_status"].eq("contract_validated")].copy()
    if validated.empty:
        return pd.DataFrame()
    baseline = validated.loc[validated["model_id"].eq("shared_mean_baseline")].set_index("cell_line")
    rows: list[dict[str, object]] = []
    for row in validated.itertuples(index=False):
        if row.model_id == "shared_mean_baseline":
            continue
        if row.object_role != "entrant":
            continue
        if row.cell_line not in baseline.index:
            continue
        baseline_row = baseline.loc[row.cell_line]
        backbone_cosine = _safe_float(getattr(row, "backbone_cosine_similarity_mean", float("nan")))
        backbone_l2 = _safe_float(getattr(row, "backbone_l2_distance_mean", float("nan")))
        backbone_top20 = _safe_float(getattr(row, "backbone_top20_overlap_mean", float("nan")))
        baseline_backbone_cosine = _safe_float(baseline_row.get("backbone_cosine_similarity_mean"))
        baseline_backbone_l2 = _safe_float(baseline_row.get("backbone_l2_distance_mean"))
        baseline_backbone_top20 = _safe_float(baseline_row.get("backbone_top20_overlap_mean"))
        backbone_recovery = _safe_float(getattr(row, "backbone_recovery_score", float("nan")))
        baseline_backbone_recovery = _safe_float(baseline_row.get("backbone_recovery_score"))
        separation = _safe_float(getattr(row, "structure_vs_context_separation_score", float("nan")))
        baseline_separation = _safe_float(baseline_row.get("structure_vs_context_separation_score"))
        failure_mode = classify_backbone_failure(
            backbone_cosine_gap=baseline_backbone_cosine - backbone_cosine,
            backbone_l2_gap=backbone_l2 - baseline_backbone_l2,
            backbone_top20_gap=baseline_backbone_top20 - backbone_top20,
            backbone_recovery_gap=baseline_backbone_recovery - backbone_recovery,
            separation_gain=separation - baseline_separation,
        )
        rows.append(
            {
                "model_id": row.model_id,
                "cell_line": row.cell_line,
                "backbone_recovery": backbone_recovery,
                "backbone_cosine": backbone_cosine,
                "backbone_L2": backbone_l2,
                "backbone_top20": backbone_top20,
                "baseline_backbone_recovery": baseline_backbone_recovery,
                "baseline_backbone_cosine": baseline_backbone_cosine,
                "baseline_backbone_L2": baseline_backbone_l2,
                "baseline_backbone_top20": baseline_backbone_top20,
                "structure_vs_context_separation": separation,
                "baseline_structure_vs_context_separation": baseline_separation,
                "failure_mode_call": failure_mode,
            }
        )
    return pd.DataFrame(rows)


def render_backbone_diagnosis_report(diagnosis: pd.DataFrame, output_path: Path) -> None:
    lines = [
        "# GEARS Backbone 诊断摘要",
        "",
        "## 定位",
        "",
        "- 这是 GEARS 正式 recipe sweep 前的最小诊断中间产物。",
        "- 它只服务于 `canonical_backbone recovery` 的失败分解，不引入新 truth object、entrant 或评分体系。",
        "- `failure_mode_call` 固定限制为：`direction / amplitude / tradeoff / mixed`。",
        "",
        "## 诊断口径",
        "",
        "- `direction`：backbone cosine 明显落后，但 top-20 overlap 没有同步明显变差，优先怀疑方向没有学到。",
        "- `amplitude`：backbone L2 明显落后，但 cosine 没有同步明显变差，优先怀疑幅度校准。",
        "- `tradeoff`：backbone recovery 落后，同时 separation 明显更强，按 backbone-vs-separation trade-off 处理。",
        "- `mixed`：不能被单一 failure mode 干净解释。",
        "",
    ]
    if diagnosis.empty:
        lines.extend(
            [
                "## 结果",
                "",
                "- 当前没有可写出的 backbone 诊断记录。",
            ]
        )
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return
    lines.extend(["## 结果", ""])
    for row in diagnosis.itertuples(index=False):
        lines.append(f"### {row.model_id} / {row.cell_line}")
        lines.append(
            f"- backbone: recovery = `{row.backbone_recovery:.3f}`；"
            f"cosine = `{row.backbone_cosine:.3f}`；"
            f"L2 = `{row.backbone_L2:.3f}`；"
            f"top-20 = `{row.backbone_top20:.3f}`。"
        )
        lines.append(
            f"- baseline: recovery = `{row.baseline_backbone_recovery:.3f}`；"
            f"cosine = `{row.baseline_backbone_cosine:.3f}`；"
            f"L2 = `{row.baseline_backbone_L2:.3f}`；"
            f"top-20 = `{row.baseline_backbone_top20:.3f}`。"
        )
        lines.append(
            f"- separation: entrant = `{row.structure_vs_context_separation:.3f}`；"
            f"baseline = `{row.baseline_structure_vs_context_separation:.3f}`。"
        )
        lines.append(f"- failure_mode_call = `{row.failure_mode_call}`。")
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for model_id, object_role in discover_smoke_objects():
        for cell_line in CELL_LINES:
            status, prediction_path = detect_status(model_id, cell_line)
            row: dict[str, object] = {
                "model_id": model_id,
                "object_role": object_role,
                "cell_line": cell_line,
                "export_status": status,
            }
            if status == "contract_validated" and prediction_path is not None:
                projected, scores = score_prediction_against_frozen_architecture(prediction_path)
                score_map = dict(zip(scores["score_name"], scores["score_value"]))
                row.update(score_map)
                target_metrics, expression_summary = score_prediction_against_truth_expression(
                    prediction_path,
                    cell_line=cell_line,
                )
                append_expression_summary_to_row(row, expression_summary)
                write_detail_outputs(
                    model_id=model_id,
                    cell_line=cell_line,
                    projected=projected,
                    structure_scores=scores,
                    target_metrics=target_metrics,
                    expression_summary=expression_summary,
                )
            rows.append(row)
    summary = pd.DataFrame(rows)
    summary.to_csv(OUTPUT_ROOT / "smoke_summary.tsv", sep="\t", index=False)
    backbone_diagnosis = build_backbone_diagnosis(summary)
    backbone_diagnosis.to_csv(BACKBONE_DIAGNOSIS_PATH, sep="\t", index=False)
    render_backbone_diagnosis_report(backbone_diagnosis, BACKBONE_DIAGNOSIS_REPORT_PATH)
    if not summary.empty:
        metric_columns = [
            "backbone_recovery_score",
            "shift_excess_identification_score",
            "structure_vs_context_separation_score",
            "cosine_similarity_mean",
            "l2_distance_mean",
            "top20_overlap_mean",
        ]
        existing_metric_columns = [column for column in metric_columns if column in summary.columns]
        comparison = (
            summary.groupby(["model_id", "object_role"], as_index=False)[existing_metric_columns]
            .mean(numeric_only=True)
            .sort_values(
                ["backbone_recovery_score", "shift_excess_identification_score", "structure_vs_context_separation_score"],
                ascending=[False, False, False],
                na_position="last",
            )
        )
        comparison.to_csv(OUTPUT_ROOT / "model_comparison.tsv", sep="\t", index=False)
    (OUTPUT_ROOT / "smoke_summary.json").write_text(
        json.dumps(summary.to_dict(orient="records"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    render_report(summary, OUTPUT_ROOT / "smoke_report.md")


if __name__ == "__main__":
    main()
