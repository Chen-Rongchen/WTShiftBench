from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

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
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="跳过重新物化评测矩阵，直接复用现有 manifest / batch。",
    )
    parser.add_argument(
        "--adapter",
        action="append",
        default=[],
        help="只运行指定 adapter，可重复传入。",
    )
    parser.add_argument(
        "--model-id",
        action="append",
        default=[],
        help="只运行指定 model_id，可重复传入。",
    )
    parser.add_argument(
        "--dataset-id",
        action="append",
        default=[],
        help="只运行指定 dataset_id，可重复传入。",
    )
    parser.add_argument(
        "--tier",
        action="append",
        default=[],
        help="只运行指定 tier，可重复传入。",
    )
    parser.add_argument(
        "--pending-only",
        action="store_true",
        help="只运行当前缺少 dataset_score_summary.json 的 model × dataset 组合。",
    )
    parser.add_argument(
        "--runs-per-batch",
        type=int,
        default=0,
        help="每个 batch 最多包含多少个 run-config；<=0 表示不拆分。",
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


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml_mapping(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 YAML 键值映射。")
    return payload


def normalize_filter(values: list[str]) -> set[str]:
    return {value for value in values if value}


def load_selected_run_configs(
    *,
    config: dict[str, object],
    matrix_root: Path,
    ready_only: bool,
    adapters: set[str],
    model_ids: set[str],
    dataset_ids: set[str],
    tiers: set[str],
    pending_only: bool,
) -> dict[str, list[str]]:
    manifest_path = matrix_root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"缺少评测矩阵 manifest: {manifest_path}")
    report_root = resolve_path(str(config.get("report_root", "reports/stage1a/eval_matrix"))) / str(config["matrix_id"])
    model_matrix_path = report_root / "model_dataset_matrix.tsv"
    if not model_matrix_path.exists():
        raise FileNotFoundError(f"缺少 model_dataset_matrix.tsv: {model_matrix_path}")

    frame = pd.read_csv(model_matrix_path, sep="\t")
    if ready_only and "ready_end_to_end" in frame.columns:
        frame = frame[frame["ready_end_to_end"].fillna(False).astype(bool)]
    if adapters:
        frame = frame[frame["adapter"].astype("string").isin(sorted(adapters))]
    if model_ids:
        frame = frame[frame["model_id"].astype("string").isin(sorted(model_ids))]
    if dataset_ids:
        frame = frame[frame["dataset_id"].astype("string").isin(sorted(dataset_ids))]
    if tiers:
        frame = frame[frame["tier"].astype("string").isin(sorted(tiers))]
    if pending_only:
        pending_mask = []
        for row in frame.itertuples(index=False):
            score_path = PROJECT_ROOT / "reports/stage1a/model_eval" / str(row.model_id) / str(row.dataset_id) / "dataset_score_summary.json"
            pending_mask.append(not score_path.exists())
        frame = frame[pd.Series(pending_mask, index=frame.index)]

    selected: dict[str, list[str]] = {}
    for row in frame.itertuples(index=False):
        selected.setdefault(str(row.adapter), []).append(str(row.run_config_path))
    return selected


def write_shard_batch_configs(
    *,
    batch_root: Path,
    batch_prefix: str,
    adapter: str,
    run_configs: list[str],
    runs_per_batch: int,
) -> list[Path]:
    if not run_configs:
        return []
    if runs_per_batch <= 0 or len(run_configs) <= runs_per_batch:
        batch_path = batch_root / f"{adapter}.{batch_prefix}.yaml"
        batch_path.write_text(
            yaml.safe_dump({"run_configs": run_configs}, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return [batch_path]

    shard_root = batch_root / "shards"
    shard_root.mkdir(parents=True, exist_ok=True)
    batch_paths: list[Path] = []
    for shard_index, start in enumerate(range(0, len(run_configs), runs_per_batch), start=1):
        chunk = run_configs[start : start + runs_per_batch]
        batch_path = shard_root / f"{adapter}.{batch_prefix}.part{shard_index:02d}.yaml"
        batch_path.write_text(
            yaml.safe_dump({"run_configs": chunk}, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        batch_paths.append(batch_path)
    return batch_paths


def main() -> None:
    args = build_parser().parse_args()
    config_path = resolve_path(args.config)

    build_command = [
        "python",
        "scripts/build_stage1a_all_datasets_eval_matrix.py",
        "--config",
        str(config_path),
    ]
    if not args.skip_build:
        run_command(build_command, dry_run=args.dry_run)

    config = load_json(config_path)
    matrix_id = str(config["matrix_id"])
    materialized_root = resolve_path(str(config.get("materialized_root", "artifacts/stage1a_eval_matrix")))
    batch_root = materialized_root / matrix_id / "batches"
    topk = [str(int(v)) for v in list(config.get("topk", [50]))]
    selected_batches = load_selected_run_configs(
        config=config,
        matrix_root=materialized_root / matrix_id,
        ready_only=args.ready_only,
        adapters=normalize_filter(args.adapter),
        model_ids=normalize_filter(args.model_id),
        dataset_ids=normalize_filter(args.dataset_id),
        tiers=normalize_filter(args.tier),
        pending_only=args.pending_only,
    )

    for model in list(config.get("models", [])):
        adapter = str(model["adapter"])
        environment = str(model["environment"])
        run_configs = selected_batches.get(adapter, [])
        if not run_configs:
            print(f"[跳过] adapter={adapter} 当前过滤条件下没有待运行 run-config。")
            continue
        batch_prefix = "ready" if args.ready_only else "all"
        if args.pending_only:
            batch_prefix += ".pending"
        batch_configs = write_shard_batch_configs(
            batch_root=batch_root,
            batch_prefix=batch_prefix,
            adapter=adapter,
            run_configs=run_configs,
            runs_per_batch=args.runs_per_batch,
        )
        for batch_config in batch_configs:
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
