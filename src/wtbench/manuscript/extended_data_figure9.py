from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes


FIGURE_ID = "extended_data_figure9"
FIGURE_TITLE = "Covariate audit details and wording boundary"
SCRIPT_PATH = Path("scripts/manuscript/build_extended_data_figure9.py")
CLAIM_BOUNDARY = "Covariate audit retains the bridge but prevents fully deconfounded wording."

COVARIATE_SUMMARY = Path("reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv")
BARCODE_NOTE = Path("reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/barcode_gem_group_mapping_note.md")
ANCHOR_TIERING = Path("reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_extended_data_v1/edfig9_covariate_audit"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / p for p in [COVARIATE_SUMMARY, BARCODE_NOTE, ANCHOR_TIERING, FINAL_CLAIM_MATRIX]]


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
    stem = f"edfig9_panel{panel_id}"
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
        panel_id=f"ED9{panel_id}",
        panel_title=panel_title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def covariate_label(value: str) -> str:
    labels = {
        "barcode_gem_group": "barcode gem group",
        "num_umis_over_threshold_bin": "UMI threshold",
        "num_umis_quantile_bin": "UMI quantile",
        "transcriptome_detected_genes_quantile_bin": "detected genes",
        "transcriptome_total_signal_quantile_bin": "total signal",
    }
    return labels.get(value, value.replace("_", " "))


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.groupby("strat_column", as_index=False).agg(mean_tvd=("mean_tvd", "mean"))
    plot["label"] = plot["strat_column"].map(covariate_label)
    plot = plot.sort_values("mean_tvd")
    y = range(len(plot))
    ax.barh(list(y), plot["mean_tvd"], color="#777777", height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot["label"])
    ax.set_xlabel("Mean TVD")
    ax.set_title("Covariate audit axes", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "a", x=-0.28)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.copy()
    plot["label"] = plot["strat_column"].map(covariate_label)
    xlabels = ["HCC38", "HCC1143"]
    x = range(len(xlabels))
    for label, sub in plot.groupby("label"):
        vals = [float(sub.loc[sub["cell_line"].eq(cl), "mean_tvd"].iloc[0]) for cl in xlabels]
        ax.plot(list(x), vals, marker="o", linewidth=1, label=label)
    ax.set_xticks(list(x))
    ax.set_xticklabels(xlabels)
    ax.set_ylabel("Mean TVD")
    ax.set_title("Covariate balance by cell line", loc="left")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1.02), borderaxespad=0)
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "b")


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("barcode_gem_group is design-proxy", loc="left", pad=4)
    rows = [
        ("HCC38", "aggrMH001-3", "not MH001/2/3 resolved"),
        ("HCC1143", "aggrMH004-6", "not MH004/5/6 resolved"),
    ]
    y = 0.76
    for cell, aggr, boundary in rows:
        ax.text(0.05, y, cell, fontweight="bold", fontsize=8, transform=ax.transAxes)
        ax.text(0.28, y, aggr, fontsize=8, color=COLORS["primary_qualified"], transform=ax.transAxes)
        ax.text(0.58, y, boundary, fontsize=7, color=COLORS["boundary"], transform=ax.transAxes)
        y -= 0.24
    ax.text(0.05, 0.12, "Allowed: aggregation/design proxy. Not allowed: single-run MH00x label.", fontsize=7, transform=ax.transAxes)
    add_panel_label(ax, "c", x=-0.04)


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.groupby("strat_column", as_index=False).agg(n_targets_tvd_gt_025=("n_targets_tvd_gt_0.25", "sum"))
    plot["label"] = plot["strat_column"].map(covariate_label)
    plot = plot.sort_values("n_targets_tvd_gt_025")
    y = range(len(plot))
    ax.barh(list(y), plot["n_targets_tvd_gt_025"], color=COLORS["supporting"], height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot["label"])
    ax.set_xlabel("Targets with TVD > 0.25")
    ax.set_title("High-imbalance target counts", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "d", x=-0.28)


