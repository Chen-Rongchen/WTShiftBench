from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from stage1a_catalog import PROJECT_ROOT, load_formal_dataset_contracts
from stage1a_split_plan_b import expected_heldout_counts_by_dataset, load_split_governance

FROZEN_TRUTH_DIR = PROJECT_ROOT / "data/frozen/stage1a_truth"
TRUTH_FREEZE_REPORT_DIR = PROJECT_ROOT / "reports/stage1a/truth_freeze"
ELIGIBLE_TARGETS_PATH = PROJECT_ROOT / "data/frozen/stage1a_formal/eligible_targets.tsv"
COMBINED_TRUTH_SUMMARY_PATH = (
    PROJECT_ROOT / "reports/stage1a/truth_building/combined_truth_summary.tsv"
)
TRUTH_OUTPUT_ROOT = PROJECT_ROOT / "data/truth/stage1a_pseudobulk_delta"
TRUTH_REGISTRY_COLUMNS = [
    "dataset_id",
    "truth_path",
    "n_targets_expected",
    "n_targets_built",
    "n_genes",
    "control_definition",
    "freeze_status",
    "matrix_source",
    "log_normalization_applied_in_truth_build",
    "delta_space",
]


def resolve_project_relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def load_pass_contract_frame() -> pd.DataFrame:
    rows = [
        {
            "dataset_id": contract.dataset_id,
            "control_definition": contract.control_definition,
            "status": contract.status,
        }
        for contract in load_formal_dataset_contracts(include_auxiliary=True)
        if contract.status in {"pass", "auxiliary_pass"}
    ]
    if not rows:
        return pd.DataFrame(columns=["dataset_id", "control_definition", "status"])
    return pd.DataFrame(rows).sort_values("dataset_id").reset_index(drop=True)


def load_plan_b_eval_target_counts() -> pd.DataFrame:
    """与 truth 构建一致：方案 B 下 default_split_seed 的 held-out 目标数。"""
    gov = load_split_governance()
    seed = int(gov["default_split_seed_for_truth_freeze"])
    return expected_heldout_counts_by_dataset(split_seed=seed)[["dataset_id", "n_targets_expected_eval"]]


def load_combined_truth_summary() -> pd.DataFrame:
    summary = pd.read_csv(COMBINED_TRUTH_SUMMARY_PATH, sep="\t")
    required_columns = [
        "dataset_id",
        "n_targets_expected",
        "n_targets_built",
        "n_genes",
        "control_definition",
        "matrix_source",
        "log_normalization_applied_in_truth_build",
        "delta_space",
        "row_count_matches_expected",
        "contains_only_eligible_targets",
        "split_scheme",
        "split_seed",
        "n_eligible_targets_pre_split",
    ]
    missing_columns = sorted(set(required_columns) - set(summary.columns))
    if missing_columns:
        raise ValueError(f"combined_truth_summary.tsv 缺少列: {missing_columns}")

    summary = summary.loc[:, required_columns].copy()
    summary["dataset_id"] = summary["dataset_id"].astype("string")
    summary["control_definition"] = summary["control_definition"].astype("string")
    summary["matrix_source"] = summary["matrix_source"].astype("string")
    summary["log_normalization_applied_in_truth_build"] = (
        summary["log_normalization_applied_in_truth_build"]
        .astype("string")
        .str.lower()
        .eq("true")
    )
    summary["delta_space"] = summary["delta_space"].astype("string")
    for column in ["row_count_matches_expected", "contains_only_eligible_targets"]:
        summary[column] = summary[column].astype("string").str.lower().eq("true")
    for column in ["n_targets_expected", "n_targets_built", "n_genes"]:
        summary[column] = pd.to_numeric(summary[column], errors="raise").astype(int)
    return summary.sort_values("dataset_id").reset_index(drop=True)


def assert_dataset_sets_match(
    pass_contracts: pd.DataFrame,
    summary: pd.DataFrame,
    eval_counts: pd.DataFrame,
) -> None:
    pass_ids = set(pass_contracts["dataset_id"].tolist())
    summary_ids = set(summary["dataset_id"].tolist())
    eval_ids = set(eval_counts["dataset_id"].tolist())

    mismatches: list[str] = []
    if pass_ids != summary_ids:
        mismatches.append(
            "pass_contracts vs combined_truth_summary 不一致: "
            f"仅在 pass_contracts={sorted(pass_ids - summary_ids)}, "
            f"仅在 combined_truth_summary={sorted(summary_ids - pass_ids)}"
        )
    if pass_ids != eval_ids:
        mismatches.append(
            "pass_contracts vs plan_b eval_counts 不一致: "
            f"仅在 pass_contracts={sorted(pass_ids - eval_ids)}, "
            f"仅在 eval_counts={sorted(eval_ids - pass_ids)}"
        )
    if mismatches:
        raise ValueError("; ".join(mismatches))


