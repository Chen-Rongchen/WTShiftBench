from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import sha256_file, write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import (
    COLORS,
    add_panel_heading,
    apply_manuscript_style,
    clean_axes,
    finalize_manuscript_figure,
    model_color,
    muted_diverging_cmap,
    short_model_label,
)


FIGURE_ID = "figure3"
FIGURE_TITLE = "Model-generated shifts reveal endpoint-recovery and common-response profiles"
SCRIPT_PATH = Path("scripts/manuscript/build_figure3_model_endpoint_recovery.py")
CLAIM_BOUNDARY = (
    "WTShiftBench audits model-generated perturbation shifts for recovery of a "
    "fixed DepMap-aligned endpoint structure. It does not evaluate models as "
    "direct DepMap, essentiality, viability, or causal-fitness predictors."
)

ROOT_SOURCE = Path("reports/model_endpoint_recovery/source_data")
METRICS = ROOT_SOURCE / "model_endpoint_recovery_metrics.tsv"
CATEGORY = ROOT_SOURCE / "model_endpoint_category_summary.tsv"
COMMON = ROOT_SOURCE / "model_common_response_metrics.tsv"
IDENTITY = ROOT_SOURCE / "model_target_identity_preservation.tsv"
REGISTRY = ROOT_SOURCE / "model_registry.tsv"
PQ = ROOT_SOURCE / "model_endpoint_recovery_pq_values.tsv"

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
MODEL_COLORS.update({"scgen_hcc_formal_v1": COLORS["scgen"], "cpa_v0.8.8": COLORS["cpa"], "cellot_hcc_formal_v1": COLORS["accent_orange"]})

CATEGORY_COLORS = {
    "Q1_anchor": COLORS["scgen"],
    "shift_excess": COLORS["cpa"],
    "dependency_excess": COLORS["accent_purple"],
    "low_information": COLORS["low_info"],
    "middle": COLORS["middle"],
}


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig3_model_endpoint_recovery"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_3"


def load_inputs(root: Path) -> dict[str, pd.DataFrame]:
    metrics = pd.read_csv(root / METRICS, sep="\t")
    target = pd.read_csv(root / "reports/model_endpoint_recovery/target_summary.tsv", sep="\t")
    category = pd.read_csv(root / CATEGORY, sep="\t")
    common = pd.read_csv(root / COMMON, sep="\t")
    identity = pd.read_csv(root / IDENTITY, sep="\t")
    registry = pd.read_csv(root / REGISTRY, sep="\t")
    pq = pd.read_csv(root / PQ, sep="\t")
    return {
        "metrics": metrics,
        "target": target,
        "category": category,
        "common": common,
        "identity": identity,
        "registry": registry,
        "pq": pq,
    }


def main_model_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df["model_id"].isin(SMALL_MULTIPLE_MODELS)].copy()


def panel_a_source(metrics: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "model_id",
        "object_role",
        "cell_line",
        "total_shift_depmap_spearman",
        "axis_aligned_depmap_spearman",
        "anchor_vs_low_information_axis_auc",
        "target_identity_preservation_spearman",
        "common_response_score",
    ]
    return metrics.loc[metrics["model_id"].isin(PROFILE_MODELS), cols].copy()


def _profile_label(model_id: str, cell_line: str) -> str:
    return f"{MODEL_LABELS.get(model_id, short_model_label(model_id).replace(chr(10), ' '))} {cell_line.replace('HCC', '')}"


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_heading(ax, "a", "Endpoint-recovery audit profile across model types", label_x=-0.08, y=1.05)
    data = df.copy()
    data["row_label"] = [_profile_label(m, c) for m, c in zip(data["model_id"], data["cell_line"])]
    metric_cols = [
        ("total_shift_depmap_spearman", "total\nrho"),
        ("axis_aligned_depmap_spearman", "axis\nrho"),
        ("anchor_vs_low_information_axis_auc", "anchor\nAUC"),
        ("target_identity_preservation_spearman", "identity\nrho"),
        ("common_response_score", "common\nscore"),
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
    display = matrix.copy()
    # Keep AUC visually centered at 0.5 so separation above chance is warm.
    auc_idx = [m for m, _ in metric_cols].index("anchor_vs_low_information_axis_auc")
    display[:, auc_idx] = display[:, auc_idx] - 0.5
    vmax = np.nanmax(np.abs(display))
    vmax = max(float(vmax), 0.5)
    im = ax.imshow(display, cmap=muted_diverging_cmap(), norm=Normalize(vmin=-vmax, vmax=vmax), aspect="auto")
    ax.set_yticks(np.arange(len(data)))
    ax.set_yticklabels(data["row_label"].astype(str), fontsize=4.9)
    ax.set_xticks(np.arange(len(metric_cols)))
    ax.set_xticklabels([label for _, label in metric_cols], fontsize=5.4)
    for i in range(display.shape[0]):
        for j in range(display.shape[1]):
            val = matrix[i, j]
            if pd.notna(val):
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=4.4)
            else:
                ax.text(j, i, "NA", ha="center", va="center", fontsize=4.4, color="#777777")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = plt.colorbar(im, ax=ax, fraction=0.024, pad=0.008)
    cbar.set_label("centered value", fontsize=5.4)
    cbar.ax.tick_params(labelsize=5.0, length=2)


