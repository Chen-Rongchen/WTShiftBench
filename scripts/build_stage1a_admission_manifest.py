from __future__ import annotations

import json
from pathlib import Path

import anndata as ad
import pandas as pd
import yaml

try:
    from scripts.stage1a.benchmark_invariant.catalog import (
        PROJECT_ROOT,
        RAW_STAGE1A_DIR,
        get_source_dataset,
        load_formal_dataset_contracts,
    )
except ModuleNotFoundError:
    from stage1a_catalog import PROJECT_ROOT, RAW_STAGE1A_DIR, load_formal_dataset_contracts
    from stage1a.benchmark_invariant.catalog import get_source_dataset


RAW_AUDIT_DIR = RAW_STAGE1A_DIR
ELIGIBILITY_PATH = PROJECT_ROOT / "reports/stage1a/pseudobulk_eligibility/combined_eligibility.tsv"
FORMAL_FILTERED_DIR = PROJECT_ROOT / "data/processed/stage1a/formal_filtered"
OUTPUT_DIR = PROJECT_ROOT / "reports/stage1a/admission"
TSV_PATH = OUTPUT_DIR / "stage1a_admission_manifest.tsv"
JSON_PATH = OUTPUT_DIR / "stage1a_admission_manifest.json"
METADATA_PATH = OUTPUT_DIR / "stage1a_admission_manifest.metadata.json"
README_PATH = OUTPUT_DIR / "README.md"
GOVERNANCE_PATH = PROJECT_ROOT / "configs/stage1a_split_governance.yaml"


def load_governance() -> dict[str, object]:
    if not GOVERNANCE_PATH.exists():
        return {"min_cells_per_group": 5, "require_umi_depth_column": True}
    payload = yaml.safe_load(GOVERNANCE_PATH.read_text(encoding="utf-8")) or {}
    payload.setdefault("min_cells_per_group", 5)
    payload.setdefault("require_umi_depth_column", True)
    return payload


def load_audit_summary(dataset_id: str) -> dict[str, object]:
    path = RAW_AUDIT_DIR / f"{dataset_id}.audit_summary.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def load_filter_report(dataset_id: str) -> dict[str, object]:
    path = FORMAL_FILTERED_DIR / f"{dataset_id}.filter_report.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_eligibility_frame() -> pd.DataFrame:
    if not ELIGIBILITY_PATH.exists():
        return pd.DataFrame(
            columns=[
                "dataset_id",
                "target_gene",
                "n_cells_perturbed",
                "n_cells_control",
                "eligible_for_pseudobulk",
                "eligible_reason",
            ]
        )
    frame = pd.read_csv(ELIGIBILITY_PATH, sep="\t")
    frame["dataset_id"] = frame["dataset_id"].astype("string").str.strip()
    frame["eligible_for_pseudobulk"] = (
        frame["eligible_for_pseudobulk"].astype("string").str.lower().eq("true")
    )
    return frame


def build_eligibility_summary(eligibility: pd.DataFrame) -> pd.DataFrame:
    if eligibility.empty:
        return pd.DataFrame(
            columns=[
                "dataset_id",
                "min_cells_perturbed",
                "n_cells_control",
                "n_eligible_targets",
                "n_ineligible_targets",
            ]
        )

    base = (
        eligibility.groupby("dataset_id", dropna=False)
        .agg(
            n_cells_control=("n_cells_control", "max"),
            n_eligible_targets=("eligible_for_pseudobulk", "sum"),
            n_targets_total=("target_gene", "size"),
        )
        .reset_index()
    )
    eligible_only = eligibility.loc[eligibility["eligible_for_pseudobulk"]].copy()
    if eligible_only.empty:
        base["min_cells_perturbed"] = pd.NA
    else:
        min_cells = (
            eligible_only.groupby("dataset_id", dropna=False)["n_cells_perturbed"]
            .min()
            .rename("min_cells_perturbed")
        )
        base = base.merge(min_cells, on="dataset_id", how="left")
    base["n_eligible_targets"] = pd.to_numeric(base["n_eligible_targets"], errors="coerce").fillna(0).astype(int)
    base["n_targets_total"] = pd.to_numeric(base["n_targets_total"], errors="coerce").fillna(0).astype(int)
    base["n_ineligible_targets"] = base["n_targets_total"] - base["n_eligible_targets"]
    base = base.drop(columns=["n_targets_total"])
    return base


