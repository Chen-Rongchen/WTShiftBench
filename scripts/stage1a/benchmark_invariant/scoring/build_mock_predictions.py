from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    PROJECT_ROOT,
    comparator_path,
    load_main_aligned_truth_entry,
    read_matrix,
    resolve_project_relative,
    write_matrix,
)


DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data/predictions/stage1a_mock_raw"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="构造 Stage 1A mock model 预测矩阵。")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument(
        "--mode",
        choices=["truth_copy", "truth_plus_noise", "mean_shift_baseline"],
        default="truth_plus_noise",
    )
    parser.add_argument("--noise-scale", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=20260323)
    parser.add_argument("--output-path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    truth_entry = load_main_aligned_truth_entry(args.dataset_id)
    truth = read_matrix(truth_entry.path)

    if args.mode == "truth_copy":
        mock = truth.copy()
    elif args.mode == "truth_plus_noise":
        rng = np.random.default_rng(args.seed)
        noise = rng.normal(loc=0.0, scale=args.noise_scale, size=truth.shape)
        mock = pd.DataFrame(
            truth.to_numpy(dtype=np.float64, copy=False) + noise,
            index=truth.index,
            columns=truth.columns,
        )
    else:
        mock = read_matrix(comparator_path(args.dataset_id, "mean_shift_baseline"))

    output_path = (
        Path(args.output_path)
        if args.output_path
        else DEFAULT_OUTPUT_ROOT / args.model_id / args.dataset_id / "predicted_shift.tsv.gz"
    )
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    write_matrix(mock, output_path)
    print(f"已写出: {resolve_project_relative(output_path)}")


if __name__ == "__main__":
    main()
