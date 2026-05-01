from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.ticker import NullLocator
from scipy import stats
from matplotlib.patches import FancyBboxPatch, Rectangle

from wtbench.manuscript.figure_io import ensure_dir, repo_root, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import (
    COLORS,
    add_panel_heading,
    add_panel_label,
    apply_manuscript_style,
    clean_axes,
    finalize_manuscript_figure,
)
from wtbench.manuscript._palette import (
    FIG5_DUMBBELL_CONNECTOR,
    FIG5_ENDPOINT_CRISPR,
    FIG5_ENDPOINT_RNAI,
    FIG5_K562_BOX_13D_EDGE,
    FIG5_K562_BOX_13D_FILL,
    FIG5_K562_BOX_7D_EDGE,
    FIG5_K562_BOX_7D_FILL,
    FIG5_K562_JITTER,
    FIG5_K562_PAIR_LINE,
    FIG5_MEDIAN,
    FIG5_K562_BOXPLOT_MEDIAN,
    FIG5_TVD_CMAP_STOPS,
    FIG5_UMI_GROUP_LINE,
    VERMILLION,
)


FIGURE_ID = "figure6"
FIGURE_TITLE = "Covariate, endpoint, and temporal audits define the benchmark claim space"
SCRIPT_PATH = Path("scripts/manuscript/build_figure6_boundary.py")
CLAIM_BOUNDARY = (
    "Boundary audits define the benchmark's bounded claim scope: "
    "covariate boundary constrains fully deconfounded wording; "
    "endpoint hierarchy constrains RNAi from serving as the primary readout; "
    "temporal boundary constrains content-level replication in K562."
)

COVARIATE_SUMMARY = Path("reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv")
TEMPORAL_BRIDGE = Path("reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_bridge_summary.tsv")
TEMPORAL_DELTA = Path("reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_target_delta.tsv")
HCC_ENDPOINT = Path("reports/stage2_truth_driven_bridge/hcc38_hcc1143_rnai_endpoint_consistency/endpoint_consistency_summary.tsv")
K562_ENDPOINT = Path("reports/stage2_truth_driven_bridge/k562_rnai_endpoint_consistency/endpoint_consistency_summary.tsv")

COVARIATE_ORDER = [
    "barcode_gem_group",
    "transcriptome_detected_genes_quantile_bin",
    "transcriptome_total_signal_quantile_bin",
    "num_umis_over_threshold_bin",
    "num_umis_quantile_bin",
]
COVARIATE_LABELS = {
    "barcode_gem_group": "barcode gem group",
    "transcriptome_detected_genes_quantile_bin": "detected genes",
    "transcriptome_total_signal_quantile_bin": "UMI signal",
    "num_umis_over_threshold_bin": "UMI threshold",
    "num_umis_quantile_bin": "UMI quantile",
}
CONTEXT_ORDER = ["HCC38", "HCC1143", "K562 7d", "K562 13d"]
# Rank-bridge bar panel (standalone d): 7d / 13d = two neutral fills (not warm temporal sand).
RANK_7D_FILL = FIG5_K562_BOX_7D_FILL
RANK_13D_FILL = FIG5_K562_BOX_13D_FILL
FIG5_GRID = "#F0F0F0"  # unused in main F5 panels (grids off); kept for any legacy call
ALIGNED_RHO_LABEL = "Aligned Spearman ρ"
# Main composite heading typography matches the other manuscript figures.
FIG5_MAIN_TITLE_FS = 8.6
FIG5_MAIN_LETTER_FS = 9.0
FIG5_FONT_SCALE = 0.82
# transAxes x for "a" on left column; also defines figure-x alignment for "c" in the composite
FIG5_COMPOSITE_PANEL_A_LABEL_X = -0.07
# Widen xlim on the right so dumbbell + n-labels sit left; legend stays lower-right in axes space
FIG5_MAIN_ENDPOINT_XLIM = (0.20, 0.93)
# Standalone: c = K562 per-target |shift| (7d/13d); d = rank-bridge bar summary (not in main composite).
PANEL_WIDTHS = {"a": 3.85, "b": 3.55, "c": 3.1, "d": 3.1}
PANEL_HEIGHTS = {"a": 2.95, "b": 2.5, "c": 1.55, "d": 1.45}
# Main-figure composite: 2×2 with c directly under a (same column width as a)
COMBINED_FIGSIZE_IN = (7.15, 4.55)
# Panels in Figure_5.png / combined source: rank-bridge (d) is supplementary standalone only
COMBINED_FIGURE_PANELS: tuple[str, ...] = ("a", "b", "c")
# Bottom row height ratio vs top row (panel c under a); vertical gap: COMBINED_HSPACE
COMBINED_ROW2_HEIGHT = 0.64
COMBINED_HSPACE = 0.11


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig6_boundary"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_5"


def manuscript_panel_dir(root: Path) -> Path:
    return manuscript_figure_dir(root) / "panels"


def overview_asset_dir(root: Path) -> Path:
    return output_dir(root) / "overview_assets"


def manuscript_overview_asset_dir(root: Path) -> Path:
    return manuscript_figure_dir(root) / "overview_assets"


def input_paths(root: Path) -> list[Path]:
    return [
        root / COVARIATE_SUMMARY,
        root / TEMPORAL_BRIDGE,
        root / TEMPORAL_DELTA,
        root / HCC_ENDPOINT,
        root / K562_ENDPOINT,
    ]


