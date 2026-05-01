#!/usr/bin/env python3
"""ED Candidate: Dataset Familiarization — 3-panel descriptive overview.

Panels:
  a. Context overview strip (4 context tiles)
  b. UMAP overview (HCC38, HCC1143, K562 7d, K562 13d)
  c. Target-gene expression change lollipop (4 contexts)

Purely descriptive. No evidence claims.
Output: reports/extended_data_candidates/dataset_familiarization/
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
import umap
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

OUT_DIR = ROOT / "reports/extended_data_candidates/dataset_familiarization"
QC_DIR = OUT_DIR / "qc"

# ─── Parameters ──────────────────────────────────────────────────────────────
MIN_PERTURBED_CELLS = 20
MIN_CONTROL_CELLS = 50
N_UMAP_NEIGHBORS = 15
N_UMAP_COMPONENTS = 2
N_HIGHLIGHT_PER_PANEL = 1  # MVP: max 1 label per UMAP panel to avoid crowding

# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_and_verify_hcc(path: Path) -> ad.AnnData:
    adata = ad.read_h5ad(path)
    sample = adata.X[:1000].toarray() if sparse.issparse(adata.X) else adata.X[:1000]
    assert sample.max() < 20, f"HCC not log-normalized: max={sample.max():.2f}"
    return adata


def load_and_verify_k562(path: Path) -> ad.AnnData:
    adata = ad.read_h5ad(path)
    sample = adata.X[:1000].toarray() if sparse.issparse(adata.X) else adata.X[:1000]
    assert sample.max() > 100, f"K562 not raw counts: max={sample.max():.2f}"
    return adata


def compute_target_shift(adata: ad.AnnData, target: str) -> float:
    """Mean target-gene expression change: perturbed - control."""
    obs = adata.obs
    control_mask = obs["is_control"].astype(bool).to_numpy()
    target_mask_np = ((~obs["is_control"].astype(bool)) & obs["target_gene"].eq(target)).to_numpy()

    if not target_mask_np.any():
        return np.nan

    X = adata.X
    if sparse.issparse(X):
        ctrl_mean = np.asarray(X[control_mask].mean(axis=0)).ravel()
        pert_mean = np.asarray(X[target_mask_np].mean(axis=0)).ravel()
    else:
        ctrl_mean = np.asarray(X[control_mask].mean(axis=0)).ravel()
        pert_mean = np.asarray(X[target_mask_np].mean(axis=0)).ravel()

    # Find target gene index
    gene_idx = None
    if target in adata.var_names:
        gene_idx = adata.var_names.get_loc(target)
    else:
        # K562 format: ENSG..._GENESYMBOL — try suffix match
        for i, v in enumerate(adata.var_names):
            if v.endswith(f"_{target}") or v == target:
                gene_idx = i
                break

    if gene_idx is None:
        return np.nan
    return float(pert_mean[gene_idx] - ctrl_mean[gene_idx])


def fit_umap(adata: ad.AnnData, n_neighbors: int = N_UMAP_NEIGHBORS) -> np.ndarray:
    """Fit UMAP on adata.X. Returns (n_cells, 2) embeddings."""
    # Compute PCA first for UMAP
    adata_copy = adata.copy()
    sc.pp.pca(adata_copy, n_comps=50, zero_center=True, svd_solver="arpack")
    reducer = umap.UMAP(n_neighbors=n_neighbors, n_components=N_UMAP_COMPONENTS, random_state=42, min_dist=0.5)
    emb = reducer.fit_transform(adata_copy.obsm["X_pca"])
    return emb


def select_highlighted_targets(adata: ad.AnnData) -> list[str]:
    """Select top 1 target by absolute mean perturbation shift."""
    all_targets = sorted(adata.obs.loc[~adata.obs["is_control"].astype(bool), "target_gene"].dropna().unique())
    shifts = []
    for t in all_targets:
        obs = adata.obs
        target_mask_np = ((~obs["is_control"].astype(bool)) & obs["target_gene"].eq(t)).to_numpy()
        n_pert = int(target_mask_np.sum())
        n_ctrl = int(obs["is_control"].astype(bool).sum())
        if n_pert >= MIN_PERTURBED_CELLS and n_ctrl >= MIN_CONTROL_CELLS:
            shift = compute_target_shift(adata, t)
            if not np.isnan(shift):
                shifts.append((t, abs(shift)))

    if not shifts:
        return []
    shifts_sorted = sorted(shifts, key=lambda x: x[1], reverse=True)
    return [t for t, _ in shifts_sorted[:N_HIGHLIGHT_PER_PANEL]]


# ═══════════════════════════════════════════════════════════════════════════════
# Panel A: Context Overview Strip
# ═══════════════════════════════════════════════════════════════════════════════

def build_context_metadata(
    datasets: dict[str, ad.AnnData],
    roles: dict[str, str],
    k562_n_genes: int | None = None,
) -> pd.DataFrame:
    records = []
    for name, adata in datasets.items():
        n_cells = adata.n_obs
        n_ctrl = int(adata.obs["is_control"].astype(bool).sum())
        n_targets = int((~adata.obs["is_control"].astype(bool)).sum())
        n_unique_targets = len(adata.obs.loc[~adata.obs["is_control"].astype(bool), "target_gene"].dropna().unique())
        # K562 shows intersection gene count, HCC shows original
        if "K562" in name and k562_n_genes is not None:
            n_genes = k562_n_genes
        else:
            n_genes = adata.n_vars
        records.append({
            "context": name,
            "role": roles[name],
            "n_cells": n_cells,
            "n_controls": n_ctrl,
            "n_perturbed_cells": n_targets,
            "n_unique_targets": n_unique_targets,
            "n_genes": n_genes,
        })
    return pd.DataFrame(records)


def render_panel_a(ax: plt.Axes, meta_df: pd.DataFrame) -> None:
    """Render context overview strip as 4 tiles."""
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 1)
    ax.set_axis_off()

    colors = {
        "primary": "#4B8A5A",
        "supplementary temporal": "#B8A64A",
    }

    for i, row in enumerate(meta_df.itertuples()):
        x = i
        w = 0.9
        color = colors.get(row.role, "#8A8A8A")

        # Background tile
        rect = plt.Rectangle((x + 0.05, 0.05), w, 0.9, facecolor=color, alpha=0.12, edgecolor=color, linewidth=1.5)
        ax.add_patch(rect)

        # Context name
        ax.text(x + 0.5, 0.82, row.context, ha="center", va="center", fontsize=9, fontweight="bold", color="#333333")
        # Role
        ax.text(x + 0.5, 0.68, row.role, ha="center", va="center", fontsize=7, color=color, style="italic")
        # Stats
        ax.text(x + 0.5, 0.48, f"{row.n_cells:,} cells", ha="center", va="center", fontsize=7, color="#555555")
        ax.text(x + 0.5, 0.35, f"{row.n_unique_targets} targets", ha="center", va="center", fontsize=7, color="#555555")
        ax.text(x + 0.5, 0.22, f"{row.n_controls:,} controls", ha="center", va="center", fontsize=7, color="#555555")
        ax.text(x + 0.5, 0.09, f"{row.n_genes:,} genes", ha="center", va="center", fontsize=7, color="#777777")

    ax.set_title("Benchmark contexts", loc="left", fontsize=8.5, pad=4)
    add_panel_label(ax, "a", x=-0.02, y=1.02)


# ═══════════════════════════════════════════════════════════════════════════════
# Panel B: UMAP Overview
# ═══════════════════════════════════════════════════════════════════════════════

def render_umap_panel(
    ax: plt.Axes,
    adata: ad.AnnData,
    embeddings: np.ndarray,
    panel_label: str,
    title: str,
    highlighted_targets: list[str],
) -> dict:
    """Render a single UMAP panel."""
    obs = adata.obs
    control_mask = obs["is_control"].astype(bool).to_numpy()
    perturbed_mask = (~obs["is_control"].astype(bool)).to_numpy()

    # Plot control cells (light gray)
    ax.scatter(
        embeddings[control_mask, 0],
        embeddings[control_mask, 1],
        c="#E0E0E0",
        s=0.8,
        alpha=0.4,
        rasterized=True,
        label="Control",
    )

    # Plot perturbed cells (green)
    ax.scatter(
        embeddings[perturbed_mask, 0],
        embeddings[perturbed_mask, 1],
        c="#72A39A",
        s=0.8,
        alpha=0.5,
        rasterized=True,
        label="Perturbed",
    )

    # Highlight target cells
    for target in highlighted_targets:
        target_mask_np = (perturbed_mask & obs["target_gene"].eq(target).to_numpy())
        if target_mask_np.sum() > 0:
            ax.scatter(
                embeddings[target_mask_np, 0],
                embeddings[target_mask_np, 1],
                c="none",
                edgecolors="#2B5E4A",
                s=8,
                linewidths=0.8,
                alpha=0.9,
                zorder=5,
                label=target,
            )
            # Add label near centroid
            centroid = embeddings[target_mask_np].mean(axis=0)
            ax.text(
                centroid[0],
                centroid[1] + 0.5,
                target,
                fontsize=5.5,
                color="#2B5E4A",
                fontweight="bold",
                ha="center",
                va="bottom",
            )

    ax.set_title(title, loc="left", fontsize=7.5)
    ax.set_xlabel("UMAP1", fontsize=6.5)
    ax.set_ylabel("UMAP2", fontsize=6.5)
    clean_axes(ax)
    add_panel_label(ax, panel_label)
    ax.set_aspect("equal", adjustable="box")

    return {
        "panel": panel_label,
        "title": title,
        "n_cells": adata.n_obs,
        "n_control": int(control_mask.sum()),
        "n_perturbed": int(perturbed_mask.sum()),
        "highlighted_targets": highlighted_targets,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Panel C: Target-gene Expression Change Lollipop
# ═══════════════════════════════════════════════════════════════════════════════

def render_lollipop_panel(
    ax: plt.Axes,
    adata: ad.AnnData,
    panel_label: str,
    title: str,
) -> pd.DataFrame:
    """Render target-gene expression change as horizontal lollipop."""
    all_targets = sorted(adata.obs.loc[~adata.obs["is_control"].astype(bool), "target_gene"].dropna().unique())

    records = []
    for t in all_targets:
        shift = compute_target_shift(adata, t)
        if not np.isnan(shift):
            records.append({"target": t, "shift": shift})

    if not records:
        ax.set_title(title, loc="left", fontsize=7.5)
        ax.text(0.5, 0.5, "No target-gene\nmatches found", ha="center", va="center", transform=ax.transAxes, fontsize=7, color="#999999")
        clean_axes(ax)
        add_panel_label(ax, panel_label, x=-0.28)
        return pd.DataFrame(columns=["target", "shift"])

    df = pd.DataFrame(records).sort_values("shift")
    y = np.arange(len(df))

    # Lollipop stems
    for i, (_, row) in enumerate(df.iterrows()):
        color = "#4B8A5A" if row["shift"] >= 0 else "#C65A4A"
        ax.plot([0, row["shift"]], [i, i], color=color, alpha=0.5, linewidth=0.8)
        ax.scatter(row["shift"], i, c=color, s=12, zorder=3, edgecolors="white", linewidths=0.3)

    ax.set_yticks(y)
    ax.set_yticklabels(df["target"], fontsize=5.5)
    ax.axvline(x=0, color="#999999", linewidth=0.5, linestyle="--")
    ax.set_xlabel("Target-gene expression change\n(perturbed − control)", fontsize=6)
    ax.set_title(title, loc="left", fontsize=7.5)
    clean_axes(ax)
    add_panel_label(ax, panel_label, x=-0.28)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)

    return df


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 65)
    print("ED Candidate: Dataset Familiarization")
    print("=" * 65)

    ensure_dir(OUT_DIR)
    ensure_dir(QC_DIR)
    apply_manuscript_style()

    # ─── Load datasets ───────────────────────────────────────────────────────
    print("\n[1/5] Loading datasets...")
    hcc38 = load_and_verify_hcc(HCC38_PATH)
    hcc1143 = load_and_verify_hcc(HCC1143_PATH)
    k562_7d = load_and_verify_k562(K562_7D_PATH)
    k562_13d = load_and_verify_k562(K562_13D_PATH)

    datasets = {
        "HCC38": hcc38,
        "HCC1143": hcc1143,
        "K562 7d": k562_7d,
        "K562 13d": k562_13d,
    }
    roles = {
        "HCC38": "primary",
        "HCC1143": "primary",
        "K562 7d": "supplementary temporal",
        "K562 13d": "supplementary temporal",
    }

    # ─── K562 preprocessing ──────────────────────────────────────────────────
    print("\n[2/5] K562 preprocessing...")
    genes_7d = set(k562_7d.var_names)
    genes_13d = set(k562_13d.var_names)
    genes_intersection = sorted(genes_7d & genes_13d)
    n_genes_7d_raw = len(genes_7d)
    n_genes_13d_raw = len(genes_13d)
    n_genes_intersection = len(genes_intersection)
    print(f"  7d raw: {n_genes_7d_raw}, 13d raw: {n_genes_13d_raw}, intersection: {n_genes_intersection}")

    k562_7d_sub = k562_7d[:, genes_intersection].copy()
    k562_13d_sub = k562_13d[:, genes_intersection].copy()

    sc.pp.normalize_total(k562_7d_sub, target_sum=1e4)
    sc.pp.log1p(k562_7d_sub)
    sc.pp.normalize_total(k562_13d_sub, target_sum=1e4)
    sc.pp.log1p(k562_13d_sub)

    # Update datasets dict with preprocessed K562
    datasets["K562 7d"] = k562_7d_sub
    datasets["K562 13d"] = k562_13d_sub

    # ─── Panel A: Context metadata ────────────────────────────────────────────
    print("\n[3/5] Building context metadata...")
    meta_df = build_context_metadata(datasets, roles, k562_n_genes=n_genes_intersection)
    meta_path = write_tsv(meta_df, QC_DIR / "context_metadata.tsv")
    print(f"  Written: {meta_path}")

    # ─── Panel B: UMAP ───────────────────────────────────────────────────────
    print("\n[3/5] Computing UMAP embeddings...")
    emb_hcc38 = fit_umap(hcc38)
    emb_hcc1143 = fit_umap(hcc1143)

    # K562 shared UMAP basis
    k562_pooled = ad.concat([k562_7d_sub, k562_13d_sub], axis=0, merge="same")
    emb_k562_pooled = fit_umap(k562_pooled)
    n_7d = k562_7d_sub.n_obs
    emb_7d = emb_k562_pooled[:n_7d]
    emb_13d = emb_k562_pooled[n_7d:]
    print(f"  HCC38 UMAP done")
    print(f"  HCC1143 UMAP done")
    print(f"  K562 shared UMAP done ({n_7d} + {k562_13d_sub.n_obs} cells)")

    # Select highlighted targets
    hl_hcc38 = select_highlighted_targets(hcc38)
    hl_hcc1143 = select_highlighted_targets(hcc1143)
    hl_k562_7d = select_highlighted_targets(k562_7d_sub)
    hl_k562_13d = select_highlighted_targets(k562_13d_sub)

    print(f"  HCC38 highlight: {hl_hcc38}")
    print(f"  HCC1143 highlight: {hl_hcc1143}")
    print(f"  K562 7d highlight: {hl_k562_7d}")
    print(f"  K562 13d highlight: {hl_k562_13d}")

    # ─── Panel C: Lollipop data ──────────────────────────────────────────────
    print("\n[4/5] Computing target-gene shifts...")
    lollipop_dfs = {}
    for name, adata in [("HCC38", hcc38), ("HCC1143", hcc1143), ("K562 7d", k562_7d_sub), ("K562 13d", k562_13d_sub)]:
        df = render_lollipop_panel(plt.subplots()[1], adata, "", name)  # dummy render to get data
        plt.close()
        lollipop_dfs[name] = df
        print(f"  {name}: {len(df)} targets")

    # ═══════════════════════════════════════════════════════════════════════════
    # Draw combined figure
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n[*] Drawing combined figure...")
    fig = plt.figure(figsize=(11.5, 13.0))

    # Grid: 3 rows
    # Row 0: Panel a (context strip) — full width
    # Row 1: Panel b (UMAP) — 2x2
    # Row 2: Panel c (lollipop) — 1x4
    gs = fig.add_gridspec(3, 4, hspace=0.55, wspace=0.45,
                          height_ratios=[0.22, 1.0, 1.0])

    # ─── Panel a: Context strip ──────────────────────────────────────────────
    ax_a = fig.add_subplot(gs[0, :])
    render_panel_a(ax_a, meta_df)

    # ─── Panel b: UMAP 2x2 ───────────────────────────────────────────────────
    umap_info = []
    ax_b1 = fig.add_subplot(gs[1, 0])
    info = render_umap_panel(ax_b1, hcc38, emb_hcc38, "b", "HCC38", hl_hcc38)
    umap_info.append(info)

    ax_b2 = fig.add_subplot(gs[1, 1])
    info = render_umap_panel(ax_b2, hcc1143, emb_hcc1143, "c", "HCC1143", hl_hcc1143)
    umap_info.append(info)

    ax_b3 = fig.add_subplot(gs[1, 2])
    info = render_umap_panel(ax_b3, k562_7d_sub, emb_7d, "d", "K562 7d", hl_k562_7d)
    umap_info.append(info)

    ax_b4 = fig.add_subplot(gs[1, 3])
    info = render_umap_panel(ax_b4, k562_13d_sub, emb_13d, "e", "K562 13d", hl_k562_13d)
    umap_info.append(info)

    # Group headers for panel b
    fig.text(0.25, 0.72, "Primary contexts", ha="center", fontsize=8, fontweight="bold", color="#555555")
    fig.text(0.75, 0.72, "Supplementary temporal panel", ha="center", fontsize=8, fontweight="bold", color="#555555")

    # ─── Panel c: Lollipop 1x4 ───────────────────────────────────────────────
    ax_c1 = fig.add_subplot(gs[2, 0])
    render_lollipop_panel(ax_c1, hcc38, "f", "HCC38")

    ax_c2 = fig.add_subplot(gs[2, 1])
    render_lollipop_panel(ax_c2, hcc1143, "g", "HCC1143")

    ax_c3 = fig.add_subplot(gs[2, 2])
    render_lollipop_panel(ax_c3, k562_7d_sub, "h", "K562 7d")

    ax_c4 = fig.add_subplot(gs[2, 3])
    render_lollipop_panel(ax_c4, k562_13d_sub, "i", "K562 13d")

    # Main title
    fig.suptitle(
        "Dataset familiarization and descriptive perturbation overview across contexts",
        fontsize=9.5,
        y=0.98,
    )

    # Save figure
    png_path = OUT_DIR / "ed_candidate_dataset_familiarization.png"
    pdf_path = OUT_DIR / "ed_candidate_dataset_familiarization.pdf"
    save_figure(fig, png_path, pdf_path)
    print(f"  Written: {png_path}")
    print(f"  Written: {pdf_path}")

    # ═══════════════════════════════════════════════════════════════════════════
    # Export source data & QC
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n[*] Exporting source data and QC...")

    # UMAP source data
    umap_records = []
    for name, adata, emb in [
        ("HCC38", hcc38, emb_hcc38),
        ("HCC1143", hcc1143, emb_hcc1143),
        ("K562 7d", k562_7d_sub, emb_7d),
        ("K562 13d", k562_13d_sub, emb_13d),
    ]:
        for i in range(adata.n_obs):
            umap_records.append({
                "context": name,
                "cell_barcode": adata.obs.index[i],
                "is_control": bool(adata.obs["is_control"].iloc[i]),
                "target_gene": adata.obs["target_gene"].iloc[i] if "target_gene" in adata.obs.columns else "",
                "umap1": float(emb[i, 0]),
                "umap2": float(emb[i, 1]),
            })
    umap_df = pd.DataFrame(umap_records)
    umap_path = write_tsv(umap_df, OUT_DIR / "ed_candidate_dataset_familiarization_umap_source_data.tsv")
    print(f"  Written: {umap_path}")

    # Lollipop source data
    lollipop_combined = pd.concat(
        [df.assign(context=name) for name, df in lollipop_dfs.items()],
        ignore_index=True,
    )
    lollipop_path = write_tsv(lollipop_combined, OUT_DIR / "ed_candidate_dataset_familiarization_lollipop_source_data.tsv")
    print(f"  Written: {lollipop_path}")

    # QC: UMAP info
    umap_info_df = pd.DataFrame(umap_info)
    umap_info_path = write_tsv(umap_info_df, QC_DIR / "umap_panel_info.tsv")
    print(f"  Written: {umap_info_path}")

    # QC: K562 preprocessing provenance
    provenance = {
        "n_genes_7d_raw": n_genes_7d_raw,
        "n_genes_13d_raw": n_genes_13d_raw,
        "n_genes_intersection": n_genes_intersection,
        "k562_cell_count_7d": int(k562_7d_sub.n_obs),
        "k562_cell_count_13d": int(k562_13d_sub.n_obs),
        "k562_control_count_7d": int(k562_7d_sub.obs["is_control"].astype(bool).sum()),
        "k562_control_count_13d": int(k562_13d_sub.obs["is_control"].astype(bool).sum()),
        "normalization": "sc.pp.normalize_total(target_sum=1e4) + sc.pp.log1p()",
        "umap_n_neighbors": N_UMAP_NEIGHBORS,
        "umap_min_dist": 0.5,
        "umap_random_state": 42,
    }
    prov_path = QC_DIR / "k562_preprocessing_provenance.json"
    prov_path.write_text(json.dumps(provenance, indent=2))
    print(f"  Written: {prov_path}")

    # Caption
    caption = """Extended Data Figure Candidate. Dataset familiarization and descriptive perturbation overview across contexts.

