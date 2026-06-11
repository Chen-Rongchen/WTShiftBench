from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.colors import LinearSegmentedColormap, Normalize

from wtbench.figures.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.figures.hash_manifest import sha256_file, write_figure_manifest, write_panel_manifest
from wtbench.figures.manuscript_style import (
    COLORS,
    apply_manuscript_style,
    clean_axes,
    finalize_manuscript_figure,
    model_color,
    muted_diverging_cmap,
    short_model_label,
)


FIGURE_ID = "figure3"
FIGURE_TITLE = "Model-generated shifts reveal endpoint recovery and output homogenization"
SCRIPT_PATH = Path("scripts/figures/build_figure3.py")
CLAIM_BOUNDARY = (
    "WTShiftBench audits model-generated perturbation shifts for recovery of a "
    "fixed DepMap-aligned endpoint structure. It does not evaluate models as "
    "direct DepMap, essentiality, viability, or causal-fitness predictors."
)

ROOT_SOURCE = Path("reports/model_endpoint_recovery/source_data")
METRICS = ROOT_SOURCE / "model_endpoint_recovery_metrics.tsv"
CATEGORY = ROOT_SOURCE / "model_endpoint_category_summary.tsv"
COMMON = ROOT_SOURCE / "model_output_homogenization_metrics.tsv"
IDENTITY = ROOT_SOURCE / "model_target_identity_preservation.tsv"
REGISTRY = ROOT_SOURCE / "model_registry.tsv"
PQ = ROOT_SOURCE / "model_endpoint_recovery_pq_values.tsv"
FINITE_BUDGET_SENSITIVITY = Path(
    "reports/model_endpoint_recovery/source_data/"
    "figure3_finite_budget_model_sensitivity.tsv"
)
FINITE_BUDGET_MANIFEST = Path("reports/figure5_sensitivity/finite_budget_manifest.tsv")
FROZEN_ENDPOINT_GRID = Path("reports/truth_bridge_decomposition/target_level_joint_grid.tsv")

SMALL_MULTIPLE_MODELS = [
    "scgen_hcc_formal_v1",
    "cpa_v0.8.8",
    "gears_hcc_formal_v1",
    "cellot_hcc_formal_v1",
    "scgpt_hcc_formal_v1",
    "geneformer_hcc_formal_v1",
]

PROFILE_MODELS = [
    "scgen_hcc_formal_v1",
    "cpa_v0.8.8",
    "gears_hcc_formal_v1",
    "cellot_hcc_formal_v1",
    "scgpt_hcc_formal_v1",
    "geneformer_hcc_formal_v1",
    "lm_train_lowrank_hcc_formal_v1",
    "lm_g_scgpt_ridge_hcc_formal_v1",
    "lm_g_geneformer_ridge_hcc_formal_v1",
    "shared_mean_baseline",
    "null_model",
]
CELL_LINES = ["HCC38", "HCC1143"]

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

MODEL_COLORS = {model: model_color(model) for model in PROFILE_MODELS}
MODEL_COLORS.update(
    {
        "scgen_hcc_formal_v1": COLORS["scgen"],
        "cpa_v0.8.8": COLORS["cpa"],
        "cellot_hcc_formal_v1": COLORS["accent_orange"],
        "scgpt_hcc_formal_v1": "#8C78B8",
        "geneformer_hcc_formal_v1": "#CC79A7",
        "lm_train_lowrank_hcc_formal_v1": "#8F8F8F",
        "lm_g_scgpt_ridge_hcc_formal_v1": "#B0B0B0",
        "lm_g_geneformer_ridge_hcc_formal_v1": "#6F6F6F",
        "shared_mean_baseline": "#333333",
        "null_model": "#D9D9D9",
    }
)

CATEGORY_LABELS = {
    "Q1_anchor": "Endpoint anchors",
    "Q2_transcriptomic_excess": "Shift-excess",
    "shift_excess": "Shift-excess",
    "Q3_dependency_excess": "Dependency-excess",
    "dependency_excess": "Dependency-excess",
    "Q4_low_information": "Low-information",
    "low_information": "Low-information",
    "middle": "Middle band",
}
CATEGORY_FILLS = {
    "Q1_anchor": "#e9f4f0",
    "Q2_transcriptomic_excess": "#eeeffb",
    "shift_excess": "#eeeffb",
    "Q3_dependency_excess": "#fbefdd",
    "dependency_excess": "#fbefdd",
    "Q4_low_information": "#f0f0f0",
    "low_information": "#f0f0f0",
    "middle": "#f9f7ee",
}
CATEGORY_EDGES = {
    "Q1_anchor": "#3b827a",
    "Q2_transcriptomic_excess": "#73729f",
    "shift_excess": "#73729f",
    "Q3_dependency_excess": "#9b5a30",
    "dependency_excess": "#9b5a30",
    "Q4_low_information": "#465261",
    "low_information": "#465261",
    "middle": "#BDBDBD",
}


def add_panel_title(ax: plt.Axes, title: str, *, x: float = 0.0, y: float = 1.055, fontsize: float = 8.6) -> None:
    for loc in ("left", "center", "right"):
        ax.set_title("", loc=loc)
    ax.text(
        x,
        y,
        title,
        transform=ax.transAxes,
        fontsize=fontsize,
        fontweight="bold",
        va="bottom",
        ha="left",
        color=COLORS["text"],
        clip_on=False,
    )


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig3_model_endpoint_recovery"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_3"


def manuscript_panel_dir(root: Path) -> Path:
    return manuscript_figure_dir(root) / "panels"


def active_panel_dirs(root: Path) -> list[Path]:
    return [
        manuscript_panel_dir(root),
        root / "figures/Figure_3/panels",
        root / "figure_build/output/Figure_3/panels",
    ]


