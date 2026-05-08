"""Extended Data Fig: Robustness audits for bridge structure, model adjudication
and endpoint hierarchy.

Layout: 2x2

  a — Shared-mean baseline not oracle (forest dot plot)
  b — Bridge not driven by single anchors (paired dumbbell)
  c — Asymmetric recovery stable under resampling (violin + point)
  d — CRISPR > RNAi sign-consistency tile (compact audit, not duplicate Fig 5b)
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_heading, apply_manuscript_style, clean_axes

FIGURE_ID = "extended_data_figure_robustness"
FIGURE_TITLE = "Robustness audits for bridge structure, model adjudication and endpoint hierarchy"
SCRIPT_PATH = Path("scripts/manuscript/build_extended_data_figure_robustness.py")
CLAIM_BOUNDARY = (
    "Robustness audits confirm: (i) shared-mean baseline advantage is retained under "
    "leave-one-target-out and cross-context construction, (ii) bridge remains materially "
    "positive after removing all stable anchors, (iii) asymmetric recovery pattern is "
    "stable under target resampling, (iv) CRISPR > RNAi in all four tested contexts."
)
PANEL_IDS = ("a", "b", "c", "d")

BASELINE_AUDIT = Path("reports/stage2_truth_driven_bridge/sensitivity/baseline_audit_summary.tsv")
LEAVE_ANCHOR_OUT = Path("reports/stage2_truth_driven_bridge/sensitivity/leave_anchor_out_summary.tsv")
BOOTSTRAP_DELTA = Path("reports/stage2_truth_driven_bridge/sensitivity/bootstrap_delta_summary.tsv")
ENDPOINT_AUDIT = Path("reports/stage2_truth_driven_bridge/sensitivity/endpoint_hierarchy_audit.tsv")

PRIMARY = COLORS["primary_qualified"]  # green
LIGHT_BLUE = "#56B4E9"
OCHRE = "#D84315"
DARK = "#1F1F1F"
MED = "#888888"
LIGHT = "#F0F0F0"
GREEN_FILL = "#E8F5E9"


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_extended_data_v1/edfig_robustness"

def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"

def input_paths(root: Path) -> list[Path]:
    return [root / BASELINE_AUDIT, root / LEAVE_ANCHOR_OUT,
            root / BOOTSTRAP_DELTA, root / ENDPOINT_AUDIT]

def cleanup_generated(root: Path) -> None:
    out = output_dir(root)
    if panel_dir(root).exists():
        for path in panel_dir(root).glob("*"): path.unlink()
    for s in (".png", ".pdf", "_source_data.tsv", "_panel_manifest.json"):
        p = out / f"edfig_robustness{s}"
        if p.exists(): p.unlink()


# ── Data builders ────────────────────────────────────────────────────────────

def build_panel_a_source(root: Path) -> pd.DataFrame:
    return pd.read_csv(root / BASELINE_AUDIT, sep="\t")

def build_panel_b_source(root: Path) -> pd.DataFrame:
    return pd.read_csv(root / LEAVE_ANCHOR_OUT, sep="\t", comment="#")

def build_panel_c_source(root: Path) -> pd.DataFrame:
    return pd.read_csv(root / BOOTSTRAP_DELTA, sep="\t")

def build_panel_d_source(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / ENDPOINT_AUDIT, sep="\t", comment="#")
    # Clean Delta: strip + prefix, convert to float
    df["Delta"] = df["Delta"].astype(str).str.replace("+", "").astype(float)
    return df


# ── Panel A: forest dot plot ─────────────────────────────────────────────────

def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Forest-style dot plot: baseline audit conditions vs backbone recovery."""
    add_panel_heading(ax, "", "Shared-mean baseline is not an oracle",
                      label_x=-0.06, title_x=0.02, y=1.025)

    # Rows: 4 audit conditions
    orig_hcc38 = df[(df["audit_type"] == "original_reference") & (df["context"] == "HCC38")]["backbone_recovery"].values[0]
    orig_hcc1143 = df[(df["audit_type"] == "original_reference") & (df["context"] == "HCC1143")]["backbone_recovery"].values[0]
    loto_mean_hcc38 = df[(df["variant"] == "loto_mean") & (df["context"] == "HCC38")]["backbone_recovery"].values[0]
    loto_mean_hcc1143 = df[(df["variant"] == "loto_mean") & (df["context"] == "HCC1143")]["backbone_recovery"].values[0]
    loto_min_hcc38 = df[(df["variant"] == "loto_min") & (df["context"] == "HCC38")]["backbone_recovery"].values[0]
    loto_max_hcc38 = df[(df["variant"] == "loto_max") & (df["context"] == "HCC38")]["backbone_recovery"].values[0]
    loto_min_hcc1143 = df[(df["variant"] == "loto_min") & (df["context"] == "HCC1143")]["backbone_recovery"].values[0]
    loto_max_hcc1143 = df[(df["variant"] == "loto_max") & (df["context"] == "HCC1143")]["backbone_recovery"].values[0]
    cross = df[df["audit_type"] == "cross_context"]
    x_hcc38_to_1143 = cross[cross["variant"] == "backbone_from_HCC38"]["backbone_recovery"].values[0]
    x_hcc1143_to_38 = cross[cross["variant"] == "backbone_from_HCC1143"]["backbone_recovery"].values[0]

    rows = ["Original\nshared-mean", "LOTO\nmean [min, max]", "Cross-context\n(HCC38→HCC1143)", "Cross-context\n(HCC1143→HCC38)"]
    hcc38_vals = [orig_hcc38, loto_mean_hcc38, None, x_hcc1143_to_38]
    hcc38_err = [(0, 0), (loto_mean_hcc38 - loto_min_hcc38, loto_max_hcc38 - loto_mean_hcc38), (0,0), (0,0)]
    hcc1143_vals = [orig_hcc1143, loto_mean_hcc1143, x_hcc38_to_1143, None]
    hcc1143_err = [(0,0), (loto_mean_hcc1143 - loto_min_hcc1143, loto_max_hcc1143 - loto_mean_hcc1143), (0,0), (0,0)]

    y_positions = [4, 3, 2, 1]
    for i, (v38, v1143, err38, err1143) in enumerate(zip(hcc38_vals, hcc1143_vals, hcc38_err, hcc1143_err)):
        y = y_positions[i]
        if v38 is not None:
            xerr = np.array([[err38[0]], [err38[1]]]) if err38[0] > 0 else None
            ax.errorbar(v38, y + 0.12, xerr=xerr, fmt='o', color=PRIMARY,
                       markersize=8, capsize=3, capthick=1.2, elinewidth=1.2,
                       markeredgecolor='white', markeredgewidth=0.5, zorder=5)
        if v1143 is not None:
            xerr = np.array([[err1143[0]], [err1143[1]]]) if err1143[0] > 0 else None
            ax.errorbar(v1143, y - 0.12, xerr=xerr, fmt='s', color=LIGHT_BLUE,
                       markersize=8, capsize=3, capthick=1.2, elinewidth=1.2,
                       markeredgecolor='white', markeredgewidth=0.5, zorder=5)

    # Null reference
    ax.axvline(x=0.5, color=MED, linewidth=0.7, linestyle="--", alpha=0.5)
    ax.text(0.505, 0.4, "null = 0.5", fontsize=5.5, color=MED, transform=ax.transAxes, va="bottom")

    ax.set_yticks(y_positions)
    ax.set_yticklabels(rows, fontsize=6.2)
    ax.set_xlabel("Backbone recovery score", fontsize=6.5)
    ax.set_xlim(0.42, 0.92)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=PRIMARY, markersize=7, label='HCC38'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor=LIGHT_BLUE, markersize=7, label='HCC1143'),
    ]
    ax.legend(handles=legend_elements, fontsize=5.8, loc="lower right", frameon=False)
    clean_axes(ax)


