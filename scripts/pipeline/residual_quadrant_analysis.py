#!/usr/bin/env python3
"""
Stage 2 — Shift vs DepMap Effect: Scatter + Residual + Quadrant Analysis

Primary axis: real_shift_mean_abs (y)  vs  aligned depmap_gene_effect (x)
Secondary (consistency check): dependency

Run: pixi run python scripts/pipeline/residual_quadrant_analysis.py
"""

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from pathlib import Path
import json

# ── paths ──────────────────────────────────────────────────────────────────
BRIDGE_TABLE = Path("data/processed/truth_driven_bridge/combined_target_level_bridge_table.tsv.gz")
OUT_DIR       = Path("reports/truth_driven_bridge/residual_quadrant_analysis")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRUTH_METRICS = ["real_shift_L2", "real_shift_mean_abs", "real_Edistance", "real_DEG_burden"]
ALIGNED_EFFECT_COL  = "depmap_gene_effect"   # higher → more negative → stronger dependency
ALIGNED_DEP_COL     = "depmap_gene_dependency"

# primary metrics for main analysis
PRIMARY_Y = "real_shift_mean_abs"
PRIMARY_X = "depmap_gene_effect"

QUADRANT_PCTS = [0.25, 0.75]  # low/high cutoffs on x and y


def load_data():
    return pd.read_csv(BRIDGE_TABLE, sep="\t")


def fit_and_residuals(x: pd.Series, y: pd.Series):
    """Simple OLS: y ~ x, returns intercept, slope, residuals."""
    mask = x.notna() & y.notna()
    x_ok, y_ok = x[mask].values, y[mask].values
    if len(x_ok) < 3:
        return np.nan, np.nan, pd.Series(dtype=float)
    beta1 = np.cov(x_ok, y_ok)[0, 1] / np.var(x_ok)
    beta0 = np.mean(y_ok) - beta1 * np.mean(x_ok)
    resid = y_ok - (beta0 + beta1 * x_ok)
    return beta0, beta1, pd.Series(resid, index=x[mask].index)


def assign_quadrant(row, x_lo, x_hi, y_lo, y_hi):
    x_ok = not pd.isna(row[PRIMARY_X])
    y_ok = not pd.isna(row[PRIMARY_Y])
    if not x_ok or not y_ok:
        return "insufficient"
    xv, yv = row[PRIMARY_X], row[PRIMARY_Y]
    xh, xl = xv >= x_hi, xv <= x_lo
    yh, yl = yv >= y_hi, yv <= y_lo
    if xh and yh: return "high_shift_high_depmap"
    if xl and yl: return "low_shift_low_depmap"
    if xh and yl: return "low_shift_high_depmap"
    if xl and yh: return "high_shift_low_depmap"
    return "middle"


