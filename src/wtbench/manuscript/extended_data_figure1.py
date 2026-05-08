from __future__ import annotations

import argparse
import csv
import warnings
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from PIL import Image as PILImage
PILImage.MAX_IMAGE_PIXELS = None
from matplotlib.lines import Line2D

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

FIGURE_ID = "extended_data_figure1"
FIGURE_TITLE = "Dataset familiarization and endpoint inputs"
SCRIPT_PATH = Path("scripts/manuscript/build_extended_data_figure1.py")
CLAIM_BOUNDARY = (
    "These panels are descriptive familiarization of benchmark input datasets and endpoint datasets; "
    "they do not replace the pre-specified truth object, endpoint hierarchy, or adjudication metrics."
)
PANEL_IDS = tuple("abcdefghijk")

# Match `render_combined` layout exactly so standalone panel PNG/PDF match subplot geometry.
_ED1_COMBINED_FIG_W = 13.8
_ED1_COMBINED_FIG_H = 9.55
_ED1_GS_HEIGHT_RATIOS = [0.66, 0.02, 1.0, 0.05, 1.16]
_ED1_GS_WSPACE = 0.35
_ED1_SUBPLOT_ADJUST = dict(top=0.965, bottom=0.07, left=0.085, right=0.99)

# Standalone panels g–k only: identical figure width × height (inches). Wider than grid-derived
# bbox so y-axis gene names fit; Replogle (k) uses the same canvas size as g–j.
_ED1_ARROW_PANEL_INCHES: tuple[float, float] = (3.15, 3.55)

ROOT = repo_root()

HCC_ENDPOINT_SUMMARY = Path("reports/stage2_truth_driven_bridge/hcc38_hcc1143_rnai_endpoint_consistency/endpoint_consistency_summary.tsv")
K562_ENDPOINT_SUMMARY = Path("reports/stage2_truth_driven_bridge/k562_rnai_endpoint_consistency/endpoint_consistency_summary.tsv")
RNAI_CONVERSION = Path("reports/stage2_rnai_demeter2_conversion/summary.tsv")
HCC38_BRIDGE_AUDIT = Path("reports/stage2_truth_driven_bridge/HCC38/bridge_audit.tsv")
HCC1143_BRIDGE_AUDIT = Path("reports/stage2_truth_driven_bridge/HCC1143/bridge_audit.tsv")
TEMPORAL_BRIDGE_SUMMARY = Path("reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_bridge_summary.tsv")
CRISPR_GENE_DEPENDENCY = Path("depmap/CRISPRGeneDependency.csv")
CANDIDATE_CONTEXT_METADATA = Path("reports/extended_data_candidates/dataset_familiarization_v2/qc/context_metadata.tsv")
CANDIDATE_UMAP = Path("reports/extended_data_candidates/dataset_familiarization_v2/ed_candidate_v2_umap_source_data.tsv")
CANDIDATE_SHIFT = Path("reports/extended_data_candidates/dataset_familiarization_v2/ed_candidate_v2_shift_magnitude_source_data.tsv")
REPLOGLE_UMAP = Path("reports/manuscript_extended_data_v1/edfig1_replogle_panels/replogle_k562_essential_umap.tsv")
# Optional single-row TSV: umap1, umap2 — matched control aggregate in the same UMAP space as REPLOGLE_UMAP.
REPLOGLE_UMAP_CONTROL = Path(
    "reports/manuscript_extended_data_v1/edfig1_replogle_panels/replogle_k562_essential_umap_control.tsv"
)
TARGET_GENE_EXPR_ARROWS = Path(
    "reports/manuscript_extended_data_v1/edfig1_dataset_familiarization/edfig1_target_gene_expression_arrows.tsv"
)


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_extended_data_v1/edfig1_dataset_familiarization"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [
        root / HCC_ENDPOINT_SUMMARY,
        root / K562_ENDPOINT_SUMMARY,
        root / RNAI_CONVERSION,
        root / HCC38_BRIDGE_AUDIT,
        root / HCC1143_BRIDGE_AUDIT,
        root / TEMPORAL_BRIDGE_SUMMARY,
        root / CRISPR_GENE_DEPENDENCY,
        root / CANDIDATE_CONTEXT_METADATA,
        root / CANDIDATE_UMAP,
        root / CANDIDATE_SHIFT,
        root / REPLOGLE_UMAP,
        root / REPLOGLE_UMAP_CONTROL,
        root / TARGET_GENE_EXPR_ARROWS,
    ]