def load_inputs(root: Path) -> dict[str, pd.DataFrame]:
    metrics = pd.read_csv(root / METRICS, sep="\t")
    target = pd.read_csv(root / "reports/model_endpoint_recovery/target_summary.tsv", sep="\t")
    frozen_grid = pd.read_csv(root / FROZEN_ENDPOINT_GRID, sep="\t")
    category = pd.read_csv(root / CATEGORY, sep="\t")
    common = pd.read_csv(root / COMMON, sep="\t")
    identity = pd.read_csv(root / IDENTITY, sep="\t")
    registry = pd.read_csv(root / REGISTRY, sep="\t")
    pq = pd.read_csv(root / PQ, sep="\t")
    finite_manifest = pd.read_csv(root / FINITE_BUDGET_MANIFEST, sep="\t")
    finite_budget = build_finite_budget_source(metrics, finite_manifest)
    finite_path = root / FINITE_BUDGET_SENSITIVITY
    finite_path.parent.mkdir(parents=True, exist_ok=True)
    finite_budget.to_csv(finite_path, sep="\t", index=False)
    return {
        "metrics": metrics,
        "target": target,
        "frozen_grid": frozen_grid,
        "category": category,
        "common": common,
        "identity": identity,
        "registry": registry,
        "pq": pq,
        "finite_budget": finite_budget,
    }


def build_finite_budget_source(
    metrics: pd.DataFrame,
    manifest: pd.DataFrame,
) -> pd.DataFrame:
    joined = manifest.merge(metrics, on="model_id", how="inner", validate="one_to_many")
    metric_map = {
        "total-shift endpoint ρ": "total_shift_depmap_spearman",
        "response-aligned endpoint ρ": "response_aligned_depmap_spearman",
        "anchor vs low-information AUC": "anchor_vs_low_information_response_auc",
    }
    rows: list[pd.DataFrame] = []
    for metric_label, column in metric_map.items():
        part = joined[
            ["model_family", "model_id", "run_type", "cell_line", "params_json", column]
        ].rename(columns={column: "metric_value"})
        part["metric"] = metric_label
        rows.append(part)
    return pd.concat(rows, ignore_index=True)


def main_model_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df["model_id"].isin(SMALL_MULTIPLE_MODELS)].copy()


def panel_a_source(metrics: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "model_id",
        "object_role",
        "cell_line",
        "total_shift_depmap_spearman",
        "response_aligned_depmap_spearman",
        "anchor_vs_low_information_response_auc",
        "target_identity_preservation_spearman",
        "predicted_target_similarity_mean",
    ]
    return metrics.loc[metrics["model_id"].isin(PROFILE_MODELS), cols].copy()


def _profile_label(model_id: str, cell_line: str) -> str:
    return f"{MODEL_LABELS.get(model_id, short_model_label(model_id).replace(chr(10), ' '))} {cell_line.replace('HCC', '')}"


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_title(ax, "Endpoint-recovery audit profile", y=1.05, fontsize=7.2)
    data = df.copy()
    data["model_label"] = data["model_id"].map(lambda m: MODEL_LABELS.get(m, short_model_label(m).replace("\n", " ")))
    data["context_label"] = data["cell_line"]
    data["row_label"] = [_profile_label(m, c) for m, c in zip(data["model_id"], data["cell_line"])]
    metric_cols = [
        ("total_shift_depmap_spearman", "total-shift\nendpoint ρ"),
        ("response_aligned_depmap_spearman", "response-aligned\nendpoint ρ"),
        ("anchor_vs_low_information_response_auc", "anchor vs\nlow-info AUC"),
        ("target_identity_preservation_spearman", "target-\nidentity ρ"),
        ("predicted_target_similarity_mean", "output homogenization\nmean target similarity ↑"),
    ]
    row_order = []
    for model in PROFILE_MODELS:
        for cell in CELL_LINES:
            label = _profile_label(model, cell)
            if label in set(data["row_label"]):
                row_order.append(label)
    data["row_label"] = pd.Categorical(data["row_label"], categories=row_order, ordered=True)
    data = data.sort_values("row_label")
    matrix = data[[m for m, _ in metric_cols]].astype(float).to_numpy()
    recovery_cmap = muted_diverging_cmap()
    common_cmap = LinearSegmentedColormap.from_list("common_warning", ["#F7F7F7", "#E7C4BE", "#B44A3C"])
    recovery_centers = {
        "total_shift_depmap_spearman": 0.0,
        "response_aligned_depmap_spearman": 0.0,
        "anchor_vs_low_information_response_auc": 0.5,
        "target_identity_preservation_spearman": 0.0,
    }
    common_values = data["predicted_target_similarity_mean"].astype(float)
    common_min = float(np.nanmin(common_values)) if common_values.notna().any() else 0.0
    common_max = float(np.nanmax(common_values)) if common_values.notna().any() else 1.0
    common_norm = Normalize(vmin=common_min, vmax=common_max if common_max > common_min else common_min + 1.0)
    ax.set_facecolor("white")
    for i in range(matrix.shape[0]):
        for j, (metric, _) in enumerate(metric_cols):
            val = matrix[i, j]
            if pd.isna(val):
                face = "#FAFAFA"
            elif metric == "predicted_target_similarity_mean":
                face = common_cmap(common_norm(val))
            else:
                center = recovery_centers[metric]
                col = data[metric].astype(float)
                spread = float(np.nanmax(np.abs(col - center))) if col.notna().any() else 0.5
                spread = max(spread, 0.5)
                face = recovery_cmap(Normalize(vmin=-spread, vmax=spread)(val - center))
            ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor=face, edgecolor="white", linewidth=0.6))
    ax.set_yticks(np.arange(len(data)))
    ax.set_yticklabels(data["context_label"].astype(str), fontsize=5.2)
    ax.set_xticks(np.arange(len(metric_cols)))
    ax.set_xticklabels([label for _, label in metric_cols], fontsize=5.4)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = matrix[i, j]
            if pd.notna(val):
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=4.4)
            else:
                ax.text(j, i, "NA", ha="center", va="center", fontsize=4.4, color="#9A9A9A")
    for model_id in PROFILE_MODELS:
        rows = np.flatnonzero(data["model_id"].eq(model_id).to_numpy())
        if len(rows):
            label = MODEL_LABELS.get(model_id, short_model_label(model_id).replace("\n", " "))
            ax.text(-0.95, float(rows.mean()), label, ha="right", va="center", fontsize=5.5, color=COLORS["text"], clip_on=False)
            ax.axhline(rows.max() + 0.5, color="white", lw=0.8)
    group_breaks = [
        "cellot_hcc_formal_v1",
        "geneformer_hcc_formal_v1",
        "lm_g_geneformer_ridge_hcc_formal_v1",
    ]
    for model_id in group_breaks:
        rows = np.flatnonzero(data["model_id"].eq(model_id).to_numpy())
        if len(rows):
            ax.axhline(rows.max() + 0.5, color="#D8D8D8", lw=0.55, clip_on=False)
    ax.axvline(3.5, color="#D8D8D8", lw=0.7, clip_on=False)
    ax.text(-0.70, -1.05, "Context", ha="center", va="bottom", fontsize=5.2, color="#444444", clip_on=False)
    ax.tick_params(length=0)
    ax.tick_params(axis="y", pad=2)
    ax.set_xlim(-0.5, len(metric_cols) - 0.5)
    ax.set_ylim(len(data) - 0.5, -0.5)
    for spine in ax.spines.values():
        spine.set_visible(False)


