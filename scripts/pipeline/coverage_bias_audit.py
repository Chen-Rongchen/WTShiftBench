#!/usr/bin/env python3
"""
Stage 2 Coverage Bias Audit — Dixit

Purpose: Assess whether DepMap-uncovered targets in Dixit constitute a structurally distinct subset.
Output: audit tables + truth-metric distribution comparison (non-parametric)

Run: pixi run python scripts/pipeline/coverage_bias_audit.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import mannwhitneyu, ks_2samp

# ── paths ──────────────────────────────────────────────────────────────────
BRIDGE_TABLE = Path("data/processed/truth_driven_bridge/combined_target_level_bridge_table.tsv.gz")
DEPMap_EFFECT = Path("depmap/CRISPRGeneEffect.csv")
DEPMap_DEP    = Path("depmap/CRISPRGeneDependency.csv")
OUT_DIR       = Path("reports/truth_driven_bridge/coverage_bias_audit")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRUTH_METRICS = ["real_shift_L2", "real_shift_mean_abs", "real_Edistance", "real_DEG_burden"]

# ── gene-category heuristics ───────────────────────────────────────────────
def rough_category(gene: str) -> str:
    g = gene.upper()
    suffixes_noncode = ("-AS1", "-IT1", "-IT2", "-DT", "LINC", "SNHG", "NEAT", "MALAT",
                        "HOTAIR", "HOTTIP", "PURPL", "NKX2-2AS")
    prefixes_mito   = ("MT-", "ATP", "COX", "NDU", "CYTB", "UQCR", "TIMM50", "TOMM")
    prefixes_ribo   = ("RPS", "RPL", "RPSA")
    if any(g.endswith(s) for s in suffixes_noncode):
        return "lncRNA / antisense"
    if g.startswith("HLA-"):
        return "HLA / immune"
    if any(g.startswith(p) for p in prefixes_mito):
        return "mitochondrial / oxidative phosphorylation"
    if any(g.startswith(p) for p in prefixes_ribo):
        return "ribosomal"
    if "BOLA" in g or "GAR1" in g or "NOP10" in g or "NHP2L1" in g:
        return "ribonucleoprotein / snoRNP"
    return "protein-coding"


# ── load DepMap to determine "not in panel" ────────────────────────────────
def load_depmap_cols(path: Path) -> set:
    df = pd.read_csv(path, index_col=0)
    cols_clean = []
    for c in df.columns:
        if " (" in c and c.endswith(")"):
            cols_clean.append(c.split(" (")[0])
        else:
            cols_clean.append(c)
    return set(cols_clean)


# ── main ───────────────────────────────────────────────────────────────────
def main():
    print("Loading bridge table …")
    df = pd.read_csv(BRIDGE_TABLE, sep="\t")

    dixit = df[df["cell_line"] == "dixit_2016_raw__control_context"].copy()
    dixit_id = dixit["depmap_model_id"].iloc[0]

    # load DepMap gene universe
    depmap_cols = load_depmap_cols(DEPMap_EFFECT)
    # also load per-cell values for Dixit to distinguish "gene exists vs cell NaN"
    dep_eff = pd.read_csv(DEPMap_EFFECT, index_col=0)
    dep_dep = pd.read_csv(DEPMap_DEP,    index_col=0)
    for _df in [dep_eff, dep_dep]:
        _df.columns = [c.split(" (")[0] if " (" in c and c.endswith(")") else c
                       for c in _df.columns]

    in_panel   = set(dep_eff.columns) & set(dep_dep.columns)
    dixit_eff  = dep_eff.loc[dixit_id]  if dixit_id in dep_eff.index  else pd.Series(dtype=float)
    dixit_dep  = dep_dep.loc[dixit_id]  if dixit_id in dep_dep.index  else pd.Series(dtype=float)

    # ── A. unmatched audit table ───────────────────────────────────────────
    unmatched = dixit[dixit["depmap_join_status"] != "both"].copy()
    rows = []
    for _, r in unmatched.iterrows():
        gene = r["target_gene"]
        if gene not in in_panel:
            reason = "not_in_depmap_panel"
        else:
            eff_val = dixit_eff.get(gene, np.nan)  if gene in dixit_eff.index  else np.nan
            dep_val = dixit_dep.get(gene, np.nan)  if gene in dixit_dep.index  else np.nan
            reason = "gene_exists_cellNaN" if (pd.isna(eff_val) and pd.isna(dep_val)) else "unknown"
        rows.append({
            "target_gene": gene,
            "reason": reason,
            "rough_category": rough_category(gene),
            "real_shift_L2": r["real_shift_L2"],
            "real_shift_mean_abs": r["real_shift_mean_abs"],
            "real_Edistance": r["real_Edistance"],
            "real_DEG_burden": r["real_DEG_burden"],
            "n_cells_target": r["n_cells_target"],
        })
    audit_a = pd.DataFrame(rows)
    audit_a.to_csv(OUT_DIR / "dixit_unmatched_audit.tsv", sep="\t", index=False)
    print(f"A. Unmatched audit: {len(audit_a)} rows → {OUT_DIR / 'dixit_unmatched_audit.tsv'}")

    # ── B. category distribution ────────────────────────────────────────────
    matched   = dixit[dixit["depmap_join_status"] == "both"]
    cat_rows  = []
    for cat in audit_a["rough_category"].unique():
        cat_rows.append({"category": cat, "unmatched_n": int((audit_a["rough_category"] == cat).sum())})
    # add matched total (all matched are protein-coding by construction here)
    matched_cats = matched["target_gene"].apply(rough_category).value_counts().reset_index()
    matched_cats.columns = ["category", "matched_n"]
    cat_df = pd.DataFrame(cat_rows).merge(matched_cats, on="category", how="outer").fillna(0)
    cat_df["unmatched_n"] = cat_df["unmatched_n"].astype(int)
    cat_df["matched_n"]    = cat_df["matched_n"].astype(int)
    cat_df["total"]       = cat_df["matched_n"] + cat_df["unmatched_n"]
    cat_df["unmatched_pct"] = cat_df["unmatched_n"] / cat_df["total"]
    cat_df = cat_df.sort_values("unmatched_n", ascending=False).reset_index(drop=True)
    cat_df.to_csv(OUT_DIR / "dixit_category_distribution.tsv", sep="\t", index=False)
    print(f"B. Category distribution → {OUT_DIR / 'dixit_category_distribution.tsv'}")

    # ── C. truth metric distribution comparison ─────────────────────────────
    m_vals = {m: matched[m].dropna().values   for m in TRUTH_METRICS}
    u_vals = {m: audit_a[m].dropna().values   for m in TRUTH_METRICS}

    mw_rows, ks_rows = [], []
    for m in TRUTH_METRICS:
        m_ok = m_vals[m].size > 0
        u_ok = u_vals[m].size > 0

        med_matched   = float(np.median(m_vals[m]))   if m_ok else np.nan
        med_unmatched = float(np.median(u_vals[m]))   if u_ok else np.nan
        iqr_matched   = np.percentile(m_vals[m], [25, 75]).tolist() if m_ok else [np.nan, np.nan]
        iqr_unmatched = np.percentile(u_vals[m], [25, 75]).tolist() if u_ok else [np.nan, np.nan]

        mw_stat, mw_p = (mannwhitneyu(m_vals[m], u_vals[m], alternative="two-sided")
                          if m_ok and u_ok and len(m_vals[m]) > 0 and len(u_vals[m]) > 0
                          else (np.nan, np.nan))
        ks_stat, ks_p  = (ks_2samp(m_vals[m], u_vals[m])
                          if m_ok and u_ok and len(m_vals[m]) > 0 and len(u_vals[m]) > 0
                          else (np.nan, np.nan))

        # Cliff's delta (rank-biserial)
        def cliffs_delta(x, y):
            nx, ny = len(x), len(y)
            more = sum(a > b for a in x for b in y)
            less = sum(a < b for a in x for b in y)
            return (more - less) / (nx * ny) if nx * ny > 0 else np.nan

        cd = cliffs_delta(m_vals[m], u_vals[m]) if m_ok and u_ok else np.nan

        mw_rows.append({
            "metric": m,
            "n_matched": len(m_vals[m]),
            "n_unmatched": len(u_vals[m]),
            "median_matched": med_matched,
            "median_unmatched": med_unmatched,
            "iqr_matched_lo": iqr_matched[0] if isinstance(iqr_matched, (list, np.ndarray)) else np.nan,
            "iqr_matched_hi": iqr_matched[1] if isinstance(iqr_matched, (list, np.ndarray)) else np.nan,
            "iqr_unmatched_lo": iqr_unmatched[0] if isinstance(iqr_unmatched, (list, np.ndarray)) else np.nan,
            "iqr_unmatched_hi": iqr_unmatched[1] if isinstance(iqr_unmatched, (list, np.ndarray)) else np.nan,
            "mannwhitney_u": mw_stat,
            "mannwhitney_p": mw_p,
            "cliffs_delta": cd,
        })
        ks_rows.append({
            "metric": m,
            "ks_statistic": ks_stat,
            "ks_pvalue": ks_p,
            "interpretation": (
                "distributions similar" if (not np.isnan(ks_stat) and ks_stat < 0.1)
                else ("distributions differ" if (not np.isnan(ks_stat) and ks_stat > 0.1) else "insufficient data")
            ),
        })

    dist_mw = pd.DataFrame(mw_rows)
    dist_ks = pd.DataFrame(ks_rows)
    dist_mw.to_csv(OUT_DIR / "dixit_truth_metric_mannwhitney.tsv", sep="\t", index=False)
    dist_ks.to_csv(OUT_DIR / "dixit_truth_metric_ks.tsv",           sep="\t", index=False)
    print(f"C. Mann-Whitney → {OUT_DIR / 'dixit_truth_metric_mannwhitney.tsv'}")
    print(f"C. KS test      → {OUT_DIR / 'dixit_truth_metric_ks.tsv'}")

    # ── print summary ──────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("COVERAGE BIAS AUDIT SUMMARY — Dixit")
    print("="*70)
    print(f"\nDixit total targets:    {len(dixit)}")
    print(f"Matched (both):          {len(matched)}")
    print(f"Unmatched (none):        {len(audit_a)}")
    print(f"  - not_in_panel:        {(audit_a['reason']=='not_in_depmap_panel').sum()}")
    print(f"  - gene_exists_cellNaN: {(audit_a['reason']=='gene_exists_cellNaN').sum()}")
    print(f"\nUnmatched by category:")
    for _, r in cat_df.iterrows():
        print(f"  {r['category']:45s}  n={r['unmatched_n']:3d}  ({r['unmatched_pct']:.1%} of total in category)")
    print("\nTruth metric comparison (Mann-Whitney + Cliff's delta):")
    for _, r in dist_mw.iterrows():
        print(f"  {r['metric']:25s}  Δ median={r['median_unmatched']-r['median_matched']:+.4f}"
              f"  cliffs δ={r['cliffs_delta']:+.3f}  MW p={r['mannwhitney_p']:.4f}")
    print("\nAll outputs written to:", OUT_DIR)


if __name__ == "__main__":
    main()
