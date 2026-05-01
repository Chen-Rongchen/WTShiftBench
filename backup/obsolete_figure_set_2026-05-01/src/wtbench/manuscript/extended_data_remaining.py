from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd

from wtbench.manuscript._palette import DIVIDER_GRAY, NEUTRAL_GRAY, PRIMARY_GREEN
from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes, short_model_label


SCRIPT_DIR = Path("scripts/manuscript")
DEFAULT_PANEL_IDS = tuple("abcdefgh")


def _cleanup_generated(out_dir: Path, figure_key: str) -> None:
    for path in (out_dir / "panels").glob(f"{figure_key}_panel*"):
        path.unlink()
    for suffix in (".png", ".pdf", "_source_data.tsv", "_panel_manifest.json"):
        path = out_dir / f"{figure_key}{suffix}"
        if path.exists():
            path.unlink()


def _grid_dimensions(n_panels: int) -> tuple[int, int]:
    ncols = 2 if n_panels > 1 else 1
    return math.ceil(n_panels / ncols), ncols


def _write_panel(
    *,
    root: Path,
    figure_key: str,
    panel_id: str,
    panel_title: str,
    script_path: Path,
    out_dir: Path,
    input_paths: list[Path],
    source_df: pd.DataFrame,
    render: Callable[[plt.Axes, pd.DataFrame], None],
    claim_boundary: str,
    width: float = 3.25,
    height: float = 2.4,
) -> dict[str, Path]:
    pdir = ensure_dir(out_dir / "panels")
    stem = f"{figure_key}_panel{panel_id}"
    source_path = write_tsv(source_df, pdir / f"{stem}_source_data.tsv")
    fig, ax = plt.subplots(figsize=(width, height))
    render(ax, source_df)
    output_paths = save_figure(fig, pdir / f"{stem}.png", pdir / f"{stem}.pdf")
    manifest_path = pdir / f"{stem}_manifest.json"
    write_panel_manifest(
        manifest_path=manifest_path,
        repo_root=root,
        panel_id=f"{figure_key.upper()}{panel_id}",
        panel_title=panel_title,
        script_path=root / script_path,
        input_paths=input_paths,
        source_data_path=source_path,
        output_paths=output_paths,
        claim_boundary=claim_boundary,
    )
    return {"source": source_path, "png": output_paths[0], "pdf": output_paths[1], "manifest": manifest_path}


def _assemble(
    *,
    root: Path,
    figure_id: str,
    figure_key: str,
    figure_title: str,
    script_path: Path,
    out_dir: Path,
    input_paths: list[Path],
    sources: dict[str, pd.DataFrame],
    renders: dict[str, Callable[[plt.Axes, pd.DataFrame], None]],
    panel_outputs: dict[str, dict[str, Path]],
    claim_boundary: str,
    panel_ids: tuple[str, ...] = DEFAULT_PANEL_IDS,
) -> None:
    combined_source_path = write_tsv(
        pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False),
        out_dir / f"{figure_key}_source_data.tsv",
    )
    nrows, ncols = _grid_dimensions(len(panel_ids))
    fig = plt.figure(figsize=(7.3, 2.9) if len(panel_ids) == 1 else (11.0, max(3.0 * nrows, 4.2)))
    gs = fig.add_gridspec(nrows, ncols, hspace=0.78, wspace=0.52)
    axes = [fig.add_subplot(gs[i, j]) for i in range(nrows) for j in range(ncols)]
    for ax, panel_id in zip(axes, panel_ids):
        renders[panel_id](ax, sources[panel_id])
    for ax in axes[len(panel_ids):]:
        ax.set_axis_off()
    output_paths = save_figure(fig, out_dir / f"{figure_key}.png", out_dir / f"{figure_key}.pdf")
    write_figure_manifest(
        manifest_path=out_dir / f"{figure_key}_panel_manifest.json",
        repo_root=root,
        figure_id=figure_id,
        figure_title=figure_title,
        script_path=root / script_path,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in panel_ids],
        combined_source_data_path=combined_source_path,
        output_paths=output_paths,
        input_paths=input_paths,
        claim_boundary=claim_boundary,
    )


