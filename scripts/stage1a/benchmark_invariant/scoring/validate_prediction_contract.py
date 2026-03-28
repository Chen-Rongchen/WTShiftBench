from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    PROJECT_ROOT,
    align_prediction_to_truth,
    load_main_aligned_truth_entry,
    read_matrix,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="验证 Stage 1A predicted_shift.tsv.gz contract。")
    parser.add_argument("--run-config")
    parser.add_argument("--dataset-id")
    parser.add_argument("--model-id")
    parser.add_argument("--prediction-path")
    parser.add_argument("--prediction-space")
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


def coalesce_arg(cli_value, config: dict[str, object], key: str, default=None):
    if cli_value is not None:
        return cli_value
    if key in config:
        return config[key]
    return default


def require_arg(name: str, value: object) -> object:
    if value in {None, ""}:
        raise ValueError(f"缺少必填参数 {name}")
    return value


def main() -> None:
    args = build_parser().parse_args()
    run_config = load_run_config(args.run_config)

    dataset_id_value = coalesce_arg(args.dataset_id, run_config, "dataset_id")
    model_id_value = coalesce_arg(args.model_id, run_config, "model_id")
    prediction_path_value = coalesce_arg(args.prediction_path, run_config, "prediction_path")
    prediction_space_value = coalesce_arg(
        args.prediction_space,
        run_config,
        "prediction_space",
        "X_pseudobulk_delta",
    )
    dataset_id = str(require_arg("dataset_id", dataset_id_value))
    model_id = str(require_arg("model_id", model_id_value))
    prediction_path = Path(str(require_arg("prediction_path", prediction_path_value)))
    if not prediction_path.is_absolute():
        prediction_path = PROJECT_ROOT / prediction_path
    prediction_space = str(require_arg("prediction_space", prediction_space_value))
    allow_missing_targets = bool(
        coalesce_arg(args.allow_missing_targets, run_config, "allow_missing_targets", True)
    )
    allow_missing_genes = bool(
        coalesce_arg(args.allow_missing_genes, run_config, "allow_missing_genes", True)
    )

    prediction = read_matrix(prediction_path)
    truth_entry = load_main_aligned_truth_entry(dataset_id)
    truth = read_matrix(truth_entry.path)
    _, summary, _ = align_prediction_to_truth(
        prediction=prediction,
        truth=truth,
        dataset_id=dataset_id,
        model_id=model_id,
        prediction_path=prediction_path,
        output_path=PROJECT_ROOT / "tmp" / "stage1a_contract_validation" / "unused.tsv.gz",
        prediction_space=prediction_space,
        allow_missing_targets=allow_missing_targets,
        allow_missing_genes=allow_missing_genes,
    )

    contract_check = {
        "dataset_id": dataset_id,
        "model_id": model_id,
        "prediction_path": str(prediction_path),
        "n_targets_input": summary["n_targets_input"],
        "n_targets_expected": summary["n_targets_expected"],
        "n_genes_input": summary["n_genes_input"],
        "n_genes_expected": summary["n_genes_expected"],
        "target_coverage_fraction": summary["target_coverage_fraction"],
        "gene_coverage_fraction": summary["gene_coverage_fraction"],
        "leaderboard_eligibility_status": summary["leaderboard_eligibility_status"],
        "leaderboard_eligibility_reason": summary["leaderboard_eligibility_reason"],
        "missing_target_count": summary["missing_target_count"],
        "missing_gene_count": summary["missing_gene_count"],
        "alignment_pass": summary["alignment_pass"],
    }
    print(json.dumps(contract_check, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
