#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "configs/entrants/stage1a_smoke_matrix_3datasets_5seeds.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="按 JSON 矩阵配置批量执行 Stage 1A entrant smoke（多数据集 × 多 seeds）。"
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="矩阵配置 JSON 路径。",
    )
    parser.add_argument(
        "--entrant",
        action="append",
        default=[],
        help="只运行指定 entrant_key；可重复传入。",
    )
    parser.add_argument(
        "--dataset-id",
        action="append",
        default=[],
        help="只运行指定 dataset_id；可重复传入。",
    )
    parser.add_argument(
        "--split-seed",
        action="append",
        type=int,
        default=[],
        help="只运行指定 split_seed；可重复传入。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将要执行的命令，不真正启动子进程。",
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


def ensure_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} 必须是 object。")
    return value


def ensure_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} 必须是非空列表。")
    return value


def build_temp_config(
    *,
    template_config_path: Path,
    entrant_name: str,
    dataset_id: str,
    split_seed: int,
    output_root: str,
    temp_root: Path,
) -> Path:
    payload = yaml.safe_load(template_config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{template_config_path} 必须是 YAML mapping。")
    payload = dict(payload)
    payload["entrant_name"] = entrant_name
    payload["dataset_id"] = dataset_id
    payload["split_seed"] = int(split_seed)
    payload["output_dir"] = f"{output_root}/{dataset_id}/seed{split_seed}"

    output_path = temp_root / entrant_name / dataset_id / f"seed{split_seed}.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return output_path


def run_command(command: list[str], dry_run: bool) -> None:
    print("开始执行:", " ".join(command), flush=True)
    if dry_run:
        return
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    args = build_parser().parse_args()
    config_path = resolve_path(args.config)
    payload = load_json(config_path)

    dataset_ids = [str(value) for value in ensure_list(payload.get("datasets"), "datasets")]
    split_seeds = [int(value) for value in ensure_list(payload.get("split_seeds"), "split_seeds")]
    entrants = ensure_list(payload.get("entrants"), "entrants")
    temp_config_root = resolve_path(str(payload.get("temp_config_root", "tmp/stage1a_smoke_matrix_configs")))

    entrant_filter = set(str(value) for value in args.entrant)
    dataset_filter = set(str(value) for value in args.dataset_id)
    seed_filter = set(int(value) for value in args.split_seed)

    run_count = 0
    for entrant_payload in entrants:
        entrant = ensure_mapping(entrant_payload, "entrant")
        entrant_key = str(entrant["entrant_key"])
        if entrant_filter and entrant_key not in entrant_filter:
            continue
        runner_env = str(entrant["runner_env"])
        runner_script = str(entrant["runner_script"])
        template_config_path = resolve_path(str(entrant["template_config"]))
        entrant_name = str(entrant["entrant_name"])
        output_root = str(entrant["output_root"])

        for dataset_id in dataset_ids:
            if dataset_filter and dataset_id not in dataset_filter:
                continue
            for split_seed in split_seeds:
                if seed_filter and split_seed not in seed_filter:
                    continue
                temp_config_path = build_temp_config(
                    template_config_path=template_config_path,
                    entrant_name=entrant_name,
                    dataset_id=dataset_id,
                    split_seed=split_seed,
                    output_root=output_root,
                    temp_root=temp_config_root,
                )
                run_command(
                    [
                        "pixi",
                        "run",
                        "--environment",
                        runner_env,
                        "python",
                        runner_script,
                        "--config",
                        str(temp_config_path),
                    ],
                    dry_run=bool(args.dry_run),
                )
                run_count += 1

    print(f"Stage 1A smoke matrix 已处理 {run_count} 个运行项。", flush=True)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"子进程失败: returncode={exc.returncode}", file=sys.stderr)
        raise
