from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import (
    COLORS,
    add_panel_heading,
    apply_manuscript_style,
    clean_axes,
    finalize_manuscript_figure,
)


FIGURE_ID = "figure1"
PUBLIC_FIGURE_ID = "Figure_1"
FIGURE_TITLE = "Endpoint-aligned recovery object and resource evidence landscape"
SCRIPT_PATH = Path("scripts/manuscript/build_figure1_truth_object.py")
CLAIM_BOUNDARY = (
    "WTShiftBench defines a fixed endpoint-recovery object and audits "
    "model-generated perturbation shifts. It is not a direct DepMap predictor, "
    "broad model-generalization benchmark, or causal fitness-inference engine."
)

GOVERNANCE = Path("reports/resource_governance_strengthening/dataset_governance_decision_table.tsv")
JOINT_GRID = Path("reports/truth_bridge_decomposition/target_level_joint_grid.tsv")
BRIDGE_SUMMARY = Path("reports/external_bridge_form_robustness/observed_shift_depmap_bridge_summary.tsv")
MODEL_METRICS = Path("reports/model_endpoint_recovery/source_data/model_endpoint_recovery_metrics.tsv")
MODEL_REGISTRY = Path("resource_registry/model_entrant_registry.tsv")
CLAIM_REGISTRY = Path("resource_registry/claim_boundary_registry.tsv")


CATEGORY_COLORS = {
    "Anchor": COLORS["scgen"],
    "Shift-excess": COLORS["cpa"],
    "Dependency-excess": COLORS["accent_purple"],
    "Low-information": COLORS["low_info"],
    "Middle": COLORS["middle"],
}

LAYER_COLORS = {
    "Primary model-audit layer": COLORS["scgen"],
    "External bridge-form / boundary layer": COLORS["gears"],
    "Secondary endpoint-extension layer": COLORS["supporting"],
    "Narrow pathway boundary candidate": COLORS["cpa"],
    "Excluded / future-extension registry": "#9A9A9A",
}

LIGHT_GREEN_CMAP = LinearSegmentedColormap.from_list(
    "wtbench_light_green", ["#FAFCFA", "#DDEFE2", "#5DAE7E"]
)


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig1_truth_object"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_1"


def manuscript_panel_dir(root: Path) -> Path:
    return manuscript_figure_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    paths = [root / GOVERNANCE, root / JOINT_GRID, root / BRIDGE_SUMMARY, root / MODEL_METRICS, root / MODEL_REGISTRY, root / CLAIM_REGISTRY]
    return [p for p in paths if p.exists()]


def evaluation_object_source() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"evaluation_object": "expression-centric", "x": 0.12, "y": 0.18, "role": "observed profile"},
            {"evaluation_object": "expression-centric", "x": 0.24, "y": 0.34, "role": "observed profile"},
            {"evaluation_object": "expression-centric", "x": 0.36, "y": 0.42, "role": "observed profile"},
            {"evaluation_object": "expression-centric", "x": 0.48, "y": 0.52, "role": "observed profile"},
            {"evaluation_object": "expression-centric", "x": 0.60, "y": 0.60, "role": "observed profile"},
            {"evaluation_object": "endpoint-anchored", "x": 0.17, "y": 0.16, "role": "low-information"},
            {"evaluation_object": "endpoint-anchored", "x": 0.84, "y": 0.84, "role": "anchor"},
            {"evaluation_object": "endpoint-anchored", "x": 0.50, "y": 0.52, "role": "middle"},
        ]
    )


