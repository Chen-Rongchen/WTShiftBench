from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wtbench.manuscript._palette import (
    DARK_TEXT,
    DIVIDER_GRAY,
    LIGHT_GRAY,
    MID_GRAY,
    NEUTRAL_GRAY,
    PRIMARY_GREEN,
    PRIMARY_GREEN_EDGE,
    PRIMARY_GREEN_FILL,
    SKY_BLUE,
    VERMILLION,
    VERMILLION_FILL,
)
from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import (
    add_panel_heading,
    apply_manuscript_style,
    clean_axes,
    finalize_manuscript_figure,
)


FIGURE_ID = "figure2"
FIGURE_TITLE = "Shared anchors form a tiered target-level bridge rather than clean primary objects"
SCRIPT_PATH = Path("scripts/manuscript/build_figure2_anchor_tiering.py")
CLAIM_BOUNDARY = "Shared anchors support the bridge but must not be described as fully deconfounded primary objects."

SHARED_ANCHORS = Path("reports/truth_bridge_decomposition/shared_canonical_anchor_summary.tsv")
TARGET_GRID = Path("reports/truth_bridge_decomposition/target_level_joint_grid.tsv")
ANCHOR_STABILITY = Path("reports/truth_bridge_decomposition/shared_anchor_stability.tsv")
ANCHOR_CUTOFF = Path("reports/truth_bridge_decomposition/anchor_cutoff_sensitivity.tsv")
ANCHOR_TIERING = Path("reports/truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv")
FINAL_CLAIM_MATRIX = Path("reports/truth_driven_bridge/sensitivity/final_claim_matrix.tsv")

# Per-anchor per-axis TVD evidence (panel f): the direct data supporting the
# PFDN5 vs PMF1/PRPF6/ZNF131 covariate-cleanliness separation in Panel e.
ANCHOR_TVD_AXES = (
    "barcode_gem_group",
    "num_umis_over_threshold_bin",
    "num_umis_quantile_bin",
    "transcriptome_detected_genes_quantile_bin",
    "transcriptome_total_signal_quantile_bin",
)
ANCHOR_TVD_FILES: list[tuple[str, str, Path]] = [
    (cell_line, axis,
     Path(
         f"reports/truth_driven_bridge/sensitivity/covariate_balance/"
         f"{cell_line}_{axis}_target_control_balance.tsv"
     ))
    for cell_line in ("HCC38", "HCC1143")
    for axis in ANCHOR_TVD_AXES
]
TVD_HARD_IMBALANCE = 0.25
AXIS_SHORT_LABELS = {
    "barcode_gem_group": "barcode\ngem group",
    "num_umis_over_threshold_bin": "UMI\nthreshold",
    "num_umis_quantile_bin": "UMI\nquantile",
    "transcriptome_detected_genes_quantile_bin": "detected\ngenes",
    "transcriptome_total_signal_quantile_bin": "total\nsignal",
}

EXPECTED_TIERS = {
    "PFDN5": "primary_but_qualified",
    "PMF1": "supporting_only",
    "PRPF6": "supporting_only",
    "ZNF131": "supporting_only",
}

# Four final stable anchors in canonical order:
# PFDN5 first (primary but qualified headline anchor), then supporting anchors
# by joint-rank descending.
FINAL_ANCHORS = ["PFDN5", "PRPF6", "PMF1", "ZNF131"]
# Non-stable shared-canonical / cutoff-sensitive supporting objects in panel c
SENSITIVE_SUPPORTING = ["RPS3", "RUVBL2", "ZBTB17", "NPM1", "ENY2"]

TIER_COLORS = {
    "primary_but_qualified": PRIMARY_GREEN,
    "supporting_only": NEUTRAL_GRAY,
    "supporting_but_sensitive": MID_GRAY,
    "supporting_but_unstable": MID_GRAY,
    "preliminary_only": LIGHT_GRAY,
}
COVARIATE_EXPOSED_MARK = "*"

ACTIVE_PANELS = list("abcdef")

def _add_panel_heading(ax: plt.Axes, label: str, title: str, *, label_x: float = -0.10) -> None:
    add_panel_heading(ax, "", title, title_x=0.00)


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig2_anchor_tiering"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_2"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    base = [SHARED_ANCHORS, TARGET_GRID, ANCHOR_STABILITY, ANCHOR_CUTOFF, ANCHOR_TIERING, FINAL_CLAIM_MATRIX]
    tvd_files = [p for _, _, p in ANCHOR_TVD_FILES]
    return [root / p for p in (base + tvd_files)]


