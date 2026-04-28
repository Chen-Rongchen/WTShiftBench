from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import (
    add_panel_heading,
    apply_manuscript_style,
    clean_axes,
    model_color,
    short_model_label,
)


FIGURE_ID = "figure4"
FIGURE_TITLE = (
    "The backbone recovery gap remains after prespecified local rebuttal tests"
)
SCRIPT_PATH = Path("scripts/manuscript/build_figure4_sweep_controls.py")
CLAIM_BOUNDARY = (
    "The backbone recovery gap remains after prespecified local rebuttal tests: "
    "a finite-budget GEARS neighborhood sweep (6 prespecified candidates) and "
    "embedding-based linear controls do not close the backbone recovery gap to "
    "the shared-mean baseline. Most stably, no tested rebuttal candidate closes "
    "the backbone gap under the pre-specified neighborhood. GEARS training is not "
    "rerun during figure production; figure panels recompose frozen Stage 2 "
    "adjudication artefacts only."
)

MODEL_COMPARISON = Path("reports/stage2_real_hcc_smoke/model_comparison.tsv")
BACKBONE_DIAGNOSIS = Path("reports/stage2_real_hcc_smoke/backbone_diagnosis.tsv")
SMOKE_SUMMARY = Path("reports/stage2_real_hcc_smoke/smoke_summary.tsv")
SWEEP_MANIFEST = Path("reports/stage2_gears_backbone_sweep/candidate_manifest.tsv")
SWEEP_ADJUDICATION = Path("reports/stage2_gears_backbone_sweep/final_adjudication.md")
WHY_BASELINE_DOC = Path("docs/why_models_do_not_stably_beat_baseline_v1.md")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")

COVERAGE_AUDITS = [
    Path("reports/stage2_lm_g_scgpt_ridge_hcc_recipe/HCC38/coverage_audit.json"),
    Path("reports/stage2_lm_g_scgpt_ridge_hcc_recipe/HCC1143/coverage_audit.json"),
    Path("reports/stage2_lm_g_geneformer_ridge_hcc_recipe/HCC38/coverage_audit.json"),
    Path("reports/stage2_lm_g_geneformer_ridge_hcc_recipe/HCC1143/coverage_audit.json"),
    Path("reports/stage2_lm_train_lowrank_hcc_recipe/HCC38/coverage_audit.json"),
    Path("reports/stage2_lm_train_lowrank_hcc_recipe/HCC1143/coverage_audit.json"),
]

EXPECTED = {
    "baseline_backbone": 0.8066666666666666,
    "formal_gears_backbone": 0.6599999999999999,
    "best_sweep_backbone": 0.6433333333333333,
    "max_sweep_shift_excess": 0.9166666666666667,
}

BEST_SWEEP_ID = "gears_hcc_formal_v1_e30_lr2e-03_wd1e-06"

LINEAR_CONTROL_IDS = [
    "lm_g_geneformer_ridge_hcc_formal_v1",
    "lm_train_lowrank_hcc_formal_v1",
    "lm_g_scgpt_ridge_hcc_formal_v1",
]

LINEAR_CONTROL_LABELS = {
    "lm_g_geneformer_ridge_hcc_formal_v1": "Geneformer-ridge control",
    "lm_train_lowrank_hcc_formal_v1": "Low-rank linear decoder",
    "lm_g_scgpt_ridge_hcc_formal_v1": "scGPT-ridge control",
}

F4_COLORS = {
    "baseline": "#333333",
    "gears": "#0072B2",
    "gears_sweep": "#85C1E9",
    "linear": "#8E8E8E",
    "threshold": "#56B4E9",
    "shaded": "#FAFAFA",
    "header_fill": "#F5F5F5",
    "panel_fill": "#F5F5F5",
    "panel_edge": "#BDBDBD",
    "cell_edge": "#E0E0E0",
    "text": "#000000",
    "grid": "#F1F1F1",
    "warning": "#D55E00",
}

MARKER_SIZES = {
    "baseline": 81,
    "gears": 49,
    "gears_sweep": 20.25,
    "linear": 16,
}


