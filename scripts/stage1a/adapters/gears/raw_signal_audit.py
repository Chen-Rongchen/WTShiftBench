from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    json_dump,
    load_main_aligned_truth_entry,
    read_matrix,
    resolve_project_relative,
    safe_cosine,
    safe_pearson,
    rmse,
)

DEFAULT_AUDIT_ROOT = PROJECT_ROOT / "reports/stage1a_audit/gears_export_space/gears_stage1a_formal"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "reports/stage1a_audit/gears_raw_signal_audit"
TRUTH_PSEUDOBULK_ROOT = PROJECT_ROOT / "data/truth/stage1a_pseudobulk_delta"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="审计 GEARS raw predicted expression 的 target-level signal 强度。")
    parser.add_argument("--run-config", required=True)
    return parser


def load_run_config(run_config_path: str) -> dict[str, object]:
    return yaml.safe_load(Path(run_config_path).read_text(encoding="utf-8")) or {}


def coalesce_arg(config: dict[str, object], key: str, default=None):
    if key in config:
        return config[key]
    return default


def resolve_path(path_value: str | Path | None) -> Path | None:
    if path_value is None:
        return None
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def read_control_truth(dataset_id: str) -> pd.DataFrame:
    return pd.read_csv(
        TRUTH_PSEUDOBULK_ROOT / dataset_id / "control_pseudobulk.tsv.gz",
        sep="\t",
        index_col=0,
    )


def read_perturbed_truth(dataset_id: str) -> pd.DataFrame:
    return pd.read_csv(
        TRUTH_PSEUDOBULK_ROOT / dataset_id / "perturbed_pseudobulk.tsv.gz",
        sep="\t",
    ).set_index("target_gene")


def abs_p95(values: np.ndarray) -> float:
    return float(np.quantile(np.abs(values), 0.95))


def l2_norm(values: np.ndarray) -> float:
    return float(np.linalg.norm(values))


def safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0.0:
        return None
    return float(numerator / denominator)


def overlap_targets(frame: pd.DataFrame, truth: pd.DataFrame) -> list[str]:
    truth_set = set(truth.index.astype(str))
    return [target for target in frame.index.astype(str) if target in truth_set]


def overlap_genes(frame: pd.DataFrame, truth: pd.DataFrame) -> list[str]:
    truth_set = set(truth.columns.astype(str))
    return [gene for gene in frame.columns.astype(str) if gene in truth_set]


def summarize_records(records: list[dict[str, object]], dataset_id: str, model_id: str) -> dict[str, object]:
    diagnostics = pd.DataFrame.from_records(records)
    near_control_mask = diagnostics["predicted_delta_vs_control_rmse_ratio"].fillna(0.0) <= 0.25
    weak_delta_mask = diagnostics["delta_strength_ratio_vs_truth"].fillna(0.0) <= 0.25
    over_strong_delta_mask = diagnostics["delta_strength_ratio_vs_truth"].fillna(0.0) >= 2.0
    negative_delta_corr_mask = diagnostics["delta_pearson_to_truth"] <= 0.0

    worst_delta = diagnostics.sort_values("delta_rmse_to_truth", ascending=False).head(10)
    strongest_delta = diagnostics.sort_values("delta_strength_ratio_vs_truth", ascending=False).head(10)
    closest_to_control = diagnostics.sort_values("predicted_delta_vs_control_rmse_ratio", ascending=True).head(10)

    return {
        "stage": "gears_raw_signal_audit",
        "dataset_id": dataset_id,
        "model_id": model_id,
        "n_targets": int(len(diagnostics)),
        "median_raw_negative_fraction": float(diagnostics["raw_negative_fraction"].median()),
        "median_shift_negative_fraction": float(diagnostics["shift_negative_fraction"].median()),
        "median_raw_scale_ratio_vs_perturbed_truth": float(diagnostics["raw_scale_ratio_vs_perturbed_truth"].median()),
        "median_delta_strength_ratio_vs_truth": float(diagnostics["delta_strength_ratio_vs_truth"].median()),
        "median_predicted_delta_vs_control_rmse_ratio": float(diagnostics["predicted_delta_vs_control_rmse_ratio"].median()),
        "median_truth_delta_vs_control_rmse": float(diagnostics["truth_delta_vs_control_rmse"].median()),
        "fraction_targets_near_control": float(near_control_mask.mean()),
        "fraction_targets_weak_delta_strength": float(weak_delta_mask.mean()),
        "fraction_targets_over_strong_delta": float(over_strong_delta_mask.mean()),
        "fraction_targets_non_positive_delta_pearson": float(negative_delta_corr_mask.mean()),
        "worst_delta_rmse_targets": worst_delta[
            [
                "target_gene",
                "delta_rmse_to_truth",
                "delta_pearson_to_truth",
                "delta_strength_ratio_vs_truth",
                "predicted_delta_vs_control_rmse_ratio",
            ]
        ].to_dict(orient="records"),
        "strongest_delta_targets": strongest_delta[
            [
                "target_gene",
                "delta_strength_ratio_vs_truth",
                "predicted_delta_vs_control_rmse_ratio",
                "delta_pearson_to_truth",
                "delta_rmse_to_truth",
            ]
        ].to_dict(orient="records"),
        "closest_to_control_targets": closest_to_control[
            [
                "target_gene",
                "predicted_delta_vs_control_rmse_ratio",
                "truth_delta_vs_control_rmse",
                "delta_strength_ratio_vs_truth",
                "delta_pearson_to_truth",
            ]
        ].to_dict(orient="records"),
    }


