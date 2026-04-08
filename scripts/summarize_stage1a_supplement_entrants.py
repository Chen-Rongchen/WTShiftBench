from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "configs/entrants/supplement_entrants.json"
DEFAULT_ANALYSIS_CONFIG_PATH = PROJECT_ROOT / "configs/stage1a/runs/supplement_entrants_single_seed_analysis.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "reports/stage1a/supplement_entrants"
DEFAULT_READINESS_PATH = (
    PROJECT_ROOT / "reports/stage1a/eval_matrix/stage1a_all_datasets_v1/dataset_readiness.tsv"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="汇总 supplement entrant 池在当前 7 个单 seed 数据集上的评测结果。")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH))
    parser.add_argument("--analysis-config", default=str(DEFAULT_ANALYSIS_CONFIG_PATH))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--readiness-path", default=str(DEFAULT_READINESS_PATH))
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_numeric(value: object) -> float | None:
    if value in ("", None):
        return None
    if pd.isna(value):
        return None
    return float(value)


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


def load_readiness_index(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path, sep="\t")
    if "dataset_id" not in frame.columns:
        return {}
    return {
        str(row["dataset_id"]): row
        for row in frame.to_dict(orient="records")
    }


def load_blocked_index(analysis_config: dict[str, object]) -> dict[tuple[str, str], dict[str, str]]:
    rows = analysis_config.get("blocked_pairs", [])
    if not isinstance(rows, list):
        return {}
    blocked_index: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = (str(row.get("entrant_id", "")), str(row.get("dataset_id", "")))
        blocked_index[key] = {
            "blocker_status": str(row.get("blocker_status", "blocked")),
            "blocker_note": str(row.get("blocker_note", "")),
        }
    return blocked_index


def status_rank(value: str) -> int:
    mapping = {
        "better_than_mean_shift_baseline": 3,
        "mixed_vs_mean_shift_baseline": 2,
        "worse_than_mean_shift_baseline": 1,
        "missing_mean_shift_comparison": 0,
        "not_evaluated": -1,
    }
    return mapping.get(value, -1)


def coverage_status_from_counts(*, evaluated: int, pending: int, blocked: int, total: int) -> str:
    if total <= 0:
        return "empty"
    if evaluated == total:
        return "fully_evaluated"
    if evaluated > 0:
        return "partially_evaluated"
    if pending == total:
        return "all_pending"
    if blocked == total:
        return "all_blocked"
    if pending > 0 and blocked > 0:
        return "mixed_pending_blocked"
    return "not_started"


