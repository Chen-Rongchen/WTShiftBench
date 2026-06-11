from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.truth_bridge import DEPMAP_ALIGNMENT_DIRECTION
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
PANEL_IDS = ("a", "b", "c")

# Panel a data (K562 temporal)
TEMPORAL_BRIDGE = Path("reports/truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_bridge_summary.tsv")
TEMPORAL_STRUCTURE = Path("reports/truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_structure_summary.tsv")
TEMP_PANEL_CALLS = Path("reports/truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_panel_calls.tsv")
TEMP_7D_EVIDENCE = Path("reports/truth_driven_bridge/dixit_axis_compression_gse90063_7d/dixit_evidence_tier_summary.tsv")
TEMP_13D_EVIDENCE = Path("reports/truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_evidence_tier_summary.tsv")
TARGET_7D = Path("data/processed/truth_driven_bridge_gse90063_7d/dixit_2016_k562_tf_7d_gse90063/target_level_bridge_table.tsv.gz")
TARGET_13D = Path("data/processed/truth_driven_bridge_gse90063_13d/dixit_2016_k562_tf_13d_gse90063/target_level_bridge_table.tsv.gz")

# Panel b data (Replogle joint grid)
REPLOGLE_JOINT_GRID = Path("reports/manuscript_extended_data_v1/edfig3_k562_replogle_joint_grid/replogle_k562_essential_joint_grid.tsv")

BRIDGE_TRUTH_METRIC = "real_shift_mean_abs"
BRIDGE_DEPMAP_ENDPOINT = "depmap_gene_dependency"
REPLOGLE_PERM_ITERATIONS = 1000
REPLOGLE_PERM_SEED = 42

PRIMARY_GREEN = COLORS["primary_qualified"]  # "#4B8A5A"
NEUTRAL_GRAY = "#8E8E8E"
SKY_BLUE = COLORS["accent_blue"]
VERMILLION = COLORS["boundary"]


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


def compute_replogle_bridge_summary(target_table: pd.DataFrame) -> dict[str, Any]:
    """Aligned Spearman on raw truth × DepMap columns, Fisher-z 95% CI, and target↔endpoint shuffle null.

    Matches the closed permutation definition in ``scripts/pipeline/bridge_rho_permutation_null.py``
    (shuffle DepMap endpoint assignments within this table; two-sided p vs |ρ_raw|).
    """
    sub = target_table[[BRIDGE_TRUTH_METRIC, BRIDGE_DEPMAP_ENDPOINT]].dropna()
    if len(sub) < 3:
        raise RuntimeError("Replogle bridge summary requires ≥3 targets with non-null truth and dependency.")
    truth = sub[BRIDGE_TRUTH_METRIC].to_numpy(dtype=float)
    dep = sub[BRIDGE_DEPMAP_ENDPOINT].to_numpy(dtype=float)
    rho_raw = float(spearmanr(truth, dep).statistic)
    direction = float(DEPMAP_ALIGNMENT_DIRECTION[BRIDGE_DEPMAP_ENDPOINT])
    rho_aligned = float(direction * rho_raw)

    n = int(len(sub))
    rho_c = float(np.clip(rho_aligned, -0.999999, 0.999999))
    z = np.arctanh(rho_c)
    se_z = 1.0 / np.sqrt(max(n - 3.0, 1.0))
    ci_lo = float(np.tanh(z - 1.96 * se_z))
    ci_hi = float(np.tanh(z + 1.96 * se_z))

    rng = np.random.default_rng(REPLOGLE_PERM_SEED)
    null = np.empty(REPLOGLE_PERM_ITERATIONS, dtype=float)
    dep_shuffled = dep.copy()
    for i in range(REPLOGLE_PERM_ITERATIONS):
        rng.shuffle(dep_shuffled)
        null[i] = float(spearmanr(truth, dep_shuffled).statistic)
    empirical_p = float(((np.abs(null) >= abs(rho_raw)).sum() + 1) / (REPLOGLE_PERM_ITERATIONS + 1))

    return {
        "bridge_truth_metric": BRIDGE_TRUTH_METRIC,
        "bridge_depmap_endpoint": BRIDGE_DEPMAP_ENDPOINT,
        "bridge_n_targets": n,
        "bridge_spearman_rho_aligned": rho_aligned,
        "bridge_ci_lo_fisher95": ci_lo,
        "bridge_ci_hi_fisher95": ci_hi,
        "bridge_ci_method": "fisher_z_transform",
        "bridge_empirical_p_two_sided_shuffle": empirical_p,
        "bridge_perm_iterations": REPLOGLE_PERM_ITERATIONS,
        "bridge_perm_seed": REPLOGLE_PERM_SEED,
        "bridge_null_type": "target_to_depmap_permutation_within_table",
    }


