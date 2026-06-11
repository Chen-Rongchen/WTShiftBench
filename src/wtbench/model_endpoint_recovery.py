from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from wtbench.model_structure_scorer import (
    DEFAULT_AXIS_MEMBERSHIP_PATH,
    DEFAULT_TRUTH_CONTRACT_PATH,
    load_prediction_matrix,
    load_tsv,
    project_prediction_to_axes,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PREDICTION_ROOT = PROJECT_ROOT / "data/predictions/hcc_scorer_ready"
DEFAULT_MANIFEST_ROOT = PROJECT_ROOT / "reports/hcc_prediction_contract"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "reports/model_endpoint_recovery"
CELL_LINES = ("HCC38", "HCC1143")
GEARS_FORMAL_MODEL_ID = "gears_hcc_formal_v1"
GEARS_SWEEP_PREFIX = "gears_hcc_formal_v1_"


@dataclass(frozen=True)
class EndpointThresholds:
    shift_low: float
    shift_high: float
    dependency_low: float
    dependency_high: float


def _safe_spearman(left: pd.Series, right: pd.Series) -> tuple[float, float]:
    frame = pd.concat([left, right], axis=1).dropna()
    if len(frame) < 3:
        return float("nan"), float("nan")
    if frame.iloc[:, 0].nunique(dropna=True) <= 1 or frame.iloc[:, 1].nunique(dropna=True) <= 1:
        return float("nan"), float("nan")
    try:
        from scipy import stats

        result = stats.spearmanr(frame.iloc[:, 0], frame.iloc[:, 1])
        return float(result.statistic), float(result.pvalue)
    except Exception:
        return float(frame.iloc[:, 0].corr(frame.iloc[:, 1], method="spearman")), float("nan")


def _spearman_with_status(left: pd.Series, right: pd.Series) -> tuple[float, float, str, int, int]:
    frame = pd.concat([left, right], axis=1).dropna()
    left_unique = int(frame.iloc[:, 0].nunique(dropna=True)) if not frame.empty else 0
    right_unique = int(frame.iloc[:, 1].nunique(dropna=True)) if not frame.empty else 0
    if len(frame) < 3:
        return float("nan"), float("nan"), "non_estimable_too_few_pairs", left_unique, right_unique
    if left_unique <= 1:
        return float("nan"), float("nan"), "non_estimable_constant_score", left_unique, right_unique
    if right_unique <= 1:
        return float("nan"), float("nan"), "non_estimable_constant_endpoint", left_unique, right_unique
    rho, pvalue = _safe_spearman(left, right)
    if pd.isna(rho):
        return rho, pvalue, "non_estimable_unknown", left_unique, right_unique
    return rho, pvalue, "estimated", left_unique, right_unique


def _bh_qvalues(pvalues: pd.Series) -> pd.Series:
    values = pd.to_numeric(pvalues, errors="coerce")
    qvalues = pd.Series(np.nan, index=values.index, dtype=float)
    valid = values.dropna()
    if valid.empty:
        return qvalues
    order = valid.sort_values().index
    ranked = valid.loc[order].to_numpy(dtype=float)
    n = float(len(ranked))
    adjusted = ranked * n / np.arange(1, len(ranked) + 1, dtype=float)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    qvalues.loc[order] = np.clip(adjusted, 0.0, 1.0)
    return qvalues


def _rank_auc(score: pd.Series, label: pd.Series) -> float:
    frame = pd.concat([score.rename("score"), label.rename("label")], axis=1).dropna()
    positives = frame.loc[frame["label"].astype(bool), "score"]
    negatives = frame.loc[~frame["label"].astype(bool), "score"]
    if positives.empty or negatives.empty:
        return float("nan")
    comparisons = (positives.to_numpy()[:, None] > negatives.to_numpy()[None, :]).mean()
    ties = (positives.to_numpy()[:, None] == negatives.to_numpy()[None, :]).mean()
    return float(comparisons + 0.5 * ties)


def _endpoint_thresholds(truth: pd.DataFrame) -> EndpointThresholds:
    return EndpointThresholds(
        shift_low=float(truth["observed_shift_mean_abs"].quantile(1.0 / 3.0)),
        shift_high=float(truth["observed_shift_mean_abs"].quantile(2.0 / 3.0)),
        dependency_low=float(truth["dependency_strength"].quantile(1.0 / 3.0)),
        dependency_high=float(truth["dependency_strength"].quantile(2.0 / 3.0)),
    )


def _assign_endpoint_category(row: pd.Series, thresholds: EndpointThresholds) -> str:
    high_shift = row["observed_shift_mean_abs"] >= thresholds.shift_high
    low_shift = row["observed_shift_mean_abs"] <= thresholds.shift_low
    high_dep = row["dependency_strength"] >= thresholds.dependency_high
    low_dep = row["dependency_strength"] <= thresholds.dependency_low
    if high_shift and high_dep:
        return "Q1_anchor"
    if high_shift and not high_dep:
        return "shift_excess"
    if high_dep and not high_shift:
        return "dependency_excess"
    if low_shift and low_dep:
        return "low_information"
    return "middle"


def load_truth_endpoint_table(cell_line: str) -> tuple[pd.DataFrame, EndpointThresholds]:
    path = PROJECT_ROOT / f"reports/truth_driven_bridge/residual_quadrant_analysis/{cell_line}_residual_quadrant.tsv"
    if not path.exists():
        path = PROJECT_ROOT / f"reports/truth_driven_bridge/{cell_line}/bridge_audit.tsv"
    truth = pd.read_csv(path, sep="\t")
    required = {"target_gene", "real_shift_mean_abs", "real_shift_L2", "depmap_gene_effect"}
    missing = sorted(required - set(truth.columns))
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    truth = truth.loc[truth["depmap_gene_effect"].notna()].copy()
    truth["target_gene"] = truth["target_gene"].astype(str)
    truth["observed_shift_mean_abs"] = truth["real_shift_mean_abs"].astype(float)
    truth["observed_shift_l2"] = truth["real_shift_L2"].astype(float)
    truth["dependency_strength"] = -truth["depmap_gene_effect"].astype(float)
    thresholds = _endpoint_thresholds(truth)
    truth["endpoint_category"] = truth.apply(_assign_endpoint_category, axis=1, thresholds=thresholds)
    columns = [
        "target_gene",
        "observed_shift_mean_abs",
        "observed_shift_l2",
        "depmap_gene_effect",
        "dependency_strength",
        "endpoint_category",
    ]
    optional = [column for column in ["depmap_gene_dependency", "residual", "quadrant"] if column in truth.columns]
    return truth.loc[:, columns + optional], thresholds


def _load_manifest_role(model_id: str, cell_line: str, manifest_root: Path) -> str:
    path = manifest_root / model_id / cell_line / "prediction_manifest.json"
    if not path.exists():
        return "unknown"
    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
        return str(payload.get("object_role", "unknown"))
    except Exception:
        return "unknown"


def discover_model_ids(prediction_root: Path = DEFAULT_PREDICTION_ROOT) -> list[str]:
    if not prediction_root.exists():
        return []
    model_ids = []
    for path in sorted(prediction_root.iterdir()):
        if not path.is_dir():
            continue
        if any((path / cell_line / "predicted_shift.tsv.gz").exists() for cell_line in CELL_LINES):
            model_ids.append(path.name)
    return model_ids


def _axis_entropy(values: pd.Series) -> float:
    clean = values.dropna().astype(float)
    clean = clean.loc[clean > 0.0]
    total = float(clean.sum())
    if clean.empty or total <= 0.0 or len(clean) <= 1:
        return float("nan")
    probabilities = clean / total
    entropy = -float((probabilities * np.log(probabilities)).sum())
    return entropy / float(np.log(len(probabilities)))


def _mean_pairwise_axis_cosine(axis_matrix: pd.DataFrame) -> float:
    if axis_matrix.shape[0] < 2:
        return float("nan")
    values = axis_matrix.to_numpy(dtype=float)
    norms = np.linalg.norm(values, axis=1)
    valid = norms > 0.0
    values = values[valid]
    norms = norms[valid]
    if values.shape[0] < 2:
        return float("nan")
    normalized = values / norms[:, None]
    cosine = normalized @ normalized.T
    upper = cosine[np.triu_indices(cosine.shape[0], k=1)]
    return float(np.mean(upper))


def _output_geometry_diagnostics(matrix: pd.DataFrame) -> dict[str, float]:
    """Axis-free diagnostics of target-output homogenization.

    Rows are target-level predicted shift vectors. The diagnostics describe
    geometric concentration only; they are not biological pathway scores.
    """
    values = matrix.to_numpy(dtype=float)
    if values.ndim != 2 or min(values.shape) < 2 or not np.isfinite(values).all():
        return {
            "predicted_target_similarity_mean": float("nan"),
            "leading_singular_energy_share": float("nan"),
            "normalized_inverse_effective_rank": float("nan"),
            "output_homogenization_score": float("nan"),
        }
    row_norms = np.linalg.norm(values, axis=1)
    valid_rows = row_norms > 0.0
    if int(valid_rows.sum()) < 2:
        return {
            "predicted_target_similarity_mean": float("nan"),
            "leading_singular_energy_share": float("nan"),
            "normalized_inverse_effective_rank": float("nan"),
            "output_homogenization_score": float("nan"),
        }
    valid_values = values[valid_rows]
    normalized = valid_values / np.linalg.norm(valid_values, axis=1)[:, None]
    cosine = normalized @ normalized.T
    upper = cosine[np.triu_indices(cosine.shape[0], k=1)]
    mean_similarity = float(np.mean(upper))

    singular_values = np.linalg.svd(valid_values, compute_uv=False)
    energy = np.square(singular_values)
    total_energy = float(energy.sum())
    if total_energy <= 0.0:
        leading_share = float("nan")
        inverse_effective_rank = float("nan")
    else:
        probabilities = energy / total_energy
        positive = probabilities[probabilities > 0.0]
        effective_rank = float(np.exp(-np.sum(positive * np.log(positive))))
        max_rank = float(min(valid_values.shape))
        leading_share = float(probabilities[0])
        inverse_effective_rank = (
            float((max_rank - effective_rank) / (max_rank - 1.0))
            if max_rank > 1.0
            else float("nan")
        )

    similarity_component = float(np.clip((mean_similarity + 1.0) / 2.0, 0.0, 1.0))
    components = np.asarray(
        [similarity_component, leading_share, inverse_effective_rank],
        dtype=float,
    )
    homogenization = float(np.nanmean(components)) if np.isfinite(components).any() else float("nan")
    return {
        "predicted_target_similarity_mean": mean_similarity,
        "leading_singular_energy_share": leading_share,
        "normalized_inverse_effective_rank": inverse_effective_rank,
        "output_homogenization_score": homogenization,
    }


def _cosine_similarity_matrix(matrix: pd.DataFrame) -> pd.DataFrame:
    values = matrix.to_numpy(dtype=float)
    norms = np.linalg.norm(values, axis=1)
    normalized = np.zeros_like(values, dtype=float)
    valid = norms > 0.0
    normalized[valid] = values[valid] / norms[valid, None]
    cosine = normalized @ normalized.T
    return pd.DataFrame(cosine, index=matrix.index.astype(str), columns=matrix.index.astype(str))


def _lower_triangle_values(matrix: pd.DataFrame) -> pd.Series:
    values = matrix.to_numpy(dtype=float)
    if values.shape[0] < 2:
        return pd.Series(dtype=float)
    rows, cols = np.tril_indices(values.shape[0], k=-1)
    index = [f"{matrix.index[row]}__{matrix.columns[col]}" for row, col in zip(rows, cols)]
    return pd.Series(values[rows, cols], index=index, dtype=float)


def _matrix_lower_triangle_spearman(left: pd.DataFrame, right: pd.DataFrame) -> tuple[float, float, str, int]:
    targets = [target for target in left.index.astype(str) if target in set(right.index.astype(str))]
    if len(targets) < 3:
        return float("nan"), float("nan"), "non_estimable_too_few_targets", 0
    left_aligned = left.loc[targets, targets]
    right_aligned = right.loc[targets, targets]
    left_values = _lower_triangle_values(left_aligned)
    right_values = _lower_triangle_values(right_aligned)
    rho, pvalue, status, _, _ = _spearman_with_status(left_values, right_values)
    return rho, pvalue, status, int(len(left_values))


def _spearman_statistic(left: pd.Series, right: pd.Series) -> float:
    frame = pd.concat([left, right], axis=1).dropna()
    if len(frame) < 3:
        return float("nan")
    if frame.iloc[:, 0].nunique(dropna=True) <= 1 or frame.iloc[:, 1].nunique(dropna=True) <= 1:
        return float("nan")
    left_rank = frame.iloc[:, 0].rank(method="average").to_numpy(dtype=float)
    right_rank = frame.iloc[:, 1].rank(method="average").to_numpy(dtype=float)
    return float(np.corrcoef(left_rank, right_rank)[0, 1])


def _target_identity_permutation(
    predicted_cosine: pd.DataFrame,
    observed_cosine: pd.DataFrame,
    *,
    n_permutations: int,
    seed: int,
) -> tuple[float, float]:
    observed_values = _lower_triangle_values(observed_cosine)
    predicted_values = _lower_triangle_values(predicted_cosine)
    observed_rho = _spearman_statistic(predicted_values, observed_values)
    if pd.isna(observed_rho) or n_permutations <= 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    null = []
    targets = predicted_cosine.index.astype(str).tolist()
    for _ in range(n_permutations):
        shuffled = rng.permutation(targets)
        shuffled_cosine = predicted_cosine.loc[shuffled, shuffled].copy()
        shuffled_cosine.index = targets
        shuffled_cosine.columns = targets
        rho = _spearman_statistic(_lower_triangle_values(shuffled_cosine), observed_values)
        if np.isfinite(rho):
            null.append(rho)
    null_values = np.asarray(null, dtype=float)
    if null_values.size == 0:
        return float("nan"), float("nan")
    pvalue = float((np.sum(null_values >= observed_rho) + 1.0) / (len(null_values) + 1.0))
    null_std = float(np.std(null_values, ddof=1)) if null_values.size > 1 else 0.0
    zscore = float((observed_rho - float(np.mean(null_values))) / null_std) if null_std > 0.0 else float("nan")
    return pvalue, zscore


def _finite_mean(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    return float(values.mean()) if values.size else float("nan")


def summarize_prediction_targets(
    *,
    prediction_path: Path,
    model_id: str,
    cell_line: str,
    object_role: str,
    truth: pd.DataFrame,
    observed_shift: pd.DataFrame,
    axis_membership: pd.DataFrame,
    truth_contract: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prediction = load_prediction_matrix(prediction_path)
    predicted = prediction.set_index("target_gene")
    target_metrics = pd.DataFrame(
        {
            "target_gene": predicted.index.astype(str),
            "predicted_shift_mean_abs": predicted.abs().mean(axis=1).to_numpy(dtype=float),
            "predicted_shift_l2": np.linalg.norm(predicted.to_numpy(dtype=float), axis=1),
            "predicted_topk_abs_shift": predicted.abs().apply(
                lambda row: float(row.nlargest(min(10, len(row))).mean()),
                axis=1,
            ),
        }
    )
    target_metrics.index.name = None

    observed = observed_shift.set_index("target_gene")
    shared_targets = [target for target in predicted.index.astype(str) if target in set(observed.index.astype(str))]
    shared_genes = [gene for gene in predicted.columns.astype(str) if gene in set(observed.columns.astype(str))]
    response_rows: list[dict[str, object]] = []
    for target_gene in shared_targets:
        pred_vector = predicted.loc[target_gene, shared_genes].to_numpy(dtype=float)
        obs_vector = observed.loc[target_gene, shared_genes].to_numpy(dtype=float)
        obs_norm = float(np.linalg.norm(obs_vector))
        pred_norm = float(np.linalg.norm(pred_vector))
        if obs_norm <= 0.0:
            signed_projection = float("nan")
            aligned_magnitude = float("nan")
            cosine = float("nan")
        else:
            signed_projection = float(np.dot(pred_vector, obs_vector) / obs_norm)
            aligned_magnitude = abs(signed_projection)
            cosine = (
                float(np.dot(pred_vector, obs_vector) / (pred_norm * obs_norm))
                if pred_norm > 0.0
                else float("nan")
            )
        response_rows.append(
            {
                "target_gene": target_gene,
                "predicted_shift_response_aligned_signed": signed_projection,
                "predicted_shift_response_aligned_magnitude": aligned_magnitude,
                "predicted_observed_shift_cosine": cosine,
            }
        )
    target_metrics = target_metrics.merge(
        pd.DataFrame(response_rows),
        on="target_gene",
        how="left",
        validate="one_to_one",
    )

    geometry = _output_geometry_diagnostics(predicted.loc[shared_targets, shared_genes])
    for column, value in geometry.items():
        target_metrics[column] = value

    # Legacy fine-axis projections remain materialized for provenance only.
    # Active manuscript metrics use the observed-response-aligned projection
    # above and the axis-free output-geometry diagnostics.
    projected = project_prediction_to_axes(prediction, axis_membership, truth_contract)
    expected = (
        projected.loc[projected["is_expected_axis"]]
        .loc[:, ["target_gene", "fine_axis", "projected_mean_abs"]]
        .rename(
            columns={
                "fine_axis": "expected_axis",
                "projected_mean_abs": "predicted_shift_axis_aligned_magnitude",
            }
        )
    )
    axis_totals = projected.groupby("target_gene")["projected_mean_abs"].sum().rename("axis_total_magnitude")
    top_axis_idx = projected.groupby("target_gene")["projected_mean_abs"].idxmax()
    top_axis = projected.loc[top_axis_idx, ["target_gene", "fine_axis", "projected_mean_abs"]].rename(
        columns={"fine_axis": "top_axis", "projected_mean_abs": "top_axis_magnitude"}
    )
    entropy = projected.groupby("target_gene")["projected_mean_abs"].apply(_axis_entropy).rename("axis_entropy")
    axis_summary = (
        expected.set_index("target_gene")
        .join(axis_totals)
        .join(top_axis.set_index("target_gene"))
        .join(entropy)
        .reset_index()
    )
    axis_summary.index.name = None
    axis_summary["top_axis_share"] = axis_summary["top_axis_magnitude"] / axis_summary["axis_total_magnitude"].replace(0, np.nan)
    axis_summary["common_axis_dominance_score"] = axis_summary["top_axis_share"]

    summary = (
        target_metrics.merge(axis_summary, on="target_gene", how="left", validate="one_to_one")
        .merge(truth, on="target_gene", how="inner", validate="one_to_one")
    )
    summary.insert(0, "cell_line", cell_line)
    summary.insert(0, "object_role", object_role)
    summary.insert(0, "model_id", model_id)
    return summary, projected


def permutation_zscore(
    *,
    values: pd.Series,
    dependency: pd.Series,
    n_permutations: int,
    seed: int,
) -> tuple[float, float, float]:
    observed, _ = _safe_spearman(values, dependency)
    frame = pd.concat([values.rename("values"), dependency.rename("dependency")], axis=1).dropna()
    if len(frame) < 3 or n_permutations <= 0 or pd.isna(observed):
        return observed, float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    null = []
    dep = frame["dependency"].to_numpy(dtype=float)
    for _ in range(n_permutations):
        shuffled = rng.permutation(dep)
        rho, _ = _safe_spearman(frame["values"], pd.Series(shuffled, index=frame.index))
        null.append(rho)
    null_values = np.asarray(null, dtype=float)
    null_values = null_values[np.isfinite(null_values)]
    if null_values.size == 0:
        return observed, float("nan"), float("nan")
    pvalue = float((np.sum(null_values >= observed) + 1.0) / (len(null_values) + 1.0))
    null_std = float(np.std(null_values, ddof=1)) if null_values.size > 1 else 0.0
    zscore = float((observed - float(np.mean(null_values))) / null_std) if null_std > 0.0 else float("nan")
    return observed, pvalue, zscore


def summarize_model_endpoint_recovery(
    target_summary: pd.DataFrame,
    *,
    n_permutations: int = 1000,
    seed: int = 1,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    model_rows: list[dict[str, object]] = []
    category_rows: list[dict[str, object]] = []
    for (model_id, object_role, cell_line), group in target_summary.groupby(
        ["model_id", "object_role", "cell_line"],
        sort=True,
    ):
        total_rho, total_p, total_status, total_unique, dependency_unique = _spearman_with_status(
            group["predicted_shift_mean_abs"],
            group["dependency_strength"],
        )
        response_rho, response_p, response_status, response_unique, _ = _spearman_with_status(
            group["predicted_shift_response_aligned_magnitude"],
            group["dependency_strength"],
        )
        obs_rho, obs_p, obs_status, _, observed_shift_unique = _spearman_with_status(
            group["predicted_shift_mean_abs"],
            group["observed_shift_mean_abs"],
        )
        _, perm_p, perm_z = permutation_zscore(
            values=group["predicted_shift_response_aligned_magnitude"],
            dependency=group["dependency_strength"],
            n_permutations=n_permutations,
            seed=seed,
        )
        is_anchor = group["endpoint_category"].eq("Q1_anchor")
        is_low_info = group["endpoint_category"].eq("low_information")
        anchor_vs_low = group.loc[is_anchor | is_low_info].copy()
        auc = _rank_auc(
            anchor_vs_low["predicted_shift_response_aligned_magnitude"],
            anchor_vs_low["endpoint_category"].eq("Q1_anchor"),
        )
        model_rows.append(
            {
                "model_id": model_id,
                "object_role": object_role,
                "cell_line": cell_line,
                "n_targets": int(len(group)),
                "total_shift_depmap_spearman": total_rho,
                "total_shift_depmap_pvalue": total_p,
                "total_shift_depmap_status": total_status,
                "predicted_shift_mean_abs_n_unique": total_unique,
                "dependency_strength_n_unique": dependency_unique,
                "response_aligned_depmap_spearman": response_rho,
                "response_aligned_depmap_pvalue": response_p,
                "response_aligned_depmap_status": response_status,
                "response_aligned_magnitude_n_unique": response_unique,
                "response_aligned_endpoint_permutation_pvalue": perm_p,
                "response_aligned_endpoint_permutation_zscore": perm_z,
                "predicted_vs_observed_shift_spearman": obs_rho,
                "predicted_vs_observed_shift_pvalue": obs_p,
                "predicted_vs_observed_shift_status": obs_status,
                "observed_shift_mean_abs_n_unique": observed_shift_unique,
                "anchor_vs_low_information_response_auc": auc,
                "q1_anchor_count": int(is_anchor.sum()),
                "low_information_count": int(is_low_info.sum()),
                "predicted_target_similarity_mean": _finite_mean(
                    group["predicted_target_similarity_mean"]
                ),
                "leading_singular_energy_share": _finite_mean(
                    group["leading_singular_energy_share"]
                ),
                "normalized_inverse_effective_rank": _finite_mean(
                    group["normalized_inverse_effective_rank"]
                ),
                "output_homogenization_score": _finite_mean(
                    group["output_homogenization_score"]
                ),
            }
        )
        for category, category_group in group.groupby("endpoint_category", sort=True):
            category_rows.append(
                {
                    "model_id": model_id,
                    "object_role": object_role,
                    "cell_line": cell_line,
                    "endpoint_category": category,
                    "n_targets": int(len(category_group)),
                    "predicted_shift_mean_abs_median": float(category_group["predicted_shift_mean_abs"].median()),
                    "response_aligned_magnitude_median": float(
                        category_group["predicted_shift_response_aligned_magnitude"].median()
                    ),
                }
            )
    return pd.DataFrame(model_rows), pd.DataFrame(category_rows)


def add_endpoint_recovery_qvalues(model_summary: pd.DataFrame) -> pd.DataFrame:
    summary = model_summary.copy()
    families = {
        "total_shift_depmap_qvalue": "total_shift_depmap_pvalue",
        "response_aligned_depmap_qvalue": "response_aligned_depmap_pvalue",
        "response_aligned_endpoint_permutation_qvalue": "response_aligned_endpoint_permutation_pvalue",
    }
    for q_column, p_column in families.items():
        summary[q_column] = summary.groupby("cell_line", group_keys=False)[p_column].apply(_bh_qvalues)
    return summary


def add_output_homogenization_quadrants(model_summary: pd.DataFrame) -> pd.DataFrame:
    summary = model_summary.copy()
    summary["endpoint_recovery_score"] = pd.to_numeric(
        summary["response_aligned_endpoint_permutation_zscore"],
        errors="coerce",
    )
    summary["output_homogenization_quadrant"] = "not_estimable"
    for cell_line, index in summary.groupby("cell_line").groups.items():
        endpoint = summary.loc[index, "endpoint_recovery_score"]
        common = summary.loc[index, "predicted_target_similarity_mean"]
        endpoint_cutoff = endpoint.median(skipna=True)
        common_cutoff = common.median(skipna=True)
        for row_index in index:
            endpoint_value = summary.at[row_index, "endpoint_recovery_score"]
            common_value = summary.at[row_index, "predicted_target_similarity_mean"]
            if pd.isna(endpoint_value) or pd.isna(common_value):
                continue
            endpoint_label = "high_recovery" if endpoint_value >= endpoint_cutoff else "low_recovery"
            common_label = "high_common" if common_value >= common_cutoff else "low_common"
            summary.at[row_index, "output_homogenization_quadrant"] = (
                f"{endpoint_label}/{common_label}"
            )
    return summary


def build_gears_selection_registry(model_summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    model_ids = sorted(str(model_id) for model_id in model_summary["model_id"].dropna().unique())
    for model_id in model_ids:
        if model_id == GEARS_FORMAL_MODEL_ID:
            rows.append(
                {
                    "model_id": model_id,
                    "selection_role": "pre_specified_formal",
                    "endpoint_used_for_selection": False,
                    "allowed_claim_role": "primary",
                    "selection_note": "Locked formal GEARS configuration; endpoint scores are audit outputs only.",
                }
            )
        elif model_id.startswith(GEARS_SWEEP_PREFIX):
            rows.append(
                {
                    "model_id": model_id,
                    "selection_role": "finite_budget_sensitivity",
                    "endpoint_used_for_selection": False,
                    "allowed_claim_role": "sensitivity",
                    "selection_note": "Finite-budget sweep configuration; do not promote endpoint-best runs to primary claims.",
                }
            )
    return pd.DataFrame(rows)


def build_target_identity_summary(
    *,
    prediction_root: Path,
    model_ids: list[str],
    axis_membership: pd.DataFrame,
    manifest_root: Path,
    n_permutations: int,
    seed: int,
) -> pd.DataFrame:
    from wtbench.hcc_prediction_export import (
        DEFAULT_TRUTH_CONFIG_PATH,
        build_dataset_specs,
        compute_truth_aligned_log_shift_matrix,
        load_config,
    )

    truth_config = load_config(DEFAULT_TRUTH_CONFIG_PATH)
    specs = {spec.cell_line: spec for spec in build_dataset_specs(truth_config)}
    rows: list[dict[str, object]] = []
    for cell_line in CELL_LINES:
        if cell_line not in specs:
            continue
        observed = compute_truth_aligned_log_shift_matrix(specs[cell_line], truth_config, axis_membership)
        observed_matrix = observed.set_index("target_gene")
        observed_cosine = _cosine_similarity_matrix(observed_matrix)
        observed_lower = _lower_triangle_values(observed_cosine)
        for model_id in model_ids:
            prediction_path = prediction_root / model_id / cell_line / "predicted_shift.tsv.gz"
            if not prediction_path.exists():
                continue
            prediction = load_prediction_matrix(prediction_path).set_index("target_gene")
            targets = [target for target in observed_matrix.index.astype(str) if target in set(prediction.index.astype(str))]
            genes = [gene for gene in observed_matrix.columns.astype(str) if gene in set(prediction.columns.astype(str))]
            if len(targets) < 3 or len(genes) < 2:
                rho, pvalue, status, n_pairs = float("nan"), float("nan"), "non_estimable_insufficient_overlap", 0
                permutation_pvalue, permutation_zscore = float("nan"), float("nan")
                predicted_mean = float("nan")
            else:
                predicted_matrix = prediction.loc[targets, genes]
                observed_aligned = observed_matrix.loc[targets, genes]
                predicted_cosine = _cosine_similarity_matrix(predicted_matrix)
                observed_cosine_aligned = _cosine_similarity_matrix(observed_aligned)
                rho, pvalue, status, n_pairs = _matrix_lower_triangle_spearman(
                    predicted_cosine,
                    observed_cosine_aligned,
                )
                permutation_pvalue, permutation_zscore = _target_identity_permutation(
                    predicted_cosine,
                    observed_cosine_aligned,
                    n_permutations=n_permutations,
                    seed=seed + sum(ord(char) for char in f"{model_id}:{cell_line}"),
                )
                predicted_mean = float(_lower_triangle_values(predicted_cosine).mean())
                observed_lower = _lower_triangle_values(observed_cosine_aligned)
            rows.append(
                {
                    "model_id": model_id,
                    "object_role": _load_manifest_role(model_id, cell_line, manifest_root),
                    "cell_line": cell_line,
                    "target_identity_preservation_spearman": rho,
                    "target_identity_preservation_pvalue": pvalue,
                    "target_identity_label_permutation_pvalue": permutation_pvalue,
                    "target_identity_label_permutation_zscore": permutation_zscore,
                    "target_identity_preservation_status": status,
                    "target_identity_n_pairs": n_pairs,
                    "predicted_target_similarity_mean": predicted_mean,
                    "observed_target_similarity_mean": float(observed_lower.mean()) if len(observed_lower) else float("nan"),
                }
            )
    return pd.DataFrame(rows)


def build_residual_endpoint_recovery(target_summary: pd.DataFrame) -> pd.DataFrame:
    shared = target_summary.loc[target_summary["model_id"].eq("shared_mean_baseline")].copy()
    if shared.empty:
        return pd.DataFrame()
    shared = shared.loc[
        :,
        [
            "cell_line",
            "target_gene",
            "predicted_shift_mean_abs",
            "predicted_shift_response_aligned_magnitude",
            "predicted_target_similarity_mean",
            "leading_singular_energy_share",
            "normalized_inverse_effective_rank",
            "dependency_strength",
        ],
    ].rename(
        columns={
            "predicted_shift_mean_abs": "shared_total",
            "predicted_shift_response_aligned_magnitude": "shared_response_aligned",
            "predicted_target_similarity_mean": "shared_target_similarity",
            "leading_singular_energy_share": "shared_leading_energy",
            "normalized_inverse_effective_rank": "shared_inverse_effective_rank",
        }
    )
    rows: list[dict[str, object]] = []
    for (model_id, object_role, cell_line), group in target_summary.groupby(
        ["model_id", "object_role", "cell_line"],
        sort=True,
    ):
        if model_id == "shared_mean_baseline":
            continue
        frame = group.merge(shared, on=["cell_line", "target_gene", "dependency_strength"], how="inner")
        if len(frame) < 6:
            continue
        predictors = frame.loc[
            :,
            [
                "shared_total",
                "shared_response_aligned",
                "shared_target_similarity",
                "shared_leading_energy",
                "shared_inverse_effective_rank",
            ],
        ]
        predictors = predictors.apply(pd.to_numeric, errors="coerce").fillna(0.0)
        y = pd.to_numeric(frame["dependency_strength"], errors="coerce").to_numpy(dtype=float)
        x = np.column_stack([np.ones(len(predictors)), predictors.to_numpy(dtype=float)])
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        residual = y - x @ beta
        residual_series = pd.Series(residual, index=frame.index)
        total_rho, total_p, total_status, _, _ = _spearman_with_status(
            frame["predicted_shift_mean_abs"],
            residual_series,
        )
        response_rho, response_p, response_status, _, _ = _spearman_with_status(
            frame["predicted_shift_response_aligned_magnitude"],
            residual_series,
        )
        rows.append(
            {
                "model_id": model_id,
                "object_role": object_role,
                "cell_line": cell_line,
                "n_targets": int(len(frame)),
                "residual_total_shift_spearman": total_rho,
                "residual_total_shift_pvalue": total_p,
                "residual_total_shift_status": total_status,
                "residual_response_aligned_spearman": response_rho,
                "residual_response_aligned_pvalue": response_p,
                "residual_response_aligned_status": response_status,
                "residual_model": (
                    "DepMap_strength ~ shared_total + shared_response_aligned + "
                    "shared_target_similarity + shared_leading_energy + "
                    "shared_inverse_effective_rank"
                ),
            }
        )
    result = pd.DataFrame(rows)
    if not result.empty:
        result["residual_total_shift_qvalue"] = result.groupby("cell_line", group_keys=False)[
            "residual_total_shift_pvalue"
        ].apply(_bh_qvalues)
        result["residual_response_aligned_qvalue"] = result.groupby("cell_line", group_keys=False)[
            "residual_response_aligned_pvalue"
        ].apply(_bh_qvalues)
    return result


def run_endpoint_recovery_audit(
    *,
    model_ids: list[str] | None = None,
    prediction_root: Path = DEFAULT_PREDICTION_ROOT,
    manifest_root: Path = DEFAULT_MANIFEST_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    n_permutations: int = 1000,
    seed: int = 1,
) -> dict[str, Path]:
    from wtbench.hcc_prediction_export import (
        DEFAULT_TRUTH_CONFIG_PATH,
        build_dataset_specs,
        compute_truth_aligned_log_shift_matrix,
        load_config,
    )

    if model_ids is None or not model_ids:
        model_ids = discover_model_ids(prediction_root)
    axis_membership = load_tsv(DEFAULT_AXIS_MEMBERSHIP_PATH)
    truth_contract = load_tsv(DEFAULT_TRUTH_CONTRACT_PATH)
    target_frames: list[pd.DataFrame] = []
    axis_frames: list[pd.DataFrame] = []
    threshold_rows: list[dict[str, object]] = []
    truth_config = load_config(DEFAULT_TRUTH_CONFIG_PATH)
    dataset_specs = {spec.cell_line: spec for spec in build_dataset_specs(truth_config)}
    for cell_line in CELL_LINES:
        truth, thresholds = load_truth_endpoint_table(cell_line)
        observed_shift = compute_truth_aligned_log_shift_matrix(
            dataset_specs[cell_line],
            truth_config,
            axis_membership,
        )
        threshold_rows.append({"cell_line": cell_line, **thresholds.__dict__})
        for model_id in model_ids:
            prediction_path = prediction_root / model_id / cell_line / "predicted_shift.tsv.gz"
            if not prediction_path.exists():
                continue
            object_role = _load_manifest_role(model_id, cell_line, manifest_root)
            target_summary, projected = summarize_prediction_targets(
                prediction_path=prediction_path,
                model_id=model_id,
                cell_line=cell_line,
                object_role=object_role,
                truth=truth,
                observed_shift=observed_shift,
                axis_membership=axis_membership,
                truth_contract=truth_contract,
            )
            target_frames.append(target_summary)
            projected.insert(0, "cell_line", cell_line)
            projected.insert(0, "object_role", object_role)
            projected.insert(0, "model_id", model_id)
            axis_frames.append(projected)
    output_root.mkdir(parents=True, exist_ok=True)
    target_summary = pd.concat(target_frames, ignore_index=True) if target_frames else pd.DataFrame()
    axis_projection = pd.concat(axis_frames, ignore_index=True) if axis_frames else pd.DataFrame()
    model_summary, category_summary = summarize_model_endpoint_recovery(
        target_summary,
        n_permutations=n_permutations,
        seed=seed,
    )
    model_summary = add_endpoint_recovery_qvalues(model_summary)
    target_identity_summary = build_target_identity_summary(
        prediction_root=prediction_root,
        model_ids=model_ids,
        axis_membership=axis_membership,
        manifest_root=manifest_root,
        n_permutations=n_permutations,
        seed=seed,
    )
    if not target_identity_summary.empty:
        target_identity_summary["target_identity_label_permutation_qvalue"] = target_identity_summary.groupby(
            "cell_line",
            group_keys=False,
        )["target_identity_label_permutation_pvalue"].apply(_bh_qvalues)
    if not target_identity_summary.empty:
        identity_merge = target_identity_summary.drop(
            columns=[
                column
                for column in [
                    "predicted_target_similarity_mean",
                ]
                if column in target_identity_summary.columns
            ]
        )
        model_summary = model_summary.merge(
            identity_merge,
            on=["model_id", "object_role", "cell_line"],
            how="left",
            validate="one_to_one",
        )
    model_summary = add_output_homogenization_quadrants(model_summary)
    residual_endpoint_recovery = build_residual_endpoint_recovery(target_summary)
    gears_selection_registry = build_gears_selection_registry(model_summary)
    paths = {
        "target_summary": output_root / "target_summary.tsv",
        "axis_projection": output_root / "axis_projection.tsv",
        "model_summary": output_root / "model_summary.tsv",
        "category_summary": output_root / "category_summary.tsv",
        "endpoint_thresholds": output_root / "endpoint_thresholds.tsv",
        "target_identity_summary": output_root / "target_identity_summary.tsv",
        "output_homogenization": output_root / "output_homogenization.tsv",
        "residual_endpoint_recovery": output_root / "residual_endpoint_recovery.tsv",
        "gears_selection_registry": output_root / "gears_selection_registry.tsv",
    }
    target_summary.to_csv(paths["target_summary"], sep="\t", index=False)
    axis_projection.to_csv(paths["axis_projection"], sep="\t", index=False)
    model_summary.to_csv(paths["model_summary"], sep="\t", index=False)
    category_summary.to_csv(paths["category_summary"], sep="\t", index=False)
    pd.DataFrame(threshold_rows).to_csv(paths["endpoint_thresholds"], sep="\t", index=False)
    target_identity_summary.to_csv(paths["target_identity_summary"], sep="\t", index=False)
    model_summary.loc[
        :,
        [
            "model_id",
            "object_role",
            "cell_line",
            "endpoint_recovery_score",
            "output_homogenization_score",
            "output_homogenization_quadrant",
            "predicted_target_similarity_mean",
            "leading_singular_energy_share",
            "normalized_inverse_effective_rank",
        ],
    ].to_csv(paths["output_homogenization"], sep="\t", index=False)
    residual_endpoint_recovery.to_csv(paths["residual_endpoint_recovery"], sep="\t", index=False)
    gears_selection_registry.to_csv(paths["gears_selection_registry"], sep="\t", index=False)

    source_root = output_root / "source_data"
    source_root.mkdir(parents=True, exist_ok=True)
    model_summary.to_csv(
        source_root / "model_endpoint_recovery_metrics.tsv",
        sep="\t",
        index=False,
    )
    model_summary.loc[
        :,
        [
            "model_id",
            "object_role",
            "cell_line",
            "total_shift_depmap_pvalue",
            "total_shift_depmap_qvalue",
            "response_aligned_depmap_pvalue",
            "response_aligned_depmap_qvalue",
            "response_aligned_endpoint_permutation_pvalue",
            "response_aligned_endpoint_permutation_qvalue",
        ],
    ].to_csv(
        source_root / "model_endpoint_recovery_pq_values.tsv",
        sep="\t",
        index=False,
    )
    category_summary.to_csv(
        source_root / "model_endpoint_category_summary.tsv",
        sep="\t",
        index=False,
    )
    model_summary.loc[
        :,
        [
            "model_id",
            "object_role",
            "cell_line",
            "endpoint_recovery_score",
            "output_homogenization_score",
            "output_homogenization_quadrant",
            "predicted_target_similarity_mean",
            "leading_singular_energy_share",
            "normalized_inverse_effective_rank",
        ],
    ].to_csv(
        source_root / "model_output_homogenization_metrics.tsv",
        sep="\t",
        index=False,
    )
    target_identity_summary.to_csv(
        source_root / "model_target_identity_preservation.tsv",
        sep="\t",
        index=False,
    )
    return paths
