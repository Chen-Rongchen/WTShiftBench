from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for candidate in (PROJECT_ROOT, SCRIPTS_DIR):
    text = str(candidate)
    if text not in sys.path:
        sys.path.insert(0, text)


DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/stage1a/runs/all_datasets_eval_matrix.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="按全数据集评测矩阵批量执行三模型 adapter，并保留 readiness 边界。"
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument(
        "--ready-only",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="默认只跑 readiness 已闭合的数据集。",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def run_command(command: list[str], *, dry_run: bool) -> None:
    print(" ".join(command))
    if dry_run:
        return
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    args = build_parser().parse_args()
    config_path = resolve_path(args.config)

    build_command = [
        "python",
        "scripts/build_stage1a_all_datasets_eval_matrix.py",
        "--config",
        str(config_path),
    ]
    run_command(build_command, dry_run=args.dry_run)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    matrix_id = str(config["matrix_id"])
    materialized_root = resolve_path(str(config.get("materialized_root", "artifacts/stage1a_eval_matrix")))
    batch_root = materialized_root / matrix_id / "batches"
    topk = [str(int(v)) for v in list(config.get("topk", [50]))]

    for model in list(config.get("models", [])):
        adapter = str(model["adapter"])
        environment = str(model["environment"])
        batch_suffix = "ready" if args.ready_only else "all"
        batch_config = batch_root / f"{adapter}.{batch_suffix}.yaml"
        run_command(
            [
                "pixi",
                "run",
                "--environment",
                environment,
                "python",
                "-m",
                "scripts.stage1a.adapters.run_adapter_batch",
                "--adapter",
                adapter,
                "--batch-config",
                str(batch_config.relative_to(PROJECT_ROOT)),
                "--topk",
                *topk,
            ],
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
