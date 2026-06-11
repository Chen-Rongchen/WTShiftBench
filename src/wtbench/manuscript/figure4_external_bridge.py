from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from wtbench.manuscript.figure_io import ensure_dir, repo_root, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import (
    COLORS,
    apply_manuscript_style,
    clean_axes,
    finalize_manuscript_figure,
)


FIGURE_ID = "figure4"
PUBLIC_FIGURE_ID = "Figure_4"
FIGURE_TITLE = "External perturbation datasets delimit bridge-form detectability"
SCRIPT_PATH = Path("scripts/manuscript/build_figure4_sweep_controls.py")
CLAIM_BOUNDARY = (
    "External perturbation datasets test whether the observed transcriptomic "
    "shift-DepMap bridge form can be re-detected beyond the primary HCC model-audit "
    "contexts and where it attenuates across temporal and target-universe "
    "boundaries. They are not model-generalization tests."
)

BRIDGE = Path("reports/external_bridge_form_robustness/observed_shift_depmap_bridge_summary.tsv")
GSE264667_GRID = Path("benchmark/registry/gse264667_endpoint_category_grid.tsv")

ORDERED_CONTEXTS = [
    "HCC38 day 14",
    "HCC1143 day 14",
    "HepG2 day 7",
    "Jurkat day 7",
    "K562 TF day 7",
    "K562 TF day 13",
    "K562 essential CRISPRi day 6",
    "K562 genome-scale CRISPRi day 8",
]

DISPLAY_CONTEXT = {
    "HCC38 day 14": "HCC38 day 14",
    "HCC1143 day 14": "HCC1143 day 14",
    "HepG2 day 7": "HepG2 day 7",
    "Jurkat day 7": "Jurkat day 7",
    "K562 TF day 7": "K562 TF day 7",
    "K562 TF day 13": "K562 TF day 13",
    "K562 essential CRISPRi day 6": "K562 essential CRISPRi day 6",
    "K562 genome-scale CRISPRi day 8": "K562 GWPS CRISPRi day 8",
}

ROLE_LABEL = {
    "HCC38 day 14": "Primary reference",
    "HCC1143 day 14": "Primary reference",
    "HepG2 day 7": "Secondary endpoint extension",
    "Jurkat day 7": "Secondary endpoint extension",
    "K562 TF day 7": "Temporal boundary",
    "K562 TF day 13": "Temporal boundary",
    "K562 essential CRISPRi day 6": "Scale/target-universe boundary",
    "K562 genome-scale CRISPRi day 8": "Scale/target-universe boundary",
}

ROLE_COLORS = {
    "Primary reference": "#3B827A",
    "Secondary endpoint extension": "#76A99F",
    "Temporal boundary": "#73729F",
    "Scale/target-universe boundary": "#9B5A30",
}

ROLE_DISPLAY_LABELS = {
    "Primary reference": "Primary reference",
    "Secondary endpoint extension": "Secondary endpoint extension",
    "Temporal boundary": "Temporal boundary",
    "Scale/target-universe boundary": "Scale / target-universe\nboundary",
}

CATEGORY_ORDER = ["Q1_anchor", "shift_excess", "dependency_excess", "low_information", "middle"]
CATEGORY_LABELS = {
    "Q1_anchor": "Endpoint anchors",
    "shift_excess": "Shift-excess",
    "dependency_excess": "Dependency-excess",
    "low_information": "Low-information",
    "middle": "Middle band",
}
CATEGORY_FILL = {
    "Q1_anchor": "#E9F4F0",
    "shift_excess": "#EEEFFB",
    "dependency_excess": "#FBEFDD",
    "low_information": "#F0F0F0",
    "middle": "#F9F7EE",
}
CATEGORY_EDGE = {
    "Q1_anchor": "#3B827A",
    "shift_excess": "#73729F",
    "dependency_excess": "#9B5A30",
    "low_information": "#465261",
    "middle": "#BDBDBD",
}


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig4_external_bridge"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_4"


def manuscript_panel_dir(root: Path) -> Path:
    return manuscript_figure_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / BRIDGE, root / GSE264667_GRID]


