from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "configs/entrants/supplement_entrants.json"
DEFAULT_MATRIX_CONFIG_PATH = PROJECT_ROOT / "configs/stage1a/runs/all_datasets_eval_matrix.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "reports/stage1a/supplement_entrants"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="汇总 supplement entrant 池在 formal/supplement 数据集上的评测结果。")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH))
    parser.add_argument("--matrix-config", default=str(DEFAULT_MATRIX_CONFIG_PATH))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_vs_mean_shift(path: Path) -> str:
    if not path.exists():
        return "not_evaluated"
    payload = load_json(path)
    comparators = payload.get("baselines", {}).get("comparators", {})
    mean_shift = comparators.get("mean_shift_baseline", {})
    family_records = mean_shift.get("primary_family_comparisons", {})
    if not family_records:
        return "missing_mean_shift_comparison"
    better_count = sum(bool(record.get("model_better")) for record in family_records.values())
    if better_count == len(family_records):
        return "better_than_mean_shift_baseline"
    if better_count == 0:
        return "worse_than_mean_shift_baseline"
    return "mixed_vs_mean_shift_baseline"


def main() -> None:
    args = build_parser().parse_args()
    registry_rows = load_json(resolve_path(args.registry)).get("entrants", [])
    dataset_rows = load_json(resolve_path(args.matrix_config)).get("datasets", [])
    output_root = resolve_path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for entrant in registry_rows:
        entrant_id = str(entrant["entrant_id"])
        model_id = str(entrant["model_id"])
        status = str(entrant["status"])
        for dataset in dataset_rows:
            dataset_id = str(dataset["dataset_id"])
            tier = str(dataset["tier"])
            summary_path = PROJECT_ROOT / "reports/stage1a/model_eval" / model_id / dataset_id / "dataset_score_summary.json"
            comparison_path = PROJECT_ROOT / "reports/stage1a/model_eval" / model_id / dataset_id / "baseline_null_comparison.json"
            aggregate_scores = {}
            if summary_path.exists():
                aggregate_scores = load_json(summary_path).get("aggregate_scores", {})
            rows.append(
                {
                    "entrant_id": entrant_id,
                    "model_id": model_id,
                    "entrant_status": status,
                    "dataset_id": dataset_id,
                    "tier": tier,
                    "evaluation_status": "evaluated" if summary_path.exists() else "missing_evaluation",
                    "vs_mean_shift_status": classify_vs_mean_shift(comparison_path),
                    "pearson_mean": aggregate_scores.get("pearson_mean", ""),
                    "rmse_mean": aggregate_scores.get("rmse_mean", ""),
                    "top50_jaccard_mean": aggregate_scores.get("top50_jaccard_mean", ""),
                }
            )

    frame = pd.DataFrame(rows).sort_values(["tier", "dataset_id", "entrant_id"]).reset_index(drop=True)
    tsv_path = output_root / "supplement_entrants_summary.tsv"
    md_path = output_root / "supplement_entrants_summary.md"
    frame.to_csv(tsv_path, sep="\t", index=False)

    lines = [
        "# Stage 1A Supplement Entrants Summary",
        "",
        "| entrant_id | model_id | dataset_id | tier | vs_mean_shift_status | evaluation_status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in frame.itertuples(index=False):
        lines.append(
            f"| {row.entrant_id} | {row.model_id} | {row.dataset_id} | {row.tier} | {row.vs_mean_shift_status} | {row.evaluation_status} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"已写出: {tsv_path}")
    print(f"已写出: {md_path}")


if __name__ == "__main__":
    main()