def _run_figure(
    figure_id: str,
    figure_key: str,
    figure_title: str,
    script_name: str,
    out_rel: str,
    input_rel: list[str],
    sources: dict[str, pd.DataFrame],
    renders: dict[str, Callable[[plt.Axes, pd.DataFrame], None]],
    titles: dict[str, str],
    claim_boundary: str,
    panels_only: bool,
    panel_ids: tuple[str, ...] = DEFAULT_PANEL_IDS,
) -> None:
    root = repo_root()
    script_path = SCRIPT_DIR / script_name
    out_dir = ensure_dir(root / out_rel)
    _cleanup_generated(out_dir, figure_key)
    input_paths = [root / p for p in input_rel]
    panel_outputs: dict[str, dict[str, Path]] = {}
    for panel_id in panel_ids:
        panel_outputs[panel_id] = _write_panel(
            root=root,
            figure_key=figure_key,
            panel_id=panel_id,
            panel_title=titles[panel_id],
            script_path=script_path,
            out_dir=out_dir,
            input_paths=input_paths,
            source_df=sources[panel_id],
            render=renders[panel_id],
            claim_boundary=claim_boundary,
            width=3.65 if panel_id in {"a", "b", "d", "f"} else 3.25,
            height=2.75 if panel_id in {"a", "b", "d", "f"} else 2.4,
        )
    if not panels_only:
        _assemble(
            root=root,
            figure_id=figure_id,
            figure_key=figure_key,
            figure_title=figure_title,
            script_path=script_path,
            out_dir=out_dir,
            input_paths=input_paths,
            sources=sources,
            renders=renders,
            panel_outputs=panel_outputs,
            claim_boundary=claim_boundary,
            panel_ids=panel_ids,
        )


def _text_panel(ax: plt.Axes, title: str, rows: list[tuple[str, str]], label: str) -> None:
    ax.set_axis_off()
    ax.set_title(title, loc="left", pad=4)
    y = 0.82
    for left, right in rows:
        ax.text(0.04, y, left, fontweight="bold", fontsize=8, transform=ax.transAxes)
        ax.text(0.38, y, right, fontsize=7.5, transform=ax.transAxes)
        y -= 0.18
    add_panel_label(ax, label, x=-0.04)


def _short_text_panel(ax: plt.Axes, title: str, rows: list[tuple[str, str]], label: str, split: float = 0.50) -> None:
    ax.set_axis_off()
    ax.set_title(title, loc="left", pad=4)
    y = 0.84
    for left, right in rows:
        ax.text(0.04, y, left[:28], fontweight="bold", fontsize=7.2, transform=ax.transAxes)
        ax.text(split, y, right[:32], fontsize=7.0, transform=ax.transAxes)
        y -= 0.16
    add_panel_label(ax, label, x=-0.04)


def _barh(ax: plt.Axes, df: pd.DataFrame, y_col: str, x_col: str, title: str, xlabel: str, label: str, color: str = "#777777") -> None:
    plot = df.sort_values(x_col)
    y = range(len(plot))
    ax.barh(list(y), plot[x_col], color=color, height=0.58)
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot[y_col])
    ax.set_xlabel(xlabel)
    ax.set_title(title, loc="left")
    clean_axes(ax)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.5)
    add_panel_label(ax, label, x=-0.28)


def _empty_or_barh(ax: plt.Axes, df: pd.DataFrame, y_col: str, x_col: str, title: str, xlabel: str, label: str, color: str) -> None:
    if df.empty:
        ax.set_axis_off()
        ax.set_title(title, loc="left", pad=4)
        ax.text(0.08, 0.55, "No formal objects under current grid", fontsize=8, color="#555555", transform=ax.transAxes)
        add_panel_label(ax, label, x=-0.04)
        return
    _barh(ax, df, y_col, x_col, title, xlabel, label, color)


def _parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--panels-only", action="store_true")
    return parser