def endpoint_plane_source(root: Path) -> pd.DataFrame:
    if (root / JOINT_GRID).exists():
        df = pd.read_csv(root / JOINT_GRID, sep="\t")
        keep = df.loc[df["cell_line"].isin(["HCC38", "HCC1143"])].copy()
        keep["category"] = keep["joint_grid"].map(
            {
                "Q1_anchor": "Anchor",
                "Q2_transcriptomic_excess": "Shift-excess",
                "Q3_dependency_excess": "Dependency-excess",
                "Q4_low_information": "Low-information",
                "middle": "Middle",
            }
        ).fillna("Middle")
        return keep[
            [
                "cell_line",
                "target_gene",
                "depmap_quantile",
                "shift_quantile",
                "depmap_strength",
                "real_shift_mean_abs",
                "category",
            ]
        ].copy()
    return pd.DataFrame(
        [
            {"cell_line": "schematic", "target_gene": "anchor", "depmap_quantile": 0.84, "shift_quantile": 0.84, "category": "Anchor"},
            {"cell_line": "schematic", "target_gene": "low", "depmap_quantile": 0.17, "shift_quantile": 0.17, "category": "Low-information"},
            {"cell_line": "schematic", "target_gene": "middle", "depmap_quantile": 0.50, "shift_quantile": 0.50, "category": "Middle"},
        ]
    )


def dataset_layer_source(root: Path) -> pd.DataFrame:
    if (root / GOVERNANCE).exists():
        gov = pd.read_csv(root / GOVERNANCE, sep="\t")
        rows = []
        mapping = {
            "Primary model-audit layer": ["HCC38 day 14", "HCC1143 day 14"],
            "External bridge-form / boundary layer": [
                "K562 TF day 7",
                "K562 TF day 13",
                "K562 essential CRISPRi day 6",
                "K562 genome-scale CRISPRi day 8",
            ],
            "Secondary endpoint-extension layer": ["HepG2 day 7", "Jurkat day 7"],
            "Narrow pathway boundary candidate": ["Adamson K562 UPR Perturb-seq", "MOLM13 mSWI/SNF Perturb-seq"],
            "Excluded / future-extension registry": [
                "RPE1 essential CRISPRi day 7",
                "Norman K562 CRISPRa",
                "Gasperini K562 enhancer CRISPRi",
                "THP-1 stimulated Perturb-seq",
                "Frangieh melanoma/TIL Perturb-CITE-seq",
            ],
        }
        for layer, contexts in mapping.items():
            matched = gov.loc[gov["context"].isin(contexts)].copy()
            observed = "; ".join(matched["context"].astype(str).tolist()) if not matched.empty else "; ".join(contexts)
            rows.append({"evidence_layer": layer, "contexts": observed, "n_contexts": len(contexts)})
        return pd.DataFrame(rows)
    return pd.DataFrame(
        [
            {"evidence_layer": "Primary model-audit layer", "contexts": "HCC38 day 14; HCC1143 day 14", "n_contexts": 2},
            {"evidence_layer": "External bridge-form / boundary layer", "contexts": "K562 temporal; Replogle CRISPRi", "n_contexts": 4},
            {"evidence_layer": "Secondary endpoint-extension layer", "contexts": "HepG2 day 7; Jurkat day 7", "n_contexts": 2},
            {"evidence_layer": "Excluded / future-extension registry", "contexts": "non-cancer, GOF, enhancer, stimulation, co-culture", "n_contexts": 5},
        ]
    )


def analysis_coverage_source() -> pd.DataFrame:
    rows = [
        ("HCC38/HCC1143", "Observed bridge", 1),
        ("HCC38/HCC1143", "DepMap matched", 1),
        ("HCC38/HCC1143", "Category grid", 1),
        ("HCC38/HCC1143", "Model audit", 1),
        ("HCC38/HCC1143", "Response GSEA", 1),
        ("K562 temporal", "Observed bridge", 1),
        ("K562 temporal", "DepMap matched", 1),
        ("K562 temporal", "Category grid", 0.35),
        ("K562 temporal", "Model audit", 0),
        ("K562 temporal", "Response GSEA", 0),
        ("Replogle K562", "Observed bridge", 1),
        ("Replogle K562", "DepMap matched", 1),
        ("Replogle K562", "Category grid", 0.35),
        ("Replogle K562", "Model audit", 0),
        ("Replogle K562", "Response GSEA", 0),
        ("HepG2/Jurkat", "Observed bridge", 1),
        ("HepG2/Jurkat", "DepMap matched", 1),
        ("HepG2/Jurkat", "Category grid", 1),
        ("HepG2/Jurkat", "Model audit", 0),
        ("HepG2/Jurkat", "Response GSEA", 0),
        ("MOLM13/Adamson", "Observed bridge", 0.35),
        ("MOLM13/Adamson", "DepMap matched", 0.35),
        ("MOLM13/Adamson", "Category grid", 0),
        ("MOLM13/Adamson", "Model audit", 0),
        ("MOLM13/Adamson", "Response GSEA", 0),
    ]
    return pd.DataFrame(rows, columns=["context_group", "analysis_module", "status"])


