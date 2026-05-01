from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import pandas as pd
from matplotlib.lines import Line2D

from wtbench.manuscript._palette import DARK_TEXT, DIVIDER_GRAY, MID_GRAY, NEUTRAL_GRAY, SKY_BLUE, VERMILLION
from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes


FIGURE_ID = "extended_data_figure4"
FIGURE_TITLE = "Descriptive axis-level signal space"
SCRIPT_PATH = Path("scripts/manuscript/build_extended_data_figure10_axis_explanatory.py")
CLAIM_BOUNDARY = (
    "Axis-level decomposition is a descriptive exploratory layer and was not used to define the benchmark truth "
    "object, endpoint hierarchy, or model-adjudication criteria. The figure displays axis-level signal summaries "
    "without promoting a new axis-level conclusion."
)
PANEL_IDS = tuple("ab")

AXIS_EXPLANATORY = Path("reports/stage2_truth_bridge_decomposition/axis_level_shared_explanatory_summary.tsv")
AXIS_BOOTSTRAP = Path("reports/stage2_truth_bridge_decomposition/axis_bootstrap_stability.tsv")
AXIS_VALIDATION = Path("reports/stage2_axis_analysis/axis_validation_summary.tsv")

PROFILE_COLORS = {
    "shift-dominant": VERMILLION,
    "dependency-dominant": SKY_BLUE,
    "balanced": "#8E63B6",
    "low signal": MID_GRAY,
}


def parse_annotation_support(value: str) -> tuple[int, int, str]:
    hits = re.search(r"enrichment_hits=(\d+)", value)
    dbs = re.search(r"databases=(\d+)", value)
    top_term = re.search(r"top_recurrent_term=([^;]+)", value)
    return (
        int(hits.group(1)) if hits else 0,
        int(dbs.group(1)) if dbs else 0,
        top_term.group(1) if top_term else "below_threshold",
    )


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_extended_data_v1/edfig10_axis_explanatory_space"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [
        root / AXIS_EXPLANATORY,
        root / AXIS_BOOTSTRAP,
        root / AXIS_VALIDATION,
    ]


def cleanup_generated(root: Path) -> None:
    out = output_dir(root)
    if panel_dir(root).exists():
        for path in panel_dir(root).glob("edfig10_panel*"):
            path.unlink()
    for suffix in (".png", ".pdf", "_source_data.tsv", "_panel_manifest.json"):
        path = out / f"edfig10{suffix}"
        if path.exists():
            path.unlink()


def _compact_axis_label(axis_id: str) -> str:
    mapping = {
        "transcription / chromatin": "transcription /\nchromatin",
        "RNA processing / spliceosome": "RNA processing /\nspliceosome",
        "ribosome biogenesis / nucleolar": "ribosome biogenesis /\nnucleolar",
        "chromatin remodeling": "chromatin\nremodeling",
        "mTOR / lysosome / signaling": "mTOR /\nlysosome /\nsignaling",
        "proteostasis / chaperone": "proteostasis /\nchaperone",
        "transcription regulation": "transcription\nregulation",
        "nuclear receptor / metabolism": "nuclear receptor /\nmetabolism",
        "TGF-beta / BMP signaling": "TGF-beta /\nBMP signaling",
    }
    return mapping.get(axis_id, axis_id)


def _compact_target_support(targets: str, n_targets: int) -> str:
    parts = [part.strip() for part in str(targets).split(";") if part.strip()]
    if n_targets <= 1:
        return f"n = {n_targets}; {parts[0]} only" if parts else f"n = {n_targets}"
    if len(parts) <= 2:
        return f"n = {n_targets}; {' / '.join(parts)}"
    return f"n = {n_targets}; {parts[0]} +{len(parts) - 1}"


def _signal_profile(shift_r2: float, depmap_r2: float) -> str:
    if max(shift_r2, depmap_r2) < 0.02:
        return "low signal"
    if shift_r2 >= 1.5 * max(depmap_r2, 1e-6):
        return "shift-dominant"
    if depmap_r2 >= 1.5 * max(shift_r2, 1e-6):
        return "dependency-dominant"
    return "balanced"


