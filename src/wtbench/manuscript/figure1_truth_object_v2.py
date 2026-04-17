from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes


FIGURE_ID = "figure1"
FIGURE_TITLE = "A truth-first benchmark defines the fitness-relevant transcriptomic bridge object"
SCRIPT_PATH = Path("scripts/manuscript/build_figure1_truth_object.py")
CLAIM_BOUNDARY = "The truth-DepMap bridge is retained as a structured truth object, not as fully deconfounded causal proof."

JOINT_GRID = Path("reports/stage2_truth_bridge_decomposition/target_level_joint_grid.tsv")
GRID_SUMMARY = Path("reports/stage2_truth_bridge_decomposition/target_level_grid_summary.tsv")
RUN_SUMMARY = Path("reports/stage2_truth_bridge_decomposition/run_summary.json")
HCC38_CORR = Path("reports/stage2_truth_driven_bridge/HCC38/correlation_summary.tsv")
HCC1143_CORR = Path("reports/stage2_truth_driven_bridge/HCC1143/correlation_summary.tsv")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")

GRID_COLORS = {
    "Q1_anchor": "#2E7D52",
    "Q2_transcriptomic_excess": "#B59B2B",
    "Q3_dependency_excess": "#8AA6A3",
    "Q4_low_information": "#BDBDBD",
    "middle": "#D9D9D9",
}

EXPECTED_Q1 = {"HCC38": 9, "HCC1143": 10}


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig1_truth_object"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / p for p in [JOINT_GRID, GRID_SUMMARY, RUN_SUMMARY, HCC38_CORR, HCC1143_CORR, FINAL_CLAIM_MATRIX]]


def load_joint_grid(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / JOINT_GRID, sep="\t")
    q1 = df.loc[df["joint_grid"].eq("Q1_anchor")].groupby("cell_line").size().to_dict()
    for cell_line, expected in EXPECTED_Q1.items():
        observed = int(q1.get(cell_line, 0))
        if observed != expected:
            raise RuntimeError(f"Fig. 1 Q1 sanity check failed for {cell_line}: observed={observed}, expected={expected}")
    return df


