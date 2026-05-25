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


FIGURE_ID = "figure2"
PUBLIC_FIGURE_ID = "Figure_2"
FIGURE_TITLE = "Primary HCC contexts establish the endpoint-recovery object"
SCRIPT_PATH = Path("scripts/manuscript/build_figure2_anchor_tiering.py")
CLAIM_BOUNDARY = (
    "HCC38/HCC1143 define the primary endpoint-recovery object for model audit. "
    "Anchor and covariate summaries qualify claim wording and do not establish "
    "fully deconfounded target-level causal effects."
)

JOINT_GRID = Path("reports/truth_bridge_decomposition/target_level_joint_grid.tsv")
NULL_SUMMARY = Path("reports/manuscript_permutation_null_v1/bridge_rho_permutation_summary.tsv")

CATEGORY_ORDER = ["Q1_anchor", "Q2_transcriptomic_excess", "Q3_dependency_excess", "Q4_low_information", "middle"]
CATEGORY_LABELS = {
    "Q1_anchor": "Anchor",
    "Q2_transcriptomic_excess": "Shift-excess",
    "Q3_dependency_excess": "Dependency-excess",
    "Q4_low_information": "Low-information",
    "middle": "Middle",
}
CATEGORY_COLORS = {
    "Q1_anchor": COLORS["scgen"],
    "Q2_transcriptomic_excess": COLORS["cpa"],
    "Q3_dependency_excess": COLORS["accent_purple"],
    "Q4_low_information": COLORS["low_info"],
    "middle": COLORS["middle"],
}


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig2_primary_hcc_object"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_2"


def manuscript_panel_dir(root: Path) -> Path:
    return manuscript_figure_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / JOINT_GRID, root / NULL_SUMMARY]


def load_grid(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / JOINT_GRID, sep="\t")
    df["category_label"] = df["joint_grid"].map(CATEGORY_LABELS).fillna(df["joint_grid"])
    return df


def scatter_source(root: Path, cell_line: str) -> pd.DataFrame:
    return load_grid(root).loc[lambda d: d["cell_line"].eq(cell_line)].copy()


def render_scatter(ax: plt.Axes, df: pd.DataFrame, panel: str, title: str) -> None:
    add_panel_heading(ax, panel, title, label_x=-0.12)
    for cat in CATEGORY_ORDER:
        sub = df.loc[df["joint_grid"].eq(cat)]
        ax.scatter(
            sub["depmap_quantile"] * 100,
            sub["shift_quantile"] * 100,
            s=30,
            color=CATEGORY_COLORS[cat],
            edgecolor="white",
            linewidth=0.5,
            alpha=0.88,
            label=CATEGORY_LABELS[cat],
        )
    rho = df[["depmap_strength", "real_shift_mean_abs"]].corr(method="spearman").iloc[0, 1]
    ax.axvline(25, color="#BDBDBD", lw=0.8, ls="--")
    ax.axvline(75, color="#BDBDBD", lw=0.8, ls="--")
    ax.axhline(25, color="#BDBDBD", lw=0.8, ls="--")
    ax.axhline(75, color="#BDBDBD", lw=0.8, ls="--")
    ax.plot([0, 100], [0, 100], color="#CFCFCF", lw=0.8, ls=":", zorder=0)
    ax.text(0.04, 0.96, f"Spearman ρ = {rho:.3f}\nn = {len(df)}", transform=ax.transAxes, va="top", fontsize=6.0, bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 1.4})
    ax.set_xlim(-2, 102)
    ax.set_ylim(-2, 102)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_xlabel("Dependency percentile (-DepMap)")
    ax.set_ylabel("Observed shift percentile")
    ax.grid(False)
    clean_axes(ax)


def category_source(root: Path) -> pd.DataFrame:
    df = load_grid(root)
    out = df.groupby(["cell_line", "joint_grid"], dropna=False).size().reset_index(name="n_targets")
    out["category_label"] = out["joint_grid"].map(CATEGORY_LABELS)
    out["fraction"] = out["n_targets"] / out.groupby("cell_line")["n_targets"].transform("sum")
    return out


