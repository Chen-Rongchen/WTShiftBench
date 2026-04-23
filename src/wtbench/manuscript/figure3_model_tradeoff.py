from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import (
    COLORS,
    add_panel_label,
    apply_manuscript_style,
    clean_axes,
    model_color,
    short_model_label,
)


FIGURE_ID = "figure3"
FIGURE_TITLE = "Model recovery is metric-dependent and reveals a backbone-separation trade-off"
SCRIPT_PATH = Path("scripts/manuscript/build_figure3_model_tradeoff.py")
CLAIM_BOUNDARY = (
    "GEARS is an architecture trade-off diagnosis; shared_mean_baseline is the backbone "
    "primary reference; do not claim model recovery proved."
)

MODEL_COMPARISON = Path("reports/stage2_real_hcc_smoke/model_comparison.tsv")
BACKBONE_DIAGNOSIS = Path("reports/stage2_real_hcc_smoke/backbone_diagnosis.tsv")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")

METRICS = [
    "backbone_recovery_score",
    "shift_excess_identification_score",
    "structure_vs_context_separation_score",
]

METRIC_SHORT_LABELS = {
    "backbone_recovery_score": "backbone",
    "shift_excess_identification_score": "shift-excess",
    "structure_vs_context_separation_score": "separation",
}

METRIC_LONG_LABELS = {
    "backbone_recovery_score": "backbone recovery",
    "shift_excess_identification_score": "shift-excess identification",
    "structure_vs_context_separation_score": "structure/context separation",
}

# Canonical row order for panel a overview heatmap: baseline first, GEARS formal
# second, foundation entrants adjacent (Geneformer above scGPT because Geneformer
# is stronger in the frozen claim), linear controls, then null reference last.
OVERVIEW_ORDER = [
    "shared_mean_baseline",
    "gears_hcc_formal_v1",
    "geneformer_hcc_formal_v1",
    "scgpt_hcc_formal_v1",
    "lm_g_geneformer_ridge_hcc_formal_v1",
    "lm_train_lowrank_hcc_formal_v1",
    "lm_g_scgpt_ridge_hcc_formal_v1",
    "null_model",
]

EXPECTED_HEADLINES = {
    ("shared_mean_baseline", "backbone_recovery_score"): 0.8066666666666666,
    ("gears_hcc_formal_v1", "backbone_recovery_score"): 0.6599999999999999,
    ("shared_mean_baseline", "structure_vs_context_separation_score"): 0.3526145586462627,
    ("gears_hcc_formal_v1", "structure_vs_context_separation_score"): 0.42841538072534885,
}


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig3_model_tradeoff"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def load_model_comparison(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / MODEL_COMPARISON, sep="\t")
    for (model_id, metric), expected in EXPECTED_HEADLINES.items():
        observed = float(df.loc[df["model_id"].eq(model_id), metric].iloc[0])
        if abs(observed - expected) > 0.02:
            raise RuntimeError(
                f"Headline sanity check failed for {model_id}/{metric}: "
                f"observed={observed:.4f}, expected={expected:.4f}. Stop and review."
            )
    return add_model_annotations(df)


def add_model_annotations(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["model_label"] = out["model_id"].map(short_model_label)
    out["plot_color"] = [model_color(row.model_id, row.object_role) for row in out.itertuples()]
    out["model_family"] = out["model_id"].map(model_family)
    out["is_formal_gears"] = out["model_id"].eq("gears_hcc_formal_v1")
    out["is_gears_sweep"] = out["model_id"].str.startswith("gears_hcc_formal_v1_")
    return out


def model_family(model_id: str) -> str:
    if model_id == "shared_mean_baseline":
        return "baseline"
    if model_id == "null_model":
        return "null"
    if model_id == "gears_hcc_formal_v1":
        return "GEARS formal"
    if model_id.startswith("gears_hcc_formal_v1_"):
        return "GEARS sweep"
    if model_id.startswith("geneformer") or model_id.startswith("scgpt"):
        return "foundation entrants"
    if model_id.startswith("lm_"):
        return "linear controls"
    return "other"


def axis_label(label: str) -> str:
    return str(label).replace("\n", " ")


def write_panel(
    *,
    root: Path,
    panel_id: str,
    panel_title: str,
    source_df: pd.DataFrame,
    input_paths: list[Path],
    render: Callable[[plt.Axes, pd.DataFrame], None],
    width: float = 3.3,
    height: float = 2.4,
) -> dict[str, Path]:
    pdir = ensure_dir(panel_dir(root))
    stem = f"{FIGURE_ID}_panel{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")

    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    png_path = pdir / f"{stem}.png"
    pdf_path = pdir / f"{stem}.pdf"
    output_paths = save_figure(fig, png_path, pdf_path)

    manifest_path = pdir / f"{stem}_manifest.json"
    write_panel_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        panel_id=f"{FIGURE_ID}{panel_id}",
        panel_title=panel_title,
        script_path=root / SCRIPT_PATH,
        input_paths=[root / p for p in input_paths],
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {
        "source": source_path,
        "png": png_path,
        "pdf": pdf_path,
        "manifest": manifest_path,
    }


# ---------------------------------------------------------------------------
# Panel a — Three-metric overview heatmap (absolute values, row-highlighted)
# ---------------------------------------------------------------------------


def _panel_a_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.set_index("model_id").reindex(OVERVIEW_ORDER).reset_index()
    return frame


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = _panel_a_frame(df)
    matrix = plot[METRICS].to_numpy(dtype=float)
    im = ax.imshow(matrix, aspect="auto", vmin=0.0, vmax=0.85, cmap="Greys")

    n_rows, n_cols = matrix.shape
    row_labels = [axis_label(v) for v in plot["model_label"]]
    ax.set_yticks(np.arange(n_rows))
    ax.set_yticklabels(row_labels)
    ax.set_xticks(np.arange(n_cols))
    ax.set_xticklabels([METRIC_SHORT_LABELS[m] for m in METRICS])

    for i in range(n_rows):
        for j in range(n_cols):
            value = matrix[i, j]
            ax.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=6,
                color="white" if value > 0.55 else "#1F1F1F",
            )

    # Row-level highlighting: frame baseline + GEARS formal; soft background behind
    # foundation entrants (Geneformer + scGPT); pale reference band on null.
    def _frame_row(idx: int, color: str, lw: float = 1.4) -> None:
        rect = mpatches.Rectangle(
            (-0.5, idx - 0.5),
            n_cols,
            1,
            fill=False,
            edgecolor=color,
            linewidth=lw,
            zorder=5,
        )
        ax.add_patch(rect)

    def _row_background(idx: int, color: str, alpha: float = 0.18) -> None:
        rect = mpatches.Rectangle(
            (-0.5, idx - 0.5),
            n_cols,
            1,
            fill=True,
            color=color,
            alpha=alpha,
            linewidth=0,
            zorder=0,
        )
        ax.add_patch(rect)

    ids = list(plot["model_id"])
    if "gears_hcc_formal_v1" in ids:
        _frame_row(ids.index("gears_hcc_formal_v1"), COLORS["gears"], lw=1.4)
    for mid in ("geneformer_hcc_formal_v1", "scgpt_hcc_formal_v1"):
        if mid in ids:
            _row_background(ids.index(mid), COLORS["foundation"], alpha=0.12)
    if "null_model" in ids:
        _row_background(ids.index("null_model"), COLORS["null"], alpha=0.7)

    ax.set_title("Three adjudication metrics separate recovery modes", loc="left")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    cbar.ax.tick_params(labelsize=5.5)
    cbar.set_label("score", fontsize=5.5, labelpad=2)
    add_panel_label(ax, "a", x=-0.36)