def build_axis_sources(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    explanatory = pd.read_csv(root / AXIS_EXPLANATORY, sep="\t")
    bootstrap = pd.read_csv(root / AXIS_BOOTSTRAP, sep="\t")
    validation = pd.read_csv(root / AXIS_VALIDATION, sep="\t")

    parsed = validation["annotation_support"].map(parse_annotation_support)
    validation["enrichment_hits"] = [value[0] for value in parsed]
    validation["databases"] = [value[1] for value in parsed]

    merged = explanatory.merge(
        bootstrap[["axis_id", "bootstrap_stability_call", "bootstrap_dominant_call_fraction"]],
        on="axis_id",
        how="left",
    ).merge(
        validation[["axis_id", "enrichment_hits", "databases", "structure_support"]],
        on="axis_id",
        how="left",
    )

    source_a = explanatory[
        [
            "axis_id",
            "shift_r2_mean",
            "depmap_r2_mean",
            "sharedness_delta",
            "explanatory_call",
            "call_tier",
            "n_targets",
            "targets",
        ]
    ].copy()
    source_a["signal_profile"] = [
        _signal_profile(shift, depmap) for shift, depmap in zip(source_a["shift_r2_mean"], source_a["depmap_r2_mean"])
    ]

    merged["max_axis_r2"] = merged[["shift_r2_mean", "depmap_r2_mean"]].max(axis=1)
    merged["signal_profile"] = [
        _signal_profile(shift, depmap) for shift, depmap in zip(merged["shift_r2_mean"], merged["depmap_r2_mean"])
    ]
    source_b = merged.nlargest(10, "max_axis_r2").copy()
    source_b = source_b[
        [
            "axis_id",
            "shift_r2_mean",
            "depmap_r2_mean",
            "n_targets",
            "targets",
            "call_tier",
            "explanatory_call",
            "bootstrap_stability_call",
            "bootstrap_dominant_call_fraction",
            "enrichment_hits",
            "databases",
            "structure_support",
            "max_axis_r2",
            "signal_profile",
        ]
    ].sort_values("max_axis_r2", ascending=False).reset_index(drop=True)
    return source_a, source_b


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_label(ax, "a", x=-0.08, y=1.025)
    lim_max = 0.26
    ax.plot([0, lim_max], [0, lim_max], color=DIVIDER_GRAY, linewidth=0.75, linestyle=(0, (3, 2)), zorder=0)

    for profile, color in PROFILE_COLORS.items():
        sub = df.loc[df["signal_profile"].eq(profile)].copy()
        if sub.empty:
            continue
        single = sub.loc[sub["n_targets"].eq(1)]
        multi = sub.loc[sub["n_targets"].ge(2)]
        if not single.empty:
            ax.scatter(
                single["depmap_r2_mean"],
                single["shift_r2_mean"],
                s=22,
                facecolor="white",
                edgecolor=color,
                linewidth=0.85,
                alpha=0.92,
                zorder=2,
            )
        if not multi.empty:
            ax.scatter(
                multi["depmap_r2_mean"],
                multi["shift_r2_mean"],
                s=30,
                c=color,
                edgecolor="white",
                linewidth=0.6,
                alpha=0.92,
                zorder=3,
            )

    label_offsets = {
        "RNA processing / spliceosome": (0.014, -0.026),
        "transcription / chromatin": (0.016, 0.028),
        "ribosomal / translation": (0.014, 0.026),
        "chromatin remodeling": (0.014, 0.014),
    }
    for axis_id, (dx, dy) in label_offsets.items():
        rows = df.loc[df["axis_id"].eq(axis_id)]
        if rows.empty:
            continue
        row = rows.iloc[0]
        color = PROFILE_COLORS[row.signal_profile]
        x = float(row.depmap_r2_mean)
        y = float(row.shift_r2_mean)
        label_x = x + dx
        label_y = y + dy
        ax.plot(
            [x, label_x - 0.003],
            [y, label_y],
            color=color,
            linewidth=0.55,
            alpha=0.85,
            zorder=1.5,
            solid_capstyle="round",
        )
        ax.text(
            label_x,
            label_y,
            _compact_axis_label(axis_id),
            fontsize=6.8,
            color=color,
            ha="left",
            va="center",
            zorder=5,
        )

    ax.set_xlabel("Dependency signal (R²)")
    ax.set_ylabel("Shift signal (R²)")
    ax.set_title("Axis-level signal space", loc="left", fontsize=8.4, fontweight="bold")
    ax.set_xlim(-0.005, lim_max)
    ax.set_ylim(-0.008, lim_max)
    ax.set_aspect("equal", adjustable="box")
    ax.set_anchor("NW")
    clean_axes(ax)
    ax.grid(False)
    profile_handles = [
        Line2D([0], [0], marker="o", linestyle="", markerfacecolor=color, markeredgecolor="white", markersize=5.0, label=profile)
        for profile, color in PROFILE_COLORS.items()
    ]
    breadth_handles = [
        Line2D([0], [0], marker="o", linestyle="", markerfacecolor="white", markeredgecolor=NEUTRAL_GRAY, markersize=4.6, label="n = 1"),
        Line2D([0], [0], marker="o", linestyle="", markerfacecolor=NEUTRAL_GRAY, markeredgecolor="white", markersize=4.6, label="n >= 2"),
    ]
    first = ax.legend(handles=profile_handles, frameon=False, loc="upper left", fontsize=5.9, handletextpad=0.35)
    ax.add_artist(first)
    ax.legend(handles=breadth_handles, frameon=False, loc="lower right", fontsize=5.9, handletextpad=0.35, title="Breadth", title_fontsize=6.1)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    add_panel_label(ax, "b", x=-0.08, y=1.02)
    sort_col = "max_axis_r2" if "max_axis_r2" in df.columns else "shift_r2_mean"
    plot = df.sort_values(sort_col, ascending=False).reset_index(drop=True)
    y = list(range(len(plot)))[::-1]
    trans = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)

    for yi, row in zip(y, plot.itertuples()):
        color = PROFILE_COLORS[row.signal_profile]
        ax.plot(
            [row.depmap_r2_mean, row.shift_r2_mean],
            [yi, yi],
            color=color,
            linewidth=1.0,
            alpha=0.62,
            zorder=1,
        )
        ax.scatter(
            [row.depmap_r2_mean],
            [yi],
            marker="s",
            s=28 if row.n_targets >= 2 else 24,
            facecolor="white",
            edgecolor=color,
            linewidth=0.9,
            zorder=3,
        )
        ax.scatter(
            [row.shift_r2_mean],
            [yi],
            marker="o",
            s=30 if row.n_targets >= 2 else 26,
            facecolor=color if row.n_targets >= 2 else "white",
            edgecolor=color,
            linewidth=1.0,
            zorder=4,
        )
        support = _compact_target_support(row.targets, int(row.n_targets))
        ax.text(
            1.02,
            yi,
            support,
            transform=trans,
            ha="left",
            va="center",
            fontsize=5.8,
            color=NEUTRAL_GRAY,
        )

    ax.set_yticks(y)
    ax.set_yticklabels([_compact_axis_label(axis_id) for axis_id in plot["axis_id"]], fontsize=6.3)
    ax.set_xlim(-0.003, 0.26)
    ax.set_ylim(-0.6, len(plot) - 0.4)
    ax.set_xlabel("Axis signal (R²)")
    ax.set_title("Paired axis R² ranking", loc="left", fontsize=8.4, fontweight="bold")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    ax.tick_params(axis="y", length=0)

    # Marker legend (Shift R² / Dependency R²) merged into legend area
    marker_handles = [
        Line2D([0], [0], marker="o", linestyle="", markerfacecolor=MID_GRAY, markeredgecolor=NEUTRAL_GRAY, markersize=4.6, label="Shift R²"),
        Line2D([0], [0], marker="s", linestyle="", markerfacecolor="white", markeredgecolor=NEUTRAL_GRAY, markersize=4.6, label="Dependency R²"),
    ]
    profile_handles = [
        Line2D([0], [0], marker="o", linestyle="", markerfacecolor=color, markeredgecolor="white", markersize=4.6, label=profile)
        for profile, color in PROFILE_COLORS.items()
    ]
    ax.legend(
        handles=marker_handles + profile_handles,
        frameon=False,
        loc="lower right",
        bbox_to_anchor=(1.0, -0.02),
        fontsize=5.6,
        handletextpad=0.35,
    )


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {"a": render_panel_a, "b": render_panel_b}[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Axis-level signal space",
        "b": "Paired axis R2 ranking",
    }[panel_id]


