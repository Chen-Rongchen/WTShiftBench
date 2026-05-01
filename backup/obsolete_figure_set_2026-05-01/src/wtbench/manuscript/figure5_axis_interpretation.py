from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript._palette import (
    DARK_TEXT,
    DIVIDER_GRAY,
    LIGHT_GRAY,
    NEUTRAL_GRAY,
    PRIMARY_GREEN,
    PRIMARY_GREEN_EDGE,
    PRIMARY_GREEN_FILL,
    SKY_BLUE,
)
from wtbench.manuscript.manuscript_style import add_panel_label, apply_manuscript_style, clean_axes


FIGURE_ID = "figure5"
FIGURE_TITLE = "Axis-level adjudication supports only a qualified transcription/chromatin interpretation"
SCRIPT_PATH = Path("scripts/manuscript/build_figure5_axis_interpretation.py")
CLAIM_BOUNDARY = (
    "Axis-level decomposition provided bounded exploratory support for a "
    "transcription/chromatin-related interpretation, while also showing that "
    "high shift R² or high bootstrap stability alone was insufficient for axis retention. "
    "Transcription/chromatin remained qualified rather than closed because breadth stayed narrow "
    "and covariate closure was not achieved."
)

AXIS_EXPLANATORY = Path("reports/stage2_truth_bridge_decomposition/axis_level_shared_explanatory_summary.tsv")
AXIS_BOOTSTRAP = Path("reports/stage2_truth_bridge_decomposition/axis_bootstrap_stability.tsv")
AXIS_VALIDATION = Path("reports/stage2_axis_analysis/axis_validation_summary.tsv")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig5_axis_interpretation"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return output_dir(root) / "manuscript_export"


def manuscript_panel_dir(root: Path) -> Path:
    return manuscript_figure_dir(root) / "panels"


