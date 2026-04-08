#!/usr/bin/env python3
"""
Stage 2 — Freeze Truth Architecture Contract

Formalizes the benchmark contract: what structural objects must a model
recover, and at what confidence level.

Defines:
  - canonical backbone axes (high confidence, shared across lines)
  - shift-excess axes (high confidence, shared shift above expectation)
  - line-skewed / context-dependent deviation (moderate confidence)
  - architecture_role per axis with confidence annotation

Run: pixi run python scripts/stage2_freeze_truth_architecture_contract.py
"""

from pathlib import Path

import pandas as pd

ATLAS_DIR  = Path("reports/stage2_truth_driven_bridge/master_atlas")
SCP542_DIR = Path("data/baselines/scp542")
OUT_DIR    = Path("reports/stage2_truth_driven_bridge/truth_architecture_contract")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Load frozen assets ──────────────────────────────────────────────────────
atlas     = pd.read_csv(ATLAS_DIR / "shared_target_master_atlas.tsv", sep="\t")
axis_mem  = pd.read_csv(ATLAS_DIR / "shared_target_axis_membership.tsv", sep="\t")
axis_sum_fine = pd.read_csv(ATLAS_DIR / "axis_summary_fine.tsv", sep="\t")
axis_sum_macro = pd.read_csv(ATLAS_DIR / "axis_summary_macro.tsv", sep="\t")
axis_consistency = pd.read_csv(ATLAS_DIR / "axis_crossline_consistency.tsv", sep="\t")

# ── Architecture role definitions ────────────────────────────────────────────
# These match the inference rules used in axis_summary
def infer_role(row):
    """Infer architecture role from grid/residual + crossline consistency.

    Rules (applied in order):
    1. If consistency is line_skewed → context_deviation (regardless of Q1)
    2. If Q1_max >= 0.5 in BOTH lines → canonical_backbone
    3. If Q1_max >= 0.5 in ONE line only → context_deviation (line-specific)
    4. If fraction_shift_excess >= 0.5 → shift_excess
    5. Otherwise → context_deviation
    """
    ax = row["fine_axis"]
    q1_38 = row.get("fraction_Q1_HCC38", 0)
    q1_1143 = row.get("fraction_Q1_HCC1143", 0)
    se = row.get("fraction_shift_excess", 0)

    # Check consistency class
    cons_rows = axis_consistency[axis_consistency["fine_axis"] == ax]
    cons_class = cons_rows["consistency_class"].values[0] if len(cons_rows) > 0 else "N/A"

    # Rule 1: line_skewed is always context deviation
    if cons_class == "line_skewed":
        return "context_deviation"

    # Rule 2: Q1 high in BOTH lines → backbone
    if q1_38 >= 0.5 and q1_1143 >= 0.5:
        return "canonical_backbone"

    # Rule 3: Q1 high in only one line → line-specific deviation
    if q1_38 >= 0.5 or q1_1143 >= 0.5:
        return "context_deviation"

    # Rule 4: shift_excess
    if se >= 0.5:
        return "shift_excess"

    return "context_deviation"

# ── Assign architecture_role to all axes ──────────────────────────────────
axis_sum_fine = axis_sum_fine.copy()
axis_sum_fine["architecture_role"] = axis_sum_fine.apply(infer_role, axis=1)

# ── Layer 1: Shared backbone (high confidence) ────────────────────────────────
# Definition: fraction_Q1 >= 0.5 in BOTH HCC38 and HCC1143
# AND consistency_class is "shared_dual_high" or "shared_shift_excess" or "shared_middle"
backbone_axes = axis_sum_fine[axis_sum_fine["architecture_role"] == "canonical_backbone"].copy()
backbone_axes = backbone_axes.sort_values(
    ["fraction_Q1_HCC38", "fraction_Q1_HCC1143"], ascending=False
)

# ── Layer 2: Shift-excess (high confidence) ────────────────────────────────
# Definition: fraction_shift_excess >= 0.5 in at least one line
shift_excess_axes = axis_sum_fine[axis_sum_fine["architecture_role"] == "shift_excess"].copy()

# ── Layer 3: Context deviation (moderate confidence) ────────────────────────
# Definition: line-skewed or heterogeneous axes
context_dev_axes = axis_sum_fine[axis_sum_fine["architecture_role"] == "context_deviation"].copy()
# Further classify line-skewed vs heterogeneous
line_skewed = axis_consistency[axis_consistency["consistency_class"] == "line_skewed"]["fine_axis"].tolist()
heterogeneous = axis_consistency[axis_consistency["consistency_class"] == "heterogeneous"]["fine_axis"].tolist()