def build_edfig1(panels_only: bool = False) -> None:
    root = repo_root()
    input_rel = [
        "reports/stage2_truth_driven_bridge/HCC38/correlation_summary.tsv",
        "reports/stage2_truth_driven_bridge/HCC1143/correlation_summary.tsv",
        "reports/stage2_gse90063_qc/dixit_2016_k562_tf_7d_summary.tsv",
        "reports/stage2_gse90063_qc/dixit_2016_k562_tf_13d_summary.tsv",
        "reports/stage2_rnai_demeter2_conversion/summary.tsv",
        "reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv",
    ]
    hcc38 = pd.read_csv(root / input_rel[0], sep="\t")
    hcc1143 = pd.read_csv(root / input_rel[1], sep="\t")
    qc7 = pd.read_csv(root / input_rel[2], sep="\t")
    qc13 = pd.read_csv(root / input_rel[3], sep="\t")
    rnai = pd.read_csv(root / input_rel[4], sep="\t")
    claim = pd.read_csv(root / input_rel[5], sep="\t")
    qc = pd.concat([qc7.assign(timepoint="7d"), qc13.assign(timepoint="13d")], ignore_index=True)
    qc_wide = qc.pivot_table(index="timepoint", columns="metric", values="value", aggfunc="first").reset_index()
    hcc = pd.concat([hcc38.assign(cell_line="HCC38"), hcc1143.assign(cell_line="HCC1143")], ignore_index=True)
    primary = hcc.loc[hcc["truth_metric"].eq("real_shift_mean_abs") & hcc["depmap_endpoint"].eq("depmap_gene_dependency")].copy()
    if set(qc_wide["timepoint"]) != {"7d", "13d"}:
        raise RuntimeError("ED Fig. 1 sanity check failed: K562 7d/13d QC missing.")
    sources = {
        "a": primary,
        "b": qc_wide[["timepoint", "matrix_cells", "kept_cells", "controls_in_kept_cells", "targets_in_kept_cells", "matrix_cells_unassigned"]],
        "c": rnai,
        "d": claim.loc[claim["object"].isin(["Dixit_K562_supplementary", "Dixit_K562_temporal_panel", "discovery_phenotype_shifter"])],
    }

    def a(ax, df): _barh(ax, df.assign(label=df["cell_line"]), "label", "spearman_rho_aligned", "HCC primary bridge admission", "Spearman", "a", COLORS["primary_qualified"])
    def b(ax, df):
        plot = df.melt(id_vars="timepoint", value_vars=["matrix_cells", "kept_cells", "matrix_cells_unassigned"], var_name="metric", value_name="cells")
        plot["cells"] = pd.to_numeric(plot["cells"])
        for metric, sub in plot.groupby("metric"):
            ax.plot(sub["timepoint"], sub["cells"], marker="o", label=metric.replace("_", " "))
        ax.set_title("K562 cell accounting", loc="left"); ax.set_ylabel("Cells"); ax.legend(frameon=False, fontsize=6); clean_axes(ax); ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5); add_panel_label(ax, "b")
    def c(ax, df):
        keep = ["score_direction", "input_cell_lines", "mapped_cell_lines", "genes"]
        plot = df.loc[df["metric"].isin(keep)].copy()
        rows = [(r.metric.replace("_", " "), str(r.value)) for r in plot.itertuples()]
        _short_text_panel(ax, "RNAi conversion summary", rows, "c")
    def d(ax, df):
        rows = [("K562 supplement", "not primary co-pillar"), ("K562 temporal", "A0/A1 supporting"), ("discovery", "gated downstream")]
        _short_text_panel(ax, "Not primary co-pillars", rows, "d")

    _run_figure(
        figure_id="extended_data_figure2",
        figure_key="edfig2",
        figure_title="Dataset and endpoint admission",
        script_name="build_extended_data_figure2.py",
        out_rel="reports/manuscript_extended_data_v1/edfig2_dataset_endpoint_admission",
        input_rel=input_rel,
        sources=sources,
        renders=dict(zip(list("abcd"), [a, b, c, d])),
        titles={k: v for k, v in zip(list("abcd"), ["HCC admission", "K562 accounting", "RNAi conversion", "Boundary"])},
        claim_boundary="Dataset and endpoint admission separates primary HCC evidence, supplementary K562 evidence and RNAi sensitivity.",
        panels_only=panels_only,
        panel_ids=tuple("abcd"),
    )


