"""M2 HCC truth-object attrition, identifier, and filter audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wtbench.revision_bridge_sensitivity import bh_adjust, infer_association
from wtbench.truth_bridge import (
    build_dataset_specs,
    clean_depmap_gene_columns,
    load_config,
    load_expression_for_called_cells,
    load_feature_metadata,
    load_single_feature_calls,
    log_normalize_csr,
    parse_target_gene,
    stringify,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_dependency_subset(path: Path, target_genes: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read required DepMap columns while retaining column-level identifier checks."""
    raw_columns = pd.read_csv(path, nrows=0).columns
    clean_columns = clean_depmap_gene_columns(raw_columns)
    column_map = pd.DataFrame(
        {"raw_column": raw_columns.astype(str), "clean_gene": clean_columns}
    )
    column_map["is_model_id"] = column_map["clean_gene"].eq("ModelID")
    column_map["is_requested_target"] = column_map["clean_gene"].isin(target_genes)
    selected = column_map.loc[
        column_map["is_model_id"] | column_map["is_requested_target"], "raw_column"
    ].tolist()
    frame = pd.read_csv(path, usecols=selected)
    frame.columns = clean_depmap_gene_columns(frame.columns)
    frame = frame.rename(columns={"ModelID": "depmap_model_id"})
    if "depmap_model_id" not in frame:
        raise ValueError("DepMap dependency table lacks ModelID.")
    return frame, column_map