def render_evaluation_contrast(ax: plt.Axes, source: pd.DataFrame) -> None:
    add_panel_heading(ax, "a", "Evaluation object", label_x=-0.08)
    ax.set_axis_off()
    left = ax.inset_axes([0.03, 0.18, 0.42, 0.70])
    right = ax.inset_axes([0.55, 0.18, 0.42, 0.70])
    left.set_title("Expression-centric", fontsize=6.8, pad=3)
    d = source.loc[source["evaluation_object"].eq("expression-centric")]
    left.plot(d["x"], d["y"], color=COLORS["middle"], lw=1.0)
    left.scatter(d["x"], d["y"], s=28, color=COLORS["middle"], edgecolor="white", linewidth=0.4)
    left.scatter(d["x"] + 0.03, d["y"] + 0.04, s=24, color=COLORS["gears"], edgecolor="white", linewidth=0.4, alpha=0.9)
    left.set_xlabel("Observed profile", fontsize=5.5)
    left.set_ylabel("Predicted profile", fontsize=5.5)
    left.set_xticks([])
    left.set_yticks([])
    clean_axes(left)
    right.set_title("WTShiftBench", fontsize=6.8, pad=3)
    for v in [25, 75]:
        right.axvline(v, color="#BDBDBD", lw=0.7, ls="--")
        right.axhline(v, color="#BDBDBD", lw=0.7, ls="--")
    right.plot([0, 100], [0, 100], color="#CFCFCF", lw=0.8, ls=":", zorder=0)
    dd = source.loc[source["evaluation_object"].eq("endpoint-anchored")]
    role_colors = {"anchor": CATEGORY_COLORS["Anchor"], "low-information": CATEGORY_COLORS["Low-information"], "middle": CATEGORY_COLORS["Middle"]}
    right.scatter(dd["x"] * 100, dd["y"] * 100, s=38, c=dd["role"].map(role_colors), edgecolor="white", linewidth=0.5)
    right.set_xlim(0, 100)
    right.set_ylim(0, 100)
    right.set_xlabel("Dependency percentile", fontsize=5.5)
    right.set_ylabel("Shift percentile", fontsize=5.5)
    right.tick_params(labelsize=5)
    clean_axes(right)
    ax.text(0.49, 0.53, "vs", transform=ax.transAxes, ha="center", va="center", fontsize=8, weight="bold", color="#555555")


def render_endpoint_plane(ax: plt.Axes, source: pd.DataFrame) -> None:
    add_panel_heading(ax, "b", "Fixed endpoint-recovery percentile plane", label_x=-0.10)
    ax.set_xlim(-2, 102)
    ax.set_ylim(-2, 102)
    ax.axvline(25, color="#BDBDBD", linewidth=0.8, linestyle="--")
    ax.axvline(75, color="#BDBDBD", linewidth=0.8, linestyle="--")
    ax.axhline(25, color="#BDBDBD", linewidth=0.8, linestyle="--")
    ax.axhline(75, color="#BDBDBD", linewidth=0.8, linestyle="--")
    ax.plot([0, 100], [0, 100], color="#CFCFCF", lw=0.8, ls=":", zorder=0)
    for category, d in source.groupby("category", sort=False):
        ax.scatter(
            d["depmap_quantile"] * 100,
            d["shift_quantile"] * 100,
            s=22,
            color=CATEGORY_COLORS.get(category, CATEGORY_COLORS["Middle"]),
            edgecolor="white",
            linewidth=0.4,
            alpha=0.82,
        )
    ax.text(87, 90, "Anchor", ha="center", va="center", fontsize=6.0, weight="bold", color="#333333")
    ax.text(15, 12, "Low-\ninformation", ha="center", va="center", fontsize=5.8, weight="bold", color="#333333")
    ax.text(50, 50, "Middle", ha="center", va="center", fontsize=5.8, color="#333333")
    ax.set_xlabel("Dependency percentile (-DepMap)")
    ax.set_ylabel("Observed shift percentile")
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_yticks([0, 25, 50, 75, 100])
    clean_axes(ax)


