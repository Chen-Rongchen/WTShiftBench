from __future__ import annotations

import matplotlib.pyplot as plt


COLORS = {
    "baseline": "#2B2B2B",
    "gears": "#4C78A8",
    "gears_sweep": "#8DB7D6",
    "foundation": "#72A39A",
    "linear": "#A6A6A6",
    "null": "#D9D9D9",
    "primary_qualified": "#4B8A5A",
    "supporting": "#B8A64A",
    "boundary": "#C65A4A",
    "grid": "#EDEDED",
    "text": "#1F1F1F",
    "point": "#8F8F8F",
    "point_light": "#C9C9C9",
    "accent_red": "#D95F4B",
    "accent_blue": "#5DA5DA",
    "accent_orange": "#E6A05A",
    "accent_purple": "#9C89C9",
}


def apply_manuscript_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 7,
            "axes.titlesize": 7.5,
            "axes.labelsize": 7,
            "xtick.labelsize": 6,
            "ytick.labelsize": 6,
            "legend.fontsize": 6,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 2.2,
            "ytick.major.size": 2.2,
            "axes.edgecolor": "#4A4A4A",
            "axes.labelcolor": COLORS["text"],
            "xtick.color": "#4A4A4A",
            "ytick.color": "#4A4A4A",
            "text.color": COLORS["text"],
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "axes.titleweight": "normal",
            "axes.titlepad": 3,
            "legend.frameon": False,
            "legend.handlelength": 1.2,
            "legend.handletextpad": 0.4,
            "patch.linewidth": 0.5,
            "lines.linewidth": 0.9,
            "lines.markersize": 3.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.dpi": 300,
        }
    )


def clean_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.6)
    ax.spines["bottom"].set_linewidth(0.6)
    ax.tick_params(axis="both", which="major", length=2.2, width=0.6, pad=1.5)


def add_panel_label(ax: plt.Axes, label: str, x: float = -0.10, y: float = 1.04) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        fontsize=8.5,
        fontweight="bold",
        va="bottom",
        ha="left",
        color=COLORS["text"],
    )


def model_color(model_id: str, object_role: str | None = None) -> str:
    if model_id == "shared_mean_baseline" or object_role == "baseline":
        return COLORS["baseline"]
    if model_id == "null_model" or object_role == "null":
        return COLORS["null"]
    if model_id == "gears_hcc_formal_v1":
        return COLORS["gears"]
    if model_id.startswith("gears_hcc_formal_v1_"):
        return COLORS["gears_sweep"]
    if model_id.startswith("geneformer") or model_id.startswith("scgpt"):
        return COLORS["foundation"]
    if model_id.startswith("lm_"):
        return COLORS["linear"]
    return "#9A9A9A"


def short_model_label(model_id: str) -> str:
    labels = {
        "shared_mean_baseline": "shared mean\nbaseline",
        "gears_hcc_formal_v1": "GEARS\nformal",
        "geneformer_hcc_formal_v1": "Geneformer",
        "scgpt_hcc_formal_v1": "scGPT",
        "lm_g_geneformer_ridge_hcc_formal_v1": "LM +\nGeneformer G",
        "lm_train_lowrank_hcc_formal_v1": "LM\nlow-rank",
        "lm_g_scgpt_ridge_hcc_formal_v1": "LM +\nscGPT G",
        "null_model": "null",
        "gears_hcc_formal_v1_e30_lr2e-03_wd1e-06": "GEARS\nsweep A",
        "gears_hcc_formal_v1_e20_lr1e-03_wd1e-06": "GEARS\nsweep B",
        "gears_hcc_formal_v1_e30_lr1e-03_wd1e-05": "GEARS\nsweep C",
        "gears_hcc_formal_v1_e30_lr5e-04_wd1e-06": "GEARS\nsweep D",
        "gears_hcc_formal_v1_e40_lr1e-03_wd1e-06": "GEARS\nsweep E",
    }
    return labels.get(model_id, model_id.replace("_hcc_formal_v1", "").replace("_", "\n"))
