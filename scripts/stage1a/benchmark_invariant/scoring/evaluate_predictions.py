from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    PROJECT_ROOT,
    STAGE1A_PRIMARY_BASELINE_NAMES,
    comparator_path,
    evaluate_prediction_frame,
    json_dump,
    load_main_aligned_truth_entry,
    read_matrix,
    resolve_project_relative,
    subset_like_truth,
)


DEFAULT_PREDICTION_ROOT = PROJECT_ROOT / "data/predictions/stage1a_main_aligned"
DEFAULT_REPORT_ROOT = PROJECT_ROOT / "reports/stage1a/model_eval"
DEFAULT_SUPPLEMENTARY_REPORT_ROOT = PROJECT_ROOT / "reports/stage1a/model_eval_supplementary"
DEFAULT_ALIGNMENT_REPORT_ROOT = PROJECT_ROOT / "reports/stage1a/prediction_alignment"
DEFAULT_LANE_REPORT_ROOT = PROJECT_ROOT / "reports/stage1a/model_eval_lanes"
BASELINE_NAMES = list(STAGE1A_PRIMARY_BASELINE_NAMES)
NULL_NAMES = ["label_shuffle", "random_pairing"]
HIGHER_IS_BETTER_PREFIXES = (
    "pearson",
    "spearman",
    "cosine_similarity",
    "top",
)
LOWER_IS_BETTER_PREFIXES = ("rmse", "l2_distance")
ELIGIBILITY_STATUS_WHITELIST = {
    "official_leaderboard_eligible",
    "degraded_or_supplementary_only",
    "supplementary_only",
}
SUPPLEMENTARY_GENE_SUBSET_ROOT = PROJECT_ROOT / "data/frozen/stage1a_supplementary_gene_subsets"
VALID_SUBSET_NAMES = ("top500_control_high_expr", "top1000_control_high_expr", "top2000_control_high_expr")
FORMAL_LANE_SPECS: tuple[tuple[str, str | None], ...] = (
    ("full_gene_lane", None),
    ("top500_lane", "top500_control_high_expr"),
    ("top1000_lane", "top1000_control_high_expr"),
    ("top2000_lane", "top2000_control_high_expr"),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage 1A 对齐预测正式评分。")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--aligned-prediction-path")
    parser.add_argument("--per-target-path")
    parser.add_argument("--dataset-summary-path")
    parser.add_argument("--comparison-path")
    parser.add_argument("--alignment-summary-path")
    parser.add_argument("--topk", nargs="+", type=int, default=[50])
    parser.add_argument(
        "--gene-subset-mode",
        choices=["full", "supplementary_subset"],
        default="full",
        help="full=使用完整 dataset-local evaluation space；supplementary_subset=使用 literature-aligned gene subset。",
    )
    parser.add_argument(
        "--supplementary-subset",
        choices=["top500_control_high_expr", "top1000_control_high_expr", "top2000_control_high_expr"],
        default=None,
        help="当 --gene-subset-mode=supplementary_subset 时指定使用哪个 gene subset。",
    )
    return parser


def metric_direction(metric_name: str) -> str:
    if metric_name.startswith(HIGHER_IS_BETTER_PREFIXES):
        return "higher"
    if metric_name.startswith(LOWER_IS_BETTER_PREFIXES):
        return "lower"
    raise ValueError(f"未知指标方向: {metric_name}")


