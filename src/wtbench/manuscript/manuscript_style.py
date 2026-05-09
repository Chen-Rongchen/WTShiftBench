from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.text import Text


FONT_FAMILY = ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"]
BASE_FONT_SIZE = 7.0
PANEL_HEADING_SIZE = 8.6
PANEL_LABEL_SIZE = 9.0
AXIS_LABEL_SIZE = 7.0
TICK_LABEL_SIZE = 6.2
LEGEND_FONT_SIZE = 6.0

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
            "font.family": "sans-serif",
            "font.sans-serif": FONT_FAMILY,
            "font.size": BASE_FONT_SIZE,
            "axes.titlesize": PANEL_HEADING_SIZE,
            "axes.labelsize": AXIS_LABEL_SIZE,
            "xtick.labelsize": TICK_LABEL_SIZE,
            "ytick.labelsize": TICK_LABEL_SIZE,
            "legend.fontsize": LEGEND_FONT_SIZE,
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
            "axes.titleweight": "bold",
            "axes.titlepad": 3,
            "legend.frameon": False,
            "legend.handlelength": 1.2,
            "legend.handletextpad": 0.4,
            "patch.linewidth": 0.5,
            "lines.linewidth": 0.9,
            "lines.markersize": 3.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.dpi": 1200,
        }
    )


def clean_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.6)
    ax.spines["bottom"].set_linewidth(0.6)
    ax.tick_params(axis="both", which="major", length=2.2, width=0.6, pad=1.5)


def finalize_manuscript_figure(fig: plt.Figure, *, font_scale: float = 1.0) -> None:
    """Normalize typography just before saving a manuscript figure."""
    for text in fig.findobj(match=Text):
        text.set_fontfamily("sans-serif")
        if font_scale != 1.0:
            text.set_fontsize(text.get_fontsize() * font_scale)
    for ax in fig.axes:
        ax.xaxis.label.set_fontsize(AXIS_LABEL_SIZE * font_scale)
        ax.yaxis.label.set_fontsize(AXIS_LABEL_SIZE * font_scale)
        ax.xaxis.label.set_fontweight("normal")
        ax.yaxis.label.set_fontweight("normal")
        for tick_label in ax.get_xticklabels() + ax.get_yticklabels():
            tick_label.set_fontsize(TICK_LABEL_SIZE * font_scale)
            tick_label.set_fontweight("normal")
        legend = ax.get_legend()
        if legend is not None:
            for legend_text in legend.get_texts():
                legend_text.set_fontsize(LEGEND_FONT_SIZE * font_scale)
                legend_text.set_fontweight("normal")


def add_panel_label(
    ax: plt.Axes,
    label: str,
    x: float = -0.03,
    y: float = 1.0,
    *,
    fontsize: float = 8.5,
) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        fontsize=fontsize,
        fontweight="bold",
        va="bottom",
        ha="left",
        color=COLORS["text"],
    )


def add_panel_heading(
    ax: plt.Axes,
    label: str,
    title: str,
    *,
    label_x: float = -0.08,
    title_x: float | None = None,
    y: float = 1.055,
    label_fontsize: float = PANEL_LABEL_SIZE,
    title_fontsize: float = PANEL_HEADING_SIZE,
    title_fontweight: str = "bold",
) -> None:
    """Place panel letter and title as one heading above the axes."""
    for loc in ("left", "center", "right"):
        ax.set_title("", loc=loc)
    if title_x is None:
        ax.text(
            label_x,
            y,
            f"{label}  {title}",
            transform=ax.transAxes,
            fontsize=title_fontsize,
            fontweight=title_fontweight,
            va="bottom",
            ha="left",
            color=COLORS["text"],
            clip_on=False,
        )
    else:
        add_panel_label(ax, label, x=label_x, y=y, fontsize=label_fontsize)
        ax.text(
            title_x,
            y,
            title,
            transform=ax.transAxes,
            fontsize=title_fontsize,
            fontweight=title_fontweight,
            va="bottom",
            ha="left",
            color=COLORS["text"],
            clip_on=False,
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
        "lm_g_geneformer_ridge_hcc_formal_v1": "LM +\nGeneformer",
        "lm_train_lowrank_hcc_formal_v1": "LM\nlow-rank",
        "lm_g_scgpt_ridge_hcc_formal_v1": "LM +\nscGPT",
        "null_model": "null",
        "gears_hcc_formal_v1_e30_lr2e-03_wd1e-06": "GEARS\nsweep A",
        "gears_hcc_formal_v1_e20_lr1e-03_wd1e-06": "GEARS\nsweep B",
        "gears_hcc_formal_v1_e30_lr1e-03_wd1e-05": "GEARS\nsweep C",
        "gears_hcc_formal_v1_e30_lr5e-04_wd1e-06": "GEARS\nsweep D",
        "gears_hcc_formal_v1_e40_lr1e-03_wd1e-06": "GEARS\nsweep E",
    }
    return labels.get(model_id, model_id.replace("_hcc_formal_v1", "").replace("_", "\n"))
