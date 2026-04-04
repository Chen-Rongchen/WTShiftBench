from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from scripts.stage1a.challengers.common import DEFAULT_CHALLENGER_REGISTRY_PATH, resolve_path


DEFAULT_BATCH_CONFIG = Path("configs/stage1a/challengers/knn_kernel_targetfeat_batch.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="汇总 knn_kernel_targetfeat 与 mean_shift_baseline 的同指标对比。")
    parser.add_argument("--batch-config", default=str(DEFAULT_BATCH_CONFIG))
    parser.add_argument("--challenger-registry", default=str(DEFAULT_CHALLENGER_REGISTRY_PATH))
    return parser


def load_json_mapping(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload


def classify(pearson_gain: float, rmse_ratio: float, jaccard_gain: float, threshold: dict[str, float]) -> str:
    if pearson_gain > 0.0 and rmse_ratio < 1.0 and jaccard_gain >= 0.0:
        return "ran_and_better_than_mean"
    catastrophic = pearson_gain < -float(threshold["catastrophic_pearson_drop"]) or rmse_ratio > float(threshold["catastrophic_rmse_ratio"])
    if not catastrophic and pearson_gain >= -float(threshold["pearson_mean_drop_max"]) and rmse_ratio <= float(threshold["rmse_mean_ratio_max"]) and jaccard_gain >= -float(threshold["top50_jaccard_mean_drop_max"]):
        return "ran_and_close_to_mean"
    return "ran_and_worse_than_mean"


def main() -> None:
    args = build_parser().parse_args()
    batch = load_json_mapping(resolve_path(args.batch_config))
    registry = load_json_mapping(resolve_path(args.challenger_registry))
    threshold = registry["close_to_mean_working_threshold"]
    challenger_id = str(batch["challenger_id"])
    rows = []
    for dataset_id in [str(x) for x in batch["dataset_ids"]]:
        baseline = load_json_mapping(resolve_path(f"reports/stage1a/model_eval/{batch['baseline_model_id']}/{dataset_id}/dataset_score_summary.json"))["aggregate_scores"]
        for n_components in [int(x) for x in batch["n_components_grid"]]:
            for n_neighbors in [int(x) for x in batch["n_neighbors_grid"]]:
                model_id = f"{batch['model_prefix']}__k{n_components}__nn{n_neighbors}"
                p = resolve_path(f"reports/stage1a/model_eval/{model_id}/{dataset_id}/dataset_score_summary.json")
                if not p.exists():
                    rows.append({"dataset_id": dataset_id, "model_id": model_id, "n_components": n_components, "n_neighbors": n_neighbors, "result_bucket": "failed_runtime"})
                    continue
                cand = load_json_mapping(p)["aggregate_scores"]
                pearson_gain = float(cand["pearson_mean"]) - float(baseline["pearson_mean"])
                rmse_ratio = float(cand["rmse_mean"]) / float(baseline["rmse_mean"])
                jaccard_gain = float(cand["top50_jaccard_mean"]) - float(baseline["top50_jaccard_mean"])
                rows.append({"dataset_id": dataset_id, "model_id": model_id, "n_components": n_components, "n_neighbors": n_neighbors, "pearson_mean": float(cand["pearson_mean"]), "rmse_mean": float(cand["rmse_mean"]), "top50_jaccard_mean": float(cand["top50_jaccard_mean"]), "baseline_pearson_mean": float(baseline["pearson_mean"]), "baseline_rmse_mean": float(baseline["rmse_mean"]), "baseline_top50_jaccard_mean": float(baseline["top50_jaccard_mean"]), "pearson_gain_vs_mean": pearson_gain, "rmse_ratio_vs_mean": rmse_ratio, "top50_jaccard_gain_vs_mean": jaccard_gain, "result_bucket": classify(pearson_gain, rmse_ratio, jaccard_gain, threshold)})
    out = resolve_path(f"reports/stage1a/challengers/{challenger_id}")
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / f"{challenger_id}_vs_mean_summary.tsv", sep="\t", index=False)
    (out / f"{challenger_id}_vs_mean_summary.json").write_text(json.dumps({"rows": rows, "threshold": threshold}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