def _metric_row(metrics: pd.DataFrame, model_id: str, cell_line: str) -> pd.Series | None:
    rows = metrics.loc[metrics["model_id"].eq(model_id) & metrics["cell_line"].eq(cell_line)]
    if rows.empty:
        return None
    return rows.iloc[0]


def _annotate_endpoint(ax: plt.Axes, row: pd.Series | None, *, metric: str) -> None:
    if row is None:
        text = "NA"
    elif metric == "total":
        status = row.get("total_shift_depmap_status", "")
        if status != "estimated":
            text = "NA\nconstant total"
        else:
            text = f"ρ = {row['total_shift_depmap_spearman']:.2f}\nq = {row['total_shift_depmap_qvalue']:.3g}"
    else:
        status = row.get("axis_aligned_depmap_status", "")
        if status != "estimated":
            text = "NA"
        else:
            text = f"ρ = {row['axis_aligned_depmap_spearman']:.2f}\nq = {row['axis_aligned_endpoint_permutation_qvalue']:.3g}"
    if row is not None and pd.notna(row.get("anchor_vs_low_information_axis_auc", np.nan)):
        text += f"; AUC={row['anchor_vs_low_information_axis_auc']:.2f}"
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
    *,
    y_col: str,
    metric: str,
    panel_label: str,
    title: str,
    title_y: float = 1.38,
) -> None:
    y_label = {
        "predicted_shift_mean_abs": "predicted shift\nmean abs",
        "predicted_shift_axis_aligned_magnitude": "axis-aligned\nmagnitude",
    }.get(y_col, y_col)
    data = target.loc[target["model_id"].isin(SMALL_MULTIPLE_MODELS)].copy()
    x_min = float(data["dependency_strength"].min())
    x_max = float(data["dependency_strength"].max())
    y_min = float(data[y_col].min())
    y_max = float(data[y_col].max())
    x_pad = max(0.05, 0.05 * (x_max - x_min))
    y_pad = max(0.002, 0.06 * (y_max - y_min))
    for r, cell_line in enumerate(CELL_LINES):
        for c, model_id in enumerate(SMALL_MULTIPLE_MODELS):
            ax = axes[r, c]
            subset = data.loc[data["cell_line"].eq(cell_line) & data["model_id"].eq(model_id)]
            for category, cat_df in subset.groupby("endpoint_category", sort=False):
                ax.scatter(
                    cat_df["dependency_strength"],
                    cat_df[y_col],
                    s=10,
                    color=CATEGORY_COLORS.get(category, "#999999"),
                    alpha=0.82,
                    edgecolors="white",
                    linewidths=0.25,
                )
            ax.set_xlim(x_min - x_pad, x_max + x_pad)
            ax.set_ylim(y_min - y_pad, y_max + y_pad)
            ax.grid(False)
            clean_axes(ax)
            row = _metric_row(metrics, model_id, cell_line)
            _annotate_endpoint(ax, row, metric=metric)
            if r == 0:
                ax.set_title(MODEL_LABELS[model_id], fontsize=6.2, weight="bold", pad=2)
            if c == 0:
                ax.set_ylabel(f"{cell_line}\n{y_label}", fontsize=5.7)
            else:
                ax.set_ylabel("")
            if r == len(CELL_LINES) - 1:
                ax.set_xlabel("Dependency strength (-DepMap)", fontsize=5.8)
            else:
                ax.set_xlabel("")
            ax.tick_params(labelsize=5.2)
    axes[0, 0].text(
        -0.37,
        title_y,
        f"{panel_label}  {title}",
        transform=axes[0, 0].transAxes,
        fontsize=7.8,
        weight="bold",
        ha="left",
        va="bottom",
    )