def render_panel_e(ax: plt.Axes, df: pd.DataFrame) -> None:
    colors = df["final_wording_tier"].map({"primary_but_qualified": COLORS["primary_qualified"], "supporting_only": COLORS["supporting"]})
    y = range(len(df))
    ax.barh(list(y), [1] * len(df), color=colors, height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(df["target_gene"])
    ax.set_xticks([])
    for yi, row in zip(y, df.itertuples()):
        ax.text(0.03, yi, row.final_wording_tier.replace("_", " "), va="center", fontsize=7, color="white" if row.final_wording_tier == "primary_but_qualified" else "#222222")
    ax.set_title("Covariate audit governs anchor wording", loc="left")
    clean_axes(ax)
    add_panel_label(ax, "e", x=-0.20)


def render_panel_f(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.loc[df["level"].isin(["global", "anchor", "axis", "covariate_axis"])].copy()
    plot = plot.groupby(["level", "covariate_status"], as_index=False).size().rename(columns={"size": "n"})
    plot["label"] = plot["level"] + "\n" + plot["covariate_status"].str.replace("_", " ")
    plot = plot.sort_values("n")
    y = range(len(plot))
    ax.barh(list(y), plot["n"], color="#8A8A8A", height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot["label"])
    ax.set_xlabel("Objects")
    ax.set_title("Covariate status in final matrix", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "f", x=-0.35)


def render_panel_g(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Allowed wording", loc="left", pad=4)
    rows = df.loc[df["object"].isin(["global_truth_depmap_bridge", "barcode_gem_group_design_proxy", "PFDN5", "transcription_chromatin_axis"])]
    y = 0.84
    for row in rows.itertuples():
        label = row.object.replace("_", " ")
        ax.text(0.04, y, label[:32], fontweight="bold", fontsize=7, transform=ax.transAxes)
        ax.text(0.04, y - 0.08, row.evidence_tier.replace("_", " "), fontsize=7, color=COLORS["primary_qualified"] if "primary" in row.evidence_tier or "retainable" in row.evidence_tier else COLORS["supporting"], transform=ax.transAxes)
        y -= 0.19
    add_panel_label(ax, "g", x=-0.04)


def render_panel_h(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Disallowed wording", loc="left", pad=4)
    rows = [
        ("bridge", "fully deconfounded"),
        ("barcode", "single MH00x resolved"),
        ("anchors", "clean primary anchors"),
        ("axis", "fully established architecture"),
    ]
    y = 0.80
    for label, text in rows:
        ax.text(0.05, y, label, fontweight="bold", fontsize=8, transform=ax.transAxes)
        ax.text(0.34, y, text, fontsize=8, color=COLORS["boundary"], transform=ax.transAxes)
        y -= 0.19
    ax.text(0.05, 0.08, "Covariate audit is a wording governor, not a full deconfounding proof.", fontsize=7, color="#555555", transform=ax.transAxes)
    add_panel_label(ax, "h", x=-0.04)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    cov = pd.read_csv(root / COVARIATE_SUMMARY, sep="\t")
    tier = pd.read_csv(root / ANCHOR_TIERING, sep="\t")
    claim = pd.read_csv(root / FINAL_CLAIM_MATRIX, sep="\t")
    barcode = pd.DataFrame(
        [
            {"cell_line": "HCC38", "aggregation": "aggrMH001-3", "boundary": "design_proxy_not_run_resolved"},
            {"cell_line": "HCC1143", "aggregation": "aggrMH004-6", "boundary": "design_proxy_not_run_resolved"},
        ]
    )
    barcode_claim = claim.loc[claim["object"].eq("barcode_gem_group_design_proxy")].iloc[0]
    if barcode_claim["evidence_tier"] != "methodological_boundary":
        raise RuntimeError("ED Fig. 9 sanity check failed: barcode_gem_group tier changed.")
    expected = tier.set_index("target_gene")["final_wording_tier"].to_dict()
    if expected != {"PFDN5": "primary_but_qualified", "PMF1": "supporting_only", "PRPF6": "supporting_only", "ZNF131": "supporting_only"}:
        raise RuntimeError("ED Fig. 9 sanity check failed: anchor tiers changed.")
    if not cov["strat_column"].isin(["barcode_gem_group"]).any():
        raise RuntimeError("ED Fig. 9 sanity check failed: barcode_gem_group covariate missing.")
    return {"a": cov, "b": cov, "c": barcode, "d": cov, "e": tier, "f": claim, "g": claim, "h": claim}


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
        "a": "Covariate audit axes",
        "b": "Cell-line covariate balance",
        "c": "Barcode-gem-group boundary",
        "d": "High-imbalance target counts",
        "e": "Anchor wording impact",
        "f": "Final matrix covariate status",
        "g": "Allowed wording",
        "h": "Disallowed wording",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> None:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / "edfig9_source_data.tsv")
    fig = plt.figure(figsize=(11.0, 10.0))
    gs = fig.add_gridspec(4, 2, hspace=0.78, wspace=0.54)
    axes = [fig.add_subplot(gs[i, j]) for i in range(4) for j in range(2)]
    for ax, panel_id in zip(axes, list("abcdefgh")):
        render_panel_by_id(panel_id)(ax, sources[panel_id])
    fig.suptitle(FIGURE_TITLE, x=0.02, y=0.995, ha="left", fontsize=10, fontweight="bold")
    png_path = out / "edfig9.png"
    pdf_path = out / "edfig9.pdf"
    output_paths = save_figure(fig, png_path, pdf_path)
    write_figure_manifest(
        manifest_path=out / "edfig9_panel_manifest.json",
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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build Extended Data Fig. 9 covariate audit panels.")
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
            width=3.65 if panel_id in {"b", "f"} else 3.2,
            height=2.75 if panel_id in {"b", "f"} else 2.35,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
