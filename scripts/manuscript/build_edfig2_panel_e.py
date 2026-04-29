#!/usr/bin/env python3
"""Generate ED Fig 2 panel e: whole-transcriptome shift vs target-gene self-expression scatter."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import anndata as ad
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
import pandas as pd
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from wtbench.manuscript.figure_io import repo_root, save_figure, ensure_dir
from wtbench.manuscript.manuscript_style import (
    AXIS_LABEL_SIZE,
    COLORS,
    TICK_LABEL_SIZE,
    apply_manuscript_style,
    clean_axes,
)

ROOT = repo_root()

HCC38_PATH = ROOT / "data/processed/stage2_hcc_gears_formal/HCC38.h5ad"
HCC1143_PATH = ROOT / "data/processed/stage2_hcc_gears_formal/HCC1143.h5ad"
JOINT_GRID = ROOT / "reports/stage2_truth_bridge_decomposition/target_level_joint_grid.tsv"

OUT_PANEL_E = ROOT / "manuscript/extended_data/Extended_Data_Figure_2/panels/Extended_Data_Figure_2_panel_e"
OUT_TEST = ROOT / "reports/manuscript_extended_data_v1/edfig2_test_panel_e"
# Continuous colormap (Mean abs shift) preview — compare with default gray/orange
OUT_TEST_SHIFT_COLOR = ROOT / "reports/manuscript_extended_data_v1/edfig2_test_panel_e_shift_colormap"

# Default (classic scatter): accent these four in orange
REFERENCE_ANCHORS = ["PFDN5", "PRPF6", "ZNF131"]


def compute_log2fc(adata: ad.AnnData, target_gene: str) -> float | None:
    """Compute log2 fold-change for target gene's self-expression."""
    obs = adata.obs
    is_pert = (~obs["is_control"].astype(bool)) & obs["target_gene"].eq(target_gene)
    is_ctrl = obs["is_control"].astype(bool)

    if not is_pert.any() or not is_ctrl.any():
        return None

    # Check if gene is in var_names
    if target_gene not in adata.var_names:
        # Try case-insensitive
        matches = [g for g in adata.var_names if g.upper() == target_gene.upper()]
        if not matches:
            return None
        target_gene = matches[0]

    X = adata[:, target_gene].X
    if sparse.issparse(X):
        X = X.toarray()

    pert_mean = float(np.mean(X[is_pert.to_numpy()]))
    ctrl_mean = float(np.mean(X[is_ctrl.to_numpy()]))

    if ctrl_mean <= 0:
        return None

    # Data is log1p-transformed; convert delta to log2 fold-change
    return float((pert_mean - ctrl_mean) / np.log(2))


def build_source(
    adata: ad.AnnData,
    cell_line: str,
    *,
    highlight_genes: set[str],
    label_genes: set[str],
) -> pd.DataFrame:
    """Build per-target source data with log2FC, shift, and dependency."""
    grid = pd.read_csv(JOINT_GRID, sep="\t")
    grid = grid.loc[grid["cell_line"] == cell_line].copy()

    targets = sorted(set(
        adata.obs.loc[~adata.obs["is_control"].astype(bool), "target_gene"].dropna()
    ))

    records = []
    for t in targets:
        log2fc = compute_log2fc(adata, t)
        if log2fc is None:
            continue
        row = grid.loc[grid["target_gene"].eq(t)]
        if row.empty:
            continue
        records.append({
            "target_gene": t,
            "log2fc": log2fc,
            "depmap_dependency": float(row["depmap_gene_dependency"].iloc[0]),
            "shift_mean_abs": float(row["real_shift_mean_abs"].iloc[0]),
            "is_anchor": t in highlight_genes,
            "is_labeled": t in label_genes,
        })

    return pd.DataFrame(records)


def render_scatter(ax: plt.Axes, df: pd.DataFrame, title: str) -> None:
    """Render single-context scatter."""
    # Background: all points
    non_anchor = df.loc[~df["is_anchor"]]
    ax.scatter(non_anchor["log2fc"], non_anchor["depmap_dependency"],
               c="#B0B0B0", s=18, edgecolors="none", alpha=0.5, zorder=1)

    # Anchor points
    anchors = df.loc[df["is_anchor"]]
    ax.scatter(anchors["log2fc"], anchors["depmap_dependency"],
               c="#D55E00", s=36, edgecolors="white", linewidths=0.5, alpha=0.9, zorder=3)

    _gene_annotations(ax, df)

    # Annotations
    log2fc_rho = df["log2fc"].corr(df["depmap_dependency"], method="spearman")
    shift_rho = df["shift_mean_abs"].corr(df["depmap_dependency"], method="spearman")
    n = len(df)

    ax.text(0.03, 0.95,
            f"{title}\nn = {n}\n"
            f"target-gene log2FC vs dependency: rho = {log2fc_rho:.2f}\n"
            f"whole-transcriptome shift vs dependency: rho = {shift_rho:.2f}",
            transform=ax.transAxes, fontsize=5.8, va="top", ha="left",
            color="#333333")

    ax.set_xlabel("Target-gene log2FC (self-expression change)")
    ax.set_ylabel("CRISPR dependency")
    clean_axes(ax)
    # No grid — clean scatter background


