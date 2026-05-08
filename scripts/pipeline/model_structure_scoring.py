from __future__ import annotations

import argparse
from pathlib import Path

from wtbench.model_structure_scorer import (
    DEFAULT_AXIS_MEMBERSHIP_PATH,
    DEFAULT_TRUTH_CONTRACT_PATH,
    score_prediction_against_frozen_architecture,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage 2 model-side structure scorer。")
    parser.add_argument("--prediction-path", required=True)
    parser.add_argument("--projected-output-path", required=True)
    parser.add_argument("--score-output-path", required=True)
    parser.add_argument("--truth-contract-path", default=str(DEFAULT_TRUTH_CONTRACT_PATH))
    parser.add_argument("--axis-membership-path", default=str(DEFAULT_AXIS_MEMBERSHIP_PATH))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    projected, scores = score_prediction_against_frozen_architecture(
        prediction_path=Path(args.prediction_path),
        truth_contract_path=Path(args.truth_contract_path),
        axis_membership_path=Path(args.axis_membership_path),
    )
    projected_output_path = Path(args.projected_output_path)
    score_output_path = Path(args.score_output_path)
    projected_output_path.parent.mkdir(parents=True, exist_ok=True)
    score_output_path.parent.mkdir(parents=True, exist_ok=True)
    projected.to_csv(projected_output_path, sep="\t", index=False)
    scores.to_csv(score_output_path, sep="\t", index=False)


if __name__ == "__main__":
    main()