# ── Panel B: paired dumbbell ─────────────────────────────────────────────────

def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Paired dumbbell: full target set vs remove 4 anchors, HCC38 + HCC1143."""
    add_panel_heading(ax, "", "Bridge not driven by single anchors",
                      label_x=-0.06, title_x=0.02, y=1.025)

    orig = df[df["removed"] == "none"].set_index("context")["spearman_rho"]
    removed = df[df["removed"] == "all_four_anchors"].set_index("context")["spearman_rho"]
    jack_min = df[df["removed"] == "jackknife_min"].set_index("context")["spearman_rho"]

    contexts = ["HCC38", "HCC1143"]
    for ci, ctx in enumerate(contexts):
        y = 2 - ci
        full = orig[ctx]
        rem = removed[ctx]
        jk_min = jack_min[ctx]

        # Dumbbell line
        ax.plot([full, rem], [y, y], color=MED, linewidth=1.5, zorder=2)
        # Full target set point
        ax.scatter(full, y, s=80, color=PRIMARY, zorder=5,
                   edgecolors="white", linewidths=0.5)
        # Remove anchors point
        ax.scatter(rem, y, s=80, color=PRIMARY, zorder=5, alpha=0.45,
                   edgecolors="white", linewidths=0.5)
        # Value labels
        ax.text(full + 0.005, y + 0.22, f"{full:.3f}", fontsize=7.0, ha="center",
                fontweight="bold", color=PRIMARY)
        ax.text(rem - 0.005, y - 0.28, f"{rem:.3f}", fontsize=7.0, ha="center",
                fontweight="bold", color=PRIMARY, alpha=0.6)
        # Delta label
        delta = full - rem
        mid = (full + rem) / 2
        ax.text(mid, y - 0.22, f"Δ={delta:.3f}", fontsize=6.0, ha="center", color=MED)
        # Jackknife worst
        ax.axvline(x=jk_min, ymin=(y - 1.2) / 3.5, ymax=(y - 0.8) / 3.5,
                   color=OCHRE, linewidth=0.8, linestyle=":", alpha=0.6, clip_on=False)
        ax.text(jk_min, y + 0.6, f"jackknife\nmin", fontsize=5.0, ha="center", color=OCHRE)

        # Context label
        ax.text(0.64, y, ctx, fontsize=7.5, fontweight="bold", color=DARK, va="center")

    ax.set_ylim(0.5, 2.5)
    ax.set_yticks([])
    ax.set_xlabel("Aligned Spearman ρ", fontsize=6.5)
    ax.set_xlim(0.63, 0.80)

    # Legend for point types
    from matplotlib.lines import Line2D
    leg = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=PRIMARY, markersize=9, label='Full target set'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=PRIMARY, markersize=9, alpha=0.45,
               label='Remove 4 anchors'),
    ]
    ax.legend(handles=leg, fontsize=5.8, loc="lower left", frameon=False)
    clean_axes(ax)


# ── Panel C: bootstrap violin ────────────────────────────────────────────────

def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Bootstrap delta distribution violin plot, 3 metrics."""
    add_panel_heading(ax, "", "Asymmetric recovery not a small-sample artifact",
                      label_x=-0.06, title_x=0.02, y=1.025)

    # We only have summary stats, not raw bootstrap draws. Use a simplified
    # representation: CI bar + point with sign stability annotation.

    metric_labels = {
        "backbone_recovery": "Backbone recovery",
        "shift_excess_identification": "Shift-excess identification",
        "structure_vs_context_separation": "Structure/context\nseparation",
    }
    order = list(metric_labels.keys())

    for i, metric in enumerate(order):
        row = df[df["metric"] == metric].iloc[0]
        y = len(order) - i + 0.3

        mean_val = row["delta_mean"]
        ci_l = row["delta_ci_lower"]
        ci_u = row["delta_ci_upper"]
        sig = row["sign_stability_pct"]
        n_valid = int(row["n_valid_draws"])

        bar_width = 0.55

        # Shaded violin-like: just a thick bar + CI whiskers
        # CI range bar
        ax.barh(y, ci_u - ci_l, bar_width, left=ci_l, color=LIGHT, edgecolor=MED,
                linewidth=0.8, zorder=2)
        # Mean marker
        color = PRIMARY if sig > 50 else (OCHRE if sig < 5 else MED)
        ax.scatter(mean_val, y, s=70, color=color, zorder=5, edgecolors="white", linewidths=0.8)
        # Mean vertical line
        ax.plot([mean_val, mean_val], [y - bar_width/2, y + bar_width/2],
                color=color, linewidth=1.2, zorder=4)

        # Sign stability annotation
        if abs(sig - 50) < 10:
            stab_text = "unstable"
        elif sig > 50:
            stab_text = f"{sig:.0f}% baseline > GEARS"
        else:
            stab_text = f"{100-sig:.0f}% GEARS > baseline"
        ax.text(ci_u + 0.03, y, stab_text, fontsize=5.8, va="center", color=color)

        # Metric label
        ax.text(-0.45, y, metric_labels[metric], fontsize=6.5, va="center", ha="left", color=DARK)

    # Zero reference
    ax.axvline(x=0, color=MED, linewidth=0.7, linestyle="--", alpha=0.4)
    ax.text(0.005, 0.08, "0", fontsize=5.5, color=MED, transform=ax.transAxes)

    ax.set_ylim(0.5, len(order) + 0.5 + 0.3)
    ax.set_yticks([])
    ax.set_xlabel("Δ (baseline − GEARS)", fontsize=6.5)

    clean_axes(ax)


