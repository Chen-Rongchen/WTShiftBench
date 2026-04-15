from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image


@dataclass(frozen=True)
class FigureConfig:
    output_dir: Path
    panel_a_image: Path
    panel_b_image: Path
    shared_anchor_summary_tsv: Path
    target_level_grid_summary_tsv: Path
    evidence_tier_summary_tsv: Path
    anchor_claim_tiering_tsv: Path
    figure_title: str
    single_panel_width_in: float
    single_panel_height_in: float
    combined_width_in: float
    combined_height_in: float
    dpi: int


TIER_ORDER = [
    "primary_but_qualified",
    "supporting_only",
    "supporting_but_sensitive",
    "primary_evidence",
    "stable_but_nonpositive_formal",
    "preliminary_only",
    "background_or_negative",
]

TIER_LABELS = {
    "primary_but_qualified": "primary,\nqualified",
    "supporting_only": "supporting\nonly",
    "supporting_but_sensitive": "supporting,\nsensitive",
    "primary_evidence": "primary\nevidence",
    "stable_but_nonpositive_formal": "stable,\nnonpositive",
    "preliminary_only": "preliminary\nonly",
    "background_or_negative": "background /\nnegative",
}

TIER_COLORS = {
    "primary_but_qualified": "#b22222",
    "supporting_only": "#8c8c8c",
    "supporting_but_sensitive": "#d8a03d",
    "primary_evidence": "#b22222",
    "stable_but_nonpositive_formal": "#6e8fb6",
    "preliminary_only": "#bdbdbd",
    "background_or_negative": "#e6e6e6",
}

GRID_ORDER = ["Q1_anchor", "middle", "Q4_low_information"]

GRID_LABELS = {
    "Q1_anchor": "canonical\nanchor",
    "middle": "middle\nband",
    "Q4_low_information": "low\ninformation",
}

GRID_COLORS = {
    "Q1_anchor": "#b22222",
    "middle": "#c8c8c8",
    "Q4_low_information": "#7f7f7f",
}

def load_config(path: Path) -> FigureConfig:
    with path.open() as fh:
        raw = json.load(fh)
    base = Path.cwd()
    return FigureConfig(
        output_dir=base / raw["output_dir"],
        panel_a_image=base / raw["panel_a_image"],
        panel_b_image=base / raw["panel_b_image"],
        shared_anchor_summary_tsv=base / raw["shared_anchor_summary_tsv"],
        target_level_grid_summary_tsv=base / raw["target_level_grid_summary_tsv"],
        evidence_tier_summary_tsv=base / raw["evidence_tier_summary_tsv"],
        anchor_claim_tiering_tsv=base / raw["anchor_claim_tiering_tsv"],
        figure_title=str(raw["figure_title"]),
        single_panel_width_in=float(raw["single_panel_width_in"]),
        single_panel_height_in=float(raw["single_panel_height_in"]),
        combined_width_in=float(raw["combined_width_in"]),
        combined_height_in=float(raw["combined_height_in"]),
        dpi=int(raw["dpi"]),
    )


def apply_style() -> None:
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
        }
    )


def add_panel_label(ax: plt.Axes, label: str, x: float = -0.02, y: float = 1.04) -> None:
    ax.text(x, y, label, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="left")


def image_panel(ax: plt.Axes, image_path: Path, label: str, title: str) -> None:
    ax.imshow(Image.open(image_path))
    ax.set_axis_off()
    ax.set_title(title, loc="left", pad=3)
    add_panel_label(ax, label, x=-0.01, y=1.02)


