#!/usr/bin/env python3
"""
Stage 2 — Shared Target Master Atlas (Frozen)

Unified object for the 47 shared HCC38 ∩ HCC1143 targets with DepMap coverage.
Combines: raw metrics, OLS residuals, absolute grid categories, residual atlas types,
cross-line consistency, and functional annotation.

Run: pixi run python scripts/stage2_freeze_shared_target_master_atlas.py
"""

import json

import numpy as np
import pandas as pd
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────
BRIDGE_TABLE = Path("data/processed/stage2_truth_driven_bridge/combined_target_level_bridge_table.tsv.gz")
RESIDUAL_DIR = Path("reports/stage2_truth_driven_bridge/residual_quadrant_analysis")
CANDIDATE_DIR = Path("reports/stage2_truth_driven_bridge/candidate_layering")
OUT_DIR       = Path("reports/stage2_truth_driven_bridge/master_atlas")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PRIMARY_Y = "real_shift_mean_abs"
PRIMARY_X = "depmap_gene_effect"


def load_ols_params(summary_json_path: Path) -> dict:
    """Dynamically load OLS and cutoff parameters from analysis_summary.json."""
    with open(summary_json_path) as f:
        data = json.load(f)
    params = {}
    for cl in ["HCC38", "HCC1143"]:
        if cl not in data:
            raise ValueError(f"{cl} not found in {summary_json_path}")
        d = data[cl]
        params[cl] = {
            "beta0": d["ols_beta0"],
            "beta1": d["ols_beta1"],
            "x_lo":  d["x_lo_cutoff"],
            "x_hi":  d["x_hi_cutoff"],
            "y_lo":  d["y_lo_cutoff"],
            "y_hi":  d["y_hi_cutoff"],
        }
    return params


OLS = load_ols_params(RESIDUAL_DIR / "analysis_summary.json")

# Functional annotation (curated, manually defined)
FUNCTIONAL_ANNOTATION = {
    "ENY2":   ("Transcription co-activator / SAGA complex",          "transcription / chromatin"),
    "TADA3":  ("Transcription regulation / SAGA complex subunit",    "transcription / chromatin"),
    "ARID1A": ("Chromatin remodeling / SWI-SNF complex",             "chromatin remodeling"),
    "LAMTOR5":("mTOR signaling / lysosome scaffold",                 "mTOR / lysosome / signaling"),
    "ZBTB17": ("Transcription factor / MYC interactor",               "transcription regulation"),
    "NPM1":   ("Ribosome biogenesis / nucleolar stress sensor",       "ribosome biogenesis / nucleolar"),
    "PRPF6":  ("Spliceosome / U4-U6-U5 tri-snRNP complex",           "RNA processing / spliceosome"),
    "ZNF131": ("Transcription factor / zinc finger",                  "transcription regulation"),
    "SS18L2": ("Transcriptional co-activator / chromatin",           "transcription / chromatin"),
    "MYBL1":  ("Transcription factor / cell cycle",                  "transcription regulation"),
    "RUVBL2": ("Chromatin remodeling / INO80 complex",               "chromatin remodeling"),
    "RPS3":   ("Ribosomal protein / translation",                     "ribosomal / translation"),
    "YBX1":   ("RNA-binding / transcription / translation",         "RNA processing"),
    "COMMD6": ("Copper metabolism / NF-κB regulation",               "signaling / copper metabolism"),
    "NCOA1":  ("Nuclear receptor co-activator",                      "transcription regulation"),
    "PFN1":   ("Actin dynamics / cell motility",                     "cytoskeleton"),
    "NONO":   ("RNA-binding / transcription / splicing",             "RNA processing / transcription"),
    "CHCHD2": ("Mitochondrial OXPHOS / transcription",               "mitochondrial / oxidative phosphorylation"),
    "CDC123": ("Cell cycle / translation initiation",                "cell cycle / translation"),
    "PUF60":  ("RNA splicing / U2AF",                                "RNA processing / spliceosome"),
    "EEF1G":  ("Translation elongation factor",                      "translation elongation"),
    "GPI":    ("Glycolysis / glucose metabolism",                    "glycolysis / metabolism"),
    "NCL":    ("Nucleolar / ribosome biogenesis",                    "nucleolar / ribosome biogenesis"),
    "PABPC1": ("mRNA poly-A binding / translation",                  "translation / mRNA stability"),
    "PPA1":   ("Mitochondrial ATP synthase subunit",                  "mitochondrial / OXPHOS"),
}

# Priority tier definition
# Tier 1: Type A (shift_excess + low viability) — highest priority for mechanism study
# Tier 2: Type B (shift_excess but still essential) — mechanism interesting
# Tier 3: Q1 canonical dual-high (not Type A/B), stable across lines
# Tier 4: Q2/Q3 unstable or line-specific
# Tier 5: Type D (DepMap-excess) or residual middle
TIER_RULES = [
    ("A: shift_excess_and_low_viability", 1),
    ("B: shift_excess_but_still_essential", 2),
    ("C: line_specific_shift_excess", 3),
    ("D: depmap_excess", 4),
    ("E: bridge_consistent", 5),
]


