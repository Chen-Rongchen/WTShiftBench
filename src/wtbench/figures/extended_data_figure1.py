from __future__ import annotations

import argparse
import shutil
import warnings
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from wtbench.figures.figure_io import ensure_dir, repo_root, write_tsv
from wtbench.figures.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.figures.manuscript_style import COLORS, apply_manuscript_style, clean_axes, finalize_manuscript_figure

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

FIGURE_ID = "extended_data_figure1"
PUBLIC_FIGURE_ID = "Extended_Data_Figure_1"
FIGURE_TITLE = "Dataset inventory and perturbation-readout quality control"
SCRIPT_PATH = Path("scripts/figures/build_extended_data_figure1.py")
CLAIM_BOUNDARY = (
    "Extended Data Fig. 1 provides descriptive dataset familiarization and target-gene "
    "readout checks. These panels do not define endpoint categories, model scores, or "
    "cross-dataset model-generalization claims."
)
PANEL_IDS = ("a", "b", "c")

ROOT = repo_root()

CANDIDATE_CONTEXT_METADATA = Path("reports/extended_data_candidates/dataset_familiarization_v2/qc/context_metadata.tsv")
CANDIDATE_UMAP = Path("reports/extended_data_candidates/dataset_familiarization_v2/ed_candidate_v2_umap_source_data.tsv")
TARGET_GENE_EXPR_ARROWS = Path(
    "reports/manuscript_extended_data_v1/edfig1_dataset_familiarization/edfig1_target_gene_expression_arrows.tsv"
)
HCC_SUPPLEMENTAL_EXPR_ARROWS = Path(
    "reports/manuscript_extended_data_v1/edfig1_dataset_familiarization/hcc_supplemental_target_expression_readouts.tsv"
)
EXTERNAL_BRIDGE = Path("reports/external_bridge_form_robustness/observed_shift_depmap_bridge_summary.tsv")
HEPG2_QC = Path("reports/gse264667_endpoint_extension/gse264667_hepg2_day7/materialization_qc.tsv")
JURKAT_QC = Path("reports/gse264667_endpoint_extension/gse264667_jurkat_day7/materialization_qc.tsv")
PREVIOUS_PANEL_A_SOURCE = Path("figures/Extended_Data_Figure_1/panels/Extended_Data_Figure_1_panel_a_source_data.tsv")
PREVIOUS_UMAP_SOURCE = Path("figures/Extended_Data_Figure_1/panels/Extended_Data_Figure_1_panel_b_source_data.tsv")
MATERIALIZED_UMAP_SOURCE = Path(
    "reports/manuscript_extended_data_v1/edfig1_dataset_familiarization/materialized/"
    "edfig1_missing_umap_source_data.tsv"
)
MATERIALIZED_EXPRESSION_SOURCE = Path(
    "reports/manuscript_extended_data_v1/edfig1_dataset_familiarization/materialized/"
    "edfig1_missing_target_expression_source_data.tsv"
)

CONTROL_COLOR = "#E58D7C"
PERT_COLOR = "#A9C8C0"
PERT_EDGE = "#3B827A"
DECREASE_COLOR = "#3B827A"
INCREASE_COLOR = "#D55E00"
UNAVAILABLE_COLOR = "#D6D6D6"

CONTEXT_ORDER = [
    "HCC38",
    "HCC1143",
    "K562 7d",
    "K562 13d",
    "Replogle K562 essential",
    "Replogle K562 GWPS",
    "HepG2 day 7",
    "Jurkat day 7",
]

CONTEXT_DISPLAY = {
    "HCC38": "GSE241115\nHCC38",
    "HCC1143": "GSE241115\nHCC1143",
    "K562 7d": "GSE90063\nK562 TF day 7",
    "K562 13d": "GSE90063\nK562 TF day 13",
    "Replogle K562 essential": "Replogle\nK562 essential",
    "Replogle K562 GWPS": "Replogle\nK562 GWPS",
    "HepG2 day 7": "GSE264667\nHepG2 day 7",
    "Jurkat day 7": "GSE264667\nJurkat day 7",
}

OVERVIEW_LABEL = {
    "HCC38": "GSE241115 (HCC38)",
    "HCC1143": "GSE241115 (HCC1143)",
    "K562 7d": "GSE90063 K562 TF day 7 (K562)",
    "K562 13d": "GSE90063 K562 TF day 13 (K562)",
    "Replogle K562 essential": "Replogle essential CRISPRi (K562)",
    "Replogle K562 GWPS": "Replogle GWPS CRISPRi (K562)",
    "HepG2 day 7": "GSE264667 (HepG2)",
    "Jurkat day 7": "GSE264667 (Jurkat)",
}


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_extended_data_v1/edfig1_dataset_familiarization"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Extended_Data_Figure_1"


