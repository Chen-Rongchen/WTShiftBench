#!/usr/bin/env python3
"""Build axis-free output-homogenization and target-identity panels."""

from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform

from wtbench.hcc_prediction_export import (
    DEFAULT_TRUTH_CONFIG_PATH,
    build_dataset_specs,
    compute_truth_aligned_log_shift_matrix,
    load_config,
)
from wtbench.figures.manuscript_style import (
    COLORS,
    apply_manuscript_style,
    clean_axes,
    finalize_manuscript_figure,
    model_color,
)
from wtbench.model_endpoint_recovery import _cosine_similarity_matrix
from wtbench.model_structure_scorer import DEFAULT_AXIS_MEMBERSHIP_PATH, load_prediction_matrix


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/manuscript_extended_data_v1/edfig5_output_geometry"
PANEL_OUT = OUT / "panels"
PUBLIC = ROOT / "manuscript/figures/Extended_Data_Figure_5"
PUBLIC_PANELS = PUBLIC / "panels"
REPO_PANELS = ROOT / "figures/Extended_Data_Figure_5/panels"
FIGURE_BUILD = ROOT / "figure_build/output/Extended_Data_Figure_5"
FIGURE_BUILD_PANELS = FIGURE_BUILD / "panels"
METRICS = ROOT / "reports/model_endpoint_recovery/source_data/model_endpoint_recovery_metrics.tsv"
IDENTITY = ROOT / "reports/model_endpoint_recovery/source_data/model_target_identity_preservation.tsv"
PREDICTION_ROOT = ROOT / "data/predictions/hcc_scorer_ready"
HOMOGENIZATION_CMAP = ("#F7F7F7", "#D9ECE8", "#2F7F73")
SIMILARITY_CMAP = ("#5B8DB8", "#F7F7F7", "#2F7F73")

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
]
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
    }
)


def save_panel(fig: plt.Figure, panel: str, source: pd.DataFrame) -> None:
    PANEL_OUT.mkdir(parents=True, exist_ok=True)
    for directory in [PUBLIC_PANELS, REPO_PANELS, FIGURE_BUILD_PANELS]:
        directory.mkdir(parents=True, exist_ok=True)
    stem = f"Extended_Data_Figure_5_panel_{panel}"
    source.to_csv(PANEL_OUT / f"edfig5_panel{panel}_source_data.tsv", sep="\t", index=False)
    finalize_manuscript_figure(fig)
    paths = {
        ".png": PANEL_OUT / f"edfig5_panel{panel}.png",
        ".pdf": PANEL_OUT / f"edfig5_panel{panel}.pdf",
        ".svg": PANEL_OUT / f"edfig5_panel{panel}.svg",
    }
    fig.savefig(paths[".png"], dpi=1200, bbox_inches="tight")
    fig.savefig(paths[".pdf"], bbox_inches="tight")
    fig.savefig(paths[".svg"], bbox_inches="tight")
    plt.close(fig)
    for directory in [PUBLIC_PANELS, REPO_PANELS, FIGURE_BUILD_PANELS]:
        for ext, path in paths.items():
            shutil.copy2(path, directory / f"{stem}{ext}")
        shutil.copy2(
            PANEL_OUT / f"edfig5_panel{panel}_source_data.tsv",
            directory / f"{stem}_source_data.tsv",
        )


def remove_stale_panel_outputs() -> None:
    """Remove panel files from the previous six-panel ED5 draft."""
    stale_panels = ["d", "e", "f"]
    directories = [PANEL_OUT, PUBLIC_PANELS, REPO_PANELS, FIGURE_BUILD_PANELS]
    for directory in directories:
        if not directory.exists():
            continue
        for panel in stale_panels:
            for pattern in (
                f"edfig5_panel{panel}.*",
                f"edfig5_panel{panel}_source_data.tsv",
                f"Extended_Data_Figure_5_panel_{panel}.*",
                f"Extended_Data_Figure_5_panel_{panel}_source_data.tsv",
            ):
                for path in directory.glob(pattern):
                    path.unlink()
        for path in directory.glob("Extended_Data_Figure_5_shared_similarity_legend.*"):
            path.unlink()


