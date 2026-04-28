"""
Pathway-response exploratory layer: compute per-target gene rankings and run fgsea.

fgsea computation is delegated to R Bioconductor `fgsea` (Korotkevich et al.,
Nat Methods 2021) via `run_fgsea.R`. The previous in-tree Python implementation
(`fgsea_core.prerank_fgsea`) is retained only as a deprecated fallback and is
no longer invoked by this entrypoint.

Usage:
    python run_pathway_response.py --context HCC38 --h5ad data/processed/stage2_hcc_gears_formal/HCC38.h5ad \
        --output-dir reports/pathway_response
    python run_pathway_response.py --context K562_7d --h5ad data/processed/stage2_gse90063/dixit_2016_k562_tf_7d_gse90063.h5ad \
        --output-dir reports/pathway_response --k562-preprocess
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import anndata as ad
from scipy import sparse

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# R fgsea wrapper script lives next to this file
R_FGSEA_SCRIPT = Path(__file__).resolve().parent / "run_fgsea.R"
DEFAULT_RSCRIPT_BIN = "/opt/R/4.3.2/bin/Rscript"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pathway-response exploratory layer")
    parser.add_argument("--context", required=True, help="Context label (e.g. HCC38, HCC1143, K562_7d, K562_13d)")
    parser.add_argument("--h5ad", required=True, help="Path to h5ad file")
    parser.add_argument("--output-dir", default="reports/pathway_response", help="Output directory")
    parser.add_argument("--gmt", default="resources/msigdb/h.all.symbols.gmt", help="Path to Hallmark GMT file")
    parser.add_argument("--k562-preprocess", action="store_true", help="Apply K562 preprocessing (normalize_total + log1p)")
    parser.add_argument("--gene-filter", action="store_true", help="Apply detection fraction filter (>= 0.05)")
    parser.add_argument("--min-target-cells", type=int, default=20)
    parser.add_argument("--min-control-cells", type=int, default=50)
    parser.add_argument("--rscript-bin", default=DEFAULT_RSCRIPT_BIN,
                        help=f"Rscript binary used to run fgsea (default {DEFAULT_RSCRIPT_BIN})")
    parser.add_argument("--eps", type=float, default=1e-10,
                        help="fgsea multilevel boundary; smaller -> higher precision (default 1e-10)")
    parser.add_argument("--n-perm-simple", type=int, default=10000,
                        help="Initial permutation count for fgsea multilevel pre-test (default 10000)")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_and_prepare_h5ad(h5ad_path: str, k562_preprocess: bool) -> tuple[sparse.csr_matrix, pd.DataFrame, pd.DataFrame]:
    """Load h5ad and return expression matrix (log-normalized), obs, var."""
    adata = ad.read_h5ad(h5ad_path)
    obs = adata.obs.copy()
    var = adata.var.copy()

    if sparse.issparse(adata.X):
        X = adata.X.tocsr()
    else:
        X = sparse.csr_matrix(np.asarray(adata.X))

    if k562_preprocess:
        # Raw counts: normalize to 1e4 total, then log1p
        import scanpy as sc
        adata_raw = ad.AnnData(X=X, obs=obs, var=var)
        sc.pp.normalize_total(adata_raw, target_sum=1e4)
        sc.pp.log1p(adata_raw)
        if sparse.issparse(adata_raw.X):
            X = adata_raw.X.tocsr()
        else:
            X = sparse.csr_matrix(np.asarray(adata_raw.X))

    # Ensure gene symbols are clean
    if "gene_name" in var.columns:
        var.index = var["gene_name"].astype(str)
    elif var.index.name is None or var.index.name == "":
        # Try to infer from index
        pass

    return X, obs, var


def extract_gene_symbols(var: pd.DataFrame, k562_mode: bool) -> list[str]:
    """Extract HUGO gene symbols from var."""
    if k562_mode:
        # K562 format: ENSG..._GENE_SYMBOL
        symbols = []
        for name in var.index.astype(str):
            if "_" in name:
                parts = name.split("_")
                # Take everything after the first underscore
                symbol = "_".join(parts[1:])
                symbols.append(symbol)
            else:
                symbols.append(name)
        return symbols
    else:
        return var.index.astype(str).tolist()


def compute_gene_ranking(
    X: sparse.csr_matrix,
    obs: pd.DataFrame,
    target_gene: str,
    gene_symbols: list[str],
    gene_filter: bool,
) -> pd.Series | None:
    """Compute signed mean difference ranking for a target."""
    # Get perturbed and control cell indices
    perturbed_mask = (~obs["is_control"].astype(bool)) & (obs["target_gene"].astype(str) == target_gene)
    control_mask = obs["is_control"].astype(bool)

    n_perturbed = int(perturbed_mask.sum())
    n_control = int(control_mask.sum())

    if n_perturbed == 0:
        return None

    perturbed_idx = np.flatnonzero(perturbed_mask.to_numpy())
    control_idx = np.flatnonzero(control_mask.to_numpy())

    # Compute mean expression
    perturbed_mean = np.asarray(X[perturbed_idx].mean(axis=0)).ravel()
    control_mean = np.asarray(X[control_idx].mean(axis=0)).ravel()

    # Ranking: mean_log_expr_perturbed - mean_log_expr_matched_control
    ranking = perturbed_mean - control_mean

    # Optional gene filter: detection fraction >= 0.05 in perturbed OR control
    if gene_filter:
        perturbed_X = X[perturbed_idx]
        control_X = X[control_idx]
        perturbed_detect = np.asarray((perturbed_X > 0).mean(axis=0)).ravel()
        control_detect = np.asarray((control_X > 0).mean(axis=0)).ravel()
        keep = (perturbed_detect >= 0.05) | (control_detect >= 0.05)
        ranking = ranking[keep]
        kept_symbols = [g for g, k in zip(gene_symbols, keep) if k]
    else:
        kept_symbols = gene_symbols

    # Create Series, sorted descending by absolute value (for display) but preserve sign
    rank_series = pd.Series(ranking, index=kept_symbols)
    # Sort by value descending (positive = upregulated in perturbed)
    rank_series = rank_series.sort_values(ascending=False)
    return rank_series


def _run_fgsea_via_r(
    ranking: pd.Series,
    gmt_path: str,
    *,
    rscript_bin: str,
    eps: float,
    n_perm_simple: int,
    seed: int,
    min_size: int = 10,
    max_size: int = 500,
) -> pd.DataFrame:
    """Run fgsea by writing the ranking to a temp TSV and invoking run_fgsea.R.

    Returns a DataFrame with the legacy schema:
        pathway, ES, NES, pval, direction,
        n_genes_in_set, n_genes_after_intersection, padj, log2err, leading_edge

    Compared to the previous in-tree Python implementation this delegates the
    actual statistical computation to R Bioconductor `fgsea`. Reproducibility
    is guaranteed by `set.seed(seed)` inside the R wrapper; identical inputs
    yield bit-identical outputs.
    """
    if not Path(rscript_bin).exists() and shutil.which(rscript_bin) is None:
        raise FileNotFoundError(
            f"Rscript binary not found: {rscript_bin}. Pass --rscript-bin to override."
        )
    if not R_FGSEA_SCRIPT.exists():
        raise FileNotFoundError(f"R fgsea wrapper missing: {R_FGSEA_SCRIPT}")

    with tempfile.TemporaryDirectory(prefix="fgsea_") as tmpdir:
        tmp_in = Path(tmpdir) / "ranking.tsv"
        tmp_out = Path(tmpdir) / "fgsea_out.tsv"

        # ranking written as gene\tscore (header required, R wrapper sorts internally)
        ranking.rename_axis("gene").reset_index(name="score").to_csv(
            tmp_in, sep="\t", index=False
        )

        cmd = [
            rscript_bin,
            str(R_FGSEA_SCRIPT),
            "--ranking-tsv", str(tmp_in),
            "--gmt", str(gmt_path),
            "--output-tsv", str(tmp_out),
            "--min-size", str(min_size),
            "--max-size", str(max_size),
            "--eps", str(eps),
            "--n-perm-simple", str(n_perm_simple),
            "--seed", str(seed),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout)
            sys.stderr.write(proc.stderr)
            raise RuntimeError(
                f"R fgsea wrapper failed (exit {proc.returncode}). Cmd: {' '.join(cmd)}"
            )

        if not tmp_out.exists():
            raise RuntimeError("R fgsea wrapper completed but output TSV not found")

        result = pd.read_csv(tmp_out, sep="\t")

    if result.empty:
        return result

    # Adapt R schema to the legacy column names consumed by select_display.py
    # and draw_heatmap.py: rename `size` -> `n_genes_after_intersection`.
    result = result.rename(columns={"size": "n_genes_after_intersection"})

    # Reorder columns to match the existing TSV layout
    cols = [
        "pathway", "ES", "NES", "pval", "direction",
        "n_genes_in_set", "n_genes_after_intersection",
        "padj", "log2err", "leading_edge",
    ]
    return result[[c for c in cols if c in result.columns]]


def run_pathway_response_for_context(
    context: str,
    h5ad_path: str,
    output_dir: str,
    gmt_path: str,
    k562_preprocess: bool,
    gene_filter: bool,
    min_target_cells: int,
    min_control_cells: int,
    rscript_bin: str,
    eps: float,
    n_perm_simple: int,
    seed: int,
) -> None:
    """Main execution function for a single context."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    qc_path = output_path / "qc"
    qc_path.mkdir(parents=True, exist_ok=True)

    print(f"[{context}] fgsea engine: R Bioconductor fgsea via {rscript_bin}")
    print(f"[{context}] GMT: {gmt_path}")

    # Load expression data
    X, obs, var = load_and_prepare_h5ad(h5ad_path, k562_preprocess)
    gene_symbols = extract_gene_symbols(var, k562_mode=k562_preprocess)
    print(f"[{context}] Expression matrix shape: {X.shape}")
    print(f"[{context}] Preprocessing: {'K562 (normalize_total + log1p)' if k562_preprocess else 'HCC (pre-log-normalized)'}")

    # Get eligible targets
    targets = sorted(obs.loc[~obs["is_control"].astype(bool), "target_gene"].astype(str).unique())
    print(f"[{context}] Found {len(targets)} targets")

    # Target inclusion QC
    qc_records = []
    fgsea_results = []
    ranking_provenance = []

    for target in targets:
        perturbed_mask = (~obs["is_control"].astype(bool)) & (obs["target_gene"].astype(str) == target)
        control_mask = obs["is_control"].astype(bool)
        n_perturbed = int(perturbed_mask.sum())
        n_control = int(control_mask.sum())

        included = True
        exclusion_reason = ""
        if n_perturbed < min_target_cells:
            included = False
            exclusion_reason = f"n_perturbed={n_perturbed} < {min_target_cells}"
        elif n_control < min_control_cells:
            included = False
            exclusion_reason = f"n_control={n_control} < {min_control_cells}"

        qc_records.append({
            "context": context,
            "target": target,
            "n_perturbed": n_perturbed,
            "n_control": n_control,
            "included": included,
            "exclusion_reason": exclusion_reason,
        })

        if not included:
            print(f"[{context}] Skipping {target}: {exclusion_reason}")
            continue

        # Compute ranking
        ranking = compute_gene_ranking(X, obs, target, gene_symbols, gene_filter)
        if ranking is None or len(ranking) == 0:
            print(f"[{context}] Skipping {target}: empty ranking")
            continue

        ranking_provenance.append({
            "context": context,
            "target": target,
            "n_genes_total": len(gene_symbols),
            "n_genes_after_filter": len(ranking),
            "gene_filter_applied": gene_filter,
            "max_rank": float(ranking.iloc[0]),
            "min_rank": float(ranking.iloc[-1]),
        })

        # Run fgsea via R Bioconductor wrapper
        result = _run_fgsea_via_r(
            ranking,
            gmt_path=gmt_path,
            rscript_bin=rscript_bin,
            eps=eps,
            n_perm_simple=n_perm_simple,
            seed=seed,
            min_size=10,
            max_size=500,
        )

        if result.empty:
            print(f"[{context}] {target}: no gene sets passed size filter")
            continue

        result["context"] = context
        result["target"] = target
        result["n_perturbed"] = n_perturbed
        result["n_control"] = n_control
        result["n_genes_ranked"] = len(ranking)
        result["ranking_method"] = "mean_log_expr_perturbed_minus_control"
        result["gene_filter"] = gene_filter
        result["msigdb_collection"] = "H"
        fgsea_results.append(result)

        print(f"[{context}] {target}: n_perturbed={n_perturbed}, n_control={n_control}, "
              f"n_pathways={len(result)}, sig_pathways={(result['padj'] < 0.10).sum()}")

    # Save outputs
    qc_df = pd.DataFrame(qc_records)
    qc_df.to_csv(output_path / f"target_inclusion_qc_{context}.tsv", sep="\t", index=False)
    print(f"[{context}] Saved QC: {len(qc_df)} targets, {qc_df['included'].sum()} included")

    if ranking_provenance:
        prov_df = pd.DataFrame(ranking_provenance)
        prov_df.to_csv(qc_path / f"ranking_provenance_{context}.tsv", sep="\t", index=False)

    if fgsea_results:
        fgsea_df = pd.concat(fgsea_results, ignore_index=True)
        fgsea_df.to_csv(output_path / f"fgsea_hallmark_{context}.tsv", sep="\t", index=False)
        print(f"[{context}] Saved fgsea results: {len(fgsea_df)} rows")
    else:
        print(f"[{context}] WARNING: No fgsea results generated")

    # Save provenance
    provenance = {
        "context": context,
        "h5ad_path": str(h5ad_path),
        "gmt_path": str(gmt_path),
        "k562_preprocess": k562_preprocess,
        "gene_filter": gene_filter,
        "min_target_cells": min_target_cells,
        "min_control_cells": min_control_cells,
        "fgsea_engine": "R Bioconductor fgsea (Korotkevich 2021)",
        "rscript_bin": rscript_bin,
        "eps": eps,
        "n_perm_simple": n_perm_simple,
        "seed": seed,
        "n_targets_total": len(targets),
        "n_targets_included": int(qc_df["included"].sum()),
        "expression_matrix_shape": list(X.shape),
    }
    with open(qc_path / f"provenance_{context}.json", "w") as f:
        json.dump(provenance, f, indent=2)

    print(f"[{context}] Done.")


if __name__ == "__main__":
    args = parse_args()
    run_pathway_response_for_context(
        context=args.context,
        h5ad_path=args.h5ad,
        output_dir=args.output_dir,
        gmt_path=args.gmt,
        k562_preprocess=args.k562_preprocess,
        gene_filter=args.gene_filter,
        min_target_cells=args.min_target_cells,
        min_control_cells=args.min_control_cells,
        rscript_bin=args.rscript_bin,
        eps=args.eps,
        n_perm_simple=args.n_perm_simple,
        seed=args.seed,
    )
