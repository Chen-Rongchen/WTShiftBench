from __future__ import annotations

import matplotlib.pyplot as plt


COLORS = {
    "baseline": "#222222",
    "gears": "#2F6B9A",
    "gears_sweep": "#77A7C8",
    "foundation": "#8AA6A3",
    "linear": "#A7A7A7",
    "null": "#D8D8D8",
    "primary_qualified": "#2E7D52",
    "supporting": "#B59B2B",
    "boundary": "#B65A5A",
    "grid": "#E6E6E6",
    "text": "#222222",
}


def apply_manuscript_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 7,
            "axes.titlesize": 8,
            "axes.labelsize": 7,
            "xtick.labelsize": 6,
            "ytick.labelsize": 6,
            "legend.fontsize": 6,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.dpi": 300,
        }
    )


def clean_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def add_panel_label(ax: plt.Axes, label: str, x: float = -0.12, y: float = 1.06) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        fontsize=10,
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

