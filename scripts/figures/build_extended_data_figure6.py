#!/usr/bin/env python3
"""Build Extended Data Fig. 6 response-program detail and robustness panels."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from textwrap import wrap

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import pandas as pd

from wtbench.figures.figure_io import ensure_dir, repo_root, write_tsv
from wtbench.figures.hash_manifest import write_panel_manifest
from wtbench.figures.manuscript_style import (
    COLORS,
    apply_manuscript_style,
    clean_axes,
    finalize_manuscript_figure,
    muted_diverging_cmap,
)


FIGURE_ID = "extended_data_figure6"
PUBLIC_FIGURE_ID = "Extended_Data_Figure_6"
SCRIPT_PATH = Path("scripts/figures/build_extended_data_figure6.py")
CLAIM_BOUNDARY = (
    "Response-program enrichment panels annotate category-level response signatures "
    "and aggregation robustness. They do not establish causal pathway mechanisms, "
    "pathway activity or immune-cell/tumor-microenvironment evidence."
)

REACTOME = Path("reports/category_response_pathway/contrasts/category_response_contrast_gsea_reactome.tsv")
GOBP = Path("reports/category_response_pathway/contrasts/category_response_contrast_gsea_gobp.tsv")
HALLMARK_MEDIAN = Path("reports/category_response_pathway/contrasts/category_response_contrast_gsea_hallmark_median_sensitivity.tsv")
HALLMARK_LOO = Path("reports/category_response_pathway/contrasts/category_response_contrast_gsea_hallmark_loo_summary.tsv")

CONTEXTS = ["HCC38", "HCC1143"]
CONTEXT_COLORS = {"HCC38": "#3b827a", "HCC1143": "#73729f"}
CONTRAST_ID = "Q1_anchor_vs_middle"

HALLMARK_PATHWAYS = [
    "Myc Targets V1",
    "E2F Targets",
    "G2-M Checkpoint",
    "Mitotic Spindle",
    "mTORC1 Signaling",
    "Glycolysis",
    "p53 Pathway",
    "TNF-alpha Signaling via NF-kB",
]

REACTOME_TERMS = {
    "Peptide Chain Elongation R-HSA-156902": "Peptide chain\nelongation",
    "Cap-dependent Translation Initiation R-HSA-72737": "Cap-dependent\ninitiation",
    "Nonsense Mediated Decay (NMD) Independent Of Exon Junction Complex (EJC) R-HSA-975956": "Nonsense-mediated\ndecay",
    "rRNA Processing R-HSA-72312": "rRNA processing",
    "Cell Cycle, Mitotic R-HSA-69278": "Mitotic cell cycle",
    "Mitotic Prometaphase R-HSA-68877": "Mitotic\nprometaphase",
    "Cell Cycle Checkpoints R-HSA-69620": "Cell-cycle\ncheckpoints",
    "Resolution Of Sister Chromatid Cohesion R-HSA-2500257": "Sister chromatid\ncohesion",
    "RHO GTPase Cycle R-HSA-9012999": "RHO GTPase\ncycle",
    "Extracellular Matrix Organization R-HSA-1474244": "Extracellular matrix\norganization",
}

GOBP_TERMS = {
    "Cytoplasmic Translation (GO:0002181)": "Cytoplasmic\ntranslation",
    "Macromolecule Biosynthetic Process (GO:0009059)": "Macromolecule\nbiosynthesis",
    "Ribonucleoprotein Complex Biogenesis (GO:0022613)": "RNP-complex\nbiogenesis",
    "Ribosome Biogenesis (GO:0042254)": "Ribosome\nbiogenesis",
    "RNA Processing (GO:0006396)": "RNA processing",
    "Chromatin Organization (GO:0006325)": "Chromatin\norganization",
    "Response to dsRNA (GO:0043331)": "Response to\ndsRNA",
    "Antimicrobial Humoral Response (GO:0019730)": "Antimicrobial/humoral\nannotation",
    "Positive Regulation of Leukocyte Mediated Cytotoxicity (GO:0001912)": "Leukocyte-cytotoxicity\nannotation",
    "Double-Strand Break Repair (GO:0006302)": "Double-strand\nbreak repair",
}

HALLMARK_LABELS = {
    "Myc Targets V1": "MYC Targets V1",
    "E2F Targets": "E2F Targets",
    "G2-M Checkpoint": "G2-M Checkpoint",
    "Mitotic Spindle": "Mitotic Spindle",
    "mTORC1 Signaling": "mTORC1 Signaling",
    "Glycolysis": "Glycolysis",
    "p53 Pathway": "p53 Pathway",
    "TNF-alpha Signaling via NF-kB": "TNF-alpha / NF-κB",
}


def output_dir(root: Path) -> Path:
    return root / "figures" / PUBLIC_FIGURE_ID


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_dir(root: Path) -> Path:
    return root / "manuscript" / "figures" / PUBLIC_FIGURE_ID


def manuscript_panel_dir(root: Path) -> Path:
    return manuscript_dir(root) / "panels"


def build_dir(root: Path) -> Path:
    return root / "figure_build" / "output" / PUBLIC_FIGURE_ID


def build_panel_dir(root: Path) -> Path:
    return build_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / REACTOME, root / GOBP, root / HALLMARK_MEDIAN, root / HALLMARK_LOO]


def add_title(ax: plt.Axes, title: str, *, y: float = 1.055) -> None:
    for loc in ("left", "center", "right"):
        ax.set_title("", loc=loc)
    ax.text(
        0,
        y,
        title,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.6,
        fontweight="bold",
        color=COLORS["text"],
        clip_on=False,
    )


def _q_col(df: pd.DataFrame) -> str:
    return "padj_within_context_contrast" if "padj_within_context_contrast" in df.columns else "padj"


def load_enrichment(root: Path, path: Path, terms: dict[str, str]) -> pd.DataFrame:
    df = pd.read_csv(root / path, sep="\t")
    df = df.loc[
        df["context"].isin(CONTEXTS)
        & df["contrast_id"].eq(CONTRAST_ID)
        & df["pathway"].isin(terms.keys())
    ].copy()
    df["display_label"] = df["pathway"].map(terms)
    df["q_value"] = pd.to_numeric(df[_q_col(df)], errors="coerce")
    df["minus_log10_FDR"] = -np.log10(df["q_value"].clip(lower=1e-12))
    df["term_order"] = df["pathway"].map({term: i for i, term in enumerate(terms.keys())})
    return df.sort_values(["term_order", "context"]).reset_index(drop=True)


def render_enrichment(ax: plt.Axes, df: pd.DataFrame, title: str) -> None:
    add_title(ax, title)
    labels = list(dict.fromkeys(df.sort_values("term_order")["display_label"]))
    y_positions = {label: len(labels) - 1 - i for i, label in enumerate(labels)}
    offsets = {"HCC38": -0.12, "HCC1143": 0.12}
    for _, row in df.iterrows():
        y = y_positions[row["display_label"]] + offsets[row["context"]]
        size = 18 + min(float(row["minus_log10_FDR"]), 6.0) * 8.0
        ax.scatter(
            float(row["NES"]),
            y,
            s=size,
            facecolor=CONTEXT_COLORS[row["context"]],
            edgecolor="white",
            linewidth=0.5,
            alpha=0.9,
            zorder=3,
        )
    ax.axvline(0, color="#A8A8A8", lw=0.7, ls=(0, (2, 2)))
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(list(reversed(labels)))
    ax.set_xlabel("NES (anchors − middle)")
    ax.set_xlim(-2.2, 2.05)
    ax.grid(axis="x", color="#F0F0F0", lw=0.35)
    clean_axes(ax)
    context_handles = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=CONTEXT_COLORS[c], markeredgecolor="white", markersize=5, label=c)
        for c in CONTEXTS
    ]
    leg1 = ax.legend(
        handles=context_handles,
        loc="lower left",
        bbox_to_anchor=(1.015, 0.02),
        borderaxespad=0,
        frameon=False,
        fontsize=5.6,
    )
    ax.add_artist(leg1)
    size_handles = [
        ax.scatter([], [], s=18 + value * 8.0, facecolor="#CFCFCF", edgecolor="#4D4D4D", linewidth=0.3)
        for value in [1, 2, 4]
    ]
    ax.legend(
        size_handles,
        ["1", "2", "4"],
        title="−log10(FDR)",
        loc="upper left",
        bbox_to_anchor=(1.015, 0.98),
        borderaxespad=0,
        frameon=False,
        fontsize=5.1,
        title_fontsize=5.2,
        scatterpoints=1,
        labelspacing=0.35,
        handletextpad=0.5,
    )


def median_source(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / HALLMARK_MEDIAN, sep="\t")
    df = df.loc[df["context"].isin(CONTEXTS) & df["pathway"].isin(HALLMARK_PATHWAYS)].copy()
    df["pathway_label"] = df["pathway"].map(HALLMARK_LABELS)
    return df.reset_index(drop=True)


def render_median(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_title(ax, "Mean-versus-median Hallmark NES")
    ax.axhline(0, color="#C8C8C8", lw=0.7)
    ax.axvline(0, color="#C8C8C8", lw=0.7)
    lim = (-2.05, 1.65)
    ax.plot(lim, lim, color="#A8A8A8", lw=0.8, ls=(0, (2, 2)), zorder=1)
    for context, sub in df.groupby("context"):
        ax.scatter(
            sub["mean_NES"],
            sub["median_NES"],
            s=34,
            facecolor=CONTEXT_COLORS[context],
            edgecolor="white",
            linewidth=0.55,
            alpha=0.9,
            label=context,
            zorder=3,
        )
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.set_xlabel("Mean-signature NES")
    ax.set_ylabel("Median-signature NES")
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.015, 1.0),
        borderaxespad=0,
        frameon=False,
        fontsize=5.6,
    )
    ax.grid(color="#F2F2F2", lw=0.35)
    clean_axes(ax)


def loo_source(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / HALLMARK_LOO, sep="\t")
    df = df.loc[df["context"].isin(CONTEXTS) & df["pathway"].isin(HALLMARK_PATHWAYS)].copy()
    df["pathway_label"] = df["pathway"].map(HALLMARK_LABELS)
    df["pathway"] = pd.Categorical(df["pathway"], categories=HALLMARK_PATHWAYS, ordered=True)
    return df.sort_values(["context", "pathway"]).reset_index(drop=True)


def render_loo(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_title(ax, "Leave-one-anchor-out Hallmark stability")
    labels = [HALLMARK_LABELS[p] for p in HALLMARK_PATHWAYS]
    y_positions = {p: len(HALLMARK_PATHWAYS) - 1 - i for i, p in enumerate(HALLMARK_PATHWAYS)}
    offsets = {"HCC38": -0.14, "HCC1143": 0.14}
    for context, sub in df.groupby("context"):
        for _, row in sub.iterrows():
            y = y_positions[str(row["pathway"])] + offsets[context]
            ax.plot([row["loo_NES_min"], row["loo_NES_max"]], [y, y], color=CONTEXT_COLORS[context], alpha=0.38, lw=2.0, solid_capstyle="round")
            ax.scatter(row["full_NES"], y, s=28, facecolor=CONTEXT_COLORS[context], edgecolor="white", linewidth=0.45, zorder=3)
    ax.axvline(0, color="#A8A8A8", lw=0.7, ls=(0, (2, 2)))
    ax.set_yticks(range(len(HALLMARK_PATHWAYS)))
    ax.set_yticklabels(list(reversed(labels)))
    ax.set_xlabel("Hallmark NES (anchors − middle)")
    ax.set_xlim(-2.15, 1.75)
    ax.grid(axis="x", color="#F0F0F0", lw=0.35)
    clean_axes(ax)
    handles = [
        plt.Line2D([0], [0], marker="o", color=CONTEXT_COLORS[c], markerfacecolor=CONTEXT_COLORS[c], markeredgecolor="white", lw=1.3, markersize=4.5, label=c)
        for c in CONTEXTS
    ]
    ax.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(1.015, 1.0),
        borderaxespad=0,
        frameon=False,
        fontsize=5.6,
    )


def write_combined(root: Path) -> None:
    """Write a synchronized combined preview from the manuscript-facing panels."""
    panel_paths = {
        panel: panel_dir(root) / f"{PUBLIC_FIGURE_ID}_panel_{panel}.png"
        for panel in ("a", "b", "c", "d")
    }
    missing = [str(path) for path in panel_paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing panel PNGs for combined figure: {missing}")

    fig = plt.figure(figsize=(11.8, 7.4))
    grid = fig.add_gridspec(
        2,
        2,
        left=0.02,
        right=0.98,
        top=0.98,
        bottom=0.03,
        wspace=0.05,
        hspace=0.10,
        width_ratios=[1.14, 1.0],
    )
    panel_grid = {
        "a": grid[0, 0],
        "b": grid[0, 1],
        "c": grid[1, 0],
        "d": grid[1, 1],
    }
    for panel, spec in panel_grid.items():
        ax = fig.add_subplot(spec)
        ax.imshow(mpimg.imread(panel_paths[panel]))
        ax.set_axis_off()

    for base in [output_dir(root), manuscript_dir(root), build_dir(root)]:
        ensure_dir(base)
        fig.savefig(base / f"{PUBLIC_FIGURE_ID}.png", dpi=600, bbox_inches="tight")
        fig.savefig(base / f"{PUBLIC_FIGURE_ID}.pdf", bbox_inches="tight")
        fig.savefig(base / f"{PUBLIC_FIGURE_ID}.svg", bbox_inches="tight")
    plt.close(fig)


def _save_to_all_roots(root: Path, panel: str, fig: plt.Figure, source: pd.DataFrame, title: str) -> None:
    stem = f"{PUBLIC_FIGURE_ID}_panel_{panel}"
    source = source.copy()
    for base in [panel_dir(root), manuscript_panel_dir(root), build_panel_dir(root)]:
        ensure_dir(base)
        source_path = write_tsv(source, base / f"{stem}_source_data.tsv")
        png = base / f"{stem}.png"
        pdf = base / f"{stem}.pdf"
        svg = base / f"{stem}.svg"
        fig.savefig(png, dpi=1200, bbox_inches="tight")
        fig.savefig(pdf, bbox_inches="tight")
        fig.savefig(svg, bbox_inches="tight")
        if base == panel_dir(root):
            write_panel_manifest(
                manifest_path=base / f"{stem}_manifest.json",
                repo_root=root,
                panel_id=f"{PUBLIC_FIGURE_ID}{panel}",
                panel_title=title,
                script_path=root / SCRIPT_PATH,
                input_paths=input_paths(root),
                source_data_path=source_path,
                output_paths=[png, pdf, svg],
                claim_boundary=CLAIM_BOUNDARY,
            )


def build_panels(root: Path) -> None:
    apply_manuscript_style()
    reactome = load_enrichment(root, REACTOME, REACTOME_TERMS)
    gobp = load_enrichment(root, GOBP, GOBP_TERMS)
    median = median_source(root)
    loo = loo_source(root)

    panels = {
        "a": (reactome, "Reactome response-program details"),
        "b": (gobp, "GO BP response-program details"),
        "c": (median, "Mean-versus-median Hallmark NES"),
        "d": (loo, "Leave-one-anchor-out Hallmark stability"),
    }
    for panel, (src, title) in panels.items():
        if panel in {"a", "b"}:
            fig, ax = plt.subplots(figsize=(5.7, 3.7))
            render_enrichment(ax, src, title)
        elif panel == "c":
            fig, ax = plt.subplots(figsize=(3.25, 3.05))
            render_median(ax, src)
        else:
            fig, ax = plt.subplots(figsize=(5.1, 3.35))
            render_loo(ax, src)
        finalize_manuscript_figure(fig, font_scale=0.95)
        _save_to_all_roots(root, panel, fig, src, title)
        plt.close(fig)

    combined = pd.concat([df.assign(panel=panel) for panel, (df, _) in panels.items()], ignore_index=True, sort=False)
    for base in [output_dir(root), manuscript_dir(root), build_dir(root)]:
        ensure_dir(base)
        write_tsv(combined, base / f"{PUBLIC_FIGURE_ID}_source_data.tsv")


def write_caption(root: Path) -> None:
    caption = """Extended Data Fig. 6. Response-program details and aggregation robustness.

