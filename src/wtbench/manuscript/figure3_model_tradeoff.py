from __future__ import annotations

import argparse
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


FIGURE_ID = "figure3"
FIGURE_TITLE = "Current entrants do not outperform the backbone baseline but reveal a recovery trade-off"
SCRIPT_PATH = Path("scripts/manuscript/build_figure3_model_tradeoff.py")
CLAIM_BOUNDARY = (
    "GEARS is an architecture trade-off diagnosis; shared_mean_baseline is the backbone "
    "primary reference; do not claim model recovery proved."
)

MODEL_COMPARISON = Path("reports/stage2_real_hcc_smoke/model_comparison.tsv")
BACKBONE_DIAGNOSIS = Path("reports/stage2_real_hcc_smoke/backbone_diagnosis.tsv")
FINAL_CLAIM_MATRIX = Path("reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv")

METRICS = [
    "backbone_recovery_score",
    "shift_excess_identification_score",
    "structure_vs_context_separation_score",
]

METRIC_LABELS = {
    "backbone_recovery_score": "backbone\nrecovery",
    "shift_excess_identification_score": "shift-excess\nidentification",
    "structure_vs_context_separation_score": "structure/context\nseparation",
}

EXPECTED_HEADLINES = {
    ("shared_mean_baseline", "backbone_recovery_score"): 0.8066666666666666,
    ("gears_hcc_formal_v1", "backbone_recovery_score"): 0.6599999999999999,
    ("shared_mean_baseline", "structure_vs_context_separation_score"): 0.3526145586462627,
    ("gears_hcc_formal_v1", "structure_vs_context_separation_score"): 0.42841538072534885,
}


def output_dir(root: Path) -> Path:
    return root / "reports/manuscript_figures_v2/fig3_model_tradeoff"


def panel_dir(root: Path) -> Path:
    return output_dir(root) / "panels"


def load_model_comparison(root: Path) -> pd.DataFrame:
    df = pd.read_csv(root / MODEL_COMPARISON, sep="\t")
    for (model_id, metric), expected in EXPECTED_HEADLINES.items():
        observed = float(df.loc[df["model_id"].eq(model_id), metric].iloc[0])
        if abs(observed - expected) > 0.02:
            raise RuntimeError(
                f"Headline sanity check failed for {model_id}/{metric}: "
                f"observed={observed:.4f}, expected={expected:.4f}. Stop and review."
            )
    return add_model_annotations(df)


