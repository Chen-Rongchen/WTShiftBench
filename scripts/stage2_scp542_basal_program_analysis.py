#!/usr/bin/env python3
"""
Stage 2 — SCP542 Basal Program Calibration Layer

Program-first, explanation-first approach.

Questions:
  Q1: Which bridge axes show high basal variation in HCC38 NMF programs?
  Q2: Which axes are closer to viability/dependency proxy in basal space?
  Q3: Can line-skewed axes be explained by basal heterogeneity?

Run: pixi run python scripts/stage2_scp542_basal_program_analysis.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

# ── paths ──────────────────────────────────────────────────────────────────
SCP542_DIR = Path("data/baselines/scp542")
ATLAS_DIR  = Path("reports/stage2_truth_driven_bridge/master_atlas")
BRIDGE_DIR = Path("data/processed/stage2_truth_driven_bridge")
OUT_DIR    = Path("reports/stage2_truth_driven_bridge/scp542_calibration")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Load frozen assets ─────────────────────────────────────────────────────
atlas = pd.read_csv(ATLAS_DIR / "shared_target_master_atlas.tsv", sep="\t")
axis_members = pd.read_csv(ATLAS_DIR / "shared_target_axis_membership.tsv", sep="\t")

# SCP542 W matrix (HCC38)
w_h38 = pd.read_csv(SCP542_DIR / "nmf_w_hcc38-breast.tsv", sep="\t", index_col=0)
# SCP542 H matrix (HCC38): cells × programs
h_h38 = pd.read_csv(SCP542_DIR / "nmf_h_hcc38-breast.tsv", sep="\t", index_col=0)
# SCP542 program gene sets
prog_sig = pd.read_csv(SCP542_DIR / "nmf_programs_sig_ccle.tsv", sep="\t",
                       header=None, names=["program_id", "genes"])
prog_sig["gene_list"] = prog_sig["genes"].apply(
    lambda x: [g.strip() for g in x.split(",")] if pd.notna(x) else []
)

# ── Coverage check ─────────────────────────────────────────────────────────
our_genes = set(atlas["target_gene"])
w_h38_genes = set(w_h38.index)
covered = our_genes & w_h38_genes
missing = our_genes - w_h38_genes
print(f"Atlas genes: {len(our_genes)} | W matrix coverage: {len(covered)} | Missing: {len(missing)}")
print(f"Missing genes: {sorted(missing)}")

# ══════════════════════════════════════════════════════════════════════════════
# Q1: Which axes have highest basal program loadings in HCC38?
# ══════════════════════════════════════════════════════════════════════════════

def axis_program_stats(axis_genes, w_mat):
    """For a set of genes, compute per-program loading statistics."""
    common = [g for g in axis_genes if g in w_mat.index]
    if not common:
        return pd.DataFrame()
    sub = w_mat.loc[common].abs()
    stats = pd.DataFrame({
        "mean_abs_loading": sub.mean(axis=0),
        "max_abs_loading":  sub.max(axis=0),
        "std_abs_loading": sub.std(axis=0),
    })
    return stats

q1_rows = []
for axis_name, grp in axis_members.groupby("fine_axis"):
    genes = grp["target_gene"].tolist()
    stats = axis_program_stats(genes, w_h38)
    if stats.empty:
        continue
    peak = stats["mean_abs_loading"].idxmax()
    q1_rows.append({
        "fine_axis": axis_name,
        "n_genes": len(genes),
        "n_genes_in_w": len([g for g in genes if g in w_h38_genes]),
        "peak_program": peak,
        "peak_mean_abs_loading": round(stats.loc[peak, "mean_abs_loading"], 6),
        "basal_heterogeneity": round(stats.loc[peak, "std_abs_loading"], 6),
        "n_programs_active": (stats["mean_abs_loading"] > 0).sum(),
    })

q1_df = pd.DataFrame(q1_rows).sort_values(
    ["n_genes_in_w", "peak_mean_abs_loading"], ascending=[False, False]
)
q1_df.to_csv(OUT_DIR / "q1_axis_basal_loading.tsv", sep="\t", index=False)

print("\n" + "="*70)
print("Q1: Axis Basal Loading (HCC38 NMF, 30 programs)")
print("="*70)
print(q1_df.to_string(index=False))

# ══════════════════════════════════════════════════════════════════════════════
# Q2: Type A vs Type B genes in basal program space — biological interpretation
# ══════════════════════════════════════════════════════════════════════════════

type_a_genes = atlas[atlas["candidate_type"].str.startswith("A:", na=False)]["target_gene"].tolist()
type_b_genes = atlas[atlas["candidate_type"].str.startswith("B:", na=False)]["target_gene"].tolist()

print("\n" + "="*70)
print("Q2: Type A / Type B Basal Program Placement")
print("="*70)

q2_results = {}
for label, genes in [("Type_A", type_a_genes), ("Type_B", type_b_genes)]:
    present = [g for g in genes if g in w_h38.index]
    if not present:
        print(f"\n{label}: no genes in W matrix")
        continue
    sub = w_h38.loc[present].abs()
    mean_loading = sub.mean(axis=0)
    top5 = mean_loading.nlargest(5)
    # Check which SCP542 global programs these overlap with
    scp542_hits = {}
    for g in present:
        hits = prog_sig[prog_sig["gene_list"].apply(lambda gl: g in gl)]
        scp542_hits[g] = list(hits["program_id"])
    q2_results[label] = {
        "genes": present,
        "top5_programs": top5,
        "scp542_hits": scp542_hits,
        "mean_loading": mean_loading,
    }
    print(f"\n{label} ({len(present)} genes in W):")
    for prog, val in top5.items():
        # Program format: "HCC38_BREAST_8.1" → extract "8.1"
        prog_id = "_".join(prog.split("_")[2:])  # "8.1"
        hits_in_prog = [g for g, ps in scp542_hits.items() if any(prog_id in p for p in ps)]
        print(f"  {prog}: {val:.5f} | SCP542 hits: {hits_in_prog[:5]}")

# Save Type A/B program loading table
for label, res in q2_results.items():
    rows = []
    for g in res["genes"]:
        if g in w_h38.index:
            row = {"gene": g}
            row.update({p: round(w_h38.loc[g, p], 6) for p in w_h38.columns})
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / f"q2_{label.lower()}_program_loading.tsv", sep="\t", index=False)

# ══════════════════════════════════════════════════════════════════════════════
# Q3: Line-skewed axes — basal heterogeneity check
# ══════════════════════════════════════════════════════════════════════════════

line_skewed = ["proteostasis / chaperone", "cell cycle / replication",
               "NF-κB / MAPK signaling", "growth / proliferation"]

print("\n" + "="*70)
print("Q3: Line-Skewed Axes — Basal Heterogeneity")
print("="*70)

q3_rows = []
for axis_name in line_skewed:
    grp = axis_members[axis_members["fine_axis"] == axis_name]
    if grp.empty:
        continue
    genes = grp["target_gene"].tolist()
    present = [g for g in genes if g in w_h38.index]
    stats = axis_program_stats(genes, w_h38)
    if stats.empty:
        continue
    # Check basal variability across programs for this axis
    mean_per_program = stats["mean_abs_loading"]
    skew_score = mean_per_program.max() / (mean_per_program.mean() + 1e-9)
    peak_prog = mean_per_program.idxmax()
    print(f"\n{axis_name} ({len(genes)} genes, {len(present)} in W):")
    print(f"  Peak program: {peak_prog} (mean |loading| = {mean_per_program.max():.5f})")
    print(f"  Skew score (max/mean): {skew_score:.2f}")
    print(f"  Programs with >50% peak loading: {(mean_per_program > 0.5 * mean_per_program.max()).sum()}")
    q3_rows.append({
        "fine_axis": axis_name,
        "peak_program": peak_prog,
        "skew_score": round(skew_score, 3),
        "n_programs_50pct": int((mean_per_program > 0.5 * mean_per_program.max()).sum()),
        "peak_mean_loading": round(mean_per_program.max(), 6),
    })

q3_df = pd.DataFrame(q3_rows)
if not q3_df.empty:
    q3_df.to_csv(OUT_DIR / "q3_line_skewed_basal.tsv", sep="\t", index=False)

# ══════════════════════════════════════════════════════════════════════════════
# Cross-line calibration: HCC38 vs BT549 (TNBC proxy)
# ══════════════════════════════════════════════════════════════════════════════
bt549_w_path = SCP542_DIR / "nmf_w_bt549-breast.tsv"
if bt549_w_path.exists():
    w_bt = pd.read_csv(bt549_w_path, sep="\t", index_col=0)
    common_genes_bt = list(covered & set(w_bt.index))
    if len(common_genes_bt) > 10:
        h38_sub = w_h38.loc[common_genes_bt].abs()
        bt_sub  = w_bt.loc[common_genes_bt].abs()
        gene_corrs = []
        for g in common_genes_bt:
            corr = pd.Series(h38_sub.loc[g].values).corr(pd.Series(bt_sub.loc[g].values))
            gene_corrs.append({"gene": g, "h38_bt549_loading_corr": corr})
        corr_df = pd.DataFrame(gene_corrs)
        corr_df = corr_df.merge(
            atlas[["target_gene", "candidate_type", "priority_tier", "residual_mean"]],
            left_on="gene", right_on="target_gene", how="left"
        )
        corr_df.to_csv(OUT_DIR / "h38_bt549_loading_corr.tsv", sep="\t", index=False)
        vals = [x["h38_bt549_loading_corr"] for x in gene_corrs]
        print("\n" + "="*70)
        print("Cross-line (HCC38 vs BT549 TNBC proxy) Loading Correlation")
        print("="*70)
        print(f"  N genes: {len(vals)}")
        print(f"  Mean: {np.nanmean(vals):.3f}, Median: {np.nanmedian(vals):.3f}")
        print(f"  Type A mean: {corr_df[corr_df['candidate_type'].str.startswith('A:', na=False)]['h38_bt549_loading_corr'].mean():.3f}")
        print(f"  Type B mean: {corr_df[corr_df['candidate_type'].str.startswith('B:', na=False)]['h38_bt549_loading_corr'].mean():.3f}")

# ══════════════════════════════════════════════════════════════════════════════
# Save our 47-gene × 30-program loading matrix (28 covered genes)
# ══════════════════════════════════════════════════════════════════════════════
our_gene_loading = w_h38.loc[[g for g in atlas["target_gene"] if g in w_h38.index]]
our_gene_loading.round(6).to_csv(OUT_DIR / "our_genes_hcc38_program_loading.tsv", sep="\t")
print(f"\nSaved gene×program loading: {our_gene_loading.shape}")

print(f"\nAll outputs → {OUT_DIR}")
