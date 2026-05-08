from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import spearmanr

from wtbench.manuscript._palette import NEUTRAL_GRAY, SKY_BLUE, VERMILLION
from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes


FIGURE_ID = "extended_data_figure5"
FIGURE_TITLE = "Exploratory pathway-response polarity heatmap"
SCRIPT_PATH = Path("scripts/manuscript/build_extended_data_figure9_biological_landing.py")
CLAIM_BOUNDARY = (
    "Pathway enrichment is an exploratory response-level summary and was not used to define the benchmark truth "
    "object, endpoint hierarchy, or model-adjudication criteria. Cross-context polarity differences are interpreted "
    "as bounded response-level divergence rather than as closed mechanism."
)
PANEL_IDS = tuple("a")

PATHWAY_HCC38 = Path("reports/pathway_response/fgsea_hallmark_HCC38.tsv")
PATHWAY_HCC1143 = Path("reports/pathway_response/fgsea_hallmark_HCC1143.tsv")
PATHWAY_K562_7D = Path("reports/pathway_response/fgsea_hallmark_K562_7d.tsv")
PATHWAY_K562_13D = Path("reports/pathway_response/fgsea_hallmark_K562_13d.tsv")
SELECTED_GENE_SETS = Path("reports/pathway_response/selected_response_gene_set_panel.tsv")
SELECTED_TARGETS = Path("reports/pathway_response/selected_targets_for_display.tsv")
DISPLAY_LOG = Path("reports/pathway_response/qc/pathway_display_selection_log.json")
GENE_SET_PROVENANCE = Path("reports/pathway_response/qc/gene_set_provenance.json")

CONTEXT_ORDER = ("HCC38", "HCC1143", "K562_7d", "K562_13d")
PARTNER_CONTEXT = {
    "HCC38": "HCC1143",
    "HCC1143": "HCC38",
    "K562_7d": "K562_13d",
    "K562_13d": "K562_7d",
}
PATHWAY_CMAP = LinearSegmentedColormap.from_list("pathway_diverging", [SKY_BLUE, "#F7F7F7", VERMILLION])


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_extended_data_v1/edfig9_biological_landing"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [
        root / PATHWAY_HCC38,
        root / PATHWAY_HCC1143,
        root / PATHWAY_K562_7D,
        root / PATHWAY_K562_13D,
        root / SELECTED_GENE_SETS,
        root / SELECTED_TARGETS,
        root / DISPLAY_LOG,
        root / GENE_SET_PROVENANCE,
    ]


def cleanup_generated(root: Path) -> None:
    out = output_dir(root)
    if panel_dir(root).exists():
        for path in panel_dir(root).glob("edfig9_panel*"):
            path.unlink()
    for suffix in (".png", ".pdf", "_source_data.tsv", "_panel_manifest.json"):
        path = out / f"edfig9{suffix}"
        if path.exists():
            path.unlink()