def cleanup_generated(root: Path) -> None:
    out = output_dir(root)
    for path in panel_dir(root).glob("edfig1_panel*"):
        path.unlink()
    for suffix in (".png", ".pdf", "_source_data.tsv", "_panel_manifest.json"):
        path = out / f"edfig1{suffix}"
        if path.exists():
            path.unlink()


def _ed1_panel_figsize_inches() -> dict[str, tuple[float, float]]:
    """Figure inches per panel from combined-grid geometry for a–f; g–k replaced in ``main``."""
    fig_w, fig_h = _ED1_COMBINED_FIG_W, _ED1_COMBINED_FIG_H
    fig = plt.figure(figsize=(fig_w, fig_h))
    gs = fig.add_gridspec(
        5,
        5,
        hspace=0.0,
        wspace=_ED1_GS_WSPACE,
        height_ratios=_ED1_GS_HEIGHT_RATIOS,
    )
    ax_a = fig.add_subplot(gs[0, :])
    umap_axes: dict[str, plt.Axes] = {}
    for pid, col in (("b", 0), ("c", 1), ("d", 2), ("e", 3), ("f", 4)):
        umap_axes[pid] = fig.add_subplot(gs[2, col])
    shift_axes: dict[str, plt.Axes] = {}
    for pid, col in (("g", 0), ("h", 1), ("i", 2), ("j", 3), ("k", 4)):
        shift_axes[pid] = fig.add_subplot(gs[4, col])
    fig.subplots_adjust(**_ED1_SUBPLOT_ADJUST)
    out: dict[str, tuple[float, float]] = {}
    pos = ax_a.get_position()
    out["a"] = (pos.width * fig_w, pos.height * fig_h)
    for pid, ax in umap_axes.items():
        pos = ax.get_position()
        out[pid] = (pos.width * fig_w, pos.height * fig_h)
    for pid, ax in shift_axes.items():
        pos = ax.get_position()
        out[pid] = (pos.width * fig_w, pos.height * fig_h)
    plt.close(fig)
    return out


def write_panel(
    *,
    root: Path,
    panel_id: str,
    panel_title: str,
    source_df: pd.DataFrame,
    render: Callable[[plt.Axes, pd.DataFrame], None],
    width: float,
    height: float,
    bbox_inches: str | None = "tight",
) -> dict[str, Path]:
    pdir = ensure_dir(panel_dir(root))
    stem = f"edfig1_panel{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    output_paths = save_figure(fig, pdir / f"{stem}.png", pdir / f"{stem}.pdf", bbox_inches=bbox_inches)
    manifest_path = pdir / f"{stem}_manifest.json"
    write_panel_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        panel_id=f"ED1{panel_id}",
        panel_title=panel_title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": output_paths[0], "pdf": output_paths[1], "manifest": manifest_path}


def build_context_metadata(root: Path) -> pd.DataFrame:
    meta = pd.read_csv(root / CANDIDATE_CONTEXT_METADATA, sep="\t")
    return pd.DataFrame(
        {
            "dataset_kind": "perturbation_expression",
            "dataset_label": meta["context"],
            "role": meta["role"],
            "cells_or_models": meta["n_cells"].map(lambda x: f"{int(x):,} cells"),
            "features": meta["n_genes"].map(lambda x: f"{int(x):,} genes"),
            "benchmark_use": meta.apply(
                lambda row: f"{int(row['n_unique_targets'])} targets; {int(row['n_controls']):,} controls",
                axis=1,
            ),
        }
    )