def ols_residual(shift: float, effect: float, beta0: float, beta1: float) -> float:
    if pd.isna(shift) or pd.isna(effect):
        return np.nan
    return shift - (beta0 + beta1 * effect)


def absolute_grid_category(effect: float, shift: float, cl: str) -> str:
    """Assign Q1/Q2/Q3/Q4 based on cutoffs."""
    p = OLS[cl]
    if pd.isna(effect) or pd.isna(shift):
        return "unknown"
    # x = effect (more negative = stronger liability); y = shift
    x_lo, x_hi = p["x_lo"], p["x_hi"]
    y_lo, y_hi = p["y_lo"], p["y_hi"]
    if effect <= x_lo and shift >= y_hi:
        return "Q1: high_liability_high_shift"
    elif effect >= x_hi and shift >= y_hi:
        return "Q2: low_liability_high_shift"
    elif effect >= x_hi and shift <= y_lo:
        return "Q3: low_liability_low_shift"
    elif effect <= x_lo and shift <= y_lo:
        return "Q4: high_liability_low_shift"
    return "middle"


def build_master_atlas():
    # Load bridge table
    df = pd.read_csv(BRIDGE_TABLE, sep="\t")

    # Filter to both-lines shared, both-DepMap-covered
    h38 = df[(df["cell_line"] == "HCC38") & (df["depmap_join_status"] == "both")].copy()
    h1143 = df[(df["cell_line"] == "HCC1143") & (df["depmap_join_status"] == "both")].copy()

    # Merge on shared targets
    cols = ["target_gene", PRIMARY_Y, PRIMARY_X, "real_shift_L2",
            "depmap_gene_effect", "depmap_gene_dependency",
            "depmap_gene_effect", "depmap_gene_dependency"]
    m38 = h38[["target_gene", PRIMARY_Y, PRIMARY_X, "real_shift_L2",
               "depmap_gene_effect", "depmap_gene_dependency"]].copy()
    m38.columns = ["target_gene", "shift_HCC38", "effect_HCC38", "L2_HCC38",
                   "dep_HCC38", "dependency_HCC38"]

    m1143 = h1143[["target_gene", PRIMARY_Y, PRIMARY_X, "real_shift_L2",
                   "depmap_gene_effect", "depmap_gene_dependency"]].copy()
    m1143.columns = ["target_gene", "shift_HCC1143", "effect_HCC1143", "L2_HCC1143",
                     "dep_HCC1143", "dependency_HCC1143"]

    atlas = m38.merge(m1143, on="target_gene", how="inner")

    # Aligned liability = -effect (higher = stronger liability)
    atlas["liability_HCC38"]  = -atlas["effect_HCC38"]
    atlas["liability_HCC1143"] = -atlas["effect_HCC1143"]

    # OLS residuals
    atlas["residual_HCC38"]  = atlas.apply(
        lambda r: ols_residual(r["shift_HCC38"],  r["effect_HCC38"],
                               OLS["HCC38"]["beta0"],  OLS["HCC38"]["beta1"]),  axis=1)
    atlas["residual_HCC1143"] = atlas.apply(
        lambda r: ols_residual(r["shift_HCC1143"], r["effect_HCC1143"],
                               OLS["HCC1143"]["beta0"], OLS["HCC1143"]["beta1"]), axis=1)

    # Absolute grid categories
    atlas["grid_HCC38"]  = atlas.apply(
        lambda r: absolute_grid_category(r["effect_HCC38"],  r["shift_HCC38"],  "HCC38"),  axis=1)
    atlas["grid_HCC1143"] = atlas.apply(
        lambda r: absolute_grid_category(r["effect_HCC1143"], r["shift_HCC1143"], "HCC1143"), axis=1)

    # Cross-line consistency
    atlas["residual_sign_HCC38"]  = np.sign(atlas["residual_HCC38"])
    atlas["residual_sign_HCC1143"] = np.sign(atlas["residual_HCC1143"])
    atlas["residual_sign_agree"]   = atlas["residual_sign_HCC38"] == atlas["residual_sign_HCC1143"]
    atlas["shift_sign_HCC38"]  = np.sign(atlas["shift_HCC38"])
    atlas["shift_sign_HCC1143"] = np.sign(atlas["shift_HCC1143"])
    atlas["shift_sign_agree"]   = atlas["shift_sign_HCC38"] == atlas["shift_sign_HCC1143"]

    # Load candidate types (Type A/B/C/D)
    candidates = pd.read_csv(CANDIDATE_DIR / "hcc38_hcc1143_dual_criteria_candidates.tsv", sep="\t")
    atlas = atlas.merge(
        candidates[["target_gene", "candidate_type", "combined_residual_label",
                    "combined_depmap_label", "both_lines_shift_excess",
                    "functional_category", "functional_description"]],
        on="target_gene", how="left"
    )

    # Fill functional annotation for genes not in the curated list
    for gene in atlas.loc[atlas["functional_category"].isna(), "target_gene"]:
        if gene in FUNCTIONAL_ANNOTATION:
            idx = atlas[atlas["target_gene"] == gene].index
            atlas.loc[idx, "functional_category"] = FUNCTIONAL_ANNOTATION[gene][1]
            atlas.loc[idx, "functional_description"] = FUNCTIONAL_ANNOTATION[gene][0]

    # Priority tier
    tier_map = dict(TIER_RULES)
    atlas["priority_tier"] = atlas["candidate_type"].map(tier_map).fillna(5).astype(int)

    # Mean metrics across lines
    atlas["shift_mean"]    = (atlas["shift_HCC38"] + atlas["shift_HCC1143"]) / 2
    atlas["liability_mean"] = (atlas["liability_HCC38"] + atlas["liability_HCC1143"]) / 2
    atlas["residual_mean"] = (atlas["residual_HCC38"] + atlas["residual_HCC1143"]) / 2

    # Round numerics for readability
    num_cols = [c for c in atlas.columns if atlas[c].dtype in (np.float64, np.float32)]
    atlas[num_cols] = atlas[num_cols].round(6)

    # Final column order
    front = [
        "target_gene", "priority_tier", "candidate_type",
        "functional_category", "functional_description",
        "combined_residual_label", "combined_depmap_label", "both_lines_shift_excess",
        "grid_HCC38", "grid_HCC1143",
        "shift_HCC38", "shift_HCC1143", "shift_mean",
        "liability_HCC38", "liability_HCC1143", "liability_mean",
        "residual_HCC38", "residual_HCC1143", "residual_mean",
        "L2_HCC38", "L2_HCC1143",
        "effect_HCC38", "effect_HCC1143",
        "dep_HCC38", "dep_HCC1143",
        "residual_sign_HCC38", "residual_sign_HCC1143", "residual_sign_agree",
        "shift_sign_HCC38", "shift_sign_HCC1143", "shift_sign_agree",
    ]
    atlas = atlas[[c for c in front if c in atlas.columns]]

    # Sort: tier, then residual_mean desc
    atlas = atlas.sort_values(["priority_tier", "residual_mean"], ascending=[True, False]).reset_index(drop=True)

    # Number of shared targets (should be 47)
    return atlas


