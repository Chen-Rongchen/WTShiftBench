from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes


FIGURE_ID = "figure5"
FIGURE_TITLE = "Axis-level interpretation is partial and claim-bounded"
SCRIPT_PATH = Path("scripts/manuscript/build_figure5_axis_interpretation.py")
CLAIM_BOUNDARY = "Only transcription / chromatin is a formal positive axis, and it remains primary but qualified."

AXIS_EXPLANATORY = Path("reports/stage2_truth_bridge_decomposition/axis_level_shared_explanatory_summary.tsv")
AXIS_BOOTSTRAP = Path("reports/stage2_truth_bridge_decomposition/axis_bootstrap_stability.tsv")
AXIS_VALIDATION = Path("reports/stage2_axis_analysis/axis_validation_summary.tsv")
AXIS_SUMMARY = Path("reports/stage2_axis_analysis/axis_summary.tsv")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig5_axis_interpretation"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [
        root / AXIS_EXPLANATORY,
        root / AXIS_BOOTSTRAP,
        root / AXIS_VALIDATION,
        root / AXIS_SUMMARY,
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


def parse_annotation_support(value: str) -> tuple[int, int]:
    hits = re.search(r"enrichment_hits=(\d+)", value)
    dbs = re.search(r"databases=(\d+)", value)
    return int(hits.group(1)), int(dbs.group(1))


def call_color(call: str) -> str:
    if call == "transcriptomic_heavy_axis":
        return COLORS["primary_qualified"]
    if "dependency_heavy" in call:
        return "#8A8A8A"
    if "shared_signal" in call:
        return COLORS["supporting"]
    return "#C8C8C8"


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    colors = [call_color(v) for v in df["explanatory_call"]]
    sizes = 28 + 12 * df["n_targets"].clip(upper=8)
    ax.scatter(df["depmap_r2_mean"], df["shift_r2_mean"], s=sizes, c=colors, edgecolor="white", linewidth=0.5, alpha=0.95)
    focus = df.loc[df["axis_id"].eq("transcription / chromatin")].iloc[0]
    ax.annotate(
        "transcription /\nchromatin",
        xy=(focus.depmap_r2_mean, focus.shift_r2_mean),
        xytext=(0.033, 0.118),
        arrowprops={"arrowstyle": "-", "linewidth": 0.6, "color": COLORS["text"]},
        fontsize=7,
    )
    ax.set_xlabel("Dependency R2")
    ax.set_ylabel("Shift R2")
    ax.set_title("Axis explanatory balance", loc="left")
    ax.set_xlim(-0.003, max(df["depmap_r2_mean"]) * 1.18)
    ax.set_ylim(-0.005, max(df["shift_r2_mean"]) * 1.12)
    clean_axes(ax)
    ax.grid(color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "a")


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.groupby(["call_tier", "explanatory_call"]).size().reset_index(name="n")
    order = ["formal", "preliminary"]
    calls = [
        "transcriptomic_heavy_axis",
        "mixed_or_low_signal_axis",
        "preliminary_transcriptomic_heavy_axis",
        "preliminary_shared_signal_axis",
        "preliminary_dependency_heavy_axis",
        "preliminary_mixed_or_low_signal_axis",
    ]
    x = np.arange(len(order))
    bottom = np.zeros(len(order))
    for call in calls:
        vals = [int(plot.loc[(plot["call_tier"].eq(tier)) & (plot["explanatory_call"].eq(call)), "n"].sum()) for tier in order]
        if sum(vals) == 0:
            continue
        ax.bar(x, vals, bottom=bottom, color=call_color(call), width=0.55, label=call.replace("_axis", "").replace("_", " "))
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.set_ylabel("Axes")
    ax.set_title("Only one formal positive axis", loc="left")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1.02), borderaxespad=0)
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "b")


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    low = df.nsmallest(7, "bootstrap_dominant_call_fraction")
    high = df.nlargest(5, "bootstrap_dominant_call_fraction")
    focus = df.loc[df["axis_id"].eq("transcription / chromatin")]
    plot = pd.concat([low, high, focus], ignore_index=True).drop_duplicates("axis_id")
    plot = plot.sort_values("bootstrap_dominant_call_fraction", ascending=True)
    y = np.arange(len(plot))
    colors = [call_color(v) for v in plot["bootstrap_dominant_call"]]
    ax.barh(y, plot["bootstrap_dominant_call_fraction"], color=colors, height=0.56)
    ax.axvline(0.8, color=COLORS["boundary"], linewidth=0.8, linestyle="--")
    ax.set_yticks(y)
    ax.set_yticklabels(plot["axis_id"])
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Dominant bootstrap call fraction")
    ax.set_title("Bootstrap stability separates positive from unstable calls", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "c", x=-0.30)


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.sort_values(["databases", "enrichment_hits", "structure_support"], ascending=[False, False, False]).head(12)
    y = np.arange(len(plot))
    sizes = 18 + plot["enrichment_hits"].clip(upper=34) * 2.4
    ax.scatter(plot["structure_support"], y, s=sizes, c=plot["databases"], cmap="Greys", vmin=0, vmax=max(3, plot["databases"].max()), edgecolor=COLORS["text"], linewidth=0.4)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["axis_id"])
    ax.set_xlabel("Structure support class")
    ax.set_title("Annotation support remains partial", loc="left")
    ax.set_xlim(0.5, 4.5)
    ax.invert_yaxis()
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "d", x=-0.30)


