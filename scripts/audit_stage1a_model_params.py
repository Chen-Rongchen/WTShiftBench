from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

try:
    from scripts.stage1a.adapters.common.runtime import PROJECT_ROOT
except ModuleNotFoundError:
    from stage1a.benchmark_invariant.catalog import PROJECT_ROOT


FORMAL_CONFIG_DIR = PROJECT_ROOT / "configs/stage1a/adapters/formal"
GEARS_DEFAULTS_PATH = PROJECT_ROOT / "configs/entrants/gears_runtime_defaults.yaml"
OUTPUT_DIR = PROJECT_ROOT / "reports/stage1a/parameter_audit"
TSV_PATH = OUTPUT_DIR / "stage1a_model_parameter_audit.tsv"
JSON_PATH = OUTPUT_DIR / "stage1a_model_parameter_audit.json"

PIPELINE_SHARED_FIELDS = [
    "prediction_space",
    "output_path",
    "summary_path",
    "manifest_path",
    "allow_missing_targets",
    "allow_missing_genes",
]


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def stringify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def audit_gears(config_path: Path, gears_defaults: dict[str, object]) -> dict[str, object]:
    config = load_yaml(config_path)
    review_notes: list[str] = []
    mismatch_fields: list[str] = []
    compare_map = {
        "epochs": "max_epochs",
        "batch_size": "batch_size",
        "lr": "learning_rate",
        "weight_decay": "weight_decay",
        "train_val_fraction": "train_val_fraction",
        "max_control_cells": "max_control_cells",
        "prediction_num_samples": "prediction_num_samples",
        "perturbation_graph_k": "perturbation_graph_k",
    }
    for config_key, default_key in compare_map.items():
        current = config.get(config_key)
        expected = gears_defaults.get(default_key)
        if stringify(current) != stringify(expected):
            mismatch_fields.append(config_key)
    if stringify(config.get("device")) != "auto":
        mismatch_fields.append("device")

    if int(config["epochs"]) < 10:
        review_notes.append("epochs 偏低，更像 smoke 参数。")
    if config.get("device") != "auto":
        review_notes.append("device 未使用 auto 语义。")
    if float(config["train_val_fraction"]) != 0.8:
        review_notes.append("train_val_fraction 未对齐 inner_val_fraction=0.2。")

    implementation_gap = (
        "runtime spec 声明 early_stopping/checkpoint_selection，但当前 "
        "scripts/stage1a/adapters/gears/build_predictions.py 未把这些项作为配置暴露。"
    )
    review_status = "aligned" if not mismatch_fields else "needs_review"
    if mismatch_fields:
        review_notes.append(f"与 GEARS runtime defaults 不一致: {', '.join(mismatch_fields)}")

    return {
        "model_family": "gears",
        "dataset_id": stringify(config["dataset_id"]),
        "prediction_mode": "trainable_adapter",
        "config_path": str(config_path.relative_to(PROJECT_ROOT)),
        "device": stringify(config.get("device")),
        "seed": stringify(config.get("seed")),
        "seed_effect": "strong",
        "checkpoint_dir": "",
        "asset_root": "",
        "top_k": "",
        "epochs": stringify(config.get("epochs")),
        "batch_size": stringify(config.get("batch_size")),
        "lr": stringify(config.get("lr")),
        "weight_decay": stringify(config.get("weight_decay")),
        "train_val_fraction": stringify(config.get("train_val_fraction")),
        "max_control_cells": stringify(config.get("max_control_cells")),
        "max_cells_per_train_condition": stringify(config.get("max_cells_per_train_condition")),
        "prediction_num_samples": stringify(config.get("prediction_num_samples")),
        "perturbation_graph_k": stringify(config.get("perturbation_graph_k")),
        "active_param_fields": ",".join(
            [
                "device",
                "seed",
                "epochs",
                "batch_size",
                "lr",
                "weight_decay",
                "train_val_fraction",
                "max_control_cells",
                "max_cells_per_train_condition",
                "prediction_num_samples",
                "perturbation_graph_k",
            ]
        ),
        "shared_pipeline_fields": ",".join(PIPELINE_SHARED_FIELDS),
        "implementation_gap": implementation_gap,
        "review_status": review_status,
        "review_note": "；".join(review_notes) if review_notes else "GEARS formal 配置已对齐当前 runtime defaults。",  # noqa: E501
    }


