#!/usr/bin/env python3
"""
Stage 2 — Functional Axis Compression (Fine + Macro Axes)

Builds four axis-layer objects from the frozen master atlas:
  1. shared_target_axis_membership.tsv   — long-format, each gene × axis
  2. axis_summary.tsv                   — per-axis aggregate statistics
  3. axis_crossline_consistency.tsv    — cross-line consistency by axis
  4. axis_priority_view.tsv            — tier × axis priority matrix

Run: pixi run python scripts/pipeline/build_axis_tables.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

ATLAS = Path("reports/truth_driven_bridge/master_atlas/shared_target_master_atlas.tsv")
OUT_DIR = Path("reports/truth_driven_bridge/master_atlas")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Fine-axis definitions (one gene → 1 primary fine axis; some genes → 2 axes)
# Structure: gene → list of (fine_axis, macro_axis, confidence, note)
# ─────────────────────────────────────────────────────────────────────────────
AXIS_MAP = {
    # Tier 1 — shift_excess + low viability (Type A)
    "ENY2":    [("transcription / chromatin",     "gene expression machinery",  "high", "SAGA complex, transcription co-activator")],
    "PRPF6":   [("RNA processing / spliceosome",  "RNA processing",             "high", "U4-U6-U5 tri-snRNP, spliceosome core")],
    "TADA3":   [("transcription / chromatin",     "gene expression machinery",  "high", "SAGA complex subunit")],
    "NPM1":    [("ribosome biogenesis / nucleolar","ribosome / nucleolar biogenesis","high","nucleolar stress sensor, ribosome biogenesis")],
    "ARID1A":  [("chromatin remodeling",          "gene expression machinery",  "high", "SWI-SNF complex core subunit")],
    "ZBTB17":  [("transcription regulation",        "gene expression machinery",  "medium","MYC interactor, transcription factor")],
    "ZNF131":  [("transcription regulation",        "gene expression machinery",  "medium","zinc finger transcription factor")],

    # Tier 2 — shift_excess but still essential (Type B)
    "LAMTOR5": [("mTOR / lysosome / signaling",    "signaling / growth control", "high","mTORC1 lysosome scaffold, Ragulator complex")],
    "MYBL1":   [("transcription regulation",        "gene expression machinery",   "medium","cell-cycle TF, A-Myb in TNBC")],
    "VEZF1":   [("transcription regulation",        "gene expression machinery",   "medium","vascular endothelial zinc finger TF")],

    # Tier 3 — line-specific (Type C)
    "PMF1":    [("transcription regulation",        "gene expression machinery",   "low",  "polyamine-modulated factor 1")],
    "CDKN2A":  [("cell cycle / replication",        "cell-state regulation",       "high","p16INK4a/p14ARF tumor suppressor")],
    "PFDN5":   [("proteostasis / chaperone",        "proteostasis",               "medium","prefoldin chaperone, 6-subunit")],
    "TAB3":    [("NF-κB / MAPK signaling",          "signaling / growth control", "medium","TAK1/TAB3 complex, NF-κB activation")],
    "GON4L":   [("transcription regulation",         "gene expression machinery",   "low",  "GON4L transcriptional co-activator")],
    "MIER1":   [("transcription regulation",          "gene expression machinery",  "low",  "mesoderm induction early response")],
    "PA2G4":   [("growth / proliferation",           "signaling / growth control", "medium","proliferation-related, ErbB3 binding")],
    "HLX":     [("transcription regulation",          "gene expression machinery", "low",  "HOX-like transcription factor")],
    "TMF1":    [("transcription regulation",          "gene expression machinery", "low",  "TCF4 fusion partner, nuclear receptor")],
    "ZBTB20":  [("transcription regulation",          "gene expression machinery", "low",  "zinc finger BTB domain TF")],

    # Tier 4 — DepMap-excess (Type D)
    "BMPR1A":  [("TGF-beta / BMP signaling",         "signaling / growth control", "medium","BMP type I receptor")],
    "THRA":    [("nuclear receptor / metabolism",    "signaling / growth control", "medium","thyroid hormone receptor α")],
    "MTDH":    [("signaling / oncogene",             "signaling / growth control", "high","metadherin, NF-κB/PI3K signaling")],
    "PARK7":   [("oxidative stress / mitochondrial", "stress response",            "medium","Parkinson's protein, redox sensor")],
    "STAT3":   [("JAK-STAT signaling",               "signaling / growth control", "high","STAT3, IL-6/JAK pathway")],
    "THAP8":   [("transcription regulation",          "gene expression machinery",  "low",  "THAP domain-containing protein")],
    "KLF3":    [("transcription regulation",          "gene expression machinery",  "medium","Kruppel-like factor 3")],
    "ZBTB5":   [("transcription regulation",          "gene expression machinery",  "low",  "zinc finger BTB domain 5")],
    "ERC1":    [("synaptic / signaling",             "signaling / growth control", "low",  "ERC1, synaptic scaffold")],
    "PEX14":   [("peroxisome / metabolism",          "metabolism",                 "medium","peroxisomal membrane protein")],
    "UBP1":    [("transcription regulation",          "gene expression machinery",  "low",  "upstream binding protein 1")],
    "HDGF":    [("growth factor / proliferation",    "signaling / growth control", "medium","hepatoma-derived growth factor")],
    "XBP1":    [("ER stress / UPR",                  "stress response",            "high","XBP1, unfolded protein response")],
    "SMAD1":   [("TGF-beta / BMP signaling",         "signaling / growth control", "high","SMAD1, BMP pathway")],
    "MAML3":   [("transcription regulation",          "gene expression machinery",  "medium","Mastermind-like co-activator 3")],
    "PCBD1":   [("metabolism / transcription",       "metabolism",                 "low",  "pterin metabolism, co-activator")],
    "ETV3":    [("transcription regulation",          "gene expression machinery",  "low",  "ETS translocation 3, repressor")],
    "ZNF566":  [("transcription regulation",          "gene expression machinery",  "low",  "zinc finger protein 566")],
    "PRDX2":   [("oxidative stress / antioxidant",  "stress response",           "high","peroxiredoxin 2, H2O2 scavenging")],
    "ZNF24":   [("transcription regulation",          "gene expression machinery",  "low",  "zinc finger protein 24")],
    "COMMD6":  [("NF-κB / copper signaling",         "signaling / growth control", "medium","COMMD6, NF-κB regulation")],
    "RORC":    [("nuclear receptor / metabolism",   "signaling / growth control", "low",  "RORγ, nuclear receptor")],
    "NCOA1":   [("nuclear receptor / co-activator", "gene expression machinery",  "medium","NCOA1, steroid receptor co-activator")],
    "TMSB4X":  [("cytoskeleton / cell motility",    "cell-state regulation",       "high","thymosin β-4, actin monomer binding")],
    "RPS3":    [("ribosomal / translation",          "ribosome / nucleolar biogenesis","high","40S ribosomal protein S3")],
    "RUVBL2":  [("chromatin remodeling",             "gene expression machinery",   "high","INO80 complex, ATPase")],
    "YBX1":    [("RNA processing / transcription",   "RNA processing",              "high","Y-box binding protein, multitasking")],
}


# ─────────────────────────────────────────────────────────────────────────────
# Object 1 — shared_target_axis_membership.tsv
# ─────────────────────────────────────────────────────────────────────────────
def build_axis_membership() -> pd.DataFrame:
    rows = []
    for gene, axes in AXIS_MAP.items():
        for (fine, macro, conf, note) in axes:
            rows.append({
                "target_gene": gene,
                "fine_axis": fine,
                "macro_axis": macro,
                "annotation_confidence": conf,
                "evidence_note": note,
            })
    df = pd.DataFrame(rows)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Object 2 — axis_summary.tsv
# ─────────────────────────────────────────────────────────────────────────────
def build_axis_summary(membership: pd.DataFrame, atlas: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in membership.iterrows():
        gene = row["target_gene"]
        fine = row["fine_axis"]
        macro = row["macro_axis"]
        a = atlas[atlas["target_gene"] == gene]
        if len(a) == 0:
            continue
        a = a.iloc[0]
        rows.append({
            "fine_axis": fine,
            "macro_axis": macro,
            "target_gene": gene,
            "priority_tier": int(a["priority_tier"]),
            "candidate_type": a["candidate_type"],
            "shift_HCC38": a["shift_HCC38"],
            "shift_HCC1143": a["shift_HCC1143"],
            "liability_HCC38": a["liability_HCC38"],
            "liability_HCC1143": a["liability_HCC1143"],
            "residual_HCC38": a["residual_HCC38"],
            "residual_HCC1143": a["residual_HCC1143"],
            "grid_HCC38": a["grid_HCC38"],
            "grid_HCC1143": a["grid_HCC1143"],
        })
    detail = pd.DataFrame(rows)

    # Per fine_axis summary
    fine_rows = []
    for fa in detail["fine_axis"].unique():
        sub = detail[detail["fine_axis"] == fa]
        genes = "; ".join(sorted(sub["target_gene"]))
        tier_counts = sub["priority_tier"].value_counts().to_dict()
        fine_rows.append({
            "fine_axis": fa,
            "macro_axis": sub["macro_axis"].iloc[0],
            "n_genes": len(sub),
            "genes": genes,
            "mean_shift_HCC38": sub["shift_HCC38"].mean(),
            "mean_shift_HCC1143": sub["shift_HCC1143"].mean(),
            "mean_liability_HCC38": sub["liability_HCC38"].mean(),
            "mean_liability_HCC1143": sub["liability_HCC1143"].mean(),
            "mean_residual_HCC38": sub["residual_HCC38"].mean(),
            "mean_residual_HCC1143": sub["residual_HCC1143"].mean(),
            "fraction_Q1_HCC38": (sub["grid_HCC38"] == "Q1: high_liability_high_shift").mean(),
            "fraction_Q1_HCC1143": (sub["grid_HCC1143"] == "Q1: high_liability_high_shift").mean(),
            "fraction_shift_excess": (sub["candidate_type"].str.startswith("A") | sub["candidate_type"].str.startswith("B")).mean(),
            "tier1_n": tier_counts.get(1, 0),
            "tier2_n": tier_counts.get(2, 0),
            "tier3_n": tier_counts.get(3, 0),
            "tier4_n": tier_counts.get(4, 0),
            "dominant_tier": min(tier_counts, key=tier_counts.get),
        })
    fine_df = pd.DataFrame(fine_rows).sort_values(["macro_axis", "n_genes"], ascending=[True, False])

    # Per macro_axis summary
    macro_rows = []
    for ma in fine_df["macro_axis"].unique():
        sub = fine_df[fine_df["macro_axis"] == ma]
        macro_rows.append({
            "macro_axis": ma,
            "n_fine_axes": len(sub),
            "total_genes": sub["n_genes"].sum(),
            "mean_shift_HCC38": sub["mean_shift_HCC38"].mean(),
            "mean_shift_HCC1143": sub["mean_shift_HCC1143"].mean(),
            "mean_liability_HCC38": sub["mean_liability_HCC38"].mean(),
            "mean_liability_HCC1143": sub["mean_liability_HCC1143"].mean(),
            "fraction_Q1_HCC38": sub["fraction_Q1_HCC38"].mean(),
            "fraction_Q1_HCC1143": sub["fraction_Q1_HCC1143"].mean(),
            "fraction_shift_excess": sub["fraction_shift_excess"].mean(),
        })
    macro_df = pd.DataFrame(macro_rows)

    return fine_df, macro_df


# ─────────────────────────────────────────────────────────────────────────────
# Object 3 — axis_crossline_consistency.tsv
# ─────────────────────────────────────────────────────────────────────────────
def build_axis_consistency(membership: pd.DataFrame, atlas: pd.DataFrame) -> pd.DataFrame:
    # Aggregate residual per fine axis per cell line
    rows = []
    for fine in membership["fine_axis"].unique():
        sub_m = membership[membership["fine_axis"] == fine]
        genes = sub_m["target_gene"].tolist()
        a_sub = atlas[atlas["target_gene"].isin(genes)]
        if len(a_sub) == 0:
            continue

        mean_res_38   = a_sub["residual_HCC38"].mean()
        mean_res_1143 = a_sub["residual_HCC1143"].mean()

        # Key signal: per-gene cross-line residual sign agreement (atlas field)
        res_sign_agree = a_sub["residual_sign_agree"].mean()

        # Secondary signal: within-axis gene-to-gene sign concordance per cell line
        # Compare gene signs within each cell line, then average across lines
        def within_line_concordance(series):
            """Fraction of gene-pairs with same sign in a cell line."""
            signs = series.values
            if len(signs) < 2:
                return 1.0
            n_same = sum(1 for i in range(len(signs)) for j in range(i+1, len(signs))
                         if signs[i] * signs[j] > 0)
            n_total = len(signs) * (len(signs) - 1) // 2
            return n_same / n_total if n_total > 0 else 1.0

        concord_38   = within_line_concordance(a_sub["residual_HCC38"])
        concord_1143 = within_line_concordance(a_sub["residual_HCC1143"])
        concord_mean = (concord_38 + concord_1143) / 2

        q1_38   = (a_sub["grid_HCC38"]  == "Q1: high_liability_high_shift").mean()
        q1_1143 = (a_sub["grid_HCC1143"] == "Q1: high_liability_high_shift").mean()
        shift_excess_n = int((a_sub["candidate_type"].str.startswith("A") |
                               a_sub["candidate_type"].str.startswith("B")).sum())

        # Consistency class — residual sign agreement is primary, Q1 fraction is secondary
        # Hierarchy:
        #   line_skewed      if cross-line sign agreement < 0.25 (gene signs flip between lines)
        #   shared_shift_excess if ≥50% genes are shift_excess (Type A or B)
        #   shared_dual_high if both lines have ≥50% Q1 AND cross-line sign agreement ≥ 0.75
        #   shared_middle    if cross-line sign agreement ≥ 0.75 but not above categories
        #   heterogeneous    if cross-line sign agreement between 0.25–0.75 OR
        #                     within-axis concordance low (genes within axis disagree)

        if res_sign_agree < 0.25:
            consistency = "line_skewed"
        elif shift_excess_n > len(genes) * 0.5:
            # strict > 0.5: require a clear majority, not a tie
            consistency = "shared_shift_excess"
        elif q1_38 >= 0.5 and q1_1143 >= 0.5 and res_sign_agree >= 0.75:
            consistency = "shared_dual_high"
        elif res_sign_agree >= 0.75:
            consistency = "shared_middle"
        else:
            consistency = "heterogeneous"

        rows.append({
            "fine_axis": fine,
            "macro_axis": sub_m["macro_axis"].iloc[0],
            "n_genes": len(genes),
            "mean_residual_HCC38": round(mean_res_38, 6),
            "mean_residual_HCC1143": round(mean_res_1143, 6),
            "fraction_residual_sign_agree": round(res_sign_agree, 3),
            "within_axis_concordance_mean": round(concord_mean, 3),
            "fraction_Q1_HCC38": round(q1_38, 3),
            "fraction_Q1_HCC1143": round(q1_1143, 3),
            "n_shift_excess": int(shift_excess_n),
            "consistency_class": consistency,
        })
    return pd.DataFrame(rows).sort_values("consistency_class")


# ─────────────────────────────────────────────────────────────────────────────
# Object 4 — axis_priority_view.tsv
# ─────────────────────────────────────────────────────────────────────────────
def build_axis_priority(membership: pd.DataFrame, atlas: pd.DataFrame) -> pd.DataFrame:
    # Which axes have the most Tier 1+2 genes?
    tier1_2 = atlas[atlas["priority_tier"].isin([1, 2])]
    rows = []
    for fine in membership["fine_axis"].unique():
        sub_m = membership[membership["fine_axis"] == fine]
        genes = sub_m["target_gene"].tolist()
        t12 = tier1_2[tier1_2["target_gene"].isin(genes)]
        rows.append({
            "fine_axis": fine,
            "macro_axis": sub_m["macro_axis"].iloc[0],
            "n_tier1_2_genes": len(t12),
            "tier1_2_genes": "; ".join(sorted(t12["target_gene"])) if len(t12) > 0 else "",
            "tier1_n": int((t12["priority_tier"] == 1).sum()),
            "tier2_n": int((t12["priority_tier"] == 2).sum()),
            "total_in_axis": len(genes),
        })
    df = pd.DataFrame(rows).sort_values("n_tier1_2_genes", ascending=False)
    df["priority_rank"] = range(1, len(df) + 1)
    return df


def main():
    atlas = pd.read_csv(ATLAS, sep="\t")
    membership = build_axis_membership()
    membership.to_csv(OUT_DIR / "shared_target_axis_membership.tsv", sep="\t", index=False)

    fine_df, macro_df = build_axis_summary(membership, atlas)
    fine_df.to_csv(OUT_DIR / "axis_summary_fine.tsv", sep="\t", index=False)
    macro_df.to_csv(OUT_DIR / "axis_summary_macro.tsv", sep="\t", index=False)

    consistency = build_axis_consistency(membership, atlas)
    consistency.to_csv(OUT_DIR / "axis_crossline_consistency.tsv", sep="\t", index=False)

    priority = build_axis_priority(membership, atlas)
    priority.to_csv(OUT_DIR / "axis_priority_view.tsv", sep="\t", index=False)

    # ── Print summary ──────────────────────────────────────────────────────
    print("="*70)
    print("FUNCTIONAL AXIS COMPRESSION — Summary")
    print("="*70)

    print(f"\n[1] Axis membership: {len(membership)} rows, {len(membership['target_gene'].unique())} genes annotated")

    print(f"\n[2] Fine-axis summary ({len(fine_df)} fine axes):")
    for _, r in fine_df.iterrows():
        print(f"  {r['fine_axis']:45s}  macro={r['macro_axis']:35s}  n={r['n_genes']}  "
              f"t1={r['tier1_n']} t2={r['tier2_n']}  "
              f"Q1_HCC38={r['fraction_Q1_HCC38']:.0%}  Q1_1143={r['fraction_Q1_HCC1143']:.0%}  "
              f"shift_excess={r['fraction_shift_excess']:.0%}")

    print(f"\n[3] Cross-line consistency ({len(consistency)} axes):")
    for _, r in consistency.iterrows():
        print(f"  {r['consistency_class']:25s}  {r['fine_axis']:45s}  "
              f"res_38={r['mean_residual_HCC38']:+.5f}  res_1143={r['mean_residual_HCC1143']:+.5f}  "
              f"signAgree={r['fraction_residual_sign_agree']:.0%}")

    print(f"\n[4] Axis priority (Tier 1+2 focus):")
    top_priority = priority[priority["n_tier1_2_genes"] > 0]
    for _, r in top_priority.iterrows():
        print(f"  rank={r['priority_rank']:2d}  {r['fine_axis']:45s}  "
              f"T1+2={r['n_tier1_2_genes']} ({r['tier1_n']}+{r['tier2_n']})  "
              f"tier1_2_genes={r['tier1_2_genes']}")

    print(f"\nAll outputs → {OUT_DIR}")


if __name__ == "__main__":
    main()
