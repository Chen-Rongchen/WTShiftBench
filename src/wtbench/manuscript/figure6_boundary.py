from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wtbench.manuscript.figure_io import ensure_dir, repo_root, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes


FIGURE_ID = "figure6"
FIGURE_TITLE = "Covariate, temporal and endpoint boundaries define the final benchmark scope"
SCRIPT_PATH = Path("scripts/manuscript/build_figure6_boundary.py")
CLAIM_BOUNDARY = (
    "Three independent boundary layers define the final benchmark scope: "
    "covariate boundary blocks fully deconfounded wording; "
    "temporal boundary blocks content-level replication and primary co-pillar; "
    "endpoint hierarchy boundary blocks treating RNAi as primary readout."
)

COVARIATE_SUMMARY = Path("reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv")
TEMPORAL_BRIDGE = Path("reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_bridge_summary.tsv")
HCC_ENDPOINT = Path("reports/stage2_truth_driven_bridge/hcc38_hcc1143_rnai_endpoint_consistency/endpoint_consistency_summary.tsv")
K562_ENDPOINT = Path("reports/stage2_truth_driven_bridge/k562_rnai_endpoint_consistency/endpoint_consistency_summary.tsv")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig6_boundary"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_5"


def manuscript_panel_dir(root: Path) -> Path:
    return manuscript_figure_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [
        root / COVARIATE_SUMMARY,
        root / TEMPORAL_BRIDGE,
        root / HCC_ENDPOINT,
        root / K562_ENDPOINT,
        root / FINAL_CLAIM_MATRIX,
    ]


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
    manuscript_pdir = ensure_dir(manuscript_panel_dir(root))
    stem = f"{FIGURE_ID}_panel{panel_id}"
    manuscript_stem = f"Figure_5_panel_{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    manuscript_source_path = write_tsv(source_df, manuscript_pdir / f"{manuscript_stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    png_path = pdir / f"{stem}.png"
    pdf_path = pdir / f"{stem}.pdf"
    manuscript_png_path = manuscript_pdir / f"{manuscript_stem}.png"
    manuscript_pdf_path = manuscript_pdir / f"{manuscript_stem}.pdf"
    for path in [png_path, pdf_path, manuscript_png_path, manuscript_pdf_path]:
        ensure_dir(path.parent)
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(manuscript_png_path, dpi=300, bbox_inches="tight")
    fig.savefig(manuscript_pdf_path, bbox_inches="tight")
    output_paths = [png_path, pdf_path]
    plt.close(fig)
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
    write_panel_manifest(
        manifest_path=manuscript_pdir / f"{manuscript_stem}_manifest.json",
        repo_root=root,
        panel_id=f"figure5{panel_id}",
        panel_title=panel_title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=manuscript_source_path,
        output_paths=[manuscript_png_path, manuscript_pdf_path],
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def load_endpoint(root: Path) -> pd.DataFrame:
    hcc = pd.read_csv(root / HCC_ENDPOINT, sep="\t")
    k562 = pd.read_csv(root / K562_ENDPOINT, sep="\t")
    df = pd.concat([hcc, k562], ignore_index=True)
    bridge = df.loc[
        df["summary_kind"].eq("truth_endpoint_bridge")
        & df["truth_metric"].eq("real_shift_mean_abs")
        & df["depmap_endpoint"].eq("depmap_gene_dependency")
    ].copy()
    pivot = bridge.pivot_table(index="timepoint", columns="platform_pair", values="spearman", aggfunc="first")
    if not (pivot["crispr"] > pivot["rnai"]).all():
        raise RuntimeError("Fig. 6 endpoint sanity check failed: CRISPR is not stronger than RNAi in every context.")
    bridge["context"] = bridge["timepoint"].map({"7d": "K562 7d", "13d": "K562 13d"}).fillna(bridge["timepoint"])
    return bridge


def load_temporal(root: Path) -> pd.DataFrame:
    bridge = pd.read_csv(root / TEMPORAL_BRIDGE, sep="\t")
    primary = bridge.loc[
        bridge["truth_metric"].eq("real_shift_mean_abs") & bridge["depmap_endpoint"].eq("depmap_gene_dependency")
    ].copy()
    vals = primary.set_index("timepoint")
    if float(vals.loc["7d", "aligned_spearman"]) <= float(vals.loc["13d", "aligned_spearman"]):
        raise RuntimeError("Fig. 6 temporal sanity check failed: 7d rank alignment is not stronger than 13d.")
    if float(vals.loc["13d", "mean_truth_metric"]) <= float(vals.loc["7d", "mean_truth_metric"]):
        raise RuntimeError("Fig. 6 temporal sanity check failed: 13d mean shift is not stronger than 7d.")
    return primary


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Boundary architecture schematic — three layers defining claim scope."""
    ax.set_axis_off()
    ax.set_title("Boundary architecture", loc="left", pad=4)

    layers = [
        {
            "label": "Covariate boundary",
            "audits": "Audits: barcode gem group, UMI / signal, detected genes",
            "blocks": "Blocks: fully deconfounded wording",
            "color": COLORS["primary_qualified"],
        },
        {
            "label": "Temporal boundary (K562)",
            "audits": "Audits: 7d / 13d supplementary panel",
            "blocks": "Blocks: content-level replication, primary co-pillar",
            "color": "#B8A64A",
        },
        {
            "label": "Endpoint hierarchy boundary",
            "audits": "Audits: CRISPR DepMap primary, RNAi DEMETER2 sensitivity",
            "blocks": "Blocks: treating RNAi as primary readout",
            "color": "#8A8A8A",
        },
    ]

    y = 0.90
    box_height = 0.20
    gap = 0.06
    for layer in layers:
        rect = plt.Rectangle(
            (0.05, y - box_height),
            0.90,
            box_height,
            transform=ax.transAxes,
            facecolor="white",
            edgecolor=layer["color"],
            linewidth=1.2,
            zorder=1,
        )
        ax.add_patch(rect)
        ax.text(0.09, y - 0.025, layer["label"], fontweight="bold", fontsize=8, color=layer["color"], transform=ax.transAxes, zorder=2)
        ax.text(0.09, y - 0.085, layer["audits"], fontsize=6.5, color="#444444", transform=ax.transAxes, zorder=2)
        ax.text(0.09, y - 0.145, layer["blocks"], fontsize=6.5, color="#666666", transform=ax.transAxes, zorder=2)
        y -= (box_height + gap)

    # Bottom arrow / convergence
    ax.annotate(
        "",
        xy=(0.50, 0.12),
        xytext=(0.50, 0.22),
        arrowprops=dict(arrowstyle="->", color="#444444", lw=1.0),
        transform=ax.transAxes,
    )
    ax.text(0.50, 0.06, "Final claim scope", ha="center", fontsize=8, fontweight="bold", color="#1F1F1F", transform=ax.transAxes)

    add_panel_label(ax, "a", x=-0.04, y=1.02)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Covariate boundary compact evidence — mean TVD matrix by axis and cell line."""
    ax.set_axis_off()
    ax.set_title("Covariate boundary", loc="left", pad=4)

    # Build matrix from source data
    pivot = df.pivot(index="strat_column", columns="cell_line", values="mean_tvd")
    pivot = pivot.reindex([
        "barcode_gem_group",
        "transcriptome_detected_genes_quantile_bin",
        "transcriptome_total_signal_quantile_bin",
        "num_umis_over_threshold_bin",
        "num_umis_quantile_bin",
    ])

    n_rows = len(pivot)
    n_cols = 3  # HCC38, HCC1143, impact
    cell_w = 0.26
    cell_h = 0.14
    x0 = 0.08
    y0 = 0.88

    # Column headers
    headers = ["HCC38", "HCC1143", "Impact on wording"]
    for ci, h in enumerate(headers):
        ax.text(x0 + ci * cell_w + cell_w / 2, y0 + 0.02, h, ha="center", va="bottom",
                fontsize=6.5, fontweight="bold", color="#1F1F1F", transform=ax.transAxes)

    # Row labels and cells
    row_labels = [s.replace("_", " ") for s in pivot.index]
    for ri, (row_label, row) in enumerate(zip(row_labels, pivot.itertuples())):
        y = y0 - (ri + 1) * cell_h
        # Row label
        ax.text(x0 - 0.02, y + cell_h / 2, row_label, ha="right", va="center",
                fontsize=5.5, color="#444444", transform=ax.transAxes)
        # HCC38 cell
        val_hcc38 = row.HCC38
        bg_color = "#F5E6C8" if val_hcc38 > 0.25 else "#F8F8F8"
        rect = plt.Rectangle((x0, y), cell_w, cell_h, transform=ax.transAxes,
                             facecolor=bg_color, edgecolor="#DDDDDD", linewidth=0.5, zorder=1)
        ax.add_patch(rect)
        ax.text(x0 + cell_w / 2, y + cell_h / 2, f"{val_hcc38:.3f}", ha="center", va="center",
                fontsize=6, color="#B8A64A" if val_hcc38 > 0.25 else "#444444", transform=ax.transAxes, zorder=2)
        # HCC1143 cell
        val_hcc1143 = row.HCC1143
        bg_color = "#F5E6C8" if val_hcc1143 > 0.25 else "#F8F8F8"
        rect = plt.Rectangle((x0 + cell_w, y), cell_w, cell_h, transform=ax.transAxes,
                             facecolor=bg_color, edgecolor="#DDDDDD", linewidth=0.5, zorder=1)
        ax.add_patch(rect)
        ax.text(x0 + cell_w * 1.5, y + cell_h / 2, f"{val_hcc1143:.3f}", ha="center", va="center",
                fontsize=6, color="#B8A64A" if val_hcc1143 > 0.25 else "#444444", transform=ax.transAxes, zorder=2)
        # Impact cell
        impact_text = _covariate_impact(pivot.index[ri])
        rect = plt.Rectangle((x0 + cell_w * 2, y), cell_w, cell_h, transform=ax.transAxes,
                             facecolor="white", edgecolor="#DDDDDD", linewidth=0.5, zorder=1)
        ax.add_patch(rect)
        ax.text(x0 + cell_w * 2.5, y + cell_h / 2, impact_text, ha="center", va="center",
                fontsize=5, color="#666666", transform=ax.transAxes, zorder=2, wrap=True)

    # TVD threshold annotation
    ax.text(0.98, 0.02, "TVD > 0.25 blocks stronger wording", ha="right", fontsize=5.5,
            color="#666666", transform=ax.transAxes, style="italic")

    add_panel_label(ax, "b", x=-0.04, y=1.02)


def _covariate_impact(strat_column: str) -> str:
    mapping = {
        "barcode_gem_group": "limits gem-group resolution",
        "transcriptome_detected_genes_quantile_bin": "minor imbalance",
        "transcriptome_total_signal_quantile_bin": "minor imbalance",
        "num_umis_over_threshold_bin": "blocks deconfounded wording",
        "num_umis_quantile_bin": "blocks deconfounded wording",
    }
    return mapping.get(strat_column, "audited")


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Temporal and endpoint hierarchy boundary — left: K562 temporal, right: endpoint hierarchy."""
    ax.set_axis_off()
    ax.set_title("Temporal and endpoint hierarchy boundary", loc="left", pad=4)

    temporal = df.loc[df["subpanel"].eq("temporal")].copy()
    endpoint = df.loc[df["subpanel"].eq("endpoint")].copy()

    # Left sub-panel: K562 temporal
    ax_left = ax.inset_axes([0.00, 0.10, 0.46, 0.80])
    x = np.arange(len(temporal))
    width = 0.34
    ax_left.bar(x - width / 2, temporal["aligned_spearman"], width=width, color="#B8A64A", label="rank bridge")
    ax2_left = ax_left.twinx()
    ax2_left.bar(x + width / 2, temporal["mean_truth_metric"], width=width, color="#D7C69B", label="mean shift")
    ax_left.set_xticks(x)
    ax_left.set_xticklabels(temporal["timepoint"])
    ax_left.set_ylabel("Rank bridge Spearman", fontsize=6, labelpad=2)
    ax2_left.set_ylabel("Mean shift", fontsize=6, labelpad=2, rotation=270, va="bottom")
    ax_left.set_ylim(0, 0.85)
    ax2_left.set_ylim(0, max(temporal["mean_truth_metric"]) * 1.35)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color="#B8A64A"),
        plt.Rectangle((0, 0), 1, 1, color="#D7C69B"),
    ]
    ax_left.legend(handles, ["rank bridge", "mean shift"], frameon=False, loc="upper right", fontsize=5.5)
    clean_axes(ax_left)
    ax2_left.spines["top"].set_visible(False)
    ax_left.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    ax_left.set_title("K562 temporal", fontsize=6.5, loc="left", pad=2)

    # Right sub-panel: endpoint hierarchy
    ax_right = ax.inset_axes([0.54, 0.10, 0.46, 0.80])
    plot = endpoint.pivot_table(index="context", columns="platform_pair", values="spearman", aggfunc="first").reset_index()
    order = ["HCC38", "HCC1143", "K562 7d", "K562 13d"]
    plot["context"] = pd.Categorical(plot["context"], categories=order, ordered=True)
    plot = plot.sort_values("context")
    x_r = np.arange(len(plot))
    width_r = 0.34
    ax_right.bar(x_r - width_r / 2, plot["crispr"], width=width_r, color=COLORS["primary_qualified"], label="CRISPR")
    ax_right.bar(x_r + width_r / 2, plot["rnai"], width=width_r, color="#C8C8C8", label="RNAi")
    ax_right.set_xticks(x_r)
    ax_right.set_xticklabels(plot["context"], rotation=25, ha="right", fontsize=5.5)
    ax_right.set_ylim(0, 0.86)
    ax_right.set_ylabel("Bridge Spearman", fontsize=6, labelpad=1)
    ax_right.legend(frameon=False, loc="upper right", fontsize=5.5)
    clean_axes(ax_right)
    ax_right.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    ax_right.set_title("Endpoint hierarchy", fontsize=6.5, loc="left", pad=2)

    add_panel_label(ax, "c", x=-0.04, y=1.02)


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Final claim boundary — structured claim ledger."""
    ax.set_axis_off()
    ax.set_title("Final claim boundary", loc="left", pad=4)

    sections = [
        ("Primary readout", [
            "CRISPR DepMap dependency (HCC38 / HCC1143)",
            "Aligned Spearman rho = 0.726 / 0.779",
        ], COLORS["primary_qualified"]),
        ("Supplementary evidence", [
            "K562 temporal panel (7d / 13d)",
            "Architecture-form recurrence, bounded bridge-form",
            "Not content-level replication",
        ], "#B8A64A"),
        ("Sensitivity endpoint", [
            "RNAi DEMETER2 (cross-platform, weaker)",
            "Bridge Spearman consistently below CRISPR",
        ], "#B29C5A"),
        ("Not claimed", [
            "Fully deconfounded architecture",
            "Content-level replication in K562",
            "RNAi as primary readout",
            "Mechanism-level recovery",
        ], "#8A8A8A"),
    ]

    y = 0.88
    for label, items, color in sections:
        ax.text(0.06, y, label, color=color, fontweight="bold", fontsize=8.5, transform=ax.transAxes)
        y -= 0.065
        for item in items:
            ax.text(0.10, y, "\u2022 " + item, fontsize=7, transform=ax.transAxes)
            y -= 0.055
        y -= 0.02

    # Bottom quantitative anchor
    anchor_text = (
        "Primary n = 47\u201348 | K562 n = 10 | "
        "CRISPR > RNAi in all 4 contexts | "
        "Covariate audited but not closed"
    )
    ax.text(0.06, 0.04, anchor_text, fontsize=6, color="#8A8A8A", transform=ax.transAxes)

    add_panel_label(ax, "d", x=-0.04, y=1.02)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    cov = pd.read_csv(root / COVARIATE_SUMMARY, sep="\t")
    temporal = load_temporal(root)
    endpoint = load_endpoint(root)

    # Panel a: boundary architecture — textual description
    source_a = pd.DataFrame([
        {"boundary_layer": "covariate", "audits": "barcode gem group, UMI/signal, detected genes", "blocks": "fully deconfounded wording"},
        {"boundary_layer": "temporal", "audits": "K562 7d/13d supplementary panel", "blocks": "content-level replication, primary co-pillar"},
        {"boundary_layer": "endpoint_hierarchy", "audits": "CRISPR DepMap primary, RNAi DEMETER2 sensitivity", "blocks": "treating RNAi as primary readout"},
    ])

    # Panel b: covariate summary
    source_b = cov[["cell_line", "strat_column", "mean_tvd", "n_targets_tvd_gt_0.25"]].copy()

    # Panel c: combined temporal + endpoint
    temporal_for_c = temporal[["timepoint", "aligned_spearman", "mean_truth_metric", "median_truth_metric"]].copy()
    endpoint_for_c = endpoint[["context", "platform_pair", "spearman", "n_shared_targets"]].copy()
    source_c = pd.concat([
        temporal_for_c.assign(subpanel="temporal"),
        endpoint_for_c.assign(subpanel="endpoint"),
    ], ignore_index=True)

    # Panel d: claim ledger
    source_d = pd.DataFrame([{
        "primary_readout": "CRISPR DepMap dependency (HCC38 / HCC1143)",
        "primary_spearman": "0.726 / 0.779",
        "supplementary": "K562 temporal panel (7d / 13d)",
        "sensitivity": "RNAi DEMETER2 (cross-platform, weaker)",
        "not_claimed": "fully deconfounded architecture; content-level replication; RNAi primary; mechanism recovery",
        "quantitative_anchor": "Primary n = 47-48 | K562 n = 10 | CRISPR > RNAi in all 4 contexts | Covariate audited but not closed",
    }])

    return {
        "a": source_a,
        "b": source_b,
        "c": source_c,
        "d": source_d,
    }


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {
        "a": render_panel_a,
        "b": render_panel_b,
        "c": render_panel_c,
        "d": render_panel_d,
    }[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Boundary architecture",
        "b": "Covariate boundary",
        "c": "Temporal and endpoint hierarchy boundary",
        "d": "Final claim boundary",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    manuscript_out = ensure_dir(manuscript_figure_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")
    manuscript_source_path = write_tsv(combined_source, manuscript_out / "Figure_5_source_data.tsv")

    fig = plt.figure(figsize=(10.5, 9.5))
    gs = fig.add_gridspec(2, 2, hspace=0.40, wspace=0.35)

    ax_a = fig.add_subplot(gs[0, 0])
    render_panel_a(ax_a, sources["a"])

    ax_b = fig.add_subplot(gs[0, 1])
    render_panel_b(ax_b, sources["b"])

    ax_c = fig.add_subplot(gs[1, 0])
    render_panel_c(ax_c, sources["c"])

    ax_d = fig.add_subplot(gs[1, 1])
    render_panel_d(ax_d, sources["d"])

    png_path = out / f"{FIGURE_ID}.png"
    pdf_path = out / f"{FIGURE_ID}.pdf"
    manuscript_png = manuscript_out / "Figure_5.png"
    manuscript_pdf = manuscript_out / "Figure_5.pdf"
    for path in [png_path, pdf_path, manuscript_png, manuscript_pdf]:
        ensure_dir(path.parent)
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(manuscript_png, dpi=300, bbox_inches="tight")
    fig.savefig(manuscript_pdf, bbox_inches="tight")
    output_paths = [png_path, pdf_path]
    plt.close(fig)
    manifest_path = out / f"{FIGURE_ID}_panel_manifest.json"
    write_figure_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in list("abcd")],
        combined_source_data_path=combined_source_path,
        output_paths=output_paths,
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )
    write_figure_manifest(
        manifest_path=manuscript_out / "Figure_5_panel_manifest.json",
        repo_root=root,
        figure_id="figure5",
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[
            manuscript_panel_dir(root) / f"Figure_5_panel_{p}_manifest.json"
            for p in list("abcd")
        ],
        combined_source_data_path=manuscript_source_path,
        output_paths=[manuscript_png, manuscript_pdf],
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": combined_source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build manuscript Figure 6 boundary panels and assembly.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    apply_manuscript_style()
    sources = build_sources(root)
    panel_outputs: dict[str, dict[str, Path]] = {}
    for panel_id in list("abcd"):
        panel_outputs[panel_id] = write_panel(
            root=root,
            panel_id=panel_id,
            panel_title=panel_title(panel_id),
            source_df=sources[panel_id],
            render=render_panel_by_id(panel_id),
            width=4.8 if panel_id == "c" else 4.2,
            height=4.2 if panel_id in {"a", "c", "d"} else 3.8,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