def compute_raw_shift_table(
    normalized,
    calls: pd.DataFrame,
    dependency_row: pd.Series,
    dependency_columns: set[str],
) -> pd.DataFrame:
    control_positions = np.flatnonzero(calls["is_control"].to_numpy(bool))
    if len(control_positions) == 0:
        raise ValueError("No single-feature intergenic controls.")
    control_mean = np.asarray(normalized[control_positions].mean(axis=0)).ravel()
    rows: list[dict[str, Any]] = []
    for target_gene, group in calls.loc[~calls["is_control"]].groupby("target_gene", sort=True):
        positions = group.index.to_numpy(dtype=np.int64)
        target_mean = np.asarray(normalized[positions].mean(axis=0)).ravel()
        endpoint = dependency_row.get(target_gene, np.nan)
        rows.append(
            {
                "target_gene": str(target_gene),
                "n_cells_target": int(len(positions)),
                "n_sgrnas_observed": int(group["feature_call"].nunique()),
                "raw_shift_mean_abs": float(np.mean(np.abs(target_mean - control_mean))),
                "depmap_gene_column_found": str(target_gene) in dependency_columns,
                "depmap_gene_dependency": float(endpoint) if pd.notna(endpoint) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def attrition_rows(
    *,
    cell_line: str,
    n_matrix_barcodes: int,
    n_called_barcodes: int,
    n_single_cells: int,
    n_control_cells: int,
    targets: pd.DataFrame,
    minimum_cells: int,
) -> list[dict[str, Any]]:
    target_cells = int(targets["n_cells_target"].sum())
    final = targets.loc[targets["final_eligible"]]
    stages = [
        ("matrix_barcodes", "", "cell", n_matrix_barcodes, np.nan, "all supplied matrix barcodes"),
        (
            "barcodes_with_protospacer_call",
            "matrix_barcodes",
            "cell",
            n_called_barcodes,
            n_matrix_barcodes - n_called_barcodes,
            "barcode appears in the protospacer call table",
        ),
        (
            "single_feature_cells",
            "barcodes_with_protospacer_call",
            "cell",
            n_single_cells,
            n_called_barcodes - n_single_cells,
            "num_features == 1",
        ),
        (
            "single_feature_controls",
            "single_feature_cells",
            "cell_partition",
            n_control_cells,
            np.nan,
            "parsed target starts with intergenic_chr_",
        ),
        (
            "single_feature_perturbed",
            "single_feature_cells",
            "cell_partition",
            target_cells,
            np.nan,
            "single-feature cells assigned to a non-control target",
        ),
        (
            "assayed_noncontrol_targets",
            "single_feature_perturbed",
            "target",
            int(len(targets)),
            0,
            "distinct parsed target symbols with >=1 single-feature cell",
        ),
        (
            "targets_passing_minimum_cells",
            "assayed_noncontrol_targets",
            "target",
            int(targets["passes_minimum_cells"].sum()),
            int((~targets["passes_minimum_cells"]).sum()),
            f"n_cells_target >= {minimum_cells}",
        ),
        (
            "targets_with_depmap_gene_column",
            "targets_passing_minimum_cells",
            "target",
            int((targets["passes_minimum_cells"] & targets["depmap_gene_column_found"]).sum()),
            int((targets["passes_minimum_cells"] & ~targets["depmap_gene_column_found"]).sum()),
            "target symbol resolves to a DepMap gene column",
        ),
        (
            "targets_with_exact_model_endpoint",
            "targets_with_depmap_gene_column",
            "target",
            int(final.shape[0]),
            int(
                (
                    targets["passes_minimum_cells"]
                    & targets["depmap_gene_column_found"]
                    & ~targets["endpoint_nonmissing"]
                ).sum()
            ),
            "dependency probability is nonmissing for the exact DepMap model",
        ),
        (
            "final_truth_object_perturbed_cells",
            "single_feature_perturbed",
            "cell",
            int(final["n_cells_target"].sum()),
            int(target_cells - final["n_cells_target"].sum()),
            "cells belonging to final endpoint-eligible targets",
        ),
    ]
    return [
        {
            "cell_line": cell_line,
            "stage_order": index + 1,
            "stage": stage,
            "parent_stage": parent_stage,
            "unit": unit,
            "n_retained": retained,
            "n_excluded_from_parent": excluded,
            "rule": rule,
        }
        for index, (stage, parent_stage, unit, retained, excluded, rule) in enumerate(stages)
    ]


def exclusion_reason(row: pd.Series) -> str:
    reasons: list[str] = []
    if not bool(row["passes_minimum_cells"]):
        reasons.append("below_minimum_cells")
    if not bool(row["depmap_gene_column_found"]):
        reasons.append("depmap_gene_column_missing")
    elif not bool(row["endpoint_nonmissing"]):
        reasons.append("exact_model_endpoint_missing")
    return ";".join(reasons) if reasons else "retained"


def process_dataset(
    *,
    spec,
    base_config: dict[str, Any],
    raw_calls: pd.DataFrame,
    dependency: pd.DataFrame,
    dependency_column_map: pd.DataFrame,
    endpoint_object: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    control_prefix = str(base_config["filters"]["control_target_prefix"])
    minimum_cells = int(base_config["filters"]["min_target_cells"])
    barcodes = pd.read_csv(spec.barcodes_path, sep="\t", header=None, names=["cell_barcode"])
    barcodes["cell_barcode"] = stringify(barcodes["cell_barcode"])
    barcode_set = set(barcodes["cell_barcode"].astype(str))
    raw_calls = raw_calls.copy()
    raw_calls["cell_barcode"] = stringify(raw_calls["cell_barcode"])
    aligned_raw = raw_calls.loc[raw_calls["cell_barcode"].isin(barcode_set)].copy()

    single_calls = load_single_feature_calls(spec, control_prefix=control_prefix)
    expression, single_calls, gene_meta = load_expression_for_called_cells(spec, single_calls)
    normalized = log_normalize_csr(
        expression,
        target_sum=float(base_config["metrics"]["normalization_target_sum"]),
    ).tocsr()

    dep_row_frame = dependency.loc[
        dependency["depmap_model_id"].astype(str).eq(spec.depmap_model_id)
    ]
    if len(dep_row_frame) != 1:
        raise ValueError(f"{spec.cell_line} does not have exactly one matching DepMap model row.")
    dependency_row = dep_row_frame.iloc[0]
    dependency_columns = set(dependency.columns) - {"depmap_model_id"}
    targets = compute_raw_shift_table(
        normalized,
        single_calls,
        dependency_row,
        dependency_columns,
    )
    targets.insert(0, "cell_line", spec.cell_line)
    targets.insert(1, "depmap_model_id", spec.depmap_model_id)
    targets["passes_minimum_cells"] = targets["n_cells_target"].ge(minimum_cells)
    targets["endpoint_nonmissing"] = targets["depmap_gene_dependency"].notna()
    targets["final_eligible"] = (
        targets["passes_minimum_cells"]
        & targets["depmap_gene_column_found"]
        & targets["endpoint_nonmissing"]
    )
    targets["exclusion_reason"] = targets.apply(exclusion_reason, axis=1)

    expression_symbols = gene_meta["feature_name"].astype(str)
    expression_counts = expression_symbols.value_counts()
    targets["expression_feature_match_count"] = targets["target_gene"].map(expression_counts).fillna(0).astype(int)

    expected = endpoint_object.loc[endpoint_object["cell_line"].eq(spec.cell_line)].copy()
    observed_set = set(targets.loc[targets["final_eligible"], "target_gene"])
    expected_set = set(expected["target_gene"])
    if observed_set != expected_set:
        raise ValueError(
            f"{spec.cell_line} final attrition target set differs from the frozen endpoint object: "
            f"missing={sorted(expected_set-observed_set)}, extra={sorted(observed_set-expected_set)}"
        )
    validation = targets.loc[targets["final_eligible"], ["target_gene", "raw_shift_mean_abs"]].merge(
        expected[["target_gene", "observed_shift_mean_abs"]],
        on="target_gene",
        validate="one_to_one",
    )
    max_error = float(
        np.max(np.abs(validation["raw_shift_mean_abs"] - validation["observed_shift_mean_abs"]))
    )
    if max_error > 1e-12:
        raise ValueError(f"{spec.cell_line} filter-on raw shift did not exactly reproduce M1: max error={max_error}")

    flow = pd.DataFrame(
        attrition_rows(
            cell_line=spec.cell_line,
            n_matrix_barcodes=len(barcodes),
            n_called_barcodes=aligned_raw["cell_barcode"].nunique(),
            n_single_cells=len(single_calls),
            n_control_cells=int(single_calls["is_control"].sum()),
            targets=targets,
            minimum_cells=minimum_cells,
        )
    )

    duplicate_expression = sorted(expression_counts.loc[expression_counts.gt(1)].index.tolist())
    requested_columns = dependency_column_map.loc[
        dependency_column_map["is_requested_target"], "clean_gene"
    ]
    identifier_rows = [
        ("raw_protospacer_call_rows", len(raw_calls), "count"),
        ("raw_call_duplicate_barcodes", int(raw_calls["cell_barcode"].duplicated().sum()), "must_be_zero"),
        ("raw_call_barcodes_not_in_matrix", int((~raw_calls["cell_barcode"].isin(barcode_set)).sum()), "must_be_zero"),
        ("expression_gene_features", len(gene_meta), "count"),
        ("duplicated_expression_gene_symbols", len(duplicate_expression), "reported_not_silently_dropped"),
        ("duplicated_expression_gene_symbols_overlapping_assayed_targets", int(targets["expression_feature_match_count"].gt(1).sum()), "must_be_zero"),
        ("assayed_targets_missing_expression_symbol", int(targets["expression_feature_match_count"].eq(0).sum()), "reported"),
        ("requested_depmap_gene_columns_with_duplicate_clean_name", int(requested_columns.duplicated().sum()), "must_be_zero"),
        ("assayed_targets_missing_depmap_gene_column", int((~targets["depmap_gene_column_found"]).sum()), "reported"),
        ("assayed_targets_with_exact_model_endpoint_missing", int((targets["depmap_gene_column_found"] & ~targets["endpoint_nonmissing"]).sum()), "reported"),
        ("final_target_set_validation_max_abs_shift_error", max_error, "must_be_le_1e-12"),
    ]
    identifiers = pd.DataFrame(
        [
            {
                "cell_line": spec.cell_line,
                "check": check,
                "value": value,
                "policy": policy,
                "details": ",".join(duplicate_expression) if check == "duplicated_expression_gene_symbols" else "",
            }
            for check, value, policy in identifier_rows
        ]
    )
    return targets, flow, identifiers, validation.assign(cell_line=spec.cell_line)


def filter_comparison(
    target_details: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    comparison = config["filter_comparison"]
    for context_index, (cell_line, context) in enumerate(
        target_details.groupby("cell_line", sort=True)
    ):
        for filter_index, (label, mask) in enumerate(
            [
                ("minimum_cell_filter_off", context["endpoint_nonmissing"]),
                ("minimum_cell_filter_on", context["final_eligible"]),
            ]
        ):
            subset = context.loc[mask].copy()
            row = infer_association(
                analysis_id=label,
                cell_line=cell_line,
                x=subset["raw_shift_mean_abs"].to_numpy(float),
                y=subset["depmap_gene_dependency"].to_numpy(float),
                bootstrap_replicates=int(comparison["bootstrap_replicates"]),
                permutation_replicates=int(comparison["endpoint_label_permutations"]),
                bootstrap_seed=int(comparison["bootstrap_seed"]) + context_index * 10 + filter_index,
                permutation_seed=int(comparison["permutation_seed"]) + context_index * 10 + filter_index,
            )
            row["minimum_cell_filter"] = "off" if label.endswith("off") else "on"
            row["minimum_cells"] = 1 if label.endswith("off") else int(config["filters"]["minimum_perturbed_cells"])
            row["included_targets"] = ",".join(sorted(subset["target_gene"]))
            row["low_coverage_targets_included_only_when_off"] = ",".join(
                sorted(context.loc[context["endpoint_nonmissing"] & ~context["passes_minimum_cells"], "target_gene"])
            )
            rows.append(row)
    output = pd.DataFrame(rows)
    output["permutation_qvalue_bh_within_filter"] = output.groupby(
        "minimum_cell_filter"
    )["permutation_pvalue_two_sided"].transform(bh_adjust)
    return output


def preprocessing_registry(base_config: dict[str, Any], specs: list[Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        entries = [
            ("readout", "cell_line", spec.cell_line),
            ("readout", "readout_day", 14),
            ("endpoint", "depmap_model_id", spec.depmap_model_id),
            ("cell_filter", "single_feature_rule", "num_features == 1"),
            ("control", "definition", "target_gene starts with intergenic_chr_"),
            ("control", "matching", "same context; all eligible intergenic controls; no further lane/batch matching"),
            ("target_filter", "minimum_perturbed_cells", base_config["filters"]["min_target_cells"]),
            ("gene_filter", "feature_type", "Gene Expression"),
            ("gene_filter", "hvg_or_expression_filter", "none"),
            ("normalization", "target_sum", base_config["metrics"]["normalization_target_sum"]),
            ("normalization", "transform", "log1p after per-cell total-count scaling"),
            ("category", "rank_scope", "within context"),
            ("category", "cutoffs", "percentile rank <=0.25 or >=0.75"),
        ]
        rows.extend(
            {
                "cell_line": spec.cell_line,
                "stage": stage,
                "parameter": parameter,
                "value": value,
            }
            for stage, parameter, value in entries
        )
    return pd.DataFrame(rows)


def context_qualification_summary(
    legacy: pd.DataFrame,
    endpoint_candidates: pd.DataFrame,
    endpoint_object: pd.DataFrame,
    gate: dict[str, Any],
) -> pd.DataFrame:
    output = legacy[[
        "dataset_id",
        "context",
        "cell_line",
        "evidence_layer",
        "n_targets_matched_depmap",
        "spearman_rho",
        "spearman_bootstrap_ci_low",
        "spearman_bootstrap_ci_high",
        "spearman_permutation_pvalue",
    ]].copy()
    output = output.rename(
        columns={
            "n_targets_matched_depmap": "raw_n_targets",
            "spearman_rho": "raw_spearman_rho",
            "spearman_bootstrap_ci_low": "raw_bootstrap_ci_low",
            "spearman_bootstrap_ci_high": "raw_bootstrap_ci_high",
            "spearman_permutation_pvalue": "raw_permutation_pvalue",
        }
    )
    output["legacy_raw_gate_pass"] = (
        output["raw_spearman_rho"].ge(float(gate["minimum_spearman_rho"]))
        & output["raw_bootstrap_ci_low"].gt(float(gate["bootstrap_ci_lower_must_exceed"]))
        & output["raw_permutation_pvalue"].lt(float(gate["permutation_p_max"]))
    )
    output["legacy_raw_gate_failure"] = ""
    for index, row in output.iterrows():
        failures: list[str] = []
        if row["raw_spearman_rho"] < float(gate["minimum_spearman_rho"]):
            failures.append("rho_below_0.30")
        if row["raw_bootstrap_ci_low"] <= float(gate["bootstrap_ci_lower_must_exceed"]):
            failures.append("ci_includes_zero")
        if row["raw_permutation_pvalue"] >= float(gate["permutation_p_max"]):
            failures.append("permutation_p_not_below_0.05")
        output.at[index, "legacy_raw_gate_failure"] = ";".join(failures)

    corrected = endpoint_candidates.loc[
        endpoint_candidates["candidate"].eq("noise_corrected_primary"),
        ["cell_line", "n_targets", "rho_with_dependency", "bootstrap_ci_low", "bootstrap_ci_high", "permutation_qvalue"],
    ].rename(
        columns={
            "n_targets": "corrected_n_targets",
            "rho_with_dependency": "corrected_spearman_rho",
            "bootstrap_ci_low": "corrected_bootstrap_ci_low",
            "bootstrap_ci_high": "corrected_bootstrap_ci_high",
            "permutation_qvalue": "corrected_permutation_qvalue",
        }
    )
    role_map = endpoint_object.drop_duplicates("cell_line").set_index("cell_line")["context_role"]
    corrected["sampling_aware_role"] = corrected["cell_line"].map(role_map)
    output = output.merge(corrected, on="cell_line", how="left", validate="many_to_one")
    output["sampling_aware_role"] = output["sampling_aware_role"].fillna(
        "not_yet_sampling_aware_qualified"
    )
    output["revised_full_audit_eligibility"] = output["sampling_aware_role"].map(
        {
            "qualified_primary_context": "eligible_after_contract_validation",
            "sensitivity_boundary_context": "sensitivity_only",
            "not_yet_sampling_aware_qualified": "pending_sampling_aware_M5_audit",
        }
    )
    return output.sort_values(["evidence_layer", "dataset_id", "context"]).reset_index(drop=True)


def build_flow_figure(
    flow: pd.DataFrame,
    filters: pd.DataFrame,
    output_path: Path,
) -> None:
    preferred = ["HCC38", "HCC1143"]
    contexts = [name for name in preferred if name in set(flow["cell_line"])]
    contexts.extend(name for name in flow["cell_line"].unique() if name not in contexts)
    fig, axes = plt.subplots(1, len(contexts), figsize=(6.2 * len(contexts), 7.5), squeeze=False)
    target_stages = [
        "assayed_noncontrol_targets",
        "targets_passing_minimum_cells",
        "targets_with_depmap_gene_column",
        "targets_with_exact_model_endpoint",
    ]
    for column, cell_line in enumerate(contexts):
        axis = axes[0, column]
        axis.axis("off")
        context = flow.loc[flow["cell_line"].eq(cell_line)].set_index("stage")
        cell_lines = [
            f"Matrix barcodes\n{int(context.loc['matrix_barcodes', 'n_retained']):,}",
            f"With protospacer call\n{int(context.loc['barcodes_with_protospacer_call', 'n_retained']):,}",
            f"Single-feature cells\n{int(context.loc['single_feature_cells', 'n_retained']):,}",
            f"Controls / perturbed\n{int(context.loc['single_feature_controls', 'n_retained']):,} / {int(context.loc['single_feature_perturbed', 'n_retained']):,}",
        ]
        target_lines = [
            "Assayed targets\n" + str(int(context.loc[target_stages[0], "n_retained"])),
            "n ≥ 20\n" + str(int(context.loc[target_stages[1], "n_retained"])),
            "DepMap column\n" + str(int(context.loc[target_stages[2], "n_retained"])),
            "Exact-model endpoint\n" + str(int(context.loc[target_stages[3], "n_retained"])),
        ]
        y_values = np.linspace(0.92, 0.55, len(cell_lines))
        for y, label in zip(y_values, cell_lines):
            axis.text(
                0.5,
                y,
                label,
                ha="center",
                va="center",
                fontsize=10,
                bbox={"boxstyle": "round,pad=0.35", "facecolor": "#E8F1F8", "edgecolor": "#477998"},
            )
        for upper, lower in zip(y_values[:-1], y_values[1:]):
            axis.annotate("", xy=(0.5, lower + 0.045), xytext=(0.5, upper - 0.045), arrowprops={"arrowstyle": "->", "color": "#555555"})
        y_values = np.linspace(0.42, 0.12, len(target_lines))
        for y, label in zip(y_values, target_lines):
            axis.text(
                0.5,
                y,
                label,
                ha="center",
                va="center",
                fontsize=10,
                bbox={"boxstyle": "round,pad=0.35", "facecolor": "#F5EAD7", "edgecolor": "#9A6B32"},
            )
        for upper, lower in zip(y_values[:-1], y_values[1:]):
            axis.annotate("", xy=(0.5, lower + 0.038), xytext=(0.5, upper - 0.038), arrowprops={"arrowstyle": "->", "color": "#555555"})
        comparison = filters.loc[filters["cell_line"].eq(cell_line)].set_index("minimum_cell_filter")
        off = comparison.loc["off"]
        on = comparison.loc["on"]
        axis.set_title(
            f"{cell_line}\nraw bridge: filter off ρ={off['spearman_rho']:.3f} (n={int(off['n_targets'])}); "
            f"on ρ={on['spearman_rho']:.3f} (n={int(on['n_targets'])})",
            fontsize=11,
        )
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    fig.savefig(output_path.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def run(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    base_config_path = PROJECT_ROOT / config["inputs"]["base_truth_config"]
    base_config = load_config(base_config_path)
    specs = build_dataset_specs(base_config)
    endpoint_path = PROJECT_ROOT / config["inputs"]["endpoint_object"]
    endpoint_object = pd.read_csv(endpoint_path, sep="\t")

    raw_calls_by_context: dict[str, pd.DataFrame] = {}
    all_targets: set[str] = set()
    for spec in specs:
        raw_calls = pd.read_csv(spec.protospacer_calls_path)
        raw_calls_by_context[spec.cell_line] = raw_calls
        single = raw_calls.loc[pd.to_numeric(raw_calls["num_features"], errors="coerce").eq(1)].copy()
        single["target_gene"] = single["feature_call"].map(parse_target_gene).astype(str)
        all_targets.update(
            target for target in single["target_gene"].unique() if not target.startswith(base_config["filters"]["control_target_prefix"])
        )

    dependency_path = PROJECT_ROOT / config["inputs"]["depmap_dependency"]
    dependency, dependency_column_map = load_dependency_subset(dependency_path, all_targets)

    target_parts: list[pd.DataFrame] = []
    flow_parts: list[pd.DataFrame] = []
    identifier_parts: list[pd.DataFrame] = []
    validation_parts: list[pd.DataFrame] = []
    for spec in specs:
        targets, flow, identifiers, validation = process_dataset(
            spec=spec,
            base_config=base_config,
            raw_calls=raw_calls_by_context[spec.cell_line],
            dependency=dependency,
            dependency_column_map=dependency_column_map,
            endpoint_object=endpoint_object,
        )
        target_parts.append(targets)
        flow_parts.append(flow)
        identifier_parts.append(identifiers)
        validation_parts.append(validation)

    target_details = pd.concat(target_parts, ignore_index=True).sort_values(["cell_line", "target_gene"])
    flow = pd.concat(flow_parts, ignore_index=True).sort_values(["cell_line", "stage_order"])
    identifiers = pd.concat(identifier_parts, ignore_index=True).sort_values(["cell_line", "check"])
    validation = pd.concat(validation_parts, ignore_index=True).sort_values(["cell_line", "target_gene"])
    comparison = filter_comparison(target_details, config)
    registry = preprocessing_registry(base_config, specs)
    legacy_context_path = PROJECT_ROOT / config["inputs"]["legacy_context_bridge_summary"]
    endpoint_candidate_path = PROJECT_ROOT / config["inputs"]["endpoint_candidate_summary"]
    context_qualification = context_qualification_summary(
        pd.read_csv(legacy_context_path, sep="\t"),
        pd.read_csv(endpoint_candidate_path, sep="\t"),
        endpoint_object,
        config["legacy_raw_gate"],
    )

    output_root.mkdir(parents=True, exist_ok=True)
    target_details.to_csv(output_root / "target_eligibility_detail.tsv", sep="\t", index=False)
    flow.to_csv(output_root / "attrition_flow.tsv", sep="\t", index=False)
    identifiers.to_csv(output_root / "identifier_audit.tsv", sep="\t", index=False)
    validation.to_csv(output_root / "frozen_target_recalculation_validation.tsv", sep="\t", index=False)
    comparison.to_csv(output_root / "minimum_cell_filter_on_off_bridge.tsv", sep="\t", index=False)
    registry.to_csv(output_root / "preprocessing_registry.tsv", sep="\t", index=False)
    context_qualification.to_csv(
        output_root / "context_qualification_summary.tsv", sep="\t", index=False
    )
    (output_root / "selection_chronology.json").write_text(
        json.dumps(config["chronology"], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    depmap_release = {
        "registry_date": config["frozen_date"],
        **config["depmap_release"],
        "primary_endpoint": {
            "local_path": config["inputs"]["depmap_dependency"],
            "filename": dependency_path.name,
            "file_size_bytes": dependency_path.stat().st_size,
            "sha256": sha256_file(dependency_path),
            "row_identifier": "ModelID",
            "column_identifier": "Gene (HUGO symbol with Entrez ID in the raw header)",
            "direction": "larger probability denotes stronger dependency",
            "depmap_model_ids": {
                spec.cell_line: spec.depmap_model_id for spec in specs
            },
        },
        "primary_form_decision": "CRISPR dependency probability is primary; CRISPR gene effect and DEMETER2 RNAi are sensitivity endpoints.",
    }
    (output_root / "depmap_release_registry.json").write_text(
        json.dumps(depmap_release, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    build_flow_figure(flow, comparison, output_root / "attrition_flow.png")

    report_lines = [
        "# M2: Target eligibility and attrition audit",
        "",
        "## Key findings",
        "",
        "- Eligibility did not use observed shift magnitude, dependency magnitude, or model output.",
        "- The only readout-based target filter required at least 20 single-feature perturbed cells per target; the table also reports raw bridges with the filter on/off.",
        "- Primary contexts and 25/75 cutoffs were benchmark-development choices, not preregistered before all observed-data/model exploration; the revision sampling-aware object was frozen before revised model rescoring.",
        "",
        "## Target attrition",
        "",
        "| context | assayed | n>=20 | endpoint nonmissing | final | excluded targets |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for cell_line, context in target_details.groupby("cell_line", sort=True):
        excluded = context.loc[~context["final_eligible"], ["target_gene", "n_cells_target", "exclusion_reason"]]
        excluded_text = "; ".join(
            f"{row.target_gene} (n={int(row.n_cells_target)}, {row.exclusion_reason})"
            for row in excluded.itertuples()
        )
        report_lines.append(
            f"| {cell_line} | {len(context)} | {int(context['passes_minimum_cells'].sum())} | "
            f"{int((context['passes_minimum_cells'] & context['endpoint_nonmissing']).sum())} | "
            f"{int(context['final_eligible'].sum())} | {excluded_text} |"
        )
    report_lines.extend(
        [
            "",
            "## Minimum-cell filter on/off",
            "",
            "| context | filter | n | rho | 95% CI | permutation q | low-coverage targets added when off |",
            "| --- | --- | ---: | ---: | --- | ---: | --- |",
        ]
    )
    for row in comparison.sort_values(["cell_line", "minimum_cell_filter"]).itertuples():
        report_lines.append(
            f"| {row.cell_line} | {row.minimum_cell_filter} | {row.n_targets} | {row.spearman_rho:.3f} | "
            f"[{row.bootstrap_ci_low:.3f}, {row.bootstrap_ci_high:.3f}] | "
            f"{row.permutation_qvalue_bh_within_filter:.4f} | {row.low_coverage_targets_included_only_when_off} |"
        )
    report_lines.extend(
        [
            "",
            "## All-context qualification status",
            "",
            "The legacy raw-shift gate is retained only as a descriptive audit. External contexts are not promoted until M5 repeats sampling-aware qualification.",
            "",
            "| context | n | raw rho | 95% CI | P | legacy gate | revised role |",
            "| --- | ---: | ---: | --- | ---: | --- | --- |",
        ]
    )
    for row in context_qualification.itertuples():
        report_lines.append(
            f"| {row.context} | {int(row.raw_n_targets)} | {row.raw_spearman_rho:.3f} | "
            f"[{row.raw_bootstrap_ci_low:.3f}, {row.raw_bootstrap_ci_high:.3f}] | "
            f"{row.raw_permutation_pvalue:.4f} | {'pass' if row.legacy_raw_gate_pass else 'fail: ' + row.legacy_raw_gate_failure} | "
            f"{row.sampling_aware_role} |"
        )
    report_lines.extend(
        [
            "",
            "## Preprocessing contract",
            "",
            f"- Cell filter: `num_features == 1`; controls are parsed targets beginning with `{base_config['filters']['control_target_prefix']}`.",
            f"- Expression: all {int(identifiers.loc[identifiers['check'].eq('expression_gene_features'), 'value'].iloc[0])} `Gene Expression` features; no HVG filter.",
            f"- Normalization: per-cell total-count scaling to {base_config['metrics']['normalization_target_sum']:.0f}, then `log1p`.",
            "- Control reference: all single-feature intergenic controls in the same cell-line context; no further lane/batch matching.",
            "- Target parser: substring before the first `_sgRNA`; exact DepMap model IDs are recorded in `preprocessing_registry.tsv`.",
            f"- Primary endpoint: {config['depmap_release']['release']} `CRISPRGeneDependency.csv` (Post-Chronos dependency probability); HCC38 `{specs[0].depmap_model_id}`, HCC1143 `{specs[1].depmap_model_id}`.",
            "- The official release metadata names the Chronos pipeline but does not expose a semantic package version; `depmap_release_registry.json` records this explicitly instead of inventing one.",
            "",
            "## Interpretation boundary",
            "",
            "Filter-off uses raw shift because the M1 matched-size correction was frozen only for eligible targets. It tests whether the n>=20 rule alone manufactures the raw bridge; it is not a replacement sampling-corrected endpoint analysis.",
            "",
        ]
    )
    (output_root / "m2_attrition_report.md").write_text("\n".join(report_lines), encoding="utf-8")

    input_paths = [
        config_path,
        base_config_path,
        endpoint_path,
        PROJECT_ROOT / config["inputs"]["endpoint_object_manifest"],
        endpoint_candidate_path,
        legacy_context_path,
        dependency_path,
    ]
    for spec in specs:
        input_paths.extend(
            [spec.matrix_path, spec.barcodes_path, spec.features_path, spec.protospacer_calls_path]
        )
    output_paths = sorted(
        path for path in output_root.iterdir() if path.is_file() and path.name != "run_manifest.json"
    )
    manifest = {
        "audit_id": config["audit_id"],
        "status": config["status"],
        "revised_model_scores_read": False,
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": sha256_file(path)}
            for path in input_paths
        ],
        "outputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": sha256_file(path)}
            for path in output_paths
        ],
    }
    (output_root / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest
