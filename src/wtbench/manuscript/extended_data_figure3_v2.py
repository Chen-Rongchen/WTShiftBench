from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_heading, apply_manuscript_style, clean_axes


FIGURE_ID = "extended_data_figure3"
FIGURE_TITLE = "K562 temporal evidence and large-scale bridge confirmation"
SCRIPT_PATH = Path("scripts/manuscript/build_extended_data_figure3_v2.py")
CLAIM_BOUNDARY = (
    "K562 remains supplementary temporal evidence under A0/A1/B tiering. "
    "The Replogle dataset provides large-n confirmation that the bridge correlation persists above null at scale; "
    "it is a single-context dataset and is not used for A0/A1/B architecture-form tiering."
)
PANEL_IDS = ("a", "b")

# Panel a data (K562 temporal)
TEMPORAL_BRIDGE = Path("reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_bridge_summary.tsv")
TEMPORAL_STRUCTURE = Path("reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_structure_summary.tsv")
TEMP_PANEL_CALLS = Path("reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_panel_calls.tsv")
TEMP_7D_EVIDENCE = Path("reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_7d/dixit_evidence_tier_summary.tsv")
TEMP_13D_EVIDENCE = Path("reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_evidence_tier_summary.tsv")
TARGET_7D = Path("data/processed/stage2_truth_driven_bridge_gse90063_7d/dixit_2016_k562_tf_7d_gse90063/target_level_bridge_table.tsv.gz")
TARGET_13D = Path("data/processed/stage2_truth_driven_bridge_gse90063_13d/dixit_2016_k562_tf_13d_gse90063/target_level_bridge_table.tsv.gz")

# Panel b data (Replogle joint grid)
REPLOGLE_JOINT_GRID = Path("reports/manuscript_extended_data_v1/edfig3_k562_replogle_joint_grid/replogle_k562_essential_joint_grid.tsv")

PRIMARY_GREEN = COLORS["primary_qualified"]  # "#4B8A5A"
NEUTRAL_GRAY = "#888888"
SKY_BLUE = "#56B4E9"
VERMILLION = "#D55E00"


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_extended_data_v1/edfig3_k562_temporal_and_replogle"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [
        root / TEMPORAL_BRIDGE,
        root / TEMPORAL_STRUCTURE,
        root / TEMP_PANEL_CALLS,
        root / TEMP_7D_EVIDENCE,
        root / TEMP_13D_EVIDENCE,
        root / TARGET_7D,
        root / TARGET_13D,
        root / REPLOGLE_JOINT_GRID,
    ]


def cleanup_generated(root: Path) -> None:
    out = output_dir(root)
    if panel_dir(root).exists():
        for path in panel_dir(root).glob("edfig3_panel*"):
            path.unlink()
    for suffix in (".png", ".pdf", "_source_data.tsv", "_panel_manifest.json"):
        path = out / f"edfig3{suffix}"
        if path.exists():
            path.unlink()


def build_panel_a_source(root: Path) -> pd.DataFrame:
    bridge = pd.read_csv(root / TEMPORAL_BRIDGE, sep="\t")
    target_7d = pd.read_csv(root / TARGET_7D, sep="\t").assign(timepoint="7d")
    target_13d = pd.read_csv(root / TARGET_13D, sep="\t").assign(timepoint="13d")

    primary = bridge.loc[bridge["truth_metric"].eq("real_shift_mean_abs") & bridge["depmap_endpoint"].eq("depmap_gene_dependency")]
    vals = primary.set_index("timepoint")
    if vals.loc["7d", "aligned_spearman"] <= vals.loc["13d", "aligned_spearman"] or vals.loc["13d", "mean_truth_metric"] <= vals.loc["7d", "mean_truth_metric"]:
        raise RuntimeError("ED Fig. 3 sanity check failed: temporal stratification changed.")

    plot = bridge.loc[
        bridge["truth_metric"].isin(["real_shift_mean_abs", "real_shift_L2"])
        & bridge["depmap_endpoint"].eq("depmap_gene_dependency")
    ].copy()
    plot["metric_label"] = plot["truth_metric"].map({"real_shift_mean_abs": "Mean abs (primary)", "real_shift_L2": "L2 sensitivity"})
    plot["timepoint_order"] = plot["timepoint"].map({"7d": 0, "13d": 1})
    plot["mean_shift_norm"] = plot.groupby("truth_metric")["mean_truth_metric"].transform(lambda s: s / s.max())

    target_values = pd.concat([target_7d, target_13d], ignore_index=True)
    shift_errors = []
    for metric, source_col in [("real_shift_mean_abs", "real_shift_mean_abs"), ("real_shift_L2", "real_shift_L2")]:
        for timepoint, sub in target_values.groupby("timepoint"):
            shift_errors.append(
                {
                    "truth_metric": metric,
                    "timepoint": timepoint,
                    "mean_shift_sem": float(sub[source_col].sem()),
                }
            )
    error_df = pd.DataFrame(shift_errors)
    plot = plot.merge(error_df, on=["truth_metric", "timepoint"], how="left")
    plot["mean_shift_sem_norm"] = plot["mean_shift_sem"] / plot.groupby("truth_metric")["mean_truth_metric"].transform("max")
    return plot.sort_values(["truth_metric", "timepoint_order"])