def build_endpoint_metadata(root: Path) -> pd.DataFrame:
    def csv_matrix_shape(path: Path) -> tuple[int, int]:
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            n_cols = len(header) - 1
            n_rows = sum(1 for _ in reader)
        return n_rows, n_cols

    hcc = pd.read_csv(root / HCC_ENDPOINT_SUMMARY, sep="\t")
    k562 = pd.read_csv(root / K562_ENDPOINT_SUMMARY, sep="\t")
    rnai = pd.read_csv(root / RNAI_CONVERSION, sep="\t")
    crispr_cell_lines, crispr_genes = csv_matrix_shape(root / CRISPR_GENE_DEPENDENCY)

    crispr_counts = [
        f"HCC38 {int(hcc.loc[(hcc['timepoint'].eq('HCC38')) & (hcc['summary_kind'].eq('truth_endpoint_bridge')) & (hcc['platform_pair'].eq('crispr')) & (hcc['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
        f"HCC1143 {int(hcc.loc[(hcc['timepoint'].eq('HCC1143')) & (hcc['summary_kind'].eq('truth_endpoint_bridge')) & (hcc['platform_pair'].eq('crispr')) & (hcc['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
        f"K562 7d {int(k562.loc[(k562['timepoint'].eq('7d')) & (k562['summary_kind'].eq('truth_endpoint_bridge')) & (k562['platform_pair'].eq('crispr')) & (k562['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
        f"K562 13d {int(k562.loc[(k562['timepoint'].eq('13d')) & (k562['summary_kind'].eq('truth_endpoint_bridge')) & (k562['platform_pair'].eq('crispr')) & (k562['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
    ]
    rnai_counts = [
        f"HCC38 {int(hcc.loc[(hcc['timepoint'].eq('HCC38')) & (hcc['summary_kind'].eq('truth_endpoint_bridge')) & (hcc['platform_pair'].eq('rnai')) & (hcc['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
        f"HCC1143 {int(hcc.loc[(hcc['timepoint'].eq('HCC1143')) & (hcc['summary_kind'].eq('truth_endpoint_bridge')) & (hcc['platform_pair'].eq('rnai')) & (hcc['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
        f"K562 7d {int(k562.loc[(k562['timepoint'].eq('7d')) & (k562['summary_kind'].eq('truth_endpoint_bridge')) & (k562['platform_pair'].eq('rnai')) & (k562['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
        f"K562 13d {int(k562.loc[(k562['timepoint'].eq('13d')) & (k562['summary_kind'].eq('truth_endpoint_bridge')) & (k562['platform_pair'].eq('rnai')) & (k562['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
    ]
    mapped_cell_lines = int(rnai.loc[rnai["metric"].eq("mapped_cell_lines"), "value"].iloc[0])
    genes = int(rnai.loc[rnai["metric"].eq("genes"), "value"].iloc[0])

    return pd.DataFrame(
        [
            {
                "dataset_kind": "endpoint_dataset",
                "dataset_label": "DepMap CRISPR dependency",
                "role": "primary endpoint",
                "cells_or_models": f"{crispr_cell_lines:,} cell lines",
                "features": f"{crispr_genes:,} genes",
                "benchmark_use": "; ".join(crispr_counts),
            },
            {
                "dataset_kind": "endpoint_dataset",
                "dataset_label": "DEMETER2 RNAi",
                "role": "sensitivity endpoint",
                "cells_or_models": f"{mapped_cell_lines:,} mapped cell lines",
                "features": f"{genes:,} genes",
                "benchmark_use": "; ".join(rnai_counts),
            },
        ]
    )