def input_paths(root: Path) -> list[Path]:
    return [
        root / AXIS_EXPLANATORY,
        root / AXIS_BOOTSTRAP,
        root / AXIS_VALIDATION,
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
    manuscript_pdir = ensure_dir(manuscript_panel_dir(root))
    stem = f"{FIGURE_ID}_panel{panel_id}"
    manuscript_stem = f"Extended_Data_Figure_12_panel_{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    manuscript_source_path = write_tsv(source_df, manuscript_pdir / f"{manuscript_stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    png_path = pdir / f"{stem}.png"
    pdf_path = pdir / f"{stem}.pdf"
    manuscript_png_path = manuscript_pdir / f"{manuscript_stem}.png"
    manuscript_pdf_path = manuscript_pdir / f"{manuscript_stem}.pdf"
    for path in [png_path, pdf_path, manuscript_png_path, manuscript_pdf_path]:
        ensure_dir(path.parent)
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(manuscript_png_path, dpi=300, bbox_inches="tight")
    fig.savefig(manuscript_pdf_path, bbox_inches="tight")
    plt.close(fig)
    output_paths = [png_path, pdf_path]
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
    write_panel_manifest(
        manifest_path=manuscript_pdir / f"{manuscript_stem}_manifest.json",
        repo_root=root,
        panel_id=f"{FIGURE_ID}{panel_id}",
        panel_title=panel_title,
        script_path=root / SCRIPT_PATH,
        input_paths=input_paths(root),
        source_data_path=manuscript_source_path,
        output_paths=[manuscript_png_path, manuscript_pdf_path],
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def parse_annotation_support(value: str) -> tuple[int, int, str]:
    hits = re.search(r"enrichment_hits=(\d+)", value)
    dbs = re.search(r"databases=(\d+)", value)
    top_term = re.search(r"top_recurrent_term=([^;]+)", value)
    return (
        int(hits.group(1)) if hits else 0,
        int(dbs.group(1)) if dbs else 0,
        top_term.group(1) if top_term else "below_threshold",
    )


def axis_display_label(axis_id: str) -> str:
    mapping = {
        "transcription / chromatin": "transcription /\nchromatin",
        "RNA processing / spliceosome": "RNA processing /\nspliceosome",
        "mTOR / lysosome / signaling": "mTOR /\nlysosome /\nsignaling",
        "ER stress / UPR": "ER stress /\nUPR",
        "ribosomal / translation": "ribosomal /\ntranslation",
        "ribosome biogenesis / nucleolar": "ribosome\nbiogenesis /\nnucleolar",
        "chromatin remodeling": "chromatin\nremodeling",
    }
    return mapping.get(axis_id, axis_id)


def axis_matrix_label(axis_id: str) -> str:
    mapping = {
        "transcription / chromatin": "transcription /\nchromatin",
        "RNA processing / spliceosome": "RNA proc. /\nspliceosome",
        "mTOR / lysosome / signaling": "mTOR /\nlysosome /\nsignaling",
        "ER stress / UPR": "ER stress /\nUPR",
        "ribosomal / translation": "ribosomal /\ntranslation",
    }
    return mapping.get(axis_id, axis_display_label(axis_id))


def axis_compact_label(axis_id: str, n_targets: int | None = None) -> str:
    mapping = {
        "transcription / chromatin": "transcription/\nchromatin",
        "RNA processing / spliceosome": "RNA processing/\nspliceosome",
        "mTOR / lysosome / signaling": "mTOR/lysosome/\nsignaling",
        "ER stress / UPR": "ER stress/\nUPR",
        "ribosomal / translation": "ribosomal/\ntranslation",
        "ribosome biogenesis / nucleolar": "ribosome\nbiogenesis",
        "chromatin remodeling": "chromatin\nremodeling",
    }
    label = mapping.get(axis_id, axis_id)
    if n_targets is not None:
        label += f", n = {n_targets}"
    return label


def compact_target_label(targets: str) -> str:
    parts = [part.strip() for part in str(targets).split(";") if part.strip()]
    if not parts:
        return "single-target"
    if len(parts) == 1:
        return f"{parts[0]} only"
    if len(parts) == 2:
        return " / ".join(parts)
    return f"{parts[0]} +{len(parts) - 1}"


def format_target_breadth(n_targets: float, targets: str) -> str:
    n = int(n_targets)
    if n <= 1:
        return f"n = {n}\n({compact_target_label(targets)})"
    if n == 2:
        return f"n = {n}\n(narrow)"
    return f"n = {n}\n(multi-target)"


def format_shift_signal(value: float) -> str:
    if value >= 0.10:
        label = "high"
    elif value >= 0.04:
        label = "moderate"
    else:
        label = "low"
    return f"{label}\nR² = {value:.3f}"


def format_dependency_signal(value: float) -> str:
    if value <= 0.01:
        label = "near zero"
    elif value <= 0.05:
        label = "non-zero"
    else:
        label = "high"
    return f"{label}\nR² = {value:.3f}"


def format_bootstrap_label(stability_call: str, fraction: float) -> str:
    if stability_call == "stable_axis_call":
        label = "stable"
    elif stability_call == "moderately_stable_axis_call":
        label = "moderate"
    else:
        label = "unstable"
    return f"{label}\n{fraction:.2f}"


def format_annotation_support(hits: float, databases: float) -> str:
    return f"{int(hits)} hits /\n{int(databases)} DBs"


def format_structure_support(value: float) -> str:
    return f"pre-defined\nclass {int(value)}"


def format_support_summary(hits: float, databases: float, structure_support: float) -> str:
    return f"{int(hits)} hits / {int(databases)} DBs\nclass {int(structure_support)}"


def format_final_status(row: pd.Series) -> str:
    axis_id = row["axis_id"]
    n_targets = int(row["n_targets"])
    if axis_id == "transcription / chromatin":
        return "qualified,\nbounded*"
    if n_targets == 1 and axis_id == "RNA processing / spliceosome":
        return "preliminary,\nsingle-target*"
    if axis_id == "ribosomal / translation":
        return "preliminary,\ndep-heavy*"
    return "preliminary*"


def format_shift_threshold(value: float) -> str:
    if value >= 0.08:
        label = "moderate"
    elif value >= 0.04:
        label = "moderate-low"
    else:
        label = "low"
    return f"{label}, R² = {value:.3f}"


def format_dependency_threshold(value: float) -> str:
    if value <= 0.01:
        return "near zero"
    if value <= 0.05:
        return f"non-zero, R² = {value:.3f}"
    return f"high, R² = {value:.3f}"


def format_breadth_threshold(n_targets: float, targets: str) -> str:
    n = int(n_targets)
    if n <= 1:
        return f"n = {n}, single-target ({compact_target_label(targets)})"
    if n == 2:
        return f"n = {n}, narrow breadth"
    return f"n = {n}, multi-target"


def format_bootstrap_threshold(stability_call: str, fraction: float) -> str:
    if stability_call == "stable_axis_call":
        return f"stable, {fraction:.2f}"
    if stability_call == "moderately_stable_axis_call":
        return f"moderate, {fraction:.2f}"
    return f"unstable, {fraction:.2f}"


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Axis-level explanatory space with x/y same scale (0–0.26) and single-target boundary."""
    lim_max = 0.26
    ax.plot([0, lim_max], [0, lim_max], color="#E0E0E0", linewidth=0.75, linestyle=(0, (3, 2)), zorder=0)

    # n = 1 / n >= 2 stay inside the same gray semantic family; shape fill encodes breadth.
    single = df.loc[df["n_targets"].eq(1)].copy()
    multi = df.loc[df["n_targets"].ge(2)].copy()
    focus_idx = df.loc[df["axis_id"].eq("transcription / chromatin")].index
    rna_idx = df.loc[df["axis_id"].eq("RNA processing / spliceosome")].index
    background_idx = df.index.difference(focus_idx.union(rna_idx))
    background = df.loc[background_idx]
    background_single = background.loc[background["n_targets"].eq(1)]
    background_multi = background.loc[background["n_targets"].ge(2)]

    ax.scatter(
        background_single["depmap_r2_mean"], background_single["shift_r2_mean"], s=16,
        facecolor="white", edgecolor=NEUTRAL_GRAY, linewidth=0.75, alpha=0.80, zorder=1,
    )
    ax.scatter(
        background_multi["depmap_r2_mean"], background_multi["shift_r2_mean"], s=16,
        c=NEUTRAL_GRAY, edgecolor="white", linewidth=0.5, alpha=0.80, zorder=1,
    )

    # Highlight transcription/chromatin (n=2) — deep green solid
    focus = df.loc[df["axis_id"].eq("transcription / chromatin")].iloc[0]
    ax.scatter(
        [focus.depmap_r2_mean], [focus.shift_r2_mean], s=110,
        c=PRIMARY_GREEN, edgecolor="white", linewidth=0.5, alpha=0.95, zorder=3,
    )
    ax.annotate(
        "transcription /\nchromatin",
        xy=(focus.depmap_r2_mean, focus.shift_r2_mean),
        xytext=(focus.depmap_r2_mean + 0.016, focus.shift_r2_mean + 0.028),
        fontsize=7.8,
        color=PRIMARY_GREEN,
        fontweight="bold",
        arrowprops={"arrowstyle": "-", "lw": 0.75, "color": NEUTRAL_GRAY},
    )

    # RNA processing / spliceosome — explicitly bounded as single-target PRPF6-only signal.
    rna_proc = df.loc[df["axis_id"].eq("RNA processing / spliceosome")]
    if not rna_proc.empty:
        row = rna_proc.iloc[0]
        ax.scatter(
            [row.depmap_r2_mean], [row.shift_r2_mean], s=26,
            facecolor="white", edgecolor=NEUTRAL_GRAY, linewidth=0.9, alpha=0.95, zorder=2,
        )
        ax.annotate(
            "RNA processing / spliceosome\n(PRPF6 only; n = 1)",
            xy=(row.depmap_r2_mean, row.shift_r2_mean),
            xytext=(0.024, 0.232),
            textcoords="data",
            fontsize=7.0,
            color=DARK_TEXT,
            ha="left",
            va="top",
            arrowprops={"arrowstyle": "-", "lw": 0.5, "color": NEUTRAL_GRAY},
        )

    ax.set_xlabel("Dependency signal (R²)")
    ax.set_ylabel("Shift signal (R²)")
    ax.set_title("Axis-level explanatory space", loc="left", fontsize=8.8, fontweight="bold")
    ax.set_xlim(-0.005, lim_max)
    ax.set_ylim(-0.008, lim_max)
    ax.set_aspect("equal", adjustable="box")
    ax.set_anchor("NW")
    clean_axes(ax)
    ax.grid(False)

    # Legend for target breadth
    ax.scatter([], [], s=28, c=PRIMARY_GREEN, edgecolor="white", linewidth=0.5, label="retained (n ≥ 2)")
    ax.scatter([], [], s=22, facecolor="white", edgecolor=NEUTRAL_GRAY, linewidth=0.75, label="preliminary (n = 1)")
    ax.scatter([], [], s=22, c=NEUTRAL_GRAY, edgecolor="white", linewidth=0.5, label="preliminary (n ≥ 2)")
    ax.legend(frameon=False, loc="lower right", fontsize=6.4, handletextpad=0.4)

    add_panel_label(ax, "a", x=-0.24, y=1.025)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    render_numerical_adjudication_forest(ax, df, panel_label="b")


PROFILE_AXES = [
    "transcription / chromatin",
    "RNA processing / spliceosome",
    "mTOR / lysosome / signaling",
    "ribosomal / translation",
]

PROFILE_CRITERIA = [
    ("Breadth", "breadth"),
    ("Shift", "shift"),
    ("Dependency", "dependency"),
    ("Bootstrap", "bootstrap"),
    ("Annotation", "annotation"),
    ("Structure", "structure"),
]


def _profile_axis_label(axis_id: str) -> str:
    labels = {
        "transcription / chromatin": "transcription /\nchromatin",
        "RNA processing / spliceosome": "RNA proc. /\nspliceosome",
        "mTOR / lysosome / signaling": "mTOR /\nlysosome",
        "ribosomal / translation": "ribosomal /\ntranslation",
    }
    return labels.get(axis_id, axis_matrix_label(axis_id))


def _profile_state(row: pd.Series, key: str) -> tuple[str, str]:
    axis_id = str(row["axis_id"])
    n_targets = int(row["n_targets"])
    shift = float(row["shift_r2_mean"])
    dep = float(row["depmap_r2_mean"])
    boot = float(row["bootstrap_dominant_call_fraction"])
    hits = int(row["enrichment_hits"])
    dbs = int(row["databases"])
    structure = int(row["structure_support"])
    if key == "breadth":
        return ("support", f"n={n_targets}") if n_targets >= 2 else ("limit", "single")
    if key == "shift":
        if shift >= 0.08:
            return ("support", f"{shift:.2f}")
        if shift >= 0.04:
            return ("partial", f"{shift:.2f}")
        return ("limit", f"{shift:.2f}")
    if key == "dependency":
        if dep <= 0.01:
            return ("support", f"{dep:.3f}")
        if axis_id == "ribosomal / translation":
            return ("limit", "dep-heavy")
        return ("limit", f"{dep:.2f}")
    if key == "bootstrap":
        return ("support", f"{boot:.2f}") if boot >= 0.90 else ("partial", f"{boot:.2f}")
    if key == "annotation":
        return ("support", f"{hits}/{dbs}") if hits >= 5 and dbs >= 2 else ("partial", f"{hits}/{dbs}")
    if key == "structure":
        return ("support", f"class {structure}") if structure <= 1 else ("partial", f"class {structure}")
    raise KeyError(key)


def _profile_style(state: str) -> tuple[str, str, str, str]:
    if state == "support":
        return "o", PRIMARY_GREEN, PRIMARY_GREEN, "white"
    if state == "limit":
        return "D", "#D55E00", "#D55E00", "white"
    return "o", "white", NEUTRAL_GRAY, DARK_TEXT


def render_panel_c_left(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Graphical multi-criterion profile moved out of the summary panel."""
    plot_df = df.set_index("axis_id").reindex(PROFILE_AXES).dropna(how="all").reset_index()
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    x_label = 0.030
    x0 = 0.315
    x_step = 0.090
    y_top = 0.760
    y_step = 0.155
    row_h = 0.112

    ax.text(0.0, 0.990, "Multi-criterion profile", ha="left", va="top", fontsize=7.4, fontweight="bold")
    for cidx, (display, _) in enumerate(PROFILE_CRITERIA):
        ax.text(
            x0 + cidx * x_step,
            0.865,
            display,
            ha="center",
            va="bottom",
            fontsize=5.8,
            color=DARK_TEXT,
            rotation=35,
            rotation_mode="anchor",
        )

    for ridx, row in enumerate(plot_df.itertuples(index=False)):
        y = y_top - ridx * y_step
        row_series = pd.Series(row._asdict())
        axis_id = str(row_series["axis_id"])
        is_focus = axis_id == "transcription / chromatin"
        if is_focus:
            ax.add_patch(
                FancyBboxPatch(
                    (0.0, y - row_h / 2),
                    0.970,
                    row_h,
                    boxstyle="round,pad=0.006,rounding_size=0.012",
                    facecolor=PRIMARY_GREEN_FILL,
                    edgecolor="none",
                    alpha=0.70,
                    transform=ax.transAxes,
                    zorder=0,
                )
            )
        ax.text(
            x_label,
            y,
            _profile_axis_label(axis_id),
            ha="left",
            va="center",
            fontsize=6.0,
            color=PRIMARY_GREEN if is_focus else DARK_TEXT,
            fontweight="bold" if is_focus else "normal",
            linespacing=0.82,
        )
        ax.plot(
            [x0 - 0.040, x0 + (len(PROFILE_CRITERIA) - 1) * x_step + 0.040],
            [y, y],
            color="#F0F0F0",
            linewidth=0.6,
            zorder=0.5,
        )
        for cidx, (_, key) in enumerate(PROFILE_CRITERIA):
            state, label = _profile_state(row_series, key)
            marker, face, edge, text_color = _profile_style(state)
            ax.scatter(
                [x0 + cidx * x_step],
                [y],
                s=44 if state == "support" else 38,
                marker=marker,
                facecolor=face,
                edgecolor=edge,
                linewidth=0.8,
                zorder=3,
            )
            if key in {"breadth", "dependency", "bootstrap"}:
                ax.text(
                    x0 + cidx * x_step,
                    y - 0.050,
                    label,
                    ha="center",
                    va="top",
                    fontsize=4.8,
                    color=text_color if state == "partial" else edge,
                    zorder=4,
                )

    legend_handles = [
        Line2D([0], [0], marker="o", linestyle="", color=PRIMARY_GREEN, markerfacecolor=PRIMARY_GREEN, markersize=4.8, label="supports retention"),
        Line2D([0], [0], marker="o", linestyle="", color=NEUTRAL_GRAY, markerfacecolor="white", markersize=4.8, label="partial/contextual"),
        Line2D([0], [0], marker="D", linestyle="", color="#D55E00", markerfacecolor="#D55E00", markersize=4.4, label="limiting factor"),
    ]
    ax.legend(handles=legend_handles, frameon=False, loc="lower left", bbox_to_anchor=(0.0, 0.025), fontsize=5.3, handletextpad=0.28, ncol=1, labelspacing=0.22)


def render_panel_c_right(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Representative boundary forest-style comparison with shift and dependency markers."""
    order = [
        "transcription / chromatin",
        "RNA processing / spliceosome",
        "ER stress / UPR",
        "mTOR / lysosome / signaling",
        "ribosomal / translation",
    ]
    order_map = {a: i for i, a in enumerate(order)}
    df = df.loc[df["axis_id"].isin(order_map)].copy()
    df["sort_key"] = df["axis_id"].map(order_map).fillna(999)
    df = df.sort_values("sort_key")

    shift_vals = df["shift_r2_mean"].astype(float).values
    dep_vals = df["depmap_r2_mean"].astype(float).values
    n_targets = df["n_targets"].astype(int).values
    axis_ids = df["axis_id"].values
    y_pos = np.arange(len(df))

    sizes = np.where(n_targets >= 2, 86, 62)
    colors = [PRIMARY_GREEN if aid == "transcription / chromatin" else NEUTRAL_GRAY for aid in axis_ids]

    ax.axhspan(-0.5, 0.5, color=PRIMARY_GREEN_FILL, alpha=0.45, zorder=0)

    for y, dep, shift, color, size in zip(y_pos, dep_vals, shift_vals, colors, sizes):
        ax.hlines(y, dep, shift, color=color, linewidth=0.9, zorder=1)
        ax.scatter(dep, y, s=34, facecolor="white", edgecolor=color, linewidth=0.9, zorder=3)
        ax.scatter(shift, y, s=size, c=color, edgecolor="white", linewidth=0.9, zorder=3)

    for dep, shift, y, aid in zip(dep_vals, shift_vals, y_pos, axis_ids):
        value_color = PRIMARY_GREEN if aid == "transcription / chromatin" else NEUTRAL_GRAY
        ax.text(shift, y - 0.16, f"shift {shift:.3f}", ha="center", va="bottom", fontsize=6.3, fontweight="bold", color=value_color)
        ax.text(max(dep, 0.002), y + 0.18, f"dep {dep:.3f}", ha="left", va="top", fontsize=5.8, color=DARK_TEXT)

    labels = []
    for aid in axis_ids:
        if aid == "transcription / chromatin":
            labels.append("transcription /\nchromatin")
        elif aid == "RNA processing / spliceosome":
            labels.append("RNA processing /\nspliceosome")
        elif aid == "ER stress / UPR":
            labels.append("ER stress /\nUPR")
        elif aid == "mTOR / lysosome / signaling":
            labels.append("mTOR / lysosome /\nsignaling")
        elif aid == "ribosomal / translation":
            labels.append("ribosomal /\ntranslation")
        else:
            labels.append(aid)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=6.1)
    for tick, axis_id in zip(ax.get_yticklabels(), axis_ids):
        if axis_id == "transcription / chromatin":
            tick.set_color(PRIMARY_GREEN)
            tick.set_fontweight("bold")
        else:
            tick.set_color(DARK_TEXT)
    ax.set_xlabel("Shift signal (R²)", fontsize=7.4)
    ax.set_xlim(0.0, 0.145)
    ax.set_ylim(-0.55, len(df) - 0.45)
    ax.invert_yaxis()
    ax.set_title("Boundary example", loc="left", fontsize=7.2, fontweight="bold")
    clean_axes(ax)
    ax.grid(axis="x", color=LIGHT_GRAY, linewidth=0.5, alpha=0.35)
    ax.set_axisbelow(True)

    dep_text = "Filled = shift; open = dependency; larger point = broader target support"
    ax.text(0.50, -0.10, dep_text, transform=ax.transAxes, ha="center", va="top", fontsize=5.9, color=DARK_TEXT)

def render_numerical_adjudication_forest(ax: plt.Axes, df: pd.DataFrame, *, panel_label: str = "b") -> None:
    """Numerical forest-style view of the adjudication evidence from panel-b source data."""
    plot_df = df.set_index("axis_id").reindex(PROFILE_AXES).dropna(how="all").reset_index()
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    metrics = [
        ("Shift signal", "shift_r2_mean", 0.0, 0.26, 0.08, "higher", "R²"),
        ("Dependency signal", "depmap_r2_mean", 0.0, 0.13, 0.01, "lower", "R²"),
        ("Bootstrap", "bootstrap_dominant_call_fraction", 0.0, 1.0, 0.90, "higher", "fraction"),
        ("Annotation", "enrichment_hits", 0.0, 35.0, 5.0, "higher", "hits"),
    ]
    axis_labels = {
        "transcription / chromatin": "transcription /\nchromatin",
        "RNA processing / spliceosome": "RNA proc. /\nspliceosome",
        "mTOR / lysosome / signaling": "mTOR /\nlysosome",
        "ribosomal / translation": "ribosomal /\ntranslation",
    }

    left_label_x = 0.038
    forest_left = 0.235
    forest_right = 0.800
    metric_w = (forest_right - forest_left) / len(metrics)
    y_top = 0.710
    y_step = 0.140
    row_h = 0.102

    add_panel_label(ax, panel_label, x=-0.045, y=1.025)
    ax.text(0.0, 1.000, "Axis adjudication profile", ha="left", va="top", fontsize=8.3, fontweight="bold", color=DARK_TEXT)
    for ridx, row in enumerate(plot_df.itertuples(index=False)):
        y = y_top - ridx * y_step
        axis_id = str(row.axis_id)
        is_focus = axis_id == "transcription / chromatin"
        if is_focus:
            ax.add_patch(
                FancyBboxPatch(
                    (0.024, y - row_h / 2),
                    0.795,
                    row_h,
                    boxstyle="round,pad=0.006,rounding_size=0.010",
                    facecolor=PRIMARY_GREEN_FILL,
                    edgecolor="none",
                    alpha=0.72,
                    transform=ax.transAxes,
                    zorder=0,
                )
            )
        label = axis_labels.get(axis_id, axis_id)
        label = f"{label}\nn={int(row.n_targets)}"
        ax.text(
            left_label_x,
            y,
            label,
            ha="left",
            va="center",
            fontsize=5.9,
            color=PRIMARY_GREEN if is_focus else DARK_TEXT,
            fontweight="bold" if is_focus else "normal",
            linespacing=0.82,
        )

    for midx, (title, column, xmin, xmax, ref, direction, unit) in enumerate(metrics):
        x_left = forest_left + midx * metric_w + 0.012
        x_right = forest_left + (midx + 1) * metric_w - 0.016
        ax.text((x_left + x_right) / 2, 0.865, title, ha="center", va="bottom", fontsize=5.9, fontweight="bold", color=DARK_TEXT)
        ref_x = x_left + (ref - xmin) / (xmax - xmin) * (x_right - x_left)

        for ridx, row in enumerate(plot_df.itertuples(index=False)):
            y = y_top - ridx * y_step
            axis_id = str(row.axis_id)
            value = float(getattr(row, column))
            value_clipped = min(max(value, xmin), xmax)
            x_val = x_left + (value_clipped - xmin) / (xmax - xmin) * (x_right - x_left)
            if direction == "higher":
                state = "support" if value >= ref else "limit"
            else:
                state = "support" if value <= ref else "limit"
            if column == "bootstrap_dominant_call_fraction" and value >= 0.80 and value < ref:
                state = "partial"
            if column == "enrichment_hits" and value >= ref and int(getattr(row, "databases")) < 2:
                state = "partial"
            marker, face, edge, _ = _profile_style(state)
            line_color = PRIMARY_GREEN if state == "support" else ("#D55E00" if state == "limit" else NEUTRAL_GRAY)
            ax.plot([x_left, x_right], [y, y], color="#E6E6E6", linewidth=0.55, solid_capstyle="butt", zorder=0.8)
            ax.plot([ref_x, ref_x], [y - 0.038, y + 0.038], color="#CFCFCF", linewidth=0.70, zorder=1.0)
            ax.plot([ref_x, x_val], [y, y], color=line_color, linewidth=0.95, alpha=0.75, solid_capstyle="butt", zorder=1.5)
            ax.scatter([x_val], [y], s=34 if state != "support" else 40, marker=marker, facecolor=face, edgecolor=edge, linewidth=0.8, zorder=3)
            if column in {"depmap_r2_mean", "bootstrap_dominant_call_fraction"}:
                label = f"{value:.2f}" if column == "bootstrap_dominant_call_fraction" else f"{value:.3f}"
                ax.text(x_val, y - 0.037, label, ha="center", va="top", fontsize=4.4, color=edge, zorder=4)

    legend_items = [
        ("o", PRIMARY_GREEN, PRIMARY_GREEN, "support"),
        ("o", "white", NEUTRAL_GRAY, "partial"),
        ("D", "#D55E00", "#D55E00", "limit"),
    ]
    legend_y = 0.500
    for idx, (marker, face, edge, label) in enumerate(legend_items):
        y = legend_y - idx * 0.060
        ax.scatter([0.858], [y], s=32, marker=marker, facecolor=face, edgecolor=edge, linewidth=0.8, transform=ax.transAxes, zorder=3)
        ax.text(0.878, y, label, ha="left", va="center", fontsize=5.2, color=DARK_TEXT, transform=ax.transAxes)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    explanatory = pd.read_csv(root / AXIS_EXPLANATORY, sep="\t")
    bootstrap = pd.read_csv(root / AXIS_BOOTSTRAP, sep="\t")
    validation = pd.read_csv(root / AXIS_VALIDATION, sep="\t")
    _ = pd.read_csv(root / FINAL_CLAIM_MATRIX, sep="\t")

    focus = explanatory.loc[explanatory["axis_id"].eq("transcription / chromatin")].iloc[0]
    focus_boot = bootstrap.loc[bootstrap["axis_id"].eq("transcription / chromatin")].iloc[0]
    if focus["explanatory_call"] != "transcriptomic_heavy_axis":
        raise RuntimeError("Fig. 5 sanity check: transcription / chromatin is not transcriptomic-heavy.")
    if focus["call_tier"] != "formal":
        raise RuntimeError("Fig. 5 sanity check: transcription / chromatin is not formal.")
    if not (0.085 <= float(focus["shift_r2_mean"]) <= 0.100):
        raise RuntimeError("Fig. 5 sanity check: transcription / chromatin shift R2 changed materially.")
    if not (0 <= float(focus["depmap_r2_mean"]) <= 0.002):
        raise RuntimeError("Fig. 5 sanity check: transcription / chromatin dependency R2 changed materially.")
    if float(focus_boot["bootstrap_dominant_call_fraction"]) < 0.90:
        raise RuntimeError("Fig. 5 sanity check: transcription / chromatin bootstrap stability dropped.")

    # Parse annotation support
    annot = validation.copy()
    parsed = annot["annotation_support"].map(parse_annotation_support)
    annot["enrichment_hits"] = [v[0] for v in parsed]
    annot["databases"] = [v[1] for v in parsed]
    annot["top_term"] = [v[2] for v in parsed]

    merged = explanatory.merge(bootstrap, on="axis_id", how="left").merge(
        annot[["axis_id", "enrichment_hits", "databases", "top_term", "structure_support", "final_call"]],
        on="axis_id",
        how="left",
    )

    # Panel a: full explanatory table with n_targets
    source_a = explanatory[[
        "axis_id", "shift_r2_mean", "depmap_r2_mean", "sharedness_delta",
        "explanatory_call", "call_tier", "n_targets", "targets",
    ]].copy()

    # Panel b: summary source — 4 representative axes only
    matrix_axes = [
        "transcription / chromatin",
        "RNA processing / spliceosome",
        "mTOR / lysosome / signaling",
        "ribosomal / translation",
    ]
    source_b = merged.loc[merged["axis_id"].isin(matrix_axes)].copy()
    source_b = source_b[[
        "axis_id", "explanatory_call", "call_tier", "shift_r2_mean", "depmap_r2_mean",
        "n_targets", "targets",
        "bootstrap_stability_call", "bootstrap_dominant_call_fraction",
        "enrichment_hits", "databases", "structure_support", "final_call",
    ]]
    supplementary_dir = ensure_dir(root / "manuscript/supplementary_tables")
    write_tsv(source_b, supplementary_dir / "Figure_5_adjudication_profile.tsv")

    return {
        "a": source_a,
        "b": source_b,
    }


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {
        "a": render_panel_a,
        "b": render_panel_b,
    }[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Axis-level explanatory space",
        "b": "Numerical adjudication forest",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    manuscript_out = ensure_dir(manuscript_figure_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")
    manuscript_source_path = write_tsv(combined_source, manuscript_out / "Extended_Data_Figure_12_source_data.tsv")

    fig = plt.figure(figsize=(11.2, 3.75))
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(
        1,
        2,
        width_ratios=[0.62, 1.70],
        wspace=0.14,
        top=0.94,
        bottom=0.13,
        left=0.070,
        right=0.985,
    )

    ax_a = fig.add_subplot(gs[0, 0])
    ax_a.set_facecolor("white")
    render_panel_a(ax_a, sources["a"])

    ax_b = fig.add_subplot(gs[0, 1])
    ax_b.set_facecolor("white")
    render_panel_b(ax_b, sources["b"])

    png_path = out / f"{FIGURE_ID}.png"
    pdf_path = out / f"{FIGURE_ID}.pdf"
    manuscript_png = manuscript_out / "Extended_Data_Figure_12.png"
    manuscript_pdf = manuscript_out / "Extended_Data_Figure_12.pdf"
    for path in [png_path, pdf_path, manuscript_png, manuscript_pdf]:
        ensure_dir(path.parent)
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(manuscript_png, dpi=300, bbox_inches="tight")
    fig.savefig(manuscript_pdf, bbox_inches="tight")
    output_paths = [png_path, pdf_path]
    plt.close(fig)
    manifest_path = out / f"{FIGURE_ID}_panel_manifest.json"
    write_figure_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in list("ab")],
        combined_source_data_path=combined_source_path,
        output_paths=output_paths,
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )
    write_figure_manifest(
        manifest_path=manuscript_out / "Extended_Data_Figure_12_panel_manifest.json",
        repo_root=root,
        figure_id="Extended_Data_Figure_12",
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[
            manuscript_panel_dir(root) / f"Extended_Data_Figure_12_panel_{p}_manifest.json"
            for p in list("ab")
        ],
        combined_source_data_path=manuscript_source_path,
        output_paths=[manuscript_png, manuscript_pdf],
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
    for panel_id in list("ab"):
        panel_outputs[panel_id] = write_panel(
            root=root,
            panel_id=panel_id,
            panel_title=panel_title(panel_id),
            source_df=sources[panel_id],
            render=render_panel_by_id(panel_id),
            width=8.4 if panel_id == "b" else 4.6,
            height=3.8,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
