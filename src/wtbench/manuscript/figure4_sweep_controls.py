from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import (
    COLORS,
    add_panel_label,
    apply_manuscript_style,
    clean_axes,
    model_color,
    short_model_label,
)


FIGURE_ID = "figure4"
FIGURE_TITLE = "Recipe and embedding controls do not close the backbone gap"
SCRIPT_PATH = Path("scripts/manuscript/build_figure4_sweep_controls.py")
CLAIM_BOUNDARY = (
    "Finite GEARS recipe variation and embedding controls do not close the backbone gap; "
    "GEARS training is not rerun during figure production."
)

MODEL_COMPARISON = Path("reports/stage2_real_hcc_smoke/model_comparison.tsv")
BACKBONE_DIAGNOSIS = Path("reports/stage2_real_hcc_smoke/backbone_diagnosis.tsv")
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


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig4_sweep_controls"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


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
            raise RuntimeError(f"Fig. 4 sanity check failed for {key}: observed={observed:.4f}, expected={EXPECTED[key]:.4f}")


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
        raise RuntimeError("Fig. 4 coverage sanity check failed: at least one control has coverage below 1.0.")
    return out


def input_paths(root: Path) -> list[Path]:
    return [
        root / MODEL_COMPARISON,
        root / BACKBONE_DIAGNOSIS,
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


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.sort_values("backbone_recovery_score", ascending=True)
    y = np.arange(len(plot))
    ax.barh(y, plot["backbone_recovery_score"], color=plot["plot_color"], height=0.62)
    ax.axvline(EXPECTED["baseline_backbone"], color=COLORS["baseline"], linestyle="--", linewidth=0.8)
    ax.text(EXPECTED["baseline_backbone"] + 0.006, len(plot) - 0.25, "shared baseline", fontsize=6, va="top")
    ax.set_yticks(y)
    ax.set_yticklabels(plot["model_label"].str.replace("\n", " ", regex=False))
    ax.set_xlim(0.45, 0.84)
    ax.set_xlabel("Backbone recovery")
    ax.set_title("No GEARS sweep candidate reaches the baseline", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "a", x=-0.28)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    for row in df.itertuples():
        edge = "#000000" if row.model_id in {"shared_mean_baseline", "gears_hcc_formal_v1"} else "white"
        size = 55 if row.model_id in {"shared_mean_baseline", "gears_hcc_formal_v1"} else 42
        ax.scatter(
            row.backbone_recovery_score,
            row.structure_vs_context_separation_score,
            color=row.plot_color,
            edgecolor=edge,
            linewidth=0.6,
            s=size,
        )
        if row.model_id in {"shared_mean_baseline", "gears_hcc_formal_v1"}:
            ax.text(row.backbone_recovery_score + 0.006, row.structure_vs_context_separation_score + 0.004, row.model_label.replace("\n", " "), fontsize=6)
    ax.text(0.515, 0.462, "GEARS sweep\ncandidates", fontsize=6, color=COLORS["gears"])
    ax.set_xlabel("Backbone recovery")
    ax.set_ylabel("Structure/context separation")
    ax.set_title("Sweep candidates move along a trade-off frontier", loc="left")
    ax.set_xlim(0.47, 0.84)
    ax.set_ylim(0.33, 0.49)
    clean_axes(ax)
    ax.grid(color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "b")


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.sort_values("shift_excess_identification_score", ascending=True)
    y = np.arange(len(plot))
    ax.barh(y, plot["shift_excess_identification_score"], color=plot["plot_color"], height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["model_label"].str.replace("\n", " ", regex=False))
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Shift-excess identification")
    ax.set_title("Shift-excess can rise while backbone remains lower", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "c", x=-0.28)


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Frozen stop rule", loc="left", pad=4)
    rows = [
        ("Varied", "epochs", "20, 30, 40"),
        ("Varied", "learning rate", "5e-4, 1e-3, 2e-3"),
        ("Varied", "weight decay", "1e-6, 1e-5"),
        ("Fixed", "truth object", "unchanged"),
        ("Fixed", "scoring system", "unchanged"),
        ("Fixed", "model class", "GEARS"),
    ]
    y = 0.88
    for status, key, value in rows:
        color = COLORS["gears"] if status == "Varied" else "#777777"
        ax.text(0.02, y, status, color=color, fontweight="bold", fontsize=7, transform=ax.transAxes)
        ax.text(0.34, y, key, fontsize=7, transform=ax.transAxes)
        ax.text(0.75, y, value, fontsize=7, transform=ax.transAxes)
        y -= 0.13
    ax.text(0.02, 0.05, "Stop if finite sweep does not close baseline backbone gap.", fontsize=6, color="#666666", transform=ax.transAxes)
    add_panel_label(ax, "d", x=-0.04)


def render_panel_e(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Linear controls test embedding and decoder explanations", loc="left", pad=4)
    boxes = [
        (0.05, 0.65, "Target\nfeatures"),
        (0.38, 0.65, "Linear / low-rank\ndecoder"),
        (0.72, 0.65, "Predicted\nshift"),
    ]
    for x, y, text in boxes:
        rect = plt.Rectangle((x, y), 0.22, 0.18, transform=ax.transAxes, facecolor="#F2F2F2", edgecolor="#888888", linewidth=0.8)
        ax.add_patch(rect)
        ax.text(x + 0.11, y + 0.09, text, ha="center", va="center", fontsize=7, transform=ax.transAxes)
    ax.annotate("", xy=(0.38, 0.74), xytext=(0.27, 0.74), xycoords=ax.transAxes, arrowprops={"arrowstyle": "->", "lw": 0.8})
    ax.annotate("", xy=(0.72, 0.74), xytext=(0.60, 0.74), xycoords=ax.transAxes, arrowprops={"arrowstyle": "->", "lw": 0.8})
    rows = [
        ("lm_train_lowrank", "train-derived low-rank structure"),
        ("lm_G_geneformer_ridge", "frozen Geneformer target embedding"),
        ("lm_G_scgpt_ridge", "frozen scGPT target embedding"),
    ]
    y = 0.40
    for model, note in rows:
        ax.text(0.06, y, model, fontsize=7, fontweight="bold", transform=ax.transAxes)
        ax.text(0.46, y, note, fontsize=7, transform=ax.transAxes)
        y -= 0.12
    add_panel_label(ax, "e", x=-0.04)


def render_panel_f(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.sort_values("backbone_recovery_score", ascending=True)
    y = np.arange(len(plot))
    ax.barh(y, plot["backbone_recovery_score"], color=plot["plot_color"], height=0.62)
    ax.axvline(EXPECTED["baseline_backbone"], color=COLORS["baseline"], linestyle="--", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["model_label"].str.replace("\n", " ", regex=False))
    ax.set_xlim(0.42, 0.84)
    ax.set_xlabel("Backbone recovery")
    ax.set_title("Linear controls do not become backbone winners", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "f", x=-0.28)


def render_panel_g(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.copy()
    plot["label"] = plot["model_id"].map(short_model_label).str.replace("\n", " ", regex=False) + "\n" + plot["cell_line"]
    x = np.arange(len(plot))
    ax.bar(x, plot["target_vocab_coverage"], color="#777777", width=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(plot["label"], rotation=45, ha="right")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Target vocabulary coverage")
    ax.set_title("Coverage is complete for linear controls", loc="left")
    for xi, row in zip(x, plot.itertuples()):
        ax.text(xi, row.target_vocab_coverage + 0.02, f"{row.mapped_targets}/{row.total_targets}", ha="center", fontsize=6)
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "g")


def render_panel_h(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Interpretation boundary", loc="left", pad=4)
    bullets = [
        ("Supported", "No finite sweep candidate closes the backbone gap."),
        ("Supported", "Linear controls have full target coverage but remain below baseline."),
        ("Not supported", "A hidden GEARS recipe is the obvious winner."),
        ("Not supported", "Coverage or embedding absence explains the gap."),
    ]
    y = 0.86
    for label, text in bullets:
        color = COLORS["primary_qualified"] if label == "Supported" else COLORS["boundary"]
        ax.text(0.02, y, label, color=color, fontweight="bold", fontsize=7, transform=ax.transAxes)
        ax.text(0.36, y, text, fontsize=7, transform=ax.transAxes)
        y -= 0.18
    ax.text(0.02, 0.05, "Most stable reading: task-structure / direction-level mismatch.", fontsize=6, color="#666666", transform=ax.transAxes)
    add_panel_label(ax, "h", x=-0.04)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    model = load_model_comparison(root)
    sweep = model.loc[model["is_sweep"]].copy()
    formal_and_sweep = model.loc[model["is_sweep"] | model["model_id"].isin(["shared_mean_baseline", "gears_hcc_formal_v1"])].copy()
    manifest = pd.read_csv(root / SWEEP_MANIFEST, sep="\t")
    coverage = load_coverage(root)

    linear_ids = [
        "shared_mean_baseline",
        "lm_g_geneformer_ridge_hcc_formal_v1",
        "lm_train_lowrank_hcc_formal_v1",
        "lm_g_scgpt_ridge_hcc_formal_v1",
    ]
    linear = model.loc[model["model_id"].isin(linear_ids)].copy()

    stop_rule = manifest[["variant_id", "epochs", "lr", "weight_decay", "candidate_rank", "model_id", "config_path"]].copy()
    boundary = pd.DataFrame(
        [
            {"claim": "finite sweep does not close backbone gap", "status": "supported"},
            {"claim": "linear controls have complete target coverage", "status": "supported"},
            {"claim": "hidden recipe winner", "status": "not_supported"},
            {"claim": "coverage explains backbone gap", "status": "not_supported"},
        ]
    )

    return {
        "a": formal_and_sweep[["model_id", "model_label", "plot_color", "backbone_recovery_score"]],
        "b": formal_and_sweep[["model_id", "model_label", "plot_color", "backbone_recovery_score", "structure_vs_context_separation_score"]],
        "c": formal_and_sweep[["model_id", "model_label", "plot_color", "shift_excess_identification_score", "backbone_recovery_score"]],
        "d": stop_rule,
        "e": pd.DataFrame(
            [
                {"control": "lm_train_lowrank", "tested_component": "train-derived low-rank structure"},
                {"control": "lm_G_geneformer_ridge", "tested_component": "frozen Geneformer target embedding"},
                {"control": "lm_G_scgpt_ridge", "tested_component": "frozen scGPT target embedding"},
            ]
        ),
        "f": linear[["model_id", "model_label", "plot_color", "backbone_recovery_score", "shift_excess_identification_score", "structure_vs_context_separation_score"]],
        "g": coverage,
        "h": boundary,
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
        "a": "GEARS sweep backbone recovery",
        "b": "GEARS sweep trade-off scatter",
        "c": "GEARS sweep shift-excess identification",
        "d": "Frozen GEARS sweep stop rule",
        "e": "Linear-control schematic",
        "f": "Linear-control ranking",
        "g": "Linear-control target coverage",
        "h": "Interpretation boundary",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")
    fig = plt.figure(figsize=(11.0, 10.0))
    gs = fig.add_gridspec(4, 2, hspace=0.72, wspace=0.44)
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
    parser = argparse.ArgumentParser(description="Build manuscript Figure 4 sweep/control panels and assembly.")
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
            width=3.45 if panel_id in {"a", "c", "f", "g"} else 3.2,
            height=2.6 if panel_id in {"a", "c", "f", "g"} else 2.35,
        )
    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
