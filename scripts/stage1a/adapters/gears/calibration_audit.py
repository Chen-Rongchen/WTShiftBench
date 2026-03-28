from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    evaluate_prediction_frame,
    load_main_aligned_truth_entry,
    read_matrix,
    resolve_project_relative,
)
DEFAULT_AUDIT_ROOT = PROJECT_ROOT / "reports/stage1a_audit/gears_export_space/gears_stage1a_formal"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "reports/stage1a_audit/gears_calibration_audit"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="对 GEARS raw output 做最小 calibration audit。")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--audit-root", default=str(DEFAULT_AUDIT_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    return parser


def clip_zero(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.clip(lower=0.0)


def shrink_toward_control(
    predicted_expression_raw: pd.DataFrame,
    control_values_full: pd.DataFrame,
    alpha: float,
) -> pd.DataFrame:
    control_row = control_values_full.iloc[0]
    return control_row + alpha * (predicted_expression_raw - control_row)


def oracle_alpha_from_truth(
    predicted_shift: pd.DataFrame,
    truth: pd.DataFrame,
) -> float:
    pred = predicted_shift.to_numpy(dtype=np.float64, copy=False).ravel()
    gold = truth.to_numpy(dtype=np.float64, copy=False).ravel()
    denom = float(np.dot(pred, pred))
    if denom == 0.0:
        return 1.0
    alpha = float(np.dot(pred, gold) / denom)
    return max(0.0, min(alpha, 4.0))


def layer_stats(frame: pd.DataFrame) -> dict[str, float]:
    values = frame.to_numpy(dtype=np.float64, copy=False).ravel()
    abs_values = np.abs(values)
    return {
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "std": float(np.std(values)),
        "abs_median": float(np.median(abs_values)),
        "abs_p95": float(np.quantile(abs_values, 0.95)),
        "negative_fraction": float(np.mean(values < 0.0)),
    }


def scale_ratio(candidate: pd.DataFrame, truth: pd.DataFrame) -> float | None:
    truth_abs_p95 = float(np.quantile(np.abs(truth.to_numpy(dtype=np.float64, copy=False).ravel()), 0.95))
    cand_abs_p95 = float(np.quantile(np.abs(candidate.to_numpy(dtype=np.float64, copy=False).ravel()), 0.95))
    if truth_abs_p95 == 0.0:
        return None
    return cand_abs_p95 / truth_abs_p95


def evaluate_variant(
    *,
    variant_name: str,
    predicted_expression_raw: pd.DataFrame,
    control_values_full: pd.DataFrame,
    truth: pd.DataFrame,
) -> dict[str, object]:
    control_row = control_values_full.iloc[0]
    predicted_shift = predicted_expression_raw.subtract(control_row, axis=1)
    predicted_shift = predicted_shift.loc[truth.index, truth.columns]
    per_target, aggregates = evaluate_prediction_frame(
        prediction=predicted_shift,
        truth=truth,
        topk_values=[50],
    )
    return {
        "variant_name": variant_name,
        "predicted_expression_raw_stats": layer_stats(predicted_expression_raw),
        "predicted_shift_stats": layer_stats(predicted_shift),
        "predicted_shift_scale_ratio_vs_truth": scale_ratio(predicted_shift, truth),
        "metrics": {
            "pearson_mean": aggregates["pearson_mean"],
            "cosine_similarity_mean": aggregates["cosine_similarity_mean"],
            "rmse_mean": aggregates["rmse_mean"],
            "top50_jaccard_mean": aggregates["top50_jaccard_mean"],
        },
    }


def main() -> None:
    args = build_parser().parse_args()
    dataset_id = args.dataset_id
    audit_root = Path(args.audit_root)
    if not audit_root.is_absolute():
        audit_root = PROJECT_ROOT / audit_root
    dataset_root = audit_root / dataset_id
    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = PROJECT_ROOT / output_root
    output_root.mkdir(parents=True, exist_ok=True)

    predicted_expression_raw = read_matrix(dataset_root / "predicted_expression_raw.tsv.gz")
    control_values_full = read_matrix(dataset_root / "control_values_full.tsv.gz")
    truth = read_matrix(load_main_aligned_truth_entry(dataset_id).path)

    variants: list[tuple[str, pd.DataFrame]] = []
    variants.append(("identity", predicted_expression_raw))
    variants.append(("clip_zero", clip_zero(predicted_expression_raw)))
    for alpha in (0.75, 0.5, 0.25):
        variants.append(
            (f"shrink_alpha_{str(alpha).replace('.', '_')}", shrink_toward_control(predicted_expression_raw, control_values_full, alpha))
        )
        variants.append(
            (
                f"clip_zero_then_shrink_alpha_{str(alpha).replace('.', '_')}",
                shrink_toward_control(clip_zero(predicted_expression_raw), control_values_full, alpha),
            )
        )

    oracle_alpha = oracle_alpha_from_truth(
        predicted_expression_raw.subtract(control_values_full.iloc[0], axis=1).loc[truth.index, truth.columns],
        truth,
    )
    variants.append(
        (
            f"oracle_shift_shrink_alpha_{oracle_alpha:.4f}",
            shrink_toward_control(predicted_expression_raw, control_values_full, oracle_alpha),
        )
    )

    variant_rows = [
        evaluate_variant(
            variant_name=name,
            predicted_expression_raw=frame,
            control_values_full=control_values_full,
            truth=truth,
        )
        for name, frame in variants
    ]

    summary_rows = []
    for row in variant_rows:
        summary_rows.append(
            {
                "variant_name": row["variant_name"],
                "raw_negative_fraction": row["predicted_expression_raw_stats"]["negative_fraction"],
                "shift_negative_fraction": row["predicted_shift_stats"]["negative_fraction"],
                "shift_scale_ratio_vs_truth": row["predicted_shift_scale_ratio_vs_truth"],
                "pearson_mean": row["metrics"]["pearson_mean"],
                "cosine_similarity_mean": row["metrics"]["cosine_similarity_mean"],
                "rmse_mean": row["metrics"]["rmse_mean"],
                "top50_jaccard_mean": row["metrics"]["top50_jaccard_mean"],
            }
        )
    summary_df = pd.DataFrame(summary_rows).sort_values("rmse_mean").reset_index(drop=True)

    summary_path = output_root / f"{dataset_id}_calibration_summary.tsv"
    detail_path = output_root / f"{dataset_id}_calibration_detail.json"
    summary_df.to_csv(summary_path, sep="\t", index=False)
    detail_path.write_text(
        json.dumps({"dataset_id": dataset_id, "variants": variant_rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"已写出: {resolve_project_relative(summary_path)}")
    print(f"已写出: {resolve_project_relative(detail_path)}")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
