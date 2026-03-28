from __future__ import annotations

from pathlib import Path

import anndata as ad
import pandas as pd
import yaml

from stage1a_catalog import PROJECT_ROOT, load_formal_dataset_contracts

GOVERNANCE_PATH = PROJECT_ROOT / "configs/stage1a_split_governance.yaml"


def load_min_cells_per_group() -> int:
    if not GOVERNANCE_PATH.exists():
        return 5
    data = yaml.safe_load(GOVERNANCE_PATH.read_text(encoding="utf-8")) or {}
    return int(data.get("min_cells_per_group", 5))


MIN_CELLS_PER_GROUP = load_min_cells_per_group()
OUTPUT_ROOT = PROJECT_ROOT / "reports/stage1a/pseudobulk_eligibility"
OUTPUT_COLUMNS = [
    "dataset_id",
    "target_gene",
    "n_cells_perturbed",
    "n_cells_control",
    "eligible_for_pseudobulk",
    "eligible_reason",
]


def stringify(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("")


def build_eligibility_reason(
    n_cells_perturbed: int,
    n_cells_control: int,
    min_cells_per_group: int = MIN_CELLS_PER_GROUP,
) -> tuple[bool, str]:
    perturbed_ok = n_cells_perturbed >= min_cells_per_group
    control_ok = n_cells_control >= min_cells_per_group

    if perturbed_ok and control_ok:
        return True, (
            f"pass: perturbed>={min_cells_per_group} 且 "
            f"control>={min_cells_per_group}"
        )
    if not perturbed_ok and not control_ok:
        return False, (
            f"fail: perturbed<{min_cells_per_group} 且 "
            f"control<{min_cells_per_group}"
        )
    if not perturbed_ok:
        return False, f"fail: perturbed<{min_cells_per_group}"
    return False, f"fail: control<{min_cells_per_group}"


def build_dataset_eligibility(dataset_id: str, dataset_path: Path) -> pd.DataFrame:
    adata = ad.read_h5ad(dataset_path, backed="r")
    try:
        obs = adata.obs.loc[:, ["is_control", "target_gene"]].copy()
    finally:
        adata.file.close()

    is_control = obs["is_control"].astype(bool)
    target_gene = stringify(obs["target_gene"])
    n_cells_control = int(is_control.sum())

    perturbed_counts = (
        target_gene.loc[~is_control]
        .loc[lambda series: series.ne("")]
        .value_counts()
        .rename_axis("target_gene")
        .reset_index(name="n_cells_perturbed")
        .sort_values(["n_cells_perturbed", "target_gene"], ascending=[False, True])
        .reset_index(drop=True)
    )

    if perturbed_counts.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    eligibility = perturbed_counts.assign(
        dataset_id=dataset_id,
        n_cells_control=n_cells_control,
    )

    flags_and_reasons = eligibility.apply(
        lambda row: build_eligibility_reason(
            n_cells_perturbed=int(row["n_cells_perturbed"]),
            n_cells_control=int(row["n_cells_control"]),
        ),
        axis=1,
        result_type="expand",
    )
    flags_and_reasons.columns = ["eligible_for_pseudobulk", "eligible_reason"]
    eligibility = pd.concat([eligibility, flags_and_reasons], axis=1)

    return eligibility.loc[:, OUTPUT_COLUMNS].sort_values(
        ["dataset_id", "eligible_for_pseudobulk", "n_cells_perturbed", "target_gene"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)


def write_dataset_eligibility(dataset_id: str, eligibility: pd.DataFrame) -> Path:
    output_dir = OUTPUT_ROOT / dataset_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "perturbation_eligibility.tsv"
    eligibility.to_csv(output_path, sep="\t", index=False)
    return output_path


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    combined_rows: list[pd.DataFrame] = []
    contracts = [
        contract
        for contract in load_formal_dataset_contracts()
        if contract.status == "pass"
    ]

    for contract in contracts:
        eligibility = build_dataset_eligibility(
            dataset_id=contract.dataset_id,
            dataset_path=contract.path,
        )
        output_path = write_dataset_eligibility(contract.dataset_id, eligibility)
        combined_rows.append(eligibility)
        print(f"已写出: {output_path}")
        print(eligibility.head(5).to_string(index=False))
        print()

    combined = (
        pd.concat(combined_rows, ignore_index=True)
        if combined_rows
        else pd.DataFrame(columns=OUTPUT_COLUMNS)
    )
    combined = combined.sort_values(
        ["dataset_id", "eligible_for_pseudobulk", "n_cells_perturbed", "target_gene"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)

    combined_path = OUTPUT_ROOT / "combined_eligibility.tsv"
    combined.to_csv(combined_path, sep="\t", index=False)
    print(f"已写出: {combined_path}")
    print(combined.groupby(["dataset_id", "eligible_for_pseudobulk"]).size().to_string())


if __name__ == "__main__":
    main()
