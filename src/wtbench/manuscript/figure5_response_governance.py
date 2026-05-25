from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from wtbench.manuscript.figure_io import ensure_dir, repo_root, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_heading, apply_manuscript_style, clean_axes, finalize_manuscript_figure


FIGURE_ID = "figure5"
PUBLIC_FIGURE_ID = "Figure_5"
FIGURE_TITLE = "Response-program annotation of endpoint-aligned recovery classes"
SCRIPT_PATH = Path("scripts/manuscript/build_figure6_boundary.py")
CLAIM_BOUNDARY = (
    "Response-level enrichment annotates category-associated transcriptomic "
    "programs. It is not target-set mechanism discovery and does not define "
    "endpoint categories or model scores."
)

GSEA = Path("reports/category_response_pathway/contrasts/category_response_contrast_gsea_hallmark.tsv")
GSEA_QC = Path("reports/category_response_pathway/contrasts/category_response_contrast_qc.tsv")

PATHWAYS = [
    "Myc Targets V1",
    "mTORC1 Signaling",
    "E2F Targets",
    "G2-M Checkpoint",
    "Mitotic Spindle",
    "TNF-alpha Signaling via NF-kB",
    "Apical Junction",
    "Glycolysis",
]


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig5_response_governance"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_5"


def manuscript_panel_dir(root: Path) -> Path:
    return manuscript_figure_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / GSEA, root / GSEA_QC]


def contrast_design_source(root: Path) -> pd.DataFrame:
    qc = pd.read_csv(root / GSEA_QC, sep="\t")
    return qc[["context", "contrast_id", "positive_category", "negative_category", "n_genes", "n_targets_positive", "n_targets_negative", "claim_role"]]


def render_contrast_design(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_heading(ax, "a", "Response contrast availability", label_x=-0.09)
    d = df.copy()
    d["contrast_label"] = d["contrast_id"].replace({"Q1_anchor_vs_Q4_low_information": "Anchor vs low-info", "Q1_anchor_vs_middle": "Anchor vs middle"})
    contexts = ["HCC38", "HCC1143"]
    contrasts = ["Anchor vs low-info", "Anchor vs middle"]
    d["n_targets_total"] = d["n_targets_positive"] + d["n_targets_negative"]
    for i, context in enumerate(contexts):
        for j, contrast in enumerate(contrasts):
            row = d.loc[d["context"].eq(context) & d["contrast_label"].eq(contrast)]
            if row.empty:
                ax.scatter(j, i, s=22, color="#E6E6E6", edgecolor="white", linewidth=0.5)
                ax.text(j, i, "-", ha="center", va="center", fontsize=5.4, color="#777777")
            else:
                r = row.iloc[0]
                ax.scatter(
                    j,
                    i,
                    s=28 + float(r["n_targets_total"]) * 5.5,
                    color=COLORS["scgen"],
                    alpha=0.86,
                    edgecolor="white",
                    linewidth=0.6,
                )
                ax.text(j, i, f"{int(r['n_targets_positive'])}/{int(r['n_targets_negative'])}", ha="center", va="center", fontsize=5.4, color="white", weight="bold")
    ax.set_xlim(-0.55, len(contrasts) - 0.45)
    ax.set_ylim(len(contexts) - 0.45, -0.55)
    ax.set_yticks(range(len(contexts)))
    ax.set_yticklabels(contexts, fontsize=6)
    ax.set_xticks(range(len(contrasts)))
    ax.set_xticklabels(contrasts, fontsize=6, rotation=20, ha="right")
    ax.tick_params(length=0)
    ax.set_xlabel("Positive/negative target counts")
    for spine in ax.spines.values():
        spine.set_visible(False)


def gsea_source(root: Path, context: str) -> pd.DataFrame:
    df = pd.read_csv(root / GSEA, sep="\t")
    df = df.loc[df["context"].eq(context) & df["pathway"].isin(PATHWAYS)].copy()
    df["minus_log10_padj"] = -np.log10(df["padj"].clip(lower=1e-12))
    df["contrast_label"] = df["contrast_id"].replace({"Q1_anchor_vs_Q4_low_information": "Anchor vs low-info", "Q1_anchor_vs_middle": "Anchor vs middle"})
    df["pathway"] = pd.Categorical(df["pathway"], categories=PATHWAYS, ordered=True)
    return df.sort_values(["contrast_label", "pathway"])


def render_gsea_dot(ax: plt.Axes, df: pd.DataFrame, panel: str, title: str) -> None:
    add_panel_heading(ax, panel, title, label_x=-0.11)
    contrasts = ["Anchor vs low-info", "Anchor vs middle"]
    y_positions = {p: i for i, p in enumerate(PATHWAYS[::-1])}
    x_positions = {c: i for i, c in enumerate(contrasts)}
    vmax = max(1.0, float(np.nanmax(np.abs(df["NES"]))))
    for _, row in df.iterrows():
        x = x_positions[row["contrast_label"]]
        y = y_positions[row["pathway"]]
        color = COLORS["scgen"] if row["NES"] > 0 else COLORS["gears"]
        size = 18 + min(90, row["minus_log10_padj"] * 15)
        ax.scatter(x, y, s=size, color=color, alpha=0.85, edgecolor="white", linewidth=0.5)
        ax.text(x + 0.08, y, f"{row['NES']:.1f}", va="center", fontsize=4.7)
    ax.set_xticks(range(len(contrasts)))
    ax.set_xticklabels(contrasts, rotation=20, ha="right")
    ax.set_yticks(range(len(PATHWAYS)))
    ax.set_yticklabels(PATHWAYS[::-1])
    ax.set_xlim(-0.45, len(contrasts) - 0.15)
    ax.set_xlabel("Response contrast")
    ax.set_ylabel("Hallmark program")
    ax.grid(False)
    clean_axes(ax)


def cross_context_source(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / GSEA, sep="\t")
    df = df.loc[df["pathway"].isin(PATHWAYS)].copy()
    df["contrast_label"] = df["contrast_id"].replace({"Q1_anchor_vs_Q4_low_information": "Anchor vs low-info", "Q1_anchor_vs_middle": "Anchor vs middle"})
    df["column_label"] = df["context"] + "\n" + df["contrast_label"]
    return df


def render_cross_context_heatmap(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_heading(ax, "d", "Cross-context NES map", label_x=-0.06)
    pivot = df.pivot_table(index="pathway", columns="column_label", values="NES", aggfunc="mean").reindex(PATHWAYS)
    vmax = max(1.0, float(np.nanmax(np.abs(pivot.to_numpy()))))
    im = ax.imshow(pivot.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=5.8)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, fontsize=5.3, rotation=35, ha="right")
    ax.tick_params(length=0)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.iloc[i, j]
            if pd.notna(val):
                ax.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=4.8, color="#222222")
    for spine in ax.spines.values():
        spine.set_visible(False)
    cb = plt.colorbar(im, ax=ax, fraction=0.025, pad=0.015)
    cb.set_label("NES", fontsize=5.5)
    cb.ax.tick_params(labelsize=5)