def _metric_row(metrics: pd.DataFrame, model_id: str, cell_line: str) -> pd.Series | None:
    rows = metrics.loc[metrics["model_id"].eq(model_id) & metrics["cell_line"].eq(cell_line)]
    if rows.empty:
        return None
    return rows.iloc[0]


def _annotate_endpoint(ax: plt.Axes, row: pd.Series | None, *, metric: str) -> None:
    def _fmt_q(value: float) -> str:
        if pd.isna(value):
            return "NA"
        return f"{value:.3f}"

    if row is None:
        text = "NA"
    elif metric == "total":
        status = row.get("total_shift_depmap_status", "")
        if status != "estimated":
            text = "non-estimable"
        else:
            text = f"ρ = {row['total_shift_depmap_spearman']:.2f}\nq = {_fmt_q(row['total_shift_depmap_qvalue'])}"
    else:
        status = row.get("response_aligned_depmap_status", "")
        if status != "estimated":
            text = "non-estimable"
        else:
            text = f"ρ = {row['response_aligned_depmap_spearman']:.2f}\nq = {_fmt_q(row['response_aligned_endpoint_permutation_qvalue'])}"
    ax.text(
        0.04,
        0.96,
        text,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=4.9,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 1.2},
    )


def _render_endpoint_grid(
    axes: np.ndarray,
    target: pd.DataFrame,
    metrics: pd.DataFrame,
    frozen_grid: pd.DataFrame,
    *,
    y_col: str,
    metric: str,
    panel_label: str,
    title: str,
    title_y: float = 1.18,
    add_xlabel: bool = True,
) -> None:
    y_label = {
        "predicted_shift_mean_abs": "Predicted total-shift\npercentile",
        "predicted_shift_response_aligned_magnitude": "Predicted response-aligned\nshift percentile",
    }.get(y_col, y_col)
    target = apply_frozen_endpoint_categories(target, frozen_grid)
    data = target.loc[target["model_id"].isin(SMALL_MULTIPLE_MODELS)].copy()
    data["dependency_strength_percentile"] = data.groupby(["model_id", "cell_line"])["dependency_strength"].rank(method="average", pct=True) * 100
    data[f"{y_col}_percentile"] = data.groupby(["model_id", "cell_line"])[y_col].rank(method="average", pct=True) * 100
    metric_status_col = "total_shift_depmap_status" if metric == "total" else "response_aligned_depmap_status"
    status = metrics[["model_id", "cell_line", metric_status_col]].rename(columns={metric_status_col: "metric_status"})
    data = data.merge(status, on=["model_id", "cell_line"], how="left")
    for r, cell_line in enumerate(CELL_LINES):
        for c, model_id in enumerate(SMALL_MULTIPLE_MODELS):
            ax = axes[r, c]
            subset = data.loc[data["cell_line"].eq(cell_line) & data["model_id"].eq(model_id)]
            is_estimable = bool(len(subset)) and subset["metric_status"].iloc[0] == "estimated" and subset[y_col].nunique(dropna=True) > 1
            if is_estimable:
                category_col = "frozen_endpoint_category" if "frozen_endpoint_category" in subset.columns else "endpoint_category"
                for category, cat_df in subset.groupby(category_col, sort=False):
                    ax.scatter(
                        cat_df["dependency_strength_percentile"],
                        cat_df[f"{y_col}_percentile"],
                        s=13,
                        facecolor=CATEGORY_FILLS.get(category, "#F0F0F0"),
                        edgecolors=CATEGORY_EDGES.get(category, "#999999"),
                        linewidths=0.55,
                        alpha=1.0,
                    )
            else:
                ax.text(0.5, 0.52, "non-estimable\nconstant output", transform=ax.transAxes, ha="center", va="center", fontsize=5.0, color="#777777")
            ax.axvline(25, color="#D0D0D0", lw=0.55, ls="--")
            ax.axvline(75, color="#D0D0D0", lw=0.55, ls="--")
            ax.axhline(25, color="#D0D0D0", lw=0.55, ls="--")
            ax.axhline(75, color="#D0D0D0", lw=0.55, ls="--")
            ax.plot([0, 100], [0, 100], color="#D8D8D8", lw=0.55, ls=":", zorder=0)
            ax.set_xlim(-2, 102)
            ax.set_ylim(-2, 102)
            ax.set_xticks([0, 50, 100])
            ax.set_yticks([0, 50, 100])
            ax.grid(False)
            clean_axes(ax)
            row = _metric_row(metrics, model_id, cell_line)
            _annotate_endpoint(ax, row, metric=metric)
            if r == 0:
                ax.set_title(MODEL_LABELS[model_id], fontsize=6.2, weight="bold", pad=2)
            if c == 0:
                ax.set_ylabel("")
                ax.text(
                    0.02,
                    1.02,
                    cell_line,
                    transform=ax.transAxes,
                    ha="left",
                    va="bottom",
                    fontsize=5.7,
                    fontweight="bold",
                    color=COLORS["text"],
                    clip_on=False,
                )
            else:
                ax.set_ylabel("")
            ax.set_xlabel("")
            ax.tick_params(labelsize=5.2)
    fig = axes.ravel()[0].figure
    fig.text(
        0.014,
        0.53,
        y_label.replace("\n", " "),
        rotation=90,
        ha="center",
        va="center",
        fontsize=5.8,
    )
    if add_xlabel:
        fig.text(
            0.53,
            0.125,
            "CRISPR dependency-strength percentile",
            ha="center",
            va="top",
            fontsize=5.8,
        )
    axes[0, 0].text(
        -0.37,
        title_y,
        title,
        transform=axes[0, 0].transAxes,
        fontsize=7.8,
        weight="bold",
        ha="left",
        va="bottom",
    )


