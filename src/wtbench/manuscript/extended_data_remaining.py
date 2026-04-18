from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd

from wtbench.manuscript.figure_io import ensure_dir, repo_root, save_figure, write_tsv
from wtbench.manuscript.hash_manifest import write_figure_manifest, write_panel_manifest
from wtbench.manuscript.manuscript_style import COLORS, add_panel_label, apply_manuscript_style, clean_axes, short_model_label


SCRIPT_DIR = Path("scripts/manuscript")


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
) -> None:
    combined_source_path = write_tsv(
        pd.concat([df.assign(panel=panel_id) for panel_id, df in sources.items()], ignore_index=True, sort=False),
        out_dir / f"{figure_key}_source_data.tsv",
    )
    fig = plt.figure(figsize=(11.0, 10.0))
    gs = fig.add_gridspec(4, 2, hspace=0.78, wspace=0.52)
    axes = [fig.add_subplot(gs[i, j]) for i in range(4) for j in range(2)]
    for ax, panel_id in zip(axes, list("abcdefgh")):
        renders[panel_id](ax, sources[panel_id])
    output_paths = save_figure(fig, out_dir / f"{figure_key}.png", out_dir / f"{figure_key}.pdf")
    write_figure_manifest(
        manifest_path=out_dir / f"{figure_key}_panel_manifest.json",
        repo_root=root,
        figure_id=figure_id,
        figure_title=figure_title,
        script_path=root / script_path,
        panel_manifest_paths=[panel_outputs[p]["manifest"] for p in list("abcdefgh")],
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
) -> None:
    root = repo_root()
    script_path = SCRIPT_DIR / script_name
    out_dir = ensure_dir(root / out_rel)
    input_paths = [root / p for p in input_rel]
    panel_outputs: dict[str, dict[str, Path]] = {}
    for panel_id in list("abcdefgh"):
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
        "b": qc_wide[["timepoint", "kept_cells", "controls_in_kept_cells", "targets_in_kept_cells", "sg_guides", "intergenic_guides"]],
        "c": rnai,
        "d": claim.loc[claim["object"].isin(["global_truth_depmap_bridge", "Dixit_K562_temporal_panel", "Replogle_RNAi_expansion_candidate"])],
        "e": pd.DataFrame(
            [
                {"endpoint": "CRISPR DepMap", "role": "primary bridge readout", "tier": "primary"},
                {"endpoint": "RNAi DEMETER2", "role": "cross-platform sensitivity", "tier": "sensitivity"},
                {"endpoint": "K562 GSE90063", "role": "supplementary temporal panel", "tier": "supplementary"},
            ]
        ),
        "f": qc_wide[["timepoint", "matrix_cells", "kept_cells", "matrix_cells_unassigned"]],
        "g": primary[["cell_line", "truth_metric", "depmap_endpoint", "spearman_rho_aligned"]],
        "h": claim.loc[claim["object"].isin(["Dixit_K562_supplementary", "Dixit_K562_temporal_panel", "discovery_phenotype_shifter"])],
    }

    def a(ax, df): _barh(ax, df.assign(label=df["cell_line"]), "label", "spearman_rho_aligned", "HCC primary bridge admission", "Spearman", "a", COLORS["primary_qualified"])
    def b(ax, df): _barh(ax, df.assign(kept_cells=pd.to_numeric(df["kept_cells"])), "timepoint", "kept_cells", "K562 kept cells", "Cells", "b", "#777777")
    def c(ax, df):
        keep = ["score_direction", "input_cell_lines", "mapped_cell_lines", "genes"]
        plot = df.loc[df["metric"].isin(keep)].copy()
        rows = [(r.metric.replace("_", " "), str(r.value)) for r in plot.itertuples()]
        _short_text_panel(ax, "RNAi conversion summary", rows, "c")
    def d(ax, df):
        rows = [("global bridge", df.loc[df["object"].eq("global_truth_depmap_bridge"), "evidence_tier"].iloc[0]), ("K562 temporal", df.loc[df["object"].eq("Dixit_K562_temporal_panel"), "evidence_tier"].iloc[0]), ("RNAi expansion", df.loc[df["object"].eq("Replogle_RNAi_expansion_candidate"), "evidence_tier"].iloc[0])]
        _short_text_panel(ax, "Admission status", rows, "d")
    def e(ax, df): _text_panel(ax, "Endpoint hierarchy", [(r.endpoint, r.tier) for r in df.itertuples()], "e")
    def f(ax, df):
        plot = df.melt(id_vars="timepoint", value_vars=["matrix_cells", "kept_cells", "matrix_cells_unassigned"], var_name="metric", value_name="cells")
        plot["cells"] = pd.to_numeric(plot["cells"])
        for metric, sub in plot.groupby("metric"):
            ax.plot(sub["timepoint"], sub["cells"], marker="o", label=metric.replace("_", " "))
        ax.set_title("K562 cell accounting", loc="left"); ax.set_ylabel("Cells"); ax.legend(frameon=False, fontsize=6); clean_axes(ax); ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5); add_panel_label(ax, "f")
    def g(ax, df): _barh(ax, df.assign(label=df["cell_line"]), "label", "spearman_rho_aligned", "Primary HCC endpoint strength", "Spearman", "g", COLORS["baseline"])
    def h(ax, df):
        rows = [("K562 supplement", "not primary co-pillar"), ("K562 temporal", "A0/A1 supporting"), ("discovery", "gated downstream")]
        _short_text_panel(ax, "Not primary co-pillars", rows, "h")

    _run_figure(
        figure_id="extended_data_figure1",
        figure_key="edfig1",
        figure_title="Dataset and endpoint admission",
        script_name="build_extended_data_figure1.py",
        out_rel="reports/manuscript_extended_data_v1/edfig1_dataset_endpoint_admission",
        input_rel=input_rel,
        sources=sources,
        renders=dict(zip(list("abcdefgh"), [a, b, c, d, e, f, g, h])),
        titles={k: v for k, v in zip(list("abcdefgh"), ["HCC admission", "K562 QC", "RNAi conversion", "Admission status", "Endpoint hierarchy", "Cell accounting", "HCC endpoint strength", "Boundary"])},
        claim_boundary="Dataset and endpoint admission separates primary HCC evidence, supplementary K562 evidence and RNAi sensitivity.",
        panels_only=panels_only,
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
        "c": grid.groupby(["cell_line", "joint_grid"], as_index=False).size().rename(columns={"size": "n"}),
        "d": grid.loc[grid["is_q1_anchor"]],
        "e": grid.loc[grid["is_q2_transcriptomic_excess"]],
        "f": grid.loc[grid["is_q3_dependency_excess"]],
        "g": evidence.loc[evidence["object_type"].eq("target_anchor")],
        "h": summary,
    }

    def scatter(label):
        def _r(ax, df):
            colors = df["joint_grid"].map({"Q1_anchor": COLORS["primary_qualified"], "Q4_low_information": "#BDBDBD"}).fillna("#888888")
            ax.scatter(df["depmap_strength"], df["shift_value"], c=colors, s=22, edgecolor="white", linewidth=0.3)
            ax.set_xlabel("Dependency strength"); ax.set_ylabel("Shift value"); ax.set_title(f"{label} full grid", loc="left"); clean_axes(ax); ax.grid(color=COLORS["grid"], linewidth=0.5); add_panel_label(ax, "a" if label == "HCC38" else "b")
        return _r
    def c(ax, df):
        piv = df.pivot(index="joint_grid", columns="cell_line", values="n").fillna(0)
        piv.plot(kind="bar", ax=ax, color=[COLORS["baseline"], COLORS["primary_qualified"]], width=0.7)
        ax.set_title("Grid category counts", loc="left"); ax.set_ylabel("Targets"); ax.legend(frameon=False); clean_axes(ax); ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5); add_panel_label(ax, "c")
    def d(ax, df): _barh(ax, df.groupby("target_gene", as_index=False).size().rename(columns={"size": "n"}), "target_gene", "n", "All Q1 anchors", "Cell-line count", "d", COLORS["primary_qualified"])
    def e(ax, df): _empty_or_barh(ax, df.groupby("target_gene", as_index=False).size().rename(columns={"size": "n"}), "target_gene", "n", "Transcriptomic-excess targets", "Cell-line count", "e", COLORS["supporting"])
    def f(ax, df): _empty_or_barh(ax, df.groupby("target_gene", as_index=False).size().rename(columns={"size": "n"}), "target_gene", "n", "Dependency-excess targets", "Cell-line count", "f", "#777777")
    def g(ax, df): _barh(ax, df.groupby("evidence_tier", as_index=False).size().rename(columns={"size": "n"}), "evidence_tier", "n", "Target evidence tiers", "Objects", "g", "#8A8A8A")
    def h(ax, df): _barh(ax, df.assign(label=df["cell_line"] + " " + df["joint_grid"]), "label", "n_targets", "Grid summary table", "Targets", "h", "#999999")

    _run_figure("extended_data_figure2", "edfig2", "Full target-level joint grid", "build_extended_data_figure2.py", "reports/manuscript_extended_data_v1/edfig2_full_target_grid", input_rel, sources, dict(zip(list("abcdefgh"), [scatter("HCC38"), scatter("HCC1143"), c, d, e, f, g, h])), {k: v for k, v in zip(list("abcdefgh"), ["HCC38 grid", "HCC1143 grid", "Counts", "Q1 anchors", "Q2", "Q3", "Evidence tiers", "Summary"])}, "Full target grid supports the bridge but does not remove covariate boundaries.", panels_only)


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
        "d": smoke,
        "e": smoke.loc[smoke["model_id"].eq("shared_mean_baseline")],
        "f": smoke.loc[smoke["model_id"].eq("gears_hcc_formal_v1")],
        "g": smoke.loc[smoke["model_id"].isin(["geneformer_hcc_formal_v1", "scgpt_hcc_formal_v1"])],
        "h": smoke.loc[smoke["model_id"].eq("null_model")],
    }
    def a(ax, df): _barh(ax, df.assign(label=df["model_id"].map(short_model_label)), "label", "backbone_recovery_score", "Full model backbone ranking", "Backbone recovery", "a", COLORS["baseline"])
    def metric(metric, label, color, panel):
        return lambda ax, df: _barh(ax, df.groupby("cell_line", as_index=False)[metric].mean(), "cell_line", metric, label, metric, panel, color)
    _run_figure("extended_data_figure4", "edfig4", "Full HCC model recovery detail", "build_extended_data_figure4.py", "reports/manuscript_extended_data_v1/edfig4_model_detail", input_rel, sources, dict(zip(list("abcdefgh"), [a, metric("backbone_recovery_score", "Per-cell-line backbone", COLORS["primary_qualified"], "b"), metric("shift_excess_identification_score", "Per-cell-line shift-excess", COLORS["supporting"], "c"), metric("structure_vs_context_separation_score", "Per-cell-line separation", COLORS["gears"], "d"), metric("top20_overlap_mean", "Baseline top20 overlap", COLORS["baseline"], "e"), metric("top20_overlap_mean", "GEARS top20 overlap", COLORS["gears"], "f"), metric("top20_overlap_mean", "Foundation top20 overlap", COLORS["foundation"], "g"), metric("top20_overlap_mean", "Null top20 overlap", "#BDBDBD", "h")])), {k: v for k, v in zip(list("abcdefgh"), ["Ranking", "Backbone", "Shift-excess", "Separation", "Baseline", "GEARS", "Foundation", "Null"])}, "Full model details support a backbone-separation trade-off, not model recovery proof.", panels_only)


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
        "e": comp.loc[comp["model_id"].str.contains("gears_hcc_formal_v1") | comp["model_id"].eq("shared_mean_baseline")],
        "f": pd.DataFrame([{"rule": "stop", "baseline_backbone": baseline, "best_sweep_backbone": sweep["backbone_recovery_score"].max(), "decision": "do not promote GEARS as primary winner"}]),
        "g": cand[["variant_id", "epochs", "lr", "weight_decay", "candidate_rank"]],
        "h": pd.DataFrame([{"boundary": "GEARS training", "status": "not rerun in figure stage"}, {"boundary": "predictions/scores", "status": "frozen and hashed"}, {"boundary": "recipe search", "status": "finite-budget control"}]),
    }
    def a(ax, df):
        rows = [(r.variant_id, f"rank {r.candidate_rank}; e{r.epochs}; lr={r.lr}") for r in df.itertuples()]
        _short_text_panel(ax, "Sweep candidate manifest", rows, "a", split=0.44)
    def b(ax, df):
        plot = df.groupby(["phase", "status"], as_index=False)["n"].sum()
        _barh(ax, plot.assign(label=plot["phase"] + " " + plot["status"]), "label", "n", "Batch status log", "Events", "b", "#8A8A8A")
    def c(ax, df): _barh(ax, df.assign(label=df["model_id"].str.replace("gears_hcc_formal_v1_", "", regex=False)), "label", "backbone_recovery_score", "Sweep backbone scores", "Backbone", "c", COLORS["gears"])
    def d(ax, df): _barh(ax, df.assign(label=df["model_id"].str.replace("gears_hcc_formal_v1_", "", regex=False)), "label", "structure_vs_context_separation_score", "Sweep separation scores", "Separation", "d", COLORS["supporting"])
    def e(ax, df):
        ax.scatter(df["backbone_recovery_score"], df["shift_excess_identification_score"], c=[COLORS["baseline"] if m == "shared_mean_baseline" else COLORS["gears"] for m in df["model_id"]], s=40)
        ax.set_xlabel("Backbone"); ax.set_ylabel("Shift-excess"); ax.set_title("Baseline versus sweep candidates", loc="left"); clean_axes(ax); ax.grid(color=COLORS["grid"], linewidth=0.5); add_panel_label(ax, "e")
    def f(ax, df): _text_panel(ax, "Stop-rule adjudication", [("baseline", f"{df.baseline_backbone.iloc[0]:.3f}"), ("best sweep", f"{df.best_sweep_backbone.iloc[0]:.3f}"), ("decision", df.decision.iloc[0])], "f")
    def g(ax, df): _text_panel(ax, "Recipe dimensions", [(r.variant_id, f"e{r.epochs}, lr={r.lr}, wd={r.weight_decay}") for r in df.itertuples()], "g")
    def h(ax, df): _text_panel(ax, "Training exemption", [(r.boundary, r.status) for r in df.itertuples()], "h")
    _run_figure("extended_data_figure5", "edfig5", "GEARS sweep and stop rule", "build_extended_data_figure5.py", "reports/manuscript_extended_data_v1/edfig5_gears_sweep", input_rel, sources, dict(zip(list("abcdefgh"), [a, b, c, d, e, f, g, h])), {k: v for k, v in zip(list("abcdefgh"), ["Candidate manifest", "Batch status", "Backbone", "Separation", "Trade-off", "Stop rule", "Recipe", "Boundary"])}, "GEARS sweep is finite-budget control and training is not rerun during figure generation.", panels_only)


