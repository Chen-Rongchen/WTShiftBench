from __future__ import annotations

import json
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

from stage1a_catalog import PROJECT_ROOT, load_formal_dataset_contracts
from stage1a_split_plan_b import filter_eligible_to_heldout, load_split_governance


FROZEN_ELIGIBLE_TARGETS_PATH = PROJECT_ROOT / "data/frozen/stage1a_formal/eligible_targets.tsv"
TRUTH_OUTPUT_ROOT = PROJECT_ROOT / "data/truth/stage1a_pseudobulk_delta"
REPORT_OUTPUT_ROOT = PROJECT_ROOT / "reports/stage1a/truth_building"
ELIGIBLE_TARGET_COLUMNS = [
    "dataset_id",
    "target_gene",
    "n_cells_perturbed",
    "n_cells_control",
    "eligible_for_pseudobulk",
]
SUMMARY_COLUMNS = [
    "dataset_id",
    "n_targets_expected",
    "n_targets_built",
    "n_cells_control",
    "n_genes",
    "control_definition",
    "matrix_source",
    "log_normalization_applied_in_truth_build",
    "delta_space",
    "source_h5ad",
    "control_in_dataset_verified",
    "row_count_matches_expected",
    "contains_only_eligible_targets",
    "split_scheme",
    "split_seed",
    "n_eligible_targets_pre_split",
]


def build_delta_space_label(
    matrix_source: str,
    log_normalization_applied_in_truth_build: bool,
) -> str:
    if log_normalization_applied_in_truth_build:
        return "log_normalized_pseudobulk_delta"
    return f"{matrix_source}_pseudobulk_delta"


def get_expression_matrix(adata) -> tuple[object, str]:
    return adata.X, "X"


def assert_replogle_control_consistency(dataset_id: str, obs: pd.DataFrame) -> None:
    if not dataset_id.startswith("replogle_2022_"):
        return
    required_cols = ["perturbation", "gene", "is_control", "target_gene"]
    missing = [c for c in required_cols if c not in obs.columns]
    if missing:
        raise ValueError(f"{dataset_id} 缺少 Replogle control 一致性断言所需字段: {missing}")

    perturbation = stringify(obs["perturbation"])
    gene = stringify(obs["gene"])
    perturbation_is_control = perturbation.eq("control").fillna(False).astype(bool)
    gene_is_non_targeting = gene.eq("non-targeting").fillna(False).astype(bool)
    is_control = obs["is_control"].astype("boolean").fillna(False).astype(bool)

    mismatch_pg = perturbation_is_control.ne(gene_is_non_targeting)
    if mismatch_pg.any():
        mismatch = obs.loc[
            mismatch_pg,
            ["dataset_id", "target_gene", "perturbation", "gene", "is_control"],
        ].head(10)
        raise ValueError(
            f"{dataset_id} 中 perturbation=='control' 与 gene=='non-targeting' 不完全对应: "
            f"{mismatch.to_dict(orient='records')}"
        )

    mismatch_pc = perturbation_is_control.ne(is_control)
    if mismatch_pc.any():
        mismatch = obs.loc[
            mismatch_pc,
            ["dataset_id", "target_gene", "perturbation", "gene", "is_control"],
        ].head(10)
        raise ValueError(
            f"{dataset_id} 中 perturbation=='control' 与 is_control 不完全对应: "
            f"{mismatch.to_dict(orient='records')}"
        )


