from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    PROJECT_ROOT,
    resolve_project_relative,
)


MODEL_EVAL_ROOT = PROJECT_ROOT / "reports/stage1a/model_eval"
SUPPLEMENTARY_MODEL_EVAL_ROOT = PROJECT_ROOT / "reports/stage1a/model_eval_supplementary"
LANE_EVAL_ROOT = PROJECT_ROOT / "reports/stage1a/model_eval_lanes"
ELIGIBILITY_STATUS_WHITELIST = {
    "official_leaderboard_eligible",
    "degraded_or_supplementary_only",
    "supplementary_only",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="渲染 Stage 1A dataset-level pass skeleton。")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--output-path")
    parser.add_argument(
        "--gene-subset-mode",
        choices=["full", "supplementary_subset"],
        default="full",
        help="full=渲染 main_aligned 结果；supplementary_subset=渲染 supplementary_aligned 结果。",
    )
    parser.add_argument(
        "--supplementary-subset",
        choices=["top500_control_high_expr", "top1000_control_high_expr", "top2000_control_high_expr"],
        default=None,
        help="当 --gene-subset-mode=supplementary_subset 时指定哪个 subset。",
    )
    return parser


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def signal_adequacy(score_summary: dict[str, object]) -> tuple[bool, dict[str, object]]:
    aggregates = score_summary["aggregate_scores"]
    checks = {
        "pearson_mean_gt_zero": bool(float(aggregates["pearson_mean"]) > 0.0),
        "spearman_mean_gt_zero": bool(float(aggregates["spearman_mean"]) > 0.0),
        "cosine_mean_gt_zero": bool(float(aggregates["cosine_similarity_mean"]) > 0.0),
    }
    topk_values = score_summary.get("topk_values", [50])
    primary_topk = int(topk_values[0])
    checks[f"top{primary_topk}_jaccard_mean_gt_zero"] = bool(
        float(aggregates[f"top{primary_topk}_jaccard_mean"]) > 0.0
    )
    return bool(all(checks.values())), checks


def load_cross_lane_summary(model_id: str, dataset_id: str) -> dict[str, object] | None:
    path = LANE_EVAL_ROOT / model_id / dataset_id / "cross_lane_summary.json"
    if not path.exists():
        return None
    payload = load_json(path)
    payload["cross_lane_summary_path"] = resolve_project_relative(path)
    return payload


