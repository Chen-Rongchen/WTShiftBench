from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes


FIGURE_ID = "extended_data_figure11"
FIGURE_TITLE = "Reproducibility and claim governance for the manuscript package"
SCRIPT_PATH = Path("scripts/manuscript/build_extended_data_figure11.py")
CLAIM_BOUNDARY = "This Extended Data figure indexes reproducibility artifacts and claim-governance boundaries; it adds no new biological claim."
PANEL_IDS = tuple("abc")

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
    return root / "reports/manuscript_extended_data_v1/edfig11_reproducibility"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / p for p in [MAIN_FIGURE_CONFIG, SUPP_TABLE_CONFIG, ED_CONFIG, SUPP_TABLE_SUMMARY, SUPP_TABLE_INDEX, SUPP_TABLE_MANIFEST, FINAL_CLAIM_MATRIX, *FIGURE_MANIFESTS]]


def cleanup_generated(root: Path) -> None:
    out = output_dir(root)
    for path in panel_dir(root).glob("edfig11_panel*"):
        path.unlink()
    for suffix in (".png", ".pdf", "_source_data.tsv", "_panel_manifest.json"):
        path = out / f"edfig11{suffix}"
        if path.exists():
            path.unlink()


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
    stem = f"edfig11_panel{panel_id}"
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
        panel_id=f"ED11{panel_id}",
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
    suffix_summary = supp_index.groupby("suffix", as_index=False).agg(n_files=("path", "count"), total_bytes=("bytes", "sum"))
    package_summary = pd.concat(
        [
            supp_summary.assign(summary_kind="table_group"),
            suffix_summary.assign(table_id=lambda x: "suffix_" + x["suffix"].astype(str), summary_kind="hash_suffix"),
        ],
        ignore_index=True,
        sort=False,
    )
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
                "scope": "extended_data_figure11",
                "short_command": "build_extended_data_figure11.py",
                "command": "pixi run --environment core python scripts/manuscript/build_extended_data_figure11.py",
                "reruns_gears_training": "no",
            },
        ]
    )
    return {
        "a": manifest,
        "b": package_summary,
        "c": pd.concat(
            [
                entrypoints.assign(summary_kind="entrypoint"),
                pd.DataFrame(
                    [
                        {"boundary": "GEARS training", "status": "exempt from figure-stage rerun", "basis": "runtime cost; frozen predictions and scores hashed", "summary_kind": "boundary"},
                        {"boundary": "figure source data", "status": "rerun", "basis": "all main figures and ED rebuild source data from frozen reports", "summary_kind": "boundary"},
                        {"boundary": "hash manifests", "status": "recorded", "basis": "input, source data and output SHA256 tracked", "summary_kind": "boundary"},
                        {"boundary": "claim wording", "status": "governed", "basis": "final claim matrix controls allowed and disallowed wording", "summary_kind": "boundary"},
                    ]
                ),
            ],
            ignore_index=True,
            sort=False,
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
    plot = df.loc[df["summary_kind"].eq("table_group")].sort_values("n_files")
    y = range(len(plot))
    ax.barh(list(y), plot["n_files"], color="#8A8A8A", height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot["table_id"].str.replace("supp_table_", "T"))
    ax.set_xlabel("Files")
    suffix = df.loc[df["summary_kind"].eq("hash_suffix"), ["suffix", "n_files"]].dropna()
    suffix_text = "; ".join(f"{r.suffix}: {int(r.n_files)}" for r in suffix.itertuples())
    ax.text(0.02, 0.95, suffix_text, transform=ax.transAxes, va="top", fontsize=7)
    ax.set_title("Submission package overview", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "b", x=-0.23)


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    # Reproducibility details stay here; claim-tier summaries remain in the main text/figures.
    ax.set_axis_off()
    ax.set_title("Rebuild entrypoints and rerun boundary", loc="left", pad=4)
    entries = df.loc[df["summary_kind"].eq("entrypoint")]
    y = 0.88
    for row in entries.itertuples():
        ax.text(0.04, y, row.scope, fontweight="bold", fontsize=7, transform=ax.transAxes)
        ax.text(0.38, y, row.short_command, fontsize=6.6, transform=ax.transAxes)
        y -= 0.12
    boundaries = df.loc[df["summary_kind"].eq("boundary")]
    y = 0.46
    for row in boundaries.itertuples():
        color = COLORS["boundary"] if "GEARS" in row.boundary else COLORS["primary_qualified"]
        ax.text(0.04, y, row.boundary, color=color, fontweight="bold", fontsize=6.8, transform=ax.transAxes)
        ax.text(0.39, y, row.status, fontsize=6.8, transform=ax.transAxes)
        y -= 0.10
    add_panel_label(ax, "c", x=-0.04)


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {
        "a": render_panel_a,
        "b": render_panel_b,
        "c": render_panel_c,
    }[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Main figure manifest overview",
        "b": "Submission package overview",
        "c": "Rerun boundary",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> None:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / "edfig11_source_data.tsv")
    ncols = 2
    nrows = math.ceil(len(PANEL_IDS) / ncols)
    fig = plt.figure(figsize=(11.0, max(3.0 * nrows, 4.2)))
    gs = fig.add_gridspec(nrows, ncols, hspace=0.76, wspace=0.52)
    axes = [fig.add_subplot(gs[i, j]) for i in range(nrows) for j in range(ncols)]
    for ax, panel_id in zip(axes, PANEL_IDS):
        render_panel_by_id(panel_id)(ax, sources[panel_id])
    png_path = out / "edfig11.png"
    pdf_path = out / "edfig11.pdf"
    output_paths = save_figure(fig, png_path, pdf_path)
    write_figure_manifest(
        manifest_path=out / "edfig11_panel_manifest.json",
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in PANEL_IDS],
        combined_source_data_path=combined_source_path,
        output_paths=output_paths,
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build Extended Data Fig. 11 reproducibility and claim governance panels.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    apply_manuscript_style()
    cleanup_generated(root)
    sources = build_sources(root)
    panel_outputs: dict[str, dict[str, Path]] = {}
    for panel_id in PANEL_IDS:
        panel_outputs[panel_id] = write_panel(
            root=root,
            panel_id=panel_id,
            panel_title=panel_title(panel_id),
            source_df=sources[panel_id],
            render=render_panel_by_id(panel_id),
            width=3.55 if panel_id in {"b", "c", "e", "f"} else 3.2,
            height=2.65 if panel_id in {"b", "c", "e", "f"} else 2.35,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