def read_umi_depth_summary(dataset_path: Path) -> dict[str, object]:
    adata = ad.read_h5ad(dataset_path, backed="r")
    try:
        obs = adata.obs.copy()
    finally:
        adata.file.close()

    if "ncounts" not in obs.columns:
        return {
            "umi_depth_column": "",
            "umi_depth_column_present": False,
            "umi_depth_median_all": None,
            "umi_depth_median_control": None,
            "umi_depth_median_perturbed": None,
            "umi_depth_p10_all": None,
            "umi_depth_p90_all": None,
        }

    ncounts = pd.to_numeric(obs["ncounts"], errors="coerce")
    is_control = pd.Series(False, index=obs.index)
    if "perturbation" in obs.columns:
        is_control = obs["perturbation"].astype("string").fillna("").eq("control")

    def safe_quantile(series: pd.Series, q: float) -> float | None:
        clean = series.dropna()
        if clean.empty:
            return None
        return float(clean.quantile(q))

    return {
        "umi_depth_column": "ncounts",
        "umi_depth_column_present": True,
        "umi_depth_median_all": safe_quantile(ncounts, 0.5),
        "umi_depth_median_control": safe_quantile(ncounts.loc[is_control], 0.5),
        "umi_depth_median_perturbed": safe_quantile(ncounts.loc[~is_control], 0.5),
        "umi_depth_p10_all": safe_quantile(ncounts, 0.1),
        "umi_depth_p90_all": safe_quantile(ncounts, 0.9),
    }


def barcode_assignment_status(audit: dict[str, object]) -> tuple[str, str]:
    guide_columns = audit.get("perturbation_related_obs_columns", {}).get("guide", [])
    if not guide_columns:
        return "hold", "缺少 guide / sgRNA 相关列。"
    if any(column in guide_columns for column in ["sgRNA_read_count", "sgRNA_umi_count"]):
        return "pass", "存在 guide 列，且含 sgRNA count/UMI 级信号。"
    return "proxy_only", "存在 guide 列，但缺少 sgRNA count/UMI 级信号。"


def moi_status(audit: dict[str, object]) -> tuple[str, str]:
    if "nperts" not in audit.get("obs_key_columns", []):
        return "hold", "缺少 nperts，无法以前置代理变量审计 observed multiplicity。"
    single = audit["single_perturbation_filterability"]
    if single["status"] != "pass":
        return "hold", "nperts 可见，但单扰动过滤规则未闭合。"
    return "proxy_only", "以 nperts 作为 observed multiplicity 代理；未见显式实验 MOI 字段。"


def processed_raw_level_status(dataset_path: Path) -> tuple[str, str, str]:
    return "pass", "processed_h5ad_resource", f"当前 formal source 为分发的 h5ad 资源：{dataset_path.name}"


def support_floor_status(
    dataset_id: str,
    eligibility_summary: pd.DataFrame,
    umi_summary: dict[str, object],
    *,
    min_cells_per_group: int,
    require_umi_depth_column: bool,
) -> tuple[str, str, dict[str, object]]:
    subset = eligibility_summary.loc[eligibility_summary["dataset_id"] == dataset_id].copy()
    if subset.empty:
        min_cells_perturbed = None
        n_cells_control = None
        eligible_targets = 0
        ineligible_targets = 0
    else:
        row = subset.iloc[0]
        min_cells_value = pd.to_numeric(pd.Series([row["min_cells_perturbed"]]), errors="coerce").iloc[0]
        control_value = pd.to_numeric(pd.Series([row["n_cells_control"]]), errors="coerce").iloc[0]
        min_cells_perturbed = None if pd.isna(min_cells_value) else int(min_cells_value)
        n_cells_control = None if pd.isna(control_value) else int(control_value)
        eligible_targets = int(row["n_eligible_targets"])
        ineligible_targets = int(row["n_ineligible_targets"])

    umi_present = bool(umi_summary["umi_depth_column_present"])
    cells_ok = (
        min_cells_perturbed is not None
        and n_cells_control is not None
        and eligible_targets > 0
        and min_cells_perturbed >= min_cells_per_group
        and n_cells_control >= min_cells_per_group
    )
    if not cells_ok:
        return "hold", "cells per perturbation / control 未达到当前 support floor。", {
            "min_cells_perturbed": min_cells_perturbed,
            "n_cells_control": n_cells_control,
            "n_eligible_targets": eligible_targets,
            "n_ineligible_targets": ineligible_targets,
        }
    if require_umi_depth_column and not umi_present:
        return "hold", "缺少可追踪的 UMI depth 列。", {
            "min_cells_perturbed": min_cells_perturbed,
            "n_cells_control": n_cells_control,
            "n_eligible_targets": eligible_targets,
            "n_ineligible_targets": ineligible_targets,
        }
    return "pass", "support floor 已显式绑定 cells per perturbation / control，并追踪 UMI depth。", {
        "min_cells_perturbed": min_cells_perturbed,
        "n_cells_control": n_cells_control,
        "n_eligible_targets": eligible_targets,
        "n_ineligible_targets": ineligible_targets,
    }