def save_panel(fig: plt.Figure, config: FigureConfig, name: str) -> None:
    fig.savefig(config.output_dir / f"{name}.png", dpi=config.dpi, bbox_inches="tight")
    fig.savefig(config.output_dir / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def panel_anchor_tiers(ax: plt.Axes, config: FigureConfig) -> None:
    shared = pd.read_csv(config.shared_anchor_summary_tsv, sep="\t")
    tiers = pd.read_csv(config.anchor_claim_tiering_tsv, sep="\t")
    anchors = shared.loc[shared["shared_anchor_call"].eq("shared_canonical_anchor")].merge(
        tiers.rename(columns={"target_gene": "target_gene"}),
        on="target_gene",
        how="left",
    )
    anchors = anchors.sort_values(["final_wording_tier", "depmap_quantile_mean"], ascending=[True, False])

    y = np.arange(len(anchors))
    colors = [TIER_COLORS.get(str(tier), "#bdbdbd") for tier in anchors["final_wording_tier"]]
    ax.scatter(anchors["depmap_quantile_mean"], y, s=36, color=colors, edgecolor="white", linewidth=0.5, label="DepMap")
    ax.scatter(
        anchors["shift_quantile_mean"],
        y,
        s=36,
        color="white",
        edgecolor=colors,
        linewidth=1.0,
        label="Transcriptome",
    )
    for _, row in anchors.iterrows():
        yy = int(np.where(anchors["target_gene"].to_numpy() == row["target_gene"])[0][0])
        x0 = float(row["shift_quantile_mean"])
        x1 = float(row["depmap_quantile_mean"])
        ax.plot([x0, x1], [yy, yy], color="#b5b5b5", linewidth=0.8, zorder=0)
        ax.text(1.02, yy, str(row["final_wording_tier"]).replace("_", " "), va="center", fontsize=6)

    ax.set_yticks(y)
    ax.set_yticklabels(anchors["target_gene"])
    ax.set_xlim(0.75, 1.05)
    ax.set_xlabel("Mean within-cell-line quantile")
    ax.set_title("Shared anchors resolve into wording tiers", loc="left")
    ax.grid(axis="x", color="#e6e6e6", linewidth=0.6)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, handletextpad=0.4)
    add_panel_label(ax, "c")


def panel_evidence_tiers(ax: plt.Axes, config: FigureConfig) -> None:
    evidence = pd.read_csv(config.evidence_tier_summary_tsv, sep="\t")
    focused = evidence.loc[~evidence["evidence_tier"].eq("background_or_negative")].copy()
    grouped = (
        focused.groupby(["object_type", "evidence_tier"], observed=True)
        .size()
        .rename("n")
        .reset_index()
    )
    pivot = grouped.pivot_table(index="object_type", columns="evidence_tier", values="n", fill_value=0)
    columns = [tier for tier in TIER_ORDER if tier in pivot.columns]
    bottom = np.zeros(len(pivot), dtype=float)
    x = np.arange(len(pivot))
    for tier in columns:
        values = pivot[tier].to_numpy(dtype=float)
        ax.bar(x, values, bottom=bottom, width=0.62, color=TIER_COLORS.get(tier, "#bdbdbd"), edgecolor="white", linewidth=0.5)
        for xi, yi, base in zip(x, values, bottom):
            if yi > 0:
                ax.text(xi, base + yi / 2, str(int(yi)), ha="center", va="center", fontsize=6)
        bottom += values

    ax.set_xticks(x)
    ax.set_xticklabels([str(v).replace("_", "\n") for v in pivot.index])
    ax.set_ylabel("Objects")
    ax.set_title("Evidence tiers separate anchors from axes", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=TIER_COLORS[tier])
        for tier in columns
    ]
    ax.legend(handles, [TIER_LABELS.get(tier, tier) for tier in columns], frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    add_panel_label(ax, "d")


def panel_grid_decomposition(ax: plt.Axes, config: FigureConfig) -> None:
    summary = pd.read_csv(config.target_level_grid_summary_tsv, sep="\t")
    summary = summary.loc[summary["joint_grid"].isin(GRID_ORDER)].copy()
    pivot = summary.pivot_table(
        index="cell_line",
        columns="joint_grid",
        values="fraction_targets",
        fill_value=0.0,
    ).reindex(columns=GRID_ORDER, fill_value=0.0)
    pivot = pivot.sort_index()

    y = np.arange(len(pivot))
    left = np.zeros(len(pivot), dtype=float)
    for grid in GRID_ORDER:
        values = pivot[grid].to_numpy(dtype=float)
        ax.barh(
            y,
            values,
            left=left,
            height=0.46,
            color=GRID_COLORS[grid],
            edgecolor="white",
            linewidth=0.5,
            label=GRID_LABELS[grid],
        )
        for yi, value, start in zip(y, values, left):
            if value >= 0.08:
                ax.text(start + value / 2, yi, f"{value:.0%}", ha="center", va="center", fontsize=6, color="white" if grid != "middle" else "#333333")
        left += values

    counts = summary.pivot_table(index="cell_line", columns="joint_grid", values="n_targets", fill_value=0).reindex(
        index=pivot.index,
        columns=GRID_ORDER,
        fill_value=0,
    )
    for yi, cell_line in zip(y, pivot.index):
        q1 = int(counts.loc[cell_line, "Q1_anchor"])
        total = int(counts.loc[cell_line].sum())
        ax.text(1.02, yi, f"{q1}/{total} Q1 anchors", va="center", fontsize=6.5)

    ax.set_yticks(y)
    ax.set_yticklabels(pivot.index)
    ax.set_xlim(0, 1.18)
    ax.set_xlabel("Fraction of target-level truth objects")
    ax.set_title("Joint-grid decomposition is structured in both HCC lines", loc="left")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=3, handlelength=1.0, columnspacing=0.8)
    add_panel_label(ax, "e", x=-0.03)