def add_panel_title(ax: plt.Axes, title: str, *, y: float = 1.08, x: float = 0.0) -> None:
    for loc in ("left", "center", "right"):
        ax.set_title("", loc=loc)
    ax.text(
        x,
        y,
        title,
        transform=ax.transAxes,
        fontsize=8.0,
        fontweight="bold",
        ha="left",
        va="bottom",
        color=COLORS["text"],
        clip_on=False,
    )


def format_p(value: float) -> str:
    if value <= 0.0015:
        return "0.001"
    return f"{value:.3f}"


def normalize_category(value: str) -> str:
    mapping = {
        "Q1_anchor": "Q1_anchor",
        "Endpoint anchors": "Q1_anchor",
        "Q2_shift_excess": "shift_excess",
        "shift_excess": "shift_excess",
        "Shift-excess": "shift_excess",
        "Q3_dependency_excess": "dependency_excess",
        "dependency_excess": "dependency_excess",
        "Dependency-excess": "dependency_excess",
        "Q4_low_information": "low_information",
        "low_information": "low_information",
        "Low-information": "low_information",
        "middle": "middle",
        "Middle band": "middle",
    }
    return mapping.get(str(value), "middle")


def load_bridge(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / BRIDGE, sep="\t")
    df = df.loc[df["context"].isin(ORDERED_CONTEXTS)].copy()
    df["context"] = pd.Categorical(df["context"], categories=ORDERED_CONTEXTS, ordered=True)
    df["display_context"] = df["context"].astype(str).map(DISPLAY_CONTEXT)
    df["evidence_role"] = df["context"].astype(str).map(ROLE_LABEL)
    return df.sort_values("context").reset_index(drop=True)


def load_secondary_grid(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / GSE264667_GRID, sep="\t")
    df = df.loc[df["context"].isin(["HepG2 day 7", "Jurkat day 7"])].copy()
    df["category_key"] = df["endpoint_category"].map(normalize_category)
    df["shift_percentile"] = 100.0 * df["shift_quantile"].astype(float)
    df["dependency_percentile"] = 100.0 * df["dependency_quantile"].astype(float)
    return df


def bridge_by_context(df: pd.DataFrame, context: str) -> pd.Series:
    rows = df.loc[df["context"].astype(str).eq(context)]
    if rows.empty:
        raise ValueError(f"Missing bridge summary for {context}")
    return rows.iloc[0]


def panel_a_source(root: Path) -> pd.DataFrame:
    return load_bridge(root)


def panel_b_source(root: Path) -> pd.DataFrame:
    return load_secondary_grid(root)


def panel_c_source(root: Path) -> pd.DataFrame:
    bridge = load_bridge(root)
    pairs = [
        ("Temporal boundary", "K562 TF day 7", "K562 TF day 13"),
        (
            "Scale/target-universe boundary",
            "K562 essential CRISPRi day 6",
            "K562 genome-scale CRISPRi day 8",
        ),
    ]
    records = []
    for boundary, start, end in pairs:
        start_row = bridge_by_context(bridge, start)
        end_row = bridge_by_context(bridge, end)
        records.extend(
            [
                {
                    "boundary": boundary,
                    "contrast_step": "start",
                    "context": start,
                    "display_context": DISPLAY_CONTEXT[start],
                    "spearman_rho": start_row["spearman_rho"],
                    "spearman_bootstrap_ci_low": start_row["spearman_bootstrap_ci_low"],
                    "spearman_bootstrap_ci_high": start_row["spearman_bootstrap_ci_high"],
                    "n_targets_matched_depmap": start_row["n_targets_matched_depmap"],
                    "delta_rho_to_next": end_row["spearman_rho"] - start_row["spearman_rho"],
                },
                {
                    "boundary": boundary,
                    "contrast_step": "end",
                    "context": end,
                    "display_context": DISPLAY_CONTEXT[end],
                    "spearman_rho": end_row["spearman_rho"],
                    "spearman_bootstrap_ci_low": end_row["spearman_bootstrap_ci_low"],
                    "spearman_bootstrap_ci_high": end_row["spearman_bootstrap_ci_high"],
                    "n_targets_matched_depmap": end_row["n_targets_matched_depmap"],
                    "delta_rho_to_next": np.nan,
                },
            ]
        )
    return pd.DataFrame(records)


