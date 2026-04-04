from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import anndata as ad
import pandas as pd
import yaml

try:
    from scripts.stage1a.dataset_semantics import canonicalize_gene_series
except ModuleNotFoundError:
    from stage1a.dataset_semantics import canonicalize_gene_series


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = (
    PROJECT_ROOT / "configs/stage1a/candidate_audits/formalization_candidates.json"
)
GOVERNANCE_PATH = PROJECT_ROOT / "configs/stage1a_split_governance.yaml"
OUTPUT_DATA_DIR = PROJECT_ROOT / "data/processed/stage1a/candidate_formal_like"
OUTPUT_REPORT_DIR = PROJECT_ROOT / "reports/stage1a/candidate_formalization"
OUTPUT_ELIGIBILITY_DIR = PROJECT_ROOT / "reports/stage1a/candidate_pseudobulk_eligibility"
CONTROL_SGRNA_REGEX = re.compile(r"NO_SITE|NON-GENE|CONTROL", flags=re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将候选数据集尽可能标准化到 formal-like 形态。")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="候选 formalization 配置 JSON。",
    )
    parser.add_argument(
        "--dataset-id",
        action="append",
        dest="dataset_ids",
        help="仅处理指定 dataset_id；可重复传入。",
    )
    return parser.parse_args()


def load_min_cells_per_group() -> int:
    if not GOVERNANCE_PATH.exists():
        return 5
    payload = yaml.safe_load(GOVERNANCE_PATH.read_text(encoding="utf-8")) or {}
    return int(payload.get("min_cells_per_group", 5))