def _format_lr(val: str) -> str:
    """Unify learning-rate display to typographic scientific notation."""
    try:
        f = float(val)
    except ValueError:
        return val
    if f == 0.001:
        return r"$1\times10^{-3}$"
    if f == 0.0005:
        return r"$5\times10^{-4}$"
    if f == 0.002:
        return r"$2\times10^{-3}$"
    if f == 0.0001:
        return r"$1\times10^{-4}$"
    # fallback: one-decimal scientific
    exp = int(np.floor(np.log10(abs(f)))) if f != 0 else 0
    mant = f / (10 ** exp)
    if abs(mant - round(mant)) < 1e-9:
        return rf"${int(round(mant))}\times10^{{{exp}}}$"
    return rf"${mant:.1f}\times10^{{{exp}}}$"


def _format_wd(val: str) -> str:
    """Unify weight-decay display to typographic scientific notation."""
    try:
        f = float(val)
    except ValueError:
        return val
    if f == 1e-6:
        return r"$1\times10^{-6}$"
    if f == 1e-5:
        return r"$1\times10^{-5}$"
    return val


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig4_sweep_controls"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def manuscript_figure_dir(root: Path) -> Path:
    return root / "manuscript/figures/Figure_4"


def manuscript_panel_dir(root: Path) -> Path:
    return manuscript_figure_dir(root) / "panels"


def load_model_comparison(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / MODEL_COMPARISON, sep="\t")
    df = df.copy()
    df["model_label"] = df["model_id"].map(short_model_label)
    df["plot_color"] = [model_color(row.model_id, row.object_role) for row in df.itertuples()]
    df["is_sweep"] = df["model_id"].str.startswith("gears_hcc_formal_v1_")
    sanity_check_model_scores(df)
    return df


def sanity_check_model_scores(df: pd.DataFrame) -> None:
    baseline = float(df.loc[df["model_id"].eq("shared_mean_baseline"), "backbone_recovery_score"].iloc[0])
    formal = float(df.loc[df["model_id"].eq("gears_hcc_formal_v1"), "backbone_recovery_score"].iloc[0])
    sweep = df.loc[df["model_id"].str.startswith("gears_hcc_formal_v1_")].copy()
    best_sweep = float(sweep["backbone_recovery_score"].max())
    max_shift = float(sweep["shift_excess_identification_score"].max())
    checks = {
        "baseline_backbone": baseline,
        "formal_gears_backbone": formal,
        "best_sweep_backbone": best_sweep,
        "max_sweep_shift_excess": max_shift,
    }
    for key, observed in checks.items():
        if abs(observed - EXPECTED[key]) > 0.02:
            raise RuntimeError(
                f"Fig. 4 sanity check failed for {key}: observed={observed:.4f}, expected={EXPECTED[key]:.4f}"
            )


def load_coverage(root: Path) -> pd.DataFrame:
    rows = []
    for rel in COVERAGE_AUDITS:
        with (root / rel).open() as fh:
            raw = json.load(fh)
        rows.append(
            {
                "model_id": raw["model_id"],
                "cell_line": raw["cell_line"],
                "feature_id": raw["feature_id"],
                "target_vocab_coverage": float(raw["target_vocab_coverage"]),
                "mapped_targets": int(raw["mapped_targets"]),
                "total_targets": int(raw["total_targets"]),
                "fallback_policy": raw.get("fallback_policy", ""),
                "source_path": str(rel),
            }
        )
    out = pd.DataFrame(rows)
    if (out["target_vocab_coverage"] < 0.999).any():
        raise RuntimeError(
            "Fig. 4 coverage sanity check failed: at least one control has coverage below 1.0."
        )
    return out


def load_smoke_summary(root: Path) -> pd.DataFrame:
    return pd.read_csv(root / SMOKE_SUMMARY, sep="\t")


def input_paths(root: Path) -> list[Path]:
    return [
        root / MODEL_COMPARISON,
        root / BACKBONE_DIAGNOSIS,
        root / SMOKE_SUMMARY,
        root / SWEEP_MANIFEST,
        root / SWEEP_ADJUDICATION,
        root / WHY_BASELINE_DOC,
        root / FINAL_CLAIM_MATRIX,
        *[root / p for p in COVERAGE_AUDITS],
    ]