def superiority_record(model_value: float, comparator_value: float, metric_name: str) -> dict[str, object]:
    direction = metric_direction(metric_name)
    if direction == "higher":
        better = bool(model_value > comparator_value)
        margin = float(model_value - comparator_value)
    else:
        better = bool(model_value < comparator_value)
        margin = float(comparator_value - model_value)
    return {
        "metric_name": metric_name,
        "direction": direction,
        "model_value": float(model_value),
        "comparator_value": float(comparator_value),
        "model_better": better,
        "margin": margin,
    }


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_alignment_summary_consistency(
    alignment_summary: dict[str, object],
    dataset_id: str,
    model_id: str,
    aligned_prediction_path: Path,
    evaluation_space: str = "main_aligned",
    skip_evaluation_space_check: bool = False,
) -> None:
    if alignment_summary.get("alignment_pass") is not True:
        raise ValueError("alignment_summary.json 的 alignment_pass 必须为 true。")
    expected = {
        "dataset_id": dataset_id,
        "model_id": model_id,
    }
    if not skip_evaluation_space_check:
        expected["evaluation_space"] = evaluation_space
    mismatched = {
        key: {
            "expected": expected_value,
            "actual": alignment_summary.get(key),
        }
        for key, expected_value in expected.items()
        if alignment_summary.get(key) != expected_value
    }
    if mismatched:
        raise ValueError(
            "alignment_summary.json 与当前评分输入不一致: "
            f"{json.dumps(mismatched, ensure_ascii=False, sort_keys=True)}"
        )
    eligibility_status = alignment_summary.get("leaderboard_eligibility_status")
    if eligibility_status not in ELIGIBILITY_STATUS_WHITELIST:
        raise ValueError(
            "alignment_summary.json 包含非法 leaderboard_eligibility_status: "
            f"{eligibility_status}"
        )
    aligned_path_value = (
        alignment_summary.get("aligned_output_path")
        if "aligned_output_path" in alignment_summary
        else alignment_summary.get("aligned_prediction_path")
    )
    if aligned_path_value is not None:
        expected_aligned_path = resolve_project_relative(aligned_prediction_path)
        if aligned_path_value != expected_aligned_path:
            raise ValueError(
                "alignment_summary.json 中的 aligned prediction path 与当前评分输入不一致: "
                f"expected={expected_aligned_path}, actual={aligned_path_value}"
            )


def build_dataset_summary(
    dataset_id: str,
    model_id: str,
    aligned_prediction_path: Path,
    alignment_summary: dict[str, object],
    truth_entry,
    aligned_truth: pd.DataFrame,
    per_target_scores: pd.DataFrame,
    aggregate_scores: dict[str, float],
    topk_values: list[int],
    evaluation_space: str = "main_aligned",
    gene_subset_info: dict[str, object] | None = None,
) -> dict[str, object]:
    primary_metrics = {
        "directional_similarity": "pearson_mean",
        "magnitude_error": "rmse_mean",
        "top_shift_overlap": f"top{topk_values[0]}_jaccard_mean",
    }
    result = {
        "stage": "stage1a_model_eval",
        "dataset_id": dataset_id,
        "model_id": model_id,
        "evaluation_space": evaluation_space,
        "formal_scoring_rule": "评分只针对 dataset-local evaluation space（根据 protocol_blueprint.md 4.3 节）。",
        "aligned_prediction_path": resolve_project_relative(aligned_prediction_path),
        "alignment_summary_path": alignment_summary["alignment_summary_path"],
        "truth_path": resolve_project_relative(truth_entry.path),
        "n_targets_scored": int(aligned_truth.shape[0]),
        "n_genes_scored": int(aligned_truth.shape[1]),
        "matrix_source": str(truth_entry.matrix_source),
        "log_normalization_applied_in_truth_build": bool(
            truth_entry.log_normalization_applied_in_truth_build
        ),
        "delta_space": str(truth_entry.delta_space),
        "topk_values": topk_values,
        "primary_aggregation_rule": {
            "per_target_first": True,
            "dataset_level_aggregates": ["mean", "median"],
            "primary_metric_family": primary_metrics,
        },
        "aggregate_scores": aggregate_scores,
        "per_target_score_columns": per_target_scores.columns.tolist(),
    }
    if gene_subset_info:
        result["gene_subset_info"] = gene_subset_info
        result["leaderboard_eligibility_status"] = "supplementary_only"
        result["leaderboard_eligibility_reason"] = "literature_aligned_gene_subset_sensitivity_analysis"
    else:
        result["leaderboard_eligibility_status"] = alignment_summary["leaderboard_eligibility_status"]
        result["leaderboard_eligibility_reason"] = alignment_summary["leaderboard_eligibility_reason"]
    return result


