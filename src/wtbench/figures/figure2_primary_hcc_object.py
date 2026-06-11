from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

from wtbench.figures.figure_io import ensure_dir, repo_root, write_tsv
from wtbench.figures.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.figures.manuscript_style import COLORS, apply_manuscript_style, clean_axes, finalize_manuscript_figure, muted_diverging_cmap


FIGURE_ID = "figure2"
PUBLIC_FIGURE_ID = "Figure_2"
FIGURE_TITLE = "Primary HCC contexts establish the endpoint-aligned recovery object"
SCRIPT_PATH = Path("scripts/figures/build_figure2.py")
CLAIM_BOUNDARY = (
    "HCC38/HCC1143 define the primary endpoint-recovery object for model audit. "
    "Anchor and covariate summaries qualify claim wording and do not establish "
    "fully deconfounded target-level causal effects."
)

JOINT_GRID = Path("reports/truth_bridge_decomposition/target_level_joint_grid.tsv")
NULL_SUMMARY = Path("reports/manuscript_permutation_null_v1/bridge_rho_permutation_summary.tsv")
NULL_DISTRIBUTION = Path("reports/manuscript_permutation_null_v1/bridge_rho_permutation_distribution.tsv.gz")
BRIDGE_CI = Path("reports/manuscript_figures_v2/fig1_truth_object/panels/figure1_panelf_source_data.tsv")
HALLMARK_CONTRAST_GSEA = Path("reports/category_response_pathway/contrasts/category_response_contrast_gsea_hallmark.tsv")
HALLMARK_MEDIAN_SENSITIVITY = Path("reports/manuscript_figures_v2/fig5_sensitivity_controls/panels/figure5_response_program_robustness_median.tsv")
HALLMARK_LOO_SENSITIVITY = Path("reports/manuscript_figures_v2/fig5_sensitivity_controls/panels/figure5_response_program_robustness_loo.tsv")

CATEGORY_ORDER = ["Q1_anchor", "Q2_transcriptomic_excess", "Q3_dependency_excess", "Q4_low_information", "middle"]
CATEGORY_LABELS = {
    "Q1_anchor": "Endpoint anchors",
    "Q2_transcriptomic_excess": "Shift-excess",
    "Q3_dependency_excess": "Dependency-excess",
    "Q4_low_information": "Low-information",
    "middle": "Middle band",
}
CATEGORY_FILLS = {
    "Q1_anchor": "#e9f4f0",
    "Q2_transcriptomic_excess": "#eeeffb",
    "Q3_dependency_excess": "#fbefdd",
    "Q4_low_information": "#f0f0f0",
    "middle": "#f9f7ee",
}
CATEGORY_EDGES = {
    "Q1_anchor": "#3b827a",
    "Q2_transcriptomic_excess": "#73729f",
    "Q3_dependency_excess": "#9b5a30",
    "Q4_low_information": "#465261",
    "middle": "#BDBDBD",
}
CONTEXT_COLORS = {"HCC38": "#3b827a", "HCC1143": "#73729f"}
NULL_FILL = "#F0F0F0"
NULL_EDGE = "#BDBDBD"

GSEA_CONTRAST = "Q1_anchor_vs_middle"
GSEA_PATHWAYS = [
    "Myc Targets V1",
    "E2F Targets",
    "G2-M Checkpoint",
    "Mitotic Spindle",
    "mTORC1 Signaling",
    "Glycolysis",
    "p53 Pathway",
    "TNF-alpha Signaling via NF-kB",
]


def add_panel_title(ax: plt.Axes, title: str, *, x: float = 0.0, y: float = 1.055, fontsize: float = 8.6) -> None:
    for loc in ("left", "center", "right"):
        ax.set_title("", loc=loc)
    ax.text(
        x,
        y,
        title,
        transform=ax.transAxes,
        fontsize=fontsize,
        fontweight="bold",
        va="bottom",
        ha="left",
        color=COLORS["text"],
        clip_on=False,
    )


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig2_primary_hcc_object"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_2"


def manuscript_panel_dir(root: Path) -> Path:
    return manuscript_figure_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [
        root / JOINT_GRID,
        root / NULL_SUMMARY,
        root / NULL_DISTRIBUTION,
        root / BRIDGE_CI,
        root / HALLMARK_CONTRAST_GSEA,
        root / HALLMARK_MEDIAN_SENSITIVITY,
        root / HALLMARK_LOO_SENSITIVITY,
    ]