def render_category(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_heading(ax, "c", "Frozen endpoint-category composition", label_x=-0.10)
    cell_lines = ["HCC38", "HCC1143"]
    left = np.zeros(len(cell_lines))
    for cat in CATEGORY_ORDER:
        vals = []
        for cell in cell_lines:
            row = df.loc[df["cell_line"].eq(cell) & df["joint_grid"].eq(cat)]
            vals.append(float(row["fraction"].iloc[0]) if not row.empty else 0.0)
        ax.barh(cell_lines, vals, left=left, color=CATEGORY_COLORS[cat], edgecolor="white", linewidth=0.6, label=CATEGORY_LABELS[cat])
        left += np.array(vals)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Fraction of matched targets")
    ax.text(
        0.02,
        -0.26,
        "Colors follow the endpoint plane: Anchor, shift-excess, dependency-excess, low-information, middle.",
        transform=ax.transAxes,
        fontsize=5.0,
        color="#444444",
    )
    clean_axes(ax)


def null_source(root: Path) -> pd.DataFrame:
    return pd.read_csv(root / NULL_SUMMARY, sep="\t")


def render_null(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_heading(ax, "d", "Endpoint-label permutation calibration", label_x=-0.10)
    y = np.arange(len(df))[::-1]
    for i, row in df.iterrows():
        yi = y[i]
        ax.plot([row["null_q025"], row["null_q975"]], [yi, yi], color="#BDBDBD", lw=4.0, solid_capstyle="round")
        ax.plot([row["null_q005"], row["null_q995"]], [yi, yi], color="#DADADA", lw=1.4, solid_capstyle="round")
        ax.scatter(row["observed_spearman_rho_aligned"], yi, s=55, color=COLORS["scgen"], edgecolor="white", linewidth=0.7, zorder=3)
        ax.text(0.98, yi, f"Spearman ρ = {row['observed_spearman_rho_aligned']:.3f}; P = {row['empirical_p_two_sided']:.3g}", ha="right", va="center", fontsize=5.8)
    ax.axvline(0, color="#777777", lw=0.7, ls="--")
    ax.set_yticks(y)
    ax.set_yticklabels(df["cell_line"])
    ax.set_xlabel("Spearman ρ under endpoint-label permutation")
    ax.set_xlim(-0.45, 1.02)
    ax.grid(axis="x", color=COLORS["grid"], lw=0.45)
    clean_axes(ax)


def anchor_source() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"target_gene": "PFDN5", "claim_tier": "primary qualified", "covariate_status": "cleaner audited profile"},
            {"target_gene": "PMF1", "claim_tier": "supporting only", "covariate_status": "UMI/TVD exposed"},
            {"target_gene": "PRPF6", "claim_tier": "supporting only", "covariate_status": "UMI/TVD exposed"},
            {"target_gene": "ZNF131", "claim_tier": "supporting only", "covariate_status": "UMI/TVD exposed"},
            {"target_gene": "cutoff-sensitive set (5)", "claim_tier": "supporting only", "covariate_status": "not primary wording"},
        ]
    )