def build_edfig2(panels_only: bool = False) -> None:
    root = repo_root()
    input_rel = [
        "reports/stage2_truth_bridge_decomposition/target_level_joint_grid.tsv",
        "reports/stage2_truth_bridge_decomposition/target_level_grid_summary.tsv",
        "reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv",
    ]
    grid = pd.read_csv(root / input_rel[0], sep="\t")
    summary = pd.read_csv(root / input_rel[1], sep="\t")
    evidence = pd.read_csv(root / input_rel[2], sep="\t")
    q1 = grid.groupby("cell_line")["is_q1_anchor"].sum().to_dict()
    if q1.get("HCC38") != 9 or q1.get("HCC1143") != 10:
        raise RuntimeError("ED Fig. 2 sanity check failed: Q1 anchor counts changed.")
    sources = {
        "a": grid.loc[grid["cell_line"].eq("HCC38")],
        "b": grid.loc[grid["cell_line"].eq("HCC1143")],
        "c": pd.concat(
            [
                grid.groupby(["cell_line", "joint_grid"], as_index=False).size().rename(columns={"size": "n"}).assign(summary_kind="grid_category"),
                grid.loc[grid["is_q1_anchor"], ["cell_line", "target_gene", "joint_grid"]].assign(n=1, summary_kind="q1_anchor"),
                pd.DataFrame(
                    [
                        {"cell_line": "all", "joint_grid": "Q2_transcriptomic_excess", "n": int(grid["is_q2_transcriptomic_excess"].sum()), "summary_kind": "zero_count_check"},
                        {"cell_line": "all", "joint_grid": "Q3_dependency_excess", "n": int(grid["is_q3_dependency_excess"].sum()), "summary_kind": "zero_count_check"},
                    ]
                ),
            ],
            ignore_index=True,
            sort=False,
        ),
        "d": evidence.loc[evidence["object_type"].eq("target_anchor")],
    }

    def scatter(label):
        def _r(ax, df):
            colors = df["joint_grid"].map({"Q1_anchor": COLORS["primary_qualified"], "Q4_low_information": "#BDBDBD"}).fillna("#888888")
            ax.scatter(df["depmap_strength"], df["shift_value"], c=colors, s=22, edgecolor="white", linewidth=0.3)
            ax.set_xlabel("Dependency strength"); ax.set_ylabel("Shift value"); ax.set_title(f"{label} full grid", loc="left"); clean_axes(ax); ax.grid(color=COLORS["grid"], linewidth=0.5); add_panel_label(ax, "a" if label == "HCC38" else "b")
        return _r
    def c(ax, df):
        counts = df.loc[df["summary_kind"].eq("grid_category")]
        piv = counts.pivot(index="joint_grid", columns="cell_line", values="n").fillna(0)
        piv.plot(kind="bar", ax=ax, color=[COLORS["baseline"], COLORS["primary_qualified"]], width=0.7)
        zeros = df.loc[df["summary_kind"].eq("zero_count_check")]
        zero_text = "; ".join(f"{r.joint_grid}: {int(r.n)}" for r in zeros.itertuples())
        q1_n = df.loc[df["summary_kind"].eq("q1_anchor"), "target_gene"].nunique()
        ax.text(0.02, 0.95, f"Q1 anchors: {q1_n}; {zero_text}", transform=ax.transAxes, fontsize=7, va="top")
        ax.set_title("Grid composition and retained zero-count classes", loc="left"); ax.set_ylabel("Targets"); ax.legend(frameon=False); clean_axes(ax); ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5); add_panel_label(ax, "c")
    def d(ax, df): _barh(ax, df.groupby("evidence_tier", as_index=False).size().rename(columns={"size": "n"}), "evidence_tier", "n", "Target evidence tiers", "Objects", "d", "#8A8A8A")

    _run_figure("extended_data_figure3", "edfig3", "Full target-level joint grid", "build_extended_data_figure3.py", "reports/manuscript_extended_data_v1/edfig3_full_target_grid", input_rel, sources, dict(zip(list("abcd"), [scatter("HCC38"), scatter("HCC1143"), c, d])), {k: v for k, v in zip(list("abcd"), ["HCC38 grid", "HCC1143 grid", "Grid composition", "Evidence tiers"])}, "Full target grid supports the bridge but does not remove covariate boundaries.", panels_only, panel_ids=tuple("abcd"))