def render_panel_b_grid(axes: np.ndarray, inputs: dict[str, pd.DataFrame], *, add_xlabel: bool = True) -> None:
    _render_endpoint_grid(
        axes,
        inputs["target"],
        inputs["metrics"],
        inputs["frozen_grid"],
        y_col="predicted_shift_mean_abs",
        metric="total",
        panel_label="b",
        title="Total-shift endpoint alignment",
        add_xlabel=add_xlabel,
    )


def render_panel_c_grid(axes: np.ndarray, inputs: dict[str, pd.DataFrame], *, add_xlabel: bool = True) -> None:
    _render_endpoint_grid(
        axes,
        inputs["target"],
        inputs["metrics"],
        inputs["frozen_grid"],
        y_col="predicted_shift_response_aligned_magnitude",
        metric="axis",
        panel_label="c",
        title="Response-aligned endpoint recovery",
        add_xlabel=add_xlabel,
    )


def endpoint_category_handles() -> list[Line2D]:
    return [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markerfacecolor=CATEGORY_FILLS[cat],
            markeredgecolor=CATEGORY_EDGES[cat],
            label=CATEGORY_LABELS[cat],
            markersize=5,
        )
        for cat in ["Q1_anchor", "shift_excess", "dependency_excess", "low_information", "middle"]
    ]


def apply_frozen_endpoint_categories(target: pd.DataFrame, frozen_grid: pd.DataFrame) -> pd.DataFrame:
    """Attach the Fig. 2 truth-side frozen endpoint categories for display.

    The model endpoint-recovery target table retains its pipeline-level
    endpoint_category column for scoring provenance. Small-multiple colors,
    however, must use the frozen observed shift × DepMap category object shown
    in Fig. 2 so model panels do not imply model-specific or residual-derived
    category reassignment.
    """
    frozen = frozen_grid[["cell_line", "target_gene", "joint_grid"]].rename(
        columns={"joint_grid": "frozen_endpoint_category"}
    )
    frozen["frozen_endpoint_category_label"] = frozen["frozen_endpoint_category"].map(CATEGORY_LABELS)
    out = target.copy()
    if "endpoint_category" in out.columns:
        out = out.rename(columns={"endpoint_category": "model_pipeline_endpoint_category"})
    out = out.merge(frozen, on=["cell_line", "target_gene"], how="left", validate="many_to_one")
    missing = out["frozen_endpoint_category"].isna()
    if missing.any():
        examples = out.loc[missing, ["cell_line", "target_gene"]].drop_duplicates().head(10).to_dict("records")
        raise RuntimeError(f"Missing frozen endpoint categories for Figure 3 small multiples: {examples}")
    out["endpoint_category"] = out["frozen_endpoint_category"]
    out["endpoint_category_source"] = "Fig. 2 frozen observed-shift x DepMap joint_grid"
    return out


def endpoint_small_multiple_source(
    target: pd.DataFrame,
    metrics: pd.DataFrame,
    frozen_grid: pd.DataFrame,
    y_col: str,
    metric: str,
) -> pd.DataFrame:
    target = apply_frozen_endpoint_categories(target, frozen_grid)
    data = target.loc[target["model_id"].isin(SMALL_MULTIPLE_MODELS)].copy()
    data["dependency_strength_percentile"] = data.groupby(["model_id", "cell_line"])["dependency_strength"].rank(method="average", pct=True) * 100
    data[f"{y_col}_percentile"] = data.groupby(["model_id", "cell_line"])[y_col].rank(method="average", pct=True) * 100
    metric_status_col = "total_shift_depmap_status" if metric == "total" else "response_aligned_depmap_status"
    status = metrics[["model_id", "cell_line", metric_status_col]].rename(columns={metric_status_col: "metric_status"})
    data = data.merge(status, on=["model_id", "cell_line"], how="left")
    data["visualization_percentile_scope"] = "within model x cell line"
    data["rank_endpoint_alignment_note"] = "Raw predicted scores retained; percentiles used for cross-model visualization."
    return data


