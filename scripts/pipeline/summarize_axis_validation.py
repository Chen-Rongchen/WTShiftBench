from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/axis_validation_summary_v1.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="汇总 Stage 2 axis validation 结果。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="axis validation summary 配置 JSON 路径。")
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload


def summarize_enrichment(enrichment: pd.DataFrame, fdr_cutoff: float) -> pd.DataFrame:
    if enrichment.empty:
        return pd.DataFrame(columns=["axis_id", "annotation_support"])
    all_axes = enrichment["axis_id"].drop_duplicates().sort_values().to_frame()
    kept = enrichment.loc[enrichment["FDR"].astype(float) <= fdr_cutoff].copy()
    if kept.empty:
        all_axes["annotation_support"] = f"enrichment_hits=0;databases=0@FDR<={fdr_cutoff}"
        return all_axes
    summary = (
        kept.groupby("axis_id", as_index=False)
        .agg(
            enrichment_hit_count=("term", "size"),
            enrichment_database_count=("database", "nunique"),
        )
    )
    summary["annotation_support"] = summary.apply(
        lambda row: f"enrichment_hits={int(row['enrichment_hit_count'])};databases={int(row['enrichment_database_count'])}@FDR<={fdr_cutoff}",
        axis=1,
    )
    merged = all_axes.merge(summary.loc[:, ["axis_id", "annotation_support"]], on="axis_id", how="left")
    merged["annotation_support"] = merged["annotation_support"].fillna(
        f"enrichment_hits=0;databases=0@FDR<={fdr_cutoff}"
    )
    return merged


def summarize_consistency(consistency: pd.DataFrame, min_recurrent_targets: int) -> pd.DataFrame:
    if consistency.empty:
        return pd.DataFrame(columns=["axis_id", "consistency_support"])
    all_axes = consistency["axis_id"].drop_duplicates().sort_values().to_frame()
    recurrence = (
        consistency.groupby(["axis_id", "database", "term"], as_index=False)["target_gene"]
        .nunique()
        .rename(columns={"target_gene": "recurrent_target_count"})
    )
    best = recurrence.sort_values(
        ["axis_id", "recurrent_target_count", "database", "term"],
        ascending=[True, False, True, True],
    ).drop_duplicates("axis_id")
    best["consistency_support"] = best.apply(
        lambda row: (
            f"top_recurrent_term={row['database']}::{row['term']};targets={int(row['recurrent_target_count'])}"
            if int(row["recurrent_target_count"]) >= min_recurrent_targets
            else "top_recurrent_term_below_threshold"
        ),
        axis=1,
    )
    merged = all_axes.merge(best.loc[:, ["axis_id", "consistency_support"]], on="axis_id", how="left")
    merged["consistency_support"] = merged["consistency_support"].fillna("top_recurrent_term_below_threshold")
    return merged


def write_markdown(path: Path, summary: pd.DataFrame) -> None:
    lines = [
        "# Stage 2 Axis Validation Summary",
        "",
        "## 说明",
        "",
        "- 本摘要只汇总当前 `axis_enrichment` 与 `per-target consistency` 的数量证据。",
        "- 它不会自动提升 frozen `final_call`，只提供保守的 validation 状态。",
        "",
        "## 逐轴摘要",
        "",
    ]
    for row in summary.itertuples(index=False):
        lines.append(f"### {row.axis_id}")
        lines.append(f"- axis_label: `{row.axis_label}`")
        lines.append(f"- structure_support: `{row.structure_support}`")
        lines.append(f"- annotation_support: `{row.annotation_support}`")
        lines.append(f"- consistency_support: `{row.consistency_support}`")
        lines.append(f"- final_call: `{row.final_call}`")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    config = load_json(resolve_path(args.config))

    axis_summary = pd.read_csv(resolve_path(str(config["input"]["axis_summary_path"])), sep="\t")
    axis_enrichment = pd.read_csv(resolve_path(str(config["input"]["axis_enrichment_path"])), sep="\t")
    axis_target_consistency = pd.read_csv(resolve_path(str(config["input"]["axis_target_consistency_path"])), sep="\t")

    fdr_cutoff = float(config["thresholds"]["enrichment_fdr_cutoff"])
    min_recurrent_targets = int(config["thresholds"]["min_recurrent_targets"])

    enrichment_summary = summarize_enrichment(axis_enrichment, fdr_cutoff=fdr_cutoff)
    consistency_summary = summarize_consistency(axis_target_consistency, min_recurrent_targets=min_recurrent_targets)

    merged = axis_summary.merge(enrichment_summary, on="axis_id", how="left", suffixes=("", "_new"))
    merged = merged.merge(consistency_summary, on="axis_id", how="left", suffixes=("", "_new"))
    if "annotation_support_new" in merged.columns:
        merged["annotation_support"] = merged["annotation_support_new"].fillna(merged["annotation_support"])
        merged = merged.drop(columns=["annotation_support_new"])
    if "consistency_support_new" in merged.columns:
        merged["consistency_support"] = merged["consistency_support_new"].fillna(merged["consistency_support"])
        merged = merged.drop(columns=["consistency_support_new"])

    table_path = resolve_path(str(config["output"]["table_path"]))
    markdown_path = resolve_path(str(config["output"]["markdown_path"]))
    table_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(table_path, sep="\t", index=False)
    write_markdown(markdown_path, merged)

    print(
        json.dumps(
            {
                "status": "completed",
                "table_path": str(table_path.relative_to(PROJECT_ROOT)),
                "markdown_path": str(markdown_path.relative_to(PROJECT_ROOT)),
                "n_axes": int(merged["axis_id"].nunique()),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