def load_grid(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / JOINT_GRID, sep="\t")
    df["category_label"] = df["joint_grid"].map(CATEGORY_LABELS).fillna(df["joint_grid"])
    return df


def scatter_source(root: Path, cell_line: str) -> pd.DataFrame:
    return load_grid(root).loc[lambda d: d["cell_line"].eq(cell_line)].copy()


def _format_p(value: float) -> str:
    p = float(value)
    return f"empirical P = {p:.3f}"


def render_scatter(ax: plt.Axes, df: pd.DataFrame, panel: str, title: str, stats: pd.Series | None = None) -> None:
    add_panel_title(ax, title)
    for cat in CATEGORY_ORDER:
        sub = df.loc[df["joint_grid"].eq(cat)]
        ax.scatter(
            sub["shift_quantile"] * 100,
            sub["depmap_quantile"] * 100,
            s=30,
            facecolor=CATEGORY_FILLS[cat],
            edgecolor=CATEGORY_EDGES[cat],
            linewidth=0.85,
            alpha=1.0,
            label=CATEGORY_LABELS[cat],
        )
    rho = df[["depmap_strength", "real_shift_mean_abs"]].corr(method="spearman").iloc[0, 1]
    ptxt = f"; {_format_p(stats['empirical_p_two_sided'])}" if stats is not None else ""
    ax.axvline(25, color="#BDBDBD", lw=0.8, ls="--")
    ax.axvline(75, color="#BDBDBD", lw=0.8, ls="--")
    ax.axhline(25, color="#BDBDBD", lw=0.8, ls="--")
    ax.axhline(75, color="#BDBDBD", lw=0.8, ls="--")
    ax.plot([0, 100], [0, 100], color="#CFCFCF", lw=0.8, ls=":", zorder=0)
    ax.text(0.04, 0.96, f"Spearman ρ = {rho:.3f}{ptxt}\nn={len(df)} targets", transform=ax.transAxes, va="top", fontsize=6.0, bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 1.4})
    ax.set_xlim(-2, 102)
    ax.set_ylim(-2, 102)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_xlabel("Observed transcriptomic shift percentile")
    ax.set_ylabel("CRISPR dependency-strength percentile")
    ax.grid(False)
    clean_axes(ax)


def bridge_strength_source(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / BRIDGE_CI, sep="\t")
    keep = df.loc[df["cell_line"].isin(["HCC38", "HCC1143"])].copy()
    return keep[[
        "cell_line",
        "truth_metric",
        "depmap_endpoint",
        "n_targets",
        "spearman_rho_aligned",
        "ci_lo_fisher95",
        "ci_hi_fisher95",
        "ci_method",
        "empirical_p_two_sided",
    ]]


def render_bridge_strength(ax: plt.Axes, df: pd.DataFrame, panel: str = "c", title: str = "Bridge strength") -> None:
    add_panel_title(ax, title)
    order = ["HCC38", "HCC1143"]
    d = df.set_index("cell_line").loc[order].reset_index()
    y = np.arange(len(d))[::-1]
    x = d["spearman_rho_aligned"].to_numpy()
    lo = d["ci_lo_fisher95"].to_numpy()
    hi = d["ci_hi_fisher95"].to_numpy()
    ax.errorbar(x, y, xerr=[x - lo, hi - x], fmt="o", color="#3b827a", ecolor="#8CBDB7", elinewidth=1.8, capsize=0, markersize=5.5)
    ax.axvline(0, color="#BBBBBB", lw=0.8, ls="--")
    for xi, yi, n in zip(x, y, d["n_targets"]):
        ax.text(xi + 0.035, yi, f"{xi:.3f}\nn={int(n)}", va="center", fontsize=5.8, color="#333333")
    ax.set_yticks(y)
    ax.set_yticklabels(d["cell_line"])
    ax.set_xlim(-0.05, 1.0)
    ax.set_xlabel("Aligned Spearman ρ")
    ax.grid(axis="x", color="#F0F0F0", lw=0.45)
    clean_axes(ax)


def category_source(root: Path) -> pd.DataFrame:
    df = load_grid(root)
    out = df.groupby(["cell_line", "joint_grid"], dropna=False).size().reset_index(name="n_targets")
    out["category_label"] = out["joint_grid"].map(CATEGORY_LABELS)
    out["fraction"] = out["n_targets"] / out.groupby("cell_line")["n_targets"].transform("sum")
    return out