def main() -> None:
    args = build_parser().parse_args()

    # Validate supplementary mode arguments
    if args.gene_subset_mode == "supplementary_subset":
        if not args.supplementary_subset:
            raise ValueError("--gene-subset-mode=supplementary_subset 时必须指定 --supplementary-subset。")
    else:
        if args.supplementary_subset:
            raise ValueError("--supplementary-subset 仅在 --gene-subset-mode=supplementary_subset 时有效。")

    if args.gene_subset_mode == "supplementary_subset":
        model_root = SUPPLEMENTARY_MODEL_EVAL_ROOT / args.model_id
        # In supplementary mode, structure is <model_id>/<dataset_id>/<subset_name>
        dataset_dirs = []
        for ds_dir in model_root.iterdir():
            if ds_dir.is_dir():
                subset_dir = ds_dir / args.supplementary_subset
                if subset_dir.is_dir():
                    dataset_dirs.append(subset_dir)
        dataset_dirs = sorted(dataset_dirs)
        output_prefix = f"stage1a_pass_skeleton_supplementary_{args.supplementary_subset}"
        eval_mode_label = "supplementary_aligned"
    else:
        model_root = MODEL_EVAL_ROOT / args.model_id
        dataset_dirs = sorted(path for path in model_root.iterdir() if path.is_dir())
        output_prefix = "stage1a_pass_skeleton_all_results"
        eval_mode_label = "main_aligned"

    if not model_root.exists():
        raise FileNotFoundError(f"目录不存在: {resolve_project_relative(model_root)}")
    if not model_root.is_dir():
        raise NotADirectoryError(f"不是目录: {resolve_project_relative(model_root)}")
    if not dataset_dirs:
        raise ValueError(f"{resolve_project_relative(model_root)} 下没有 dataset 评测结果。")

    rows: list[dict[str, object]] = []
    for dataset_dir in dataset_dirs:
        if not dataset_dir.exists():
            raise FileNotFoundError(f"目录不存在: {resolve_project_relative(dataset_dir)}")
        if not dataset_dir.is_dir():
            raise NotADirectoryError(f"不是目录: {resolve_project_relative(dataset_dir)}")
        score_summary_path = dataset_dir / "dataset_score_summary.json"
        comparison_path = dataset_dir / "baseline_null_comparison.json"
        if not score_summary_path.exists():
            raise FileNotFoundError(f"文件不存在: {resolve_project_relative(score_summary_path)}")
        # comparison_path may not exist in supplementary mode
        comparison = None
        if comparison_path.exists():
            comparison = load_json(comparison_path)
        score_summary = load_json(score_summary_path)
        eligibility_status = score_summary["leaderboard_eligibility_status"]
        if eligibility_status not in ELIGIBILITY_STATUS_WHITELIST:
            raise ValueError(
                f"{resolve_project_relative(score_summary_path)} 包含非法 "
                f"leaderboard_eligibility_status={eligibility_status}"
            )
        signal_pass, signal_details = signal_adequacy(score_summary)
        cross_lane_summary = load_cross_lane_summary(args.model_id, str(score_summary["dataset_id"]))

        # For supplementary mode, baseline/null comparison may not exist
        if comparison is not None:
            baseline_family = comparison.get("baselines", {}).get("primary_family_superiority", {})
            null_family = comparison.get("nulls", {}).get("primary_family_superiority", {})
            baseline_superiority_pass = bool(
                comparison.get("baselines", {}).get("all_primary_families_superior", False)
            )
            null_superiority_pass = bool(comparison.get("nulls", {}).get("all_primary_families_superior", False))
            baseline_details_json = json.dumps(baseline_family, ensure_ascii=False, sort_keys=True)
            null_details_json = json.dumps(null_family, ensure_ascii=False, sort_keys=True)
            overall_skeleton_pass = bool(
                signal_pass
                and comparison.get("baselines", {}).get("all_primary_families_superior", False)
                and comparison.get("nulls", {}).get("all_primary_families_superior", False)
            )
        else:
            baseline_family = {}
            null_family = {}
            baseline_superiority_pass = None
            null_superiority_pass = None
            baseline_details_json = json.dumps({}, ensure_ascii=False, sort_keys=True)
            null_details_json = json.dumps({}, ensure_ascii=False, sort_keys=True)
            overall_skeleton_pass = None

        if cross_lane_summary is not None:
            cross_lane_signal_count = int(cross_lane_summary["n_lanes_signal_adequate"])
            cross_lane_null_count = int(cross_lane_summary["n_lanes_null_superior"])
            cross_lane_baseline_count = int(cross_lane_summary["n_lanes_baseline_competitive"])
            cross_lane_contract_ok = bool(cross_lane_summary["absence_of_lane_specific_contract_failure"])
            cross_lane_consistency = json.dumps(
                cross_lane_summary["lane_performance_consistency"],
                ensure_ascii=False,
                sort_keys=True,
            )
            if comparison is not None:
                overall_skeleton_pass = bool(
                    signal_pass
                    and baseline_superiority_pass
                    and null_superiority_pass
                    and cross_lane_signal_count >= 4
                    and cross_lane_null_count >= 4
                    and cross_lane_contract_ok
                )
        else:
            cross_lane_signal_count = None
            cross_lane_null_count = None
            cross_lane_baseline_count = None
            cross_lane_contract_ok = None
            cross_lane_consistency = json.dumps({}, ensure_ascii=False, sort_keys=True)

        row = {
            "model_id": args.model_id,
            "dataset_id": score_summary["dataset_id"],
            "evaluation_space": score_summary["evaluation_space"],
            "n_targets_scored": int(score_summary["n_targets_scored"]),
            "n_genes_scored": int(score_summary["n_genes_scored"]),
            "leaderboard_eligibility_status": eligibility_status,
            "leaderboard_eligibility_reason": score_summary["leaderboard_eligibility_reason"],
            "signal_adequacy_pass": signal_pass,
            "signal_adequacy_details": json.dumps(signal_details, ensure_ascii=False, sort_keys=True),
            "baseline_superiority_pass": baseline_superiority_pass,
            "baseline_superiority_details": baseline_details_json,
            "null_superiority_pass": null_superiority_pass,
            "null_superiority_details": null_details_json,
            "n_lanes_signal_adequate": cross_lane_signal_count,
            "n_lanes_null_superior": cross_lane_null_count,
            "n_lanes_baseline_competitive": cross_lane_baseline_count,
            "absence_of_lane_specific_contract_failure": cross_lane_contract_ok,
            "lane_performance_consistency": cross_lane_consistency,
            "robustness_placeholder": (
                cross_lane_summary["cross_lane_summary_path"]
                if cross_lane_summary is not None
                else "pending"
            ),
            "overall_skeleton_pass": overall_skeleton_pass,
        }
        # Add gene subset info if in supplementary mode
        if "gene_subset_info" in score_summary:
            row["gene_subset_info"] = json.dumps(score_summary["gene_subset_info"], ensure_ascii=False)
        rows.append(row)

    output_path = (
        Path(args.output_path)
        if args.output_path
        else model_root / f"{output_prefix}.tsv"
    )
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    skeleton = pd.DataFrame(rows).sort_values("dataset_id").reset_index(drop=True)
    skeleton.to_csv(output_path, sep="\t", index=False)

    if args.gene_subset_mode == "supplementary_subset":
        # For supplementary, only one output file
        print(f"已写出: {resolve_project_relative(output_path)}")
    else:
        official_output_path = output_path.with_name("stage1a_pass_skeleton_official_leaderboard.tsv")
        supplementary_output_path = output_path.with_name(
            "stage1a_pass_skeleton_supplementary_or_degraded.tsv"
        )
        skeleton.loc[
            skeleton["leaderboard_eligibility_status"] == "official_leaderboard_eligible"
        ].to_csv(official_output_path, sep="\t", index=False)
        skeleton.loc[
            skeleton["leaderboard_eligibility_status"] == "degraded_or_supplementary_only"
        ].to_csv(supplementary_output_path, sep="\t", index=False)
        print(
            "已写出: "
            f"{resolve_project_relative(output_path)} "
            "(all results, not formal leaderboard)"
        )
        print(f"已写出: {resolve_project_relative(official_output_path)}")
        print(f"已写出: {resolve_project_relative(supplementary_output_path)}")


if __name__ == "__main__":
    main()