# ── SCP542 evaluability ───────────────────────────────────────────────────
# Check W matrix coverage for each axis gene
w_h38_path = SCP542_DIR / "nmf_w_hcc38-breast.tsv"
bt549_path = SCP542_DIR / "nmf_w_bt549-breast.tsv"

scp542_evaluable = {}
if w_h38_path.exists():
    w_h38 = pd.read_csv(w_h38_path, sep="\t", index_col=0)
    w_genes = set(w_h38.index)
    for _, row in axis_sum_fine.iterrows():
        ax = row["fine_axis"]
        genes_in_axis = axis_mem[axis_mem["fine_axis"] == ax]["target_gene"].tolist()
        covered = sum(1 for g in genes_in_axis if g in w_genes)
        scp542_evaluable[ax] = covered / max(len(genes_in_axis), 1)

# ── Confidence annotation ──────────────────────────────────────────────────
def confidence_level(row):
    """Assign confidence annotation based on evidence quality.

    For this benchmark contract, the key objects models must recover are:
      - canonical_backbone axes (shared across both lines)
      - shift_excess axes

    Confidence levels reflect how robustly defined each object is:
      - high: 2+ genes OR (1 gene with Q1 in BOTH lines) + SCP542 coverage ≥50%
      - moderate: 1 gene with Q1 in both lines, SCP542 partial
      - provisional: line_skewed, or 1-gene backbone without SCP542 coverage
    """
    ax = row["fine_axis"]
    genes = axis_mem[axis_mem["fine_axis"] == ax]["target_gene"].tolist()
    n_genes = len(genes)
    scp_coverage = scp542_evaluable.get(ax, 0)
    arch = row["architecture_role"]

    # High: 2+ genes in backbone/shift_excess, with SCP542 coverage
    if n_genes >= 2 and arch in ("canonical_backbone", "shift_excess") and scp_coverage >= 0.5:
        return "high"
    # High: 1 gene backbone with Q1 in BOTH lines, SCP542 evaluable
    if (arch == "canonical_backbone" and n_genes == 1 and scp_coverage >= 0.5 and
            row.get("fraction_Q1_HCC38", 0) >= 0.5 and row.get("fraction_Q1_HCC1143", 0) >= 0.5):
        return "high"
    # Moderate: 1 gene in backbone or shift_excess, SCP542 evaluable
    if arch in ("canonical_backbone", "shift_excess") and scp_coverage >= 0.5:
        return "moderate"
    # Moderate: 2+ gene context_deviation with shared_middle consistency
    if arch == "context_deviation" and n_genes >= 2:
        return "moderate"
    return "provisional"

axis_sum_fine = axis_sum_fine.copy()
axis_sum_fine["confidence"] = axis_sum_fine.apply(confidence_level, axis=1)

# ── Helper: SCP542 note ─────────────────────────────────────────────────────
def _scp542_note(row, coverage, consistency_class):
    """Generate a note about SCP542 evaluability and what can/cannot be claimed."""
    arch = row["architecture_role"]
    if coverage >= 0.5:
        if arch == "canonical_backbone":
            return "broad/distributed placement — NOT 'single anchor program'"
        elif arch == "shift_excess":
            return "distributed basal placement — NOT single basal program match"
        return "SCP542 evaluable — distributed placement"
    elif arch == "canonical_backbone":
        return "SCP542 partial — backbone confirmed, basal placement not evaluable"
    elif arch == "shift_excess":
        return "SCP542 partial/N/A — shift_excess from perturbation data, basal explanation N/A"
    return "SCP542 N/A — context-dependence from perturbation data only"

# ── Build architecture contract table ─────────────────────────────────────
contract_rows = []
for _, row in axis_sum_fine.iterrows():
    ax = row["fine_axis"]
    genes = axis_mem[axis_mem["fine_axis"] == ax]["target_gene"].tolist()
    cons_row = axis_consistency[axis_consistency["fine_axis"] == ax]
    cons_class = cons_row["consistency_class"].values[0] if len(cons_row) > 0 else "N/A"
    scp_cov = scp542_evaluable.get(ax, 0)

    contract_rows.append({
        "fine_axis": ax,
        "macro_axis": row["macro_axis"],
        "architecture_role": row["architecture_role"],
        "confidence": row["confidence"],
        "n_genes": len(genes),
        "genes": ",".join(genes),
        "fraction_Q1_HCC38": round(row.get("fraction_Q1_HCC38", 0), 3),
        "fraction_Q1_HCC1143": round(row.get("fraction_Q1_HCC1143", 0), 3),
        "fraction_shift_excess": round(row.get("fraction_shift_excess", 0), 3),
        "scp542_coverage": round(scp_cov, 3),
        "scp542_evaluable": scp_cov >= 0.5,
        "consistency_class": cons_class,
        "scp542_role_note": _scp542_note(row, scp_cov, cons_class),
    })

