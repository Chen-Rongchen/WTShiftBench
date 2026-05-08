#!/usr/bin/env python3
"""Build `edfig1_target_gene_expression_arrows.tsv` for Extended Data Fig. 1 panels g–k.

Each row: context, target, expression_control, expression_perturbed (target gene,
log-normalized mean expression in control vs perturbed cells). Matches manuscript /
Extended Data Fig. 1 legend (arrow base = control, tip = perturbed).

Requires processed AnnData objects on disk (same layout as legacy dataset-familiarization export).

Usage (from repo root):
    python scripts/manuscript/build_edfig1_target_gene_expression_source.py
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from wtbench.manuscript.figure_io import ensure_dir, repo_root, write_tsv


ROOT = repo_root()

HCC38_PATH = ROOT / "data/processed/hcc_gears_formal/HCC38.h5ad"
HCC1143_PATH = ROOT / "data/processed/hcc_gears_formal/HCC1143.h5ad"
K562_7D_PATH = ROOT / "data/processed/gse90063/dixit_2016_k562_tf_7d_gse90063.h5ad"
K562_13D_PATH = ROOT / "data/processed/gse90063/dixit_2016_k562_tf_13d_gse90063.h5ad"
REPLOGLE_PATH = ROOT / "data/processed/replogle_k562_essential/essential_processed.h5ad"

OUT_TSV = ROOT / "reports/manuscript_extended_data_v1/edfig1_dataset_familiarization/edfig1_target_gene_expression_arrows.tsv"

MIN_PERTURBED_CELLS = 20
MIN_CONTROL_CELLS = 50


def load_and_verify_hcc(path: Path):
    import anndata as ad

    adata = ad.read_h5ad(path)
    sample = adata.X[:1000].toarray() if sparse.issparse(adata.X) else adata.X[:1000]
    assert sample.max() < 20, f"HCC not log-normalized: max={sample.max():.2f}"
    return adata


def load_and_verify_k562(path: Path):
    import anndata as ad

    adata = ad.read_h5ad(path)
    sample = adata.X[:1000].toarray() if sparse.issparse(adata.X) else adata.X[:1000]
    assert sample.max() > 100, f"K562 not raw counts: max={sample.max():.2f}"
    return adata


def load_replogle_normalized(path: Path):
    """Replogle ``essential_processed`` keeps raw counts (see ``preprocess_replogle_k562_essential.py``).

    Apply the same ``normalize_total(target_sum=1e4)`` + ``log1p`` as Dixit K562 arrow panels so panel k
    shares scale with g–j. Uses global ``X.max()`` (not a row subsample) so we never mis-detect dense peaks.
    """
    import anndata as ad
    import scanpy as sc

    adata = ad.read_h5ad(path)
    X = adata.X
    mx = float(X.max()) if sparse.issparse(X) else float(np.asarray(X).max())
    # Raw Perturb-seq counts are ≫30; already-lognorm matrices sit far lower (cf. HCC formal h5ad).
    if mx > 30:
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)
    return adata


def target_gene_expression_means(adata, target: str) -> tuple[float, float]:
    """Mean target-gene expression (log-normalized space): control, perturbed."""
    obs = adata.obs
    control_mask = obs["is_control"].astype(bool).to_numpy()
    target_mask_np = ((~obs["is_control"].astype(bool)) & obs["target_gene"].eq(target)).to_numpy()

    if not target_mask_np.any():
        return np.nan, np.nan

    X = adata.X
    if sparse.issparse(X):
        ctrl_mean = np.asarray(X[control_mask].mean(axis=0)).ravel()
        pert_mean = np.asarray(X[target_mask_np].mean(axis=0)).ravel()
    else:
        ctrl_mean = np.asarray(X[control_mask].mean(axis=0)).ravel()
        pert_mean = np.asarray(X[target_mask_np].mean(axis=0)).ravel()

    gene_idx = None
    if target in adata.var_names:
        gene_idx = adata.var_names.get_loc(target)
    else:
        for i, v in enumerate(adata.var_names):
            if v.endswith(f"_{target}") or v == target:
                gene_idx = i
                break

    if gene_idx is None:
        return np.nan, np.nan
    return float(ctrl_mean[gene_idx]), float(pert_mean[gene_idx])


def rows_for_context(context_name: str, adata) -> list[dict]:
    obs = adata.obs
    ctrl_n = int(obs["is_control"].astype(bool).sum())
    if ctrl_n < MIN_CONTROL_CELLS:
        return []

    all_targets = sorted(obs.loc[~obs["is_control"].astype(bool), "target_gene"].dropna().unique())
    rows = []
    for t in all_targets:
        tgt_mask = ((~obs["is_control"].astype(bool)) & obs["target_gene"].eq(t)).to_numpy()
        if int(tgt_mask.sum()) < MIN_PERTURBED_CELLS:
            continue
        xc, xp = target_gene_expression_means(adata, t)
        if np.isnan(xc) or np.isnan(xp):
            continue
        rows.append(
            {
                "context": context_name,
                "target": t,
                "expression_control": xc,
                "expression_perturbed": xp,
            }
        )
    return rows


def main() -> None:
    import scanpy as sc

    print("[edfig1] Loading AnnData objects …")
    hcc38 = load_and_verify_hcc(HCC38_PATH)
    hcc1143 = load_and_verify_hcc(HCC1143_PATH)
    k562_7d = load_and_verify_k562(K562_7D_PATH)
    k562_13d = load_and_verify_k562(K562_13D_PATH)

    genes_7d = set(k562_7d.var_names)
    genes_13d = set(k562_13d.var_names)
    genes_intersection = sorted(genes_7d & genes_13d)
    k562_7d_sub = k562_7d[:, genes_intersection].copy()
    k562_13d_sub = k562_13d[:, genes_intersection].copy()
    sc.pp.normalize_total(k562_7d_sub, target_sum=1e4)
    sc.pp.log1p(k562_7d_sub)
    sc.pp.normalize_total(k562_13d_sub, target_sum=1e4)
    sc.pp.log1p(k562_13d_sub)

    records: list[dict] = []
    records.extend(rows_for_context("HCC38", hcc38))
    records.extend(rows_for_context("HCC1143", hcc1143))
    records.extend(rows_for_context("K562 7d", k562_7d_sub))
    records.extend(rows_for_context("K562 13d", k562_13d_sub))

    if REPLOGLE_PATH.exists():
        replogle = load_replogle_normalized(REPLOGLE_PATH)
        records.extend(rows_for_context("Replogle K562 essential", replogle))
    else:
        print(f"[edfig1] WARNING: skip Replogle ({REPLOGLE_PATH} missing)")

    df = pd.DataFrame.from_records(records)
    ensure_dir(OUT_TSV.parent)
    write_tsv(df, OUT_TSV)
    print(f"[edfig1] Wrote {len(df)} rows → {OUT_TSV}")


if __name__ == "__main__":
    main()