def build_pathway_source(root: Path) -> pd.DataFrame:
    panel = pd.read_csv(root / SELECTED_GENE_SETS, sep="\t")
    target_selection = pd.read_csv(root / SELECTED_TARGETS, sep="\t")
    fgsea = pd.concat(
        [
            pd.read_csv(root / PATHWAY_HCC38, sep="\t"),
            pd.read_csv(root / PATHWAY_HCC1143, sep="\t"),
            pd.read_csv(root / PATHWAY_K562_7D, sep="\t"),
            pd.read_csv(root / PATHWAY_K562_13D, sep="\t"),
        ],
        ignore_index=True,
    )
    selected_pairs = set(zip(target_selection["context"], target_selection["target"], strict=False))
    selected_pathways = set(panel["exact_gs_name"])
    pathway_df = fgsea.loc[
        fgsea.apply(lambda row: (row["context"], row["target"]) in selected_pairs, axis=1)
        & fgsea["pathway"].isin(selected_pathways)
    ].copy()
    pathway_df = pathway_df.merge(
        panel[["display_group", "display_name", "exact_gs_name"]],
        left_on="pathway",
        right_on="exact_gs_name",
        how="left",
    )
    pathway_df["context_target"] = pathway_df["context"] + " / " + pathway_df["target"]
    context_order = {context: idx for idx, context in enumerate(CONTEXT_ORDER)}
    selection_order = target_selection.reset_index().rename(columns={"index": "row_order"})[
        ["context", "target", "row_order", "selection_tier", "selection_reason"]
    ]
    row_order = selection_order.assign(context_target=selection_order["context"] + " / " + selection_order["target"])
    row_order["row_order"] = row_order.index
    pathway_df = pathway_df.merge(
        row_order[["context_target", "row_order", "selection_tier", "selection_reason"]],
        on="context_target",
        how="left",
    )
    panel_order = panel.sort_values(["display_group", "exact_gs_name"]).reset_index(drop=True)
    pathway_df["pathway_order"] = pathway_df["pathway"].map({row.exact_gs_name: idx for idx, row in enumerate(panel_order.itertuples())})

    summary_rows: list[dict[str, float | int | str]] = []
    for row in row_order.itertuples():
        context = row.context
        target = row.target
        partner = PARTNER_CONTEXT[context]
        full_pivot = (
            fgsea.loc[fgsea["context"].isin([context, partner]) & fgsea["target"].eq(target)]
            .pivot_table(index="pathway", columns="context", values="NES", aggfunc="first")
            .dropna()
        )
        if full_pivot.empty:
            continue
        summary_rows.append(
            {
                "context": context,
                "target": target,
                "context_target": row.context_target,
                "partner_context": partner,
                "spearman_rho": float(spearmanr(full_pivot[context], full_pivot[partner]).statistic),
                "sign_agree_fraction": float(((full_pivot[context] * full_pivot[partner]) > 0).mean()),
                "n_pathways": int(len(full_pivot)),
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    pathway_df = pathway_df.merge(summary_df, on=["context", "target", "context_target"], how="left")
    return pathway_df.sort_values(["row_order", "pathway_order"]).reset_index(drop=True)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    source_a = build_pathway_source(root)
    return {"a": source_a}


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    # add_panel_label(ax, "a", x=-0.08, y=1.02)  # panel letter removed
    ax.text(
        0.02,
        1.02,
        "Exploratory pathway-level summaries of target-control perturbation responses",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.6,
        fontweight="bold",
    )

    heat_ax = ax.inset_axes([0.05, 0.17, 0.74, 0.76])
    sign_ax = ax.inset_axes([0.82, 0.17, 0.055, 0.76])
    rho_ax = ax.inset_axes([0.895, 0.17, 0.060, 0.76])
    cbar_ax = ax.inset_axes([0.985, 0.20, 0.012, 0.68])

    row_labels = list(df.sort_values("row_order")["context_target"].drop_duplicates())
    col_labels = list(df.sort_values("pathway_order")["display_name"].drop_duplicates())
    matrix = (
        df.pivot_table(index="context_target", columns="display_name", values="NES", aggfunc="first")
        .reindex(index=row_labels, columns=col_labels)
        .to_numpy(dtype=float)
    )
    sig = (
        df.assign(sig=df["padj"].lt(0.10))
        .pivot_table(index="context_target", columns="display_name", values="sig", aggfunc="first")
        .reindex(index=row_labels, columns=col_labels)
        .fillna(False)
        .to_numpy(dtype=bool)
    )

    im = heat_ax.imshow(matrix, cmap=PATHWAY_CMAP, vmin=-2.1, vmax=2.1, aspect="auto")
    heat_ax.set_xticks(range(len(col_labels)))
    heat_ax.set_xticklabels(col_labels, rotation=45, ha="right")
    heat_ax.set_yticks(range(len(row_labels)))
    heat_ax.set_yticklabels(row_labels)
    heat_ax.set_title("Pathway NES", loc="left", fontsize=8.0, fontweight="bold")
    row_contexts = [label.split(" / ", 1)[0] for label in row_labels]
    context_breaks = {idx for idx in range(1, len(row_contexts)) if row_contexts[idx] != row_contexts[idx - 1]}
    for i in range(matrix.shape[0]):
        if i in context_breaks:
            heat_ax.axhline(i - 0.5, color="white", linewidth=1.1)
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            heat_ax.text(
                j,
                i,
                f"{value:.1f}",
                ha="center",
                va="center",
                fontsize=4.9,
                color="white" if abs(value) > 1.35 else "#2F2F2F",
            )
            if sig[i, j]:
                heat_ax.text(j + 0.30, i - 0.26, "*", ha="center", va="center", fontsize=6.2, color="#1F1F1F")
    heat_ax.text(
        1.0,
        1.02,
        "* FDR < 0.10",
        ha="right",
        va="bottom",
        fontsize=5.8,
        color=NEUTRAL_GRAY,
        transform=heat_ax.transAxes,
    )
    clean_axes(heat_ax)
    for spine in heat_ax.spines.values():
        spine.set_visible(False)
    heat_ax.tick_params(length=0)
    cbar = plt.colorbar(im, cax=cbar_ax)
    cbar.ax.tick_params(labelsize=5.6, length=2)
    cbar.set_label("NES", fontsize=6.2)

    summary = (
        df[["context_target", "spearman_rho", "sign_agree_fraction"]]
        .drop_duplicates()
        .set_index("context_target")
        .reindex(row_labels)
    )
    sign_values = summary[["sign_agree_fraction"]].to_numpy(dtype=float) * 100
    rho_values = summary[["spearman_rho"]].to_numpy(dtype=float)

    sign_ax.imshow(sign_values, cmap="Greens", vmin=0, vmax=100, aspect="auto")
    rho_ax.imshow(rho_values, cmap=PATHWAY_CMAP, vmin=-1, vmax=1, aspect="auto")
    for i in range(len(row_labels)):
        sign_ax.text(0, i, f"{sign_values[i, 0]:.0f}", ha="center", va="center", fontsize=5.4, color="#1F1F1F")
        rho_ax.text(0, i, f"{rho_values[i, 0]:+.2f}", ha="center", va="center", fontsize=5.4, color="#1F1F1F")
        if i in context_breaks:
            sign_ax.axhline(i - 0.5, color="white", linewidth=1.1)
            rho_ax.axhline(i - 0.5, color="white", linewidth=1.1)

    for strip_ax, title in [(sign_ax, "Sign\nagree %"), (rho_ax, "Spearman\nρ")]:
        strip_ax.set_xticks([0])
        strip_ax.set_xticklabels([title])
        strip_ax.set_yticks([])
        strip_ax.tick_params(length=0)
        for spine in strip_ax.spines.values():
            spine.set_visible(False)


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {"a": render_panel_a}[panel_id]


def panel_title(panel_id: str) -> str:
    return {"a": "Pathway-response polarity heatmap"}[panel_id]


def write_panel(
    *,
    root: Path,
    panel_id: str,
    source_df: pd.DataFrame,
    render: Callable[[plt.Axes, pd.DataFrame], None],
    width: float = 10.8,
    height: float = 7.2,
) -> dict[str, Path]:
    pdir = ensure_dir(panel_dir(root))
    stem = f"edfig9_panel{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    output_paths = save_figure(fig, pdir / f"{stem}.png", pdir / f"{stem}.pdf")
    manifest_path = pdir / f"{stem}_manifest.json"
    write_panel_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        panel_id=f"ED5{panel_id}",
        panel_title=panel_title(panel_id),
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": output_paths[0], "pdf": output_paths[1], "manifest": manifest_path}


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> None:
    out = ensure_dir(output_dir(root))
    combined_source_path = write_tsv(sources["a"], out / "edfig9_source_data.tsv")
    fig, ax = plt.subplots(figsize=(10.8, 7.2))
    render_panel_a(ax, sources["a"])
    output_paths = save_figure(fig, out / "edfig9.png", out / "edfig9.pdf")
    write_figure_manifest(
        manifest_path=out / "edfig9_panel_manifest.json",
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs["a"]["manifest"]],
        combined_source_data_path=combined_source_path,
        output_paths=output_paths,
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build Extended Data Fig. 5 pathway polarity figure.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    apply_manuscript_style()
    root = repo_root()
    cleanup_generated(root)
    sources = build_sources(root)
    panel_outputs = {
        panel_id: write_panel(root=root, panel_id=panel_id, source_df=sources[panel_id], render=render_panel_by_id(panel_id))
        for panel_id in PANEL_IDS
    }
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
