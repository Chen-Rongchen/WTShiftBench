from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for candidate in (PROJECT_ROOT, SCRIPTS_DIR):
    text = str(candidate)
    if text not in sys.path:
        sys.path.insert(0, text)


DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/stage1a/runs/all_datasets_eval_matrix.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="汇总全数据集评测矩阵的模型结果，并判断是否打过 mean_shift_baseline。"
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument(
        "--model-id",
        action="append",
        default=[],
        help="只汇总指定 model_id，可重复传入。",
    )
    parser.add_argument(
        "--dataset-id",
        action="append",
        default=[],
        help="只汇总指定 dataset_id，可重复传入。",
    )
    parser.add_argument(
        "--tier",
        action="append",
        default=[],
        help="只汇总指定 tier，可重复传入。",
    )
    parser.add_argument(
        "--evaluated-only",
        action="store_true",
        help="只输出已产生 evaluation 结果的行。",
    )
    parser.add_argument(
        "--output-suffix",
        default="",
        help="输出文件后缀；例如 shard_gears，会生成 model_vs_baseline.shard_gears.tsv/md。",
    )
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_filter(values: list[str]) -> set[str]:
    return {value for value in values if value}


def classify_vs_baseline(comparison: dict[str, object]) -> tuple[str, int]:
    baselines = comparison.get("baselines", {})
    comparators = baselines.get("comparators", {})
    mean_shift = comparators.get("mean_shift_baseline", {})
    family_records = mean_shift.get("primary_family_comparisons", {})
    if not family_records:
        return "missing_mean_shift_comparison", 0
    better_count = sum(bool(record.get("model_better")) for record in family_records.values())
    family_count = len(family_records)
    if better_count == family_count:
        return "better_than_mean_shift_baseline", better_count
    if better_count == 0:
        return "worse_than_mean_shift_baseline", 0
    return "mixed_vs_mean_shift_baseline", better_count


def main() -> None:
    args = build_parser().parse_args()
    config_path = resolve_path(args.config)
    config = load_json(config_path)
    matrix_id = str(config["matrix_id"])
    report_root = resolve_path(str(config.get("report_root", "reports/stage1a/eval_matrix"))) / matrix_id
    readiness_path = report_root / "dataset_readiness.tsv"
    readiness = (
        pd.read_csv(readiness_path, sep="\t")
        if readiness_path.exists()
        else pd.DataFrame(columns=["dataset_id", "tier", "ready_end_to_end", "readiness_note"])
    )
    readiness_index = {
        str(row["dataset_id"]): row for row in readiness.to_dict(orient="records")
    }

    dataset_filter = normalize_filter(args.dataset_id)
    tier_filter = normalize_filter(args.tier)
    model_filter = normalize_filter(args.model_id)

    rows: list[dict[str, object]] = []
    for model in list(config.get("models", [])):
        model_id = str(model["model_id"])
        adapter = str(model["adapter"])
        if model_filter and model_id not in model_filter:
            continue
        for dataset in list(config.get("datasets", [])):
            dataset_id = str(dataset["dataset_id"])
            tier = str(dataset["tier"])
            if dataset_filter and dataset_id not in dataset_filter:
                continue
            if tier_filter and tier not in tier_filter:
                continue
            eval_dir = PROJECT_ROOT / "reports/stage1a/model_eval" / model_id / dataset_id
            summary_path = eval_dir / "dataset_score_summary.json"
            comparison_path = eval_dir / "baseline_null_comparison.json"
            readiness_row = readiness_index.get(dataset_id, {})
            if not summary_path.exists() or not comparison_path.exists():
                rows.append(
                    {
                        "dataset_id": dataset_id,
                        "tier": tier,
                        "adapter": adapter,
                        "model_id": model_id,
                        "evaluation_status": "missing_evaluation",
                        "vs_mean_shift_status": "not_available",
                        "better_primary_family_count": 0,
                        "pearson_mean": "",
                        "rmse_mean": "",
                        "top50_jaccard_mean": "",
                        "ready_end_to_end": readiness_row.get("ready_end_to_end", ""),
                        "readiness_note": readiness_row.get("readiness_note", ""),
                    }
                )
                continue

            summary = load_json(summary_path)
            comparison = load_json(comparison_path)
            vs_status, better_count = classify_vs_baseline(comparison)
            scores = dict(summary.get("aggregate_scores", {}))
            rows.append(
                {
                    "dataset_id": dataset_id,
                    "tier": tier,
                    "adapter": adapter,
                    "model_id": model_id,
                    "evaluation_status": "evaluated",
                    "vs_mean_shift_status": vs_status,
                    "better_primary_family_count": better_count,
                    "pearson_mean": scores.get("pearson_mean", ""),
                    "rmse_mean": scores.get("rmse_mean", ""),
                    "top50_jaccard_mean": scores.get("top50_jaccard_mean", ""),
                    "ready_end_to_end": readiness_row.get("ready_end_to_end", ""),
                    "readiness_note": readiness_row.get("readiness_note", ""),
                }
            )

    if args.evaluated_only:
        rows = [row for row in rows if row["evaluation_status"] == "evaluated"]

    summary_frame = pd.DataFrame(rows).sort_values(
        ["dataset_id", "adapter", "model_id"]
    ).reset_index(drop=True)
    suffix = f".{args.output_suffix}" if args.output_suffix else ""
    summary_path = report_root / f"model_vs_baseline{suffix}.tsv"
    summary_frame.to_csv(summary_path, sep="\t", index=False)

    md_lines = [
        f"# {matrix_id} 结果汇总",
        "",
        "| dataset_id | tier | model_id | vs_mean_shift_status | evaluation_status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in summary_frame.itertuples(index=False):
        md_lines.append(
            f"| {row.dataset_id} | {row.tier} | {row.model_id} | {row.vs_mean_shift_status} | {row.evaluation_status} |"
        )
    markdown_path = report_root / f"model_vs_baseline{suffix}.md"
    markdown_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"已写出: {summary_path.relative_to(PROJECT_ROOT)}")
    print(f"已写出: {markdown_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
