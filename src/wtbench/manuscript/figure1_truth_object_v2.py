from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import (
    COLORS,
    add_panel_heading,
    add_panel_label,
    apply_manuscript_style,
    clean_axes,
    finalize_manuscript_figure,
)


FIGURE_ID = "figure1"
FIGURE_TITLE = "A truth-anchored benchmark defines a pre-specified perturbation-fitness recovery object in HCC38 and HCC1143"
SCRIPT_PATH = Path("scripts/manuscript/build_figure1_truth_object.py")
CLAIM_BOUNDARY = "The truth-DepMap bridge is retained as a structured target-level recovery object, not as fully deconfounded causal proof."

JOINT_GRID = Path("reports/stage2_truth_bridge_decomposition/target_level_joint_grid.tsv")
GRID_SUMMARY = Path("reports/stage2_truth_bridge_decomposition/target_level_grid_summary.tsv")
RUN_SUMMARY = Path("reports/stage2_truth_bridge_decomposition/run_summary.json")
HCC38_CORR = Path("reports/stage2_truth_driven_bridge/HCC38/correlation_summary.tsv")
HCC1143_CORR = Path("reports/stage2_truth_driven_bridge/HCC1143/correlation_summary.tsv")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")
BRIDGE_RHO_NULL = Path("reports/manuscript_permutation_null_v1/bridge_rho_permutation_summary.tsv")

FIG1_GREEN = "#009E73"
FIG1_GREEN_EDGE = "#007A5E"
FIG1_GREEN_FILL = "#E8F5E9"
FIG1_ORANGE = "#D55E00"
FIG1_ORANGE_ANNOTATION = "#CC5500"
FIG1_SKY_BLUE = "#56B4E9"
FIG1_WARM_GRAY = "#AAAAAA"
FIG1_LIGHT_GRAY = "#F5F5F5"
FIG1_PALE_GRAY = "#E8E8E8"
FIG1_MID_GRAY = "#BDBDBD"
FIG1_SEGMENT_EDGE = "#D6D6D6"
FIG1_AXIS = "#333333"
FIG1_BLACK = "#000000"
FIG1_DEEP_GRAY = "#424242"
FIG1_SUBDUED = "#616161"

GRID_COLORS = {
    "Q1_anchor": FIG1_GREEN,
    "Q2_transcriptomic_excess": FIG1_PALE_GRAY,
    "Q3_dependency_excess": FIG1_PALE_GRAY,
    "Q4_low_information": FIG1_LIGHT_GRAY,
    "middle": FIG1_MID_GRAY,
}

EXPECTED_Q1 = {"HCC38": 9, "HCC1143": 10}
ACTIVE_PANELS = list("cdef")  # old a/b moved to manual overview; c→new_a, d→new_b, e→new_c, f→new_d
PANEL_A_COLORS = {
    "divider": "#E0E0E0",
    "heading": FIG1_BLACK,
    "text": FIG1_DEEP_GRAY,
    "subline": FIG1_SUBDUED,
}


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig1_truth_object"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_1"


def manuscript_panel_dir(root: Path) -> Path:
    return manuscript_figure_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / p for p in [JOINT_GRID, GRID_SUMMARY, RUN_SUMMARY, HCC38_CORR, HCC1143_CORR, FINAL_CLAIM_MATRIX, BRIDGE_RHO_NULL]]