def write_panel(
    *,
    root: Path,
    panel_id: str,
    panel_title: str,
    source_df: pd.DataFrame,
    render: Callable[[plt.Axes, pd.DataFrame], None],
    width: float = 3.2,
    height: float = 2.35,
) -> dict[str, Path]:
    pdir = ensure_dir(panel_dir(root))
    manuscript_pdir = ensure_dir(manuscript_panel_dir(root))
    stem = f"{FIGURE_ID}_panel{panel_id}"
    manuscript_stem = f"Figure_5_panel_{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    manuscript_source_path = write_tsv(source_df, manuscript_pdir / f"{manuscript_stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    png_path = pdir / f"{stem}.png"
    pdf_path = pdir / f"{stem}.pdf"
    manuscript_png_path = manuscript_pdir / f"{manuscript_stem}.png"
    manuscript_pdf_path = manuscript_pdir / f"{manuscript_stem}.pdf"
    for path in [png_path, pdf_path, manuscript_png_path, manuscript_pdf_path]:
        ensure_dir(path.parent)
    finalize_manuscript_figure(fig, font_scale=FIG5_FONT_SCALE)
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(manuscript_png_path, dpi=300, bbox_inches="tight")
    fig.savefig(manuscript_pdf_path, bbox_inches="tight")
    output_paths = [png_path, pdf_path]
    plt.close(fig)
    manifest_path = pdir / f"{stem}_manifest.json"
    write_panel_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        panel_id=f"{FIGURE_ID}{panel_id}",
        panel_title=panel_title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    write_panel_manifest(
        manifest_path=manuscript_pdir / f"{manuscript_stem}_manifest.json",
        repo_root=root,
        panel_id=f"figure5{panel_id}",
        panel_title=panel_title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=manuscript_source_path,
        output_paths=[manuscript_png_path, manuscript_pdf_path],
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def _place_figure5_composite_letters(fig: plt.Figure, ax_a: plt.Axes, ax_b: plt.Axes, ax_c: plt.Axes) -> None:
    """Align `a` and `c` on the same figure-x; place `b` in the top-row gap between columns a and b."""
    bb_a = ax_a.get_position()
    bb_b = ax_b.get_position()
    bb_c = ax_c.get_position()
    x_left = bb_a.x0 + FIG5_COMPOSITE_PANEL_A_LABEL_X * bb_a.width
    y_row = bb_a.y0 + 1.01 * bb_a.height
    fs = FIG5_MAIN_LETTER_FS
    xa = (x_left - bb_a.x0) / bb_a.width
#     add_panel_label(ax_a, "a", x=xa, y=1.01, fontsize=fs)  # PIL
    xc = (x_left - bb_c.x0) / bb_c.width
#     add_panel_label(ax_c, "c", x=xc, y=1.01, fontsize=fs)  # PIL
    x_gap = (bb_a.x1 + bb_b.x0) / 2
    fig.text(
        x_gap,
        y_row,
        "b",
        transform=fig.transFigure,
        ha="center",
        va="bottom",
        fontsize=fs,
        fontweight="bold",
        color=COLORS["text"],
    )


def write_overview_asset(root: Path, source_df: pd.DataFrame) -> dict[str, Path]:
    """Save the boundary gate flow outside the Figure 5 panel set for future Figure 1a reuse."""
    out = ensure_dir(overview_asset_dir(root))
    manuscript_out = ensure_dir(manuscript_overview_asset_dir(root))
    source_path = write_tsv(source_df, out / "boundary_gate_flow_overview_source_data.tsv")
    manuscript_source_path = write_tsv(source_df, manuscript_out / "boundary_gate_flow_overview_source_data.tsv")

    fig, ax = plt.subplots(figsize=(6.8, 1.5))
    render_panel_a(ax, source_df)
    finalize_manuscript_figure(fig, font_scale=FIG5_FONT_SCALE)
    for path in [
        out / "boundary_gate_flow_overview.png",
        out / "boundary_gate_flow_overview.pdf",
        manuscript_out / "boundary_gate_flow_overview.png",
        manuscript_out / "boundary_gate_flow_overview.pdf",
    ]:
        ensure_dir(path.parent)
        fig.savefig(path, dpi=300 if path.suffix == ".png" else None, bbox_inches="tight")
    plt.close(fig)
    return {
        "source": source_path,
        "manuscript_source": manuscript_source_path,
        "png": out / "boundary_gate_flow_overview.png",
        "pdf": out / "boundary_gate_flow_overview.pdf",
    }


def load_covariate(root: Path) -> pd.DataFrame:
    cov = pd.read_csv(root / COVARIATE_SUMMARY, sep="\t")
    cov["strat_column"] = pd.Categorical(cov["strat_column"], categories=COVARIATE_ORDER, ordered=True)
    cov = cov.sort_values(["strat_column", "cell_line"]).reset_index(drop=True)
    return cov


def load_endpoint(root: Path) -> pd.DataFrame:
    hcc = pd.read_csv(root / HCC_ENDPOINT, sep="\t")
    k562 = pd.read_csv(root / K562_ENDPOINT, sep="\t")
    df = pd.concat([hcc, k562], ignore_index=True)
    bridge = df.loc[
        df["summary_kind"].eq("truth_endpoint_bridge")
        & df["truth_metric"].eq("real_shift_mean_abs")
        & df["depmap_endpoint"].eq("depmap_gene_dependency")
    ].copy()
    pivot = bridge.pivot_table(index="timepoint", columns="platform_pair", values="spearman", aggfunc="first")
    if not (pivot["crispr"] > pivot["rnai"]).all():
        raise RuntimeError("Fig. 5 endpoint sanity check failed: CRISPR is not stronger than RNAi in every context.")
    bridge["context"] = bridge["timepoint"].map({"7d": "K562 7d", "13d": "K562 13d"}).fillna(bridge["timepoint"])
    bridge["context"] = pd.Categorical(bridge["context"], categories=CONTEXT_ORDER, ordered=True)
    return bridge.sort_values(["context", "platform_pair"]).reset_index(drop=True)


def load_temporal(root: Path) -> pd.DataFrame:
    bridge = pd.read_csv(root / TEMPORAL_BRIDGE, sep="\t")
    primary = bridge.loc[
        bridge["truth_metric"].eq("real_shift_mean_abs") & bridge["depmap_endpoint"].eq("depmap_gene_dependency")
    ].copy()
    primary["timepoint"] = pd.Categorical(primary["timepoint"], categories=["7d", "13d"], ordered=True)
    primary = primary.sort_values("timepoint").reset_index(drop=True)
    vals = primary.set_index("timepoint")
    if float(vals.loc["7d", "aligned_spearman"]) <= float(vals.loc["13d", "aligned_spearman"]):
        raise RuntimeError("Fig. 5 temporal sanity check failed: 7d rank alignment is not stronger than 13d.")
    if float(vals.loc["13d", "mean_truth_metric"]) <= float(vals.loc["7d", "mean_truth_metric"]):
        raise RuntimeError("Fig. 5 temporal sanity check failed: 13d mean shift is not stronger than 7d.")
    return primary


def load_temporal_delta(root: Path) -> pd.DataFrame:
    delta = pd.read_csv(root / TEMPORAL_DELTA, sep="\t")
    delta = delta.sort_values("delta_13d_minus_7d_real_shift_mean_abs").reset_index(drop=True)
    delta["target_order"] = np.arange(len(delta))
    return delta


def _format_pvalue_two_sided(p: float) -> str:
    if not np.isfinite(p):
        return "P = —"
    if p < 1e-4:
        return f"P = {p:.1e}"
    if p < 0.001:
        return "P < 0.001"
    return f"P = {p:.3f}"


def _covariate_cmap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list("covariate_tvd_bluegray", list(FIG5_TVD_CMAP_STOPS))


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Thin navigation strip for the boundary gates."""
    ax.set_axis_off()
    ax.set_title("Boundary gate flow", loc="left", pad=0)

    positions = [0.10, 0.34, 0.58, 0.84]
    width = 0.18
    height = 0.48
    colors = [COLORS["boundary"], COLORS["primary_qualified"], COLORS["supporting"], "#6A6A6A"]
    labels = [
        ("Covariate gate", "UMI / detected genes /\ngem group"),
        ("Endpoint gate", "CRISPR > RNAi"),
        ("Temporal gate", "K562 7d / 13d"),
        ("Bounded claim scope", "primary / supplementary /\nsensitivity / not claimed"),
    ]
    for i, (x, color, text) in enumerate(zip(positions, colors, labels)):
        box = FancyBboxPatch(
            (x - width / 2, 0.27),
            width,
            height,
            boxstyle="round,pad=0.02,rounding_size=0.03",
            transform=ax.transAxes,
            facecolor="white",
            edgecolor=color,
            linewidth=1.0,
        )
        ax.add_patch(box)
        ax.text(x, 0.60, text[0], ha="center", va="center", fontsize=7.2, fontweight="bold", color=color, transform=ax.transAxes)
        ax.text(x, 0.41, text[1], ha="center", va="center", fontsize=5.7, color="#4A4A4A", transform=ax.transAxes)
        if i < len(positions) - 1:
            ax.annotate(
                "",
                xy=(positions[i + 1] - width / 2 - 0.02, 0.51),
                xytext=(x + width / 2 + 0.02, 0.51),
                arrowprops=dict(arrowstyle="->", lw=0.8, color="#8A8A8A"),
                transform=ax.transAxes,
            )

#     add_panel_label(ax, "a", x=-0.05, y=1.01)  # PIL


def render_panel_b(
    ax: plt.Axes, df: pd.DataFrame, *, composite: bool = False, main_fig: bool = False, draw_panel_letter: bool = True
) -> None:
    """Heatmap with target-level threshold-hit glyphs.

    When ``composite`` is True (Figure 5 assembly), the grid is widened in axes coordinates so the
    heatmap reaches farther right, removing the large empty margin that otherwise sits before panel b.
    """
    wide_layout = composite or main_fig
    ax.set_axis_off()
    add_panel_heading(
        ax,
        "",
        "Covariate boundary",
        title_x=0.00,
        y=1.055,
        label_fontsize=FIG5_MAIN_LETTER_FS if main_fig else 8.5,
        title_fontsize=FIG5_MAIN_TITLE_FS if main_fig else 8.4,
    )

    ordered = df.copy()
    ordered["strat_column"] = pd.Categorical(ordered["strat_column"], categories=COVARIATE_ORDER, ordered=True)
    ordered = ordered.sort_values(["strat_column", "cell_line"])
    pivot_mean = ordered.pivot(index="strat_column", columns="cell_line", values="mean_tvd").reindex(COVARIATE_ORDER)
    pivot_hits = ordered.pivot(index="strat_column", columns="cell_line", values="n_targets_tvd_gt_0.25").reindex(COVARIATE_ORDER)

    if main_fig:
        # Larger painted grid in 2×2; keep room below for two-row legend (ticks must clear glyph row)
        x0, y0 = 0.10, 0.90
        cell_w, cell_h = 0.38, 0.136
    elif wide_layout:
        # Two wide columns; lower grid slightly for more headroom; legend more separated below.
        x0, y0 = 0.108, 0.83
        cell_w, cell_h = 0.35, 0.135
    else:
        x0, y0 = 0.175, 0.90
        cell_w, cell_h = 0.25, 0.135
    cmap = _covariate_cmap()
    norm = Normalize(vmin=0.05, vmax=0.14)
    # UMI-related rows: flat vertical divider (palette), not gold dendrogram prongs
    if main_fig:
        branch_x = -0.072
    elif wide_layout:
        branch_x = -0.063
    else:
        branch_x = -0.055
    branch_y = [y0 - (ri + 1) * cell_h + cell_h / 2 for ri in [2, 3, 4]]
    y_umit = y0 - 2 * cell_h
    y_umib = y0 - 5 * cell_h
    ax.plot(
        [branch_x, branch_x],
        [y_umit, y_umib],
        color=FIG5_UMI_GROUP_LINE,
        lw=2.0,
        solid_capstyle="butt",
        transform=ax.transAxes,
        clip_on=False,
        zorder=0,
    )
    umi_label_x = branch_x - 0.024
    ax.text(
        umi_label_x,
        np.mean(branch_y),
        "UMI-related axes",
        ha="center",
        va="center",
        rotation=90,
        fontsize=5.2,
        color="#4A4A4A",
        transform=ax.transAxes,
        clip_on=False,
    )

    col_fs = 5.8 if wide_layout else 6.3
    for ci, col in enumerate(["HCC38", "HCC1143"]):
        ax.text(x0 + ci * cell_w + cell_w / 2, y0 + 0.03, col, ha="center", va="bottom", fontsize=col_fs, fontweight="bold", transform=ax.transAxes)

    label_r = x0 - 0.012
    row_labels = [COVARIATE_LABELS[key] for key in COVARIATE_ORDER]
    t_fs = 5.2 if wide_layout else 5.7
    for ri, row_key in enumerate(COVARIATE_ORDER):
        y = y0 - (ri + 1) * cell_h
        ax.text(label_r, y + cell_h / 2, row_labels[ri], ha="right", va="center", fontsize=5.7, color="#444444", transform=ax.transAxes)
        for ci, col in enumerate(["HCC38", "HCC1143"]):
            x = x0 + ci * cell_w
            value = float(pivot_mean.loc[row_key, col])
            hits = int(pivot_hits.loc[row_key, col])
            face = cmap(norm(value))
            edge = VERMILLION if hits > 0 else "#D7D7D7"
            rect = Rectangle(
                (x, y),
                cell_w,
                cell_h,
                transform=ax.transAxes,
                facecolor=face,
                edgecolor=edge,
                linewidth=1.0 if hits > 0 else 0.6,
            )
            ax.add_patch(rect)
            ax.text(
                x + cell_w / 2,
                y + cell_h / 2,
                f"{value:.3f}",
                ha="center",
                va="center",
                fontsize=t_fs,
                fontweight="bold" if hits > 0 else "normal",
                color="#333333",
                transform=ax.transAxes,
                zorder=3,
            )

    # Encoding key just below the heatmap (wording matches caption, not "shade"/"dot" shorthand)
    y_grid_bottom = y0 - 5 * cell_h
    if main_fig:
        # Tight two-row key (no numeric ticks under the gradient); match wide_layout spacing
        y_leg1 = y_grid_bottom - 0.062
        y_leg2 = y_grid_bottom - 0.118
    elif wide_layout:
        y_leg1 = y_grid_bottom - 0.065
        y_leg2 = y_grid_bottom - 0.118
    else:
        y_leg1 = y_grid_bottom - 0.038
        y_leg2 = y_grid_bottom - 0.072
    if main_fig:
        grad_w, grad_h = 0.10, 0.022
    else:
        grad_w, grad_h = 0.14, 0.022
    grad_ax = ax.inset_axes([x0, y_leg1, grad_w, grad_h])
    grad = np.linspace(0, 1, 256).reshape(1, -1)
    grad_ax.imshow(grad, aspect="auto", cmap=cmap)
    grad_ax.set_axis_off()
    ax.text(
        x0 + grad_w + 0.014,
        y_leg1 + 0.002,
        "Mean target-control TVD",
        fontsize=5.0 if main_fig else 4.8,
        color="#4A4A4A",
        va="bottom",
        transform=ax.transAxes,
    )
    key_w, key_h = (0.030, 0.020) if main_fig else (0.036, 0.022)
    ax.add_patch(
        Rectangle(
            (x0, y_leg2 - 0.010),
            key_w,
            key_h,
            transform=ax.transAxes,
            facecolor="white",
            edgecolor=VERMILLION,
            linewidth=1.0,
        )
    )
    ax.text(
        x0 + key_w + 0.014,
        y_leg2,
        "Cell has at least one target with TVD > 0.25",
        fontsize=5.0 if main_fig else 4.8,
        color="#4A4A4A",
        va="center",
        transform=ax.transAxes,
    )
def render_panel_c(ax: plt.Axes, df: pd.DataFrame, *, compact: bool = False, main_fig: bool = False) -> None:
    """Temporal boundary: K562 7d vs 13d rank bridge Spearman (summary bridge strength)."""
    t_fs = 4.3 if compact else 6
    lab_fs = 4.4 if compact else 5.6
    ylabel_fs = 4.6 if compact else 6
    ylp = 0 if compact else 2
    if main_fig:
        ax.set_title("K562 temporal rank bridge", loc="left", pad=0, fontsize=FIG5_MAIN_TITLE_FS)
    else:
        title = "K562 rank bridge" if compact else "Temporal boundary (rank bridge)"
        t_pad = 1 if compact else 2
        ax.set_title(title, loc="left", pad=t_pad, fontsize=t_fs if compact else 10.5)
    temporal = df.loc[df["subpanel"].eq("temporal")].copy().sort_values("timepoint")
    if temporal.empty:
    #     add_panel_label(ax, "d", x=-0.07, y=1.01, fontsize=FIG5_MAIN_LETTER_FS if main_fig else 8.5)  # PIL
        return
    if main_fig:
        t_fs = 8.0
        lab_fs = 7.6
        ylabel_fs = 8.0
        ylp = 2
    colors = (RANK_7D_FILL, RANK_13D_FILL) if (main_fig or compact) else (FIG5_K562_BOX_7D_FILL, FIG5_K562_BOX_13D_FILL, "#A0A0A0")
    if compact and not main_fig:
        # Horizontal bars: Spearman on x, timepoint on y (legacy narrow column; 7d on top)
        n = len(temporal)
        y = np.arange(n, dtype=float)
        vals = temporal["aligned_spearman"].to_numpy()
        heights = 0.44
        clist = [colors[i % len(colors)] for i in range(n)]
        bars = ax.barh(
            y,
            vals,
            height=heights,
            color=clist,
            align="center",
        )
        for yi, v in zip(y, vals):
            ax.text(
                min(v + 0.02, 0.84),
                yi,
                f"{v:.3f}",
                va="center",
                ha="left",
                fontsize=lab_fs,
            )
        ax.set_yticks(y)
        ax.set_yticklabels([str(t) for t in temporal["timepoint"]], fontsize=4.3)
        ax.set_xlim(0, 0.80)
        ax.set_xlabel(ALIGNED_RHO_LABEL, fontsize=ylabel_fs, labelpad=1)
        ax.set_ylabel("")
        ax.invert_yaxis()
        ax.grid(axis="x", color=FIG5_GRID, linewidth=0.4)
    elif main_fig:
        x = np.arange(len(temporal))
        bw = 0.5
        bar_colors = [RANK_7D_FILL, RANK_13D_FILL][: len(temporal)]
        bars = ax.bar(
            x,
            temporal["aligned_spearman"],
            width=bw,
            color=bar_colors,
        )
        y_off = 0.025
        for xi, value in zip(x, temporal["aligned_spearman"]):
            ax.text(
                xi,
                value + y_off,
                r"$\rho$" + f" = {value:.3f}",
                ha="center",
                va="bottom",
                fontsize=lab_fs,
            )
        ax.set_xticks(x)
        ax.set_xticklabels([str(t) for t in temporal["timepoint"]], fontsize=7.6)
        ax.set_ylim(0, 0.80)
        ax.set_ylabel(ALIGNED_RHO_LABEL, fontsize=ylabel_fs, labelpad=ylp)
    else:
        x = np.arange(len(temporal))
        bw = 0.55
        bars = ax.bar(
            x,
            temporal["aligned_spearman"],
            width=bw,
            color=[colors[i % len(colors)] for i in range(len(temporal))],
        )
        y_off = 0.03
        for xi, value in zip(x, temporal["aligned_spearman"]):
            ax.text(xi, value + y_off, f"{value:.3f}", ha="center", va="bottom", fontsize=lab_fs)
        ax.set_xticks(x)
        ax.set_xticklabels(temporal["timepoint"], fontsize=6.0)
        ax.set_ylim(0, 0.86)
        ylab = "Rank bridge Spearman"
        ax.set_ylabel(ylab, fontsize=ylabel_fs, labelpad=ylp)
        ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    clean_axes(ax)
    for bar in bars:
        bar.set_linewidth(0)
    plf = FIG5_MAIN_LETTER_FS if main_fig else 8.5
    plx = -0.1 if (compact and not main_fig) else -0.08
#     add_panel_label(ax, "d", x=plx, y=1.01, fontsize=plf)  # PIL


def render_temporal_target_shift_box(
    ax: plt.Axes,
    df: pd.DataFrame,
    *,
    compact: bool = False,
    main_fig: bool = False,
    draw_panel_letter: bool = True,
    fig5_composite: bool = False,
) -> None:
    """K562 per-target 7d vs 13d |real shift| with paired boxplot, lines, and two-sided Wilcoxon P."""
    if main_fig:
        add_panel_heading(
            ax,
            "",
            "K562 temporal shift magnitude",
            title_x=0.00,
            y=1.055,
            label_fontsize=FIG5_MAIN_LETTER_FS,
            title_fontsize=FIG5_MAIN_TITLE_FS,
        )
    else:
        ti_fs = 4.2 if compact else 5.6
        add_panel_heading(
            ax,
            "",
            "Per-target |shift|" if compact else "Per-target |shift| (K562)",
            title_x=0.00,
            y=1.055,
            label_fontsize=8.5,
            title_fontsize=ti_fs,
        )
    delta = df.loc[df["subpanel"].eq("delta")].copy().sort_values("delta_13d_minus_7d_real_shift_mean_abs")
    if delta.empty:
        return
    y7 = delta["7d_real_shift_mean_abs"].to_numpy(dtype=float)
    y13 = delta["13d_real_shift_mean_abs"].to_numpy(dtype=float)
    n = len(y7)
    p_w: float
    try:
        p_w = float(stats.wilcoxon(y7, y13, alternative="two-sided", method="auto").pvalue)
    except (ValueError, TypeError):
        p_w = float("nan")

    b_w = 0.28 if compact else 0.36
    sc_s = 8 if compact else 14
    ptxt = _format_pvalue_two_sided(p_w)
    pfs = 3.5 if compact else 5.0
    y7p, y13p = y7, y13
    if main_fig:
        pfs = 7.5
        b_w = 0.32
        sc_s = 9
        y7p = y7 * 1.0e3
        y13p = y13 * 1.0e3

    bp = ax.boxplot(
        [y7p, y13p],
        positions=[0, 1],
        widths=b_w,
        patch_artist=True,
        showfliers=False,
        whis=(5, 95),
        zorder=2,
    )
    _bedges = (FIG5_K562_BOX_7D_EDGE, FIG5_K562_BOX_13D_EDGE) if main_fig else (None, None)
    bcols = (FIG5_K562_BOX_7D_FILL, FIG5_K562_BOX_13D_FILL) if main_fig else (None, None)
    for k, box in enumerate(bp["boxes"]):
        if main_fig:
            box.set_facecolor(bcols[k])
            box.set_edgecolor(_bedges[k])
        else:
            box.set_facecolor("#D8D6D3")
            box.set_edgecolor("#8A7A5A")
        box.set_alpha(1.0 if main_fig else 0.55)
        box.set_linewidth(1.0 if main_fig else 0.6)
    for i, w in enumerate(bp["whiskers"]):
        bi = i // 2
        w.set_color(_bedges[bi] if main_fig else "#3A3A3A")
        w.set_linewidth(0.6)
    for i, c in enumerate(bp["caps"]):
        bi = i // 2
        c.set_color(_bedges[bi] if main_fig else "#3A3A3A")
        c.set_linewidth(0.6)
    for m in bp["medians"]:
        m.set_color(FIG5_K562_BOXPLOT_MEDIAN if main_fig else FIG5_MEDIAN)
        m.set_linewidth(1.5 if main_fig else 0.65)

    rng = np.random.default_rng(0)
    jit = (rng.random(n) - 0.5) * 0.12
    lw = 0.4 if (compact or not main_fig) else 0.5
    line_col = FIG5_K562_PAIR_LINE if main_fig else "#8C8C8C"
    for a, b, j in zip(y7p, y13p, jit):
        ax.plot(
            [0.0 + j, 1.0 + j],
            [a, b],
            color=line_col,
            linewidth=0.5 if main_fig else lw,
            zorder=1,
            alpha=1.0 if main_fig else 0.35,
        )
    jcol = FIG5_K562_JITTER if main_fig else "#2A2A2A"
    ja = 0.85 if main_fig else 0.45
    ax.scatter(0.0 + jit, y7p, s=sc_s, c=jcol, alpha=ja, zorder=3, linewidths=0)
    ax.scatter(1.0 + jit, y13p, s=sc_s, c=jcol, alpha=ja, zorder=3, linewidths=0)
    if main_fig:
        _pty = 0.91 if fig5_composite else 0.94
        ax.text(
            0.5,
            _pty,
            f"paired Wilcoxon, {ptxt}",
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=7.5,
            fontweight="bold",
            color=COLORS["text"],
        )
    elif compact:
        ax.text(
            0.5,
            0.99,
            f"Wilcoxon {ptxt}\n(n = {n})",
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=pfs,
            color="#2A2A2A",
            linespacing=1.05,
        )
    else:
        ax.text(
            0.5,
            0.99,
            f"paired Wilcoxon\n{ptxt}\n(n = {n})",
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=pfs,
            color="#2A2A2A",
            linespacing=1.1,
        )
    ax.set_xlim((-0.32, 1.32) if compact else (-0.35, 1.35))
    ylo = min(float(y7p.min()), float(y13p.min()))
    yhi = max(float(y7p.max()), float(y13p.max()))
    pad = max((yhi - ylo) * 0.1, 0.3 if main_fig else 0.0003)
    top_mul = 1.02 if (main_fig and fig5_composite) else (1.1 if compact or main_fig else 1.5)
    ax.set_ylim(ylo - pad, yhi + pad * top_mul)
    ax.set_xticks([0, 1])
    tickx = 7.6 if main_fig else (3.8 if compact else 5.4)
    ticky = 7.5 if main_fig else (3.7 if compact else 4.8)
    ax.set_xticklabels(["7d", "13d"], fontsize=tickx)
    if main_fig:
        ax.set_ylabel(r"Mean $|$real shift$|$ ($\times 10^{-3}$)", fontsize=8.0, labelpad=1)
    else:
        ylab = "|shift| (mean abs.)" if compact else "target |real shift| (mean abs.)"
        ax.set_ylabel(ylab, fontsize=3.8 if compact else 5.4, labelpad=0)
    if not main_fig:
        ax.grid(axis="y", color=COLORS["grid"], linewidth=0.4)
    ax.tick_params(axis="x", labelsize=tickx, pad=0.5)
    ax.tick_params(axis="y", labelsize=ticky, pad=0.5)
    clean_axes(ax)

def render_endpoint_hierarchy(
    ax: plt.Axes,
    df: pd.DataFrame,
    *,
    compact: bool = False,
    plot_ax: plt.Axes | None = None,
    main_fig: bool = False,
    draw_panel_letter: bool = True,
) -> None:
    """Endpoint hierarchy as a paired dumbbell plot.

    If ``plot_ax`` is set (composite figure), the title and panel label use ``ax`` (full-height, aligned with
    panels a/b); data draw on ``plot_ax`` (e.g. inset). Otherwise all drawing uses ``ax`` (single-panel export).
    """
    pax = plot_ax if plot_ax is not None else ax
    if plot_ax is not None:
        add_panel_heading(ax, "", "Endpoint hierarchy", title_x=0.00, y=1.055)
        ax.set_axis_off()
    elif main_fig:
        add_panel_heading(
            ax,
            "",
            "Endpoint hierarchy",
            title_x=0.00,
            y=1.055,
            label_fontsize=FIG5_MAIN_LETTER_FS,
            title_fontsize=FIG5_MAIN_TITLE_FS,
        )
    else:
        add_panel_heading(ax, "", "Endpoint hierarchy", title_x=0.00, y=1.055)

    plot = df.copy().sort_values("context")
    crispr = plot.loc[plot["platform_pair"].eq("crispr")].set_index("context").loc[CONTEXT_ORDER].reset_index()
    rnai = plot.loc[plot["platform_pair"].eq("rnai")].set_index("context").loc[CONTEXT_ORDER].reset_index()
    y = np.arange(len(CONTEXT_ORDER))[::-1]

    n_fs = 5.0 if compact else 5.4
    sc_r, sc_c = (26, 30) if compact else (30, 34)
    lw = 0.5 if (main_fig and plot_ax is None) else (0.9 if compact else 1.0)
    if main_fig and plot_ax is None:
        n_fs = 7.2
        y_fs = 7.6
        sc_r, sc_c = 36, 49
    else:
        y_fs = 5.4 if compact else 6.0
    if compact and plot_ax is not None:
        y_lo, y_hi = -0.36, 3.24
    elif compact and not main_fig:
        y_lo, y_hi = -0.28, 3.22
    else:
        y_lo, y_hi = -0.25, len(CONTEXT_ORDER) - 0.75
    if main_fig and plot_ax is None:
        xlab_pad = 2
    elif plot_ax is not None:
        xlab_pad = 1
    else:
        xlab_pad = 0 if compact else 1
    if main_fig and plot_ax is None:
        leg_fs = 7.5
    else:
        leg_fs = 3.7 if (compact and plot_ax is not None) else (4.8 if compact else 5.2)
    n_label_dx = 0.014 if main_fig else 0.020

    for yi, ctx, c_val, r_val, c_n, r_n in zip(
        y,
        CONTEXT_ORDER,
        crispr["spearman"],
        rnai["spearman"],
        crispr["n_shared_targets"],
        rnai["n_shared_targets"],
    ):
        pax.plot([r_val, c_val], [yi, yi], color=FIG5_DUMBBELL_CONNECTOR, lw=lw, zorder=1.25, solid_capstyle="round")
        pax.scatter(r_val, yi, s=sc_r, color=FIG5_ENDPOINT_RNAI, zorder=2, edgecolors="none")
        pax.scatter(c_val, yi, s=sc_c, color=FIG5_ENDPOINT_CRISPR, zorder=3, edgecolors="none")
        cni, cxi = int(min(c_n, r_n)), int(max(c_n, r_n))
        nlab = f"n = {cni}/{cxi}" if (main_fig and plot_ax is None) else f"n={cni}-{cxi}"
        pax.text(
            max(c_val, r_val) + n_label_dx,
            yi,
            nlab,
            va="center",
            fontsize=n_fs,
            color="#767676",
        )

    pax.set_yticks(y)
    pax.set_yticklabels(CONTEXT_ORDER, fontsize=y_fs)
    pax.set_ylim(y_lo, y_hi)
    if main_fig and plot_ax is None:
        pax.set_xlim(*FIG5_MAIN_ENDPOINT_XLIM)
    else:
        pax.set_xlim(0.20, 0.84)
    xlab_str = ALIGNED_RHO_LABEL if (main_fig and plot_ax is None) else "Bridge Spearman rho"
    xlab_s = 8.0 if (main_fig and plot_ax is None) else 6.0
    pax.set_xlabel(xlab_str, fontsize=xlab_s, labelpad=xlab_pad)
    if not (main_fig and plot_ax is None):
        gcol, gw = (FIG5_GRID, 0.4) if (main_fig and plot_ax is None) else (COLORS["grid"], 0.6)
        pax.grid(axis="x", color=gcol, linewidth=gw)
    clean_axes(pax)
    pax.tick_params(axis="y", length=0, pad=1)
    if main_fig and plot_ax is None:
        pax.grid(False)
        pax.xaxis.set_minor_locator(NullLocator())
        pax.yaxis.set_minor_locator(NullLocator())
    pax.scatter([], [], color=FIG5_ENDPOINT_CRISPR, label="CRISPR DepMap")
    pax.scatter([], [], color=FIG5_ENDPOINT_RNAI, label="RNAi DEMETER2")
    _legend_kwargs = {
        "fontsize": leg_fs,
        "handletextpad": 0.35,
        "borderpad": 0.35,
        "frameon": False,
    }
    if plot_ax is not None:
        # Slightly outside the data axes (x>1 in transAxes) so the legend is not in the plot interior.
        _leg = pax.legend(
            loc="lower left",
            bbox_to_anchor=(1.01, 0.02),
            ncol=1,
            labelspacing=0.45,
            borderaxespad=0.0,
            fancybox=False,
            **_legend_kwargs,
        )
        _leg.set_clip_on(False)
    elif main_fig:
        _leg_main = {**_legend_kwargs, "borderaxespad": 0.0, "borderpad": 0.35}
        pax.legend(
            loc="lower right",
            bbox_to_anchor=(0.995, 0.008),
            bbox_transform=pax.transAxes,
            ncol=1,
            labelspacing=0.35,
            fancybox=False,
            **_leg_main,
        )
    else:
        pax.legend(loc="lower right", fancybox=False, **_legend_kwargs)

# Panel b (endpoint dumbbell) — name kept for render_panel_by_id
render_panel_d = render_endpoint_hierarchy


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    cov = load_covariate(root)
    temporal = load_temporal(root)
    delta = load_temporal_delta(root)
    endpoint = load_endpoint(root)

    source_a = pd.DataFrame(
        [
            {"step": 1, "gate": "Covariate gate", "subtitle": "UMI / detected genes / gem group"},
            {"step": 2, "gate": "Endpoint gate", "subtitle": "CRISPR > RNAi"},
            {"step": 3, "gate": "Temporal gate", "subtitle": "K562 7d / 13d"},
            {"step": 4, "gate": "Bounded claim scope", "subtitle": "primary / supplementary / sensitivity / not claimed"},
        ]
    )

    source_b = cov[["cell_line", "strat_column", "mean_tvd", "n_targets_tvd_gt_0.25", "median_tvd"]].copy()

    source_c = delta[
        [
            "target_gene",
            "7d_real_shift_mean_abs",
            "13d_real_shift_mean_abs",
            "delta_13d_minus_7d_real_shift_mean_abs",
            "ratio_13d_over_7d_real_shift_mean_abs",
            "target_order",
        ]
    ].assign(subpanel="delta")
    source_d = temporal[
        ["timepoint", "aligned_spearman", "mean_truth_metric", "median_truth_metric"]
    ].assign(subpanel="temporal")
    source_endpoint = endpoint[["context", "platform_pair", "spearman", "n_shared_targets"]].copy()

    return {
        "overview": source_a,
        "a": source_b,
        "b": source_endpoint,
        "c": source_c,
        "d": source_d,
    }


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {
        "a": render_panel_b,
        "b": render_panel_d,
        "c": render_temporal_target_shift_box,
        "d": render_panel_c,
    }[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Covariate boundary",
        "b": "Endpoint hierarchy",
        "c": "Per-target temporal |shift|",
        "d": "Temporal boundary (rank bridge)",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    manuscript_out = ensure_dir(manuscript_figure_dir(root))
    figure_panels = list(COMBINED_FIGURE_PANELS)
    combined_source = pd.concat([sources[p].assign(panel=p) for p in figure_panels], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")
    manuscript_source_path = write_tsv(combined_source, manuscript_out / "Figure_5_source_data.tsv")

    fig = plt.figure(figsize=COMBINED_FIGSIZE_IN)
    # 2×2: a|b on top; c in bottom-left (same width as a, directly below a); bottom-right empty
    h2 = COMBINED_ROW2_HEIGHT
    gs = fig.add_gridspec(
        2,
        2,
        height_ratios=[1.05, h2],
        width_ratios=[1, 1],
        hspace=COMBINED_HSPACE,
        wspace=0.26,
    )
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    render_panel_b(ax_a, sources["a"], composite=True, main_fig=True, draw_panel_letter=True)
    render_panel_d(ax_b, sources["b"], compact=False, plot_ax=None, main_fig=True, draw_panel_letter=True)
    render_temporal_target_shift_box(
        ax_c, sources["c"], compact=False, main_fig=True, draw_panel_letter=True, fig5_composite=True
    )
    fig.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.07)

    png_path = out / f"{FIGURE_ID}.png"
    pdf_path = out / f"{FIGURE_ID}.pdf"
    manuscript_png = manuscript_out / "Figure_5.png"
    manuscript_pdf = manuscript_out / "Figure_5.pdf"
    for path in [png_path, pdf_path, manuscript_png, manuscript_pdf]:
        ensure_dir(path.parent)
    finalize_manuscript_figure(fig, font_scale=FIG5_FONT_SCALE)
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(manuscript_png, dpi=300, bbox_inches="tight")
    fig.savefig(manuscript_pdf, bbox_inches="tight")
    output_paths = [png_path, pdf_path]
    plt.close(fig)
    manifest_path = out / f"{FIGURE_ID}_panel_manifest.json"
    write_figure_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in figure_panels],
        combined_source_data_path=combined_source_path,
        output_paths=output_paths,
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )
    write_figure_manifest(
        manifest_path=manuscript_out / "Figure_5_panel_manifest.json",
        repo_root=root,
        figure_id="figure5",
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[
            manuscript_panel_dir(root) / f"Figure_5_panel_{p}_manifest.json"
            for p in figure_panels
        ],
        combined_source_data_path=manuscript_source_path,
        output_paths=[manuscript_png, manuscript_pdf],
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": combined_source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build manuscript Figure 5 boundary panels and assembly.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    apply_manuscript_style()
    sources = build_sources(root)
    write_overview_asset(root, sources["overview"])
    panel_outputs: dict[str, dict[str, Path]] = {}
    for panel_id in list("abcd"):
        panel_outputs[panel_id] = write_panel(
            root=root,
            panel_id=panel_id,
            panel_title=panel_title(panel_id),
            source_df=sources[panel_id],
            render=render_panel_by_id(panel_id),
            width=PANEL_WIDTHS[panel_id],
            height=PANEL_HEIGHTS[panel_id],
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