def observed_hcc1143() -> pd.DataFrame:
    config = load_config(DEFAULT_TRUTH_CONFIG_PATH)
    specs = {spec.cell_line: spec for spec in build_dataset_specs(config)}
    membership = pd.read_csv(DEFAULT_AXIS_MEMBERSHIP_PATH, sep="\t")
    return compute_truth_aligned_log_shift_matrix(specs["HCC1143"], config, membership).set_index(
        "target_gene"
    )


def shared_profile_observed(observed: pd.DataFrame) -> pd.DataFrame:
    """Restrict the focused matrices to one common model-audit target contract."""
    shared = set(observed.index.astype(str))
    shared_genes = set(observed.columns.astype(str))
    for model_id in [
        "scgen_hcc_formal_v1",
        "cpa_v0.8.8",
        "shared_mean_baseline",
    ]:
        predicted = load_prediction_matrix(
            PREDICTION_ROOT / model_id / "HCC1143/predicted_shift.tsv.gz"
        )
        shared &= set(predicted["target_gene"].astype(str))
        shared_genes &= set(predicted.columns.astype(str)) - {"target_gene"}
    targets = [target for target in observed.index.astype(str) if target in shared]
    genes = [gene for gene in observed.columns.astype(str) if gene in shared_genes]
    return observed.loc[targets, genes]


def aligned_similarity(
    model_id: str,
    observed: pd.DataFrame,
) -> pd.DataFrame:
    predicted = load_prediction_matrix(
        PREDICTION_ROOT / model_id / "HCC1143/predicted_shift.tsv.gz"
    ).set_index("target_gene")
    targets = [target for target in observed.index if target in predicted.index]
    genes = [gene for gene in observed.columns if gene in predicted.columns]
    return _cosine_similarity_matrix(predicted.loc[targets, genes])


def similarity_order(observed_similarity: pd.DataFrame) -> list[str]:
    distance = np.clip(1.0 - observed_similarity.to_numpy(dtype=float), 0.0, 2.0)
    np.fill_diagonal(distance, 0.0)
    condensed = squareform(distance, checks=False)
    order = leaves_list(linkage(condensed, method="average"))
    return observed_similarity.index[order].astype(str).tolist()


