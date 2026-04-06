from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from scripts.stage1a.adapters.common.runtime import resolve_path
from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT
from scripts.stage1a.challengers.common import resolve_dataset_formal_h5ad_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="批量运行 pretrained feature ridge challenger，并接入 scoring 主线。")
    parser.add_argument("--batch-config", required=True)
    parser.add_argument("--skip-build", action="store_true")
    return parser


def alpha_slug(value: float) -> str:
    return str(value).replace(".", "p")


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
    batch_config_path = resolve_path(args.batch_config)
    payload = load_json_mapping(batch_config_path)

    challenger_id = str(payload["challenger_id"])
    feature_id = str(payload["feature_id"])
    dataset_ids = [str(item) for item in payload["dataset_ids"]]
    n_components_grid = [int(item) for item in payload["n_components_grid"]]
    ridge_lambda_grid = [float(item) for item in payload["ridge_lambda_grid"]]
    model_prefix = str(payload["model_prefix"])

    run_config_root = PROJECT_ROOT / "artifacts/stage1a_challengers" / challenger_id / "run_configs"
    run_config_root.mkdir(parents=True, exist_ok=True)

    run_configs: list[str] = []
    materialized_paths: list[Path] = []
    for dataset_id in dataset_ids:
        formal_h5ad_path = str(resolve_dataset_formal_h5ad_path(dataset_id).relative_to(PROJECT_ROOT))
        for n_components in n_components_grid:
            for ridge_lambda in ridge_lambda_grid:
                model_id = f"{model_prefix}__k{n_components}__a{alpha_slug(ridge_lambda)}"
                run_config_path = run_config_root / f"{model_id}__{dataset_id}.json"
                run_payload = {
                    "challenger_id": challenger_id,
                    "dataset_id": dataset_id,
                    "model_id": model_id,
                    "feature_id": feature_id,
                    "n_components": n_components,
                    "ridge_lambda": ridge_lambda,
                    "formal_h5ad_path": formal_h5ad_path,
                    "prediction_path": f"data/predictions/stage1a_challengers_raw/{model_id}/{dataset_id}/predicted_shift.tsv.gz",
                    "metadata_path": f"data/predictions/stage1a_challengers_raw/{model_id}/{dataset_id}/adapter_metadata.json",
                    "prediction_space": "X_pseudobulk_delta",
                    "output_path": f"data/predictions/stage1a_main_aligned/{model_id}/{dataset_id}/predicted_shift_aligned.tsv.gz",
                    "summary_path": f"reports/stage1a/prediction_alignment/{model_id}/{dataset_id}/alignment_summary.json",
                    "manifest_path": f"reports/stage1a/prediction_alignment/{model_id}/{dataset_id}/alignment_manifest.json",
                    "allow_missing_targets": False,
                    "allow_missing_genes": False
                }
                run_config_path.write_text(json.dumps(run_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                run_configs.append(str(run_config_path.relative_to(PROJECT_ROOT)))
                materialized_paths.append(run_config_path)

    if not args.skip_build:
        for run_config_path in materialized_paths:
            run_command(
                [
                    sys.executable,
                    "-m",
                    "scripts.stage1a.challengers.build_external_feature_ridge_predictions",
                    "--run-config",
                    str(run_config_path),
                ]
            )

    scoring_batch_path = PROJECT_ROOT / "artifacts/stage1a_challengers" / challenger_id / "run_batch_scoring.json"
    scoring_batch_path.write_text(json.dumps({"run_configs": run_configs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    run_command(
        [
            sys.executable,
            "-m",
            "scripts.stage1a.benchmark_invariant.scoring.run_batch_scoring_pipeline",
            "--batch-config",
            str(scoring_batch_path),
            "--topk",
            "50",
        ]
    )


if __name__ == "__main__":
    main()
