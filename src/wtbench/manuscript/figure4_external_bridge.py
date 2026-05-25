from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

from wtbench.manuscript.figure_io import ensure_dir, repo_root, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_heading, apply_manuscript_style, clean_axes, finalize_manuscript_figure


FIGURE_ID = "figure4"
PUBLIC_FIGURE_ID = "Figure_4"
FIGURE_TITLE = "External datasets support bridge-form detectability and define temporal/modality boundaries"
SCRIPT_PATH = Path("scripts/manuscript/build_figure4_sweep_controls.py")
CLAIM_BOUNDARY = (
    "External datasets test observed shift-DepMap bridge-form detectability, "
    "endpoint-object portability, and temporal/modality/scale/lineage boundaries. "
    "They are not model-generalization tests."
)

BRIDGE = Path("reports/external_bridge_form_robustness/observed_shift_depmap_bridge_summary.tsv")
LAYERS = Path("reports/resource_governance_strengthening/dataset_governance_decision_table.tsv")
GSE_CAT = Path("reports/gse264667_endpoint_extension/category_grid/gse264667_endpoint_category_composition.tsv")

LAYER_COLORS = {
    "primary_model_audit": COLORS["scgen"],
    "external_bridge_form_boundary": COLORS["gears"],
    "candidate_secondary_endpoint_extension": COLORS["supporting"],
    "excluded_future_registry": "#9A9A9A",
}

CATEGORY_LABELS = {
    "Q1_anchor": "Anchor",
    "Q2_shift_excess": "Shift-excess",
    "Q3_dependency_excess": "Dependency-excess",
    "Q4_low_information": "Low-information",
    "middle": "Middle",
}

CATEGORY_COLORS = {
    "Q1_anchor": COLORS["scgen"],
    "Q2_shift_excess": COLORS["cpa"],
    "Q3_dependency_excess": COLORS["accent_purple"],
    "Q4_low_information": COLORS["low_info"],
    "middle": COLORS["middle"],
}


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig4_external_bridge"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_4"


def manuscript_panel_dir(root: Path) -> Path:
    return manuscript_figure_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / BRIDGE, root / LAYERS, root / GSE_CAT]


def load_bridge(root: Path) -> pd.DataFrame:
    order = [
        "HCC38 day 14",
        "HCC1143 day 14",
        "K562 TF day 7",
        "K562 TF day 13",
        "K562 essential CRISPRi day 6",
        "K562 genome-scale CRISPRi day 8",
        "HepG2 day 7",
        "Jurkat day 7",
    ]
    df = pd.read_csv(root / BRIDGE, sep="\t")
    df["context"] = pd.Categorical(df["context"], categories=order, ordered=True)
    return df.sort_values("context").reset_index(drop=True)


def render_forest(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_heading(ax, "a", "Observed shift-DepMap bridge-form robustness", label_x=-0.12)
    y = np.arange(len(df))[::-1]
    for i, row in df.iterrows():
        yi = y[i]
        color = LAYER_COLORS.get(row["evidence_layer"], "#8F8F8F")
        ax.plot([row["spearman_bootstrap_ci_low"], row["spearman_bootstrap_ci_high"]], [yi, yi], color=color, lw=1.6)
        size = max(28, min(135, np.sqrt(float(row["n_targets_matched_depmap"])) * 1.8))
        ax.scatter(row["spearman_rho"], yi, s=size, color=color, edgecolor="white", linewidth=0.7, zorder=3)
        p = float(row["spearman_permutation_pvalue"])
        ptxt = "P < 0.001" if p <= 0.001 else f"P = {p:.3f}"
        ax.text(1.02, yi, f"n={int(row['n_targets_matched_depmap']):,}; {ptxt}", ha="right", va="center", fontsize=5.7)
    ax.axvline(0, color="#777777", lw=0.7, ls="--")
    ax.set_yticks(y)
    ax.set_yticklabels(df["context"].astype(str))
    ax.set_xlim(-0.22, 1.05)
    ax.set_xlabel("Spearman ρ: observed shift magnitude vs dependency strength")
    ax.grid(axis="x", color="#F5F5F5", lw=0.35)
    clean_axes(ax)


def layer_source(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / LAYERS, sep="\t")
    keep = df.loc[df["decision"].isin(["include_primary_model_audit", "include_external_bridge_boundary", "include_secondary_endpoint_extension", "excluded_or_future_extension"])].copy()
    return keep[["context", "manuscript_layer_label", "resource_role", "supported_claim", "not_used_to_claim"]]


def render_layer_matrix(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_heading(ax, "b", "Evidence-layer governance", label_x=-0.09)
    ax.set_axis_off()
    labels = [
        "Primary model-audit layer",
        "External bridge-form / boundary layer",
        "Secondary endpoint-extension layer",
        "Excluded / future-extension registry",
    ]
    y0 = 0.86
    for i, label in enumerate(labels):
        subset = df.loc[df["manuscript_layer_label"].eq(label)]
        contexts = "; ".join(subset["context"].astype(str).head(4).tolist())
        if len(subset) > 4:
            contexts += "; ..."
        color_key = {
            "Primary model-audit layer": "primary_model_audit",
            "External bridge-form / boundary layer": "external_bridge_form_boundary",
            "Secondary endpoint-extension layer": "candidate_secondary_endpoint_extension",
            "Excluded / future-extension registry": "excluded_future_registry",
        }[label]
        y = y0 - i * 0.20
        ax.add_patch(Rectangle((0.02, y - 0.035), 0.025, 0.07, transform=ax.transAxes, color=LAYER_COLORS[color_key]))
        ax.text(0.06, y + 0.018, label, transform=ax.transAxes, fontsize=6.1, weight="bold", va="center")
        ax.text(0.06, y - 0.035, contexts, transform=ax.transAxes, fontsize=5.2, va="center", color="#444444")


def category_source(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / GSE_CAT, sep="\t")
    return df.loc[df["endpoint_category"].isin(CATEGORY_LABELS)].copy()


def render_category_bars(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_heading(ax, "c", "Secondary endpoint-extension category composition", label_x=-0.09)
    order = ["Q1_anchor", "Q2_shift_excess", "Q3_dependency_excess", "Q4_low_information", "middle"]
    contexts = ["HepG2 day 7", "Jurkat day 7"]
    left = np.zeros(len(contexts))
    for cat in order:
        values = []
        for context in contexts:
            rows = df.loc[df["context"].eq(context) & df["endpoint_category"].eq(cat)]
            values.append(float(rows["fraction_targets"].iloc[0]) if not rows.empty else 0.0)
        ax.barh(contexts, values, left=left, color=CATEGORY_COLORS[cat], edgecolor="white", linewidth=0.6, label=CATEGORY_LABELS[cat])
        left += np.array(values)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Fraction of matched targets")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.43), ncol=3, frameon=False, fontsize=5.5)
    clean_axes(ax)


def boundary_source() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"boundary": "time", "evidence": "K562 day 7 > day 13 directionally", "interpretation": "temporal compatibility matters"},
            {"boundary": "modality", "evidence": "CRISPRi bridge remains detectable", "interpretation": "attenuated versus primary KO"},
            {"boundary": "scale", "evidence": "GWPS rho detectable with large n", "interpretation": "effect size, not p-value alone"},
            {"boundary": "lineage", "evidence": "HepG2/Jurkat secondary extension", "interpretation": "not primary model-audit evidence"},
        ]
    )


