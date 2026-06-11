from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

from wtbench.model_endpoint_recovery import (
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_PREDICTION_ROOT,
    run_endpoint_recovery_audit,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run model endpoint-recovery and output-homogenization audit for HCC predictions.",
    )
    parser.add_argument("--model-id", action="append", help="Model id to score. Repeatable. Defaults to all discovered.")
    parser.add_argument("--prediction-root", default=str(DEFAULT_PREDICTION_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--n-permutations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=1)
    return parser


def main() -> None:
    warnings.filterwarnings("ignore", message="Mean of empty slice", category=RuntimeWarning)
    args = build_parser().parse_args()
    paths = run_endpoint_recovery_audit(
        model_ids=args.model_id,
        prediction_root=Path(args.prediction_root),
        output_root=Path(args.output_root),
        n_permutations=args.n_permutations,
        seed=args.seed,
    )
    print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
