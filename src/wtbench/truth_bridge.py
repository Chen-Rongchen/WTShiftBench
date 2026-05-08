from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.io import mmread
from scipy.spatial import distance
from scipy.stats import mannwhitneyu, pearsonr, spearmanr
from sklearn.decomposition import TruncatedSVD


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRUTH_METRIC_COLUMNS = [
    "real_shift_L2",
    "real_shift_mean_abs",
    "real_shift_top20_mean",
    "real_shift_top50_mean",
    "real_shift_top100_mean",
    "real_shift_top50_concentration",
    "real_Edistance",
    "real_DEG_burden",
]
DEPMAP_ENDPOINT_COLUMNS = [
    "depmap_gene_effect",
    "depmap_gene_dependency",
]
METRIC_TIERS = {
    "real_shift_L2": "primary",
    "real_shift_mean_abs": "primary",
    "real_Edistance": "supplementary",
    "real_DEG_burden": "auxiliary",
    "real_shift_top20_mean": "exploratory",
    "real_shift_top50_mean": "exploratory",
    "real_shift_top100_mean": "exploratory",
    "real_shift_top50_concentration": "exploratory",
}
DATASET_ROLE_TO_SECTION = {
    "primary": "main",
    "supplementary": "supplement",
    "exploratory": "appendix",
}
DEPMAP_ALIGNMENT_DIRECTION = {
    "depmap_gene_effect": -1.0,
    "depmap_gene_dependency": 1.0,
}
DEFAULT_EDISTANCE_PAIRWISE_MAX_POINTS = 5000


@dataclass(frozen=True)
class DatasetSpec:
    cell_line: str
    depmap_model_id: str
    source_kind: str
    dataset_role: str = "primary"
    matrix_path: Path | None = None
    barcodes_path: Path | None = None
    features_path: Path | None = None
    protospacer_calls_path: Path | None = None
    h5ad_path: Path | None = None