def public_figure_dir(root: Path) -> Path:
    return root / "figures/Extended_Data_Figure_1"


def figure_build_dir(root: Path) -> Path:
    return root / "figure_build/output/Extended_Data_Figure_1"


def input_paths(root: Path) -> list[Path]:
    return [
        root / CANDIDATE_CONTEXT_METADATA,
        root / CANDIDATE_UMAP,
        root / TARGET_GENE_EXPR_ARROWS,
        root / HCC_SUPPLEMENTAL_EXPR_ARROWS,
        root / EXTERNAL_BRIDGE,
        root / HEPG2_QC,
        root / JURKAT_QC,
        root / PREVIOUS_PANEL_A_SOURCE,
        root / PREVIOUS_UMAP_SOURCE,
        root / MATERIALIZED_UMAP_SOURCE,
        root / MATERIALIZED_EXPRESSION_SOURCE,
    ]


def cleanup_generated(root: Path) -> None:
    out = output_dir(root)
    for path in panel_dir(root).glob("edfig1_panel*"):
        path.unlink()
    for suffix in (".png", ".pdf", ".svg", "_source_data.tsv", "_panel_manifest.json"):
        path = out / f"edfig1{suffix}"
        if path.exists():
            path.unlink()


def save_panel(fig: plt.Figure, stem: Path, *, bbox_inches: str | None = "tight") -> list[Path]:
    ensure_dir(stem.parent)
    finalize_manuscript_figure(fig)
    paths = [stem.with_suffix(".png"), stem.with_suffix(".pdf"), stem.with_suffix(".svg")]
    save_kw: dict = {"dpi": 1200}
    save_kw["bbox_inches"] = bbox_inches
    for path in paths:
        fig.savefig(path, **save_kw)
    plt.close(fig)
    return paths


