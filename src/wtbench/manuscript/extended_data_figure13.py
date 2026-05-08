from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import spearmanr

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript._palette import (
    DIVIDER_GRAY,
    FIG5_DUMBBELL_CONNECTOR,
    FIG5_ENDPOINT_CRISPR,
    FIG5_ENDPOINT_RNAI,
    LIGHT_GRAY,
    MID_GRAY,
    NEUTRAL_GRAY,
    PRIMARY_GREEN,
    PRIMARY_GREEN_EDGE,
    PRIMARY_GREEN_FILL,
    SKY_BLUE,
    VERMILLION,
)
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes
from wtbench.truth_bridge import (
    DEPMAP_ALIGNMENT_DIRECTION,
    build_dataset_specs,
    load_config,
    load_depmap_endpoint,
    mean_vector,
    prepare_bridge_inputs,
    resolve_path,
    top_k_mean_abs,
)


FIGURE_ID = "extended_data_figure13"
FIGURE_TITLE = "Robustness of perturbation-fitness bridge metric selection"
SCRIPT_PATH = Path("scripts/manuscript/build_extended_data_figure13.py")
CLAIM_BOUNDARY = (
    "Top-n gene-subset analyses are sensitivity checks and are not used to select a post hoc optimum; "
    "the primary bridge metric remains full-transcriptome mean absolute shift versus CRISPR dependency."
)
PANEL_IDS = tuple("abcd")
CONTROL_SUBSAMPLE = Path("reports/truth_driven_bridge/sensitivity/control_subsample_summary.tsv")

CONFIG_PATH = Path("configs/truth_driven_bridge_hcc38_hcc1143_v1.json")
HCC38_CORR = Path("reports/truth_driven_bridge/HCC38/correlation_summary.tsv")
HCC1143_CORR = Path("reports/truth_driven_bridge/HCC1143/correlation_summary.tsv")
RNAI_ENDPOINT = Path("reports/truth_driven_bridge/hcc38_hcc1143_rnai_endpoint_consistency/endpoint_consistency_summary.tsv")
K562_RNAI_ENDPOINT = Path("reports/truth_driven_bridge/k562_rnai_endpoint_consistency/endpoint_consistency_summary.tsv")

TOP_N_VALUES = (100, 500, 1000, 2000, "all")
CURVE_METRICS = (
    "real_shift_mean_abs",
    "real_shift_L2",
    "real_DEG_burden",
)
SUMMARY_METRICS = (
    "real_shift_mean_abs",
    "real_shift_L2",
    "real_DEG_burden",
    "real_shift_top20_mean",
    "real_shift_top50_mean",
    "real_shift_top100_mean",
    "real_Edistance",
)
METRIC_LABELS = {
    "real_shift_mean_abs": "Mean abs",
    "real_shift_L2": "L2",
    "real_shift_top20_mean": "Top 20",
    "real_shift_top50_mean": "Top 50",
    "real_shift_top100_mean": "Top 100",
    "real_Edistance": "E-distance",
    "real_DEG_burden": "DEG burden",
}
RANKING_LABELS = {
    "control_expression": "Genes ranked by control expression",
    "perturbation_response": "Genes ranked by perturbation response",
}
CURVE_COLORS = {
    "real_shift_mean_abs": PRIMARY_GREEN,
    "real_shift_L2": SKY_BLUE,
    "real_DEG_burden": VERMILLION,
    "real_shift_top20_mean": "#6E6E6E",
    "real_shift_top50_mean": "#8A8A8A",
    "real_shift_top100_mean": "#A3A3A3",
    "real_Edistance": MID_GRAY,
}
ROBUSTNESS_CMAP = LinearSegmentedColormap.from_list(
    "metric_robustness_green",
    [LIGHT_GRAY, PRIMARY_GREEN_FILL, PRIMARY_GREEN],
)


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_extended_data_v1/edfig13_metric_robustness"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / p for p in [CONFIG_PATH, HCC38_CORR, HCC1143_CORR, RNAI_ENDPOINT, K562_RNAI_ENDPOINT, CONTROL_SUBSAMPLE]]


