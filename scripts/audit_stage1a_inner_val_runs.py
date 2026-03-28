#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "configs/entrants/stage1a_smoke_matrix_3datasets_seed101.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="审计 Stage 1A inner validation 运行产物。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="矩阵配置 JSON 路径。")
    parser.add_argument(
        "--output-dir",
        default="artifacts/audits/stage1a_inner_val_seed101",
        help="审计输出目录。",
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


def ensure_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} 必须是非空列表。")
    return value


def relative_str(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON object。")
    return payload


def main() -> None:
    args = build_parser().parse_args()
    matrix_config = load_json(resolve_path(args.config))
    datasets = [str(value) for value in ensure_list(matrix_config.get("datasets"), "datasets")]
    split_seeds = [int(value) for value in ensure_list(matrix_config.get("split_seeds"), "split_seeds")]
    entrants = ensure_list(matrix_config.get("entrants"), "entrants")
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    warnings: list[str] = []

    for entrant_payload in entrants:
        entrant_key = str(entrant_payload["entrant_key"])
        entrant_name = str(entrant_payload["entrant_name"])
        output_root = resolve_path(str(entrant_payload["output_root"]))
        for dataset_id in datasets:
            for split_seed in split_seeds:
                run_dir = output_root / dataset_id / f"seed{split_seed}"
                prediction_path = run_dir / "predicted_shift.tsv.gz"
                run_summary_path = run_dir / "run_summary.json"
                selected_recipe_path = run_dir / "selected_recipe.json"
                epoch_grid_path = run_dir / "inner_val_epoch_grid.tsv"
                hooks_path = run_dir / "benchmark_hooks.json"

                run_summary = read_json_if_exists(run_summary_path)
                selected_recipe = read_json_if_exists(selected_recipe_path)
                hooks = read_json_if_exists(hooks_path)
                epoch_grid_exists = epoch_grid_path.is_file()
                epoch_grid_rows = 0
                if epoch_grid_exists:
                    epoch_grid_rows = int(len(pd.read_csv(epoch_grid_path, sep="\t")))

                row = {
                    "entrant_key": entrant_key,
                    "entrant_name": entrant_name,
                    "dataset_id": dataset_id,
                    "split_seed": split_seed,
                    "run_dir": relative_str(run_dir),
                    "prediction_exists": prediction_path.is_file(),
                    "run_summary_exists": run_summary is not None,
                    "selected_recipe_exists": selected_recipe is not None,
                    "epoch_grid_exists": epoch_grid_exists,
                    "epoch_grid_rows": epoch_grid_rows,
                    "selected_epoch": None if selected_recipe is None else selected_recipe.get("selected_epoch"),
                    "inner_seed": None if selected_recipe is None else selected_recipe.get("inner_seed"),
                    "inner_val_fraction": None if selected_recipe is None else selected_recipe.get("inner_val_fraction"),
                    "outer_heldout_usage": None if selected_recipe is None else selected_recipe.get("outer_heldout_usage"),
                    "inner_split_type": None if selected_recipe is None else selected_recipe.get("inner_split_type"),
                    "inner_train_target_count": None
                    if selected_recipe is None
                    else selected_recipe.get("inner_train_target_count"),
                    "inner_val_target_count": None
                    if selected_recipe is None
                    else selected_recipe.get("inner_val_target_count"),
                    "device": None if run_summary is None else run_summary.get("device"),
                    "split_train_target_count": None if run_summary is None else run_summary.get("train_target_count"),
                    "split_heldout_target_count": None
                    if run_summary is None
                    else run_summary.get("heldout_target_count"),
                    "aligned_prediction_exists": False
                    if hooks is None
                    else bool(Path(str(hooks.get("align_prediction_path", ""))).is_file()),
                    "contract_valid": None if hooks is None else hooks.get("validate_contract", {}).get("ok"),
                    "status": "ok",
                }

                issues: list[str] = []
                if not row["prediction_exists"]:
                    issues.append("missing_prediction")
                if not row["run_summary_exists"]:
                    issues.append("missing_run_summary")
                if not row["selected_recipe_exists"]:
                    issues.append("missing_selected_recipe")
                if not row["epoch_grid_exists"]:
                    issues.append("missing_inner_val_epoch_grid")
                if row["selected_recipe_exists"] and row["selected_epoch"] is None:
                    issues.append("missing_selected_epoch")
                if row["selected_recipe_exists"] and row["inner_seed"] != 11:
                    issues.append("inner_seed_not_11")
                if row["selected_recipe_exists"] and float(row["inner_val_fraction"]) != 0.2:
                    issues.append("inner_val_fraction_not_0.2")
                if row["selected_recipe_exists"] and row["outer_heldout_usage"] != "final_evaluation_only":
                    issues.append("outer_heldout_usage_invalid")
                if row["selected_recipe_exists"] and row["inner_split_type"] != "target_level":
                    issues.append("inner_split_type_invalid")
                if row["epoch_grid_exists"] and row["epoch_grid_rows"] <= 0:
                    issues.append("empty_epoch_grid")
                if row["contract_valid"] is False:
                    issues.append("contract_invalid")
                if row["inner_val_target_count"] == 1:
                    warnings.append(
                        f"{entrant_key}/{dataset_id}/seed{split_seed} 的 inner_val_target_count=1，epoch 选择稳定性较弱。"
                    )
                if issues:
                    row["status"] = "failed"
                    row["issues"] = ",".join(issues)
                else:
                    row["issues"] = ""
                rows.append(row)

    audit_df = pd.DataFrame(rows).sort_values(["entrant_key", "dataset_id", "split_seed"]).reset_index(drop=True)
    audit_tsv_path = output_dir / "audit_stage1a_inner_val_runs.tsv"
    audit_df.to_csv(audit_tsv_path, sep="\t", index=False)

    failed_rows = audit_df.loc[audit_df["status"].ne("ok")]
    summary = {
        "matrix_config": relative_str(resolve_path(args.config)),
        "audit_output_dir": relative_str(output_dir),
        "run_count": int(len(audit_df)),
        "ok_count": int(audit_df["status"].eq("ok").sum()),
        "failed_count": int(len(failed_rows)),
        "warning_count": len(warnings),
        "warnings": warnings,
        "audit_tsv_path": relative_str(audit_tsv_path),
    }
    summary_path = output_dir / "audit_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"audit_tsv_path={relative_str(audit_tsv_path)}")
    print(f"audit_summary_path={relative_str(summary_path)}")
    print(f"run_count={summary['run_count']}")
    print(f"ok_count={summary['ok_count']}")
    print(f"failed_count={summary['failed_count']}")
    print(f"warning_count={summary['warning_count']}")
    for warning in warnings:
        print(f"warning={warning}")


if __name__ == "__main__":
    main()