def stringify(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("")


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_config(config_path: Path) -> dict[str, Any]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    required = {"datasets", "depmap", "output", "filters", "metrics", "group_comparison"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"Stage 2 bridge 配置缺少字段: {missing}")
    return payload


def build_dataset_specs(config: dict[str, Any]) -> list[DatasetSpec]:
    specs: list[DatasetSpec] = []
    for item in config["datasets"]:
        source_kind = str(item.get("source_kind", "mtx_protospacer"))
        dataset_role = str(item.get("dataset_role", "primary"))
        if dataset_role not in DATASET_ROLE_TO_SECTION:
            raise ValueError(f"不支持的 dataset_role: {dataset_role}")
        specs.append(
            DatasetSpec(
                cell_line=str(item["cell_line"]),
                depmap_model_id=str(item["depmap_model_id"]),
                source_kind=source_kind,
                dataset_role=dataset_role,
                matrix_path=resolve_path(item["matrix_path"]) if item.get("matrix_path") else None,
                barcodes_path=resolve_path(item["barcodes_path"]) if item.get("barcodes_path") else None,
                features_path=resolve_path(item["features_path"]) if item.get("features_path") else None,
                protospacer_calls_path=resolve_path(item["protospacer_calls_path"])
                if item.get("protospacer_calls_path")
                else None,
                h5ad_path=resolve_path(item["h5ad_path"]) if item.get("h5ad_path") else None,
            )
        )
    return specs


def parse_target_gene(feature_call: str) -> str:
    text = str(feature_call or "")
    if "_sgRNA" not in text:
        return text
    return text.split("_sgRNA", 1)[0]


def is_control_target(target_gene: str, control_prefix: str) -> bool:
    return str(target_gene).startswith(control_prefix)


def clean_depmap_gene_columns(columns: pd.Index) -> list[str]:
    cleaned: list[str] = []
    for column in columns:
        text = str(column)
        if text == "Unnamed: 0":
            cleaned.append("ModelID")
            continue
        if " (" in text and text.endswith(")"):
            cleaned.append(text.split(" (", 1)[0])
        else:
            cleaned.append(text)
    return cleaned


def load_depmap_endpoint(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame.columns = clean_depmap_gene_columns(pd.Index(frame.columns))
    frame = frame.rename(columns={"ModelID": "depmap_model_id"})
    if "depmap_model_id" not in frame.columns:
        raise ValueError(f"{path} 缺少 depmap_model_id 列。")
    return frame


def load_feature_metadata(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        sep="\t",
        header=None,
        names=["feature_id", "feature_name", "feature_type"],
    )
    frame["feature_name"] = stringify(frame["feature_name"])
    frame["feature_type"] = stringify(frame["feature_type"])
    return frame


def load_single_feature_calls(spec: DatasetSpec, control_prefix: str) -> pd.DataFrame:
    if spec.protospacer_calls_path is None:
        raise ValueError(f"{spec.cell_line} 缺少 protospacer_calls_path。")
    calls = pd.read_csv(spec.protospacer_calls_path)
    required = {"cell_barcode", "num_features", "feature_call", "num_umis"}
    missing = sorted(required - set(calls.columns))
    if missing:
        raise ValueError(f"{spec.cell_line} protospacer calls 缺少列: {missing}")

    calls = calls.loc[calls["num_features"] == 1].copy()
    calls["cell_barcode"] = stringify(calls["cell_barcode"])
    calls["feature_call"] = stringify(calls["feature_call"])
    calls["target_gene"] = calls["feature_call"].map(parse_target_gene).astype("string")
    calls["is_control"] = calls["target_gene"].map(
        lambda x: is_control_target(str(x), control_prefix)
    )
    return calls.sort_values("cell_barcode").reset_index(drop=True)


def resolve_single_perturbation_status(
    obs: pd.DataFrame,
    *,
    allow_degraded_unverified: bool,
) -> tuple[pd.Series, str, str]:
    if "is_single_perturbation" in obs.columns:
        mask = obs["is_control"].astype(bool) | obs["is_single_perturbation"].astype(bool)
        return mask, "verified_single_perturbation", "is_single_perturbation"
    if "num_features" in obs.columns:
        mask = obs["is_control"].astype(bool) | obs["num_features"].eq(1)
        return mask, "verified_via_num_features_eq_1", "num_features"
    if allow_degraded_unverified:
        return (
            pd.Series(True, index=obs.index),
            "degraded_unverified_single_perturbation",
            "unverified",
        )
    raise ValueError(
        "formal 模式要求显式单扰动证据；当前输入既无 is_single_perturbation，也无 num_features==1 可验证。"
    )


def load_expression_for_called_cells(
    spec: DatasetSpec,
    calls: pd.DataFrame,
) -> tuple[sparse.csr_matrix, pd.DataFrame, pd.DataFrame]:
    if spec.barcodes_path is None or spec.features_path is None or spec.matrix_path is None:
        raise ValueError(f"{spec.cell_line} 的 mtx_protospacer 源缺少必要路径。")
    barcodes = pd.read_csv(spec.barcodes_path, sep="\t", header=None, names=["cell_barcode"])
    barcodes["cell_barcode"] = stringify(barcodes["cell_barcode"])
    barcode_index = pd.Series(np.arange(len(barcodes), dtype=np.int64), index=barcodes["cell_barcode"])

    calls = calls.loc[calls["cell_barcode"].isin(barcode_index.index)].copy()
    if calls.empty:
        raise ValueError(f"{spec.cell_line} 没有任何 single-feature cells 能在 barcode 列表中对齐。")
    calls["matrix_col_index"] = calls["cell_barcode"].map(barcode_index).astype(int)
    calls = calls.sort_values("matrix_col_index").reset_index(drop=True)

    feature_meta = load_feature_metadata(spec.features_path)
    gene_mask = feature_meta["feature_type"].eq("Gene Expression").to_numpy()
    gene_meta = feature_meta.loc[gene_mask, ["feature_id", "feature_name"]].reset_index(drop=True)

    matrix = mmread(spec.matrix_path).tocsr()
    selected = matrix[gene_mask, :][:, calls["matrix_col_index"].to_numpy()].transpose().tocsr()
    return selected, calls, gene_meta


def load_expression_from_h5ad(
    spec: DatasetSpec,
    control_prefix: str,
    *,
    allow_degraded_unverified: bool,
) -> tuple[sparse.csr_matrix, pd.DataFrame, pd.DataFrame]:
    if spec.h5ad_path is None:
        raise ValueError(f"{spec.cell_line} 缺少 h5ad_path。")
    import anndata as ad

    adata = ad.read_h5ad(spec.h5ad_path)
    obs = adata.obs.copy()
    required_obs = {"target_gene", "is_control"}
    missing = sorted(required_obs - set(obs.columns))
    if missing:
        raise ValueError(f"{spec.cell_line} h5ad.obs 缺少列: {missing}")

    obs["target_gene"] = stringify(obs["target_gene"])
    obs["is_control"] = obs["is_control"].astype(bool)
    single_mask, single_status, single_evidence = resolve_single_perturbation_status(
        obs,
        allow_degraded_unverified=allow_degraded_unverified,
    )
    obs = obs.loc[single_mask].copy()
    if "formal_like_keep" in obs.columns:
        obs = obs.loc[obs["formal_like_keep"].astype(bool)]
    obs = obs.loc[obs["target_gene"].ne("") | obs["is_control"]]
    adata = adata[obs.index]
    obs = adata.obs.copy()
    obs["target_gene"] = stringify(obs["target_gene"])
    obs["is_control"] = obs["is_control"].astype(bool)
    if "sgRNA" in obs.columns:
        obs["feature_call"] = stringify(obs["sgRNA"])
    elif "perturbation_label_raw" in obs.columns:
        obs["feature_call"] = stringify(obs["perturbation_label_raw"])
    else:
        obs["feature_call"] = obs["target_gene"]
    if "num_features" not in obs.columns:
        obs["num_features"] = pd.Series(np.nan, index=obs.index)
    obs["num_umis"] = np.nan
    obs["is_control"] = obs["is_control"] | obs["target_gene"].map(
        lambda x: is_control_target(str(x), control_prefix)
    )
    obs["single_perturbation_filter_status"] = single_status
    obs["single_perturbation_evidence_source"] = single_evidence
    obs = obs.reset_index(drop=False).rename(columns={"index": "cell_barcode"})

    if sparse.issparse(adata.X):
        matrix = adata.X.tocsr()
    else:
        matrix = sparse.csr_matrix(np.asarray(adata.X))
    if matrix.shape[0] != len(obs):
        raise ValueError(f"{spec.cell_line} h5ad X 与 obs 行数不一致。")

    gene_meta = pd.DataFrame(
        {
            "feature_id": adata.var.index.astype(str),
            "feature_name": adata.var.index.astype(str),
        }
    ).reset_index(drop=True)
    return matrix, obs, gene_meta


def log_normalize_csr(matrix: sparse.csr_matrix, target_sum: float) -> sparse.csr_matrix:
    if matrix.shape[0] == 0:
        raise ValueError("收到空矩阵，无法做 log-normalization。")
    libsize = np.asarray(matrix.sum(axis=1)).ravel().astype(np.float64)
    if np.any(libsize <= 0):
        raise ValueError("存在 library size <= 0 的细胞，无法归一化。")
    scaling = target_sum / libsize
    normalized = matrix.multiply(scaling[:, None]).tocsr()
    normalized.data = np.log1p(normalized.data)
    return normalized


def mean_vector(matrix: sparse.csr_matrix) -> np.ndarray:
    if matrix.shape[0] == 0:
        raise ValueError("空细胞集合无法计算均值向量。")
    return np.asarray(matrix.mean(axis=0)).ravel().astype(np.float64, copy=False)


def compute_embedding(matrix: sparse.csr_matrix, n_components: int) -> np.ndarray:
    usable_components = int(min(n_components, matrix.shape[0] - 1, matrix.shape[1] - 1))
    if usable_components < 2:
        raise ValueError("细胞数或基因数不足，无法稳定计算 E-distance embedding。")
    svd = TruncatedSVD(n_components=usable_components, random_state=0)
    return svd.fit_transform(matrix)


def resolve_edistance_pairwise_max_points(metrics_cfg: dict[str, Any]) -> int | None:
    value = metrics_cfg.get("edistance_pairwise_max_points", DEFAULT_EDISTANCE_PAIRWISE_MAX_POINTS)
    if value is None:
        return None
    max_points = int(value)
    if max_points < 2:
        raise ValueError("edistance_pairwise_max_points 必须 >= 2，或设为 null 以使用精确全量距离。")
    return max_points


def subsample_rows_for_pairwise_distance(values: np.ndarray, max_points: int | None) -> np.ndarray:
    if max_points is None or values.shape[0] <= max_points:
        return values
    positions = np.linspace(0, values.shape[0] - 1, num=max_points, dtype=np.int64)
    return values[np.unique(positions)]


def mean_pairwise_distance(values: np.ndarray, max_points: int | None = None) -> float:
    if values.shape[0] <= 1:
        return 0.0
    sampled = subsample_rows_for_pairwise_distance(values, max_points)
    return float(distance.cdist(sampled, sampled, metric="euclidean").mean())


def energy_distance(
    target_values: np.ndarray,
    control_values: np.ndarray,
    control_within: float,
    *,
    max_points: int | None = None,
) -> float:
    target_sample = subsample_rows_for_pairwise_distance(target_values, max_points)
    control_sample = subsample_rows_for_pairwise_distance(control_values, max_points)
    cross_mean = float(distance.cdist(target_sample, control_sample, metric="euclidean").mean())
    target_within = mean_pairwise_distance(target_values, max_points=max_points)
    return float((2.0 * cross_mean) - target_within - control_within)


def count_deg_burden(
    delta: np.ndarray,
    control_mean: np.ndarray,
    perturbed_mean: np.ndarray,
    *,
    abs_delta_threshold: float,
    expression_floor: float,
) -> int:
    expression_mask = np.maximum(control_mean, perturbed_mean) >= expression_floor
    return int(np.count_nonzero(expression_mask & (np.abs(delta) >= abs_delta_threshold)))


def top_k_mean_abs(delta: np.ndarray, k: int) -> float:
    """Mean of the k largest absolute delta values."""
    if len(delta) == 0:
        return np.nan
    k = min(k, len(delta))
    return float(np.mean(np.sort(np.abs(delta))[-k:]))


def top_k_concentration_ratio(delta: np.ndarray, k: int) -> float:
    """Ratio of top-k abs(delta) sum to total abs(delta) sum."""
    total = np.sum(np.abs(delta))
    if total == 0:
        return np.nan
    k = min(k, len(delta))
    top_k_sum = np.sum(np.sort(np.abs(delta))[-k:])
    return float(top_k_sum / total)


def classify_join_status(effect: float | None, dependency: float | None) -> str:
    effect_ok = effect is not None and not pd.isna(effect)
    dependency_ok = dependency is not None and not pd.isna(dependency)
    if effect_ok and dependency_ok:
        return "both"
    if effect_ok:
        return "effect_only"
    if dependency_ok:
        return "dependency_only"
    return "none"


def build_bridge_records(
    spec: DatasetSpec,
    filters: dict[str, Any],
    metrics_cfg: dict[str, Any],
    normalized: sparse.csr_matrix,
    embeddings: np.ndarray,
    calls: pd.DataFrame,
    control_positions: np.ndarray,
    effect_series: pd.Series,
    dependency_series: pd.Series,
) -> pd.DataFrame:
    """在给定 control 细胞行号子集上计算 target-level truth 与 DepMap join（行号与 calls / normalized 对齐）。"""
    min_target_cells = int(filters["min_target_cells"])
    control_mask = calls["is_control"].to_numpy(dtype=bool)
    all_control = np.flatnonzero(control_mask)
    control_set = set(int(x) for x in all_control.tolist())
    pos_set = {int(x) for x in np.asarray(control_positions).ravel().tolist()}
    if not pos_set.issubset(control_set):
        raise ValueError("control_positions 必须全部为 is_control 行。")
    if len(pos_set) < int(filters["min_control_cells"]):
        raise ValueError(
            f"control 子集细胞数 {len(pos_set)} < min_control_cells={filters['min_control_cells']}"
        )

    control_positions = np.sort(np.asarray(control_positions, dtype=np.int64))
    control_matrix = normalized[control_positions]
    control_embedding = embeddings[control_positions]
    control_mean = mean_vector(control_matrix)
    edistance_pairwise_max_points = resolve_edistance_pairwise_max_points(metrics_cfg)
    control_within = mean_pairwise_distance(
        control_embedding,
        max_points=edistance_pairwise_max_points,
    )

    records: list[dict[str, Any]] = []
    for target_gene, target_calls in calls.loc[~calls["is_control"]].groupby("target_gene", sort=True):
        n_cells = int(len(target_calls))
        if n_cells < min_target_cells:
            continue

        target_index = target_calls.index.to_numpy()
        target_matrix = normalized[target_index]
        target_mean = mean_vector(target_matrix)
        delta = target_mean - control_mean
        target_embedding = embeddings[target_index]

        depmap_effect_value = effect_series.get(target_gene, np.nan)
        depmap_dependency_value = dependency_series.get(target_gene, np.nan)
        join_status = classify_join_status(depmap_effect_value, depmap_dependency_value)

        records.append(
            {
                "cell_line": spec.cell_line,
                "depmap_model_id": spec.depmap_model_id,
                "target_gene": str(target_gene),
                "n_cells_target": n_cells,
                "n_cells_control": int(len(control_positions)),
                "n_sgrnas_observed": int(target_calls["feature_call"].nunique()),
                "truth_source_cell_count": int(normalized.shape[0]),
                "gene_universe_size": int(normalized.shape[1]),
                "source_kind": spec.source_kind,
                "dataset_role": spec.dataset_role,
                "control_target_prefix": str(filters["control_target_prefix"]),
                "single_perturbation_filter_status": str(
                    target_calls["single_perturbation_filter_status"].iloc[0]
                ),
                "single_perturbation_evidence_source": str(
                    target_calls["single_perturbation_evidence_source"].iloc[0]
                ),
                "real_shift_L2": float(np.linalg.norm(delta)),
                "real_shift_mean_abs": float(np.abs(delta).mean()),
                "real_shift_top20_mean": top_k_mean_abs(delta, 20),
                "real_shift_top50_mean": top_k_mean_abs(delta, 50),
                "real_shift_top100_mean": top_k_mean_abs(delta, 100),
                "real_shift_top50_concentration": top_k_concentration_ratio(delta, 50),
                "real_Edistance": energy_distance(
                    target_embedding,
                    control_embedding,
                    control_within,
                    max_points=edistance_pairwise_max_points,
                ),
                "real_DEG_burden": count_deg_burden(
                    delta,
                    control_mean,
                    target_mean,
                    abs_delta_threshold=float(metrics_cfg["deg_abs_log1p_delta_threshold"]),
                    expression_floor=float(metrics_cfg["deg_expression_floor"]),
                ),
                "depmap_gene_effect": float(depmap_effect_value) if not pd.isna(depmap_effect_value) else np.nan,
                "depmap_gene_dependency": float(depmap_dependency_value)
                if not pd.isna(depmap_dependency_value)
                else np.nan,
                "depmap_effect_found": bool(not pd.isna(depmap_effect_value)),
                "depmap_dependency_found": bool(not pd.isna(depmap_dependency_value)),
                "depmap_join_status": join_status,
            }
        )

    bridge_table = pd.DataFrame(records).sort_values(["cell_line", "target_gene"]).reset_index(drop=True)
    if bridge_table.empty:
        raise ValueError(f"{spec.cell_line} 没有任何 target 满足最小细胞数阈值。")
    if bridge_table.duplicated(["cell_line", "target_gene"]).any():
        raise ValueError(f"{spec.cell_line} bridge table 出现重复主键。")
    return bridge_table


def prepare_bridge_inputs(
    spec: DatasetSpec,
    config: dict[str, Any],
    depmap_effect: pd.DataFrame,
    depmap_dependency: pd.DataFrame,
) -> tuple[sparse.csr_matrix, np.ndarray, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """加载表达、log-normalize、SVD embedding，并解析 DepMap 行向量。"""
    filters = config["filters"]
    metrics_cfg = config["metrics"]
    if spec.source_kind == "mtx_protospacer":
        calls = load_single_feature_calls(spec, control_prefix=str(filters["control_target_prefix"]))
        expression, calls, gene_meta = load_expression_for_called_cells(spec, calls)
        calls["single_perturbation_filter_status"] = "verified_via_num_features_eq_1"
        calls["single_perturbation_evidence_source"] = "num_features"
    elif spec.source_kind == "h5ad_obs":
        expression, calls, gene_meta = load_expression_from_h5ad(
            spec,
            control_prefix=str(filters["control_target_prefix"]),
            allow_degraded_unverified=bool(
                filters.get("allow_degraded_unverified_single_perturbation", False)
            ),
        )
    else:
        raise ValueError(f"不支持的 source_kind: {spec.source_kind}")

    min_control_cells = int(filters["min_control_cells"])

    normalized = log_normalize_csr(expression, target_sum=float(metrics_cfg["normalization_target_sum"]))
    embeddings = compute_embedding(normalized, n_components=int(metrics_cfg["edistance_n_components"]))

    control_mask = calls["is_control"].to_numpy(dtype=bool)
    if int(control_mask.sum()) < min_control_cells:
        raise ValueError(
            f"{spec.cell_line} control cells 不足: {int(control_mask.sum())} < {min_control_cells}"
        )

    effect_row = depmap_effect.loc[
        depmap_effect["depmap_model_id"].astype("string").eq(spec.depmap_model_id)
    ]
    dependency_row = depmap_dependency.loc[
        depmap_dependency["depmap_model_id"].astype("string").eq(spec.depmap_model_id)
    ]
    if effect_row.empty or dependency_row.empty:
        raise ValueError(f"{spec.cell_line} 在 DepMap 中找不到 model_id={spec.depmap_model_id}。")
    effect_series = effect_row.iloc[0]
    dependency_series = dependency_row.iloc[0]

    return normalized, embeddings, calls, gene_meta, effect_series, dependency_series


def build_bridge_table_for_dataset(
    spec: DatasetSpec,
    config: dict[str, Any],
    depmap_effect: pd.DataFrame,
    depmap_dependency: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    filters = config["filters"]
    metrics_cfg = config["metrics"]
    min_target_cells = int(filters["min_target_cells"])
    min_control_cells = int(filters["min_control_cells"])
    normalized, embeddings, calls, gene_meta, effect_series, dependency_series = prepare_bridge_inputs(
        spec, config, depmap_effect, depmap_dependency
    )

    control_mask = calls["is_control"].to_numpy(dtype=bool)
    control_positions = np.flatnonzero(control_mask)
    bridge_table = build_bridge_records(
        spec=spec,
        filters=filters,
        metrics_cfg=metrics_cfg,
        normalized=normalized,
        embeddings=embeddings,
        calls=calls,
        control_positions=control_positions,
        effect_series=effect_series,
        dependency_series=dependency_series,
    )
    edistance_pairwise_max_points = resolve_edistance_pairwise_max_points(metrics_cfg)

    audit = pd.DataFrame(
        [
            {
                "cell_line": spec.cell_line,
                "depmap_model_id": spec.depmap_model_id,
                "n_cells_with_single_feature": int(len(calls)),
                "n_control_cells": int(control_mask.sum()),
                "n_targets_in_bridge_table": int(len(bridge_table)),
                "n_targets_with_both_depmap": int(bridge_table["depmap_join_status"].eq("both").sum()),
                "depmap_both_join_rate": float(bridge_table["depmap_join_status"].eq("both").mean()),
                "source_kind": spec.source_kind,
                "dataset_role": spec.dataset_role,
                "min_target_cells_threshold": min_target_cells,
                "min_control_cells_threshold": min_control_cells,
                "single_perturbation_filter_status": str(
                    calls["single_perturbation_filter_status"].iloc[0]
                ),
                "single_perturbation_evidence_source": str(
                    calls["single_perturbation_evidence_source"].iloc[0]
                ),
                "deg_abs_log1p_delta_threshold": float(metrics_cfg["deg_abs_log1p_delta_threshold"]),
                "deg_expression_floor": float(metrics_cfg["deg_expression_floor"]),
                "edistance_n_components": int(metrics_cfg["edistance_n_components"]),
                "edistance_pairwise_max_points": edistance_pairwise_max_points
                if edistance_pairwise_max_points is not None
                else "exact_full_pairwise",
                "n_gene_features": int(len(gene_meta)),
            }
        ]
    )
    return bridge_table, audit


def safe_corr(values_x: pd.Series, values_y: pd.Series, fn) -> tuple[float, float]:
    if len(values_x) < 3 or values_x.nunique() < 2 or values_y.nunique() < 2:
        return np.nan, np.nan
    rho, pvalue = fn(values_x, values_y)
    return float(rho), float(pvalue)


def summarize_correlations(bridge_table: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for truth_metric in TRUTH_METRIC_COLUMNS:
        if truth_metric not in bridge_table.columns:
            continue
        for endpoint in DEPMAP_ENDPOINT_COLUMNS:
            if endpoint not in bridge_table.columns:
                continue
            subset = bridge_table.loc[:, ["target_gene", truth_metric, endpoint]].dropna()
            spearman_rho, spearman_p = safe_corr(subset[truth_metric], subset[endpoint], spearmanr)
            pearson_rho, pearson_p = safe_corr(subset[truth_metric], subset[endpoint], pearsonr)
            direction = float(DEPMAP_ALIGNMENT_DIRECTION[endpoint])
            rows.append(
                {
                    "cell_line": bridge_table["cell_line"].iloc[0],
                    "truth_metric": truth_metric,
                    "depmap_endpoint": endpoint,
                    "n_targets": int(len(subset)),
                    "spearman_rho_raw": spearman_rho,
                    "spearman_pvalue": spearman_p,
                    "pearson_r_raw": pearson_rho,
                    "pearson_pvalue": pearson_p,
                    "spearman_rho_aligned": float(direction * spearman_rho)
                    if not pd.isna(spearman_rho)
                    else np.nan,
                    "pearson_r_aligned": float(direction * pearson_rho)
                    if not pd.isna(pearson_rho)
                    else np.nan,
                    "alignment_note": (
                        "depmap_gene_effect: aligned>0 表示 truth metric 越高，gene effect 越负；"
                        "depmap_gene_dependency: aligned>0 表示 truth metric 越高，gene dependency 越高"
                    ),
                }
            )
    return pd.DataFrame(rows)


def assign_quantile_groups(values: pd.Series, q_low: float, q_high: float) -> pd.Series:
    low_cut = float(values.quantile(q_low))
    high_cut = float(values.quantile(q_high))
    groups = pd.Series("mid", index=values.index, dtype="string")
    groups.loc[values <= low_cut] = "low"
    groups.loc[values >= high_cut] = "high"
    return groups


def summarize_group_comparisons(bridge_table: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_cfg = config["group_comparison"]
    for truth_metric in TRUTH_METRIC_COLUMNS:
        if truth_metric not in bridge_table.columns:
            continue
        groups = assign_quantile_groups(
            bridge_table[truth_metric],
            q_low=float(group_cfg["quantile_low"]),
            q_high=float(group_cfg["quantile_high"]),
        )
        for endpoint in DEPMAP_ENDPOINT_COLUMNS:
            if endpoint not in bridge_table.columns:
                continue
            subset = bridge_table.loc[:, [truth_metric, endpoint]].copy()
            subset["truth_group"] = groups
            subset = subset.loc[subset["truth_group"].isin(["low", "high"])].dropna()
            low_values = subset.loc[subset["truth_group"].eq("low"), endpoint]
            high_values = subset.loc[subset["truth_group"].eq("high"), endpoint]
            if min(len(low_values), len(high_values)) < int(group_cfg["min_group_size"]):
                statistic = np.nan
                pvalue = np.nan
            else:
                statistic, pvalue = mannwhitneyu(
                    high_values.to_numpy(),
                    low_values.to_numpy(),
                    alternative="two-sided",
                )
            high_median = float(high_values.median()) if not high_values.empty else np.nan
            low_median = float(low_values.median()) if not low_values.empty else np.nan
            direction = float(DEPMAP_ALIGNMENT_DIRECTION[endpoint])
            rows.append(
                {
                    "cell_line": bridge_table["cell_line"].iloc[0],
                    "truth_metric": truth_metric,
                    "depmap_endpoint": endpoint,
                    "n_high": int(len(high_values)),
                    "n_low": int(len(low_values)),
                    "high_group_median_raw": high_median,
                    "low_group_median_raw": low_median,
                    "high_minus_low_raw": high_median - low_median
                    if not (pd.isna(high_median) or pd.isna(low_median))
                    else np.nan,
                    "aligned_effect_direction": direction * (high_median - low_median)
                    if not (pd.isna(high_median) or pd.isna(low_median))
                    else np.nan,
                    "mannwhitney_u": float(statistic) if not pd.isna(statistic) else np.nan,
                    "pvalue": float(pvalue) if not pd.isna(pvalue) else np.nan,
                    "alignment_note": (
                        "aligned_effect_direction>0 表示 high truth 组更符合桥接方向；"
                        "gene effect 为更负，gene dependency 为更高"
                    ),
                }
            )
    return pd.DataFrame(rows)


def centered_sign(values: pd.Series) -> pd.Series:
    centered = values - values.median()
    signs = np.sign(centered).astype(int)
    return pd.Series(signs, index=values.index)


def build_cross_cell_line_outputs(bridge_tables: list[pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """逐对 cell line 做 inner join（target_gene）与相关；三数据集时为 C(3,2)=3 对，互不混在一个宽表里。"""
    if len(bridge_tables) < 2:
        raise ValueError("跨 cell line 一致性分析至少需要两个数据集。")

    variables = [*TRUTH_METRIC_COLUMNS, *DEPMAP_ENDPOINT_COLUMNS]
    summary_rows: list[dict[str, Any]] = []
    shared_parts: list[pd.DataFrame] = []

    for i in range(len(bridge_tables)):
        for j in range(i + 1, len(bridge_tables)):
            left = bridge_tables[i]
            right = bridge_tables[j]
            left_name = str(left["cell_line"].iloc[0])
            right_name = str(right["cell_line"].iloc[0])
            merged = left.merge(
                right,
                on="target_gene",
                how="inner",
                suffixes=(f"_{left_name}", f"_{right_name}"),
            )
            pair_label = " vs ".join(sorted([left_name, right_name]))

            if merged.empty:
                for variable in variables:
                    summary_rows.append(
                        {
                            "cell_line_pair": pair_label,
                            "variable": variable,
                            "n_shared_targets": 0,
                            "pearson_r": np.nan,
                            "pearson_pvalue": np.nan,
                            "spearman_rho": np.nan,
                            "spearman_pvalue": np.nan,
                            "centered_sign_concordance": np.nan,
                        }
                    )
                continue

            for variable in variables:
                lc = f"{variable}_{left_name}"
                rc = f"{variable}_{right_name}"
                if lc not in merged.columns or rc not in merged.columns:
                    summary_rows.append(
                        {
                            "cell_line_pair": pair_label,
                            "variable": variable,
                            "n_shared_targets": 0,
                            "pearson_r": np.nan,
                            "pearson_pvalue": np.nan,
                            "spearman_rho": np.nan,
                            "spearman_pvalue": np.nan,
                            "centered_sign_concordance": np.nan,
                        }
                    )
                    continue
                subset = pd.DataFrame({"left": merged[lc], "right": merged[rc]}).dropna()
                if subset.empty:
                    summary_rows.append(
                        {
                            "cell_line_pair": pair_label,
                            "variable": variable,
                            "n_shared_targets": 0,
                            "pearson_r": np.nan,
                            "pearson_pvalue": np.nan,
                            "spearman_rho": np.nan,
                            "spearman_pvalue": np.nan,
                            "centered_sign_concordance": np.nan,
                        }
                    )
                    continue
                pearson_r, pearson_p = safe_corr(subset["left"], subset["right"], pearsonr)
                spearman_rho, spearman_p = safe_corr(subset["left"], subset["right"], spearmanr)
                concordance = (
                    centered_sign(subset["left"]).eq(centered_sign(subset["right"])).mean()
                    if len(subset) > 0
                    else np.nan
                )
                summary_rows.append(
                    {
                        "cell_line_pair": pair_label,
                        "variable": variable,
                        "n_shared_targets": int(len(subset)),
                        "pearson_r": pearson_r,
                        "pearson_pvalue": pearson_p,
                        "spearman_rho": spearman_rho,
                        "spearman_pvalue": spearman_p,
                        "centered_sign_concordance": float(concordance),
                    }
                )

            shared_rows: list[dict[str, Any]] = []
            for _, row in merged.iterrows():
                record: dict[str, Any] = {"target_gene": row["target_gene"]}
                for variable in variables:
                    lc = f"{variable}_{left_name}"
                    rc = f"{variable}_{right_name}"
                    if lc not in merged.columns or rc not in merged.columns:
                        continue
                    left_value = row[lc]
                    right_value = row[rc]
                    record[f"{variable}_{left_name}"] = left_value
                    record[f"{variable}_{right_name}"] = right_value
                    if not (pd.isna(left_value) or pd.isna(right_value)):
                        record[f"{variable}_abs_diff"] = float(abs(left_value - right_value))
                    else:
                        record[f"{variable}_abs_diff"] = np.nan
                shared_rows.append(record)
            part_df = pd.DataFrame(shared_rows)
            if len(bridge_tables) > 2:
                part_df.insert(0, "cell_line_pair", pair_label)
            shared_parts.append(part_df)

    summary_df = pd.DataFrame(summary_rows)
    if not shared_parts:
        return pd.DataFrame(), summary_df
    if len(bridge_tables) == 2:
        return shared_parts[0], summary_df
    return pd.concat(shared_parts, ignore_index=True), summary_df


def metric_rows_for_tier(correlation: pd.DataFrame, tier: str) -> pd.DataFrame:
    allowed_metrics = [metric for metric, metric_tier in METRIC_TIERS.items() if metric_tier == tier]
    return correlation.loc[correlation["truth_metric"].isin(allowed_metrics)].sort_values(
        ["depmap_endpoint", "spearman_rho_aligned"],
        ascending=[True, False],
    )


def select_summary_rows(correlation: pd.DataFrame, tiers: list[str]) -> pd.DataFrame:
    parts = [metric_rows_for_tier(correlation, tier) for tier in tiers]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def write_markdown_report(
    report_path: Path,
    per_line_audits: pd.DataFrame,
    correlation_summaries: list[pd.DataFrame],
    group_summaries: list[pd.DataFrame],
    cross_summary: pd.DataFrame,
) -> None:
    summary_by_cell_line = {
        frame["cell_line"].iloc[0]: frame.sort_values("spearman_rho_aligned", ascending=False)
        for frame in correlation_summaries
    }
    group_by_cell_line = {
        frame["cell_line"].iloc[0]: frame.sort_values("aligned_effect_direction", ascending=False)
        for frame in group_summaries
    }
    roles = (
        per_line_audits.loc[:, ["cell_line", "dataset_role"]]
        .drop_duplicates()
        .set_index("cell_line")["dataset_role"]
        .to_dict()
    )

    lines = [
        "# Stage 2 Truth-Driven Bridge v1",
        "",
        "## 摘要",
        "",
        "- 本报告只覆盖 truth-side bridge，不包含任何 entrant predicted shift。",
        "- `DepMap gene effect` 与 `gene dependency` 并列输出；主报告严格按 dataset role 与 evidence tier 分层。",
        "- 主结论只允许 primary datasets 的 primary truth metrics；supplementary datasets 与非 primary metrics 不进入主结论。",
    ]
    primary_datasets = [name for name, role in roles.items() if role == "primary"]
    if primary_datasets:
        lines.extend(
            [
                "",
                "## 主结论",
                "",
            ]
        )
    for cell_line in primary_datasets:
        correlation = summary_by_cell_line[cell_line]
        best = select_summary_rows(correlation, ["primary"])
        lines.append(f"### {cell_line}")
        audit_row = per_line_audits.loc[per_line_audits["cell_line"].eq(cell_line)].iloc[0]
        lines.append(
            f"- single-feature cells: `{int(audit_row['n_cells_with_single_feature'])}`；control cells: `{int(audit_row['n_control_cells'])}`；可分析 targets: `{int(audit_row['n_targets_in_bridge_table'])}`。"
        )
        lines.append(
            f"- DepMap 双端点同时 join 成功率：`{audit_row['depmap_both_join_rate']:.1%}`。"
        )
        lines.append(
            f"- 单扰动判定：`{audit_row['single_perturbation_filter_status']}`（evidence=`{audit_row['single_perturbation_evidence_source']}`）。"
        )
        for row in best.itertuples(index=False):
            lines.append(
                f"- `{row.truth_metric}` vs `{row.depmap_endpoint}` 的 aligned Spearman = `{row.spearman_rho_aligned:.3f}`（n=`{row.n_targets}`）。"
            )
        lines.append("")

    if primary_datasets:
        lines.extend(
            [
                "## 补充证据",
                "",
            ]
        )
    for cell_line in primary_datasets:
        correlation = summary_by_cell_line[cell_line]
        supplementary = select_summary_rows(correlation, ["supplementary", "auxiliary"])
        lines.append(f"### {cell_line}")
        if supplementary.empty:
            lines.append("- 无 supplementary / auxiliary 指标可报告。")
        for row in supplementary.itertuples(index=False):
            lines.append(
                f"- `{row.truth_metric}`（{METRIC_TIERS[row.truth_metric]}）vs `{row.depmap_endpoint}` 的 aligned Spearman = `{row.spearman_rho_aligned:.3f}`（n=`{row.n_targets}`）。"
            )
        lines.append("")

    if primary_datasets:
        lines.extend(
            [
                "## 分组比较",
                "",
            ]
        )
    for cell_line in primary_datasets:
        group_summary = group_by_cell_line[cell_line]
        best = group_summary.loc[
            group_summary["truth_metric"].isin(
                ["real_shift_L2", "real_shift_mean_abs", "real_Edistance", "real_DEG_burden"]
            )
        ]
        lines.append(f"### {cell_line}")
        for row in best.itertuples(index=False):
            lines.append(
                f"- `{row.truth_metric}` 分层后，`{row.depmap_endpoint}` 的 aligned_effect_direction = `{row.aligned_effect_direction:.3f}`（high=`{row.n_high}`，low=`{row.n_low}`）。"
            )
        lines.append("")

    supplementary_datasets = [name for name, role in roles.items() if role == "supplementary"]
    if supplementary_datasets:
        lines.extend(
            [
                "## 外部补充复现",
                "",
            ]
        )
        for cell_line in supplementary_datasets:
            correlation = summary_by_cell_line[cell_line]
            audit_row = per_line_audits.loc[per_line_audits["cell_line"].eq(cell_line)].iloc[0]
            best = select_summary_rows(correlation, ["primary", "supplementary", "auxiliary"]).head(4)
            lines.append(f"### {cell_line}")
            lines.append(
                f"- dataset role: `{audit_row['dataset_role']}`；single-feature cells: `{int(audit_row['n_cells_with_single_feature'])}`；control cells: `{int(audit_row['n_control_cells'])}`；可分析 targets: `{int(audit_row['n_targets_in_bridge_table'])}`。"
            )
            lines.append(
                f"- 单扰动判定：`{audit_row['single_perturbation_filter_status']}`（evidence=`{audit_row['single_perturbation_evidence_source']}`）。"
            )
            for row in best.itertuples(index=False):
                lines.append(
                    f"- `{row.truth_metric}`（{METRIC_TIERS[row.truth_metric]}）vs `{row.depmap_endpoint}` 的 aligned Spearman = `{row.spearman_rho_aligned:.3f}`（n=`{row.n_targets}`）。"
                )
            lines.append("")

    lines.extend(
        [
            "## 跨 Cell Line 一致性",
            "",
        ]
    )
    if cross_summary.empty:
        lines.append("- 本配置仅含单个 cell line / 数据集，未计算跨 cell line 一致性。")
    else:
        allowed_cross = [*DEPMAP_ENDPOINT_COLUMNS, "real_shift_L2", "real_shift_mean_abs", "real_Edistance", "real_DEG_burden"]
        top_cross = cross_summary.loc[cross_summary["variable"].isin(allowed_cross)].sort_values(
            "spearman_rho",
            ascending=False,
            na_position="last",
        )
        for row in top_cross.itertuples(index=False):
            n_shared = int(row.n_shared_targets) if not pd.isna(row.n_shared_targets) else 0
            if n_shared < 3:
                lines.append(
                    f"- `{row.variable}` 在 `{row.cell_line_pair}` 上：两线 **inner join 共享 target** 仅 `{n_shared}` 个，不足以报告稳定 Spearman（靶基因重叠极少属预期）。"
                )
                continue
            lines.append(
                f"- `{row.variable}` 在 `{row.cell_line_pair}` 上的 Spearman = `{row.spearman_rho:.3f}`，centered sign concordance = `{row.centered_sign_concordance:.3f}`。"
            )

    lines.extend(
        [
            "",
            "## 附录",
            "",
            "- `aligned` 方向按 endpoint 区分：`gene effect` 为更负，`gene dependency` 为更高。",
            "- `real_DEG_burden` 在 v1 中按 `abs(log1p-normalized delta) >= threshold` 且表达达到 floor 的基因数定义。",
            "- `real_Edistance` 在 v1 中基于同 cell line 单扰动细胞的 log-normalized expression SVD embedding 计算。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def run_from_config(config_path: Path) -> dict[str, Path]:
    config = load_config(config_path)
    specs = build_dataset_specs(config)

    depmap_effect = load_depmap_endpoint(resolve_path(config["depmap"]["gene_effect_path"]))
    depmap_dependency = load_depmap_endpoint(resolve_path(config["depmap"]["gene_dependency_path"]))

    output_cfg = config["output"]
    data_root = resolve_path(output_cfg["data_root"])
    report_root = resolve_path(output_cfg["report_root"])
    data_root.mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)

    bridge_tables: list[pd.DataFrame] = []
    audit_tables: list[pd.DataFrame] = []
    correlation_tables: list[pd.DataFrame] = []
    group_tables: list[pd.DataFrame] = []

    for spec in specs:
        bridge_table, audit = build_bridge_table_for_dataset(
            spec=spec,
            config=config,
            depmap_effect=depmap_effect,
            depmap_dependency=depmap_dependency,
        )
        correlations = summarize_correlations(bridge_table)
        groups = summarize_group_comparisons(bridge_table, config=config)

        cell_data_dir = data_root / spec.cell_line
        cell_report_dir = report_root / spec.cell_line
        cell_data_dir.mkdir(parents=True, exist_ok=True)
        cell_report_dir.mkdir(parents=True, exist_ok=True)

        bridge_table.to_csv(cell_data_dir / "target_level_bridge_table.tsv.gz", sep="\t", index=False)
        audit.to_csv(cell_report_dir / "bridge_audit.tsv", sep="\t", index=False)
        correlations.to_csv(cell_report_dir / "correlation_summary.tsv", sep="\t", index=False)
        groups.to_csv(cell_report_dir / "group_comparison_summary.tsv", sep="\t", index=False)

        bridge_tables.append(bridge_table)
        audit_tables.append(audit)
        correlation_tables.append(correlations)
        group_tables.append(groups)

    combined_bridge = pd.concat(bridge_tables, ignore_index=True)
    combined_audit = pd.concat(audit_tables, ignore_index=True)
    combined_bridge.to_csv(data_root / "combined_target_level_bridge_table.tsv.gz", sep="\t", index=False)
    combined_audit.to_csv(report_root / "combined_bridge_audit.tsv", sep="\t", index=False)

    if len(bridge_tables) >= 2:
        shared_targets, cross_summary = build_cross_cell_line_outputs(bridge_tables)
    else:
        shared_targets = pd.DataFrame()
        cross_summary = pd.DataFrame(
            columns=[
                "cell_line_pair",
                "variable",
                "n_shared_targets",
                "pearson_r",
                "pearson_pvalue",
                "spearman_rho",
                "spearman_pvalue",
                "centered_sign_concordance",
            ]
        )
    shared_targets.to_csv(report_root / "cross_cell_line_shared_targets.tsv", sep="\t", index=False)
    cross_summary.to_csv(report_root / "cross_cell_line_consistency_summary.tsv", sep="\t", index=False)

    report_path = report_root / "stage2_truth_driven_bridge_report.md"
    write_markdown_report(
        report_path=report_path,
        per_line_audits=combined_audit,
        correlation_summaries=correlation_tables,
        group_summaries=group_tables,
        cross_summary=cross_summary,
    )

    return {
        "combined_bridge_table": data_root / "combined_target_level_bridge_table.tsv.gz",
        "combined_audit": report_root / "combined_bridge_audit.tsv",
        "cross_summary": report_root / "cross_cell_line_consistency_summary.tsv",
        "report": report_path,
    }


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="构建 Stage 2 truth-driven bridge 主线产物。")
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs/truth_driven_bridge_hcc38_hcc1143_v1.json",
        help="Stage 2 truth-driven bridge 配置 JSON 路径。",
    )
    return parser


def main() -> None:
    args = build_argparser().parse_args()
    outputs = run_from_config(args.config)
    print("Stage 2 truth-driven bridge 完成。")
    for key, value in outputs.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