def write_panel(
    *,
    root: Path,
    panel_id: str,
    source_df: pd.DataFrame,
    render: Callable[[plt.Axes, pd.DataFrame], None],
) -> dict[str, Path]:
    pdir = ensure_dir(panel_dir(root))
    stem = f"edfig10_panel{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    width, height = ((4.1, 3.4) if panel_id == "a" else (5.1, 3.4))
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    output_paths = save_figure(fig, pdir / f"{stem}.png", pdir / f"{stem}.pdf")
    manifest_path = pdir / f"{stem}_manifest.json"
    write_panel_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        panel_id=f"ED4{panel_id}",
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
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / "edfig10_source_data.tsv")
    fig = plt.figure(figsize=(10.2, 3.85))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.2], wspace=0.30)
    axes = {
        "a": fig.add_subplot(gs[0, 0]),
        "b": fig.add_subplot(gs[0, 1]),
    }
    for panel_id in PANEL_IDS:
        render_panel_by_id(panel_id)(axes[panel_id], sources[panel_id])
    output_paths = save_figure(fig, out / "edfig10.png", out / "edfig10.pdf")
    write_figure_manifest(
        manifest_path=out / "edfig10_panel_manifest.json",
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
    parser = argparse.ArgumentParser(description="Build Extended Data Fig. 4 axis explanatory figure.")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    apply_manuscript_style()
    root = repo_root()
    cleanup_generated(root)
    source_a, source_b = build_axis_sources(root)
    sources = {"a": source_a, "b": source_b}
    panel_outputs = {
        panel_id: write_panel(root=root, panel_id=panel_id, source_df=sources[panel_id], render=render_panel_by_id(panel_id))
        for panel_id in PANEL_IDS
    }
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