a, Reactome response-program details. Reactome gene-set enrichment results are shown for category-level endpoint-anchor versus middle-band response signatures. NES values indicate the anchors − middle contrast. Terms are displayed with shortened labels; full gene-set names and statistics are provided in source data and Supplementary Tables.

b, GO Biological Process response-program details. Representative non-redundant GO BP terms are shown for the same response-level contrast. Immune- or antimicrobial-associated GO terms were interpreted as annotation-overlapping stress/response terms in cancer-cell perturbation signatures, not immune-cell activity or tumor-microenvironment evidence.

c, Mean-versus-median Hallmark NES. Hallmark NES values computed from mean-based and median-based category signatures are compared to assess aggregation sensitivity. The diagonal indicates equal NES values.

d, Leave-one-anchor-out Hallmark stability. Points show full endpoint-anchor versus middle-band Hallmark NES values, and horizontal intervals show the range obtained after leaving out one endpoint-anchor target at a time. These analyses assess response-program annotation robustness and do not establish causal pathway mechanisms.
"""
    for base in [output_dir(root), manuscript_dir(root), build_dir(root)]:
        ensure_dir(base)
        (base / f"{PUBLIC_FIGURE_ID}_caption.md").write_text(caption, encoding="utf-8")


def copy_legacy_combined_if_present(root: Path) -> None:
    write_combined(root)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panels-only", action="store_true", help="Kept for wrapper compatibility; combined figure is not assembled.")
    parser.parse_args(argv)
    root = repo_root()
    build_panels(root)
    write_caption(root)
    copy_legacy_combined_if_present(root)
    print(f"Built {PUBLIC_FIGURE_ID} response-program panels in {panel_dir(root)}")


if __name__ == "__main__":
    main()