def build_edfig4(panels_only: bool = False) -> None:
    root = repo_root()
    input_rel = ["reports/stage2_real_hcc_smoke/model_comparison.tsv", "reports/stage2_real_hcc_smoke/smoke_summary.tsv"]
    comp = pd.read_csv(root / input_rel[0], sep="\t")
    smoke = pd.read_csv(root / input_rel[1], sep="\t")
    vals = comp.set_index("model_id")
    if vals.loc["shared_mean_baseline", "backbone_recovery_score"] <= vals.loc["gears_hcc_formal_v1", "backbone_recovery_score"]:
        raise RuntimeError("ED Fig. 4 sanity check failed: baseline no longer exceeds formal GEARS backbone.")
    sources = {
        "a": comp,
        "b": smoke,
        "c": smoke,
    }
    def a(ax, df): _barh(ax, df.assign(label=df["model_id"].map(short_model_label)), "label", "backbone_recovery_score", "Full model backbone ranking", "Backbone recovery", "a", COLORS["baseline"])
    def b(ax, df):
        metrics = ["backbone_recovery_score", "shift_excess_identification_score", "structure_vs_context_separation_score"]
        plot = df.groupby("cell_line", as_index=False)[metrics].mean()
        x = range(len(plot))
        for offset, metric_name, color in [(-0.22, metrics[0], COLORS["primary_qualified"]), (0.0, metrics[1], COLORS["supporting"]), (0.22, metrics[2], COLORS["gears"])]:
            ax.bar([i + offset for i in x], plot[metric_name], width=0.20, color=color, label=metric_name.replace("_score", "").replace("_", " "))
        ax.set_xticks(list(x)); ax.set_xticklabels(plot["cell_line"])
        ax.set_ylabel("Mean score"); ax.set_title("Per-cell-line multi-metric comparison", loc="left")
        ax.legend(frameon=False, fontsize=6); clean_axes(ax); ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5); add_panel_label(ax, "b")
    def c(ax, df):
        groups = {
            "baseline": ["shared_mean_baseline"],
            "GEARS": ["gears_hcc_formal_v1"],
            "foundation": ["geneformer_hcc_formal_v1", "scgpt_hcc_formal_v1"],
            "null": ["null_model"],
        }
        rows = []
        for group, models in groups.items():
            sub = df.loc[df["model_id"].isin(models)]
            rows.append({"model_group": group, "top20_overlap_mean": sub["top20_overlap_mean"].mean()})
        _barh(ax, pd.DataFrame(rows), "model_group", "top20_overlap_mean", "Top-20 overlap comparison", "Mean top-20 overlap", "c", "#8A8A8A")
    _run_figure("extended_data_figure5", "edfig5", "Full HCC model recovery detail", "build_extended_data_figure5.py", "reports/manuscript_extended_data_v1/edfig5_model_detail", input_rel, sources, dict(zip(list("abc"), [a, b, c])), {k: v for k, v in zip(list("abc"), ["Ranking", "Per-cell-line metrics", "Top-20 overlap"])}, "Full model details support an asymmetric recovery pattern, not model recovery proof.", panels_only, panel_ids=tuple("abc"))


def build_edfig5(panels_only: bool = False) -> None:
    root = repo_root()
    input_rel = ["reports/stage2_gears_backbone_sweep/candidate_manifest.tsv", "reports/stage2_gears_backbone_sweep/batch_run/batch_status.tsv", "reports/stage2_real_hcc_smoke/model_comparison.tsv"]
    cand = pd.read_csv(root / input_rel[0], sep="\t")
    batch = pd.read_csv(root / input_rel[1], sep="\t")
    comp = pd.read_csv(root / input_rel[2], sep="\t")
    sweep = comp.loc[comp["model_id"].str.startswith("gears_hcc_formal_v1_")]
    baseline = float(comp.loc[comp["model_id"].eq("shared_mean_baseline"), "backbone_recovery_score"].iloc[0])
    if float(sweep["backbone_recovery_score"].max()) >= baseline:
        raise RuntimeError("ED Fig. 5 sanity check failed: GEARS sweep reached baseline backbone.")
    sources = {
        "a": cand,
        "b": batch.groupby(["variant_id", "phase", "status"], as_index=False).size().rename(columns={"size": "n"}),
        "c": sweep,
        "d": sweep,
        "e": pd.DataFrame([{"rule": "stop", "baseline_backbone": baseline, "best_sweep_backbone": sweep["backbone_recovery_score"].max(), "decision": "do not promote GEARS as primary winner"}]),
        "f": pd.DataFrame([{"boundary": "GEARS training", "status": "not rerun in figure stage"}, {"boundary": "predictions/scores", "status": "frozen and hashed"}, {"boundary": "recipe search", "status": "finite-budget control"}]),
    }
    def a(ax, df):
        rows = [(r.variant_id, f"rank {r.candidate_rank}; e{r.epochs}; lr={r.lr}") for r in df.itertuples()]
        _short_text_panel(ax, "Sweep candidate manifest", rows, "a", split=0.44)
    def b(ax, df):
        plot = df.groupby(["phase", "status"], as_index=False)["n"].sum()
        _barh(ax, plot.assign(label=plot["phase"] + " " + plot["status"]), "label", "n", "Batch status log", "Events", "b", "#8A8A8A")
    def c(ax, df): _barh(ax, df.assign(label=df["model_id"].str.replace("gears_hcc_formal_v1_", "", regex=False)), "label", "backbone_recovery_score", "Sweep backbone scores", "Backbone", "c", COLORS["gears"])
    def d(ax, df): _barh(ax, df.assign(label=df["model_id"].str.replace("gears_hcc_formal_v1_", "", regex=False)), "label", "structure_vs_context_separation_score", "Sweep separation scores", "Separation", "d", COLORS["supporting"])
    def e(ax, df): _text_panel(ax, "Stop-rule adjudication", [("baseline", f"{df.baseline_backbone.iloc[0]:.3f}"), ("best sweep", f"{df.best_sweep_backbone.iloc[0]:.3f}"), ("decision", df.decision.iloc[0])], "e")
    def f(ax, df): _text_panel(ax, "Training exemption", [(r.boundary, r.status) for r in df.itertuples()], "f")
    _run_figure("extended_data_figure6", "edfig6", "GEARS sweep and stop rule", "build_extended_data_figure6.py", "reports/manuscript_extended_data_v1/edfig6_gears_sweep", input_rel, sources, dict(zip(list("abcdef"), [a, b, c, d, e, f])), {k: v for k, v in zip(list("abcdef"), ["Candidate manifest", "Batch status", "Backbone", "Separation", "Stop rule", "Boundary"])}, "GEARS sweep is finite-budget control and training is not rerun during figure generation.", panels_only, panel_ids=tuple("abcdef"))