def render_panel_b_grid(axes: np.ndarray, inputs: dict[str, pd.DataFrame]) -> None:
    _render_endpoint_grid(
        axes,
        inputs["target"],
        inputs["metrics"],
        y_col="predicted_shift_mean_abs",
        metric="total",
        panel_label="b",
        title="Total generated shift versus dependency",
    )


def render_panel_c_grid(axes: np.ndarray, inputs: dict[str, pd.DataFrame]) -> None:
    _render_endpoint_grid(
        axes,
        inputs["target"],
        inputs["metrics"],
        y_col="predicted_shift_axis_aligned_magnitude",
        metric="axis",
        panel_label="c",
        title="Axis-aligned generated shift versus dependency",
        title_y=1.10,
    )


def render_panel_d(ax: plt.Axes, common: pd.DataFrame) -> None:
    add_panel_heading(ax, "d", "Common-response audit", label_x=-0.16, title_x=-0.02, y=1.08)
    data = common.loc[common["model_id"].isin(PROFILE_MODELS)].copy()
    data = data.loc[data["common_response_quadrant"].ne("not_estimable")]
    for model_id, model_df in data.groupby("model_id", sort=False):
        ax.scatter(
            model_df["endpoint_recovery_score"],
            model_df["common_response_score"],
            s=38 if model_id not in {"shared_mean_baseline", "scgen_hcc_formal_v1"} else 54,
            color=MODEL_COLORS[model_id],
            label=MODEL_LABELS.get(model_id, short_model_label(model_id).replace("\n", " ")),
            edgecolors="white",
            linewidths=0.5,
            alpha=0.9,
        )
        for _, row in model_df.iterrows():
            if model_id in {"scgen_hcc_formal_v1", "cpa_v0.8.8", "gears_hcc_formal_v1", "shared_mean_baseline"}:
                ax.text(row["endpoint_recovery_score"] + 0.03, row["common_response_score"], row["cell_line"], fontsize=5.2)
    ax.axvline(0, color="#BDBDBD", linewidth=0.7)
    ax.axhline(data["common_response_score"].median(), color="#BDBDBD", linewidth=0.7, linestyle="--")
    ax.set_xlabel("Axis endpoint recovery z", fontsize=6.4)
    ax.set_ylabel("Common-response score", fontsize=6.4)
    ax.grid(False)
    clean_axes(ax)


def render_panel_e(ax: plt.Axes, identity: pd.DataFrame) -> None:
    add_panel_heading(ax, "e", "Target-identity preservation", label_x=-0.16, title_x=-0.02, y=1.08)
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
        for _, row in subset.iterrows():
            if row["target_identity_preservation_status"] == "estimated" and pd.notna(row["target_identity_label_permutation_qvalue"]):
                label = f"q={row['target_identity_label_permutation_qvalue']:.2g}"
                ax.text(
                    x_positions[row["model_id"]] + jitter[cell_line],
                    row["target_identity_preservation_spearman"] + 0.025,
                    label,
                    ha="center",
                    fontsize=4.8,
                )
    ax.axhline(0, color="#BDBDBD", linewidth=0.7)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([MODEL_LABELS.get(m, short_model_label(m).replace("\n", " ")) for m in models], rotation=38, ha="right")
    ax.set_ylabel("Spearman ρ", fontsize=6.4)
    ax.set_ylim(-0.10, 0.52)
    ax.grid(True, axis="y", color="#F5F5F5", linewidth=0.35)
    clean_axes(ax)


