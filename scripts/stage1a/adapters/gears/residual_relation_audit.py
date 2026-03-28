from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    json_dump,
    resolve_project_relative,
    safe_pearson,
    safe_spearman,
)


DEFAULT_RAW_SIGNAL_ROOT = PROJECT_ROOT / "reports/stage1a_audit/gears_raw_signal_audit"
DEFAULT_COVERAGE_ROOT = PROJECT_ROOT / "reports/stage1a_audit/gears_coverage_audit"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "reports/stage1a_audit/gears_residual_relation_audit"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="联查 GEARS residual 强度与 support / abundance 的关系。")
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


def pair_stat(frame: pd.DataFrame, x_col: str, y_col: str) -> dict[str, float | str]:
    x = frame[x_col].to_numpy(dtype=float, copy=False)
    y = frame[y_col].to_numpy(dtype=float, copy=False)
    return {
        "x": x_col,
        "y": y_col,
        "pearson": safe_pearson(x, y),
        "spearman": safe_spearman(x, y),
    }


def main() -> None:
    args = build_parser().parse_args()
    run_config = load_run_config(args.run_config)

    dataset_id = str(coalesce_arg(run_config, "dataset_id", "tian_2019_day7neuron"))
    model_id = str(coalesce_arg(run_config, "model_id", "gears_stage1a_formal"))
    raw_signal_root = resolve_path(coalesce_arg(run_config, "raw_signal_root", DEFAULT_RAW_SIGNAL_ROOT))
    coverage_root = resolve_path(coalesce_arg(run_config, "coverage_root", DEFAULT_COVERAGE_ROOT))
    output_root = resolve_path(coalesce_arg(run_config, "output_root", DEFAULT_OUTPUT_ROOT))
    assert raw_signal_root is not None
    assert coverage_root is not None
    assert output_root is not None

    raw_signal_path = raw_signal_root / model_id / dataset_id / "per_target_diagnostics.tsv"
    coverage_path = coverage_root / model_id / dataset_id / "heldout_targets.tsv"

    raw_signal = pd.read_csv(raw_signal_path, sep="\t")
    coverage = pd.read_csv(coverage_path, sep="\t")
    merged = raw_signal.merge(coverage, on="target_gene", how="inner")
    if merged.empty:
        raise ValueError("raw_signal 与 coverage 没有 target overlap。")

    relation_pairs = [
        ("n_cells_perturbed_eligibility", "delta_rmse_to_truth"),
        ("n_cells_perturbed_eligibility", "delta_pearson_to_truth"),
        ("support_rank_ascending", "delta_rmse_to_truth"),
        ("support_rank_ascending", "delta_pearson_to_truth"),
        ("target_control_mean_expression", "delta_rmse_to_truth"),
        ("target_control_mean_expression", "delta_pearson_to_truth"),
        ("target_perturbed_mean_expression", "delta_rmse_to_truth"),
        ("target_perturbed_mean_expression", "delta_pearson_to_truth"),
        ("truth_delta_l2", "delta_rmse_to_truth"),
        ("truth_delta_l2", "delta_pearson_to_truth"),
        ("truth_delta_vs_control_rmse", "delta_rmse_to_truth"),
        ("truth_delta_vs_control_rmse", "delta_pearson_to_truth"),
        ("target_control_detection_fraction", "delta_rmse_to_truth"),
        ("target_control_detection_fraction", "delta_pearson_to_truth"),
    ]
    relation_stats = [pair_stat(merged, x_col, y_col) for x_col, y_col in relation_pairs]

    merged["support_bucket"] = merged["support_stratum"].astype(str)
    merged["target_abundance_bucket"] = pd.cut(
        merged["target_control_mean_expression"],
        bins=[-1.0, 0.001, 0.01, 1.0],
        labels=["ultra_low", "low", "moderate_plus"],
    ).astype(str)

    summary = {
        "stage": "gears_residual_relation_audit",
        "dataset_id": dataset_id,
        "model_id": model_id,
        "n_targets": int(len(merged)),
        "sources": {
            "raw_signal_path": resolve_project_relative(raw_signal_path),
            "coverage_path": resolve_project_relative(coverage_path),
        },
        "relation_stats": relation_stats,
        "targets_sorted_by_delta_rmse": merged.sort_values("delta_rmse_to_truth", ascending=False)[
            [
                "target_gene",
                "delta_rmse_to_truth",
                "delta_pearson_to_truth",
                "n_cells_perturbed_eligibility",
                "support_stratum",
                "target_control_mean_expression",
                "truth_delta_vs_control_rmse",
            ]
        ].to_dict(orient="records"),
        "targets_sorted_by_delta_pearson": merged.sort_values("delta_pearson_to_truth", ascending=True)[
            [
                "target_gene",
                "delta_pearson_to_truth",
                "delta_rmse_to_truth",
                "n_cells_perturbed_eligibility",
                "support_stratum",
                "target_control_mean_expression",
                "truth_delta_vs_control_rmse",
            ]
        ].to_dict(orient="records"),
        "bucket_summary": merged.groupby(["support_bucket", "target_abundance_bucket"], dropna=False)
        .agg(
            n_targets=("target_gene", "count"),
            delta_rmse_to_truth_mean=("delta_rmse_to_truth", "mean"),
            delta_pearson_to_truth_mean=("delta_pearson_to_truth", "mean"),
            delta_strength_ratio_vs_truth_mean=("delta_strength_ratio_vs_truth", "mean"),
        )
        .reset_index()
        .to_dict(orient="records"),
    }

    output_dir = output_root / model_id / dataset_id
    output_dir.mkdir(parents=True, exist_ok=True)
    merged_path = output_dir / "joined_target_relations.tsv"
    summary_path = output_dir / "summary.json"
    merged.to_csv(merged_path, sep="\t", index=False)
    json_dump(summary, summary_path)

    print(f"已写出: {resolve_project_relative(merged_path)}")
    print(f"已写出: {resolve_project_relative(summary_path)}")
    print(merged.sort_values('delta_rmse_to_truth', ascending=False).to_string(index=False))


if __name__ == "__main__":
    main()
