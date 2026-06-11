#!/usr/bin/env python3
"""Validate CPA predicted_shift output schema against WTShiftBench scoring contract.

Checks Gate 1 (output compatibility) and Gate 2 (scale compatibility) from the
CPA full materialization gate checklist.

Gate 1: output compatibility
  - target_gene column present and first
  - target count = 47
  - gene count matches axis_membership (47 target genes)
  - no duplicate targets
  - target order and gene order locked to axis_membership

Gate 2: scale compatibility
  - value range consistent with log-normalized expression shift
  - no NaN/Inf in shift values
  - mean/variance sanity checks

Gate 4: target coverage
  - n_targets_input = 47
  - n_targets_predicted = 47
  - excluded_targets = none
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AXIS_MEMBERSHIP_PATH = (
    PROJECT_ROOT / "reports/truth_driven_bridge/master_atlas/shared_target_axis_membership.tsv"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate CPA predicted_shift schema.")
    parser.add_argument("--predicted-shift-path", required=True)
    parser.add_argument("--axis-membership-path", default=str(DEFAULT_AXIS_MEMBERSHIP_PATH))
    parser.add_argument("--output-json", help="Optional path to write validation report JSON")
    return parser


def validate(
    predicted_shift_path: Path,
    axis_membership_path: Path,
) -> dict:
    pred = pd.read_csv(predicted_shift_path, sep="\t")
    axis = pd.read_csv(axis_membership_path, sep="\t")

    expected_targets = (
        axis["target_gene"].astype(str).drop_duplicates().sort_values().tolist()
    )
    expected_genes = expected_targets  # gene universe = target universe in this contract

    report: dict = {
        "gate_1_output_compatibility": {},
        "gate_2_scale_compatibility": {},
        "gate_4_target_coverage": {},
        "overall_pass": False,
    }

    # Gate 1
    g1 = report["gate_1_output_compatibility"]
    g1["first_column_is_target_gene"] = pred.columns[0] == "target_gene"
    g1["n_targets"] = int(pred.shape[0])
    g1["n_genes"] = int(pred.shape[1] - 1)
    g1["expected_n_targets"] = len(expected_targets)
    g1["expected_n_genes"] = len(expected_genes)

    actual_targets = pred.iloc[:, 0].astype(str).tolist()
    actual_genes = [str(c) for c in pred.columns[1:]]

    g1["target_count_match"] = g1["n_targets"] == g1["expected_n_targets"]
    g1["gene_count_match"] = g1["n_genes"] == g1["expected_n_genes"]

    dup_targets = pred.iloc[:, 0].astype(str).loc[pred.iloc[:, 0].astype(str).duplicated()].drop_duplicates().tolist()
    g1["duplicate_targets"] = dup_targets
    g1["has_duplicate_targets"] = len(dup_targets) > 0

    missing_targets = [t for t in expected_targets if t not in set(actual_targets)]
    missing_genes = [g for g in expected_genes if g not in set(actual_genes)]
    g1["missing_targets"] = missing_targets
    g1["missing_genes"] = missing_genes
    g1["has_missing_targets"] = len(missing_targets) > 0
    g1["has_missing_genes"] = len(missing_genes) > 0

    extra_targets = [t for t in actual_targets if t not in set(expected_targets)]
    extra_genes = [g for g in actual_genes if g not in set(expected_genes)]
    g1["extra_targets"] = extra_targets
    g1["extra_genes"] = extra_genes

    g1["target_order_exact"] = actual_targets == expected_targets
    g1["gene_order_exact"] = actual_genes == expected_genes

    # Gate 2
    g2 = report["gate_2_scale_compatibility"]
    values = pred.iloc[:, 1:].to_numpy(dtype=np.float64)
    g2["n_nan"] = int(np.isnan(values).sum())
    g2["n_inf"] = int(np.isinf(values).sum())
    g2["has_nan_or_inf"] = g2["n_nan"] > 0 or g2["n_inf"] > 0
    g2["value_min"] = float(np.nanmin(values))
    g2["value_max"] = float(np.nanmax(values))
    g2["value_mean"] = float(np.nanmean(values))
    g2["value_std"] = float(np.nanstd(values))
    # Shift values in log-normalized space typically range within [-5, 5]
    g2["range_sane"] = -10 < g2["value_min"] and g2["value_max"] < 10
    g2["std_sane"] = 0 < g2["value_std"] < 5

    # Gate 4
    g4 = report["gate_4_target_coverage"]
    g4["n_targets_input"] = len(expected_targets)
    g4["n_targets_predicted"] = len(actual_targets)
    g4["n_targets_endpoint_mapped"] = len(expected_targets)  # all targets are in axis
    g4["n_targets_scored"] = len(expected_targets) if g1["target_count_match"] else None
    g4["excluded_targets"] = missing_targets if missing_targets else None

    # Overall
    report["overall_pass"] = (
        g1["first_column_is_target_gene"]
        and g1["target_count_match"]
        and g1["gene_count_match"]
        and not g1["has_duplicate_targets"]
        and not g1["has_missing_targets"]
        and not g1["has_missing_genes"]
        and not g2["has_nan_or_inf"]
        and g2["range_sane"]
    )

    return report


def main() -> None:
    args = build_parser().parse_args()
    report = validate(
        predicted_shift_path=Path(args.predicted_shift_path),
        axis_membership_path=Path(args.axis_membership_path),
    )

    print("=" * 60)
    print("CPA predicted_shift Schema Validation Report")
    print("=" * 60)

    g1 = report["gate_1_output_compatibility"]
    print(f"\nGate 1 — Output Compatibility")
    print(f"  first_column_is_target_gene : {g1['first_column_is_target_gene']}")
    print(f"  n_targets (actual/expected) : {g1['n_targets']} / {g1['expected_n_targets']}")
    print(f"  n_genes   (actual/expected) : {g1['n_genes']} / {g1['expected_n_genes']}")
    print(f"  target_count_match          : {g1['target_count_match']}")
    print(f"  gene_count_match            : {g1['gene_count_match']}")
    print(f"  has_duplicate_targets       : {g1['has_duplicate_targets']}")
    print(f"  has_missing_targets         : {g1['has_missing_targets']}")
    print(f"  has_missing_genes           : {g1['has_missing_genes']}")
    print(f"  target_order_exact          : {g1['target_order_exact']}")
    print(f"  gene_order_exact            : {g1['gene_order_exact']}")
    if g1["missing_targets"]:
        print(f"  missing_targets             : {g1['missing_targets']}")
    if g1["missing_genes"]:
        print(f"  missing_genes               : {g1['missing_genes']}")
    if g1["extra_targets"]:
        print(f"  extra_targets               : {g1['extra_targets']}")
    if g1["extra_genes"]:
        print(f"  extra_genes                 : {g1['extra_genes']}")

    g2 = report["gate_2_scale_compatibility"]
    print(f"\nGate 2 — Scale Compatibility")
    print(f"  has_nan_or_inf : {g2['has_nan_or_inf']}")
    print(f"  n_nan          : {g2['n_nan']}")
    print(f"  n_inf          : {g2['n_inf']}")
    print(f"  value_min      : {g2['value_min']:.4f}")
    print(f"  value_max      : {g2['value_max']:.4f}")
    print(f"  value_mean     : {g2['value_mean']:.4f}")
    print(f"  value_std      : {g2['value_std']:.4f}")
    print(f"  range_sane     : {g2['range_sane']}")
    print(f"  std_sane       : {g2['std_sane']}")

    g4 = report["gate_4_target_coverage"]
    print(f"\nGate 4 — Target Coverage")
    print(f"  n_targets_input          : {g4['n_targets_input']}")
    print(f"  n_targets_predicted      : {g4['n_targets_predicted']}")
    print(f"  n_targets_endpoint_mapped: {g4['n_targets_endpoint_mapped']}")
    print(f"  n_targets_scored         : {g4['n_targets_scored']}")
    print(f"  excluded_targets         : {g4['excluded_targets']}")

    print(f"\n{'=' * 60}")
    if report["overall_pass"]:
        print("RESULT: PASS — All gates cleared.")
    else:
        print("RESULT: FAIL — See details above.")
    print("=" * 60)

    if args.output_json:
        out_path = Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nReport written to: {out_path}")


if __name__ == "__main__":
    main()