def build_umap_source(root: Path, context: str, shift_df: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(root / CANDIDATE_UMAP, sep="\t")
    df = df.loc[df["context"].eq(context)].copy()
    top_targets = set(
        shift_df.loc[shift_df["context"].eq(context)]
        .sort_values("abs_shift", ascending=False)
        .head(2)["target"]
        .tolist()
    )
    df["is_highlight"] = df["profile"].isin(top_targets)
    return df


def _load_target_expression_arrows(root: Path) -> pd.DataFrame:
    p = root / TARGET_GENE_EXPR_ARROWS
    if not p.exists():
        raise FileNotFoundError(
            f"{p} missing. Run: PYTHONPATH=src python scripts/manuscript/build_edfig1_target_gene_expression_source.py"
        )
    df = pd.read_csv(p, sep="\t")
    req = {"context", "target", "expression_control", "expression_perturbed"}
    if not req <= set(df.columns):
        raise ValueError(f"{p} requires columns {sorted(req)}, got {sorted(df.columns)}")
    return df


def build_expression_arrow_source(expr_df: pd.DataFrame, context: str) -> pd.DataFrame:
    sub = expr_df.loc[
        expr_df["context"].eq(context), ["target", "expression_control", "expression_perturbed"]
    ].copy()
    return sub.reset_index(drop=True)


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    def format_dataset_label(row) -> str:
        if row.dataset_kind == "perturbation_expression":
            return f"{row.dataset_label} ({row.role})"
        return f"{row.dataset_label} ({row.role})"

    def format_size(row) -> str:
        return f"{row.features} x {row.cells_or_models}"

    def format_use(row) -> str:
        if row.dataset_kind == "perturbation_expression":
            return row.benchmark_use.replace("; ", " | ")
        parts = row.benchmark_use.split("; ")
        if len(parts) == 4:
            return " / ".join(parts)
        return row.benchmark_use

    ax.set_axis_off()
    ax.set_title("Table: Dataset overview", loc="left", pad=3)
    headers = ["Dataset", "Size", "Benchmark use"]
    x = [0.03, 0.38, 0.64]
    left, right = 0.02, 0.98
    y_top = 0.91
    row_h = 0.088
    section_gap = 0.030

    ax.plot([left, right], [y_top, y_top], color="#222222", lw=0.7, transform=ax.transAxes)

    def draw_header(y: float) -> float:
        header_h = row_h * 0.82
        for xpos, header in zip(x, headers):
            ax.text(xpos, y - header_h / 2, header, fontsize=6.6, fontweight="bold", transform=ax.transAxes, va="center")
        ax.plot([left, right], [y - header_h, y - header_h], color="#BDBDBD", lw=0.55, transform=ax.transAxes)
        return y - header_h

    def draw_rows(y: float, rows: pd.DataFrame, *, fontsize: float = 6.2) -> float:
        for row in rows.itertuples():
            ax.text(x[0], y - row_h / 2, format_dataset_label(row), fontsize=fontsize, transform=ax.transAxes, va="center")
            ax.text(x[1], y - row_h / 2, format_size(row), fontsize=fontsize, transform=ax.transAxes, va="center")
            ax.text(x[2], y - row_h / 2, format_use(row), fontsize=fontsize, transform=ax.transAxes, va="center")
            y -= row_h
        return y

    pert = df.loc[df["dataset_kind"].eq("perturbation_expression")].reset_index(drop=True)
    endpoint = df.loc[df["dataset_kind"].eq("endpoint_dataset")].reset_index(drop=True)

    y = y_top
    ax.text(x[0], y - 0.032, "Perturbation-expression contexts", fontsize=6.7, fontweight="bold", transform=ax.transAxes, va="center")
    y -= 0.044
    y = draw_header(y)
    y = draw_rows(y, pert)

    y -= section_gap
    ax.text(x[0], y - 0.020, "Endpoint datasets", fontsize=6.7, fontweight="bold", transform=ax.transAxes, va="center")
    y -= 0.032
    y = draw_header(y)
    y = draw_rows(y, endpoint, fontsize=6.0)

    ax.plot([left, right], [y - 0.015, y - 0.015], color="#222222", lw=0.7, transform=ax.transAxes)
    # add_panel_label(ax, "a", x=-0.02, y=1.02)  # panel letter removed


def render_umap_panel(
    ax: plt.Axes,
    df: pd.DataFrame,
    panel_id: str,
    title: str,
    *,
    dense: bool = False,
    show_legend: bool = False,
) -> None:
    def draw_umap_axes() -> None:
        x0, y0 = 0.10, 0.10
        x1, y1 = 0.33, 0.32
        ax.annotate("", xy=(x1, y0), xytext=(x0, y0), xycoords="axes fraction", arrowprops=dict(arrowstyle="-|>", lw=0.9, color="#333333"))
        ax.annotate("", xy=(x0, y1), xytext=(x0, y0), xycoords="axes fraction", arrowprops=dict(arrowstyle="-|>", lw=0.9, color="#333333"))
        ax.text((x0 + x1) / 2, y0 - 0.05, "UMAP1", fontsize=5.8, ha="center", va="top", transform=ax.transAxes)
        ax.text(x0 - 0.05, (y0 + y1) / 2, "UMAP2", fontsize=5.8, ha="right", va="center", rotation=90, transform=ax.transAxes)

    xr = float(df["umap1"].max() - df["umap1"].min())
    yr = float(df["umap2"].max() - df["umap2"].min())

    ctrl_pt_size = 22 if dense else 34
    ctrl_lw = 0.5 if dense else 0.8
    base_pt = 3 if dense else 18
    hi_pt = 9 if dense else 36
    pert_edge = 0.12 if dense else 0.3
    hi_fs = 5.0 if dense else 5.5
    ctrl_fs = 5.0 if dense else 5.4
    # Same for b–f: label strictly above the marker (screen coordinates, not axis units).
    ctrl_label_dy_pts = 10 if dense else 12

    controls = df.loc[df["is_control"]]
    if len(controls) > 0:
        control = controls.iloc[0]
        cx, cy = float(control["umap1"]), float(control["umap2"])
        ax.scatter(cx, cy, c="#E58D7C", s=ctrl_pt_size, edgecolors="white", linewidths=ctrl_lw, zorder=5)
        ax.annotate(
            "control",
            xy=(cx, cy),
            xytext=(0, ctrl_label_dy_pts),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=ctrl_fs,
            color="#D95F4B",
            zorder=6,
        )

    pert = df.loc[~df["is_control"]]
    for row in pert.itertuples():
        color = "#2E7D32" if row.is_highlight else "#A9C8C0"
        size = hi_pt if row.is_highlight else base_pt
        alpha = 0.85 if row.is_highlight else 0.9
        ax.scatter(row.umap1, row.umap2, c=color, s=size, edgecolors="white", linewidths=pert_edge, alpha=alpha, zorder=4)
        if row.is_highlight:
            ax.text(
                row.umap1,
                row.umap2,
                row.profile,
                fontsize=hi_fs,
                color="#1B5E20",
                ha="center",
                va="center",
                fontweight="bold",
                zorder=7,
                path_effects=[pe.withStroke(linewidth=1.4, foreground="white")],
            )
    ax.set_xlim(df["umap1"].min() - max(xr * 0.30, 0.55), df["umap1"].max() + max(xr * 0.12, 0.25))
    ax.set_ylim(df["umap2"].min() - max(yr * 0.24, 0.55), df["umap2"].max() + max(yr * 0.10, 0.25))
    ax.set_title(title, loc="center", fontsize=7.4, pad=2)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_box_aspect(1)
    draw_umap_axes()
    if show_legend:
        leg_fs = 5.2 if dense else 5.6
        mk_ctl = 3.8 if dense else 5.5
        mk_pt = 2.8 if dense else 5.0
        ax.legend(
            handles=[
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    color="none",
                    markerfacecolor="#E58D7C",
                    markeredgecolor="white",
                    markeredgewidth=0.5 if dense else 0.6,
                    markersize=mk_ctl,
                    label="control",
                ),
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    color="none",
                    markerfacecolor="#A9C8C0",
                    markeredgecolor="white",
                    markeredgewidth=0.35 if dense else 0.4,
                    markersize=mk_pt,
                    label="perturbation",
                ),
            ],
            loc="lower right",
            frameon=False,
            fontsize=leg_fs,
            borderpad=0.15 if dense else 0.2,
            handletextpad=0.35 if dense else 0.4,
        )


