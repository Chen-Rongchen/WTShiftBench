from __future__ import annotations

from pathlib import Path
import re

import anndata as ad
import pandas as pd

from stage1a_catalog import FORMAL_SOURCE_DATASETS, RAW_STAGE1A_DIR

KEY_COLUMNS = ["perturbation", "gene", "target", "guide_id", "condition"]
FREQUENCY_COLUMNS = ["perturbation", "gene", "guide_id"]
CONTROL_PATTERNS = [
    r"control",
    r"non[-_ ]?target",
    r"\bntc\b",
    r"mock",
    r"neg",
    r"neutral",
    r"safe",
    r"gal4",
    r"63\(mod\)",
]
CONTROL_REGEX = re.compile("|".join(CONTROL_PATTERNS), flags=re.IGNORECASE)


def format_columns(columns) -> str:
    return ",".join(map(str, columns))


def describe_presence(adata, column: str) -> str:
    in_obs = column in adata.obs.columns
    in_var = column in adata.var.columns
    if in_obs and in_var:
        return "obs,var"
    if in_obs:
        return "obs"
    if in_var:
        return "var"
    return "不存在"


def stringify_series(series: pd.Series) -> pd.Series:
    return series.astype("string")


def top_value_counts(series: pd.Series, limit: int = 30) -> pd.Series:
    values = stringify_series(series).fillna("<NA>")
    return values.value_counts(dropna=False).head(limit)


def find_control_candidates(series: pd.Series) -> pd.Series:
    values = stringify_series(series).dropna()
    matched = values[values.str.contains(CONTROL_REGEX, na=False)]
    if matched.empty:
        return matched
    return matched.value_counts()


def collect_source_columns(adata) -> list[str]:
    source_columns: list[str] = []
    for column in adata.obs.columns:
        candidates = find_control_candidates(adata.obs[column])
        if not candidates.empty:
            source_columns.append(str(column))
    return source_columns


def print_top_values(adata, dataset_name: str) -> None:
    print(f"=== {dataset_name} ===")
    print(f"shape: {adata.shape}")
    print(f"obs.columns: {list(map(str, adata.obs.columns))}")
    print(f"var.columns: {list(map(str, adata.var.columns))}")
    print("关键列检查:")
    for column in KEY_COLUMNS:
        print(f"  - {column}: {describe_presence(adata, column)}")

    for column in FREQUENCY_COLUMNS:
        if column not in adata.obs.columns:
            print(f"[{column}] 不存在")
            continue
        print(f"[{column}] top 30:")
        counts = top_value_counts(adata.obs[column], limit=30)
        print(counts.to_string())

    print()


def build_audit_row(dataset_name: str, adata) -> dict[str, object]:
    source_columns = collect_source_columns(adata)
    return {
        "dataset": dataset_name,
        "n_cells": adata.n_obs,
        "n_genes": adata.n_vars,
        "obs_columns": format_columns(adata.obs.columns),
        "var_columns": format_columns(adata.var.columns),
        "has_perturbation_label": any(
            column in adata.obs.columns or column in adata.var.columns
            for column in ["perturbation", "gene", "target", "guide_id"]
        ),
        "has_control_or_condition": ("condition" in adata.obs.columns) or bool(source_columns),
        "candidate_control_source_columns": ",".join(source_columns),
    }


def build_control_rows(
    dataset_name: str, adata, limit_per_column: int = 30
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for column in adata.obs.columns:
        counts = find_control_candidates(adata.obs[column]).head(limit_per_column)
        if counts.empty:
            continue
        for label, count in counts.items():
            rows.append(
                {
                    "dataset": dataset_name,
                    "source_column": str(column),
                    "label_value": str(label),
                    "count": int(count),
                    "fraction": float(count) / float(adata.n_obs),
                }
            )
    return rows


def main() -> None:
    output_dir = RAW_STAGE1A_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    audit_rows: list[dict[str, object]] = []
    control_rows: list[dict[str, object]] = []

    for dataset in FORMAL_SOURCE_DATASETS:
        dataset_name = dataset.name
        dataset_path = dataset.path
        adata = ad.read_h5ad(dataset_path, backed="r")
        try:
            print_top_values(adata, dataset_name)
            audit_rows.append(build_audit_row(dataset_name, adata))
            control_rows.extend(build_control_rows(dataset_name, adata))
        finally:
            adata.file.close()

    audit_df = pd.DataFrame(audit_rows)
    control_df = pd.DataFrame(control_rows).sort_values(
        by=["dataset", "count", "source_column", "label_value"],
        ascending=[True, False, True, True],
    )

    audit_path = output_dir / "audit_summary.tsv"
    control_path = output_dir / "control_candidate_report.tsv"
    audit_df.to_csv(audit_path, sep="\t", index=False)
    control_df.to_csv(control_path, sep="\t", index=False)

    print(f"audit_summary 已保存: {audit_path}")
    print(audit_df.to_string(index=False))
    print()
    print(f"control_candidate_report 已保存: {control_path}")
    print(control_df.to_string(index=False))


if __name__ == "__main__":
    main()