def render_category(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_title(ax, "Endpoint-category composition")
    cell_lines = ["HCC38", "HCC1143"]
    left = np.zeros(len(cell_lines))
    for cat in CATEGORY_ORDER:
        vals = []
        for cell in cell_lines:
            row = df.loc[df["cell_line"].eq(cell) & df["joint_grid"].eq(cat)]
            vals.append(float(row["fraction"].iloc[0]) if not row.empty else 0.0)
        ax.barh(cell_lines, vals, left=left, color=CATEGORY_FILLS[cat], edgecolor=CATEGORY_EDGES[cat], linewidth=0.65, label=CATEGORY_LABELS[cat])
        left += np.array(vals)
    totals = df.groupby("cell_line")["n_targets"].sum().to_dict()
    for y, cell in enumerate(cell_lines):
        ax.text(1.01, y, f"n={int(totals[cell])}", va="center", fontsize=5.8, color="#444444")
    ax.set_xlim(0, 1.13)
    ax.set_xlabel("Fraction of matched targets")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.42), ncol=2, frameon=False, fontsize=5.2)
    ax.invert_yaxis()
    clean_axes(ax)


def gsea_source(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / HALLMARK_CONTRAST_GSEA, sep="\t")
    df = df.loc[
        df["context"].isin(["HCC38", "HCC1143"])
        & df["contrast_id"].eq(GSEA_CONTRAST)
        & df["pathway"].isin(GSEA_PATHWAYS)
    ].copy()
    q_col = "padj_within_context_contrast" if "padj_within_context_contrast" in df.columns else "padj"
    df["q_value"] = pd.to_numeric(df[q_col], errors="coerce")
    df["minus_log10_q"] = -np.log10(df["q_value"].clip(lower=1e-12))
    df["pathway"] = pd.Categorical(df["pathway"], categories=GSEA_PATHWAYS, ordered=True)
    return df.sort_values(["pathway", "context"]).reset_index(drop=True)


def _pathway_display_name(pathway: str) -> str:
    return (
        pathway.replace("Myc Targets V1", "MYC Targets V1")
        .replace("TNF-alpha Signaling via NF-kB", "TNF-alpha Signaling via NF-κB")
        .replace("Interferon Alpha Response", "Interferon alpha")
        .replace("Interferon Gamma Response", "Interferon gamma")
    )


