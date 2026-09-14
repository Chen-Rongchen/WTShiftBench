#!/usr/bin/env python
"""Consolidate existing robustness assets and freeze the M1_FINAL report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_combined_robustness(output_root: Path) -> pd.DataFrame:
    inference_path = output_root / "bridge_inference_summary.tsv"
    control_path = PROJECT_ROOT / "reports/truth_driven_bridge/sensitivity/control_subsample_summary.tsv"
    anchor_path = PROJECT_ROOT / "reports/truth_driven_bridge/sensitivity/leave_anchor_out_summary.tsv"
    inference = pd.read_csv(inference_path, sep="\t")
    control = pd.read_csv(control_path, sep="\t")
    anchor = pd.read_csv(anchor_path, sep="\t", comment="#")

    rows: list[dict[str, object]] = []
    shift_rows = inference.loc[
        inference["analysis_id"].eq("raw_observed_shift")
        | inference["analysis_id"].str.startswith("alternative_")
    ]
    for _, row in shift_rows.iterrows():
        rows.append(
            {
                "evidence_type": "shift_metric_definition",
                "cell_line": row["cell_line"],
                "analysis": row["analysis_id"],
                "n_targets": int(row["n_targets"]),
                "estimate": row["spearman_rho"],
                "interval_low": row["bootstrap_ci_low"],
                "interval_high": row["bootstrap_ci_high"],
                "interval_type": "target_bootstrap_95pct",
                "source_file": str(inference_path.relative_to(PROJECT_ROOT)),
                "note": "dependency-probability endpoint",
            }
        )

    control = control.loc[control["depmap_endpoint"].eq("depmap_gene_dependency")]
    target_counts = {"HCC38": 47, "HCC1143": 48}
    for _, row in control.iterrows():
        rows.append(
            {
                "evidence_type": "control_cell_subsampling",
                "cell_line": row["cell_line"],
                "analysis": row["truth_metric"],
                "n_targets": target_counts[str(row["cell_line"])],
                "estimate": row["spearman_aligned_mean"],
                "interval_low": row["spearman_aligned_q025"],
                "interval_high": row["spearman_aligned_q975"],
                "interval_type": "24_replicate_interval",
                "source_file": str(control_path.relative_to(PROJECT_ROOT)),
                "note": f"control subsample n={int(row['n_replicates'])} replicates",
            }
        )

    anchor = anchor.loc[
        anchor["removed"].isin(["none", "all_four_anchors", "jackknife_min", "jackknife_max"])
    ]
    for _, row in anchor.iterrows():
        rows.append(
            {
                "evidence_type": "anchor_influence",
                "cell_line": row["context"],
                "analysis": row["removed"],
                "n_targets": int(row["n_targets"]),
                "estimate": row["spearman_rho"],
                "interval_low": np.nan,
                "interval_high": np.nan,
                "interval_type": "not_applicable",
                "source_file": str(anchor_path.relative_to(PROJECT_ROOT)),
                "note": f"rho_delta={row['rho_delta']:.6f}",
            }
        )

    combined = pd.DataFrame(rows).sort_values(
        ["evidence_type", "cell_line", "analysis"]
    )
    combined.to_csv(output_root / "combined_robustness_summary.tsv", sep="\t", index=False)
    return combined


def build_attrition_tables(output_root: Path) -> None:
    targets = pd.read_csv(
        output_root / "target_level_covariates_and_corrected_shift.tsv",
        sep="\t",
    )
    rows: list[dict[str, object]] = []
    for cell_line, context in targets.groupby("cell_line"):
        for depth in [20, 25, 50, 100]:
            for status, subset in [
                ("retained", context.loc[context["n_cells_target"].ge(depth)]),
                ("excluded", context.loc[context["n_cells_target"].lt(depth)]),
            ]:
                rows.append(
                    {
                        "cell_line": cell_line,
                        "depth": depth,
                        "status": status,
                        "n_targets": len(subset),
                        "target_genes": ",".join(sorted(subset["target_gene"])),
                        "median_observed_shift": subset["observed_shift_mean_abs"].median(),
                        "min_observed_shift": subset["observed_shift_mean_abs"].min(),
                        "max_observed_shift": subset["observed_shift_mean_abs"].max(),
                        "median_dependency": subset["depmap_gene_dependency"].median(),
                        "min_dependency": subset["depmap_gene_dependency"].min(),
                        "max_dependency": subset["depmap_gene_dependency"].max(),
                    }
                )
    pd.DataFrame(rows).to_csv(
        output_root / "equal_n_attrition_summary.tsv",
        sep="\t",
        index=False,
    )
    fixed = targets.loc[targets["n_cells_target"].ge(100), [
        "cell_line",
        "target_gene",
        "n_cells_target",
        "observed_shift_mean_abs",
        "noise_corrected_shift",
        "depmap_gene_dependency",
    ]].sort_values(["cell_line", "target_gene"])
    fixed.to_csv(output_root / "fixed_cohort_targets.tsv", sep="\t", index=False)


def write_final_report(output_root: Path, combined: pd.DataFrame) -> Path:
    core_report = (output_root / "m1_report.md").read_text(encoding="utf-8")
    control = combined.loc[
        combined["evidence_type"].eq("control_cell_subsampling")
        & combined["analysis"].eq("real_shift_mean_abs")
    ]
    anchors = combined.loc[
        combined["evidence_type"].eq("anchor_influence")
        & combined["analysis"].eq("all_four_anchors")
    ]
    lines = [
        "# M1_FINAL",
        "",
        "Status: `FINAL`. A002 corrects implementation after initial results; outcome awareness is documented publicly.",
        "",
        core_report,
        "## Recovered existing robustness evidence",
        "",
        "| evidence | context | estimate | interval/change |",
        "| --- | --- | ---: | --- |",
    ]
    for _, row in control.sort_values("cell_line").iterrows():
        lines.append(
            f"| 500-control subsampling | {row['cell_line']} | {row['estimate']:.3f} | "
            f"[{row['interval_low']:.3f}, {row['interval_high']:.3f}] across 24 replicates |"
        )
    for _, row in anchors.sort_values("cell_line").iterrows():
        lines.append(
            f"| remove all four original anchors | {row['cell_line']} | {row['estimate']:.3f} | "
            f"{row['note']} |"
        )
    lines.extend(
        [
            "",
            "Complete alternative-shift, control-subsampling, and anchor-influence values are in combined_robustness_summary.tsv.",
            "Retained/excluded lists and distributions for each equal-n threshold are in equal_n_attrition_summary.tsv; fixed-cohort membership is in fixed_cohort_targets.tsv.",
            "",
            "## M1_FINAL decision",
            "",
            "- Cell-count structure substantially amplifies raw association; raw shift cannot remain an unqualified primary endpoint statistic.",
            "- Under prespecified equal-n and matched-control null analyses, finite sampling does not fully reproduce raw association.",
            "- HCC38 partial-rank and OLS/HC3 analyses do not support independent association after controlling log cell count; HCC1143 evidence is stronger but not fully consistent across model forms.",
            "- The frozen dual-context Gate returns STOP_AND_REASSESS; select and freeze a corrected endpoint object before model scoring.",
            "- Low recovered cell count is described as consistent with depletion/reduced recovery, not demonstrated cell death or a causal mechanism.",
            "",
        ]
    )
    path = output_root / "M1_FINAL.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_manifest(output_root: Path, final_report: Path) -> None:
    input_paths = [
        PROJECT_ROOT / "src/wtbench/revision_bridge_sensitivity.py",
        PROJECT_ROOT / "scripts/revision/run_m1_bridge_sensitivity.py",
        PROJECT_ROOT / "scripts/revision/finalize_m1_outputs.py",
        PROJECT_ROOT / "configs/revision/revision_analysis_registry_v1.json",
        PROJECT_ROOT / "configs/revision/amendment_001_m1_statistical_clarifications.json",
        PROJECT_ROOT / "configs/revision/amendment_002_m1_code_audit.json",
        PROJECT_ROOT / "reports/truth_driven_bridge/sensitivity/control_subsample_summary.tsv",
        PROJECT_ROOT / "reports/truth_driven_bridge/sensitivity/leave_anchor_out_summary.tsv",
        output_root / "run_manifest.json",
    ]
    output_paths = sorted(
        path
        for path in output_root.iterdir()
        if path.is_file() and path.name != "m1_final_manifest.json"
    )
    payload = {
        "status": "M1_FINAL",
        "date": "2026-09-04",
        "final_report": str(final_report.relative_to(PROJECT_ROOT)),
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": sha256_file(path)}
            for path in input_paths
        ],
        "outputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": sha256_file(path)}
            for path in output_paths
        ],
    }
    (output_root / "m1_final_manifest.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        default="reports/revision/m1_bridge_confounding",
    )
    args = parser.parse_args()
    output_root = PROJECT_ROOT / args.output_root
    combined = build_combined_robustness(output_root)
    build_attrition_tables(output_root)
    final_report = write_final_report(output_root, combined)
    write_manifest(output_root, final_report)
    print(f"M1_FINAL generated: {final_report}")


if __name__ == "__main__":
    main()