def build_truth_registry() -> pd.DataFrame:
    pass_contracts = load_pass_contract_frame()
    eval_counts = load_plan_b_eval_target_counts()
    summary = load_combined_truth_summary()
    assert_dataset_sets_match(
        pass_contracts=pass_contracts,
        summary=summary,
        eval_counts=eval_counts,
    )

    registry = pass_contracts.merge(summary, on=["dataset_id", "control_definition"], how="inner")
    merged_dataset_ids = set(registry["dataset_id"].tolist())
    expected_dataset_ids = set(pass_contracts["dataset_id"].tolist())
    if merged_dataset_ids != expected_dataset_ids:
        missing_after_merge = sorted(expected_dataset_ids - merged_dataset_ids)
        unexpected_after_merge = sorted(merged_dataset_ids - expected_dataset_ids)
        raise ValueError(
            "pass_contracts 与 combined_truth_summary 合并后 dataset 集合发生变化: "
            f"missing_after_merge={missing_after_merge}, "
            f"unexpected_after_merge={unexpected_after_merge}"
        )
    registry = registry.merge(eval_counts, on="dataset_id", how="left")
    registry["n_targets_expected_eval"] = (
        pd.to_numeric(registry["n_targets_expected_eval"], errors="coerce")
        .fillna(0)
        .astype(int)
    )
    pre_filter_dataset_ids = set(registry["dataset_id"].tolist())
    registry = registry.loc[
        registry["row_count_matches_expected"] & registry["contains_only_eligible_targets"]
    ].copy()
    post_filter_dataset_ids = set(registry["dataset_id"].tolist())
    if post_filter_dataset_ids != pre_filter_dataset_ids:
        dropped_dataset_ids = sorted(pre_filter_dataset_ids - post_filter_dataset_ids)
        raise ValueError(
            "truth registry 过滤后 dataset 数减少，formal 冻结不允许静默退出: "
            f"dropped_dataset_ids={dropped_dataset_ids}"
        )

    if registry.empty:
        raise ValueError("truth registry 为空，无法冻结 formal truth。")

    mismatched_expected = registry.loc[
        registry["n_targets_expected"] != registry["n_targets_expected_eval"],
        ["dataset_id", "n_targets_expected", "n_targets_expected_eval"],
    ]
    if not mismatched_expected.empty:
        raise ValueError(
            "truth summary 与方案 B held-out 预期 target 数不一致: "
            f"{mismatched_expected.to_dict(orient='records')}"
        )

    registry["truth_path"] = registry["dataset_id"].map(
        lambda dataset_id: resolve_project_relative(
            TRUTH_OUTPUT_ROOT / str(dataset_id) / "pseudobulk_delta.tsv.gz"
        )
    )
    missing_truth_paths = [
        truth_path
        for truth_path in registry["truth_path"].tolist()
        if not (PROJECT_ROOT / truth_path).exists()
    ]
    if missing_truth_paths:
        raise FileNotFoundError(f"缺少 truth 文件: {missing_truth_paths}")

    registry["freeze_status"] = "frozen"
    registry = registry.loc[:, TRUTH_REGISTRY_COLUMNS].copy()
    return registry.sort_values("dataset_id").reset_index(drop=True)


def build_truth_manifest(truth_registry: pd.DataFrame) -> dict[str, object]:
    datasets = truth_registry.to_dict(orient="records")
    return {
        "stage": "stage1a_truth",
        "truth_type": "stage1a_pseudobulk_delta",
        "freeze_status": "frozen",
        "source_inputs": {
            "formal_datasets_yaml": resolve_project_relative(
                PROJECT_ROOT / "configs/stage1a_formal_datasets.yaml"
            ),
            "eligible_targets_tsv": resolve_project_relative(ELIGIBLE_TARGETS_PATH),
            "split_governance_yaml": resolve_project_relative(
                PROJECT_ROOT / "configs/stage1a_split_governance.yaml"
            ),
            "truth_root": resolve_project_relative(TRUTH_OUTPUT_ROOT),
            "combined_truth_summary_tsv": resolve_project_relative(COMBINED_TRUTH_SUMMARY_PATH),
        },
        "truth_build_normalization": {
            "matrix_source": "frozen_per_dataset_in_registry",
            "log_normalization_applied_in_truth_build": False,
            "delta_space": "frozen_per_dataset_in_registry",
        },
        "n_datasets": int(len(datasets)),
        "datasets": datasets,
    }


def main() -> None:
    FROZEN_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    TRUTH_FREEZE_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    truth_registry = build_truth_registry()
    truth_registry_path = FROZEN_TRUTH_DIR / "truth_registry.tsv"
    truth_manifest_path = TRUTH_FREEZE_REPORT_DIR / "truth_manifest.json"

    truth_registry.to_csv(truth_registry_path, sep="\t", index=False)
    truth_manifest = build_truth_manifest(truth_registry=truth_registry)
    truth_manifest_path.write_text(
        json.dumps(truth_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"已写出: {truth_registry_path}")
    print(f"已写出: {truth_manifest_path}")
    if not truth_registry.empty:
        print(truth_registry.to_string(index=False))


if __name__ == "__main__":
    main()
