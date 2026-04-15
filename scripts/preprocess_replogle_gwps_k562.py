#!/usr/bin/env python3
"""
Preprocess Replogle 2022 K562 GWPS h5ad for stage2_truth_bridge pipeline.

Adds:
- is_control: True for nperts==0, False otherwise
- num_features: renamed from nperts
- target_gene: copied from gene

This makes the h5ad compatible with load_expression_from_h5ad() pipeline.
"""
from __future__ import annotations

import anndata as ad
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data/raw/stage1a/candidates/replogle_2022_k562_gwps.h5ad"
OUTPUT_PATH = PROJECT_ROOT / "data/processed/stage2_replogle_gwps_k562/replogle_2022_k562_gwps_processed.h5ad"


def preprocess_gwps(in_path: Path, out_path: Path) -> None:
    print(f"Loading {in_path} ...")
    adata = ad.read_h5ad(in_path)

    # is_control: nperts==0 are controls
    adata.obs["is_control"] = adata.obs["nperts"] == 0

    # num_features: renamed from nperts (pipeline checks num_features == 1)
    adata.obs["num_features"] = adata.obs["nperts"].astype(int)

    # target_gene: pipeline reads target_gene from obs
    adata.obs["target_gene"] = adata.obs["gene"].copy()

    print(f"  Total cells: {adata.n_obs}")
    print(f"  Control cells (nperts==0): {adata.obs['is_control'].sum()}")
    print(f"  Single-perturbation cells (nperts==1): {(adata.obs['nperts'] == 1).sum()}")
    print(f"  Multi-perturbation cells (nperts>1): {(adata.obs['nperts'] > 1).sum()}")
    print(f"  Unique target genes: {adata.obs['gene'].nunique()}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing to {out_path} ...")
    adata.write_h5ad(out_path)
    print("Done.")


if __name__ == "__main__":
    preprocess_gwps(INPUT_PATH, OUTPUT_PATH)