def panel_sources(inputs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {
        "a": panel_a_source(inputs["metrics"]),
        "b": inputs["target"].loc[inputs["target"]["model_id"].isin(SMALL_MULTIPLE_MODELS)].copy(),
        "c": inputs["target"].loc[inputs["target"]["model_id"].isin(SMALL_MULTIPLE_MODELS)].copy(),
        "d": inputs["common"].loc[inputs["common"]["model_id"].isin(PROFILE_MODELS)].copy(),
        "e": inputs["identity"].loc[inputs["identity"]["model_id"].isin(PROFILE_MODELS)].copy(),
    }


def write_standalone_panels(root: Path, inputs: dict[str, pd.DataFrame]) -> dict[str, dict[str, Path]]:
    pdir = ensure_dir(panel_dir(root))
    sources = panel_sources(inputs)
    outputs: dict[str, dict[str, Path]] = {}
    input_paths = [root / METRICS, root / CATEGORY, root / COMMON, root / IDENTITY, root / REGISTRY, root / PQ]

    for panel_id, source in sources.items():
        stem = f"{FIGURE_ID}_panel{panel_id}"
        source_path = write_tsv(source, pdir / f"{stem}_source_data.tsv")
        if panel_id == "a":
            fig, ax = plt.subplots(figsize=(7.0, 1.8))
            render_panel_a(ax, source)
        elif panel_id in {"b", "c"}:
            ncols = len(SMALL_MULTIPLE_MODELS)
            fig = plt.figure(figsize=(8.4, 3.25))
            grid = fig.add_gridspec(2, ncols, left=0.07, right=0.99, top=0.83, bottom=0.16, wspace=0.30, hspace=0.34)
            axes = np.array([[fig.add_subplot(grid[r, c]) for c in range(ncols)] for r in range(2)])
            if panel_id == "b":
                render_panel_b_grid(axes, inputs)
            else:
                render_panel_c_grid(axes, inputs)
        elif panel_id == "d":
            fig, ax = plt.subplots(figsize=(3.9, 2.9))
            render_panel_d(ax, source)
        else:
            fig, ax = plt.subplots(figsize=(4.2, 2.9))
            render_panel_e(ax, source)
        png = pdir / f"{stem}.png"
        pdf = pdir / f"{stem}.pdf"
        output_paths = save_figure(fig, png, pdf)
        manifest = pdir / f"{stem}_manifest.json"
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
        outputs[panel_id] = {"source": source_path, "png": png, "pdf": pdf, "manifest": manifest}
    return outputs


def panel_title(panel_id: str) -> str:
    return {
        "a": "Evaluation contract",
        "b": "Total generated shift versus dependency",
        "c": "Axis-aligned generated shift versus dependency",
        "d": "Common-response quadrant",
        "e": "Target-identity preservation",
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

    fig = plt.figure(figsize=(11.2, 10.4))
    outer = fig.add_gridspec(
        5,
        6,
        height_ratios=[1.85, 1.05, 1.05, 1.05, 1.05],
        left=0.06,
        right=0.98,
        top=0.96,
        bottom=0.06,
        hspace=0.48,
        wspace=0.38,
    )
    ax_a = fig.add_subplot(outer[0, :3])
    ax_d = fig.add_subplot(outer[0, 3:4])
    ax_e = fig.add_subplot(outer[0, 4:6])
    ncols = len(SMALL_MULTIPLE_MODELS)
    b_grid = outer[1:3, :].subgridspec(2, ncols, wspace=0.30, hspace=0.33)
    c_grid = outer[3:5, :].subgridspec(2, ncols, wspace=0.30, hspace=0.33)
    axes_b = np.array([[fig.add_subplot(b_grid[r, c]) for c in range(ncols)] for r in range(2)])
    axes_c = np.array([[fig.add_subplot(c_grid[r, c]) for c in range(ncols)] for r in range(2)])

    render_panel_a(ax_a, sources["a"])
    render_panel_d(ax_d, sources["d"])
    render_panel_e(ax_e, sources["e"])
    render_panel_b_grid(axes_b, inputs)
    render_panel_c_grid(axes_c, inputs)

    handles = [
        Line2D([0], [0], marker="o", linestyle="", markerfacecolor=color, markeredgecolor="white", label=label, markersize=5)
        for label, color in CATEGORY_COLORS.items()
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.52, 0.005), fontsize=6.0)

    png = out / f"{FIGURE_ID}.png"
    pdf = out / f"{FIGURE_ID}.pdf"
    manuscript_png = manuscript_out / "Figure_3.png"
    manuscript_pdf = manuscript_out / "Figure_3.pdf"
    for path in [png, pdf, manuscript_png, manuscript_pdf]:
        ensure_dir(path.parent)
    finalize_manuscript_figure(fig)
    fig.savefig(png, dpi=1200, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(manuscript_png, dpi=1200, bbox_inches="tight")
    fig.savefig(manuscript_pdf, bbox_inches="tight")
    plt.close(fig)

    input_paths = [root / METRICS, root / CATEGORY, root / COMMON, root / IDENTITY, root / REGISTRY, root / PQ]
    manifest = out / f"{FIGURE_ID}_panel_manifest.json"
    write_figure_manifest(
        manifest_path=manifest,
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in ["a", "b", "c", "d", "e"]],
        combined_source_data_path=combined_source_path,
        output_paths=[png, pdf],
        input_paths=input_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    write_figure_manifest(
        manifest_path=manuscript_out / "Figure_3_panel_manifest.json",
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in ["a", "b", "c", "d", "e"]],
        combined_source_data_path=manuscript_source_path,
        output_paths=[manuscript_png, manuscript_pdf],
        input_paths=input_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": combined_source_path, "png": png, "pdf": pdf, "manifest": manifest}


def copy_to_figure_build(root: Path) -> None:
    src = output_dir(root)
    dst = ensure_dir(root / "figure_build/output/Figure_3")
    panel_dst = ensure_dir(dst / "panels")
    for ext in [".png", ".pdf", "_source_data.tsv"]:
        s = src / f"{FIGURE_ID}{ext}"
        if s.exists():
            shutil.copy2(s, dst / f"Figure_3{ext}")
    for panel in ["a", "b", "c", "d", "e"]:
        for ext in [".png", ".pdf", "_source_data.tsv"]:
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
        "model_common_response_metrics.tsv": sha256_file(source_root / "model_common_response_metrics.tsv"),
        "model_target_identity_preservation.tsv": sha256_file(source_root / "model_target_identity_preservation.tsv"),
    }
    records = [
        ("Figure_3", "a", "model_endpoint_recovery_interpretation.md", "claim ceiling/evaluation regime", "scripts/manuscript/build_figure3_model_endpoint_recovery.py", "reports/manuscript_figures_v2/fig3_model_endpoint_recovery/panels/figure3_panela.png"),
        ("Figure_3", "b", "source_data/model_endpoint_recovery_metrics.tsv; reports/model_endpoint_recovery/target_summary.tsv", "dependency_strength,predicted_shift_mean_abs,total_shift_depmap_status,total_shift_depmap_qvalue,anchor_vs_low_information_axis_auc", "scripts/manuscript/build_figure3_model_endpoint_recovery.py", "reports/manuscript_figures_v2/fig3_model_endpoint_recovery/panels/figure3_panelb.png"),
        ("Figure_3", "c", "source_data/model_endpoint_recovery_metrics.tsv; reports/model_endpoint_recovery/target_summary.tsv", "dependency_strength,predicted_shift_axis_aligned_magnitude,axis_aligned_endpoint_permutation_qvalue", "scripts/manuscript/build_figure3_model_endpoint_recovery.py", "reports/manuscript_figures_v2/fig3_model_endpoint_recovery/panels/figure3_panelc.png"),
        ("Figure_3", "d", "source_data/model_common_response_metrics.tsv", "endpoint_recovery_score,common_response_score,common_response_quadrant", "scripts/manuscript/build_figure3_model_endpoint_recovery.py", "reports/manuscript_figures_v2/fig3_model_endpoint_recovery/panels/figure3_paneld.png"),
        ("Figure_3", "e", "source_data/model_target_identity_preservation.tsv", "target_identity_preservation_spearman,target_identity_label_permutation_qvalue,target_identity_preservation_status", "scripts/manuscript/build_figure3_model_endpoint_recovery.py", "reports/manuscript_figures_v2/fig3_model_endpoint_recovery/panels/figure3_panele.png"),
    ]
    for figure_id, panel_id, source_file, columns, script, output_file in records:
        output_path = root / output_file
        source_hash = ";".join(
            source_hashes[key]
            for key in source_hashes
            if key in source_file
            or (key == "target_summary.tsv" and "target_summary" in source_file)
            or (key == "model_common_response_metrics.tsv" and "model_common_response_metrics" in source_file)
            or (
                key == "model_target_identity_preservation.tsv"
                and "model_target_identity_preservation" in source_file
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
    inputs = load_inputs(root)
    panel_outputs = write_standalone_panels(root, inputs)
    if not args.panels_only:
        render_combined(root, inputs, panel_outputs)
        copy_to_figure_build(root)
        update_panel_source_manifest(root)


if __name__ == "__main__":
    main()