def load_joint_grid(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / JOINT_GRID, sep="\t")
    q1 = df.loc[df["joint_grid"].eq("Q1_anchor")].groupby("cell_line").size().to_dict()
    for cell_line, expected in EXPECTED_Q1.items():
        observed = int(q1.get(cell_line, 0))
        if observed != expected:
            raise RuntimeError(f"Fig. 1 Q1 sanity check failed for {cell_line}: observed={observed}, expected={expected}")
    return df


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
    manuscript_stem = f"Figure_1_panel_{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    manuscript_source_path = write_tsv(source_df, manuscript_pdir / f"{manuscript_stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    render(ax, source_df)
    png_path = pdir / f"{stem}.png"
    pdf_path = pdir / f"{stem}.pdf"
    manuscript_png_path = manuscript_pdir / f"{manuscript_stem}.png"
    manuscript_pdf_path = manuscript_pdir / f"{manuscript_stem}.pdf"
    for path in [png_path, pdf_path, manuscript_png_path, manuscript_pdf_path]:
        ensure_dir(path.parent)
    finalize_manuscript_figure(fig)
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(manuscript_png_path, dpi=300, bbox_inches="tight")
    fig.savefig(manuscript_pdf_path, bbox_inches="tight")
    plt.close(fig)
    output_paths = [png_path, pdf_path]
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
        panel_id=f"{FIGURE_ID}{panel_id}",
        panel_title=panel_title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=manuscript_source_path,
        output_paths=[manuscript_png_path, manuscript_pdf_path],
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_facecolor("white")
    add_panel_heading(ax, "", "Study workflow and frozen recovery object", title_x=0.00, title_fontsize=8.8)

    def rounded_box(
        x: float,
        y: float,
        w: float,
        h: float,
        label: str,
        *,
        face: str = "white",
        edge: str = FIG1_SEGMENT_EDGE,
        text_color: str = FIG1_DEEP_GRAY,
        lw: float = 0.75,
        weight: str = "normal",
        fontsize: float = 7.0,
        zorder: float = 2,
    ) -> None:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.010,rounding_size=0.012",
                facecolor=face,
                edgecolor=edge,
                linewidth=lw,
                transform=ax.transAxes,
                zorder=zorder,
            )
        )
        ax.text(
            x + w / 2,
            y + h / 2,
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            color=text_color,
            fontweight=weight,
            transform=ax.transAxes,
            linespacing=0.86,
            zorder=zorder + 1,
        )

    top_y = 0.66
    box_w = 0.135
    box_h = 0.205
    flow_xs = [0.040, 0.215, 0.390, 0.590, 0.785]
    steps = [
        ("perturbation\ntruth", FIG1_LIGHT_GRAY, FIG1_MID_GRAY, FIG1_DEEP_GRAY),
        ("DepMap\nCRISPR\nendpoint", FIG1_LIGHT_GRAY, FIG1_MID_GRAY, FIG1_DEEP_GRAY),
        ("frozen\nbridge\nobject", FIG1_GREEN, FIG1_GREEN_EDGE, "white"),
        ("model\nrecovery\nadjudication", "white", FIG1_MID_GRAY, FIG1_DEEP_GRAY),
        ("qualified\nclaim\nboundary", "#FFF3E0", FIG1_ORANGE, FIG1_DEEP_GRAY),
    ]
    phase_y = 0.905
    phase_specs = [
        (flow_xs[0], flow_xs[2] + box_w, "1. define object"),
        (flow_xs[3], flow_xs[4] + box_w, "2. adjudicate recovery"),
    ]
    for x0, x1, label in phase_specs:
        ax.plot(
            [x0, x1],
            [phase_y, phase_y],
            color="#E8E8E8",
            linewidth=0.8,
            transform=ax.transAxes,
            solid_capstyle="butt",
            zorder=1,
        )
        ax.text(
            (x0 + x1) / 2,
            phase_y + 0.015,
            label,
            ha="center",
            va="bottom",
            fontsize=6.4,
            color=FIG1_SUBDUED,
            fontweight="semibold",
            transform=ax.transAxes,
        )
    for idx, (x, (label, face, edge, text_color)) in enumerate(zip(flow_xs, steps)):
        rounded_box(
            x,
            top_y,
            box_w,
            box_h,
            label,
            face=face,
            edge=edge,
            text_color=text_color,
            lw=1.0 if idx in {2, 4} else 0.75,
            weight="semibold" if idx in {2, 4} else "normal",
        )
        if idx < len(flow_xs) - 1:
            ax.annotate(
                "",
                xy=(flow_xs[idx + 1] - 0.012, top_y + box_h / 2),
                xytext=(x + box_w + 0.012, top_y + box_h / 2),
                xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color=FIG1_DEEP_GRAY, lw=0.8, shrinkA=0, shrinkB=0),
                zorder=3,
            )

    lock_x = (flow_xs[2] + box_w + flow_xs[3]) / 2
    ax.text(
        lock_x,
        top_y - 0.030,
        "object locked",
        ha="center",
        va="top",
        fontsize=5.9,
        color=FIG1_SUBDUED,
        fontstyle="italic",
        transform=ax.transAxes,
    )

    entrant_x0 = flow_xs[3] - 0.052
    entrant_y0 = 0.405
    entrant_w = 0.244
    entrant_h = 0.108
    ax.text(
        entrant_x0,
        entrant_y0 + entrant_h + 0.018,
        "entrant set",
        ha="left",
        va="bottom",
        fontsize=6.4,
        color=FIG1_SUBDUED,
        fontweight="semibold",
        transform=ax.transAxes,
    )
    rounded_box(
        entrant_x0,
        entrant_y0,
        entrant_w,
        entrant_h,
        "baseline  |  GEARS\nfoundation / linear\n+ null / rebuttal checks",
        face="white",
        edge=FIG1_SEGMENT_EDGE,
        fontsize=6.5,
        lw=0.7,
        zorder=2,
    )
    ax.plot(
        [entrant_x0 + entrant_w * 0.45, entrant_x0 + entrant_w * 0.45],
        [entrant_y0 + 0.060, entrant_y0 + entrant_h - 0.018],
        color="#EAF4FB",
        linewidth=2.2,
        transform=ax.transAxes,
        solid_capstyle="round",
        zorder=2.5,
    )
    ax.annotate(
        "",
        xy=(flow_xs[3] + box_w / 2, top_y - 0.010),
        xytext=(flow_xs[3] + box_w / 2, entrant_y0 + entrant_h + 0.008),
        xycoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color=FIG1_MID_GRAY, lw=0.7, shrinkA=0, shrinkB=0),
        zorder=1.5,
    )

    strip_x = 0.045
    strip_y = 0.075
    strip_w = 0.870
    strip_h = 0.210
    ax.add_patch(
        FancyBboxPatch(
            (strip_x, strip_y),
            strip_w,
            strip_h,
            boxstyle="round,pad=0.012,rounding_size=0.014",
            facecolor="white",
            edgecolor=FIG1_SEGMENT_EDGE,
            linewidth=0.75,
            transform=ax.transAxes,
            zorder=1,
        )
    )
    ax.annotate(
        "",
        xy=(strip_x + strip_w * 0.50, strip_y + strip_h + 0.010),
        xytext=(flow_xs[2] + box_w / 2, top_y - 0.010),
        xycoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color=FIG1_GREEN, lw=0.75, shrinkA=0, shrinkB=0),
        zorder=1.5,
    )
    ax.text(
        strip_x + 0.018,
        strip_y + strip_h + 0.030,
        "Truth object fixed before model comparison",
        fontsize=7.3,
        color=FIG1_BLACK,
        fontweight="semibold",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
    )
    chips = [
        ("truth signal", "absolute mean\nperturbation shift"),
        ("endpoint", "CRISPR dependency"),
        ("category rule", "25/75 joint grid\n(Q1 / middle / Q4)"),
    ]
    chip_w = 0.255
    for i, (heading, value) in enumerate(chips):
        x = strip_x + 0.025 + i * (chip_w + 0.035)
        rounded_box(x, strip_y + 0.043, chip_w, 0.120, value, face=FIG1_LIGHT_GRAY, edge="#F0F0F0", fontsize=6.5, lw=0.5, zorder=2)
        ax.text(
            x,
            strip_y + 0.174,
            heading,
            fontsize=6.3,
            color=FIG1_SUBDUED,
            fontweight="semibold",
            transform=ax.transAxes,
            ha="left",
            va="center",
        )
    ax.text(
        0.920,
        0.155,
        "retained\nobject",
        fontsize=6.4,
        color=FIG1_GREEN,
        fontweight="bold",
        transform=ax.transAxes,
        ha="left",
        va="center",
        linespacing=0.85,
    )


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Primary benchmark contexts", loc="left", pad=0)
    cols = ["context", "truth", "endpoint", "n"]
    y0 = 0.76
    xs = [0.03, 0.30, 0.57, 0.90]
    for x, col in zip(xs, cols):
        ax.text(x, y0, col, fontsize=7, fontweight="bold", transform=ax.transAxes, color="#333333")
    ax.plot([0.03, 0.97], [0.71, 0.71], color="#B5B5B5", linewidth=0.7, transform=ax.transAxes)
    for i, row in enumerate(df.itertuples()):
        y = y0 - 0.18 * (i + 1)
        ax.text(xs[0], y, row.context, fontsize=7, transform=ax.transAxes)
        ax.text(xs[1], y, "absolute\nmean shift", fontsize=7, transform=ax.transAxes, linespacing=0.9)
        ax.text(xs[2], y, "CRISPR\nDepMap", fontsize=7, transform=ax.transAxes, linespacing=0.9)
        ax.text(xs[3], y, str(row.targets), fontsize=7, transform=ax.transAxes)
    ax.text(0.03, 0.12, "Larger aligned endpoint values indicate stronger dependency/liability.", fontsize=6, color="#666666", transform=ax.transAxes)
    # panel letter removed (PIL)


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_heading(ax, "", "Pre-specified 25/75 rule", title_x=0.00, title_fontsize=8.8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal", adjustable="box")
    for threshold in [0.25, 0.75]:
        ax.axvline(threshold, color=FIG1_SKY_BLUE, linewidth=0.75, alpha=0.80, linestyle=(0, (4, 2)), zorder=1)
        ax.axhline(threshold, color=FIG1_SKY_BLUE, linewidth=0.75, alpha=0.80, linestyle=(0, (4, 2)), zorder=1)
    quadrant_positions = {
        "Q1": (0.875, 0.925, "anchor", 0.875, 0.845),
        "Q2": (0.875, 0.205, "tx.\nexcess", 0.875, 0.125),
        "Q3": (0.125, 0.925, "dep.\nexcess", 0.125, 0.845),
        "Q4": (0.125, 0.205, "low\ninfo", 0.125, 0.125),
    }
    for tag, (tag_x, tag_y, desc, desc_x, desc_y) in quadrant_positions.items():
        ax.text(
            tag_x,
            tag_y,
            tag,
            ha="center",
            va="center",
            fontsize=8.0,
            color=FIG1_BLACK,
            fontweight="bold",
        )
        ax.text(
            desc_x,
            desc_y,
            desc,
            ha="center",
            va="top",
            fontsize=7.0,
            color=FIG1_DEEP_GRAY,
            fontweight="normal",
            linespacing=0.92,
        )
    ax.add_patch(
        plt.Rectangle(
            (0.80, 0.88),
            0.035,
            0.035,
            facecolor=FIG1_GREEN,
            edgecolor=FIG1_GREEN,
            transform=ax.transData,
            zorder=2,
        )
    )
    ax.text(
        0.50,
        0.50,
        "retained\nmiddle band",
        ha="center",
        va="center",
        fontsize=7.5,
        color=FIG1_DEEP_GRAY,
        linespacing=0.86,
    )
    ax.set_xticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0", "0.25", "0.5", "0.75", "1"], fontsize=7.5, color=FIG1_AXIS)
    ax.set_yticklabels(["0", "0.25", "0.5", "0.75", "1"], fontsize=7.5, color=FIG1_AXIS)
    ax.set_xlabel("")
    ax.set_ylabel("")
    for spine in ax.spines.values():
        spine.set_color(FIG1_AXIS)
        spine.set_linewidth(0.8)
    ax.tick_params(axis="both", colors=FIG1_AXIS, length=2.2, width=0.8, pad=1.2)
    ax.text(0.50, -0.105, "shift quantile", fontsize=7.5, color=FIG1_BLACK, transform=ax.transAxes, ha="center")
    ax.text(
        -0.16,
        0.50,
        "CRISPR dependency quantile",
        fontsize=7.5,
        color=FIG1_BLACK,
        transform=ax.transAxes,
        rotation=90,
        ha="center",
        va="center",
    )


def _style_axes_for_figure1(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.spines["left"].set_color(FIG1_AXIS)
    ax.spines["bottom"].set_color(FIG1_AXIS)
    ax.tick_params(axis="both", which="major", length=2.4, width=0.8, pad=1.5, colors=FIG1_AXIS)
    ax.grid(False)


def _add_joint_grid_key(ax: plt.Axes) -> None:
    key_x = 0.04
    key_y = 0.71
    ax.scatter(
        [key_x],
        [key_y],
        transform=ax.transAxes,
        s=34,
        facecolors=FIG1_GREEN,
        edgecolors=FIG1_GREEN_EDGE,
        linewidths=0.75,
        clip_on=False,
        zorder=5,
    )
    ax.text(
        key_x + 0.035,
        key_y,
        "Q1 anchors",
        transform=ax.transAxes,
        fontsize=7.6,
        color=FIG1_BLACK,
        va="center",
        ha="left",
    )
    ax.scatter(
        [key_x],
        [key_y - 0.075],
        transform=ax.transAxes,
        s=26,
        facecolors="none",
        edgecolors=FIG1_WARM_GRAY,
        linewidths=0.75,
        clip_on=False,
        zorder=5,
    )
    ax.text(
        key_x + 0.035,
        key_y - 0.075,
        "other targets",
        transform=ax.transAxes,
        fontsize=7.6,
        color=FIG1_BLACK,
        va="center",
        ha="left",
    )


def render_joint_grid(ax: plt.Axes, df: pd.DataFrame, cell_line: str, label: str) -> None:
    plot = df.loc[df["cell_line"].eq(cell_line)].copy()
    shared_anchor_labels = {"PFDN5", "PMF1", "PRPF6", "ZNF131"}
    q1 = plot.loc[plot["joint_grid"].eq("Q1_anchor")]
    labeled_q1 = q1.loc[q1["target_gene"].isin(shared_anchor_labels)]
    unlabeled_q1 = q1.loc[~q1["target_gene"].isin(shared_anchor_labels)]
    background = plot.loc[~plot["joint_grid"].eq("Q1_anchor")]
    ax.scatter(
        background["shift_quantile"],
        background["depmap_quantile"],
        facecolors="none",
        edgecolors=FIG1_WARM_GRAY,
        s=24,
        alpha=0.95,
        linewidth=0.75,
        zorder=2,
    )
    ax.scatter(
        unlabeled_q1["shift_quantile"],
        unlabeled_q1["depmap_quantile"],
        c=GRID_COLORS["Q1_anchor"],
        s=49,
        alpha=1.0,
        edgecolor=FIG1_GREEN_EDGE,
        linewidth=0.75,
        zorder=4,
    )
    ax.scatter(
        labeled_q1["shift_quantile"],
        labeled_q1["depmap_quantile"],
        c=GRID_COLORS["Q1_anchor"],
        s=49,
        alpha=1.0,
        edgecolor=FIG1_GREEN_EDGE,
        linewidth=0.75,
        zorder=4,
    )

    label_x = 1.15
    label_entries = labeled_q1.sort_values("depmap_quantile", ascending=False).reset_index(drop=True)
    n_labels = len(label_entries)
    if n_labels > 0:
        min_gap = 0.085
        upper_bound = 1.02
        lower_bound = 0.56
        desired_y = label_entries["depmap_quantile"].to_numpy(dtype=float)
        label_y = np.clip(desired_y.copy(), lower_bound, upper_bound)
        for i in range(1, n_labels):
            max_allowed = label_y[i - 1] - min_gap
            if label_y[i] > max_allowed:
                label_y[i] = max_allowed
        for i in range(n_labels - 1, 0, -1):
            if label_y[i] < lower_bound:
                deficit = lower_bound - label_y[i]
                for j in range(i + 1):
                    label_y[j] += deficit
        label_y = np.clip(label_y, lower_bound, upper_bound)
        for (row_data, ly) in zip(label_entries.itertuples(), label_y):
            ax.plot(
                [row_data.shift_quantile, label_x - 0.020],
                [row_data.depmap_quantile, ly],
                color=FIG1_ORANGE_ANNOTATION,
                alpha=0.85,
                linewidth=0.75,
                zorder=4.2,
            )
            ax.text(
                label_x,
                ly,
                row_data.target_gene,
                fontsize=7.5,
                color=FIG1_BLACK,
                va="center",
                ha="right",
                clip_on=True,
                zorder=5,
            )

    for threshold in [0.25, 0.75]:
        ax.axvline(threshold, color=FIG1_SKY_BLUE, linewidth=0.75, alpha=0.80, linestyle=(0, (4, 2)), zorder=1)
        ax.axhline(threshold, color=FIG1_SKY_BLUE, linewidth=0.75, alpha=0.80, linestyle=(0, (4, 2)), zorder=1)
    ax.set_xlim(-0.02, 1.18)
    ax.set_ylim(-0.02, 1.08)
    ax.set_xticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0", "0.25", "0.5", "0.75", "1"], fontsize=7.5)
    ax.set_yticklabels(["0", "0.25", "0.5", "0.75", "1"], fontsize=7.5)
    ax.set_xlabel("Transcriptomic perturbation shift quantile")
    ax.set_ylabel("CRISPR dependency quantile")
    rho = plot["spearman_rho_aligned"].dropna()
    n_targets = plot["n_targets"].dropna()
    rho_text = f"{float(rho.iloc[0]):.3f}" if not rho.empty else "NA"
    n_text = f"{int(n_targets.iloc[0])}" if not n_targets.empty else f"{len(plot)}"
    add_panel_heading(
        ax,
        "",
        f"{cell_line} target-level joint grid",
        title_x=0.00,
        title_fontsize=8.8,
    )
    ax.text(0.03, 0.96, f"n={n_text}", transform=ax.transAxes, fontsize=8.0, color=FIG1_BLACK, fontweight="bold", va="top")
    ax.text(0.03, 0.89, f"Spearman \u03c1 = {rho_text}", transform=ax.transAxes, fontsize=8.0, color=FIG1_BLACK, fontweight="bold", va="top")
    ax.text(
        0.03,
        0.82,
        f"Q1: {len(q1)} anchors",
        transform=ax.transAxes,
        fontsize=8.0,
        color=GRID_COLORS["Q1_anchor"],
        fontweight="bold",
        va="top",
    )
    _add_joint_grid_key(ax)
    _style_axes_for_figure1(ax)


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    render_joint_grid(ax, df, "HCC38", "c")


def render_panel_e(ax: plt.Axes, df: pd.DataFrame) -> None:
    render_joint_grid(ax, df, "HCC1143", "d")


def render_panel_f(ax: plt.Axes, df: pd.DataFrame) -> None:
    order = ["Q4_low_information", "Q3_dependency_excess", "middle", "Q2_transcriptomic_excess", "Q1_anchor"]
    labels = {
        "Q1_anchor": "Q1 anchors",
        "Q2_transcriptomic_excess": "Q2",
        "Q3_dependency_excess": "Q3",
        "middle": "Retained middle band",
        "Q4_low_information": "Q4 low info",
    }
    pivot = df.pivot_table(index="cell_line", columns="joint_grid", values="fraction_targets", fill_value=0).reindex(columns=order).fillna(0)
    counts = df.pivot_table(index="cell_line", columns="joint_grid", values="n_targets", fill_value=0).reindex(columns=order).fillna(0)
    pivot = pivot.reindex(["HCC38", "HCC1143"])
    counts = counts.reindex(["HCC38", "HCC1143"])
    y = np.array([0.0, 1.05])
    bar_h = 0.72
    left = np.zeros(len(pivot))
    q1_counts_by_line = {cl: int(counts.loc[cl, "Q1_anchor"]) for cl in pivot.index}
    for grid in order:
        vals = pivot[grid].to_numpy()
        edgecolor = FIG1_SEGMENT_EDGE if grid == "Q4_low_information" else "white"
        linewidth = 1.0 if grid == "Q4_low_information" else 0.8
        ax.barh(y, vals, left=left, height=bar_h, color=GRID_COLORS[grid], edgecolor=edgecolor, linewidth=linewidth)
        for yi, val, start, cell_line in zip(y, vals, left, pivot.index):
            if val >= 0.10:
                pct = f"{val * 100:.0f}%"
                is_q1 = grid == "Q1_anchor"
                color = FIG1_BLACK
                weight = "bold"
                fontsize = 7.5 if grid != "Q4_low_information" else 7.1
                if is_q1:
                    text = f"Q1 anchors\nn={q1_counts_by_line[cell_line]}, {pct}"
                elif grid == "middle":
                    text = f"retained middle band\n{pct}"
                else:
                    text = f"{labels[grid]}\n{pct}"
                ax.text(
                    start + val / 2,
                    yi,
                    text,
                    ha="center",
                    va="center",
                    fontsize=fontsize,
                    color=color,
                    fontweight=weight,
                    linespacing=0.90,
                )
        left += vals
    ax.set_yticks(y)
    ax.set_yticklabels(pivot.index, fontsize=7.0)
    ax.invert_yaxis()
    ax.set_ylim(1.80, -0.60)
    ax.set_xlim(-0.015, 1.10)
    ax.set_xticks(np.linspace(0, 1, 6))
    ax.set_xticklabels([f"{int(x * 100)}%" for x in np.linspace(0, 1, 6)], fontsize=7.5)
    ax.set_xlabel("Target composition")
    add_panel_heading(ax, "", "Grid composition across primary contexts", title_x=0.00, title_fontsize=8.8)
    ax.tick_params(axis="y", length=0)
    ax.grid(False)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_bounds(0.0, 1.0)
    ax.spines["bottom"].set_color(FIG1_AXIS)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(axis="x", colors=FIG1_AXIS, width=0.8, length=2.4, pad=1.5)


def render_panel_bridge_strength(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Panel (f): headline aligned Spearman bridge strength with Fisher 95% CI and
    an empirical permutation null envelope. The panel is intentionally minimal:
    two context dots, per-context CI, and a single null band. No bootstrap, no
    tiering, no per-target annotation."""
    order = ["HCC38", "HCC1143"]
    ordered = df.set_index("cell_line").reindex(order).reset_index()
    x = np.array([0.0, 0.52])
    rho = ordered["spearman_rho_aligned"].to_numpy()
    ci_lo = ordered["ci_lo_fisher95"].to_numpy()
    ci_hi = ordered["ci_hi_fisher95"].to_numpy()
    n_targets = ordered["n_targets"].to_numpy()
    null_lo = float(ordered["null_q025"].min())
    null_hi = float(ordered["null_q975"].max())
    null_iter = int(ordered["null_iterations"].max())
    series_colors = {"HCC38": FIG1_ORANGE, "HCC1143": FIG1_GREEN}
    ax.axhspan(null_lo, null_hi, color=FIG1_PALE_GRAY, alpha=0.30, zorder=0, linewidth=0)
    ax.axhline(0.0, color=FIG1_AXIS, linewidth=0.8, zorder=0.5)
    for xi, rho_val, lo, hi, ni, cell_line in zip(x, rho, ci_lo, ci_hi, n_targets, order):
        color = series_colors[cell_line]
        ax.errorbar(
            [xi],
            [rho_val],
            yerr=[[rho_val - lo], [hi - rho_val]],
            fmt="none",
            ecolor=color,
            elinewidth=1.0,
            capsize=4.0,
            capthick=1.0,
            zorder=2,
        )
        ax.scatter(
            [xi],
            [rho_val],
            s=42,
            c=color,
            edgecolor=color,
            linewidth=0.75,
            zorder=3,
        )
        ax.text(
            xi + 0.045,
            rho_val + 0.003,
            f"{rho_val:.3f} / n={int(ni)}",
            fontsize=7.0,
            color=FIG1_BLACK,
            fontweight="bold",
            va="bottom",
            ha="left",
            zorder=4,
        )
    ax.text(
        0.50,
        -0.180,
        r"points = aligned Spearman $\rho$;  bars = Fisher z 95% CI",
        transform=ax.transAxes,
        fontsize=7.0,
        color=FIG1_SUBDUED,
        va="top",
        ha="center",
    )
    ax.text(
        0.50,
        -0.275,
        rf"gray band = null ($\rho=0$) 95% envelope, {null_iter} perm.",
        transform=ax.transAxes,
        fontsize=7.0,
        color=FIG1_SUBDUED,
        va="top",
        ha="center",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.set_xlim(-0.16, 0.96)
    ax.set_ylim(-0.08, 1.0)
    ax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0.00", "0.25", "0.50", "0.75", "1.00"], fontsize=7.5)
    ax.set_ylabel(r"Aligned Spearman $\rho$")
    add_panel_heading(ax, "", "Bridge strength", title_x=0.00, title_fontsize=8.8)
    _style_axes_for_figure1(ax)
    ax.legend(
        handles=[
            Line2D([0], [0], marker="o", linestyle="", color="none", markerfacecolor=FIG1_ORANGE, markeredgecolor=FIG1_ORANGE, markersize=5.2, label=f"HCC38 (n={int(n_targets[0])})"),
            Line2D([0], [0], marker="o", linestyle="", color="none", markerfacecolor=FIG1_GREEN, markeredgecolor=FIG1_GREEN, markersize=5.2, label=f"HCC1143 (n={int(n_targets[1])})"),
            Patch(facecolor=FIG1_PALE_GRAY, edgecolor="none", alpha=0.30, label="Null envelope"),
        ],
        loc="center left",
        bbox_to_anchor=(1.02, 0.46),
        fontsize=7.5,
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=0.95,
        borderpad=0.35,
        labelspacing=0.30,
        handlelength=1.0,
        handletextpad=0.50,
    )


def render_panel_h(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Claim boundary", loc="left", pad=0)
    rows = [
        ("Allowed", "structured target-level recovery object"),
        ("Allowed", "categories fixed before entrant adjudication"),
        ("Not allowed", "fully deconfounded causal proof"),
        ("Not allowed", "target proof from bridge structure alone"),
    ]
    y = 0.86
    for status, text in rows:
        color = COLORS["primary_qualified"] if status == "Allowed" else COLORS["boundary"]
        ax.text(0.02, y, status, color=color, fontweight="bold", fontsize=7, transform=ax.transAxes)
        ax.text(0.34, y, text, fontsize=7, transform=ax.transAxes)
        y -= 0.18
    ax.text(0.02, 0.05, "Boundary fixed before model comparison.", fontsize=6, color="#666666", transform=ax.transAxes)
    # panel letter removed (PIL)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    joint = load_joint_grid(root)
    summary = pd.read_csv(root / GRID_SUMMARY, sep="\t")
    hcc38 = pd.read_csv(root / HCC38_CORR, sep="\t")
    hcc1143 = pd.read_csv(root / HCC1143_CORR, sep="\t")
    corr = pd.concat([hcc38, hcc1143], ignore_index=True)
    corr = corr.loc[
        corr["truth_metric"].eq("real_shift_mean_abs") & corr["depmap_endpoint"].eq("depmap_gene_dependency"),
        ["cell_line", "truth_metric", "depmap_endpoint", "n_targets", "spearman_rho_aligned", "pearson_r_aligned"],
    ]
    workflow = pd.DataFrame(
        [
            {"step": 1, "name": "perturbation truth", "role": "input"},
            {"step": 2, "name": "DepMap CRISPR endpoint", "role": "alignment endpoint"},
            {"step": 3, "name": "frozen bridge object", "role": "pre-specified recovery object"},
            {"step": 4, "name": "model recovery adjudication", "role": "baseline, GEARS, foundation models, linear controls"},
            {"step": 5, "name": "qualified claim boundary", "role": "bounded interpretation"},
            {"step": 6, "name": "truth signal = absolute mean perturbation shift", "role": "truth-object definition"},
            {"step": 7, "name": "category rule = 25/75 joint grid", "role": "truth-object definition"},
        ]
    )
    definition = pd.DataFrame(
        [
            {"region": "Q1_anchor", "shift_band": "high", "depmap_band": "high"},
            {"region": "Q2_transcriptomic_excess", "shift_band": "high", "depmap_band": "low"},
            {"region": "Q3_dependency_excess", "shift_band": "low", "depmap_band": "high"},
            {"region": "Q4_low_information", "shift_band": "low", "depmap_band": "low"},
            {"region": "middle", "shift_band": "middle_any", "depmap_band": "middle_any"},
        ]
    )
    q1_counts = joint.loc[joint["joint_grid"].eq("Q1_anchor")].groupby("cell_line").size().rename("q1_anchors")
    corr = corr.merge(q1_counts, on="cell_line", how="left")
    joint = joint.merge(
        corr[["cell_line", "n_targets", "spearman_rho_aligned"]],
        on="cell_line",
        how="left",
    )
    bridge_strength = _build_bridge_strength_frame(corr, root=root)
    return {
        "a": workflow,
        "b": definition,
        "c": joint.loc[joint["cell_line"].eq("HCC38")],
        "d": joint.loc[joint["cell_line"].eq("HCC1143")],
        "e": summary,
        "f": bridge_strength,
    }


def _build_bridge_strength_frame(corr: pd.DataFrame, *, root: Path) -> pd.DataFrame:
    """Build the panel-(f) source data: observed aligned Spearman rho with a
    Fisher z-transform 95% CI around the point, plus a rho=0 null envelope
    taken from the empirical permutation null (see
    `reports/manuscript_permutation_null_v1/bridge_rho_permutation_summary.tsv`).
    Point-level CI and null envelope are kept as separate concepts."""
    columns = ["cell_line", "truth_metric", "depmap_endpoint", "n_targets", "spearman_rho_aligned"]
    frame = corr[columns].copy()
    n = frame["n_targets"].to_numpy(dtype=float)
    rho = frame["spearman_rho_aligned"].to_numpy(dtype=float)
    rho_clipped = np.clip(rho, -0.999999, 0.999999)
    z = np.arctanh(rho_clipped)
    se_z = 1.0 / np.sqrt(np.maximum(n - 3.0, 1.0))
    frame["ci_lo_fisher95"] = np.tanh(z - 1.96 * se_z)
    frame["ci_hi_fisher95"] = np.tanh(z + 1.96 * se_z)
    frame["ci_method"] = "fisher_z_transform"

    null_path = root / BRIDGE_RHO_NULL
    if not null_path.exists():
        raise RuntimeError(
            f"Missing permutation null summary at {null_path}; run scripts/run_bridge_rho_permutation_null.py first."
        )
    null_df = pd.read_csv(null_path, sep="\t")
    null_cols = ["cell_line", "null_q025", "null_q975", "null_iterations", "empirical_p_two_sided"]
    missing = [c for c in null_cols if c not in null_df.columns]
    if missing:
        raise RuntimeError(f"Bridge rho permutation null missing columns: {missing}")
    frame = frame.merge(null_df[null_cols], on="cell_line", how="left")
    if frame[["null_q025", "null_q975"]].isna().any().any():
        raise RuntimeError("Permutation null not available for every primary context")
    frame["null_type"] = "target_to_depmap_permutation"
    return frame.reset_index(drop=True)


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {
        "a": render_panel_a,
        "b": render_panel_c,
        "c": render_panel_d,
        "d": render_panel_e,
        "e": render_panel_f,
        "f": render_panel_bridge_strength,
        "h": render_panel_h,
    }[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Pre-specified recovery object",
        "b": "Pre-specified 25/75 category rule",
        "c": "HCC38 target-level joint grid",
        "d": "HCC1143 target-level joint grid",
        "e": "Grid composition across primary contexts",
        "f": "Bridge strength",
        "h": "Truth-object claim boundary",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    manuscript_out = ensure_dir(manuscript_figure_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")
    write_tsv(combined_source, manuscript_out / "Figure_1_source_data.tsv")
    fig = plt.figure(figsize=(11.0, 7.0))
    fig.patch.set_facecolor("white")
    mosaic = [
        ["c", "c", "c", "c", "c", "d", "d", "d", "d", "d"],
        ["c", "c", "c", "c", "c", "d", "d", "d", "d", "d"],
        ["e", "e", "e", "e", "e", "e", "f", "f", "f", "."],
        ["e", "e", "e", "e", "e", "e", "f", "f", "f", "."],
    ]
    axes = fig.subplot_mosaic(
        mosaic,
        gridspec_kw={"hspace": 0.95, "wspace": 0.84, "height_ratios": [1.0, 1.0, 1.44, 1.44]},
    )
    for panel_id in ACTIVE_PANELS:
        render_panel_by_id(panel_id)(axes[panel_id], sources[panel_id])
    png_path = out / f"{FIGURE_ID}.png"
    pdf_path = out / f"{FIGURE_ID}.pdf"
    manuscript_png = manuscript_out / "Figure_1.png"
    manuscript_pdf = manuscript_out / "Figure_1.pdf"
    for path in [png_path, pdf_path, manuscript_png, manuscript_pdf]:
        ensure_dir(path.parent)
    finalize_manuscript_figure(fig)
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
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in ACTIVE_PANELS],
        combined_source_data_path=combined_source_path,
        output_paths=output_paths,
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": combined_source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build manuscript Figure 1 truth-object panels and assembly.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    apply_manuscript_style()
    sources = build_sources(root)
    panel_outputs: dict[str, dict[str, Path]] = {}
    panel_sizes = {
        "a": (5.15, 2.40),
        "b": (3.55, 2.70),
        "c": (3.55, 2.70),
        "d": (3.55, 2.70),
        "e": (4.85, 2.20),
        "f": (2.95, 2.85),
    }
    for panel_id in ACTIVE_PANELS:
        width, height = panel_sizes.get(panel_id, (3.20, 2.35))
        panel_outputs[panel_id] = write_panel(
            root=root,
            panel_id=panel_id,
            panel_title=panel_title(panel_id),
            source_df=sources[panel_id],
            render=render_panel_by_id(panel_id),
            width=width,
            height=height,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
