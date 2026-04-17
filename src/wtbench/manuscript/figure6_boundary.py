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


FIGURE_ID = "figure6"
FIGURE_TITLE = "Covariate, temporal and endpoint analyses define the final claim boundary"
SCRIPT_PATH = Path("scripts/manuscript/build_figure6_boundary.py")
CLAIM_BOUNDARY = "Final claims are limitation-bounded: CRISPR is primary, RNAi is sensitivity, K562 is supplementary, discovery is gated."

COVARIATE_SUMMARY = Path("reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv")
BARCODE_NOTE = Path("reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/barcode_gem_group_mapping_note.md")
ANCHOR_TIERING = Path("reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv")
TEMPORAL_BRIDGE = Path("reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_bridge_summary.tsv")
TEMPORAL_CALLS = Path("reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_panel_calls.tsv")
TEMPORAL_STRUCTURE = Path("reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_structure_summary.tsv")
K562_TIER_13D = Path("reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_evidence_tier_summary.tsv")
K562_TIER_7D = Path("reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_7d/dixit_evidence_tier_summary.tsv")
HCC_ENDPOINT = Path("reports/stage2_truth_driven_bridge/hcc38_hcc1143_rnai_endpoint_consistency/endpoint_consistency_summary.tsv")
K562_ENDPOINT = Path("reports/stage2_truth_driven_bridge/k562_rnai_endpoint_consistency/endpoint_consistency_summary.tsv")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig6_boundary"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [
        root / COVARIATE_SUMMARY,
        root / BARCODE_NOTE,
        root / ANCHOR_TIERING,
        root / TEMPORAL_BRIDGE,
        root / TEMPORAL_CALLS,
        root / TEMPORAL_STRUCTURE,
        root / K562_TIER_13D,
        root / K562_TIER_7D,
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
    plot = df.groupby("strat_column", as_index=False).agg(mean_tvd=("mean_tvd", "mean"), max_targets_gt025=("n_targets_tvd_gt_0.25", "sum"))
    plot = plot.sort_values("mean_tvd", ascending=True)
    y = np.arange(len(plot))
    ax.barh(y, plot["mean_tvd"], color="#777777", height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["strat_column"].str.replace("_", " "))
    ax.set_xlabel("Mean TVD across HCC contexts")
    ax.set_title("Five covariate axes enter claim governance", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "a", x=-0.30)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    colors = df["final_wording_tier"].map({"primary_but_qualified": COLORS["primary_qualified"], "supporting_only": "#B59B2B"}).fillna("#BBBBBB")
    y = np.arange(len(df))
    ax.barh(y, [1] * len(df), color=colors, height=0.58)
    ax.set_yticks(y)
    ax.set_yticklabels(df["target_gene"])
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    for yi, row in zip(y, df.itertuples()):
        ax.text(0.03, yi, row.final_wording_tier.replace("_", " "), va="center", fontsize=7, color="white" if row.final_wording_tier == "primary_but_qualified" else "#222222")
    ax.set_title("Covariate-aware tiering downgrades strongest wording", loc="left")
    clean_axes(ax)
    add_panel_label(ax, "b", x=-0.20)


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("barcode_gem_group is a design-proxy axis", loc="left", pad=4)
    rows = [
        ("HCC38", "aggrMH001-3", "not MH001/2/3 resolved"),
        ("HCC1143", "aggrMH004-6", "not MH004/5/6 resolved"),
    ]
    y = 0.75
    for cell, aggr, boundary in rows:
        ax.text(0.05, y, cell, fontweight="bold", fontsize=8, transform=ax.transAxes)
        ax.text(0.28, y, aggr, fontsize=8, transform=ax.transAxes)
        ax.text(0.58, y, boundary, fontsize=7, color=COLORS["boundary"], transform=ax.transAxes)
        y -= 0.22
    ax.text(0.05, 0.18, "Allowed: aggregation/design proxy", color=COLORS["primary_qualified"], fontsize=7, transform=ax.transAxes)
    ax.text(0.05, 0.06, "Not allowed: single-run MH00x label", color=COLORS["boundary"], fontsize=7, transform=ax.transAxes)
    add_panel_label(ax, "c", x=-0.04)


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.copy()
    x = np.arange(len(plot))
    ax.bar(x, plot["n_formal_bridgeable_targets"], color="#777777", width=0.55)
    for xi, row in zip(x, plot.itertuples()):
        role = "early\nprobe" if row.timepoint == "7d" else "primary\nsupp."
        ax.text(xi, row.n_formal_bridgeable_targets + 0.3, role, ha="center", fontsize=6)
    ax.set_xticks(x)
    ax.set_xticklabels(plot["timepoint"])
    ax.set_ylim(0, 14)
    ax.set_ylabel("Formal bridgeable targets")
    ax.set_title("K562 temporal panel is supplementary", loc="left")
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "d")


