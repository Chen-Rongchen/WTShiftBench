from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from scripts.stage1a.adapters.common.runtime import resolve_path
from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT
from scripts.stage1a.challengers.common import resolve_dataset_formal_h5ad_path


DEFAULT_BATCH_CONFIG = PROJECT_ROOT / "configs/stage1a/challengers/rf_targetfeat_lowrank_batch.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="批量运行 rf_targetfeat_lowrank，并接入现有 scoring 主线。")
    parser.add_argument("--batch-config", default=str(DEFAULT_BATCH_CONFIG))
    parser.add_argument("--skip-build", action="store_true")
    return parser


def load_json_mapping(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload


def run_command(command: list[str]) -> None:
    print(f"开始执行: {' '.join(command)}")
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    args = build_parser().parse_args()
    payload = load_json_mapping(resolve_path(args.batch_config))
    challenger_id = str(payload["challenger_id"])
    feature_id = str(payload["feature_id"])
    dataset_ids = [str(item) for item in payload["dataset_ids"]]
    feature_components_grid = [int(item) for item in payload["feature_components_grid"]]
    latent_rank_grid = [int(item) for item in payload["latent_rank_grid"]]
    max_depth_grid = [int(item) for item in payload["max_depth_grid"]]
    n_estimators = int(payload["n_estimators"])
    model_prefix = str(payload.get("model_prefix", challenger_id))
    run_config_root = PROJECT_ROOT / "artifacts/stage1a_challengers" / challenger_id / "run_configs"
    run_config_root.mkdir(parents=True, exist_ok=True)

    run_configs: list[str] = []
    materialized_specs: list[Path] = []
    for dataset_id in dataset_ids:
        formal_h5ad_path = str(resolve_dataset_formal_h5ad_path(dataset_id).relative_to(PROJECT_ROOT))
        for feature_components in feature_components_grid:
            for latent_rank in latent_rank_grid:
                for max_depth in max_depth_grid:
                    model_id = f"{model_prefix}__fc{feature_components}__lr{latent_rank}__md{max_depth}"
                    run_config_path = run_config_root / f"{model_id}__{dataset_id}.json"
                    run_payload = {
                        "challenger_id": challenger_id,
                        "dataset_id": dataset_id,
                        "model_id": model_id,
                        "feature_id": feature_id,
                        "feature_components": feature_components,
                        "latent_rank": latent_rank,
                        "max_depth": max_depth,
                        "n_estimators": n_estimators,
                        "formal_h5ad_path": formal_h5ad_path,
                        "prediction_path": f"data/predictions/stage1a_challengers_raw/{model_id}/{dataset_id}/predicted_shift.tsv.gz",
                        "metadata_path": f"data/predictions/stage1a_challengers_raw/{model_id}/{dataset_id}/adapter_metadata.json",
                        "prediction_space": "X_pseudobulk_delta",
                        "output_path": f"data/predictions/stage1a_main_aligned/{model_id}/{dataset_id}/predicted_shift_aligned.tsv.gz",
                        "summary_path": f"reports/stage1a/prediction_alignment/{model_id}/{dataset_id}/alignment_summary.json",
                        "manifest_path": f"reports/stage1a/prediction_alignment/{model_id}/{dataset_id}/alignment_manifest.json",
                        "allow_missing_targets": False,
                        "allow_missing_genes": False,
                    }
                    run_config_path.write_text(json.dumps(run_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    run_configs.append(str(run_config_path.relative_to(PROJECT_ROOT)))
                    materialized_specs.append(run_config_path)

    if not args.skip_build:
        for run_config_path in materialized_specs:
            run_command([sys.executable, "-m", "scripts.stage1a.challengers.build_rf_targetfeat_lowrank_predictions", "--run-config", str(run_config_path)])

    materialized_batch_path = PROJECT_ROOT / "artifacts/stage1a_challengers" / challenger_id / "run_batch_scoring.json"
    materialized_batch_path.write_text(json.dumps({"run_configs": run_configs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    run_command([sys.executable, "-m", "scripts.stage1a.benchmark_invariant.scoring.run_batch_scoring_pipeline", "--batch-config", str(materialized_batch_path), "--topk", "50"])


if __name__ == "__main__":
    main()