def add_model_annotations(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["model_label"] = out["model_id"].map(short_model_label)
    out["plot_color"] = [model_color(row.model_id, row.object_role) for row in out.itertuples()]
    out["model_family"] = out["model_id"].map(model_family)
    out["is_formal_gears"] = out["model_id"].eq("gears_hcc_formal_v1")
    out["is_gears_sweep"] = out["model_id"].str.startswith("gears_hcc_formal_v1_")
    return out


def model_family(model_id: str) -> str:
    if model_id == "shared_mean_baseline":
        return "baseline"
    if model_id == "null_model":
        return "null"
    if model_id == "gears_hcc_formal_v1":
        return "GEARS formal"
    if model_id.startswith("gears_hcc_formal_v1_"):
        return "GEARS sweep"
    if model_id.startswith("geneformer") or model_id.startswith("scgpt"):
        return "foundation entrants"
    if model_id.startswith("lm_"):
        return "linear controls"
    return "other"


def axis_label(label: str) -> str:
    return str(label).replace("\n", " ")


def write_panel(
    *,
    root: Path,
    panel_id: str,
    panel_title: str,
    source_df: pd.DataFrame,
    input_paths: list[Path],
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
        input_paths=[root / p for p in input_paths],
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {
        "source": source_path,
        "png": png_path,
        "pdf": pdf_path,
        "manifest": manifest_path,
    }


def render_panel_a(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.sort_values("backbone_recovery_score", ascending=True).copy()
    y = np.arange(len(plot))
    ax.barh(y, plot["backbone_recovery_score"], color=plot["plot_color"], height=0.65)
    ax.set_yticks(y)
    ax.set_yticklabels([axis_label(v) for v in plot["model_label"]])
    ax.set_xlim(0, 0.88)
    ax.set_xlabel("Backbone recovery score")
    ax.set_title("Backbone recovery is led by the shared baseline", loc="left")
    ax.axvline(0.8067, color=COLORS["baseline"], linestyle="--", linewidth=0.8)
    ax.text(0.812, len(plot) - 0.4, "baseline", va="top", fontsize=6, color=COLORS["baseline"])
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "a", x=-0.28)


def render_panel_b(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.copy()
    priority = {
        "shared_mean_baseline": 0,
        "gears_hcc_formal_v1": 1,
        "geneformer_hcc_formal_v1": 2,
        "scgpt_hcc_formal_v1": 3,
        "lm_g_geneformer_ridge_hcc_formal_v1": 4,
        "lm_train_lowrank_hcc_formal_v1": 5,
        "lm_g_scgpt_ridge_hcc_formal_v1": 6,
        "null_model": 7,
    }
    plot["priority"] = plot["model_id"].map(priority).fillna(99)
    plot = plot.sort_values(["priority", "backbone_recovery_score"], ascending=[True, False]).head(8)
    matrix = plot[METRICS].to_numpy(dtype=float)
    im = ax.imshow(matrix, aspect="auto", vmin=0, vmax=0.9, cmap="Greys")
    ax.set_yticks(np.arange(len(plot)))
    ax.set_yticklabels([axis_label(v) for v in plot["model_label"]])
    ax.set_xticks(np.arange(len(METRICS)))
    ax.set_xticklabels([METRIC_LABELS[m] for m in METRICS])
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", fontsize=6, color="white" if matrix[i, j] > 0.55 else "#222222")
    ax.set_title("Three adjudication metrics separate recovery modes", loc="left")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.02).ax.tick_params(labelsize=5)
    add_panel_label(ax, "b", x=-0.28)


def render_panel_c(ax: plt.Axes, df: pd.DataFrame) -> None:
    rows = df.loc[df["model_id"].isin(["shared_mean_baseline", "gears_hcc_formal_v1"])].copy()
    rows = rows.set_index("model_id").loc[["shared_mean_baseline", "gears_hcc_formal_v1"]].reset_index()
    x = np.arange(2)
    width = 0.34
    ax.bar(x - width / 2, rows["backbone_recovery_score"], width=width, color=[COLORS["baseline"], COLORS["gears"]], label="backbone")
    ax.bar(
        x + width / 2,
        rows["structure_vs_context_separation_score"],
        width=width,
        color=[COLORS["baseline"], COLORS["gears"]],
        alpha=0.45,
        label="separation",
    )
    for xi, row in zip(x, rows.itertuples()):
        ax.text(xi - width / 2, row.backbone_recovery_score + 0.025, f"{row.backbone_recovery_score:.3f}", ha="center", fontsize=6)
        ax.text(xi + width / 2, row.structure_vs_context_separation_score + 0.025, f"{row.structure_vs_context_separation_score:.3f}", ha="center", fontsize=6)
    ax.set_xticks(x)
    ax.set_xticklabels(rows["model_label"])
    ax.set_ylim(0, 0.92)
    ax.set_ylabel("Score")
    ax.set_title("Baseline recovers backbone; GEARS separates context", loc="left")
    ax.legend(frameon=False, loc="upper right")
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "c")


def render_panel_d(ax: plt.Axes, df: pd.DataFrame) -> None:
    for row in df.itertuples():
        size = 48 if row.model_id in {"shared_mean_baseline", "gears_hcc_formal_v1"} else 30
        edge = "#000000" if row.model_id in {"shared_mean_baseline", "gears_hcc_formal_v1"} else "white"
        ax.scatter(
            row.backbone_recovery_score,
            row.structure_vs_context_separation_score,
            s=size,
            color=row.plot_color,
            edgecolor=edge,
            linewidth=0.6,
            zorder=3,
        )
        if row.model_id in {"shared_mean_baseline", "gears_hcc_formal_v1", "geneformer_hcc_formal_v1", "scgpt_hcc_formal_v1"}:
            ax.text(row.backbone_recovery_score + 0.01, row.structure_vs_context_separation_score + 0.004, short_model_label(row.model_id).replace("\n", " "), fontsize=6)
    ax.set_xlabel("Backbone recovery")
    ax.set_ylabel("Structure/context separation")
    ax.set_title("Entrants occupy a backbone-separation trade-off", loc="left")
    ax.set_xlim(0.42, 0.84)
    ax.set_ylim(0.22, 0.50)
    clean_axes(ax)
    ax.grid(color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "d")


def render_panel_e(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.loc[df["model_id"].eq("gears_hcc_formal_v1")].copy()
    x = np.arange(len(plot))
    width = 0.34
    ax.bar(x - width / 2, plot["baseline_backbone_recovery"], width=width, color=COLORS["baseline"], label="baseline backbone")
    ax.bar(x + width / 2, plot["backbone_recovery"], width=width, color=COLORS["gears"], label="GEARS backbone")
    for xi, row in zip(x, plot.itertuples()):
        ax.plot([xi - width / 2, xi + width / 2], [row.baseline_backbone_recovery, row.backbone_recovery], color="#777777", linewidth=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(plot["cell_line"])
    ax.set_ylim(0, 0.95)
    ax.set_ylabel("Per-cell-line backbone recovery")
    ax.set_title("Representative HCC recovery shows the same direction", loc="left")
    ax.legend(frameon=False, loc="upper right")
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "e")


def render_panel_f(ax: plt.Axes, df: pd.DataFrame) -> None:
    plot = df.loc[df["model_id"].str.startswith("gears_hcc_formal_v1") | df["model_id"].eq("shared_mean_baseline")].copy()
    plot = plot.sort_values("shift_excess_identification_score", ascending=True)
    y = np.arange(len(plot))
    ax.barh(y, plot["shift_excess_identification_score"], color=plot["plot_color"], height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels([axis_label(v) for v in plot["model_label"]])
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Shift-excess identification")
    ax.set_title("Shift-excess gains do not imply backbone superiority", loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "f", x=-0.28)


def render_panel_g(ax: plt.Axes, df: pd.DataFrame) -> None:
    order = ["baseline", "GEARS formal", "foundation entrants", "linear controls", "GEARS sweep", "null"]
    grouped = (
        df.groupby("model_family", observed=True)
        .agg(
            backbone_mean=("backbone_recovery_score", "mean"),
            backbone_max=("backbone_recovery_score", "max"),
            separation_mean=("structure_vs_context_separation_score", "mean"),
            n=("model_id", "size"),
        )
        .reindex(order)
        .dropna()
        .reset_index()
    )
    x = np.arange(len(grouped))
    ax.scatter(x, grouped["backbone_mean"], color="#222222", s=38, label="mean backbone")
    ax.scatter(x, grouped["separation_mean"], color=COLORS["gears"], s=38, label="mean separation")
    for xi, row in zip(x, grouped.itertuples()):
        ax.vlines(xi, row.backbone_mean, row.separation_mean, color="#BDBDBD", linewidth=0.8)
        ax.text(xi, max(row.backbone_mean, row.separation_mean) + 0.025, f"n={int(row.n)}", ha="center", fontsize=6)
    ax.set_xticks(x)
    ax.set_xticklabels(grouped["model_family"], rotation=35, ha="right")
    ax.set_ylim(0, 0.9)
    ax.set_ylabel("Family mean score")
    ax.set_title("Model families do not displace the backbone reference", loc="left")
    ax.legend(frameon=False, loc="upper right")
    clean_axes(ax)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, "g")


def render_panel_h(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_title("Model-side claim boundary", loc="left", pad=4)
    bullets = [
        ("Allowed", "GEARS is an architecture trade-off diagnosis."),
        ("Allowed", "shared_mean_baseline remains the backbone primary reference."),
        ("Not allowed", "model recovery proved."),
        ("Not allowed", "GEARS is the overall HCC primary winner."),
    ]
    y = 0.88
    for label, text in bullets:
        color = COLORS["primary_qualified"] if label == "Allowed" else COLORS["boundary"]
        ax.text(0.02, y, label, color=color, fontweight="bold", fontsize=7, transform=ax.transAxes)
        ax.text(0.32, y, text, color=COLORS["text"], fontsize=7, transform=ax.transAxes)
        y -= 0.18
    ax.text(0.02, 0.05, "Boundary fixed by final claim matrix.", fontsize=6, color="#666666", transform=ax.transAxes)
    add_panel_label(ax, "h", x=-0.04)


def build_sources(root: Path) -> dict[str, pd.DataFrame]:
    model = load_model_comparison(root)
    backbone = pd.read_csv(root / BACKBONE_DIAGNOSIS, sep="\t")
    backbone = backbone.merge(model[["model_id", "model_label", "plot_color"]], on="model_id", how="left")

    claim = pd.read_csv(root / FINAL_CLAIM_MATRIX, sep="\t")
    boundary_rows = claim.loc[claim["object"].isin(["GEARS_tradeoff_diagnosis", "global_truth_depmap_bridge"])].copy()

    return {
        "a": model[["model_id", "object_role", "model_label", "plot_color", "backbone_recovery_score"]],
        "b": model[["model_id", "model_label", *METRICS]],
        "c": model.loc[model["model_id"].isin(["shared_mean_baseline", "gears_hcc_formal_v1"])],
        "d": model[["model_id", "object_role", "model_label", "plot_color", "backbone_recovery_score", "structure_vs_context_separation_score"]],
        "e": backbone.loc[
            backbone["model_id"].eq("gears_hcc_formal_v1"),
            [
                "model_id",
                "cell_line",
                "backbone_recovery",
                "baseline_backbone_recovery",
                "structure_vs_context_separation",
                "baseline_structure_vs_context_separation",
                "failure_mode_call",
            ],
        ],
        "f": model.loc[model["model_id"].str.startswith("gears_hcc_formal_v1") | model["model_id"].eq("shared_mean_baseline")],
        "g": model[["model_id", "model_family", "backbone_recovery_score", "structure_vs_context_separation_score"]],
        "h": boundary_rows[["object", "evidence_tier", "allowed_wording", "disallowed_wording"]],
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
        "a": "Formal HCC model comparison by backbone recovery",
        "b": "Three-metric model adjudication heatmap",
        "c": "Baseline versus GEARS headline comparison",
        "d": "Backbone-separation trade-off scatter",
        "e": "Per-cell-line representative recovery comparison",
        "f": "Shift-excess gains without backbone superiority",
        "g": "Model family summary",
        "h": "Model-side claim boundary",
    }[panel_id]


def render_combined(root: Path, sources: dict[str, pd.DataFrame], panel_outputs: dict[str, dict[str, Path]]) -> dict[str, Path]:
    out = ensure_dir(output_dir(root))
    combined_source = pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False)
    combined_source_path = write_tsv(combined_source, out / f"{FIGURE_ID}_source_data.tsv")

    fig = plt.figure(figsize=(11.0, 10.0))
    gs = fig.add_gridspec(4, 2, hspace=0.72, wspace=0.42)
    axes = [fig.add_subplot(gs[i, j]) for i in range(4) for j in range(2)]
    for ax, panel_id in zip(axes, list("abcdefgh")):
        render_panel_by_id(panel_id)(ax, sources[panel_id])
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
        input_paths=[root / MODEL_COMPARISON, root / BACKBONE_DIAGNOSIS, root / FINAL_CLAIM_MATRIX],
        claim_boundary=CLAIM_BOUNDARY,
    )
    return {"source": combined_source_path, "png": png_path, "pdf": pdf_path, "manifest": manifest_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build manuscript Figure 3 model trade-off panels and assembly.")
    parser.add_argument("--panels-only", action="store_true", help="Render individual panels but skip combined assembly.")
    args = parser.parse_args(argv)

    root = repo_root()
    apply_manuscript_style()
    sources = build_sources(root)
    panel_outputs: dict[str, dict[str, Path]] = {}
    input_paths = [MODEL_COMPARISON, BACKBONE_DIAGNOSIS, FINAL_CLAIM_MATRIX]

    for panel_id in list("abcdefgh"):
        panel_outputs[panel_id] = write_panel(
            root=root,
            panel_id=panel_id,
            panel_title=panel_title(panel_id),
            source_df=sources[panel_id],
            input_paths=input_paths,
            render=render_panel_by_id(panel_id),
            width=3.45 if panel_id in {"a", "b", "f"} else 3.2,
            height=2.6 if panel_id in {"a", "b", "f"} else 2.35,
        )

    if not args.panels_only:
        render_combined(root, sources, panel_outputs)


if __name__ == "__main__":
    main()