def main() -> None:
    args = build_parser().parse_args()
    registry_rows = load_json(resolve_path(args.registry)).get("entrants", [])
    analysis_config = load_json(resolve_path(args.analysis_config))
    analysis_id = str(analysis_config["analysis_id"])
    dataset_rows = analysis_config.get("dataset_scope", [])
    output_root = resolve_path(args.output_root) / analysis_id
    readiness_index = load_readiness_index(resolve_path(args.readiness_path))
    blocked_index = load_blocked_index(analysis_config)
    output_root.mkdir(parents=True, exist_ok=True)

    dataset_level_rows: list[dict[str, object]] = []
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
            readiness_row = readiness_index.get(dataset_id, {})
            blocked_row = blocked_index.get((entrant_id, dataset_id))
            if summary_path.exists():
                evaluation_status = "evaluated"
                blocker_status = ""
                blocker_note = ""
            elif blocked_row is not None:
                evaluation_status = "blocked"
                blocker_status = blocked_row["blocker_status"]
                blocker_note = blocked_row["blocker_note"]
            elif bool(readiness_row.get("ready_end_to_end", False)):
                evaluation_status = "pending"
                blocker_status = ""
                blocker_note = ""
            else:
                evaluation_status = "blocked"
                blocker_status = "dataset_not_ready"
                blocker_note = str(readiness_row.get("readiness_note", "dataset readiness 未闭合。"))
            dataset_level_rows.append(
                {
                    "entrant_id": entrant_id,
                    "model_id": model_id,
                    "entrant_status": status,
                    "dataset_id": dataset_id,
                    "tier": tier,
                    "usage": str(dataset.get("usage", "")),
                    "evaluation_status": evaluation_status,
                    "blocker_status": blocker_status,
                    "blocker_note": blocker_note,
                    "vs_mean_shift_status": classify_vs_mean_shift(comparison_path),
                    "pearson_mean": normalize_numeric(aggregate_scores.get("pearson_mean")),
                    "rmse_mean": normalize_numeric(aggregate_scores.get("rmse_mean")),
                    "top50_jaccard_mean": normalize_numeric(aggregate_scores.get("top50_jaccard_mean")),
                }
            )

    dataset_level_frame = pd.DataFrame(dataset_level_rows).sort_values(
        ["tier", "dataset_id", "entrant_id"]
    ).reset_index(drop=True)

    entrant_overview_rows: list[dict[str, object]] = []
    for entrant in registry_rows:
        entrant_id = str(entrant["entrant_id"])
        model_id = str(entrant["model_id"])
        entrant_frame = dataset_level_frame[dataset_level_frame["entrant_id"] == entrant_id].copy()
        evaluated_frame = entrant_frame[entrant_frame["evaluation_status"] == "evaluated"].copy()
        entrant_overview_rows.append(
            {
                "entrant_id": entrant_id,
                "model_id": model_id,
                "entrant_status": str(entrant["status"]),
                "split_seed": int(analysis_config["split_seed"]),
                "dataset_count": int(len(entrant_frame)),
                "evaluated_dataset_count": int(len(evaluated_frame)),
                "better_count": int(
                    (entrant_frame["vs_mean_shift_status"] == "better_than_mean_shift_baseline").sum()
                ),
                "mixed_count": int(
                    (entrant_frame["vs_mean_shift_status"] == "mixed_vs_mean_shift_baseline").sum()
                ),
                "worse_count": int(
                    (entrant_frame["vs_mean_shift_status"] == "worse_than_mean_shift_baseline").sum()
                ),
                "pending_count": int((entrant_frame["evaluation_status"] == "pending").sum()),
                "blocked_count": int((entrant_frame["evaluation_status"] == "blocked").sum()),
                "formal_better_count": int(
                    (
                        (entrant_frame["tier"] == "formal")
                        & (entrant_frame["vs_mean_shift_status"] == "better_than_mean_shift_baseline")
                    ).sum()
                ),
                "supplement_better_count": int(
                    (
                        (entrant_frame["tier"] == "supplement")
                        & (entrant_frame["vs_mean_shift_status"] == "better_than_mean_shift_baseline")
                    ).sum()
                ),
                "pearson_mean_avg": (
                    round(float(evaluated_frame["pearson_mean"].dropna().mean()), 6)
                    if not evaluated_frame["pearson_mean"].dropna().empty
                    else None
                ),
                "rmse_mean_avg": (
                    round(float(evaluated_frame["rmse_mean"].dropna().mean()), 6)
                    if not evaluated_frame["rmse_mean"].dropna().empty
                    else None
                ),
                "top50_jaccard_mean_avg": (
                    round(float(evaluated_frame["top50_jaccard_mean"].dropna().mean()), 6)
                    if not evaluated_frame["top50_jaccard_mean"].dropna().empty
                    else None
                ),
            }
        )
    entrant_overview_frame = pd.DataFrame(entrant_overview_rows).sort_values(
        [
            "better_count",
            "formal_better_count",
            "supplement_better_count",
            "pearson_mean_avg",
            "entrant_id",
        ],
        ascending=[False, False, False, False, True],
    ).reset_index(drop=True)

    dataset_coverage_rows: list[dict[str, object]] = []
    for dataset in dataset_rows:
        dataset_id = str(dataset["dataset_id"])
        dataset_frame = dataset_level_frame[dataset_level_frame["dataset_id"] == dataset_id].copy()
        evaluated_count = int((dataset_frame["evaluation_status"] == "evaluated").sum())
        pending_count = int((dataset_frame["evaluation_status"] == "pending").sum())
        blocked_count = int((dataset_frame["evaluation_status"] == "blocked").sum())
        total_count = int(len(dataset_frame))
        dataset_coverage_rows.append(
            {
                "dataset_id": dataset_id,
                "tier": str(dataset["tier"]),
                "usage": str(dataset.get("usage", "")),
                "entrant_count": total_count,
                "evaluated_count": evaluated_count,
                "pending_count": pending_count,
                "blocked_count": blocked_count,
                "coverage_status": coverage_status_from_counts(
                    evaluated=evaluated_count,
                    pending=pending_count,
                    blocked=blocked_count,
                    total=total_count,
                ),
            }
        )
    dataset_coverage_frame = pd.DataFrame(dataset_coverage_rows).sort_values(
        ["tier", "dataset_id"]
    ).reset_index(drop=True)

    dataset_leader_rows: list[dict[str, object]] = []
    for dataset in dataset_rows:
        dataset_id = str(dataset["dataset_id"])
        dataset_frame = dataset_level_frame[
            (dataset_level_frame["dataset_id"] == dataset_id)
            & (dataset_level_frame["evaluation_status"] == "evaluated")
        ].copy()
        if dataset_frame.empty:
            dataset_leader_rows.append(
                {
                    "dataset_id": dataset_id,
                    "tier": str(dataset["tier"]),
                    "usage": str(dataset.get("usage", "")),
                    "leader_entrant_id": "",
                    "leader_model_id": "",
                    "leader_vs_mean_shift_status": "not_evaluated",
                    "leader_pearson_mean": None,
                    "leader_rmse_mean": None,
                }
            )
            continue
        dataset_frame["vs_rank"] = dataset_frame["vs_mean_shift_status"].map(status_rank)
        dataset_frame = dataset_frame.sort_values(
            ["vs_rank", "pearson_mean", "rmse_mean", "entrant_id"],
            ascending=[False, False, True, True],
            na_position="last",
        ).reset_index(drop=True)
        leader = dataset_frame.iloc[0]
        dataset_leader_rows.append(
            {
                "dataset_id": dataset_id,
                "tier": str(dataset["tier"]),
                "usage": str(dataset.get("usage", "")),
                "leader_entrant_id": str(leader["entrant_id"]),
                "leader_model_id": str(leader["model_id"]),
                "leader_vs_mean_shift_status": str(leader["vs_mean_shift_status"]),
                "leader_pearson_mean": normalize_numeric(leader["pearson_mean"]),
                "leader_rmse_mean": normalize_numeric(leader["rmse_mean"]),
            }
        )
    dataset_leader_frame = pd.DataFrame(dataset_leader_rows).sort_values(
        ["tier", "dataset_id"]
    ).reset_index(drop=True)

    dataset_level_tsv_path = output_root / "dataset_level.tsv"
    entrant_overview_tsv_path = output_root / "entrant_overview.tsv"
    dataset_coverage_tsv_path = output_root / "dataset_coverage.tsv"
    dataset_leader_tsv_path = output_root / "dataset_leaders.tsv"
    md_path = output_root / "summary.md"

    dataset_level_frame.to_csv(dataset_level_tsv_path, sep="\t", index=False)
    entrant_overview_frame.to_csv(entrant_overview_tsv_path, sep="\t", index=False)
    dataset_coverage_frame.to_csv(dataset_coverage_tsv_path, sep="\t", index=False)
    dataset_leader_frame.to_csv(dataset_leader_tsv_path, sep="\t", index=False)

    lines = [
        f"# {analysis_id}",
        "",
        f"- split seed：`{analysis_config['split_seed']}`",
        f"- 数据集范围：`{len(dataset_rows)}` 个（`3 formal + 4 supplement/runnable`）",
        f"- entrant 范围：`{len(registry_rows)}` 个 supplement entrants",
        "",
        "## Entrant Overview",
        "",
        "| entrant_id | model_id | better_count | mixed_count | worse_count | pending_count | blocked_count |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in entrant_overview_frame.itertuples(index=False):
        lines.append(
            f"| {row.entrant_id} | {row.model_id} | {row.better_count} | {row.mixed_count} | {row.worse_count} | {row.pending_count} | {row.blocked_count} |"
        )
    lines.extend(
        [
            "",
            "## Dataset Coverage",
            "",
            "| dataset_id | tier | coverage_status | evaluated_count | pending_count | blocked_count |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in dataset_coverage_frame.itertuples(index=False):
        lines.append(
            f"| {row.dataset_id} | {row.tier} | {row.coverage_status} | {row.evaluated_count} | {row.pending_count} | {row.blocked_count} |"
        )
    lines.extend(
        [
            "",
            "## Dataset Leaders",
            "",
            "| dataset_id | tier | leader_entrant_id | leader_model_id | leader_vs_mean_shift_status |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in dataset_leader_frame.itertuples(index=False):
        lines.append(
            f"| {row.dataset_id} | {row.tier} | {row.leader_entrant_id} | {row.leader_model_id} | {row.leader_vs_mean_shift_status} |"
        )
    lines.extend(
        [
            "",
            "## Dataset Level",
            "",
            "| entrant_id | dataset_id | tier | vs_mean_shift_status | evaluation_status | blocker_status |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in dataset_level_frame.itertuples(index=False):
        lines.append(
            f"| {row.entrant_id} | {row.dataset_id} | {row.tier} | {row.vs_mean_shift_status} | {row.evaluation_status} | {row.blocker_status} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"已写出: {dataset_level_tsv_path}")
    print(f"已写出: {entrant_overview_tsv_path}")
    print(f"已写出: {dataset_coverage_tsv_path}")
    print(f"已写出: {dataset_leader_tsv_path}")
    print(f"已写出: {md_path}")


if __name__ == "__main__":
    main()
