from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from scripts.stage1a.adapters.common.runtime import coalesce_arg, load_run_config, resolve_path
from scripts.stage1a.benchmark_invariant.prediction_eval_common import json_dump, read_matrix, resolve_project_relative, write_matrix
from scripts.stage1a.challengers.common import DEFAULT_CHALLENGER_REGISTRY_PATH, get_challenger_entry


DEFAULT_MODEL_ID = "fixed_late_fusion_v1"
DEFAULT_PREDICTION_ROOT = Path("data/predictions/stage1a_challengers_raw")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="构建 fixed_late_fusion_v1 的加权 predicted_shift.tsv.gz。")
    parser.add_argument("--run-config", required=True)
    parser.add_argument("--challenger-registry", default=str(DEFAULT_CHALLENGER_REGISTRY_PATH))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_config = load_run_config(args.run_config)

    challenger_id = str(coalesce_arg(None, run_config, "challenger_id", DEFAULT_MODEL_ID))
    dataset_id = str(run_config["dataset_id"])
    model_id = str(coalesce_arg(None, run_config, "model_id", DEFAULT_MODEL_ID))
    prediction_path = resolve_path(
        str(
            coalesce_arg(
                None,
                run_config,
                "prediction_path",
                DEFAULT_PREDICTION_ROOT / model_id / dataset_id / "predicted_shift.tsv.gz",
            )
        )
    )
    metadata_path = resolve_path(
        str(coalesce_arg(None, run_config, "metadata_path", prediction_path.with_name("adapter_metadata.json")))
    )
    members = run_config.get("members")
    if not isinstance(members, list) or not members:
        raise ValueError("fixed_late_fusion_v1 需要非空 members 列表。")

    challenger_entry = get_challenger_entry(challenger_id, resolve_path(args.challenger_registry))
    if not challenger_entry.implemented or not challenger_entry.wired_to_eval:
        raise ValueError(f"{challenger_id} 尚未处于可运行状态。")

    weighted_sum: pd.DataFrame | None = None
    normalized_members: list[dict[str, object]] = []
    total_weight = 0.0
    for row in members:
        if not isinstance(row, dict):
            raise ValueError("members 项必须是对象。")
        member_model_id = str(row["model_id"])
        weight = float(row["weight"])
        if weight <= 0.0:
            raise ValueError(f"member={member_model_id} 的 weight 必须为正。")
        member_prediction_path = resolve_path(
            str(
                row.get(
                    "prediction_path",
                    f"data/predictions/stage1a_challengers_raw/{member_model_id}/{dataset_id}/predicted_shift.tsv.gz",
                )
            )
        )
        member_prediction = read_matrix(member_prediction_path)
        if weighted_sum is None:
            weighted_sum = member_prediction * weight
        else:
            if not weighted_sum.index.equals(member_prediction.index):
                raise ValueError(f"{member_model_id} 的 target index 与前序成员不一致。")
            if not weighted_sum.columns.equals(member_prediction.columns):
                raise ValueError(f"{member_model_id} 的 gene columns 与前序成员不一致。")
            weighted_sum = weighted_sum.add(member_prediction * weight, fill_value=0.0)
        total_weight += weight
        normalized_members.append(
            {
                "model_id": member_model_id,
                "weight": weight,
                "prediction_path": resolve_project_relative(member_prediction_path),
            }
        )

    if weighted_sum is None:
        raise ValueError("没有可融合的 member predictions。")
    predicted_shift = weighted_sum / total_weight
    predicted_shift.index.name = "target_gene"
    write_matrix(predicted_shift, prediction_path)
    json_dump(
        {
            "challenger_id": challenger_id,
            "dataset_id": dataset_id,
            "model_id": model_id,
            "fusion_rule": "weighted_average_of_pre_registered_member_predictions",
            "weight_normalization": "divide_by_sum_of_positive_weights",
            "members": normalized_members,
            "total_weight": total_weight,
            "prediction_path": resolve_project_relative(prediction_path),
            "claim_scope": "当前仅作为 non-formal single-seed challenger；在 exploratory override 下实现/运行，不构成 formal superiority 或 entrant ready。",
        },
        metadata_path,
    )
    print(f"已写出: {resolve_project_relative(prediction_path)}")
    print(f"已写出: {resolve_project_relative(metadata_path)}")
    print(
        json.dumps(
            {
                "challenger_id": challenger_id,
                "dataset_id": dataset_id,
                "model_id": model_id,
                "n_members": len(normalized_members),
                "total_weight": total_weight,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