def compare_against_group(
    group_name: str,
    comparator_names: list[str],
    truth_subset: pd.DataFrame,
    topk_values: list[int],
    model_summary: dict[str, object],
) -> dict[str, object]:
    aggregate_scores = model_summary["aggregate_scores"]
    primary_metrics = model_summary["primary_aggregation_rule"]["primary_metric_family"]
    comparators: dict[str, object] = {}
    family_superiority: dict[str, bool] = {}

    comparator_aggregates_by_name: dict[str, dict[str, float]] = {}
    comparator_paths: dict[str, str] = {}
    for comparator_name in comparator_names:
        comparator_file = comparator_path(model_summary["dataset_id"], comparator_name)
        comparator = read_matrix(comparator_file)
        comparator_subset = subset_like_truth(comparator, truth_subset)
        _, comparator_aggregates = evaluate_prediction_frame(
            prediction=comparator_subset,
            truth=truth_subset,
            topk_values=topk_values,
        )
        comparator_aggregates_by_name[comparator_name] = comparator_aggregates
        comparator_paths[comparator_name] = resolve_project_relative(comparator_file)

    for family_name, primary_metric in primary_metrics.items():
        family_superiority[family_name] = True
        for comparator_name in comparator_names:
            comparator_aggregates = comparator_aggregates_by_name[comparator_name]
            record = superiority_record(
                model_value=float(aggregate_scores[primary_metric]),
                comparator_value=float(comparator_aggregates[primary_metric]),
                metric_name=primary_metric,
            )
            comparators.setdefault(
                comparator_name,
                {
                    "comparator_path": comparator_paths[comparator_name],
                    "aggregate_scores": comparator_aggregates,
                    "primary_family_comparisons": {},
                },
            )
            comparators[comparator_name]["primary_family_comparisons"][family_name] = record
            family_superiority[family_name] = family_superiority[family_name] and bool(
                record["model_better"]
            )

    return {
        "group_name": group_name,
        "primary_family_superiority": family_superiority,
        "all_primary_families_superior": bool(all(family_superiority.values())),
        "comparators": comparators,
    }


