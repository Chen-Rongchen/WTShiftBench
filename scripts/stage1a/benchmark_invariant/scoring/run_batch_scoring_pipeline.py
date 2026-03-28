from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="对多个 predicted_shift contract 批量执行 Stage 1A benchmark-invariant scoring。"
    )
    parser.add_argument(
        "--batch-config",
        required=True,
        help="包含 run_configs 列表的 YAML 配置。",
    )
    parser.add_argument(
        "--topk",
        nargs="+",
        type=int,
        default=[50],
        help="传递给 evaluate 的 top-k 列表。",
    )
    return parser


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_yaml_mapping(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是键值映射。")
    return payload


def load_batch_run_configs(batch_config_path: Path) -> list[Path]:
    payload = load_yaml_mapping(batch_config_path)
    run_configs = payload.get("run_configs")
    if not isinstance(run_configs, list) or not run_configs:
        raise ValueError("batch-config 必须包含非空 run_configs 列表。")
    resolved = [resolve_path(str(item)) for item in run_configs]
    missing = [str(path) for path in resolved if not path.exists()]
    if missing:
        raise FileNotFoundError(f"以下 run-config 不存在: {missing}")
    return resolved


def run_command(command: list[str]) -> None:
    print(f"开始执行: {' '.join(command)}")
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    args = build_parser().parse_args()
    batch_config_path = resolve_path(args.batch_config)
    run_config_paths = load_batch_run_configs(batch_config_path)

    model_ids: set[str] = set()
    run_configs: list[tuple[Path, str, str]] = []
    for run_config_path in run_config_paths:
        payload = load_yaml_mapping(run_config_path)
        dataset_id = payload.get("dataset_id")
        model_id = payload.get("model_id")
        if not dataset_id or not model_id:
            raise ValueError(f"{run_config_path} 缺少 dataset_id 或 model_id。")
        model_ids.add(str(model_id))
        run_configs.append((run_config_path, str(dataset_id), str(model_id)))

    for run_config_path, dataset_id, model_id in run_configs:
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
                dataset_id,
                "--model-id",
                model_id,
                "--topk",
                *[str(value) for value in args.topk],
            ]
        )

    for model_id in sorted(model_ids):
        run_command(
            [
                sys.executable,
                "-m",
                "scripts.stage1a.benchmark_invariant.scoring.render_pass_skeleton",
                "--model-id",
                model_id,
            ]
        )

    print("Stage 1A benchmark-invariant batch scoring 主线已完成。")


if __name__ == "__main__":
    main()
