#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "configs/entrants/stage1a_inner_val_pipeline_seed101.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="执行 Stage 1A inner validation 收口流水线。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="pipeline 配置 JSON 路径。")
    parser.add_argument("--dry-run", action="store_true", help="只打印命令，不真正执行。")
    parser.add_argument(
        "--start-step",
        type=int,
        default=1,
        help="从第几步开始执行，范围 1-6。",
    )
    parser.add_argument(
        "--end-step",
        type=int,
        default=6,
        help="执行到第几步结束，范围 1-6。",
    )
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON object。")
    return payload


def run_command(command: list[str], *, dry_run: bool) -> None:
    print("开始执行:", " ".join(command), flush=True)
    if dry_run:
        return
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    args = build_parser().parse_args()
    if args.start_step < 1 or args.end_step > 6 or args.start_step > args.end_step:
        raise ValueError("--start-step / --end-step 必须满足 1 <= start <= end <= 6。")

    payload = load_json(resolve_path(args.config))
    split_config = str(payload["split_config"])
    matrix_config = str(payload["matrix_config"])
    audit_output_dir = str(payload["audit_output_dir"])

    summary_command = [
        "pixi",
        "run",
        "--environment",
        "core",
        "python",
        "scripts/audit_stage1a_inner_val_runs.py",
        "--config",
        matrix_config,
        "--output-dir",
        audit_output_dir,
    ]

    steps: list[tuple[int, str, list[str]]] = [
        (
            1,
            "物化 shared outer/inner split",
            [
                "pixi",
                "run",
                "--environment",
                "core",
                "python",
                "scripts/materialize_stage1a_inner_splits.py",
                "--config",
                split_config,
            ],
        ),
        (
            2,
            "dry-run 预览矩阵命令",
            [
                "pixi",
                "run",
                "--environment",
                "core",
                "python",
                "scripts/run_stage1a_smoke_matrix.py",
                "--config",
                matrix_config,
                "--dry-run",
            ],
        ),
        (
            3,
            "正式运行矩阵",
            [
                "pixi",
                "run",
                "--environment",
                "core",
                "python",
                "scripts/run_stage1a_smoke_matrix.py",
                "--config",
                matrix_config,
            ],
        ),
        (
            4,
            "审计 required artifacts",
            [
                "pixi",
                "run",
                "--environment",
                "core",
                "python",
                "scripts/audit_stage1a_inner_val_runs.py",
                "--config",
                matrix_config,
                "--output-dir",
                audit_output_dir,
            ],
        ),
        (
            5,
            "复查 selected_recipe / heldout 边界",
            summary_command,
        ),
        (
            6,
            "生成最终审计摘要",
            summary_command,
        ),
    ]

    for step_index, step_label, command in steps:
        if args.start_step <= step_index <= args.end_step:
            print(f"[step {step_index}] {step_label}", flush=True)
            run_command(command, dry_run=bool(args.dry_run))


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"子进程失败: returncode={exc.returncode}", file=sys.stderr)
        raise