def render_gsea(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_title(ax, "Endpoint-anchor response programs")
    clean_axes(ax)


def render_gsea_axis(ax: plt.Axes, df: pd.DataFrame, context: str, *, show_y: bool) -> None:
    add_panel_title(ax, context, y=1.03)
    pathways = list(reversed(GSEA_PATHWAYS))
    y_positions = {pathway: i for i, pathway in enumerate(pathways)}
    d = df.loc[df["context"].eq(context)]
    for _, row in d.iterrows():
        y = y_positions[str(row["pathway"])]
        size = 18 + min(78, float(row["minus_log10_q"]) * 12.5)
        ax.scatter(
            float(row["NES"]),
            y,
            s=size,
            facecolor=CONTEXT_COLORS[context],
            edgecolor="white",
            linewidth=0.55,
            alpha=0.88,
            zorder=3,
        )
    ax.axvline(0, color="#9A9A9A", lw=0.7, ls=(0, (2.2, 2.2)), zorder=1)
    ax.set_yticks(range(len(pathways)))
    ax.set_yticklabels([_pathway_display_name(p) for p in pathways] if show_y else [])
    ax.set_xlabel("Hallmark NES (anchors − middle)")
    ax.set_xlim(-2.15, 1.85)
    ax.grid(axis="x", color="#F1F1F1", lw=0.35)
    clean_axes(ax)
    ax.tick_params(axis="y", length=0)


def add_gsea_size_legend(fig: plt.Figure, ax: plt.Axes) -> None:
    values = [1, 2, 3]
    handles = [
        ax.scatter(
            [],
            [],
            s=18 + value * 12.5,
            facecolor="#8A8A8A",
            edgecolor="white",
            linewidth=0.55,
            alpha=0.75,
        )
        for value in values
    ]
    bbox = ax.get_position()
    leg = fig.legend(
        handles,
        [str(value) for value in values],
        title="−log10(FDR)",
        loc="center left",
        bbox_to_anchor=(bbox.x1 + 0.010, bbox.y0 + 0.30 * bbox.height),
        frameon=False,
        fontsize=5.3,
        title_fontsize=5.5,
        scatterpoints=1,
        handletextpad=0.5,
        borderaxespad=0.0,
        labelspacing=0.45,
    )


def render_gsea_facet(fig: plt.Figure, axes: list[plt.Axes], df: pd.DataFrame) -> None:
    axes[0].text(
        0.0,
        1.17,
        "Endpoint-anchor response programs",
        transform=axes[0].transAxes,
        fontsize=8.6,
        fontweight="bold",
        ha="left",
        va="bottom",
        color=COLORS["text"],
        clip_on=False,
    )
    render_gsea_axis(axes[0], df, "HCC38", show_y=True)
    render_gsea_axis(axes[1], df, "HCC1143", show_y=False)
    add_gsea_size_legend(fig, axes[1])


def response_program_sensitivity_source(root: Path) -> pd.DataFrame:
    contrast = pd.read_csv(root / HALLMARK_CONTRAST_GSEA, sep="\t")
    median = pd.read_csv(root / HALLMARK_MEDIAN_SENSITIVITY, sep="\t")
    loo = pd.read_csv(root / HALLMARK_LOO_SENSITIVITY, sep="\t")

    contrast = contrast.loc[
        contrast["context"].isin(["HCC38", "HCC1143"])
        & contrast["pathway"].isin(GSEA_PATHWAYS)
        & contrast["contrast_id"].eq("Q1_anchor_vs_middle")
    ].copy()
    contrast["sensitivity_layer"] = "anchor_vs_middle_direction"
    q_col = "padj_within_context_contrast" if "padj_within_context_contrast" in contrast.columns else "padj"
    contrast["FDR"] = pd.to_numeric(contrast[q_col], errors="coerce")
    contrast["minus_log10_FDR"] = -np.log10(contrast["FDR"].clip(lower=1e-12))
    contrast_out = contrast[["context", "pathway", "sensitivity_layer", "NES", "FDR", "minus_log10_FDR"]].rename(
        columns={"NES": "value"}
    )

    median = median.loc[median["context"].isin(["HCC38", "HCC1143"]) & median["pathway"].isin(GSEA_PATHWAYS)].copy()
    median["sensitivity_layer"] = "median_aggregation_agrees"
    median_out = median[["context", "pathway", "sensitivity_layer", "sign_agree", "mean_NES", "median_NES"]].copy()
    median_out["value"] = median_out["sign_agree"].astype(float)
    median_out["FDR"] = np.nan
    median_out["minus_log10_FDR"] = np.nan

    loo = loo.loc[loo["context"].isin(["HCC38", "HCC1143"]) & loo["pathway"].isin(GSEA_PATHWAYS)].copy()
    loo["sensitivity_layer"] = "leave_one_target_direction_retained"
    loo_out = loo[[
        "context",
        "pathway",
        "sensitivity_layer",
        "loo_sign_retained_fraction",
        "loo_fdr010_retained_fraction",
        "full_NES",
        "loo_NES_min",
        "loo_NES_max",
    ]].copy()
    loo_out["value"] = loo_out["loo_sign_retained_fraction"]
    loo_out["FDR"] = np.nan
    loo_out["minus_log10_FDR"] = np.nan

    out = pd.concat([contrast_out, median_out, loo_out], ignore_index=True, sort=False)
    out["pathway"] = pd.Categorical(out["pathway"], categories=GSEA_PATHWAYS, ordered=True)
    out["pathway_label"] = out["pathway"].astype(str).map(_pathway_display_name)
    return out.sort_values(["context", "pathway", "sensitivity_layer"]).reset_index(drop=True)


def render_response_program_sensitivity(ax: plt.Axes, df: pd.DataFrame, context: str, *, show_y: bool) -> None:
    title = "HCC38" if context == "HCC38" else "HCC1143"
    add_panel_title(ax, title, y=1.04, fontsize=7.2)
    layers = [
        ("anchor_vs_middle_direction", "anchors −\nmiddle"),
        ("median_aggregation_agrees", "median\ndirection"),
        ("leave_one_target_direction_retained", "LOO\nretention"),
    ]
    pathways = list(reversed(GSEA_PATHWAYS))
    y_positions = {pathway: i for i, pathway in enumerate(pathways)}
    cmap = muted_diverging_cmap("fig2f_muted_nes")
    norm = plt.Normalize(vmin=-2.2, vmax=1.8)
    for x, (layer, _) in enumerate(layers):
        sub = df.loc[df["context"].eq(context) & df["sensitivity_layer"].eq(layer)]
        for _, row in sub.iterrows():
            y = y_positions[str(row["pathway"])]
            if layer == "anchor_vs_middle_direction":
                value = float(row["value"])
                size = 22 + min(float(row.get("minus_log10_FDR", 0.0) or 0.0), 6.0) * 7.5
                ax.scatter(x, y, s=size, facecolor=cmap(norm(value)), edgecolor="#4D4D4D", linewidth=0.25, zorder=3)
            elif layer == "median_aggregation_agrees":
                face = "#3b827a" if float(row["value"]) >= 0.5 else "#D55E00"
                ax.scatter(x, y, s=26, marker="s", facecolor=face, edgecolor="white", linewidth=0.35, zorder=3)
            else:
                retained = float(row["value"])
                ax.plot([x - 0.25, x - 0.25 + retained * 0.50], [y, y], color="#3b827a", lw=1.7, solid_capstyle="round", zorder=3)
                ax.plot([x - 0.25 + retained * 0.50, x + 0.25], [y, y], color="#E4E4E4", lw=1.7, solid_capstyle="round", zorder=2)
    ax.set_xlim(-0.55, len(layers) - 0.45)
    ax.set_ylim(-0.55, len(pathways) - 0.45)
    ax.set_xticks(range(len(layers)))
    ax.set_xticklabels([label for _, label in layers], fontsize=5.3)
    ax.set_yticks(range(len(pathways)))
    ax.set_yticklabels([_pathway_display_name(p) for p in pathways] if show_y else [])
    ax.tick_params(length=0)
    ax.grid(False)
    clean_axes(ax)
    ax.tick_params(axis="y", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)


def render_response_program_sensitivity_facet(fig: plt.Figure, axes: list[plt.Axes], df: pd.DataFrame) -> None:
    axes[0].text(
        0.0,
        1.18,
        "Response-program sensitivity",
        transform=axes[0].transAxes,
        fontsize=8.6,
        fontweight="bold",
        ha="left",
        va="bottom",
        color=COLORS["text"],
        clip_on=False,
    )
    render_response_program_sensitivity(axes[0], df, "HCC38", show_y=True)
    render_response_program_sensitivity(axes[1], df, "HCC1143", show_y=False)
    bbox = axes[1].get_position()
    cax = fig.add_axes([bbox.x1 + 0.040, bbox.y0 + 0.25 * bbox.height, 0.012, 0.56 * bbox.height])
    cb = plt.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(vmin=-2.2, vmax=1.8), cmap=muted_diverging_cmap("fig2f_muted_nes_colorbar")), cax=cax)
    cb.set_label("NES", fontsize=5.4)
    cb.ax.tick_params(labelsize=5.0, length=1.8)
    size_ax = fig.add_axes([bbox.x1 + 0.105, bbox.y0 + 0.58 * bbox.height, 0.16, 0.30 * bbox.height], frame_on=False)
    size_ax.set_axis_off()
    size_ax.text(0.0, 0.98, "−log10(FDR)", fontsize=5.0, va="top")
    for i, value in enumerate([1, 2, 4]):
        y = 0.70 - i * 0.27
        size_ax.scatter(0.11, y, s=22 + value * 7.5, facecolor="#D4D4D4", edgecolor="#4D4D4D", linewidth=0.25)
        size_ax.text(0.28, y, str(value), fontsize=4.8, va="center")
    size_ax.set_xlim(0, 1)
    size_ax.set_ylim(0, 1)

    leg_ax = fig.add_axes([bbox.x1 + 0.105, bbox.y0 + 0.03 * bbox.height, 0.24, 0.42 * bbox.height], frame_on=False)
    leg_ax.set_axis_off()
    leg_ax.scatter(0.06, 0.82, s=24, marker="s", facecolor="#3b827a", edgecolor="white", linewidth=0.35)
    leg_ax.text(0.18, 0.82, "median agrees", fontsize=5.0, va="center")
    leg_ax.scatter(0.06, 0.62, s=24, marker="s", facecolor="#D55E00", edgecolor="white", linewidth=0.35)
    leg_ax.text(0.18, 0.62, "median differs", fontsize=5.0, va="center")
    leg_ax.plot([0.03, 0.20], [0.33, 0.33], color="#3b827a", lw=1.7, solid_capstyle="round")
    leg_ax.plot([0.20, 0.37], [0.33, 0.33], color="#E4E4E4", lw=1.7, solid_capstyle="round")
    leg_ax.text(0.42, 0.33, "LOO direction\nretention", fontsize=5.0, va="center")
    leg_ax.text(0.03, 0.16, "bar length = fraction retained", fontsize=4.7, va="center", color="#555555")
    leg_ax.set_xlim(0, 1)
    leg_ax.set_ylim(0, 1)