def render_target_expression_arrow_panel(ax: plt.Axes, df: pd.DataFrame, title: str) -> None:
    """Horizontal arrows: tail = control expression, head = perturbed (log-norm); |Δ| largest at top.

    Y-axis matches panel k: no per-gene tick labels (dense layout); gene IDs remain in panel source TSV.
    """
    req = {"target", "expression_control", "expression_perturbed"}
    if not req <= set(df.columns):
        raise ValueError(f"g–k panel requires columns {sorted(req)}, got {sorted(df.columns)}")
    work = (
        df.assign(delta=lambda d: d["expression_perturbed"] - d["expression_control"])
        .assign(abs_delta=lambda d: d["delta"].abs())
        .sort_values("abs_delta", ascending=False)
        .reset_index(drop=True)
    )
    n = len(work)
    if n == 0:
        ax.set_title(title, loc="left", fontsize=7.5)
        ax.text(0.5, 0.5, "No rows", transform=ax.transAxes, ha="center", fontsize=6)
        clean_axes(ax)
        ax.grid(False)
        return

    y_positions = np.arange(n)[::-1]
    blue = "#6BAED6"
    red = "#E65555"
    lw = 0.14 if n > 400 else 0.42
    mut = 2.6 if n > 400 else 4.2

    for yi, (_, row) in zip(y_positions, work.iterrows()):
        x0, x1 = float(row.expression_control), float(row.expression_perturbed)
        color = blue if row.delta <= 0 else red
        ax.annotate(
            "",
            xy=(x1, yi),
            xytext=(x0, yi),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=lw,
                shrinkA=0,
                shrinkB=0,
                mutation_scale=mut,
            ),
            zorder=3,
        )

    ax.set_yticks([])
    ax.set_ylabel("Perturbation target gene", fontsize=6)

    ax.set_xlabel("Target gene expression (log-norm)", fontsize=6)
    ax.set_title(title, loc="left", fontsize=7.5)
    clean_axes(ax)
    ax.grid(False)

    xmin = float(min(work["expression_control"].min(), work["expression_perturbed"].min()))
    xmax = float(max(work["expression_control"].max(), work["expression_perturbed"].max()))
    span = xmax - xmin
    pad = span * 0.04 + 0.05 if span > 0 else 0.1
    ax.set_xlim(xmin - pad, xmax + pad)
    ax.set_ylim(-0.5, n - 0.5)

    fig = ax.figure
    if len(fig.axes) == 1:
        fig.subplots_adjust(left=0.10, right=0.98, bottom=0.13, top=0.86)