def write_panel(
    *,
    root: Path,
    panel_id: str,
    panel_title: str,
    source_df: pd.DataFrame,
    render: Callable[[plt.Axes, pd.DataFrame], None],
    width: float = 3.3,
    height: float = 2.4,
) -> dict[str, Path]:
    pdir = ensure_dir(panel_dir(root))
    manuscript_pdir = ensure_dir(manuscript_panel_dir(root))
    stem = f"{FIGURE_ID}_panel{panel_id}"
    manuscript_stem = f"Figure_4_panel_{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    manuscript_source_path = write_tsv(source_df, manuscript_pdir / f"{manuscript_stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    png_path = pdir / f"{stem}.png"
    pdf_path = pdir / f"{stem}.pdf"
    output_paths = save_figure(fig, png_path, pdf_path)
    manuscript_png_path = manuscript_pdir / f"{manuscript_stem}.png"
    manuscript_pdf_path = manuscript_pdir / f"{manuscript_stem}.pdf"
    ensure_dir(manuscript_png_path.parent)
    shutil.copy2(png_path, manuscript_png_path)
    shutil.copy2(pdf_path, manuscript_pdf_path)
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


# ---------------------------------------------------------------------------
# Panel a — Pre-specified finite-budget GEARS candidates (table)
# ---------------------------------------------------------------------------


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    add_panel_heading(ax, "", "Pre-specified finite-budget GEARS candidates", title_x=0.00, title_fontsize=8.8)

    recipes = df[df["step"] == "sweep_recipe_entry"].copy()
    recipes = recipes[recipes["model_id"].isin(SWEEP_LETTERS.keys())].copy()
    recipes["epochs"] = pd.to_numeric(recipes["epochs"], errors="coerce").astype(int)
    recipe_by_id = {row["model_id"]: row for _, row in recipes.iterrows()}
    table_rows = []
    table_rows.append(
        {
            "candidate": "GEARS formal",
            "epochs": 30,
            "lr": r"$1\times10^{-3}$",
            "wd": r"$1\times10^{-6}$",
            "role": "reference recipe",
        }
    )
    for mid in SWEEP_LETTER_ORDER:
        row = recipe_by_id[mid]
        letter = SWEEP_LETTERS[mid]
        is_best = mid == BEST_SWEEP_ID
        table_rows.append(
            {
                "candidate": f"{letter} (best)" if is_best else letter,
                "epochs": int(row["epochs"]),
                "lr": _format_lr(str(row["lr"])),
                "wd": _format_wd(str(row["weight_decay"])),
                "role": "best sweep candidate" if is_best else "sweep candidate",
            }
        )

    table_df = pd.DataFrame(table_rows)
    headers = ["Candidate", "Epoch", "LR", "WD", "Role"]
    col_widths = [0.27, 0.10, 0.12, 0.11, 0.31]
    n_rows = len(table_df)
    left_margin = 0.03
    table_top = 0.90
    row_h = 0.105
    col_xs = [left_margin]
    for w in col_widths[:-1]:
        col_xs.append(col_xs[-1] + w)
    table_right = col_xs[-1] + col_widths[-1]
    col_align = [0, 1, 1, 1, 0]
    col_pad = [0.012, 0.0, 0.0, 0.0, 0.012]
    table_left = col_xs[0]
    table_bottom = table_top - row_h * (n_rows + 1)

    for ci, hdr in enumerate(headers):
        rect = plt.Rectangle(
            (col_xs[ci], table_top - row_h),
            col_widths[ci],
            row_h,
            facecolor=F4_COLORS["header_fill"],
            edgecolor=F4_COLORS["cell_edge"],
            linewidth=0.5,
            transform=ax.transAxes,
            zorder=1,
        )
        ax.add_patch(rect)
        x_pos = col_xs[ci] + col_pad[ci] if col_align[ci] == 0 else col_xs[ci] + col_widths[ci] / 2
        ax.text(
            x_pos,
            table_top - row_h / 2,
            hdr,
            ha="left" if col_align[ci] == 0 else "center",
            va="center",
            fontsize=7.5,
            fontweight="bold",
            color=F4_COLORS["text"],
            transform=ax.transAxes,
            zorder=3,
        )

    ax.plot(
        [table_left, table_right],
        [table_top - row_h, table_top - row_h],
        color=F4_COLORS["panel_edge"],
        linewidth=1.0,
        transform=ax.transAxes,
        solid_capstyle="butt",
        zorder=2,
    )

    for ri, row in enumerate(table_df.itertuples()):
        row_bottom = table_top - row_h * (ri + 2)
        cy = row_bottom + row_h / 2
        is_formal = row.candidate == "GEARS formal"
        is_best = row.candidate == "A (best)"
        for ci, value in enumerate([row.candidate, str(row.epochs), row.lr, row.wd, row.role]):
            rect = plt.Rectangle(
                (col_xs[ci], row_bottom),
                col_widths[ci],
                row_h,
                facecolor="white",
                edgecolor=F4_COLORS["cell_edge"],
                linewidth=0.5,
                transform=ax.transAxes,
                zorder=1,
            )
            ax.add_patch(rect)
            x_pos = col_xs[ci] + col_pad[ci] if col_align[ci] == 0 else col_xs[ci] + col_widths[ci] / 2
            is_bold = (is_formal and ci == 0) or (is_best and ci == 0)
            font_size = 7.2 if ci == 4 else 7.5
            ax.text(
                x_pos,
                cy,
                value,
                ha="left" if col_align[ci] == 0 else "center",
                va="center",
                fontsize=font_size,
                fontweight="bold" if is_bold else "normal",
                color=F4_COLORS["text"],
                transform=ax.transAxes,
                zorder=3,
            )

        if is_formal:
            ax.add_patch(
                plt.Rectangle(
                    (table_left + 0.003, row_bottom + 0.01),
                    0.008,
                    row_h - 0.02,
                    facecolor=F4_COLORS["gears"],
                    edgecolor="none",
                    transform=ax.transAxes,
                    zorder=2,
                )
            )

        if ri == 0:
            sep_y = row_bottom
            ax.plot(
                [table_left, table_right],
                [sep_y, sep_y],
                color=F4_COLORS["cell_edge"],
                linewidth=0.75,
                transform=ax.transAxes,
                solid_capstyle="butt",
                zorder=2,
            )



# ---------------------------------------------------------------------------
# Panel b — Unified rebuttal trade-off map (central quantitative panel)
# ---------------------------------------------------------------------------


SWEEP_LETTER_ORDER = [
    "gears_hcc_formal_v1_e30_lr2e-03_wd1e-06",
    "gears_hcc_formal_v1_e20_lr1e-03_wd1e-06",
    "gears_hcc_formal_v1_e30_lr1e-03_wd1e-05",
    "gears_hcc_formal_v1_e30_lr5e-04_wd1e-06",
    "gears_hcc_formal_v1_e40_lr1e-03_wd1e-06",
]
SWEEP_LETTERS = {mid: chr(ord("A") + i) for i, mid in enumerate(SWEEP_LETTER_ORDER)}


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    baseline_x = float(df.loc[df["model_id"].eq("shared_mean_baseline"), "backbone_recovery_score"].iloc[0])
    families = {
        "baseline": [],
        "gears_formal": [],
        "gears_sweep": [],
        "linear": [],
    }
    for row in df.itertuples():
        mid = row.model_id
        if mid == "shared_mean_baseline":
            families["baseline"].append(row)
        elif mid == "gears_hcc_formal_v1":
            families["gears_formal"].append(row)
        elif mid.startswith("gears_hcc_formal_v1_"):
            families["gears_sweep"].append(row)
        elif mid.startswith("lm_"):
            families["linear"].append(row)

    add_panel_heading(
        ax,
        "",
        "Prespecified rebuttal candidates do not close the backbone gap",
        label_x=-0.08,
        title_fontsize=8.8,
    )
    ax.set_xlim(0.45, 0.85)
    ax.set_ylim(0.25, 0.50)
    ax.axvspan(
        baseline_x,
        0.85,
        facecolor=F4_COLORS["shaded"],
        edgecolor="none",
        zorder=0,
    )
    ax.axvline(
        baseline_x,
        color=F4_COLORS["threshold"],
        linestyle=(0, (4, 2)),
        linewidth=1.0,
        zorder=1,
    )

    ax.set_xlabel("Backbone recovery score")
    ax.set_ylabel("Structure / context separation")
    ax.set_xticks([0.45, 0.55, 0.65, 0.75, 0.85])
    ax.set_yticks([0.25, 0.30, 0.35, 0.40, 0.45, 0.50])
    clean_axes(ax)

    for row in families["linear"]:
        ax.scatter(
            row.backbone_recovery_score,
            row.structure_vs_context_separation_score,
            s=MARKER_SIZES["linear"],
            color=F4_COLORS["linear"],
            marker="D",
            edgecolor="none",
            zorder=3,
        )
    for row in families["gears_sweep"]:
        ax.scatter(
            row.backbone_recovery_score,
            row.structure_vs_context_separation_score,
            s=MARKER_SIZES["gears_sweep"],
            color=F4_COLORS["gears_sweep"],
            edgecolor="none",
            zorder=4,
        )
    for row in families["gears_formal"]:
        ax.scatter(
            row.backbone_recovery_score,
            row.structure_vs_context_separation_score,
            s=MARKER_SIZES["gears"],
            color=F4_COLORS["gears"],
            edgecolor="white",
            linewidth=0.6,
            zorder=5,
        )
    for row in families["baseline"]:
        ax.scatter(
            row.backbone_recovery_score,
            row.structure_vs_context_separation_score,
            s=MARKER_SIZES["baseline"],
            color=F4_COLORS["baseline"],
            edgecolor="white",
            linewidth=0.6,
            zorder=6,
        )

    for row in families["baseline"]:
        ax.text(
            row.backbone_recovery_score - 0.014,
            row.structure_vs_context_separation_score + 0.004,
            "shared mean\nbaseline (0.807)",
            fontsize=7.0,
            fontweight="bold",
            ha="right",
            va="center",
            color=F4_COLORS["text"],
            zorder=7,
        )
    for row in families["gears_formal"]:
        ax.text(
            row.backbone_recovery_score + 0.012,
            row.structure_vs_context_separation_score + 0.004,
            "GEARS formal\n(0.660)",
            fontsize=7.0,
            fontweight="bold",
            ha="left",
            va="center",
            color=F4_COLORS["text"],
            zorder=7,
        )

    letter_offsets = {
        "gears_hcc_formal_v1_e30_lr2e-03_wd1e-06": (0.004, 0.008),
        "gears_hcc_formal_v1_e20_lr1e-03_wd1e-06": (0.005, 0.006),
        "gears_hcc_formal_v1_e30_lr1e-03_wd1e-05": (0.005, -0.010),
        "gears_hcc_formal_v1_e30_lr5e-04_wd1e-06": (0.005, 0.006),
        "gears_hcc_formal_v1_e40_lr1e-03_wd1e-06": (-0.005, 0.008),
    }
    for row in families["gears_sweep"]:
        letter = SWEEP_LETTERS.get(row.model_id)
        if letter is None:
            continue
        dx, dy = letter_offsets.get(row.model_id, (0.004, 0.006))
        ha = "left" if dx >= 0 else "right"
        label = f"{letter} (best)" if row.model_id == BEST_SWEEP_ID else letter
        ax.text(
            row.backbone_recovery_score + dx,
            row.structure_vs_context_separation_score + dy,
            label,
            fontsize=7.0,
            color=F4_COLORS["text"],
            fontweight="bold",
            ha=ha,
            va="bottom" if dy >= 0 else "top",
            zorder=7,
        )

    handles = [
        Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            color=F4_COLORS["baseline"],
            markersize=5.0,
            label="shared mean baseline",
        ),
        Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            color=F4_COLORS["gears"],
            markersize=4.4,
            label="GEARS formal",
        ),
        Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            color=F4_COLORS["gears_sweep"],
            markersize=3.7,
            label="sweeps A\u2013E",
        ),
        Line2D(
            [],
            [],
            marker="D",
            linestyle="",
            color=F4_COLORS["linear"],
            markersize=3.6,
            label="linear controls",
        ),
    ]
    ax.legend(
        handles=handles,
        loc="center left",
        bbox_to_anchor=(1.02, 0.42),
        frameon=False,
        fontsize=7.2,
        handletextpad=0.35,
        labelspacing=0.35,
        borderpad=0.2,
        ncol=1,
        columnspacing=0.8,
    )
    best_sweep_x = max(r.backbone_recovery_score for r in families["gears_sweep"])
    bracket_y = 0.262
    delta_display = round(baseline_x, 3) - round(best_sweep_x, 3)
    ax.annotate(
        "",
        xy=(baseline_x, bracket_y),
        xytext=(best_sweep_x, bracket_y),
        arrowprops={
            "arrowstyle": "<->",
            "linewidth": 0.75,
            "color": F4_COLORS["text"],
            "shrinkA": 0,
            "shrinkB": 0,
        },
        zorder=7,
    )
    ax.text(
        (best_sweep_x + baseline_x) / 2,
        bracket_y + 0.006,
        f"gap = {delta_display:.3f}",
        ha="center",
        va="bottom",
        fontsize=7.5,
        fontweight="bold",
        color=F4_COLORS["text"],
        zorder=7,
    )
    ax.text(
        baseline_x + 0.012,
        0.488,
        "baseline boundary",
        fontsize=7.0,
        color=F4_COLORS["threshold"],
        ha="left",
        va="top",
        zorder=7,
    )