def render_panel_e(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.melt(id_vars=["axis_id", "targets", "bootstrap_dominant_call_fraction"], value_vars=["shift_r2_mean", "depmap_r2_mean"], var_name="readout", value_name="r2")
    labels = {"shift_r2_mean": "shift", "depmap_r2_mean": "dependency"}
    x = np.arange(len(plot))
    colors = [COLORS["primary_qualified"] if r == "shift_r2_mean" else "#BDBDBD" for r in plot["readout"]]
    ax.bar(x, plot["r2"], color=colors, width=0.56)
    ax.set_xticks(x)
    ax.set_xticklabels([labels[v] for v in plot["readout"]])
    ax.set_ylabel("Mean R2")
    ax.set_title("Transcription/chromatin is transcriptomic-heavy", loc="left")
    ax.text(0.02, 0.86, "targets: ENY2, TADA3", transform=ax.transAxes, fontsize=7)
    ax.text(0.02, 0.74, f"bootstrap call fraction: {float(df['bootstrap_dominant_call_fraction'].iloc[0]):.3f}", transform=ax.transAxes, fontsize=7)
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "e")


def render_panel_f(ax: plt.Axes, df: pd.DataFrame) -> None:
    counts = df.groupby(["axis_family", "final_call"]).size().reset_index(name="n")
    plot = counts.sort_values("n", ascending=True)
    y = np.arange(len(plot))
    ax.barh(y, plot["n"], color="#8A8A8A", height=0.58)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["axis_family"])
    ax.set_xlabel("Axes")
    ax.set_title("All annotation-backed axes remain partial", loc="left")
    for yi, row in zip(y, plot.itertuples()):
        ax.text(row.n + 0.08, yi, row.final_call.replace("_", " "), va="center", fontsize=6)
    ax.set_xlim(0, max(plot["n"]) + 2.2)
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "f", x=-0.27)


