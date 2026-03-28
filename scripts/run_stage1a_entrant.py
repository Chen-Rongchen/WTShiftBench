"""
DEPRECATED: 此脚本已被弃用，不可使用。

原因：
- 依赖 wtbench.entrants.registry 模块（已标记为 deprecated）
- wtbench.entrants.base 中缺少以下函数：
  build_output_paths, build_provenance, build_run_summary,
  build_standard_output_dir, run_contract_validator, validate_recipe_identity,
  write_prediction_frame, write_sidecars
- wtbench.entrants.base.EntrantContext 与 smoke 脚本中的 EntrantContext 定义不一致

当前支持的入口：scripts/smoke_stage1a_*.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

raise RuntimeError(
    "scripts/run_stage1a_entrant.py 已弃用，请使用 scripts/smoke_stage1a_gears.py / "
    "scripts/smoke_stage1a_scgpt.py / scripts/smoke_stage1a_geneformer.py"
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from wtbench.entrants.base import (
    EntrantContext,
    build_output_paths,
    build_provenance,
    build_run_summary,
    build_standard_output_dir,
    load_mapping_config,
    run_contract_validator,
    utc_timestamp,
    validate_recipe_identity,
    write_prediction_frame,
    write_sidecars,
)
from wtbench.entrants.registry import get_registry_entry, instantiate_adapter, load_entrant_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="统一执行 Stage 1A entrant recipe：adapter → predicted_shift → provenance → validator。"
    )
    parser.add_argument("--entrant-id")
    parser.add_argument("--config", help="recipe 配置文件路径（推荐 configs/*.json）。")
    parser.add_argument("--dataset-id")
    parser.add_argument("--split-seed", type=int)
    parser.add_argument("--output-dir")
    parser.add_argument("--device")
    parser.add_argument("--list", action="store_true", help="打印当前 entrant registry。")
    return parser


def print_registry() -> None:
    rows = [
        {
            "entrant_id": entry.entrant_id,
            "entrant_version": entry.entrant_version,
            "model_family": entry.model_family,
            "status": entry.status,
            "default_config_path": str(entry.default_config_path.relative_to(PROJECT_ROOT)),
            "notes": entry.notes,
        }
        for entry in load_entrant_registry()
    ]
    print(json.dumps(rows, ensure_ascii=False, indent=2))


def main() -> None:
    args = build_parser().parse_args()
    if args.list:
        print_registry()
        return
    if not args.entrant_id:
        raise ValueError("--entrant-id 为必填参数，除非使用 --list。")

    registry_entry = get_registry_entry(args.entrant_id)
    recipe_config_path = Path(args.config) if args.config else registry_entry.default_config_path
    if not recipe_config_path.is_absolute():
        recipe_config_path = PROJECT_ROOT / recipe_config_path
    if not recipe_config_path.exists():
        raise FileNotFoundError(f"entrant config 不存在: {recipe_config_path}")

    raw_config = load_mapping_config(recipe_config_path)
    validate_recipe_identity(raw_config)
    if str(raw_config["entrant_id"]) != registry_entry.entrant_id:
        raise ValueError(
            f"config entrant_id={raw_config['entrant_id']} 与 registry entrant_id={registry_entry.entrant_id} 不一致。"
        )

    dataset_id = str(args.dataset_id or raw_config.get("dataset_id"))
    if not dataset_id:
        raise ValueError("缺少 dataset_id。")

    config_split_seed = raw_config.get("split_seed")
    if config_split_seed is None and args.split_seed is None:
        raise ValueError("缺少 split_seed。")
    split_seed = int(args.split_seed if args.split_seed is not None else config_split_seed)

    if (
        args.split_seed is not None
        and config_split_seed is not None
        and int(args.split_seed) != int(config_split_seed)
        and args.output_dir is None
    ):
        raise ValueError(
            "CLI 覆盖 split_seed 但未显式提供 --output-dir。标准输出路径不含 split_seed，"
            "为避免覆盖已有产物，请显式指定输出目录或更新 entrant_version。"
        )

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else build_standard_output_dir(
            entrant_id=str(raw_config["entrant_id"]),
            entrant_version=str(raw_config["entrant_version"]),
            dataset_id=dataset_id,
        )
    )
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir

    context = EntrantContext(
        project_root=PROJECT_ROOT,
        recipe_config_path=recipe_config_path,
        raw_config=raw_config,
        dataset_id=dataset_id,
        split_seed=split_seed,
        device=args.device or raw_config.get("runtime", {}).get("device"),
        output_dir=output_dir,
        timestamp=utc_timestamp(),
    )
    adapter = instantiate_adapter(registry_entry.adapter_class)
    adapter_result = adapter.run(context)

    paths = build_output_paths(output_dir)
    write_prediction_frame(paths, adapter_result.predicted_shift)
    validator_summary = run_contract_validator(
        dataset_id=dataset_id,
        model_id=str(raw_config["entrant_version"]),
        prediction_path=paths.prediction_path,
    )
    provenance = build_provenance(context, adapter_result, paths)
    run_summary = build_run_summary(context, adapter_result, validator_summary)
    write_sidecars(paths, provenance, run_summary)

    print(f"已写出: {paths.prediction_path.relative_to(PROJECT_ROOT)}")
    print(f"已写出: {paths.provenance_path.relative_to(PROJECT_ROOT)}")
    print(f"已写出: {paths.run_summary_path.relative_to(PROJECT_ROOT)}")
    print(json.dumps(validator_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
