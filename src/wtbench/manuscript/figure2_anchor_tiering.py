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


FIGURE_ID = "figure2"
FIGURE_TITLE = "Shared anchors form a tiered target-level bridge rather than clean primary objects"
SCRIPT_PATH = Path("scripts/manuscript/build_figure2_anchor_tiering.py")
CLAIM_BOUNDARY = "Shared anchors support the bridge but must not be described as fully deconfounded primary objects."

SHARED_ANCHORS = Path("reports/stage2_truth_bridge_decomposition/shared_canonical_anchor_summary.tsv")
TARGET_GRID = Path("reports/stage2_truth_bridge_decomposition/target_level_joint_grid.tsv")
ANCHOR_STABILITY = Path("reports/stage2_truth_bridge_decomposition/shared_anchor_stability.tsv")
ANCHOR_CUTOFF = Path("reports/stage2_truth_bridge_decomposition/anchor_cutoff_sensitivity.tsv")
ANCHOR_TIERING = Path("reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")

EXPECTED_TIERS = {
    "PFDN5": "primary_but_qualified",
    "PMF1": "supporting_only",
    "PRPF6": "supporting_only",
    "ZNF131": "supporting_only",
}

TIER_COLORS = {
    "primary_but_qualified": "#2E7D52",
    "supporting_only": "#B59B2B",
    "supporting_but_sensitive": "#C4A15A",
    "supporting_but_unstable": "#BDBDBD",
    "preliminary_only": "#D9D9D9",
}


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig2_anchor_tiering"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / p for p in [SHARED_ANCHORS, TARGET_GRID, ANCHOR_STABILITY, ANCHOR_CUTOFF, ANCHOR_TIERING, FINAL_CLAIM_MATRIX]]


