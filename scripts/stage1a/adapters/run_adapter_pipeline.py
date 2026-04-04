from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT


ADAPTER_BUILD_COMMANDS = {
    "gears": ["scripts/stage1a/adapters/gears/launch_build_predictions.py"],
    "scgpt": ["-m", "scripts.stage1a.adapters.scgpt.build_predictions"],
    "geneformer": ["-m", "scripts.stage1a.adapters.geneformer.build_predictions"],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="执行单个 Stage 1A adapter run-config 的正式主线。")
    parser.add_argument("--adapter", required=True, choices=sorted(ADAPTER_BUILD_COMMANDS))
    parser.add_argument("--run-config", required=True)
    parser.add_argument("--topk", nargs="+", type=int, default=[50])
    parser.add_argument("--skip-render", action="store_true")
    return parser


def resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_run_config(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是键值映射。")
    return payload


def run_command(command: list[str]) -> None:
    print(f"开始执行: {' '.join(command)}")
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    args = build_parser().parse_args()
    run_config_path = resolve_path(args.run_config)
    run_config = load_run_config(run_config_path)
    dataset_id = run_config.get("dataset_id")
    model_id = run_config.get("model_id")
    if not dataset_id or not model_id:
        raise ValueError(f"{run_config_path} 缺少 dataset_id 或 model_id。")

    run_command(
        [
            sys.executable,
            *ADAPTER_BUILD_COMMANDS[args.adapter],
            "--run-config",
            str(run_config_path),
        ]
    )
    run_command(
        [
            sys.executable,
            "-m",
            "scripts.stage1a.benchmark_invariant.scoring.validate_prediction_contract",
            "--run-config",
            str(run_config_path),
        ]
    )
    run_command(
        [
            sys.executable,
            "-m",
            "scripts.stage1a.benchmark_invariant.scoring.ingest_predictions",
            "--run-config",
            str(run_config_path),
        ]
    )
    run_command(
        [
            sys.executable,
            "-m",
            "scripts.stage1a.benchmark_invariant.scoring.evaluate_predictions",
            "--dataset-id",
            str(dataset_id),
            "--model-id",
            str(model_id),
            *(
                ["--truth-registry-path", str(run_config["truth_registry_path"])]
                if run_config.get("truth_registry_path")
                else []
            ),
            *(
                ["--baseline-root", str(run_config["baseline_root"])]
                if run_config.get("baseline_root")
                else []
            ),
            *(
                ["--null-root", str(run_config["null_root"])]
                if run_config.get("null_root")
                else []
            ),
            "--topk",
            *[str(value) for value in args.topk],
        ]
    )
    if not args.skip_render:
        run_command(
            [
                sys.executable,
                "-m",
                "scripts.stage1a.benchmark_invariant.scoring.render_pass_skeleton",
                "--model-id",
                str(model_id),
            ]
        )

    print("Stage 1A adapter 单链路已完成。")


if __name__ == "__main__":
    main()