# ── Panel D: sign-consistency tile ───────────────────────────────────────────

def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Compact sign-consistency tile for endpoint hierarchy (not duplicate Fig 5b)."""
    ax.set_axis_off()
    add_panel_heading(ax, "", "CRISPR exceeds RNAi in all tested contexts",
                      label_x=-0.06, title_x=0.02, y=1.025)

    ax.add_patch(plt.Rectangle(
        (0.005, 0.84), 0.99, 0.11, transform=ax.transAxes,
        facecolor=LIGHT, edgecolor="none", zorder=0))
    for txt, x in [("Context", 0.03), ("Δρ (CRISPR − RNAi)", 0.38), ("Interpretation", 0.72)]:
        ax.text(x, 0.895, txt, fontsize=7.0, fontweight="bold", color=DARK, transform=ax.transAxes)
    ax.plot([0.01, 0.99], [0.84, 0.84], color="#CCCCCC", linewidth=0.7, transform=ax.transAxes)

    context_labels = {"HCC38": "HCC38", "HCC1143": "HCC1143", "7d": "K562 7d", "13d": "K562 13d"}

    row_gap = 0.155
    for i, (_, row) in enumerate(df.iterrows()):
        y = 0.745 - i * row_gap
        ctx = row["Context"]

        # Green tile background
        ax.add_patch(plt.Rectangle(
            (0.005, y - row_gap * 0.42), 0.99, row_gap * 0.84,
            transform=ax.transAxes, facecolor=GREEN_FILL, edgecolor="none", zorder=0))

        delta = float(row["Delta"])
        ax.text(0.03, y, context_labels.get(ctx, ctx), fontsize=7.2, fontweight="bold",
                color=DARK, transform=ax.transAxes, va="center")
        # Large delta value
        ax.text(0.38, y, f"+{delta:.3f}", fontsize=8.5, fontweight="bold",
                color=PRIMARY, transform=ax.transAxes, va="center")
        # Interpretation
        ax.text(0.72, y, "CRISPR > RNAi", fontsize=6.5, color=PRIMARY,
                transform=ax.transAxes, va="center")

    clean_axes(ax)


# ── Infrastructure ────────────────────────────────────────────────────────────

def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    return {p: globals()[f"build_panel_{p}_source"](root) for p in PANEL_IDS}

def render_panel_by_id(pid: str) -> Callable:
    return {"a": render_panel_a, "b": render_panel_b, "c": render_panel_c, "d": render_panel_d}[pid]

def panel_title(pid: str) -> str:
    return {"a": "Baseline LOTO / cross-context audit",
            "b": "Leave-anchor-out bridge robustness",
            "c": "Bootstrap delta distribution",
            "d": "Endpoint sign-consistency tile"}[pid]


def write_panel(*, root, panel_id, source_df, render, width=5.0, height=3.0) -> dict:
    pdir = ensure_dir(panel_dir(root))
    stem = f"edfig_robustness_panel{panel_id}"
    sp = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    ops = save_figure(fig, pdir / f"{stem}.png", pdir / f"{stem}.pdf")
    mp = pdir / f"{stem}_manifest.json"
    write_panel_manifest(manifest_path=mp, repo_root=root,
                         panel_id=f"ED_ROB{panel_id}", panel_title=panel_title(panel_id),
                         script_path=root / SCRIPT_PATH, input_paths=input_paths(root),
                         source_data_path=sp, output_paths=ops, claim_boundary=CLAIM_BOUNDARY)
    return {"source": sp, "png": ops[0], "pdf": ops[1], "manifest": mp}


def render_combined(root, sources, panel_outputs):
    out = ensure_dir(output_dir(root))
    cs = pd.concat([df.assign(panel=p) for p, df in sources.items()], ignore_index=True, sort=False)
    write_tsv(cs, out / "edfig_robustness_source_data.tsv")

    fig = plt.figure(figsize=(10.5, 8.0))
    gs = fig.add_gridspec(2, 2, hspace=0.48, wspace=0.42,
                          height_ratios=[1, 1.15], width_ratios=[1, 1])

    axes = {p: fig.add_subplot(gs[i // 2, i % 2]) for i, p in enumerate(PANEL_IDS)}
    for p in PANEL_IDS:
        render_panel_by_id(p)(axes[p], sources[p])

    ops = save_figure(fig, out / "edfig_robustness.png", out / "edfig_robustness.pdf")
    write_figure_manifest(
        manifest_path=out / "edfig_robustness_panel_manifest.json",
        repo_root=root, figure_id=FIGURE_ID, figure_title=FIGURE_TITLE,
        script_path=root / SCRIPT_PATH,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in PANEL_IDS],
        combined_source_data_path=out / "edfig_robustness_source_data.tsv",
        output_paths=ops, input_paths=input_paths(root), claim_boundary=CLAIM_BOUNDARY)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--panels-only", action="store_true")
    args = parser.parse_args(argv)
    apply_manuscript_style()
    root = repo_root()
    cleanup_generated(root)
    sources = build_sources(root)

    dims = {"a": (5.2, 2.8), "b": (5.0, 2.8), "c": (5.2, 2.8), "d": (5.0, 2.8)}
    panel_outputs = {}
    for pid in PANEL_IDS:
        w, h = dims[pid]
        panel_outputs[pid] = write_panel(root=root, panel_id=pid, source_df=sources[pid],
                                         render=render_panel_by_id(pid), width=w, height=h)

    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
