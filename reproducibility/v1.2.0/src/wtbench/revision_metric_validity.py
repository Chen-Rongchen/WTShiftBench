"""M3/M4 revised audit metrics under the sampling-aware endpoint."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

from wtbench.hcc_prediction_export import (
    build_dataset_specs,
    compute_truth_aligned_log_shift_matrix,
    load_axis_membership,
    load_config,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _derived_seed(base_seed: int, *parts: object) -> int:
    text = "::".join(str(part) for part in parts)
    offset = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
    return int(base_seed + offset % 1_000_000)


def contract_axes(axis_membership: pd.DataFrame) -> tuple[list[str], list[str]]:
    if "target_gene" not in axis_membership:
        raise ValueError("Axis membership lacks target_gene.")
    axis = axis_membership["target_gene"].astype(str)
    targets = sorted(axis.drop_duplicates().tolist())
    genes = targets.copy()
    return targets, genes


def validate_contract_matrix(
    frame: pd.DataFrame,
    *,
    target_order: list[str],
    gene_order: list[str],
    matrix_name: str,
) -> pd.DataFrame:
    if frame.empty or str(frame.columns[0]) != "target_gene":
        raise ValueError(f"{matrix_name}: first column must be target_gene.")
    work = frame.copy()
    work["target_gene"] = work["target_gene"].astype(str)
    duplicates = work.loc[work["target_gene"].duplicated(), "target_gene"].tolist()
    if duplicates:
        raise ValueError(f"{matrix_name}: duplicate targets: {sorted(set(duplicates))}")
    actual_targets = set(work["target_gene"])
    missing_targets = [target for target in target_order if target not in actual_targets]
    missing_genes = [gene for gene in gene_order if gene not in work.columns]
    if missing_targets or missing_genes:
        raise ValueError(
            f"{matrix_name}: contract missing targets={missing_targets}, genes={missing_genes}"
        )
    matrix = work.set_index("target_gene").loc[target_order, gene_order].astype(float)
    if not np.isfinite(matrix.to_numpy(dtype=float)).all():
        raise ValueError(f"{matrix_name}: contains nonfinite values.")
    return matrix


def _safe_spearman(left: np.ndarray, right: np.ndarray) -> tuple[float, str, int]:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    keep = np.isfinite(left) & np.isfinite(right)
    left = left[keep]
    right = right[keep]
    if left.size < 3:
        return float("nan"), "non_estimable_too_few_targets", int(left.size)
    left_scale = max(1.0, float(np.max(np.abs(left))))
    right_scale = max(1.0, float(np.max(np.abs(right))))
    if float(np.ptp(left)) <= 1e-12 * left_scale:
        return float("nan"), "non_estimable_constant_score", int(left.size)
    if float(np.ptp(right)) <= 1e-12 * right_scale:
        return float("nan"), "non_estimable_constant_endpoint", int(left.size)
    return float(stats.spearmanr(left, right).statistic), "estimated", int(left.size)


def rank_auc(score: np.ndarray, label: np.ndarray) -> float:
    score = np.asarray(score, dtype=float)
    label = np.asarray(label, dtype=bool)
    keep = np.isfinite(score)
    score = score[keep]
    label = label[keep]
    positive = score[label]
    negative = score[~label]
    if positive.size == 0 or negative.size == 0:
        return float("nan")
    greater = (positive[:, None] > negative[None, :]).mean()
    ties = (positive[:, None] == negative[None, :]).mean()
    return float(greater + 0.5 * ties)


def _percentile_ci(values: list[float], confidence: float) -> tuple[float, float]:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return float("nan"), float("nan")
    alpha = (1.0 - confidence) / 2.0
    return tuple(np.quantile(finite, [alpha, 1.0 - alpha]).astype(float))


def bootstrap_median_ci(
    values: np.ndarray,
    *,
    replicates: int,
    seed: int,
    confidence: float,
) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, values.size, size=(replicates, values.size))
    estimates = np.median(values[draws], axis=1)
    return _percentile_ci(estimates.tolist(), confidence)


def bootstrap_spearman_ci(
    left: np.ndarray,
    right: np.ndarray,
    *,
    replicates: int,
    seed: int,
    confidence: float,
) -> tuple[float, float]:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    keep = np.isfinite(left) & np.isfinite(right)
    left = left[keep]
    right = right[keep]
    if left.size < 3:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    estimates: list[float] = []
    for _ in range(replicates):
        draw = rng.integers(0, left.size, size=left.size)
        estimate, status, _ = _safe_spearman(left[draw], right[draw])
        if status == "estimated":
            estimates.append(estimate)
    return _percentile_ci(estimates, confidence)


def bootstrap_auc_ci(
    score: np.ndarray,
    label: np.ndarray,
    *,
    replicates: int,
    seed: int,
    confidence: float,
) -> tuple[float, float]:
    score = np.asarray(score, dtype=float)
    label = np.asarray(label, dtype=bool)
    keep = np.isfinite(score)
    score = score[keep]
    label = label[keep]
    positive = score[label]
    negative = score[~label]
    if positive.size == 0 or negative.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(replicates):
        pos_draw = positive[rng.integers(0, positive.size, size=positive.size)]
        neg_draw = negative[rng.integers(0, negative.size, size=negative.size)]
        estimates.append(
            rank_auc(
                np.concatenate([pos_draw, neg_draw]),
                np.concatenate(
                    [np.ones(pos_draw.size, dtype=bool), np.zeros(neg_draw.size, dtype=bool)]
                ),
            )
        )
    return _percentile_ci(estimates, confidence)


def cosine_similarity_matrix(values: np.ndarray, *, tolerance: float) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(values, dtype=float)
    norms = np.linalg.norm(values, axis=1)
    valid = norms > tolerance
    normalized = values[valid] / norms[valid, None]
    return normalized @ normalized.T, valid


def mean_off_diagonal_cosine(values: np.ndarray, *, tolerance: float) -> tuple[float, int]:
    values = np.asarray(values, dtype=float)
    norms = np.linalg.norm(values, axis=1)
    valid = norms > tolerance
    normalized = values[valid] / norms[valid, None]
    n = normalized.shape[0]
    if n < 2:
        return float("nan"), int(valid.sum())
    summed = normalized.sum(axis=0)
    pair_sum_twice = float(np.dot(summed, summed) - n)
    return pair_sum_twice / (n * (n - 1)), int(valid.sum())


def target_identity_mantel(
    predicted: np.ndarray,
    observed: np.ndarray,
    *,
    tolerance: float,
    permutations: int,
    seed: int,
) -> dict[str, Any]:
    predicted = np.asarray(predicted, dtype=float)
    observed = np.asarray(observed, dtype=float)
    pred_norm = np.linalg.norm(predicted, axis=1)
    obs_norm = np.linalg.norm(observed, axis=1)
    valid = (pred_norm > tolerance) & (obs_norm > tolerance)
    predicted = predicted[valid]
    observed = observed[valid]
    n_targets = int(valid.sum())
    if n_targets < 3:
        return {
            "rho": float("nan"),
            "pvalue": float("nan"),
            "status": "non_estimable_too_few_targets",
            "n_targets": n_targets,
            "n_pairs": 0,
        }
    pred_unit = predicted / np.linalg.norm(predicted, axis=1)[:, None]
    obs_unit = observed / np.linalg.norm(observed, axis=1)[:, None]
    pred_similarity = pred_unit @ pred_unit.T
    obs_similarity = obs_unit @ obs_unit.T
    lower = np.tril_indices(n_targets, k=-1)
    pred_values = pred_similarity[lower]
    obs_values = obs_similarity[lower]
    rho, status, n_pairs = _safe_spearman(pred_values, obs_values)
    if status != "estimated" or permutations <= 0:
        return {
            "rho": rho,
            "pvalue": float("nan"),
            "status": status,
            "n_targets": n_targets,
            "n_pairs": n_pairs,
        }

    obs_ranks = stats.rankdata(obs_values, method="average")
    pred_pair_ranks = stats.rankdata(pred_values, method="average")
    pred_rank_matrix = np.zeros((n_targets, n_targets), dtype=float)
    pred_rank_matrix[lower] = pred_pair_ranks
    pred_rank_matrix[(lower[1], lower[0])] = pred_pair_ranks
    obs_centered = obs_ranks - obs_ranks.mean()
    obs_scale = float(np.linalg.norm(obs_centered))
    rng = np.random.default_rng(seed)
    exceed = 0
    valid_null = 0
    for _ in range(permutations):
        order = rng.permutation(n_targets)
        permuted = pred_rank_matrix[order[lower[0]], order[lower[1]]]
        permuted = permuted - permuted.mean()
        denominator = float(np.linalg.norm(permuted) * obs_scale)
        if denominator <= tolerance:
            continue
        null_rho = float(np.dot(permuted, obs_centered) / denominator)
        valid_null += 1
        exceed += int(null_rho >= rho)
    pvalue = (
        float((exceed + 1.0) / (valid_null + 1.0)) if valid_null else float("nan")
    )
    return {
        "rho": rho,
        "pvalue": pvalue,
        "status": "estimated" if valid_null else "non_estimable_null",
        "n_targets": n_targets,
        "n_pairs": n_pairs,
    }


def build_target_metrics(
    *,
    prediction: pd.DataFrame,
    observed: pd.DataFrame,
    endpoint: pd.DataFrame,
    cell_line: str,
    entrant_id: str,
    reference_type: str,
    reference_seed: int | None,
    tolerance: float,
) -> pd.DataFrame:
    if not prediction.index.equals(observed.index) or not prediction.columns.equals(observed.columns):
        raise ValueError("Prediction and observed contract target/gene ordering differ.")
    pred = prediction.to_numpy(dtype=float)
    obs = observed.to_numpy(dtype=float)
    pred_norm = np.linalg.norm(pred, axis=1)
    obs_norm = np.linalg.norm(obs, axis=1)
    valid_direction = (pred_norm > tolerance) & (obs_norm > tolerance)
    dot = np.einsum("ij,ij->i", pred, obs)

    cosine = np.full(len(pred), np.nan, dtype=float)
    signed_projection = np.full(len(pred), np.nan, dtype=float)
    cosine[valid_direction] = dot[valid_direction] / (
        pred_norm[valid_direction] * obs_norm[valid_direction]
    )
    signed_projection[valid_direction] = dot[valid_direction] / obs_norm[valid_direction]

    pred_centered = pred - pred.mean(axis=1, keepdims=True)
    obs_centered = obs - obs.mean(axis=1, keepdims=True)
    pred_centered_norm = np.linalg.norm(pred_centered, axis=1)
    obs_centered_norm = np.linalg.norm(obs_centered, axis=1)
    valid_pearson = (pred_centered_norm > tolerance) & (obs_centered_norm > tolerance)
    pearson = np.full(len(pred), np.nan, dtype=float)
    pearson[valid_pearson] = np.einsum(
        "ij,ij->i", pred_centered[valid_pearson], obs_centered[valid_pearson]
    ) / (pred_centered_norm[valid_pearson] * obs_centered_norm[valid_pearson])

    observed_rms = np.sqrt(np.mean(np.square(obs), axis=1))
    rmse = np.sqrt(np.mean(np.square(pred - obs), axis=1))
    normalized_rmse = np.full(len(pred), np.nan, dtype=float)
    valid_rmse = observed_rms > tolerance
    normalized_rmse[valid_rmse] = rmse[valid_rmse] / observed_rms[valid_rmse]

    target = pd.DataFrame(
        {
            "cell_line": cell_line,
            "entrant_id": entrant_id,
            "entrant_kind": "reference",
            "reference_type": reference_type,
            "reference_seed": reference_seed,
            "target_gene": prediction.index.astype(str),
            "predicted_shift_mean_abs": np.mean(np.abs(pred), axis=1),
            "predicted_shift_l2": pred_norm,
            "observed_contract_shift_mean_abs": np.mean(np.abs(obs), axis=1),
            "observed_contract_shift_l2": obs_norm,
            "signed_cosine": cosine,
            "signed_response_axis_projection": signed_projection,
            "absolute_response_axis_projection": np.abs(signed_projection),
            "pearson": pearson,
            "normalized_rmse": normalized_rmse,
            "direction_status": np.where(valid_direction, "estimated", "non_estimable_zero_norm"),
            "pearson_status": np.where(valid_pearson, "estimated", "non_estimable_zero_variance"),
            "normalized_rmse_status": np.where(valid_rmse, "estimated", "non_estimable_zero_observed_rms"),
        }
    )
    endpoint_columns = [
        "target_gene",
        "context_role",
        "depmap_gene_dependency",
        "noise_corrected_shift",
        "endpoint_category",
        "corrected_shift_percentile",
        "corrected_dependency_percentile",
    ]
    target = target.merge(
        endpoint.loc[:, endpoint_columns],
        on="target_gene",
        how="left",
        validate="one_to_one",
    )
    if target["depmap_gene_dependency"].isna().any():
        missing = target.loc[target["depmap_gene_dependency"].isna(), "target_gene"].tolist()
        raise ValueError(f"{cell_line}: endpoint object missing contract targets: {missing}")
    return target


def score_context(
    *,
    prediction: pd.DataFrame,
    observed: pd.DataFrame,
    endpoint: pd.DataFrame,
    cell_line: str,
    entrant_id: str,
    reference_type: str,
    reference_seed: int | None,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    numerical = config["numerical_rules"]
    inference = config["inference"]
    tolerance = float(numerical["zero_norm_tolerance"])
    bootstrap_replicates = int(inference["bootstrap_replicates"])
    confidence = float(inference["confidence_level"])
    base_bootstrap_seed = int(inference["bootstrap_seed"])
    identity_seed = int(inference["target_identity_seed"])
    seed_parts = (cell_line, entrant_id, reference_seed)

    target = build_target_metrics(
        prediction=prediction,
        observed=observed,
        endpoint=endpoint,
        cell_line=cell_line,
        entrant_id=entrant_id,
        reference_type=reference_type,
        reference_seed=reference_seed,
        tolerance=tolerance,
    )
    dependency = target["depmap_gene_dependency"].to_numpy(dtype=float)
    magnitude = target["predicted_shift_mean_abs"].to_numpy(dtype=float)
    total_rho, total_status, total_n = _safe_spearman(magnitude, dependency)
    total_ci = bootstrap_spearman_ci(
        magnitude,
        dependency,
        replicates=bootstrap_replicates,
        seed=_derived_seed(base_bootstrap_seed, *seed_parts, "total"),
        confidence=confidence,
    )

    directional = target["signed_cosine"].to_numpy(dtype=float)
    directional_median = float(np.nanmedian(directional)) if np.isfinite(directional).any() else float("nan")
    directional_ci = bootstrap_median_ci(
        directional,
        replicates=bootstrap_replicates,
        seed=_derived_seed(base_bootstrap_seed, *seed_parts, "directional"),
        confidence=confidence,
    )

    anchor_subset = target["endpoint_category"].isin(["endpoint_anchor", "low_information"])
    anchor_scores = target.loc[anchor_subset, "predicted_shift_mean_abs"].to_numpy(dtype=float)
    anchor_labels = target.loc[anchor_subset, "endpoint_category"].eq("endpoint_anchor").to_numpy()
    anchor_auc = rank_auc(anchor_scores, anchor_labels)
    anchor_ci = bootstrap_auc_ci(
        anchor_scores,
        anchor_labels,
        replicates=bootstrap_replicates,
        seed=_derived_seed(base_bootstrap_seed, *seed_parts, "anchor_auc"),
        confidence=confidence,
    )

    identity = target_identity_mantel(
        prediction.to_numpy(dtype=float),
        observed.to_numpy(dtype=float),
        tolerance=tolerance,
        permutations=int(inference["target_identity_permutations"]),
        seed=_derived_seed(identity_seed, *seed_parts, "identity"),
    )

    predicted_values = prediction.to_numpy(dtype=float)
    observed_values = observed.to_numpy(dtype=float)
    pred_h, pred_h_n = mean_off_diagonal_cosine(predicted_values, tolerance=tolerance)
    obs_h, obs_h_n = mean_off_diagonal_cosine(observed_values, tolerance=tolerance)
    pred_centered = predicted_values - predicted_values.mean(axis=0, keepdims=True)
    obs_centered = observed_values - observed_values.mean(axis=0, keepdims=True)
    pred_h_centered, pred_h_centered_n = mean_off_diagonal_cosine(
        pred_centered, tolerance=tolerance
    )
    obs_h_centered, obs_h_centered_n = mean_off_diagonal_cosine(
        obs_centered, tolerance=tolerance
    )

    def median_with_ci(column: str) -> tuple[float, float, float, int]:
        values = target[column].to_numpy(dtype=float)
        finite = values[np.isfinite(values)]
        estimate = float(np.median(finite)) if finite.size else float("nan")
        low, high = bootstrap_median_ci(
            values,
            replicates=bootstrap_replicates,
            seed=_derived_seed(base_bootstrap_seed, *seed_parts, column),
            confidence=confidence,
        )
        return estimate, low, high, int(finite.size)

    pearson_median, pearson_low, pearson_high, pearson_n = median_with_ci("pearson")
    nrmse_median, nrmse_low, nrmse_high, nrmse_n = median_with_ci("normalized_rmse")
    abs_projection_median, abs_projection_low, abs_projection_high, abs_projection_n = median_with_ci(
        "absolute_response_axis_projection"
    )

    endpoint_target_set = set(endpoint["target_gene"].astype(str))
    contract_target_set = set(target["target_gene"].astype(str))
    summary: dict[str, Any] = {
        "cell_line": cell_line,
        "context_role": str(endpoint["context_role"].iloc[0]),
        "entrant_id": entrant_id,
        "entrant_kind": "reference",
        "reference_type": reference_type,
        "reference_seed": reference_seed,
        "full_endpoint_n_targets": len(endpoint_target_set),
        "contract_n_targets": len(contract_target_set),
        "endpoint_coverage_fraction": len(contract_target_set) / len(endpoint_target_set),
        "missing_endpoint_targets": ",".join(sorted(endpoint_target_set - contract_target_set)),
        "contract_n_genes": prediction.shape[1],
        "endpoint_alignment_spearman": total_rho,
        "endpoint_alignment_ci_low": total_ci[0],
        "endpoint_alignment_ci_high": total_ci[1],
        "endpoint_alignment_status": total_status,
        "endpoint_alignment_n": total_n,
        "directional_recovery_median_signed_cosine": directional_median,
        "directional_recovery_ci_low": directional_ci[0],
        "directional_recovery_ci_high": directional_ci[1],
        "directional_recovery_n": int(np.isfinite(directional).sum()),
        "anchor_separation_auc": anchor_auc,
        "anchor_separation_ci_low": anchor_ci[0],
        "anchor_separation_ci_high": anchor_ci[1],
        "anchor_n": int(anchor_labels.sum()),
        "low_information_n": int((~anchor_labels).sum()),
        "target_identity_spearman": identity["rho"],
        "target_identity_label_permutation_pvalue": identity["pvalue"],
        "target_identity_status": identity["status"],
        "target_identity_n_targets": identity["n_targets"],
        "target_identity_n_pairs": identity["n_pairs"],
        "predicted_homogenization_uncentered": pred_h,
        "observed_homogenization_uncentered": obs_h,
        "excess_homogenization_uncentered": pred_h - obs_h,
        "predicted_homogenization_uncentered_n": pred_h_n,
        "observed_homogenization_uncentered_n": obs_h_n,
        "predicted_homogenization_centered": pred_h_centered,
        "observed_homogenization_centered": obs_h_centered,
        "excess_homogenization_centered": pred_h_centered - obs_h_centered,
        "predicted_homogenization_centered_n": pred_h_centered_n,
        "observed_homogenization_centered_n": obs_h_centered_n,
        "conventional_pearson_median": pearson_median,
        "conventional_pearson_ci_low": pearson_low,
        "conventional_pearson_ci_high": pearson_high,
        "conventional_pearson_n": pearson_n,
        "conventional_normalized_rmse_median": nrmse_median,
        "conventional_normalized_rmse_ci_low": nrmse_low,
        "conventional_normalized_rmse_ci_high": nrmse_high,
        "conventional_normalized_rmse_n": nrmse_n,
        "secondary_absolute_projection_median": abs_projection_median,
        "secondary_absolute_projection_ci_low": abs_projection_low,
        "secondary_absolute_projection_ci_high": abs_projection_high,
        "secondary_absolute_projection_n": abs_projection_n,
    }
    return target, summary


def build_random_direction_prediction(observed: pd.DataFrame, *, seed: int) -> pd.DataFrame:
    values = observed.to_numpy(dtype=float)
    observed_norm = np.linalg.norm(values, axis=1)
    rng = np.random.default_rng(seed)
    random = rng.normal(size=values.shape)
    random_norm = np.linalg.norm(random, axis=1)
    random = random / random_norm[:, None] * observed_norm[:, None]
    return pd.DataFrame(random, index=observed.index.copy(), columns=observed.columns.copy())


def _reference_acceptance(
    context_summary: pd.DataFrame,
    target_summary: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    limits = config["reference_acceptance"]
    rows: list[dict[str, Any]] = []

    def add(check_id: str, context: str, observed: float, threshold: float, passed: bool, rule: str) -> None:
        rows.append(
            {
                "check_id": check_id,
                "cell_line": context,
                "observed": observed,
                "threshold": threshold,
                "rule": rule,
                "passed": bool(passed),
            }
        )

    for cell_line, group in context_summary.groupby("cell_line", sort=True):
        oracle = group.loc[group["reference_type"].eq("observed_shift_oracle")].iloc[0]
        negated = group.loc[group["reference_type"].eq("negated_oracle")].iloc[0]
        shared = group.loc[group["reference_type"].eq("shared_mean_baseline")].iloc[0]
        random = group.loc[group["reference_type"].eq("observed_magnitude_random_direction")]

        oracle_error = abs(float(oracle["directional_recovery_median_signed_cosine"]) - 1.0)
        oracle_limit = float(limits["oracle_directional_median_absolute_error_max"])
        add("oracle_signed_cosine", cell_line, oracle_error, oracle_limit, oracle_error <= oracle_limit, "absolute_error<=threshold")

        negated_error = abs(float(negated["directional_recovery_median_signed_cosine"]) + 1.0)
        negated_limit = float(limits["negated_directional_median_absolute_error_max"])
        add("negated_signed_cosine", cell_line, negated_error, negated_limit, negated_error <= negated_limit, "absolute_error<=threshold")

        projection_difference = abs(
            float(oracle["secondary_absolute_projection_median"])
            - float(negated["secondary_absolute_projection_median"])
        )
        projection_limit = float(limits["oracle_vs_negated_absolute_projection_difference_max"])
        add("absolute_projection_sign_blindness", cell_line, projection_difference, projection_limit, projection_difference <= projection_limit, "absolute_difference<=threshold")

        random_grand_mean = float(random["directional_recovery_median_signed_cosine"].mean())
        random_limit = float(limits["random_direction_grand_mean_directional_median_absolute_max"])
        add("random_direction_near_zero", cell_line, abs(random_grand_mean), random_limit, abs(random_grand_mean) <= random_limit, "absolute_grand_mean<=threshold")

        shared_h = float(shared["predicted_homogenization_uncentered"])
        shared_min = float(limits["shared_mean_uncentered_homogenization_min"])
        add("shared_mean_homogenization", cell_line, shared_h, shared_min, shared_h >= shared_min, "value>=threshold")

        random_target = target_summary.loc[
            target_summary["cell_line"].eq(cell_line)
            & target_summary["reference_type"].eq("observed_magnitude_random_direction")
        ]
        denominator = random_target["observed_contract_shift_l2"].abs().clip(lower=1e-300)
        relative_error = (
            (random_target["predicted_shift_l2"] - random_target["observed_contract_shift_l2"]).abs()
            / denominator
        )
        max_error = float(relative_error.max())
        l2_limit = float(limits["random_direction_target_l2_relative_error_max"])
        add("random_direction_l2_preservation", cell_line, max_error, l2_limit, max_error <= l2_limit, "max_relative_error<=threshold")
    return pd.DataFrame(rows)


def _write_report(
    output_root: Path,
    context_summary: pd.DataFrame,
    acceptance: pd.DataFrame,
    validation: pd.DataFrame,
) -> Path:
    lines = [
        "# M3: Reference-control validation",
        "",
        "Status: `FINAL`. This stage runs only prefrozen reference controls; real-model outputs are neither read nor rescored.",
        "",
        "## Common output contract",
        "",
        "- All comparisons use the truth-aligned log1p shift contract of 47 targets by 47 response genes.",
        "- HCC1143 categories remain defined by the full 48-target corrected object; SS18L2 is excluded only because it is absent from the historical common model-output axis. Percentiles/categories are not recalculated.",
        "- With 47 genes, conventional metrics describe common-contract-space reconstruction only.",
        "",
        "## Reference behavior",
        "",
        "| context | reference | directional median | absolute projection median | endpoint rho | identity rho | Hpred | Hobs |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    selected = context_summary.loc[
        ~context_summary["reference_type"].eq("observed_magnitude_random_direction")
    ]
    for _, row in selected.sort_values(["cell_line", "reference_type"]).iterrows():
        lines.append(
            f"| {row['cell_line']} | {row['reference_type']} | "
            f"{row['directional_recovery_median_signed_cosine']:.3f} | "
            f"{row['secondary_absolute_projection_median']:.4f} | "
            f"{row['endpoint_alignment_spearman']:.3f} | "
            f"{row['target_identity_spearman']:.3f} | "
            f"{row['predicted_homogenization_uncentered']:.3f} | "
            f"{row['observed_homogenization_uncentered']:.3f} |"
        )
    lines.extend(["", "Random-direction controls（10 seeds）:", ""])
    random = context_summary.loc[
        context_summary["reference_type"].eq("observed_magnitude_random_direction")
    ]
    for cell_line, group in random.groupby("cell_line", sort=True):
        directional = group["directional_recovery_median_signed_cosine"]
        endpoint = group["endpoint_alignment_spearman"]
        anchor_auc = group["anchor_separation_auc"]
        identity = group["target_identity_spearman"]
        lines.append(
            f"- {cell_line}: signed-cosine median across seed-specific controls "
            f"mean={directional.mean():.3f}, range=[{directional.min():.3f}, {directional.max():.3f}]; "
            f"endpoint rho mean={endpoint.mean():.3f}, range=[{endpoint.min():.3f}, {endpoint.max():.3f}]; "
            f"anchor AUC mean={anchor_auc.mean():.3f}, range=[{anchor_auc.min():.3f}, {anchor_auc.max():.3f}]; "
            f"identity rho mean={identity.mean():.3f}, range=[{identity.min():.3f}, {identity.max():.3f}]."
        )
    lines.extend(
        [
            "",
            "## Acceptance decision",
            "",
            f"- {int(acceptance['passed'].sum())}/{len(acceptance)} pre-frozen checks passed。",
            f"- Contract validation rows: {len(validation)}；failed={int((~validation['passed']).sum())}。",
            "- Oracle and negated oracle may share magnitude-sensitive summaries, but primary signed cosine must have opposite signs; this directly motivates a multidimensional profile rather than composite ranking.",
            "- If magnitude-only random directions retain endpoint magnitude signal without directional recovery or target identity, magnitude calibration does not replace these dimensions.",
            "",
        ]
    )
    path = output_root / "M3_REFERENCE_FINAL.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_reference_validation(config_path: Path, output_root: Path | None = None) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if output_root is None:
        output_root = PROJECT_ROOT / config["outputs"]["root"]
    output_root.mkdir(parents=True, exist_ok=True)

    inputs = config["inputs"]
    truth_config_path = PROJECT_ROOT / inputs["truth_config"]
    axis_path = PROJECT_ROOT / inputs["axis_membership"]
    endpoint_path = PROJECT_ROOT / inputs["sampling_aware_endpoint_object"]
    truth_config = load_config(truth_config_path)
    axis_membership = load_axis_membership(axis_path)
    target_order, gene_order = contract_axes(axis_membership)
    expected_targets = int(config["contract"]["expected_target_count"])
    expected_genes = int(config["contract"]["expected_gene_count"])
    if len(target_order) != expected_targets or len(gene_order) != expected_genes:
        raise ValueError(
            f"Frozen contract dimension mismatch: observed={len(target_order)}x{len(gene_order)}, "
            f"expected={expected_targets}x{expected_genes}"
        )

    endpoints = pd.read_csv(endpoint_path, sep="\t")
    specs = {spec.cell_line: spec for spec in build_dataset_specs(truth_config)}
    target_tables: list[pd.DataFrame] = []
    context_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []
    materialized_observed_paths: list[Path] = []

    for cell_line in config["contexts"]:
        if cell_line not in specs:
            raise ValueError(f"Truth config lacks {cell_line}.")
        observed_frame = compute_truth_aligned_log_shift_matrix(
            specs[cell_line], truth_config, axis_membership
        )
        observed = validate_contract_matrix(
            observed_frame,
            target_order=target_order,
            gene_order=gene_order,
            matrix_name=f"observed:{cell_line}",
        )
        observed_path = output_root / f"observed_shift_{cell_line}.tsv.gz"
        observed.reset_index().to_csv(observed_path, sep="\t", index=False)
        materialized_observed_paths.append(observed_path)

        endpoint = endpoints.loc[endpoints["cell_line"].eq(cell_line)].copy()
        endpoint_targets = set(endpoint["target_gene"].astype(str))
        missing_endpoint = sorted(endpoint_targets - set(target_order))
        validation_rows.append(
            {
                "cell_line": cell_line,
                "object": "observed_shift",
                "n_targets": observed.shape[0],
                "n_genes": observed.shape[1],
                "full_endpoint_n_targets": len(endpoint_targets),
                "missing_endpoint_targets": ",".join(missing_endpoint),
                "passed": observed.shape == (expected_targets, expected_genes),
            }
        )

        shared_path = PROJECT_ROOT / inputs["shared_mean_paths"][cell_line]
        shared_frame = pd.read_csv(shared_path, sep="\t")
        shared = validate_contract_matrix(
            shared_frame,
            target_order=target_order,
            gene_order=gene_order,
            matrix_name=f"shared_mean:{cell_line}",
        )
        validation_rows.append(
            {
                "cell_line": cell_line,
                "object": "shared_mean_baseline",
                "n_targets": shared.shape[0],
                "n_genes": shared.shape[1],
                "full_endpoint_n_targets": len(endpoint_targets),
                "missing_endpoint_targets": ",".join(missing_endpoint),
                "passed": shared.shape == (expected_targets, expected_genes),
            }
        )

        references: list[tuple[str, str, int | None, pd.DataFrame]] = [
            ("observed_shift_oracle", "observed_shift_oracle", None, observed.copy()),
            ("negated_oracle", "negated_oracle", None, -observed),
            ("shared_mean_baseline", "shared_mean_baseline", None, shared),
        ]
        for seed in config["reference_entrants"]["observed_magnitude_random_direction"]["replicate_seeds"]:
            seed = int(seed)
            references.append(
                (
                    f"observed_magnitude_random_direction_seed{seed}",
                    "observed_magnitude_random_direction",
                    seed,
                    build_random_direction_prediction(observed, seed=seed),
                )
            )

        for entrant_id, reference_type, reference_seed, prediction in references:
            target, summary = score_context(
                prediction=prediction,
                observed=observed,
                endpoint=endpoint,
                cell_line=cell_line,
                entrant_id=entrant_id,
                reference_type=reference_type,
                reference_seed=reference_seed,
                config=config,
            )
            target_tables.append(target)
            context_rows.append(summary)

    target_summary = pd.concat(target_tables, ignore_index=True)
    context_summary = pd.DataFrame(context_rows)
    validation = pd.DataFrame(validation_rows)
    acceptance = _reference_acceptance(context_summary, target_summary, config)
    if bool(config["reference_acceptance"]["all_checks_must_pass"]) and not acceptance["passed"].all():
        failed = acceptance.loc[~acceptance["passed"]].to_dict(orient="records")
        raise AssertionError(f"M3 reference acceptance failed: {failed}")
    if not validation["passed"].all():
        raise AssertionError("M3 contract validation failed.")

    target_path = output_root / config["outputs"]["reference_target_summary"]
    context_path = output_root / config["outputs"]["reference_context_summary"]
    seed_path = output_root / config["outputs"]["reference_seed_summary"]
    validation_path = output_root / config["outputs"]["contract_validation"]
    acceptance_path = output_root / "reference_acceptance.tsv"
    target_summary.to_csv(target_path, sep="\t", index=False)
    context_summary.to_csv(context_path, sep="\t", index=False)
    context_summary.loc[
        context_summary["reference_type"].eq("observed_magnitude_random_direction")
    ].to_csv(seed_path, sep="\t", index=False)
    validation.to_csv(validation_path, sep="\t", index=False)
    acceptance.to_csv(acceptance_path, sep="\t", index=False)
    report_path = _write_report(output_root, context_summary, acceptance, validation)

    input_paths = [
        config_path,
        PROJECT_ROOT / config["amendment"],
        truth_config_path,
        axis_path,
        endpoint_path,
        PROJECT_ROOT / inputs["prediction_contract"],
        PROJECT_ROOT / inputs["truth_architecture_contract"],
        PROJECT_ROOT / inputs["prediction_completion_matrix"],
        PROJECT_ROOT / "src/wtbench/revision_metric_validity.py",
        PROJECT_ROOT / "scripts/revision/run_m3_reference_validation.py",
    ]
    for cell_line in config["contexts"]:
        input_paths.append(PROJECT_ROOT / inputs["shared_mean_paths"][cell_line])
        spec = specs[cell_line]
        for field in [
            spec.matrix_path,
            spec.barcodes_path,
            spec.features_path,
            spec.protospacer_calls_path,
            spec.h5ad_path,
        ]:
            if field is not None:
                input_paths.append(field)
    output_paths = [
        *materialized_observed_paths,
        target_path,
        context_path,
        seed_path,
        validation_path,
        acceptance_path,
        report_path,
    ]
    manifest = {
        "status": "M3_REFERENCE_FINAL",
        "date": "2026-09-04",
        "spec_id": config["spec_id"],
        "real_model_outputs_scored": False,
        "all_reference_checks_passed": bool(acceptance["passed"].all()),
        "inputs": [
            {"path": _relative(path), "sha256": sha256_file(path)} for path in input_paths
        ],
        "outputs": [
            {"path": _relative(path), "sha256": sha256_file(path)} for path in output_paths
        ],
    }
    manifest_path = output_root / config["outputs"]["manifest"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest
