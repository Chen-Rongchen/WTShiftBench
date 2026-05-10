from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import (
    COLORS,
    add_panel_heading,
    add_panel_label,
    apply_manuscript_style,
    clean_axes,
    finalize_manuscript_figure,
    model_color,
    short_model_label,
)


FIGURE_ID = "figure3"
FIGURE_TITLE = "Model recovery is metric-dependent and reveals an asymmetric recovery pattern"
SCRIPT_PATH = Path("scripts/manuscript/build_figure3_model_tradeoff.py")
CLAIM_BOUNDARY = (
    "GEARS is an architecture-level diagnosis; shared_mean_baseline is the backbone "
    "primary reference; do not claim model recovery proved."
)

MODEL_COMPARISON = Path("reports/real_hcc_smoke/model_comparison.tsv")
BACKBONE_DIAGNOSIS = Path("reports/real_hcc_smoke/backbone_diagnosis.tsv")
SMOKE_SUMMARY = Path("reports/real_hcc_smoke/smoke_summary.tsv")
FINAL_CLAIM_MATRIX = Path("reports/truth_driven_bridge/sensitivity/final_claim_matrix.tsv")

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
    "structure_vs_context_separation_score": "structure / context separation",
}

FIG3_COLORS = {
    "baseline": "#333333",
    "gears": "#0072B2",
    "foundation": "#8E8E8E",
    "linear": "#D0D0D0",
    "gears_sweep": "#D0D0D0",
    "null": "#D0D0D0",
    "null_band": "#F5F5F5",
    "divider": "#D0D0D0",
    "hcc38": "#D55E00",
    "hcc1143": "#009E73",
    "threshold": "#56B4E9",
    "reference_grid": "#E8E8E8",
    "cloud_text": "#616161",
    "shade": "#FAFAFA",
    "heat_highlight": "#009E73",
    "heat_low": "#FFFFFF",
    "heat_mid": "#BDBDBD",
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


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_3"


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
    out["model_family"] = out["model_id"].map(model_family)
    out["is_formal_gears"] = out["model_id"].eq("gears_hcc_formal_v1")
    out["is_gears_sweep"] = out["model_id"].str.startswith("gears_hcc_formal_v1_")
    out["plot_color"] = [figure3_model_color(row.model_id, row.object_role) for row in out.itertuples()]
    return out


def figure3_model_color(model_id: str, object_role: str | None = None) -> str:
    if model_id == "shared_mean_baseline" or object_role == "baseline":
        return FIG3_COLORS["baseline"]
    if model_id == "null_model" or object_role == "null":
        return FIG3_COLORS["null"]
    if model_id == "gears_hcc_formal_v1":
        return FIG3_COLORS["gears"]
    if model_id.startswith("gears_hcc_formal_v1_"):
        return FIG3_COLORS["gears_sweep"]
    if model_id.startswith("geneformer") or model_id.startswith("scgpt"):
        return FIG3_COLORS["foundation"]
    if model_id.startswith("lm_"):
        return FIG3_COLORS["linear"]
    return model_color(model_id, object_role)


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
    neutral_cmap = LinearSegmentedColormap.from_list(
        "fig3_neutral",
        [FIG3_COLORS["heat_low"], "#F0F0F0", "#A8A8A8"],
    )
    im = ax.imshow(matrix, aspect="auto", vmin=0.0, vmax=0.85, cmap=neutral_cmap, zorder=1)

    n_rows, n_cols = matrix.shape
    ax.set_xlim(-0.5, n_cols - 0.5)
    ax.set_ylim(n_rows - 0.5, -0.5)
    row_labels = [axis_label(v) for v in plot["model_label"]]
    ax.set_yticks(np.arange(n_rows))
    ax.set_yticklabels(row_labels, fontsize=7.5)
    ax.set_xticks(np.arange(n_cols))
    ax.set_xticklabels([METRIC_SHORT_LABELS[m] for m in METRICS], fontsize=7.5)

    for x in np.arange(-0.5, n_cols, 1):
        ax.axvline(x, color="white", linewidth=0.7, zorder=2)
    for y in np.arange(-0.5, n_rows, 1):
        ax.axhline(y, color="white", linewidth=0.7, zorder=2)
    for i in range(n_rows):
        for j in range(n_cols):
            value = matrix[i, j]
            ax.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=7.3,
                fontweight="bold" if value >= 0.6 else "normal",
                color="white" if value >= 0.6 else FIG3_COLORS["baseline"],
                zorder=3,
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
    if "null_model" in ids:
        null_idx = ids.index("null_model")
        _row_background(null_idx, FIG3_COLORS["null_band"], alpha=1.0)
        ax.hlines(
            [null_idx - 0.5, null_idx + 0.5],
            xmin=-0.5,
            xmax=n_cols - 0.5,
            colors=FIG3_COLORS["divider"],
            linewidth=0.75,
            zorder=6,
        )

    add_panel_heading(
        ax,
        "",
        "Three adjudication metrics separate recovery modes",
        title_x=0.00,
    )
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.ax.tick_params(labelsize=7.0, length=2)
    cbar.set_label("score", fontsize=7.0, labelpad=2)


# ---------------------------------------------------------------------------
# Panel b — Headline baseline vs GEARS paired summary (dumbbell)
# ---------------------------------------------------------------------------


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    rows = df.set_index("model_id").loc[["shared_mean_baseline", "gears_hcc_formal_v1"]]

    metrics = [
        "backbone_recovery_score",
        "structure_vs_context_separation_score",
    ]
    short_labels = ["Backbone\nrecovery", "Structure /\ncontext separation"]

    y = np.arange(len(metrics))[::-1]
    for yi, metric in zip(y, metrics):
        baseline_val = float(rows.loc["shared_mean_baseline", metric])
        gears_val = float(rows.loc["gears_hcc_formal_v1", metric])
        ax.plot(
            [baseline_val, gears_val],
            [yi, yi],
            color=FIG3_COLORS["divider"],
            linewidth=0.75,
            zorder=1,
        )
        ax.scatter(
            [baseline_val],
            [yi],
            s=62,
            color=FIG3_COLORS["baseline"],
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
        ax.scatter(
            [gears_val],
            [yi],
            s=62,
            color=FIG3_COLORS["gears"],
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
        ax.text(
            baseline_val,
            yi - 0.22,
            f"{baseline_val:.2f}",
            ha="center",
            va="top",
            fontsize=7.5,
            color=FIG3_COLORS["baseline"],
        )
        ax.text(
            gears_val,
            yi - 0.22,
            f"{gears_val:.2f}",
            ha="center",
            va="top",
            fontsize=7.5,
            color=FIG3_COLORS["baseline"],
        )

    ax.set_yticks(y)
    ax.set_yticklabels(short_labels, fontsize=7.5)
    ax.set_xlim(0.0, 0.95)
    ax.set_xlabel("Adjudication score", fontsize=7.5)
    ax.tick_params(axis="x", labelsize=7.5)
    ax.set_ylim(-0.7, len(metrics) - 0.2)
    add_panel_heading(
        ax,
        "",
        "Reference leads backbone; GEARS leads separation",
        title_x=0.00,
    )
    clean_axes(ax)
    handles = [
        plt.Line2D(
            [], [], marker="o", linestyle="", color=FIG3_COLORS["baseline"],
            markersize=5.5, markeredgecolor="white", markeredgewidth=0.5,
            label="diagnostic shared-mean reference",
        ),
        plt.Line2D(
            [], [], marker="o", linestyle="", color=FIG3_COLORS["gears"],
            markersize=5.5, markeredgecolor="white", markeredgewidth=0.5,
            label="GEARS formal",
        ),
    ]
    ax.legend(
        handles=handles,
        loc="lower right",
        frameon=False,
        fontsize=7.0,
        handletextpad=0.35,
        labelspacing=0.3,
        borderpad=0.2,
    )


# ---------------------------------------------------------------------------
# Panel c — Trade-off scatter (central, larger; no frontier line)
# ---------------------------------------------------------------------------


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    # Upper-right absence region: backbone > 0.75 AND separation > 0.40.
    # Reader-facing claim = "no entrant occupies upper-right": baseline sits
    # just below the region (high backbone, mid separation), GEARS formal
    # just to the left (mid backbone, high separation), so the empty rectangle
    # itself becomes the visual evidence for the asymmetric recovery claim. Kept extremely
    # light (#F5F5F5, no edge) so it reads as an absence window, not a target box.
    # Epistemic status: ILLUSTRATIVE visual aid only. Thresholds (0.75, 0.40)
    # were chosen so that the two headline entrants are tangent to the region
    # edges (baseline below, GEARS left). The region is NOT a decision threshold
    # and is NOT used for scoring or adjudication; see Fig. 3 caption.
    absence = mpatches.Rectangle(
        (0.75, 0.40),
        0.90 - 0.75,
        0.54 - 0.40,
        fill=True,
        color=FIG3_COLORS["shade"],
        alpha=0.15,
        linewidth=0,
        zorder=0,
    )
    ax.add_patch(absence)

    named = {
        "shared_mean_baseline": ("diagnostic\nshared-mean reference", "right"),
        "gears_hcc_formal_v1": ("GEARS formal", "left"),
        "geneformer_hcc_formal_v1": ("Geneformer", "left"),
        "scgpt_hcc_formal_v1": ("scGPT", "left"),
    }

    for row in df.itertuples():
        if row.model_id.startswith("gears_hcc_formal_v1_") or row.model_id == "null_model" or row.model_id.startswith("lm_"):
            continue
        is_baseline = row.model_id == "shared_mean_baseline"
        is_gears = row.model_id == "gears_hcc_formal_v1"
        is_named = row.model_id in named
        if is_baseline:
            size, edge, lw, zorder = 125, "white", 0.6, 5
        elif is_gears:
            size, edge, lw, zorder = 78, "white", 0.6, 5
        elif row.model_family == "foundation entrants":
            size, edge, lw, zorder = 18, "white", 0.3, 4
        else:
            size, edge, lw, zorder = 8, "white", 0.25, 2
        ax.scatter(
            row.backbone_recovery_score,
            row.structure_vs_context_separation_score,
            s=size,
            color=row.plot_color,
            edgecolor=edge,
            linewidth=lw,
            zorder=zorder,
            alpha=1.0 if is_named else 0.85,
        )

    label_offsets = {
        "shared_mean_baseline": (0.000, 0.032, "center", "bottom"),
        "gears_hcc_formal_v1": (0.000, 0.032, "center", "bottom"),
        "geneformer_hcc_formal_v1": (0.012, -0.002, "left", "center"),
        "scgpt_hcc_formal_v1": (0.012, 0.000, "left", "center"),
    }
    for row in df.itertuples():
        if row.model_id.startswith("gears_hcc_formal_v1_") or row.model_id == "null_model" or row.model_id.startswith("lm_"):
            continue
        if row.model_id in label_offsets:
            dx, dy, ha, va = label_offsets[row.model_id]
            is_headline = row.model_id in {"shared_mean_baseline", "gears_hcc_formal_v1"}
            ax.text(
                row.backbone_recovery_score + dx,
                row.structure_vs_context_separation_score + dy,
                named[row.model_id][0],
                fontsize=8.0 if is_headline else 7.5,
                fontweight="bold" if is_headline else "normal",
                ha=ha,
                va=va,
                color=FIG3_COLORS["baseline"],
            )

    ax.set_xlabel("Backbone recovery", fontsize=7.5)
    ax.set_ylabel("Structure-versus-context separation", fontsize=7.5)
    add_panel_heading(
        ax,
        "",
        "Asymmetric recovery space",
        title_x=0.00,
    )
    ax.set_xlim(0.40, 0.90)
    ax.set_ylim(0.20, 0.54)
    clean_axes(ax)
    ax.tick_params(axis="both", labelsize=7.5)

    handles = [
        plt.Line2D(
            [], [], marker="o", linestyle="", color=FIG3_COLORS["baseline"],
            markersize=6.0, markeredgecolor="white", markeredgewidth=0.5,
            label="diagnostic reference",
        ),
        plt.Line2D(
            [], [], marker="o", linestyle="", color=FIG3_COLORS["gears"],
            markersize=5.3, markeredgecolor="white", markeredgewidth=0.5,
            label="GEARS formal",
        ),
        plt.Line2D(
            [], [], marker="o", linestyle="", color=FIG3_COLORS["foundation"],
            markersize=4.2, markeredgecolor="white", markeredgewidth=0.4,
            label="foundation entrants",
        ),
    ]
    ax.legend(
        handles=handles,
        loc="lower right",
        bbox_to_anchor=(1.15, 0.02),
        frameon=False,
        fontsize=7.0,
        handletextpad=0.35,
        labelspacing=0.28,
        borderpad=0.2,
        ncol=1,
        columnspacing=0.8,
    )



# ---------------------------------------------------------------------------
# Panel d — Per-cell-line grouped bars (fixes the prior rendering bug)
# ---------------------------------------------------------------------------


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    add_panel_heading(
        ax,
        "",
        "Relative backbone recovery is consistent across the two primary contexts",
        title_x=0.00,
    )

    ORDERED_IDS = [
        "gears_hcc_formal_v1",
        "geneformer_hcc_formal_v1",
        "scgpt_hcc_formal_v1",
    ]
    LABELS = {
        "gears_hcc_formal_v1": "GEARS formal",
        "geneformer_hcc_formal_v1": "Geneformer",
        "scgpt_hcc_formal_v1": "scGPT",
    }
    COLORS_CONTEXT = {
        "HCC38": FIG3_COLORS["hcc38"],
        "HCC1143": FIG3_COLORS["hcc1143"],
    }

    ax_plot = ax.inset_axes([0.06, 0.04, 0.88, 0.90])

    # Baseline reference line
    ax_plot.axvline(
        1.0,
        color=FIG3_COLORS["threshold"],
        linewidth=0.75,
        linestyle="--",
        zorder=1,
    )
    ax_plot.text(
        1.0 + 0.012, len(ORDERED_IDS) - 0.5, "reference = 1.0",
        fontsize=7.5, color=FIG3_COLORS["threshold"], va="top", ha="left",
    )

    # Horizontal grid at each row
    for yi in range(len(ORDERED_IDS)):
        ax_plot.axhline(yi, color="#F0F0F0", linewidth=0.5, zorder=0)

    xmax = 1.08
    for i, mid in enumerate(reversed(ORDERED_IDS)):
        for cell_line in ["HCC38", "HCC1143"]:
            row = df.loc[(df["model_id"] == mid) & (df["cell_line"] == cell_line)].iloc[0]
            ratio_mean = float(row["ratio_mean"])
            se = float(row["se"])
            y_pos = i
            color = COLORS_CONTEXT[cell_line]
            offset = -0.22 if cell_line == "HCC38" else 0.22

            # SE whisker (±1 SE)
            lower = ratio_mean - se
            upper = ratio_mean + se
            # If upper exceeds xmax, truncate and add arrow
            if upper > xmax:
                ax_plot.annotate(
                    "",
                    xy=(xmax, y_pos + offset),
                    xytext=(lower, y_pos + offset),
                    arrowprops=dict(
                        arrowstyle="->",
                        color=color,
                        lw=0.8,
                        alpha=0.6,
                    ),
                    zorder=2,
                )
            else:
                ax_plot.plot(
                    [lower, upper],
                    [y_pos + offset, y_pos + offset],
                    color=color,
                    linewidth=0.8,
                    alpha=0.6,
                    zorder=2,
                )
            # Point
            ax_plot.scatter(
                ratio_mean,
                y_pos + offset,
                s=45,
                color=color,
                edgecolor="white",
                linewidth=0.5,
                zorder=3,
            )
            # Value label (above the dot/line)
            ax_plot.text(
                ratio_mean,
                y_pos + offset + 0.18,
                f"{ratio_mean:.3f}",
                ha="center",
                va="bottom",
                fontsize=7.5,
                color=FIG3_COLORS["baseline"],
            )

    ax_plot.set_yticks(range(len(ORDERED_IDS)))
    ax_plot.set_yticklabels(
        [LABELS[mid] for mid in reversed(ORDERED_IDS)],
        fontsize=7.5,
    )
    ax_plot.set_xlabel("Relative backbone recovery (reference = 1.0)", fontsize=7.5, labelpad=1)
    ax_plot.set_xlim(0.0, xmax)
    clean_axes(ax_plot)
    ax_plot.tick_params(axis="x", labelsize=7.5)

    # Legend
    handles = [
        plt.Line2D(
            [], [], marker="o", linestyle="", color=COLORS_CONTEXT["HCC38"],
            markersize=4.5, markeredgecolor="#333333", markeredgewidth=0.5, label="HCC38",
        ),
        plt.Line2D(
            [], [], marker="o", linestyle="", color=COLORS_CONTEXT["HCC1143"],
            markersize=4.5, markeredgecolor="#333333", markeredgewidth=0.5, label="HCC1143",
        ),
    ]
    ax_plot.legend(
        handles=handles,
        loc="lower right",
        bbox_to_anchor=(1.12, 0.02),
        frameon=False,
        fontsize=7.5,
        handletextpad=0.3,
        labelspacing=0.3,
        borderpad=0.2,
    )



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
    # panel letter removed (PIL)


# ---------------------------------------------------------------------------
# Source assembly + combined rendering
# ---------------------------------------------------------------------------


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    model = load_model_comparison(root)
    backbone = pd.read_csv(root / BACKBONE_DIAGNOSIS, sep="\t")
    backbone = backbone.merge(model[["model_id", "model_label", "plot_color"]], on="model_id", how="left")
    smoke = pd.read_csv(root / SMOKE_SUMMARY, sep="\t")

    overview_cols = ["model_id", "model_label", "model_family", "plot_color", *METRICS]
    overview = (
        model.set_index("model_id")
        .reindex(OVERVIEW_ORDER)
        .reset_index()[overview_cols]
    )

    # Panel d: bootstrap ratio to baseline (3 main entrants, per-context)
    CONSISTENCY_IDS = [
        "gears_hcc_formal_v1",
        "geneformer_hcc_formal_v1",
        "scgpt_hcc_formal_v1",
    ]

    def _load_backbone_scores(model_id: str, cell_line: str) -> np.ndarray:
        path = root / f"reports/real_hcc_smoke/details/{model_id}/{cell_line}/axis_projection.tsv"
        df = pd.read_csv(path, sep="\t")
        backbone_targets = df.loc[
            df["is_expected_axis"] & df["architecture_role"].eq("canonical_backbone"),
            "target_gene",
        ].dropna().astype(str).unique().tolist()
        scores = []
        for target_gene, group in df.loc[df["target_gene"].isin(backbone_targets)].groupby("target_gene", sort=True):
            expected = group.loc[group["is_expected_axis"]]
            if expected.empty:
                continue
            series = group.set_index("fine_axis")["projected_mean_abs"]
            ranked = series.rank(method="average", ascending=False)
            axis_count = int(series.notna().sum())
            if axis_count <= 1:
                continue
            target_rank = float(ranked.loc[str(expected["fine_axis"].iloc[0])])
            score = 1.0 - ((target_rank - 1.0) / (axis_count - 1.0))
            scores.append(score)
        return np.array(scores)

    def _bootstrap_ratio(
        model_scores: np.ndarray,
        baseline_scores: np.ndarray,
        n_boot: int = 2000,
        seed: int = 42,
    ) -> tuple[float, float]:
        rng = np.random.RandomState(seed)
        n_model = len(model_scores)
        n_baseline = len(baseline_scores)
        ratios = []
        for _ in range(n_boot):
            m_idx = rng.choice(n_model, size=n_model, replace=True)
            b_idx = rng.choice(n_baseline, size=n_baseline, replace=True)
            m_mean = np.nanmean(model_scores[m_idx])
            b_mean = np.nanmean(baseline_scores[b_idx])
            ratios.append(m_mean / b_mean)
        ratios_arr = np.array(ratios)
        return float(np.mean(ratios_arr)), float(np.std(ratios_arr))

    panel_d_rows = []
    for cell_line in ["HCC38", "HCC1143"]:
        baseline_scores = _load_backbone_scores("shared_mean_baseline", cell_line)
        for model_id in CONSISTENCY_IDS:
            model_scores = _load_backbone_scores(model_id, cell_line)
            ratio_mean, se = _bootstrap_ratio(model_scores, baseline_scores)
            panel_d_rows.append({
                "model_id": model_id,
                "cell_line": cell_line,
                "ratio_mean": ratio_mean,
                "se": se,
            })
    panel_d_source = pd.DataFrame(panel_d_rows)

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
        "d": panel_d_source,
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
        "b": "Headline diagnostic reference versus GEARS dumbbell",
        "c": "Backbone–separation asymmetric recovery scatter",
        "d": "Backbone recovery relative to the diagnostic reference is consistent across the two primary contexts",
    }[panel_id]


PANEL_IDS: list[str] = ["a", "b", "c", "d"]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    manuscript_out = ensure_dir(manuscript_figure_dir(root))
    combined_source = pd.concat(
        [df.assign(panel=panel_id) for panel_id, df in sources.items()],
        ignore_index=True,
        sort=False,
    )
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")
    manuscript_source_path = write_tsv(combined_source, manuscript_out / "Figure_3_source_data.tsv")

    fig = plt.figure(figsize=(10.0, 6.5))
    # Two-level layout: top row = a + b; bottom row = c (3/10) + d (7/10).
    # Bottom row height compressed by ~1/3 vs prior version to keep the figure
    # compact and prevent c/d from feeling vertically stretched.
    outer = fig.add_gridspec(
        2,
        1,
        height_ratios=[1.0, 1.12],
        hspace=0.28,
        left=0.09,
        right=0.97,
        top=0.95,
        bottom=0.08,
    )
    top = outer[0].subgridspec(1, 2, wspace=0.38)
    ax_a = fig.add_subplot(top[0, 0])
    ax_b = fig.add_subplot(top[0, 1])
    bot = outer[1].subgridspec(1, 2, width_ratios=[3, 7], wspace=0.28)
    ax_c = fig.add_subplot(bot[0])
    ax_d = fig.add_subplot(bot[1])

    render_panel_a(ax_a, sources["a"])
    render_panel_b(ax_b, sources["b"])
    render_panel_c(ax_c, sources["c"])
    render_panel_d(ax_d, sources["d"])

    png_path = out / f"{FIGURE_ID}.png"
    pdf_path = out / f"{FIGURE_ID}.pdf"
    manuscript_png = manuscript_out / "Figure_3.png"
    manuscript_pdf = manuscript_out / "Figure_3.pdf"
    for path in [png_path, pdf_path, manuscript_png, manuscript_pdf]:
        ensure_dir(path.parent)
    finalize_manuscript_figure(fig)
    fig.savefig(png_path, dpi=1200, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(manuscript_png, dpi=1200, bbox_inches="tight")
    fig.savefig(manuscript_pdf, bbox_inches="tight")
    plt.close(fig)
    output_paths = [png_path, pdf_path]

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
    write_figure_manifest(
        manifest_path=manuscript_out / "Figure_3_panel_manifest.json",
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in PANEL_IDS],
        combined_source_data_path=manuscript_source_path,
        output_paths=[manuscript_png, manuscript_pdf],
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
    input_paths = [MODEL_COMPARISON, BACKBONE_DIAGNOSIS, SMOKE_SUMMARY, FINAL_CLAIM_MATRIX]

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