a, Benchmark contexts. Primary HCC38 and HCC1143 contexts and the supplementary K562 7d and 13d temporal contexts used in the benchmark are summarized with their corresponding cell and perturbation counts.

b–e, Low-dimensional visualization of cells across contexts. Cells are shown in context-specific or context-paired UMAP embeddings, with matched controls and perturbed cells indicated separately. HCC38 and HCC1143 were visualized in separate embeddings. K562 7d and 13d were visualized in a shared normalized and log-transformed feature space after gene intersection across time points, and then displayed as separate temporal panels. These embeddings are intended for descriptive visualization only.

f–i, Target-gene expression change across perturbations. For each perturbation target, the displayed value summarizes the target-gene expression difference between perturbed cells and matched control cells within each context. Targets are shown as a descriptive overview of perturbation-associated target-gene expression behavior across contexts.

Claim boundary. These panels are intended as descriptive visualization of the input data and do not replace the pre-specified perturbation-shift metric used for benchmark adjudication.
"""

    caption_path = OUT_DIR / "ed_candidate_dataset_familiarization_caption.md"
    caption_path.write_text(caption)
    print(f"  Written: {caption_path}")

    # Summary
    print("\n" + "=" * 65)
    print("ED CANDIDATE COMPLETE")
    print("=" * 65)
    print(f"Output dir: {OUT_DIR}")
    print(f"  Figure: {png_path}")
    print(f"  QC dir: {QC_DIR}")
    for info in umap_info:
        print(f"  {info['panel']} {info['title']}: {info['n_cells']} cells, {info['n_perturbed']} perturbed, highlight={info['highlighted_targets']}")


if __name__ == "__main__":
    main()
