from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.stage1a.benchmark_invariant.catalog import (
    PROJECT_ROOT,
    load_stage1a_aligned_truth_registry,
)


COMMON_EVALUABLE_GENES_PATH = PROJECT_ROOT / "data/frozen/stage1a_truth/common_evaluable_genes.txt"
BASELINE_ROOT = PROJECT_ROOT / "data/baselines/stage1a_main_aligned"
NULL_ROOT = PROJECT_ROOT / "data/nulls/stage1a_main_aligned"

STAGE1A_PRIMARY_BASELINE_NAMES: tuple[str, ...] = (
    "zero_shift_null",
    "mean_shift_baseline",
)
STAGE1A_BASELINE_COMPARATOR_NAMES = frozenset(STAGE1A_PRIMARY_BASELINE_NAMES)


def resolve_project_relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def load_supplementary_common_genes() -> list[str]:
    """加载跨数据集共同基因交集，仅用于 supplementary consistency / sensitivity analysis。

    根据 protocol_blueprint.md 4.3 节，Stage 1A formal main evaluation
    使用 dataset-local evaluation space，不再使用共同交集。
    此函数仅用于 supplementary 分析。
    """
    genes = [
        line.strip()
        for line in COMMON_EVALUABLE_GENES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not genes:
        raise ValueError("common evaluable gene space 为空。")
    return genes


def load_main_aligned_truth_entry(dataset_id: str):
    entries = load_stage1a_aligned_truth_registry()
    matched = [
        entry
        for entry in entries
        if entry.dataset_id == dataset_id
        and str(entry.evaluation_space) == "main_aligned"
        and str(entry.freeze_status) == "frozen"
    ]
    if not matched:
        raise ValueError(f"未找到 dataset_id={dataset_id} 的 frozen main_aligned truth entry。")
    if len(matched) != 1:
        raise ValueError(
            f"dataset_id={dataset_id} 的 frozen main_aligned truth entry 不唯一，"
            f"实际匹配到 {len(matched)} 条。"
        )
    return matched[0]


def read_matrix(matrix_path: Path) -> pd.DataFrame:
    frame = pd.read_csv(matrix_path, sep="\t")
    if frame.empty:
        raise ValueError(f"{matrix_path} 为空。")
    if frame.columns[0] != "target_gene":
        raise ValueError(f"{matrix_path} 首列必须是 target_gene。")
    frame = frame.set_index("target_gene")
    frame.index = frame.index.astype(str)
    frame.columns = frame.columns.astype(str)
    if frame.index.has_duplicates:
        raise ValueError(f"{matrix_path} target_gene 存在重复。")
    if frame.columns.has_duplicates:
        raise ValueError(f"{matrix_path} gene 列存在重复。")
    try:
        frame = frame.apply(pd.to_numeric, errors="raise")
    except ValueError as exc:
        raise ValueError(f"{matrix_path} 存在非 numeric 数值。") from exc
    if frame.isna().any().any():
        raise ValueError(f"{matrix_path} 存在 NaN。")
    if not np.isfinite(frame.to_numpy(dtype=np.float64, copy=False)).all():
        raise ValueError(f"{matrix_path} 存在 inf 或 -inf。")
    return frame


def write_matrix(frame: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        output_path,
        sep="\t",
        compression="gzip",
        index=True,
        index_label="target_gene",
    )


def json_dump(payload: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def align_prediction_to_truth(
    prediction: pd.DataFrame,
    truth: pd.DataFrame,
    dataset_id: str,
    model_id: str,
    prediction_path: Path,
    output_path: Path,
    prediction_space: str,
    allow_missing_targets: bool,
    allow_missing_genes: bool,
) -> tuple[pd.DataFrame, dict[str, object], dict[str, object]]:
    # 根据 protocol_blueprint.md 4.3 节，Stage 1A formal main evaluation
    # 使用 dataset-local evaluation space，不再使用跨数据集共同交集。
    # evaluable genes 从 truth 矩阵的列获取。
    evaluable_genes = list(truth.columns)
    truth_targets = list(truth.index)
    prediction_targets = set(prediction.index)
    evaluable_gene_set = set(evaluable_genes)
    extra_targets = [target for target in prediction.index if target not in truth.index]
    missing_targets = [target for target in truth_targets if target not in prediction_targets]
    aligned_targets = [target for target in truth_targets if target in prediction_targets]

    aligned_genes = [gene for gene in evaluable_genes if gene in prediction.columns]
    missing_genes = [gene for gene in evaluable_genes if gene not in prediction.columns]
    extra_genes = [gene for gene in prediction.columns if gene not in evaluable_gene_set]

    if missing_targets and not allow_missing_targets:
        raise ValueError(f"{dataset_id}::{model_id} 缺少 target，但 contract 不允许。")
    if missing_genes and not allow_missing_genes:
        raise ValueError(f"{dataset_id}::{model_id} 缺少 gene，但 contract 不允许。")
    if not aligned_targets:
        raise ValueError(f"{dataset_id}::{model_id} 没有可对齐的 target。")
    if not aligned_genes:
        raise ValueError(f"{dataset_id}::{model_id} 没有可对齐的 gene。")

    aligned = prediction.loc[aligned_targets, aligned_genes].copy()

    n_targets_expected = int(len(truth_targets))
    n_targets_input = int(prediction.shape[0])
    n_targets_aligned = int(len(aligned_targets))
    missing_target_count = int(len(missing_targets))
    target_coverage_fraction = float(n_targets_aligned / n_targets_expected)

    n_genes_expected = int(len(evaluable_genes))
    n_genes_input = int(prediction.shape[1])
    n_genes_aligned = int(len(aligned_genes))
    missing_gene_count = int(len(missing_genes))
    gene_coverage_fraction = float(n_genes_aligned / n_genes_expected)

    full_target_coverage = missing_target_count == 0 and n_targets_aligned == n_targets_expected
    full_gene_coverage = missing_gene_count == 0 and n_genes_aligned == n_genes_expected
    if full_target_coverage and full_gene_coverage:
        leaderboard_eligibility_status = "official_leaderboard_eligible"
        leaderboard_eligibility_reason = "full_target_and_gene_coverage"
    elif not full_target_coverage and not full_gene_coverage:
        leaderboard_eligibility_status = "degraded_or_supplementary_only"
        leaderboard_eligibility_reason = "missing_targets_and_genes"
    elif not full_target_coverage:
        leaderboard_eligibility_status = "degraded_or_supplementary_only"
        leaderboard_eligibility_reason = "missing_targets"
    else:
        leaderboard_eligibility_status = "degraded_or_supplementary_only"
        leaderboard_eligibility_reason = "missing_genes"

    summary = {
        "model_id": model_id,
        "dataset_id": dataset_id,
        "prediction_space": prediction_space,
        "input_prediction_path": resolve_project_relative(prediction_path),
        "aligned_output_path": resolve_project_relative(output_path),
        "truth_path": resolve_project_relative(load_main_aligned_truth_entry(dataset_id).path),
        "evaluation_space": "main_aligned",
        "formal_scoring_rule": "正式主榜只在 dataset-local evaluation space 上评分（根据 protocol_blueprint.md 4.3 节）。",
        "coverage_policy": "coverage 不足时允许对齐与评分，但必须降级为 degraded_or_supplementary_only。",
        "allow_missing_targets": bool(allow_missing_targets),
        "allow_missing_genes": bool(allow_missing_genes),
        "n_targets_expected": n_targets_expected,
        "n_targets_input": n_targets_input,
        "n_targets_aligned": n_targets_aligned,
        "missing_target_count": missing_target_count,
        "missing_targets_sample": missing_targets[:20],
        "target_coverage_fraction": target_coverage_fraction,
        "n_targets_extra_in_prediction": int(len(extra_targets)),
        "n_genes_expected": n_genes_expected,
        "n_genes_input": n_genes_input,
        "n_genes_aligned": n_genes_aligned,
        "missing_gene_count": missing_gene_count,
        "missing_genes_sample": missing_genes[:20],
        "gene_coverage_fraction": gene_coverage_fraction,
        "n_genes_extra_in_prediction": int(len(extra_genes)),
        "dropped_targets": missing_targets,
        "extra_targets_ignored": extra_targets,
        "dropped_genes": missing_genes,
        "extra_genes_ignored": extra_genes,
        "leaderboard_eligibility_status": leaderboard_eligibility_status,
        "leaderboard_eligibility_reason": leaderboard_eligibility_reason,
        "alignment_pass": True,
    }
    manifest = {
        "stage": "stage1a_prediction_alignment",
        "dataset_id": dataset_id,
        "model_id": model_id,
        "prediction_space": prediction_space,
        "evaluation_space": "main_aligned",
        "coverage_policy": {
            "official_leaderboard_requires_full_target_coverage": True,
            "official_leaderboard_requires_full_gene_coverage": True,
            "degraded_predictions_may_align_and_score_on_intersection_only": True,
        },
        "sources": {
            "prediction_path": resolve_project_relative(prediction_path),
            "truth_registry": "data/frozen/stage1a_truth/aligned_truth_registry.tsv",
            "truth_path": resolve_project_relative(load_main_aligned_truth_entry(dataset_id).path),
            "evaluable_genes_source": "从 truth 矩阵的列获取，不使用跨数据集共同交集。",
        },
        "outputs": {
            "aligned_prediction_path": resolve_project_relative(output_path),
        },
        "contract_flags": {
            "allow_missing_targets": bool(allow_missing_targets),
            "allow_missing_genes": bool(allow_missing_genes),
        },
        "coverage_audit": {
            "n_targets_expected": n_targets_expected,
            "n_targets_input": n_targets_input,
            "n_targets_aligned": n_targets_aligned,
            "missing_target_count": missing_target_count,
            "missing_targets_sample": missing_targets[:20],
            "target_coverage_fraction": target_coverage_fraction,
            "n_genes_expected": n_genes_expected,
            "n_genes_input": n_genes_input,
            "n_genes_aligned": n_genes_aligned,
            "missing_gene_count": missing_gene_count,
            "missing_genes_sample": missing_genes[:20],
            "gene_coverage_fraction": gene_coverage_fraction,
            "leaderboard_eligibility_status": leaderboard_eligibility_status,
            "leaderboard_eligibility_reason": leaderboard_eligibility_reason,
        },
    }
    return aligned, summary, manifest


def safe_pearson(x: np.ndarray, y: np.ndarray) -> float:
    x_std = float(np.std(x))
    y_std = float(np.std(y))
    if x_std == 0.0 or y_std == 0.0:
        return 1.0 if np.allclose(x, y) else 0.0
    return float(np.corrcoef(x, y)[0, 1])


def safe_spearman(x: np.ndarray, y: np.ndarray) -> float:
    x_rank = pd.Series(x).rank(method="average").to_numpy(dtype=np.float64, copy=False)
    y_rank = pd.Series(y).rank(method="average").to_numpy(dtype=np.float64, copy=False)
    return safe_pearson(x_rank, y_rank)


def safe_cosine(x: np.ndarray, y: np.ndarray) -> float:
    x_norm = float(np.linalg.norm(x))
    y_norm = float(np.linalg.norm(y))
    if x_norm == 0.0 or y_norm == 0.0:
        return 1.0 if np.allclose(x, y) else 0.0
    return float(np.dot(x, y) / (x_norm * y_norm))


def rmse(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.sqrt(np.mean((x - y) ** 2)))


def l2_distance(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.linalg.norm(x - y))


def topk_overlap_metrics(x: np.ndarray, y: np.ndarray, k: int) -> dict[str, float]:
    if k < 1:
        raise ValueError("top-k 必须大于等于 1。")
    k_eff = min(k, x.shape[0], y.shape[0])
    if k_eff == x.shape[0]:
        x_top = set(range(x.shape[0]))
    else:
        x_top = set(np.argpartition(np.abs(x), -k_eff)[-k_eff:].tolist())
    if k_eff == y.shape[0]:
        y_top = set(range(y.shape[0]))
    else:
        y_top = set(np.argpartition(np.abs(y), -k_eff)[-k_eff:].tolist())
    intersection = len(x_top & y_top)
    union = len(x_top | y_top)
    return {
        f"top{k}_jaccard": float(intersection / union) if union else 1.0,
        f"top{k}_overlap_fraction": float(intersection / k_eff) if k_eff else 1.0,
    }


def evaluate_prediction_frame(
    prediction: pd.DataFrame,
    truth: pd.DataFrame,
    topk_values: list[int],
) -> tuple[pd.DataFrame, dict[str, float]]:
    if not prediction.index.equals(truth.index):
        raise ValueError("prediction 与 truth 的 target 顺序不一致。")
    if not prediction.columns.equals(truth.columns):
        raise ValueError("prediction 与 truth 的 gene 顺序不一致。")

    records: list[dict[str, object]] = []
    for target in prediction.index:
        pred_vec = prediction.loc[target].to_numpy(dtype=np.float64, copy=False)
        truth_vec = truth.loc[target].to_numpy(dtype=np.float64, copy=False)
        row = {
            "target_gene": target,
            "pearson": safe_pearson(pred_vec, truth_vec),
            "spearman": safe_spearman(pred_vec, truth_vec),
            "cosine_similarity": safe_cosine(pred_vec, truth_vec),
            "rmse": rmse(pred_vec, truth_vec),
            "l2_distance": l2_distance(pred_vec, truth_vec),
        }
        for topk in topk_values:
            row.update(topk_overlap_metrics(pred_vec, truth_vec, topk))
        records.append(row)

    per_target = pd.DataFrame.from_records(records)
    metric_columns = [column for column in per_target.columns if column != "target_gene"]
    aggregates: dict[str, float] = {}
    for column in metric_columns:
        aggregates[f"{column}_mean"] = float(per_target[column].mean())
        aggregates[f"{column}_median"] = float(per_target[column].median())
    return per_target, aggregates


def subset_like_truth(candidate: pd.DataFrame, truth: pd.DataFrame) -> pd.DataFrame:
    return candidate.loc[truth.index, truth.columns].copy()


def comparator_path(dataset_id: str, comparator_name: str) -> Path:
    if comparator_name in STAGE1A_BASELINE_COMPARATOR_NAMES:
        return BASELINE_ROOT / dataset_id / f"{comparator_name}.tsv.gz"
    if comparator_name in {"label_shuffle", "random_pairing"}:
        return NULL_ROOT / dataset_id / f"{comparator_name}.tsv.gz"
    raise ValueError(f"未知 comparator: {comparator_name}")
