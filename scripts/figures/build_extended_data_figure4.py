from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "figures/Extended_Data_Figure_4"
BUILD = ROOT / "figure_build/output/Extended_Data_Figure_4"
MANUSCRIPT = ROOT / "manuscript/figures/Extended_Data_Figure_4"

GREEN = "#2F7F73"
CORAL = "#E58D7C"
BLUE = "#4C78A8"
PURPLE = "#8A6FB0"
GRAY = "#A5A5A5"
LIGHT = "#E7E7E7"

MODEL_LABELS = {
    "scgen_hcc_formal_v1": "scGen",
    "cpa_v0.8.8": "CPA",
    "gears_hcc_formal_v1": "GEARS formal",
    "cellot_hcc_formal_v1": "CellOT",
    "scgpt_hcc_formal_v1": "scGPT",
    "geneformer_hcc_formal_v1": "Geneformer",
    "lm_train_lowrank_hcc_formal_v1": "low-rank",
    "lm_g_scgpt_ridge_hcc_formal_v1": "scGPT-ridge",
    "lm_g_geneformer_ridge_hcc_formal_v1": "Geneformer-ridge",
    "shared_mean_baseline": "shared mean",
    "null_model": "null",
}

MODEL_ORDER = list(MODEL_LABELS.values())
CALIBRATION_MODEL_ORDER = [model for model in MODEL_ORDER if model != "null"]
SENSITIVITY_ORDER = ["scGen", "GEARS", "CPA", "CellOT"]


def clean(ax: plt.Axes, grid_axis: str | None = None) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=7)
    if grid_axis:
        ax.grid(axis=grid_axis, color="#F0F0F0", linewidth=0.45, zorder=0)
    else:
        ax.grid(False)
    ax.set_axisbelow(True)


def panel_title(ax: plt.Axes, text: str) -> None:
    ax.set_title(text, loc="left", fontsize=9, fontweight="bold", pad=9)


def save_panel(letter: str, fig: plt.Figure, source: pd.DataFrame) -> None:
    for base in (PUBLIC, BUILD, MANUSCRIPT):
        panel_dir = base / "panels"
        panel_dir.mkdir(parents=True, exist_ok=True)
        stem = panel_dir / f"Extended_Data_Figure_4_panel_{letter}"
        fig.savefig(stem.with_suffix(".png"), dpi=600, bbox_inches="tight")
        fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
        fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
        source.to_csv(f"{stem}_source_data.tsv", sep="\t", index=False)
    plt.close(fig)


def formal_metrics() -> pd.DataFrame:
    metrics = pd.read_csv(
        ROOT / "reports/model_endpoint_recovery/source_data/model_endpoint_recovery_metrics.tsv",
        sep="\t",
    )
    metrics = metrics.loc[metrics["model_id"].isin(MODEL_LABELS)].copy()
    metrics["model"] = metrics["model_id"].map(MODEL_LABELS)
    return metrics


def q_source(metrics: pd.DataFrame) -> pd.DataFrame:
    specs = [
        ("Total-shift endpoint", "total_shift_depmap_qvalue"),
        ("Response-aligned endpoint", "response_aligned_depmap_qvalue"),
        (
            "Response-aligned permutation",
            "response_aligned_endpoint_permutation_qvalue",
        ),
    ]
    out = []
    for family, column in specs:
        part = metrics[["model_id", "model", "cell_line", column]].rename(
            columns={column: "q_value"}
        )
        part["metric_family"] = family
        out.append(part)
    return pd.concat(out, ignore_index=True)


def panel_a(source: pd.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 4.3), sharex=True, sharey=True)
    colors = {
        "Total-shift endpoint": GREEN,
        "Response-aligned endpoint": CORAL,
        "Response-aligned permutation": BLUE,
    }
    offsets = {
        "Total-shift endpoint": -0.16,
        "Response-aligned endpoint": 0.0,
        "Response-aligned permutation": 0.16,
    }
    for ax, context in zip(axes, ["HCC38", "HCC1143"]):
        d = source.loc[source.cell_line.eq(context)].dropna(subset=["q_value"]).copy()
        ymap = {m: i for i, m in enumerate(CALIBRATION_MODEL_ORDER)}
        for family, color in colors.items():
            sub = d.loc[d.metric_family.eq(family)]
            y = sub.model.map(ymap).astype(float) + offsets[family]
            ax.scatter(
                -np.log10(sub.q_value.clip(lower=1e-6)),
                y,
                s=28,
                color=color,
                edgecolor="white",
                linewidth=0.4,
                label=family,
                zorder=3,
            )
        threshold = -np.log10(0.1)
        ax.axvline(threshold, color="#A8A8A8", lw=0.8, ls=(0, (3, 2)))
        ax.text(
            threshold + 0.06,
            0.985,
            "q = 0.1",
            transform=ax.get_xaxis_transform(),
            ha="left",
            va="top",
            fontsize=6.2,
            color="#777777",
        )
        ax.set_title(context, fontsize=8)
        ax.set_xlabel("−log10(q)")
        clean(ax, "x")
    axes[0].set_yticks(
        range(len(CALIBRATION_MODEL_ORDER)),
        CALIBRATION_MODEL_ORDER,
    )
    axes[0].set_ylim(len(CALIBRATION_MODEL_ORDER) - 0.5, -0.5)
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        frameon=False,
        fontsize=6.1,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.01),
        ncol=3,
        columnspacing=1.1,
        handletextpad=0.4,
    )
    fig.suptitle(
        "Endpoint-alignment statistical calibration",
        x=0.08,
        ha="left",
        fontsize=9,
        fontweight="bold",
    )
    fig.subplots_adjust(left=0.23, right=0.98, bottom=0.24, top=0.80, wspace=0.10)
    return fig