def render_panel_d(ax: plt.Axes, common: pd.DataFrame, *, include_legend: bool = False) -> None:
    add_panel_title(ax, "Recovery versus output homogenization", x=-0.02, y=1.06, fontsize=7.0)
    data = common.loc[common["model_id"].isin(PROFILE_MODELS)].copy()
    data = data.dropna(
        subset=["endpoint_recovery_score", "predicted_target_similarity_mean"]
    )
    x_min = min(-1.0, float(data["endpoint_recovery_score"].min(skipna=True)) - 0.18)
    x_max = float(data["endpoint_recovery_score"].max(skipna=True)) + 0.35
    y_min = max(-0.06, float(data["predicted_target_similarity_mean"].min(skipna=True)) - 0.04)
    y_max = float(data["predicted_target_similarity_mean"].max(skipna=True)) + 0.06
    endpoint_cut = 0.0

    context_markers = {"HCC38": "o", "HCC1143": "s"}
    for model_id, model_df in data.groupby("model_id", sort=False):
        for cell_line, cell_df in model_df.groupby("cell_line", sort=False):
            size = 46 if model_id not in {"shared_mean_baseline", "scgen_hcc_formal_v1"} else 60
            ax.scatter(
                cell_df["endpoint_recovery_score"],
                cell_df["predicted_target_similarity_mean"],
                s=size,
                marker=context_markers.get(cell_line, "o"),
                color=MODEL_COLORS[model_id],
                label=MODEL_LABELS.get(model_id, short_model_label(model_id).replace("\n", " ")),
                edgecolors="white",
                linewidths=0.55,
                alpha=0.92,
                zorder=3,
            )
    ax.axvline(endpoint_cut, color="#BDBDBD", linewidth=0.75)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xticks([-1, 0, 1, 2, 3])
    ax.set_yticks([0, 0.25, 0.50, 0.75, 1.00])
    ax.set_xlabel("Response-aligned endpoint recovery z", fontsize=6.4)
    ax.set_ylabel("Predicted mean target-target similarity", fontsize=6.4)
    ax.grid(False)
    clean_axes(ax)
    if include_legend:
        model_handles = [
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="",
                markerfacecolor=MODEL_COLORS[model_id],
                markeredgecolor="white",
                markeredgewidth=0.5,
                label=MODEL_LABELS.get(model_id, short_model_label(model_id).replace("\n", " ")),
                markersize=4.6,
            )
            for model_id in PROFILE_MODELS
            if model_id in set(data["model_id"])
        ]
        context_handles = [
            Line2D([0], [0], marker="o", linestyle="", color="#4A4A4A", label="HCC38", markersize=4.6),
            Line2D([0], [0], marker="s", linestyle="", color="#4A4A4A", label="HCC1143", markersize=4.6),
        ]
        legend1 = ax.legend(handles=model_handles, loc="center left", bbox_to_anchor=(1.01, 0.52), frameon=False, title="Model / reference", fontsize=5.4, title_fontsize=5.6)
        ax.add_artist(legend1)
        ax.legend(handles=context_handles, loc="lower left", bbox_to_anchor=(1.01, 0.02), frameon=False, title="Context", fontsize=5.4, title_fontsize=5.6)


def render_panel_e(ax: plt.Axes, identity: pd.DataFrame) -> None:
    add_panel_title(ax, "Target-identity preservation", x=-0.02, y=1.06, fontsize=7.0)
    models = [m for m in PROFILE_MODELS if m not in {"shared_mean_baseline", "null_model"}]
    data = identity.loc[identity["model_id"].isin(models)].copy()
    x_positions = {model_id: i for i, model_id in enumerate(models)}
    jitter = {"HCC38": -0.09, "HCC1143": 0.09}
    for cell_line, marker in [("HCC38", "o"), ("HCC1143", "s")]:
        subset = data.loc[data["cell_line"].eq(cell_line)]
        ax.scatter(
            [x_positions[m] + jitter[cell_line] for m in subset["model_id"]],
            subset["target_identity_preservation_spearman"],
            marker=marker,
            s=42,
            color=[MODEL_COLORS[m] for m in subset["model_id"]],
            edgecolors="white",
            linewidths=0.5,
            label=cell_line,
        )
    ax.axhline(0, color="#BDBDBD", linewidth=0.7)
    ax.axvline(3.5, color="#E0E0E0", linewidth=0.55, zorder=0)
    ax.axvline(5.5, color="#E0E0E0", linewidth=0.55, zorder=0)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([MODEL_LABELS.get(m, short_model_label(m).replace("\n", " ")) for m in models], rotation=38, ha="right")
    ax.set_ylabel("Target-identity Spearman ρ", fontsize=6.4)
    ax.set_ylim(-0.10, 0.52)
    ax.grid(True, axis="y", color="#F2F2F2", linewidth=0.30)
    clean_axes(ax)
    handles = [
        Line2D([0], [0], marker="o", linestyle="", color="#4A4A4A", label="HCC38", markersize=4.6),
        Line2D([0], [0], marker="s", linestyle="", color="#4A4A4A", label="HCC1143", markersize=4.6),
    ]
    ax.legend(handles=handles, loc="upper right", frameon=False, title="Context", fontsize=5.4, title_fontsize=5.6)


def panel_f_source(finite_budget: pd.DataFrame) -> pd.DataFrame:
    keep_metrics = ["response-aligned endpoint ρ", "anchor vs low-information AUC"]
    keep_models = ["scGen", "CPA", "GEARS", "CellOT"]
    out = finite_budget.loc[
        finite_budget["metric"].isin(keep_metrics)
        & finite_budget["model_family"].isin(keep_models)
        & finite_budget["cell_line"].isin(CELL_LINES)
    ].copy()
    out["sensitivity_role"] = np.where(out["run_type"].eq("formal"), "formal run", "finite-budget sensitivity")
    out["claim_boundary"] = "finite-budget sensitivity envelope; does not replace formal model entrants"
    return out