def panel_a(metrics: pd.DataFrame) -> None:
    columns = [
        ("predicted_target_similarity_mean", "mean target\nsimilarity"),
        ("leading_singular_energy_share", "leading singular\nenergy share"),
        ("normalized_inverse_effective_rank", "inverse\neffective rank"),
    ]
    data = metrics.loc[
        metrics["model_id"].isin(PROFILE_MODELS),
        ["model_id", "cell_line"] + [column for column, _ in columns],
    ].copy()
    order = [
        (model, context)
        for model in PROFILE_MODELS
        for context in ["HCC38", "HCC1143"]
        if not data.loc[
            data["model_id"].eq(model) & data["cell_line"].eq(context)
        ].empty
    ]
    data["_order"] = pd.Categorical(
        list(zip(data["model_id"], data["cell_line"])),
        categories=order,
        ordered=True,
    )
    data = data.sort_values("_order")
    raw = data[[column for column, _ in columns]].to_numpy(dtype=float)
    scaled = np.full_like(raw, np.nan)
    for index in range(raw.shape[1]):
        values = raw[:, index]
        finite = np.isfinite(values)
        if finite.any():
            lo, hi = np.nanmin(values), np.nanmax(values)
            scaled[finite, index] = (
                (values[finite] - lo) / (hi - lo) if hi > lo else 0.0
            )
    cmap = LinearSegmentedColormap.from_list(
        "homogenization",
        HOMOGENIZATION_CMAP,
    )
    fig, ax = plt.subplots(figsize=(4.9, 5.25))
    image = ax.imshow(scaled, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    labels = [
        f"{MODEL_LABELS.get(model, model)} {context}"
        for model, context in zip(data["model_id"], data["cell_line"])
    ]
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels(labels, fontsize=5.8)
    ax.set_xticks(range(len(columns)))
    ax.set_xticklabels([label for _, label in columns], fontsize=6.0)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(
        "Axis-free output-homogenization diagnostics",
        loc="left",
        fontsize=7.2,
        fontweight="bold",
        pad=8,
    )
    cbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_ticks([0, 1])
    cbar.set_ticklabels(["low", "high"])
    cbar.ax.tick_params(labelsize=5.2, length=0)
    cbar.outline.set_visible(False)
    cbar.set_label("within-metric scale", fontsize=5.5, labelpad=2)
    source = data.drop(columns="_order")
    source["fill_scale"] = "within metric; raw values are provided in source data"
    save_panel(fig, "a", source)


def similarity_panel(
    panel: str,
    title: str,
    similarity: pd.DataFrame,
    order: list[str],
) -> None:
    matrix = similarity.loc[order, order]
    values = matrix.to_numpy(dtype=float).copy()
    np.fill_diagonal(values, np.nan)
    cmap = LinearSegmentedColormap.from_list(
        "similarity",
        SIMILARITY_CMAP,
    )
    cmap.set_bad("#EFEFEF")
    fig, ax = plt.subplots(figsize=(3.15, 3.05))
    ax.imshow(values, cmap=cmap, vmin=-1, vmax=1, aspect="equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(title, loc="left", fontsize=8.2, fontweight="bold", pad=7)
    source_matrix = matrix.copy()
    source_matrix.index.name = "target_1"
    source_matrix.columns.name = "target_2"
    source = (
        source_matrix.stack(dropna=False)
        .rename("target_target_cosine_similarity")
        .reset_index()
    )
    source["matrix_title"] = title
    source["target_order"] = source["target_1"].map({target: i for i, target in enumerate(order)})
    source["diagonal_masked_in_figure"] = source["target_1"].eq(source["target_2"])
    source["color_scale"] = "shared diverging scale, vmin=-1, center=0, vmax=1; diagonal excluded from color scaling"
    save_panel(fig, panel, source)


def similarity_source(
    title: str,
    similarity: pd.DataFrame,
    order: list[str],
) -> pd.DataFrame:
    matrix = similarity.loc[order, order]
    source_matrix = matrix.copy()
    source_matrix.index.name = "target_1"
    source_matrix.columns.name = "target_2"
    source = (
        source_matrix.stack(dropna=False)
        .rename("target_target_cosine_similarity")
        .reset_index()
    )
    source["matrix_title"] = title
    source["target_order"] = source["target_1"].map({target: i for i, target in enumerate(order)})
    source["diagonal_masked_in_figure"] = source["target_1"].eq(source["target_2"])
    source["color_scale"] = (
        "shared diverging scale, vmin=-1, center=0, vmax=1; "
        "diagonal excluded from color scaling"
    )
    return source


def panel_b_geometry_examples(
    observed_similarity: pd.DataFrame,
    scgen_similarity: pd.DataFrame,
    cpa_similarity: pd.DataFrame,
    shared_mean_similarity: pd.DataFrame,
    order: list[str],
) -> None:
    matrices = [
        ("Observed HCC1143\ntarget geometry", observed_similarity),
        ("scGen HCC1143\npredicted geometry", scgen_similarity),
        ("CPA HCC1143\npredicted geometry", cpa_similarity),
        ("Shared-mean HCC1143\nreference", shared_mean_similarity),
    ]
    cmap = LinearSegmentedColormap.from_list("similarity", SIMILARITY_CMAP)
    cmap.set_bad("#EFEFEF")
    fig, axes = plt.subplots(1, 4, figsize=(9.6, 2.65))
    source_frames = []
    for ax, (title, similarity) in zip(axes, matrices):
        matrix = similarity.loc[order, order]
        values = matrix.to_numpy(dtype=float).copy()
        np.fill_diagonal(values, np.nan)
        ax.imshow(values, cmap=cmap, vmin=-1, vmax=1, aspect="equal")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(title, loc="left", fontsize=7.1, fontweight="bold", pad=5)
        source_frames.append(similarity_source(title.replace("\n", " "), similarity, order))
    fig.suptitle(
        "Focused HCC1143 target-geometry examples",
        x=0.02,
        y=0.995,
        ha="left",
        fontsize=8.0,
        fontweight="bold",
    )
    fig.subplots_adjust(left=0.02, right=0.995, top=0.78, bottom=0.04, wspace=0.10)
    source = pd.concat(source_frames, ignore_index=True)
    save_panel(fig, "b", source)


def save_similarity_legend() -> None:
    cmap = LinearSegmentedColormap.from_list(
        "similarity",
        SIMILARITY_CMAP,
    )
    fig, ax = plt.subplots(figsize=(3.0, 0.55))
    image = ax.imshow(np.linspace(-1, 1, 256)[None, :], cmap=cmap, aspect="auto")
    ax.set_yticks([])
    ax.set_xticks([0, 128, 255], ["−1", "0", "1"], fontsize=5.5)
    ax.set_xlabel("Target-target cosine similarity", fontsize=6.0, labelpad=2)
    for spine in ax.spines.values():
        spine.set_visible(False)
    finalize_manuscript_figure(fig)
    for directory in [PANEL_OUT, PUBLIC_PANELS, REPO_PANELS, FIGURE_BUILD_PANELS]:
        directory.mkdir(parents=True, exist_ok=True)
        stem = directory / "Extended_Data_Figure_5_shared_similarity_legend"
        fig.savefig(stem.with_suffix(".png"), dpi=1200, bbox_inches="tight")
        fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
        fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def panel_c(metrics: pd.DataFrame, identity: pd.DataFrame) -> None:
    data = metrics[
        ["model_id", "cell_line", "predicted_target_similarity_mean"]
    ].merge(
        identity[
            [
                "model_id",
                "cell_line",
                "target_identity_preservation_spearman",
                "target_identity_preservation_status",
            ]
        ],
        on=["model_id", "cell_line"],
        how="left",
    )
    data = data.loc[data["model_id"].isin(PROFILE_MODELS)].copy()
    fig, ax = plt.subplots(figsize=(5.2, 3.5))
    markers = {"HCC38": "o", "HCC1143": "s"}
    highlighted = {
        "scgen_hcc_formal_v1",
        "cpa_v0.8.8",
        "shared_mean_baseline",
    }
    estimable = data.loc[data["target_identity_preservation_status"].eq("estimated")]
    for _, row in estimable.iterrows():
        model_id = str(row["model_id"])
        color = MODEL_COLORS[model_id] if model_id in highlighted else COLORS["point_light"]
        alpha = 0.95 if model_id in highlighted else 0.62
        ax.scatter(
            row["predicted_target_similarity_mean"],
            row["target_identity_preservation_spearman"],
            s=46 if model_id in highlighted else 27,
            marker=markers.get(str(row["cell_line"]), "o"),
            color=color,
            edgecolor="white",
            linewidth=0.5,
            alpha=alpha,
            zorder=3,
        )
        if model_id in {"scgen_hcc_formal_v1", "cpa_v0.8.8"}:
            label_offsets = {
                ("scgen_hcc_formal_v1", "HCC38"): (4, 3, "left", "bottom"),
                ("scgen_hcc_formal_v1", "HCC1143"): (4, 3, "left", "bottom"),
                ("cpa_v0.8.8", "HCC38"): (9, 8, "left", "bottom"),
                ("cpa_v0.8.8", "HCC1143"): (9, -9, "left", "top"),
            }
            dx, dy, ha, va = label_offsets.get(
                (model_id, str(row["cell_line"])),
                (4, 3, "left", "bottom"),
            )
            ax.annotate(
                f"{MODEL_LABELS[model_id]} {str(row['cell_line']).replace('HCC', '')}",
                (
                    row["predicted_target_similarity_mean"],
                    row["target_identity_preservation_spearman"],
                ),
                xytext=(dx, dy),
                textcoords="offset points",
                fontsize=5.4,
                ha=ha,
                va=va,
            )
    ax.axhline(0, color="#C8C8C8", lw=0.7)
    ax.set_xlim(
        min(0.0, float(data["predicted_target_similarity_mean"].min(skipna=True)) - 0.04),
        1.02,
    )
    ax.set_ylim(-0.15, 0.52)
    ax.set_xlabel("Predicted mean target-target similarity (homogenization)", fontsize=6.4)
    ax.set_ylabel("Target-identity Spearman ρ", fontsize=6.4)
    ax.set_title(
        "Homogenization versus target-identity preservation",
        loc="left",
        fontsize=7.2,
        fontweight="bold",
        pad=7,
    )
    ax.grid(False)
    clean_axes(ax)
    ax.legend(
        handles=[
            Line2D([0], [0], marker="o", linestyle="", color="#555555", label="HCC38", markersize=4.5),
            Line2D([0], [0], marker="s", linestyle="", color="#555555", label="HCC1143", markersize=4.5),
        ],
        frameon=False,
        fontsize=5.5,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0.0,
        title="Context",
        title_fontsize=5.7,
    )
    data["interpretation"] = (
        "High predicted similarity indicates homogenization and is not a performance metric."
    )
    data.loc[
        data["model_id"].eq("shared_mean_baseline"),
        "interpretation",
    ] = (
        "Shared-mean reference illustrates complete output homogenization; "
        "target-identity correlation is undefined when predicted geometry is degenerate."
    )
    save_panel(fig, "c", data)


def write_combined_outputs() -> None:
    """Build a lightweight combined figure from the active axis-free panels.

    The user-facing submission workflow uses individual SVG panels, but keeping
    the combined ED5 file synchronized prevents accidental reuse of the previous
    functional-axis draft.
    """
    panel_paths = {
        "a": PANEL_OUT / "edfig5_panela.png",
        "b": PANEL_OUT / "edfig5_panelb.png",
        "c": PANEL_OUT / "edfig5_panelc.png",
    }
    fig = plt.figure(figsize=(11.8, 7.6))
    grid = fig.add_gridspec(
        2,
        2,
        height_ratios=[0.78, 1.0],
        left=0.02,
        right=0.98,
        top=0.98,
        bottom=0.04,
        wspace=0.10,
        hspace=0.05,
    )
    layout = [
        ("a", grid[0, 0]),
        ("c", grid[0, 1]),
        ("b", grid[1, :]),
    ]
    for key, spec in layout:
        ax = fig.add_subplot(spec)
        ax.imshow(plt.imread(panel_paths[key]))
        ax.set_axis_off()
    finalize_manuscript_figure(fig)

    for directory in [OUT, PUBLIC, ROOT / "figures/Extended_Data_Figure_5", FIGURE_BUILD]:
        directory.mkdir(parents=True, exist_ok=True)
        stem = directory / "Extended_Data_Figure_5"
        fig.savefig(stem.with_suffix(".png"), dpi=600, bbox_inches="tight")
        fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
        fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)

    source_frames = []
    for panel in ["a", "b", "c"]:
        source_path = PANEL_OUT / f"edfig5_panel{panel}_source_data.tsv"
        source_frames.append(pd.read_csv(source_path, sep="\t").assign(panel=panel))
    combined_source = pd.concat(source_frames, ignore_index=True, sort=False)
    for directory in [OUT, PUBLIC, ROOT / "figures/Extended_Data_Figure_5", FIGURE_BUILD]:
        directory.mkdir(parents=True, exist_ok=True)
        combined_source.to_csv(
            directory / "Extended_Data_Figure_5_source_data.tsv",
            sep="\t",
            index=False,
        )


def main() -> None:
    apply_manuscript_style()
    remove_stale_panel_outputs()
    metrics = pd.read_csv(METRICS, sep="\t")
    identity = pd.read_csv(IDENTITY, sep="\t")
    panel_a(metrics)

    observed = shared_profile_observed(observed_hcc1143())
    observed_similarity = _cosine_similarity_matrix(observed)
    order = similarity_order(observed_similarity)
    panel_b_geometry_examples(
        observed_similarity,
        aligned_similarity("scgen_hcc_formal_v1", observed),
        aligned_similarity("cpa_v0.8.8", observed),
        aligned_similarity("shared_mean_baseline", observed),
        order,
    )
    save_similarity_legend()
    panel_c(metrics, identity)
    write_combined_outputs()


if __name__ == "__main__":
    main()