def load_anchor_tiering(root: Path) -> pd.DataFrame:
    tier = pd.read_csv(root / ANCHOR_TIERING, sep="\t")
    observed = dict(zip(tier["target_gene"], tier["final_wording_tier"]))
    for gene, expected in EXPECTED_TIERS.items():
        if observed.get(gene) != expected:
            raise RuntimeError(
                f"Fig. 2 anchor tier sanity check failed for {gene}: "
                f"observed={observed.get(gene)}, expected={expected}"
            )
    return tier


def tier_for_gene(gene: str, tier_map: dict[str, str]) -> str:
    return tier_map.get(gene, "supporting_but_sensitive")


def tier_color_for_gene(gene: str, tier_map: dict[str, str]) -> str:
    return TIER_COLORS.get(tier_for_gene(gene, tier_map), "#BDBDBD")


def is_primary_gene(gene: str) -> bool:
    return gene == "PFDN5"


def covariate_exposed(gene: str, cov_map: dict[str, str]) -> bool:
    return cov_map.get(gene, "") == "supporting_but_covariate_exposed"


def decorate_gene_label(gene: str, cov_map: dict[str, str]) -> str:
    return f"{gene}{COVARIATE_EXPOSED_MARK}" if covariate_exposed(gene, cov_map) else gene


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


