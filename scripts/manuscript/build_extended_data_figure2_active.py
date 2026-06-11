from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "figures/Extended_Data_Figure_2"
BUILD = ROOT / "figure_build/output/Extended_Data_Figure_2"
MANUSCRIPT = ROOT / "manuscript/figures/Extended_Data_Figure_2"

GREEN = "#009E73"
GREEN_DARK = "#2F7F73"
GREEN_LIGHT = "#B8D8D1"
CORAL = "#E58D7C"
BLUE = "#4C78A8"
ORANGE = "#D55E00"
GRAY = "#8F8F8F"
LIGHT_GRAY = "#E8E8E8"
TEXT = "#303030"

METRIC_LABELS = {
    "real_shift_mean_abs": "Mean absolute shift",
    "real_shift_L2": "L2 shift",
    "real_shift_top20_mean": "Top-20 mean",
    "real_shift_top50_mean": "Top-50 mean",
    "real_shift_top100_mean": "Top-100 mean",
    "real_Edistance": "E-distance",
    "real_DEG_burden": "DEG burden",
}


def clean(ax: plt.Axes, *, grid_axis: str | None = None) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=7)
    if grid_axis:
        ax.grid(axis=grid_axis, color="#F0F0F0", linewidth=0.45, zorder=0)
    else:
        ax.grid(False)


def title(ax: plt.Axes, value: str) -> None:
    ax.set_title(value, loc="left", fontsize=9, fontweight="bold", pad=9)


def save_panel(letter: str, fig: plt.Figure, source: pd.DataFrame) -> None:
    for base in (PUBLIC, BUILD, MANUSCRIPT):
        panel_dir = base / "panels"
        panel_dir.mkdir(parents=True, exist_ok=True)
        stem = panel_dir / f"Extended_Data_Figure_2_panel_{letter}"
        fig.savefig(stem.with_suffix(".png"), dpi=600, bbox_inches="tight")
        fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
        fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
        source.to_csv(f"{stem}_source_data.tsv", sep="\t", index=False)
    plt.close(fig)


def panel_a(source: pd.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.1), sharey=True)
    colors = {
        "real_shift_mean_abs": GREEN,
        "real_shift_L2": CORAL,
        "real_DEG_burden": BLUE,
    }
    ranking_order = [
        ("control_expression", "Genes ranked by control expression"),
        ("perturbation_response", "Genes ranked by perturbation response"),
    ]
    for ax, (ranking, subtitle) in zip(axes, ranking_order):
        d = source.loc[source["ranking"].eq(ranking)].dropna(subset=["aligned_spearman"]).copy()
        d["n_genes"] = pd.to_numeric(d["n_genes"], errors="coerce")
        for metric, color in colors.items():
            g = d.loc[d["truth_metric"].eq(metric)]
            summary = g.groupby("n_genes")["aligned_spearman"].agg(["mean", "min", "max"]).reset_index()
            ax.fill_between(summary["n_genes"], summary["min"], summary["max"], color=color, alpha=0.12)
            ax.plot(summary["n_genes"], summary["mean"], marker="o", ms=4, lw=1.2, color=color, label=METRIC_LABELS[metric])
        ax.set_xscale("log")
        ax.set_xticks([100, 500, 1000, 2000, d["n_genes"].max()])
        ax.set_xticklabels(["100", "500", "1k", "2k", "all"])
        ax.set_xlabel("Gene subset size")
        ax.set_title(subtitle, fontsize=7.5, pad=5)
        clean(ax, grid_axis="y")
    axes[0].set_ylabel("Aligned Spearman ρ")
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.015),
        ncol=3,
        frameon=False,
        fontsize=6.2,
        handletextpad=0.5,
        columnspacing=1.2,
    )
    fig.suptitle("Alternative shift-metric sensitivity", x=0.07, ha="left", fontsize=9, fontweight="bold")
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.26, top=0.78, wspace=0.18)
    return fig


