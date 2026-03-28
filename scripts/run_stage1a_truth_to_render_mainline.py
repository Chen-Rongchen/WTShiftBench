from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="旧入口：依次执行 benchmark-invariant truth-space 与 scoring。"
    )
    parser.add_argument("--run-config", required=True)
    parser.add_argument("--dataset-id")
    parser.add_argument("--model-id")
    parser.add_argument("--topk", nargs="+", type=int, default=[50])
    return parser


def run_command(command: list[str]) -> None:
    print(f"开始执行: {' '.join(command)}")
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    args = build_parser().parse_args()
    run_command(
        [
            sys.executable,
            "-m",
            "scripts.stage1a.benchmark_invariant.truth_space.run_truth_space_mainline",
        ]
    )
    scoring_command = [
        sys.executable,
        "-m",
        "scripts.stage1a.benchmark_invariant.scoring.run_scoring_pipeline",
        "--run-config",
        args.run_config,
        "--topk",
        *[str(value) for value in args.topk],
    ]
    if args.dataset_id:
        scoring_command.extend(["--dataset-id", args.dataset_id])
    if args.model_id:
        scoring_command.extend(["--model-id", args.model_id])
    run_command(scoring_command)
    print("Stage 1A legacy truth-to-render 入口已转发到双层主线。")


if __name__ == "__main__":
    main()