def _gene_annotations(ax: plt.Axes, df: pd.DataFrame) -> None:
    # Labels BELOW data points, diagonal arrows pointing UP to the gene spot.
    label_offsets = {
        "PFDN5":   (0, -22),
        "PRPF6":   (0, -28),
        "ZNF131":  (0, -16),
    }
    for _, row in df.loc[df["is_labeled"]].iterrows():
        gene = row["target_gene"]
        dx, dy = label_offsets.get(gene, (8, -20))
        ax.annotate(
            gene,
            xy=(row["log2fc"], row["depmap_dependency"]),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=5.2,
            fontweight="bold",
            ha="center",
            va="top",
            color="#333333",
            arrowprops=dict(arrowstyle="->", color="#666666", lw=0.6),
        )


def shift_color_norm_bounds(src_38: pd.DataFrame, src_1143: pd.DataFrame) -> tuple[float, float]:
    """Shared vmin/vmax; span at least manuscript reference (~0.004–~0.014) when data allow."""
    v = pd.concat([src_38["shift_mean_abs"], src_1143["shift_mean_abs"]], ignore_index=True)
    dmin, dmax = float(v.min()), float(v.max())
    # Pad range similar to Extended Data caption / colorbar (~0.004 cream → ~0.014+ maroon)
    vmin = min(0.004, dmin)
    vmax = max(0.014, dmax)
    if vmin >= vmax:
        vmax = vmin + 1e-6
    return vmin, vmax


def render_scatter_shift_colormap(
    ax: plt.Axes,
    df: pd.DataFrame,
    title: str,
    norm: Normalize,
    cmap_name: str = "YlOrRd",
    rho_pos: str = "left",
):
    """Scatter colored + sized by mean abs shift (shared norm across contexts)."""
    cmap = plt.get_cmap(cmap_name).copy()
    shift = df["shift_mean_abs"].to_numpy(dtype=float)
    widths = shift - norm.vmin
    span = norm.vmax - norm.vmin
    if span <= 0:
        span = 1e-9
    w = np.clip(widths / span, 0.0, 1.0)
    sizes = 14.0 + 95.0 * w

    ax.scatter(
        df["log2fc"],
        df["depmap_dependency"],
        c=shift,
        s=sizes,
        cmap=cmap,
        norm=norm,
        edgecolors="#FFFFFFCC",
        linewidths=0.35,
        alpha=0.9,
        zorder=2,
    )

    log2fc_rho = df["log2fc"].corr(df["depmap_dependency"], method="spearman")
    shift_rho = df["shift_mean_abs"].corr(df["depmap_dependency"], method="spearman")
    n = len(df)

    rho_x = 1.04 if rho_pos == "left" else 1.04
    rho_ha = "left" if rho_pos == "left" else "left"
    ax.text(
        rho_x,
        0.98,
        f"n = {n}\nrho(tg_logFC) = {log2fc_rho:.2f}\nrho(transcr.) = {shift_rho:.2f}",
        transform=ax.transAxes,
        fontsize=5.8,
        va="top",
        ha=rho_ha,
        color="#333333",
        linespacing=1.35,
        clip_on=False,
    )

    # Context label top-left, not bold (matching panel d style)
    ax.text(0.02, 1.06, title, transform=ax.transAxes, fontsize=8.0,
            va="bottom", ha="left", color="#333333", clip_on=False)

    ax.set_xlabel("Target gene log2 FC", labelpad=2)
    ax.set_ylabel("DepMap dependency", labelpad=2)
    clean_axes(ax)
    # No grid — clean scatter background
    _gene_annotations(ax, df)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    return sm


