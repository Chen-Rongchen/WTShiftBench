#!/usr/bin/env python3
"""P2 MVP: Build reserve figure — PCA centroid-arrow displacement visualization.

Follows the frozen spec in docs/reserve_figure_pca_displacement_spec.md.
Output: reports/extended_data_candidates/pca_displacement/
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
from scipy import sparse

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# ─── Paths ───────────────────────────────────────────────────────────────────
ROOT = repo_root()

HCC38_PATH = ROOT / "data/processed/stage2_hcc_gears_formal/HCC38.h5ad"
HCC1143_PATH = ROOT / "data/processed/stage2_hcc_gears_formal/HCC1143.h5ad"
K562_7D_PATH = ROOT / "data/processed/stage2_gse90063/dixit_2016_k562_tf_7d_gse90063.h5ad"
K562_13D_PATH = ROOT / "data/processed/stage2_gse90063/dixit_2016_k562_tf_13d_gse90063.h5ad"

OUT_DIR = ROOT / "reports/extended_data_candidates/pca_displacement"
QC_DIR = OUT_DIR / "qc"

# ─── Parameters ──────────────────────────────────────────────────────────────
MIN_PERTURBED_CELLS = 20
MIN_CONTROL_CELLS = 50
N_PCA_COMPONENTS = 50
N_HIGHLIGHT = 2  # MVP: 2 labels per panel
HIGHLIGHT_COLOR = COLORS["accent_red"]
ARROW_COLOR_ALL = "#BBBBBB"
BG_COLOR = "#F5F5F5"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_and_verify_hcc(path: Path) -> ad.AnnData:
    """Load HCC h5ad and verify it is log-normalized."""
    adata = ad.read_h5ad(path)
    # Verify log-normalized: max should be < 20
    sample = adata.X[:1000].toarray() if sparse.issparse(adata.X) else adata.X[:1000]
    assert sample.max() < 20, f"HCC file {path} does not appear log-normalized (max={sample.max():.2f})"
    return adata


def load_and_verify_k562(path: Path) -> ad.AnnData:
    """Load K562 h5ad and verify it is raw counts."""
    adata = ad.read_h5ad(path)
    sample = adata.X[:1000].toarray() if sparse.issparse(adata.X) else adata.X[:1000]
    # Raw counts should have max > 100
    assert sample.max() > 100, f"K562 file {path} does not appear to be raw counts (max={sample.max():.2f})"
    return adata


def compute_mean_shift(adata: ad.AnnData, target: str, evaluable_genes: list[str] | None = None) -> float:
    """Compute absolute mean perturbation shift for a target."""
    obs = adata.obs
    control_mask = obs["is_control"].astype(bool).to_numpy()
    target_mask = (~obs["is_control"].astype(bool)) & obs["target_gene"].eq(target).to_numpy()

    if not target_mask.any():
        return 0.0

    X = adata.X
    gene_idx = None
    if evaluable_genes is not None:
        gene_idx = adata.var_names.get_indexer(evaluable_genes)
        gene_idx = gene_idx[gene_idx >= 0]
        if len(gene_idx) == 0:
            gene_idx = None

    control_mask_np = np.asarray(control_mask)
    target_mask_np = np.asarray(target_mask)
    if sparse.issparse(X):
        ctrl_mean = np.asarray(X[control_mask_np].mean(axis=0)).ravel()
        pert_mean = np.asarray(X[target_mask_np].mean(axis=0)).ravel()
    else:
        ctrl_mean = np.asarray(X[control_mask_np].mean(axis=0)).ravel()
        pert_mean = np.asarray(X[target_mask_np].mean(axis=0)).ravel()

    if gene_idx is not None:
        ctrl_mean = ctrl_mean[gene_idx]
        pert_mean = pert_mean[gene_idx]

    delta = pert_mean - ctrl_mean
    return float(np.mean(np.abs(delta)))


def fit_pca(adata: ad.AnnData, n_comps: int = N_PCA_COMPONENTS) -> tuple[np.ndarray, np.ndarray]:
    """Fit PCA on adata.X and return (cell_embeddings, explained_variance_ratio)."""
    adata_copy = adata.copy()
    sc.pp.pca(adata_copy, n_comps=n_comps, zero_center=True, svd_solver="arpack")
    embeddings = adata_copy.obsm["X_pca"]
    evr = adata_copy.uns["pca"]["variance_ratio"]
    return embeddings, evr


def compute_centroids(adata: ad.AnnData, embeddings: np.ndarray, target: str) -> dict | None:
    """Compute control and perturbed centroids in PC1/PC2 for a target."""
    obs = adata.obs
    control_mask = obs["is_control"].astype(bool).to_numpy()
    target_mask = (~obs["is_control"].astype(bool)) & obs["target_gene"].eq(target).to_numpy()

    n_ctrl = int(control_mask.sum())
    n_pert = int(target_mask.sum())

    if n_pert < MIN_PERTURBED_CELLS or n_ctrl < MIN_CONTROL_CELLS:
        return None

    ctrl_centroid = embeddings[control_mask, :2].mean(axis=0)
    pert_centroid = embeddings[target_mask, :2].mean(axis=0)

    return {
        "target": target,
        "ctrl_x": float(ctrl_centroid[0]),
        "ctrl_y": float(ctrl_centroid[1]),
        "pert_x": float(pert_centroid[0]),
        "pert_y": float(pert_centroid[1]),
        "n_ctrl": n_ctrl,
        "n_pert": n_pert,
    }


def select_highlighted_targets_hcc(
    adata: ad.AnnData,
    all_targets: list[str],
) -> list[str]:
    """Select top 2 targets by mean shift. Retain PFDN5 if available and passes threshold."""
    shifts = []
    for t in all_targets:
        shift = compute_mean_shift(adata, t)
        shifts.append((t, shift))

    shifts_sorted = sorted(shifts, key=lambda x: x[1], reverse=True)

    highlighted = []
    # Try to include PFDN5 if available and has enough cells
    has_pfdn5 = False
    for t, _ in shifts_sorted:
        if t.upper() == "PFDN5":
            n_pert = int((~adata.obs["is_control"].astype(bool) & adata.obs["target_gene"].eq(t)).sum())
            n_ctrl = int(adata.obs["is_control"].astype(bool).sum())
            if n_pert >= MIN_PERTURBED_CELLS and n_ctrl >= MIN_CONTROL_CELLS:
                highlighted.append(t)
                has_pfdn5 = True
            break

    # Fill remaining slots with top-ranked by shift
    for t, _ in shifts_sorted:
        if t in highlighted:
            continue
        n_pert = int((~adata.obs["is_control"].astype(bool) & adata.obs["target_gene"].eq(t)).sum())
        n_ctrl = int(adata.obs["is_control"].astype(bool).sum())
        if n_pert >= MIN_PERTURBED_CELLS and n_ctrl >= MIN_CONTROL_CELLS:
            highlighted.append(t)
        if len(highlighted) >= N_HIGHLIGHT:
            break

    return highlighted[:N_HIGHLIGHT]


def select_highlighted_targets_k562(
    adata_7d: ad.AnnData,
    adata_13d: ad.AnnData,
) -> list[str]:
    """Select top 2 targets present in both 7d and 13d, ranked by average shift."""
    # Get targets present in both with sufficient cells
    targets_7d = set(adata_7d.obs.loc[~adata_7d.obs["is_control"].astype(bool), "target_gene"].dropna().unique())
    targets_13d = set(adata_13d.obs.loc[~adata_13d.obs["is_control"].astype(bool), "target_gene"].dropna().unique())

    common = sorted(targets_7d & targets_13d)

    # Get evaluable gene intersection for fair comparison
    common_genes = sorted(set(adata_7d.var_names) & set(adata_13d.var_names))

    shifts = []
    for t in common:
        shift_7d = compute_mean_shift(adata_7d, t, common_genes)
        shift_13d = compute_mean_shift(adata_13d, t, common_genes)
        avg_shift = (shift_7d + shift_13d) / 2

        # Check cell counts
        n_pert_7d = int((~adata_7d.obs["is_control"].astype(bool) & adata_7d.obs["target_gene"].eq(t)).sum())
        n_pert_13d = int((~adata_13d.obs["is_control"].astype(bool) & adata_13d.obs["target_gene"].eq(t)).sum())
        n_ctrl_7d = int(adata_7d.obs["is_control"].astype(bool).sum())
        n_ctrl_13d = int(adata_13d.obs["is_control"].astype(bool).sum())

        if (n_pert_7d >= MIN_PERTURBED_CELLS and n_ctrl_7d >= MIN_CONTROL_CELLS and
            n_pert_13d >= MIN_PERTURBED_CELLS and n_ctrl_13d >= MIN_CONTROL_CELLS):
            shifts.append((t, avg_shift))

    shifts_sorted = sorted(shifts, key=lambda x: x[1], reverse=True)
    return [t for t, _ in shifts_sorted[:N_HIGHLIGHT]]


def compute_pc_depth_correlation(adata: ad.AnnData, embeddings: np.ndarray) -> dict[str, float]:
    """Compute correlation between PC1/PC2 and sequencing depth metrics."""
    ncount = np.asarray(adata.X.sum(axis=1)).ravel()
    nfeature = np.asarray((adata.X > 0).sum(axis=1)).ravel()

    results = {}
    for pc_name, pc_idx in [("PC1", 0), ("PC2", 1)]:
        pc_vals = embeddings[:, pc_idx]
        results[f"cor({pc_name}, log10_nCount)"] = float(np.corrcoef(pc_vals, np.log10(ncount + 1))[0, 1])
        results[f"cor({pc_name}, nFeature)"] = float(np.corrcoef(pc_vals, nfeature)[0, 1])
    return results


def draw_panel(
    ax: plt.Axes,
    adata: ad.AnnData,
    embeddings: np.ndarray,
    panel_label: str,
    title: str,
    highlighted_targets: list[str],
) -> list[dict]:
    """Draw a single panel with centroid arrows."""
    # Background: all cells as very light scatter
    ax.scatter(embeddings[:, 0], embeddings[:, 1], c=BG_COLOR, s=1, alpha=0.3, rasterized=True)

    # Get all qualifying targets
    all_targets = sorted(
        adata.obs.loc[~adata.obs["is_control"].astype(bool), "target_gene"].dropna().unique()
    )

    arrows = []
    for target in all_targets:
        cent = compute_centroids(adata, embeddings, target)
        if cent is None:
            continue
        arrows.append(cent)

        is_highlight = target in highlighted_targets
        color = HIGHLIGHT_COLOR if is_highlight else ARROW_COLOR_ALL
        alpha = 0.9 if is_highlight else 0.4
        lw = 1.2 if is_highlight else 0.5

        dx = cent["pert_x"] - cent["ctrl_x"]
        dy = cent["pert_y"] - cent["ctrl_y"]

        ax.annotate(
            "",
            xy=(cent["pert_x"], cent["pert_y"]),
            xytext=(cent["ctrl_x"], cent["ctrl_y"]),
            arrowprops=dict(arrowstyle="->", color=color, lw=lw, alpha=alpha),
        )

        # Control centroid: open circle
        ax.scatter(cent["ctrl_x"], cent["ctrl_y"], c="white", edgecolors=color, s=15 if is_highlight else 6, linewidths=0.8 if is_highlight else 0.4, zorder=3)
        # Perturbation centroid: filled circle
        ax.scatter(cent["pert_x"], cent["pert_y"], c=color, s=20 if is_highlight else 8, edgecolors="white", linewidths=0.5, zorder=3)

        if is_highlight:
            # Offset label slightly
            ax.text(cent["pert_x"] + dx * 0.15, cent["pert_y"] + dy * 0.15, target, fontsize=6, color=color, fontweight="bold")

    ax.set_title(title, loc="left", fontsize=7.5)
    ax.set_xlabel("PC1", fontsize=6.5)
    ax.set_ylabel("PC2", fontsize=6.5)
    clean_axes(ax)
    add_panel_label(ax, panel_label)
    ax.set_aspect("equal", adjustable="box")

    return arrows


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("P2 MVP: Reserve Figure PCA Centroid-Arrow Displacement")
    print("=" * 60)

    ensure_dir(OUT_DIR)
    ensure_dir(QC_DIR)
    apply_manuscript_style()

    # ─── Step 1-4: HCC ───────────────────────────────────────────────────────
    print("\n[Step 1-2] Loading HCC38 / HCC1143...")
    hcc38 = load_and_verify_hcc(HCC38_PATH)
    hcc1143 = load_and_verify_hcc(HCC1143_PATH)

    print(f"  HCC38: {hcc38.shape}")
    print(f"  HCC1143: {hcc1143.shape}")

    print("\n[Step 3-4] Fitting context-specific PCA for HCC...")
    emb_hcc38, evr_hcc38 = fit_pca(hcc38)
    emb_hcc1143, evr_hcc1143 = fit_pca(hcc1143)
    print(f"  HCC38 PCA: top 2 EV = {evr_hcc38[:2].sum():.3f}")
    print(f"  HCC1143 PCA: top 2 EV = {evr_hcc1143[:2].sum():.3f}")

    # ─── Step 5-11: K562 ─────────────────────────────────────────────────────
    print("\n[Step 5] Loading K562 7d / 13d...")
    k562_7d = load_and_verify_k562(K562_7D_PATH)
    k562_13d = load_and_verify_k562(K562_13D_PATH)
    print(f"  K562 7d: {k562_7d.shape}")
    print(f"  K562 13d: {k562_13d.shape}")

    print("\n[Step 6-7] Gene intersection...")
    genes_7d = set(k562_7d.var_names)
    genes_13d = set(k562_13d.var_names)
    genes_intersection = sorted(genes_7d & genes_13d)
    n_genes_7d_raw = len(genes_7d)
    n_genes_13d_raw = len(genes_13d)
    n_genes_intersection = len(genes_intersection)
    print(f"  7d raw genes: {n_genes_7d_raw}")
    print(f"  13d raw genes: {n_genes_13d_raw}")
    print(f"  Intersection: {n_genes_intersection}")

    k562_7d = k562_7d[:, genes_intersection].copy()
    k562_13d = k562_13d[:, genes_intersection].copy()

    print("\n[Step 8] normalize_total(1e4) + log1p for K562...")
    sc.pp.normalize_total(k562_7d, target_sum=1e4)
    sc.pp.log1p(k562_7d)
    sc.pp.normalize_total(k562_13d, target_sum=1e4)
    sc.pp.log1p(k562_13d)

    print("\n[Step 9-10] Pool 7d + 13d and fit shared PCA...")
    k562_pooled = ad.concat([k562_7d, k562_13d], axis=0, merge="same")
    emb_pooled, evr_pooled = fit_pca(k562_pooled)
    print(f"  Pooled PCA: top 2 EV = {evr_pooled[:2].sum():.3f}")

    print("\n[Step 11] Project 7d and 13d into shared basis...")
    n_7d = k562_7d.n_obs
    emb_7d = emb_pooled[:n_7d]
    emb_13d = emb_pooled[n_7d:]

    # ─── Step 12: Select highlighted targets ─────────────────────────────────
    print("\n[Step 12] Selecting highlighted targets...")
    hcc38_targets = sorted(hcc38.obs.loc[~hcc38.obs["is_control"].astype(bool), "target_gene"].dropna().unique())
    hcc1143_targets = sorted(hcc1143.obs.loc[~hcc1143.obs["is_control"].astype(bool), "target_gene"].dropna().unique())

    hl_hcc38 = select_highlighted_targets_hcc(hcc38, hcc38_targets)
    hl_hcc1143 = select_highlighted_targets_hcc(hcc1143, hcc1143_targets)
    hl_k562 = select_highlighted_targets_k562(k562_7d, k562_13d)

    print(f"  HCC38 highlights: {hl_hcc38}")
    print(f"  HCC1143 highlights: {hl_hcc1143}")
    print(f"  K562 highlights: {hl_k562}")

    # ─── Step 13: PC-depth correlation ────────────────────────────────────────
    print("\n[Step 13] Computing PC-depth correlations...")
    depth_corr_records = []

    for label, adata, emb in [
        ("HCC38", hcc38, emb_hcc38),
        ("HCC1143", hcc1143, emb_hcc1143),
        ("K562_7d", k562_7d, emb_7d),
        ("K562_13d", k562_13d, emb_13d),
    ]:
        corr = compute_pc_depth_correlation(adata, emb)
        corr["context"] = label
        depth_corr_records.append(corr)
        print(f"  {label}: PC1-nCount r={corr['cor(PC1, log10_nCount)']:.3f}, PC2-nCount r={corr['cor(PC2, log10_nCount)']:.3f}")

    depth_corr_df = pd.DataFrame(depth_corr_records)
    depth_corr_path = write_tsv(depth_corr_df, QC_DIR / "pca_depth_correlation.tsv")
    print(f"  Written: {depth_corr_path}")

    # ─── Step 14: Draw figure ────────────────────────────────────────────────
    print("\n[Step 14] Drawing 2x2 figure...")
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 7.0))
    fig.suptitle("Low-dimensional geometric visualization of perturbation displacement", fontsize=9, y=0.98)

    arrows_hcc38 = draw_panel(axes[0, 0], hcc38, emb_hcc38, "a", "HCC38", hl_hcc38)
    arrows_hcc1143 = draw_panel(axes[0, 1], hcc1143, emb_hcc1143, "b", "HCC1143", hl_hcc1143)
    arrows_k562_7d = draw_panel(axes[1, 0], k562_7d, emb_7d, "c", "K562 7d", hl_k562)
    arrows_k562_13d = draw_panel(axes[1, 1], k562_13d, emb_13d, "d", "K562 13d", hl_k562)

    # Add group headers
    fig.text(0.25, 0.92, "Primary contexts", ha="center", fontsize=8, fontweight="bold", color="#555555")
    fig.text(0.75, 0.92, "Supplementary temporal panel", ha="center", fontsize=8, fontweight="bold", color="#555555")

    plt.tight_layout(rect=[0, 0, 1, 0.91])

    png_path = OUT_DIR / "extended_data_pca_displacement.png"
    pdf_path = OUT_DIR / "extended_data_pca_displacement.pdf"
    save_figure(fig, png_path, pdf_path)
    print(f"  Written: {png_path}")
    print(f"  Written: {pdf_path}")

    # ─── Step 15: Export source data and QC ──────────────────────────────────
    print("\n[Step 15] Exporting source data and QC...")

    # Source data: all arrows
    all_arrows = []
    for panel_id, panel_title, arrows_list in [
        ("a", "HCC38", arrows_hcc38),
        ("b", "HCC1143", arrows_hcc1143),
        ("c", "K562_7d", arrows_k562_7d),
        ("d", "K562_13d", arrows_k562_13d),
    ]:
        for a in arrows_list:
            all_arrows.append({
                "panel": panel_id,
                "panel_title": panel_title,
                "target": a["target"],
                "ctrl_x": a["ctrl_x"],
                "ctrl_y": a["ctrl_y"],
                "pert_x": a["pert_x"],
                "pert_y": a["pert_y"],
                "n_ctrl": a["n_ctrl"],
                "n_pert": a["n_pert"],
                "is_highlighted": a["target"] in (hl_hcc38 if panel_id == "a" else hl_hcc1143 if panel_id == "b" else hl_k562),
            })

    source_df = pd.DataFrame(all_arrows)
    source_path = write_tsv(source_df, OUT_DIR / "extended_data_pca_displacement_source_data.tsv")
    print(f"  Written: {source_path}")

    # Target cell counts
    count_records = []
    for label, adata in [("HCC38", hcc38), ("HCC1143", hcc1143), ("K562_7d", k562_7d), ("K562_13d", k562_13d)]:
        n_ctrl = int(adata.obs["is_control"].astype(bool).sum())
        for t in sorted(adata.obs.loc[~adata.obs["is_control"].astype(bool), "target_gene"].dropna().unique()):
            n_pert = int((~adata.obs["is_control"].astype(bool) & adata.obs["target_gene"].eq(t)).sum())
            count_records.append({"context": label, "target": t, "n_ctrl": n_ctrl, "n_pert": n_pert})

    counts_df = pd.DataFrame(count_records)
    counts_path = write_tsv(counts_df, QC_DIR / "target_cell_counts.tsv")
    print(f"  Written: {counts_path}")

    # K562 cell counts
    k562_counts = pd.DataFrame([
        {"dataset": "K562_7d", "n_cells": k562_7d.n_obs, "n_genes": k562_7d.n_vars},
        {"dataset": "K562_13d", "n_cells": k562_13d.n_obs, "n_genes": k562_13d.n_vars},
    ])
    k562_counts_path = write_tsv(k562_counts, QC_DIR / "k562_cell_counts_7d_13d.tsv")
    print(f"  Written: {k562_counts_path}")

    # PCA basis provenance
    provenance = {
        "n_genes_7d_raw": n_genes_7d_raw,
        "n_genes_13d_raw": n_genes_13d_raw,
        "n_genes_intersection": n_genes_intersection,
        "k562_cell_count_7d": int(k562_7d.n_obs),
        "k562_cell_count_13d": int(k562_13d.n_obs),
        "cell_count_ratio": round(min(k562_7d.n_obs, k562_13d.n_obs) / max(k562_7d.n_obs, k562_13d.n_obs), 3),
        "balanced_subsampling": False,
        "hcc38_top2_evr": round(float(evr_hcc38[:2].sum()), 4),
        "hcc1143_top2_evr": round(float(evr_hcc1143[:2].sum()), 4),
        "k562_pooled_top2_evr": round(float(evr_pooled[:2].sum()), 4),
        "hcc38_highlighted": hl_hcc38,
        "hcc1143_highlighted": hl_hcc1143,
        "k562_highlighted": hl_k562,
        "min_perturbed_cells": MIN_PERTURBED_CELLS,
        "min_control_cells": MIN_CONTROL_CELLS,
    }
    prov_path = QC_DIR / "pca_basis_provenance.json"
    prov_path.write_text(json.dumps(provenance, indent=2))
    print(f"  Written: {prov_path}")

    # Caption
    depth_warning = ""
    max_depth_r = max(abs(depth_corr_df["cor(PC1, log10_nCount)"]).max(), abs(depth_corr_df["cor(PC2, log10_nCount)"]).max())
    if max_depth_r > 0.5:
        depth_warning = (
            " PC axes showed partial correlation with sequencing-depth-related covariates; "
            "these panels are therefore used only as low-dimensional geometric visualization."
        )

    caption = f"""Extended Data Fig. X (Reserve). Low-dimensional geometric visualization of perturbation displacement across primary and supplementary contexts.