def analyze_cell_line(df_cl: pd.DataFrame, cell_line: str) -> dict:
    both = df_cl[df_cl["depmap_join_status"] == "both"].copy()
    n = len(both)

    x = both[PRIMARY_X]
    y = both[PRIMARY_Y]
    mask = x.notna() & y.notna()
    x_v, y_v = x[mask], y[mask]

    # Pearson + Spearman
    pearson_r, pearson_p = pearsonr(x_v, y_v) if len(x_v) > 2 else (np.nan, np.nan)
    spearman_r, spearman_p = spearmanr(x_v, y_v) if len(x_v) > 2 else (np.nan, np.nan)

    # OLS fit: y ~ x
    beta0, beta1, residuals = fit_and_residuals(x, y)
    both["residual"] = residuals

    # quadrant cutoffs (x: effect is negative → "high" means more negative = stronger)
    x_lo, x_hi = x_v.quantile(QUADRANT_PCTS[0]), x_v.quantile(QUADRANT_PCTS[1])
    y_lo, y_hi = y_v.quantile(QUADRANT_PCTS[0]), y_v.quantile(QUADRANT_PCTS[1])
    both["quadrant"] = both.apply(
        lambda r: assign_quadrant(r, x_lo, x_hi, y_lo, y_hi), axis=1
    )

    # dependency consistency check
    dep_rho, dep_p = spearmanr(y_v, both.loc[y_v.index, ALIGNED_DEP_COL][mask]) if len(x_v) > 2 else (np.nan, np.nan)

    # scatter points as list of dicts for JSON serialization
    scatter = both[["target_gene", PRIMARY_Y, PRIMARY_X, "residual", "quadrant"]].to_dict(orient="records")

    summary = {
        "cell_line": cell_line,
        "n_targets": n,
        "pearson_r": float(pearson_r),
        "pearson_p": float(pearson_p),
        "spearman_r": float(spearman_r),
        "spearman_p": float(spearman_p),
        "ols_beta0": float(beta0),
        "ols_beta1": float(beta1),
        "dependency_spearman_r": float(dep_rho),
        "dependency_spearman_p": float(dep_p),
        "effect_range": [float(x_v.min()), float(x_v.max())],
        "shift_range":  [float(y_v.min()), float(y_v.max())],
        "x_lo_cutoff": float(x_lo),
        "x_hi_cutoff": float(x_hi),
        "y_lo_cutoff": float(y_lo),
        "y_hi_cutoff": float(y_hi),
    }

    return both, summary, scatter


def shared_target_analysis(hcc38: pd.DataFrame, hcc1143: pd.DataFrame):
    """Merge HCC38 and HCC1143 on shared targets for cross-line residual comparison."""
    m38 = hcc38[["target_gene", "residual", PRIMARY_Y, PRIMARY_X]].copy()
    m38.columns = ["target_gene", "residual_HCC38", "shift_HCC38", "effect_HCC38"]
    m1143 = hcc1143[["target_gene", "residual", PRIMARY_Y, PRIMARY_X]].copy()
    m1143.columns = ["target_gene", "residual_HCC1143", "shift_HCC1143", "effect_HCC1143"]

    merged = m38.merge(m1143, on="target_gene", how="inner")

    # consistency: sign of residuals across lines
    merged["residual_sign_HCC38"]  = np.sign(merged["residual_HCC38"])
    merged["residual_sign_HCC1143"] = np.sign(merged["residual_HCC1143"])
    merged["residual_sign_agree"]   = merged["residual_sign_HCC38"] == merged["residual_sign_HCC1143"]

    # jointly high-shift / low-depmap (both lines have positive residual AND effect less than median)
    both_hi_shift_lo_depmap = merged[
        (merged["residual_HCC38"]  > 0) &
        (merged["residual_HCC1143"] > 0) &
        (merged["effect_HCC38"]  < hcc38[PRIMARY_X].median()) &
        (merged["effect_HCC1143"] < hcc1143[PRIMARY_X].median())
    ].copy()

    return merged, both_hi_shift_lo_depmap