def load_anchor_tiering(root: Path) -> pd.DataFrame:
    tier = pd.read_csv(root / ANCHOR_TIERING, sep="\t")
    observed = dict(zip(tier["target_gene"], tier["final_wording_tier"]))
    for gene, expected in EXPECTED_TIERS.items():
        if observed.get(gene) != expected:
            raise RuntimeError(f"Fig. 2 anchor tier sanity check failed for {gene}: observed={observed.get(gene)}, expected={expected}")
    return tier


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
    plot = df.sort_values("depmap_quantile_mean", ascending=True)
    y = np.arange(len(plot))
    ax.scatter(plot["shift_quantile_mean"], y, color="white", edgecolor="#333333", s=36, label="shift quantile")
    ax.scatter(plot["depmap_quantile_mean"], y, color="#333333", edgecolor="white", s=36, label="dependency quantile")
    for yi, row in zip(y, plot.itertuples()):
        ax.plot([row.shift_quantile_mean, row.depmap_quantile_mean], [yi, yi], color="#BBBBBB", linewidth=0.8, zorder=0)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["target_gene"])
    ax.set_xlim(0.72, 1.02)
    ax.set_xlabel("Mean within-cell-line quantile")
    ax.set_title("Shared-canonical candidates occupy high joint ranks", loc="left")
    ax.text(0.98, 0.06, "open = shift\nfilled = dependency", transform=ax.transAxes, fontsize=5.8, ha="right", color="#555555")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "a", x=-0.22)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    anchors = sorted(df["target_gene"].unique())
    matrix = df.pivot_table(index="target_gene", columns="cell_line", values="is_q1_anchor", aggfunc="max").reindex(anchors).fillna(False)
    arr = matrix.astype(int).to_numpy()
    ax.imshow(arr, aspect="auto", cmap="Greens", vmin=0, vmax=1)
    ax.set_yticks(np.arange(len(matrix)))
    ax.set_yticklabels(matrix.index)
    ax.set_xticks(np.arange(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            ax.text(j, i, "Q1" if arr[i, j] else "", ha="center", va="center", fontsize=6)
    ax.set_title("Stable anchors recur across both HCC contexts", loc="left")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    add_panel_label(ax, "b", x=-0.22)


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.loc[df["stability_call"].isin(["stable_shared_anchor", "cutoff_sensitive_shared_anchor"])].copy()
    plot = plot.sort_values("shared_anchor_stability_fraction", ascending=True)
    y = np.arange(len(plot))
    colors = np.where(plot["stability_call"].eq("stable_shared_anchor"), COLORS["primary_qualified"], "#B59B2B")
    ax.barh(y, plot["shared_anchor_stability_fraction"], color=colors, height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["target_gene"])
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Shared-anchor stability fraction")
    ax.set_title("Cutoff sensitivity separates stable from sensitive anchors", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "c", x=-0.22)


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.copy().sort_values("depmap_quantile_mean", ascending=False)
    x = np.arange(len(plot))
    ax.bar(x - 0.18, plot["shift_quantile_mean"], width=0.36, color="#D9D9D9", label="shift")
    ax.bar(x + 0.18, plot["depmap_quantile_mean"], width=0.36, color=COLORS["baseline"], label="dependency")
    ax.set_xticks(x)
    ax.set_xticklabels(plot["target_gene"], rotation=30, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Mean quantile")
    ax.set_title("Final stable anchors retain high shift and dependency ranks", loc="left")
    ax.text(0.02, 0.94, "light = shift; dark = dependency", transform=ax.transAxes, fontsize=6, color="#555555")
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "d")


def render_panel_e(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.sort_values("shared_anchor_stability_fraction", ascending=True)
    y = np.arange(len(plot))
    ax.barh(y, plot["shared_anchor_stability_fraction"], color="#B59B2B", height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["target_gene"])
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Stability fraction")
    ax.set_title("Supporting objects remain cutoff sensitive", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "e", x=-0.22)


def render_panel_f(ax: plt.Axes, df: pd.DataFrame) -> None:
    counts = df["evidence_tier"].value_counts().rename_axis("tier").reset_index(name="n")
    counts["color"] = counts["tier"].map(TIER_COLORS).fillna("#CCCCCC")
    x = np.arange(len(counts))
    ax.bar(x, counts["n"], color=counts["color"])
    for xi, row in zip(x, counts.itertuples()):
        ax.text(xi, row.n + 0.05, str(row.n), ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(counts["tier"].str.replace("_", "\n"), rotation=0)
    ax.set_ylabel("Objects")
    ax.set_title("Final claim matrix tiers bridge objects", loc="left")
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "f")


def render_panel_g(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Anchor claim matrix", loc="left", pad=4)
    y = 0.84
    for row in df.itertuples():
        color = TIER_COLORS.get(row.final_wording_tier, "#CCCCCC")
        ax.text(0.03, y, row.target_gene, fontsize=8, fontweight="bold", transform=ax.transAxes)
        ax.text(0.36, y, row.final_wording_tier.replace("_", " "), fontsize=7, color=color, fontweight="bold", transform=ax.transAxes)
        ax.text(0.03, y - 0.07, row.covariate_cleanliness.replace("_", " "), fontsize=5.8, color="#666666", transform=ax.transAxes)
        y -= 0.22
    add_panel_label(ax, "g", x=-0.04)


def render_panel_h(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Anchor-level wording boundary", loc="left", pad=4)
    rows = [
        ("Allowed", "shared anchors support a structured bridge"),
        ("Allowed", "PFDN5 is primary but qualified"),
        ("Not allowed", "anchors are fully deconfounded strongest objects"),
        ("Not allowed", "one anchor proves the bridge"),
    ]
    y = 0.86
    for status, text in rows:
        color = COLORS["primary_qualified"] if status == "Allowed" else COLORS["boundary"]
        ax.text(0.02, y, status, color=color, fontweight="bold", fontsize=7, transform=ax.transAxes)
        ax.text(0.34, y, text, fontsize=7, transform=ax.transAxes)
        y -= 0.18
    ax.text(0.02, 0.05, "Boundary fixed by anchor claim tiering.", fontsize=6, color="#666666", transform=ax.transAxes)
    add_panel_label(ax, "h", x=-0.04)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    shared = pd.read_csv(root / SHARED_ANCHORS, sep="\t")
    tier = load_anchor_tiering(root)
    stability = pd.read_csv(root / ANCHOR_STABILITY, sep="\t")
    target_grid = pd.read_csv(root / TARGET_GRID, sep="\t")
    final_claim = pd.read_csv(root / FINAL_CLAIM_MATRIX, sep="\t")

    shared_candidates = shared.loc[shared["shared_anchor_call"].eq("shared_canonical_anchor")].copy()
    final_stable = shared_candidates.loc[shared_candidates["target_gene"].isin(EXPECTED_TIERS)].copy()
    recurrence = target_grid.loc[target_grid["target_gene"].isin(EXPECTED_TIERS), ["target_gene", "cell_line", "is_q1_anchor"]].copy()
    sensitive = stability.loc[stability["stability_call"].eq("cutoff_sensitive_shared_anchor")].copy()
    sensitive = sensitive.loc[sensitive["target_gene"].isin(["ENY2", "NPM1", "RPS3", "RUVBL2", "ZBTB17"])]
    claim_rows = final_claim.loc[
        final_claim["object"].isin(["PFDN5", "PMF1", "PRPF6", "ZNF131", "cutoff_sensitive_anchor_set"]),
        ["object", "evidence_tier", "allowed_wording", "disallowed_wording"],
    ]
    return {
        "a": shared_candidates[["target_gene", "shift_quantile_mean", "depmap_quantile_mean", "q1_anchor_count"]],
        "b": recurrence,
        "c": stability.loc[stability["target_gene"].isin(list(EXPECTED_TIERS) + ["RPS3", "RUVBL2", "ZBTB17", "ENY2", "NPM1"])],
        "d": final_stable[["target_gene", "shift_quantile_mean", "depmap_quantile_mean", "shift_value_mean", "depmap_strength_mean"]],
        "e": sensitive[["target_gene", "shared_anchor_stability_fraction", "stability_call"]],
        "f": claim_rows.rename(columns={"object": "target_or_group"}),
        "g": tier,
        "h": claim_rows,
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
        "a": "Shared-canonical anchor ranking",
        "b": "Stable anchor recurrence",
        "c": "Anchor cutoff stability",
        "d": "Representative stable anchors",
        "e": "Cutoff-sensitive supporting objects",
        "f": "Evidence-tier summary",
        "g": "Anchor claim matrix",
        "h": "Anchor-level wording boundary",
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
    parser = argparse.ArgumentParser(description="Build manuscript Figure 2 anchor-tiering panels and assembly.")
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
            width=3.45 if panel_id in {"a", "c", "e"} else 3.2,
            height=2.6 if panel_id in {"a", "c", "e"} else 2.35,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
