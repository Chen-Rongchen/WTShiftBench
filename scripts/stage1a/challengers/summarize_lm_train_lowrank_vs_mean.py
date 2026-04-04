from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from scripts.stage1a.challengers.common import DEFAULT_CHALLENGER_REGISTRY_PATH, resolve_path


DEFAULT_BATCH_CONFIG = Path("configs/stage1a/challengers/lm_train_lowrank_batch.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="汇总 lm_train_lowrank 与 mean_shift_baseline 的同指标对比。")
    parser.add_argument("--batch-config", default=str(DEFAULT_BATCH_CONFIG))
    parser.add_argument("--challenger-registry", default=str(DEFAULT_CHALLENGER_REGISTRY_PATH))
    return parser


def load_json_mapping(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload


def classify_against_mean(
    pearson_gain: float,
    rmse_ratio: float,
    jaccard_gain: float,
    threshold: dict[str, float],
) -> str:
    if pearson_gain > 0.0 and rmse_ratio < 1.0 and jaccard_gain >= 0.0:
        return "ran_and_better_than_mean"
    catastrophic = (
        pearson_gain < -float(threshold["catastrophic_pearson_drop"])
        or rmse_ratio > float(threshold["catastrophic_rmse_ratio"])
    )
    if not catastrophic and (
        pearson_gain >= -float(threshold["pearson_mean_drop_max"])
        and rmse_ratio <= float(threshold["rmse_mean_ratio_max"])
        and jaccard_gain >= -float(threshold["top50_jaccard_mean_drop_max"])
    ):
        return "ran_and_close_to_mean"
    return "ran_and_worse_than_mean"


def main() -> None:
    args = build_parser().parse_args()
    batch_payload = load_json_mapping(resolve_path(args.batch_config))
    registry_payload = load_json_mapping(resolve_path(args.challenger_registry))
    threshold = registry_payload["close_to_mean_working_threshold"]
    challenger_id = str(batch_payload["challenger_id"])

    dataset_ids = [str(item) for item in batch_payload["dataset_ids"]]
    n_components_grid = [int(item) for item in batch_payload["n_components_grid"]]
    ridge_lambda_grid = [float(item) for item in batch_payload["ridge_lambda_grid"]]
    model_prefix = str(batch_payload.get("model_prefix", "lm_train_lowrank"))
    baseline_model_id = str(batch_payload["baseline_model_id"])

    rows: list[dict[str, object]] = []
    for dataset_id in dataset_ids:
        baseline_path = resolve_path(f"reports/stage1a/model_eval/{baseline_model_id}/{dataset_id}/dataset_score_summary.json")
        baseline_summary = load_json_mapping(baseline_path)
        baseline_scores = baseline_summary["aggregate_scores"]
        for n_components in n_components_grid:
            for ridge_lambda in ridge_lambda_grid:
                model_id = f"{model_prefix}__k{n_components}__a{str(ridge_lambda).replace('.', 'p')}"
                summary_path = resolve_path(f"reports/stage1a/model_eval/{model_id}/{dataset_id}/dataset_score_summary.json")
                if not summary_path.exists():
                    rows.append(
                        {
                            "dataset_id": dataset_id,
                            "model_id": model_id,
                            "n_components": n_components,
                            "ridge_lambda": ridge_lambda,
                            "result_bucket": "failed_runtime",
                        }
                    )
                    continue
                candidate_summary = load_json_mapping(summary_path)
                candidate_scores = candidate_summary["aggregate_scores"]
                pearson_gain = float(candidate_scores["pearson_mean"]) - float(baseline_scores["pearson_mean"])
                rmse_ratio = float(candidate_scores["rmse_mean"]) / float(baseline_scores["rmse_mean"])
                jaccard_gain = float(candidate_scores["top50_jaccard_mean"]) - float(baseline_scores["top50_jaccard_mean"])
                rows.append(
                    {
                        "dataset_id": dataset_id,
                        "model_id": model_id,
                        "n_components": n_components,
                        "ridge_lambda": ridge_lambda,
                        "pearson_mean": float(candidate_scores["pearson_mean"]),
                        "rmse_mean": float(candidate_scores["rmse_mean"]),
                        "top50_jaccard_mean": float(candidate_scores["top50_jaccard_mean"]),
                        "baseline_pearson_mean": float(baseline_scores["pearson_mean"]),
                        "baseline_rmse_mean": float(baseline_scores["rmse_mean"]),
                        "baseline_top50_jaccard_mean": float(baseline_scores["top50_jaccard_mean"]),
                        "pearson_gain_vs_mean": pearson_gain,
                        "rmse_ratio_vs_mean": rmse_ratio,
                        "top50_jaccard_gain_vs_mean": jaccard_gain,
                        "result_bucket": classify_against_mean(pearson_gain, rmse_ratio, jaccard_gain, threshold),
                    }
                )

    frame = pd.DataFrame(rows).sort_values(["dataset_id", "result_bucket", "n_components", "ridge_lambda"]).reset_index(drop=True)
    output_root = resolve_path(f"reports/stage1a/challengers/{challenger_id}")
    output_root.mkdir(parents=True, exist_ok=True)
    summary_tsv_path = output_root / f"{challenger_id}_vs_mean_summary.tsv"
    summary_json_path = output_root / f"{challenger_id}_vs_mean_summary.json"
    frame.to_csv(summary_tsv_path, sep="\t", index=False)
    summary_json_path.write_text(
        json.dumps(
            {
                "stage": "stage1a_challenger_summary",
                "challenger_id": challenger_id,
                "baseline_model_id": baseline_model_id,
                "threshold": threshold,
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"已写出: {summary_tsv_path}")
    print(f"已写出: {summary_json_path}")


if __name__ == "__main__":
    main()
