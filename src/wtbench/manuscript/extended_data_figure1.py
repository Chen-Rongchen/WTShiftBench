from __future__ import annotations

import argparse
import csv
import warnings
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

FIGURE_ID = "extended_data_figure1"
FIGURE_TITLE = "Dataset familiarization and endpoint inputs"
SCRIPT_PATH = Path("scripts/manuscript/build_extended_data_figure1.py")
CLAIM_BOUNDARY = (
    "These panels are descriptive familiarization of benchmark input datasets and endpoint datasets; "
    "they do not replace the pre-specified truth object, endpoint hierarchy, or adjudication metrics."
)
PANEL_IDS = tuple("abcdefghi")

ROOT = repo_root()

HCC_ENDPOINT_SUMMARY = Path("reports/stage2_truth_driven_bridge/hcc38_hcc1143_rnai_endpoint_consistency/endpoint_consistency_summary.tsv")
K562_ENDPOINT_SUMMARY = Path("reports/stage2_truth_driven_bridge/k562_rnai_endpoint_consistency/endpoint_consistency_summary.tsv")
RNAI_CONVERSION = Path("reports/stage2_rnai_demeter2_conversion/summary.tsv")
HCC38_BRIDGE_AUDIT = Path("reports/stage2_truth_driven_bridge/HCC38/bridge_audit.tsv")
HCC1143_BRIDGE_AUDIT = Path("reports/stage2_truth_driven_bridge/HCC1143/bridge_audit.tsv")
TEMPORAL_BRIDGE_SUMMARY = Path("reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_bridge_summary.tsv")
CRISPR_GENE_DEPENDENCY = Path("depmap/CRISPRGeneDependency.csv")
CANDIDATE_CONTEXT_METADATA = Path("reports/extended_data_candidates/dataset_familiarization_v2/qc/context_metadata.tsv")
CANDIDATE_UMAP = Path("reports/extended_data_candidates/dataset_familiarization_v2/ed_candidate_v2_umap_source_data.tsv")
CANDIDATE_SHIFT = Path("reports/extended_data_candidates/dataset_familiarization_v2/ed_candidate_v2_shift_magnitude_source_data.tsv")


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_extended_data_v1/edfig1_dataset_familiarization"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [
        root / HCC_ENDPOINT_SUMMARY,
        root / K562_ENDPOINT_SUMMARY,
        root / RNAI_CONVERSION,
        root / HCC38_BRIDGE_AUDIT,
        root / HCC1143_BRIDGE_AUDIT,
        root / TEMPORAL_BRIDGE_SUMMARY,
        root / CRISPR_GENE_DEPENDENCY,
        root / CANDIDATE_CONTEXT_METADATA,
        root / CANDIDATE_UMAP,
        root / CANDIDATE_SHIFT,
    ]


def cleanup_generated(root: Path) -> None:
    out = output_dir(root)
    for path in panel_dir(root).glob("edfig1_panel*"):
        path.unlink()
    for suffix in (".png", ".pdf", "_source_data.tsv", "_panel_manifest.json"):
        path = out / f"edfig1{suffix}"
        if path.exists():
            path.unlink()


def write_panel(
    *,
    root: Path,
    panel_id: str,
    panel_title: str,
    source_df: pd.DataFrame,
    render: Callable[[plt.Axes, pd.DataFrame], None],
    width: float,
    height: float,
) -> dict[str, Path]:
    pdir = ensure_dir(panel_dir(root))
    stem = f"edfig1_panel{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    output_paths = save_figure(fig, pdir / f"{stem}.png", pdir / f"{stem}.pdf")
    manifest_path = pdir / f"{stem}_manifest.json"
    write_panel_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        panel_id=f"ED1{panel_id}",
        panel_title=panel_title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": output_paths[0], "pdf": output_paths[1], "manifest": manifest_path}