def main():
    print("Loading bridge table …")
    df = load_data()

    results = {}
    scatter_data = {}
    all_both = {}

    for cl in ["HCC38", "HCC1143", "dixit_2016_raw__control_context"]:
        df_cl = df[df["cell_line"] == cl]
        if df_cl.empty:
            print(f"  WARNING: {cl} not found in bridge table")
            continue

        both, summary, scatter = analyze_cell_line(df_cl, cl)
        both.to_csv(OUT_DIR / f"{cl.replace('/', '_')}_residual_quadrant.tsv", sep="\t", index=False)

        results[cl] = summary
        scatter_data[cl] = scatter
        all_both[cl] = both

        print(f"\n{'='*60}")
        print(f"  {cl}  (n={summary['n_targets']})")
        print(f"{'='*60}")
        print(f"  real_shift_mean_abs vs depmap_gene_effect:")
        print(f"    Pearson  r = {summary['pearson_r']:+.3f}  p = {summary['pearson_p']:.2e}")
        print(f"    Spearman ρ = {summary['spearman_r']:+.3f}  p = {summary['spearman_p']:.2e}")
        print(f"  OLS: shift = {summary['ols_beta0']:.4f} + ({summary['ols_beta1']:.4f}) × effect")
        print(f"  Dependency consistency check:")
        print(f"    Spearman ρ = {summary['dependency_spearman_r']:+.3f}  p = {summary['dependency_spearman_p']:.2e}")
        print(f"\n  Quadrant distribution:")
        for q, cnt in both["quadrant"].value_counts().items():
            print(f"    {q:35s}  n={cnt:3d}  ({cnt/len(both):.1%})")

        # Top residuals
        print(f"\n  Top-5 positive residuals (shift > DepMap expectation):")
        top_pos = both.nlargest(5, "residual")[["target_gene", "residual", PRIMARY_Y, PRIMARY_X]]
        for _, r in top_pos.iterrows():
            print(f"    {r['target_gene']:20s}  res=+{r['residual']:.4f}  shift={r[PRIMARY_Y]:.4f}  effect={r[PRIMARY_X]:+.4f}")

        print(f"\n  Top-5 negative residuals (shift < DepMap expectation):")
        top_neg = both.nsmallest(5, "residual")[["target_gene", "residual", PRIMARY_Y, PRIMARY_X]]
        for _, r in top_neg.iterrows():
            print(f"    {r['target_gene']:20s}  res={r['residual']:.4f}  shift={r[PRIMARY_Y]:.4f}  effect={r[PRIMARY_X]:+.4f}")

    # ── Shared target analysis (HCC38 ∩ HCC1143) ────────────────────────────
    print(f"\n{'='*60}")
    print("  Shared targets: HCC38 ∩ HCC1143")
    print(f"{'='*60}")

    merged, hi_lo_candidates = shared_target_analysis(all_both["HCC38"], all_both["HCC1143"])
    merged.to_csv(OUT_DIR / "hcc38_hcc1143_shared_residuals.tsv", sep="\t", index=False)
    hi_lo_candidates.to_csv(OUT_DIR / "hcc38_hcc1143_hi_shift_lo_depmap_candidates.tsv", sep="\t", index=False)

    agree_n = int(merged["residual_sign_agree"].sum())
    print(f"\n  Shared targets: {len(merged)}")
    print(f"  Residual sign agreement (both lines same direction): {agree_n}/{len(merged)} ({agree_n/len(merged):.1%})")
    print(f"\n  Joint hi-shift / lo-depmap candidates: {len(hi_lo_candidates)}")
    if len(hi_lo_candidates) > 0:
        print(f"  {'':20s} {'HCC38_res':>10s} {'HCC1143_res':>12s} {'HCC38_eff':>10s} {'HCC1143_eff':>12s}")
        for _, r in hi_lo_candidates.iterrows():
            print(f"  {r['target_gene']:20s} {r['residual_HCC38']:>+10.4f} {r['residual_HCC1143']:>+12.4f}"
                  f" {r['effect_HCC38']:>+10.4f} {r['effect_HCC1143']:>+12.4f}")

    # ── Dixit quadrant ──────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  Dixit quadrant distribution (supplementary)")
    print(f"{'='*60}")
    if "dixit_2016_raw__control_context" in all_both:
        dixit_both = all_both["dixit_2016_raw__control_context"]
        for q, cnt in dixit_both["quadrant"].value_counts().items():
            print(f"    {q:35s}  n={cnt:3d}  ({cnt/len(dixit_both):.1%})")

    # ── Save summary JSON ────────────────────────────────────────────────────
    out_json = OUT_DIR / "analysis_summary.json"
    # convert non-serializable
    for k, v in results.items():
        for kk, vv in v.items():
            if isinstance(vv, (np.floating,)):
                results[k][kk] = float(vv)
            elif isinstance(vv, (np.integer,)):
                results[k][kk] = int(vv)
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n\nAll outputs → {OUT_DIR}")


if __name__ == "__main__":
    main()