def build_panel_b_source(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / REPLOGLE_JOINT_GRID, sep="\t")
    # Compute within-context rank percentiles
    df["shift_quantile"] = df["real_shift_mean_abs"].rank(pct=True)
    df["depmap_quantile"] = df["depmap_gene_dependency"].rank(pct=True)
    return df


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    add_panel_heading(ax, "a", "Temporal bridge-magnitude dissociation", label_x=-0.025, title_x=0.035, y=1.015)

    ax.plot([0.52, 0.555], [0.93, 0.93], color=PRIMARY_GREEN, linewidth=1.2, transform=ax.transAxes, clip_on=False)
    ax.scatter([0.5375], [0.93], s=14, color=PRIMARY_GREEN, transform=ax.transAxes, clip_on=False)
    ax.text(0.565, 0.93, "Mean abs (primary)", transform=ax.transAxes, va="center", fontsize=6.0)
    ax.plot([0.73, 0.765], [0.93, 0.93], color=NEUTRAL_GRAY, linewidth=1.2, transform=ax.transAxes, clip_on=False)
    ax.scatter([0.7475], [0.93], s=14, marker="s", color=NEUTRAL_GRAY, transform=ax.transAxes, clip_on=False)
    ax.text(0.775, 0.93, "L2 sensitivity", transform=ax.transAxes, va="center", fontsize=6.0)

    rank_ax = ax.inset_axes([0.05, 0.22, 0.38, 0.49])
    shift_ax = ax.inset_axes([0.58, 0.22, 0.38, 0.49])

    metric_styles = {
        "real_shift_mean_abs": {"color": PRIMARY_GREEN, "marker": "o", "label": "Mean abs (primary)", "zorder": 3},
        "real_shift_L2": {"color": NEUTRAL_GRAY, "marker": "s", "label": "L2 sensitivity", "zorder": 2},
    }
    x_map = {"7d": 0, "13d": 1}
    for metric, style in metric_styles.items():
        sub = df.loc[df["truth_metric"].eq(metric)].sort_values("timepoint_order")
        xs = [x_map[v] for v in sub["timepoint"]]
        rank_ax.plot(xs, sub["aligned_spearman"], color=style["color"], marker=style["marker"], linewidth=1.2, markersize=4.2, label=style["label"], zorder=style["zorder"])
        shift_ax.errorbar(
            xs, sub["mean_shift_norm"], yerr=sub["mean_shift_sem_norm"],
            color=style["color"], marker=style["marker"], linewidth=1.2, markersize=4.2,
            capsize=2.0, capthick=0.7, elinewidth=0.8, label=style["label"], zorder=style["zorder"],
        )

    for sub_ax in (rank_ax, shift_ax):
        sub_ax.set_xlim(-0.25, 1.25)
        sub_ax.set_xticks([0, 1])
        sub_ax.set_xticklabels(["7d", "13d"])
        sub_ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
        clean_axes(sub_ax)

    rank_ax.set_ylim(0.35, 0.88)
    rank_ax.set_ylabel("Bridge rho", labelpad=2)
    rank_ax.set_title("Rank bridge weakens at 13d", loc="left", fontsize=7.0, fontweight="bold", pad=2)
    shift_ax.set_ylim(0.55, 1.15)
    shift_ax.set_ylabel("Mean shift (norm.)", labelpad=2)
    shift_ax.set_title("Perturbation magnitude increases at 13d", loc="left", fontsize=7.0, fontweight="bold", pad=2)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Square Replogle K562 essential joint grid scatter."""
    quadrant_colors = {
        "Q1_anchor": "#D55E00",          # red-orange, matching Fig 1 Q1
        "Q2_shift_excess": SKY_BLUE,
        "Q3_dep_excess": SKY_BLUE,
        "Q4_low_info": "#BDBDBD",
        "middle": "#E0E0E0",
    }
    quadrant_zorder = {
        "Q1_anchor": 5,
        "Q2_shift_excess": 3,
        "Q3_dep_excess": 3,
        "Q4_low_info": 2,
        "middle": 1,
    }
    quadrant_size = {
        "Q1_anchor": 14,
        "middle": 4,
    }

    # Background layer: middle band
    for quad, sub in df.groupby("quadrant"):
        if quad == "middle":
            ax.scatter(
                sub["shift_quantile"], sub["depmap_quantile"],
                c=quadrant_colors.get(quad, "#CCCCCC"),
                s=quadrant_size.get(quad, 6),
                edgecolors="none",
                alpha=0.5,
                zorder=quadrant_zorder.get(quad, 1),
            )

    # Foreground: Q1-Q4 quadrants
    foreground_quads = ["Q1_anchor", "Q2_shift_excess", "Q3_dep_excess", "Q4_low_info"]
    for quad in foreground_quads:
        sub = df.loc[df["quadrant"].eq(quad)]
        if sub.empty:
            continue
        ax.scatter(
            sub["shift_quantile"], sub["depmap_quantile"],
            c=quadrant_colors.get(quad, "#CCCCCC"),
            s=quadrant_size.get(quad, 8),
            edgecolors="white",
            linewidths=0.3,
            alpha=0.85,
            zorder=quadrant_zorder.get(quad, 3),
            label=quad.replace("_", " "),
        )

    # 25th/75th percentile lines
    for pct in [0.25, 0.75]:
        ax.axvline(pct, color="#888888", linewidth=0.6, linestyle="--", alpha=0.6)
        ax.axhline(pct, color="#888888", linewidth=0.6, linestyle="--", alpha=0.6)

    ax.set_xlabel("Perturbation shift (rank percentile)")
    ax.set_ylabel("CRISPR dependency (rank percentile)")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)

    # Annotations
    n = len(df)
    rho_val = 0.402
    ci_low, ci_high = 0.363, 0.439
    n_q1 = int((df["quadrant"] == "Q1_anchor").sum())

    ax.text(
        0.02, 0.96,
        f"Replogle K562 essential (day 7)\nn = {n} matched CRISPRi targets\nQ1 anchors = {n_q1}",
        transform=ax.transAxes, fontsize=6.2, va="top", ha="left",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.85),
    )
    ax.text(
        0.98, 0.06,
        f"aligned Spearman rho = {rho_val:.3f}\n95% CI [{ci_low:.3f}, {ci_high:.3f}]\nempirical p = 0.001",
        transform=ax.transAxes, fontsize=6.0, va="bottom", ha="right",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.85),
    )

    # Quadrant legend
    legend_elements = [
        Patch(facecolor=quadrant_colors["Q1_anchor"], edgecolor="white", label=f"Q1 anchor ({n_q1})"),
        Patch(facecolor=SKY_BLUE, edgecolor="white", label="Q2/Q3 excess"),
        Patch(facecolor="#BDBDBD", edgecolor="white", label="Q4 low info"),
        Patch(facecolor="#E0E0E0", label=f"middle ({int((df['quadrant'] == 'middle').sum())})"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", frameon=True, fontsize=5.6,
              framealpha=0.9, edgecolor="#DDDDDD", handlelength=1.0, borderpad=0.4)

    clean_axes(ax)
    ax.set_box_aspect(1)
    add_panel_heading(ax, "b", "Large-scale perturbation-fitness bridge confirmation", label_x=-0.08, title_x=0.02, y=1.035)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    return {
        "a": build_panel_a_source(root),
        "b": build_panel_b_source(root),
    }


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {"a": render_panel_a, "b": render_panel_b}[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "K562 temporal bridge-magnitude dissociation",
        "b": "Replogle K562 essential large-scale perturbation-fitness bridge",
    }[panel_id]


def write_panel(
    *,
    root: Path,
    panel_id: str,
    source_df: pd.DataFrame,
    render: Callable[[plt.Axes, pd.DataFrame], None],
    width: float = 7.0,
    height: float = 4.2,
) -> dict[str, Path]:
    pdir = ensure_dir(panel_dir(root))
    stem = f"edfig3_panel{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    output_paths = save_figure(fig, pdir / f"{stem}.png", pdir / f"{stem}.pdf")
    manifest_path = pdir / f"{stem}_manifest.json"
    write_panel_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        panel_id=f"ED3{panel_id}",
        panel_title=panel_title(panel_id),
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": output_paths[0], "pdf": output_paths[1], "manifest": manifest_path}


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> None:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / "edfig3_source_data.tsv")

    fig = plt.figure(figsize=(11.0, 9.4))
    gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.35, height_ratios=[1, 1.3])

    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, 0])
    # Right cell of bottom row left empty to keep panel b square

    render_panel_a(ax_a, sources["a"])
    render_panel_b(ax_b, sources["b"])

    output_paths = save_figure(fig, out / "edfig3.png", out / "edfig3.pdf")
    write_figure_manifest(
        manifest_path=out / "edfig3_panel_manifest.json",
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in PANEL_IDS],
        combined_source_data_path=combined_source_path,
        output_paths=output_paths,
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build Extended Data Fig. 3: K562 temporal + Replogle large-scale.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    apply_manuscript_style()
    root = repo_root()
    cleanup_generated(root)
    sources = build_sources(root)

    panel_outputs = {}
    # Panel a: temporal (wider)
    panel_outputs["a"] = write_panel(root=root, panel_id="a", source_df=sources["a"], render=render_panel_a, width=7.0, height=4.2)
    # Panel b: Replogle scatter (square)
    panel_outputs["b"] = write_panel(root=root, panel_id="b", source_df=sources["b"], render=render_panel_b, width=6.0, height=6.2)

    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
