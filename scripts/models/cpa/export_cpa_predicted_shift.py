#!/usr/bin/env python3
"""Export CPA predicted_shift to WTShiftBench scorer-ready format.

Reads CPA raw predicted_shift (full gene universe), aligns it to the
shared_target_axis_membership contract (target order + gene order),
and writes scorer-ready TSV plus prediction manifest JSON.

This script is the bridge between CPA model output and WTShiftBench scoring.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Import from existing export infrastructure
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from wtbench.hcc_prediction_export import (
    PROJECT_ROOT,
    DEFAULT_AXIS_MEMBERSHIP_PATH,
    DEFAULT_CONTRACT_PATH,
    export_external_hcc_prediction,
    RawPredictionSource,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export CPA predicted_shift to scorer-ready format.")
    parser.add_argument("--cell-line", required=True, choices=["HCC38", "HCC1143"])
    parser.add_argument("--model-id", default="cpa_v0.8.8")
    parser.add_argument("--model-version", default="0.8.8")
    parser.add_argument("--object-role", default="candidate", choices=["candidate", "null", "baseline"])
    parser.add_argument(
        "--raw-prediction-path",
        required=True,
        help="Path to CPA raw predicted_shift.tsv.gz (full gene universe)",
    )
    parser.add_argument(
        "--axis-membership-path",
        default=str(DEFAULT_AXIS_MEMBERSHIP_PATH),
    )
    parser.add_argument("--contract-path", default=str(DEFAULT_CONTRACT_PATH))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    raw_path = Path(args.raw_prediction_path)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw prediction not found: {raw_path}")

    # CPA uses log-normalized expression; counterfactual shift is log-space delta.
    # The HCC inputs were already log-normalized during CPA input preparation.
    extra_fields = {
        "prediction_space": "truth_aligned_log_shift",
        "normalization_applied_in_export": True,
        "log1p_applied_in_export": True,
        "endpoint_blind": True,
        "hvg_subset": False,
        "model_family": "CPA",
        "model_class": "compositional_perturbation_autoencoder",
    }

    raw_source = RawPredictionSource(
        prediction_path=raw_path,
        source_kind="cpa_counterfactual",
        export_script="scripts/models/cpa/export_cpa_predicted_shift.py",
        extra_manifest_fields=extra_fields,
    )

    result = export_external_hcc_prediction(
        cell_line=args.cell_line,
        model_id=args.model_id,
        model_version=args.model_version,
        object_role=args.object_role,
        export_timestamp=datetime.now(timezone.utc).isoformat(),
        raw_source=raw_source,
        contract_path=Path(args.contract_path),
        axis_membership_path=Path(args.axis_membership_path),
    )

    print(f"Export result:")
    print(f"  export_status: {result['export_status']}")
    print(f"  contract_pass: {result['contract_pass']}")
    print(f"  raw_prediction_path: {result['raw_prediction_path']}")
    print(f"  aligned_prediction_path: {result['aligned_prediction_path']}")
    print(f"  scorer_ready_prediction_path: {result['scorer_ready_prediction_path']}")
    print(f"  manifest_path: {result['manifest_path']}")
    print(f"  validation_summary_path: {result['validation_summary_path']}")

    if not result["contract_pass"]:
        print("\n[WARNING] Contract validation FAILED. See validation_summary for details.")
        # Still write result for inspection
    else:
        print("\n[SUCCESS] Contract validation PASSED. Scorer-ready output available.")


if __name__ == "__main__":
    main()
