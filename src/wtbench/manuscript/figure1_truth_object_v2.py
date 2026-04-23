from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wtbench.manuscript._palette import (
    DARK_TEXT,
    PRIMARY_GREEN,
    PRIMARY_GREEN_EDGE,
    PRIMARY_GREEN_FILL,
)
from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes


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

GRID_COLORS = {
    "Q1_anchor": PRIMARY_GREEN,
    "Q2_transcriptomic_excess": "#D0D0D0",
    "Q3_dependency_excess": "#DCDCDC",
    "Q4_low_information": "#EEEEEE",
    "middle": "#BDBDBD",
}

EXPECTED_Q1 = {"HCC38": 9, "HCC1143": 10}
ACTIVE_PANELS = list("abcdef")
PANEL_A_COLORS = {
    "divider": "#ECECEC",
    "heading": DARK_TEXT,
    "text": "#4A4A4A",
    "subline": "#858585",
}


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig1_truth_object"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


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
    stem = f"{FIGURE_ID}_panel{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
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
        input_paths=input_paths(root),
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_facecolor("white")
    ax.set_title("Truth-first recovery object", loc="left", pad=4)

    flow_y = 0.830
    flow_box_h = 0.210
    flow_steps = [
        "real\nperturbation\ntruth",
        "DepMap\nCRISPR\ndependency",
        "frozen\nbridge\nobject",
        "model\nrecovery\nadjudication",
        "gated\ndiscovery",
    ]
    flow_xs = np.linspace(0.095, 0.905, len(flow_steps))
    box_half_w = (flow_xs[1] - flow_xs[0]) * 0.40
    frozen_idx = 2
    frozen_cx = flow_xs[frozen_idx]
    for i, (cx, label) in enumerate(zip(flow_xs, flow_steps)):
        is_frozen = i == frozen_idx
        face = PRIMARY_GREEN_FILL if is_frozen else "#F6F6F6"
        edge = PRIMARY_GREEN_EDGE if is_frozen else "#B5B5B5"
        ax.add_patch(
            plt.Rectangle(
                (cx - box_half_w, flow_y - flow_box_h / 2),
                2 * box_half_w,
                flow_box_h,
                facecolor=face,
                edgecolor=edge,
                linewidth=0.65 if is_frozen else 0.55,
                transform=ax.transAxes,
                zorder=2,
            )
        )
        ax.text(
            cx,
            flow_y,
            label,
            ha="center",
            va="center",
            fontsize=6.0,
            color="#2B2B2B" if is_frozen else "#3A3A3A",
            fontweight="semibold" if is_frozen else "normal",
            transform=ax.transAxes,
            linespacing=0.88,
            zorder=3,
        )
    for cx_from, cx_to in zip(flow_xs[:-1], flow_xs[1:]):
        ax.annotate(
            "",
            xy=(cx_to - box_half_w - 0.003, flow_y),
            xytext=(cx_from + box_half_w + 0.003, flow_y),
            xycoords="axes fraction",
            arrowprops=dict(arrowstyle="-|>", color="#7A7A7A", lw=0.55, shrinkA=0, shrinkB=0),
            zorder=2,
        )

    strip_x = 0.040
    strip_y = 0.040
    strip_w = 0.920
    strip_h = 0.540

    connector_top = flow_y - flow_box_h / 2
    connector_bot = strip_y + strip_h + 0.012
    ax.annotate(
        "",
        xy=(frozen_cx, connector_bot),
        xytext=(frozen_cx, connector_top - 0.008),
        xycoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color=PRIMARY_GREEN_EDGE, lw=0.65, shrinkA=0, shrinkB=0),
        zorder=2,
    )
    ax.text(
        frozen_cx + 0.020,
        (connector_top + connector_bot) / 2,
        "unpacked",
        fontsize=5.5,
        color=PRIMARY_GREEN_EDGE,
        va="center",
        ha="left",
        transform=ax.transAxes,
        fontstyle="italic",
        zorder=3,
    )

    ax.add_patch(
        plt.Rectangle(
            (strip_x, strip_y),
            strip_w,
            strip_h,
            facecolor="#F8F8F8",
            edgecolor="#CDCDCD",
            linewidth=0.55,
            transform=ax.transAxes,
            zorder=1,
        )
    )
    for frac in (1 / 3, 2 / 3):
        x = strip_x + strip_w * frac
        ax.plot(
            [x, x],
            [strip_y + 0.024, strip_y + strip_h - 0.024],
            color=PANEL_A_COLORS["divider"],
            linewidth=0.38,
            transform=ax.transAxes,
            solid_capstyle="butt",
            zorder=2,
        )
    columns = [
        ("Truth object", "Absolute mean\nperturbation shift", "Perturbation-defined\ntranscriptomic signal"),
        ("Alignment endpoint", "CRISPR dependency", "DepMap phenotype-aligned\nreference endpoint"),
        ("Category rule", "Pre-specified\n25/75 joint grid", "Q1 anchor / middle band /\nQ4 low info"),
    ]
    for index, (heading, object_text, note) in enumerate(columns):
        center_x = strip_x + strip_w * (index + 0.5) / 3
        ax.text(
            center_x,
            strip_y + strip_h - 0.078,
            heading,
            ha="center",
            va="center",
            fontsize=6.0,
            fontweight="semibold",
            color=PANEL_A_COLORS["heading"],
            transform=ax.transAxes,
            zorder=3,
        )
        ax.text(
            center_x,
            strip_y + strip_h * 0.50,
            object_text,
            ha="center",
            va="center",
            fontsize=5.55,
            fontweight="semibold",
            color=PANEL_A_COLORS["text"],
            transform=ax.transAxes,
            linespacing=0.84,
            zorder=3,
        )
        ax.text(
            center_x,
            strip_y + 0.074,
            note,
            ha="center",
            va="center",
            fontsize=5.5,
            color=PANEL_A_COLORS["subline"],
            transform=ax.transAxes,
            linespacing=0.92,
            zorder=3,
        )
    add_panel_label(ax, "a", x=-0.04)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Primary benchmark contexts", loc="left", pad=4)
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
    add_panel_label(ax, "b", x=-0.04)


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_title("Pre-specified 25/75 rule", loc="left", fontweight="normal", fontsize=6.4)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal", adjustable="box")
    corner_gray = "#F5F5F5"
    ax.add_patch(plt.Rectangle((0.75, 0.75), 0.25, 0.25, facecolor=PRIMARY_GREEN_FILL, edgecolor="none", zorder=0))
    for x, y in [(0, 0.75), (0.75, 0), (0, 0)]:
        ax.add_patch(plt.Rectangle((x, y), 0.25, 0.25, facecolor=corner_gray, edgecolor="none", zorder=0))
    for threshold in [0.25, 0.75]:
        ax.axvline(threshold, color="#9A9A9A", linewidth=0.55, linestyle=(0, (4, 2)), zorder=1)
        ax.axhline(threshold, color="#9A9A9A", linewidth=0.55, linestyle=(0, (4, 2)), zorder=1)
    quadrants = [
        ("Q1", "anchor", 0.875, 0.875, GRID_COLORS["Q1_anchor"], PRIMARY_GREEN_EDGE),
        ("Q2", "transcriptomic\nexcess", 0.875, 0.125, "#3A3A3A", "#6F6F6F"),
        ("Q3", "dependency\nexcess", 0.125, 0.875, "#3A3A3A", "#6F6F6F"),
        ("Q4", "low\ninfo", 0.125, 0.125, "#3A3A3A", "#6F6F6F"),
    ]
    tag_fontsize = 6.8
    desc_fontsize = 5.5
    tag_offset = 0.055
    desc_offset = 0.020
    for tag, desc, x, y, tag_color, desc_color in quadrants:
        ax.text(
            x,
            y + tag_offset,
            tag,
            ha="center",
            va="center",
            fontsize=tag_fontsize,
            color=tag_color,
            fontweight="bold",
        )
        ax.text(
            x,
            y - desc_offset,
            desc,
            ha="center",
            va="top",
            fontsize=desc_fontsize,
            color=desc_color,
            fontweight="normal",
            linespacing=0.92,
        )
    ax.text(
        0.50,
        0.50,
        "retained\nmiddle band",
        ha="center",
        va="center",
        fontsize=6.0,
        color="#4A4A4A",
        linespacing=0.86,
    )
    ax.set_xticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0", "0.25", "0.5", "0.75", "1"], fontsize=5.5, color="#7A7A7A")
    ax.set_yticklabels(["0", "0.25", "0.5", "0.75", "1"], fontsize=5.5, color="#7A7A7A")
    ax.set_xlabel("")
    ax.set_ylabel("")
    for spine in ax.spines.values():
        spine.set_color("#8A8A8A")
        spine.set_linewidth(0.50)
    ax.tick_params(axis="both", colors="#7A7A7A", length=1.8, width=0.5, pad=1.2)
    ax.text(0.50, -0.105, "shift quantile", fontsize=5.5, color="#6F6F6F", transform=ax.transAxes, ha="center")
    ax.text(-0.150, 0.50, "dependency quantile", fontsize=5.5, color="#6F6F6F", transform=ax.transAxes, rotation=90, va="center")
    add_panel_label(ax, "b", x=-0.12)


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
        c="#D2D2D2",
        s=18,
        alpha=0.80,
        edgecolor="none",
        zorder=2,
    )
    ax.scatter(
        unlabeled_q1["shift_quantile"],
        unlabeled_q1["depmap_quantile"],
        c=GRID_COLORS["Q1_anchor"],
        s=31,
        alpha=1.0,
        edgecolor="white",
        linewidth=0.35,
        zorder=4,
    )
    ax.scatter(
        labeled_q1["shift_quantile"],
        labeled_q1["depmap_quantile"],
        c=GRID_COLORS["Q1_anchor"],
        s=33,
        alpha=1.0,
        edgecolor="white",
        linewidth=0.35,
        zorder=4,
    )

    label_x = 1.10
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
                color="#B8B8B8",
                linewidth=0.38,
                zorder=4.2,
            )
            ax.text(
                label_x,
                ly,
                row_data.target_gene,
                fontsize=6.0,
                color="#2B2B2B",
                va="center",
                ha="left",
                zorder=5,
            )

    for threshold in [0.25, 0.75]:
        ax.axvline(threshold, color="#929292", linewidth=0.50, linestyle=(0, (4, 2)), zorder=1)
        ax.axhline(threshold, color="#929292", linewidth=0.50, linestyle=(0, (4, 2)), zorder=1)
    ax.set_xlim(-0.02, 1.22)
    ax.set_ylim(-0.02, 1.08)
    ax.set_xticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0", "0.25", "0.5", "0.75", "1"])
    ax.set_yticklabels(["0", "0.25", "0.5", "0.75", "1"])
    ax.set_xlabel("Transcriptomic perturbation shift quantile")
    ax.set_ylabel("CRISPR dependency quantile")
    rho = plot["spearman_rho_aligned"].dropna()
    n_targets = plot["n_targets"].dropna()
    rho_text = f"{float(rho.iloc[0]):.3f}" if not rho.empty else "NA"
    n_text = f"{int(n_targets.iloc[0])}" if not n_targets.empty else f"{len(plot)}"
    ax.set_title(f"{cell_line} target-level joint grid", loc="left")
    ax.text(0.03, 0.96, f"n={n_text}", transform=ax.transAxes, fontsize=6.0, color="#2B2B2B", va="top")
    ax.text(0.03, 0.89, rf"$\rho$={rho_text}", transform=ax.transAxes, fontsize=6.0, color="#2B2B2B", va="top")
    ax.text(
        0.03,
        0.82,
        f"Q1={len(q1)}",
        transform=ax.transAxes,
        fontsize=6.0,
        color=GRID_COLORS["Q1_anchor"],
        fontweight="bold",
        va="top",
    )
    clean_axes(ax)
    ax.grid(False)
    add_panel_label(ax, label)


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
        ax.barh(y, vals, left=left, height=bar_h, color=GRID_COLORS[grid], edgecolor="white", linewidth=0.6)
        for yi, val, start, cell_line in zip(y, vals, left, pivot.index):
            if val >= 0.10:
                pct = f"{val * 100:.0f}%"
                is_q1 = grid == "Q1_anchor"
                color = "white" if is_q1 else ("#3F3F3F" if grid == "middle" else "#2B2B2B")
                weight = "bold" if is_q1 else "normal"
                # Middle band carries object-definition weight ("retained middle
                # band" is part of the truth object, not ignorable residual) and
                # must read as a peer of Q1 anchors. Aligned to Q1 font size;
                # differentiation kept via weight (Q1 bold, middle regular),
                # not via font size.
                fontsize = 7.0 if is_q1 else (6.0 if grid == "Q4_low_information" else 7.0)
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
    ax.set_xlim(-0.06, 1.0)
    ax.set_xticks(np.linspace(0, 1, 6))
    ax.set_xticklabels([f"{int(x * 100)}%" for x in np.linspace(0, 1, 6)])
    ax.set_xlabel("Target composition")
    ax.set_title("Grid composition across primary contexts", loc="left")
    clean_axes(ax)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#F3F3F3", linewidth=0.24)
    if "bottom" in ax.spines:
        ax.spines["bottom"].set_bounds(0.0, 1.0)
    ax.text(
        0.0,
        1.62,
        "Pre-specified but empty: Q2 transcriptomic excess = 0, Q3 dependency excess = 0 in both contexts.",
        fontsize=5.8,
        color="#6A6A6A",
        va="center",
    )
    add_panel_label(ax, "e")