def write_panel(
    *,
    root: Path,
    panel_id: str,
    panel_title: str,
    source_df: pd.DataFrame,
    render: Callable[[plt.Axes, pd.DataFrame], None],
    width: float = 3.2,
    height: float = 2.35,
) -> dict[str, Path]:
    pdir = ensure_dir(panel_dir(root))
    stem = f"{FIGURE_ID}_panel{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    png_path = pdir / f"{stem}.png"
    pdf_path = pdir / f"{stem}.pdf"
    output_paths = save_figure(fig, png_path, pdf_path)
    manifest_path = pdir / f"{stem}_manifest.json"
    write_panel_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        panel_id=f"{FIGURE_ID}{panel_id}",
        panel_title=panel_title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Truth-first evaluation order", loc="left", pad=4)
    nodes = [
        (0.03, "real\nperturbation\ntruth"),
        (0.25, "DepMap\nfitness\nendpoint"),
        (0.48, "frozen\nbridge\nobject"),
        (0.70, "model\nrecovery\nadjudication"),
        (0.91, "gated\ndiscovery"),
    ]
    for x, text in nodes:
        rect = plt.Rectangle((x, 0.55), 0.16, 0.22, transform=ax.transAxes, facecolor="#F2F2F2", edgecolor="#888888", linewidth=0.8)
        ax.add_patch(rect)
        ax.text(x + 0.08, 0.66, text, ha="center", va="center", fontsize=7, transform=ax.transAxes)
    for x0 in [0.19, 0.41, 0.64, 0.86]:
        ax.annotate("", xy=(x0 + 0.045, 0.66), xytext=(x0, 0.66), xycoords=ax.transAxes, arrowprops={"arrowstyle": "->", "lw": 0.8})
    ax.text(0.04, 0.25, "Define the object before ranking models.", fontsize=8, fontweight="bold", transform=ax.transAxes)
    ax.text(0.04, 0.12, "Model comparison is downstream of truth-object construction.", fontsize=7, color="#555555", transform=ax.transAxes)
    add_panel_label(ax, "a", x=-0.04)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Primary HCC truth object", loc="left", pad=4)
    cols = ["context", "truth metric", "endpoint", "targets"]
    y0 = 0.78
    xs = [0.04, 0.30, 0.64, 0.92]
    for x, col in zip(xs, cols):
        ax.text(x, y0, col, fontsize=7, fontweight="bold", transform=ax.transAxes)
    for i, row in enumerate(df.itertuples()):
        y = y0 - 0.18 * (i + 1)
        ax.text(xs[0], y, row.context, fontsize=7, transform=ax.transAxes)
        ax.text(xs[1], y, "real_shift\nmean_abs", fontsize=7, transform=ax.transAxes, linespacing=0.9)
        ax.text(xs[2], y, "CRISPR\nDepMap", fontsize=7, transform=ax.transAxes, linespacing=0.9)
        ax.text(xs[3], y, str(row.targets), fontsize=7, transform=ax.transAxes)
    ax.text(0.04, 0.12, "Endpoint direction: larger values indicate stronger dependency/liability.", fontsize=6, color="#666666", transform=ax.transAxes)
    add_panel_label(ax, "b", x=-0.04)


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_title("Joint-grid definition", loc="left")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axvspan(0, 0.25, color="#F4F4F4", zorder=0)
    ax.axvspan(0.75, 1, color="#F4F4F4", zorder=0)
    ax.axhspan(0, 0.25, color="#F4F4F4", zorder=0)
    ax.axhspan(0.75, 1, color="#F4F4F4", zorder=0)
    ax.axvline(0.25, color="#888888", linewidth=0.8)
    ax.axvline(0.75, color="#888888", linewidth=0.8)
    ax.axhline(0.25, color="#888888", linewidth=0.8)
    ax.axhline(0.75, color="#888888", linewidth=0.8)
    labels = [
        (0.875, 0.875, "Q1\nanchor", GRID_COLORS["Q1_anchor"]),
        (0.875, 0.125, "Q2\ntranscriptomic\nexcess", GRID_COLORS["Q2_transcriptomic_excess"]),
        (0.125, 0.875, "Q3\ndependency\nexcess", GRID_COLORS["Q3_dependency_excess"]),
        (0.125, 0.125, "Q4\nlow\ninformation", "#777777"),
        (0.50, 0.50, "middle band\nretained", "#777777"),
    ]
    for x, y, text, color in labels:
        ax.text(x, y, text, ha="center", va="center", fontsize=7, color=color, fontweight="bold")
    ax.set_xlabel("Transcriptomic shift quantile")
    ax.set_ylabel("Dependency strength quantile")
    clean_axes(ax)
    add_panel_label(ax, "c")


def render_joint_grid(ax: plt.Axes, df: pd.DataFrame, cell_line: str, label: str) -> None:
    plot = df.loc[df["cell_line"].eq(cell_line)].copy()
    colors = plot["joint_grid"].map(GRID_COLORS).fillna(GRID_COLORS["middle"])
    sizes = np.where(plot["joint_grid"].eq("Q1_anchor"), 32, 18)
    ax.scatter(plot["shift_quantile"], plot["depmap_quantile"], c=colors, s=sizes, edgecolor="white", linewidth=0.4)
    shared_anchor_labels = {"PFDN5", "PMF1", "PRPF6", "ZNF131"}
    q1 = plot.loc[plot["joint_grid"].eq("Q1_anchor")]
    for row in q1.loc[q1["target_gene"].isin(shared_anchor_labels)].itertuples():
        ax.text(row.shift_quantile + 0.012, row.depmap_quantile + 0.008, row.target_gene, fontsize=5.5)
    ax.text(0.03, 0.95, f"Q1 anchors: n={len(q1)}", transform=ax.transAxes, fontsize=7, fontweight="bold", va="top")
    ax.axvline(0.25, color="#999999", linewidth=0.6)
    ax.axvline(0.75, color="#999999", linewidth=0.6)
    ax.axhline(0.25, color="#999999", linewidth=0.6)
    ax.axhline(0.75, color="#999999", linewidth=0.6)
    ax.set_xlim(-0.02, 1.08)
    ax.set_ylim(-0.02, 1.08)
    ax.set_xlabel("Shift quantile")
    ax.set_ylabel("Dependency quantile")
    ax.set_title(f"{cell_line}: Q1 anchors concentrate high shift and dependency", loc="left")
    clean_axes(ax)
    ax.grid(color=COLORS["grid"], linewidth=0.4)
    add_panel_label(ax, label)


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    render_joint_grid(ax, df, "HCC38", "d")


