#!/usr/bin/env python3
"""ED Candidate Dataset Familiarization — Version A (descriptive-only).

Panels:
  a. Context overview strip (4 tiles)
  b. UMAP of perturbation-level mean profiles (4 independent embeddings)
  c. Target-level absolute mean perturbation-shift magnitude (ranked dot plot)

No target-gene expression change. No efficacy claim. Pure descriptive.
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

OUT_DIR = ROOT / "reports/extended_data_candidates/dataset_familiarization_v2"
QC_DIR = OUT_DIR / "qc"

# ─── Parameters ──────────────────────────────────────────────────────────────
MIN_PERTURBED_CELLS = 20
MIN_CONTROL_CELLS = 50
N_UMAP_NEIGHBORS = 5  # small because n_points is small (10-50 targets)
N_HIGHLIGHT_PER_PANEL = 2


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_hcc(path: Path) -> ad.AnnData:
    adata = ad.read_h5ad(path)
    sample = adata.X[:1000].toarray() if sparse.issparse(adata.X) else adata.X[:1000]
    assert sample.max() < 20, f"HCC not log-normalized: max={sample.max():.2f}"
    return adata


def load_k562(path: Path) -> ad.AnnData:
    adata = ad.read_h5ad(path)
    sample = adata.X[:1000].toarray() if sparse.issparse(adata.X) else adata.X[:1000]
    assert sample.max() > 100, f"K562 not raw counts: max={sample.max():.2f}"
    return adata


def compute_perturbation_mean_profile(adata: ad.AnnData, target: str) -> np.ndarray | None:
    """Compute mean expression vector for a target's perturbed cells."""
    obs = adata.obs
    target_mask_np = ((~obs["is_control"].astype(bool)) & obs["target_gene"].eq(target)).to_numpy()
    n_pert = int(target_mask_np.sum())
    if n_pert < MIN_PERTURBED_CELLS:
        return None
    X = adata.X
    if sparse.issparse(X):
        return np.asarray(X[target_mask_np].mean(axis=0)).ravel().astype(np.float64)
    return np.asarray(X[target_mask_np].mean(axis=0)).ravel().astype(np.float64)


def compute_control_mean_profile(adata: ad.AnnData) -> np.ndarray:
    """Compute mean expression vector for control cells."""
    obs = adata.obs
    control_mask = obs["is_control"].astype(bool).to_numpy()
    assert control_mask.sum() >= MIN_CONTROL_CELLS, "Too few control cells"
    X = adata.X
    if sparse.issparse(X):
        return np.asarray(X[control_mask].mean(axis=0)).ravel().astype(np.float64)
    return np.asarray(X[control_mask].mean(axis=0)).ravel().astype(np.float64)


def compute_absolute_mean_shift(adata: ad.AnnData, target: str) -> float:
    """Whole-transcriptome absolute mean perturbation shift."""
    pert = compute_perturbation_mean_profile(adata, target)
    if pert is None:
        return np.nan
    ctrl = compute_control_mean_profile(adata)
    return float(np.mean(np.abs(pert - ctrl)))


def build_mean_profile_matrix(adata: ad.AnnData) -> tuple[np.ndarray, list[str], np.ndarray]:
    """Build matrix of (n_targets + 1, n_genes) mean profiles.
    Returns: profiles array, label list (targets + 'control'), control profile.
    """
    targets = sorted(adata.obs.loc[~adata.obs["is_control"].astype(bool), "target_gene"].dropna().unique())
    ctrl = compute_control_mean_profile(adata)
    profiles = [ctrl]
    labels = ["control"]
    for t in targets:
        pert = compute_perturbation_mean_profile(adata, t)
        if pert is not None:
            profiles.append(pert)
            labels.append(t)
    return np.array(profiles, dtype=np.float64), labels, ctrl


def fit_umap_on_profiles(profiles: np.ndarray, n_neighbors: int = N_UMAP_NEIGHBORS) -> np.ndarray:
    """Fit UMAP on mean profile matrix."""
    reducer = umap.UMAP(n_neighbors=n_neighbors, n_components=2, random_state=42, min_dist=0.3)
    return reducer.fit_transform(profiles)


