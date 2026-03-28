from __future__ import annotations

"""
Stage 1A Baseline and Null Models.

Baseline Family:
---------------
1. zero_shift_null: 预测所有 gene 的 shift 为 0。验证模型是否优于零预测。

2. mean_shift_baseline: 预测所有 perturbation 的 shift 为训练集的平均 shift。
   验证模型是否优于均值预测。

3. linear_delta_baseline_legacy:
   警告：此 baseline 不是 Ahlmann-Eltze et al. 2025 Nature Methods 论文中的
   PCA-derived linear model。

   当前实现是 deterministic random-feature ridge baseline：
   - 使用随机特征设计矩阵 + ridge 回归
   - 不是从 training data 学习低秩结构
   - 不是 paper-aligned 实现

   新增的 paper-aligned baseline 请参考：
   - linear_pca_shift_baseline (src/wtbench/baselines/linear_pca_shift_baseline.py)
   - linear_external_p_shift_baseline (待实现)

Null Models:
------------
1. label_shuffle: 将 perturbation labels 打乱，测试标签随机化下的性能。

2. random_pairing: 将 truth 值与 perturbation 随机配对，测试随机配对下的性能。
"""

import hashlib
import json
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

from stage1a_split_plan_b import load_split_governance, plan_b_heldout_targets
from stage1a_catalog import PROJECT_ROOT, get_formal_dataset_contract, load_stage1a_aligned_truth_registry


BASELINE_OUTPUT_ROOT = PROJECT_ROOT / "data/baselines/stage1a_main_aligned"
NULL_OUTPUT_ROOT = PROJECT_ROOT / "data/nulls/stage1a_main_aligned"
REPORT_OUTPUT_ROOT = PROJECT_ROOT / "reports/stage1a/baselines_nulls"
COMBINED_SUMMARY_PATH = REPORT_OUTPUT_ROOT / "combined_baseline_null_summary.tsv"
MANIFEST_PATH = REPORT_OUTPUT_ROOT / "baseline_null_manifest.json"
FROZEN_ELIGIBLE_TARGETS_PATH = PROJECT_ROOT / "data/frozen/stage1a_formal/eligible_targets.tsv"
EXPECTED_EVALUATION_SPACE = "main_aligned"
EXPECTED_FREEZE_STATUS = "frozen"

# Legacy baseline names (保留用于兼容历史结果)
BASELINE_NAMES = [
    "zero_shift_null",
    "mean_shift_baseline",
    "linear_delta_baseline_legacy",  # 标记为 legacy
]

# 新增 paper-aligned baselines 将通过独立脚本运行
# See: src/wtbench/baselines/linear_pca_shift_baseline.py

NULL_NAMES = ["label_shuffle", "random_pairing"]
OUTPUT_NAMES = [*BASELINE_NAMES, *NULL_NAMES]

# Legacy linear baseline 参数
LINEAR_DELTA_RIDGE_LAMBDA = 1.0
LINEAR_DELTA_FEATURE_DIM = 32