def null_source(root: Path) -> pd.DataFrame:
    return pd.read_csv(root / NULL_SUMMARY, sep="\t")


def null_distribution_source(root: Path) -> pd.DataFrame:
    return pd.read_csv(root / NULL_DISTRIBUTION, sep="\t")


def render_null_calibrated_bridge(ax: plt.Axes, source: pd.DataFrame) -> None:
    add_panel_title(ax, "Null-calibrated bridge strength")
    order = ["HCC38", "HCC1143"]
    bins = np.linspace(-0.48, 0.48, 42)
    for idx, cell in enumerate(order):
        y0 = len(order) - 1 - idx
        vals = source.loc[source["cell_line"].eq(cell) & source["source_type"].eq("endpoint_label_permutation"), "spearman_rho"].dropna().to_numpy()
        hist, edges = np.histogram(vals, bins=bins, density=True)
        hist = hist / hist.max() * 0.32
        centers = (edges[:-1] + edges[1:]) / 2
        ax.fill_between(centers, y0, y0 + hist, color=NULL_FILL, alpha=1.0, linewidth=0)
        ax.plot(centers, y0 + hist, color=NULL_EDGE, lw=0.7)
        row = source.loc[source["cell_line"].eq(cell) & source["source_type"].eq("observed")].iloc[0]
        observed = float(row["spearman_rho"])
        ci_lo = float(row["ci_lo_fisher95"])
        ci_hi = float(row["ci_hi_fisher95"])
        ax.plot([ci_lo, ci_hi], [y0 + 0.12, y0 + 0.12], color=CONTEXT_COLORS[cell], lw=1.8, solid_capstyle="round")
        ax.scatter([observed], [y0 + 0.12], color=CONTEXT_COLORS[cell], edgecolor="white", linewidth=0.5, s=32, zorder=5)
        ptxt = _format_p(row["empirical_p_two_sided"])
        ax.text(observed + 0.018, y0 + 0.31, f"Spearman ρ = {observed:.3f}\n{ptxt}", fontsize=5.8, color=CONTEXT_COLORS[cell], va="bottom")
    ax.axvline(0, color="#BBBBBB", lw=0.8, ls="--")
    handles = [
        Patch(facecolor=NULL_FILL, edgecolor=NULL_EDGE, label="Endpoint-label null"),
        Line2D([0], [0], color="#3b827a", marker="o", markersize=4.2, lw=1.4, markerfacecolor="#3b827a", markeredgecolor="white", label="Observed ρ ± 95% CI"),
    ]
    ax.legend(handles=handles, loc="upper right", bbox_to_anchor=(1.0, -0.18), ncol=2, frameon=False, fontsize=5.4, handlelength=1.8, columnspacing=1.2)
    ax.set_yticks([1, 0])
    ax.set_yticklabels(order)
    ax.set_ylim(-0.12, 1.45)
    ax.set_xlim(-0.48, 0.90)
    ax.set_xlabel("Aligned Spearman ρ")
    ax.grid(axis="x", color="#F0F0F0", lw=0.45)
    clean_axes(ax)


