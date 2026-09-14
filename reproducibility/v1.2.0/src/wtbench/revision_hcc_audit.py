"""M4: Rescore HCC entrants using the frozen sampling-aware object."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from wtbench.revision_metric_validity import (
    PROJECT_ROOT,
    contract_axes,
    score_context,
    sha256_file,
    validate_contract_matrix,
)
from wtbench.hcc_prediction_export import load_axis_membership


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _derived_seed(base_seed: int, *parts: object) -> int:
    text = "::".join(str(part) for part in parts)
    offset = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
    return int(base_seed + offset % 1_000_000)


def endpoint_label_permutation_pvalue(
    score: np.ndarray,
    endpoint: np.ndarray,
    *,
    permutations: int,
    seed: int,
    two_sided: bool = True,
) -> float:
    score = np.asarray(score, dtype=float)
    endpoint = np.asarray(endpoint, dtype=float)
    keep = np.isfinite(score) & np.isfinite(endpoint)
    score = score[keep]
    endpoint = endpoint[keep]
    if score.size < 3 or np.unique(score).size <= 1 or np.unique(endpoint).size <= 1:
        return float("nan")
    score_rank = stats.rankdata(score, method="average")
    endpoint_rank = stats.rankdata(endpoint, method="average")
    score_centered = score_rank - score_rank.mean()
    endpoint_centered = endpoint_rank - endpoint_rank.mean()
    denominator = float(np.linalg.norm(score_centered) * np.linalg.norm(endpoint_centered))
    observed = float(np.dot(score_centered, endpoint_centered) / denominator)
    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(permutations):
        permuted = rng.permutation(endpoint_centered)
        null = float(np.dot(score_centered, permuted) / denominator)
        exceed += int(abs(null) >= abs(observed) if two_sided else null >= observed)
    return float((exceed + 1.0) / (permutations + 1.0))


def bh_qvalues(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    result = pd.Series(np.nan, index=values.index, dtype=float)
    valid = numeric.dropna()
    if valid.empty:
        return result
    ordered_index = valid.sort_values().index
    ordered = valid.loc[ordered_index].to_numpy(dtype=float)
    n = len(ordered)
    adjusted = ordered * n / np.arange(1, n + 1, dtype=float)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    result.loc[ordered_index] = np.clip(adjusted, 0.0, 1.0)
    return result


def _zscore(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    mean = numeric.mean()
    std = numeric.std(ddof=0)
    if not np.isfinite(std) or std <= 0.0:
        return pd.Series(0.0, index=values.index)
    return ((numeric - mean) / std).fillna(0.0)


def build_metric_long(context_metrics: pd.DataFrame) -> pd.DataFrame:
    formal = context_metrics.loc[context_metrics["entrant_role"].eq("formal")].copy()
    definitions = [
        (
            "total_shift_endpoint_alignment",
            "endpoint_alignment_spearman",
            "endpoint_alignment_ci_low",
            "endpoint_alignment_ci_high",
            1.0,
            "higher_better",
        ),
        (
            "directional_response_recovery",
            "directional_recovery_median_signed_cosine",
            "directional_recovery_ci_low",
            "directional_recovery_ci_high",
            1.0,
            "higher_better",
        ),
        (
            "endpoint_anchor_separation",
            "anchor_separation_auc",
            "anchor_separation_ci_low",
            "anchor_separation_ci_high",
            1.0,
            "higher_better",
        ),
        (
            "target_identity_preservation",
            "target_identity_spearman",
            None,
            None,
            1.0,
            "higher_better",
        ),
        (
            "excess_output_homogenization",
            "excess_homogenization_uncentered",
            None,
            None,
            -1.0,
            "higher_is_warning",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for _, row in formal.iterrows():
        for metric, value_col, low_col, high_col, orientation, direction in definitions:
            raw = float(row[value_col]) if pd.notna(row[value_col]) else float("nan")
            rows.append(
                {
                    "cell_line": row["cell_line"],
                    "context_role": row["context_role"],
                    "model_id": row["entrant_id"],
                    "display_name": row["display_name"],
                    "model_family": row["model_family"],
                    "metric": metric,
                    "raw_value": raw,
                    "ci_low": float(row[low_col]) if low_col and pd.notna(row[low_col]) else np.nan,
                    "ci_high": float(row[high_col]) if high_col and pd.notna(row[high_col]) else np.nan,
                    "orientation_multiplier": orientation,
                    "oriented_value": raw * orientation,
                    "direction": direction,
                }
            )
    result = pd.DataFrame(rows)
    result["display_zscore_within_context_metric"] = result.groupby(
        ["cell_line", "metric"], sort=False
    )["oriented_value"].transform(_zscore)
    return result


def build_metric_correlations(context_metrics: pd.DataFrame) -> pd.DataFrame:
    formal = context_metrics.loc[context_metrics["entrant_role"].eq("formal")].copy()
    formal["negative_excess_homogenization_uncentered"] = -formal[
        "excess_homogenization_uncentered"
    ]
    formal["negative_conventional_normalized_rmse_median"] = -formal[
        "conventional_normalized_rmse_median"
    ]
    columns = [
        "endpoint_alignment_spearman",
        "directional_recovery_median_signed_cosine",
        "anchor_separation_auc",
        "target_identity_spearman",
        "negative_excess_homogenization_uncentered",
        "conventional_pearson_median",
        "negative_conventional_normalized_rmse_median",
    ]
    scopes: list[tuple[str, pd.DataFrame]] = [
        (cell_line, group) for cell_line, group in formal.groupby("cell_line", sort=True)
    ]
    scopes.append(("pooled_model_context_descriptive", formal))
    rows: list[dict[str, Any]] = []
    for scope, group in scopes:
        for left, right in itertools.combinations_with_replacement(columns, 2):
            if left == right:
                pair = group[[left]].dropna()
                rho = 1.0 if len(pair) >= 3 and pair[left].nunique() > 1 else float("nan")
            else:
                pair = group[[left, right]].dropna()
                rho = (
                    float(stats.spearmanr(pair[left], pair[right]).statistic)
                    if len(pair) >= 3 and pair[left].nunique() > 1 and pair[right].nunique() > 1
                    else float("nan")
                )
            rows.append(
                {
                    "scope": scope,
                    "metric_x": left,
                    "metric_y": right,
                    "n_model_contexts": len(pair),
                    "spearman_rho": rho,
                    "inference_role": "descriptive_not_independent_model_trials",
                }
            )
    return pd.DataFrame(rows)


def build_discordance_tables(
    context_metrics: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    formal = context_metrics.loc[context_metrics["entrant_role"].eq("formal")].copy()
    formal["negative_conventional_normalized_rmse_median"] = -formal[
        "conventional_normalized_rmse_median"
    ]
    formal["negative_excess_homogenization_uncentered"] = -formal[
        "excess_homogenization_uncentered"
    ]
    conventional = list(config["discordance"]["conventional_oriented_metrics"])
    audit = list(config["discordance"]["audit_oriented_metrics"])
    all_rows: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    warning_rows: list[dict[str, Any]] = []
    top_n = int(config["discordance"]["report_top_n_per_context"])

    for cell_line, group in formal.groupby("cell_line", sort=True):
        group = group.copy().reset_index(drop=True)
        standardized = pd.DataFrame(index=group.index)
        for column in conventional + audit:
            standardized[column] = _zscore(group[column])
        pair_rows = []
        for left_index, right_index in itertools.combinations(group.index, 2):
            conventional_distance = float(
                np.linalg.norm(
                    standardized.loc[left_index, conventional].to_numpy(dtype=float)
                    - standardized.loc[right_index, conventional].to_numpy(dtype=float)
                )
            )
            audit_distance = float(
                np.linalg.norm(
                    standardized.loc[left_index, audit].to_numpy(dtype=float)
                    - standardized.loc[right_index, audit].to_numpy(dtype=float)
                )
            )
            pair_rows.append(
                {
                    "cell_line": cell_line,
                    "model_a": group.loc[left_index, "entrant_id"],
                    "model_b": group.loc[right_index, "entrant_id"],
                    "conventional_distance": conventional_distance,
                    "audit_profile_distance": audit_distance,
                    "discordance_ratio": audit_distance / (conventional_distance + 0.25),
                }
            )
        pairs = pd.DataFrame(pair_rows)
        conventional_median = float(pairs["conventional_distance"].median())
        audit_median = float(pairs["audit_profile_distance"].median())
        pairs["conventional_distance_median"] = conventional_median
        pairs["audit_profile_distance_median"] = audit_median
        pairs["is_predefined_candidate"] = pairs["conventional_distance"].lt(
            conventional_median
        ) & pairs["audit_profile_distance"].gt(audit_median)
        pairs = pairs.sort_values("discordance_ratio", ascending=False)
        all_rows.extend(pairs.to_dict(orient="records"))
        selected_rows.extend(
            pairs.loc[pairs["is_predefined_candidate"]].head(top_n).to_dict(orient="records")
        )

        reconstruction_composite = (
            _zscore(group["conventional_pearson_median"])
            + _zscore(-group["conventional_normalized_rmse_median"])
        ) / 2.0
        threshold = float(reconstruction_composite.median())
        warning_mask = reconstruction_composite.ge(threshold) & group[
            "excess_homogenization_uncentered"
        ].gt(0.10)
        for index in group.index[warning_mask]:
            warning_rows.append(
                {
                    "cell_line": cell_line,
                    "model_id": group.loc[index, "entrant_id"],
                    "display_name": group.loc[index, "display_name"],
                    "conventional_composite_z": reconstruction_composite.loc[index],
                    "context_median_conventional_composite_z": threshold,
                    "excess_homogenization_uncentered": group.loc[
                        index, "excess_homogenization_uncentered"
                    ],
                }
            )
    pair_columns = [
        "cell_line",
        "model_a",
        "model_b",
        "conventional_distance",
        "audit_profile_distance",
        "discordance_ratio",
        "conventional_distance_median",
        "audit_profile_distance_median",
        "is_predefined_candidate",
    ]
    warning_columns = [
        "cell_line",
        "model_id",
        "display_name",
        "conventional_composite_z",
        "context_median_conventional_composite_z",
        "excess_homogenization_uncentered",
    ]
    return (
        pd.DataFrame(all_rows, columns=pair_columns),
        pd.DataFrame(selected_rows, columns=pair_columns),
        pd.DataFrame(warning_rows, columns=warning_columns),
    )


def build_training_registry(config: dict[str, Any]) -> pd.DataFrame:
    recipe_paths = {
        "gears_hcc_formal_v1": PROJECT_ROOT / "configs/gears_hcc_formal_v1.json",
        "geneformer_hcc_formal_v1": PROJECT_ROOT / "configs/geneformer_hcc_formal_v1.json",
        "scgpt_hcc_formal_v1": PROJECT_ROOT / "configs/scgpt_hcc_formal_v1.json",
        "lm_train_lowrank_hcc_formal_v1": PROJECT_ROOT / "configs/lm_train_lowrank_hcc_formal_v1.json",
        "lm_g_geneformer_ridge_hcc_formal_v1": PROJECT_ROOT / "configs/lm_g_geneformer_ridge_hcc_formal_v1.json",
        "lm_g_scgpt_ridge_hcc_formal_v1": PROJECT_ROOT / "configs/lm_g_scgpt_ridge_hcc_formal_v1.json",
    }
    exposure = {
        "cellot_hcc_formal_v1": (False, "per-target same-context fit uses observed target cells", "scripts/models/cellot/prepare_cellot_hcc_smoke.py"),
        "cpa_v0.8.8": (False, "same-context CPA fit includes all scored perturbation labels", "scripts/models/cpa/run_cpa_full_materialization.py"),
        "gears_hcc_formal_v1": (False, "all targets enter train/validation conditions; no held-out test target set", "scripts/pipeline/gears_hcc_predictions.py"),
        "geneformer_hcc_formal_v1": (True, "leave-one-target-out adapter/kernel prediction", "configs/geneformer_hcc_formal_v1.json"),
        "scgen_hcc_formal_v1": (False, "same-context fit and latent target delta use each scored target's observed cells", "scripts/models/scgen/run_scgen_hcc_smoke.py"),
        "scgpt_hcc_formal_v1": (True, "leave-one-target-out adapter/kernel prediction", "configs/scgpt_hcc_formal_v1.json"),
        "lm_train_lowrank_hcc_formal_v1": (True, "leave-one-target-out closed-form control", "configs/lm_train_lowrank_hcc_formal_v1.json"),
        "lm_g_geneformer_ridge_hcc_formal_v1": (True, "leave-one-target-out closed-form control", "configs/lm_g_geneformer_ridge_hcc_formal_v1.json"),
        "lm_g_scgpt_ridge_hcc_formal_v1": (True, "leave-one-target-out closed-form control", "configs/lm_g_scgpt_ridge_hcc_formal_v1.json"),
        "null_model": (None, "no training", "built-in diagnostic"),
        "shared_mean_baseline": (False, "constructed from observed canonical-backbone targets; diagnostic only", "src/wtbench/hcc_prediction_export.py"),
    }
    rows = []
    entrants = [
        *(dict(item, entrant_role="formal") for item in config["formal_entrants"]),
        *(dict(item, entrant_role="diagnostic") for item in config["diagnostic_entrants"]),
    ]
    for entrant in entrants:
        model_id = entrant["model_id"]
        recipe_path = recipe_paths.get(model_id)
        recipe = json.loads(recipe_path.read_text()) if recipe_path and recipe_path.exists() else {}
        runtime = recipe.get("runtime", {})
        heldout, evaluation_design, evidence = exposure[model_id]
        for cell_line in config["contexts"]:
            manifest_path = (
                PROJECT_ROOT
                / config["inputs"]["prediction_manifest_root"]
                / model_id
                / cell_line
                / "prediction_manifest.json"
            )
            manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
            checkpoint = recipe.get("checkpoint_key", manifest.get("source_checkpoint", "not_applicable_or_not_recorded"))
            extra_runtime: dict[str, Any] = dict(runtime)
            source_files = [evidence, _relative(manifest_path)]
            if recipe_path is not None and recipe_path.exists():
                source_files.append(_relative(recipe_path))
            if model_id == "cpa_v0.8.8":
                cost_path = PROJECT_ROOT / f"reports/model_eligibility/cpa_full_materialization/training_cost_report_{cell_line}.json"
                cost = json.loads(cost_path.read_text())
                extra_runtime = {key: cost.get(key) for key in ["seed", "max_epochs", "early_stopping_patience", "batch_size", "n_latent", "device"]}
                checkpoint = f"reports/model_eligibility/cpa_full_materialization/checkpoint_{cell_line}/model.pt"
                source_files.append(_relative(cost_path))
            elif model_id == "scgen_hcc_formal_v1":
                report_path = PROJECT_ROOT / f"reports/model_eligibility/scgen_hcc_smoke/{cell_line}/smoke_report.json"
                report = json.loads(report_path.read_text())
                extra_runtime = {key: report.get(key) for key in ["max_epochs", "batch_size", "early_stopping_patience"]}
                extra_runtime["seed"] = 1
                source_files.append("scripts/pipeline/run_hcc_model_queue.py")
                source_files.append(_relative(report_path))
            elif model_id == "cellot_hcc_formal_v1":
                staging_path = PROJECT_ROOT / f"reports/model_eligibility/cellot_hcc_smoke/{cell_line}/staging_manifest.json"
                staging = json.loads(staging_path.read_text())
                extra_runtime = {key: staging.get(key) for key in ["n_iters", "max_control_cells", "max_target_cells", "gene_space", "n_genes"]}
                extra_runtime["seed"] = "not_recorded_in_staging_or_model_yaml"
                checkpoint = "per-target CellOT model.pt checkpoints"
                source_files.append(_relative(staging_path))
            rows.append(
                {
                    "model_id": model_id,
                    "display_name": entrant["display_name"],
                    "model_family": entrant["model_family"],
                    "entrant_role": entrant["entrant_role"],
                    "cell_line": cell_line,
                    "same_context_training_or_construction": True,
                    "scored_target_held_out_from_fit": heldout,
                    "evaluation_design": evaluation_design,
                    "source_kind": manifest.get("source_kind", "not_recorded"),
                    "model_version": manifest.get("model_version", "not_recorded"),
                    "checkpoint_or_reference": checkpoint,
                    "runtime_and_hyperparameters_json": json.dumps(extra_runtime, sort_keys=True),
                    "prediction_space": manifest.get("prediction_space", "not_recorded"),
                    "normalization_applied_in_export": manifest.get("normalization_applied_in_export"),
                    "log1p_applied_in_export": manifest.get("log1p_applied_in_export"),
                    "contract_pass": manifest.get("contract_pass"),
                    "source_files": ";".join(source_files),
                    "documentation_gap": (
                        "CellOT seed not recorded"
                        if model_id == "cellot_hcc_formal_v1"
                        else "none"
                    ),
                }
            )
    return pd.DataFrame(rows)


def _format_number(value: object, digits: int = 3) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "NA"
    return f"{numeric:.{digits}f}" if np.isfinite(numeric) else "NA"


def _write_report(
    output_root: Path,
    context_metrics: pd.DataFrame,
    discordant: pd.DataFrame,
    warnings: pd.DataFrame,
    training: pd.DataFrame,
) -> Path:
    formal = context_metrics.loc[context_metrics["entrant_role"].eq("formal")].copy()
    lines = [
        "# M4: Revised HCC full audit",
        "",
        "Status: `FINAL`. All formal entrants are rescored consistently using the A003 sampling-aware endpoint object, A004 metrics, and A005 entrant scope; no retraining or configuration selection based on revised scores.",
        "",
        "## Interpretation scope",
        "",
        "- HCC1143 is the sampling-aware qualified primary context; HCC38 is a sensitivity/boundary context.",
        "- All values use the common 47-target by 47-gene contract and describe only common-contract-space audit/reconstruction.",
        "- HCC1143 SS18L2 remains an anchor in the full 48-target endpoint object but is excluded from model scoring because it is absent from the historical common prediction axis; categories were not recalculated.",
        "- The five dimensions form an audit profile, not a composite leaderboard.",
        "",
    ]
    for cell_line in ["HCC1143", "HCC38"]:
        group = formal.loc[formal["cell_line"].eq(cell_line)].sort_values("display_name")
        lines.extend(
            [
                f"## {cell_line}",
                "",
                "| entrant | endpoint rho [95% CI] (perm P/q) | signed cosine median [95% CI] | anchor AUC [95% CI] | identity rho (perm P/q) | ΔH | centered ΔH | Pearson | nRMSE |",
                "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for _, row in group.iterrows():
            lines.append(
                f"| {row['display_name']} | "
                f"{_format_number(row['endpoint_alignment_spearman'])} "
                f"[{_format_number(row['endpoint_alignment_ci_low'])}, {_format_number(row['endpoint_alignment_ci_high'])}] "
                f"({_format_number(row['endpoint_alignment_label_permutation_pvalue'], 4)}/"
                f"{_format_number(row['endpoint_alignment_permutation_qvalue_bh'], 4)}) | "
                f"{_format_number(row['directional_recovery_median_signed_cosine'])} "
                f"[{_format_number(row['directional_recovery_ci_low'])}, {_format_number(row['directional_recovery_ci_high'])}] | "
                f"{_format_number(row['anchor_separation_auc'])} "
                f"[{_format_number(row['anchor_separation_ci_low'])}, {_format_number(row['anchor_separation_ci_high'])}] | "
                f"{_format_number(row['target_identity_spearman'])} "
                f"({_format_number(row['target_identity_label_permutation_pvalue'], 4)}/"
                f"{_format_number(row['target_identity_permutation_qvalue_bh'], 4)}) | "
                f"{_format_number(row['excess_homogenization_uncentered'])} | "
                f"{_format_number(row['excess_homogenization_centered'])} | "
                f"{_format_number(row['conventional_pearson_median'])} | "
                f"{_format_number(row['conventional_normalized_rmse_median'])} |"
            )
        lines.append("")

    lines.extend(["## Predefined discordance search", ""])
    if discordant.empty:
        lines.append("- No model pair met the frozen similar-reconstruction/different-audit candidate rule; thresholds were not relaxed after observing results.")
    else:
        for _, row in discordant.sort_values(["cell_line", "discordance_ratio"], ascending=[True, False]).iterrows():
            lines.append(
                f"- {row['cell_line']}: `{row['model_a']}` vs `{row['model_b']}`，"
                f"conventional distance={row['conventional_distance']:.3f}，"
                f"audit-profile distance={row['audit_profile_distance']:.3f}，"
                f"ratio={row['discordance_ratio']:.3f}。"
            )
    lines.extend(["", "## Homogenization warning search", ""])
    if warnings.empty:
        lines.append("- No formal entrant met both above-median conventional reconstruction and Delta H > 0.10; the warning rule was not lowered after observing results.")
    else:
        for _, row in warnings.iterrows():
            lines.append(
                f"- {row['cell_line']} {row['display_name']}: ΔH="
                f"{row['excess_homogenization_uncentered']:.3f}。"
            )

    h1143_scgen = formal.loc[
        formal["cell_line"].eq("HCC1143")
        & formal["entrant_id"].eq("scgen_hcc_formal_v1")
    ].iloc[0]
    h38_scgpt = formal.loc[
        formal["cell_line"].eq("HCC38")
        & formal["entrant_id"].eq("scgpt_hcc_formal_v1")
    ].iloc[0]
    h1143_cpa = formal.loc[
        formal["cell_line"].eq("HCC1143")
        & formal["entrant_id"].eq("cpa_v0.8.8")
    ].iloc[0]
    h1143_cellot = formal.loc[
        formal["cell_line"].eq("HCC1143")
        & formal["entrant_id"].eq("cellot_hcc_formal_v1")
    ].iloc[0]
    lines.extend(
        [
            "",
            "## Data-supported audit findings",
            "",
            f"- In qualified HCC1143, scGen endpoint rho={h1143_scgen['endpoint_alignment_spearman']:.3f}, "
            f"directional median={h1143_scgen['directional_recovery_median_signed_cosine']:.3f}、"
            f"identity rho={h1143_scgen['target_identity_spearman']:.3f}; however, uncentered Delta H="
            f"{h1143_scgen['excess_homogenization_uncentered']:.3f}, showing that stronger recovery can coexist with shared-output concentration. scGen uses scored-target observed cells, so this finding is restricted to a fit-output audit.",
            f"- In boundary HCC38, scGPT kernel endpoint rho={h38_scgpt['endpoint_alignment_spearman']:.3f}, "
            f"but directional median={h38_scgpt['directional_recovery_median_signed_cosine']:.3f}, "
            f"identity rho={h38_scgpt['target_identity_spearman']:.3f}; this illustrates disagreement between endpoint magnitude ordering and direction/identity.",
            f"- Centering sensitivity distinguishes homogenization structures: HCC1143 CPA Delta H "
            f"{h1143_cpa['excess_homogenization_uncentered']:.3f}→{h1143_cpa['excess_homogenization_centered']:.3f}，"
            f"whereas CellOT changes from {h1143_cellot['excess_homogenization_uncentered']:.3f} to "
            f"{h1143_cellot['excess_homogenization_centered']:.3f}. The former mainly reflects a shared cross-target component; the latter retains excess similarity after removing the shared mean.",
        ]
    )

    heldout_counts = training.loc[training["entrant_role"].eq("formal")].groupby(
        "scored_target_held_out_from_fit", dropna=False
    )["model_id"].nunique()
    heldout_n = int(heldout_counts.get(True, 0))
    in_sample_n = int(heldout_counts.get(False, 0))
    lines.extend(
        [
            "",
            "## Training/evaluation boundary",
            "",
            f"- {heldout_n} formal entrants use target-held-out/leave-one-target-out construction; {in_sample_n} use same-context observed data from scored targets for fitting or validation.",
            "- This worked example combines held-out prediction audits and in-sample/fit-output audits; it is not an overall unseen-target generalization comparison.",
            "- scGen batch commands did not explicitly pass a seed and use the frozen runner default of 1; CellOT staging/model YAML did not record a seed, a reproducibility gap to resolve or disclose in M7.",
            "",
            "## Statistical notes",
            "",
            "- Endpoint alignment uses two-sided endpoint-label permutation; target identity uses one-sided target-label/Mantel permutation.",
            "- BH correction is applied separately to 18 formal entrant-context endpoint tests and 18 identity tests; diagnostic/sensitivity runs are excluded from these families.",
            "- Anchor AUC compares frozen anchors with low-information targets and includes class-stratified bootstrap CIs; point estimates are not used for ranking.",
            "- Homogenization uses observed target geometry as reference and reports predicted minus observed; there is no universal cutoff.",
            "",
        ]
    )
    path = output_root / "M4_HCC_AUDIT_FINAL.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _render_template(template: str, **values: str) -> str:
    for key, value in values.items():
        template = template.replace(f"<{key}>", value)
    return template


def _completion_audit(
    config: dict[str, Any], entrant_definitions: list[dict[str, Any]]
) -> pd.DataFrame:
    registered = pd.read_csv(PROJECT_ROOT / config["inputs"]["completion_matrix"], sep="\t")
    rows = []
    for entrant in entrant_definitions:
        model_id = entrant["model_id"]
        for cell_line in config["contexts"]:
            source = registered.loc[
                registered["model_id"].eq(model_id) & registered["cell_line"].eq(cell_line)
            ]
            if len(source) != 1:
                rows.append(
                    {
                        "model_id": model_id,
                        "cell_line": cell_line,
                        "entrant_role": entrant["entrant_role"],
                        "completion_call": "missing_or_duplicate_registry_row",
                        "current_sha256": "",
                        "registered_sha256": "",
                        "hash_matches_registry": False,
                    }
                )
                continue
            row = source.iloc[0]
            path = PROJECT_ROOT / str(row["prediction_path"])
            current_hash = sha256_file(path) if path.exists() else ""
            rows.append(
                {
                    "model_id": model_id,
                    "cell_line": cell_line,
                    "entrant_role": entrant["entrant_role"],
                    "completion_call": row["completion_call"],
                    "prediction_path": row["prediction_path"],
                    "n_targets": row["n_targets"],
                    "n_genes": row["n_genes"],
                    "contract_pass": row["contract_pass"],
                    "current_sha256": current_hash,
                    "registered_sha256": row["prediction_sha256"],
                    "hash_matches_registry": current_hash == row["prediction_sha256"],
                }
            )
    return pd.DataFrame(rows)


def run_hcc_audit(config_path: Path, output_root: Path | None = None) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    metric_spec_path = PROJECT_ROOT / config["metric_spec"]
    metric_spec = json.loads(metric_spec_path.read_text(encoding="utf-8"))
    if output_root is None:
        output_root = PROJECT_ROOT / config["outputs"]["root"]
    output_root.mkdir(parents=True, exist_ok=True)

    endpoint_path = PROJECT_ROOT / config["inputs"]["endpoint_object"]
    endpoints = pd.read_csv(endpoint_path, sep="\t")
    axis_path = PROJECT_ROOT / metric_spec["inputs"]["axis_membership"]
    axis = load_axis_membership(axis_path)
    target_order, gene_order = contract_axes(axis)

    entrant_definitions = [
        *(dict(item, entrant_role="formal") for item in config["formal_entrants"]),
        *(dict(item, entrant_role="diagnostic") for item in config["diagnostic_entrants"]),
    ]
    registered_completion = pd.read_csv(
        PROJECT_ROOT / config["inputs"]["completion_matrix"], sep="\t"
    )
    fixed_ids = {item["model_id"] for item in entrant_definitions}
    sensitivity_ids = sorted(
        set(
            registered_completion.loc[
                registered_completion["revision_rescore_eligible"]
                .astype(str)
                .str.lower()
                .eq("true"),
                "model_id",
            ].astype(str)
        )
        - fixed_ids
    )

    def sensitivity_family(model_id: str) -> str:
        for prefix, family in [
            ("cellot_", "CellOT"),
            ("cpa_", "CPA"),
            ("gears_", "GEARS"),
            ("scgen_", "scGen"),
        ]:
            if model_id.startswith(prefix):
                return family
        return "other"

    sensitivity_definitions = [
        {
            "model_id": model_id,
            "display_name": model_id,
            "model_family": sensitivity_family(model_id),
            "entrant_role": "sensitivity",
        }
        for model_id in sensitivity_ids
    ]
    completion = _completion_audit(
        config, [*entrant_definitions, *sensitivity_definitions]
    )
    if not completion["hash_matches_registry"].all() or not completion["completion_call"].eq(
        "valid_for_rescore"
    ).all():
        raise ValueError("Formal/diagnostic prediction completion or hash validation failed.")

    target_frames: list[pd.DataFrame] = []
    context_rows: list[dict[str, Any]] = []
    input_paths: list[Path] = [
        config_path,
        PROJECT_ROOT / config["amendment"],
        metric_spec_path,
        PROJECT_ROOT / metric_spec["amendment"],
        endpoint_path,
        axis_path,
        PROJECT_ROOT / config["inputs"]["completion_matrix"],
        PROJECT_ROOT / config["inputs"]["finite_budget_registry"],
        PROJECT_ROOT / "src/wtbench/revision_hcc_audit.py",
        PROJECT_ROOT / "src/wtbench/revision_metric_validity.py",
        PROJECT_ROOT / "scripts/revision/run_m4_hcc_audit.py",
    ]
    definitions_by_id = {item["model_id"]: item for item in entrant_definitions}
    for cell_line in config["contexts"]:
        observed_path = (
            PROJECT_ROOT
            / config["inputs"]["observed_shift_root"]
            / _render_template(
                config["inputs"]["observed_shift_template"], cell_line=cell_line
            )
        )
        observed = validate_contract_matrix(
            pd.read_csv(observed_path, sep="\t"),
            target_order=target_order,
            gene_order=gene_order,
            matrix_name=f"observed:{cell_line}",
        )
        input_paths.append(observed_path)
        endpoint = endpoints.loc[endpoints["cell_line"].eq(cell_line)].copy()
        for model_id, entrant in definitions_by_id.items():
            relative_prediction = _render_template(
                config["inputs"]["prediction_template"],
                model_id=model_id,
                cell_line=cell_line,
            )
            prediction_path = PROJECT_ROOT / config["inputs"]["prediction_root"] / relative_prediction
            prediction = validate_contract_matrix(
                pd.read_csv(prediction_path, sep="\t"),
                target_order=target_order,
                gene_order=gene_order,
                matrix_name=f"{model_id}:{cell_line}",
            )
            target, summary = score_context(
                prediction=prediction,
                observed=observed,
                endpoint=endpoint,
                cell_line=cell_line,
                entrant_id=model_id,
                reference_type="",
                reference_seed=None,
                config=metric_spec,
            )
            target["entrant_kind"] = entrant["entrant_role"]
            target["display_name"] = entrant["display_name"]
            target["model_family"] = entrant["model_family"]
            summary["entrant_kind"] = entrant["entrant_role"]
            summary["entrant_role"] = entrant["entrant_role"]
            summary["display_name"] = entrant["display_name"]
            summary["model_family"] = entrant["model_family"]
            summary["endpoint_alignment_label_permutation_pvalue"] = endpoint_label_permutation_pvalue(
                target["predicted_shift_mean_abs"].to_numpy(dtype=float),
                target["depmap_gene_dependency"].to_numpy(dtype=float),
                permutations=int(config["inference"]["endpoint_label_permutations"]),
                seed=_derived_seed(
                    int(config["inference"]["endpoint_label_seed"]), model_id, cell_line
                ),
                two_sided=True,
            )
            target_frames.append(target)
            context_rows.append(summary)
            input_paths.append(prediction_path)
            manifest_path = (
                PROJECT_ROOT
                / config["inputs"]["prediction_manifest_root"]
                / model_id
                / cell_line
                / "prediction_manifest.json"
            )
            input_paths.append(manifest_path)

    target_metrics = pd.concat(target_frames, ignore_index=True)
    context_metrics = pd.DataFrame(context_rows)
    formal_mask = context_metrics["entrant_role"].eq("formal")
    context_metrics["endpoint_alignment_permutation_qvalue_bh"] = np.nan
    context_metrics.loc[formal_mask, "endpoint_alignment_permutation_qvalue_bh"] = bh_qvalues(
        context_metrics.loc[formal_mask, "endpoint_alignment_label_permutation_pvalue"]
    )
    context_metrics["target_identity_permutation_qvalue_bh"] = np.nan
    context_metrics.loc[formal_mask, "target_identity_permutation_qvalue_bh"] = bh_qvalues(
        context_metrics.loc[formal_mask, "target_identity_label_permutation_pvalue"]
    )

    metric_long = build_metric_long(context_metrics)
    correlations = build_metric_correlations(context_metrics)
    all_pairs, discordant, warnings = build_discordance_tables(context_metrics, config)
    training = build_training_registry(config)
    training_provenance_paths = [
        PROJECT_ROOT / "configs/gears_hcc_formal_v1.json",
        PROJECT_ROOT / "configs/geneformer_hcc_formal_v1.json",
        PROJECT_ROOT / "configs/scgpt_hcc_formal_v1.json",
        PROJECT_ROOT / "configs/lm_train_lowrank_hcc_formal_v1.json",
        PROJECT_ROOT / "configs/lm_g_geneformer_ridge_hcc_formal_v1.json",
        PROJECT_ROOT / "configs/lm_g_scgpt_ridge_hcc_formal_v1.json",
        PROJECT_ROOT / "configs/checkpoint_registry_v1.yaml",
        PROJECT_ROOT / "scripts/models/cpa/run_cpa_full_materialization.py",
        PROJECT_ROOT / "scripts/models/scgen/run_scgen_hcc_smoke.py",
        PROJECT_ROOT / "scripts/pipeline/run_hcc_model_queue.py",
        PROJECT_ROOT / "scripts/models/cellot/prepare_cellot_hcc_smoke.py",
        PROJECT_ROOT / "scripts/models/cellot/run_cellot_hcc_staged.py",
        PROJECT_ROOT / "scripts/pipeline/gears_hcc_predictions.py",
        PROJECT_ROOT / "scripts/stage1a/adapters/gears/build_predictions.py",
        PROJECT_ROOT / "src/wtbench/hcc_prediction_export.py",
    ]
    for cell_line in config["contexts"]:
        training_provenance_paths.extend(
            [
                PROJECT_ROOT
                / f"reports/model_eligibility/cpa_full_materialization/training_cost_report_{cell_line}.json",
                PROJECT_ROOT
                / f"reports/model_eligibility/scgen_hcc_smoke/{cell_line}/smoke_report.json",
                PROJECT_ROOT
                / f"reports/model_eligibility/cellot_hcc_smoke/{cell_line}/staging_manifest.json",
                PROJECT_ROOT
                / f"data/predictions/gears_raw/gears_hcc_formal_v1/{cell_line}/provenance.json",
            ]
        )
    missing_training_provenance = [
        path for path in training_provenance_paths if not path.exists()
    ]
    if missing_training_provenance:
        raise FileNotFoundError(
            "Missing training registry provenance: "
            + ", ".join(_relative(path) for path in missing_training_provenance)
        )
    input_paths.extend(training_provenance_paths)

    point_metric_spec = json.loads(json.dumps(metric_spec))
    point_metric_spec["inference"]["bootstrap_replicates"] = 1
    point_metric_spec["inference"]["target_identity_permutations"] = 0
    sensitivity_rows: list[dict[str, Any]] = []
    for cell_line in config["contexts"]:
        observed_path = (
            PROJECT_ROOT
            / config["inputs"]["observed_shift_root"]
            / _render_template(
                config["inputs"]["observed_shift_template"], cell_line=cell_line
            )
        )
        observed = validate_contract_matrix(
            pd.read_csv(observed_path, sep="\t"),
            target_order=target_order,
            gene_order=gene_order,
            matrix_name=f"observed:{cell_line}:sensitivity",
        )
        endpoint = endpoints.loc[endpoints["cell_line"].eq(cell_line)].copy()
        for entrant in sensitivity_definitions:
            model_id = entrant["model_id"]
            relative_prediction = _render_template(
                config["inputs"]["prediction_template"],
                model_id=model_id,
                cell_line=cell_line,
            )
            prediction_path = (
                PROJECT_ROOT / config["inputs"]["prediction_root"] / relative_prediction
            )
            prediction = validate_contract_matrix(
                pd.read_csv(prediction_path, sep="\t"),
                target_order=target_order,
                gene_order=gene_order,
                matrix_name=f"{model_id}:{cell_line}:sensitivity",
            )
            _, summary = score_context(
                prediction=prediction,
                observed=observed,
                endpoint=endpoint,
                cell_line=cell_line,
                entrant_id=model_id,
                reference_type="",
                reference_seed=None,
                config=point_metric_spec,
            )
            summary["entrant_role"] = "sensitivity"
            summary["display_name"] = model_id
            summary["model_family"] = entrant["model_family"]
            sensitivity_rows.append(summary)
            input_paths.append(prediction_path)
            manifest_path = (
                PROJECT_ROOT
                / config["inputs"]["prediction_manifest_root"]
                / model_id
                / cell_line
                / "prediction_manifest.json"
            )
            input_paths.append(manifest_path)
    sensitivity_metrics = pd.DataFrame(sensitivity_rows)

    outputs = config["outputs"]
    target_path = output_root / outputs["target_metrics"]
    context_path = output_root / outputs["context_metrics"]
    long_path = output_root / outputs["metric_long"]
    correlation_path = output_root / outputs["metric_correlations"]
    discordant_path = output_root / outputs["discordant_pairs"]
    warning_path = output_root / outputs["homogenization_warnings"]
    completion_path = output_root / outputs["completion"]
    training_path = output_root / outputs["training_registry"]
    all_pairs_path = output_root / "all_formal_pair_distances.tsv"
    sensitivity_path = output_root / config["sensitivity_policy"]["output"]

    def write_tsv(table: pd.DataFrame, path: Path) -> None:
        output_table = table.replace(r"^\s*$", "NA", regex=True).fillna("NA")
        output_table.to_csv(path, sep="\t", index=False)

    write_tsv(target_metrics, target_path)
    write_tsv(context_metrics, context_path)
    write_tsv(metric_long, long_path)
    write_tsv(correlations, correlation_path)
    write_tsv(discordant, discordant_path)
    write_tsv(warnings, warning_path)
    write_tsv(completion, completion_path)
    write_tsv(training, training_path)
    write_tsv(all_pairs, all_pairs_path)
    write_tsv(sensitivity_metrics, sensitivity_path)
    report_path = _write_report(output_root, context_metrics, discordant, warnings, training)

    output_paths = [
        target_path,
        context_path,
        long_path,
        correlation_path,
        discordant_path,
        warning_path,
        completion_path,
        training_path,
        all_pairs_path,
        sensitivity_path,
        report_path,
    ]
    manifest = {
        "status": "M4_HCC_AUDIT_FINAL",
        "date": "2026-09-04",
        "audit_id": config["audit_id"],
        "real_models_retrained": False,
        "formal_model_contexts_scored": int(formal_mask.sum()),
        "diagnostic_model_contexts_scored": int((~formal_mask).sum()),
        "sensitivity_model_contexts_point_scored": int(len(sensitivity_metrics)),
        "inputs": [
            {"path": _relative(path), "sha256": sha256_file(path)}
            for path in dict.fromkeys(input_paths)
        ],
        "outputs": [
            {"path": _relative(path), "sha256": sha256_file(path)}
            for path in output_paths
        ],
    }
    manifest_path = output_root / outputs["manifest"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest
