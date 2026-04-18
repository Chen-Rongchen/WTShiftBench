from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes


FIGURE_ID = "extended_data_figure10"
FIGURE_TITLE = "Reproducibility and claim governance for the manuscript package"
SCRIPT_PATH = Path("scripts/manuscript/build_extended_data_figure10.py")
CLAIM_BOUNDARY = "This Extended Data figure indexes reproducibility artifacts and claim-governance boundaries; it adds no new biological claim."

MAIN_FIGURE_CONFIG = Path("configs/manuscript/main_figures_v2.json")
SUPP_TABLE_CONFIG = Path("configs/manuscript/supplementary_tables_v1.json")
ED_CONFIG = Path("configs/manuscript/extended_data_figures_v1.json")
SUPP_TABLE_SUMMARY = Path("reports/manuscript_supplementary_tables_v1/supplementary_table_summary.tsv")
SUPP_TABLE_INDEX = Path("reports/manuscript_supplementary_tables_v1/supplementary_table_file_index.tsv")
SUPP_TABLE_MANIFEST = Path("reports/manuscript_supplementary_tables_v1/supplementary_table_manifest.json")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")
FIGURE_MANIFESTS = [
    Path("reports/manuscript_figures_v2/fig1_truth_object/figure1_panel_manifest.json"),
    Path("reports/manuscript_figures_v2/fig2_anchor_tiering/figure2_panel_manifest.json"),
    Path("reports/manuscript_figures_v2/fig3_model_tradeoff/figure3_panel_manifest.json"),
    Path("reports/manuscript_figures_v2/fig4_sweep_controls/figure4_panel_manifest.json"),
    Path("reports/manuscript_figures_v2/fig5_axis_interpretation/figure5_panel_manifest.json"),
    Path("reports/manuscript_figures_v2/fig6_boundary/figure6_panel_manifest.json"),
]


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_extended_data_v1/edfig10_reproducibility"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / p for p in [MAIN_FIGURE_CONFIG, SUPP_TABLE_CONFIG, ED_CONFIG, SUPP_TABLE_SUMMARY, SUPP_TABLE_INDEX, SUPP_TABLE_MANIFEST, FINAL_CLAIM_MATRIX, *FIGURE_MANIFESTS]]


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
    stem = f"edfig10_panel{panel_id}"
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
        panel_id=f"ED10{panel_id}",
        panel_title=panel_title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def manifest_rows(root: Path) -> pd.DataFrame:
    rows = []
    for rel in FIGURE_MANIFESTS:
        with (root / rel).open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        rows.append(
            {
                "figure_id": data["figure_id"],
                "n_panel_manifests": len(data["panel_manifests"]),
                "n_inputs": len(data["inputs"]),
                "n_outputs": len(data["outputs"]),
                "combined_source_sha256": data["combined_source_data"]["sha256"],
                "png_sha256": next(v["sha256"] for v in data["outputs"] if v["path"].endswith(".png")),
                "pdf_sha256": next(v["sha256"] for v in data["outputs"] if v["path"].endswith(".pdf")),
                "git_commit": data["git"]["commit"],
            }
        )
    return pd.DataFrame(rows)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    manifest = manifest_rows(root)
    supp_summary = pd.read_csv(root / SUPP_TABLE_SUMMARY, sep="\t")
    supp_index = pd.read_csv(root / SUPP_TABLE_INDEX, sep="\t")
    final_claim = pd.read_csv(root / FINAL_CLAIM_MATRIX, sep="\t")
    suffix_summary = supp_index.groupby("suffix", as_index=False).agg(n_files=("path", "count"), total_bytes=("bytes", "sum"))
    tier_summary = final_claim.groupby("evidence_tier", as_index=False).size().rename(columns={"size": "n_objects"}).sort_values("n_objects", ascending=True)
    key_claims = final_claim.loc[
        final_claim["object"].isin(
            [
                "GEARS_tradeoff_diagnosis",
                "PFDN5",
                "PMF1",
                "PRPF6",
                "ZNF131",
                "transcription_chromatin_axis",
                "Dixit_K562_temporal_panel",
                "Replogle_RNAi_expansion_candidate",
                "discovery_phenotype_shifter",
            ]
        ),
        ["object", "evidence_tier", "allowed_wording", "disallowed_wording"],
    ]
    entrypoints = pd.DataFrame(
        [
            {
                "scope": "main_figures",
                "short_command": "build_all_main_figures.py",
                "command": "pixi run --environment core python scripts/manuscript/build_all_main_figures.py",
                "reruns_gears_training": "no",
            },
            {
                "scope": "supplementary_tables",
                "short_command": "build_supplementary_table_index.py",
                "command": "pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py",
                "reruns_gears_training": "no",
            },
            {
                "scope": "extended_data_figure10",
                "short_command": "build_extended_data_figure10.py",
                "command": "pixi run --environment core python scripts/manuscript/build_extended_data_figure10.py",
                "reruns_gears_training": "no",
            },
        ]
    )
    disallowed = final_claim[["object", "evidence_tier", "disallowed_wording"]].copy()
    disallowed["n_disallowed_phrases"] = disallowed["disallowed_wording"].fillna("").map(lambda v: len([x for x in v.split(";") if x.strip()]))
    return {
        "a": manifest,
        "b": supp_summary,
        "c": suffix_summary,
        "d": tier_summary,
        "e": key_claims,
        "f": entrypoints,
        "g": disallowed,
        "h": pd.DataFrame(
            [
                {"boundary": "GEARS training", "status": "exempt from figure-stage rerun", "basis": "runtime cost; frozen predictions and scores hashed"},
                {"boundary": "figure source data", "status": "rerun", "basis": "all main figures and ED10 rebuild source data from frozen reports"},
                {"boundary": "hash manifests", "status": "recorded", "basis": "input, source data and output SHA256 tracked"},
                {"boundary": "claim wording", "status": "governed", "basis": "final claim matrix controls allowed and disallowed wording"},
            ]
        ),
    }


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.copy()
    x = range(len(plot))
    ax.bar(x, plot["n_panel_manifests"], color=COLORS["primary_qualified"], width=0.56)
    ax.set_xticks(list(x))
    ax.set_xticklabels(plot["figure_id"].str.replace("figure", "Fig. "), rotation=25, ha="right")
    ax.set_ylim(0, 9)
    ax.set_ylabel("Panel manifests")
    ax.set_title("Main figures have panel-level manifests", loc="left")
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "a")


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.sort_values("n_files")
    y = range(len(plot))
    ax.barh(list(y), plot["n_files"], color="#8A8A8A", height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot["table_id"].str.replace("supp_table_", "T"))
    ax.set_xlabel("Files")
    ax.set_title("Supplementary table groups are indexed", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "b", x=-0.23)


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.bar(df["suffix"], df["n_files"], color=[COLORS["baseline"], COLORS["foundation"], COLORS["supporting"]][: len(df)])
    ax.set_ylabel("Files")
    ax.set_title("Hash coverage by file type", loc="left")
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "c")


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    y = range(len(df))
    colors = [COLORS["primary_qualified"] if "primary" in v else (COLORS["supporting"] if "support" in v or "A0" in v else "#BDBDBD") for v in df["evidence_tier"]]
    ax.barh(list(y), df["n_objects"], color=colors, height=0.56)
    ax.set_yticks(list(y))
    ax.set_yticklabels(df["evidence_tier"])
    ax.set_xlabel("Objects")
    ax.set_title("Final claim matrix governs evidence tiers", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "d", x=-0.35)