def render_forest(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_title(ax, "Bridge detectability across perturbation contexts", y=1.05)
    y = np.arange(len(df))[::-1]

    primary = df.loc[df["evidence_role"].eq("Primary reference")]
    ax.axvspan(
        primary["spearman_rho"].min(),
        primary["spearman_rho"].max(),
        color="#D8D8D8",
        alpha=0.15,
        zorder=0,
    )
    ax.text(
        primary["spearman_rho"].mean(),
        y.max() + 0.58,
        "primary reference range",
        ha="center",
        va="bottom",
        fontsize=5.6,
        color="#666666",
    )

    last_role = None
    for i, row in df.iterrows():
        yi = y[i]
        role = row["evidence_role"]
        color = ROLE_COLORS[role]
        if last_role is not None and role != last_role:
            ax.axhline(yi + 0.5, color="#E7E7E7", lw=0.65, zorder=0)
        if role != last_role:
            ax.text(
                0.015,
                yi + 0.46,
                ROLE_DISPLAY_LABELS[role],
                transform=ax.get_yaxis_transform(),
                ha="left",
                va="bottom",
                fontsize=5.25,
                fontweight="bold",
                color="#555555",
                linespacing=0.95,
            )
        last_role = role
        ax.plot(
            [row["spearman_bootstrap_ci_low"], row["spearman_bootstrap_ci_high"]],
            [yi, yi],
            color=color,
            lw=1.45,
            solid_capstyle="round",
            zorder=2,
        )
        ax.scatter(
            row["spearman_rho"],
            yi,
            s=58,
            facecolor="white",
            edgecolor=color,
            linewidth=1.15,
            zorder=3,
        )
        ax.text(
            1.05,
            yi,
            f"n={int(row['n_targets_matched_depmap'])}",
            ha="right",
            va="center",
            fontsize=5.8,
            color="#555555",
        )

    ax.axvline(0, color="#8A8A8A", lw=0.7, ls=(0, (2.2, 2.2)), zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels(df["display_context"].astype(str))
    ax.set_xlim(-0.24, 1.10)
    ax.set_ylim(-0.75, len(df) - 0.25)
    ax.set_xlabel("Aligned Spearman ρ")
    ax.grid(axis="x", color="#F1F1F1", lw=0.35)
    clean_axes(ax)


def render_secondary_plane_axes(axes: list[plt.Axes], grid: pd.DataFrame, bridge: pd.DataFrame) -> list[plt.Axes]:
    for ax, context, anchor in zip(axes, ["HepG2 day 7", "Jurkat day 7"], ["E", "W"], strict=True):
        rows = grid.loc[grid["context"].eq(context)].copy()
        for cat in CATEGORY_ORDER:
            cat_rows = rows.loc[rows["category_key"].eq(cat)]
            if cat_rows.empty:
                continue
            alpha = 0.22 if cat == "middle" else 0.92
            size = 10 if cat == "middle" else 12
            ax.scatter(
                cat_rows["shift_percentile"],
                cat_rows["dependency_percentile"],
                s=size,
                facecolor=CATEGORY_FILL[cat],
                edgecolor=CATEGORY_EDGE[cat],
                linewidth=0.42,
                alpha=alpha,
                label=CATEGORY_LABELS[cat],
            )
        for cutoff in (25, 75):
            ax.axhline(cutoff, color="#BDBDBD", lw=0.55, ls=(0, (3, 2)), zorder=0)
            ax.axvline(cutoff, color="#BDBDBD", lw=0.55, ls=(0, (3, 2)), zorder=0)
        ax.plot([0, 100], [0, 100], color="#C8C8C8", lw=0.55, ls=(0, (1, 2.2)), zorder=0)
        stat = bridge_by_context(bridge, context)
        ax.set_title(context, fontsize=6.2, fontweight="bold", pad=10)
        ax.text(
            0.5,
            1.020,
            f"Spearman $\\rho$ = {stat['spearman_rho']:.3f}; "
            f"empirical P = {format_p(float(stat['spearman_permutation_pvalue']))}",
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=4.6,
            fontweight="normal",
            color="#333333",
            clip_on=False,
        )
        ax.set_aspect("equal", adjustable="box")
        ax.set_anchor(anchor)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.grid(False)
        clean_axes(ax)
    axes[0].set_ylabel("CRISPR dependency-strength percentile")
    axes[1].tick_params(axis="y", labelleft=False)
    return axes


def render_secondary_planes(fig: plt.Figure, subgs, grid: pd.DataFrame, bridge: pd.DataFrame) -> list[plt.Axes]:
    axes = [fig.add_subplot(subgs[0, 0]), fig.add_subplot(subgs[0, 1])]
    return render_secondary_plane_axes(axes, grid, bridge)


def add_category_legend(ax: plt.Axes, *, anchor: tuple[float, float] = (1.0, -0.22)) -> None:
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markersize=4,
            markerfacecolor=CATEGORY_FILL[cat],
            markeredgecolor=CATEGORY_EDGE[cat],
            markeredgewidth=0.7,
            label=CATEGORY_LABELS[cat],
        )
        for cat in CATEGORY_ORDER
    ]
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=anchor,
        ncol=5,
        frameon=False,
        fontsize=5.6,
        handletextpad=0.35,
        columnspacing=0.75,
    )