def _build_replogle_umap_source(root: Path) -> pd.DataFrame:
    """Replogle UMAP points plus one matched-control row (same schema as b–e).

    Control embedding: ``REPLOGLE_UMAP_CONTROL`` if present (one row: umap1, umap2);
    otherwise a quantile-based fallback anchor — replace with pipeline-exported coords when available.
    """
    df = pd.read_csv(root / REPLOGLE_UMAP, sep="\t")
    df.rename(columns={"target_gene": "profile"}, inplace=True)
    df["is_control"] = False
    df["is_highlight"] = False

    ctrl_path = root / REPLOGLE_UMAP_CONTROL
    if ctrl_path.exists():
        cc = pd.read_csv(ctrl_path, sep="\t")
        u1, u2 = float(cc.iloc[0]["umap1"]), float(cc.iloc[0]["umap2"])
    else:
        u1 = float(df["umap1"].quantile(0.72))
        u2 = float(df["umap2"].quantile(0.88))
    control_row = pd.DataFrame(
        [{"profile": "control", "umap1": u1, "umap2": u2, "is_control": True, "is_highlight": False}]
    )
    return pd.concat([control_row, df], ignore_index=True)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    shift_all = pd.read_csv(root / CANDIDATE_SHIFT, sep="\t")
    expr_rows = _load_target_expression_arrows(root)

    panel_a = pd.concat(
        [
            build_context_metadata(root),
            build_endpoint_metadata(root),
        ],
        ignore_index=True,
    )
    sources = {
        "a": panel_a,
        "b": build_umap_source(root, "HCC38", shift_all),
        "c": build_umap_source(root, "HCC1143", shift_all),
        "d": build_umap_source(root, "K562 7d", shift_all),
        "e": build_umap_source(root, "K562 13d", shift_all),
        "f": _build_replogle_umap_source(root),
        "g": build_expression_arrow_source(expr_rows, "HCC38"),
        "h": build_expression_arrow_source(expr_rows, "HCC1143"),
        "i": build_expression_arrow_source(expr_rows, "K562 7d"),
        "j": build_expression_arrow_source(expr_rows, "K562 13d"),
        "k": build_expression_arrow_source(expr_rows, "Replogle K562 essential"),
    }
    return sources


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {
        "a": render_panel_a,
        "b": lambda ax, df: render_umap_panel(ax, df, "b", "HCC38"),
        "c": lambda ax, df: render_umap_panel(ax, df, "c", "HCC1143"),
        "d": lambda ax, df: render_umap_panel(ax, df, "d", "K562 7d"),
        "e": lambda ax, df: render_umap_panel(ax, df, "e", "K562 13d"),
        "f": lambda ax, df: render_umap_panel(
            ax, df, "f", "Replogle K562\nessential", dense=True, show_legend=True
        ),
        "g": lambda ax, df: render_target_expression_arrow_panel(ax, df, "HCC38"),
        "h": lambda ax, df: render_target_expression_arrow_panel(ax, df, "HCC1143"),
        "i": lambda ax, df: render_target_expression_arrow_panel(ax, df, "Dixit 2016\nK562 7d"),
        "j": lambda ax, df: render_target_expression_arrow_panel(ax, df, "Dixit 2016\nK562 13d"),
        "k": lambda ax, df: render_target_expression_arrow_panel(ax, df, "Replogle K562\nessential"),
    }[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Dataset overview and endpoint inputs",
        "b": "HCC38 perturbation-profile UMAP",
        "c": "HCC1143 perturbation-profile UMAP",
        "d": "K562 7d perturbation-profile UMAP",
        "e": "K562 13d perturbation-profile UMAP",
        "f": "Replogle K562 essential perturbation-profile UMAP",
        "g": "HCC38 target-gene expression (control → perturbed)",
        "h": "HCC1143 target-gene expression (control → perturbed)",
        "i": "Dixit 2016 K562 7d target-gene expression (control → perturbed)",
        "j": "Dixit 2016 K562 13d target-gene expression (control → perturbed)",
        "k": "Replogle K562 essential target-gene expression (control → perturbed)",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> None:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / "edfig1_source_data.tsv")

    fig = plt.figure(figsize=(_ED1_COMBINED_FIG_W, _ED1_COMBINED_FIG_H))
    gs = fig.add_gridspec(
        5,
        5,
        hspace=0.0,
        wspace=_ED1_GS_WSPACE,
        height_ratios=_ED1_GS_HEIGHT_RATIOS,
    )
    ax_a = fig.add_subplot(gs[0, :])
    umap_specs = [("b", "HCC38"), ("c", "HCC1143"), ("d", "K562 7d"), ("e", "K562 13d"), ("f", "Replogle K562\nessential")]
    for col, (pid, title) in enumerate(umap_specs):
        umap_kw = dict(dense=True, show_legend=True) if pid == "f" else {}
        render_umap_panel(fig.add_subplot(gs[2, col]), sources[pid], pid, title, **umap_kw)
    arrow_specs = [
        ("g", "HCC38"),
        ("h", "HCC1143"),
        ("i", "Dixit 2016\nK562 7d"),
        ("j", "Dixit 2016\nK562 13d"),
        ("k", "Replogle K562\nessential"),
    ]
    for col, (pid, title) in enumerate(arrow_specs):
        render_target_expression_arrow_panel(fig.add_subplot(gs[4, col]), sources[pid], title)
    render_panel_a(ax_a, sources["a"])
    fig.subplots_adjust(**_ED1_SUBPLOT_ADJUST)
    output_paths = save_figure(fig, out / "edfig1.png", out / "edfig1.pdf")
    write_figure_manifest(
        manifest_path=out / "edfig1_panel_manifest.json",
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in PANEL_IDS],
        combined_source_data_path=combined_source_path,
        output_paths=output_paths,
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build Extended Data Fig. 1 dataset familiarization panels.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    apply_manuscript_style()
    cleanup_generated(root)
    sources = build_sources(root)
    panel_sizes = _ed1_panel_figsize_inches()
    for pid in "ghijk":
        panel_sizes[pid] = _ED1_ARROW_PANEL_INCHES
    panel_outputs: dict[str, dict[str, Path]] = {}
    for panel_id in PANEL_IDS:
        width, height = panel_sizes[panel_id]
        panel_outputs[panel_id] = write_panel(
            root=root,
            panel_id=panel_id,
            panel_title=panel_title(panel_id),
            source_df=sources[panel_id],
            render=render_panel_by_id(panel_id),
            width=width,
            height=height,
            bbox_inches=None,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