def render_panel_e(ax: plt.Axes, df: pd.DataFrame) -> None:
    x = np.arange(len(df))
    width = 0.34
    ax.bar(x - width / 2, df["aligned_spearman"], width=width, color=COLORS["baseline"], label="rank bridge")
    ax2 = ax.twinx()
    ax2.bar(x + width / 2, df["mean_truth_metric"], width=width, color=COLORS["gears"], label="mean shift")
    ax.set_xticks(x)
    ax.set_xticklabels(df["timepoint"])
    ax.set_title("Temporal stratification is not monotonic improvement", loc="left")
    ax.set_ylabel("Rank bridge Spearman")
    ax2.set_ylabel("Mean shift")
    ax.set_ylim(0, 0.85)
    ax2.set_ylim(0, max(df["mean_truth_metric"]) * 1.35)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=COLORS["baseline"]),
        plt.Rectangle((0, 0), 1, 1, color=COLORS["gears"]),
    ]
    ax.legend(handles, ["rank bridge", "mean shift"], frameon=False, loc="upper right")
    clean_axes(ax)
    ax2.spines["top"].set_visible(False)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "e")


def render_panel_f(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.copy()
    counts = plot.groupby(["timepoint", "tier_group"]).size().reset_index(name="n")
    tiers = ["A0 confirmed", "A1 supporting", "B not eligible"]
    colors = {"A0 confirmed": COLORS["primary_qualified"], "A1 supporting": "#B59B2B", "B not eligible": "#BDBDBD"}
    xlabels = [tp for tp in ["7d", "13d"] if tp in set(counts["timepoint"])]
    x = np.arange(len(xlabels))
    bottom = np.zeros(len(xlabels))
    for tier in tiers:
        vals = [int(counts.loc[(counts["timepoint"].eq(tp)) & (counts["tier_group"].eq(tier)), "n"].sum()) for tp in xlabels]
        ax.bar(x, vals, bottom=bottom, color=colors[tier], width=0.55, label=tier)
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(xlabels)
    ax.set_ylabel("Evidence objects")
    ax.set_title("K562 evidence remains supplementary-tiered", loc="left")
    ax.legend(frameon=False, loc="upper right")
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "f")


def render_panel_g(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.pivot_table(index="context", columns="platform_pair", values="spearman", aggfunc="first").reset_index()
    order = ["HCC38", "HCC1143", "K562 7d", "K562 13d"]
    plot["context"] = pd.Categorical(plot["context"], categories=order, ordered=True)
    plot = plot.sort_values("context")
    x = np.arange(len(plot))
    width = 0.34
    ax.bar(x - width / 2, plot["crispr"], width=width, color=COLORS["baseline"], label="CRISPR DepMap")
    ax.bar(x + width / 2, plot["rnai"], width=width, color="#BDBDBD", label="RNAi DEMETER2")
    ax.set_xticks(x)
    ax.set_xticklabels(plot["context"], rotation=20, ha="right")
    ax.set_ylim(0, 0.86)
    ax.set_ylabel("Bridge Spearman")
    ax.set_title("CRISPR bridge remains stronger in every context", loc="left")
    ax.legend(frameon=False, loc="upper right")
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "g")