def build_context_metadata(root: Path) -> pd.DataFrame:
    meta = pd.read_csv(root / CANDIDATE_CONTEXT_METADATA, sep="\t")
    return pd.DataFrame(
        {
            "dataset_kind": "perturbation_expression",
            "dataset_label": meta["context"],
            "role": meta["role"],
            "cells_or_models": meta["n_cells"].map(lambda x: f"{int(x):,} cells"),
            "features": meta["n_genes"].map(lambda x: f"{int(x):,} genes"),
            "benchmark_use": meta.apply(
                lambda row: f"{int(row['n_unique_targets'])} targets; {int(row['n_controls']):,} controls",
                axis=1,
            ),
        }
    )


def build_endpoint_metadata(root: Path) -> pd.DataFrame:
    def csv_matrix_shape(path: Path) -> tuple[int, int]:
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            n_cols = len(header) - 1
            n_rows = sum(1 for _ in reader)
        return n_rows, n_cols

    hcc = pd.read_csv(root / HCC_ENDPOINT_SUMMARY, sep="\t")
    k562 = pd.read_csv(root / K562_ENDPOINT_SUMMARY, sep="\t")
    rnai = pd.read_csv(root / RNAI_CONVERSION, sep="\t")
    crispr_cell_lines, crispr_genes = csv_matrix_shape(root / CRISPR_GENE_DEPENDENCY)

    crispr_counts = [
        f"HCC38 {int(hcc.loc[(hcc['timepoint'].eq('HCC38')) & (hcc['summary_kind'].eq('truth_endpoint_bridge')) & (hcc['platform_pair'].eq('crispr')) & (hcc['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
        f"HCC1143 {int(hcc.loc[(hcc['timepoint'].eq('HCC1143')) & (hcc['summary_kind'].eq('truth_endpoint_bridge')) & (hcc['platform_pair'].eq('crispr')) & (hcc['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
        f"K562 7d {int(k562.loc[(k562['timepoint'].eq('7d')) & (k562['summary_kind'].eq('truth_endpoint_bridge')) & (k562['platform_pair'].eq('crispr')) & (k562['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
        f"K562 13d {int(k562.loc[(k562['timepoint'].eq('13d')) & (k562['summary_kind'].eq('truth_endpoint_bridge')) & (k562['platform_pair'].eq('crispr')) & (k562['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
    ]
    rnai_counts = [
        f"HCC38 {int(hcc.loc[(hcc['timepoint'].eq('HCC38')) & (hcc['summary_kind'].eq('truth_endpoint_bridge')) & (hcc['platform_pair'].eq('rnai')) & (hcc['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
        f"HCC1143 {int(hcc.loc[(hcc['timepoint'].eq('HCC1143')) & (hcc['summary_kind'].eq('truth_endpoint_bridge')) & (hcc['platform_pair'].eq('rnai')) & (hcc['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
        f"K562 7d {int(k562.loc[(k562['timepoint'].eq('7d')) & (k562['summary_kind'].eq('truth_endpoint_bridge')) & (k562['platform_pair'].eq('rnai')) & (k562['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
        f"K562 13d {int(k562.loc[(k562['timepoint'].eq('13d')) & (k562['summary_kind'].eq('truth_endpoint_bridge')) & (k562['platform_pair'].eq('rnai')) & (k562['truth_metric'].eq('real_shift_mean_abs')), 'n_shared_targets'].iloc[0])}",
    ]
    mapped_cell_lines = int(rnai.loc[rnai["metric"].eq("mapped_cell_lines"), "value"].iloc[0])
    genes = int(rnai.loc[rnai["metric"].eq("genes"), "value"].iloc[0])

    return pd.DataFrame(
        [
            {
                "dataset_kind": "endpoint_dataset",
                "dataset_label": "DepMap CRISPR dependency",
                "role": "primary endpoint",
                "cells_or_models": f"{crispr_cell_lines:,} cell lines",
                "features": f"{crispr_genes:,} genes",
                "benchmark_use": "; ".join(crispr_counts),
            },
            {
                "dataset_kind": "endpoint_dataset",
                "dataset_label": "DEMETER2 RNAi",
                "role": "sensitivity endpoint",
                "cells_or_models": f"{mapped_cell_lines:,} mapped cell lines",
                "features": f"{genes:,} genes",
                "benchmark_use": "; ".join(rnai_counts),
            },
        ]
    )