def sensitivity_source() -> pd.DataFrame:
    source = pd.read_csv(
        ROOT
        / "reports/manuscript_figures_v2/fig5_sensitivity_controls/panels/figure5_finite_budget_model_sensitivity.tsv",
        sep="\t",
    )
    return source.loc[
        source["metric"].isin(
            ["response-aligned endpoint ρ", "anchor vs low-information AUC"]
        )
    ].copy()


def panel_b(source: pd.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(2, 2, figsize=(8.0, 5.3), sharey=True)
    metrics = [
        (
            "response-aligned endpoint ρ",
            "Response-aligned endpoint ρ",
            (-0.35, 0.70),
            0,
        ),
        (
            "anchor vs low-information AUC",
            "Anchor vs low-information AUC",
            (0.20, 1.00),
            0.5,
        ),
    ]
    context_colors = {"HCC38": GREEN, "HCC1143": CORAL}
    ymap = {m: i for i, m in enumerate(SENSITIVITY_ORDER)}
    for row, context in enumerate(["HCC38", "HCC1143"]):
        for col, (metric, xlabel, xlim, reference) in enumerate(metrics):
            ax = axes[row, col]
            d = source.loc[
                source.cell_line.eq(context) & source.metric.eq(metric)
            ].copy()
            for model in SENSITIVITY_ORDER:
                group = d.loc[d.model_family.eq(model)]
                finite = group.loc[group.run_type.ne("formal"), "metric_value"]
                formal = group.loc[group.run_type.eq("formal"), "metric_value"]
                y = ymap[model]
                if not finite.empty:
                    ax.hlines(y, finite.min(), finite.max(), color=LIGHT, lw=3.0, zorder=1)
                    ax.scatter(
                        finite,
                        np.full(len(finite), y),
                        s=22,
                        color=GRAY,
                        alpha=0.85,
                        edgecolor="white",
                        linewidth=0.35,
                        zorder=2,
                    )
                if not formal.empty:
                    ax.scatter(
                        formal.iloc[0],
                        y,
                        s=44,
                        color=context_colors[context],
                        edgecolor="white",
                        linewidth=0.5,
                        zorder=3,
                    )
            ax.axvline(reference, color="#A8A8A8", lw=0.8, ls=(0, (3, 2)))
            ax.set_xlim(*xlim)
            if row == 1:
                ax.set_xlabel(xlabel)
            if col == 0:
                ax.set_ylabel(context, fontsize=8)
            clean(ax, "x")
    axes[0, 0].set_yticks(range(len(SENSITIVITY_ORDER)), SENSITIVITY_ORDER)
    axes[0, 0].set_ylim(len(SENSITIVITY_ORDER) - 0.5, -0.5)
    axes[0, 0].set_title("Response-aligned endpoint recovery", fontsize=8)
    axes[0, 1].set_title("Anchor separation", fontsize=8)
    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=GRAY, markeredgecolor="white", markersize=5, label="finite-budget run"),
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=GREEN, markeredgecolor="white", markersize=6, label="HCC38 formal"),
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=CORAL, markeredgecolor="white", markersize=6, label="HCC1143 formal"),
        plt.Line2D([0], [0], color=LIGHT, lw=3, label="finite-budget range"),
    ]
    fig.legend(
        handles=legend_handles,
        frameon=False,
        fontsize=6.2,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.005),
        ncol=4,
    )
    fig.suptitle(
        "Expanded finite-budget model sensitivity",
        x=0.08,
        ha="left",
        fontsize=9,
        fontweight="bold",
    )
    fig.subplots_adjust(left=0.18, right=0.98, bottom=0.20, top=0.82, hspace=0.16, wspace=0.12)
    return fig


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Arimo", "Liberation Sans", "DejaVu Sans"],
            "axes.linewidth": 0.65,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    metrics = formal_metrics()
    qdata = q_source(metrics)
    sensitivity = sensitivity_source()
    panels = {"a": qdata, "b": sensitivity}
    figures = {"a": panel_a(qdata), "b": panel_b(sensitivity)}
    for letter in "ab":
        save_panel(letter, figures[letter], panels[letter])
    print("Built active Extended Data Fig. 4 panels a–b")


if __name__ == "__main__":
    main()
