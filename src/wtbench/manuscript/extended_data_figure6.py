from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes


FIGURE_ID = "extended_data_figure6"
FIGURE_TITLE = "Full axis annotation and bootstrap support"
SCRIPT_PATH = Path("scripts/manuscript/build_extended_data_figure6.py")
CLAIM_BOUNDARY = "Axis interpretation remains partial; transcription / chromatin is primary but qualified."

AXIS_EXPLANATORY = Path("reports/stage2_truth_bridge_decomposition/axis_level_shared_explanatory_summary.tsv")
AXIS_BOOTSTRAP = Path("reports/stage2_truth_bridge_decomposition/axis_bootstrap_stability.tsv")
AXIS_SUMMARY = Path("reports/stage2_axis_analysis/axis_summary.tsv")
AXIS_VALIDATION = Path("reports/stage2_axis_analysis/axis_validation_summary.tsv")
AXIS_ENRICHMENT = Path("reports/stage2_axis_analysis/axis_enrichment.tsv")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_extended_data_v1/edfig6_axis_annotation"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [root / p for p in [AXIS_EXPLANATORY, AXIS_BOOTSTRAP, AXIS_SUMMARY, AXIS_VALIDATION, AXIS_ENRICHMENT, FINAL_CLAIM_MATRIX]]


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
    stem = f"edfig6_panel{panel_id}"
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
        panel_id=f"ED6{panel_id}",
        panel_title=panel_title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def parse_annotation_support(value: str) -> tuple[int, int]:
    hits = re.search(r"enrichment_hits=(\d+)", value)
    dbs = re.search(r"databases=(\d+)", value)
    return int(hits.group(1)), int(dbs.group(1))


def call_color(call: str) -> str:
    if call == "transcriptomic_heavy_axis":
        return COLORS["primary_qualified"]
    if "dependency" in call:
        return "#777777"
    if "shared_signal" in call:
        return COLORS["supporting"]
    return "#C8C8C8"


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    colors = [call_color(v) for v in df["explanatory_call"]]
    ax.scatter(df["depmap_r2_mean"], df["shift_r2_mean"], c=colors, s=34, edgecolor="white", linewidth=0.4)
    focus = df.loc[df["axis_id"].eq("transcription / chromatin")].iloc[0]
    ax.text(focus["depmap_r2_mean"] + 0.006, focus["shift_r2_mean"], "tx/chromatin", fontsize=7)
    ax.set_xlabel("Dependency R2")
    ax.set_ylabel("Shift R2")
    ax.set_title("Full axis explanatory balance", loc="left")
    clean_axes(ax)
    ax.grid(color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "a")


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    low = df.nsmallest(7, "bootstrap_dominant_call_fraction")
    high = df.nlargest(5, "bootstrap_dominant_call_fraction")
    focus = df.loc[df["axis_id"].eq("transcription / chromatin")]
    plot = pd.concat([low, high, focus], ignore_index=True).drop_duplicates("axis_id")
    plot = plot.sort_values("bootstrap_dominant_call_fraction")
    y = range(len(plot))
    ax.barh(list(y), plot["bootstrap_dominant_call_fraction"], color=[call_color(v) for v in plot["bootstrap_dominant_call"]], height=0.50)
    ax.axvline(0.8, color=COLORS["boundary"], linewidth=0.8, linestyle="--")
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot["axis_id"])
    ax.set_xlabel("Dominant call fraction")
    ax.set_title("Full bootstrap axis-call stability", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "b", x=-0.30)


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    counts = df.groupby("axis_label", as_index=False).size().rename(columns={"size": "n"})
    counts = counts.sort_values("n")
    y = range(len(counts))
    ax.barh(list(y), counts["n"], color="#8A8A8A", height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(counts["axis_label"])
    ax.set_xlabel("Axes")
    ax.set_title("Axis families in validation summary", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "c", x=-0.28)


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.groupby("axis_id", as_index=False).agg(enrichment_hits=("term", "count"), databases=("database", "nunique"))
    plot = plot.sort_values(["enrichment_hits", "databases"], ascending=True).tail(12)
    y = range(len(plot))
    ax.barh(list(y), plot["enrichment_hits"], color="#777777", height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot["axis_id"])
    ax.set_xlabel("Enrichment hits")
    ax.set_title("Top axes by enrichment hits", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "d", x=-0.30)


def render_panel_e(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.groupby("database", as_index=False).size().rename(columns={"size": "n_terms"}).sort_values("n_terms")
    ax.bar(plot["database"], plot["n_terms"], color=COLORS["supporting"], width=0.58)
    ax.set_ylabel("Terms")
    ax.set_title("Enrichment database coverage", loc="left")
    ax.tick_params(axis="x", rotation=25)
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "e")


def render_panel_f(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.groupby(["call_tier", "explanatory_call"], as_index=False).size().rename(columns={"size": "n"})
    plot["label"] = plot["call_tier"] + "\n" + plot["explanatory_call"].str.replace("_axis", "").str.replace("_", " ")
    plot = plot.sort_values("n", ascending=True)
    y = range(len(plot))
    ax.barh(list(y), plot["n"], color=[call_color(v) for v in plot["explanatory_call"]], height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot["label"])
    ax.set_xlabel("Axes")
    ax.set_title("Formal and preliminary axis calls", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "f", x=-0.34)


def render_panel_g(ax: plt.Axes, df: pd.DataFrame) -> None:
    top = df.sort_values("FDR").head(10).copy()
    top["short_term"] = top["term"].str.replace(r"\s+R-HSA-.*$", "", regex=True).str.slice(0, 22)
    y = range(len(top))
    ax.barh(list(y), -top["FDR"].map(lambda v: pd.NA if v <= 0 else __import__("math").log10(v)), color=COLORS["primary_qualified"], height=0.56)
    ax.set_yticks(list(y))
    ax.set_yticklabels(top["axis_id"].str.slice(0, 18) + " | " + top["short_term"])
    ax.set_xlabel("-log10 FDR")
    ax.set_title("Top recurrent annotation terms", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "g", x=-0.38)


def render_panel_h(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Axis claim boundary", loc="left", pad=4)
    rows = df.loc[df["object"].isin(["transcription_chromatin_axis", "other_axes"])]
    y = 0.76
    for row in rows.itertuples():
        label = row.object.replace("transcription_chromatin_axis", "tx/chromatin axis")
        ax.text(0.04, y, label, fontsize=8, fontweight="bold", transform=ax.transAxes)
        ax.text(0.43, y, row.evidence_tier, fontsize=7, color=COLORS["primary_qualified"] if "primary" in row.evidence_tier else COLORS["supporting"], transform=ax.transAxes)
        y -= 0.22
    ax.text(0.04, 0.12, "Not allowed: fully established or fully deconfounded shared explanatory architecture.", fontsize=7, color=COLORS["boundary"], transform=ax.transAxes)
    add_panel_label(ax, "h", x=-0.04)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    explanatory = pd.read_csv(root / AXIS_EXPLANATORY, sep="\t")
    bootstrap = pd.read_csv(root / AXIS_BOOTSTRAP, sep="\t")
    summary = pd.read_csv(root / AXIS_SUMMARY, sep="\t")
    validation = pd.read_csv(root / AXIS_VALIDATION, sep="\t")
    enrichment = pd.read_csv(root / AXIS_ENRICHMENT, sep="\t")
    claim = pd.read_csv(root / FINAL_CLAIM_MATRIX, sep="\t")
    focus = explanatory.loc[explanatory["axis_id"].eq("transcription / chromatin")].iloc[0]
    focus_boot = bootstrap.loc[bootstrap["axis_id"].eq("transcription / chromatin")].iloc[0]
    focus_claim = claim.loc[claim["object"].eq("transcription_chromatin_axis")].iloc[0]
    if focus["explanatory_call"] != "transcriptomic_heavy_axis" or focus["call_tier"] != "formal":
        raise RuntimeError("ED Fig. 6 sanity check failed: transcription / chromatin axis call changed.")
    if not (0.085 <= float(focus["shift_r2_mean"]) <= 0.100) or not (0 <= float(focus["depmap_r2_mean"]) <= 0.002):
        raise RuntimeError("ED Fig. 6 sanity check failed: transcription / chromatin R2 values changed materially.")
    if float(focus_boot["bootstrap_dominant_call_fraction"]) < 0.90:
        raise RuntimeError("ED Fig. 6 sanity check failed: transcription / chromatin bootstrap stability dropped.")
    if focus_claim["evidence_tier"] != "primary_axis_but_qualified":
        raise RuntimeError("ED Fig. 6 sanity check failed: transcription / chromatin tier changed.")
    parsed = validation["annotation_support"].map(parse_annotation_support)
    validation = validation.assign(enrichment_hits=[v[0] for v in parsed], databases=[v[1] for v in parsed])
    return {
        "a": explanatory,
        "b": bootstrap,
        "c": summary,
        "d": enrichment,
        "e": enrichment,
        "f": explanatory,
        "g": enrichment,
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
        "a": "Full axis explanatory balance",
        "b": "Full bootstrap stability",
        "c": "Axis families",
        "d": "Enrichment hits",
        "e": "Database coverage",
        "f": "Axis call composition",
        "g": "Top annotation terms",
        "h": "Axis claim boundary",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> None:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / "edfig6_source_data.tsv")
    fig = plt.figure(figsize=(11.0, 10.0))
    gs = fig.add_gridspec(4, 2, hspace=0.82, wspace=0.54)
    axes = [fig.add_subplot(gs[i, j]) for i in range(4) for j in range(2)]
    for ax, panel_id in zip(axes, list("abcdefgh")):
        render_panel_by_id(panel_id)(ax, sources[panel_id])
    png_path = out / "edfig6.png"
    pdf_path = out / "edfig6.pdf"
    output_paths = save_figure(fig, png_path, pdf_path)
    write_figure_manifest(
        manifest_path=out / "edfig6_panel_manifest.json",
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
    parser = argparse.ArgumentParser(description="Build Extended Data Fig. 6 axis annotation and bootstrap panels.")
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
            width=3.65 if panel_id in {"b", "d", "f", "g"} else 3.2,
            height=3.0 if panel_id in {"b", "d", "f", "g"} else 2.35,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