def build_umap_source(root: Path, context: str, shift_df: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(root / CANDIDATE_UMAP, sep="\t")
    df = df.loc[df["context"].eq(context)].copy()
    top_targets = set(
        shift_df.loc[shift_df["context"].eq(context)]
        .sort_values("abs_shift", ascending=False)
        .head(2)["target"]
        .tolist()
    )
    df["is_highlight"] = df["profile"].isin(top_targets)
    return df


def build_shift_source(root: Path, context: str) -> pd.DataFrame:
    df = pd.read_csv(root / CANDIDATE_SHIFT, sep="\t")
    return df.loc[df["context"].eq(context)].sort_values("abs_shift").reset_index(drop=True)


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    def format_dataset_label(row) -> str:
        if row.dataset_kind == "perturbation_expression":
            return f"{row.dataset_label} ({row.role})"
        return f"{row.dataset_label} ({row.role})"

    def format_size(row) -> str:
        return f"{row.features} x {row.cells_or_models}"

    def format_use(row) -> str:
        if row.dataset_kind == "perturbation_expression":
            return row.benchmark_use.replace("; ", " | ")
        parts = row.benchmark_use.split("; ")
        if len(parts) == 4:
            return " / ".join(parts)
        return row.benchmark_use

    ax.set_axis_off()
    ax.set_title("Table: Dataset overview", loc="left", pad=3)
    headers = ["Dataset", "Size", "Benchmark use"]
    x = [0.03, 0.38, 0.64]
    left, right = 0.02, 0.98
    y_top = 0.91
    row_h = 0.088
    section_gap = 0.030

    ax.plot([left, right], [y_top, y_top], color="#222222", lw=0.7, transform=ax.transAxes)

    def draw_header(y: float) -> float:
        header_h = row_h * 0.82
        for xpos, header in zip(x, headers):
            ax.text(xpos, y - header_h / 2, header, fontsize=6.6, fontweight="bold", transform=ax.transAxes, va="center")
        ax.plot([left, right], [y - header_h, y - header_h], color="#BDBDBD", lw=0.55, transform=ax.transAxes)
        return y - header_h

    def draw_rows(y: float, rows: pd.DataFrame, *, fontsize: float = 6.2) -> float:
        for row in rows.itertuples():
            ax.text(x[0], y - row_h / 2, format_dataset_label(row), fontsize=fontsize, transform=ax.transAxes, va="center")
            ax.text(x[1], y - row_h / 2, format_size(row), fontsize=fontsize, transform=ax.transAxes, va="center")
            ax.text(x[2], y - row_h / 2, format_use(row), fontsize=fontsize, transform=ax.transAxes, va="center")
            y -= row_h
        return y

    pert = df.loc[df["dataset_kind"].eq("perturbation_expression")].reset_index(drop=True)
    endpoint = df.loc[df["dataset_kind"].eq("endpoint_dataset")].reset_index(drop=True)

    y = y_top
    ax.text(x[0], y - 0.032, "Perturbation-expression contexts", fontsize=6.7, fontweight="bold", transform=ax.transAxes, va="center")
    y -= 0.044
    y = draw_header(y)
    y = draw_rows(y, pert)

    y -= section_gap
    ax.text(x[0], y - 0.020, "Endpoint datasets", fontsize=6.7, fontweight="bold", transform=ax.transAxes, va="center")
    y -= 0.032
    y = draw_header(y)
    y = draw_rows(y, endpoint, fontsize=6.0)

    ax.plot([left, right], [y - 0.015, y - 0.015], color="#222222", lw=0.7, transform=ax.transAxes)
    # add_panel_label(ax, "a", x=-0.02, y=1.02)  # panel letter removed


def render_umap_panel(ax: plt.Axes, df: pd.DataFrame, panel_id: str, title: str) -> None:
    def draw_umap_axes() -> None:
        x0, y0 = 0.10, 0.10
        x1, y1 = 0.33, 0.32
        ax.annotate("", xy=(x1, y0), xytext=(x0, y0), xycoords="axes fraction", arrowprops=dict(arrowstyle="-|>", lw=0.9, color="#333333"))
        ax.annotate("", xy=(x0, y1), xytext=(x0, y0), xycoords="axes fraction", arrowprops=dict(arrowstyle="-|>", lw=0.9, color="#333333"))
        ax.text((x0 + x1) / 2, y0 - 0.05, "UMAP1", fontsize=5.8, ha="center", va="top", transform=ax.transAxes)
        ax.text(x0 - 0.05, (y0 + y1) / 2, "UMAP2", fontsize=5.8, ha="right", va="center", rotation=90, transform=ax.transAxes)

    control = df.loc[df["is_control"]].iloc[0]
    ax.scatter(control["umap1"], control["umap2"], c="#E58D7C", s=34, edgecolors="white", linewidths=0.8, zorder=5)
    ax.text(control["umap1"], control["umap2"] + 0.35, "control", fontsize=5.4, color="#D95F4B", ha="center", va="bottom")
    pert = df.loc[~df["is_control"]]
    for row in pert.itertuples():
        color = "#2E7D32" if row.is_highlight else "#A9C8C0"
        size = 36 if row.is_highlight else 18
        alpha = 0.85 if row.is_highlight else 0.9
        ax.scatter(row.umap1, row.umap2, c=color, s=size, edgecolors="white", linewidths=0.3, alpha=alpha, zorder=4)
        if row.is_highlight:
            ax.text(
                row.umap1,
                row.umap2,
                row.profile,
                fontsize=5.5,
                color="#1B5E20",
                ha="center",
                va="center",
                fontweight="bold",
                zorder=7,
                path_effects=[pe.withStroke(linewidth=1.4, foreground="white")],
            )
    xr = df["umap1"].max() - df["umap1"].min()
    yr = df["umap2"].max() - df["umap2"].min()
    ax.set_xlim(df["umap1"].min() - max(xr * 0.30, 0.55), df["umap1"].max() + max(xr * 0.12, 0.25))
    ax.set_ylim(df["umap2"].min() - max(yr * 0.24, 0.55), df["umap2"].max() + max(yr * 0.10, 0.25))
    ax.set_title(title, loc="center", fontsize=7.4, pad=2)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    # add_panel_label(ax, panel_id)  # panel letter removed
    # Keep all four UMAP panels the same visual size in the combined figure.
    ax.set_box_aspect(1)
    draw_umap_axes()
    if panel_id == "e":
        ax.legend(
            handles=[
                Line2D([0], [0], marker="o", color="none", markerfacecolor="#E58D7C", markeredgecolor="white", markeredgewidth=0.6, markersize=5.5, label="control"),
                Line2D([0], [0], marker="o", color="none", markerfacecolor="#A9C8C0", markeredgecolor="white", markeredgewidth=0.4, markersize=5.0, label="perturbation"),
            ],
            loc="lower right",
            frameon=False,
            fontsize=5.6,
            borderpad=0.2,
            handletextpad=0.4,
        )


def render_shift_panel(ax: plt.Axes, df: pd.DataFrame, panel_id: str, title: str) -> None:
    y = np.arange(len(df))
    for i, row in enumerate(df.itertuples()):
        ax.plot([0, row.abs_shift], [i, i], color="#72A39A", alpha=0.5, linewidth=0.8)
        ax.scatter(row.abs_shift, i, c="#4B8A5A", s=12, zorder=3, edgecolors="white", linewidths=0.3)
    ax.set_yticks(y)
    ax.set_yticklabels(df["target"], fontsize=5.5)
    ax.set_xlabel("Absolute mean perturbation shift", fontsize=6)
    ax.set_title(title, loc="left", fontsize=7.5)
    clean_axes(ax)
    # add_panel_label(ax, panel_id, x=-0.28)  # panel letter removed
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    shift_all = pd.read_csv(root / CANDIDATE_SHIFT, sep="\t")

    panel_a = pd.concat(
        [
            build_context_metadata(root),
            build_endpoint_metadata(root),
        ],
        ignore_index=True,
    )
    sources = {
        "a": panel_a,
        "b": build_umap_source(root, "HCC38", shift_all),
        "c": build_umap_source(root, "HCC1143", shift_all),
        "d": build_umap_source(root, "K562 7d", shift_all),
        "e": build_umap_source(root, "K562 13d", shift_all),
        "f": build_shift_source(root, "HCC38"),
        "g": build_shift_source(root, "HCC1143"),
        "h": build_shift_source(root, "K562 7d"),
        "i": build_shift_source(root, "K562 13d"),
    }
    return sources


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {
        "a": render_panel_a,
        "b": lambda ax, df: render_umap_panel(ax, df, "b", "HCC38"),
        "c": lambda ax, df: render_umap_panel(ax, df, "c", "HCC1143"),
        "d": lambda ax, df: render_umap_panel(ax, df, "d", "K562 7d"),
        "e": lambda ax, df: render_umap_panel(ax, df, "e", "K562 13d"),
        "f": lambda ax, df: render_shift_panel(ax, df, "f", "HCC38"),
        "g": lambda ax, df: render_shift_panel(ax, df, "g", "HCC1143"),
        "h": lambda ax, df: render_shift_panel(ax, df, "h", "K562 7d"),
        "i": lambda ax, df: render_shift_panel(ax, df, "i", "K562 13d"),
    }[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Dataset overview and endpoint inputs",
        "b": "HCC38 perturbation-profile UMAP",
        "c": "HCC1143 perturbation-profile UMAP",
        "d": "K562 7d perturbation-profile UMAP",
        "e": "K562 13d perturbation-profile UMAP",
        "f": "HCC38 perturbation-shift magnitude",
        "g": "HCC1143 perturbation-shift magnitude",
        "h": "K562 7d perturbation-shift magnitude",
        "i": "K562 13d perturbation-shift magnitude",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> None:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / "edfig1_source_data.tsv")

    fig = plt.figure(figsize=(11.2, 9.55))
    gs = fig.add_gridspec(5, 4, hspace=0.0, wspace=0.40, height_ratios=[0.66, 0.02, 1.0, 0.05, 1.16])
    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[2, 0])
    ax_c = fig.add_subplot(gs[2, 1])
    ax_d = fig.add_subplot(gs[2, 2])
    ax_e = fig.add_subplot(gs[2, 3])
    ax_f = fig.add_subplot(gs[4, 0])
    ax_g = fig.add_subplot(gs[4, 1])
    ax_h = fig.add_subplot(gs[4, 2])
    ax_i = fig.add_subplot(gs[4, 3])
    render_panel_a(ax_a, sources["a"])
    render_umap_panel(ax_b, sources["b"], "b", "HCC38")
    render_umap_panel(ax_c, sources["c"], "c", "HCC1143")
    render_umap_panel(ax_d, sources["d"], "d", "K562 7d")
    render_umap_panel(ax_e, sources["e"], "e", "K562 13d")
    render_shift_panel(ax_f, sources["f"], "f", "HCC38")
    render_shift_panel(ax_g, sources["g"], "g", "HCC1143")
    render_shift_panel(ax_h, sources["h"], "h", "K562 7d")
    render_shift_panel(ax_i, sources["i"], "i", "K562 13d")
    fig.subplots_adjust(top=0.965, bottom=0.07, left=0.05, right=0.99)
    output_paths = save_figure(fig, out / "edfig1.png", out / "edfig1.pdf")
    write_figure_manifest(
        manifest_path=out / "edfig1_panel_manifest.json",
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
    parser = argparse.ArgumentParser(description="Build Extended Data Fig. 1 dataset familiarization panels.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    apply_manuscript_style()
    cleanup_generated(root)
    sources = build_sources(root)
    panel_outputs: dict[str, dict[str, Path]] = {}
    for panel_id in PANEL_IDS:
        width = 10.2 if panel_id == "a" else 3.0
        height = 3.7 if panel_id == "a" else (3.15 if panel_id in {"f", "g", "h", "i"} else 2.9)
        panel_outputs[panel_id] = write_panel(
            root=root,
            panel_id=panel_id,
            panel_title=panel_title(panel_id),
            source_df=sources[panel_id],
            render=render_panel_by_id(panel_id),
            width=width,
            height=height,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