def render_panel_h(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Final claim boundary", loc="left", pad=4)
    rows = [
        ("Primary", "CRISPR DepMap bridge readout"),
        ("Sensitivity", "RNAi DEMETER2 endpoint"),
        ("Supplementary", "K562 temporal architecture form"),
        ("Gated", "discovery / phenotype shifter"),
    ]
    y = 0.84
    for label, text in rows:
        color = COLORS["primary_qualified"] if label == "Primary" else ("#B59B2B" if label in {"Sensitivity", "Supplementary"} else COLORS["boundary"])
        ax.text(0.04, y, label, color=color, fontweight="bold", fontsize=8, transform=ax.transAxes)
        ax.text(0.38, y, text, fontsize=8, transform=ax.transAxes)
        y -= 0.19
    ax.text(0.04, 0.06, "Not allowed: K562 primary co-pillar, RNAi primary evidence, broad cross-context validation.", fontsize=6, color="#666666", transform=ax.transAxes)
    add_panel_label(ax, "h", x=-0.04)


def tier_group(raw: str) -> str:
    if raw == "supplementary_confirmed":
        return "A0 confirmed"
    if raw == "supplementary_supporting":
        return "A1 supporting"
    return "B not eligible"


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    cov = pd.read_csv(root / COVARIATE_SUMMARY, sep="\t")
    anchor = pd.read_csv(root / ANCHOR_TIERING, sep="\t")
    temporal = load_temporal(root)
    structure = pd.read_csv(root / TEMPORAL_STRUCTURE, sep="\t")
    tiers_13 = pd.read_csv(root / K562_TIER_13D, sep="\t").assign(timepoint="13d")
    tiers_7 = pd.read_csv(root / K562_TIER_7D, sep="\t").assign(timepoint="7d")
    tiers = pd.concat([tiers_7, tiers_13], ignore_index=True)
    tiers["tier_group"] = tiers["evidence_tier"].map(tier_group)
    endpoint = load_endpoint(root)
    final_claim = pd.read_csv(root / FINAL_CLAIM_MATRIX, sep="\t")
    temporal_overview = temporal[["timepoint", "role", "n_formal_bridgeable_targets", "n_cells_with_single_feature", "n_control_cells"]].drop_duplicates()
    final_boundary = final_claim.loc[
        final_claim["object"].isin(["Dixit_K562_temporal_panel", "Dixit_K562_supplementary", "discovery_phenotype_shifter"]),
        ["object", "evidence_tier", "allowed_wording", "disallowed_wording"],
    ]
    # Add architecture class rows to tier source to preserve the confirmed backbone_plus_shift_excess call.
    arch = structure.loc[structure["comparison_field"].eq("architecture class"), ["timepoint", "comparison_field", "replication_status"]].copy()
    arch["object_type"] = "dataset_level"
    arch["object_id"] = "architecture_class"
    arch["observed_pattern"] = arch["replication_status"]
    arch["evidence_tier"] = "supplementary_confirmed"
    arch["claim_boundary"] = "architecture form confirmed; content-level replication not eligible"
    arch["tier_group"] = "A0 confirmed"
    tiers_for_plot = pd.concat([tiers[["timepoint", "object_type", "object_id", "observed_pattern", "evidence_tier", "claim_boundary", "tier_group"]], arch[["timepoint", "object_type", "object_id", "observed_pattern", "evidence_tier", "claim_boundary", "tier_group"]]], ignore_index=True)
    return {
        "a": cov,
        "b": anchor,
        "c": pd.DataFrame(
            [
                {"cell_line": "HCC38", "aggregation": "aggrMH001-3", "boundary": "design proxy, not run resolved"},
                {"cell_line": "HCC1143", "aggregation": "aggrMH004-6", "boundary": "design proxy, not run resolved"},
            ]
        ),
        "d": temporal_overview,
        "e": temporal[["timepoint", "role", "aligned_spearman", "mean_truth_metric", "median_truth_metric"]],
        "f": tiers_for_plot,
        "g": endpoint[["context", "platform_pair", "spearman", "n_shared_targets"]],
        "h": final_boundary,
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
        "a": "Covariate audit overview",
        "b": "Anchor tiers after covariate audit",
        "c": "barcode_gem_group boundary",
        "d": "K562 temporal panel overview",
        "e": "K562 temporal stratification",
        "f": "K562 A0/A1/B tiering",
        "g": "CRISPR versus RNAi endpoint hierarchy",
        "h": "Final claim boundary",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")
    fig = plt.figure(figsize=(11.0, 10.0))
    gs = fig.add_gridspec(4, 2, hspace=0.72, wspace=0.46)
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
    parser = argparse.ArgumentParser(description="Build manuscript Figure 6 boundary panels and assembly.")
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
            width=3.45 if panel_id in {"a", "g"} else 3.2,
            height=2.6 if panel_id in {"a", "g"} else 2.35,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