def save_single_panels(config: FigureConfig) -> None:
    specs = [
        ("figure1a_HCC38_joint_grid", lambda ax: image_panel(ax, config.panel_a_image, "a", "HCC38 target-level joint grid")),
        ("figure1b_HCC1143_joint_grid", lambda ax: image_panel(ax, config.panel_b_image, "b", "HCC1143 target-level joint grid")),
        ("figure1c_shared_anchor_tiers", lambda ax: panel_anchor_tiers(ax, config)),
        ("figure1d_evidence_tiers", lambda ax: panel_evidence_tiers(ax, config)),
        ("figure1e_joint_grid_decomposition", lambda ax: panel_grid_decomposition(ax, config)),
    ]
    for name, draw in specs:
        fig, ax = plt.subplots(figsize=(config.single_panel_width_in, config.single_panel_height_in))
        draw(ax)
        fig.tight_layout()
        save_panel(fig, config, name)


def save_combined(config: FigureConfig) -> None:
    fig = plt.figure(figsize=(config.combined_width_in, config.combined_height_in), constrained_layout=False)
    gs = fig.add_gridspec(2, 6, height_ratios=[1.1, 0.9], hspace=0.28, wspace=0.42)
    ax_a = fig.add_subplot(gs[0, 0:3])
    ax_b = fig.add_subplot(gs[0, 3:6])
    ax_c = fig.add_subplot(gs[1, 0:2])
    ax_d = fig.add_subplot(gs[1, 2:4])
    ax_e = fig.add_subplot(gs[1, 4:6])

    image_panel(ax_a, config.panel_a_image, "a", "HCC38 target-level joint grid")
    image_panel(ax_b, config.panel_b_image, "b", "HCC1143 target-level joint grid")
    panel_anchor_tiers(ax_c, config)
    panel_evidence_tiers(ax_d, config)
    panel_grid_decomposition(ax_e, config)
    fig.suptitle(config.figure_title, x=0.02, y=0.99, ha="left", fontsize=11, fontweight="bold")
    fig.savefig(config.output_dir / "figure1_truth_object_combined.png", dpi=config.dpi, bbox_inches="tight")
    fig.savefig(config.output_dir / "figure1_truth_object_combined.pdf", bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render manuscript Figure 1 truth-object panels.")
    parser.add_argument(
        "--config",
        default="configs/manuscript/figure1_truth_object_v1.json",
        help="Path to the figure configuration JSON.",
    )
    return parser.parse_args()


def run_from_config(config_path: Path) -> dict[str, Path]:
    config = load_config(Path(config_path))
    config.output_dir.mkdir(parents=True, exist_ok=True)
    apply_style()
    save_single_panels(config)
    save_combined(config)
    return {
        "output_dir": config.output_dir,
        "combined_png": config.output_dir / "figure1_truth_object_combined.png",
        "combined_pdf": config.output_dir / "figure1_truth_object_combined.pdf",
    }


def main() -> None:
    args = parse_args()
    run_from_config(Path(args.config))
    config = load_config(Path(args.config))
    print(f"Wrote Figure 1 panels to {config.output_dir}")