def summary_stats(atlas: pd.DataFrame):
    print("\n" + "="*70)
    print("SHARED TARGET MASTER ATLAS — HCC38 ∩ HCC1143 (Frozen)")
    print("="*70)
    print(f"\nTotal shared & covered targets: {len(atlas)}")
    print(f"  Tier 1 (Type A):              {(atlas['priority_tier']==1).sum()}")
    print(f"  Tier 2 (Type B):              {(atlas['priority_tier']==2).sum()}")
    print(f"  Tier 3 (Type C):              {(atlas['priority_tier']==3).sum()}")
    print(f"  Tier 4 (Type D):              {(atlas['priority_tier']==4).sum()}")
    print(f"  Tier 5 (E / middle):          {(atlas['priority_tier']==5).sum()}")

    print(f"\nGrid distribution HCC38:")
    for g, c in atlas["grid_HCC38"].value_counts().items():
        print(f"  {g:40s}  n={c}")

    print(f"\nGrid distribution HCC1143:")
    for g, c in atlas["grid_HCC1143"].value_counts().items():
        print(f"  {g:40s}  n={c}")

    print(f"\nResidual sign agreement: {atlas['residual_sign_agree'].sum()}/{len(atlas)} "
          f"({atlas['residual_sign_agree'].mean():.1%})")

    print(f"\nFunctional category breakdown:")
    for cat, cnt in atlas["functional_category"].fillna("uncategorized").value_counts().items():
        print(f"  {cat:45s}  n={cnt}")

    print(f"\nTop residual targets (both lines):")
    top = atlas.nlargest(10, "residual_mean")[
        ["target_gene", "candidate_type", "residual_HCC38", "residual_HCC1143", "residual_mean"]]
    for _, r in top.iterrows():
        print(f"  {r['target_gene']:20s}  type={r['candidate_type']:45s}  "
              f"HCC38={r['residual_HCC38']:+.5f}  HCC1143={r['residual_HCC1143']:+.5f}  "
              f"mean={r['residual_mean']:+.5f}")


def write_tier_tables(atlas: pd.DataFrame):
    """Write separate tables per tier for downstream use."""
    for tier in range(1, 6):
        subset = atlas[atlas["priority_tier"] == tier]
        if len(subset) == 0:
            continue
        tier_name = subset["candidate_type"].iloc[0] if "candidate_type" in subset else f"tier_{tier}"
        safe_name = tier_name.replace(" ", "_").replace(":", "").replace("/", "_")
        subset.to_csv(OUT_DIR / f"tier_{tier}_{safe_name}.tsv", sep="\t", index=False)


def main():
    atlas = build_master_atlas()
    atlas.to_csv(OUT_DIR / "shared_target_master_atlas.tsv", sep="\t", index=False)
    write_tier_tables(atlas)
    summary_stats(atlas)
    print(f"\nAll outputs → {OUT_DIR}")
    print(f"Master atlas: {OUT_DIR / 'shared_target_master_atlas.tsv'}")


if __name__ == "__main__":
    main()