def render_panel_f(fig: plt.Figure, spec, source: pd.DataFrame) -> None:
    sub = spec.subgridspec(1, 4, wspace=0.26)
    metric_order = ["response-aligned endpoint ρ", "anchor vs low-information AUC"]
    context_order = ["HCC38", "HCC1143"]
    model_order = ["scGen", "CPA", "GEARS", "CellOT"]
    y_positions = {model: i for i, model in enumerate(model_order)}
    axes = []
    for idx, (cell_line, metric) in enumerate([(c, m) for c in context_order for m in metric_order]):
        ax = fig.add_subplot(sub[0, idx])
        axes.append(ax)
        data = source.loc[source["cell_line"].eq(cell_line) & source["metric"].eq(metric)].copy()
        for _, row in data.iterrows():
            model = str(row["model_family"])
            y = y_positions[model]
            is_formal = row["run_type"] == "formal"
            ax.scatter(
                float(row["metric_value"]),
                y,
                s=34 if is_formal else 13,
                facecolor=MODEL_COLORS.get(str(row["model_id"]), MODEL_COLORS.get("cellot_hcc_formal_v1", "#777777")) if is_formal else "#A8A8A8",
                edgecolor="white",
                linewidth=0.35,
                alpha=0.95 if is_formal else 0.50,
                marker="o" if cell_line == "HCC38" else "s",
                zorder=3 if is_formal else 2,
            )
        for model in model_order:
            vals = data.loc[data["model_family"].eq(model), "metric_value"].dropna().astype(float)
            if len(vals) > 1:
                ax.plot([vals.min(), vals.max()], [y_positions[model], y_positions[model]], color="#C7C7C7", lw=0.7, zorder=1)
        if metric.endswith("AUC"):
            ax.axvline(0.5, color="#BDBDBD", lw=0.65, ls="--")
            ax.set_xlim(0.2, 0.95)
            xlabel = "anchor vs\nlow-information AUC"
        else:
            ax.axvline(0, color="#BDBDBD", lw=0.65, ls="--")
            ax.set_xlim(-0.45, 0.75)
            xlabel = "response-aligned\nendpoint ρ"
        ax.set_ylim(-0.55, len(model_order) - 0.45)
        ax.invert_yaxis()
        ax.set_yticks(range(len(model_order)))
        ax.set_yticklabels(model_order if idx == 0 else [], fontsize=5.3)
        ax.set_xlabel(xlabel, fontsize=5.5)
        ax.set_title(cell_line if metric == metric_order[0] else "", fontsize=6.0, fontweight="bold", pad=2)
        ax.tick_params(axis="x", labelsize=5.0, length=1.8)
        ax.tick_params(axis="y", length=0)
        ax.grid(False)
        clean_axes(ax)
    first_ax = axes[0]
    first_ax.text(
        -0.18,
        1.20,
        "Finite-budget model sensitivity",
        transform=first_ax.transAxes,
        fontsize=7.0,
        fontweight="bold",
        ha="left",
        va="bottom",
        clip_on=False,
    )
    handles = [
        Line2D([0], [0], marker="o", linestyle="", markerfacecolor="#3b827a", markeredgecolor="white", markeredgewidth=0.35, markersize=4.6, label="formal run"),
        Line2D([0], [0], marker="o", linestyle="", markerfacecolor="#A8A8A8", markeredgecolor="white", markeredgewidth=0.35, markersize=3.6, alpha=0.65, label="finite-budget"),
        Line2D([0, 1], [0, 0], color="#C7C7C7", lw=0.8, label="range"),
    ]
    axes[-1].legend(handles=handles, loc="upper left", bbox_to_anchor=(1.02, 1.02), frameon=False, fontsize=5.2, handlelength=1.1, borderaxespad=0.0)