def _save_panel(root: Path, pid: str, title: str, fig: plt.Figure, source: pd.DataFrame) -> dict[str, Path]:
    stem = f"{FIGURE_ID}_panel{pid}"
    public_stem = f"{PUBLIC_FIGURE_ID}_panel_{pid}"
    src = write_tsv(source, panel_dir(root) / f"{stem}_source_data.tsv")
    public_src = write_tsv(source, manuscript_panel_dir(root) / f"{public_stem}_source_data.tsv")
    png = panel_dir(root) / f"{stem}.png"
    pdf = panel_dir(root) / f"{stem}.pdf"
    public_png = manuscript_panel_dir(root) / f"{public_stem}.png"
    public_pdf = manuscript_panel_dir(root) / f"{public_stem}.pdf"
    finalize_manuscript_figure(fig, font_scale=0.94)
    for path in [png, pdf, public_png, public_pdf]:
        ensure_dir(path.parent)
    fig.savefig(png, dpi=1200, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(public_png, dpi=1200, bbox_inches="tight")
    fig.savefig(public_pdf, bbox_inches="tight")
    plt.close(fig)
    manifest = panel_dir(root) / f"{stem}_manifest.json"
    write_panel_manifest(manifest_path=manifest, repo_root=root, panel_id=f"{FIGURE_ID}{pid}", panel_title=title, script_path=root / SCRIPT_PATH, input_paths=input_paths(root), source_data_path=src, output_paths=[png, pdf], claim_boundary=CLAIM_BOUNDARY)
    write_panel_manifest(manifest_path=manuscript_panel_dir(root) / f"{public_stem}_manifest.json", repo_root=root, panel_id=f"{PUBLIC_FIGURE_ID}{pid}", panel_title=title, script_path=root / SCRIPT_PATH, input_paths=input_paths(root), source_data_path=public_src, output_paths=[public_png, public_pdf], claim_boundary=CLAIM_BOUNDARY)
    return {"source": src, "png": png, "pdf": pdf, "manifest": manifest}


def build_panels(root: Path) -> dict[str, dict[str, Path]]:
    sources = {
        "a": contrast_design_source(root),
        "b": gsea_source(root, "HCC38"),
        "c": gsea_source(root, "HCC1143"),
        "d": cross_context_source(root),
    }
    outputs = {}
    for pid, src in sources.items():
        fig, ax = plt.subplots(figsize={"a": (4.2, 2.4), "b": (4.4, 3.1), "c": (4.4, 3.1), "d": (5.4, 3.2)}[pid])
        {"a": render_contrast_design, "b": lambda a, d: render_gsea_dot(a, d, "b", "HCC38 response-program tendencies"), "c": lambda a, d: render_gsea_dot(a, d, "c", "HCC1143 response-program tendencies"), "d": render_cross_context_heatmap}[pid](ax, src)
        outputs[pid] = _save_panel(root, pid, {"a": "Response contrast availability", "b": "HCC38 Hallmark response GSEA", "c": "HCC1143 Hallmark response GSEA", "d": "Cross-context NES heatmap"}[pid], fig, src)
    return outputs


def build_combined(root: Path, panels: dict[str, dict[str, Path]]) -> None:
    sources = {"a": contrast_design_source(root), "b": gsea_source(root, "HCC38"), "c": gsea_source(root, "HCC1143"), "d": cross_context_source(root)}
    combined = pd.concat([df.assign(panel=pid) for pid, df in sources.items()], ignore_index=True, sort=False)
    source = write_tsv(combined, output_dir(root) / f"{FIGURE_ID}_source_data.tsv")
    public_source = write_tsv(combined, manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}_source_data.tsv")
    fig = plt.figure(figsize=(10.4, 7.4))
    gs = fig.add_gridspec(2, 3, left=0.06, right=0.98, top=0.94, bottom=0.10, wspace=0.34, hspace=0.42, width_ratios=[0.9, 1.0, 1.0])
    axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[0, 2]), fig.add_subplot(gs[1, :])]
    render_contrast_design(axes[0], sources["a"])
    render_gsea_dot(axes[1], sources["b"], "b", "HCC38 response-program tendencies")
    render_gsea_dot(axes[2], sources["c"], "c", "HCC1143 response-program tendencies")
    render_cross_context_heatmap(axes[3], sources["d"])
    finalize_manuscript_figure(fig, font_scale=0.94)
    png = output_dir(root) / f"{FIGURE_ID}.png"
    pdf = output_dir(root) / f"{FIGURE_ID}.pdf"
    public_png = manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}.png"
    public_pdf = manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}.pdf"
    for path in [png, pdf, public_png, public_pdf]:
        ensure_dir(path.parent)
    fig.savefig(png, dpi=1200, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(public_png, dpi=1200, bbox_inches="tight")
    fig.savefig(public_pdf, bbox_inches="tight")
    plt.close(fig)
    write_figure_manifest(manifest_path=output_dir(root) / f"{FIGURE_ID}_panel_manifest.json", repo_root=root, figure_id=FIGURE_ID, figure_title=FIGURE_TITLE, script_path=root / SCRIPT_PATH, panel_manifest_paths=[panels[p]["manifest"] for p in ["a", "b", "c", "d"]], combined_source_data_path=source, output_paths=[png, pdf], input_paths=input_paths(root), claim_boundary=CLAIM_BOUNDARY)
    write_figure_manifest(manifest_path=manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}_panel_manifest.json", repo_root=root, figure_id=PUBLIC_FIGURE_ID, figure_title=FIGURE_TITLE, script_path=root / SCRIPT_PATH, panel_manifest_paths=[manuscript_panel_dir(root) / f"{PUBLIC_FIGURE_ID}_panel_{p}_manifest.json" for p in ["a", "b", "c", "d"]], combined_source_data_path=public_source, output_paths=[public_png, public_pdf], input_paths=input_paths(root), claim_boundary=CLAIM_BOUNDARY)


def copy_to_figure_build(root: Path) -> None:
    src = output_dir(root)
    dst = ensure_dir(root / "figure_build/output/Figure_5")
    pdst = ensure_dir(dst / "panels")
    for ext in [".png", ".pdf", "_source_data.tsv"]:
        s = src / f"{FIGURE_ID}{ext}"
        if s.exists():
            shutil.copy2(s, dst / f"{PUBLIC_FIGURE_ID}{ext}")
    for panel in ["a", "b", "c", "d"]:
        for ext in [".png", ".pdf", "_source_data.tsv"]:
            s = src / "panels" / f"{FIGURE_ID}_panel{panel}{ext}"
            if s.exists():
                shutil.copy2(s, pdst / f"{PUBLIC_FIGURE_ID}_panel_{panel}{ext}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build Figure 5 response-level GSEA annotation.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    apply_manuscript_style()
    ensure_dir(output_dir(root))
    ensure_dir(panel_dir(root))
    ensure_dir(manuscript_figure_dir(root))
    ensure_dir(manuscript_panel_dir(root))
    panels = build_panels(root)
    if not args.panels_only:
        build_combined(root, panels)
        copy_to_figure_build(root)


if __name__ == "__main__":
    main()