def render_layer_matrix(ax: plt.Axes, source: pd.DataFrame) -> None:
    add_panel_heading(ax, "c", "Dataset evidence-layer matrix", label_x=-0.07)
    layers = list(LAYER_COLORS)
    contexts = source["evidence_layer"].tolist()
    mat = np.zeros((len(contexts), len(layers)))
    for i, layer in enumerate(contexts):
        if layer in layers:
            mat[i, layers.index(layer)] = 1
    ax.imshow(mat * 0.85, aspect="auto", cmap=LIGHT_GREEN_CMAP, vmin=0, vmax=1)
    ax.set_yticks(range(len(contexts)))
    ax.set_yticklabels([c.replace(" / ", "\n") for c in contexts], fontsize=5.3)
    ax.set_xticks(range(len(layers)))
    ax.set_xticklabels([l.replace(" layer", "").replace(" / ", "\n") for l in layers], rotation=35, ha="right", fontsize=5.2)
    ax.tick_params(length=0)
    for i, (_, row) in enumerate(source.iterrows()):
        ax.text(layers.index(row["evidence_layer"]), i, str(int(row["n_contexts"])), ha="center", va="center", fontsize=5.6, color="#222222", weight="bold")
    for spine in ax.spines.values():
        spine.set_visible(False)


def render_coverage_heatmap(ax: plt.Axes, source: pd.DataFrame) -> None:
    add_panel_heading(ax, "d", "Analysis coverage map", label_x=-0.07)
    pivot = source.pivot_table(index="context_group", columns="analysis_module", values="status", aggfunc="max").fillna(0)
    pivot = pivot.loc[["HCC38/HCC1143", "K562 temporal", "Replogle K562", "HepG2/Jurkat", "MOLM13/Adamson"]]
    pivot = pivot[["Observed bridge", "DepMap matched", "Category grid", "Model audit", "Response GSEA"]]
    ax.imshow(pivot.to_numpy(), aspect="auto", cmap=LIGHT_GREEN_CMAP, vmin=0, vmax=1)
    ax.set_yticks(range(len(pivot)))
    ax.set_yticklabels(pivot.index, fontsize=5.7)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=35, ha="right", fontsize=5.4)
    ax.tick_params(length=0)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.iloc[i, j]
            label = "full" if val >= 0.99 else ("partial" if val > 0 else "-")
            ax.text(j, i, label, ha="center", va="center", fontsize=5.0, color="#222222")
    for spine in ax.spines.values():
        spine.set_visible(False)