def cleanup_generated(root: Path) -> None:
    out = output_dir(root)
    for path in panel_dir(root).glob("edfig13_panel*"):
        path.unlink()
    for suffix in (".png", ".pdf", "_source_data.tsv", "_panel_manifest.json"):
        path = out / f"edfig13{suffix}"
        if path.exists():
            path.unlink()


def aligned_spearman(truth_values: pd.Series, endpoint_values: pd.Series, endpoint: str) -> float:
    subset = pd.DataFrame({"truth": truth_values, "endpoint": endpoint_values}).dropna()
    if len(subset) < 3 or subset["truth"].nunique() < 2 or subset["endpoint"].nunique() < 2:
        return np.nan
    rho = float(spearmanr(subset["truth"], subset["endpoint"]).statistic)
    return float(DEPMAP_ALIGNMENT_DIRECTION[endpoint] * rho)


def metric_from_delta(delta: np.ndarray, metric: str) -> float:
    if metric == "real_shift_mean_abs":
        return float(np.abs(delta).mean())
    if metric == "real_shift_L2":
        return float(np.linalg.norm(delta))
    if metric == "real_shift_top20_mean":
        return top_k_mean_abs(delta, 20)
    if metric == "real_shift_top50_mean":
        return top_k_mean_abs(delta, 50)
    if metric == "real_DEG_burden":
        return float(np.count_nonzero(np.abs(delta) >= 0.25))
    raise ValueError(f"Unsupported top-n metric: {metric}")