def audit_scgpt(config_path: Path) -> dict[str, object]:
    config = load_yaml(config_path)
    return {
        "model_family": "scgpt",
        "dataset_id": stringify(config["dataset_id"]),
        "prediction_mode": "embedding_kernel",
        "config_path": str(config_path.relative_to(PROJECT_ROOT)),
        "device": "auto",
        "seed": stringify(config.get("seed")),
        "seed_effect": "weak",
        "checkpoint_dir": stringify(config.get("checkpoint_dir")),
        "asset_root": "",
        "top_k": stringify(config.get("top_k")),
        "epochs": "",
        "batch_size": "",
        "lr": "",
        "weight_decay": "",
        "train_val_fraction": "",
        "max_control_cells": "",
        "max_cells_per_train_condition": "",
        "prediction_num_samples": "",
        "perturbation_graph_k": "",
        "active_param_fields": ",".join(["checkpoint_dir", "device", "top_k"]),
        "shared_pipeline_fields": ",".join(PIPELINE_SHARED_FIELDS),
        "implementation_gap": "MIN_HELDOUT_COVERAGE=0.8 当前硬编码在脚本中，未外提到配置层。",
        "review_status": "aligned",
        "review_note": "当前为 frozen embedding + cosine kernel adapter；seed 基本只作元数据记录，top_k 才是主要超参。",
    }


def audit_geneformer(config_path: Path) -> dict[str, object]:
    config = load_yaml(config_path)
    return {
        "model_family": "geneformer",
        "dataset_id": stringify(config["dataset_id"]),
        "prediction_mode": "embedding_kernel",
        "config_path": str(config_path.relative_to(PROJECT_ROOT)),
        "device": "auto",
        "seed": stringify(config.get("seed")),
        "seed_effect": "weak",
        "checkpoint_dir": stringify(config.get("checkpoint_dir")),
        "asset_root": stringify(config.get("asset_root")),
        "top_k": stringify(config.get("top_k")),
        "epochs": "",
        "batch_size": "",
        "lr": "",
        "weight_decay": "",
        "train_val_fraction": "",
        "max_control_cells": "",
        "max_cells_per_train_condition": "",
        "prediction_num_samples": "",
        "perturbation_graph_k": "",
        "active_param_fields": ",".join(["checkpoint_dir", "asset_root", "device", "top_k"]),
        "shared_pipeline_fields": ",".join(PIPELINE_SHARED_FIELDS),
        "implementation_gap": "MIN_HELDOUT_COVERAGE=0.8 当前硬编码在脚本中，未外提到配置层。",
        "review_status": "aligned",
        "review_note": "当前为 frozen embedding + cosine kernel adapter；seed 基本只作元数据记录，top_k 才是主要超参。",
    }


def main() -> None:
    gears_defaults = load_yaml(GEARS_DEFAULTS_PATH)
    rows: list[dict[str, object]] = []
    for config_path in sorted((FORMAL_CONFIG_DIR / "gears_stage1a_formal").glob("*.yaml")):
        rows.append(audit_gears(config_path, gears_defaults))
    for config_path in sorted((FORMAL_CONFIG_DIR / "scgpt_embedding_kernel_formal").glob("*.yaml")):
        rows.append(audit_scgpt(config_path))
    for config_path in sorted((FORMAL_CONFIG_DIR / "geneformer_embedding_kernel_formal").glob("*.yaml")):
        rows.append(audit_geneformer(config_path))

    frame = pd.DataFrame(rows).sort_values(["model_family", "dataset_id"]).reset_index(drop=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(TSV_PATH, sep="\t", index=False)
    JSON_PATH.write_text(
        json.dumps(frame.to_dict(orient="records"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"已写出: {TSV_PATH}")
    print(f"已写出: {JSON_PATH}")
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
