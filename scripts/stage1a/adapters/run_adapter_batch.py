from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="批量执行 Stage 1A adapter formal runs。")
    parser.add_argument("--adapter", required=True, choices=["gears", "scgpt", "geneformer"])
    parser.add_argument("--batch-config", required=True)
    parser.add_argument("--topk", nargs="+", type=int, default=[50])
    return parser


def resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_yaml_mapping(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是键值映射。")
    return payload


def load_run_configs(batch_config_path: Path) -> list[Path]:
    payload = load_yaml_mapping(batch_config_path)
    run_configs = payload.get("run_configs")
    if not isinstance(run_configs, list) or not run_configs:
        raise ValueError("batch-config 必须包含非空 run_configs 列表。")
    resolved = [resolve_path(str(item)) for item in run_configs]
    missing = [str(path) for path in resolved if not path.exists()]
    if missing:
        raise FileNotFoundError(f"以下 run-config 不存在: {missing}")
    return resolved


def run_command(command: list[str]) -> subprocess.CompletedProcess:
    print(f"开始执行: {' '.join(command)}")
    return subprocess.run(command, cwd=PROJECT_ROOT, check=False)


def main() -> None:
    args = build_parser().parse_args()
    batch_config_path = resolve_path(args.batch_config)
    run_config_paths = load_run_configs(batch_config_path)

    model_ids: set[str] = set()
    failed_runs: list[tuple[str, int]] = []

    for run_config_path in run_config_paths:
        payload = load_yaml_mapping(run_config_path)
        model_id = payload.get("model_id")
        if not model_id:
            raise ValueError(f"{run_config_path} 缺少 model_id。")
        model_ids.add(str(model_id))
        result = run_command(
            [
                sys.executable,
                "-m",
                "scripts.stage1a.adapters.run_adapter_pipeline",
                "--adapter",
                args.adapter,
                "--run-config",
                str(run_config_path),
                "--topk",
                *[str(value) for value in args.topk],
                "--skip-render",
            ]
        )
        if result.returncode != 0:
            print(f"[警告] {run_config_path.name} 执行失败，退出码: {result.returncode}，跳过继续。")
            failed_runs.append((str(run_config_path.name), result.returncode))

    for model_id in sorted(model_ids):
        result = run_command(
            [
                sys.executable,
                "-m",
                "scripts.stage1a.benchmark_invariant.scoring.render_pass_skeleton",
                "--model-id",
                model_id,
            ]
        )
        if result.returncode != 0:
            print(f"[警告] render_pass_skeleton for {model_id} 执行失败，退出码: {result.returncode}，跳过继续。")

    print("Stage 1A adapter batch 主线已完成。")
    if failed_runs:
        print("\n=== 错误报告 ===")
        for name, code in failed_runs:
            print(f"  - {name}: 退出码 {code}")


if __name__ == "__main__":
    main()