# ---------------------------------------------------------------------------
# Panel b — Headline baseline vs GEARS paired summary (dumbbell)
# ---------------------------------------------------------------------------


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    rows = df.set_index("model_id").loc[["shared_mean_baseline", "gears_hcc_formal_v1"]]

    metrics = [
        "backbone_recovery_score",
        "structure_vs_context_separation_score",
    ]
    short_labels = ["backbone\nrecovery", "structure/context\nseparation"]

    y = np.arange(len(metrics))[::-1]
    first_row = True
    for yi, metric in zip(y, metrics):
        baseline_val = float(rows.loc["shared_mean_baseline", metric])
        gears_val = float(rows.loc["gears_hcc_formal_v1", metric])
        ax.plot(
            [baseline_val, gears_val],
            [yi, yi],
            color="#D3D3D3",
            linewidth=0.9,
            zorder=1,
        )
        ax.scatter(
            [baseline_val],
            [yi],
            s=62,
            color=COLORS["baseline"],
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
        ax.scatter(
            [gears_val],
            [yi],
            s=62,
            color=COLORS["gears"],
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
        # In-point labels on the first row only; value labels on every row.
        if first_row:
            ax.annotate(
                "shared mean baseline",
                xy=(baseline_val, yi),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=5.8,
                color=COLORS["baseline"],
                ha="left",
                va="bottom",
            )
            ax.annotate(
                "GEARS formal",
                xy=(gears_val, yi),
                xytext=(-4, 4),
                textcoords="offset points",
                fontsize=5.8,
                color=COLORS["gears"],
                ha="right",
                va="bottom",
            )
            first_row = False
        ax.text(
            baseline_val,
            yi - 0.22,
            f"{baseline_val:.2f}",
            ha="center",
            va="top",
            fontsize=5.5,
            color=COLORS["baseline"],
        )
        ax.text(
            gears_val,
            yi - 0.22,
            f"{gears_val:.2f}",
            ha="center",
            va="top",
            fontsize=5.5,
            color=COLORS["gears"],
        )

    ax.set_yticks(y)
    ax.set_yticklabels(short_labels)
    ax.set_xlim(0.0, 0.95)
    ax.set_xlabel("Score")
    ax.set_ylim(-0.7, len(metrics) - 0.2)
    ax.set_title(
        "Baseline leads backbone recovery, whereas GEARS leads context separation",
        loc="left",
    )
    clean_axes(ax)
    ax.grid(axis="x", color="#F2F2F2", linewidth=0.4)
    add_panel_label(ax, "b")


# ---------------------------------------------------------------------------
# Panel c — Trade-off scatter (central, larger; no frontier line)
# ---------------------------------------------------------------------------


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    # Upper-right absence region: backbone > 0.75 AND separation > 0.40.
    # Reader-facing claim = "no entrant occupies upper-right": baseline sits
    # just below the region (high backbone, mid separation), GEARS formal
    # just to the left (mid backbone, high separation), so the empty rectangle
    # itself becomes the visual evidence for the trade-off claim. Kept extremely
    # light (#F5F5F5, no edge) so it reads as an absence window, not a target box.
    # Epistemic status: ILLUSTRATIVE visual aid only. Thresholds (0.75, 0.40)
    # were chosen so that the two headline entrants are tangent to the region
    # edges (baseline below, GEARS left). The region is NOT a decision threshold
    # and is NOT used for scoring or adjudication; see Fig. 3 caption.
    absence = mpatches.Rectangle(
        (0.75, 0.40),
        0.88 - 0.75,
        0.54 - 0.40,
        fill=True,
        color="#F5F5F5",
        linewidth=0,
        zorder=0,
    )
    ax.add_patch(absence)

    named = {
        "shared_mean_baseline": ("shared mean baseline", "right"),
        "gears_hcc_formal_v1": ("GEARS formal", "left"),
        "geneformer_hcc_formal_v1": ("Geneformer", "left"),
        "scgpt_hcc_formal_v1": ("scGPT", "left"),
    }

    for row in df.itertuples():
        is_headline = row.model_id in {"shared_mean_baseline", "gears_hcc_formal_v1"}
        is_named = row.model_id in named
        # Headline points (baseline + GEARS formal) carry the core trade-off
        # claim; enlarged so they read as visual anchors even when surrounded
        # by the sweep/linear/null background cloud.
        size = 150 if is_headline else (55 if is_named else 28)
        edge = "#111111" if is_headline else ("#333333" if is_named else "white")
        lw = 1.1 if is_headline else 0.6
        alpha = 1.0 if is_named else 0.70
        ax.scatter(
            row.backbone_recovery_score,
            row.structure_vs_context_separation_score,
            s=size,
            color=row.plot_color,
            edgecolor=edge,
            linewidth=lw,
            zorder=4 if is_headline else 3,
            alpha=alpha,
        )

    label_offsets = {
        "shared_mean_baseline": (-0.012, 0.010, "right", "bottom"),
        "gears_hcc_formal_v1": (0.012, 0.010, "left", "bottom"),
        "geneformer_hcc_formal_v1": (0.012, -0.002, "left", "center"),
        "scgpt_hcc_formal_v1": (0.012, 0.000, "left", "center"),
    }
    for row in df.itertuples():
        if row.model_id in label_offsets:
            dx, dy, ha, va = label_offsets[row.model_id]
            is_headline = row.model_id in {"shared_mean_baseline", "gears_hcc_formal_v1"}
            ax.text(
                row.backbone_recovery_score + dx,
                row.structure_vs_context_separation_score + dy,
                named[row.model_id][0],
                fontsize=7.0 if is_headline else 6.0,
                fontweight="bold" if is_headline else "normal",
                ha=ha,
                va=va,
                color=COLORS["text"],
            )

    ax.set_xlabel("Backbone recovery score")
    ax.set_ylabel("Structure/context separation score")
    ax.set_title(
        "Entrants occupy a backbone–separation trade-off space",
        loc="left",
    )
    ax.set_xlim(0.40, 0.88)
    ax.set_ylim(0.20, 0.54)
    clean_axes(ax)
    ax.grid(color="#F2F2F2", linewidth=0.4)

    # Family-oriented legend (not per-entrant): panel c carries the only legend
    # in the figure; black=baseline / blue=GEARS semantics established here
    # apply across all other panels by convention.
    handles = [
        plt.Line2D([], [], marker="o", linestyle="", color=COLORS["baseline"], markersize=5.5,
                   markeredgecolor="#111111", markeredgewidth=0.6, label="baseline reference"),
        plt.Line2D([], [], marker="o", linestyle="", color=COLORS["gears"], markersize=5.5,
                   markeredgecolor="#111111", markeredgewidth=0.6, label="GEARS formal"),
        plt.Line2D([], [], marker="o", linestyle="", color=COLORS["foundation"], markersize=4,
                   label="foundation entrants"),
        plt.Line2D([], [], marker="o", linestyle="", color=COLORS["gears_sweep"], markersize=3.2,
                   alpha=0.5, label="GEARS sweep variants"),
        plt.Line2D([], [], marker="o", linestyle="", color=COLORS["linear"], markersize=3.2,
                   alpha=0.5, label="linear controls"),
        plt.Line2D([], [], marker="o", linestyle="", color=COLORS["null"], markersize=3.2,
                   alpha=0.7, label="null"),
    ]
    # Legend placed lower-right: upper-right is reserved for the absence region
    # (trade-off claim), upper-left has sweep points. Lower-right quadrant
    # (backbone>0.7, separation<0.30) is empty of data and can hold the legend
    # without covering any point or the absence region.
    legend = ax.legend(
        handles=handles,
        loc="lower right",
        frameon=False,
        fontsize=5.5,
        handletextpad=0.3,
        labelspacing=0.32,
        borderpad=0.2,
        ncol=2,
        columnspacing=0.7,
        labelcolor="#3A3A3A",
    )

    add_panel_label(ax, "c")


# ---------------------------------------------------------------------------
# Panel d — Per-cell-line grouped bars (fixes the prior rendering bug)
# ---------------------------------------------------------------------------


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    # Per-context paired dots (dumbbell) for baseline vs GEARS formal on the
    # two HCC primary contexts. We intentionally do not use grouped bars here:
    # the claim is a qualitative ordering ("same direction"), and paired dots
    # show this with the lowest possible ink footprint.
    cell_line_order = ["HCC38", "HCC1143"]
    plot = (
        df.set_index("cell_line")
        .reindex(cell_line_order)
        .reset_index()
    )
    y = np.arange(len(plot))[::-1]

    for yi, row in zip(y, plot.itertuples()):
        baseline_val = float(row.baseline_backbone_recovery)
        gears_val = float(row.backbone_recovery)
        low, high = sorted((baseline_val, gears_val))
        ax.plot([low, high], [yi, yi], color="#D3D3D3", linewidth=0.9, zorder=1)
        ax.scatter([baseline_val], [yi], s=62, color=COLORS["baseline"],
                   edgecolor="white", linewidth=0.5, zorder=3)
        ax.scatter([gears_val], [yi], s=62, color=COLORS["gears"],
                   edgecolor="white", linewidth=0.5, zorder=3)
        ax.text(baseline_val, yi - 0.28, f"{baseline_val:.2f}", ha="center",
                va="top", fontsize=5.5, color=COLORS["baseline"])
        ax.text(gears_val, yi - 0.28, f"{gears_val:.2f}", ha="center",
                va="top", fontsize=5.5, color=COLORS["gears"])

    ax.set_yticks(y)
    ax.set_yticklabels(plot["cell_line"])
    ax.set_xlim(0.40, 1.0)
    ax.set_ylim(-0.7, len(plot) - 0.3)
    ax.set_xlabel("Backbone recovery score (per cell line)")
    ax.set_title(
        "The same qualitative ordering is preserved in HCC38 and HCC1143",
        loc="left",
    )
    clean_axes(ax)
    ax.grid(axis="x", color="#F2F2F2", linewidth=0.4)
    add_panel_label(ax, "d")


# ---------------------------------------------------------------------------
# Panel e — GEARS sweep: shift-excess vs backbone (dumbbell, one row per model)
# ---------------------------------------------------------------------------


SWEEP_ORDER_IDS = [
    "shared_mean_baseline",
    "gears_hcc_formal_v1",
    "gears_hcc_formal_v1_e20_lr1e-03_wd1e-06",
    "gears_hcc_formal_v1_e30_lr2e-03_wd1e-06",
    "gears_hcc_formal_v1_e30_lr1e-03_wd1e-05",
    "gears_hcc_formal_v1_e30_lr5e-04_wd1e-06",
    "gears_hcc_formal_v1_e40_lr1e-03_wd1e-06",
]


def render_panel_e(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.set_index("model_id").reindex(SWEEP_ORDER_IDS).dropna(subset=["backbone_recovery_score"]).copy()
    plot["tradeoff_gap"] = (
        plot["shift_excess_identification_score"] - plot["backbone_recovery_score"]
    )
    # Sort by (shift_excess − backbone) ascending: most backbone-lean (baseline)
    # at the top, most shift-excess-biased sweep at the bottom.
    plot = plot.sort_values("tradeoff_gap", ascending=True).reset_index()
    y = np.arange(len(plot))[::-1]

    first_row = True
    for yi, row in zip(y, plot.itertuples()):
        backbone = row.backbone_recovery_score
        shift = row.shift_excess_identification_score
        low, high = (backbone, shift) if backbone < shift else (shift, backbone)
        ax.plot([low, high], [yi, yi], color="#D3D3D3", linewidth=0.9, zorder=1)
        ax.scatter([backbone], [yi], s=52, color=COLORS["baseline"], edgecolor="white",
                   linewidth=0.5, zorder=3)
        ax.scatter([shift], [yi], s=52, color=COLORS["accent_orange"], edgecolor="white",
                   linewidth=0.5, zorder=3)
        if first_row:
            ax.annotate(
                "backbone recovery",
                xy=(backbone, yi),
                xytext=(-5, 8),
                textcoords="offset points",
                fontsize=5.6,
                color=COLORS["baseline"],
                ha="right",
                va="bottom",
            )
            ax.annotate(
                "shift-excess identification",
                xy=(shift, yi),
                xytext=(5, 8),
                textcoords="offset points",
                fontsize=5.6,
                color=COLORS["accent_orange"],
                ha="left",
                va="bottom",
            )
            first_row = False

    ax.set_yticks(y)
    ax.set_yticklabels([axis_label(v) for v in plot["model_label"]])
    ax.set_xlim(0, 1.02)
    ax.set_ylim(-0.6, len(plot) + 0.3)
    ax.set_xlabel("Score")
    ax.set_title("GEARS sweeps gain shift-excess without recovering backbone", loc="left")
    baseline_backbone = float(
        df.loc[df["model_id"].eq("shared_mean_baseline"), "backbone_recovery_score"].iloc[0]
    )
    ax.axvline(
        baseline_backbone,
        color=COLORS["baseline"],
        linestyle="--",
        linewidth=0.5,
        alpha=0.35,
    )
    ax.text(
        baseline_backbone - 0.005,
        -0.45,
        "baseline",
        fontsize=5.5,
        color="#8A8A8A",
        va="top",
        ha="right",
    )
    clean_axes(ax)
    ax.grid(axis="x", color="#F2F2F2", linewidth=0.4)
    add_panel_label(ax, "e", x=-0.34)


# ---------------------------------------------------------------------------
# Source assembly + combined rendering
# ---------------------------------------------------------------------------


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    model = load_model_comparison(root)
    backbone = pd.read_csv(root / BACKBONE_DIAGNOSIS, sep="\t")
    backbone = backbone.merge(model[["model_id", "model_label", "plot_color"]], on="model_id", how="left")

    overview_cols = ["model_id", "model_label", "model_family", "plot_color", *METRICS]
    overview = (
        model.set_index("model_id")
        .reindex(OVERVIEW_ORDER)
        .reset_index()[overview_cols]
    )

    return {
        "a": overview,
        "b": model.loc[model["model_id"].isin(["shared_mean_baseline", "gears_hcc_formal_v1"]),
                       ["model_id", "model_label", "plot_color", *METRICS]].copy(),
        "c": model[
            [
                "model_id",
                "object_role",
                "model_family",
                "model_label",
                "plot_color",
                "backbone_recovery_score",
                "structure_vs_context_separation_score",
            ]
        ],
        "d": backbone.loc[
            backbone["model_id"].eq("gears_hcc_formal_v1"),
            [
                "model_id",
                "cell_line",
                "backbone_recovery",
                "baseline_backbone_recovery",
                "failure_mode_call",
            ],
        ],
    }


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {
        "a": render_panel_a,
        "b": render_panel_b,
        "c": render_panel_c,
        "d": render_panel_d,
    }[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Three-metric adjudication overview heatmap",
        "b": "Headline baseline versus GEARS dumbbell",
        "c": "Backbone–separation trade-off scatter",
        "d": "Per-cell-line backbone recovery (HCC38 and HCC1143)",
    }[panel_id]


PANEL_IDS: list[str] = ["a", "b", "c", "d"]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat(
        [df.assign(panel=panel_id) for panel_id, df in sources.items()],
        ignore_index=True,
        sort=False,
    )
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")

    fig = plt.figure(figsize=(10.0, 8.4))
    # Two-level layout to give independent control of vertical gaps:
    #   outer[0] = top-row "contract + headline" band (a + b)
    #   outer[1] = centre-and-tail band (c tall + d short, tight hspace)
    # This lets a/b sit close-ish to c, and d sit *closer* to c than to the
    # page bottom (so d reads as a continuation of c, not an orphan strip).
    outer = fig.add_gridspec(
        2,
        1,
        height_ratios=[1.0, 2.1],
        hspace=0.14,
        left=0.09,
        right=0.97,
        top=0.95,
        bottom=0.08,
    )
    top = outer[0].subgridspec(1, 2, wspace=0.38)
    ax_a = fig.add_subplot(top[0, 0])
    ax_b = fig.add_subplot(top[0, 1])
    bot = outer[1].subgridspec(2, 1, height_ratios=[1.55, 0.55], hspace=0.28)
    ax_c = fig.add_subplot(bot[0])
    # d width ~78% of c width, left-aligned with c so that the panel letters
    # a, c and d all sit on the same vertical line.
    d_sub = bot[1].subgridspec(1, 2, width_ratios=[7, 2], wspace=0.0)
    ax_d = fig.add_subplot(d_sub[0, 0])

    render_panel_a(ax_a, sources["a"])
    render_panel_b(ax_b, sources["b"])
    render_panel_c(ax_c, sources["c"])
    render_panel_d(ax_d, sources["d"])

    # Panel letters were added inside each render_panel_* using axes-relative
    # coordinates, so their absolute x positions depend on each axis width.
    # Re-anchor them in figure coordinates so a, c and d sit on the same
    # vertical line; b sits on a second vertical line aligned with b's axis.
    def _rebind_panel_letter(ax: plt.Axes, letter: str, fig_x: float) -> None:
        for txt in list(ax.texts):
            if txt.get_text() == letter and txt.get_fontweight() == "bold":
                txt.set_visible(False)
                bbox = ax.get_position()
                fig.text(
                    fig_x,
                    bbox.y1 + 0.003,
                    letter,
                    fontsize=txt.get_fontsize(),
                    fontweight="bold",
                    color=txt.get_color(),
                    va="bottom",
                    ha="left",
                )
                break

    left_letter_x = 0.015
    _rebind_panel_letter(ax_a, "a", left_letter_x)
    _rebind_panel_letter(ax_c, "c", left_letter_x)
    _rebind_panel_letter(ax_d, "d", left_letter_x)
    # b stays anchored to its own column left edge.
    b_bbox = ax_b.get_position()
    _rebind_panel_letter(ax_b, "b", max(b_bbox.x0 - 0.035, left_letter_x + 0.48))

    png_path = out / f"{FIGURE_ID}.png"
    pdf_path = out / f"{FIGURE_ID}.pdf"
    output_paths = save_figure(fig, png_path, pdf_path)

    manifest_path = out / f"{FIGURE_ID}_panel_manifest.json"
    write_figure_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in PANEL_IDS],
        combined_source_data_path=combined_source_path,
        output_paths=output_paths,
        input_paths=[root / MODEL_COMPARISON, root / BACKBONE_DIAGNOSIS, root / FINAL_CLAIM_MATRIX],
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": combined_source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build manuscript Figure 3 model trade-off panels and assembly.")
    parser.add_argument("--panels-only", action="store_true", help="Render individual panels but skip combined assembly.")
    args = parser.parse_args(argv)

    root = repo_root()
    apply_manuscript_style()
    sources = build_sources(root)
    panel_outputs: dict[str, dict[str, Path]] = {}
    input_paths = [MODEL_COMPARISON, BACKBONE_DIAGNOSIS, FINAL_CLAIM_MATRIX]

    for panel_id in PANEL_IDS:
        panel_outputs[panel_id] = write_panel(
            root=root,
            panel_id=panel_id,
            panel_title=panel_title(panel_id),
            source_df=sources[panel_id],
            input_paths=input_paths,
            render=render_panel_by_id(panel_id),
            width=3.6 if panel_id in {"a", "c", "e"} else 3.3,
            height=2.8 if panel_id == "c" else 2.4,
        )

    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