def resolve_project_relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def dataset_seed(dataset_id: str, method_name: str) -> int:
    digest = hashlib.sha256(f"{dataset_id}::{method_name}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="little", signed=False)


def load_main_aligned_truth_entries() -> list:
    entries = load_stage1a_aligned_truth_registry()
    filtered = [
        entry
        for entry in entries
        if str(entry.evaluation_space) == EXPECTED_EVALUATION_SPACE
        and str(entry.freeze_status) == EXPECTED_FREEZE_STATUS
    ]
    if not filtered:
        raise ValueError("未找到 evaluation_space=main_aligned 且 freeze_status=frozen 的 truth。")
    return filtered


def load_eligible_rows_for_dataset(dataset_id: str) -> pd.DataFrame:
    eligible = pd.read_csv(FROZEN_ELIGIBLE_TARGETS_PATH, sep="\t")
    eligible["eligible_for_pseudobulk"] = (
        eligible["eligible_for_pseudobulk"].astype("string").str.lower().eq("true")
    )
    sub = eligible.loc[
        eligible["dataset_id"].astype("string").eq(dataset_id) & eligible["eligible_for_pseudobulk"]
    ].copy()
    if sub.empty:
        raise ValueError(f"{dataset_id}: frozen eligible 为空。")
    return sub


def mean_expression(matrix: object) -> np.ndarray:
    if getattr(matrix, "shape", None) is not None and matrix.shape[0] == 0:
        raise ValueError("pseudobulk 聚合时收到空细胞集合。")
    if sparse.issparse(matrix):
        values = np.asarray(matrix.mean(axis=0)).ravel()
    else:
        values = np.asarray(matrix.mean(axis=0)).ravel()
    return values.astype(np.float64, copy=False)


def compute_train_target_deltas(
    adata: ad.AnnData,
    evaluable_genes: list[str],
    heldout_targets: set[str],
) -> tuple[list[str], np.ndarray]:
    obs = adata.obs.copy()
    obs["is_control"] = obs["is_control"].astype(bool)
    obs["target_gene"] = obs["target_gene"].astype("string")
    gene_names = adata.var.index.astype(str)
    gene_index = pd.Index(gene_names)
    gene_positions = gene_index.get_indexer(evaluable_genes)
    if (gene_positions < 0).any():
        missing = [evaluable_genes[i] for i, pos in enumerate(gene_positions) if pos < 0][:10]
        raise ValueError(f"缺少 evaluable gene: {missing}")

    control_mask = obs["is_control"].to_numpy()
    control_values = mean_expression(adata.X[control_mask])
    train_targets = sorted(
        target
        for target in obs.loc[~obs["is_control"], "target_gene"].dropna().unique().tolist()
        if target not in heldout_targets
    )
    if not train_targets:
        raise ValueError("没有可用的非 held-out train targets。")

    delta_rows = []
    for target in train_targets:
        target_mask = (~obs["is_control"]).to_numpy() & obs["target_gene"].eq(target).fillna(False).to_numpy(dtype=bool)
        perturbed_values = mean_expression(adata.X[target_mask])
        delta_rows.append((perturbed_values - control_values)[gene_positions])
    return train_targets, np.asarray(delta_rows, dtype=np.float64)


def linear_delta_design_matrix(targets: list[str], dataset_id: str, n_features: int) -> np.ndarray:
    rows = []
    for t in targets:
        rng = np.random.default_rng(dataset_seed(dataset_id, f"linear_delta_baseline::{t}"))
        feat = rng.standard_normal(n_features)
        rows.append(np.concatenate([[1.0], feat]))
    return np.asarray(rows, dtype=np.float64)


def ridge_multivariate(Y_train: np.ndarray, X_train: np.ndarray, X_query: np.ndarray, ridge_lambda: float) -> np.ndarray:
    """Y_train: (n_train, n_genes), X_train: (n_train, p), X_query: (n_query, p) -> (n_query, n_genes)"""
    p = X_train.shape[1]
    xt_x = X_train.T @ X_train
    xt_y = X_train.T @ Y_train
    coef = np.linalg.solve(xt_x + ridge_lambda * np.eye(p), xt_y)
    return X_query @ coef


def build_linear_delta_baseline_legacy(truth: pd.DataFrame, dataset_id: str, split_seed: int) -> pd.DataFrame:
    contract = get_formal_dataset_contract(dataset_id)
    # 根据 protocol_blueprint.md 4.3 节，使用 dataset-local evaluation space
    evaluable_genes = list(truth.columns)

    eligible = load_eligible_rows_for_dataset(dataset_id)
    heldout_order = plan_b_heldout_targets(eligible, dataset_id, split_seed)
    if [str(x) for x in truth.index] != [str(x) for x in heldout_order]:
        raise ValueError(f"{dataset_id}: truth 行顺序与方案 B held-out 不一致。")

    heldout_set = set(str(x) for x in heldout_order)
    adata = ad.read_h5ad(contract.path)
    try:
        train_targets, y_train = compute_train_target_deltas(adata, evaluable_genes, heldout_set)
        n_feat = min(LINEAR_DELTA_FEATURE_DIM, max(4, len(train_targets)))
        x_train = linear_delta_design_matrix(train_targets, dataset_id, n_feat)
        test_targets = [str(x) for x in truth.index.tolist()]
        x_test = linear_delta_design_matrix(test_targets, dataset_id, n_feat)
        y_pred = ridge_multivariate(
            y_train,
            x_train,
            x_test,
            ridge_lambda=LINEAR_DELTA_RIDGE_LAMBDA,
        )
        return pd.DataFrame(y_pred, index=truth.index, columns=truth.columns)
    finally:
        del adata


def load_truth_matrix(truth_path: Path) -> pd.DataFrame:
    truth = pd.read_csv(truth_path, sep="\t")
    if truth.empty:
        raise ValueError(f"{truth_path} 为空。")
    if truth.columns[0] != "target_gene":
        raise ValueError(f"{truth_path} 首列不是 target_gene。")
    truth = truth.set_index("target_gene")
    truth.index = truth.index.astype(str)
    truth.columns = truth.columns.astype(str)
    if truth.index.has_duplicates:
        raise ValueError(f"{truth_path} target_gene 存在重复。")
    if truth.columns.has_duplicates:
        raise ValueError(f"{truth_path} gene 列存在重复。")
    return truth


def build_zero_shift_null(truth: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        np.zeros(truth.shape, dtype=np.float64),
        index=truth.index,
        columns=truth.columns,
    )


def build_mean_shift_baseline(truth: pd.DataFrame) -> pd.DataFrame:
    mean_vector = truth.mean(axis=0).to_numpy(dtype=np.float64, copy=False)
    values = np.tile(mean_vector, (truth.shape[0], 1))
    return pd.DataFrame(values, index=truth.index, columns=truth.columns)


def build_label_shuffle(truth: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    shuffled_index = truth.index.to_numpy(copy=True)[rng.permutation(truth.shape[0])]
    shuffled = truth.copy()
    shuffled.index = shuffled_index
    return shuffled.reindex(truth.index)


def derangement(size: int, rng: np.random.Generator) -> np.ndarray:
    if size < 2:
        raise ValueError("random_pairing 至少需要 2 个 target 才能构造无固定点随机配对。")
    while True:
        permutation = rng.permutation(size)
        if np.all(permutation != np.arange(size)):
            return permutation


def build_random_pairing(truth: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    permuted_positions = derangement(truth.shape[0], rng)
    paired_values = truth.to_numpy(copy=True)[permuted_positions, :]
    return pd.DataFrame(paired_values, index=truth.index, columns=truth.columns)


def validate_output(truth: pd.DataFrame, candidate: pd.DataFrame) -> dict[str, bool]:
    return {
        "n_rows_matches_truth": candidate.shape[0] == truth.shape[0],
        "n_columns_matches_truth": candidate.shape[1] == truth.shape[1],
        "target_index_matches_truth": candidate.index.equals(truth.index),
        "gene_columns_match_truth": candidate.columns.equals(truth.columns),
    }


def write_matrix(frame: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, sep="\t", compression="gzip", index=True, index_label="target_gene")


def build_dataset_outputs(entry, split_seed: int) -> dict[str, object]:
    truth = load_truth_matrix(entry.path)
    baseline_dir = BASELINE_OUTPUT_ROOT / entry.dataset_id
    null_dir = NULL_OUTPUT_ROOT / entry.dataset_id
    report_dir = REPORT_OUTPUT_ROOT / entry.dataset_id
    report_dir.mkdir(parents=True, exist_ok=True)

    outputs: dict[str, dict[str, object]] = {}

    zero_shift_null = build_zero_shift_null(truth)
    mean_shift_baseline = build_mean_shift_baseline(truth)
    linear_delta_baseline_legacy = build_linear_delta_baseline_legacy(truth, entry.dataset_id, split_seed)
    label_shuffle_seed = dataset_seed(entry.dataset_id, "label_shuffle")
    random_pairing_seed = dataset_seed(entry.dataset_id, "random_pairing")
    label_shuffle = build_label_shuffle(truth, label_shuffle_seed)
    random_pairing = build_random_pairing(truth, random_pairing_seed)

    built_frames = {
        "zero_shift_null": zero_shift_null,
        "mean_shift_baseline": mean_shift_baseline,
        "linear_delta_baseline_legacy": linear_delta_baseline_legacy,
        "label_shuffle": label_shuffle,
        "random_pairing": random_pairing,
    }

    output_paths = {
        name: (baseline_dir if name in BASELINE_NAMES else null_dir) / f"{name}.tsv.gz"
        for name in OUTPUT_NAMES
    }

    for name in OUTPUT_NAMES:
        frame = built_frames[name]
        checks = validate_output(truth=truth, candidate=frame)
        if not all(checks.values()):
            raise ValueError(f"{entry.dataset_id}::{name} 未通过对齐校验: {checks}")
        write_matrix(frame=frame, output_path=output_paths[name])
        outputs[name] = {
            "path": resolve_project_relative(output_paths[name]),
            **checks,
        }

    dataset_summary = {
        "dataset_id": entry.dataset_id,
        "truth_path": resolve_project_relative(entry.path),
        "evaluation_space": str(entry.evaluation_space),
        "n_targets": int(truth.shape[0]),
        "n_genes": int(truth.shape[1]),
        "control_definition": entry.control_definition,
        "freeze_status": entry.freeze_status,
        "matrix_source": str(entry.matrix_source),
        "log_normalization_applied_in_truth_build": bool(
            entry.log_normalization_applied_in_truth_build
        ),
        "delta_space": str(entry.delta_space),
        "split_seed_for_linear_delta": int(split_seed),
        "linear_delta_baseline_legacy": {
            "ridge_lambda": LINEAR_DELTA_RIDGE_LAMBDA,
            "feature_dim_cap": LINEAR_DELTA_FEATURE_DIM,
            "definition": (
                "legacy 随机特征 ridge 实现；对 train perturbations 的 delta 做 ridge 回归，"
                "特征为截距 + 与 target_gene 绑定的确定性随机向量；仅用于拟合 Y_train，"
                "对 held-out 行用同一特征映射预测，不使用 held-out 真值。"
            ),
            "formal_status": "legacy_only_not_canonical_stage1a_linear_baseline",
        },
        "random_seeds": {
            "label_shuffle": label_shuffle_seed,
            "random_pairing": random_pairing_seed,
        },
        "outputs": outputs,
    }
    summary_path = report_dir / "baseline_null_summary.json"
    summary_path.write_text(
        json.dumps(dataset_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    combined_row: dict[str, object] = {
        "dataset_id": entry.dataset_id,
        "truth_path": resolve_project_relative(entry.path),
        "evaluation_space": str(entry.evaluation_space),
        "n_targets": int(truth.shape[0]),
        "n_genes": int(truth.shape[1]),
        "control_definition": entry.control_definition,
        "freeze_status": entry.freeze_status,
        "matrix_source": str(entry.matrix_source),
        "log_normalization_applied_in_truth_build": bool(
            entry.log_normalization_applied_in_truth_build
        ),
        "delta_space": str(entry.delta_space),
        "label_shuffle_seed": label_shuffle_seed,
        "random_pairing_seed": random_pairing_seed,
    }
    for name in OUTPUT_NAMES:
        o = outputs[name]
        combined_row[f"{name}_path"] = o["path"]
        combined_row[f"{name}_n_rows_matches_truth"] = o["n_rows_matches_truth"]
        combined_row[f"{name}_n_columns_matches_truth"] = o["n_columns_matches_truth"]
        combined_row[f"{name}_target_index_matches_truth"] = o["target_index_matches_truth"]
        combined_row[f"{name}_gene_columns_match_truth"] = o["gene_columns_match_truth"]
    combined_row["dataset_summary_path"] = resolve_project_relative(summary_path)
    print(f"已写出: {summary_path}")
    return combined_row


def build_manifest(combined_summary: pd.DataFrame) -> dict[str, object]:
    return {
        "stage": "stage1a_main_aligned",
        "freeze_status": EXPECTED_FREEZE_STATUS,
        "evaluation_space": EXPECTED_EVALUATION_SPACE,
        "source_truth_registry": "data/frozen/stage1a_truth/aligned_truth_registry.tsv",
        "baseline_output_root": "data/baselines/stage1a_main_aligned",
        "null_output_root": "data/nulls/stage1a_main_aligned",
        "combined_summary_path": resolve_project_relative(COMBINED_SUMMARY_PATH),
        "provenance_fields": [
            "matrix_source",
            "log_normalization_applied_in_truth_build",
            "delta_space",
        ],
        "n_datasets": int(len(combined_summary)),
        "baselines": {
            "zero_shift_null": "与 truth shape 一致的全零 shift（旧称 no_change）",
            "mean_shift_baseline": "按基因对 truth 在 target 维度取均值后广播到所有 target 行",
            "linear_delta_baseline_legacy": (
                "legacy 随机特征 ridge baseline；仅用 train perturbation 的 delta 拟合，"
                "不作为当前仓库 Stage 1A canonical linear baseline"
            ),
        },
        "nulls": {
            "label_shuffle": "固定 seed，对 truth 的 target 标签做随机重排；profile 行顺序本体不变",
            "random_pairing": "固定 seed，对 truth 行做无固定点随机重排并形成随机 target-to-profile 配对",
        },
        "datasets": combined_summary.to_dict(orient="records"),
    }


def main() -> None:
    BASELINE_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    NULL_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    gov = load_split_governance()
    split_seed = int(gov["default_split_seed_for_truth_freeze"])

    entries = load_main_aligned_truth_entries()
    combined_rows = [build_dataset_outputs(entry, split_seed) for entry in entries]
    combined_summary = pd.DataFrame(combined_rows).sort_values("dataset_id").reset_index(drop=True)
    combined_summary.to_csv(COMBINED_SUMMARY_PATH, sep="\t", index=False)
    MANIFEST_PATH.write_text(
        json.dumps(build_manifest(combined_summary), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"已写出: {COMBINED_SUMMARY_PATH}")
    print(f"已写出: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