a,b, Primary HCC contexts (HCC38 and HCC1143). c,d, Supplementary temporal K562 panel (7d and 13d). Within each panel, low-dimensional coordinates are shown for the indicated context, and each arrow connects the centroid of matched control cells to the centroid of perturbed cells for one target. Light gray arrows show all displayed perturbations, whereas labeled arrows highlight a small set of representative targets selected by pre-specified perturbation-shift ranking and, in the HCC panels, anchored to benchmark-relevant exemplars where appropriate. HCC38 and HCC1143 were visualized in context-specific PCA bases, whereas K562 7d and 13d were projected into a shared K562 PCA basis fitted on the pooled set of both time points. These panels provide geometric intuition for perturbation displacement and do not replace the pre-specified perturbation-shift metric used for benchmark adjudication.{depth_warning}
"""

    caption_path = OUT_DIR / "extended_data_pca_displacement_caption.md"
    caption_path.write_text(caption)
    print(f"  Written: {caption_path}")

    # Summary
    print("\n" + "=" * 60)
    print("P2 MVP COMPLETE")
    print("=" * 60)
    print(f"Output dir: {OUT_DIR}")
    print(f"  Figure: {png_path}")
    print(f"  Source data: {source_path}")
    print(f"  Caption: {caption_path}")
    print(f"  QC dir: {QC_DIR}")
    print(f"\nArrows drawn:")
    print(f"  HCC38: {len(arrows_hcc38)} targets")
    print(f"  HCC1143: {len(arrows_hcc1143)} targets")
    print(f"  K562 7d: {len(arrows_k562_7d)} targets")
    print(f"  K562 13d: {len(arrows_k562_13d)} targets")
    print(f"\nPC-depth correlation max |r|: {max_depth_r:.3f}")
    if max_depth_r > 0.5:
        print("  ⚠ Depth-correlation downgrade APPENDED to caption.")
    else:
        print("  ✓ Depth-correlation OK (|r| ≤ 0.5).")


if __name__ == "__main__":
    main()