def panel_b(source: pd.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.5), sharex=True, sharey=True)
    d = source.dropna(subset=["spearman_rho_aligned"]).copy()
    rows = list(METRIC_LABELS)
    endpoint_styles = [
        ("depmap_gene_dependency", "CRISPR dependency", "o", -0.08),
        ("depmap_gene_effect", "CRISPR gene effect", "s", 0.08),
    ]
    for ax, context, color in zip(axes, ["HCC38", "HCC1143"], [GREEN_DARK, CORAL]):
        context_data = d.loc[d.cell_line.eq(context)]
        y = np.arange(len(rows))
        for endpoint, label, marker, offset in endpoint_styles:
            values = (
                context_data.loc[context_data.depmap_endpoint.eq(endpoint)]
                .set_index("truth_metric")
                .reindex(rows)["spearman_rho_aligned"]
            )
            ax.scatter(
                values,
                y + offset,
                marker=marker,
                s=32,
                color=color,
                edgecolor="white",
                linewidth=0.45,
                label=label,
                zorder=3,
            )
        for yi, metric in enumerate(rows):
            pair = context_data.loc[
                context_data.truth_metric.eq(metric), "spearman_rho_aligned"
            ].dropna()
            if len(pair) == 2:
                ax.hlines(yi, pair.min(), pair.max(), color=color, lw=1.0, alpha=0.45)
        ax.set_title(context, fontsize=8)
        ax.set_xlabel("Aligned Spearman ρ")
        clean(ax, grid_axis="x")
    axes[0].set_yticks(np.arange(len(rows)), [METRIC_LABELS[x] for x in rows])
    axes[0].set_ylim(len(rows) - 0.5, -0.5)
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.015),
        ncol=2,
        frameon=False,
        fontsize=6.0,
        handletextpad=0.5,
        columnspacing=1.4,
    )
    fig.suptitle(
        "CRISPR endpoint-form and shift-metric sensitivity",
        x=0.08,
        ha="left",
        fontsize=9,
        fontweight="bold",
    )
    fig.subplots_adjust(left=0.23, right=0.98, bottom=0.26, top=0.78, wspace=0.10)
    return fig


def panel_c(source: pd.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.5), sharex=True, sharey=True)
    rows = list(METRIC_LABELS)
    for ax, context, color in zip(axes, ["HCC38", "HCC1143"], [GREEN_DARK, CORAL]):
        d = source.loc[source.cell_line.eq(context)].set_index("truth_metric").reindex(rows).reset_index()
        y = np.arange(len(d))
        ax.hlines(y, d.spearman_aligned_q025, d.spearman_aligned_q975, color=color, lw=1.4)
        ax.scatter(d.spearman_aligned_mean, y, color=color, s=28, edgecolor="white", linewidth=0.4, zorder=3)
        ax.set_title(context, fontsize=8)
        ax.set_xlabel("Aligned Spearman ρ")
        clean(ax, grid_axis="x")
    axes[0].set_yticks(np.arange(len(rows)), [METRIC_LABELS[x] for x in rows])
    axes[0].set_ylim(len(rows) - 0.5, -0.5)
    fig.suptitle("Control-subsampling robustness", x=0.08, ha="left", fontsize=9, fontweight="bold")
    fig.subplots_adjust(left=0.23, right=0.98, bottom=0.17, top=0.78, wspace=0.10)
    return fig


def panel_d(source: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    order = ["none", "PFDN5", "PRPF6", "PMF1", "ZNF131", "all_four_anchors", "jackknife_min", "jackknife_mean", "jackknife_max"]
    labels = ["None", "PFDN5", "PRPF6", "PMF1", "ZNF131", "All four anchors", "Jackknife minimum", "Jackknife mean", "Jackknife maximum"]
    y = np.arange(len(order))
    for context, offset, color, marker in [("HCC38", -0.10, GREEN_DARK, "o"), ("HCC1143", 0.10, CORAL, "s")]:
        d = source.loc[source.context.eq(context)].set_index("removed").reindex(order)
        ax.scatter(d.spearman_rho, y + offset, color=color, marker=marker, s=28, label=context, zorder=3)
        baseline = float(d.loc["none", "spearman_rho"])
        ax.axvline(baseline, color=color, lw=0.7, alpha=0.24)
    ax.set_yticks(y, labels)
    ax.set_ylim(len(order) - 0.5, -0.5)
    ax.set_xlabel("Spearman ρ after target removal")
    ax.legend(
        frameon=False,
        fontsize=6.5,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.25),
        ncol=2,
        handletextpad=0.5,
        columnspacing=1.3,
    )
    title(ax, "Anchor-influence jackknife")
    clean(ax, grid_axis="x")
    fig.subplots_adjust(left=0.30, right=0.97, bottom=0.28, top=0.82)
    return fig


