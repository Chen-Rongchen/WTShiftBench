#!/usr/bin/env python3
"""
Preprocess Frangieh 2021 (melanoma + TIL co-culture) h5ad for stage2_truth_bridge pipeline.

Key mapping:
- sgRNA: "GENENAME_N" -> extract gene name via rsplit('_', 1)[0]
- condition == "Control" -> is_control = True
- num_features: MOI (multiplicity of infection)
- target_gene: extracted gene symbol from sgRNA

Note: This dataset has NO DepMap endpoint. It can only serve as
exploratory / tumor-immune complex boundary test, not formal bridge.
"""
from __future__ import annotations

import anndata as ad
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data/raw/stage1a/candidates/dixit_2016_raw.h5ad"
OUTPUT_DIR = PROJECT_ROOT / "data/processed/stage2_frangieh_2021_melanoma"
OUTPUT_PATH = OUTPUT_DIR / "frangieh_2021_processed.h5ad"


def extract_gene(sgRNA: str) -> str:
    """Extract gene symbol from sgRNA name like 'IFNGR2_2' -> 'IFNGR2'."""
    parts = str(sgRNA).rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0]
    return str(sgRNA)


def preprocess(in_path: Path, out_path: Path) -> None:
    print(f"Loading {in_path} ...")
    adata = ad.read_h5ad(in_path)

    # is_control: condition == "Control"
    adata.obs["is_control"] = adata.obs["condition"] == "Control"

    # num_features: MOI as integer
    adata.obs["num_features"] = adata.obs["MOI"].astype(int)

    # target_gene: extracted from sgRNA
    adata.obs["target_gene"] = adata.obs["sgRNA"].apply(extract_gene)

    # Summarize
    print(f"  Total cells: {adata.n_obs}")
    print(f"  Conditions: {adata.obs['condition'].value_counts().to_dict()}")
    print(f"  MOI range: {adata.obs['MOI'].astype(int).min()} - {adata.obs['MOI'].astype(int).max()}")
    print(f"  Unique sgRNAs: {adata.obs['sgRNA'].nunique()}")
    print(f"  Unique extracted genes: {adata.obs['target_gene'].nunique()}")
    print(f"  Control cells: {adata.obs['is_control'].sum()}")
    print(f"  Single-perturbation cells (MOI=1, non-control): {((adata.obs['num_features'] == 1) & (~adata.obs['is_control'])).sum()}")
    print(f"  Multi-perturbation cells (MOI>1): {(adata.obs['num_features'] > 1).sum()}")

    # Gene-level summary
    gene_counts = adata.obs.groupby("target_gene").size()
    print(f"  Gene-level: {len(gene_counts)} unique genes, median cells/gene: {gene_counts.median():.0f}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing to {out_path} ...")
    adata.write_h5ad(out_path)
    print("Done.")


if __name__ == "__main__":
    preprocess(INPUT_PATH, OUTPUT_PATH)