def render_anchor(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_heading(ax, "e", "Compact anchor claim tiering", label_x=-0.10)
    ax.set_axis_off()
    y = 0.80
    for _, row in df.iterrows():
        color = COLORS["scgen"] if row["claim_tier"] == "primary qualified" else ("#9A9A9A" if row["claim_tier"] == "supporting only" else COLORS["supporting"])
        ax.scatter(0.05, y, s=52, color=color, transform=ax.transAxes, edgecolor="white", linewidth=0.6)
        ax.text(0.11, y, row["target_gene"], transform=ax.transAxes, fontsize=6.0, weight="bold", va="center")
        ax.text(0.40, y, row["claim_tier"], transform=ax.transAxes, fontsize=5.7, va="center")
        ax.text(0.68, y, row["covariate_status"], transform=ax.transAxes, fontsize=5.2, va="center", color="#444444")
        ax.plot([0.03, 0.96], [y - 0.075, y - 0.075], transform=ax.transAxes, color="#E5E5E5", lw=0.5)
        y -= 0.16


def _save_panel(root: Path, pid: str, title: str, fig: plt.Figure, source: pd.DataFrame) -> dict[str, Path]:
    stem = f"{FIGURE_ID}_panel{pid}"
    public_stem = f"{PUBLIC_FIGURE_ID}_panel_{pid}"
    src = write_tsv(source, panel_dir(root) / f"{stem}_source_data.tsv")
    public_src = write_tsv(source, manuscript_panel_dir(root) / f"{public_stem}_source_data.tsv")
    png = panel_dir(root) / f"{stem}.png"
    pdf = panel_dir(root) / f"{stem}.pdf"
    public_png = manuscript_panel_dir(root) / f"{public_stem}.png"
    public_pdf = manuscript_panel_dir(root) / f"{public_stem}.pdf"
    finalize_manuscript_figure(fig, font_scale=0.95)
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
    sources = {"a": scatter_source(root, "HCC38"), "b": scatter_source(root, "HCC1143"), "c": category_source(root), "d": null_source(root), "e": anchor_source()}
    outputs = {}
    for pid, src in sources.items():
        fig, ax = plt.subplots(figsize={"a": (3.8, 3.0), "b": (3.8, 3.0), "c": (4.0, 2.5), "d": (4.8, 2.5), "e": (5.0, 2.5)}[pid])
        {"a": lambda a, d: render_scatter(a, d, "a", "HCC38 primary endpoint bridge"), "b": lambda a, d: render_scatter(a, d, "b", "HCC1143 primary endpoint bridge"), "c": render_category, "d": render_null, "e": render_anchor}[pid](ax, src)
        outputs[pid] = _save_panel(root, pid, {"a": "HCC38 observed shift-DepMap bridge", "b": "HCC1143 observed shift-DepMap bridge", "c": "Endpoint category composition", "d": "Permutation calibration", "e": "Anchor claim tiering"}[pid], fig, src)
    return outputs


def build_combined(root: Path, panels: dict[str, dict[str, Path]]) -> None:
    sources = {"a": scatter_source(root, "HCC38"), "b": scatter_source(root, "HCC1143"), "c": category_source(root), "d": null_source(root), "e": anchor_source()}
    combined = pd.concat([df.assign(panel=pid) for pid, df in sources.items()], ignore_index=True, sort=False)
    src = write_tsv(combined, output_dir(root) / f"{FIGURE_ID}_source_data.tsv")
    public_src = write_tsv(combined, manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}_source_data.tsv")
    fig = plt.figure(figsize=(10.4, 7.2))
    gs = fig.add_gridspec(2, 3, left=0.06, right=0.98, top=0.94, bottom=0.10, wspace=0.34, hspace=0.44, width_ratios=[1, 1, 1.2])
    axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[0, 2]), fig.add_subplot(gs[1, :2]), fig.add_subplot(gs[1, 2])]
    render_scatter(axes[0], sources["a"], "a", "HCC38 primary endpoint bridge")
    render_scatter(axes[1], sources["b"], "b", "HCC1143 primary endpoint bridge")
    render_category(axes[2], sources["c"])
    render_null(axes[3], sources["d"])
    render_anchor(axes[4], sources["e"])
    finalize_manuscript_figure(fig, font_scale=0.95)
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
    write_figure_manifest(manifest_path=output_dir(root) / f"{FIGURE_ID}_panel_manifest.json", repo_root=root, figure_id=FIGURE_ID, figure_title=FIGURE_TITLE, script_path=root / SCRIPT_PATH, panel_manifest_paths=[panels[p]["manifest"] for p in ["a", "b", "c", "d", "e"]], combined_source_data_path=src, output_paths=[png, pdf], input_paths=input_paths(root), claim_boundary=CLAIM_BOUNDARY)
    write_figure_manifest(manifest_path=manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}_panel_manifest.json", repo_root=root, figure_id=PUBLIC_FIGURE_ID, figure_title=FIGURE_TITLE, script_path=root / SCRIPT_PATH, panel_manifest_paths=[manuscript_panel_dir(root) / f"{PUBLIC_FIGURE_ID}_panel_{p}_manifest.json" for p in ["a", "b", "c", "d", "e"]], combined_source_data_path=public_src, output_paths=[public_png, public_pdf], input_paths=input_paths(root), claim_boundary=CLAIM_BOUNDARY)


def copy_to_figure_build(root: Path) -> None:
    src = output_dir(root)
    dst = ensure_dir(root / "figure_build/output/Figure_2")
    pdst = ensure_dir(dst / "panels")
    for ext in [".png", ".pdf", "_source_data.tsv"]:
        s = src / f"{FIGURE_ID}{ext}"
        if s.exists():
            shutil.copy2(s, dst / f"{PUBLIC_FIGURE_ID}{ext}")
    for panel in ["a", "b", "c", "d", "e"]:
        for ext in [".png", ".pdf", "_source_data.tsv"]:
            s = src / "panels" / f"{FIGURE_ID}_panel{panel}{ext}"
            if s.exists():
                shutil.copy2(s, pdst / f"{PUBLIC_FIGURE_ID}_panel_{panel}{ext}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build Figure 2 primary HCC endpoint object.")
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