def render_panel_e(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Key allowed wording is tiered", loc="left", pad=4)
    order = [
        "GEARS_tradeoff_diagnosis",
        "PFDN5",
        "PMF1",
        "PRPF6",
        "ZNF131",
        "transcription_chromatin_axis",
        "Dixit_K562_temporal_panel",
    ]
    plot = df.set_index("object").loc[order].reset_index()
    y = 0.89
    for row in plot.itertuples():
        label = row.object.replace("transcription_chromatin_axis", "tx/chromatin axis").replace("GEARS_tradeoff_diagnosis", "GEARS tradeoff")
        label = label.replace("Dixit_K562_temporal_panel", "K562 temporal")
        tier = row.evidence_tier.replace("_", " ")
        ax.text(0.03, y, label, fontsize=6.8, fontweight="bold", transform=ax.transAxes)
        ax.text(0.54, y, tier, fontsize=6.5, color=COLORS["primary_qualified"] if "primary" in row.evidence_tier else COLORS["supporting"], transform=ax.transAxes)
        y -= 0.118
    add_panel_label(ax, "e", x=-0.04)


def render_panel_f(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Configured rebuild entrypoints", loc="left", pad=4)
    y = 0.78
    for row in df.itertuples():
        ax.text(0.04, y, row.scope, fontweight="bold", fontsize=8, transform=ax.transAxes)
        ax.text(0.04, y - 0.10, row.short_command, fontsize=7, transform=ax.transAxes)
        ax.text(0.62, y - 0.10, f"GEARS train: {row.reruns_gears_training}", fontsize=7, color=COLORS["boundary"], transform=ax.transAxes)
        y -= 0.27
    add_panel_label(ax, "f", x=-0.04)


def render_panel_g(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.sort_values("n_disallowed_phrases", ascending=True).tail(10)
    y = range(len(plot))
    ax.barh(list(y), plot["n_disallowed_phrases"], color=COLORS["boundary"], height=0.56)
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot["object"])
    ax.set_xlabel("Disallowed phrases")
    ax.set_title("Boundary wording is explicitly enumerated", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "g", x=-0.32)


def render_panel_h(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Rerun boundary", loc="left", pad=4)
    y = 0.82
    for row in df.itertuples():
        color = COLORS["boundary"] if "GEARS" in row.boundary else COLORS["primary_qualified"]
        ax.text(0.04, y, row.boundary, color=color, fontweight="bold", fontsize=8, transform=ax.transAxes)
        ax.text(0.39, y, row.status, fontsize=8, transform=ax.transAxes)
        ax.text(0.04, y - 0.09, row.basis, fontsize=6.5, color="#555555", transform=ax.transAxes)
        y -= 0.21
    add_panel_label(ax, "h", x=-0.04)


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
        "a": "Main figure manifest overview",
        "b": "Supplementary table groups",
        "c": "Hash coverage",
        "d": "Claim tier overview",
        "e": "Allowed wording",
        "f": "Rebuild entrypoints",
        "g": "Disallowed wording",
        "h": "Rerun boundary",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> None:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / "edfig10_source_data.tsv")
    fig = plt.figure(figsize=(11.0, 10.0))
    gs = fig.add_gridspec(4, 2, hspace=0.76, wspace=0.52)
    axes = [fig.add_subplot(gs[i, j]) for i in range(4) for j in range(2)]
    for ax, panel_id in zip(axes, list("abcdefgh")):
        render_panel_by_id(panel_id)(ax, sources[panel_id])
    png_path = out / "edfig10.png"
    pdf_path = out / "edfig10.pdf"
    output_paths = save_figure(fig, png_path, pdf_path)
    write_figure_manifest(
        manifest_path=out / "edfig10_panel_manifest.json",
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
    parser = argparse.ArgumentParser(description="Build Extended Data Fig. 10 reproducibility and claim governance panels.")
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
            width=3.55 if panel_id in {"b", "d", "g"} else 3.2,
            height=2.65 if panel_id in {"b", "d", "g"} else 2.35,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