def select_highlights(adata: ad.AnnData) -> list[str]:
    """Top-2 targets by absolute mean shift."""
    targets = sorted(adata.obs.loc[~adata.obs["is_control"].astype(bool), "target_gene"].dropna().unique())
    shifts = []
    for t in targets:
        s = compute_absolute_mean_shift(adata, t)
        if not np.isnan(s):
            shifts.append((t, s))
    shifts_sorted = sorted(shifts, key=lambda x: x[1], reverse=True)
    return [t for t, _ in shifts_sorted[:N_HIGHLIGHT_PER_PANEL]]


# ═══════════════════════════════════════════════════════════════════════════════
# Panel A: Context Overview Strip
# ═══════════════════════════════════════════════════════════════════════════════

def build_context_metadata(datasets: dict[str, ad.AnnData], roles: dict[str, str]) -> pd.DataFrame:
    records = []
    for name, adata in datasets.items():
        n_cells = adata.n_obs
        n_ctrl = int(adata.obs["is_control"].astype(bool).sum())
        n_unique_targets = len(adata.obs.loc[~adata.obs["is_control"].astype(bool), "target_gene"].dropna().unique())
        n_genes = adata.n_vars
        records.append({
            "context": name,
            "role": roles[name],
            "n_cells": n_cells,
            "n_controls": n_ctrl,
            "n_unique_targets": n_unique_targets,
            "n_genes": n_genes,
        })
    return pd.DataFrame(records)


def render_panel_a(ax: plt.Axes, meta_df: pd.DataFrame) -> None:
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    colors = {"primary": "#4B8A5A", "supplementary temporal": "#B8A64A"}

    for i, row in enumerate(meta_df.itertuples()):
        x = i
        w = 0.9
        color = colors.get(row.role, "#8A8A8A")
        rect = plt.Rectangle((x + 0.05, 0.05), w, 0.9, facecolor=color, alpha=0.12, edgecolor=color, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + 0.5, 0.82, row.context, ha="center", va="center", fontsize=9, fontweight="bold", color="#333333")
        ax.text(x + 0.5, 0.68, row.role, ha="center", va="center", fontsize=7, color=color, style="italic")
        ax.text(x + 0.5, 0.48, f"{row.n_cells:,} cells", ha="center", va="center", fontsize=7, color="#555555")
        ax.text(x + 0.5, 0.35, f"{row.n_unique_targets} targets", ha="center", va="center", fontsize=7, color="#555555")
        ax.text(x + 0.5, 0.22, f"{row.n_controls:,} controls", ha="center", va="center", fontsize=7, color="#555555")
        ax.text(x + 0.5, 0.09, f"{row.n_genes:,} genes", ha="center", va="center", fontsize=7, color="#777777")

    ax.set_title("Benchmark contexts", loc="left", fontsize=8.5, pad=4)
    add_panel_label(ax, "a", x=-0.02, y=1.02)


# ═══════════════════════════════════════════════════════════════════════════════
# Panel B: UMAP of perturbation-level mean profiles
# ═══════════════════════════════════════════════════════════════════════════════

