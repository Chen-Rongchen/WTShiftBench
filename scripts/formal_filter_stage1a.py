from __future__ import annotations

import argparse
import json
from pathlib import Path

import anndata as ad
import pandas as pd

from stage1a_catalog import FORMAL_SOURCE_DATASETS
from scripts.stage1a.dataset_semantics import (
    canonicalize_gene_series,
    is_adamson_control_target,
    parse_adamson_target_series,
)

OUTPUT_DIR = Path("data/processed/stage1a/formal_filtered")
STANDARD_STRING_COLUMNS = [
    "dataset_id",
    "cell_id",
    "perturbation_label_raw",
    "perturbation_label_clean",
    "target_gene",
    "target_gene_id",
]


def json_ready(value):
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_ready(v) for v in value]
    if isinstance(value, tuple):
        return [json_ready(v) for v in value]
    if pd.isna(value):
        return None
    return value


def stringify(series: pd.Series) -> pd.Series:
    return series.astype("string")


def to_object_string(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).astype(object)


def assert_retained_targets_complete(dataset_name: str, filtered_obs: pd.DataFrame) -> None:
    non_control_mask = ~filtered_obs["is_control"].astype(bool)
    invalid_target_rows = filtered_obs.loc[
        non_control_mask & filtered_obs["target_gene"].astype("string").str.strip().eq(""),
        ["cell_id", "perturbation_label_raw", "perturbation_label_clean", "target_gene"],
    ]
    if not invalid_target_rows.empty:
        raise ValueError(
            f"{dataset_name} 存在被保留但 target_gene 为空的非 control 细胞: "
            f"{invalid_target_rows.head(10).to_dict(orient='records')}"
        )


def build_standard_obs(dataset_name: str, obs: pd.DataFrame, var_names: pd.Index | None = None) -> pd.DataFrame:
    if "perturbation" not in obs.columns or "nperts" not in obs.columns:
        raise ValueError(f"{dataset_name} 缺少 formal filtering 所需关键列。")

    standardized = obs.copy()
    perturbation = stringify(standardized["perturbation"]).fillna("")
    nperts = pd.to_numeric(standardized["nperts"], errors="coerce")

    is_control = perturbation.eq("control")
    is_single_perturbation = (~is_control) & nperts.eq(1)
    formal_keep = is_control | is_single_perturbation

    standardized["dataset_id"] = dataset_name
    standardized["cell_id"] = standardized.index.astype(str)
    standardized["is_control"] = is_control.astype(bool)
    standardized["perturbation_label_raw"] = perturbation
    standardized["is_single_perturbation"] = is_single_perturbation.astype(bool)
    standardized["formal_keep"] = formal_keep.astype(bool)

    if dataset_name in {"replogle_2022_k562_essential", "replogle_2022_rpe1"}:
        if "gene" not in standardized.columns or "gene_id" not in standardized.columns:
            raise ValueError(f"{dataset_name} 缺少 `gene/gene_id`，无法清洗 target。")

        gene = stringify(standardized["gene"]).fillna("")
        gene_id = stringify(standardized["gene_id"]).fillna("")

        target_gene = gene.where(~gene.eq("non-targeting"), other="")
        target_gene_id = gene_id.where(~gene.eq("non-targeting"), other="")
        perturbation_label_clean = target_gene.where(~is_control, other="control")

        standardized["perturbation_label_clean"] = perturbation_label_clean
        standardized["target_gene"] = target_gene
        standardized["target_gene_id"] = target_gene_id
    elif dataset_name in {"tian_2019_day7neuron", "tian_2019_ipsc", "tian_2021_crispri"}:
        target_gene = perturbation.where(~is_control, other="")
        perturbation_label_clean = perturbation.where(~is_control, other="control")

        standardized["perturbation_label_clean"] = perturbation_label_clean
        standardized["target_gene"] = target_gene
        standardized["target_gene_id"] = pd.Series("", index=standardized.index, dtype=object)
    elif dataset_name == "norman_2019":
        target_gene = canonicalize_gene_series(perturbation.where(~is_control, other=""))
        valid_targets = set(map(str, var_names.astype(str))) if var_names is not None else None
        if valid_targets is not None:
            valid_single_target = target_gene.isin(valid_targets)
            is_single_perturbation = is_single_perturbation & valid_single_target
            formal_keep = is_control | is_single_perturbation
        perturbation_label_clean = target_gene.where(~is_control, other="control")

        standardized["is_single_perturbation"] = is_single_perturbation.astype(bool)
        standardized["formal_keep"] = formal_keep.astype(bool)
        standardized["perturbation_label_clean"] = perturbation_label_clean
        standardized["target_gene"] = target_gene
        standardized["target_gene_id"] = pd.Series("", index=standardized.index, dtype=object)
    elif dataset_name == "adamson_2016_upr_perturb_seq":
        parsed_target = canonicalize_gene_series(parse_adamson_target_series(perturbation))
        is_control = is_adamson_control_target(parsed_target)
        is_single_perturbation = parsed_target.ne("") & ~is_control
        formal_keep = is_control | is_single_perturbation

        standardized["is_control"] = is_control.astype(bool)
        standardized["is_single_perturbation"] = is_single_perturbation.astype(bool)
        standardized["formal_keep"] = formal_keep.astype(bool)
        standardized["perturbation_label_clean"] = parsed_target.where(~is_control, other="control")
        standardized["target_gene"] = parsed_target.where(~is_control, other="")
        standardized["target_gene_id"] = pd.Series("", index=standardized.index, dtype=object)
    else:
        raise ValueError(f"未定义的数据集过滤规则: {dataset_name}")

    for column in STANDARD_STRING_COLUMNS:
        standardized[column] = to_object_string(standardized[column])

    return standardized