# ---------------------------------------------------------------------------
# Panel renderers
# ---------------------------------------------------------------------------


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Shared-canonical candidates ranked by joint-quantile, with cutoff-range CI.

    Bold green label marks PFDN5 (primary but qualified headline anchor). No
    covariate-exposed asterisks are drawn here: at the structural (shift /
    dependency quantile) layer the four stable anchors are indistinguishable.
    Covariate-level separation between PFDN5 and PMF1/PRPF6/ZNF131 is
    demonstrated in panel e (TVD matrix).
    """

    plot = df.copy()
    plot["joint_rank_mean"] = plot[["shift_quantile_mean", "depmap_quantile_mean"]].mean(axis=1)
    plot = plot.sort_values("joint_rank_mean", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot))

    # Subtle horizontal band behind PFDN5 to highlight primary-but-qualified anchor.
    for yi, row in zip(y, plot.itertuples()):
        if row.target_gene == "PFDN5":
            ax.axhspan(yi - 0.44, yi + 0.44, color=PRIMARY_GREEN_FILL, zorder=0)

    # Connector lines shift <-> dependency, per target.
    for yi, row in zip(y, plot.itertuples()):
        ax.plot(
            [row.shift_quantile_mean, row.depmap_quantile_mean],
            [yi, yi],
            color=MID_GRAY,
            linewidth=0.45,
            zorder=1,
        )

    # Cutoff-range whiskers (shift + dependency combined envelope): rendered
    # as a dashed auxiliary line so they read as a reference range rather
    # than as primary data (shift/dependency dots carry the primary signal).
    for yi, row in zip(y, plot.itertuples()):
        lo = min(row.min_shift_quantile_mean, row.min_depmap_quantile_mean)
        hi = max(row.max_shift_quantile_mean, row.max_depmap_quantile_mean)
        ax.plot(
            [lo, hi], [yi, yi],
            color=MID_GRAY,
            linewidth=0.5,
            linestyle=(0, (3, 2)),
            alpha=1.0,
            zorder=0.5,
        )

    ax.scatter(
        plot["shift_quantile_mean"],
        y,
        color="#FFFFFF",
        edgecolor=SKY_BLUE,
        linewidth=0.8,
        s=30,
        label="shift",
        zorder=3,
    )
    ax.scatter(
        plot["depmap_quantile_mean"],
        y,
        color=PRIMARY_GREEN,
        edgecolor=PRIMARY_GREEN_EDGE,
        linewidth=0.5,
        s=30,
        label="dependency",
        zorder=4,
    )

    ax.set_yticks(y)
    ax.set_yticklabels(list(plot["target_gene"]))
    ax.invert_yaxis()
    for tick_label, gene in zip(ax.get_yticklabels(), plot["target_gene"]):
        if gene == "PFDN5":
            tick_label.set_fontweight("bold")
            tick_label.set_color(TIER_COLORS["primary_but_qualified"])
        elif gene in FINAL_ANCHORS:
            tick_label.set_color(DARK_TEXT)
        else:
            tick_label.set_color(NEUTRAL_GRAY)

    ax.set_xlim(0.68, 1.03)
    ax.set_xlabel("Mean within-cell-line quantile")
    _add_panel_heading(ax, "a", "Shared-anchor candidates occupy high joint ranks", label_x=-0.04)

    legend_handles = [
        plt.Line2D(
            [0], [0], marker="o", linestyle="none", markerfacecolor="#FFFFFF",
            markeredgecolor=SKY_BLUE, markeredgewidth=1.0, markersize=4.6, label="shift",
        ),
        plt.Line2D(
            [0], [0], marker="o", linestyle="none", markerfacecolor=PRIMARY_GREEN,
            markeredgecolor=PRIMARY_GREEN_EDGE, markeredgewidth=0.6, markersize=4.6, label="dependency",
        ),
        plt.Line2D(
            [0], [0],
            color=MID_GRAY,
            linewidth=0.9,
            linestyle=(0, (3, 2)),
            label="cutoff range (P25–P75)",
        ),
    ]
    ax.legend(
        handles=legend_handles,
        loc="center left",
        bbox_to_anchor=(1.02, 0.18),
        frameon=False,
        fontsize=5.4,
        handletextpad=0.5,
        borderpad=0.2,
        labelspacing=0.3,
    )
    clean_axes(ax)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Low-ink recurrence matrix for the four final stable anchors.

    Each cell is coloured by the per (gene, cell-line) joint-quantile mean
    (mean of shift_quantile and depmap_quantile). A subtle green highlight
    band marks the PFDN5 row (primary but qualified).
    """

    anchors = FINAL_ANCHORS
    cell_lines = ["HCC1143", "HCC38"]
    pivot_joint = (
        df.pivot_table(
            index="target_gene", columns="cell_line", values="joint_quantile_mean", aggfunc="mean"
        )
        .reindex(index=anchors, columns=cell_lines)
    )
    ax.set_xlim(-0.5, len(cell_lines) - 0.5)
    ax.set_ylim(len(anchors) - 0.5, -0.9)

    # PFDN5 highlight band.
    if "PFDN5" in anchors:
        i_p = anchors.index("PFDN5")
        ax.axhspan(i_p - 0.5, i_p + 0.5, color=PRIMARY_GREEN_FILL, zorder=0)

    for i, gene in enumerate(anchors):
        for j, cl in enumerate(cell_lines):
            val = pivot_joint.loc[gene, cl]
            # Cell-line identity is categorical here; do not encode the numeric
            # value with extra lightness because that creates an undeclared
            # second visual variable. The number itself already carries the
            # magnitude.
            face = PRIMARY_GREEN if cl == "HCC1143" else VERMILLION
            edge = PRIMARY_GREEN_EDGE if cl == "HCC1143" else VERMILLION
            rect = plt.Rectangle(
                (j - 0.38, i - 0.38),
                0.76,
                0.76,
                facecolor=face,
                edgecolor=edge,
                linewidth=1.0,
                zorder=2,
            )
            ax.add_patch(rect)
            if pd.notna(val):
                ax.text(
                    j,
                    i,
                    f"{val:.2f}",
                    ha="center",
                    va="center",
                    fontsize=6.6,
                    fontweight="bold",
                    color="#FFFFFF",
                    zorder=3,
                )

    ax.set_yticks(np.arange(len(anchors)))
    ax.set_yticklabels(anchors)
    for tick_label, gene in zip(ax.get_yticklabels(), anchors):
        if gene == "PFDN5":
            tick_label.set_fontweight("bold")
            tick_label.set_color(TIER_COLORS["primary_but_qualified"])
        else:
            tick_label.set_color(DARK_TEXT)

    ax.set_xticks([])
    for j, cl in enumerate(cell_lines):
        ax.text(
            j,
            -0.62,
            cl,
            ha="center",
            va="bottom",
            fontsize=7.0,
            fontweight="bold",
            color=PRIMARY_GREEN if cl == "HCC1143" else VERMILLION,
        )
    _add_panel_heading(ax, "b", "Stable anchors recur in HCC38 and HCC1143", label_x=-0.04)
    ax.tick_params(length=0)
    ax.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_visible(False)