def render_panel_e(ax: plt.Axes, df: pd.DataFrame) -> None:
    render_joint_grid(ax, df, "HCC1143", "e")


def render_panel_f(ax: plt.Axes, df: pd.DataFrame) -> None:
    order = ["Q1_anchor", "middle", "Q4_low_information"]
    labels = {"Q1_anchor": "Q1 anchors", "middle": "middle band", "Q4_low_information": "Q4 low info"}
    pivot = df.pivot_table(index="cell_line", columns="joint_grid", values="fraction_targets", fill_value=0).reindex(columns=order)
    pivot = pivot.sort_index()
    y = np.arange(len(pivot))
    left = np.zeros(len(pivot))
    for grid in order:
        vals = pivot[grid].to_numpy()
        ax.barh(y, vals, left=left, height=0.48, color=GRID_COLORS[grid], edgecolor="white", linewidth=0.5, label=labels[grid])
        for yi, val, start in zip(y, vals, left):
            if val > 0.10:
                text_color = "white" if grid == "Q1_anchor" else "#333333"
                ax.text(start + val / 2, yi, labels[grid].replace(" ", "\n"), ha="center", va="center", fontsize=5.5, color=text_color)
        left += vals
    counts = df.pivot_table(index="cell_line", columns="joint_grid", values="n_targets", fill_value=0).reindex(index=pivot.index, columns=order)
    for yi, cell_line in zip(y, pivot.index):
        ax.text(1.02, yi, f"Q1={int(counts.loc[cell_line, 'Q1_anchor'])}", va="center", fontsize=7)
    ax.set_yticks(y)
    ax.set_yticklabels(pivot.index)
    ax.set_xlim(0, 1.18)
    ax.set_xlabel("Fraction of bridgeable targets")
    ax.set_title("Both HCC contexts contain a Q1 anchor component", loc="left")
    clean_axes(ax)
    ax.tick_params(axis="y", length=0)
    add_panel_label(ax, "f")


def render_panel_g(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.copy()
    x = np.arange(len(plot))
    ax.bar(x, plot["spearman_rho_aligned"], color=COLORS["baseline"], width=0.55)
    for xi, row in zip(x, plot.itertuples()):
        ax.text(xi, row.spearman_rho_aligned + 0.025, f"rho={row.spearman_rho_aligned:.3f}\nn={int(row.n_targets)}", ha="center", fontsize=6)
    ax.set_xticks(x)
    ax.set_xticklabels(plot["cell_line"])
    ax.set_ylim(0, 0.86)
    ax.set_ylabel("Aligned Spearman")
    ax.set_title("Primary CRISPR bridge is strong in both HCC contexts", loc="left")
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "g")