def null_calibrated_bridge_source(root: Path) -> pd.DataFrame:
    bridge = bridge_strength_source(root)
    observed = bridge.rename(
        columns={
            "spearman_rho_aligned": "spearman_rho",
            "n_targets": "n_targets",
        }
    ).copy()
    observed["source_type"] = "observed"
    observed["permutation_id"] = pd.NA
    observed = observed[[
        "cell_line",
        "source_type",
        "permutation_id",
        "n_targets",
        "spearman_rho",
        "ci_lo_fisher95",
        "ci_hi_fisher95",
        "ci_method",
        "empirical_p_two_sided",
    ]]

    dist = null_distribution_source(root).copy()
    if "permutation_id" not in dist.columns:
        dist["permutation_id"] = np.arange(len(dist))
    dist = dist.rename(columns={"null_rho": "spearman_rho"})
    dist["source_type"] = "endpoint_label_permutation"
    dist["n_targets"] = pd.NA
    dist["ci_lo_fisher95"] = pd.NA
    dist["ci_hi_fisher95"] = pd.NA
    dist["ci_method"] = pd.NA
    dist["empirical_p_two_sided"] = pd.NA
    dist = dist[observed.columns].dropna(axis=1, how="all")
    return pd.concat([observed, dist], ignore_index=True, sort=False)