def panel_e(source: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(5.8, 3.4))
    anchor_labels = {"Q1_anchor", "endpoint_anchor", "Endpoint anchors"}
    d = source.loc[source.joint_grid.isin(anchor_labels)].copy()
    for context, color, marker in [("HCC38", GREEN_DARK, "o"), ("HCC1143", CORAL, "s")]:
        g = d.loc[d.cell_line.eq(context)].sort_values("quantile_high")
        ax.plot(g.quantile_high, g.fraction_targets, marker=marker, ms=5, lw=1.2, color=color, label=context)
    ax.axvline(0.75, color="#A8A8A8", lw=0.8, ls=(0, (3, 2)))
    ax.set_xlabel("High-percentile cutoff")
    ax.set_ylabel("Fraction endpoint anchors")
    ax.set_xticks([0.67, 0.75, 0.80])
    ax.legend(
        frameon=False,
        fontsize=6.5,
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        ncol=1,
        handletextpad=0.5,
    )
    title(ax, "Endpoint-anchor cutoff sensitivity")
    clean(ax, grid_axis="y")
    fig.subplots_adjust(left=0.16, right=0.76, bottom=0.20, top=0.82)
    return fig


def covariate_label(value: str) -> str:
    return {
        "barcode_gem_group": "GEM group",
        "num_umis_over_threshold_bin": "UMIs above threshold",
        "num_umis_quantile_bin": "UMI quantile",
        "transcriptome_detected_genes_quantile_bin": "Detected-gene quantile",
        "transcriptome_total_signal_quantile_bin": "Transcriptome-signal quantile",
    }.get(value, value.replace("_", " "))


def panel_f(source: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6.1, 3.7))
    d = source.copy()
    d["label"] = d.apply(lambda r: f"{r.cell_line} · {covariate_label(r.strat_column)}", axis=1)
    d = d.sort_values("mean_tvd")
    colors = np.where(d.n_targets_tvd_gt_0_25 > 0, ORANGE, GRAY) if "n_targets_tvd_gt_0_25" in d else np.where(d["n_targets_tvd_gt_0.25"] > 0, ORANGE, GRAY)
    y = np.arange(len(d))
    ax.hlines(y, 0, d.mean_tvd, color=colors, lw=2.2, alpha=0.75)
    ax.scatter(d.mean_tvd, y, color=colors, s=30, zorder=3)
    ax.set_yticks(y, d.label)
    ax.set_xlabel("Mean target–control TVD")
    ax.legend(
        handles=[
            Line2D([0], [0], marker="o", color=ORANGE, lw=1.6, label="At least one target with TVD > 0.25"),
            Line2D([0], [0], marker="o", color=GRAY, lw=1.6, label="No target with TVD > 0.25"),
        ],
        frameon=False,
        fontsize=6.2,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.24),
        ncol=2,
        handletextpad=0.5,
        columnspacing=1.2,
    )
    title(ax, "Covariate TVD audit")
    clean(ax, grid_axis="x")
    fig.subplots_adjust(left=0.42, right=0.96, bottom=0.35, top=0.82)
    return fig


def main() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Arimo", "Liberation Sans", "DejaVu Sans"],
        "axes.linewidth": 0.65,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })
    sources = {
        x: pd.read_csv(PUBLIC / "panels" / f"Extended_Data_Figure_2_panel_{x}_source_data.tsv", sep="\t")
        for x in "abcdef"
    }
    drawers = {
        "a": panel_a,
        "b": panel_b,
        "c": panel_c,
        "d": panel_d,
        "e": panel_e,
        "f": panel_f,
    }
    for letter in "abcdef":
        save_panel(letter, drawers[letter](sources[letter]), sources[letter])


if __name__ == "__main__":
    main()
