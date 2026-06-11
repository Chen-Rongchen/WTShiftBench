#!/usr/bin/env python3
"""Build Extended Data Fig. 3 as one raw external-bridge small-multiple panel."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

from wtbench.manuscript.figure_io import ensure_dir, repo_root, write_tsv
from wtbench.manuscript.manuscript_style import (
    COLORS,
    apply_manuscript_style,
    clean_axes,
    finalize_manuscript_figure,
)


PUBLIC_FIGURE_ID = "Extended_Data_Figure_3"
SCRIPT_PATH = Path("scripts/manuscript/build_extended_data_figure3_raw_bridge_small_multiples.py")

INPUT_PANEL_DIR = Path("figure_build/output/Extended_Data_Figure_3/panels")
CONTEXTS = [
    ("a", "K562 TF day 7", "K562 TF day 7", 0.028),
    ("b", "K562 TF day 13", "K562 TF day 13", 0.149),
    ("c", "K562 essential CRISPRi day 6", "K562 essential CRISPRi day 6", 0.001),
    ("d", "K562 genome-wide CRISPRi day 8", "K562 genome-wide CRISPRi day 8", 0.001),
    ("e", "HepG2 day 7", "HepG2 day 7", 0.001),
    ("f", "Jurkat day 7", "Jurkat day 7", 0.001),
]

POINT_COLOR = "#2B8CBE"


def output_dirs(root: Path) -> list[Path]:
    return [
        root / "figure_build" / "output" / PUBLIC_FIGURE_ID,
        root / "figures" / PUBLIC_FIGURE_ID,
        root / "manuscript" / "figures" / PUBLIC_FIGURE_ID,
    ]


def load_context(root: Path, panel_id: str, title: str, p_value: float) -> pd.DataFrame:
    path = root / INPUT_PANEL_DIR / f"{PUBLIC_FIGURE_ID}_panel_{panel_id}_source_data.tsv"
    df = pd.read_csv(path, sep="\t")
    out = df[["target_gene", "real_shift_mean_abs", "depmap_gene_dependency"]].copy()
    out["context"] = title
    out["empirical_p"] = p_value
    return out


def build_source(root: Path) -> pd.DataFrame:
    legacy_paths = [
        root / INPUT_PANEL_DIR / f"{PUBLIC_FIGURE_ID}_panel_{panel_id}_source_data.tsv"
        for panel_id, *_ in CONTEXTS
    ]
    if not all(path.exists() for path in legacy_paths):
        for source_path in [
            root / "figure_build" / "output" / PUBLIC_FIGURE_ID / f"{PUBLIC_FIGURE_ID}_source_data.tsv",
            root / "figures" / PUBLIC_FIGURE_ID / f"{PUBLIC_FIGURE_ID}_source_data.tsv",
            root / "manuscript" / "figures" / PUBLIC_FIGURE_ID / f"{PUBLIC_FIGURE_ID}_source_data.tsv",
        ]:
            if source_path.exists():
                return pd.read_csv(source_path, sep="\t")
        missing = ", ".join(str(path.relative_to(root)) for path in legacy_paths if not path.exists())
        raise FileNotFoundError(f"Missing Extended Data Fig. 3 source inputs: {missing}")
    return pd.concat(
        [load_context(root, panel_id, title, p_value) for panel_id, title, _, p_value in CONTEXTS],
        ignore_index=True,
    )


def format_p(p_value: float) -> str:
    return f"{p_value:.3f}" if p_value >= 0.001 else "<0.001"


def render_context(ax: plt.Axes, df: pd.DataFrame, title: str, p_value: float) -> None:
    x = pd.to_numeric(df["depmap_gene_dependency"], errors="coerce")
    y = pd.to_numeric(df["real_shift_mean_abs"], errors="coerce")
    keep = x.notna() & y.notna()
    x = x.loc[keep]
    y = y.loc[keep]
    rho = float(spearmanr(x, y).statistic)
    n = int(keep.sum())
    size = 22 if n <= 20 else 8 if n <= 2000 else 5
    alpha = 0.70 if n <= 20 else 0.36 if n <= 2000 else 0.25
    ax.scatter(x, y, s=size, color=POINT_COLOR, alpha=alpha, edgecolors="none", rasterized=False)
    ax.text(
        0.045,
        0.90,
        f"Spearman rho = {rho:.3f}\nn={n}; P = {format_p(p_value)}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.0,
        color=COLORS["text"],
    )
    ax.set_title(title, loc="left", fontsize=8.2, fontweight="bold", pad=5)
    ax.set_xlabel("CRISPR dependency strength")
    ax.set_ylabel("Observed shift mean abs")
    ax.grid(False)
    clean_axes(ax)


def render_figure(source: pd.DataFrame) -> plt.Figure:
    apply_manuscript_style()
    fig, axes = plt.subplots(2, 3, figsize=(10.6, 6.4))
    for ax, (_, title, display_title, p_value) in zip(axes.flat, CONTEXTS):
        render_context(ax, source.loc[source["context"].eq(title)], display_title, p_value)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.92, bottom=0.10, wspace=0.34, hspace=0.48)
    finalize_manuscript_figure(fig, font_scale=1.0)
    return fig


def clear_legacy_panels(out_dir: Path) -> None:
    panel_dir = out_dir / "panels"
    if not panel_dir.exists():
        return
    for path in panel_dir.glob(f"{PUBLIC_FIGURE_ID}_panel_*"):
        path.unlink()


def write_caption(root: Path) -> None:
    caption = """Extended Data Fig. 3. Raw external bridge evidence across perturbation contexts.

