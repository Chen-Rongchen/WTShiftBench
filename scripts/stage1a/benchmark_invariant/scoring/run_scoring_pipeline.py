from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="对单个 predicted_shift contract 执行 Stage 1A benchmark-invariant scoring。"
    )
    parser.add_argument("--run-config", required=True, help="模型 adapter 产物对应的运行配置。")
    parser.add_argument("--dataset-id", help="可选。覆盖 run-config 中的 dataset_id。")
    parser.add_argument("--model-id", help="可选。覆盖 run-config 中的 model_id。")
    parser.add_argument(
        "--topk",
        nargs="+",
        type=int,
        default=[50],
        help="传递给 evaluate 的 top-k 列表。",
    )
    parser.add_argument(
        "--gene-subset-mode",
        choices=["full", "supplementary_subset"],
        default="full",
        help="full=使用完整 evaluation space；supplementary_subset=使用 gene subset。",
    )
    parser.add_argument(
        "--supplementary-subset",
        choices=["top500_control_high_expr", "top1000_control_high_expr", "top2000_control_high_expr"],
        default=None,
        help="当 --gene-subset-mode=supplementary_subset 时指定。",
    )
    return parser


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_run_config(run_config_path: Path) -> dict[str, object]:
    payload = yaml.safe_load(run_config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("run-config 必须是键值映射。")
    return payload


def run_command(command: list[str]) -> None:
    print(f"开始执行: {' '.join(command)}")
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    args = build_parser().parse_args()
    run_config_path = resolve_path(args.run_config)
    run_config = load_run_config(run_config_path)

    dataset_id = args.dataset_id or run_config.get("dataset_id")
    model_id = args.model_id or run_config.get("model_id")
    if not dataset_id or not model_id:
        raise ValueError("run-config 或命令行参数中必须提供 dataset_id 与 model_id。")

    # Validate supplementary mode arguments
    if args.gene_subset_mode == "supplementary_subset":
        if not args.supplementary_subset:
            raise ValueError("--gene-subset-mode=supplementary_subset 时必须指定 --supplementary-subset。")
    else:
        if args.supplementary_subset:
            raise ValueError("--supplementary-subset 仅在 --gene-subset-mode=supplementary_subset 时有效。")

    # Build common arguments for evaluate and render
    evaluate_extra_args: list[str] = []
    render_extra_args: list[str] = []
    if args.gene_subset_mode == "supplementary_subset":
        evaluate_extra_args.extend(["--gene-subset-mode", "supplementary_subset", "--supplementary-subset", args.supplementary_subset])
        render_extra_args.extend(["--gene-subset-mode", "supplementary_subset", "--supplementary-subset", args.supplementary_subset])

    run_command(
        [
            sys.executable,
            "-m",
            "scripts.stage1a.benchmark_invariant.scoring.ingest_predictions",
            "--run-config",
            str(run_config_path),
        ]
    )
    evaluate_cmd = [
        sys.executable,
        "-m",
        "scripts.stage1a.benchmark_invariant.scoring.evaluate_predictions",
        "--dataset-id",
        str(dataset_id),
        "--model-id",
        str(model_id),
        "--topk",
        *[str(value) for value in args.topk],
    ] + evaluate_extra_args
    run_command(evaluate_cmd)
    render_cmd = [
        sys.executable,
        "-m",
        "scripts.stage1a.benchmark_invariant.scoring.render_pass_skeleton",
        "--model-id",
        str(model_id),
    ] + render_extra_args
    run_command(render_cmd)

    mode_label = "supplementary" if args.gene_subset_mode == "supplementary_subset" else "主线"
    print(f"Stage 1A benchmark-invariant scoring {mode_label}已完成。")


if __name__ == "__main__":
    main()