def render_panel_bridge_strength(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Panel (f): headline aligned Spearman bridge strength with Fisher 95% CI and
    an empirical permutation null envelope. The panel is intentionally minimal:
    two context dots, per-context CI, and a single null band. No bootstrap, no
    tiering, no per-target annotation."""
    order = ["HCC38", "HCC1143"]
    ordered = df.set_index("cell_line").reindex(order).reset_index()
    x = np.arange(len(ordered))
    rho = ordered["spearman_rho_aligned"].to_numpy()
    ci_lo = ordered["ci_lo_fisher95"].to_numpy()
    ci_hi = ordered["ci_hi_fisher95"].to_numpy()
    n_targets = ordered["n_targets"].to_numpy()
    null_lo = float(ordered["null_q025"].min())
    null_hi = float(ordered["null_q975"].max())
    null_iter = int(ordered["null_iterations"].max())
    ax.axhspan(null_lo, null_hi, color="#ECECEC", zorder=0)
    ax.axhline(0.0, color="#B0B0B0", linewidth=0.4, linestyle="--", zorder=0.5)
    ax.errorbar(
        x,
        rho,
        yerr=[rho - ci_lo, ci_hi - rho],
        fmt="none",
        ecolor="#4A4A4A",
        elinewidth=0.85,
        capsize=2.6,
        capthick=0.85,
        zorder=2,
    )
    ax.scatter(
        x,
        rho,
        s=30,
        c=GRID_COLORS["Q1_anchor"],
        edgecolor="white",
        linewidth=0.45,
        zorder=3,
    )
    for xi, rho_val, ni in zip(x, rho, n_targets):
        ax.text(
            xi + 0.13,
            rho_val + 0.005,
            f"{rho_val:.3f}",
            fontsize=5.6,
            color="#2B2B2B",
            va="bottom",
            ha="left",
            zorder=4,
        )
        ax.text(
            xi + 0.13,
            rho_val - 0.005,
            f"n={int(ni)}",
            fontsize=5.5,
            color="#6A6A6A",
            va="top",
            ha="left",
            zorder=4,
        )
    ax.text(
        0.50,
        -0.215,
        r"points = aligned Spearman $\rho$;  bars = Fisher z 95% CI",
        transform=ax.transAxes,
        fontsize=5.5,
        color="#6A6A6A",
        va="top",
        ha="center",
    )
    ax.text(
        0.50,
        -0.305,
        rf"gray band = null ($\rho=0$) 95% envelope, {null_iter} perm.",
        transform=ax.transAxes,
        fontsize=5.5,
        color="#8A8A8A",
        va="top",
        ha="center",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.set_xlim(-0.55, len(ordered) - 0.35)
    ax.set_ylim(-0.08, 1.0)
    ax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylabel(r"Aligned Spearman $\rho$")
    ax.set_title("Bridge strength", loc="left")
    clean_axes(ax)
    ax.grid(axis="y", color="#F3F3F3", linewidth=0.24)
    add_panel_label(ax, "f")


def render_panel_h(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Claim boundary", loc="left", pad=4)
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
    add_panel_label(ax, "h", x=-0.04)


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
            {"step": 1, "name": "perturbation truth"},
            {"step": 2, "name": "aligned CRISPR dependency"},
            {"step": 3, "name": "fixed target categories"},
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
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")
    fig = plt.figure(figsize=(11.0, 8.4))
    fig.patch.set_facecolor("white")
    mosaic = [
        ["a", "a", "a", "a", "a", "b", "b", "b", "b", "b"],
        ["a", "a", "a", "a", "a", "b", "b", "b", "b", "b"],
        ["c", "c", "c", "c", "c", "d", "d", "d", "d", "d"],
        ["c", "c", "c", "c", "c", "d", "d", "d", "d", "d"],
        ["e", "e", "e", "e", "e", ".", "f", "f", "f", "f"],
    ]
    axes = fig.subplot_mosaic(
        mosaic,
        gridspec_kw={"hspace": 0.88, "wspace": 0.55, "height_ratios": [0.62, 0.62, 1.0, 1.0, 1.04]},
    )
    for panel_id in ACTIVE_PANELS:
        render_panel_by_id(panel_id)(axes[panel_id], sources[panel_id])
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
        "e": (4.20, 2.70),
        "f": (2.30, 2.70),
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