def render_boundary(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_heading(ax, "d", "Boundary interpretation", label_x=-0.09)
    ax.set_axis_off()
    y = 0.78
    for _, row in df.iterrows():
        ax.text(0.03, y, row["boundary"], transform=ax.transAxes, fontsize=6.3, weight="bold", va="center")
        ax.text(0.21, y, row["evidence"], transform=ax.transAxes, fontsize=5.4, va="center")
        ax.text(0.68, y, row["interpretation"], transform=ax.transAxes, fontsize=5.4, va="center", color="#444444")
        ax.plot([0.02, 0.98], [y - 0.075, y - 0.075], transform=ax.transAxes, color="#E0E0E0", lw=0.5)
        y -= 0.18


def _save_panel(root: Path, pid: str, title: str, fig: plt.Figure, source: pd.DataFrame) -> dict[str, Path]:
    stem = f"{FIGURE_ID}_panel{pid}"
    public_stem = f"{PUBLIC_FIGURE_ID}_panel_{pid}"
    source_path = write_tsv(source, panel_dir(root) / f"{stem}_source_data.tsv")
    public_source = write_tsv(source, manuscript_panel_dir(root) / f"{public_stem}_source_data.tsv")
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
    write_panel_manifest(manifest_path=manifest, repo_root=root, panel_id=f"{FIGURE_ID}{pid}", panel_title=title, script_path=root / SCRIPT_PATH, input_paths=input_paths(root), source_data_path=source_path, output_paths=[png, pdf], claim_boundary=CLAIM_BOUNDARY)
    write_panel_manifest(manifest_path=manuscript_panel_dir(root) / f"{public_stem}_manifest.json", repo_root=root, panel_id=f"{PUBLIC_FIGURE_ID}{pid}", panel_title=title, script_path=root / SCRIPT_PATH, input_paths=input_paths(root), source_data_path=public_source, output_paths=[public_png, public_pdf], claim_boundary=CLAIM_BOUNDARY)
    return {"source": source_path, "png": png, "pdf": pdf, "manifest": manifest}


def build_panels(root: Path) -> dict[str, dict[str, Path]]:
    sources = {"a": load_bridge(root), "b": layer_source(root), "c": category_source(root), "d": boundary_source()}
    outputs = {}
    for pid, source in sources.items():
        fig, ax = plt.subplots(figsize={"a": (5.6, 3.0), "b": (5.6, 2.6), "c": (4.7, 2.6), "d": (5.2, 2.6)}[pid])
        {"a": render_forest, "b": render_layer_matrix, "c": render_category_bars, "d": render_boundary}[pid](ax, source)
        outputs[pid] = _save_panel(root, pid, {"a": "Bridge forest plot", "b": "Evidence-layer matrix", "c": "GSE264667 category composition", "d": "Boundary summary"}[pid], fig, source)
    return outputs


def build_combined(root: Path, panels: dict[str, dict[str, Path]]) -> None:
    sources = {"a": load_bridge(root), "b": layer_source(root), "c": category_source(root), "d": boundary_source()}
    combined = pd.concat([df.assign(panel=pid) for pid, df in sources.items()], ignore_index=True, sort=False)
    source = write_tsv(combined, output_dir(root) / f"{FIGURE_ID}_source_data.tsv")
    public_source = write_tsv(combined, manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}_source_data.tsv")
    fig = plt.figure(figsize=(10.4, 7.2))
    gs = fig.add_gridspec(2, 2, left=0.06, right=0.98, top=0.94, bottom=0.10, wspace=0.32, hspace=0.42)
    axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])]
    render_forest(axes[0], sources["a"])
    render_layer_matrix(axes[1], sources["b"])
    render_category_bars(axes[2], sources["c"])
    render_boundary(axes[3], sources["d"])
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
    dst = ensure_dir(root / "figure_build/output/Figure_4")
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
    parser = argparse.ArgumentParser(description="Build Figure 4 external bridge-form robustness.")
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