def build_panel_b_source(root: Path) -> pd.DataFrame:
    raw = pd.read_csv(root / REPLOGLE_JOINT_GRID, sep="\t")
    raw["shift_quantile"] = raw["real_shift_mean_abs"].rank(pct=True)
    raw["depmap_quantile"] = raw["depmap_gene_dependency"].rank(pct=True)
    summary_dict = compute_replogle_bridge_summary(raw)

    scatter = raw.copy()
    for k in summary_dict:
        scatter[k] = np.nan
    scatter["record_type"] = "joint_grid_target"

    blank = {c: np.nan for c in scatter.columns}
    for k, v in summary_dict.items():
        blank[k] = v
    blank["record_type"] = "replogle_bridge_correlation_summary"
    summary_df = pd.DataFrame([blank]).reindex(columns=scatter.columns)

    return pd.concat([scatter, summary_df], ignore_index=True)


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    add_panel_heading(ax, "", "Temporal bridge-magnitude dissociation", label_x=-0.025, title_x=0.035, y=1.015)

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
    rank_ax.set_ylabel(r"Bridge Spearman $\rho$", labelpad=2)
    rank_ax.set_title("Rank bridge weakens at 13d", loc="left", fontsize=7.0, fontweight="bold", pad=2)
    shift_ax.set_ylim(0.55, 1.15)
    shift_ax.set_ylabel("Mean shift (norm.)", labelpad=2)
    shift_ax.set_title("Perturbation magnitude increases at 13d", loc="left", fontsize=7.0, fontweight="bold", pad=2)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Square Replogle K562 essential joint grid scatter."""
    plot_df = df.loc[df["record_type"].eq("joint_grid_target")].copy()
    summ = df.loc[df["record_type"].eq("replogle_bridge_correlation_summary")]
    if summ.empty:
        raise RuntimeError("Panel b source is missing replogle_bridge_correlation_summary row.")
    summ = summ.iloc[0]

    quadrant_colors = {
        "Q1_anchor": PRIMARY_GREEN,
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
    for quad, sub in plot_df.groupby("quadrant"):
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
        sub = plot_df.loc[plot_df["quadrant"].eq(quad)]
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

    # Stats and legend placed in the right gutter (between panels b and c)
    n = int(summ["bridge_n_targets"])
    rho_val = float(summ["bridge_spearman_rho_aligned"])
    ci_low = float(summ["bridge_ci_lo_fisher95"])
    ci_high = float(summ["bridge_ci_hi_fisher95"])
    p_perm = float(summ["bridge_empirical_p_two_sided_shuffle"])
    n_q1 = int((plot_df["quadrant"] == "Q1_anchor").sum())
    n_mid = int((plot_df["quadrant"] == "middle").sum())

    # Rho stats — right of scatter, clipped outside axes
    ax.text(
        1.06, 0.78,
        f"Spearman $\\rho$ = {rho_val:.3f}\n95% CI {ci_low:.3f}\u2013{ci_high:.3f}\nempirical p = {p_perm:.3g}\nn={n}",
        transform=ax.transAxes, fontsize=5.8, va="top", ha="left", color="#333333", clip_on=False,
    )

    # Quadrant swatches — right of scatter
    legend_spec = [
        ("Q1 anchor", n_q1, quadrant_colors["Q1_anchor"]),
        ("Q2/Q3 excess", int((plot_df["quadrant"].isin(["Q2_shift_excess", "Q3_dep_excess"])).sum()), SKY_BLUE),
        ("Q4 low info", int((plot_df["quadrant"] == "Q4_low_info").sum()), "#BDBDBD"),
        ("middle", n_mid, "#E0E0E0"),
    ]
    for i, (label, count, color) in enumerate(legend_spec):
        y = 0.40 - i * 0.07
        ax.add_patch(
            plt.Rectangle((1.06, y), 0.03, 0.04, transform=ax.transAxes,
                          facecolor=color, edgecolor="white", linewidth=0.3, clip_on=False))
        ax.text(1.105, y + 0.02, f"{label} ({count})", transform=ax.transAxes,
                fontsize=5.2, va="center", ha="left", color="#333333", clip_on=False)

    clean_axes(ax)
    ax.set_box_aspect(1)
    add_panel_heading(ax, "", "Large-scale bridge-form support", label_x=-0.08, title_x=0.02, y=1.035)


def build_panel_c_source(root: Path) -> pd.DataFrame:
    ""r"Evidence-tier checklist; numeric $\rho$ row is taken from the same temporal bridge table as panel a."""
    bridge = pd.read_csv(root / TEMPORAL_BRIDGE, sep="\t")
    primary = bridge.loc[
        bridge["truth_metric"].eq(BRIDGE_TRUTH_METRIC)
        & bridge["depmap_endpoint"].eq(BRIDGE_DEPMAP_ENDPOINT)
    ].set_index("timepoint")
    rho_7d = float(primary.loc["7d", "aligned_spearman"])
    rho_13d = float(primary.loc["13d", "aligned_spearman"])

    return pd.DataFrame(
        [
            {
                "evidence_item": r"Bridge Spearman $\rho$ above null",
                "tier": "A1",
                "status": "yes",
                "note": rf"$\rho$ = {rho_7d:.3f} / {rho_13d:.3f}",
            },
            {
                "evidence_item": "Joint grid defined",
                "tier": "",
                "status": "yes",
                "note": "25/75 grid applied",
            },
            {
                "evidence_item": "Q1 region present",
                "tier": "",
                "status": "yes",
                "note": "quadrant observed",
            },
            {
                "evidence_item": "Backbone / shift-excess structure",
                "tier": "A0",
                "status": "yes",
                "note": "matches primary",
            },
            {
                "evidence_item": "Content-level replication",
                "tier": "B",
                "status": "no",
                "note": "composition differs",
            },
            {
                "evidence_item": "Assigned tier",
                "tier": "",
                "status": "A0/A1 supported; B not supported",
                "note": "",
            },
        ]
    )


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    """K562 evidence-tier checklist — compact Fig 2f claim matrix style."""
    ax.set_axis_off()

    LIGHT_GRAY = "#F0F0F0"
    DIVIDER_GRAY = "#CCCCCC"
    DARK_TEXT = "#1F1F1F"
    GREEN = COLORS["primary_qualified"]
    OCHRE = COLORS["boundary"]
    GREEN_FILL = COLORS["pale_green"]

    rows = list(df[["evidence_item", "tier", "status", "note"]].itertuples(index=False, name=None))

    # Header bar (Fig 2f style)
    ax.add_patch(
        plt.Rectangle((0.005, 0.87), 0.99, 0.08, transform=ax.transAxes,
                      facecolor=LIGHT_GRAY, edgecolor="none", zorder=0))
    headers = [("Evidence item", 0.02), ("Tier", 0.42), ("Status", 0.54), ("Note", 0.72)]
    for text, x in headers:
        ax.text(x, 0.91, text, fontsize=7.0, fontweight="bold", color=DARK_TEXT, transform=ax.transAxes)
    ax.plot([0.01, 0.99], [0.87, 0.87], color=DIVIDER_GRAY, linewidth=0.7, transform=ax.transAxes)

    row_gap = 0.07
    for i, (item, supports, status, note) in enumerate(rows):
        y = 0.79 - i * row_gap
        is_yes = status == "yes"
        is_tier = "A0/A1" in status and "supported" in status

        if is_tier:
            ax.add_patch(
                plt.Rectangle((0.005, y - row_gap * 0.44), 0.99, row_gap * 0.86,
                              transform=ax.transAxes, facecolor=GREEN_FILL, edgecolor="none", zorder=0))

        fw = "bold" if is_tier else "normal"
        fs = 7.2 if is_tier else 6.5
        ax.text(0.02, y, item, fontsize=fs, fontweight=fw,
                color=GREEN if is_tier else DARK_TEXT, transform=ax.transAxes, va="center")

        if supports:
            ax.text(0.42, y, supports, fontsize=6.5, va="center", fontweight="bold",
                    color="#888888", transform=ax.transAxes)

        chip_color = GREEN if (is_yes or is_tier) else OCHRE
        ax.add_patch(
            plt.Rectangle((0.54, y - 0.022), 0.022, 0.044, transform=ax.transAxes,
                          facecolor=chip_color, edgecolor="none"))
        status_text = "yes" if is_yes else "no"
        if is_tier:
            status_text = "A0/A1, not B"
        ax.text(0.57, y, status_text, fontsize=6.5 if is_tier else 6.0, va="center",
                fontweight="bold", color=chip_color, transform=ax.transAxes)

        if note:
            ax.text(0.72, y, note, fontsize=5.2, va="center", ha="left",
                    color="#999999", transform=ax.transAxes)

    add_panel_heading(ax, "", "K562 evidence-tier checklist", label_x=-0.08, title_x=0.02, y=1.035)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    return {
        "a": build_panel_a_source(root),
        "b": build_panel_b_source(root),
        "c": build_panel_c_source(root),
    }


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {"a": render_panel_a, "b": render_panel_b, "c": render_panel_c}[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "K562 temporal bridge-magnitude dissociation",
        "b": "Replogle K562 essential large-scale perturbation-fitness bridge",
        "c": "K562 evidence-tier checklist",
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

    fig = plt.figure(figsize=(11.0, 9.0))
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.50, height_ratios=[1, 1.3])

    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1])

    render_panel_a(ax_a, sources["a"])
    render_panel_b(ax_b, sources["b"])
    render_panel_c(ax_c, sources["c"])

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
    # Panel c: evidence-tier checklist
    panel_outputs["c"] = write_panel(root=root, panel_id="c", source_df=sources["c"], render=render_panel_c, width=5.0, height=6.2)

    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