def build_edfig7(panels_only: bool = False) -> None:
    root = repo_root()
    input_rel = [
        "reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_bridge_summary.tsv",
        "reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_structure_summary.tsv",
        "reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_panel_calls.tsv",
        "reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_7d/dixit_evidence_tier_summary.tsv",
        "reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_evidence_tier_summary.tsv",
        "data/processed/stage2_truth_driven_bridge_gse90063_7d/dixit_2016_k562_tf_7d_gse90063/target_level_bridge_table.tsv.gz",
        "data/processed/stage2_truth_driven_bridge_gse90063_13d/dixit_2016_k562_tf_13d_gse90063/target_level_bridge_table.tsv.gz",
    ]
    bridge = pd.read_csv(root / input_rel[0], sep="\t")
    target_7d = pd.read_csv(root / input_rel[5], sep="\t").assign(timepoint="7d")
    target_13d = pd.read_csv(root / input_rel[6], sep="\t").assign(timepoint="13d")
    primary = bridge.loc[bridge["truth_metric"].eq("real_shift_mean_abs") & bridge["depmap_endpoint"].eq("depmap_gene_dependency")]
    vals = primary.set_index("timepoint")
    if vals.loc["7d", "aligned_spearman"] <= vals.loc["13d", "aligned_spearman"] or vals.loc["13d", "mean_truth_metric"] <= vals.loc["7d", "mean_truth_metric"]:
        raise RuntimeError("ED Fig. 3 sanity check failed: temporal stratification changed.")
    plot = bridge.loc[
        bridge["truth_metric"].isin(["real_shift_mean_abs", "real_shift_L2"])
        & bridge["depmap_endpoint"].eq("depmap_gene_dependency")
    ].copy()
    plot["metric_label"] = plot["truth_metric"].map({"real_shift_mean_abs": "Mean abs (primary)", "real_shift_L2": "L2 sensitivity"})
    plot["timepoint_order"] = plot["timepoint"].map({"7d": 0, "13d": 1})
    plot["mean_shift_norm"] = plot.groupby("truth_metric")["mean_truth_metric"].transform(lambda s: s / s.max())
    plot["mean_shift_display"] = plot.apply(
        lambda row: row["mean_truth_metric"] * 1000 if row["truth_metric"] == "real_shift_mean_abs" else row["mean_truth_metric"],
        axis=1,
    )
    target_values = pd.concat([target_7d, target_13d], ignore_index=True)
    shift_errors = []
    for metric, source_col in [("real_shift_mean_abs", "real_shift_mean_abs"), ("real_shift_L2", "real_shift_L2")]:
        for timepoint, sub in target_values.groupby("timepoint"):
            shift_errors.append(
                {
                    "truth_metric": metric,
                    "timepoint": timepoint,
                    "mean_shift_sem": float(sub[source_col].sem()),
                }
            )
    error_df = pd.DataFrame(shift_errors)
    plot = plot.merge(error_df, on=["truth_metric", "timepoint"], how="left")
    plot["mean_shift_sem_norm"] = plot["mean_shift_sem"] / plot.groupby("truth_metric")["mean_truth_metric"].transform("max")
    sources = {"a": plot.sort_values(["truth_metric", "timepoint_order"])}

    def a(ax, df):
        ax.set_axis_off()
        add_panel_label(ax, "a", x=-0.025, y=1.02)
        ax.text(
            0.030,
            1.015,
            "Temporal bridge-magnitude dissociation",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=8.4,
            fontweight="bold",
        )
        ax.plot([0.52, 0.555], [0.93, 0.93], color=PRIMARY_GREEN, linewidth=1.2, transform=ax.transAxes, clip_on=False)
        ax.scatter([0.5375], [0.93], s=14, color=PRIMARY_GREEN, transform=ax.transAxes, clip_on=False)
        ax.text(0.565, 0.93, "Mean abs (primary)", transform=ax.transAxes, va="center", fontsize=6.0)
        ax.plot([0.73, 0.765], [0.93, 0.93], color=NEUTRAL_GRAY, linewidth=1.2, transform=ax.transAxes, clip_on=False)
        ax.scatter([0.7475], [0.93], s=14, marker="s", color=NEUTRAL_GRAY, transform=ax.transAxes, clip_on=False)
        ax.text(0.775, 0.93, "L2 sensitivity", transform=ax.transAxes, va="center", fontsize=6.0)
        rank_ax = ax.inset_axes([0.05, 0.22, 0.38, 0.49])
        shift_ax = ax.inset_axes([0.58, 0.22, 0.38, 0.49])
        metric_styles = {
            "real_shift_mean_abs": {"color": PRIMARY_GREEN, "marker": "o", "label": "Mean abs (primary)", "zorder": 3},
            "real_shift_L2": {"color": NEUTRAL_GRAY, "marker": "s", "label": "L2 sensitivity", "zorder": 2},
        }
        x_map = {"7d": 0, "13d": 1}
        for metric, style in metric_styles.items():
            sub = df.loc[df["truth_metric"].eq(metric)].sort_values("timepoint_order")
            xs = [x_map[v] for v in sub["timepoint"]]
            rank_ax.plot(xs, sub["aligned_spearman"], color=style["color"], marker=style["marker"], linewidth=1.2, markersize=4.2, label=style["label"], zorder=style["zorder"])
            shift_ax.errorbar(
                xs,
                sub["mean_shift_norm"],
                yerr=sub["mean_shift_sem_norm"],
                color=style["color"],
                marker=style["marker"],
                linewidth=1.2,
                markersize=4.2,
                capsize=2.0,
                capthick=0.7,
                elinewidth=0.8,
                label=style["label"],
                zorder=style["zorder"],
            )
        for sub_ax in (rank_ax, shift_ax):
            sub_ax.set_xlim(-0.25, 1.25)
            sub_ax.set_xticks([0, 1])
            sub_ax.set_xticklabels(["7d", "13d"])
            sub_ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5)
            clean_axes(sub_ax)
        rank_ax.set_ylim(0.35, 0.88)
        rank_ax.set_ylabel("Bridge rho", labelpad=2)
        rank_ax.set_title("Rank bridge weakens at 13d", loc="left", fontsize=7.0, fontweight="bold", pad=2)
        shift_ax.set_ylim(0.55, 1.15)
        shift_ax.set_ylabel("Mean shift (norm.)", labelpad=2)
        shift_ax.set_title("Perturbation magnitude increases at 13d", loc="left", fontsize=7.0, fontweight="bold", pad=2)
        # divider line removed

    _run_figure(
        "extended_data_figure3",
        "edfig8",
        "K562 temporal bridge-magnitude dissociation",
        "build_extended_data_figure8.py",
        "reports/manuscript_extended_data_v1/edfig8_k562_temporal",
        input_rel,
        sources,
        {"a": a},
        {"a": "Temporal bridge-magnitude dissociation"},
        "K562 remains supplementary temporal evidence: larger 13d perturbation magnitude does not strengthen the rank bridge.",
        panels_only,
        panel_ids=tuple("a"),
    )


