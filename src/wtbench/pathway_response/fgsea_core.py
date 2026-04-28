"""
DEPRECATED: Lightweight Python implementation of pre-ranked GSEA (fgsea).

As of 2026-04-27 this module is no longer the production fgsea engine.
`run_pathway_response.py` now delegates fgsea computation to R Bioconductor
`fgsea` (Korotkevich et al., Nat Methods 2021) via `run_fgsea.R`. The R
implementation provides:
  - adaptive multilevel permutation (precision down to ~1e-50 pvals)
  - bit-identical reproducibility under fixed `set.seed()`
  - peer-reviewed NES normalization

This file is kept only for historical reference. Do not call `prerank_fgsea`
from new code; importing it will emit a DeprecationWarning.

Based on Subramanian et al. 2005 PNAS and Korotkevich et al. 2021 Nature Methods.
Uses numba for accelerated permutation testing.

Weighted ES: uses absolute ranking values as weights for hits,
consistent with standard pre-ranked GSEA.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from numba import njit, prange

warnings.warn(
    "wtbench.pathway_response.fgsea_core is deprecated; "
    "fgsea is now run via R Bioconductor through run_fgsea.R. "
    "Do not use prerank_fgsea in new code.",
    DeprecationWarning,
    stacklevel=2,
)


@njit
def _compute_es_weighted(is_hit: np.ndarray, rank_weights: np.ndarray, n_hits: int, N: int) -> float:
    """Compute weighted enrichment score."""
    if n_hits == 0 or n_hits == N:
        return 0.0

    # Sum of absolute rank weights for hits
    hit_weight_sum = 0.0
    for i in range(N):
        if is_hit[i]:
            hit_weight_sum += rank_weights[i]

    if hit_weight_sum == 0.0:
        return 0.0

    miss_weight = 1.0 / (N - n_hits)

    hit_cumsum = 0.0
    miss_cumsum = 0.0
    max_dev = 0.0
    min_dev = 0.0

    for i in range(N):
        if is_hit[i]:
            hit_cumsum += rank_weights[i] / hit_weight_sum
        else:
            miss_cumsum += miss_weight
        running = hit_cumsum - miss_cumsum
        if running > max_dev:
            max_dev = running
        if running < min_dev:
            min_dev = running

    if abs(max_dev) >= abs(min_dev):
        return max_dev
    return min_dev


@njit(parallel=True)
def _compute_null_es_weighted_parallel(
    n_hits: int,
    rank_weights: np.ndarray,
    N: int,
    n_perm: int,
    seed: int,
) -> np.ndarray:
    """Compute null ES distribution with weighted hits, parallelized."""
    np.random.seed(seed)
    null_es = np.zeros(n_perm, dtype=np.float64)

    for p in prange(n_perm):
        hit_positions = np.random.choice(N, size=n_hits, replace=False)
        is_hit = np.zeros(N, dtype=np.bool_)
        is_hit[hit_positions] = True
        null_es[p] = _compute_es_weighted(is_hit, rank_weights, n_hits, N)

    return null_es


def _bh_fdr(pvals: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg FDR correction."""
    m = len(pvals)
    if m == 0:
        return pvals.copy()
    order = np.argsort(pvals)
    sorted_pvals = pvals[order]
    padj = np.zeros(m)
    for i in range(m - 1, -1, -1):
        raw = sorted_pvals[i] * m / (i + 1)
        if i == m - 1:
            padj[order[i]] = raw
        else:
            padj[order[i]] = min(raw, padj[order[i + 1]])
    return padj


def prerank_fgsea(
    ranking: pd.Series,
    gene_sets: dict[str, list[str]],
    *,
    min_size: int = 10,
    max_size: int = 500,
    n_perm: int = 200,
    seed: int = 0,
) -> pd.DataFrame:
    """
    Run pre-ranked GSEA on a single ranked gene list.

    Parameters
    ----------
    ranking : pd.Series
        Gene-level ranking scores, index = gene symbols.
        Genes are ranked by descending score.
    gene_sets : dict
        Mapping from pathway name to list of gene symbols.
    min_size, max_size : int
        Filter gene sets by size after intersecting with ranking genes.
    n_perm : int
        Number of permutations for null distribution.
    seed : int
        Random seed.

    Returns
    -------
    pd.DataFrame with columns: pathway, ES, NES, pval, padj, direction,
    n_genes_in_set, n_genes_after_intersection
    """
    all_genes = set(ranking.index)
    N = len(ranking)
    ranked_genes = ranking.index.to_numpy()
    gene_to_rank = {g: i for i, g in enumerate(ranked_genes)}

    # Absolute rank weights (consistent with standard pre-ranked GSEA)
    rank_weights = np.abs(ranking.to_numpy())

    # Filter gene sets
    filtered_sets = {}
    for name, genes in gene_sets.items():
        intersection = [g for g in genes if g in all_genes]
        n_after = len(intersection)
        if min_size <= n_after <= max_size:
            filtered_sets[name] = {
                "genes": intersection,
                "n_after": n_after,
            }

    if not filtered_sets:
        return pd.DataFrame(
            columns=[
                "pathway",
                "ES",
                "NES",
                "pval",
                "padj",
                "direction",
                "n_genes_in_set",
                "n_genes_after_intersection",
            ]
        )

    results = []

    for name, info in filtered_sets.items():
        genes = info["genes"]
        n_after = info["n_after"]
        n_raw = len(gene_sets[name])

        # Build hit indicator for actual ES
        is_hit = np.zeros(N, dtype=np.bool_)
        for g in genes:
            is_hit[gene_to_rank[g]] = True

        es = _compute_es_weighted(is_hit, rank_weights, n_after, N)

        # Compute null distribution
        pathway_seed = int(seed + abs(hash(name)) % 10000)
        null_es = _compute_null_es_weighted_parallel(n_after, rank_weights, N, n_perm, pathway_seed)

        # Compute p-value and NES
        # NES normalization: use mean(|null ES|) to preserve ES sign
        abs_null = np.abs(null_es)
        mean_abs_null = abs_null.mean() if len(abs_null) > 0 else 1e-10

        if es >= 0:
            pval = max((null_es >= es).sum() / n_perm, 1.0 / n_perm)
            pos_null = null_es[null_es >= 0]
            denom = pos_null.mean() if len(pos_null) > 0 else mean_abs_null
            nes = es / max(denom, 1e-10)
        else:
            pval = max((null_es <= es).sum() / n_perm, 1.0 / n_perm)
            neg_null = null_es[null_es <= 0]
            denom = abs(neg_null.mean()) if len(neg_null) > 0 else mean_abs_null
            nes = es / max(denom, 1e-10)

        direction = "up" if es > 0 else "down" if es < 0 else "neutral"

        results.append(
            {
                "pathway": name,
                "ES": float(es),
                "NES": float(nes),
                "pval": float(pval),
                "direction": direction,
                "n_genes_in_set": n_raw,
                "n_genes_after_intersection": n_after,
            }
        )

    df = pd.DataFrame(results)
    if not df.empty:
        df["padj"] = _bh_fdr(df["pval"].to_numpy())
    return df


def load_gmt(path: str) -> dict[str, list[str]]:
    """Load GMT file into dict."""
    gene_sets = {}
    with open(path) as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue
            name = parts[0]
            # parts[1] is description URL, skip
            genes = [g.strip() for g in parts[2:] if g.strip()]
            gene_sets[name] = genes
    return gene_sets