def build_edfig7(panels_only: bool = False) -> None:
    root = repo_root()
    input_rel = ["reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_bridge_summary.tsv", "reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_structure_summary.tsv", "reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_panel_calls.tsv", "reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_7d/dixit_evidence_tier_summary.tsv", "reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_evidence_tier_summary.tsv"]
    bridge = pd.read_csv(root / input_rel[0], sep="\t")
    struct = pd.read_csv(root / input_rel[1], sep="\t")
    calls = pd.read_csv(root / input_rel[2], sep="\t")
    t7 = pd.read_csv(root / input_rel[3], sep="\t").assign(timepoint="7d")
    t13 = pd.read_csv(root / input_rel[4], sep="\t").assign(timepoint="13d")
    primary = bridge.loc[bridge["truth_metric"].eq("real_shift_mean_abs") & bridge["depmap_endpoint"].eq("depmap_gene_dependency")]
    vals = primary.set_index("timepoint")
    if vals.loc["7d", "aligned_spearman"] <= vals.loc["13d", "aligned_spearman"] or vals.loc["13d", "mean_truth_metric"] <= vals.loc["7d", "mean_truth_metric"]:
        raise RuntimeError("ED Fig. 7 sanity check failed: temporal stratification changed.")
    tiers = pd.concat([t7, t13], ignore_index=True)
    sources = {"a": bridge.loc[bridge["timepoint"].eq("7d")], "b": bridge.loc[bridge["timepoint"].eq("13d")], "c": primary, "d": struct, "e": t7, "f": t13, "g": calls, "h": tiers}
    def bridge_bar(panel, title):
        return lambda ax, df: _barh(ax, df.assign(label=df["truth_metric"]), "label", "aligned_spearman", title, "Spearman", panel, COLORS["primary_qualified"])
    def c(ax, df):
        plot = df.copy()
        plot["rank_bridge_norm"] = plot["aligned_spearman"] / plot["aligned_spearman"].max()
        plot["mean_shift_norm"] = plot["mean_truth_metric"] / plot["mean_truth_metric"].max()
        x = range(len(plot))
        ax.bar([i - 0.18 for i in x], plot["rank_bridge_norm"], width=0.34, color=COLORS["baseline"], label="rank bridge")
        ax.bar([i + 0.18 for i in x], plot["mean_shift_norm"], width=0.34, color=COLORS["gears"], label="mean shift")
        ax.set_xticks(list(x)); ax.set_xticklabels(plot["timepoint"])
        ax.set_ylim(0, 1.15); ax.set_ylabel("Normalized value")
        ax.set_title("Temporal stratification", loc="left"); ax.legend(frameon=False); clean_axes(ax); ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5); add_panel_label(ax, "c")
    def d(ax, df): _barh(ax, df.assign(label=df["timepoint"] + " " + df["comparison_field"]), "label", df.assign(n=1)["n"].name if False else "n", "", "", "d")
    def d(ax, df):
        plot = df.groupby(["timepoint", "replication_status"], as_index=False).size().rename(columns={"size": "n"}); _barh(ax, plot.assign(label=plot["timepoint"] + " " + plot["replication_status"]), "label", "n", "Temporal structure calls", "Calls", "d", "#777777")
    def tier(panel, title):
        return lambda ax, df: _barh(ax, df.groupby("evidence_tier", as_index=False).size().rename(columns={"size": "n"}), "evidence_tier", "n", title, "Objects", panel, COLORS["supporting"])
    def g(ax, df): _short_text_panel(ax, "Temporal panel call", [("rank bridge", "not stronger at 13d"), ("mean shift", "stronger at 13d"), ("boundary", "13d formal; 7d sensitivity")], "g")
    def h(ax, df): _barh(ax, df.groupby(["timepoint", "evidence_tier"], as_index=False).size().rename(columns={"size": "n"}).assign(label=lambda x: x["timepoint"] + " " + x["evidence_tier"]), "label", "n", "A0/A1/B tier distribution", "Objects", "h", "#8A8A8A")
    _run_figure("extended_data_figure7", "edfig7", "K562 temporal evidence detail", "build_extended_data_figure7.py", "reports/manuscript_extended_data_v1/edfig7_k562_temporal", input_rel, sources, dict(zip(list("abcdefgh"), [bridge_bar("a", "7d bridge summary"), bridge_bar("b", "13d bridge summary"), c, d, tier("e", "7d evidence tiers"), tier("f", "13d evidence tiers"), g, h])), {k: v for k, v in zip(list("abcdefgh"), ["7d bridge", "13d bridge", "Temporal comparison", "Structure", "7d tiers", "13d tiers", "Panel call", "Tier distribution"])}, "K562 is supplementary temporal architecture evidence, not a primary co-pillar.", panels_only)


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
    sources = {"a": hcc, "b": k562, "c": consistency, "d": conv, "e": bridge, "f": claim.loc[claim["object"].isin(["Replogle_RNAi_expansion_candidate", "global_truth_depmap_bridge"])], "g": bridge, "h": claim.loc[claim["object"].str.contains("RNAi|global|Dixit", regex=True)]}
    def endpoint(panel, title):
        return lambda ax, df: _barh(ax, df.loc[df["summary_kind"].eq("truth_endpoint_bridge") & df["truth_metric"].eq("real_shift_mean_abs") & df["depmap_endpoint"].eq("depmap_gene_dependency")].assign(label=lambda x: x["timepoint"].astype(str) + " " + x["platform_pair"]), "label", "spearman", title, "Spearman", panel, COLORS["primary_qualified"])
    def c(ax, df): _barh(ax, df.assign(label=df["timepoint"].astype(str)), "label", "spearman", "CRISPR-RNAi endpoint agreement", "Spearman", "c", "#777777")
    def d(ax, df):
        keep = ["score_direction", "input_cell_lines", "mapped_cell_lines", "genes"]
        plot = df.loc[df["metric"].isin(keep)].copy()
        rows = [(r.metric.replace("_", " "), str(r.value)) for r in plot.itertuples()]
        _short_text_panel(ax, "DEMETER2 conversion summary", rows, "d")
    def e(ax, df):
        piv = df.pivot_table(index="timepoint", columns="platform_pair", values="spearman").reset_index()
        ax.bar(range(len(piv)), piv["crispr"], width=0.35, color=COLORS["baseline"], label="CRISPR"); ax.bar([i+0.35 for i in range(len(piv))], piv["rnai"], width=0.35, color="#BDBDBD", label="RNAi")
        ax.set_xticks([i+0.175 for i in range(len(piv))]); ax.set_xticklabels(piv["timepoint"], rotation=20, ha="right"); ax.set_ylabel("Spearman"); ax.set_title("Endpoint hierarchy", loc="left"); ax.legend(frameon=False); clean_axes(ax); ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5); add_panel_label(ax, "e")
    def f(ax, df): _short_text_panel(ax, "RNAi sensitivity boundary", [("global bridge", "retainable global claim"), ("RNAi expansion", "admission required")], "f")
    def g(ax, df): _barh(ax, df.assign(delta=df.groupby("timepoint")["spearman"].transform(lambda s: s.max() - s.min())).drop_duplicates("timepoint").assign(label=lambda x: x["timepoint"].astype(str)), "label", "delta", "CRISPR-RNAi bridge gap", "Spearman gap", "g", COLORS["boundary"])
    def h(ax, df): _short_text_panel(ax, "Endpoint claim boundary", [("CRISPR", "primary bridge readout"), ("RNAi", "weaker sensitivity endpoint"), ("K562", "supplementary evidence"), ("discovery", "not formal primary")], "h")
    _run_figure("extended_data_figure8", "edfig8", "CRISPR versus RNAi endpoint detail", "build_extended_data_figure8.py", "reports/manuscript_extended_data_v1/edfig8_endpoint_hierarchy", input_rel, sources, dict(zip(list("abcdefgh"), [endpoint("a", "HCC endpoint bridge"), endpoint("b", "K562 endpoint bridge"), c, d, e, f, g, h])), {k: v for k, v in zip(list("abcdefgh"), ["HCC", "K562", "Agreement", "Conversion", "Hierarchy", "Boundary", "Gap", "Claims"])}, "CRISPR is the primary bridge endpoint; RNAi is a weaker sensitivity endpoint.", panels_only)


def main_edfig1(argv: list[str] | None = None) -> None:
    build_edfig1(_parser("Build ED Fig. 1").parse_args(argv).panels_only)


def main_edfig2(argv: list[str] | None = None) -> None:
    build_edfig2(_parser("Build ED Fig. 2").parse_args(argv).panels_only)


def main_edfig4(argv: list[str] | None = None) -> None:
    build_edfig4(_parser("Build ED Fig. 4").parse_args(argv).panels_only)


def main_edfig5(argv: list[str] | None = None) -> None:
    build_edfig5(_parser("Build ED Fig. 5").parse_args(argv).panels_only)


def main_edfig7(argv: list[str] | None = None) -> None:
    build_edfig7(_parser("Build ED Fig. 7").parse_args(argv).panels_only)


def main_edfig8(argv: list[str] | None = None) -> None:
    build_edfig8(_parser("Build ED Fig. 8").parse_args(argv).panels_only)
