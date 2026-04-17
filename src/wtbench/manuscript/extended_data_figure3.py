from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes


FIGURE_ID = "extended_data_figure3"
FIGURE_TITLE = "Anchor sensitivity and claim tiering"
SCRIPT_PATH = Path("scripts/manuscript/build_extended_data_figure3.py")
CLAIM_BOUNDARY = "Anchor stability supports the bridge, but covariate-aware governance prevents fully deconfounded anchor wording."

SHARED_ANCHORS = Path("reports/stage2_truth_bridge_decomposition/shared_canonical_anchor_summary.tsv")
EVIDENCE_TIER = Path("reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv")
CONTROL_SUBSAMPLE = Path("reports/stage2_truth_driven_bridge/sensitivity/control_subsample_summary.tsv")
ANCHOR_TIERING = Path("reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_extended_data_v1/edfig3_anchor_sensitivity"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / p for p in [SHARED_ANCHORS, EVIDENCE_TIER, CONTROL_SUBSAMPLE, ANCHOR_TIERING, FINAL_CLAIM_MATRIX]]


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
    stem = f"edfig3_panel{panel_id}"
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
        panel_id=f"ED3{panel_id}",
        panel_title=panel_title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    colors = df["shared_anchor_call"].map({"shared_canonical_anchor": COLORS["primary_qualified"]}).fillna("#BDBDBD")
    ax.scatter(df["depmap_quantile_mean"], df["shift_quantile_mean"], c=colors, s=28, edgecolor="white", linewidth=0.4)
    for gene in ["PFDN5", "PMF1", "PRPF6", "ZNF131"]:
        row = df.loc[df["target_gene"].eq(gene)].iloc[0]
        ax.text(row["depmap_quantile_mean"] + 0.012, row["shift_quantile_mean"], gene, fontsize=6)
    ax.set_xlabel("Dependency quantile")
    ax.set_ylabel("Shift quantile")
    ax.set_title("Full target-level anchor distribution", loc="left")
    clean_axes(ax)
    ax.grid(color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "a")


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.loc[df["shared_anchor_call"].eq("shared_canonical_anchor")].sort_values("depmap_strength_mean")
    y = range(len(plot))
    ax.barh(list(y), plot["depmap_strength_mean"], color=COLORS["primary_qualified"], height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot["target_gene"])
    ax.set_xlabel("Mean dependency strength")
    ax.set_title("Shared canonical anchors", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "b", x=-0.22)


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.loc[df["evidence_tier"].eq("supporting_but_sensitive")].sort_values("stability_fraction")
    y = range(len(plot))
    ax.barh(list(y), plot["stability_fraction"], color=COLORS["supporting"], height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot["object_id"])
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Stability fraction")
    ax.set_title("Cutoff-sensitive supporting objects", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "c", x=-0.24)


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.loc[df["truth_metric"].eq("real_shift_mean_abs") & df["depmap_endpoint"].eq("depmap_gene_dependency")].copy()
    x = range(len(plot))
    ax.errorbar(
        list(x),
        plot["spearman_aligned_mean"],
        yerr=[plot["spearman_aligned_mean"] - plot["spearman_aligned_q025"], plot["spearman_aligned_q975"] - plot["spearman_aligned_mean"]],
        fmt="o",
        color=COLORS["baseline"],
        ecolor="#777777",
        capsize=3,
    )
    ax.set_xticks(list(x))
    ax.set_xticklabels(plot["cell_line"])
    ax.set_ylabel("Aligned Spearman")
    ax.set_title("Control subsampling keeps bridge intervals citable", loc="left")
    ax.set_ylim(0.68, 0.81)
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "d")