def _save_panel(root: Path, pid: str, title: str, fig: plt.Figure, source: pd.DataFrame) -> dict[str, Path]:
    stem = f"{FIGURE_ID}_panel{pid}"
    public_stem = f"{PUBLIC_FIGURE_ID}_panel_{pid}"
    src = write_tsv(source, panel_dir(root) / f"{stem}_source_data.tsv")
    public_src = write_tsv(source, manuscript_panel_dir(root) / f"{public_stem}_source_data.tsv")
    png = panel_dir(root) / f"{stem}.png"
    pdf = panel_dir(root) / f"{stem}.pdf"
    svg = panel_dir(root) / f"{stem}.svg"
    public_png = manuscript_panel_dir(root) / f"{public_stem}.png"
    public_pdf = manuscript_panel_dir(root) / f"{public_stem}.pdf"
    public_svg = manuscript_panel_dir(root) / f"{public_stem}.svg"
    finalize_manuscript_figure(fig, font_scale=0.95)
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
    write_panel_manifest(manifest_path=manifest, repo_root=root, panel_id=f"{FIGURE_ID}{pid}", panel_title=title, script_path=root / SCRIPT_PATH, input_paths=input_paths(root), source_data_path=src, output_paths=[png, pdf, svg], claim_boundary=CLAIM_BOUNDARY)
    write_panel_manifest(manifest_path=manuscript_panel_dir(root) / f"{public_stem}_manifest.json", repo_root=root, panel_id=f"{PUBLIC_FIGURE_ID}{pid}", panel_title=title, script_path=root / SCRIPT_PATH, input_paths=input_paths(root), source_data_path=public_src, output_paths=[public_png, public_pdf, public_svg], claim_boundary=CLAIM_BOUNDARY)
    return {"source": src, "png": png, "pdf": pdf, "svg": svg, "manifest": manifest}


def render_primary_endpoint_planes(fig: plt.Figure, axes: list[plt.Axes], root: Path) -> pd.DataFrame:
    null_summary = null_source(root)
    hcc38 = scatter_source(root, "HCC38")
    hcc1143 = scatter_source(root, "HCC1143")
    axes[0].text(
        0.0,
        1.18,
        "Primary endpoint planes",
        transform=axes[0].transAxes,
        fontsize=8.6,
        fontweight="bold",
        ha="left",
        va="bottom",
        color=COLORS["text"],
        clip_on=False,
    )
    render_scatter(
        axes[0],
        hcc38,
        "a",
        "HCC38 endpoint plane",
        null_summary.loc[null_summary["cell_line"].eq("HCC38")].iloc[0],
    )
    render_scatter(
        axes[1],
        hcc1143,
        "a",
        "HCC1143 endpoint plane",
        null_summary.loc[null_summary["cell_line"].eq("HCC1143")].iloc[0],
    )
    return pd.concat([hcc38, hcc1143], ignore_index=True)


def build_panels(root: Path) -> dict[str, dict[str, Path]]:
    null_summary = null_source(root)
    sources = {
        "a": pd.concat([scatter_source(root, "HCC38"), scatter_source(root, "HCC1143")], ignore_index=True),
        "b": null_calibrated_bridge_source(root),
        "c": category_source(root),
        "d": gsea_source(root),
        "e": response_program_sensitivity_source(root),
    }
    outputs = {}
    for pid, src in sources.items():
        if pid == "a":
            fig = plt.figure(figsize=(7.8, 3.55))
            gs = fig.add_gridspec(1, 2, left=0.08, right=0.99, top=0.80, bottom=0.18, wspace=0.24)
            render_primary_endpoint_planes(fig, [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])], root)
            outputs[pid] = _save_panel(root, pid, "Primary endpoint planes", fig, src)
            continue
        if pid == "d":
            fig = plt.figure(figsize=(5.8, 3.2))
            gs = fig.add_gridspec(1, 3, left=0.20, right=0.98, top=0.77, bottom=0.19, wspace=0.13, width_ratios=[1, 1, 0.16])
            axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])]
            render_gsea_facet(fig, axes, src)
            outputs[pid] = _save_panel(root, pid, "Endpoint-anchor response programs", fig, src)
            continue
        if pid == "e":
            fig = plt.figure(figsize=(8.8, 3.35))
            gs = fig.add_gridspec(1, 2, left=0.145, right=0.66, top=0.76, bottom=0.23, wspace=0.18)
            axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])]
            render_response_program_sensitivity_facet(fig, axes, src)
            outputs[pid] = _save_panel(root, pid, "Response-program sensitivity", fig, src)
            continue
        fig, ax = plt.subplots(figsize={"b": (5.0, 2.7), "c": (4.0, 2.7)}[pid])
        renderers = {
            "b": render_null_calibrated_bridge,
            "c": render_category,
        }
        renderers[pid](ax, src)
        outputs[pid] = _save_panel(root, pid, {"b": "Null-calibrated bridge strength", "c": "Endpoint-category composition"}[pid], fig, src)
    return outputs