def render_panel_g(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.sort_values("sharedness_delta")
    y = np.arange(len(plot))
    colors = [COLORS["primary_qualified"] if v == "transcriptomic_heavy_axis" else ("#8A8A8A" if "dependency" in v else "#C8C8C8") for v in plot["explanatory_call"]]
    ax.barh(y, plot["sharedness_delta"], color=colors, height=0.55)
    ax.axvline(0, color=COLORS["text"], linewidth=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["axis_id"])
    ax.set_xlabel("Shift R2 - dependency R2")
    ax.set_title("Most non-positive axes are preliminary or mixed", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "g", x=-0.30)


def render_panel_h(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Axis claim boundary", loc="left", pad=4)
    rows = [
        ("Formal positive", "transcription / chromatin"),
        ("Allowed wording", "unique stable formal positive axis"),
        ("Required qualifier", "covariate not formally closed"),
        ("Not allowed", "fully deconfounded architecture"),
    ]
    y = 0.82
    for label, text in rows:
        color = COLORS["primary_qualified"] if label in {"Formal positive", "Allowed wording"} else (COLORS["supporting"] if label == "Required qualifier" else COLORS["boundary"])
        ax.text(0.04, y, label, color=color, fontweight="bold", fontsize=8, transform=ax.transAxes)
        ax.text(0.43, y, text, fontsize=8, transform=ax.transAxes)
        y -= 0.20
    row = df.loc[df["object"].eq("transcription_chromatin_axis")].iloc[0]
    ax.text(0.04, 0.05, row["evidence_tier"], fontsize=7, color=COLORS["text"], transform=ax.transAxes)
    add_panel_label(ax, "h", x=-0.04)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    explanatory = pd.read_csv(root / AXIS_EXPLANATORY, sep="\t")
    bootstrap = pd.read_csv(root / AXIS_BOOTSTRAP, sep="\t")
    validation = pd.read_csv(root / AXIS_VALIDATION, sep="\t")
    final_claim = pd.read_csv(root / FINAL_CLAIM_MATRIX, sep="\t")

    focus = explanatory.loc[explanatory["axis_id"].eq("transcription / chromatin")].iloc[0]
    focus_boot = bootstrap.loc[bootstrap["axis_id"].eq("transcription / chromatin")].iloc[0]
    focus_claim = final_claim.loc[final_claim["object"].eq("transcription_chromatin_axis")].iloc[0]
    if focus["explanatory_call"] != "transcriptomic_heavy_axis":
        raise RuntimeError("Fig. 5 sanity check failed: transcription / chromatin is not transcriptomic-heavy.")
    if focus["call_tier"] != "formal":
        raise RuntimeError("Fig. 5 sanity check failed: transcription / chromatin is not formal.")
    if not (0.085 <= float(focus["shift_r2_mean"]) <= 0.100):
        raise RuntimeError("Fig. 5 sanity check failed: transcription / chromatin shift R2 changed materially.")
    if not (0 <= float(focus["depmap_r2_mean"]) <= 0.002):
        raise RuntimeError("Fig. 5 sanity check failed: transcription / chromatin dependency R2 changed materially.")
    if float(focus_boot["bootstrap_dominant_call_fraction"]) < 0.90:
        raise RuntimeError("Fig. 5 sanity check failed: transcription / chromatin bootstrap stability dropped.")
    if focus_claim["evidence_tier"] != "primary_axis_but_qualified":
        raise RuntimeError("Fig. 5 sanity check failed: transcription / chromatin claim tier changed.")

    annot = validation.copy()
    parsed = annot["annotation_support"].map(parse_annotation_support)
    annot["enrichment_hits"] = [v[0] for v in parsed]
    annot["databases"] = [v[1] for v in parsed]
    family = explanatory[["axis_id", "axis_family"]].drop_duplicates()
    annot = annot.merge(family, on="axis_id", how="left")
    focus_df = explanatory.loc[explanatory["axis_id"].eq("transcription / chromatin")].merge(
        bootstrap[["axis_id", "bootstrap_dominant_call_fraction", "bootstrap_stability_call"]], on="axis_id", how="left"
    )
    preliminary = explanatory.loc[
        explanatory["call_tier"].eq("preliminary") | explanatory["explanatory_call"].str.contains("mixed_or_low_signal")
    ].copy()
    preliminary = preliminary.sort_values("sharedness_delta").head(14)
    return {
        "a": explanatory,
        "b": explanatory[["axis_id", "call_tier", "explanatory_call", "formal_call_eligible"]],
        "c": bootstrap,
        "d": annot[["axis_id", "axis_family", "structure_support", "annotation_support", "enrichment_hits", "databases", "final_call"]],
        "e": focus_df[
            [
                "axis_id",
                "targets",
                "shift_r2_mean",
                "depmap_r2_mean",
                "sharedness_delta",
                "bootstrap_dominant_call_fraction",
                "bootstrap_stability_call",
            ]
        ],
        "f": annot[["axis_id", "axis_family", "structure_support", "enrichment_hits", "databases", "final_call"]],
        "g": preliminary[["axis_id", "call_tier", "explanatory_call", "sharedness_delta", "shift_r2_mean", "depmap_r2_mean"]],
        "h": final_claim.loc[
            final_claim["object"].isin(["transcription_chromatin_axis", "other_axes"]),
            ["object", "evidence_tier", "allowed_wording", "disallowed_wording"],
        ],
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
        "a": "Axis explanatory balance",
        "b": "Formal and preliminary axis calls",
        "c": "Bootstrap stability",
        "d": "Annotation support",
        "e": "Transcription/chromatin focus",
        "f": "Partial support by axis family",
        "g": "Preliminary and mixed axes",
        "h": "Axis claim boundary",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")
    fig = plt.figure(figsize=(11.0, 10.0))
    gs = fig.add_gridspec(4, 2, hspace=0.78, wspace=0.48)
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
    parser = argparse.ArgumentParser(description="Build manuscript Figure 5 axis interpretation panels and assembly.")
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
            width=3.55 if panel_id in {"c", "d", "g"} else 3.2,
            height=2.8 if panel_id in {"c", "d", "g"} else 2.35,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