def write_panel(
    *,
    root: Path,
    panel_id: str,
    panel_title: str,
    source_df: pd.DataFrame,
    render: Callable[[plt.Axes, pd.DataFrame], None],
    width: float,
    height: float,
    bbox_inches: str | None = "tight",
) -> dict[str, Path]:
    pdir = ensure_dir(panel_dir(root))
    stem = pdir / f"edfig1_panel{panel_id}"
    source_path = write_tsv(source_df, pdir / f"edfig1_panel{panel_id}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    output_paths = save_panel(fig, stem, bbox_inches=bbox_inches)
    manifest_path = pdir / f"edfig1_panel{panel_id}_manifest.json"
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
    return {
        "source": source_path,
        "png": output_paths[0],
        "pdf": output_paths[1],
        "svg": output_paths[2],
        "manifest": manifest_path,
    }


def _fmt_int(value: int | float | str | None) -> str:
    if pd.isna(value):
        return "not available"
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return str(value)


def _size_text(n_genes: int | float | str | None, n_cells: int | float | str | None) -> str:
    if pd.isna(n_genes) or pd.isna(n_cells):
        return "not available"
    return f"{_fmt_int(n_genes)} × {_fmt_int(n_cells)}"


def _load_meta(root: Path) -> pd.DataFrame:
    meta = pd.read_csv(root / CANDIDATE_CONTEXT_METADATA, sep="\t")
    meta["context_norm"] = meta["context"].replace(
        {
            "Dixit 2016 K562 7d": "K562 7d",
            "Dixit 2016 K562 13d": "K562 13d",
            "Replogle K562 essential day 7": "Replogle K562 essential",
        }
    )
    return meta


def build_panel_a_source(root: Path) -> pd.DataFrame:
    meta = _load_meta(root)
    bridge = pd.read_csv(root / EXTERNAL_BRIDGE, sep="\t")
    bridge_targets = dict(zip(bridge["context"], bridge["n_targets_matched_depmap"]))
    previous = pd.DataFrame()
    if (root / PREVIOUS_PANEL_A_SOURCE).exists():
        previous = pd.read_csv(root / PREVIOUS_PANEL_A_SOURCE, sep="\t")
    bridge_context_map = {
        "HCC38": "HCC38 day 14",
        "HCC1143": "HCC1143 day 14",
        "K562 7d": "K562 TF day 7",
        "K562 13d": "K562 TF day 13",
        "Replogle K562 essential": "K562 essential CRISPRi day 6",
        "Replogle K562 GWPS": "K562 genome-scale CRISPRi day 8",
        "HepG2 day 7": "HepG2 day 7",
        "Jurkat day 7": "Jurkat day 7",
    }
    out: list[dict[str, object]] = []
    for context in CONTEXT_ORDER:
        n_cells = n_genes = n_perturbations = None
        source_note = "dataset familiarization QC"
        if context in set(meta["context_norm"]):
            row = meta.loc[meta["context_norm"].eq(context)].iloc[0]
            n_cells, n_genes, n_perturbations = row["n_cells"], row["n_genes"], row["n_unique_targets"]
        elif context == "Replogle K562 GWPS" and not previous.empty:
            prev = previous.loc[previous["context"].eq(context)]
            if not prev.empty:
                n_cells = prev["n_cells"].iloc[0]
                n_genes = prev["n_genes"].iloc[0]
                n_perturbations = bridge_targets.get("K562 genome-scale CRISPRi day 8")
                source_note = "previous active panel source"
        elif context == "HepG2 day 7" and (root / HEPG2_QC).exists():
            row = pd.read_csv(root / HEPG2_QC, sep="\t").iloc[0]
            n_cells, n_genes, n_perturbations = row["n_obs"], row["n_vars"], row["n_targets_output"]
            source_note = "GSE264667 materialization QC"
        elif context == "Jurkat day 7" and (root / JURKAT_QC).exists():
            row = pd.read_csv(root / JURKAT_QC, sep="\t").iloc[0]
            n_cells, n_genes, n_perturbations = row["n_obs"], row["n_vars"], row["n_targets_output"]
            source_note = "GSE264667 materialization QC"
        bridge_context = bridge_context_map.get(context)
        if bridge_context in bridge_targets:
            n_perturbations = bridge_targets[bridge_context]
            source_note = "endpoint-matched bridge count"
        out.append(
            {
                "context": context,
                "dataset_cell_line": OVERVIEW_LABEL[context],
                "size_genes_x_cells": _size_text(n_genes, n_cells),
                "perturbations": f"{_fmt_int(n_perturbations)} matched perturbations",
                "n_genes": n_genes,
                "n_cells": n_cells,
                "n_single_perturbations": n_perturbations,
                "source_note": source_note,
            }
        )
    return pd.DataFrame(out)


def _candidate_umap(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / CANDIDATE_UMAP, sep="\t")
    df["context"] = df["context"].replace(
        {
            "Dixit 2016 K562 7d": "K562 7d",
            "Dixit 2016 K562 13d": "K562 13d",
        }
    )
    df["umap_available"] = True
    return df


def _previous_replogle_umap(root: Path) -> pd.DataFrame:
    p = root / PREVIOUS_UMAP_SOURCE
    if not p.exists():
        return pd.DataFrame(columns=["context", "profile", "umap1", "umap2", "is_control", "is_highlight", "umap_available"])
    df = pd.read_csv(p, sep="\t")
    df = df.loc[df["context"].isin(["Replogle K562", "Replogle K562 essential"])].copy()
    if df.empty:
        return pd.DataFrame(columns=["context", "profile", "umap1", "umap2", "is_control", "is_highlight", "umap_available"])
    df["context"] = "Replogle K562 essential"
    df["umap_available"] = True
    return df


def build_panel_b_source(root: Path) -> pd.DataFrame:
    materialized_path = root / MATERIALIZED_UMAP_SOURCE
    if not materialized_path.exists():
        raise FileNotFoundError(
            f"{materialized_path} missing. Run scripts/figures/materialize_extended_data_figure1.py "
            "with the gears environment before building Extended Data Fig. 1."
        )
    materialized = pd.read_csv(materialized_path, sep="\t")
    materialized["is_highlight"] = False
    materialized["umap_available"] = True
    frames = [_candidate_umap(root), materialized]
    df = pd.concat(frames, ignore_index=True, sort=False)
    if "is_highlight" not in df.columns:
        df["is_highlight"] = False
    df["is_highlight"] = df["is_highlight"].fillna(False).astype(bool)
    missing = [c for c in CONTEXT_ORDER if c not in set(df["context"].dropna())]
    if missing:
        raise ValueError(f"ED1 panel b is missing materialized UMAP contexts: {missing}")
    df["context"] = pd.Categorical(df["context"], categories=CONTEXT_ORDER, ordered=True)
    return df.sort_values(["context", "is_control"], ascending=[True, False]).reset_index(drop=True)


def build_panel_c_source(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / TARGET_GENE_EXPR_ARROWS, sep="\t")
    supplemental_path = root / HCC_SUPPLEMENTAL_EXPR_ARROWS
    if supplemental_path.exists():
        supplemental = pd.read_csv(supplemental_path, sep="\t")
        df = pd.concat(
            [
                df[["context", "target", "expression_control", "expression_perturbed"]],
                supplemental[["context", "target", "expression_control", "expression_perturbed"]],
            ],
            ignore_index=True,
        )
    materialized_path = root / MATERIALIZED_EXPRESSION_SOURCE
    if not materialized_path.exists():
        raise FileNotFoundError(
            f"{materialized_path} missing. Run scripts/figures/materialize_extended_data_figure1.py "
            "with the gears environment before building Extended Data Fig. 1."
        )
    missing_expression = pd.read_csv(materialized_path, sep="\t")
    df = pd.concat(
        [
            df[["context", "target", "expression_control", "expression_perturbed"]],
            missing_expression[["context", "target", "expression_control", "expression_perturbed"]],
        ],
        ignore_index=True,
    )
    df["context"] = df["context"].replace(
        {
            "Replogle K562 essential": "Replogle K562 essential",
        }
    )
    df["delta"] = df["expression_perturbed"] - df["expression_control"]
    df["abs_delta"] = df["delta"].abs()
    df["direction"] = np.where(df["delta"] > 0, "increased", "decreased_or_unchanged")
    df["expression_available"] = True
    # Every mappable target gene is shown. Target names remain in source data,
    # while the panel uses an absolute-change rank to remain readable at scale.
    df["shown_in_panel"] = True
    missing = [c for c in CONTEXT_ORDER if c not in set(df["context"].dropna())]
    if missing:
        raise ValueError(f"ED1 panel c is missing target-expression contexts: {missing}")
    df["context"] = pd.Categorical(df["context"], categories=CONTEXT_ORDER, ordered=True)
    return df.sort_values(["context", "abs_delta"], ascending=[True, False], na_position="last").reset_index(drop=True)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    return {
        "a": build_panel_a_source(root),
        "b": build_panel_b_source(root),
        "c": build_panel_c_source(root),
    }


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Dataset overview", loc="left", fontsize=7.4, fontweight="bold", pad=2)
    headers = ["Dataset (cell line)", "Size (genes × cells)", "Matched perturbations"]
    x = [0.025, 0.56, 0.78]
    y_top = 0.90
    row_h = 0.086
    left, right = 0.02, 0.985
    ax.plot([left, right], [y_top, y_top], color="#222222", lw=0.75, transform=ax.transAxes, clip_on=False)
    header_y = y_top - 0.050
    for xpos, header in zip(x, headers):
        ax.text(xpos, header_y, header, transform=ax.transAxes, fontsize=6.8, fontweight="bold", va="center")
    ax.plot([left, right], [y_top - 0.088, y_top - 0.088], color="#BDBDBD", lw=0.55, transform=ax.transAxes, clip_on=False)
    y = y_top - 0.088
    for i, row in enumerate(df.itertuples(index=False)):
        yc = y - row_h / 2
        if i % 2 == 0:
            ax.add_patch(
                plt.Rectangle(
                    (left, y - row_h),
                    right - left,
                    row_h,
                    transform=ax.transAxes,
                    facecolor="#FAFAFA",
                    edgecolor="none",
                    zorder=0,
                )
            )
        ax.text(x[0], yc, row.dataset_cell_line, transform=ax.transAxes, fontsize=6.35, va="center")
        ax.text(x[1], yc, row.size_genes_x_cells, transform=ax.transAxes, fontsize=6.35, va="center")
        ax.text(x[2], yc, row.perturbations, transform=ax.transAxes, fontsize=6.35, va="center")
        ax.plot([left, right], [y - row_h, y - row_h], color="#ECECEC", lw=0.4, transform=ax.transAxes, clip_on=False)
        y -= row_h
    ax.plot([left, right], [y, y], color="#222222", lw=0.75, transform=ax.transAxes, clip_on=False)


def _draw_umap_axes(ax: plt.Axes) -> None:
    x0, y0 = 0.10, 0.10
    x1, y1 = 0.30, 0.30
    ax.annotate("", xy=(x1, y0), xytext=(x0, y0), xycoords="axes fraction", arrowprops=dict(arrowstyle="-|>", lw=0.7, color="#444444"))
    ax.annotate("", xy=(x0, y1), xytext=(x0, y0), xycoords="axes fraction", arrowprops=dict(arrowstyle="-|>", lw=0.7, color="#444444"))
    ax.text((x0 + x1) / 2, y0 - 0.055, "UMAP1", transform=ax.transAxes, ha="center", va="top", fontsize=5.4)
    ax.text(x0 - 0.055, (y0 + y1) / 2, "UMAP2", transform=ax.transAxes, ha="right", va="center", rotation=90, fontsize=5.4)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    fig = ax.figure
    ax.remove()
    gs = fig.add_gridspec(2, 4, left=0.045, right=0.982, bottom=0.155, top=0.875, wspace=0.12, hspace=0.30)
    fig.text(0.045, 0.935, "UMAP of dataset-level perturbation profiles", fontsize=7.4, fontweight="bold", ha="left", va="center")
    for i, context in enumerate(CONTEXT_ORDER):
        sub_ax = fig.add_subplot(gs[i // 4, i % 4])
        sub = df.loc[df["context"].astype(str).eq(context)].copy()
        sub_ax.set_title(CONTEXT_DISPLAY[context], fontsize=6.7, fontweight="bold", pad=2)
        sub_ax.set_xticks([])
        sub_ax.set_yticks([])
        for spine in sub_ax.spines.values():
            spine.set_visible(False)
        sub_ax.set_box_aspect(1)
        controls = sub.loc[sub["is_control"].fillna(False).astype(bool)]
        pert = sub.loc[~sub["is_control"].fillna(False).astype(bool)]
        dense = len(pert) > 500
        sub_ax.scatter(
            pert["umap1"],
            pert["umap2"],
            s=2.0 if dense else 10.0,
            color=PERT_COLOR,
            edgecolor="none",
            alpha=0.42 if dense else 0.78,
            rasterized=False,
            zorder=2,
        )
        if not controls.empty:
            sub_ax.scatter(
                controls["umap1"],
                controls["umap2"],
                s=26 if dense else 34,
                color=CONTROL_COLOR,
                edgecolor="white",
                lw=0.6,
                zorder=5,
            )
            ctrl = controls.iloc[0]
            sub_ax.annotate(
                "control",
                xy=(ctrl["umap1"], ctrl["umap2"]),
                xytext=(0, 8),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=5.3,
                color="#B85749",
                path_effects=[pe.withStroke(linewidth=1.3, foreground="white")],
            )
        xr = float(sub["umap1"].max() - sub["umap1"].min())
        yr = float(sub["umap2"].max() - sub["umap2"].min())
        sub_ax.set_xlim(sub["umap1"].min() - max(0.25 * xr, 0.35), sub["umap1"].max() + max(0.10 * xr, 0.25))
        sub_ax.set_ylim(sub["umap2"].min() - max(0.22 * yr, 0.35), sub["umap2"].max() + max(0.10 * yr, 0.25))
        _draw_umap_axes(sub_ax)
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=CONTROL_COLOR, markeredgecolor="white", markeredgewidth=0.6, markersize=5.8, label="control"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=PERT_COLOR, markeredgecolor="none", markersize=5.0, label="perturbation"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.045), ncol=2, frameon=False, fontsize=6.1)


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    fig = ax.figure
    ax.remove()
    gs = fig.add_gridspec(2, 4, left=0.070, right=0.985, bottom=0.155, top=0.865, wspace=0.42, hspace=0.42)
    fig.text(0.070, 0.935, "Change of perturbation target gene expression", fontsize=7.4, fontweight="bold", ha="left", va="center")
    for i, context in enumerate(CONTEXT_ORDER):
        sub_ax = fig.add_subplot(gs[i // 4, i % 4])
        sub = df.loc[df["context"].astype(str).eq(context)].copy()
        sub_ax.set_title(
            CONTEXT_DISPLAY[context],
            fontsize=6.45,
            fontweight="bold",
            pad=2,
        )
        shown = sub.loc[sub["shown_in_panel"].fillna(False).astype(bool)].sort_values("abs_delta", ascending=False)
        shown = shown.reset_index(drop=True)
        y = np.arange(len(shown), dtype=float)
        x0 = shown["expression_control"].to_numpy(float)
        delta = shown["delta"].to_numpy(float)
        increased = delta > 0
        dense = len(shown) > 250
        very_dense = len(shown) > 1500
        sub_ax.scatter(
            x0,
            y,
            s=0.7 if very_dense else (1.2 if dense else 5.5),
            color="#BDBDBD",
            alpha=0.28 if very_dense else (0.38 if dense else 0.75),
            edgecolor="none",
            rasterized=very_dense,
            zorder=2,
        )
        for mask, color in ((~increased, DECREASE_COLOR), (increased, INCREASE_COLOR)):
            if not np.any(mask):
                continue
            sub_ax.quiver(
                x0[mask],
                y[mask],
                delta[mask],
                np.zeros(mask.sum()),
                angles="xy",
                scale_units="xy",
                scale=1,
                width=0.0010 if very_dense else (0.0015 if dense else 0.0030),
                headwidth=3.2,
                headlength=4.2,
                headaxislength=3.8,
                color=color,
                alpha=0.32 if very_dense else (0.48 if dense else 0.92),
                rasterized=very_dense,
                zorder=3,
            )
        sub_ax.set_yticks([])
        if i // 4 == 1:
            sub_ax.set_xlabel("Target-gene expression", fontsize=6.2)
        clean_axes(sub_ax)
        sub_ax.grid(axis="x", color="#EFEFEF", lw=0.45)
        xmin = float(np.nanmin([shown["expression_control"].min(), shown["expression_perturbed"].min()]))
        xmax = float(np.nanmax([shown["expression_control"].max(), shown["expression_perturbed"].max()]))
        span = xmax - xmin
        sub_ax.set_xlim(xmin - 0.06 * span - 0.02, xmax + 0.08 * span + 0.02)
        sub_ax.set_ylim(len(shown) - 0.5, -0.5)
    fig.text(
        0.014,
        0.50,
        "Perturbation target genes (ranked by absolute change)",
        rotation=90,
        ha="center",
        va="center",
        fontsize=6.5,
    )
    handles = [
        Line2D([0, 1], [0, 0], color=DECREASE_COLOR, marker=">", markevery=[1], lw=0.9, markersize=4.5, label="decreased or unchanged"),
        Line2D([0, 1], [0, 0], color=INCREASE_COLOR, marker=">", markevery=[1], lw=0.9, markersize=4.5, label="increased"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.52, 0.045), ncol=2, frameon=False, fontsize=6.0)


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {
        "a": render_panel_a,
        "b": render_panel_b,
        "c": render_panel_c,
    }[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Dataset overview",
        "b": "UMAP of dataset-level perturbation profiles",
        "c": "Perturbation target-gene expression change",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> None:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / "edfig1_source_data.tsv")

    fig = plt.figure(figsize=(12.4, 9.0))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.15, 1.95, 2.25], hspace=0.34)
    render_panel_a(fig.add_subplot(gs[0, 0]), sources["a"])
    render_panel_b(fig.add_subplot(gs[1, 0]), sources["b"])
    render_panel_c(fig.add_subplot(gs[2, 0]), sources["c"])
    output_paths = save_panel(fig, out / "edfig1", bbox_inches="tight")
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


def sync_public_outputs(root: Path) -> None:
    src = output_dir(root)
    targets = [public_figure_dir(root), figure_build_dir(root), manuscript_figure_dir(root)]
    for target in targets:
        ensure_dir(target / "panels")
        for ext in (".png", ".pdf", ".svg", "_source_data.tsv"):
            src_file = src / f"edfig1{ext}"
            if src_file.exists():
                shutil.copy2(src_file, target / f"{PUBLIC_FIGURE_ID}{ext}")
        for panel_id in PANEL_IDS:
            for ext in (".png", ".pdf", ".svg", "_source_data.tsv"):
                src_file = src / "panels" / f"edfig1_panel{panel_id}{ext}"
                if src_file.exists():
                    shutil.copy2(src_file, target / "panels" / f"{PUBLIC_FIGURE_ID}_panel_{panel_id}{ext}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build Extended Data Fig. 1 dataset familiarization panels.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    apply_manuscript_style()
    cleanup_generated(root)
    sources = build_sources(root)
    panel_specs = {
        "a": (7.2, 2.45),
        "b": (10.6, 4.9),
        "c": (11.6, 5.6),
    }
    panel_outputs: dict[str, dict[str, Path]] = {}
    for panel_id in PANEL_IDS:
        width, height = panel_specs[panel_id]
        panel_outputs[panel_id] = write_panel(
            root=root,
            panel_id=panel_id,
            panel_title=panel_title(panel_id),
            source_df=sources[panel_id],
            render=render_panel_by_id(panel_id),
            width=width,
            height=height,
            bbox_inches="tight",
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)
    sync_public_outputs(root)


if __name__ == "__main__":
    main()
