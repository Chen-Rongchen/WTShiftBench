from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT


DEFAULT_BATCH_CONFIG = PROJECT_ROOT / "configs/stage1a/runs/baseline_ladder_smoke.batch.yaml"
BASELINE_PREDICTION_ROOT = PROJECT_ROOT / "data/baselines/stage1a_main_aligned"
NULL_PREDICTION_ROOT = PROJECT_ROOT / "data/nulls/stage1a_main_aligned"


@dataclass(frozen=True)
class BaselineSmokeRunSpec:
    run_config_path: Path
    dataset_id: str
    model_id: str
    prediction_path: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="执行 Stage 1A baseline ladder 最小 smoke：baseline 生成 -> ingest/evaluate/render。"
    )
    parser.add_argument(
        "--batch-config",
        default=str(DEFAULT_BATCH_CONFIG),
        help="baseline smoke 使用的 batch run-config。",
    )
    parser.add_argument(
        "--topk",
        nargs="+",
        type=int,
        default=[50],
        help="传递给 evaluate 的 top-k 列表。",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="跳过 baseline/null 构建，直接对现有 baseline 产物执行 scoring。",
    )
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_yaml_mapping(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是键值映射。")
    return payload


def load_baseline_smoke_run_specs(batch_config_path: Path) -> list[BaselineSmokeRunSpec]:
    batch_payload = load_yaml_mapping(batch_config_path)
    run_configs = batch_payload.get("run_configs")
    if not isinstance(run_configs, list) or not run_configs:
        raise ValueError(f"{batch_config_path} 必须包含非空 run_configs 列表。")

    specs: list[BaselineSmokeRunSpec] = []
    for run_config_item in run_configs:
        run_config_path = resolve_path(str(run_config_item))
        run_payload = load_yaml_mapping(run_config_path)
        dataset_id = str(run_payload.get("dataset_id") or "")
        model_id = str(run_payload.get("model_id") or "")
        prediction_path_value = str(run_payload.get("prediction_path") or "")
        if not dataset_id or not model_id or not prediction_path_value:
            raise ValueError(
                f"{run_config_path} 缺少 dataset_id、model_id 或 prediction_path。"
            )
        prediction_path = resolve_path(prediction_path_value)
        is_under_baseline = str(prediction_path).startswith(str(BASELINE_PREDICTION_ROOT))
        is_under_null = str(prediction_path).startswith(str(NULL_PREDICTION_ROOT))
        if not (is_under_baseline or is_under_null):
            raise ValueError(
                f"{run_config_path} 的 prediction_path 必须位于 "
                f"{BASELINE_PREDICTION_ROOT.relative_to(PROJECT_ROOT)} 或 "
                f"{NULL_PREDICTION_ROOT.relative_to(PROJECT_ROOT)} 下。"
            )
        specs.append(
            BaselineSmokeRunSpec(
                run_config_path=run_config_path,
                dataset_id=dataset_id,
                model_id=model_id,
                prediction_path=prediction_path,
            )
        )
    return specs


def assert_prediction_paths_exist(specs: list[BaselineSmokeRunSpec]) -> None:
    missing = [
        str(spec.prediction_path.relative_to(PROJECT_ROOT))
        for spec in specs
        if not spec.prediction_path.exists()
    ]
    if missing:
        raise FileNotFoundError(
            "以下 baseline 预测文件不存在，请先执行构建步骤: "
            f"{missing}"
        )


def run_command(command: list[str]) -> None:
    print(f"开始执行: {' '.join(command)}")
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    args = build_parser().parse_args()
    batch_config_path = resolve_path(args.batch_config)
    run_specs = load_baseline_smoke_run_specs(batch_config_path)

    dataset_ids = sorted({spec.dataset_id for spec in run_specs})
    model_ids = [spec.model_id for spec in run_specs]
    print(f"baseline smoke 数据集: {dataset_ids}")
    print(f"baseline smoke 运行项: {model_ids}")

    if not args.skip_build:
        run_command(
            [
                sys.executable,
                "-m",
                "scripts.build_stage1a_main_aligned_baselines_nulls",
            ]
        )
    assert_prediction_paths_exist(run_specs)
    run_command(
        [
            sys.executable,
            "-m",
            "scripts.stage1a.benchmark_invariant.scoring.run_batch_scoring_pipeline",
            "--batch-config",
            str(batch_config_path),
            "--topk",
            *[str(value) for value in args.topk],
        ]
    )
    print("Stage 1A baseline ladder smoke 已完成。")


if __name__ == "__main__":
    main()