def stringify(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("")


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_pass_contracts() -> list:
    return [
        contract
        for contract in load_formal_dataset_contracts(include_auxiliary=True)
        if contract.status in {"pass"}
    ]


def load_frozen_eligible_targets() -> pd.DataFrame:
    eligible = pd.read_csv(FROZEN_ELIGIBLE_TARGETS_PATH, sep="\t")
    missing_columns = set(ELIGIBLE_TARGET_COLUMNS) - set(eligible.columns)
    if missing_columns:
        raise ValueError(f"frozen eligible targets 缺少列: {sorted(missing_columns)}")

    eligible["eligible_for_pseudobulk"] = (
        eligible["eligible_for_pseudobulk"].astype("string").str.lower().eq("true")
    )
    eligible = eligible.loc[eligible["eligible_for_pseudobulk"], ELIGIBLE_TARGET_COLUMNS].copy()
    eligible["dataset_id"] = stringify(eligible["dataset_id"])
    eligible["target_gene"] = stringify(eligible["target_gene"])
    eligible["n_cells_perturbed"] = pd.to_numeric(
        eligible["n_cells_perturbed"], errors="raise"
    ).astype(int)
    eligible["n_cells_control"] = pd.to_numeric(
        eligible["n_cells_control"], errors="raise"
    ).astype(int)
    return eligible.sort_values(["dataset_id", "target_gene"]).reset_index(drop=True)


def mean_expression(matrix) -> np.ndarray:
    if matrix.shape[0] == 0:
        raise ValueError("pseudobulk 聚合时收到空细胞集合。")
    if sparse.issparse(matrix):
        values = np.asarray(matrix.mean(axis=0)).ravel()
    else:
        values = np.asarray(matrix.mean(axis=0)).ravel()
    return values.astype(np.float64, copy=False)


def build_dataset_truth(
    contract,
    eligible_targets: pd.DataFrame,
    split_seed: int,
) -> dict[str, object]:
    dataset_id = contract.dataset_id
    dataset_output_dir = TRUTH_OUTPUT_ROOT / dataset_id
    dataset_report_dir = REPORT_OUTPUT_ROOT / dataset_id
    dataset_output_dir.mkdir(parents=True, exist_ok=True)
    dataset_report_dir.mkdir(parents=True, exist_ok=True)

    adata = ad.read_h5ad(contract.path)
    try:
        obs_columns = ["dataset_id", "is_control", "target_gene", "perturbation", "gene"]
        available_obs_columns = [column for column in obs_columns if column in adata.obs.columns]
        obs = adata.obs.loc[:, available_obs_columns].copy()
        obs["dataset_id"] = stringify(obs["dataset_id"])
        obs["target_gene"] = stringify(obs["target_gene"])
        obs["is_control"] = obs["is_control"].astype(bool)
        if "perturbation" in obs.columns:
            obs["perturbation"] = stringify(obs["perturbation"])
        if "gene" in obs.columns:
            obs["gene"] = stringify(obs["gene"])

        gene_symbols = pd.Index(adata.var.index.astype(str), name="gene_symbol")
        control_mask = obs["is_control"].to_numpy()
        expression_matrix, matrix_source = get_expression_matrix(adata)
        log_normalization_applied_in_truth_build = False
        delta_space = build_delta_space_label(
            matrix_source=matrix_source,
            log_normalization_applied_in_truth_build=log_normalization_applied_in_truth_build,
        )

        if not np.all(obs["dataset_id"].eq(dataset_id)):
            raise ValueError(f"{dataset_id} 的 obs.dataset_id 存在跨数据集记录。")
        if contract.control_definition != "in-dataset control baseline":
            raise ValueError(
                f"{dataset_id} 的 control_definition 非约定值: {contract.control_definition}"
            )
        if control_mask.sum() == 0:
            raise ValueError(f"{dataset_id} 不存在 in-dataset controls。")
        assert_replogle_control_consistency(dataset_id=dataset_id, obs=obs)

        eligible_before = eligible_targets.loc[
            eligible_targets["dataset_id"].eq(dataset_id)
        ].copy()
        n_eligible_pre = len(eligible_before)
        eligible_subset = filter_eligible_to_heldout(eligible_targets, dataset_id, split_seed)
        eligible_target_genes = eligible_subset["target_gene"].tolist()
        eligible_target_set = set(eligible_target_genes)

        observed_perturbed_targets = set(obs.loc[~obs["is_control"], "target_gene"])
        if eligible_target_set - observed_perturbed_targets:
            missing_targets = sorted(eligible_target_set - observed_perturbed_targets)
            raise ValueError(f"{dataset_id} 缺少 frozen eligible target: {missing_targets[:10]}")

        control_values = mean_expression(expression_matrix[control_mask])
        control_frame = pd.DataFrame([control_values], index=["control"], columns=gene_symbols)

        perturbed_rows: list[np.ndarray] = []
        delta_rows: list[np.ndarray] = []
        metadata_rows: list[dict[str, object]] = []

        control_cells = int(control_mask.sum())

        for row in eligible_subset.itertuples(index=False):
            target_mask = (~obs["is_control"]).to_numpy() & obs["target_gene"].eq(row.target_gene).to_numpy()
            perturbed_cells = int(target_mask.sum())
            if perturbed_cells == 0:
                raise ValueError(f"{dataset_id}::{row.target_gene} 没有 perturbed cells。")

            perturbed_values = mean_expression(expression_matrix[target_mask])
            delta_values = perturbed_values - control_values

            perturbed_rows.append(perturbed_values)
            delta_rows.append(delta_values)
            metadata_rows.append(
                {
                    "dataset_id": dataset_id,
                    "target_gene": row.target_gene,
                    "n_cells_perturbed": perturbed_cells,
                    "n_cells_control": control_cells,
                    "eligible_for_pseudobulk": True,
                }
            )

        perturbed_frame = pd.DataFrame(
            perturbed_rows,
            index=eligible_target_genes,
            columns=gene_symbols,
        )
        perturbed_frame.index.name = "target_gene"

        delta_frame = pd.DataFrame(
            delta_rows,
            index=eligible_target_genes,
            columns=gene_symbols,
        )
        delta_frame.index.name = "target_gene"

        metadata_frame = pd.DataFrame(metadata_rows).sort_values(
            ["dataset_id", "target_gene"]
        ).reset_index(drop=True)

        built_targets = set(delta_frame.index.astype(str))
        full_eligible_set = set(eligible_before["target_gene"].astype("string"))
        contains_only_eligible_targets = built_targets <= full_eligible_set
        row_count_matches_expected = len(delta_frame) == len(eligible_subset)

        if not contains_only_eligible_targets:
            raise ValueError(f"{dataset_id} 输出包含 ineligible targets。")
        if not row_count_matches_expected:
            raise ValueError(
                f"{dataset_id} delta 行数与 eligible target 数不一致: "
                f"{len(delta_frame)} != {len(eligible_subset)}"
            )

        perturbed_path = dataset_output_dir / "perturbed_pseudobulk.tsv.gz"
        control_path = dataset_output_dir / "control_pseudobulk.tsv.gz"
        delta_path = dataset_output_dir / "pseudobulk_delta.tsv.gz"
        metadata_path = dataset_output_dir / "target_metadata.tsv"
        summary_path = dataset_report_dir / "truth_summary.json"

        perturbed_frame.to_csv(perturbed_path, sep="\t", compression="gzip")
        control_frame.to_csv(control_path, sep="\t", compression="gzip")
        delta_frame.to_csv(delta_path, sep="\t", compression="gzip")
        metadata_frame.to_csv(metadata_path, sep="\t", index=False)

        gov = load_split_governance()
        summary = {
            "dataset_id": dataset_id,
            "n_targets_expected": int(len(eligible_subset)),
            "n_targets_built": int(len(delta_frame)),
            "n_cells_control": control_cells,
            "n_genes": int(adata.n_vars),
            "control_definition": contract.control_definition,
            "matrix_source": matrix_source,
            "log_normalization_applied_in_truth_build": log_normalization_applied_in_truth_build,
            "delta_space": delta_space,
            "source_h5ad": str(contract.path),
            "control_in_dataset_verified": True,
            "row_count_matches_expected": row_count_matches_expected,
            "contains_only_eligible_targets": contains_only_eligible_targets,
            "split_scheme": str(gov.get("split_scheme", "B")),
            "split_seed": int(split_seed),
            "n_eligible_targets_pre_split": int(n_eligible_pre),
            "output_files": {
                "perturbed_pseudobulk": str(perturbed_path),
                "control_pseudobulk": str(control_path),
                "pseudobulk_delta": str(delta_path),
                "target_metadata": str(metadata_path),
            },
        }
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"已写出: {perturbed_path}")
        print(f"已写出: {control_path}")
        print(f"已写出: {delta_path}")
        print(f"已写出: {metadata_path}")
        print(f"已写出: {summary_path}")
        return summary
    finally:
        del adata


def main() -> None:
    TRUTH_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    eligible_targets = load_frozen_eligible_targets()
    gov = load_split_governance()
    split_seed = int(gov["default_split_seed_for_truth_freeze"])
    contracts = load_pass_contracts()
    summaries = [
        build_dataset_truth(
            contract=contract,
            eligible_targets=eligible_targets,
            split_seed=split_seed,
        )
        for contract in contracts
    ]

    combined_summary = pd.DataFrame(summaries)
    if combined_summary.empty:
        combined_summary = pd.DataFrame(columns=SUMMARY_COLUMNS)
    else:
        combined_summary = combined_summary.loc[:, SUMMARY_COLUMNS].sort_values(
            "dataset_id"
        ).reset_index(drop=True)

    combined_summary_path = REPORT_OUTPUT_ROOT / "combined_truth_summary.tsv"
    combined_summary.to_csv(combined_summary_path, sep="\t", index=False)
    print(f"已写出: {combined_summary_path}")
    print(combined_summary.to_string(index=False))


if __name__ == "__main__":
    main()
