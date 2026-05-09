#!/usr/bin/env python3
"""
Standalone generator for Extended Data Figure 2 panel e (no wtbench package).

Same inputs/outputs as scripts/manuscript/build_edfig2_panel_e.py:
  - Reads: data/processed/hcc_gears_formal/{HCC38,HCC1143}.h5ad
           reports/truth_bridge_decomposition/target_level_joint_grid.tsv
  - Writes: --out-dir/panel_e.{png,pdf} and source TSV (default; use --out-dir)

Usage (from repository root):
    python scripts/manuscript/edfig2_panel_e_standalone.py --out-dir ./edfig2_panel_e_only

Dependencies: anndata, matplotlib, numpy, pandas, scipy (and pillow if you use max_width).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Literal

import anndata as ad
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.text import Text
import numpy as np
import pandas as pd
from scipy import sparse

# ---------------------------------------------------------------------------
# Inline minimal figure I/O + style (normally from wtbench.manuscript.*)
# ---------------------------------------------------------------------------

FONT_FAMILY = ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"]
BASE_FONT_SIZE = 7.0
AXIS_LABEL_SIZE = 7.0
TICK_LABEL_SIZE = 6.2

COLORS = {"text": "#1F1F1F"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_tsv(df: pd.DataFrame, path: Path) -> Path:
    ensure_dir(path.parent)
    df.to_csv(path, sep="\t", index=False)
    return path


def apply_manuscript_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": FONT_FAMILY,
            "font.size": BASE_FONT_SIZE,
            "axes.labelsize": AXIS_LABEL_SIZE,
            "xtick.labelsize": TICK_LABEL_SIZE,
            "ytick.labelsize": TICK_LABEL_SIZE,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 2.2,
            "ytick.major.size": 2.2,
            "axes.edgecolor": "#4A4A4A",
            "axes.labelcolor": COLORS["text"],
            "xtick.color": "#4A4A4A",
            "ytick.color": "#4A4A4A",
            "text.color": COLORS["text"],
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.dpi": 1200,
        }
    )


def clean_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.6)
    ax.spines["bottom"].set_linewidth(0.6)
    ax.tick_params(axis="both", which="major", length=2.2, width=0.6, pad=1.5)


def finalize_manuscript_figure(fig: plt.Figure) -> None:
    for text in fig.findobj(match=Text):
        text.set_fontfamily("sans-serif")
    for ax in fig.axes:
        ax.xaxis.label.set_fontsize(AXIS_LABEL_SIZE)
        ax.yaxis.label.set_fontsize(AXIS_LABEL_SIZE)
        ax.xaxis.label.set_fontweight("normal")
        ax.yaxis.label.set_fontweight("normal")
        for tick_label in ax.get_xticklabels() + ax.get_yticklabels():
            tick_label.set_fontsize(TICK_LABEL_SIZE)
            tick_label.set_fontweight("normal")


def save_figure(
    fig: plt.Figure,
    png_path: Path,
    pdf_path: Path,
    *,
    dpi: int = 1200,
    max_width: int | None = None,
    bbox_inches: Literal["tight"] | None = "tight",
) -> list[Path]:
    ensure_dir(png_path.parent)
    ensure_dir(pdf_path.parent)
    finalize_manuscript_figure(fig)
    save_kw: dict = {"dpi": dpi}
    save_kw["bbox_inches"] = bbox_inches if bbox_inches else None
    fig.savefig(png_path, **save_kw)
    fig.savefig(pdf_path, **save_kw)
    plt.close(fig)
    if max_width and png_path.exists():
        from PIL import Image as PILImage

        im = PILImage.open(png_path)
        if im.width > max_width:
            im = im.resize((max_width, int(im.height * max_width / im.width)), PILImage.LANCZOS)
            im.save(png_path, dpi=(dpi, dpi))
    return [png_path, pdf_path]


# ---------------------------------------------------------------------------
# Panel e logic (mirrors build_edfig2_panel_e.py)
# ---------------------------------------------------------------------------

ROOT = repo_root()

REFERENCE_ANCHORS = ["PFDN5", "PMF1", "PRPF6", "ZNF131"]
ANCHOR_GENE_LABELS = ["PFDN5", "PRPF6", "ZNF131"]
PANEL_E_SOURCE_NAME = "Extended_Data_Figure_2_panel_e_source_data.tsv"


def compute_log2fc(adata: ad.AnnData, target_gene: str) -> float | None:
    obs = adata.obs
    is_pert = (~obs["is_control"].astype(bool)) & obs["target_gene"].eq(target_gene)
    is_ctrl = obs["is_control"].astype(bool)

    if not is_pert.any() or not is_ctrl.any():
        return None

    if target_gene not in adata.var_names:
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

    return float((pert_mean - ctrl_mean) / np.log(2))


def build_source(
    adata: ad.AnnData,
    cell_line: str,
    joint_grid: Path,
    *,
    highlight_genes: set[str],
    label_genes: set[str],
) -> pd.DataFrame:
    grid = pd.read_csv(joint_grid, sep="\t")
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


def combined_panel_e_source(src_38: pd.DataFrame, src_1143: pd.DataFrame) -> pd.DataFrame:
    out = pd.concat(
        [src_38.assign(cell_line="HCC38"), src_1143.assign(cell_line="HCC1143")],
        ignore_index=True,
    )
    cols = [
        "cell_line",
        "target_gene",
        "log2fc",
        "depmap_dependency",
        "shift_mean_abs",
        "is_anchor",
        "is_labeled",
    ]
    return out.loc[:, cols].sort_values(["cell_line", "target_gene"]).reset_index(drop=True)


def _gene_annotations(ax: plt.Axes, df: pd.DataFrame) -> None:
    label_offsets = {
        "PFDN5": (0, -22),
        "PRPF6": (0, -28),
        "ZNF131": (0, -16),
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
    v = pd.concat([src_38["shift_mean_abs"], src_1143["shift_mean_abs"]], ignore_index=True)
    dmin, dmax = float(v.min()), float(v.max())
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
    *,
    rho_pos: str,
) -> None:
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

    rho_ha = "left" if rho_pos == "left" else "left"
    rho_x = 1.04 if rho_pos == "left" else 1.02
    ax.text(
        rho_x,
        0.98,
        f"n = {n}\nSpearman $\\rho$ (tg_logFC) = {log2fc_rho:.2f}\n"
        f"Spearman $\\rho$ (transcr.) = {shift_rho:.2f}",
        transform=ax.transAxes,
        fontsize=5.8,
        va="top",
        ha=rho_ha,
        color="#333333",
        linespacing=1.35,
        clip_on=False,
    )

    ax.text(
        0.02,
        1.06,
        title,
        transform=ax.transAxes,
        fontsize=8.0,
        va="bottom",
        ha="left",
        color="#333333",
        clip_on=False,
    )

    ax.set_xlabel("Target gene log2 FC", labelpad=2)
    ax.set_ylabel("DepMap dependency", labelpad=2)
    clean_axes(ax)
    _gene_annotations(ax, df)


def build_figure_shift_colormap(src_38: pd.DataFrame, src_1143: pd.DataFrame) -> plt.Figure:
    low, high = shift_color_norm_bounds(src_38, src_1143)
    norm = Normalize(vmin=low, vmax=high)

    fig = plt.figure(figsize=(11.0, 2.2))
    gs = gridspec.GridSpec(
        1,
        2,
        figure=fig,
        width_ratios=[1.0, 1.0],
        wspace=0.38,
        left=0.07,
        right=0.93,
        top=0.85,
        bottom=0.16,
    )
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    cmap = plt.get_cmap("YlOrRd").copy()
    render_scatter_shift_colormap(ax1, src_38, "HCC38", norm, rho_pos="left")
    render_scatter_shift_colormap(ax2, src_1143, "HCC1143", norm, rho_pos="right")

    fig.suptitle(
        "Whole-transcriptome shift vs target-gene self-expression",
        fontsize=8.5,
        fontweight="bold",
        y=1.04,
    )

    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cb = fig.colorbar(sm, ax=ax2, fraction=0.085, pad=0.002)
    cb.set_label("Mean abs shift", fontsize=AXIS_LABEL_SIZE)
    cb.ax.minorticks_off()
    cb.ax.tick_params(labelsize=TICK_LABEL_SIZE)

    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        metavar="DIR",
        help="Output directory for panel_e.png, panel_e.pdf, and source-data TSV.",
    )
    parser.add_argument(
        "--h38",
        type=Path,
        default=None,
        help="Override HCC38 AnnData path (default: repo data/processed/...)",
    )
    parser.add_argument(
        "--h1143",
        type=Path,
        default=None,
        help="Override HCC1143 AnnData path.",
    )
    parser.add_argument(
        "--joint-grid",
        type=Path,
        default=None,
        help="Override target_level_joint_grid.tsv path.",
    )
    args = parser.parse_args()

    root = repo_root()
    h38_path = Path(args.h38).expanduser() if args.h38 else root / "data/processed/hcc_gears_formal/HCC38.h5ad"
    h1143_path = Path(args.h1143).expanduser() if args.h1143 else root / "data/processed/hcc_gears_formal/HCC1143.h5ad"
    joint = Path(args.joint_grid).expanduser() if args.joint_grid else root / (
        "reports/truth_bridge_decomposition/target_level_joint_grid.tsv"
    )

    out_dir = Path(args.out_dir).expanduser().resolve()
    ensure_dir(out_dir)

    ref_set = set(REFERENCE_ANCHORS)
    highlight_genes = ref_set
    label_genes = set(ANCHOR_GENE_LABELS)

    apply_manuscript_style()

    print("Loading HCC38...")
    hcc38 = ad.read_h5ad(h38_path)
    print("Loading HCC1143...")
    hcc1143 = ad.read_h5ad(h1143_path)

    src_38 = build_source(hcc38, "HCC38", joint, highlight_genes=highlight_genes, label_genes=label_genes)
    src_1143 = build_source(hcc1143, "HCC1143", joint, highlight_genes=highlight_genes, label_genes=label_genes)
    print(f"HCC38: {len(src_38)} targets, HCC1143: {len(src_1143)} targets")

    source_tbl = combined_panel_e_source(src_38, src_1143)
    fig = build_figure_shift_colormap(src_38, src_1143)

    outp = out_dir / "panel_e"
    save_figure(fig, outp.with_suffix(".png"), outp.with_suffix(".pdf"))
    write_tsv(source_tbl, out_dir / PANEL_E_SOURCE_NAME)
    print(f"[OK] Wrote {outp.with_suffix('.png')}")
    print(f"[OK] Wrote {out_dir / PANEL_E_SOURCE_NAME}")


if __name__ == "__main__":
    main()
