from __future__ import annotations

import argparse
import json
import subprocess
import sys
import traceback
from pathlib import Path

from scripts.stage1a.adapters.common.runtime import resolve_path
from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT
from scripts.stage1a.challengers.common import resolve_dataset_formal_h5ad_path


DEFAULT_BATCH_CONFIG = PROJECT_ROOT / "configs/stage1a/challengers/lm_train_lowrank_batch.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按冻结 grid 运行 lm_train_lowrank，并接入现有 scoring 主线。")
    parser.add_argument(
        "--batch-config",
        default=str(DEFAULT_BATCH_CONFIG),
        help="lm_train_lowrank batch JSON。",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="跳过 challenger 原始 predicted_shift 构建，只执行 ingest/evaluate/render。",
    )
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
    model_prefix = str(payload.get("model_prefix", "lm_train_lowrank"))

    run_configs: list[str] = []
    run_config_root = PROJECT_ROOT / "artifacts/stage1a_challengers/lm_train_lowrank/run_configs"
    run_config_root.mkdir(parents=True, exist_ok=True)

    materialized_specs: list[Path] = []
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
                    "allow_missing_genes": False,
                }
                run_config_path.write_text(json.dumps(run_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                run_configs.append(str(run_config_path.relative_to(PROJECT_ROOT)))
                materialized_specs.append(run_config_path)

    successful_run_configs = list(run_configs) if args.skip_build else []
    failed_runs: list[dict[str, object]] = []

    if not args.skip_build:
        for run_config_path in materialized_specs:
            command = [
                sys.executable,
                "-m",
                "scripts.stage1a.challengers.build_lm_train_lowrank_predictions",
                "--run-config",
                str(run_config_path),
            ]
            try:
                run_command(command)
                successful_run_configs.append(str(run_config_path.relative_to(PROJECT_ROOT)))
            except subprocess.CalledProcessError as exc:
                failed_runs.append(
                    {
                        "run_config": str(run_config_path.relative_to(PROJECT_ROOT)),
                        "returncode": int(exc.returncode),
                        "error_type": exc.__class__.__name__,
                        "error_message": str(exc),
                        "traceback": traceback.format_exc(),
                    }
                )
                print(f"[警告] {run_config_path.name} 构建失败，退出码={exc.returncode}，继续后续配置。")

    report_path = PROJECT_ROOT / "artifacts/stage1a_challengers/lm_train_lowrank/run_batch_report.json"
    report_path.write_text(
        json.dumps(
            {
                "challenger_id": challenger_id,
                "batch_config": str(batch_config_path.relative_to(PROJECT_ROOT)),
                "skip_build": bool(args.skip_build),
                "requested_run_config_count": len(run_configs),
                "successful_run_config_count": len(successful_run_configs),
                "failed_run_config_count": len(failed_runs),
                "successful_run_configs": successful_run_configs,
                "failed_runs": failed_runs,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    if not successful_run_configs:
        raise RuntimeError(f"lm_train_lowrank batch 没有可继续 scoring 的成功 run-config。详见 {report_path}")

    materialized_batch_path = PROJECT_ROOT / "artifacts/stage1a_challengers/lm_train_lowrank/run_batch_scoring.json"
    materialized_batch_path.write_text(
        json.dumps({"run_configs": successful_run_configs}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    run_command(
        [
            sys.executable,
            "-m",
            "scripts.stage1a.benchmark_invariant.scoring.run_batch_scoring_pipeline",
            "--batch-config",
            str(materialized_batch_path),
            "--topk",
            "50",
        ]
    )
    print(f"已写出: {report_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