def add_category_legend_to_figure(fig: plt.Figure, *, anchor: tuple[float, float]) -> None:
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markersize=4,
            markerfacecolor=CATEGORY_FILL[cat],
            markeredgecolor=CATEGORY_EDGE[cat],
            markeredgewidth=0.7,
            label=CATEGORY_LABELS[cat],
        )
        for cat in CATEGORY_ORDER
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=anchor,
        ncol=5,
        frameon=False,
        fontsize=5.6,
        handletextpad=0.35,
        columnspacing=0.75,
    )


def render_attenuation(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_title(ax, "Boundary attenuation contrasts", y=1.05)
    y_positions = {"Temporal boundary": 1.0, "Scale/target-universe boundary": 0.0}
    labels = {
        "Temporal boundary": "day 7 \u2192 day 13",
        "Scale/target-universe boundary": "essential \u2192 genome-wide",
    }
    for boundary, rows in df.groupby("boundary", sort=False):
        color = ROLE_COLORS[boundary]
        rows = rows.sort_values("contrast_step", key=lambda s: s.map({"start": 0, "end": 1}))
        y = y_positions[boundary]
        start_row = rows.loc[rows["contrast_step"].eq("start")].iloc[0]
        end_row = rows.loc[rows["contrast_step"].eq("end")].iloc[0]
        start_x = float(start_row["spearman_rho"])
        end_x = float(end_row["spearman_rho"])
        ax.annotate(
            "",
            xy=(end_x, y),
            xytext=(start_x, y),
            arrowprops={
                "arrowstyle": "-|>",
                "color": color,
                "lw": 1.25,
                "shrinkA": 5,
                "shrinkB": 5,
                "mutation_scale": 8,
            },
            zorder=2,
        )
        for row in [start_row, end_row]:
            x = float(row["spearman_rho"])
            ax.scatter(x, y, s=48, facecolor="white", edgecolor=color, linewidth=1.15, zorder=3)
        ax.text(
            (start_x + end_x) / 2,
            y + 0.13,
            labels[boundary],
            ha="center",
            va="bottom",
            fontsize=5.8,
            color="#555555",
        )
        delta = float(start_row["delta_rho_to_next"])
        ax.text(
            (start_x + end_x) / 2,
            y - 0.17,
            f"Δρ = {delta:.3f}",
            ha="center",
            va="top",
            fontsize=6.0,
            color="#555555",
        )
    ax.axvline(0, color="#8A8A8A", lw=0.7, ls=(0, (2.2, 2.2)), zorder=1)
    ax.set_yticks([1.0, 0.0])
    ax.set_yticklabels(["Temporal\nboundary", "Scale/target-\nuniverse\nboundary"])
    ax.set_xlim(-0.20, 1.00)
    ax.set_ylim(-0.42, 1.38)
    ax.set_xlabel("Aligned Spearman ρ")
    ax.grid(axis="x", color="#F1F1F1", lw=0.35)
    clean_axes(ax)


def _save_panel(root: Path, pid: str, title: str, fig: plt.Figure, source: pd.DataFrame) -> dict[str, Path]:
    stem = f"{FIGURE_ID}_panel{pid}"
    public_stem = f"{PUBLIC_FIGURE_ID}_panel_{pid}"
    source_path = write_tsv(source, panel_dir(root) / f"{stem}_source_data.tsv")
    public_source = write_tsv(source, manuscript_panel_dir(root) / f"{public_stem}_source_data.tsv")
    png = panel_dir(root) / f"{stem}.png"
    pdf = panel_dir(root) / f"{stem}.pdf"
    svg = panel_dir(root) / f"{stem}.svg"
    public_png = manuscript_panel_dir(root) / f"{public_stem}.png"
    public_pdf = manuscript_panel_dir(root) / f"{public_stem}.pdf"
    public_svg = manuscript_panel_dir(root) / f"{public_stem}.svg"
    finalize_manuscript_figure(fig, font_scale=0.94)
    for path in [png, pdf, svg, public_png, public_pdf, public_svg]:
        ensure_dir(path.parent)
    fig.savefig(png, dpi=1200, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    fig.savefig(public_png, dpi=1200, bbox_inches="tight")
    fig.savefig(public_pdf, bbox_inches="tight")
    fig.savefig(public_svg, bbox_inches="tight")
    plt.close(fig)
    manifest = panel_dir(root) / f"{stem}_manifest.json"
    write_panel_manifest(
        manifest_path=manifest,
        repo_root=root,
        panel_id=f"{FIGURE_ID}{pid}",
        panel_title=title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=source_path,
        output_paths=[png, pdf, svg],
        claim_boundary=CLAIM_BOUNDARY,
    )
    write_panel_manifest(
        manifest_path=manuscript_panel_dir(root) / f"{public_stem}_manifest.json",
        repo_root=root,
        panel_id=f"{PUBLIC_FIGURE_ID}{pid}",
        panel_title=title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=public_source,
        output_paths=[public_png, public_pdf, public_svg],
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": png, "pdf": pdf, "svg": svg, "manifest": manifest}


def build_panels(root: Path) -> dict[str, dict[str, Path]]:
    bridge = panel_a_source(root)
    grid = panel_b_source(root)
    attenuation = panel_c_source(root)
    outputs: dict[str, dict[str, Path]] = {}

    fig, ax = plt.subplots(figsize=(5.7, 3.4))
    render_forest(ax, bridge)
    outputs["a"] = _save_panel(root, "a", "Bridge detectability across perturbation contexts", fig, bridge)

    fig = plt.figure(figsize=(6.4, 3.0))
    gs = fig.add_gridspec(1, 2, left=0.09, right=0.98, top=0.70, bottom=0.30, wspace=0.04)
    title_ax = fig.add_axes([0.09, 0.83, 0.89, 0.08], frameon=False)
    title_ax.set_axis_off()
    title_ax.text(0, 0.0, "Secondary endpoint-extension planes", fontsize=8.0, fontweight="bold", ha="left", va="bottom")
    axes = render_secondary_planes(fig, gs, grid, bridge)
    fig.text(0.535, 0.235, "Observed transcriptomic shift percentile", ha="center", va="center", fontsize=7.0)
    add_category_legend(axes[-1], anchor=(0.0, -0.28))
    outputs["b"] = _save_panel(root, "b", "Secondary endpoint-extension planes", fig, grid)

    fig, ax = plt.subplots(figsize=(4.7, 3.0))
    render_attenuation(ax, attenuation)
    outputs["c"] = _save_panel(root, "c", "Boundary attenuation contrasts", fig, attenuation)
    return outputs


def build_combined(root: Path, panels: dict[str, dict[str, Path]]) -> None:
    bridge = panel_a_source(root)
    grid = panel_b_source(root)
    attenuation = panel_c_source(root)
    combined = pd.concat(
        [
            bridge.assign(panel="a"),
            grid.assign(panel="b"),
            attenuation.assign(panel="c"),
        ],
        ignore_index=True,
        sort=False,
    )
    source = write_tsv(combined, output_dir(root) / f"{FIGURE_ID}_source_data.tsv")
    public_source = write_tsv(combined, manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}_source_data.tsv")

    fig = plt.figure(figsize=(10.8, 6.25))
    gs = fig.add_gridspec(
        2,
        2,
        left=0.07,
        right=0.985,
        top=0.90,
        bottom=0.16,
        width_ratios=[1.05, 1.12],
        height_ratios=[1.03, 1.0],
        hspace=0.46,
        wspace=0.18,
    )
    ax_a = fig.add_subplot(gs[:, 0])
    render_forest(ax_a, bridge)

    sub_b = gs[0, 1].subgridspec(2, 2, height_ratios=[0.32, 1.0], hspace=0.18, wspace=0.28)
    title_ax = fig.add_subplot(sub_b[0, :])
    title_ax.set_axis_off()
    title_ax.text(
        0.0,
        0.35,
        "Secondary endpoint-extension planes",
        fontsize=8.0,
        fontweight="bold",
        ha="left",
        va="bottom",
    )
    axes_b = [fig.add_subplot(sub_b[1, 0]), fig.add_subplot(sub_b[1, 1])]
    render_secondary_plane_axes(axes_b, grid, bridge)
    bbox_l = axes_b[0].get_position()
    bbox_r = axes_b[1].get_position()
    fig.text(
        (bbox_l.x0 + bbox_r.x1) / 2,
        min(bbox_l.y0, bbox_r.y0) - 0.050,
        "Observed transcriptomic shift percentile",
        ha="center",
        va="center",
        fontsize=7.0,
    )
    add_category_legend_to_figure(fig, anchor=(0.75, 0.045))

    ax_c = fig.add_subplot(gs[1, 1])
    render_attenuation(ax_c, attenuation)

    finalize_manuscript_figure(fig, font_scale=0.94)
    png = output_dir(root) / f"{FIGURE_ID}.png"
    pdf = output_dir(root) / f"{FIGURE_ID}.pdf"
    svg = output_dir(root) / f"{FIGURE_ID}.svg"
    public_png = manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}.png"
    public_pdf = manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}.pdf"
    public_svg = manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}.svg"
    for path in [png, pdf, svg, public_png, public_pdf, public_svg]:
        ensure_dir(path.parent)
    fig.savefig(png, dpi=1200, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    fig.savefig(public_png, dpi=1200, bbox_inches="tight")
    fig.savefig(public_pdf, bbox_inches="tight")
    fig.savefig(public_svg, bbox_inches="tight")
    plt.close(fig)
    write_figure_manifest(
        manifest_path=output_dir(root) / f"{FIGURE_ID}_panel_manifest.json",
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panels[p]["manifest"] for p in ["a", "b", "c"]],
        combined_source_data_path=source,
        output_paths=[png, pdf, svg],
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )
    write_figure_manifest(
        manifest_path=manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}_panel_manifest.json",
        repo_root=root,
        figure_id=PUBLIC_FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[manuscript_panel_dir(root) / f"{PUBLIC_FIGURE_ID}_panel_{p}_manifest.json" for p in ["a", "b", "c"]],
        combined_source_data_path=public_source,
        output_paths=[public_png, public_pdf, public_svg],
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )


def copy_to_figure_build(root: Path) -> None:
    src = output_dir(root)
    dst = ensure_dir(root / "figure_build/output/Figure_4")
    pdst = ensure_dir(dst / "panels")
    for ext in [".png", ".pdf", ".svg", "_source_data.tsv"]:
        s = src / f"{FIGURE_ID}{ext}"
        if s.exists():
            shutil.copy2(s, dst / f"{PUBLIC_FIGURE_ID}{ext}")
    for panel in ["a", "b", "c"]:
        for ext in [".png", ".pdf", ".svg", "_source_data.tsv"]:
            s = src / "panels" / f"{FIGURE_ID}_panel{panel}{ext}"
            if s.exists():
                shutil.copy2(s, pdst / f"{PUBLIC_FIGURE_ID}_panel_{panel}{ext}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build Figure 4 external bridge-form boundary figure.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    apply_manuscript_style()
    ensure_dir(output_dir(root))
    ensure_dir(panel_dir(root))
    ensure_dir(manuscript_figure_dir(root))
    ensure_dir(manuscript_panel_dir(root))
    panels = build_panels(root)
    if not args.panels_only:
        build_combined(root, panels)
        copy_to_figure_build(root)


if __name__ == "__main__":
    main()