def main() -> None:
    args = build_parser().parse_args()
    run_config = load_run_config(args.run_config)

    dataset_id = str(coalesce_arg(run_config, "dataset_id", "tian_2019_day7neuron"))
    model_id = str(coalesce_arg(run_config, "model_id", "gears_stage1a_formal"))

    audit_root = resolve_path(coalesce_arg(run_config, "audit_root", DEFAULT_AUDIT_ROOT))
    output_root = resolve_path(coalesce_arg(run_config, "output_root", DEFAULT_OUTPUT_ROOT))
    assert audit_root is not None
    assert output_root is not None

    dataset_audit_root = audit_root / dataset_id
    dataset_output_root = output_root / model_id / dataset_id
    dataset_output_root.mkdir(parents=True, exist_ok=True)

    predicted_expression_raw = read_matrix(dataset_audit_root / "predicted_expression_raw.tsv.gz")
    control_values_full = read_matrix(dataset_audit_root / "control_values_full.tsv.gz")
    predicted_shift = read_matrix(dataset_audit_root / "predicted_shift_pre_align.tsv.gz")

    truth_shift = read_matrix(load_main_aligned_truth_entry(dataset_id).path)
    perturbed_truth = read_perturbed_truth(dataset_id)
    control_truth = read_control_truth(dataset_id)

    target_order = overlap_targets(predicted_shift, truth_shift)
    if not target_order:
        raise ValueError(f"{dataset_id} 没有可审计的 target overlap。")

    gene_order = overlap_genes(predicted_shift, truth_shift)
    if not gene_order:
        raise ValueError(f"{dataset_id} 没有可审计的 gene overlap。")

    predicted_expression_raw = predicted_expression_raw.loc[target_order, gene_order]
    predicted_shift = predicted_shift.loc[target_order, gene_order]
    truth_shift = truth_shift.loc[target_order, gene_order]
    perturbed_truth = perturbed_truth.loc[target_order, gene_order]
    control_row = control_values_full.loc["control", gene_order].to_numpy(dtype=np.float64, copy=False)
    control_truth_row = control_truth.loc["control", gene_order].to_numpy(dtype=np.float64, copy=False)

    records: list[dict[str, object]] = []
    for target in target_order:
        predicted_raw_vec = predicted_expression_raw.loc[target].to_numpy(dtype=np.float64, copy=False)
        predicted_shift_vec = predicted_shift.loc[target].to_numpy(dtype=np.float64, copy=False)
        truth_raw_vec = perturbed_truth.loc[target].to_numpy(dtype=np.float64, copy=False)
        truth_shift_vec = truth_shift.loc[target].to_numpy(dtype=np.float64, copy=False)

        predicted_delta_vs_control_rmse = rmse(predicted_raw_vec, control_row)
        truth_delta_vs_control_rmse = rmse(truth_raw_vec, control_truth_row)

        predicted_delta_l2 = l2_norm(predicted_shift_vec)
        truth_delta_l2 = l2_norm(truth_shift_vec)
        control_l2 = l2_norm(control_row)

        records.append(
            {
                "target_gene": target,
                "raw_negative_fraction": float(np.mean(predicted_raw_vec < 0.0)),
                "shift_negative_fraction": float(np.mean(predicted_shift_vec < 0.0)),
                "raw_abs_p95": abs_p95(predicted_raw_vec),
                "truth_raw_abs_p95": abs_p95(truth_raw_vec),
                "raw_scale_ratio_vs_perturbed_truth": safe_ratio(abs_p95(predicted_raw_vec), abs_p95(truth_raw_vec)),
                "raw_pearson_to_perturbed_truth": safe_pearson(predicted_raw_vec, truth_raw_vec),
                "raw_cosine_to_perturbed_truth": safe_cosine(predicted_raw_vec, truth_raw_vec),
                "raw_rmse_to_perturbed_truth": rmse(predicted_raw_vec, truth_raw_vec),
                "predicted_delta_l2": predicted_delta_l2,
                "truth_delta_l2": truth_delta_l2,
                "control_expression_l2": control_l2,
                "delta_strength_ratio_vs_truth": safe_ratio(predicted_delta_l2, truth_delta_l2),
                "predicted_delta_vs_control_l2_ratio": safe_ratio(predicted_delta_l2, control_l2),
                "truth_delta_vs_control_l2_ratio": safe_ratio(truth_delta_l2, control_l2),
                "predicted_delta_vs_control_rmse": predicted_delta_vs_control_rmse,
                "truth_delta_vs_control_rmse": truth_delta_vs_control_rmse,
                "predicted_delta_vs_control_rmse_ratio": safe_ratio(
                    predicted_delta_vs_control_rmse,
                    truth_delta_vs_control_rmse,
                ),
                "delta_pearson_to_truth": safe_pearson(predicted_shift_vec, truth_shift_vec),
                "delta_cosine_to_truth": safe_cosine(predicted_shift_vec, truth_shift_vec),
                "delta_rmse_to_truth": rmse(predicted_shift_vec, truth_shift_vec),
            }
        )

    diagnostics = pd.DataFrame.from_records(records).sort_values("delta_rmse_to_truth", ascending=False).reset_index(drop=True)
    summary = summarize_records(records, dataset_id=dataset_id, model_id=model_id)
    summary["sources"] = {
        "predicted_expression_raw_path": resolve_project_relative(dataset_audit_root / "predicted_expression_raw.tsv.gz"),
        "control_values_full_path": resolve_project_relative(dataset_audit_root / "control_values_full.tsv.gz"),
        "predicted_shift_pre_align_path": resolve_project_relative(dataset_audit_root / "predicted_shift_pre_align.tsv.gz"),
        "truth_shift_path": resolve_project_relative(load_main_aligned_truth_entry(dataset_id).path),
        "perturbed_truth_path": resolve_project_relative(TRUTH_PSEUDOBULK_ROOT / dataset_id / "perturbed_pseudobulk.tsv.gz"),
        "control_truth_path": resolve_project_relative(TRUTH_PSEUDOBULK_ROOT / dataset_id / "control_pseudobulk.tsv.gz"),
    }

    diagnostics_path = dataset_output_root / "per_target_diagnostics.tsv"
    summary_path = dataset_output_root / "summary.json"
    diagnostics.to_csv(diagnostics_path, sep="\t", index=False)
    json_dump(summary, summary_path)

    print(f"已写出: {resolve_project_relative(diagnostics_path)}")
    print(f"已写出: {resolve_project_relative(summary_path)}")
    print(diagnostics.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