def render_panel_h(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Truth-object claim boundary", loc="left", pad=4)
    rows = [
        ("Allowed", "truth-DepMap bridge retained at global/structural level"),
        ("Allowed", "structured object enters model adjudication"),
        ("Not allowed", "bridge is fully deconfounded"),
        ("Not allowed", "bridge is proved without confounding risk"),
    ]
    y = 0.86
    for status, text in rows:
        color = COLORS["primary_qualified"] if status == "Allowed" else COLORS["boundary"]
        ax.text(0.02, y, status, color=color, fontweight="bold", fontsize=7, transform=ax.transAxes)
        ax.text(0.34, y, text, fontsize=7, transform=ax.transAxes)
        y -= 0.18
    ax.text(0.02, 0.05, "Boundary fixed by final claim matrix.", fontsize=6, color="#666666", transform=ax.transAxes)
    add_panel_label(ax, "h", x=-0.04)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    joint = load_joint_grid(root)
    summary = pd.read_csv(root / GRID_SUMMARY, sep="\t")
    hcc38 = pd.read_csv(root / HCC38_CORR, sep="\t")
    hcc1143 = pd.read_csv(root / HCC1143_CORR, sep="\t")
    corr = pd.concat([hcc38, hcc1143], ignore_index=True)
    corr = corr.loc[
        corr["truth_metric"].eq("real_shift_mean_abs") & corr["depmap_endpoint"].eq("depmap_gene_dependency"),
        ["cell_line", "truth_metric", "depmap_endpoint", "n_targets", "spearman_rho_aligned", "pearson_r_aligned"],
    ]
    claim = pd.read_csv(root / FINAL_CLAIM_MATRIX, sep="\t")
    boundary = claim.loc[claim["object"].eq("global_truth_depmap_bridge")].copy()
    overview = pd.DataFrame(
        [
            {"context": "HCC38", "truth_metric": "real_shift_mean_abs", "endpoint": "CRISPR DepMap dependency", "targets": 47},
            {"context": "HCC1143", "truth_metric": "real_shift_mean_abs", "endpoint": "CRISPR DepMap dependency", "targets": 48},
        ]
    )
    workflow = pd.DataFrame(
        [
            {"step": 1, "name": "real perturbation truth"},
            {"step": 2, "name": "DepMap fitness endpoint"},
            {"step": 3, "name": "frozen bridge object"},
            {"step": 4, "name": "model recovery adjudication"},
            {"step": 5, "name": "gated discovery"},
        ]
    )
    definition = pd.DataFrame(
        [
            {"region": "Q1_anchor", "shift_band": "high", "depmap_band": "high"},
            {"region": "Q2_transcriptomic_excess", "shift_band": "high", "depmap_band": "low"},
            {"region": "Q3_dependency_excess", "shift_band": "low", "depmap_band": "high"},
            {"region": "Q4_low_information", "shift_band": "low", "depmap_band": "low"},
            {"region": "middle", "shift_band": "middle_any", "depmap_band": "middle_any"},
        ]
    )
    return {
        "a": workflow,
        "b": overview,
        "c": definition,
        "d": joint.loc[joint["cell_line"].eq("HCC38")],
        "e": joint.loc[joint["cell_line"].eq("HCC1143")],
        "f": summary,
        "g": corr,
        "h": boundary[["object", "evidence_tier", "allowed_wording", "disallowed_wording"]],
    }


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {
        "a": render_panel_a,
        "b": render_panel_b,
        "c": render_panel_c,
        "d": render_panel_d,
        "e": render_panel_e,
        "f": render_panel_f,
        "g": render_panel_g,
        "h": render_panel_h,
    }[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Truth-first benchmark workflow",
        "b": "Primary HCC truth object overview",
        "c": "Q1-Q4 joint-grid definition",
        "d": "HCC38 target-level joint grid",
        "e": "HCC1143 target-level joint grid",
        "f": "Joint-grid composition",
        "g": "Primary CRISPR bridge strength",
        "h": "Truth-object claim boundary",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")
    fig = plt.figure(figsize=(11.0, 10.0))
    gs = fig.add_gridspec(4, 2, hspace=0.72, wspace=0.42)
    axes = [fig.add_subplot(gs[i, j]) for i in range(4) for j in range(2)]
    for ax, panel_id in zip(axes, list("abcdefgh")):
        render_panel_by_id(panel_id)(ax, sources[panel_id])
    fig.suptitle(FIGURE_TITLE, x=0.02, y=0.995, ha="left", fontsize=10, fontweight="bold")
    png_path = out / f"{FIGURE_ID}.png"
    pdf_path = out / f"{FIGURE_ID}.pdf"
    output_paths = save_figure(fig, png_path, pdf_path)
    manifest_path = out / f"{FIGURE_ID}_panel_manifest.json"
    write_figure_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in list("abcdefgh")],
        combined_source_data_path=combined_source_path,
        output_paths=output_paths,
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": combined_source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build manuscript Figure 1 truth-object panels and assembly.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    apply_manuscript_style()
    sources = build_sources(root)
    panel_outputs: dict[str, dict[str, Path]] = {}
    for panel_id in list("abcdefgh"):
        panel_outputs[panel_id] = write_panel(
            root=root,
            panel_id=panel_id,
            panel_title=panel_title(panel_id),
            source_df=sources[panel_id],
            render=render_panel_by_id(panel_id),
            width=3.45 if panel_id in {"d", "e", "f"} else 3.2,
            height=2.65 if panel_id in {"d", "e", "f"} else 2.35,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