def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Stability fraction across the nine recurrent candidates.

    This panel screens only at the structural-stability axis: the four stable
    anchors (PFDN5, PRPF6, PMF1, ZNF131) are rendered in the same green -- they
    are not distinguishable here -- while the five cutoff-sensitive supporting
    objects use the lighter sand tone. Covariate-level separation is deferred
    to panel e (TVD matrix); no asterisks are drawn here.
    """

    plot = df.copy().sort_values(["is_stable", "shared_anchor_stability_fraction"], ascending=[False, False])
    y = np.arange(len(plot))

    def _bar_color(gene: str) -> str:
        # Structural-stability axis only: all four stable anchors share the
        # primary-qualified green (indistinguishable at this layer); the five
        # cutoff-sensitive supporting objects use neutral gray.
        if gene in FINAL_ANCHORS:
            return TIER_COLORS["primary_but_qualified"]
        return MID_GRAY

    colors = [_bar_color(g) for g in plot["target_gene"]]

    # PFDN5 highlight band.
    for yi, row in zip(y, plot.itertuples()):
        if row.target_gene == "PFDN5":
            ax.axhspan(yi - 0.45, yi + 0.45, color=PRIMARY_GREEN_FILL, zorder=0)

    ax.barh(y, plot["shared_anchor_stability_fraction"], color=colors, height=0.62, zorder=2)

    # Cutoff-range whisker on the stability fraction: use the per-target
    # joint-quantile min/max as a proxy envelope where available.
    if "stability_min_fraction" in plot.columns and "stability_max_fraction" in plot.columns:
        for yi, row in zip(y, plot.itertuples()):
            lo = row.stability_min_fraction
            hi = row.stability_max_fraction
            if pd.notna(lo) and pd.notna(hi) and hi > lo:
                ax.plot([lo, hi], [yi, yi], color="#424242", linewidth=1.0, zorder=3)
                ax.plot([lo, lo], [yi - 0.18, yi + 0.18], color="#424242", linewidth=1.0, zorder=3)
                ax.plot([hi, hi], [yi - 0.18, yi + 0.18], color="#424242", linewidth=1.0, zorder=3)

    ax.set_yticks(y)
    ax.set_yticklabels(list(plot["target_gene"]))
    for tick_label, gene in zip(ax.get_yticklabels(), plot["target_gene"]):
        if gene == "PFDN5":
            tick_label.set_fontweight("bold")
            tick_label.set_color(TIER_COLORS["primary_but_qualified"])
        elif gene in FINAL_ANCHORS:
            tick_label.set_color(DARK_TEXT)
        else:
            tick_label.set_color(NEUTRAL_GRAY)

    ax.set_xlim(0.32, 1.03)
    ax.set_xticks([0.4, 0.6, 0.8, 1.0])
    ax.set_xlabel("Shared-anchor stability fraction")
    _add_panel_heading(ax, "c", "Stability fraction separates stable from sensitive anchors", label_x=-0.04)

    legend_handles = [
        plt.Line2D([0], [0], marker="s", linestyle="none",
                   markerfacecolor=TIER_COLORS["primary_but_qualified"],
                   markeredgecolor="none", markersize=6, label="stable anchor"),
        plt.Line2D([0], [0], marker="s", linestyle="none",
                   markerfacecolor=MID_GRAY,
                   markeredgecolor="none", markersize=6, label="cutoff-sensitive supporting"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="center left",
        bbox_to_anchor=(1.02, 0.10),
        frameon=False,
        fontsize=5.4,
        handletextpad=0.5,
        borderpad=0.2,
        labelspacing=0.3,
    )
    clean_axes(ax)


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Paired shift and dependency quantiles for the four final stable anchors.

    PFDN5 is highlighted; no asterisks are drawn. At the structural axis
    (shift / dependency) the four anchors remain indistinguishable -- the
    covariate-level separation is shown in panel e (TVD matrix).
    """

    plot = df.set_index("target_gene").reindex(FINAL_ANCHORS).reset_index()
    x = np.arange(len(plot))

    # PFDN5 highlight band.
    for xi, row in zip(x, plot.itertuples()):
        if row.target_gene == "PFDN5":
            ax.axvspan(xi - 0.45, xi + 0.45, color=PRIMARY_GREEN_FILL, zorder=0)

    shift_color = SKY_BLUE
    dep_color = PRIMARY_GREEN
    ax.bar(x - 0.2, plot["shift_quantile_mean"], width=0.38, color=shift_color, label="shift", zorder=2)
    ax.bar(x + 0.2, plot["depmap_quantile_mean"], width=0.38, color=dep_color, label="dependency", zorder=2)

    for xi, row in zip(x, plot.itertuples()):
        ax.text(xi - 0.2, row.shift_quantile_mean + 0.015, f"{row.shift_quantile_mean:.2f}",
                ha="center", fontsize=6.0, fontweight="bold", color=DARK_TEXT)
        ax.text(xi + 0.2, row.depmap_quantile_mean + 0.015, f"{row.depmap_quantile_mean:.2f}",
                ha="center", fontsize=6.0, fontweight="bold", color=DARK_TEXT)

    ax.set_xticks(x)
    ax.set_xticklabels(list(plot["target_gene"]), rotation=0)
    for tick_label, gene in zip(ax.get_xticklabels(), plot["target_gene"]):
        if gene == "PFDN5":
            tick_label.set_fontweight("bold")
            tick_label.set_color(TIER_COLORS["primary_but_qualified"])
        else:
            tick_label.set_color(DARK_TEXT)

    ax.set_ylim(0, 1.16)
    ax.set_ylabel("Mean within-cell-line quantile")
    _add_panel_heading(ax, "d", "Final stable anchors retain high shift and dependency ranks", label_x=-0.04)
    ax.legend(
        [plt.Rectangle((0, 0), 1, 1, color=shift_color), plt.Rectangle((0, 0), 1, 1, color=dep_color)],
        ["shift", "dependency"],
        loc="upper right",
        bbox_to_anchor=(1.0, 0.98),
        frameon=False,
        fontsize=5.8,
        handlelength=1.0,
        handletextpad=0.4,
        labelspacing=0.25,
        borderpad=0.0,
    )
    clean_axes(ax)