def build_combined(root: Path, panels: dict[str, dict[str, Path]]) -> None:
    sources = {
        "a": pd.concat([scatter_source(root, "HCC38"), scatter_source(root, "HCC1143")], ignore_index=True),
        "b": null_calibrated_bridge_source(root),
        "c": category_source(root),
        "d": gsea_source(root),
        "e": response_program_sensitivity_source(root),
    }
    combined = pd.concat([df.assign(panel=pid) for pid, df in sources.items()], ignore_index=True, sort=False)
    src = write_tsv(combined, output_dir(root) / f"{FIGURE_ID}_source_data.tsv")
    public_src = write_tsv(combined, manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}_source_data.tsv")
    fig = plt.figure(figsize=(10.1, 9.25))
    gs = fig.add_gridspec(4, 4, left=0.06, right=0.98, top=0.96, bottom=0.08, wspace=0.55, hspace=0.66, width_ratios=[1, 1, 1.05, 0.95], height_ratios=[1.0, 0.82, 0.92, 0.78])
    sub_a = gs[0, :].subgridspec(1, 2, wspace=0.22)
    render_primary_endpoint_planes(fig, [fig.add_subplot(sub_a[0, 0]), fig.add_subplot(sub_a[0, 1])], root)
    render_null_calibrated_bridge(fig.add_subplot(gs[1, 0:2]), sources["b"])
    render_category(fig.add_subplot(gs[1, 2:4]), sources["c"])
    sub_d = gs[2, :].subgridspec(1, 3, wspace=0.12, width_ratios=[1, 1, 0.13])
    axes_d = [fig.add_subplot(sub_d[0, 0]), fig.add_subplot(sub_d[0, 1])]
    render_gsea_facet(fig, axes_d, sources["d"])
    sub_e = gs[3, :].subgridspec(1, 3, wspace=0.13, width_ratios=[1, 1, 0.18])
    axes_e = [fig.add_subplot(sub_e[0, 0]), fig.add_subplot(sub_e[0, 1])]
    render_response_program_sensitivity_facet(fig, axes_e, sources["e"])
    finalize_manuscript_figure(fig, font_scale=0.95)
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
    write_figure_manifest(manifest_path=output_dir(root) / f"{FIGURE_ID}_panel_manifest.json", repo_root=root, figure_id=FIGURE_ID, figure_title=FIGURE_TITLE, script_path=root / SCRIPT_PATH, panel_manifest_paths=[panels[p]["manifest"] for p in ["a", "b", "c", "d", "e"]], combined_source_data_path=src, output_paths=[png, pdf, svg], input_paths=input_paths(root), claim_boundary=CLAIM_BOUNDARY)
    write_figure_manifest(manifest_path=manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}_panel_manifest.json", repo_root=root, figure_id=PUBLIC_FIGURE_ID, figure_title=FIGURE_TITLE, script_path=root / SCRIPT_PATH, panel_manifest_paths=[manuscript_panel_dir(root) / f"{PUBLIC_FIGURE_ID}_panel_{p}_manifest.json" for p in ["a", "b", "c", "d", "e"]], combined_source_data_path=public_src, output_paths=[public_png, public_pdf, public_svg], input_paths=input_paths(root), claim_boundary=CLAIM_BOUNDARY)


def copy_to_figure_build(root: Path) -> None:
    src = output_dir(root)
    dst = ensure_dir(root / "figure_build/output/Figure_2")
    pdst = ensure_dir(dst / "panels")
    for ext in [".png", ".pdf", ".svg", "_source_data.tsv"]:
        s = src / f"{FIGURE_ID}{ext}"
        if s.exists():
            shutil.copy2(s, dst / f"{PUBLIC_FIGURE_ID}{ext}")
    for panel in ["a", "b", "c", "d", "e"]:
        for ext in [".png", ".pdf", ".svg", "_source_data.tsv"]:
            s = src / "panels" / f"{FIGURE_ID}_panel{panel}{ext}"
            if s.exists():
                shutil.copy2(s, pdst / f"{PUBLIC_FIGURE_ID}_panel_{panel}{ext}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build Figure 2 primary HCC endpoint object.")
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