Raw matched-target scatterplots show continuous observed transcriptomic-shift magnitude versus CRISPR dependency strength across K562 temporal-boundary, Replogle scale/target-universe-boundary and GSE264667 secondary endpoint-extension contexts. Each point represents one matched perturbation target. Spearman rho, empirical P and matched-target count are shown within each small multiple. These panels use raw continuous values, not percentile endpoint planes or model predictions. Raw shift-magnitude scales are context-specific and are not interpreted as directly comparable across datasets; cross-context bridge strength is summarized using rank-based Spearman rho. These panels provide raw bridge-form evidence underlying Fig. 4 and are not model predictions, direct DepMap predictions or cross-dataset model-generalization tests.
"""
    for out_dir in output_dirs(root):
        ensure_dir(out_dir)
        (out_dir / f"{PUBLIC_FIGURE_ID}_caption.md").write_text(caption, encoding="utf-8")


def main() -> None:
    root = repo_root()
    source = build_source(root)
    fig = render_figure(source)
    for out_dir in output_dirs(root):
        ensure_dir(out_dir)
        clear_legacy_panels(out_dir)
        panel_dir = out_dir / "panels"
        ensure_dir(panel_dir)
        write_tsv(source, out_dir / f"{PUBLIC_FIGURE_ID}_source_data.tsv")
        write_tsv(source, panel_dir / f"{PUBLIC_FIGURE_ID}_panel_a_source_data.tsv")
        fig.savefig(out_dir / f"{PUBLIC_FIGURE_ID}.png", dpi=1200, bbox_inches="tight")
        fig.savefig(out_dir / f"{PUBLIC_FIGURE_ID}.pdf", bbox_inches="tight")
        fig.savefig(out_dir / f"{PUBLIC_FIGURE_ID}.svg", bbox_inches="tight")
        fig.savefig(panel_dir / f"{PUBLIC_FIGURE_ID}_panel_a.png", dpi=1200, bbox_inches="tight")
        fig.savefig(panel_dir / f"{PUBLIC_FIGURE_ID}_panel_a.pdf", bbox_inches="tight")
        fig.savefig(panel_dir / f"{PUBLIC_FIGURE_ID}_panel_a.svg", bbox_inches="tight")
    plt.close(fig)
    write_caption(root)
    print(f"Built {PUBLIC_FIGURE_ID} raw external bridge small multiples")


if __name__ == "__main__":
    main()