def render_panel_e(ax: plt.Axes, df: pd.DataFrame) -> None:
    colors = df["final_wording_tier"].map({"primary_but_qualified": COLORS["primary_qualified"], "supporting_only": COLORS["supporting"]})
    y = range(len(df))
    ax.barh(list(y), [1] * len(df), color=colors, height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(df["target_gene"])
    ax.set_xticks([])
    for yi, row in zip(y, df.itertuples()):
        ax.text(0.03, yi, row.final_wording_tier.replace("_", " "), va="center", fontsize=7, color="white" if row.final_wording_tier == "primary_but_qualified" else "#222222")
    ax.set_title("Covariate-aware anchor wording", loc="left")
    clean_axes(ax)
    add_panel_label(ax, "e", x=-0.20)


def render_panel_f(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.groupby("evidence_tier", as_index=False).size().rename(columns={"size": "n"})
    plot = plot.sort_values("n")
    y = range(len(plot))
    ax.barh(list(y), plot["n"], color="#8A8A8A", height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot["evidence_tier"])
    ax.set_xlabel("Objects")
    ax.set_title("Evidence tiers include many non-primary objects", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "f", x=-0.32)


def render_panel_g(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Anchor downgrade rationale", loc="left", pad=4)
    y = 0.82
    for row in df.itertuples():
        ax.text(0.04, y, row.target_gene, fontweight="bold", fontsize=8, transform=ax.transAxes)
        ax.text(0.24, y, row.covariate_cleanliness, fontsize=7, color=COLORS["boundary"] if "exposed" in row.covariate_cleanliness else COLORS["primary_qualified"], transform=ax.transAxes)
        y -= 0.18
    ax.text(0.04, 0.08, "Structural stability is not equivalent to deconfounded primary wording.", fontsize=7, color="#555555", transform=ax.transAxes)
    add_panel_label(ax, "g", x=-0.04)


def render_panel_h(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Allowed and disallowed anchor claims", loc="left", pad=4)
    rows = df.loc[df["object"].isin(["PFDN5", "PMF1", "PRPF6", "ZNF131"])]
    y = 0.82
    for row in rows.itertuples():
        ax.text(0.04, y, row.object, fontweight="bold", fontsize=8, transform=ax.transAxes)
        ax.text(0.22, y, row.evidence_tier, fontsize=7, color=COLORS["primary_qualified"] if "primary" in row.evidence_tier else COLORS["supporting"], transform=ax.transAxes)
        y -= 0.16
    ax.text(0.04, 0.12, "Not allowed: fully deconfounded strongest anchors.", fontsize=7, color=COLORS["boundary"], transform=ax.transAxes)
    add_panel_label(ax, "h", x=-0.04)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    shared = pd.read_csv(root / SHARED_ANCHORS, sep="\t")
    evidence = pd.read_csv(root / EVIDENCE_TIER, sep="\t")
    subsample = pd.read_csv(root / CONTROL_SUBSAMPLE, sep="\t")
    tiering = pd.read_csv(root / ANCHOR_TIERING, sep="\t")
    claim = pd.read_csv(root / FINAL_CLAIM_MATRIX, sep="\t")
    expected = tiering.set_index("target_gene")["final_wording_tier"].to_dict()
    if expected != {"PFDN5": "primary_but_qualified", "PMF1": "supporting_only", "PRPF6": "supporting_only", "ZNF131": "supporting_only"}:
        raise RuntimeError("ED Fig. 3 sanity check failed: anchor claim tiers changed.")
    shared_primary = shared.loc[shared["shared_anchor_call"].eq("shared_canonical_anchor"), "target_gene"].tolist()
    if not {"PFDN5", "PMF1", "PRPF6", "ZNF131"}.issubset(shared_primary):
        raise RuntimeError("ED Fig. 3 sanity check failed: primary shared anchors are missing.")
    return {
        "a": shared,
        "b": shared,
        "c": evidence,
        "d": subsample,
        "e": tiering,
        "f": evidence,
        "g": tiering,
        "h": claim,
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
        "a": "Full target-level anchor distribution",
        "b": "Shared canonical anchors",
        "c": "Cutoff-sensitive supporting objects",
        "d": "Control subsampling intervals",
        "e": "Covariate-aware wording tiers",
        "f": "Evidence-tier composition",
        "g": "Downgrade rationale",
        "h": "Anchor claim boundary",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> None:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / "edfig3_source_data.tsv")
    fig = plt.figure(figsize=(11.0, 10.0))
    gs = fig.add_gridspec(4, 2, hspace=0.78, wspace=0.50)
    axes = [fig.add_subplot(gs[i, j]) for i in range(4) for j in range(2)]
    for ax, panel_id in zip(axes, list("abcdefgh")):
        render_panel_by_id(panel_id)(ax, sources[panel_id])
    fig.suptitle(FIGURE_TITLE, x=0.02, y=0.995, ha="left", fontsize=10, fontweight="bold")
    png_path = out / "edfig3.png"
    pdf_path = out / "edfig3.pdf"
    output_paths = save_figure(fig, png_path, pdf_path)
    write_figure_manifest(
        manifest_path=out / "edfig3_panel_manifest.json",
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
    parser = argparse.ArgumentParser(description="Build Extended Data Fig. 3 anchor sensitivity and tiering panels.")
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
            width=3.55 if panel_id in {"a", "f"} else 3.2,
            height=2.7 if panel_id in {"a", "f"} else 2.35,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