def _save_panel(root: Path, panel_id: str, title: str, fig: plt.Figure, source: pd.DataFrame) -> dict[str, Path]:
    stem = f"{FIGURE_ID}_panel{panel_id}"
    public_stem = f"{PUBLIC_FIGURE_ID}_panel_{panel_id}"
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
    write_panel_manifest(
        manifest_path=manifest,
        repo_root=root,
        panel_id=f"{FIGURE_ID}{panel_id}",
        panel_title=title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=src,
        output_paths=[png, pdf],
        claim_boundary=CLAIM_BOUNDARY,
    )
    write_panel_manifest(
        manifest_path=manuscript_panel_dir(root) / f"{public_stem}_manifest.json",
        repo_root=root,
        panel_id=f"{PUBLIC_FIGURE_ID}{panel_id}",
        panel_title=title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=public_src,
        output_paths=[public_png, public_pdf],
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": src, "png": png, "pdf": pdf, "manifest": manifest}


def build_panels(root: Path) -> dict[str, dict[str, Path]]:
    sources = {
        "a": evaluation_object_source(),
        "b": endpoint_plane_source(root),
        "c": dataset_layer_source(root),
        "d": analysis_coverage_source(),
    }
    outputs: dict[str, dict[str, Path]] = {}
    for panel_id, source in sources.items():
        if panel_id == "a":
            fig, ax = plt.subplots(figsize=(4.3, 3.0))
            render_evaluation_contrast(ax, source)
            title = "Evaluation-object contrast"
        elif panel_id == "b":
            fig, ax = plt.subplots(figsize=(3.5, 3.0))
            render_endpoint_plane(ax, source)
            title = "Endpoint-recovery percentile plane"
        elif panel_id == "c":
            fig, ax = plt.subplots(figsize=(5.1, 3.0))
            render_layer_matrix(ax, source)
            title = "Dataset evidence-layer matrix"
        else:
            fig, ax = plt.subplots(figsize=(4.8, 3.0))
            render_coverage_heatmap(ax, source)
            title = "Analysis coverage map"
        outputs[panel_id] = _save_panel(root, panel_id, title, fig, source)
    return outputs


def build_combined(root: Path, panel_outputs: dict[str, dict[str, Path]]) -> None:
    sources = {
        "a": evaluation_object_source(),
        "b": endpoint_plane_source(root),
        "c": dataset_layer_source(root),
        "d": analysis_coverage_source(),
    }
    combined = pd.concat([df.assign(panel=p) for p, df in sources.items()], ignore_index=True, sort=False)
    src = write_tsv(combined, output_dir(root) / f"{FIGURE_ID}_source_data.tsv")
    public_src = write_tsv(combined, manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}_source_data.tsv")

    fig = plt.figure(figsize=(10.4, 6.6))
    gs = fig.add_gridspec(2, 2, left=0.06, right=0.98, top=0.94, bottom=0.10, wspace=0.30, hspace=0.42, width_ratios=[1, 1.05])
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])
    render_evaluation_contrast(ax_a, sources["a"])
    render_endpoint_plane(ax_b, sources["b"])
    render_layer_matrix(ax_c, sources["c"])
    render_coverage_heatmap(ax_d, sources["d"])
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
    write_figure_manifest(
        manifest_path=output_dir(root) / f"{FIGURE_ID}_panel_manifest.json",
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in ["a", "b", "c", "d"]],
        combined_source_data_path=src,
        output_paths=[png, pdf],
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )
    write_figure_manifest(
        manifest_path=manuscript_figure_dir(root) / f"{PUBLIC_FIGURE_ID}_panel_manifest.json",
        repo_root=root,
        figure_id=PUBLIC_FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[manuscript_panel_dir(root) / f"{PUBLIC_FIGURE_ID}_panel_{p}_manifest.json" for p in ["a", "b", "c", "d"]],
        combined_source_data_path=public_src,
        output_paths=[public_png, public_pdf],
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )


def copy_to_figure_build(root: Path) -> None:
    src = output_dir(root)
    dst = ensure_dir(root / "figure_build/output/Figure_1")
    panel_dst = ensure_dir(dst / "panels")
    for ext in [".png", ".pdf", "_source_data.tsv"]:
        s = src / f"{FIGURE_ID}{ext}"
        if s.exists():
            shutil.copy2(s, dst / f"{PUBLIC_FIGURE_ID}{ext}")
    for panel in ["a", "b", "c", "d"]:
        for ext in [".png", ".pdf", "_source_data.tsv"]:
            s = src / "panels" / f"{FIGURE_ID}_panel{panel}{ext}"
            if s.exists():
                shutil.copy2(s, panel_dst / f"{PUBLIC_FIGURE_ID}_panel_{panel}{ext}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build Figure 1 endpoint-recovery resource contract map.")
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