def load_config(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    datasets = payload.get("datasets", [])
    if not datasets:
        raise ValueError(f"{path} 未定义 datasets。")
    return [dict(item) for item in datasets]


def stringify(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("")


def to_object_string(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).astype(object)


def build_standard_obs(adata, item: dict[str, object]) -> tuple[pd.DataFrame, str]:
    dataset_id = str(item["dataset_id"])
    mode = str(item["mode"])
    obs = adata.obs.copy()
    standardized = obs.copy()
    standardized["dataset_id"] = dataset_id
    standardized["cell_id"] = standardized.index.astype(str)

    note = ""

    if mode == "tian_like":
        perturbation = stringify(standardized["perturbation"])
        nperts = pd.to_numeric(standardized["nperts"], errors="coerce")
        is_control = perturbation.eq("control")
        is_single = (~is_control) & nperts.eq(1)
        formal_keep = is_control | is_single
        standardized["perturbation_label_raw"] = perturbation
        standardized["perturbation_label_clean"] = perturbation.where(~is_control, other="control")
        standardized["target_gene"] = perturbation.where(~is_control, other="")
        standardized["target_gene_id"] = pd.Series("", index=standardized.index, dtype=object)
        standardized["is_control"] = is_control.astype(bool)
        standardized["is_single_perturbation"] = is_single.astype(bool)
        standardized["formal_like_keep"] = formal_keep.astype(bool)
        note = "沿用 Tian 系列的 nperts == 1 single-target 规则。"
    elif mode == "replogle_gwps":
        gene = stringify(standardized["gene"])
        gene_id = stringify(standardized["gene_id"]) if "gene_id" in standardized.columns else pd.Series("", index=standardized.index, dtype="string")
        is_control = gene.eq("non-targeting")
        is_single = gene.ne("") & ~is_control
        formal_keep = is_control | is_single
        standardized["perturbation_label_raw"] = gene
        standardized["perturbation_label_clean"] = gene.where(~is_control, other="control")
        standardized["target_gene"] = gene.where(~is_control, other="")
        standardized["target_gene_id"] = gene_id.where(~is_control, other="")
        standardized["is_control"] = is_control.astype(bool)
        standardized["is_single_perturbation"] = is_single.astype(bool)
        standardized["formal_like_keep"] = formal_keep.astype(bool)
        note = "按 gene-level target 聚合；保留 paired-guide 身份，但 formal-like 主键落在 target_gene。"
    elif mode == "norman_raw":
        guide_ids = stringify(standardized["guide_ids"])
        target_gene = canonicalize_gene_series(guide_ids)
        if "gene_symbols" in adata.var.columns:
            valid_targets = set(map(str, stringify(adata.var["gene_symbols"]).tolist()))
        else:
            valid_targets = set(map(str, adata.var_names.astype(str)))
        is_control = guide_ids.eq("")
        is_single = guide_ids.ne("") & ~guide_ids.str.contains(",", na=False)
        valid_single = target_gene.isin(valid_targets)
        is_single = is_single & valid_single
        formal_keep = is_control | is_single
        standardized["perturbation_label_raw"] = guide_ids
        standardized["perturbation_label_clean"] = target_gene.where(~is_control, other="control")
        standardized["target_gene"] = target_gene.where(~is_control, other="")
        standardized["target_gene_id"] = pd.Series("", index=standardized.index, dtype=object)
        standardized["is_control"] = is_control.astype(bool)
        standardized["is_single_perturbation"] = is_single.astype(bool)
        standardized["formal_like_keep"] = formal_keep.astype(bool)
        note = "从 guide_ids 切出 single-target 子集；组合扰动保留在 side-track 语义里，不写入 formal-like 过滤结果。"
    elif mode == "dixit_context":
        condition = stringify(standardized["condition"])
        moi = stringify(standardized["MOI"])
        sgrna = stringify(standardized["sgRNA"])
        subset_condition = str(item["subset_condition"])
        in_context = condition.eq(subset_condition)
        control_like = sgrna.str.contains(CONTROL_SGRNA_REGEX, na=False)
        non_empty = sgrna.ne("")
        is_control = in_context & control_like
        is_single = in_context & moi.eq("1") & non_empty & ~control_like
        formal_keep = is_control | is_single
        target_gene = sgrna.str.replace(r"_[0-9]+$", "", regex=True)
        standardized["perturbation_label_raw"] = sgrna
        standardized["perturbation_label_clean"] = target_gene.where(~is_control, other="control")
        standardized["target_gene"] = target_gene.where(~is_control, other="")
        standardized["target_gene_id"] = pd.Series("", index=standardized.index, dtype=object)
        standardized["is_control"] = is_control.astype(bool)
        standardized["is_single_perturbation"] = is_single.astype(bool)
        standardized["formal_like_keep"] = formal_keep.astype(bool)
        note = f"按 condition={subset_condition} 且 MOI==1 切成 context-specific formal-like 子集；整包 dixit_2016_raw 仍不作为单一 formal 数据集。"
    else:
        raise ValueError(f"未定义的 formalization mode: {mode}")

    for column in [
        "dataset_id",
        "cell_id",
        "perturbation_label_raw",
        "perturbation_label_clean",
        "target_gene",
        "target_gene_id",
    ]:
        standardized[column] = to_object_string(standardized[column])
    return standardized, note


def build_eligibility(filtered_obs: pd.DataFrame, min_cells_per_group: int) -> pd.DataFrame:
    is_control = filtered_obs["is_control"].astype(bool)
    target_gene = stringify(filtered_obs["target_gene"])
    n_cells_control = int(is_control.sum())
    perturbed_counts = (
        target_gene.loc[~is_control]
        .loc[lambda s: s.ne("")]
        .value_counts()
        .rename_axis("target_gene")
        .reset_index(name="n_cells_perturbed")
        .sort_values(["n_cells_perturbed", "target_gene"], ascending=[False, True])
        .reset_index(drop=True)
    )
    if perturbed_counts.empty:
        return pd.DataFrame(
            columns=[
                "target_gene",
                "n_cells_perturbed",
                "n_cells_control",
                "eligible_for_pseudobulk",
                "eligible_reason",
            ]
        )
    eligibility = perturbed_counts.assign(n_cells_control=n_cells_control)
    eligibility["eligible_for_pseudobulk"] = (
        eligibility["n_cells_perturbed"].ge(min_cells_per_group)
        & eligibility["n_cells_control"].ge(min_cells_per_group)
    )
    eligibility["eligible_reason"] = eligibility["eligible_for_pseudobulk"].map(
        {
            True: f"pass: perturbed>={min_cells_per_group} 且 control>={min_cells_per_group}",
            False: f"fail: perturbed<{min_cells_per_group} 或 control<{min_cells_per_group}",
        }
    )
    return eligibility


def build_report(
    dataset_id: str,
    input_path: Path,
    output_path: Path | None,
    raw_obs: pd.DataFrame,
    filtered_obs: pd.DataFrame,
    eligibility: pd.DataFrame,
    mode_note: str,
    min_cells_per_group: int,
) -> dict[str, object]:
    is_control_raw = raw_obs["is_control"].astype(bool)
    is_single_raw = raw_obs["is_single_perturbation"].astype(bool)
    keep_raw = raw_obs["formal_like_keep"].astype(bool)
    eligible_mask = eligibility["eligible_for_pseudobulk"] if not eligibility.empty else pd.Series(dtype=bool)
    return {
        "dataset_id": dataset_id,
        "input_path": str(input_path),
        "output_path": "" if output_path is None else str(output_path),
        "raw_cells": int(raw_obs.shape[0]),
        "kept_cells": int(filtered_obs.shape[0]),
        "kept_controls": int(filtered_obs["is_control"].astype(bool).sum()),
        "kept_perturbed_cells": int((~filtered_obs["is_control"].astype(bool)).sum()),
        "removed_non_single_cells": int(((~is_control_raw) & (~is_single_raw)).sum()),
        "removed_non_kept_cells": int((~keep_raw).sum()),
        "unique_targets_kept": int(
            stringify(filtered_obs.loc[~filtered_obs["is_control"].astype(bool), "target_gene"]).nunique()
        ),
        "eligible_targets_ge_floor": int(eligible_mask.sum()) if not eligibility.empty else 0,
        "min_cells_per_group": int(min_cells_per_group),
        "formalization_note": mode_note,
    }


def process_item(item: dict[str, object], min_cells_per_group: int) -> tuple[str, Path, Path]:
    dataset_id = str(item["dataset_id"])
    input_path = PROJECT_ROOT / str(item["input_path"])
    OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ELIGIBILITY_DIR / dataset_id).mkdir(parents=True, exist_ok=True)

    write_filtered_h5ad = bool(item.get("write_filtered_h5ad", True))
    output_path = OUTPUT_DATA_DIR / f"{dataset_id}.h5ad"
    if write_filtered_h5ad:
        adata = ad.read_h5ad(input_path)
        standardized_obs, mode_note = build_standard_obs(adata, item)
        adata.obs = standardized_obs
        keep_mask = adata.obs["formal_like_keep"].astype(bool).to_numpy()
        filtered_obs = adata.obs.loc[keep_mask].copy()
        filtered = adata[keep_mask].copy()
        filtered.obs = filtered_obs
        filtered.write_h5ad(output_path)
        raw_obs_for_report = adata.obs
    else:
        adata = ad.read_h5ad(input_path, backed="r")
        try:
            standardized_obs, mode_note = build_standard_obs(adata, item)
        finally:
            adata.file.close()
        keep_mask = standardized_obs["formal_like_keep"].astype(bool).to_numpy()
        filtered_obs = standardized_obs.loc[keep_mask].copy()
        raw_obs_for_report = standardized_obs

    eligibility = build_eligibility(filtered_obs, min_cells_per_group=min_cells_per_group)
    eligibility.insert(0, "dataset_id", dataset_id)
    eligibility_path = OUTPUT_ELIGIBILITY_DIR / dataset_id / "perturbation_eligibility.tsv"
    eligibility.to_csv(eligibility_path, sep="\t", index=False)

    report = build_report(
        dataset_id=dataset_id,
        input_path=input_path,
        output_path=output_path if write_filtered_h5ad else None,
        raw_obs=raw_obs_for_report,
        filtered_obs=filtered_obs,
        eligibility=eligibility.drop(columns=["dataset_id"]),
        mode_note=mode_note,
        min_cells_per_group=min_cells_per_group,
    )
    report["write_filtered_h5ad"] = write_filtered_h5ad
    report_path = OUTPUT_REPORT_DIR / f"{dataset_id}.formalization_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return dataset_id, output_path, report_path


def main() -> None:
    args = parse_args()
    min_cells_per_group = load_min_cells_per_group()
    items = load_config(args.config)
    if args.dataset_ids:
        wanted = set(args.dataset_ids)
        items = [item for item in items if str(item["dataset_id"]) in wanted]

    for item in items:
        dataset_id, output_path, report_path = process_item(
            item=item,
            min_cells_per_group=min_cells_per_group,
        )
        print(f"已写出: {output_path}")
        print(f"已写出: {report_path}")


if __name__ == "__main__":
    main()
