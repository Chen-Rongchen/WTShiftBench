#!/usr/bin/env python3
"""ED Fig 3 current manuscript builder (standalone override script).

NOTE: This script directly writes to manuscript/extended_data/Extended_Data_Figure_3/
and is the ACTUAL builder for the current manuscript figure. It overrides the standard
pipeline (build_extended_data_figure3_v2.py → extended_data_figure3_v2.py).

The standard pipeline (extended_data_figure3_v2.py) now also supports panel c, but
uses matplotlib compositing instead of PIL. This script is preserved as the
authoritative builder for the current submission version."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from wtbench.manuscript.figure_io import repo_root, save_figure
from wtbench.manuscript.manuscript_style import COLORS, apply_manuscript_style, clean_axes

ROOT = repo_root()

# Data
REPLOGLE_TSV = ROOT / "reports/manuscript_extended_data_v1/edfig3_k562_replogle_joint_grid/replogle_k562_essential_joint_grid.tsv"

# Output
OUT_DIR = ROOT / "manuscript/extended_data/Extended_Data_Figure_3"

QUADRANT_COLORS = {
    "Q1_anchor": "#D55E00",
    "Q2_shift_excess": "#009E73",
    "Q3_dep_excess": "#56B4E9",
    "Q4_low_info": "#BDBDBD",
    "middle": "#F0F0F0",
}


# ─── Panel A data ──────────────────────────────────────────────────────────

TEMPORAL_BRIDGE = ROOT / "reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_bridge_summary.tsv"
TARGET_7D = ROOT / "data/processed/stage2_truth_driven_bridge_gse90063_7d/dixit_2016_k562_tf_7d_gse90063/target_level_bridge_table.tsv.gz"
TARGET_13D = ROOT / "data/processed/stage2_truth_driven_bridge_gse90063_13d/dixit_2016_k562_tf_13d_gse90063/target_level_bridge_table.tsv.gz"


def build_panel_a_source() -> pd.DataFrame:
    bridge = pd.read_csv(TEMPORAL_BRIDGE, sep="\t")
    t7 = pd.read_csv(TARGET_7D, sep="\t").assign(timepoint="7d")
    t13 = pd.read_csv(TARGET_13D, sep="\t").assign(timepoint="13d")
    plot = bridge.loc[
        bridge["truth_metric"].isin(["real_shift_mean_abs", "real_shift_L2"])
        & bridge["depmap_endpoint"].eq("depmap_gene_dependency")
    ].copy()
    plot["timepoint_order"] = plot["timepoint"].map({"7d": 0, "13d": 1})
    plot["mean_shift_norm"] = plot.groupby("truth_metric")["mean_truth_metric"].transform(lambda s: s / s.max())
    tv = pd.concat([t7, t13], ignore_index=True)
    errs = []
    for m, col in [("real_shift_mean_abs", "real_shift_mean_abs"), ("real_shift_L2", "real_shift_L2")]:
        for tp, sub in tv.groupby("timepoint"):
            errs.append({"truth_metric": m, "timepoint": tp, "mean_shift_sem": float(sub[col].sem())})
    edf = pd.DataFrame(errs)
    plot = plot.merge(edf, on=["truth_metric", "timepoint"], how="left")
    plot["mean_shift_sem_norm"] = plot["mean_shift_sem"] / plot.groupby("truth_metric")["mean_truth_metric"].transform("max")
    return plot.sort_values(["truth_metric", "timepoint_order"])


def generate_panel_a(src_a: pd.DataFrame) -> Path:
    """Render panel a with wider gap between two inset plots."""
    apply_manuscript_style()
    fig, ax = plt.subplots(figsize=(5.0, 0.9))
    ax.set_axis_off()

    PG = COLORS["primary_qualified"]
    NG = "#888888"

    # Legend up top
    # Legend — bottom-right, below inset axes
    # Legend — bottom-right, two stacked rows, shifted right
    ax.plot([1.05, 1.08], [0.14, 0.14], color=PG, linewidth=1.2, transform=ax.transAxes, clip_on=False)
    ax.scatter([1.065], [0.14], s=14, color=PG, transform=ax.transAxes, clip_on=False)
    ax.text(1.09, 0.14, "Mean abs (primary)", transform=ax.transAxes, va="center", fontsize=5.8)
    ax.plot([1.05, 1.08], [0.06, 0.06], color=NG, linewidth=1.2, transform=ax.transAxes, clip_on=False)
    ax.scatter([1.065], [0.06], s=14, marker="s", color=NG, transform=ax.transAxes, clip_on=False)
    ax.text(1.09, 0.06, "L2 sensitivity", transform=ax.transAxes, va="center", fontsize=5.8)

    # Two inset plots with WIDER GAP
    rank_ax = ax.inset_axes([0.03, 0.10, 0.38, 0.68])
    shift_ax = ax.inset_axes([0.59, 0.10, 0.38, 0.68])

    styles = {
        "real_shift_mean_abs": {"color": PG, "marker": "o", "zorder": 3},
        "real_shift_L2": {"color": NG, "marker": "s", "zorder": 2},
    }
    x_map = {"7d": 0, "13d": 1}
    for metric, style in styles.items():
        sub = src_a.loc[src_a["truth_metric"].eq(metric)].sort_values("timepoint_order")
        xs = [x_map[v] for v in sub["timepoint"]]
        rank_ax.plot(xs, sub["aligned_spearman"], color=style["color"], marker=style["marker"],
                     linewidth=1.2, markersize=4.2, zorder=style["zorder"])
        shift_ax.errorbar(xs, sub["mean_shift_norm"], yerr=sub["mean_shift_sem_norm"],
                          color=style["color"], marker=style["marker"], linewidth=1.2,
                          markersize=4.2, capsize=2.0, capthick=0.7, elinewidth=0.8, zorder=style["zorder"])

    for sa in (rank_ax, shift_ax):
        sa.set_xlim(-0.25, 1.25)
        sa.set_xticks([0, 1])
        sa.set_xticklabels(["7d", "13d"])
        sa.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
        clean_axes(sa)

    rank_ax.set_ylim(0.35, 0.88)
    rank_ax.set_ylabel("Bridge rho", labelpad=2)
    rank_ax.set_title("Rank bridge weakens at 13d", loc="left", fontsize=7.0, fontweight="bold", pad=2)
    shift_ax.set_ylim(0.55, 1.15)
    shift_ax.set_ylabel("Mean shift (norm.)", labelpad=2)
    shift_ax.set_title("Perturbation magnitude increases at 13d", loc="left", fontsize=7.0, fontweight="bold", pad=2)

    # Title added via PIL compositing for alignment

    png = OUT_DIR / "panels" / "Extended_Data_Figure_3_panel_a.png"
    pdf = OUT_DIR / "panels" / "Extended_Data_Figure_3_panel_a.pdf"
    save_figure(fig, png, pdf)
    plt.close(fig)
    return png


def generate_square_panel_b():
    """Generate square Replogle scatter panel b. Info + legend outside right, no borders."""
    df = pd.read_csv(REPLOGLE_TSV, sep="\t")
    df["shift_quantile"] = df["real_shift_mean_abs"].rank(pct=True)
    df["depmap_quantile"] = df["depmap_gene_dependency"].rank(pct=True)

    apply_manuscript_style()
    fig, ax = plt.subplots(figsize=(4.5, 1.4))

    # Middle band
    mid = df.loc[df["quadrant"] == "middle"]
    ax.scatter(mid["shift_quantile"], mid["depmap_quantile"],
               c=QUADRANT_COLORS["middle"], s=4, edgecolors="none", alpha=0.5, zorder=1)

    # Q1-Q4
    for quad in ["Q1_anchor", "Q2_shift_excess", "Q3_dep_excess", "Q4_low_info"]:
        sub = df.loc[df["quadrant"] == quad]
        if sub.empty:
            continue
        s = 14 if quad == "Q1_anchor" else 8
        z = 5 if quad == "Q1_anchor" else 3
        ax.scatter(sub["shift_quantile"], sub["depmap_quantile"],
                   c=QUADRANT_COLORS[quad], s=s, edgecolors="white",
                   linewidths=0.3, alpha=0.85, zorder=z)

    # 25/75 lines
    for pct in [0.25, 0.75]:
        ax.axvline(pct, color="#888888", linewidth=0.6, linestyle="--", alpha=0.6)
        ax.axhline(pct, color="#888888", linewidth=0.6, linestyle="--", alpha=0.6)

    ax.set_xlabel("Perturbation shift (rank percentile)", fontsize=6.0)
    ax.set_ylabel("CRISPR dependency (rank percentile)", fontsize=6.0)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)

    n = len(df)
    n_q1 = int((df["quadrant"] == "Q1_anchor").sum())
    n_q2 = int((df["quadrant"] == "Q2_shift_excess").sum())
    n_q3 = int((df["quadrant"] == "Q3_dep_excess").sum())
    n_q4 = int((df["quadrant"] == "Q4_low_info").sum())
    n_mid = int((df["quadrant"] == "middle").sum())

    # Stats outside right
    stats_y = 0.95
    ax.text(1.08, stats_y,
            f"aligned Spearman rho = 0.402\n"
            f"95% CI [0.363, 0.439]\n"
            f"empirical p = 0.001",
            transform=ax.transAxes, fontsize=5.2, va="top", ha="left", color="#333333")

    # Color swatches outside right
    quad_info = [
        ("Q1 anchor", n_q1, QUADRANT_COLORS["Q1_anchor"]),
        ("Q2 shift excess", n_q2, QUADRANT_COLORS["Q2_shift_excess"]),
        ("Q3 dep excess", n_q3, QUADRANT_COLORS["Q3_dep_excess"]),
        ("Q4 low info", n_q4, QUADRANT_COLORS["Q4_low_info"]),
        ("middle", n_mid, QUADRANT_COLORS["middle"]),
    ]
    for i, (label, count, color) in enumerate(quad_info):
        y = 0.55 - i * 0.048
        ax.plot(1.08, y, marker="s", color=color, markersize=4,
                transform=ax.transAxes, clip_on=False)
        ax.text(1.12, y, f"{label} ({count})", transform=ax.transAxes,
                fontsize=5.0, va="center", ha="left", color="#333333")

    ax.tick_params(labelsize=5.5)
    clean_axes(ax)
    ax.set_box_aspect(1)

    png_path = OUT_DIR / "panels" / "Extended_Data_Figure_3_panel_b.png"
    pdf_path = OUT_DIR / "panels" / "Extended_Data_Figure_3_panel_b.pdf"
    save_figure(fig, png_path, pdf_path)
    plt.close(fig)
    return png_path


def generate_panel_c() -> Path:
    """K562 evidence-tier checklist — exact Fig 2f compact claim matrix style."""
    apply_manuscript_style()

    fig, ax = plt.subplots(figsize=(5.0, 1.8))
    ax.set_axis_off()

    LIGHT_GRAY = "#F0F0F0"
    DIVIDER_GRAY = "#CCCCCC"
    DARK_TEXT = "#1F1F1F"
    GREEN = "#2E7D32"
    OCHRE = "#D84315"
    GREEN_FILL = "#E8F5E9"

    rows = [
        ("Bridge rho above null",            "A1", "yes", "\u03c1=0.733 / 0.515"),
        ("Joint grid defined",                "",  "yes", "25/75 grid applied"),
        ("Q1 region present",                 "",  "yes", "quadrant observed"),
        ("Backbone / shift-excess structure", "A0","yes", "matches primary form"),
        ("Content-level replication",          "B", "no",  "composition differs"),
        ("Assigned tier",                      "",  "A0/A1, not B", ""),
    ]

    # Header bar (Fig 2f style)
    ax.add_patch(
        plt.Rectangle((0.005, 0.86), 0.99, 0.08, transform=ax.transAxes,
                      facecolor=LIGHT_GRAY, edgecolor="none", zorder=0))
    headers = [("Evidence item", 0.02), ("Tier", 0.46), ("Status", 0.58)]
    for text, x in headers:
        ax.text(x, 0.90, text, fontsize=7.2, fontweight="bold", color=DARK_TEXT, transform=ax.transAxes)
    ax.plot([0.01, 0.99], [0.86, 0.86], color=DIVIDER_GRAY, linewidth=0.7, transform=ax.transAxes)

    row_gap = 0.118
    for i, (item, supports, status, note) in enumerate(rows):
        y = 0.78 - i * row_gap
        is_yes = status == "yes"
        is_tier = "A0/A1" in status

        if is_tier:
            ax.add_patch(
                plt.Rectangle((0.005, y - row_gap * 0.44), 0.99, row_gap * 0.86,
                              transform=ax.transAxes, facecolor=GREEN_FILL, edgecolor="none", zorder=0))

        fw = "bold" if is_tier else "normal"
        fs = 7.5 if is_tier else 6.8
        ax.text(0.02, y, item, fontsize=fs, fontweight=fw,
                color=GREEN if is_tier else DARK_TEXT, transform=ax.transAxes, va="center")

        if supports:
            ax.text(0.46, y, supports, fontsize=6.8, va="center", fontweight="bold",
                    color="#888888", transform=ax.transAxes)

        chip_color = GREEN if is_yes else OCHRE
        ax.add_patch(
            plt.Rectangle((0.58, y - 0.025), 0.025, 0.05, transform=ax.transAxes,
                          facecolor=chip_color, edgecolor="none"))
        status_text = "yes" if is_yes else "no"
        if is_tier:
            status_text = "A0/A1, not B"
        ax.text(0.615, y, status_text, fontsize=6.8 if is_tier else 6.2, va="center",
                fontweight="bold", color=chip_color, transform=ax.transAxes)

        if note:
            ax.text(0.98, y, note, fontsize=5.5, va="center", ha="right",
                    color="#999999", transform=ax.transAxes)

    clean_axes(ax)

    png_path = OUT_DIR / "panels" / "Extended_Data_Figure_3_panel_c.png"
    pdf_path = OUT_DIR / "panels" / "Extended_Data_Figure_3_panel_c.pdf"
    save_figure(fig, png_path, pdf_path)
    plt.close(fig)
    return png_path


def composite_with_pil(panel_a_png: Path, panel_b_png: Path, panel_c_png: Path):
    """Layout: row0=panel_a (full), row1=panel_b | panel_c (c at native width, b fills rest)."""
    from PIL import Image, ImageDraw, ImageFont

    img_a = Image.open(panel_a_png)
    img_b = Image.open(panel_b_png)
    img_c = Image.open(panel_c_png)

    target_w = 4500
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    pad_title = 70

    img_a = img_a.resize((target_w, int(img_a.height * target_w / img_a.width)), Image.LANCZOS)
    draw_a = ImageDraw.Draw(img_a)
    draw_a.text((32, 12), "K562 temporal stratification (7d vs 13d)", fill="#1F1F1F", font=font)

    img_b = img_b.resize((target_w, int(img_b.height * target_w / img_b.width)), Image.LANCZOS)
    b_titled = Image.new("RGB", (img_b.width, img_b.height + pad_title), "white")
    b_titled.paste(img_b, (0, pad_title))
    draw_b = ImageDraw.Draw(b_titled)
    draw_b.text((32, 12), "Large-scale perturbation-fitness bridge confirmation", fill="#1F1F1F", font=font)

    img_c = img_c.resize((target_w, int(img_c.height * target_w / img_c.width)), Image.LANCZOS)
    c_titled = Image.new("RGB", (img_c.width, img_c.height + pad_title), "white")
    c_titled.paste(img_c, (0, pad_title))
    draw_c = ImageDraw.Draw(c_titled)
    draw_c.text((32, 12), "K562 evidence-tier checklist", fill="#1F1F1F", font=font)

    total_h = img_a.height + b_titled.height + c_titled.height
    composite = Image.new("RGB", (target_w, total_h), "white")
    composite.paste(img_a, (0, 0))
    composite.paste(b_titled, (0, img_a.height))
    composite.paste(c_titled, (0, img_a.height + b_titled.height))

    composite.save(OUT_DIR / "Extended_Data_Figure_3.png")
    composite.save(OUT_DIR / "Extended_Data_Figure_3.pdf")
    print(f"[OK] Composite: {target_w}x{total_h}")


def main():
    src_a = build_panel_a_source()
    a_png = generate_panel_a(src_a)
    print(f"[OK] Panel a generated: {a_png}")

    b_png = generate_square_panel_b()
    print(f"[OK] Panel b generated: {b_png}")

    c_png = generate_panel_c()
    print(f"[OK] Panel c generated: {c_png}")

    composite_with_pil(a_png, b_png, c_png)


if __name__ == "__main__":
    main()