def build_filter_report(
    dataset_name: str,
    raw_adata,
    filtered_adata,
    raw_obs: pd.DataFrame,
    filtered_obs: pd.DataFrame,
    output_path: Path,
) -> dict[str, object]:
    raw_cells = int(raw_adata.n_obs)
    kept_cells = int(filtered_adata.n_obs)
    kept_controls = int(filtered_obs["is_control"].sum())
    kept_perturbed_cells = int((~filtered_obs["is_control"]).sum())
    removed_multi_perturbation_cells = int(
        ((~raw_obs["is_control"]) & (~raw_obs["is_single_perturbation"])).sum()
    )
    removed_non_target_resolved_cells = int(
        (
            (~raw_obs["is_control"])
            & raw_obs["is_single_perturbation"].astype(bool)
            & raw_obs["target_gene"].astype("string").str.strip().ne("")
            & (~raw_obs["formal_keep"].astype(bool))
        ).sum()
    )
    unique_target_count = int(
        filtered_obs.loc[~filtered_obs["is_control"], "target_gene"].astype("string").nunique()
    )
    track_target_gene_id = dataset_name in {"replogle_2022_k562_essential", "replogle_2022_rpe1"}
    missing_target_gene_id_rows = (
        int(
            (
                (~filtered_obs["is_control"].astype(bool))
                & filtered_obs["target_gene_id"].astype("string").str.strip().eq("")
            ).sum()
        )
        if track_target_gene_id
        else 0
    )

    return {
        "dataset": dataset_name,
        "raw_cells": raw_cells,
        "kept_cells": kept_cells,
        "kept_controls": kept_controls,
        "kept_perturbed_cells": kept_perturbed_cells,
        "removed_multi_perturbation_cells": removed_multi_perturbation_cells,
        "removed_unresolved_target_cells": removed_non_target_resolved_cells,
        "unique_target_count": unique_target_count,
        "missing_target_gene_id_rows": missing_target_gene_id_rows,
        "final_status": "pass",
        "output_path": str(output_path),
        "note": (
            "已按 formal 主线规则完成过滤并补齐标准 obs 字段。"
            if missing_target_gene_id_rows == 0 and removed_non_target_resolved_cells == 0
            else "已按 formal 主线规则完成过滤；保留 target_gene 作为 formal 主键，部分细胞缺少 source gene_id。"
            if missing_target_gene_id_rows > 0
            else "已按 formal 主线规则完成过滤；剔除了 target 未闭合的细胞。"
        ),
    }


def process_dataset(dataset_name: str, input_path: Path) -> tuple[dict[str, object], Path]:
    print(f"开始处理: {dataset_name}")
    adata = ad.read_h5ad(input_path)

    standardized_obs = build_standard_obs(dataset_name, adata.obs, adata.var_names)
    adata.obs = standardized_obs

    filtered = adata[adata.obs["formal_keep"].astype(bool)].copy()
    assert_retained_targets_complete(dataset_name=dataset_name, filtered_obs=filtered.obs)
    output_path = OUTPUT_DIR / f"{dataset_name}.h5ad"
    filtered.write_h5ad(output_path)

    report = build_filter_report(
        dataset_name=dataset_name,
        raw_adata=adata,
        filtered_adata=filtered,
        raw_obs=adata.obs,
        filtered_obs=filtered.obs,
        output_path=output_path,
    )

    report_path = OUTPUT_DIR / f"{dataset_name}.filter_report.json"
    report_path.write_text(
        json.dumps(json_ready(report), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"已写出: {output_path}")
    print(f"已写出: {report_path}")
    return report, report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按 Stage 1A formal 规则过滤数据集。")
    parser.add_argument(
        "--dataset",
        action="append",
        dest="datasets",
        help="仅处理指定 dataset_id；可重复传入多次。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict[str, object]] = []
    selected = set(args.datasets or [])

    for dataset in FORMAL_SOURCE_DATASETS:
        if selected and dataset.name not in selected:
            continue
        report, _ = process_dataset(dataset.name, dataset.path)
        summary_rows.append(report)

    if not summary_rows:
        raise ValueError("未匹配到任何待处理数据集。")

    summary_df = pd.DataFrame(summary_rows).sort_values("dataset").reset_index(drop=True)
    summary_path = OUTPUT_DIR / "formal_filter_summary.tsv"
    summary_df.to_csv(summary_path, sep="\t", index=False)
    print(f"已写出: {summary_path}")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