def _facet_marker(model_id: str) -> str:
    if model_id in LINEAR_CONTROL_IDS:
        return "D"
    return "o"


def _facet_color(model_id: str) -> str:
    if model_id == "gears_hcc_formal_v1":
        return F4_COLORS["gears"]
    if model_id == BEST_SWEEP_ID:
        return F4_COLORS["gears_sweep"]
    return F4_COLORS["linear"]


def _facet_size(model_id: str) -> float:
    if model_id == "gears_hcc_formal_v1":
        return MARKER_SIZES["gears"]
    if model_id == BEST_SWEEP_ID:
        return MARKER_SIZES["gears_sweep"]
    return MARKER_SIZES["linear"]


def _facet_zorder(model_id: str) -> float:
    if model_id == "gears_hcc_formal_v1":
        return 4.2
    if model_id == BEST_SWEEP_ID:
        return 3.8
    return 3.2


def _render_c_facet(
    facet_ax: plt.Axes,
    pivot: pd.DataFrame,
    ordered_ids: list[str],
    labels: dict[str, str],
    cell_line: str,
    *,
    show_labels: bool,
    x_min: float,
    x_max: float,
) -> None:
    y_positions = {mid: len(ordered_ids) - 1 - idx for idx, mid in enumerate(ordered_ids)}
    facet_ax.axvline(
        0,
        color=F4_COLORS["threshold"],
        linewidth=1.0,
        linestyle=(0, (4, 2)),
        zorder=1,
    )
    for y in y_positions.values():
        facet_ax.axhline(y, color=F4_COLORS["grid"], linewidth=0.5, zorder=0)

    for mid in ordered_ids:
        y = y_positions[mid]
        val = float(pivot.loc[mid, cell_line])
        facet_ax.plot(
            [min(val, 0), max(val, 0)],
            [y, y],
            color="#D0D0D0",
            linewidth=0.75,
            solid_capstyle="butt",
            zorder=2,
        )
        facet_ax.scatter(
            val,
            y,
            s=_facet_size(mid),
            marker=_facet_marker(mid),
            color=_facet_color(mid),
            edgecolor="white",
            linewidth=0.6,
            zorder=_facet_zorder(mid),
        )
        facet_ax.annotate(
            f"{val:+.3f}",
            xy=(val, y),
            xytext=(4, -4),
            textcoords="offset points",
            ha="left",
            va="top",
            fontsize=7.5,
            fontweight="bold",
            color=F4_COLORS["text"],
            zorder=4,
        )
    facet_ax.set_xlim(x_min, x_max)
    facet_ax.set_ylim(-0.5, len(ordered_ids) - 0.5)
    facet_ax.set_xticks([-0.40, -0.30, -0.20, -0.10, 0.00])
    facet_ax.set_yticks(list(y_positions.values()))
    facet_ax.set_yticklabels(
        [labels[mid] for mid in ordered_ids] if show_labels else [""] * len(ordered_ids),
        fontsize=7.5,
    )
    facet_ax.set_xlabel("\u0394 backbone recovery vs baseline", fontsize=7.5, labelpad=2)
    facet_ax.set_title(cell_line, fontsize=9, fontweight="bold", pad=0)
    facet_ax.tick_params(axis="y", labelleft=show_labels, left=True, length=2.2, width=0.6)
    clean_axes(facet_ax)


