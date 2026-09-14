"""M1 perturbed-cell counts and sampling-noise robustness analysis."""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import sparse, stats

from wtbench.truth_bridge import (
    build_dataset_specs,
    load_config,
    load_expression_for_called_cells,
    load_single_feature_calls,
    log_normalize_csr,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ContextData:
    cell_line: str
    normalized: sparse.csr_matrix
    calls: pd.DataFrame
    gene_names: np.ndarray
    bridge: pd.DataFrame
    control_positions: np.ndarray
    target_positions: dict[str, np.ndarray]
    target_covariates: pd.DataFrame


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bh_adjust(values: pd.Series) -> pd.Series:
    output = pd.Series(np.nan, index=values.index, dtype=float)
    finite = values.dropna().astype(float)
    if finite.empty:
        return output
    order = np.argsort(finite.to_numpy())
    ranked = finite.to_numpy()[order]
    adjusted = ranked * len(ranked) / np.arange(1, len(ranked) + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    output.loc[finite.index[order]] = adjusted
    return output


def finite_frame(x: np.ndarray, y: np.ndarray, covariates: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    z: np.ndarray | None = None
    if covariates is not None:
        z = np.asarray(covariates, dtype=float)
        if z.ndim == 1:
            z = z[:, None]
        mask &= np.isfinite(z).all(axis=1)
        z = z[mask]
    return x[mask], y[mask], z


def spearman_statistic(x: np.ndarray, y: np.ndarray, covariates: np.ndarray | None = None) -> float:
    x, y, _ = finite_frame(x, y, covariates)
    if len(x) < 3 or np.unique(x).size < 2 or np.unique(y).size < 2:
        return np.nan
    return float(stats.spearmanr(x, y).statistic)


def partial_spearman_statistic(x: np.ndarray, y: np.ndarray, covariates: np.ndarray) -> float:
    x, y, z = finite_frame(x, y, covariates)
    if z is None or len(x) < z.shape[1] + 3 or np.unique(x).size < 2 or np.unique(y).size < 2:
        return np.nan
    residual_x, residual_y, _, _ = partial_rank_components(x, y, z)
    if np.isclose(np.std(residual_x), 0.0, atol=1e-12) or np.isclose(
        np.std(residual_y), 0.0, atol=1e-12
    ):
        return np.nan
    return float(np.corrcoef(residual_x, residual_y)[0, 1])


def residualize(values: np.ndarray, design: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    return values - design @ np.linalg.lstsq(design, values, rcond=None)[0]


def partial_rank_components(
    x: np.ndarray,
    y: np.ndarray,
    covariates: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ranked_x = stats.rankdata(x)
    ranked_y = stats.rankdata(y)
    ranked_z = np.column_stack(
        [stats.rankdata(covariates[:, column]) for column in range(covariates.shape[1])]
    )
    design = np.column_stack([np.ones(len(x)), ranked_z])
    residual_x = residualize(ranked_x, design)
    residual_y = residualize(ranked_y, design)
    fitted_y = ranked_y - residual_y
    return residual_x, residual_y, fitted_y, design


def bootstrap_interval(
    x: np.ndarray,
    y: np.ndarray,
    statistic: Callable[[np.ndarray, np.ndarray, np.ndarray | None], float],
    *,
    covariates: np.ndarray | None,
    replicates: int,
    seed: int,
) -> tuple[float, float, int]:
    x, y, z = finite_frame(x, y, covariates)
    rng = np.random.default_rng(seed)
    estimates: list[float] = []
    for _ in range(replicates):
        index = rng.integers(0, len(x), size=len(x))
        value = statistic(x[index], y[index], None if z is None else z[index])
        if np.isfinite(value):
            estimates.append(value)
    if not estimates:
        return np.nan, np.nan, 0
    low, high = np.quantile(estimates, [0.025, 0.975])
    return float(low), float(high), len(estimates)


def permutation_pvalue(
    x: np.ndarray,
    y: np.ndarray,
    statistic: Callable[[np.ndarray, np.ndarray, np.ndarray | None], float],
    *,
    covariates: np.ndarray | None,
    permutations: int,
    seed: int,
) -> tuple[float, int]:
    x, y, z = finite_frame(x, y, covariates)
    observed = statistic(x, y, z)
    if not np.isfinite(observed):
        return np.nan, 0
    rng = np.random.default_rng(seed)
    extreme = 0
    completed = 0
    if z is not None:
        residual_x, residual_y, fitted_y, design = partial_rank_components(x, y, z)
        for _ in range(permutations):
            pseudo_ranked_y = fitted_y + rng.permutation(residual_y)
            permuted_residual_y = residualize(pseudo_ranked_y, design)
            if np.isclose(np.std(permuted_residual_y), 0.0, atol=1e-12):
                continue
            value = float(np.corrcoef(residual_x, permuted_residual_y)[0, 1])
            if np.isfinite(value):
                completed += 1
                extreme += int(abs(value) >= abs(observed))
        return float((extreme + 1) / (completed + 1)), completed
    for _ in range(permutations):
        value = statistic(x, rng.permutation(y), z)
        if np.isfinite(value):
            completed += 1
            extreme += int(abs(value) >= abs(observed))
    return float((extreme + 1) / (completed + 1)), completed


def infer_association(
    *,
    analysis_id: str,
    cell_line: str,
    x: np.ndarray,
    y: np.ndarray,
    bootstrap_replicates: int,
    permutation_replicates: int,
    bootstrap_seed: int,
    permutation_seed: int,
    covariates: np.ndarray | None = None,
) -> dict[str, Any]:
    statistic = partial_spearman_statistic if covariates is not None else spearman_statistic
    x_valid, y_valid, z_valid = finite_frame(x, y, covariates)
    estimate = statistic(x_valid, y_valid, z_valid)
    ci_low, ci_high, bootstrap_completed = bootstrap_interval(
        x_valid,
        y_valid,
        statistic,
        covariates=z_valid,
        replicates=bootstrap_replicates,
        seed=bootstrap_seed,
    )
    pvalue, permutations_completed = permutation_pvalue(
        x_valid,
        y_valid,
        statistic,
        covariates=z_valid,
        permutations=permutation_replicates,
        seed=permutation_seed,
    )
    return {
        "analysis_id": analysis_id,
        "cell_line": cell_line,
        "n_targets": len(x_valid),
        "spearman_rho": estimate,
        "bootstrap_ci_low": ci_low,
        "bootstrap_ci_high": ci_high,
        "permutation_pvalue_two_sided": pvalue,
        "bootstrap_replicates_completed": bootstrap_completed,
        "permutations_completed": permutations_completed,
        "statistic": "partial_spearman" if covariates is not None else "spearman",
        "permutation_method": (
            "freedman_lane_rank_residual" if covariates is not None else "endpoint_label"
        ),
    }


def standardized_ols_hc3(
    frame: pd.DataFrame,
    *,
    analysis_id: str,
    outcome: str,
    predictors: list[str],
    focus_predictor: str,
) -> dict[str, Any]:
    subset = frame[[outcome, *predictors]].dropna().copy()
    standardized = (subset - subset.mean()) / subset.std(ddof=0)
    y = standardized[outcome].to_numpy(float)
    x = np.column_stack(
        [np.ones(len(standardized)), standardized[predictors].to_numpy(float)]
    )
    inverse = np.linalg.pinv(x.T @ x)
    beta = inverse @ x.T @ y
    fitted = x @ beta
    residuals = y - fitted
    leverage = np.sum((x @ inverse) * x, axis=1)
    scaled_residuals = residuals / np.clip(1.0 - leverage, 1e-12, None)
    meat = x.T @ ((scaled_residuals**2)[:, None] * x)
    covariance = inverse @ meat @ inverse
    standard_errors = np.sqrt(np.clip(np.diag(covariance), 0.0, None))
    focus_index = predictors.index(focus_predictor) + 1
    degrees_freedom = len(y) - x.shape[1]
    critical = float(stats.t.ppf(0.975, degrees_freedom))
    estimate = float(beta[focus_index])
    standard_error = float(standard_errors[focus_index])
    t_value = estimate / standard_error if standard_error > 0 else np.nan
    pvalue = float(2.0 * stats.t.sf(abs(t_value), degrees_freedom)) if np.isfinite(t_value) else np.nan
    total_sum_squares = float(np.sum((y - y.mean()) ** 2))
    r_squared = 1.0 - float(np.sum(residuals**2)) / total_sum_squares
    return {
        "analysis_id": analysis_id,
        "cell_line": str(frame["cell_line"].iloc[0]),
        "outcome": outcome,
        "predictors": "+".join(predictors),
        "focus_predictor": focus_predictor,
        "n_targets": len(y),
        "standardized_beta": estimate,
        "hc3_standard_error": standard_error,
        "hc3_ci_low": estimate - critical * standard_error,
        "hc3_ci_high": estimate + critical * standard_error,
        "hc3_pvalue": pvalue,
        "model_r_squared": r_squared,
    }


def sample_shift_replicates(
    matrix: sparse.csr_matrix,
    positions: np.ndarray,
    reference_mean: np.ndarray,
    *,
    depth: int,
    replicates: int,
    seed: int,
    batch_size: int = 50,
) -> np.ndarray:
    positions = np.asarray(positions, dtype=np.int64)
    if depth > len(positions):
        raise ValueError(f"Sampling depth {depth} exceeds available cells {len(positions)}.")
    group = matrix[positions]
    rng = np.random.default_rng(seed)
    output = np.empty(replicates, dtype=float)
    for start in range(0, replicates, batch_size):
        stop = min(start + batch_size, replicates)
        size = stop - start
        selected = np.vstack([rng.choice(len(positions), size=depth, replace=False) for _ in range(size)])
        rows = np.repeat(np.arange(size), depth)
        weights = sparse.csr_matrix(
            (np.full(size * depth, 1.0 / depth), (rows, selected.ravel())),
            shape=(size, len(positions)),
        )
        means = (weights @ group).toarray()
        output[start:stop] = np.mean(np.abs(means - reference_mean), axis=1)
    return output


def matched_control_null_replicates(
    control_matrix: sparse.csr_matrix,
    *,
    depth: int,
    replicates: int,
    seed: int,
    batch_size: int = 50,
) -> np.ndarray:
    n_control = control_matrix.shape[0]
    if depth >= n_control:
        raise ValueError("The pseudo-perturbed sample must be smaller than the control pool.")
    full_mean = np.asarray(control_matrix.mean(axis=0)).ravel()
    sampled = sample_shift_replicates(
        control_matrix,
        np.arange(n_control),
        full_mean,
        depth=depth,
        replicates=replicates,
        seed=seed,
        batch_size=batch_size,
    )
    return sampled * (n_control / (n_control - depth))


def load_context(spec: Any, base_config: dict[str, Any], bridge_path: Path) -> ContextData:
    calls = load_single_feature_calls(
        spec,
        control_prefix=str(base_config["filters"]["control_target_prefix"]),
    )
    expression, calls, gene_meta = load_expression_for_called_cells(spec, calls)
    normalized = log_normalize_csr(
        expression,
        target_sum=float(base_config["metrics"]["normalization_target_sum"]),
    ).tocsr()
    bridge = pd.read_csv(bridge_path, sep="\t")
    bridge = bridge.loc[bridge["depmap_gene_dependency"].notna()].drop_duplicates("target_gene").copy()
    bridge["target_gene"] = bridge["target_gene"].astype(str)
    eligible = set(bridge["target_gene"])
    control_positions = np.flatnonzero(calls["is_control"].to_numpy(bool))
    target_positions = {
        str(target): group.index.to_numpy(dtype=np.int64)
        for target, group in calls.loc[(~calls["is_control"]) & calls["target_gene"].astype(str).isin(eligible)].groupby(
            "target_gene", sort=True
        )
    }
    if set(target_positions) != eligible:
        missing = sorted(eligible - set(target_positions))
        raise ValueError(f"{spec.cell_line} missing eligible target cells: {missing}")

    raw_library = np.asarray(expression.sum(axis=1)).ravel().astype(float)
    detected = np.asarray(expression.getnnz(axis=1)).ravel().astype(float)
    control_mean = np.asarray(normalized[control_positions].mean(axis=0)).ravel()
    gene_names = gene_meta["feature_name"].astype(str).to_numpy()
    gene_to_position = {name: index for index, name in enumerate(gene_names)}
    duplicate_eligible = [target for target in eligible if int(np.sum(gene_names == target)) > 1]
    if duplicate_eligible:
        raise ValueError(f"Duplicate features for eligible target gene symbols: {duplicate_eligible}")

    covariate_rows: list[dict[str, Any]] = []
    for target in sorted(target_positions):
        positions = target_positions[target]
        target_mean = np.asarray(normalized[positions].mean(axis=0)).ravel()
        recomputed_shift = float(np.mean(np.abs(target_mean - control_mean)))
        bridge_row = bridge.loc[bridge["target_gene"].eq(target)].iloc[0]
        gene_position = gene_to_position.get(target)
        baseline = control_mean[gene_position] if gene_position is not None else np.nan
        perturbed = target_mean[gene_position] if gene_position is not None else np.nan
        covariate_rows.append(
            {
                "cell_line": spec.cell_line,
                "target_gene": target,
                "n_cells_target": len(positions),
                "log_n_cells_target": float(np.log(len(positions))),
                "depmap_gene_dependency": float(bridge_row["depmap_gene_dependency"]),
                "observed_shift_mean_abs": float(bridge_row["real_shift_mean_abs"]),
                "recomputed_shift_mean_abs": recomputed_shift,
                "shift_recalculation_abs_error": abs(recomputed_shift - float(bridge_row["real_shift_mean_abs"])),
                "real_shift_L2": float(bridge_row["real_shift_L2"]),
                "real_shift_top20_mean": float(bridge_row["real_shift_top20_mean"]),
                "real_shift_top50_mean": float(bridge_row["real_shift_top50_mean"]),
                "real_shift_top100_mean": float(bridge_row["real_shift_top100_mean"]),
                "real_DEG_burden": float(bridge_row["real_DEG_burden"]),
                "median_raw_library_size": float(np.median(raw_library[positions])),
                "median_detected_gene_count": float(np.median(detected[positions])),
                "median_protospacer_umis": float(pd.to_numeric(calls.loc[positions, "num_umis"], errors="coerce").median()),
                "baseline_target_expression": float(baseline),
                "perturbed_target_expression": float(perturbed),
                "rna_level_reduction_strength": float(baseline - perturbed),
                "target_expression_available": gene_position is not None,
            }
        )
    target_covariates = pd.DataFrame(covariate_rows)
    expected_counts = bridge.set_index("target_gene")["n_cells_target"].astype(int)
    observed_counts = target_covariates.set_index("target_gene")["n_cells_target"].astype(int)
    if not observed_counts.equals(expected_counts.loc[observed_counts.index]):
        raise ValueError(f"{spec.cell_line} target cell counts differ from the frozen bridge table.")
    return ContextData(
        cell_line=spec.cell_line,
        normalized=normalized,
        calls=calls,
        gene_names=gene_names,
        bridge=bridge,
        control_positions=control_positions,
        target_positions=target_positions,
        target_covariates=target_covariates,
    )


def pairwise_covariate_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    covariates = [
        "n_cells_target",
        "median_raw_library_size",
        "median_detected_gene_count",
        "median_protospacer_umis",
        "baseline_target_expression",
        "rna_level_reduction_strength",
        "real_DEG_burden",
    ]
    outcomes = ["observed_shift_mean_abs", "depmap_gene_dependency"]
    rows: list[dict[str, Any]] = []
    for covariate in covariates:
        for outcome in outcomes:
            subset = frame[[covariate, outcome]].dropna()
            rows.append(
                {
                    "cell_line": frame["cell_line"].iloc[0],
                    "covariate": covariate,
                    "outcome": outcome,
                    "n_targets": len(subset),
                    "spearman_rho": spearman_statistic(subset[covariate].to_numpy(), subset[outcome].to_numpy()),
                }
            )
    return rows


def summarize_equal_n_correlations(equal_rhos: pd.DataFrame) -> pd.DataFrame:
    return (
        equal_rhos.groupby(["cell_line", "depth", "n_targets"])["spearman_rho"]
        .agg(
            rho_mean="mean",
            rho_median="median",
            rho_sd="std",
            rho_q025=lambda values: values.quantile(0.025),
            rho_q975=lambda values: values.quantile(0.975),
        )
        .reset_index()
    )


def coverage_masks(frame: pd.DataFrame) -> dict[str, np.ndarray]:
    n_cells = frame["n_cells_target"].to_numpy(float)
    shift = frame["observed_shift_mean_abs"].to_numpy(float)
    dependency = frame["depmap_gene_dependency"].to_numpy(float)
    n_q05, n_q10, n_q95 = np.quantile(n_cells, [0.05, 0.10, 0.95])
    s_q05, s_q95 = np.quantile(shift, [0.05, 0.95])
    d_q05, d_q95 = np.quantile(dependency, [0.05, 0.95])
    return {
        "coverage_exclude_below_q10": n_cells >= n_q10,
        "cell_count_trim_q05_q95": (n_cells >= n_q05) & (n_cells <= n_q95),
        "endpoint_plane_trim_q05_q95":
            (shift >= s_q05) & (shift <= s_q95) & (dependency >= d_q05) & (dependency <= d_q95),
    }


def save_table(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    compression = "gzip" if path.suffix == ".gz" else None
    frame.to_csv(path, sep="\t", index=False, compression=compression)


def build_figure(targets: pd.DataFrame, output_path: Path) -> None:
    contexts = list(targets["cell_line"].drop_duplicates())
    fig, axes = plt.subplots(len(contexts), 3, figsize=(12, 3.7 * len(contexts)), squeeze=False)
    columns = [
        ("n_cells_target", "depmap_gene_dependency", "Perturbed cells per target", "Dependency probability"),
        ("n_cells_target", "observed_shift_mean_abs", "Perturbed cells per target", "Observed mean-absolute shift"),
        ("noise_corrected_shift", "depmap_gene_dependency", "Noise-corrected shift", "Dependency probability"),
    ]
    for row_index, context in enumerate(contexts):
        subset = targets.loc[targets["cell_line"].eq(context)]
        for column_index, (x_name, y_name, x_label, y_label) in enumerate(columns):
            axis = axes[row_index, column_index]
            axis.scatter(subset[x_name], subset[y_name], s=28, alpha=0.8, color="#3366AA")
            rho = spearman_statistic(subset[x_name].to_numpy(), subset[y_name].to_numpy())
            axis.set_title(f"{context}: Spearman ρ={rho:.3f}")
            axis.set_xlabel(x_label)
            axis.set_ylabel(y_label)
            axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    fig.savefig(output_path.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def build_equal_n_figure(
    full_summary: pd.DataFrame,
    fixed_summary: pd.DataFrame,
    output_path: Path,
) -> None:
    contexts = list(full_summary["cell_line"].drop_duplicates())
    fig, axes = plt.subplots(1, len(contexts), figsize=(5.5 * len(contexts), 4.2), squeeze=False)
    for column_index, context in enumerate(contexts):
        axis = axes[0, column_index]
        for label, source, color, marker in [
            ("Threshold-eligible cohort", full_summary, "#3366AA", "o"),
            ("Fixed n≥100 cohort", fixed_summary, "#BB5566", "s"),
        ]:
            subset = source.loc[source["cell_line"].eq(context)].sort_values("depth")
            yerr = np.vstack(
                [
                    subset["rho_median"] - subset["rho_q025"],
                    subset["rho_q975"] - subset["rho_median"],
                ]
            )
            axis.errorbar(
                subset["depth"],
                subset["rho_median"],
                yerr=yerr,
                color=color,
                marker=marker,
                capsize=3,
                linewidth=1.5,
                label=label,
            )
        axis.axhline(0.0, color="#777777", linewidth=0.8, linestyle="--")
        axis.set_title(context)
        axis.set_xlabel("Perturbed cells sampled per target")
        axis.set_ylabel("Replicate-wise Spearman ρ")
        axis.spines[["top", "right"]].set_visible(False)
        axis.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    fig.savefig(output_path.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def run(registry_path: Path, output_root: Path) -> dict[str, Any]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    base_config_path = PROJECT_ROOT / registry["inputs"]["base_truth_config"]
    base_config = load_config(base_config_path)
    truth_cfg = registry["truth_side"]
    inference_cfg = truth_cfg["inference"]
    equal_cfg = truth_cfg["equal_n_subsampling"]
    null_cfg = truth_cfg["matched_size_control_null"]
    context_specs = build_dataset_specs(base_config)
    bridge_paths = {
        Path(path).parent.name: PROJECT_ROOT / path
        for path in registry["inputs"]["processed_truth_tables"]
    }

    target_frames: list[pd.DataFrame] = []
    pairwise_rows: list[dict[str, Any]] = []
    equal_target_rows: list[dict[str, Any]] = []
    equal_rho_rows: list[dict[str, Any]] = []
    fixed_equal_rho_rows: list[dict[str, Any]] = []
    fixed_equal_inference_rows: list[dict[str, Any]] = []
    null_target_rows: list[dict[str, Any]] = []
    null_replicate_rows: list[dict[str, Any]] = []
    inference_rows: list[dict[str, Any]] = []
    linear_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []

    for context_index, spec in enumerate(context_specs):
        print(f"[M1] Loading {spec.cell_line} raw expression...", flush=True)
        context = load_context(spec, base_config, bridge_paths[spec.cell_line])
        frame = context.target_covariates.sort_values("target_gene").reset_index(drop=True)
        validation_rows.append(
            {
                "cell_line": spec.cell_line,
                "n_targets": len(frame),
                "n_control_cells": len(context.control_positions),
                "n_gene_features": len(context.gene_names),
                "max_shift_recalculation_abs_error": frame["shift_recalculation_abs_error"].max(),
                "target_count_min": frame["n_cells_target"].min(),
                "target_count_median": frame["n_cells_target"].median(),
                "target_count_max": frame["n_cells_target"].max(),
            }
        )
        pairwise_rows.extend(pairwise_covariate_rows(frame))
        control_mean = np.asarray(context.normalized[context.control_positions].mean(axis=0)).ravel()

        all_depths = [int(equal_cfg["primary_cells_per_target"]), *map(int, equal_cfg["secondary_depths"])]
        fixed_cohort_minimum = max(all_depths)
        fixed_cohort_targets = [
            target
            for target in frame["target_gene"]
            if len(context.target_positions[target]) >= fixed_cohort_minimum
        ]
        primary_mean_by_target: dict[str, float] = {}
        for depth_index, depth in enumerate(all_depths):
            eligible_targets = [target for target in frame["target_gene"] if len(context.target_positions[target]) >= depth]
            if len(eligible_targets) < 3:
                continue
            per_target: dict[str, np.ndarray] = {}
            print(f"[M1] {spec.cell_line} equal-n depth={depth}, targets={len(eligible_targets)}...", flush=True)
            for target_index, target in enumerate(eligible_targets):
                seed = int(equal_cfg["seed"]) + context_index * 100000 + depth_index * 10000 + target_index
                values = sample_shift_replicates(
                    context.normalized,
                    context.target_positions[target],
                    control_mean,
                    depth=depth,
                    replicates=int(equal_cfg["replicates"]),
                    seed=seed,
                )
                per_target[target] = values
                equal_target_rows.append(
                    {
                        "cell_line": spec.cell_line,
                        "depth": depth,
                        "target_gene": target,
                        "n_cells_available": len(context.target_positions[target]),
                        "equal_n_shift_mean": values.mean(),
                        "equal_n_shift_sd": values.std(ddof=1),
                        "equal_n_shift_q025": np.quantile(values, 0.025),
                        "equal_n_shift_q975": np.quantile(values, 0.975),
                    }
                )
                if depth == int(equal_cfg["primary_cells_per_target"]):
                    primary_mean_by_target[target] = float(values.mean())
            dependency = frame.set_index("target_gene").loc[eligible_targets, "depmap_gene_dependency"].to_numpy(float)
            matrix = np.column_stack([per_target[target] for target in eligible_targets])
            for replicate in range(matrix.shape[0]):
                equal_rho_rows.append(
                    {
                        "cell_line": spec.cell_line,
                        "depth": depth,
                        "replicate": replicate,
                        "n_targets": len(eligible_targets),
                        "spearman_rho": spearman_statistic(matrix[replicate], dependency),
                    }
                )
            mean_shift = matrix.mean(axis=0)
            inference_rows.append(
                infer_association(
                    analysis_id=f"equal_n_expected_shift_depth_{depth}",
                    cell_line=spec.cell_line,
                    x=mean_shift,
                    y=dependency,
                    bootstrap_replicates=int(inference_cfg["target_bootstrap_replicates"]),
                    permutation_replicates=int(inference_cfg["endpoint_label_permutations"]),
                    bootstrap_seed=int(inference_cfg["target_bootstrap_seed"]) + context_index * 100 + depth_index,
                    permutation_seed=int(inference_cfg["endpoint_permutation_seed"]) + context_index * 100 + depth_index,
                )
            )

            fixed_indices = [eligible_targets.index(target) for target in fixed_cohort_targets]
            fixed_matrix = matrix[:, fixed_indices]
            fixed_dependency = frame.set_index("target_gene").loc[
                fixed_cohort_targets, "depmap_gene_dependency"
            ].to_numpy(float)
            for replicate in range(fixed_matrix.shape[0]):
                fixed_equal_rho_rows.append(
                    {
                        "cell_line": spec.cell_line,
                        "minimum_available_cells": fixed_cohort_minimum,
                        "depth": depth,
                        "replicate": replicate,
                        "n_targets": len(fixed_cohort_targets),
                        "spearman_rho": spearman_statistic(
                            fixed_matrix[replicate], fixed_dependency
                        ),
                    }
                )
            fixed_equal_inference_rows.append(
                infer_association(
                    analysis_id=f"fixed_cohort_expected_shift_depth_{depth}",
                    cell_line=spec.cell_line,
                    x=fixed_matrix.mean(axis=0),
                    y=fixed_dependency,
                    bootstrap_replicates=int(inference_cfg["target_bootstrap_replicates"]),
                    permutation_replicates=int(inference_cfg["endpoint_label_permutations"]),
                    bootstrap_seed=int(inference_cfg["target_bootstrap_seed"])
                    + 500
                    + context_index * 100
                    + depth_index,
                    permutation_seed=int(inference_cfg["endpoint_permutation_seed"])
                    + 500
                    + context_index * 100
                    + depth_index,
                )
            )

        frame["equal_n_primary_shift"] = frame["target_gene"].map(primary_mean_by_target)
        control_matrix = context.normalized[context.control_positions]
        print(f"[M1] {spec.cell_line} matched-size control null...", flush=True)
        null_cache: dict[int, np.ndarray] = {}
        for count_index, depth in enumerate(sorted(frame["n_cells_target"].astype(int).unique())):
            null_cache[depth] = matched_control_null_replicates(
                control_matrix,
                depth=depth,
                replicates=int(null_cfg["replicates"]),
                seed=int(null_cfg["seed"]) + context_index * 100000 + count_index,
            )
        for _, row in frame.iterrows():
            values = null_cache[int(row["n_cells_target"])]
            null_mean = float(values.mean())
            corrected = float(row["observed_shift_mean_abs"] - null_mean)
            null_target_rows.append(
                {
                    "cell_line": spec.cell_line,
                    "target_gene": row["target_gene"],
                    "n_cells_target": int(row["n_cells_target"]),
                    "observed_shift_mean_abs": row["observed_shift_mean_abs"],
                    "matched_null_shift_mean": null_mean,
                    "matched_null_shift_sd": values.std(ddof=1),
                    "matched_null_shift_q025": np.quantile(values, 0.025),
                    "matched_null_shift_q975": np.quantile(values, 0.975),
                    "noise_corrected_shift": corrected,
                }
            )
            for replicate, value in enumerate(values):
                null_replicate_rows.append(
                    {
                        "cell_line": spec.cell_line,
                        "target_gene": row["target_gene"],
                        "n_cells_target": int(row["n_cells_target"]),
                        "replicate": replicate,
                        "matched_null_shift": value,
                    }
                )
        null_frame = pd.DataFrame(null_target_rows)
        null_context = null_frame.loc[null_frame["cell_line"].eq(spec.cell_line)]
        frame = frame.merge(
            null_context[["target_gene", "matched_null_shift_mean", "noise_corrected_shift"]],
            on="target_gene",
            how="left",
            validate="one_to_one",
        )

        x_raw = frame["observed_shift_mean_abs"].to_numpy(float)
        x_corrected = frame["noise_corrected_shift"].to_numpy(float)
        y = frame["depmap_gene_dependency"].to_numpy(float)
        base_bootstrap_seed = int(inference_cfg["target_bootstrap_seed"]) + context_index * 1000
        base_permutation_seed = int(inference_cfg["endpoint_permutation_seed"]) + context_index * 1000
        inference_rows.extend(
            [
                infer_association(
                    analysis_id="raw_observed_shift",
                    cell_line=spec.cell_line,
                    x=x_raw,
                    y=y,
                    bootstrap_replicates=int(inference_cfg["target_bootstrap_replicates"]),
                    permutation_replicates=int(inference_cfg["endpoint_label_permutations"]),
                    bootstrap_seed=base_bootstrap_seed,
                    permutation_seed=base_permutation_seed,
                ),
                infer_association(
                    analysis_id="noise_corrected_shift",
                    cell_line=spec.cell_line,
                    x=x_corrected,
                    y=y,
                    bootstrap_replicates=int(inference_cfg["target_bootstrap_replicates"]),
                    permutation_replicates=int(inference_cfg["endpoint_label_permutations"]),
                    bootstrap_seed=base_bootstrap_seed + 1,
                    permutation_seed=base_permutation_seed + 1,
                ),
            ]
        )

        covariate_models = {
            "partial_model_a_log_n": ["log_n_cells_target"],
            "partial_model_b_log_n_library": ["log_n_cells_target", "median_raw_library_size"],
            "partial_model_c_log_n_expression_efficiency": [
                "log_n_cells_target",
                "baseline_target_expression",
                "rna_level_reduction_strength",
            ],
            "partial_model_d_log_n_deg_breadth": ["log_n_cells_target", "real_DEG_burden"],
        }
        for model_index, (analysis_id, columns) in enumerate(covariate_models.items()):
            inference_rows.append(
                infer_association(
                    analysis_id=analysis_id,
                    cell_line=spec.cell_line,
                    x=x_raw,
                    y=y,
                    covariates=frame[columns].to_numpy(float),
                    bootstrap_replicates=int(inference_cfg["target_bootstrap_replicates"]),
                    permutation_replicates=int(inference_cfg["endpoint_label_permutations"]),
                    bootstrap_seed=base_bootstrap_seed + 10 + model_index,
                    permutation_seed=base_permutation_seed + 10 + model_index,
                )
            )

        for outcome in ["observed_shift_mean_abs", "noise_corrected_shift"]:
            linear_rows.append(
                standardized_ols_hc3(
                    frame,
                    analysis_id=f"{outcome}_on_dependency_plus_log_n",
                    outcome=outcome,
                    predictors=["depmap_gene_dependency", "log_n_cells_target"],
                    focus_predictor="depmap_gene_dependency",
                )
            )

        for mask_index, (analysis_id, mask) in enumerate(coverage_masks(frame).items()):
            inference_rows.append(
                infer_association(
                    analysis_id=analysis_id,
                    cell_line=spec.cell_line,
                    x=x_raw[mask],
                    y=y[mask],
                    bootstrap_replicates=int(inference_cfg["target_bootstrap_replicates"]),
                    permutation_replicates=int(inference_cfg["endpoint_label_permutations"]),
                    bootstrap_seed=base_bootstrap_seed + 20 + mask_index,
                    permutation_seed=base_permutation_seed + 20 + mask_index,
                )
            )

        alternative_metrics = [
            "real_shift_L2",
            "real_shift_top20_mean",
            "real_shift_top50_mean",
            "real_shift_top100_mean",
            "real_DEG_burden",
        ]
        for metric_index, metric in enumerate(alternative_metrics):
            inference_rows.append(
                infer_association(
                    analysis_id=f"alternative_{metric}",
                    cell_line=spec.cell_line,
                    x=frame[metric].to_numpy(float),
                    y=y,
                    bootstrap_replicates=int(inference_cfg["target_bootstrap_replicates"]),
                    permutation_replicates=int(inference_cfg["endpoint_label_permutations"]),
                    bootstrap_seed=base_bootstrap_seed + 30 + metric_index,
                    permutation_seed=base_permutation_seed + 30 + metric_index,
                )
            )
        target_frames.append(frame)

    targets = pd.concat(target_frames, ignore_index=True)
    pairwise = pd.DataFrame(pairwise_rows)
    equal_targets = pd.DataFrame(equal_target_rows)
    equal_rhos = pd.DataFrame(equal_rho_rows)
    equal_summary = summarize_equal_n_correlations(equal_rhos)
    fixed_equal_rhos = pd.DataFrame(fixed_equal_rho_rows)
    fixed_equal_summary = summarize_equal_n_correlations(fixed_equal_rhos)
    fixed_equal_inference = pd.DataFrame(fixed_equal_inference_rows)
    fixed_equal_inference["permutation_qvalue_bh_within_analysis"] = fixed_equal_inference.groupby(
        "analysis_id"
    )["permutation_pvalue_two_sided"].transform(bh_adjust)
    null_targets = pd.DataFrame(null_target_rows)
    null_replicates = pd.DataFrame(null_replicate_rows)
    linear_sensitivity = pd.DataFrame(linear_rows)
    inference = pd.DataFrame(inference_rows)
    inference["permutation_qvalue_bh_within_analysis"] = inference.groupby("analysis_id")[
        "permutation_pvalue_two_sided"
    ].transform(bh_adjust)

    gate_cfg = truth_cfg["revised_gate_1"]
    gate_ids = [
        "equal_n_expected_shift_depth_20",
        "noise_corrected_shift",
        "partial_model_a_log_n",
    ]
    gate = inference.loc[inference["analysis_id"].isin(gate_ids)].copy()
    gate["effect_pass"] = gate["spearman_rho"].ge(float(gate_cfg["minimum_spearman_rho"]))
    gate["ci_pass"] = gate["bootstrap_ci_low"].gt(float(gate_cfg["bootstrap_ci_lower_must_exceed"]))
    gate["q_pass"] = gate["permutation_qvalue_bh_within_analysis"].le(float(gate_cfg["permutation_q_max"]))
    gate["component_pass"] = gate[["effect_pass", "ci_pass", "q_pass"]].all(axis=1)
    context_decision = gate.groupby("cell_line", as_index=False)["component_pass"].all()
    context_decision = context_decision.rename(columns={"component_pass": "all_primary_components_pass"})
    dual_context_pass = bool(context_decision["all_primary_components_pass"].all())
    context_decision["dual_context_endpoint_object_pass"] = dual_context_pass
    context_decision["decision"] = np.where(
        context_decision["all_primary_components_pass"],
        "proceed_for_context",
        "stop_and_reassess_endpoint_object",
    )

    save_table(targets, output_root / "target_level_covariates_and_corrected_shift.tsv")
    save_table(pairwise, output_root / "covariate_pairwise_correlations.tsv")
    save_table(equal_targets, output_root / "equal_n_target_summary.tsv")
    save_table(equal_rhos, output_root / "equal_n_replicate_correlations.tsv.gz")
    save_table(equal_summary, output_root / "equal_n_depth_summary.tsv")
    save_table(
        fixed_equal_rhos,
        output_root / "fixed_cohort_equal_n_replicate_correlations.tsv.gz",
    )
    save_table(fixed_equal_summary, output_root / "fixed_cohort_equal_n_depth_summary.tsv")
    save_table(fixed_equal_inference, output_root / "fixed_cohort_equal_n_inference.tsv")
    save_table(null_targets, output_root / "matched_size_null_target_summary.tsv")
    save_table(null_replicates, output_root / "matched_size_null_replicates.tsv.gz")
    save_table(inference, output_root / "bridge_inference_summary.tsv")
    save_table(gate, output_root / "revised_gate_components.tsv")
    save_table(context_decision, output_root / "m1_go_no_go_decision.tsv")
    save_table(linear_sensitivity, output_root / "linear_model_sensitivity.tsv")
    save_table(pd.DataFrame(validation_rows), output_root / "truth_recalculation_validation.tsv")
    build_figure(targets, output_root / "m1_sampling_confounding.png")
    build_equal_n_figure(
        equal_summary,
        fixed_equal_summary,
        output_root / "m1_equal_n_depth_sensitivity.png",
    )

    key = inference.loc[inference["analysis_id"].isin(["raw_observed_shift", *gate_ids])].copy()
    lines = [
        "# M1: Cells-per-target and sampling-noise audit",
        "",
        "## Go/No-Go decision",
        "",
        f"- Dual-context endpoint object: `{'PASS' if dual_context_pass else 'STOP_AND_REASSESS'}`.",
    ]
    for _, row in context_decision.iterrows():
        lines.append(f"- {row['cell_line']}：`{row['decision']}`。")
    lines.extend(
        [
            "",
            "## Principal Gate statistics",
            "",
            "The equal-n Gate component is the association of target-level expected equal-n shift with dependency, not the mean of 1,000 replicate-wise rho values.",
            "",
            "| analysis | context | n | rho | 95% CI | permutation q |",
            "| --- | --- | ---: | ---: | --- | ---: |",
        ]
    )
    for _, row in key.sort_values(["analysis_id", "cell_line"]).iterrows():
        lines.append(
            f"| {row['analysis_id']} | {row['cell_line']} | {int(row['n_targets'])} | {row['spearman_rho']:.3f} | "
            f"[{row['bootstrap_ci_low']:.3f}, {row['bootstrap_ci_high']:.3f}] | "
            f"{row['permutation_qvalue_bh_within_analysis']:.4g} |"
        )
    lines.extend(
        [
            "",
            "## Equal-n replicate distribution",
            "",
            "| cohort | context | depth | targets | median rho | 95% replicate interval |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for cohort, source in [("threshold-eligible", equal_summary), ("fixed n≥100", fixed_equal_summary)]:
        for _, row in source.sort_values(["cell_line", "depth"]).iterrows():
            lines.append(
                f"| {cohort} | {row['cell_line']} | {int(row['depth'])} | {int(row['n_targets'])} | "
                f"{row['rho_median']:.3f} | [{row['rho_q025']:.3f}, {row['rho_q975']:.3f}] |"
            )
    lines.extend(
        [
            "",
            "## Parsimonious linear sensitivity",
            "",
            "Standardized OLS jointly includes dependency and log target-cell count; the table reports the dependency coefficient with HC3 robust uncertainty.",
            "",
            "| analysis | context | n | beta | 95% CI | P | R2 |",
            "| --- | --- | ---: | ---: | --- | ---: | ---: |",
        ]
    )
    for _, row in linear_sensitivity.sort_values(["analysis_id", "cell_line"]).iterrows():
        lines.append(
            f"| {row['analysis_id']} | {row['cell_line']} | {int(row['n_targets'])} | "
            f"{row['standardized_beta']:.3f} | [{row['hc3_ci_low']:.3f}, {row['hc3_ci_high']:.3f}] | "
            f"{row['hc3_pvalue']:.4g} | {row['model_r_squared']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "- Equal-n addresses perturbed-cell sampling depth; it does not equalize per-cell UMI/nFeature.",
            "- Threshold-eligible 25/50/100 sensitivity changes target composition; only the fixed n>=100 cohort isolates sampling depth.",
            "- The matched-size null estimates expected sampling-only shift at the same target-specific cell count.",
            "- Partial-rank P values use rank-scale Freedman-Lane residual permutation, retaining the fitted dependency-covariate structure.",
            "- Library complexity and target RNA reduction may contain technical and biological components; they are robustness checks/proxies, not complete deconfounding.",
            "- The response-breadth conditional model is an incremental biological decomposition, not a purely technical correction.",
            "",
        ]
    )
    (output_root / "m1_report.md").write_text("\n".join(lines), encoding="utf-8")

    raw_input_paths = [
        path
        for spec in context_specs
        for path in [spec.matrix_path, spec.barcodes_path, spec.features_path, spec.protospacer_calls_path]
        if path is not None
    ]
    input_paths = [
        registry_path,
        base_config_path,
        PROJECT_ROOT / "configs/revision/amendment_001_m1_statistical_clarifications.json",
        PROJECT_ROOT / "configs/revision/amendment_002_m1_code_audit.json",
        PROJECT_ROOT / "configs/revision/revision_asset_inventory_v1.tsv",
        PROJECT_ROOT / registry["inputs"]["depmap_primary_endpoint"]["path"],
        *bridge_paths.values(),
        *raw_input_paths,
    ]
    input_paths = list(dict.fromkeys(input_paths))
    manifest = {
        "stage": "BIB_revision_M1",
        "registry": str(registry_path.relative_to(PROJECT_ROOT)),
        "amendments": [
            "configs/revision/amendment_001_m1_statistical_clarifications.json",
            "configs/revision/amendment_002_m1_code_audit.json",
        ],
        "dual_context_endpoint_object_pass": dual_context_pass,
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": sha256_file(path)} for path in input_paths
        ],
        "parameters": {
            "equal_n": equal_cfg,
            "matched_size_null": null_cfg,
            "inference": inference_cfg,
            "gate": gate_cfg,
        },
    }
    (output_root / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest
