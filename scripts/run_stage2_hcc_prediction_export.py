from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from wtbench.stage2_hcc_prediction_export import (
    DEFAULT_STAGE2_CONTRACT_PATH,
    DEFAULT_STAGE2_TRUTH_CONFIG_PATH,
    RawPredictionSource,
    export_external_stage2_hcc_prediction,
    export_builtin_stage2_hcc_prediction,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="导出 Stage 2 HCC scorer-ready prediction。")
    parser.add_argument("--cell-line", required=True, choices=["HCC38", "HCC1143"])
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-version", default="v1")
    parser.add_argument("--object-role", required=True, choices=["null", "baseline", "entrant"])
    parser.add_argument("--stage2-truth-config", default=str(DEFAULT_STAGE2_TRUTH_CONFIG_PATH))
    parser.add_argument("--contract-path", default=str(DEFAULT_STAGE2_CONTRACT_PATH))
    parser.add_argument("--input-prediction-path")
    parser.add_argument("--source-kind")
    parser.add_argument("--source-checkpoint")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    export_timestamp = datetime.now(timezone.utc).isoformat()
    if args.object_role == "entrant":
        if not args.input_prediction_path:
            raise ValueError("object_role=entrant 时必须提供 --input-prediction-path。")
        result = export_external_stage2_hcc_prediction(
            cell_line=args.cell_line,
            model_id=args.model_id,
            model_version=args.model_version,
            object_role=args.object_role,
            export_timestamp=export_timestamp,
            raw_source=RawPredictionSource(
                prediction_path=Path(args.input_prediction_path),
                source_kind=str(args.source_kind or "external_predicted_shift"),
                export_script="scripts/run_stage2_hcc_prediction_export.py",
                extra_manifest_fields=(
                    {"source_checkpoint": str(args.source_checkpoint)}
                    if args.source_checkpoint
                    else None
                ),
            ),
            contract_path=Path(args.contract_path),
        )
    else:
        result = export_builtin_stage2_hcc_prediction(
            cell_line=args.cell_line,
            model_id=args.model_id,
            model_version=args.model_version,
            object_role=args.object_role,
            export_timestamp=export_timestamp,
            stage2_truth_config_path=Path(args.stage2_truth_config),
            contract_path=Path(args.contract_path),
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