# ---------------------------------------------------------------------------
# Panel c — Dumbbell delta plot of backbone gap summary
# ---------------------------------------------------------------------------


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    add_panel_heading(
        ax,
        "",
        "No tested rebuttal candidate closes the backbone gap to the shared-mean baseline",
        title_x=0.00,
        title_fontsize=8.8,
    )

    pivot = df.pivot(index="model_id", columns="cell_line", values="delta_backbone")
    ordered_ids = [
        "gears_hcc_formal_v1",
        BEST_SWEEP_ID,
        "lm_g_scgpt_ridge_hcc_formal_v1",
        "lm_g_geneformer_ridge_hcc_formal_v1",
        "lm_train_lowrank_hcc_formal_v1",
    ]
    labels = {
        "gears_hcc_formal_v1": "GEARS formal",
        BEST_SWEEP_ID: "Best GEARS sweep candidate",
        "lm_g_scgpt_ridge_hcc_formal_v1": "scGPT-ridge control",
        "lm_g_geneformer_ridge_hcc_formal_v1": "Geneformer-ridge control",
        "lm_train_lowrank_hcc_formal_v1": "Low-rank decoder",
    }
    ax_hcc38 = ax.inset_axes([0.11, 0.18, 0.37, 0.68])
    ax_hcc1143 = ax.inset_axes([0.56, 0.18, 0.37, 0.68])
    x_min = min(float(pivot["HCC38"].min()), float(pivot["HCC1143"].min())) * 1.12
    x_max = 0.02
    _render_c_facet(
        ax_hcc38,
        pivot,
        ordered_ids,
        labels,
        "HCC38",
        show_labels=True,
        x_min=x_min,
        x_max=x_max,
    )
    _render_c_facet(
        ax_hcc1143,
        pivot,
        ordered_ids,
        labels,
        "HCC1143",
        show_labels=False,
        x_min=x_min,
        x_max=x_max,
    )