def main() -> None:
    governance = load_governance()
    eligibility = load_eligibility_frame()
    eligibility_summary = build_eligibility_summary(eligibility)
    rows: list[dict[str, object]] = []

    for contract in load_formal_dataset_contracts(include_auxiliary=True):
        audit = load_audit_summary(contract.dataset_id)
        filter_report = load_filter_report(contract.dataset_id)
        source_dataset = get_source_dataset(contract.dataset_id)
        umi_summary = read_umi_depth_summary(source_dataset.path)

        control = audit["selected_control"]
        single = audit["single_perturbation_filterability"]
        target = audit["gene_level_target_cleaning"]
        moi_state, moi_note = moi_status(audit)
        barcode_state, barcode_note = barcode_assignment_status(audit)
        level_state, level_value, level_note = processed_raw_level_status(
            source_dataset.path
        )
        support_state, support_note, support_metrics = support_floor_status(
            contract.dataset_id,
            eligibility_summary,
            umi_summary,
            min_cells_per_group=int(governance["min_cells_per_group"]),
            require_umi_depth_column=bool(governance["require_umi_depth_column"]),
        )

        metadata_blocking = any(
            status == "hold"
            for status in [
                control["status"],
                single["status"],
                target["status"],
                support_state,
                level_state,
            ]
        )
        if metadata_blocking:
            admission_decision = "hold"
        elif contract.default_in_mainline:
            admission_decision = "pass"
        else:
            admission_decision = "supplement_pass"

        rows.append(
            {
                "dataset_id": contract.dataset_id,
                "role": contract.role,
                "default_in_mainline": contract.default_in_mainline,
                "registry_status": contract.status,
                "formal_filter_status": filter_report.get("final_status", "missing"),
                "support_floor_status": support_state,
                "support_floor_note": support_note,
                "min_cells_perturbed": support_metrics["min_cells_perturbed"],
                "n_cells_control": support_metrics["n_cells_control"],
                "n_eligible_targets": support_metrics["n_eligible_targets"],
                "n_ineligible_targets": support_metrics["n_ineligible_targets"],
                "umi_depth_column": umi_summary["umi_depth_column"],
                "umi_depth_column_present": umi_summary["umi_depth_column_present"],
                "umi_depth_median_all": umi_summary["umi_depth_median_all"],
                "umi_depth_median_control": umi_summary["umi_depth_median_control"],
                "umi_depth_median_perturbed": umi_summary["umi_depth_median_perturbed"],
                "umi_depth_p10_all": umi_summary["umi_depth_p10_all"],
                "umi_depth_p90_all": umi_summary["umi_depth_p90_all"],
                "control_definition_status": control["status"],
                "control_definition_note": control["note"],
                "single_vs_multi_target_status": single["status"],
                "single_vs_multi_target_note": single["note"],
                "moi_audit_status": moi_state,
                "moi_audit_note": moi_note,
                "barcode_assignment_status": barcode_state,
                "barcode_assignment_note": barcode_note,
                "processed_raw_level_status": level_state,
                "processed_raw_level_value": level_value,
                "processed_raw_level_note": level_note,
                "target_mapping_status": target["status"],
                "target_mapping_note": target["note"],
                "admission_decision": admission_decision,
                "admission_note": (
                    "可进入 formal mainline。"
                    if admission_decision == "pass"
                    else "可作为 supplement 数据集保留。"
                    if admission_decision == "supplement_pass"
                    else "关键 admission 维度未闭合。"
                ),
            }
        )

    frame = pd.DataFrame(rows).sort_values(["default_in_mainline", "dataset_id"], ascending=[False, True])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(TSV_PATH, sep="\t", index=False)
    JSON_PATH.write_text(
        json.dumps(frame.to_dict(orient="records"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    metadata = {
        "manifest_id": "stage1a_admission_manifest",
        "snapshot_status": "historical_snapshot_pending_migration",
        "status_note": (
            "该 admission manifest 属于旧 formal/admission 链路快照；其中 dataset_id 可能仍保留旧命名体系，"
            "当前 formal + supplement 数据集治理应以 dataset_tiering.md、admission_matrix.tsv 与 "
            "configs/stage1a/dataset_governance.json 为准。"
        ),
        "migration_policy": "pending_migration_to_current_dataset_naming",
        "authoritative_current_sources": [
            "dataset_tiering.md",
            "admission_matrix.tsv",
            "configs/stage1a/dataset_governance.json",
        ],
    }
    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    README_PATH.write_text(
        "\n".join(
            [
                "# admission 目录说明",
                "",
                "- `stage1a_admission_manifest.tsv/json` 是旧 formal/admission 链路生成的历史快照。",
                "- 当前这些文件仍可用于回溯旧运行，但不应直接当作现行 `formal + supplement` 命名体系的唯一准据。",
                "- 当前数据集治理与命名口径以 `dataset_tiering.md`、`admission_matrix.tsv`、`configs/stage1a/dataset_governance.json` 为准。",
                "- 若要彻底消除歧义，应后续把该 manifest 迁移到新命名体系，而不是继续模糊并存。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"已写出: {TSV_PATH}")
    print(f"已写出: {JSON_PATH}")
    print(f"已写出: {METADATA_PATH}")
    print(f"已写出: {README_PATH}")
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
