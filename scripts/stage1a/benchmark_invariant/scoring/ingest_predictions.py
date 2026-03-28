from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    PROJECT_ROOT,
    align_prediction_to_truth,
    json_dump,
    load_main_aligned_truth_entry,
    read_matrix,
    resolve_project_relative,
    write_matrix,
)


DEFAULT_PREDICTION_ROOT = PROJECT_ROOT / "data/predictions/stage1a_main_aligned"
DEFAULT_REPORT_ROOT = PROJECT_ROOT / "reports/stage1a/prediction_alignment"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage 1A 模型预测接入与主空间对齐。")
    parser.add_argument("--run-config")
    parser.add_argument("--dataset-id")
    parser.add_argument("--model-id")
    parser.add_argument("--prediction-path")
    parser.add_argument("--prediction-space")
    parser.add_argument("--output-path")
    parser.add_argument("--summary-path")
    parser.add_argument("--manifest-path")
    parser.add_argument(
        "--allow-missing-targets",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--allow-missing-genes",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    return parser


def load_run_config(run_config_path: str | None) -> dict[str, object]:
    if not run_config_path:
        return {}
    payload = yaml.safe_load(Path(run_config_path).read_text(encoding="utf-8")) or {}
    return payload


def coalesce_arg(cli_value, config: dict[str, object], key: str):
    if cli_value is not None:
        return cli_value
    return config.get(key)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run_config = load_run_config(args.run_config)

    dataset_id = coalesce_arg(args.dataset_id, run_config, "dataset_id")
    model_id = coalesce_arg(args.model_id, run_config, "model_id")
    prediction_path_value = coalesce_arg(args.prediction_path, run_config, "prediction_path")
    prediction_space = coalesce_arg(args.prediction_space, run_config, "prediction_space")
    output_path_value = coalesce_arg(args.output_path, run_config, "output_path")
    summary_path_value = coalesce_arg(args.summary_path, run_config, "summary_path")
    manifest_path_value = coalesce_arg(args.manifest_path, run_config, "manifest_path")
    allow_missing_targets_value = coalesce_arg(
        args.allow_missing_targets, run_config, "allow_missing_targets"
    )
    allow_missing_genes_value = coalesce_arg(
        args.allow_missing_genes, run_config, "allow_missing_genes"
    )
    allow_missing_targets = (
        True if allow_missing_targets_value is None else bool(allow_missing_targets_value)
    )
    allow_missing_genes = (
        True if allow_missing_genes_value is None else bool(allow_missing_genes_value)
    )

    required = {
        "dataset_id": dataset_id,
        "model_id": model_id,
        "prediction_path": prediction_path_value,
        "prediction_space": prediction_space,
    }
    missing = [key for key, value in required.items() if value in {None, ""}]
    if missing:
        raise ValueError(f"缺少必填参数: {missing}")

    prediction_path = Path(str(prediction_path_value))
    if not prediction_path.is_absolute():
        prediction_path = PROJECT_ROOT / prediction_path

    output_path = (
        Path(str(output_path_value))
        if output_path_value
        else DEFAULT_PREDICTION_ROOT / str(model_id) / str(dataset_id) / "predicted_shift_aligned.tsv.gz"
    )
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    summary_path = (
        Path(str(summary_path_value))
        if summary_path_value
        else DEFAULT_REPORT_ROOT / str(model_id) / str(dataset_id) / "alignment_summary.json"
    )
    if not summary_path.is_absolute():
        summary_path = PROJECT_ROOT / summary_path

    manifest_path = (
        Path(str(manifest_path_value))
        if manifest_path_value
        else DEFAULT_REPORT_ROOT / str(model_id) / str(dataset_id) / "alignment_manifest.json"
    )
    if not manifest_path.is_absolute():
        manifest_path = PROJECT_ROOT / manifest_path

    prediction = read_matrix(prediction_path)
    truth_entry = load_main_aligned_truth_entry(str(dataset_id))
    truth = read_matrix(truth_entry.path)

    aligned, summary, manifest = align_prediction_to_truth(
        prediction=prediction,
        truth=truth,
        dataset_id=str(dataset_id),
        model_id=str(model_id),
        prediction_path=prediction_path,
        output_path=output_path,
        prediction_space=str(prediction_space),
        allow_missing_targets=allow_missing_targets,
        allow_missing_genes=allow_missing_genes,
    )
    write_matrix(aligned, output_path)
    json_dump(summary, summary_path)
    json_dump(manifest, manifest_path)

    print(f"已写出: {resolve_project_relative(output_path)}")
    print(f"已写出: {resolve_project_relative(summary_path)}")
    print(f"已写出: {resolve_project_relative(manifest_path)}")


if __name__ == "__main__":
    main()