contract = pd.DataFrame(contract_rows)

# Sort: backbone first, then shift_excess, then context_deviation; within role by n_genes desc
role_order = {"canonical_backbone": 0, "shift_excess": 1, "context_deviation": 2}
contract["role_sort"] = contract["architecture_role"].map(role_order)
contract = contract.sort_values(["role_sort", "n_genes"], ascending=[True, False]).reset_index(drop=True)
contract = contract.drop(columns=["role_sort"])

contract.to_csv(OUT_DIR / "truth_architecture_contract.tsv", sep="\t", index=False)

# ── Backbone detail table ─────────────────────────────────────────────────
bb_rows = []
for _, row in backbone_axes.iterrows():
    ax = row["fine_axis"]
    genes = axis_mem[axis_mem["fine_axis"] == ax]["target_gene"].tolist()
    bb_rows.append({
        "fine_axis": ax,
        "macro_axis": row["macro_axis"],
        "n_genes": len(genes),
        "genes": ",".join(genes),
        "fraction_Q1_HCC38": round(row.get("fraction_Q1_HCC38", 0), 3),
        "fraction_Q1_HCC1143": round(row.get("fraction_Q1_HCC1143", 0), 3),
        "mean_residual_HCC38": round(row.get("mean_residual_HCC38", 0), 6),
        "mean_residual_HCC1143": round(row.get("mean_residual_HCC1143", 0), 6),
        "scp542_coverage": round(scp542_evaluable.get(ax, 0), 3),
        "scp542_evaluable": scp542_evaluable.get(ax, 0) >= 0.5,
        "SCP542_role_note": _scp542_note(row, scp542_evaluable.get(ax, 0),
                                          axis_consistency[axis_consistency["fine_axis"]==ax]["consistency_class"].values[0] if len(axis_consistency[axis_consistency["fine_axis"]==ax]) > 0 else "N/A"),
    })

backbone_detail = pd.DataFrame(bb_rows)
backbone_detail.to_csv(OUT_DIR / "truth_architecture_backbone_detail.tsv", sep="\t", index=False)

# ── Summary statistics ──────────────────────────────────────────────────────
print("="*70)
print("TRUTH ARCHITECTURE CONTRACT — Freeze")
print("="*70)
print(f"\nTotal fine axes: {len(contract)}")
print(f"\nArchitecture role distribution:")
print(contract["architecture_role"].value_counts())
print(f"\nConfidence distribution:")
print(contract["confidence"].value_counts())
print(f"\nSCP542 evaluability:")
print(f"  Evaluable (>=50% coverage): {contract['scp542_evaluable'].sum()}/{len(contract)}")
print(f"  Not evaluable: {(~contract['scp542_evaluable']).sum()}/{len(contract)}")

print(f"\nCanonical backbone axes (n={len(backbone_detail)}):")
for _, r in backbone_detail.iterrows():
    ev = "✓ SCP542" if r["scp542_evaluable"] else "✗ SCP542 N/A"
    print(f"  [{r['n_genes']} genes] {r['fine_axis']:45s} "
          f"Q1_H38={r['fraction_Q1_HCC38']:.2f} Q1_H1143={r['fraction_Q1_HCC1143']:.2f} {ev}")

print(f"\nShift-excess axes (n={len(shift_excess_axes)}):")
for _, r in shift_excess_axes.iterrows():
    ax = r["fine_axis"]
    genes = axis_mem[axis_mem["fine_axis"] == ax]["target_gene"].tolist()
    ev = "✓" if scp542_evaluable.get(ax, 0) >= 0.5 else "✗"
    print(f"  {ax:45s} se_frac={r['fraction_shift_excess']:.2f} genes={genes}")

print(f"\nContext deviation axes (n={len(context_dev_axes)}):")
for _, r in context_dev_axes.iterrows():
    ax = r["fine_axis"]
    cons = axis_consistency[axis_consistency["fine_axis"] == ax]["consistency_class"].values
    cons_str = cons[0] if len(cons) > 0 else "N/A"
    ev = "✓" if scp542_evaluable.get(ax, 0) >= 0.5 else "✗"
    print(f"  {ax:45s} consistency={cons_str:25s} ev={ev}")

print(f"\nContract saved → {OUT_DIR}")
print(f"  truth_architecture_contract.tsv")
print(f"  truth_architecture_backbone_detail.tsv")