def build_figure_shift_colormap(src_38: pd.DataFrame, src_1143: pd.DataFrame) -> plt.Figure:
    low, high = shift_color_norm_bounds(src_38, src_1143)
    norm = Normalize(vmin=low, vmax=high)

    fig = plt.figure(figsize=(11.0, 2.2))
    gs = gridspec.GridSpec(
        1,
        3,
        figure=fig,
        width_ratios=[1.0, 1.0, 0.08],
        wspace=0.60,
        left=0.07,
        right=0.94,
        top=0.85,
        bottom=0.16,
    )
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    cax = fig.add_subplot(gs[0, 2])

    sm = render_scatter_shift_colormap(ax1, src_38, "HCC38", norm, rho_pos="left")
    render_scatter_shift_colormap(ax2, src_1143, "HCC1143", norm, rho_pos="right")

    fig.suptitle("Whole-transcriptome shift vs target-gene self-expression", fontsize=8.5, fontweight="bold", y=1.04)

    cb = fig.colorbar(sm, cax=cax)
    cb.set_label("Mean abs shift", fontsize=AXIS_LABEL_SIZE)
    cb.ax.minorticks_off()
    cax.tick_params(labelsize=TICK_LABEL_SIZE)

    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument(
        "--reference",
        action="store_true",
        help=(
            "Publication Extended Data Fig. 2 panel e: YlOrRd by Mean abs shift, shared colorbar, "
            "four anchor labels (PFDN5, PMF1, PRPF6, ZNF131), rho top-right. "
            "Writes manuscript panels + shift_colormap reports path."
        ),
    )
    grp.add_argument(
        "--classic",
        action="store_true",
        help="Gray non-anchor / orange anchor scatter (legacy). Writes manuscript panels + edfig2_test_panel_e.",
    )
    parser.add_argument(
        "--test-shift-color",
        action="store_true",
        help="Same figure as --reference; write only reports/…/edfig2_test_panel_e_shift_colormap.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Write panel_e PNG/PDF only under this directory (files: panel_e.png / panel_e.pdf). "
            "Does not touch manuscript/ …/panels/ nor default reports paths."
        ),
    )
    args = parser.parse_args()

    use_reference = args.reference or args.test_shift_color
    use_classic = args.classic and not use_reference
    if not use_reference and not use_classic:
        use_reference = True

    ref_set = set(REFERENCE_ANCHORS)
    apply_manuscript_style()

    print("Loading HCC38...")
    hcc38 = ad.read_h5ad(HCC38_PATH)
    print("Loading HCC1143...")
    hcc1143 = ad.read_h5ad(HCC1143_PATH)

    highlight_genes = ref_set
    label_genes = ref_set

    src_38 = build_source(hcc38, "HCC38", highlight_genes=highlight_genes, label_genes=label_genes)
    src_1143 = build_source(hcc1143, "HCC1143", highlight_genes=highlight_genes, label_genes=label_genes)
    print(f"HCC38: {len(src_38)} targets, HCC1143: {len(src_1143)} targets")

    if args.output_dir is not None:
        out_only = Path(args.output_dir).expanduser().resolve()
        ensure_dir(out_only)

    if use_reference:
        fig = build_figure_shift_colormap(src_38, src_1143)
        if args.output_dir is not None:
            outp = out_only / "panel_e"
            save_figure(fig, outp.with_suffix(".png"), outp.with_suffix(".pdf"))
            print(f"[OK] Preview only → {outp.with_suffix('.png')}")
            return

        if args.test_shift_color:
            ensure_dir(OUT_TEST_SHIFT_COLOR)
            outp = OUT_TEST_SHIFT_COLOR / "panel_e"
            save_figure(fig, outp.with_suffix(".png"), outp.with_suffix(".pdf"))
            print(f"[OK] Shift-colored test: {outp.with_suffix('.png')}")
            return

        ensure_dir(OUT_PANEL_E.parent)
        ensure_dir(OUT_TEST_SHIFT_COLOR)
        save_figure(fig, OUT_PANEL_E.with_suffix(".png"), OUT_PANEL_E.with_suffix(".pdf"))
        save_figure(fig, OUT_TEST_SHIFT_COLOR / "panel_e.png", OUT_TEST_SHIFT_COLOR / "panel_e.pdf")
        print(f"[OK] ED Fig 2 panel e (reference): {OUT_PANEL_E.with_suffix('.png')}")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.9, 3.2))
    render_scatter(ax1, src_38, "HCC38")
    render_scatter(ax2, src_1143, "HCC1143")

    fig.tight_layout()

    if args.output_dir is not None:
        outp = out_only / "panel_e"
        save_figure(fig, outp.with_suffix(".png"), outp.with_suffix(".pdf"))
        print(f"[OK] Preview only (classic) → {outp.with_suffix('.png')}")
        return

    ensure_dir(OUT_PANEL_E.parent)
    ensure_dir(OUT_TEST)
    save_figure(fig, OUT_PANEL_E.with_suffix(".png"), OUT_PANEL_E.with_suffix(".pdf"))
    save_figure(fig, OUT_TEST / "panel_e.png", OUT_TEST / "panel_e.pdf")
    print(f"[OK] Panel e (classic): {OUT_PANEL_E.with_suffix('.png')}")


if __name__ == "__main__":
    main()