def panel_sources(inputs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {
        "a": panel_a_source(inputs["metrics"]),
        "b": endpoint_small_multiple_source(
            inputs["target"],
            inputs["metrics"],
            inputs["frozen_grid"],
            "predicted_shift_mean_abs",
            "total",
        ),
        "c": endpoint_small_multiple_source(
            inputs["target"],
            inputs["metrics"],
            inputs["frozen_grid"],
            "predicted_shift_response_aligned_magnitude",
            "axis",
        ),
        "d": inputs["common"].loc[inputs["common"]["model_id"].isin(PROFILE_MODELS)].copy(),
        "e": inputs["identity"].loc[inputs["identity"]["model_id"].isin(PROFILE_MODELS)].copy(),
        "f": panel_f_source(inputs["finite_budget"]),
    }


def write_standalone_panels(root: Path, inputs: dict[str, pd.DataFrame]) -> dict[str, dict[str, Path]]:
    pdir = ensure_dir(panel_dir(root))
    sources = panel_sources(inputs)
    outputs: dict[str, dict[str, Path]] = {}
    input_paths = [root / METRICS, root / FROZEN_ENDPOINT_GRID, root / CATEGORY, root / COMMON, root / IDENTITY, root / REGISTRY, root / PQ, root / FINITE_BUDGET_SENSITIVITY]

    for panel_id, source in sources.items():
        stem = f"{FIGURE_ID}_panel{panel_id}"
        source_path = write_tsv(source, pdir / f"{stem}_source_data.tsv")
        if panel_id == "a":
            fig, ax = plt.subplots(figsize=(7.0, 2.7))
            render_panel_a(ax, source)
        elif panel_id in {"b", "c"}:
            ncols = len(SMALL_MULTIPLE_MODELS)
            fig = plt.figure(figsize=(8.4, 3.25))
            grid = fig.add_gridspec(2, ncols, left=0.07, right=0.99, top=0.83, bottom=0.22, wspace=0.30, hspace=0.34)
            axes = np.array([[fig.add_subplot(grid[r, c]) for c in range(ncols)] for r in range(2)])
            if panel_id == "b":
                render_panel_b_grid(axes, inputs)
            else:
                render_panel_c_grid(axes, inputs)
                fig.legend(
                    handles=endpoint_category_handles(),
                    loc="lower right",
                    ncol=5,
                    frameon=False,
                    bbox_to_anchor=(0.99, 0.02),
                    fontsize=5.8,
                    handletextpad=0.35,
                    columnspacing=0.9,
                )
        elif panel_id == "d":
            fig, ax = plt.subplots(figsize=(5.7, 3.15))
            render_panel_d(ax, source, include_legend=True)
        elif panel_id == "e":
            fig, ax = plt.subplots(figsize=(4.2, 2.9))
            render_panel_e(ax, source)
        else:
            fig = plt.figure(figsize=(6.2, 1.9))
            gs = fig.add_gridspec(1, 1, left=0.12, right=0.98, top=0.74, bottom=0.25)
            render_panel_f(fig, gs[0, 0], source)
        png = pdir / f"{stem}.png"
        pdf = pdir / f"{stem}.pdf"
        svg = pdir / f"{stem}.svg"
        finalize_manuscript_figure(fig)
        fig.savefig(png, dpi=1200, bbox_inches="tight")
        fig.savefig(pdf, bbox_inches="tight")
        fig.savefig(svg, bbox_inches="tight")
        plt.close(fig)
        output_paths = [png, pdf, svg]
        manifest = pdir / f"{stem}_manifest.json"
        public_stem = f"Figure_3_panel_{panel_id}"
        for public_dir in active_panel_dirs(root):
            ensure_dir(public_dir)
            shutil.copy2(source_path, public_dir / f"{public_stem}_source_data.tsv")
            shutil.copy2(png, public_dir / f"{public_stem}.png")
            shutil.copy2(pdf, public_dir / f"{public_stem}.pdf")
            shutil.copy2(svg, public_dir / f"{public_stem}.svg")
        write_panel_manifest(
            manifest_path=manifest,
            repo_root=root,
            panel_id=f"{FIGURE_ID}{panel_id}",
            panel_title=panel_title(panel_id),
            script_path=root / SCRIPT_PATH,
            input_paths=input_paths,
            source_data_path=source_path,
            output_paths=output_paths,
            claim_boundary=CLAIM_BOUNDARY,
        )
        write_panel_manifest(
            manifest_path=public_dir / f"{public_stem}_manifest.json",
            repo_root=root,
            panel_id=f"Figure_3{panel_id}",
            panel_title=panel_title(panel_id),
            script_path=root / SCRIPT_PATH,
            input_paths=input_paths,
            source_data_path=public_dir / f"{public_stem}_source_data.tsv",
            output_paths=[public_dir / f"{public_stem}.png", public_dir / f"{public_stem}.pdf", public_dir / f"{public_stem}.svg"],
            claim_boundary=CLAIM_BOUNDARY,
        )
        outputs[panel_id] = {"source": source_path, "png": png, "pdf": pdf, "manifest": manifest}
    return outputs


def panel_title(panel_id: str) -> str:
    return {
        "a": "Evaluation contract",
        "b": "Total generated shift versus dependency",
        "c": "Response-aligned endpoint recovery",
        "d": "Output-homogenization diagnostic",
        "e": "Target-identity preservation",
        "f": "Finite-budget model sensitivity",
    }[panel_id]


def render_combined(root: Path, inputs: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    manuscript_out = ensure_dir(manuscript_figure_dir(root))
    sources = panel_sources(inputs)
    combined_source = pd.concat(
        [df.assign(panel=panel_id) for panel_id, df in sources.items()],
        ignore_index=True,
        sort=False,
    )
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")
    manuscript_source_path = write_tsv(combined_source, manuscript_out / "Figure_3_source_data.tsv")

    fig = plt.figure(figsize=(11.2, 12.75))
    outer = fig.add_gridspec(
        6,
        6,
        height_ratios=[2.45, 0.92, 1.10, 1.10, 1.10, 1.10],
        left=0.06,
        right=0.98,
        top=0.96,
        bottom=0.055,
        hspace=0.64,
        wspace=0.38,
    )
    ax_a = fig.add_subplot(outer[0, :3])
    ax_d = fig.add_subplot(outer[0, 3:4])
    ax_e = fig.add_subplot(outer[0, 4:6])
    ncols = len(SMALL_MULTIPLE_MODELS)
    render_panel_f(fig, outer[1, :], sources["f"])
    b_grid = outer[2:4, :].subgridspec(2, ncols, wspace=0.30, hspace=0.33)
    c_grid = outer[4:6, :].subgridspec(2, ncols, wspace=0.30, hspace=0.33)
    axes_b = np.array([[fig.add_subplot(b_grid[r, c]) for c in range(ncols)] for r in range(2)])
    axes_c = np.array([[fig.add_subplot(c_grid[r, c]) for c in range(ncols)] for r in range(2)])

    render_panel_a(ax_a, sources["a"])
    render_panel_d(ax_d, sources["d"], include_legend=False)
    render_panel_e(ax_e, sources["e"])
    render_panel_b_grid(axes_b, inputs, add_xlabel=False)
    render_panel_c_grid(axes_c, inputs, add_xlabel=False)
    fig.text(0.52, 0.455, "CRISPR dependency-strength percentile", ha="center", va="top", fontsize=5.8)
    fig.text(0.52, 0.095, "CRISPR dependency-strength percentile", ha="center", va="top", fontsize=5.8)

    fig.legend(handles=endpoint_category_handles(), loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.52, 0.005), fontsize=6.0)

    png = out / f"{FIGURE_ID}.png"
    pdf = out / f"{FIGURE_ID}.pdf"
    svg = out / f"{FIGURE_ID}.svg"
    manuscript_png = manuscript_out / "Figure_3.png"
    manuscript_pdf = manuscript_out / "Figure_3.pdf"
    manuscript_svg = manuscript_out / "Figure_3.svg"
    for path in [png, pdf, svg, manuscript_png, manuscript_pdf, manuscript_svg]:
        ensure_dir(path.parent)
    finalize_manuscript_figure(fig)
    fig.savefig(png, dpi=1200, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    fig.savefig(manuscript_png, dpi=1200, bbox_inches="tight")
    fig.savefig(manuscript_pdf, bbox_inches="tight")
    fig.savefig(manuscript_svg, bbox_inches="tight")
    plt.close(fig)

    input_paths = [root / METRICS, root / FROZEN_ENDPOINT_GRID, root / CATEGORY, root / COMMON, root / IDENTITY, root / REGISTRY, root / PQ, root / FINITE_BUDGET_SENSITIVITY]
    manifest = out / f"{FIGURE_ID}_panel_manifest.json"
    write_figure_manifest(
        manifest_path=manifest,
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in ["a", "b", "c", "d", "e", "f"]],
        combined_source_data_path=combined_source_path,
        output_paths=[png, pdf, svg],
        input_paths=input_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    write_figure_manifest(
        manifest_path=manuscript_out / "Figure_3_panel_manifest.json",
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in ["a", "b", "c", "d", "e", "f"]],
        combined_source_data_path=manuscript_source_path,
        output_paths=[manuscript_png, manuscript_pdf, manuscript_svg],
        input_paths=input_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": combined_source_path, "png": png, "pdf": pdf, "manifest": manifest}


def copy_to_figure_build(root: Path) -> None:
    src = output_dir(root)
    dst = ensure_dir(root / "figure_build/output/Figure_3")
    panel_dst = ensure_dir(dst / "panels")
    for ext in [".png", ".pdf", ".svg", "_source_data.tsv"]:
        s = src / f"{FIGURE_ID}{ext}"
        if s.exists():
            shutil.copy2(s, dst / f"Figure_3{ext}")
    for panel in ["a", "b", "c", "d", "e", "f"]:
        for ext in [".png", ".pdf", ".svg", "_source_data.tsv"]:
            s = src / "panels" / f"{FIGURE_ID}_panel{panel}{ext}"
            if s.exists():
                shutil.copy2(s, panel_dst / f"Figure_3_panel_{panel}{ext}")


def update_panel_source_manifest(root: Path) -> None:
    rows = []
    source_root = root / ROOT_SOURCE
    source_hashes = {
        "model_endpoint_recovery_interpretation.md": sha256_file(
            root / "reports/model_endpoint_recovery/model_endpoint_recovery_interpretation.md"
        ),
        "model_endpoint_recovery_metrics.tsv": sha256_file(source_root / "model_endpoint_recovery_metrics.tsv"),
        "target_summary.tsv": sha256_file(root / "reports/model_endpoint_recovery/target_summary.tsv"),
        "model_output_homogenization_metrics.tsv": sha256_file(
            source_root / "model_output_homogenization_metrics.tsv"
        ),
        "model_target_identity_preservation.tsv": sha256_file(source_root / "model_target_identity_preservation.tsv"),
        "figure3_finite_budget_model_sensitivity.tsv": sha256_file(
            source_root / "figure3_finite_budget_model_sensitivity.tsv"
        ),
    }
    records = [
        ("Figure_3", "a", "model_endpoint_recovery_interpretation.md", "claim ceiling/evaluation regime", "scripts/figures/build_figure3.py", "reports/manuscript_figures_v2/fig3_model_endpoint_recovery/panels/figure3_panela.png"),
        ("Figure_3", "b", "source_data/model_endpoint_recovery_metrics.tsv; reports/model_endpoint_recovery/target_summary.tsv", "dependency_strength,predicted_shift_mean_abs,total_shift_depmap_status,total_shift_depmap_qvalue,anchor_vs_low_information_response_auc", "scripts/figures/build_figure3.py", "reports/manuscript_figures_v2/fig3_model_endpoint_recovery/panels/figure3_panelb.png"),
        ("Figure_3", "c", "source_data/model_endpoint_recovery_metrics.tsv; reports/model_endpoint_recovery/target_summary.tsv", "dependency_strength,predicted_shift_response_aligned_magnitude,response_aligned_endpoint_permutation_qvalue", "scripts/figures/build_figure3.py", "reports/manuscript_figures_v2/fig3_model_endpoint_recovery/panels/figure3_panelc.png"),
        ("Figure_3", "d", "source_data/model_output_homogenization_metrics.tsv", "endpoint_recovery_score,predicted_target_similarity_mean,output_homogenization_quadrant", "scripts/figures/build_figure3.py", "reports/manuscript_figures_v2/fig3_model_endpoint_recovery/panels/figure3_paneld.png"),
        ("Figure_3", "e", "source_data/model_target_identity_preservation.tsv", "target_identity_preservation_spearman,target_identity_label_permutation_qvalue,target_identity_preservation_status", "scripts/figures/build_figure3.py", "reports/manuscript_figures_v2/fig3_model_endpoint_recovery/panels/figure3_panele.png"),
        ("Figure_3", "f", "reports/model_endpoint_recovery/source_data/figure3_finite_budget_model_sensitivity.tsv", "model_family,run_type,cell_line,metric,metric_value", "scripts/figures/build_figure3.py", "reports/manuscript_figures_v2/fig3_model_endpoint_recovery/panels/figure3_panelf.png"),
    ]
    for figure_id, panel_id, source_file, columns, script, output_file in records:
        output_path = root / output_file
        source_hash = ";".join(
            source_hashes[key]
            for key in source_hashes
            if key in source_file
            or (key == "target_summary.tsv" and "target_summary" in source_file)
            or (
                key == "model_output_homogenization_metrics.tsv"
                and "model_output_homogenization_metrics" in source_file
            )
            or (
                key == "model_target_identity_preservation.tsv"
                and "model_target_identity_preservation" in source_file
            )
            or (
                key == "figure3_finite_budget_model_sensitivity.tsv"
                and "figure3_finite_budget_model_sensitivity" in source_file
            )
        )
        rows.append(
            {
                "figure_id": figure_id,
                "panel_id": panel_id,
                "source_file": source_file,
                "columns_used": columns,
                "source_hash": source_hash,
                "script": script,
                "output_file": output_file,
                "output_hash": sha256_file(output_path) if output_path.exists() else "",
            }
        )
    write_tsv(pd.DataFrame(rows), source_root / "figure_panel_source_manifest.tsv")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build Figure 3 model endpoint-recovery audit.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)

    root = repo_root()
    apply_manuscript_style()
    ensure_dir(manuscript_figure_dir(root))
    ensure_dir(manuscript_panel_dir(root))
    inputs = load_inputs(root)
    panel_outputs = write_standalone_panels(root, inputs)
    if not args.panels_only:
        render_combined(root, inputs, panel_outputs)
        copy_to_figure_build(root)
        update_panel_source_manifest(root)


if __name__ == "__main__":
    main()