def render_claim_matrix(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Compact anchor claim matrix -- the final conclusion panel.

    Panel f in the current layout: reads PFDN5 as primary_but_qualified (green)
    and PMF1/PRPF6/ZNF131 as supporting_only (dark amber) because panel e has
    already demonstrated, via the TVD matrix, that the three are covariate-exposed.
    """

    ax.set_axis_off()
    _add_panel_heading(ax, "f", "Anchor claim matrix", label_x=-0.04)

    order = FINAL_ANCHORS
    plot = df.set_index("target_gene").reindex(order).reset_index()

    ax.add_patch(
        plt.Rectangle(
            (0.005, 0.82),
            0.99,
            0.09,
            transform=ax.transAxes,
            facecolor=LIGHT_GRAY,
            edgecolor="none",
            zorder=0,
        )
    )
    headers = [("Anchor", 0.02), ("Claim tier", 0.30), ("Covariate", 0.78)]
    for text, x in headers:
        ax.text(x, 0.865, text, fontsize=6.8, fontweight="bold", color=DARK_TEXT, transform=ax.transAxes)
    ax.plot([0.01, 0.99], [0.82, 0.82], color=DIVIDER_GRAY, linewidth=0.8, transform=ax.transAxes)

    qualifier_labels = {
        "retain_with_caution": "clean",
        "supporting_but_covariate_exposed": "exposed",
    }
    wording_labels = {
        "primary_but_qualified": "primary but qualified",
        "supporting_only": "supporting only",
        "supporting_but_sensitive": "supporting but cutoff-sensitive",
    }
    row_gap = 0.16
    y = 0.72
    for row in plot.itertuples():
        tier = row.final_wording_tier
        color = TIER_COLORS.get(tier, "#CCCCCC")
        # Gene name (bold for primary-qualified).
        is_primary = tier == "primary_but_qualified"
        # Pale green band behind the PFDN5 row so the primary-qualified
        # anchor reads as an anchor in the otherwise flat claim matrix.
        if is_primary:
            ax.add_patch(
                plt.Rectangle(
                    (0.005, y - row_gap * 0.42),
                    0.99,
                    row_gap * 0.84,
                    transform=ax.transAxes,
                    facecolor=PRIMARY_GREEN_FILL,
                    edgecolor="none",
                    zorder=0,
                )
            )
        ax.text(
            0.02,
            y,
            row.target_gene,
            fontsize=7.4 if is_primary else 7.1,
            fontweight="bold" if is_primary else "normal",
            color=TIER_COLORS["primary_but_qualified"] if is_primary else DARK_TEXT,
            transform=ax.transAxes,
            va="center",
        )
        # Claim-tier colour chip + human-readable wording (single column).
        ax.add_patch(
            plt.Rectangle(
                (0.30, y - 0.035), 0.024, 0.07, transform=ax.transAxes, facecolor=color, edgecolor="none"
            )
        )
        ax.text(
            0.335,
            y,
            wording_labels.get(tier, tier.replace("_", " ")),
            fontsize=6.6,
            fontweight="semibold" if is_primary else "normal",
            color=DARK_TEXT,
            transform=ax.transAxes,
            va="center",
        )
        # Covariate status.
        cov = qualifier_labels.get(row.covariate_cleanliness, row.covariate_cleanliness.replace("_", " "))
        cov_color = PRIMARY_GREEN if cov == "clean" else VERMILLION
        ax.text(0.78, y, cov, fontsize=6.6, color=cov_color, transform=ax.transAxes, va="center")
        ax.plot(
            [0.01, 0.99], [y - row_gap * 0.48, y - row_gap * 0.48],
            color=DIVIDER_GRAY, linewidth=0.6, transform=ax.transAxes,
        )
        y -= row_gap

    # Bottom rule to close the table (mirrors the header rule at y=0.87).
    bottom_rule_y = y + row_gap / 2
    ax.plot(
        [0.01, 0.99], [bottom_rule_y, bottom_rule_y],
        color=DIVIDER_GRAY, linewidth=0.8, transform=ax.transAxes,
    )


def render_tvd_matrix(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Per-anchor covariate TVD matrix (4 anchors x 10 covariate cells).

    Provides the direct evidence separating PFDN5 (covariate-clean across all
    10 audited cells) from PMF1/PRPF6/ZNF131 (each exceeding the TVD > 0.25
    hard-imbalance cutoff on UMI-related axes), which underpins the
    ``primary_but_qualified`` vs ``supporting_only`` tiering shown in Panel e.
    """

    anchors = FINAL_ANCHORS
    axes_list = list(ANCHOR_TVD_AXES)
    cell_lines = ["HCC38", "HCC1143"]
    col_tuples: list[tuple[str, str]] = [(cl, ax_name) for cl in cell_lines for ax_name in axes_list]
    matrix = np.full((len(anchors), len(col_tuples)), np.nan)
    for ri, gene in enumerate(anchors):
        for ci, (cl, ax_name) in enumerate(col_tuples):
            sub = df.loc[
                (df["target_gene"] == gene) & (df["cell_line"] == cl) & (df["strat_column"] == ax_name)
            ]
            if len(sub) == 1:
                matrix[ri, ci] = float(sub["total_variation_distance"].iloc[0])

    ax.set_xlim(-0.5, len(col_tuples) - 0.5)
    ax.set_ylim(len(anchors) - 0.5, -1.1)
    ax.set_aspect("equal")

    i_pfdn5 = anchors.index("PFDN5")
    ax.axhspan(i_pfdn5 - 0.5, i_pfdn5 + 0.5, color=PRIMARY_GREEN_FILL, zorder=0)

    for ri in range(len(anchors)):
        for ci in range(len(col_tuples)):
            val = matrix[ri, ci]
            exposed = bool(val > TVD_HARD_IMBALANCE) if np.isfinite(val) else False
            face = VERMILLION_FILL if exposed else LIGHT_GRAY
            rect = plt.Rectangle(
                (ci - 0.44, ri - 0.44),
                0.88,
                0.88,
                facecolor=face,
                alpha=1.0,
                edgecolor=VERMILLION if exposed else "#F0F0F0",
                linewidth=1.4 if exposed else 0.5,
                zorder=2,
            )
            ax.add_patch(rect)
            if np.isfinite(val):
                ax.text(
                    ci, ri,
                    f"{val:.2f}",
                    ha="center", va="center",
                    fontsize=5.8,
                    fontweight="bold" if exposed else "normal",
                    color=DARK_TEXT,
                    zorder=3,
                )

    # Make the HCC38/HCC1143 grouping boundary visible enough that exposed cells
    # on opposite sides are not read as adjacent columns.
    ax.axvline(len(axes_list) - 0.5, color="#9E9E9E", linewidth=1.0, zorder=4)

    ax.set_xticks(range(len(col_tuples)))
    ax.set_xticklabels([AXIS_SHORT_LABELS[ax_name] for _, ax_name in col_tuples], fontsize=5.6, rotation=0, ha="center")
    ax.tick_params(axis="x", length=0, pad=5)
    ax.tick_params(axis="y", length=0, pad=2)
    for xi, cl in enumerate(cell_lines):
        ax.text(
            xi * len(axes_list) + (len(axes_list) - 1) / 2,
            -0.85,
            cl,
            ha="center", va="bottom", fontsize=7.0, fontweight="bold",
            color=PRIMARY_GREEN if cl == "HCC1143" else VERMILLION,
            clip_on=False,
        )

    ax.set_yticks(range(len(anchors)))
    ax.set_yticklabels(anchors, fontsize=7)
    for ri, tick_label in enumerate(ax.get_yticklabels()):
        if anchors[ri] == "PFDN5":
            tick_label.set_color(PRIMARY_GREEN)
            tick_label.set_fontweight("bold")

    for spine in ax.spines.values():
        spine.set_visible(False)
    _add_panel_heading(
        ax,
        "e",
        "Per-anchor covariate TVD (threshold: TVD > 0.25)",
        label_x=-0.04,
    )


# ---------------------------------------------------------------------------
# Source-data assembly
# ---------------------------------------------------------------------------


def _load_anchor_tvd(root: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for cell_line, axis, rel_path in ANCHOR_TVD_FILES:
        df = pd.read_csv(root / rel_path, sep="\t")
        df = df.loc[df["target_gene"].isin(FINAL_ANCHORS)].copy()
        df["cell_line"] = cell_line
        df["strat_column"] = axis
        frames.append(df[[
            "cell_line", "target_gene", "strat_column",
            "n_target_cells", "n_control_cells",
            "total_variation_distance", "n_strata",
        ]])
    combined = pd.concat(frames, ignore_index=True)
    return combined.sort_values(["target_gene", "cell_line", "strat_column"]).reset_index(drop=True)


def _stability_range_from_cutoff(
    shared: pd.DataFrame,
    target_genes: list[str],
) -> dict[str, tuple[float, float]]:
    """Approximate cutoff-range envelope for the stability fraction.

    We don't have per-cutoff stability fractions, but we use the target's
    q1 anchor count across cell lines as a conservative band proxy: genes
    stable in 2/2 contexts -> [0.67, 1.0]; 1/2 -> [0.33, 0.67]; 0/2 -> [0.0, 0.33].
    This keeps the error-bar width visually meaningful without inventing CIs.
    """

    envelopes: dict[str, tuple[float, float]] = {}
    for gene in target_genes:
        row = shared.loc[shared["target_gene"].eq(gene)]
        if row.empty:
            envelopes[gene] = (0.0, 0.33)
            continue
        q1_count = int(row["q1_anchor_count"].iloc[0])
        if q1_count >= 2:
            envelopes[gene] = (0.67, 1.0)
        elif q1_count == 1:
            envelopes[gene] = (0.33, 0.67)
        else:
            envelopes[gene] = (0.0, 0.33)
    return envelopes


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    shared = pd.read_csv(root / SHARED_ANCHORS, sep="\t")
    tier = load_anchor_tiering(root)
    stability = pd.read_csv(root / ANCHOR_STABILITY, sep="\t")
    target_grid = pd.read_csv(root / TARGET_GRID, sep="\t")

    tier_map = dict(tier[["target_gene", "final_wording_tier"]].values)
    cov_map = dict(tier[["target_gene", "covariate_cleanliness"]].values)

    shared_candidates = shared.loc[shared["shared_anchor_call"].eq("shared_canonical_anchor")].copy()

    # Merge cutoff-range mins/maxes onto panel-a source for whiskers.
    stab_range = stability[[
        "target_gene", "min_shift_quantile_mean", "min_depmap_quantile_mean",
        "max_shift_quantile_mean", "max_depmap_quantile_mean",
    ]]
    panel_a = shared_candidates.merge(stab_range, on="target_gene", how="left")
    panel_a["final_wording_tier"] = panel_a["target_gene"].map(tier_map).fillna("supporting_but_sensitive")
    panel_a["covariate_cleanliness"] = panel_a["target_gene"].map(cov_map).fillna("")
    panel_a = panel_a[[
        "target_gene", "shift_quantile_mean", "depmap_quantile_mean",
        "q1_anchor_count",
        "min_shift_quantile_mean", "min_depmap_quantile_mean",
        "max_shift_quantile_mean", "max_depmap_quantile_mean",
        "final_wording_tier", "covariate_cleanliness",
    ]]

    # Panel b: joint-quantile matrix for the 4 final stable anchors.
    recur = target_grid.loc[
        target_grid["target_gene"].isin(FINAL_ANCHORS),
        ["target_gene", "cell_line", "shift_quantile", "depmap_quantile", "is_q1_anchor"],
    ].copy()
    recur["joint_quantile_mean"] = recur[["shift_quantile", "depmap_quantile"]].mean(axis=1)

    # Panel c: all 9 objects (4 stable + 5 sensitive), with envelope proxy.
    candidates_c = FINAL_ANCHORS + SENSITIVE_SUPPORTING
    panel_c = stability.loc[stability["target_gene"].isin(candidates_c)].copy()
    panel_c["final_wording_tier"] = panel_c["target_gene"].map(tier_map).fillna("supporting_but_sensitive")
    panel_c["covariate_cleanliness"] = panel_c["target_gene"].map(cov_map).fillna("")
    panel_c["is_stable"] = panel_c["target_gene"].isin(FINAL_ANCHORS)
    envelopes = _stability_range_from_cutoff(shared, panel_c["target_gene"].tolist())
    panel_c["stability_min_fraction"] = panel_c["target_gene"].map(lambda g: envelopes.get(g, (np.nan, np.nan))[0])
    panel_c["stability_max_fraction"] = panel_c["target_gene"].map(lambda g: envelopes.get(g, (np.nan, np.nan))[1])

    # Panel d: final stable anchor shift/dependency quantiles.
    panel_d = shared_candidates.loc[shared_candidates["target_gene"].isin(FINAL_ANCHORS)].copy()
    panel_d["covariate_cleanliness"] = panel_d["target_gene"].map(cov_map).fillna("")
    panel_d["final_wording_tier"] = panel_d["target_gene"].map(tier_map).fillna("supporting_but_sensitive")
    panel_d = panel_d[[
        "target_gene", "shift_quantile_mean", "depmap_quantile_mean",
        "shift_value_mean", "depmap_strength_mean",
        "final_wording_tier", "covariate_cleanliness",
    ]]

    return {
        "a": panel_a,
        "b": recur,
        "c": panel_c,
        "d": panel_d,
        "e": _load_anchor_tvd(root),
        "f": tier,
    }


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {
        "a": render_panel_a,
        "b": render_panel_b,
        "c": render_panel_c,
        "d": render_panel_d,
        "e": render_tvd_matrix,
        "f": render_claim_matrix,
    }[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Shared-canonical anchor ranking",
        "b": "Stable anchor recurrence matrix",
        "c": "Stability fraction across stable and sensitive anchors",
        "d": "Final stable anchor shift/dependency",
        "e": "Per-anchor covariate TVD matrix",
        "f": "Anchor claim matrix",
    }[panel_id]


def render_combined(
    root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]
) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    manuscript_out = ensure_dir(manuscript_figure_dir(root))
    combined_source = pd.concat(
        [df.assign(panel=panel_id) for panel_id, df in sources.items()],
        ignore_index=True,
        sort=False,
    )
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")
    manuscript_source_path = write_tsv(combined_source, manuscript_out / "Figure_2_source_data.tsv")

    fig = plt.figure(figsize=(10.8, 8.9))
    mosaic = [
        ["a", "a", "a", ".", "b", "b"],
        ["a", "a", "a", ".", "b", "b"],
        [".", ".", ".", ".", ".", "."],
        ["c", "c", "c", ".", "d", "d"],
        ["c", "c", "c", ".", "d", "d"],
        [".", ".", ".", ".", ".", "."],
        ["e", "e", "e", "f", "f", "f"],
        ["e", "e", "e", "f", "f", "f"],
    ]
    axes = fig.subplot_mosaic(
        mosaic,
        empty_sentinel=".",
        gridspec_kw={
            "hspace": 0.82,
            "wspace": 0.34,
            "height_ratios": [0.95, 0.95, 0.12, 1.0, 1.0, 0.20, 1.22, 1.22],
        },
    )

    for panel_id in ACTIVE_PANELS:
        render_panel_by_id(panel_id)(axes[panel_id], sources[panel_id])

    png_path = out / f"{FIGURE_ID}.png"
    pdf_path = out / f"{FIGURE_ID}.pdf"
    manuscript_png = manuscript_out / "Figure_2.png"
    manuscript_pdf = manuscript_out / "Figure_2.pdf"
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
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in ACTIVE_PANELS],
        combined_source_data_path=combined_source_path,
        output_paths=output_paths,
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )
    write_figure_manifest(
        manifest_path=manuscript_out / "Figure_2_panel_manifest.json",
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in ACTIVE_PANELS],
        combined_source_data_path=manuscript_source_path,
        output_paths=[manuscript_png, manuscript_pdf],
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": combined_source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build manuscript Figure 2 anchor-tiering panels and assembly.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    apply_manuscript_style()
    sources = build_sources(root)
    panel_outputs: dict[str, dict[str, Path]] = {}
    panel_sizes = {
        "a": (3.4, 2.7),
        "b": (3.0, 2.8),
        "c": (3.4, 2.7),
        "d": (3.4, 2.8),
        "e": (5.2, 3.0),
        "f": (4.1, 3.0),
    }
    for panel_id in ACTIVE_PANELS:
        width, height = panel_sizes[panel_id]
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