def load_supplementary_gene_subset(dataset_id: str, subset_name: str) -> list[str]:
    """Load a literature-aligned supplementary gene subset."""
    subset_path = SUPPLEMENTARY_GENE_SUBSET_ROOT / dataset_id / f"{subset_name}_genes.txt"
    if not subset_path.exists():
        raise FileNotFoundError(
            f"Supplementary gene subset not found: {resolve_project_relative(subset_path)}。"
            "请先运行 scripts/build_stage1a_supplementary_gene_subsets.py。"
        )
    genes = [line.strip() for line in subset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not genes:
        raise ValueError(f"Supplementary gene subset 为空: {resolve_project_relative(subset_path)}")
    return genes


def signal_adequacy_from_summary(score_summary: dict[str, object]) -> tuple[bool, dict[str, bool]]:
    aggregates = score_summary["aggregate_scores"]
    topk_values = score_summary.get("topk_values", [50])
    primary_topk = int(topk_values[0])
    checks = {
        "pearson_mean_gt_zero": bool(float(aggregates["pearson_mean"]) > 0.0),
        "spearman_mean_gt_zero": bool(float(aggregates["spearman_mean"]) > 0.0),
        "cosine_similarity_mean_gt_zero": bool(float(aggregates["cosine_similarity_mean"]) > 0.0),
        f"top{primary_topk}_jaccard_mean_gt_zero": bool(float(aggregates[f"top{primary_topk}_jaccard_mean"]) > 0.0),
    }
    return bool(all(checks.values())), checks


def build_lane_subset(
    aligned_truth: pd.DataFrame,
    aligned_prediction: pd.DataFrame,
    dataset_id: str,
    subset_name: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    if subset_name is None:
        truth_subset = aligned_truth.loc[aligned_prediction.index, aligned_prediction.columns].copy()
        return aligned_prediction.copy(), truth_subset, {
            "lane_id": "full_gene_lane",
            "subset_name": None,
            "gene_ranking_rule": "dataset_local_all_evaluable_genes",
            "n_genes_requested": int(aligned_truth.shape[1]),
            "n_genes_scored": int(truth_subset.shape[1]),
        }

    subset_genes = load_supplementary_gene_subset(dataset_id, subset_name)
    subset_gene_set = set(subset_genes)
    common_genes = [gene for gene in aligned_prediction.columns if gene in subset_gene_set]
    if not common_genes:
        raise ValueError(
            f"{dataset_id}: lane subset 与 prediction 没有交集。subset={subset_name}, "
            f"n_subset_genes={len(subset_genes)}"
        )
    prediction_subset = aligned_prediction.loc[:, common_genes].copy()
    truth_subset = aligned_truth.loc[prediction_subset.index, common_genes].copy()
    return prediction_subset, truth_subset, {
        "lane_id": subset_name.replace("_control_high_expr", "") + "_lane",
        "subset_name": subset_name,
        "gene_ranking_rule": "control_mean_expression_desc",
        "n_genes_requested": len(subset_genes),
        "n_genes_scored": int(len(common_genes)),
    }


def build_comparison_summary(
    dataset_summary: dict[str, object],
    truth_subset: pd.DataFrame,
    topk_values: list[int],
) -> dict[str, object]:
    baseline_comparison = compare_against_group(
        group_name="baselines",
        comparator_names=BASELINE_NAMES,
        truth_subset=truth_subset,
        topk_values=topk_values,
        model_summary=dataset_summary,
    )
    null_comparison = compare_against_group(
        group_name="nulls",
        comparator_names=NULL_NAMES,
        truth_subset=truth_subset,
        topk_values=topk_values,
        model_summary=dataset_summary,
    )
    return {
        "stage": "stage1a_model_eval",
        "dataset_id": dataset_summary["dataset_id"],
        "model_id": dataset_summary["model_id"],
        "evaluation_space": dataset_summary["evaluation_space"],
        "primary_metric_family": dataset_summary["primary_aggregation_rule"]["primary_metric_family"],
        "baselines": baseline_comparison,
        "nulls": null_comparison,
    }


def lane_order_key(lane_id: str) -> int:
    ordered_lane_ids = [lane_name for lane_name, _ in FORMAL_LANE_SPECS]
    try:
        return ordered_lane_ids.index(lane_id)
    except ValueError:
        return len(ordered_lane_ids)


def build_cross_lane_summary(
    dataset_id: str,
    model_id: str,
    lane_records: list[dict[str, object]],
) -> dict[str, object]:
    lane_rows = sorted(lane_records, key=lambda item: lane_order_key(str(item["lane_id"])))
    pearsons = [float(row["aggregate_scores"]["pearson_mean"]) for row in lane_rows]
    signal_count = sum(bool(row["signal_adequacy_pass"]) for row in lane_rows)
    null_count = sum(bool(row["null_superiority_pass"]) for row in lane_rows)
    baseline_count = sum(bool(row["baseline_superiority_pass"]) for row in lane_rows)
    contract_failures = [
        str(row["lane_id"])
        for row in lane_rows
        if row["leaderboard_eligibility_status"] != "official_leaderboard_eligible"
    ]
    consistency = {
        "pearson_min": min(pearsons),
        "pearson_max": max(pearsons),
        "pearson_range": max(pearsons) - min(pearsons),
        "all_lanes_non_negative": bool(all(value >= 0.0 for value in pearsons)),
    }
    return {
        "stage": "stage1a_cross_lane_adjudication",
        "dataset_id": dataset_id,
        "model_id": model_id,
        "formal_lane_set": [row["lane_id"] for row in lane_rows],
        "n_lanes_signal_adequate": int(signal_count),
        "n_lanes_null_superior": int(null_count),
        "n_lanes_baseline_competitive": int(baseline_count),
        "lane_performance_consistency": consistency,
        "absence_of_lane_specific_contract_failure": bool(not contract_failures),
        "lane_specific_contract_failures": contract_failures,
        "lane_rows": lane_rows,
    }


def main() -> None:
    args = build_parser().parse_args()

    # Validate supplementary mode arguments
    if args.gene_subset_mode == "supplementary_subset":
        if not args.supplementary_subset:
            raise ValueError("--gene-subset-mode=supplementary_subset 时必须指定 --supplementary-subset。")
        if args.supplementary_subset not in VALID_SUBSET_NAMES:
            raise ValueError(f"无效的 --supplementary-subset: {args.supplementary_subset}")
    else:
        if args.supplementary_subset:
            raise ValueError("--supplementary-subset 仅在 --gene-subset-mode=supplementary_subset 时有效。")

    aligned_prediction_path = (
        Path(args.aligned_prediction_path)
        if args.aligned_prediction_path
        else DEFAULT_PREDICTION_ROOT
        / args.model_id
        / args.dataset_id
        / "predicted_shift_aligned.tsv.gz"
    )
    if not aligned_prediction_path.is_absolute():
        aligned_prediction_path = PROJECT_ROOT / aligned_prediction_path

    # Determine report root based on mode
    if args.gene_subset_mode == "supplementary_subset":
        report_root = DEFAULT_SUPPLEMENTARY_REPORT_ROOT
        evaluation_space = "supplementary_aligned"
        report_subdir = args.supplementary_subset
    else:
        report_root = DEFAULT_REPORT_ROOT
        evaluation_space = "main_aligned"
        report_subdir = args.dataset_id

    report_dir = report_root / args.model_id / report_subdir
    per_target_path = (
        Path(args.per_target_path)
        if args.per_target_path
        else report_dir / "per_target_scores.tsv"
    )
    if not per_target_path.is_absolute():
        per_target_path = PROJECT_ROOT / per_target_path

    dataset_summary_path = (
        Path(args.dataset_summary_path)
        if args.dataset_summary_path
        else report_dir / "dataset_score_summary.json"
    )
    if not dataset_summary_path.is_absolute():
        dataset_summary_path = PROJECT_ROOT / dataset_summary_path

    comparison_path = (
        Path(args.comparison_path)
        if args.comparison_path
        else report_dir / "baseline_null_comparison.json"
    )
    if not comparison_path.is_absolute():
        comparison_path = PROJECT_ROOT / comparison_path

    alignment_summary_path = (
        Path(args.alignment_summary_path)
        if args.alignment_summary_path
        else DEFAULT_ALIGNMENT_REPORT_ROOT / args.model_id / args.dataset_id / "alignment_summary.json"
    )
    if not alignment_summary_path.is_absolute():
        alignment_summary_path = PROJECT_ROOT / alignment_summary_path
    alignment_summary = load_json(alignment_summary_path)
    alignment_summary["alignment_summary_path"] = resolve_project_relative(alignment_summary_path)
    # For supplementary_subset mode, alignment was done in main_aligned space; skip the evaluation_space check
    skip_eval_space_check = args.gene_subset_mode == "supplementary_subset"
    assert_alignment_summary_consistency(
        alignment_summary=alignment_summary,
        dataset_id=args.dataset_id,
        model_id=args.model_id,
        aligned_prediction_path=aligned_prediction_path,
        evaluation_space=evaluation_space,
        skip_evaluation_space_check=skip_eval_space_check,
    )

    truth_entry = load_main_aligned_truth_entry(args.dataset_id)
    aligned_truth = read_matrix(truth_entry.path)
    aligned_prediction = read_matrix(aligned_prediction_path)

    subset_name = args.supplementary_subset if args.gene_subset_mode == "supplementary_subset" else None
    aligned_prediction, truth_subset, lane_subset_info = build_lane_subset(
        aligned_truth=aligned_truth,
        aligned_prediction=aligned_prediction,
        dataset_id=args.dataset_id,
        subset_name=subset_name,
    )
    if subset_name is None:
        gene_subset_info = None
    else:
        gene_subset_info = {
            "subset_name": subset_name,
            "n_subset_genes_requested": int(lane_subset_info["n_genes_requested"]),
            "n_genes_in_intersection": int(lane_subset_info["n_genes_scored"]),
            "gene_ranking_rule": str(lane_subset_info["gene_ranking_rule"]),
        }

    per_target_scores, aggregate_scores = evaluate_prediction_frame(
        prediction=aligned_prediction,
        truth=truth_subset,
        topk_values=args.topk,
    )

    per_target_path.parent.mkdir(parents=True, exist_ok=True)
    per_target_scores.to_csv(per_target_path, sep="\t", index=False)
    dataset_summary = build_dataset_summary(
        dataset_id=args.dataset_id,
        model_id=args.model_id,
        aligned_prediction_path=aligned_prediction_path,
        alignment_summary=alignment_summary,
        truth_entry=truth_entry,
        aligned_truth=truth_subset,
        per_target_scores=per_target_scores,
        aggregate_scores=aggregate_scores,
        topk_values=args.topk,
        evaluation_space=evaluation_space,
        gene_subset_info=gene_subset_info,
    )
    json_dump(dataset_summary, dataset_summary_path)

    comparison_summary = build_comparison_summary(
        dataset_summary=dataset_summary,
        truth_subset=truth_subset,
        topk_values=args.topk,
    )
    json_dump(comparison_summary, comparison_path)

    if args.gene_subset_mode == "full":
        lane_report_dir = DEFAULT_LANE_REPORT_ROOT / args.model_id / args.dataset_id
        lane_report_dir.mkdir(parents=True, exist_ok=True)
        lane_rows: list[dict[str, object]] = []
        for lane_id, lane_subset_name in FORMAL_LANE_SPECS:
            lane_prediction, lane_truth, lane_info = build_lane_subset(
                aligned_truth=read_matrix(truth_entry.path),
                aligned_prediction=aligned_prediction if lane_subset_name is None else read_matrix(aligned_prediction_path),
                dataset_id=args.dataset_id,
                subset_name=lane_subset_name,
            )
            lane_per_target_scores, lane_aggregate_scores = evaluate_prediction_frame(
                prediction=lane_prediction,
                truth=lane_truth,
                topk_values=args.topk,
            )
            lane_dataset_summary = build_dataset_summary(
                dataset_id=args.dataset_id,
                model_id=args.model_id,
                aligned_prediction_path=aligned_prediction_path,
                alignment_summary=alignment_summary,
                truth_entry=truth_entry,
                aligned_truth=lane_truth,
                per_target_scores=lane_per_target_scores,
                aggregate_scores=lane_aggregate_scores,
                topk_values=args.topk,
                evaluation_space="main_aligned",
                gene_subset_info=None if lane_subset_name is None else {
                    "subset_name": lane_subset_name,
                    "n_subset_genes_requested": int(lane_info["n_genes_requested"]),
                    "n_genes_in_intersection": int(lane_info["n_genes_scored"]),
                    "gene_ranking_rule": str(lane_info["gene_ranking_rule"]),
                },
            )
            lane_comparison = build_comparison_summary(
                dataset_summary=lane_dataset_summary,
                truth_subset=lane_truth,
                topk_values=args.topk,
            )
            lane_signal_pass, lane_signal_details = signal_adequacy_from_summary(lane_dataset_summary)
            lane_rows.append(
                {
                    "lane_id": lane_id,
                    "subset_name": lane_subset_name,
                    "n_targets_scored": int(lane_dataset_summary["n_targets_scored"]),
                    "n_genes_scored": int(lane_dataset_summary["n_genes_scored"]),
                    "leaderboard_eligibility_status": lane_dataset_summary["leaderboard_eligibility_status"],
                    "aggregate_scores": lane_dataset_summary["aggregate_scores"],
                    "signal_adequacy_pass": lane_signal_pass,
                    "signal_adequacy_details": lane_signal_details,
                    "baseline_superiority_pass": bool(lane_comparison["baselines"]["all_primary_families_superior"]),
                    "null_superiority_pass": bool(lane_comparison["nulls"]["all_primary_families_superior"]),
                    "baselines": lane_comparison["baselines"],
                    "nulls": lane_comparison["nulls"],
                }
            )
        lane_results_path = lane_report_dir / "lane_results.json"
        lane_summary_path = lane_report_dir / "lane_summary.tsv"
        cross_lane_summary_path = lane_report_dir / "cross_lane_summary.json"
        json_dump(
            {
                "stage": "stage1a_lane_wise_formal_outputs",
                "dataset_id": args.dataset_id,
                "model_id": args.model_id,
                "lane_rows": lane_rows,
            },
            lane_results_path,
        )
        pd.DataFrame(
            [
                {
                    "dataset_id": args.dataset_id,
                    "model_id": args.model_id,
                    "lane_id": row["lane_id"],
                    "subset_name": row["subset_name"],
                    "n_targets_scored": row["n_targets_scored"],
                    "n_genes_scored": row["n_genes_scored"],
                    "leaderboard_eligibility_status": row["leaderboard_eligibility_status"],
                    "signal_adequacy_pass": row["signal_adequacy_pass"],
                    "baseline_superiority_pass": row["baseline_superiority_pass"],
                    "null_superiority_pass": row["null_superiority_pass"],
                    "pearson_mean": row["aggregate_scores"]["pearson_mean"],
                    "rmse_mean": row["aggregate_scores"]["rmse_mean"],
                    "top50_jaccard_mean": row["aggregate_scores"]["top50_jaccard_mean"],
                }
                for row in lane_rows
            ]
        ).to_csv(lane_summary_path, sep="\t", index=False)
        json_dump(
            build_cross_lane_summary(
                dataset_id=args.dataset_id,
                model_id=args.model_id,
                lane_records=lane_rows,
            ),
            cross_lane_summary_path,
        )
        print(f"已写出: {resolve_project_relative(lane_results_path)}")
        print(f"已写出: {resolve_project_relative(lane_summary_path)}")
        print(f"已写出: {resolve_project_relative(cross_lane_summary_path)}")

    print(f"已写出: {resolve_project_relative(per_target_path)}")
    print(f"已写出: {resolve_project_relative(dataset_summary_path)}")
    print(f"已写出: {resolve_project_relative(comparison_path)}")


if __name__ == "__main__":
    main()