# ---------------------------------------------------------------------------
# Source-data builders
# ---------------------------------------------------------------------------


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    model = load_model_comparison(root)
    manifest = pd.read_csv(root / SWEEP_MANIFEST, sep="\t")
    coverage = load_coverage(root)
    smoke = load_smoke_summary(root)

    rebuttal_ids = (
        ["shared_mean_baseline", "gears_hcc_formal_v1"]
        + list(model.loc[model["is_sweep"], "model_id"])
        + LINEAR_CONTROL_IDS
    )
    unified = model.loc[model["model_id"].isin(rebuttal_ids)].copy()

    # Panel a source: candidate table data
    design_rows = [
        {
            "step_order": 1,
            "step": "pre_specified_neighborhood",
            "detail": "GEARS hyperparameter neighborhood defined in advance",
        },
        {
            "step_order": 2,
            "step": "finite_sweep_budget",
            "detail": "limited candidate set, no open-ended search",
        },
        {
            "step_order": 3,
            "step": "truth_and_scoring_unchanged",
            "detail": "truth object and scoring system fixed",
        },
        {
            "step_order": 4,
            "step": "check_gap_closure",
            "detail": "compare sweep candidates to shared-mean baseline",
        },
        {
            "step_order": 5,
            "step": "stop_if_gap_remains",
            "detail": "stop rule triggered when baseline backbone gap remains open",
        },
    ]
    design_df = pd.DataFrame(design_rows)
    sweep_recipe = manifest[[
        "variant_id",
        "epochs",
        "lr",
        "weight_decay",
        "candidate_rank",
        "model_id",
        "config_path",
    ]].copy()
    sweep_recipe.insert(0, "step_order", 0)
    sweep_recipe.insert(1, "step", "sweep_recipe_entry")
    sweep_recipe["detail"] = (
        "epochs="
        + sweep_recipe["epochs"].astype(str)
        + ", lr="
        + sweep_recipe["lr"].astype(str)
        + ", wd="
        + sweep_recipe["weight_decay"].astype(str)
    )
    panel_a_source = pd.concat(
        [
            design_df,
            sweep_recipe[["step_order", "step", "detail", "variant_id", "epochs", "lr", "weight_decay", "candidate_rank", "model_id", "config_path"]],
        ],
        ignore_index=True,
        sort=False,
    )

    panel_b_source = unified[
        [
            "model_id",
            "model_label",
            "plot_color",
            "backbone_recovery_score",
            "structure_vs_context_separation_score",
            "shift_excess_identification_score",
            "is_sweep",
            "object_role",
        ]
    ].copy()

    # Panel c source: forest plot data (per-context delta to baseline)
    FOREST_IDS = [
        "gears_hcc_formal_v1",
        BEST_SWEEP_ID,
        "lm_g_scgpt_ridge_hcc_formal_v1",
        "lm_g_geneformer_ridge_hcc_formal_v1",
        "lm_train_lowrank_hcc_formal_v1",
    ]
    FOREST_LABELS = {
        "gears_hcc_formal_v1": "GEARS formal",
        BEST_SWEEP_ID: "Best GEARS sweep candidate",
        "lm_g_scgpt_ridge_hcc_formal_v1": "scGPT-ridge control",
        "lm_g_geneformer_ridge_hcc_formal_v1": "Geneformer-ridge control",
        "lm_train_lowrank_hcc_formal_v1": "Low-rank decoder",
    }

    forest = smoke.loc[smoke["model_id"].isin(FOREST_IDS)].copy()
    baseline_by_context = (
        smoke.loc[smoke["model_id"] == "shared_mean_baseline"]
        .set_index("cell_line")["backbone_recovery_score"]
        .to_dict()
    )
    forest["baseline_backbone"] = forest["cell_line"].map(baseline_by_context)
    forest["delta_backbone"] = forest["backbone_recovery_score"] - forest["baseline_backbone"]
    forest["display_label"] = forest["model_id"].map(FOREST_LABELS)
    forest["sort_order"] = forest["model_id"].map({mid: i for i, mid in enumerate(FOREST_IDS)})
    panel_c_source = (
        forest.sort_values("sort_order")[
            [
                "model_id",
                "display_label",
                "cell_line",
                "backbone_recovery_score",
                "baseline_backbone",
                "delta_backbone",
            ]
        ]
        .copy()
    )

    return {
        "a": panel_a_source,
        "b": panel_b_source,
        "c": panel_c_source,
    }


def render_panel_by_id(panel_id: str) -> Callable[[plt.Axes, pd.DataFrame], None]:
    return {
        "a": render_panel_a,
        "b": render_panel_b,
        "c": render_panel_c,
    }[panel_id]


def panel_title(panel_id: str) -> str:
    return {
        "a": "Pre-specified finite-budget GEARS candidates",
        "b": "Prespecified rebuttal candidates do not close the backbone gap",
        "c": "No tested rebuttal candidate closes the backbone gap to the shared-mean baseline",
    }[panel_id]


PANEL_IDS: list[str] = ["a", "b", "c"]


def render_combined(
    root: Path,
    sources: dict[str, pd.DataFrame],
    panel_outputs: dict[str, dict[str, Path]],
) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    manuscript_out = ensure_dir(manuscript_figure_dir(root))
    combined_source = pd.concat(
        [df.assign(panel=panel_id) for panel_id, df in sources.items()],
        ignore_index=True,
        sort=False,
    )
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")
    manuscript_source_path = write_tsv(combined_source, manuscript_out / "Figure_4_source_data.tsv")

    fig = plt.figure(figsize=(9.6, 6.9))
    outer = fig.add_gridspec(
        2,
        1,
        height_ratios=[0.92, 1.02],
        hspace=0.28,
        left=0.060,
        right=0.975,
        top=0.950,
        bottom=0.088,
    )
    top = outer[0].subgridspec(1, 2, width_ratios=[0.90, 1.0], wspace=0.18)
    ax_a = fig.add_subplot(top[0, 0])
    ax_b = fig.add_subplot(top[0, 1])
    ax_c = fig.add_subplot(outer[1])

    render_panel_a(ax_a, sources["a"])
    render_panel_b(ax_b, sources["b"])
    render_panel_c(ax_c, sources["c"])

    png_path = out / f"{FIGURE_ID}.png"
    pdf_path = out / f"{FIGURE_ID}.pdf"
    output_paths = save_figure(fig, png_path, pdf_path)
    manuscript_png = manuscript_out / "Figure_4.png"
    manuscript_pdf = manuscript_out / "Figure_4.pdf"
    shutil.copy2(png_path, manuscript_png)
    shutil.copy2(pdf_path, manuscript_pdf)

    manifest_path = out / f"{FIGURE_ID}_panel_manifest.json"
    write_figure_manifest(
        manifest_path=manifest_path,
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
    write_figure_manifest(
        manifest_path=manuscript_out / "Figure_4_panel_manifest.json",
        repo_root=root,
        figure_id=FIGURE_ID,
        figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[
            manuscript_panel_dir(root) / f"Figure_4_panel_{p}_manifest.json"
            for p in PANEL_IDS
        ],
        combined_source_data_path=manuscript_source_path,
        output_paths=[manuscript_png, manuscript_pdf],
        input_paths=input_paths(root),
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": combined_source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build manuscript Figure 4 (local rebuttal / boundary figure).")
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    apply_manuscript_style()
    sources = build_sources(root)
    panel_outputs: dict[str, dict[str, Path]] = {}
    panel_dims = {
        "a": (5.2, 3.0),
        "b": (7.4, 4.6),
        "c": (9.0, 3.6),
    }
    for panel_id in PANEL_IDS:
        w, h = panel_dims[panel_id]
        panel_outputs[panel_id] = write_panel(
            root=root,
            panel_id=panel_id,
            panel_title=panel_title(panel_id),
            source_df=sources[panel_id],
            render=render_panel_by_id(panel_id),
            width=w,
            height=h,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
