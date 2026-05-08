#!/usr/bin/env python3
"""
Stage 2 — Dual-Criteria Candidate Table + Functional Annotation

For shared HCC38 ∩ HCC1143 targets:
  Label 1 (Residual): residual > 0 AND top quartile of positive residuals
  Label 2 (Absolute DepMap): strong / intermediate / weak by effect distribution

Run: pixi run python scripts/pipeline/dual_criteria_candidate_table.py
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr

BRIDGE_TABLE = Path("data/processed/truth_driven_bridge/combined_target_level_bridge_table.tsv.gz")
RESIDUAL_DIR = Path("reports/truth_driven_bridge/residual_quadrant_analysis")
OUT_DIR      = Path("reports/truth_driven_bridge/candidate_layering")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PRIMARY_Y = "real_shift_mean_abs"
PRIMARY_X = "depmap_gene_effect"

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
    "NCL":    ("Nucleolar / ribosome biogenesis",                     "nucleolar / ribosome biogenesis"),
    "PABPC1": ("mRNA poly-A binding / translation",                  "translation / mRNA stability"),
    "PPA1":   ("Mitochondrial ATP synthase subunit",                  "mitochondrial / OXPHOS"),
}


def load_residual_tables():
    """Load per-cell-line residual tables from previous step."""
    h38 = pd.read_csv(RESIDUAL_DIR / "HCC38_residual_quadrant.tsv", sep="\t")
    h1143 = pd.read_csv(RESIDUAL_DIR / "HCC1143_residual_quadrant.tsv", sep="\t")
    return h38, h1143


def assign_residual_label(residual: float, top_quartile_threshold: float) -> str:
    if residual > 0 and residual >= top_quartile_threshold:
        return "shift_excess_top_residual"
    elif residual > 0:
        return "shift_excess"
    elif residual < 0:
        return "shift_deficient"
    return "middle"


def assign_absolute_depmap_label(effect: float, q33: float, q66: float) -> str:
    if pd.isna(effect):
        return "unknown"
    if effect <= q33:
        return "weak_viability_liability"
    elif effect <= q66:
        return "intermediate_viability_liability"
    else:
        return "strong_viability_liability"


def build_dual_criteria_table(h38: pd.DataFrame, h1143: pd.DataFrame):
    # Merge on shared targets
    m38 = h38[["target_gene", "residual", PRIMARY_Y, PRIMARY_X, "depmap_gene_dependency"]].copy()
    m38.columns = ["target_gene", "residual_HCC38", "shift_HCC38", "effect_HCC38", "dep_HCC38"]
    m1143 = h1143[["target_gene", "residual", PRIMARY_Y, PRIMARY_X, "depmap_gene_dependency"]].copy()
    m1143.columns = ["target_gene", "residual_HCC1143", "shift_HCC1143", "effect_HCC1143", "dep_HCC1143"]

    merged = m38.merge(m1143, on="target_gene", how="inner")

    # Residual label (per line)
    # Use top quartile of positive residuals across both lines combined
    all_pos_res = pd.concat([merged["residual_HCC38"], merged["residual_HCC1143"]])
    top_q_res = all_pos_res[all_pos_res > 0].quantile(0.75)

    merged["residual_label_HCC38"]  = merged["residual_HCC38"].apply(
        lambda r: assign_residual_label(r, top_q_res))
    merged["residual_label_HCC1143"] = merged["residual_HCC1143"].apply(
        lambda r: assign_residual_label(r, top_q_res))

    # Absolute DepMap label (per line)
    # Use joint effect quantiles
    q33_38, q66_38 = merged["effect_HCC38"].quantile([0.33, 0.66])
    q33_1143, q66_1143 = merged["effect_HCC1143"].quantile([0.33, 0.66])

    merged["depmap_label_HCC38"]  = merged["effect_HCC38"].apply(
        lambda e: assign_absolute_depmap_label(e, q33_38, q66_38))
    merged["depmap_label_HCC1143"] = merged["effect_HCC1143"].apply(
        lambda e: assign_absolute_depmap_label(e, q33_1143, q66_1143))

    # Combined label: residual label + absolute depmap label (take worse across lines)
    merged["combined_residual_label"] = merged.apply(
        lambda r: "top_residual_in_both"
        if (r["residual_label_HCC38"].startswith("shift_excess") and
            r["residual_label_HCC1143"].startswith("shift_excess"))
        else ("top_residual_in_one"
              if (r["residual_label_HCC38"].startswith("shift_excess") or
                  r["residual_label_HCC1143"].startswith("shift_excess"))
              else r["residual_label_HCC38"]), axis=1)

    merged["combined_depmap_label"] = merged.apply(
        lambda r: min([r["depmap_label_HCC38"], r["depmap_label_HCC1143"]],
                      key=lambda x: {"strong_viability_liability": 0,
                                     "intermediate_viability_liability": 1,
                                     "weak_viability_liability": 2}.get(x, 3)), axis=1)

    # Functional annotation
    merged["functional_description"] = merged["target_gene"].map(
        lambda g: FUNCTIONAL_ANNOTATION.get(g, (None, None))[0])
    merged["functional_category"] = merged["target_gene"].map(
        lambda g: FUNCTIONAL_ANNOTATION.get(g, (None, None))[1])

    # Joint candidate: positive residual in both lines
    merged["both_lines_shift_excess"] = (
        (merged["residual_HCC38"] > 0) & (merged["residual_HCC1143"] > 0))

    return merged, top_q_res


def build_candidate_summary(merged: pd.DataFrame):
    """Build the main candidate table with all labels."""
    cols = [
        "target_gene",
        "residual_HCC38", "residual_HCC1143",
        "shift_HCC38", "shift_HCC1143",
        "effect_HCC38", "effect_HCC1143",
        "dep_HCC38", "dep_HCC1143",
        "residual_label_HCC38", "residual_label_HCC1143",
        "depmap_label_HCC38", "depmap_label_HCC1143",
        "combined_residual_label", "combined_depmap_label",
        "both_lines_shift_excess",
        "functional_description", "functional_category",
    ]
    summary = merged[cols].sort_values(
        ["both_lines_shift_excess", "residual_HCC38", "residual_HCC1143"],
        ascending=[False, False, False]
    ).reset_index(drop=True)
    return summary


def categorize_candidates(merged: pd.DataFrame):
    """
    Final candidate type assignment:
      Type A: both_lines_shift_excess AND weak_viability_liability in at least one line
      Type B: both_lines_shift_excess AND (not weak in either line, i.e., intermediate or strong)
      Bridge-consistent: residual in one line only or residual ≈ 0
      DepMap-excess: negative residual (DepMap > shift expectation)
    """
    rows = []
    for _, r in merged.iterrows():
        if r["both_lines_shift_excess"]:
            if (r["depmap_label_HCC38"] == "weak_viability_liability" or
                r["depmap_label_HCC1143"] == "weak_viability_liability"):
                cand_type = "A: shift_excess_and_low_viability"
            else:
                cand_type = "B: shift_excess_but_still_essential"
        elif r["residual_HCC38"] > 0 or r["residual_HCC1143"] > 0:
            cand_type = "C: line_specific_shift_excess"
        elif r["residual_HCC38"] < 0 or r["residual_HCC1143"] < 0:
            cand_type = "D: depmap_excess"
        else:
            cand_type = "E: bridge_consistent"
        rows.append({"target_gene": r["target_gene"], "candidate_type": cand_type})
    return pd.DataFrame(rows)


def main():
    print("Loading residual tables …")
    h38, h1143 = load_residual_tables()
    merged, top_q_res = build_dual_criteria_table(h38, h1143)

    types = categorize_candidates(merged)
    summary = build_candidate_summary(merged)
    summary = summary.merge(types, on="target_gene")

    # Reorder columns with candidate_type near front
    front = ["target_gene", "candidate_type", "combined_residual_label", "combined_depmap_label",
             "both_lines_shift_excess", "functional_category", "functional_description",
             "residual_HCC38", "residual_HCC1143", "shift_HCC38", "shift_HCC1143",
             "effect_HCC38", "effect_HCC1143", "dep_HCC38", "dep_HCC1143",
             "residual_label_HCC38", "residual_label_HCC1143",
             "depmap_label_HCC38", "depmap_label_HCC1143"]
    summary = summary[[c for c in front if c in summary.columns]]
    summary.to_csv(OUT_DIR / "hcc38_hcc1143_dual_criteria_candidates.tsv", sep="\t", index=False)

    # ── Print summary ───────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("DUAL-CRITERIA CANDIDATE SUMMARY — HCC38 ∩ HCC1143")
    print("="*70)

    print(f"\nTop residual quartile threshold (positive): {top_q_res:.5f}")
    print(f"\nTotal shared targets: {len(summary)}")

    print("\nCandidate type distribution:")
    for t, cnt in summary["candidate_type"].value_counts().items():
        print(f"  {t:45s}  n={cnt:3d}")

    print("\nFunctional category breakdown for Type A candidates:")
    type_a = summary[summary["candidate_type"] == "A: shift_excess_and_low_viability"]
    for cat in type_a["functional_category"].dropna().unique():
        genes = type_a[type_a["functional_category"] == cat]["target_gene"].tolist()
        print(f"  {cat:40s}  {', '.join(genes)}")

    print("\nFunctional category breakdown for Type B candidates:")
    type_b = summary[summary["candidate_type"] == "B: shift_excess_but_still_essential"]
    for cat in type_b["functional_category"].dropna().unique():
        genes = type_b[type_b["functional_category"] == cat]["target_gene"].tolist()
        print(f"  {cat:40s}  {', '.join(genes)}")

    print("\nFull Type A table:")
    cols_show = ["target_gene", "functional_category", "effect_HCC38", "effect_HCC1143",
                 "residual_HCC38", "residual_HCC1143", "depmap_label_HCC38", "depmap_label_HCC1143"]
    print(type_a[cols_show].to_string(index=False))

    print("\nFull Type B table:")
    print(type_b[cols_show].to_string(index=False))

    print(f"\nOutputs → {OUT_DIR}")

    # ── Dixit category-level analysis ─────────────────────────────────────
    print("\n" + "="*70)
    print("DIXIT — Category-level对照 (supplementary)")
    print("="*70)

    dixit_path = RESIDUAL_DIR / "dixit_2016_raw__control_context_residual_quadrant.tsv"
    if dixit_path.exists():
        dixit = pd.read_csv(dixit_path, sep="\t")
        dixit_pos_res = dixit[dixit["residual"] > 0]
        dixit_neg_res = dixit[dixit["residual"] < 0]
        top_q_dixit = dixit_pos_res["residual"].quantile(0.75) if len(dixit_pos_res) > 0 else np.nan

        q33, q66 = dixit["depmap_gene_effect"].quantile([0.33, 0.66])
        dixit["depmap_label"] = dixit["depmap_gene_effect"].apply(
            lambda e: assign_absolute_depmap_label(e, q33, q66))
        dixit["functional_category"] = dixit["target_gene"].map(
            lambda g: FUNCTIONAL_ANNOTATION.get(g, (None, None))[1])

        # Re-derive subsets after enrichment columns added
        dixit_pos_res = dixit[dixit["residual"] > 0]
        dixit_neg_res = dixit[dixit["residual"] < 0]

        print(f"\nDixit total matched: {len(dixit)}")
        print(f"Shift-excess (residual > 0): {len(dixit_pos_res)} ({len(dixit_pos_res)/len(dixit):.1%})")
        print(f"Shift-deficient (residual < 0): {len(dixit_neg_res)} ({len(dixit_neg_res)/len(dixit):.1%})")
        print(f"Top quartile threshold (Dixit): {top_q_dixit:.5f}" if not np.isnan(top_q_dixit) else "")

        # Functional categories for shift-excess
        print("\nFunctional categories in Dixit shift-excess targets:")
        cat_counts = dixit_pos_res["functional_category"].fillna("uncategorized").value_counts()
        for cat, cnt in cat_counts.items():
            print(f"  {cat:40s}  n={cnt:3d}  ({cnt/len(dixit_pos_res):.1%})")

        dixit_out = dixit[["target_gene", "residual", "real_shift_mean_abs",
                            "depmap_gene_effect", "depmap_label", "functional_category"]].copy()
        dixit_out = dixit_out.sort_values("residual", ascending=False)
        dixit_out.to_csv(OUT_DIR / "dixit_shift_excess_candidates.tsv", sep="\t", index=False)
        print(f"\nDixit shift-excess table → {OUT_DIR / 'dixit_shift_excess_candidates.tsv'}")
    else:
        print("Dixit residual table not found, skipping.")


if __name__ == "__main__":
    main()