def build_edfig8(panels_only: bool = False) -> None:
    root = repo_root()
    input_rel = ["reports/stage2_truth_driven_bridge/hcc38_hcc1143_rnai_endpoint_consistency/endpoint_consistency_summary.tsv", "reports/stage2_truth_driven_bridge/k562_rnai_endpoint_consistency/endpoint_consistency_summary.tsv", "reports/stage2_rnai_demeter2_conversion/summary.tsv", "reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv"]
    hcc = pd.read_csv(root / input_rel[0], sep="\t")
    k562 = pd.read_csv(root / input_rel[1], sep="\t")
    conv = pd.read_csv(root / input_rel[2], sep="\t")
    claim = pd.read_csv(root / input_rel[3], sep="\t")
    all_ep = pd.concat([hcc, k562], ignore_index=True)
    bridge = all_ep.loc[all_ep["summary_kind"].eq("truth_endpoint_bridge") & all_ep["truth_metric"].eq("real_shift_mean_abs") & all_ep["depmap_endpoint"].eq("depmap_gene_dependency")].copy()
    pivot = bridge.pivot_table(index="timepoint", columns="platform_pair", values="spearman", aggfunc="first")
    if not (pivot["crispr"] > pivot["rnai"]).all():
        raise RuntimeError("ED Fig. 8 sanity check failed: CRISPR no longer exceeds RNAi in every context.")
    consistency = all_ep.loc[all_ep["summary_kind"].eq("endpoint_consistency")]
    sources = {
        "a": hcc,
        "b": k562,
        "c": consistency,
        "d": claim.loc[claim["object"].isin(["Replogle_RNAi_expansion_candidate", "global_truth_depmap_bridge"])],
        "e": bridge,
        "f": pd.concat([conv.assign(summary_kind="demeter2_conversion"), claim.loc[claim["object"].str.contains("RNAi|global|Dixit", regex=True)].assign(summary_kind="claim_boundary")], ignore_index=True, sort=False),
    }
    def endpoint(panel, title):
        return lambda ax, df: _barh(ax, df.loc[df["summary_kind"].eq("truth_endpoint_bridge") & df["truth_metric"].eq("real_shift_mean_abs") & df["depmap_endpoint"].eq("depmap_gene_dependency")].assign(label=lambda x: x["timepoint"].astype(str) + " " + x["platform_pair"]), "label", "spearman", title, "Spearman", panel, COLORS["primary_qualified"])
    def c(ax, df): _barh(ax, df.assign(label=df["timepoint"].astype(str)), "label", "spearman", "CRISPR-RNAi endpoint agreement", "Spearman", "c", "#777777")
    def d(ax, df): _short_text_panel(ax, "RNAi sensitivity boundary", [("global bridge", "retainable global claim"), ("RNAi expansion", "admission required")], "d")
    def e(ax, df): _barh(ax, df.assign(delta=df.groupby("timepoint")["spearman"].transform(lambda s: s.max() - s.min())).drop_duplicates("timepoint").assign(label=lambda x: x["timepoint"].astype(str)), "label", "delta", "CRISPR-RNAi bridge gap", "Spearman gap", "e", COLORS["boundary"])
    def f(ax, df):
        conv_rows = df.loc[df["summary_kind"].eq("demeter2_conversion") & df["metric"].isin(["score_direction", "mapped_cell_lines", "genes"])]
        rows = [(r.metric.replace("_", " "), str(r.value)) for r in conv_rows.itertuples()]
        rows.extend([("CRISPR", "primary bridge readout"), ("RNAi", "weaker sensitivity endpoint")])
        _short_text_panel(ax, "Endpoint claim boundary + DEMETER2", rows, "f")
    _run_figure("extended_data_figure4", "edfig9", "CRISPR versus RNAi endpoint detail", "build_extended_data_figure9.py", "reports/manuscript_extended_data_v1/edfig9_endpoint_hierarchy", input_rel, sources, dict(zip(list("abcdef"), [endpoint("a", "HCC endpoint bridge"), endpoint("b", "K562 endpoint bridge"), c, d, e, f])), {k: v for k, v in zip(list("abcdef"), ["HCC", "K562", "Agreement", "Boundary", "Gap", "Claims and conversion"])}, "CRISPR is the primary bridge endpoint; RNAi is a weaker sensitivity endpoint.", panels_only, panel_ids=tuple("abcdef"))


def main_edfig1(argv: list[str] | None = None) -> None:
    build_edfig1(_parser("Build ED Fig. 1").parse_args(argv).panels_only)


def main_edfig2(argv: list[str] | None = None) -> None:
    build_edfig2(_parser("Build ED Fig. 2").parse_args(argv).panels_only)


def main_edfig4(argv: list[str] | None = None) -> None:
    build_edfig4(_parser("Build ED Fig. 4").parse_args(argv).panels_only)


def main_edfig5(argv: list[str] | None = None) -> None:
    build_edfig5(_parser("Build ED Fig. 5").parse_args(argv).panels_only)


def main_edfig7(argv: list[str] | None = None) -> None:
    build_edfig7(_parser("Build ED Fig. 3").parse_args(argv).panels_only)


def main_edfig8(argv: list[str] | None = None) -> None:
    build_edfig8(_parser("Build ED Fig. 4").parse_args(argv).panels_only)