def render_umap_panel(
    ax: plt.Axes,
    profiles: np.ndarray,
    labels: list[str],
    panel_label: str,
    title: str,
    highlighted: list[str],
) -> dict:
    """Each point = one perturbation mean profile; first point = control."""
    emb = fit_umap_on_profiles(profiles)

    # Control point (first)
    ax.scatter(emb[0, 0], emb[0, 1], c="#D95F4B", s=80, edgecolors="white", linewidths=1.2, zorder=5, marker="*")
    ax.text(emb[0, 0], emb[0, 1] + 0.8, "control", fontsize=5.5, color="#D95F4B", ha="center", va="bottom", fontweight="bold")

    # Perturbation points
    for i, label in enumerate(labels[1:], start=1):
        is_highlight = label in highlighted
        color = "#2B5E4A" if is_highlight else "#72A39A"
        s = 50 if is_highlight else 25
        alpha = 0.9 if is_highlight else 0.6
        ax.scatter(emb[i, 0], emb[i, 1], c=color, s=s, edgecolors="white", linewidths=0.5, alpha=alpha, zorder=4)
        if is_highlight:
            offset_x = 0.5 if emb[i, 0] < emb[0, 0] else -0.5
            ax.text(emb[i, 0] + offset_x, emb[i, 1], label, fontsize=5.5, color="#2B5E4A", ha="center" if abs(offset_x) < 0.3 else ("right" if offset_x > 0 else "left"), va="center", fontweight="bold")

    ax.set_title(title, loc="left", fontsize=7.5)
    ax.set_xlabel("UMAP1", fontsize=6.5)
    ax.set_ylabel("UMAP2", fontsize=6.5)
    clean_axes(ax)
    add_panel_label(ax, panel_label)
    ax.set_aspect("equal", adjustable="box")

    return {"panel": panel_label, "title": title, "n_profiles": len(labels), "highlighted": highlighted}


# ═══════════════════════════════════════════════════════════════════════════════
# Panel C: Absolute mean perturbation-shift magnitude
# ═══════════════════════════════════════════════════════════════════════════════