def target_delta_table(root: Path, config: dict, spec, depmap_effect: pd.DataFrame, depmap_dependency: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    normalized, _, calls, _, effect_series, dependency_series = prepare_bridge_inputs(spec, config, depmap_effect, depmap_dependency)
    filters = config["filters"]
    min_target_cells = int(filters["min_target_cells"])
    control_mask = calls["is_control"].to_numpy(dtype=bool)
    control_positions = np.flatnonzero(control_mask)
    control_mean = mean_vector(normalized[control_positions])

    rows: list[dict[str, object]] = []
    deltas: list[np.ndarray] = []
    for target_gene, target_calls in calls.loc[~calls["is_control"]].groupby("target_gene", sort=True):
        if len(target_calls) < min_target_cells:
            continue
        target_mean = mean_vector(normalized[target_calls.index.to_numpy()])
        delta = target_mean - control_mean
        deltas.append(delta)
        rows.append(
            {
                "cell_line": spec.cell_line,
                "target_gene": str(target_gene),
                "n_cells_target": int(len(target_calls)),
                "depmap_gene_effect": float(effect_series.get(target_gene, np.nan)),
                "depmap_gene_dependency": float(dependency_series.get(target_gene, np.nan)),
            }
        )
    if not rows:
        raise RuntimeError(f"{spec.cell_line} produced no eligible target deltas.")
    return control_mean, pd.DataFrame(rows).assign(delta=list(deltas))


def topn_rows_for_dataset(root: Path, config: dict, spec, depmap_effect: pd.DataFrame, depmap_dependency: pd.DataFrame) -> list[dict[str, object]]:
    control_mean, target_table = target_delta_table(root, config, spec, depmap_effect, depmap_dependency)
    delta_matrix = np.vstack(target_table["delta"].to_list())
    response_rank = np.abs(delta_matrix).mean(axis=0)
    rankings = {
        "control_expression": np.argsort(-control_mean),
        "perturbation_response": np.argsort(-response_rank),
    }
    rows: list[dict[str, object]] = []
    for ranking_name, order in rankings.items():
        for top_n in TOP_N_VALUES:
            if top_n == "all":
                gene_idx = order
                n_genes = int(len(order))
                top_n_label = "all"
            else:
                n = int(top_n)
                gene_idx = order[: min(n, len(order))]
                n_genes = int(len(gene_idx))
                top_n_label = str(top_n)
            values = pd.DataFrame(
                {
                    "target_gene": target_table["target_gene"],
                    "depmap_gene_dependency": target_table["depmap_gene_dependency"],
                }
            )
            for metric in CURVE_METRICS:
                values[metric] = [metric_from_delta(delta[gene_idx], metric) for delta in target_table["delta"]]
                rows.append(
                    {
                        "summary_kind": "topn_curve",
                        "cell_line": spec.cell_line,
                        "ranking": ranking_name,
                        "top_n": top_n_label,
                        "n_genes": n_genes,
                        "truth_metric": metric,
                        "depmap_endpoint": "depmap_gene_dependency",
                        "aligned_spearman": aligned_spearman(values[metric], values["depmap_gene_dependency"], "depmap_gene_dependency"),
                        "n_targets": int(values[["depmap_gene_dependency", metric]].dropna().shape[0]),
                    }
                )
    return rows


def build_topn_source(root: Path) -> pd.DataFrame:
    config = load_config(root / CONFIG_PATH)
    specs = build_dataset_specs(config)
    depmap_effect = load_depmap_endpoint(resolve_path(config["depmap"]["gene_effect_path"]))
    depmap_dependency = load_depmap_endpoint(resolve_path(config["depmap"]["gene_dependency_path"]))
    rows: list[dict[str, object]] = []
    for spec in specs:
        rows.extend(topn_rows_for_dataset(root, config, spec, depmap_effect, depmap_dependency))
    return pd.DataFrame(rows)


def build_summary_source(root: Path) -> pd.DataFrame:
    crispr = pd.concat(
        [
            pd.read_csv(root / HCC38_CORR, sep="\t"),
            pd.read_csv(root / HCC1143_CORR, sep="\t"),
        ],
        ignore_index=True,
    )
    crispr = crispr.loc[crispr["truth_metric"].isin(SUMMARY_METRICS)].copy()
    crispr["summary_kind"] = "crispr_metric_endpoint"
    crispr["platform_pair"] = "crispr"
    crispr["timepoint"] = crispr["cell_line"]

    endpoint = pd.concat(
        [
            pd.read_csv(root / RNAI_ENDPOINT, sep="\t").assign(context_role="primary_hcc"),
            pd.read_csv(root / K562_RNAI_ENDPOINT, sep="\t").assign(context_role="supplementary_k562"),
        ],
        ignore_index=True,
    )
    endpoint = endpoint.loc[
        endpoint["summary_kind"].eq("truth_endpoint_bridge")
        & endpoint["timepoint"].isin(["HCC38", "HCC1143", "7d", "13d"])
        & endpoint["truth_metric"].isin(["real_shift_mean_abs", "real_shift_L2"])
        & endpoint["depmap_endpoint"].eq("depmap_gene_dependency")
        & endpoint["platform_pair"].isin(["crispr", "rnai"])
    ].copy()
    endpoint["cell_line"] = endpoint["timepoint"]
    endpoint["spearman_rho_aligned"] = endpoint["spearman"]
    endpoint["n_targets"] = endpoint["n_shared_targets"]
    endpoint["summary_kind"] = "endpoint_sensitivity"

    keep_cols = [
        "summary_kind",
        "cell_line",
        "timepoint",
        "truth_metric",
        "depmap_endpoint",
        "platform_pair",
        "context_role",
        "n_targets",
        "spearman_rho_aligned",
    ]
    crispr["context_role"] = "primary_hcc"
    return pd.concat([crispr[keep_cols], endpoint[keep_cols]], ignore_index=True, sort=False)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    summary_source = build_summary_source(root)
    control_source = pd.read_csv(root / CONTROL_SUBSAMPLE, sep="\t")
    control_source = control_source.loc[
        control_source["truth_metric"].isin(SUMMARY_METRICS)
        & control_source["depmap_endpoint"].eq("depmap_gene_dependency")
    ].copy()
    return {
        "a": build_topn_source(root),
        "b": summary_source.loc[summary_source["summary_kind"].eq("crispr_metric_endpoint")].copy(),
        "c": summary_source.loc[summary_source["summary_kind"].eq("endpoint_sensitivity")].copy(),
        "d": control_source,
    }


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    # panel letter drawn by PIL
    ax.text(
        0.035,
        0.96,
        "Top-n gene-subset sensitivity",
        fontsize=8.4,
        fontweight="bold",
        va="bottom",
        transform=ax.transAxes,
    )
    axes = [
        ax.inset_axes([0.06, 0.12, 0.41, 0.70]),
        ax.inset_axes([0.55, 0.12, 0.41, 0.70]),
    ]
    for inset, ranking in zip(axes, RANKING_LABELS):
        sub = df.loc[df["ranking"].eq(ranking)].copy()
        summary = (
            sub.groupby(["truth_metric", "top_n", "n_genes"], as_index=False)
            .agg(mean_rho=("aligned_spearman", "mean"), min_rho=("aligned_spearman", "min"), max_rho=("aligned_spearman", "max"))
            .sort_values("n_genes")
        )
        for metric in CURVE_METRICS:
            plot = summary.loc[summary["truth_metric"].eq(metric)].sort_values("n_genes")
            x = plot["n_genes"].to_numpy(dtype=float)
            y = plot["mean_rho"].to_numpy(dtype=float)
            inset.fill_between(x, plot["min_rho"], plot["max_rho"], color=CURVE_COLORS[metric], alpha=0.12, linewidth=0)
            inset.plot(x, y, marker="o", color=CURVE_COLORS[metric], label=METRIC_LABELS[metric], linewidth=1.1)
        inset.set_xscale("log")
        inset.set_ylim(0.45, 0.85)
        inset.set_xticks([100, 500, 1000, 2000, float(summary["n_genes"].max())])
        inset.set_xticklabels(["100", "500", "1k", "2k", "all"], rotation=0)
        inset.set_title(RANKING_LABELS[ranking], loc="left", fontsize=7.0, fontweight="normal")
        inset.set_xlabel("Top n genes")
        if ranking == "control_expression":
            inset.set_ylabel("Aligned Spearman ρ")
        clean_axes(inset)
        inset.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    axes[1].legend(loc="lower right", fontsize=5.8, frameon=False)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    # b label drawn by PIL
    ax.text(
        0.04,
        0.93,
        "Metric x CRISPR endpoint",
        fontsize=8.0,
        fontweight="bold",
        va="bottom",
        transform=ax.transAxes,
    )
    heat_ax = ax.inset_axes([0.12, 0.17, 0.68, 0.70])

    crispr = df.loc[df["summary_kind"].eq("crispr_metric_endpoint")].copy()
    crispr_summary = crispr.groupby(["truth_metric", "depmap_endpoint"], as_index=False)["spearman_rho_aligned"].mean()
    rows = list(SUMMARY_METRICS)
    cols = ["depmap_gene_dependency", "depmap_gene_effect"]
    matrix = np.array(
        [
            [
                float(
                    crispr_summary.loc[
                        crispr_summary["truth_metric"].eq(row) & crispr_summary["depmap_endpoint"].eq(col),
                        "spearman_rho_aligned",
                    ].iloc[0]
                )
                for col in cols
            ]
            for row in rows
        ]
    )
    im = heat_ax.imshow(matrix, vmin=0.45, vmax=0.82, cmap=ROBUSTNESS_CMAP, aspect="auto")
    heat_ax.set_xticks(range(len(cols)))
    heat_ax.set_xticklabels(["CRISPR\ndependency", "CRISPR\ngene effect"])
    heat_ax.set_yticks(range(len(rows)))
    heat_ax.set_yticklabels([METRIC_LABELS[r] for r in rows])
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            heat_ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", fontsize=6.0, color="#1F1F1F")
    heat_ax.add_patch(plt.Rectangle((-0.5, -0.5), 1, 1, fill=False, edgecolor=PRIMARY_GREEN_EDGE, linewidth=1.2))
    heat_ax.tick_params(length=0)
    for spine in heat_ax.spines.values():
        spine.set_visible(False)
    cbar = plt.colorbar(im, ax=heat_ax, fraction=0.046, pad=0.03)
    cbar.ax.tick_params(labelsize=5.5, length=2)


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    # c label drawn by PIL
    ax.text(
        0.06,
        0.93,
        "CRISPR vs RNAi endpoint gap",
        fontsize=8.0,
        fontweight="bold",
        va="bottom",
        transform=ax.transAxes,
    )
    endpoint_ax = ax.inset_axes([0.13, 0.17, 0.60, 0.70])

    endpoint_df = df.loc[
        df["summary_kind"].eq("endpoint_sensitivity")
        & df["truth_metric"].isin(["real_shift_mean_abs", "real_shift_L2"])
        & df["platform_pair"].isin(["crispr", "rnai"])
    ].copy()
    endpoint_df["endpoint_label"] = endpoint_df["platform_pair"].map({"crispr": "CRISPR", "rnai": "RNAi"})
    endpoint_df = endpoint_df.rename(columns={"spearman_rho_aligned": "rho"})
    colors = {"CRISPR": FIG5_ENDPOINT_CRISPR, "RNAi": FIG5_ENDPOINT_RNAI}
    context_order = ["HCC38", "HCC1143", "7d", "13d"]
    context_labels = ["HCC38", "HCC1143", "K562 7d", "K562 13d"]
    metric_labels = {"real_shift_mean_abs": "Mean abs", "real_shift_L2": "L2"}
    y_ticks: list[float] = []
    y_labels: list[str] = []
    for metric_i, metric in enumerate(["real_shift_mean_abs", "real_shift_L2"]):
        sub_metric = endpoint_df.loc[endpoint_df["truth_metric"].eq(metric)].copy()
        base_y = metric_i * 5
        endpoint_ax.text(
            0.16,
            base_y - 0.55,
            metric_labels[metric],
            fontsize=6.4,
            fontweight="bold",
            va="center",
            ha="left",
        )
        for context_i, context in enumerate(context_order):
            y = base_y + context_i
            sub = sub_metric.loc[sub_metric["cell_line"].eq(context)].set_index("endpoint_label")
            if {"CRISPR", "RNAi"}.issubset(sub.index):
                rnai = float(sub.loc["RNAi", "rho"])
                crispr = float(sub.loc["CRISPR", "rho"])
                endpoint_ax.plot([rnai, crispr], [y, y], color=FIG5_DUMBBELL_CONNECTOR, linewidth=0.9, zorder=1)
                marker = "o" if context in {"HCC38", "HCC1143"} else "^"
                endpoint_ax.scatter([rnai], [y], color=colors["RNAi"], marker=marker, s=18, alpha=0.9, zorder=2)
                endpoint_ax.scatter([crispr], [y], color=colors["CRISPR"], marker=marker, s=18, alpha=0.95, zorder=3)
            y_ticks.append(y)
            y_labels.append(context_labels[context_i])
    endpoint_ax.axhline(4.0, color=DIVIDER_GRAY, linewidth=0.8)
    endpoint_ax.set_xlim(0.15, 0.85)
    endpoint_ax.set_ylim(8.6, -0.9)
    endpoint_ax.set_yticks(y_ticks)
    endpoint_ax.set_yticklabels(y_labels)
    endpoint_ax.set_xlabel("Aligned Spearman ρ")
    legend_x = 0.80
    ax.scatter([legend_x], [0.39], color=colors["CRISPR"], s=16, transform=ax.transAxes, clip_on=False)
    ax.text(legend_x + 0.035, 0.39, "CRISPR", color=colors["CRISPR"], fontsize=5.6, va="center", transform=ax.transAxes)
    ax.scatter([legend_x], [0.31], color=colors["RNAi"], s=16, transform=ax.transAxes, clip_on=False)
    ax.text(legend_x + 0.035, 0.31, "RNAi", color=colors["RNAi"], fontsize=5.6, va="center", transform=ax.transAxes)
    ax.scatter([legend_x], [0.23], color=NEUTRAL_GRAY, marker="o", s=16, transform=ax.transAxes, clip_on=False)
    ax.text(legend_x + 0.035, 0.23, "HCC", color=NEUTRAL_GRAY, fontsize=5.6, va="center", transform=ax.transAxes)
    ax.scatter([legend_x], [0.15], color=NEUTRAL_GRAY, marker="^", s=16, transform=ax.transAxes, clip_on=False)
    ax.text(legend_x + 0.035, 0.15, "K562", color=NEUTRAL_GRAY, fontsize=5.6, va="center", transform=ax.transAxes)
    clean_axes(endpoint_ax)
    endpoint_ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    # d label drawn by PIL
    ax.text(
        0.035,
        0.94,
        "Control-subsampling robustness",
        fontsize=8.0,
        fontweight="bold",
        va="bottom",
        transform=ax.transAxes,
    )
    axes = [
        ax.inset_axes([0.10, 0.16, 0.38, 0.62]),
        ax.inset_axes([0.56, 0.16, 0.38, 0.62]),
    ]
    rows = list(SUMMARY_METRICS)
    for inset, cell_line in zip(axes, ["HCC38", "HCC1143"]):
        sub = (
            df.loc[df["cell_line"].eq(cell_line)]
            .set_index("truth_metric")
            .reindex(rows)
            .reset_index()
        )
        y = np.arange(len(rows))
        for yi, row in enumerate(sub.itertuples()):
            color = CURVE_COLORS[row.truth_metric]
            inset.plot(
                [row.spearman_aligned_q025, row.spearman_aligned_q975],
                [yi, yi],
                color=color,
                linewidth=1.3,
                solid_capstyle="round",
                alpha=0.95,
                zorder=1,
            )
            inset.scatter(
                [row.spearman_aligned_mean],
                [yi],
                color=color,
                s=18,
                zorder=2,
            )
        inset.set_xlim(0.48, 0.81)
        inset.set_ylim(len(rows) - 0.5, -0.5)
        inset.set_yticks(y)
        inset.set_yticklabels([METRIC_LABELS[r] for r in rows] if cell_line == "HCC38" else [])
        inset.set_title(cell_line, loc="left", fontsize=7.0, fontweight="normal")
        inset.set_xlabel("Aligned Spearman ρ")
        clean_axes(inset)
        inset.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    axes[0].set_ylabel("Truth metric")


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {"a": render_panel_a, "b": render_panel_b, "c": render_panel_c, "d": render_panel_d}[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Top-n gene-subset sensitivity",
        "b": "Metric and CRISPR endpoint robustness",
        "c": "CRISPR versus RNAi endpoint sensitivity",
        "d": "Control-subsampling robustness",
    }[panel_id]


def write_panel(
    *,
    root: Path,
    panel_id: str,
    source_df: pd.DataFrame,
    render: Callable[[plt.Axes, pd.DataFrame], None],
    width: float = 6.9,
    height: float = 3.0,
) -> dict[str, Path]:
    pdir = ensure_dir(panel_dir(root))
    stem = f"edfig13_panel{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    output_paths = save_figure(fig, pdir / f"{stem}.png", pdir / f"{stem}.pdf", max_width=None)
    manifest_path = pdir / f"{stem}_manifest.json"
    write_panel_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        panel_id=f"ED13{panel_id}",
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
    combined_source_path = write_tsv(combined_source, out / "edfig13_source_data.tsv")
    fig = plt.figure(figsize=(7.3, 7.15))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.15, 1.0, 0.95], hspace=0.22, wspace=0.18)
    axes = {
        "a": fig.add_subplot(gs[0, :]),
        "b": fig.add_subplot(gs[1, 0]),
        "c": fig.add_subplot(gs[1, 1]),
        "d": fig.add_subplot(gs[2, :]),
    }
    for panel_id in PANEL_IDS:
        render_panel_by_id(panel_id)(axes[panel_id], sources[panel_id])
    output_paths = save_figure(fig, out / "edfig13.png", out / "edfig13.pdf", max_width=None)
    write_figure_manifest(
        manifest_path=out / "edfig13_panel_manifest.json",
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
    parser = argparse.ArgumentParser(description="Build Extended Data Fig. 13 metric robustness audit.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    apply_manuscript_style()
    root = repo_root()
    cleanup_generated(root)
    sources = build_sources(root)
    panel_outputs = {
        panel_id: write_panel(root=root, panel_id=panel_id, source_df=sources[panel_id], render=render_panel_by_id(panel_id))
        for panel_id in PANEL_IDS
    }
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