def render_shift_panel(ax: plt.Axes, adata: ad.AnnData, panel_label: str, title: str) -> pd.DataFrame:
    targets = sorted(adata.obs.loc[~adata.obs["is_control"].astype(bool), "target_gene"].dropna().unique())
    records = []
    for t in targets:
        s = compute_absolute_mean_shift(adata, t)
        if not np.isnan(s):
            records.append({"target": t, "abs_shift": s})

    df = pd.DataFrame(records).sort_values("abs_shift")
    y = np.arange(len(df))

    for i, (_, row) in enumerate(df.iterrows()):
        ax.plot([0, row["abs_shift"]], [i, i], color="#72A39A", alpha=0.5, linewidth=0.8)
        ax.scatter(row["abs_shift"], i, c="#4B8A5A", s=12, zorder=3, edgecolors="white", linewidths=0.3)

    ax.set_yticks(y)
    ax.set_yticklabels(df["target"], fontsize=5.5)
    ax.set_xlabel("Absolute mean perturbation shift", fontsize=6)
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
    print("ED Candidate Dataset Familiarization — Version A")
    print("=" * 65)

    ensure_dir(OUT_DIR)
    ensure_dir(QC_DIR)
    apply_manuscript_style()

    # ─── Load datasets ───────────────────────────────────────────────────────
    print("\n[1/4] Loading datasets...")
    hcc38 = load_hcc(HCC38_PATH)
    hcc1143 = load_hcc(HCC1143_PATH)
    k562_7d_raw = load_k562(K562_7D_PATH)
    k562_13d_raw = load_k562(K562_13D_PATH)

    # K562 preprocessing
    genes_7d = set(k562_7d_raw.var_names)
    genes_13d = set(k562_13d_raw.var_names)
    genes_intersection = sorted(genes_7d & genes_13d)
    n_genes_7d_raw = len(genes_7d)
    n_genes_13d_raw = len(genes_13d)
    n_genes_intersection = len(genes_intersection)

    k562_7d = k562_7d_raw[:, genes_intersection].copy()
    k562_13d = k562_13d_raw[:, genes_intersection].copy()
    sc.pp.normalize_total(k562_7d, target_sum=1e4)
    sc.pp.log1p(k562_7d)
    sc.pp.normalize_total(k562_13d, target_sum=1e4)
    sc.pp.log1p(k562_13d)

    datasets = {"HCC38": hcc38, "HCC1143": hcc1143, "K562 7d": k562_7d, "K562 13d": k562_13d}
    roles = {"HCC38": "primary", "HCC1143": "primary", "K562 7d": "supplementary temporal", "K562 13d": "supplementary temporal"}

    # ─── Panel A metadata ────────────────────────────────────────────────────
    meta_df = build_context_metadata(datasets, roles)
    meta_df.loc[meta_df["context"].str.startswith("K562"), "n_genes"] = n_genes_intersection
    write_tsv(meta_df, QC_DIR / "context_metadata.tsv")

    # ─── Panel B: mean profile matrices ──────────────────────────────────────
    print("\n[2/4] Building perturbation-level mean profiles...")
    prof_hcc38, labels_hcc38, _ = build_mean_profile_matrix(hcc38)
    prof_hcc1143, labels_hcc1143, _ = build_mean_profile_matrix(hcc1143)
    prof_k562_7d, labels_k562_7d, _ = build_mean_profile_matrix(k562_7d)
    prof_k562_13d, labels_k562_13d, _ = build_mean_profile_matrix(k562_13d)
    print(f"  HCC38: {len(labels_hcc38)} profiles")
    print(f"  HCC1143: {len(labels_hcc1143)} profiles")
    print(f"  K562 7d: {len(labels_k562_7d)} profiles")
    print(f"  K562 13d: {len(labels_k562_13d)} profiles")

    hl_hcc38 = select_highlights(hcc38)
    hl_hcc1143 = select_highlights(hcc1143)
    hl_k562_7d = select_highlights(k562_7d)
    hl_k562_13d = select_highlights(k562_13d)
    print(f"  Highlights: HCC38={hl_hcc38}, HCC1143={hl_hcc1143}, K562_7d={hl_k562_7d}, K562_13d={hl_k562_13d}")

    # ─── Panel C: shift data ─────────────────────────────────────────────────
    print("\n[3/4] Computing shift magnitudes...")
    shift_dfs = {}
    for name, adata in [("HCC38", hcc38), ("HCC1143", hcc1143), ("K562 7d", k562_7d), ("K562 13d", k562_13d)]:
        df = render_shift_panel(plt.subplots()[1], adata, "", name)
        plt.close()
        shift_dfs[name] = df
        print(f"  {name}: {len(df)} targets, max shift={df['abs_shift'].max():.4f}, median={df['abs_shift'].median():.4f}")

    # ─── Draw combined figure ────────────────────────────────────────────────
    print("\n[4/4] Drawing combined figure...")
    fig = plt.figure(figsize=(11.5, 13.0))
    gs = fig.add_gridspec(3, 4, hspace=0.55, wspace=0.45, height_ratios=[0.22, 1.0, 1.0])

    # Panel a
    ax_a = fig.add_subplot(gs[0, :])
    render_panel_a(ax_a, meta_df)

    # Panel b: UMAP 2x2
    umap_info = []
    ax_b1 = fig.add_subplot(gs[1, 0])
    info = render_umap_panel(ax_b1, prof_hcc38, labels_hcc38, "b", "HCC38", hl_hcc38)
    umap_info.append(info)

    ax_b2 = fig.add_subplot(gs[1, 1])
    info = render_umap_panel(ax_b2, prof_hcc1143, labels_hcc1143, "c", "HCC1143", hl_hcc1143)
    umap_info.append(info)

    ax_b3 = fig.add_subplot(gs[1, 2])
    info = render_umap_panel(ax_b3, prof_k562_7d, labels_k562_7d, "d", "K562 7d", hl_k562_7d)
    umap_info.append(info)

    ax_b4 = fig.add_subplot(gs[1, 3])
    info = render_umap_panel(ax_b4, prof_k562_13d, labels_k562_13d, "e", "K562 13d", hl_k562_13d)
    umap_info.append(info)

    fig.text(0.25, 0.72, "Primary contexts", ha="center", fontsize=8, fontweight="bold", color="#555555")
    fig.text(0.75, 0.72, "Supplementary temporal panel", ha="center", fontsize=8, fontweight="bold", color="#555555")

    # Panel c: shift magnitude 1x4
    ax_c1 = fig.add_subplot(gs[2, 0])
    render_shift_panel(ax_c1, hcc38, "f", "HCC38")

    ax_c2 = fig.add_subplot(gs[2, 1])
    render_shift_panel(ax_c2, hcc1143, "g", "HCC1143")

    ax_c3 = fig.add_subplot(gs[2, 2])
    render_shift_panel(ax_c3, k562_7d, "h", "K562 7d")

    ax_c4 = fig.add_subplot(gs[2, 3])
    render_shift_panel(ax_c4, k562_13d, "i", "K562 13d")

    fig.suptitle("Descriptive overview of benchmark input datasets across primary and supplementary contexts", fontsize=9.5, y=0.98)

    png_path = OUT_DIR / "ed_candidate_dataset_familiarization_v2.png"
    pdf_path = OUT_DIR / "ed_candidate_dataset_familiarization_v2.pdf"
    save_figure(fig, png_path, pdf_path)
    print(f"  Written: {png_path}")

    # ─── Export source data & QC ─────────────────────────────────────────────
    print("\n[*] Exporting source data and QC...")

    # UMAP embeddings source data
    umap_records = []
    for name, prof, labels in [
        ("HCC38", prof_hcc38, labels_hcc38),
        ("HCC1143", prof_hcc1143, labels_hcc1143),
        ("K562 7d", prof_k562_7d, labels_k562_7d),
        ("K562 13d", prof_k562_13d, labels_k562_13d),
    ]:
        emb = fit_umap_on_profiles(prof)
        for i, label in enumerate(labels):
            umap_records.append({"context": name, "profile": label, "umap1": float(emb[i, 0]), "umap2": float(emb[i, 1]), "is_control": label == "control"})
    umap_df = pd.DataFrame(umap_records)
    write_tsv(umap_df, OUT_DIR / "ed_candidate_v2_umap_source_data.tsv")

    # Shift magnitude source data
    shift_combined = pd.concat([df.assign(context=name) for name, df in shift_dfs.items()], ignore_index=True)
    write_tsv(shift_combined, OUT_DIR / "ed_candidate_v2_shift_magnitude_source_data.tsv")

    # QC
    write_tsv(pd.DataFrame(umap_info), QC_DIR / "umap_panel_info.tsv")
    provenance = {
        "n_genes_7d_raw": n_genes_7d_raw,
        "n_genes_13d_raw": n_genes_13d_raw,
        "n_genes_intersection": n_genes_intersection,
        "k562_normalization": "sc.pp.normalize_total(target_sum=1e4) + sc.pp.log1p()",
        "panel_b_identity": "UMAP of perturbation-level mean expression profiles (each point = one target mean vector + control mean vector)",
        "panel_c_identity": "Absolute mean whole-transcriptome perturbation shift magnitude (perturbed mean - control mean, averaged across all genes)",
    }
    (QC_DIR / "provenance.json").write_text(json.dumps(provenance, indent=2))

    # Caption
    caption = """Extended Data Figure Candidate. Descriptive overview of benchmark input datasets across primary and supplementary contexts.

a, Benchmark contexts. Primary HCC38 and HCC1143 contexts and the supplementary K562 7d and 13d temporal contexts used in the benchmark are summarized with their corresponding cell and perturbation counts.

b–e, UMAP of perturbation-level mean profiles. Each point represents the mean expression profile of one perturbation target (green) or the matched control aggregate (red star) within the indicated context. Embeddings are shown independently for each context and are intended for descriptive visualization only.

f–i, Target-level perturbation-shift magnitude. For each perturbation target, the displayed value summarizes the absolute mean whole-transcriptome perturbation shift relative to matched controls within the indicated context. Targets are ranked to provide a descriptive overview of transcriptomic perturbation magnitude.

Claim boundary. These panels are provided as descriptive visualization of the input datasets and do not replace the pre-specified perturbation-shift metric and endpoint definitions used for benchmark adjudication.
"""
    (OUT_DIR / "ed_candidate_dataset_familiarization_v2_caption.md").write_text(caption)

    print("\n" + "=" * 65)
    print("ED CANDIDATE V2 COMPLETE")
    print("=" * 65)
    print(f"Output: {OUT_DIR}")
    for info in umap_info:
        print(f"  {info['panel']} {info['title']}: {info['n_profiles']} profiles, highlights={info['highlighted']}")


if __name__ == "__main__":
    main()
