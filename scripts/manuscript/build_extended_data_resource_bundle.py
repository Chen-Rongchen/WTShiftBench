from __future__ import annotations

import math
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

COLORS = {
    "green": "#009E73",
    "blue": "#0072B2",
    "orange": "#D55E00",
    "purple": "#CC79A7",
    "yellow": "#B59B1B",
    "gray": "#8F8F8F",
    "light": "#F3F3F3",
    "dark": "#333333",
    "red": "#B55D5A",
}

CAT_COLORS = {
    "Q1_anchor": COLORS["green"],
    "shift_excess": COLORS["orange"],
    "dependency_excess": COLORS["purple"],
    "Q4_low_information": COLORS["gray"],
    "low_information": COLORS["gray"],
    "middle": "#56B4E9",
}

MODEL_LABELS = {
    "scgen_hcc_formal_v1": "scGen",
    "cpa_v0.8.8": "CPA",
    "gears_hcc_formal_v1": "GEARS",
    "cellot_hcc_formal_v1": "CellOT",
    "scgpt_hcc_formal_v1": "scGPT",
    "geneformer_hcc_formal_v1": "Geneformer",
    "lm_train_lowrank_hcc_formal_v1": "low-rank",
    "lm_g_scgpt_ridge_hcc_formal_v1": "scGPT-ridge",
    "lm_g_geneformer_ridge_hcc_formal_v1": "Geneformer-ridge",
    "shared_mean_baseline": "shared mean",
    "null_model": "null",
}

MODEL_ORDER = list(MODEL_LABELS)


def read_tsv(path: str | Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / path, sep="\t", **kwargs)


def ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def out_dirs(fig_id: int) -> tuple[Path, Path, Path, Path]:
    public = ensure(ROOT / "figures" / f"Extended_Data_Figure_{fig_id}")
    public_panels = ensure(public / "panels")
    build = ensure(ROOT / "figure_build" / "output" / f"Extended_Data_Figure_{fig_id}")
    build_panels = ensure(build / "panels")
    return public, public_panels, build, build_panels


def save(fig: plt.Figure, public_path: Path, build_path: Path) -> None:
    fig.savefig(public_path.with_suffix(".png"), dpi=600, bbox_inches="tight")
    fig.savefig(public_path.with_suffix(".pdf"), bbox_inches="tight")
    shutil.copy2(public_path.with_suffix(".png"), build_path.with_suffix(".png"))
    shutil.copy2(public_path.with_suffix(".pdf"), build_path.with_suffix(".pdf"))
    plt.close(fig)


def write_source(df: pd.DataFrame, public_path: Path, build_path: Path) -> None:
    df.to_csv(public_path, sep="\t", index=False)
    shutil.copy2(public_path, build_path)


def panel_heading(ax: plt.Axes, letter: str, title: str) -> None:
    ax.text(0, 1.08, f"{letter}  {title}", transform=ax.transAxes, ha="left", va="bottom", weight="bold", fontsize=9)


def clean(ax: plt.Axes, *, light_grid: bool = False, grid_axis: str = "both") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=7)
    if light_grid:
        ax.grid(True, axis=grid_axis, color="#F5F5F5", linewidth=0.35, zorder=0)
    else:
        ax.grid(False)


def table_panel(ax: plt.Axes, df: pd.DataFrame, letter: str, title: str, *, font: float = 6.5, scale_y: float = 1.25) -> None:
    ax.axis("off")
    panel_heading(ax, letter, title)
    d = df.copy()
    for col in d.columns:
        d[col] = d[col].astype(str).str.slice(0, 42)
    tab = ax.table(cellText=d.values, colLabels=d.columns, loc="center", cellLoc="left", colLoc="left")
    tab.auto_set_font_size(False)
    tab.set_fontsize(font)
    tab.scale(1, scale_y)
    for (r, _), cell in tab.get_celld().items():
        cell.set_edgecolor("#DDDDDD")
        cell.set_linewidth(0.35)
        if r == 0:
            cell.set_facecolor("#EFEFEF")
            cell.set_text_props(weight="bold")


def compact_table_panel(
    ax: plt.Axes,
    df: pd.DataFrame,
    letter: str,
    title: str,
    *,
    columns: list[str] | None = None,
    max_rows: int = 8,
    font: float = 5.6,
    scale_y: float = 1.12,
) -> None:
    d = df.copy()
    if columns is not None:
        keep = [c for c in columns if c in d.columns]
        d = d[keep]
    d = d.head(max_rows)
    table_panel(ax, d, letter, title, font=font, scale_y=scale_y)


def status_matrix_panel(ax: plt.Axes, df: pd.DataFrame, letter: str, title: str, row_col: str, cols: list[str]) -> pd.DataFrame:
    panel_heading(ax, letter, title)
    d = df[[row_col] + [c for c in cols if c in df.columns]].copy().head(12)
    status = d.set_index(row_col)
    numeric = status.map(lambda x: 1.0 if str(x).lower() in {"estimated", "yes", "true", "primary", "sensitivity"} else 0.35)
    ax.imshow(numeric.to_numpy(), aspect="auto", cmap="Greens", vmin=0, vmax=1)
    ax.set_yticks(range(len(numeric.index)))
    ax.set_yticklabels(numeric.index.astype(str).str.slice(0, 22), fontsize=5.2)
    ax.set_xticks(range(len(numeric.columns)))
    ax.set_xticklabels([c.replace("_", "\n") for c in numeric.columns], fontsize=5.4)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return d


def fdr_family_matrix(ax: plt.Axes, df: pd.DataFrame, letter: str, title: str) -> pd.DataFrame:
    panel_heading(ax, letter, title)
    families = [
        "total_endpoint_alignment",
        "axis_aligned_endpoint_alignment",
        "anchor_separation",
        "target_identity",
        "residual_endpoint_recovery",
    ]
    columns = ["rho", "AUC", "permutation", "q-value"]
    rows = []
    for fam in families:
        sub = df.loc[df["metric_family"].eq(fam)]
        row = {"metric_family": fam}
        joined = " ".join(sub.astype(str).to_numpy().ravel().tolist()).lower()
        row["rho"] = float("rho" in joined or "spearman" in joined)
        row["AUC"] = float("auc" in joined)
        row["permutation"] = float("permutation" in joined or "pvalue" in joined)
        row["q-value"] = float("qvalue" in joined)
        rows.append(row)
    out = pd.DataFrame(rows)
    mat = out[columns].to_numpy()
    ax.imshow(mat, aspect="auto", cmap="Greens", vmin=0, vmax=1)
    ax.set_yticks(range(len(out)))
    ax.set_yticklabels(out["metric_family"].str.replace("_", " "), fontsize=5.6)
    ax.set_xticks(range(len(columns)))
    ax.set_xticklabels(columns, fontsize=6)
    ax.tick_params(length=0)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, "yes" if mat[i, j] else "-", ha="center", va="center", fontsize=5.4, color="#222222")
    for spine in ax.spines.values():
        spine.set_visible(False)
    return out


def ora_dot_panel(ax: plt.Axes, df: pd.DataFrame, letter: str, title: str) -> pd.DataFrame:
    panel_heading(ax, letter, title)
    d = df.sort_values(["padj", "pvalue"]).head(10).copy()
    d["label"] = d["context"].astype(str) + " " + d["endpoint_category"].astype(str) + " / " + d["pathway"].astype(str).str.slice(0, 22)
    y = np.arange(len(d))
    color_map = {"Q1_anchor": COLORS["green"], "Q4_low_information": COLORS["gray"], "middle": "#56B4E9"}
    colors = d["endpoint_category"].map(color_map).fillna(COLORS["orange"])
    sizes = 24 + d["n_overlap"].fillna(0).astype(float) * 18
    ax.scatter(d["n_overlap"], y, s=sizes, c=colors, edgecolor="white", linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels(d["label"], fontsize=5.0)
    ax.invert_yaxis()
    ax.set_xlabel("Overlap count")
    ax.text(0.02, -0.16, "Descriptive target-membership annotation only", transform=ax.transAxes, fontsize=5.3, color="#555555")
    clean(ax)
    return d


def binary_matrix(
    ax: plt.Axes,
    mat: pd.DataFrame,
    letter: str,
    title: str,
    *,
    yes_label: str = "yes",
    no_label: str = "-",
) -> None:
    panel_heading(ax, letter, title)
    values = mat.astype(float).to_numpy()
    ax.imshow(values, aspect="auto", cmap="Greens", vmin=0, vmax=1)
    ax.set_yticks(range(len(mat.index)))
    ax.set_yticklabels(mat.index.astype(str).str.slice(0, 26), fontsize=5.4)
    ax.set_xticks(range(len(mat.columns)))
    ax.set_xticklabels([str(c).replace("_", "\n") for c in mat.columns], fontsize=5.5)
    ax.tick_params(length=0)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, yes_label if values[i, j] >= 0.5 else no_label, ha="center", va="center", fontsize=5.2)
    for spine in ax.spines.values():
        spine.set_visible(False)


def registry_role_matrix(ax: plt.Axes, registry: pd.DataFrame, letter: str, title: str) -> pd.DataFrame:
    d = registry.copy()
    d["label"] = d["model_name"].astype(str).str.slice(0, 24)
    roles = ["primary_entrant", "embedding_control", "diagnostic_control", "excluded"]
    mat = pd.DataFrame(0.0, index=d["label"], columns=roles)
    for _, row in d.iterrows():
        role = row.get("included_role", "")
        if role in roles:
            mat.loc[row["label"], role] = 1.0
    binary_matrix(ax, mat, letter, title)
    return mat.reset_index(names="model_name")


def regime_matrix(ax: plt.Axes, regime: pd.DataFrame, letter: str, title: str) -> pd.DataFrame:
    d = regime.copy()
    d["label"] = d["model_id"].map(MODEL_LABELS).fillna(d["model_id"]).astype(str).str.slice(0, 26)
    mat = pd.DataFrame(
        {
            "formal": d["selection_role"].eq("pre_specified_formal").astype(float).to_numpy(),
            "sensitivity": d["selection_role"].str.contains("sensitivity", na=False).astype(float).to_numpy(),
            "endpoint selected": d["endpoint_used_for_selection"].astype(bool).astype(float).to_numpy(),
        },
        index=d["label"],
    )
    binary_matrix(ax, mat, letter, title)
    return mat.reset_index(names="model_id")


def hash_size_panel(ax: plt.Axes, hashes: pd.DataFrame, letter: str, title: str) -> pd.DataFrame:
    panel_heading(ax, letter, title)
    d = hashes.copy()
    label_col = "artifact_role" if "artifact_role" in d.columns else "artifact"
    d["size_mb"] = pd.to_numeric(d["size_bytes"], errors="coerce").fillna(0) / 1_000_000
    d = d.sort_values("size_mb", ascending=False).head(10)
    ax.barh(d[label_col].astype(str).str.slice(0, 28), d["size_mb"], color=COLORS["gray"])
    ax.invert_yaxis()
    ax.set_xlabel("Artifact size (MB)")
    clean(ax)
    return d


def manifest_coverage_panel(ax: plt.Axes, manifest: pd.DataFrame, letter: str, title: str) -> pd.DataFrame:
    panel_heading(ax, letter, title)
    d = manifest.groupby("figure_group").agg(n_files=("path", "count"), total_mb=("bytes", lambda x: float(pd.to_numeric(x, errors="coerce").fillna(0).sum()) / 1_000_000)).reset_index()
    d = d.sort_values("figure_group")
    ax.scatter(d["total_mb"], np.arange(len(d)), s=18 + d["n_files"] * 2.5, color=COLORS["green"], alpha=0.85, edgecolor="white", linewidth=0.5)
    ax.set_yticks(np.arange(len(d)))
    ax.set_yticklabels(d["figure_group"].astype(str).str.replace("_", " "), fontsize=5.5)
    ax.set_xlabel("Source-data size (MB); point size = files")
    clean(ax)
    return d


def qc_availability_panel(ax: plt.Axes, qc: pd.DataFrame, letter: str, title: str) -> pd.DataFrame:
    panel_heading(ax, letter, title)
    d = qc.copy()
    d["label"] = d["context"] + "\n" + d["contrast_id"].str.replace("_", " ")
    d["n_targets_total"] = d["n_targets_positive"] + d["n_targets_negative"]
    y = np.arange(len(d))
    ax.scatter(d["n_genes"], y, s=20 + d["n_targets_total"] * 3.5, color=COLORS["green"], edgecolor="white", linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels(d["label"], fontsize=5.6)
    ax.set_xlabel("Ranked genes; point size = targets in contrast")
    clean(ax)
    return d


def finish_figure(fig_id: int, panels: dict[str, pd.DataFrame]) -> None:
    public, _, build, _ = out_dirs(fig_id)
    combined = pd.concat([v.assign(panel=k) for k, v in panels.items()], ignore_index=True, sort=False)
    write_source(
        combined,
        public / f"Extended_Data_Figure_{fig_id}_source_data.tsv",
        build / f"Extended_Data_Figure_{fig_id}_source_data.tsv",
    )


def save_panel(fig_id: int, letter: str, fig: plt.Figure, source: pd.DataFrame) -> None:
    _, pp, _, bp = out_dirs(fig_id)
    stem = f"Extended_Data_Figure_{fig_id}_panel_{letter}"
    save(fig, pp / stem, bp / stem)
    write_source(source, pp / f"{stem}_source_data.tsv", bp / f"{stem}_source_data.tsv")


def ed1() -> None:
    fig_id = 1
    a = read_tsv("figures/Extended_Data_Figure_1/panels/Extended_Data_Figure_1_panel_a_source_data.tsv")
    emb = []
    for letter in "bcdef":
        p = ROOT / f"figures/Extended_Data_Figure_1/panels/Extended_Data_Figure_1_panel_{letter}_source_data.tsv"
        if p.exists():
            d = pd.read_csv(p, sep="\t")
            if "context" not in d.columns:
                d["context"] = "Replogle K562"
            emb.append(d)
    b = pd.concat(emb, ignore_index=True)
    expr = []
    for letter, context in zip("ghijk", ["HCC38", "HCC1143", "K562 7d", "K562 13d", "Replogle essential"]):
        p = ROOT / f"figures/Extended_Data_Figure_1/panels/Extended_Data_Figure_1_panel_{letter}_source_data.tsv"
        if p.exists():
            d = pd.read_csv(p, sep="\t")
            d["context"] = context
            d["delta"] = d["expression_perturbed"] - d["expression_control"]
            expr.append(d)
    c = pd.concat(expr, ignore_index=True)

    fig = plt.figure(figsize=(11, 7))
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.2], hspace=0.45, wspace=0.35)
    ax_a = fig.add_subplot(gs[0, :])
    table_panel(ax_a, a[["dataset_label", "role", "cells_or_models", "features", "benchmark_use"]], "a", "Dataset inventory", font=6.2)
    ax_b = fig.add_subplot(gs[1, :2])
    panel_heading(ax_b, "b", "Perturbation-level embedding")
    for ctx, d in b.groupby("context"):
        ax_b.scatter(d["umap1"], d["umap2"], s=np.where(d["is_control"], 44, 12), label=ctx, alpha=np.where(d["is_control"], 1, 0.65), edgecolor="white", linewidth=0.25)
    ax_b.set_xlabel("UMAP 1")
    ax_b.set_ylabel("UMAP 2")
    ax_b.legend(frameon=False, fontsize=5.5, ncol=2)
    clean(ax_b)
    ax_c = fig.add_subplot(gs[1, 2])
    panel_heading(ax_c, "c", "Target-expression readout")
    summary = c.groupby("context")["delta"].agg(["median", "mean"]).reset_index()
    ax_c.axvline(0, color="#BBBBBB", linewidth=0.8)
    ax_c.barh(summary["context"], summary["median"], color=np.where(summary["median"] < 0, COLORS["blue"], COLORS["orange"]))
    ax_c.set_xlabel("Median perturbed-control expression")
    clean(ax_c)
    save(fig, *[d / "Extended_Data_Figure_1" for d in (out_dirs(fig_id)[0], out_dirs(fig_id)[2])])
    panels = {"a": a, "b": b, "c": c}
    finish_figure(fig_id, panels)
    for k, src in panels.items():
        pf = plt.figure(figsize=(5, 3))
        ax = pf.add_subplot(111)
        if k == "a":
            table_panel(ax, a[["dataset_label", "role", "cells_or_models", "features", "benchmark_use"]], "a", "Dataset inventory")
        elif k == "b":
            panel_heading(ax, "b", "Perturbation-level embedding")
            for ctx, d in b.groupby("context"):
                ax.scatter(d["umap1"], d["umap2"], s=np.where(d["is_control"], 44, 12), label=ctx, alpha=0.7)
            ax.legend(frameon=False, fontsize=6)
            clean(ax)
        else:
            panel_heading(ax, "c", "Target-expression readout")
            ax.axvline(0, color="#BBBBBB", linewidth=0.8)
            ax.barh(summary["context"], summary["median"], color=np.where(summary["median"] < 0, COLORS["blue"], COLORS["orange"]))
            clean(ax)
        save_panel(fig_id, k, pf, src)


def ed2() -> None:
    fig_id = 2
    panel_a = read_tsv("figures/Extended_Data_Figure_2/panels/Extended_Data_Figure_2_panel_a_source_data.tsv")
    panel_b = read_tsv("figures/Extended_Data_Figure_2/panels/Extended_Data_Figure_2_panel_b_source_data.tsv")
    panel_c = read_tsv("reports/manuscript_extended_data_v1/edfig13_metric_robustness/panels/edfig13_paneld_source_data.tsv")
    leave = read_tsv("reports/truth_driven_bridge/sensitivity/leave_anchor_out_summary.tsv")
    cutoff = read_tsv("reports/truth_bridge_decomposition/anchor_cutoff_sensitivity.tsv")
    cov = read_tsv("reports/truth_driven_bridge/sensitivity/covariate_balance/summary.tsv")
    tier = read_tsv("reports/truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv")
    panels = {
        "a": panel_a.copy(),
        "b": panel_b.copy(),
        "c": panel_c.copy(),
        "d": leave,
        "e": cutoff,
        "f": cov,
    }
    fig = plt.figure(figsize=(12, 8.5))
    gs = fig.add_gridspec(2, 3, hspace=0.42, wspace=0.35)
    ax = fig.add_subplot(gs[0, 0]); panel_heading(ax, "a", "Alternative shift metrics")
    d = panels["a"].dropna(subset=["aligned_spearman"]).copy()
    d["top_n_numeric"] = pd.to_numeric(d["top_n"], errors="coerce")
    d = d.loc[d["top_n_numeric"].isin([100, 500, 1000, 2000])]
    for metric, g in d.groupby("truth_metric"):
        gg = g.groupby("top_n_numeric")["aligned_spearman"].mean().reset_index()
        ax.plot(gg["top_n_numeric"], gg["aligned_spearman"], marker="o", label=metric.replace("real_shift_", ""))
    ax.set_xlabel("Top n genes"); ax.set_ylabel("Spearman ρ"); ax.legend(frameon=False, fontsize=6); clean(ax)
    ax = fig.add_subplot(gs[0, 1]); panel_heading(ax, "b", "Endpoint sensitivity")
    d = panels["b"].dropna(subset=["spearman_rho_aligned"]).copy()
    show = d.loc[d["truth_metric"].isin(["real_shift_mean_abs", "real_shift_L2"])].copy()
    show = show.groupby(["truth_metric", "depmap_endpoint"])["spearman_rho_aligned"].mean().reset_index().head(12)
    ax.barh(np.arange(len(show)), show["spearman_rho_aligned"], color=COLORS["green"])
    ax.set_yticks(np.arange(len(show))); ax.set_yticklabels((show["truth_metric"] + "\n" + show["depmap_endpoint"]).str.replace("depmap_", ""), fontsize=5)
    ax.set_xlabel("Mean Spearman ρ"); clean(ax)
    ax = fig.add_subplot(gs[0, 2]); panel_heading(ax, "c", "Control subsampling")
    d = panels["c"].dropna(subset=["spearman_aligned_mean"]).copy()
    y = np.arange(len(d))
    ax.errorbar(d["spearman_aligned_mean"], y, xerr=[d["spearman_aligned_mean"]-d["spearman_aligned_q025"], d["spearman_aligned_q975"]-d["spearman_aligned_mean"]], fmt="o", color=COLORS["blue"])
    ax.set_yticks(y); ax.set_yticklabels(d["cell_line"].astype(str), fontsize=6); ax.set_xlabel("rho"); clean(ax)
    ax = fig.add_subplot(gs[1, 0]); panel_heading(ax, "d", "Anchor-influence jackknife")
    for ctx, g in leave.groupby("context"):
        ax.plot(g["spearman_rho"], np.arange(len(g)) + (0.08 if ctx == "HCC1143" else -0.08), "o", label=ctx)
    ax.set_yticks(np.arange(len(leave["removed"].unique()))); ax.set_yticklabels(leave["removed"].drop_duplicates(), fontsize=6); ax.set_xlabel("rho after removal"); ax.legend(frameon=False, fontsize=6); clean(ax)
    ax = fig.add_subplot(gs[1, 1]); panel_heading(ax, "e", "Category cutoff sensitivity")
    q1 = cutoff.loc[cutoff["joint_grid"].eq("Q1_anchor")]
    for cell, g in q1.groupby("cell_line"):
        ax.plot(g["quantile_high"], g["fraction_targets"], marker="o", label=cell)
    ax.set_xlabel("High quantile cutoff"); ax.set_ylabel("Fraction Q1 anchors"); ax.legend(frameon=False, fontsize=6); clean(ax)
    ax = fig.add_subplot(gs[1, 2]); panel_heading(ax, "f", "Covariate TVD audit")
    cov2 = cov.copy()
    cov2["label"] = cov2["cell_line"] + " " + cov2["strat_column"].str.replace("_", " ").str.slice(0, 18)
    cov2 = cov2.sort_values("mean_tvd").tail(12)
    ax.barh(cov2["label"], cov2["mean_tvd"], color=np.where(cov2["n_targets_tvd_gt_0.25"] > 0, COLORS["orange"], COLORS["gray"]))
    ax.set_xlabel("Mean target-control TVD"); clean(ax)
    save(fig, *[d / "Extended_Data_Figure_2" for d in (out_dirs(fig_id)[0], out_dirs(fig_id)[2])])
    finish_figure(fig_id, panels)
    for k, src in panels.items():
        figp = plt.figure(figsize=(4, 3))
        axp = figp.add_subplot(111)
        table_panel(axp, src.head(12), k, {"a":"Alternative shift metrics","b":"Endpoint sensitivity","c":"Control subsampling","d":"Anchor-influence jackknife","e":"Cutoff sensitivity","f":"Covariate TVD"}[k], font=5.2)
        save_panel(fig_id, k, figp, src)


def _external_data(context: str) -> pd.DataFrame:
    summary = read_tsv("reports/external_bridge_form_robustness/observed_shift_depmap_bridge_summary.tsv")
    row = summary.loc[summary["context"].eq(context)].iloc[0]
    df = pd.read_csv(ROOT / row["source_path"], sep="\t")
    df = df.loc[df["depmap_gene_dependency"].notna() & df["real_shift_mean_abs"].notna()].copy()
    df["context"] = context
    return df


def ed3() -> None:
    fig_id = 3
    contexts = ["K562 TF day 7", "K562 TF day 13", "K562 essential CRISPRi day 6", "K562 genome-scale CRISPRi day 8", "HepG2 day 7", "Jurkat day 7"]
    summary = read_tsv("reports/external_bridge_form_robustness/observed_shift_depmap_bridge_summary.tsv")
    panels = {chr(97+i): _external_data(ctx) for i, ctx in enumerate(contexts)}
    panels["g"] = summary.loc[summary["context"].isin(contexts)].copy()
    fig = plt.figure(figsize=(12, 9))
    gs = fig.add_gridspec(3, 3, hspace=0.45, wspace=0.35)
    for i, ctx in enumerate(contexts):
        ax = fig.add_subplot(gs[i//3, i%3])
        letter = chr(97+i)
        panel_heading(ax, letter, ctx)
        d = panels[letter]
        plot = d.sample(min(len(d), 2500), random_state=1) if len(d) > 2500 else d
        ax.scatter(plot["depmap_gene_dependency"], plot["real_shift_mean_abs"], s=8, color=COLORS["blue"], alpha=0.35, edgecolors="none")
        r = summary.loc[summary["context"].eq(ctx)].iloc[0]
        ax.text(0.04, 0.96, f"Spearman ρ = {r['spearman_rho']:.3f}\nn = {int(r['n_targets_matched_depmap']):,}; P = {r['spearman_permutation_pvalue']:.3g}", transform=ax.transAxes, va="top", fontsize=7)
        ax.set_xlabel("Dependency strength (-DepMap)")
        ax.set_ylabel("Observed shift mean abs")
        clean(ax)
    ax = fig.add_subplot(gs[2, :])
    panel_heading(ax, "g", "External bridge calibration summary")
    d = panels["g"].sort_values("spearman_rho")
    xerr = np.vstack([d["spearman_rho"] - d["spearman_bootstrap_ci_low"], d["spearman_bootstrap_ci_high"] - d["spearman_rho"]])
    ax.errorbar(d["spearman_rho"], np.arange(len(d)), xerr=xerr, fmt="o", color=COLORS["green"])
    ax.axvline(0, color="#BBBBBB", linewidth=0.8)
    ax.set_yticks(np.arange(len(d))); ax.set_yticklabels(d["context"], fontsize=7)
    ax.set_xlabel("Spearman ρ with bootstrap CI")
    clean(ax)
    save(fig, *[d / "Extended_Data_Figure_3" for d in (out_dirs(fig_id)[0], out_dirs(fig_id)[2])])
    finish_figure(fig_id, panels)
    for k, src in panels.items():
        figp = plt.figure(figsize=(4, 3))
        axp = figp.add_subplot(111)
        if k != "g":
            panel_heading(axp, k, src["context"].iloc[0])
            plot = src.sample(min(len(src), 2500), random_state=1) if len(src) > 2500 else src
            axp.scatter(plot["depmap_gene_dependency"], plot["real_shift_mean_abs"], s=8, color=COLORS["blue"], alpha=0.4, edgecolors="none")
            clean(axp)
        else:
            table_panel(axp, src[["context","n_targets_matched_depmap","spearman_rho","spearman_permutation_pvalue","claim_role"]], "g", "External bridge calibration", font=5.2)
        save_panel(fig_id, k, figp, src)


def ed4() -> None:
    fig_id = 4
    registry = read_tsv("resource_registry/model_entrant_registry.tsv")
    regime = read_tsv("reports/model_endpoint_recovery/source_data/model_registry.tsv")
    metrics = read_tsv("reports/model_endpoint_recovery/source_data/model_endpoint_recovery_metrics.tsv")
    hashes = read_tsv("reports/model_endpoint_recovery/closure_artifact_hashes.tsv")
    figsrc = read_tsv("resource_registry/figure_source_data_manifest.tsv")
    panels = {
        "a": registry,
        "b": regime,
        "c": metrics[["model_id","cell_line","total_shift_depmap_status","axis_aligned_depmap_status","target_identity_preservation_status"]].copy(),
        "d": registry[["model_name","included_role","claim_ceiling"]].copy(),
        "e": hashes,
        "f": figsrc,
    }
    fig = plt.figure(figsize=(12, 8))
    gs = fig.add_gridspec(3, 2, hspace=0.5, wspace=0.25)
    titles = {"a":"Model family inclusion matrix","b":"Training/evaluation regime","c":"Output-contract availability","d":"Inclusion/exclusion audit","e":"Artifact hash closure","f":"Figure/source-data manifest"}
    ax = fig.add_subplot(gs[0, 0])
    panels["a_display"] = registry_role_matrix(ax, panels["a"], "a", titles["a"])
    ax = fig.add_subplot(gs[0, 1])
    panels["b_display"] = regime_matrix(ax, panels["b"], "b", titles["b"])
    ax = fig.add_subplot(gs[1, 0])
    status_matrix_panel(ax, panels["c"], "c", titles["c"], "model_id", ["total_shift_depmap_status", "axis_aligned_depmap_status", "target_identity_preservation_status"])
    ax = fig.add_subplot(gs[1, 1])
    include = panels["d"].copy()
    include["included"] = include["included_role"].ne("excluded").astype(float)
    include["excluded/future"] = include["included_role"].eq("excluded").astype(float)
    include_mat = include.set_index(include["model_name"].astype(str).str.slice(0, 24))[["included", "excluded/future"]]
    binary_matrix(ax, include_mat, "d", titles["d"])
    panels["d_display"] = include_mat.reset_index(names="model_name")
    ax = fig.add_subplot(gs[2, 0])
    panels["e_display"] = hash_size_panel(ax, panels["e"], "e", titles["e"])
    ax = fig.add_subplot(gs[2, 1])
    panels["f_display"] = manifest_coverage_panel(ax, panels["f"], "f", titles["f"])
    save(fig, *[d / "Extended_Data_Figure_4" for d in (out_dirs(fig_id)[0], out_dirs(fig_id)[2])])
    finish_figure(fig_id, {k: v for k, v in panels.items() if not k.endswith("_display")})
    for k, src in panels.items():
        if k.endswith("_display"):
            continue
        figp = plt.figure(figsize=(5, 3))
        axp = figp.add_subplot(111)
        if k == "a":
            registry_role_matrix(axp, src, k, titles[k])
        elif k == "b":
            regime_matrix(axp, src, k, titles[k])
        elif k == "c":
            status_matrix_panel(axp, src, k, titles[k], "model_id", ["total_shift_depmap_status", "axis_aligned_depmap_status", "target_identity_preservation_status"])
        elif k == "d":
            include = src.copy()
            include["included"] = include["included_role"].ne("excluded").astype(float)
            include["excluded/future"] = include["included_role"].eq("excluded").astype(float)
            binary_matrix(axp, include.set_index(include["model_name"].astype(str).str.slice(0, 24))[["included", "excluded/future"]], k, titles[k])
        elif k == "e":
            hash_size_panel(axp, src, k, titles[k])
        else:
            manifest_coverage_panel(axp, src, k, titles[k])
        save_panel(fig_id, k, figp, src)


def ed5() -> None:
    fig_id = 5
    metrics = read_tsv("reports/model_endpoint_recovery/source_data/model_endpoint_recovery_metrics.tsv")
    pq = read_tsv("reports/model_endpoint_recovery/source_data/model_endpoint_recovery_pq_values.tsv")
    gears = metrics.loc[metrics["model_id"].str.contains("gears_hcc_formal_v1", regex=False)].copy()
    target = read_tsv("reports/model_endpoint_recovery/target_summary.tsv")
    bridge = read_tsv("reports/external_bridge_form_robustness/observed_shift_depmap_bridge_summary.tsv")
    panels = {
        "a": metrics[["model_id","cell_line","total_shift_depmap_spearman","total_shift_depmap_pvalue","total_shift_depmap_qvalue","total_shift_depmap_status"]].copy(),
        "b": metrics[["model_id","cell_line","axis_aligned_depmap_spearman","axis_aligned_depmap_pvalue","axis_aligned_depmap_qvalue","axis_aligned_endpoint_permutation_qvalue"]].copy(),
        "c": metrics[["model_id","cell_line","anchor_vs_low_information_axis_auc"]].copy(),
        "d": pq,
        "e": gears,
        "f": target.loc[target["model_id"].isin(["null_model","shared_mean_baseline"])].copy(),
        "g": bridge.loc[bridge["evidence_layer"].eq("primary_model_audit")].copy(),
    }
    fig = plt.figure(figsize=(12, 9))
    gs = fig.add_gridspec(3, 3, hspace=0.5, wspace=0.35)
    specs = [
        ("a","Total-shift permutation/q", "total_shift_depmap_spearman", "total_shift_depmap_qvalue"),
        ("b","Axis-aligned permutation/q", "axis_aligned_depmap_spearman", "axis_aligned_depmap_qvalue"),
        ("c","Anchor separation AUC", "anchor_vs_low_information_axis_auc", None),
    ]
    for idx, (k, title, val, q) in enumerate(specs):
        ax = fig.add_subplot(gs[0, idx]); panel_heading(ax, k, title)
        d = panels[k].dropna(subset=[val]).copy()
        d["label"] = d["model_id"].map(MODEL_LABELS).fillna(d["model_id"]) + " " + d["cell_line"].str.replace("HCC","")
        priority = ["scgen_hcc_formal_v1", "cpa_v0.8.8", "gears_hcc_formal_v1", "cellot_hcc_formal_v1", "scgpt_hcc_formal_v1", "geneformer_hcc_formal_v1", "shared_mean_baseline", "null_model"]
        d = d.loc[d["model_id"].isin(priority)].head(16)
        ax.barh(d["label"], d[val], color=COLORS["blue"])
        ax.tick_params(axis="y", labelsize=5)
        ax.set_xlabel(val.replace("_", " "))
        clean(ax)
    ax = fig.add_subplot(gs[1, 0])
    panels["d_display"] = fdr_family_matrix(ax, panels["d"], "d", "FDR family matrix")
    ax = fig.add_subplot(gs[1, 1]); panel_heading(ax, "e", "GEARS formal versus sweep")
    d = panels["e"].dropna(subset=["axis_aligned_depmap_spearman"]).copy()
    ax.scatter(d["axis_aligned_depmap_spearman"], d["anchor_vs_low_information_axis_auc"], c=np.where(d["model_id"].eq("gears_hcc_formal_v1"), COLORS["green"], COLORS["orange"]), s=42)
    ax.set_xlabel("Axis Spearman ρ"); ax.set_ylabel("Anchor AUC"); clean(ax)
    ax = fig.add_subplot(gs[1, 2]); panel_heading(ax, "f", "Null/reference output structure")
    d = panels["f"].groupby(["model_id","cell_line"])["predicted_shift_mean_abs"].nunique().reset_index(name="unique_total_shift")
    ax.barh(d["model_id"].map(MODEL_LABELS).fillna(d["model_id"]) + " " + d["cell_line"].str.replace("HCC",""), d["unique_total_shift"], color=COLORS["gray"])
    ax.set_xlabel("Unique target-level total shifts"); clean(ax)
    ax = fig.add_subplot(gs[2, :]); panel_heading(ax, "g", "Observed-shift oracle / truth-side ceiling")
    d = panels["g"].sort_values("spearman_rho")
    y = np.arange(len(d))
    xerr = np.vstack([d["spearman_rho"] - d["spearman_bootstrap_ci_low"], d["spearman_bootstrap_ci_high"] - d["spearman_rho"]])
    ax.errorbar(d["spearman_rho"], y, xerr=xerr, fmt="o", color=COLORS["green"], ecolor=COLORS["green"], elinewidth=1.2, capsize=2)
    ax.set_yticks(y); ax.set_yticklabels(d["context"], fontsize=6)
    ax.set_xlabel("Observed-shift Spearman ρ with 95% CI")
    ax.axvline(0, color="#BBBBBB", linewidth=0.8)
    clean(ax, light_grid=True, grid_axis="x")
    save(fig, *[d / "Extended_Data_Figure_5" for d in (out_dirs(fig_id)[0], out_dirs(fig_id)[2])])
    finish_figure(fig_id, {k: v for k, v in panels.items() if k != "d_display"})
    for k, src in panels.items():
        if k.endswith("_display"):
            continue
        figp = plt.figure(figsize=(5, 3)); axp = figp.add_subplot(111)
        if k == "g":
            panel_heading(axp, k, "Oracle ceiling")
            d = src.sort_values("spearman_rho")
            y = np.arange(len(d))
            xerr = np.vstack([d["spearman_rho"] - d["spearman_bootstrap_ci_low"], d["spearman_bootstrap_ci_high"] - d["spearman_rho"]])
            axp.errorbar(d["spearman_rho"], y, xerr=xerr, fmt="o", color=COLORS["green"], ecolor=COLORS["green"], elinewidth=1.2, capsize=2)
            axp.set_yticks(y); axp.set_yticklabels(d["context"], fontsize=6)
            axp.set_xlabel("Observed-shift Spearman ρ with 95% CI")
            axp.axvline(0, color="#BBBBBB", linewidth=0.8)
            clean(axp, light_grid=True, grid_axis="x")
        else:
            table_panel(axp, src.head(12), k, {"a":"Total-shift calibration","b":"Axis calibration","c":"AUC calibration","d":"FDR families","e":"GEARS sensitivity","f":"Shuffle/null structure","g":"Oracle ceiling"}[k], font=5.2)
        save_panel(fig_id, k, figp, src)


def _axis_heat(ax: plt.Axes, df: pd.DataFrame, model: str, cell: str, letter: str, title: str) -> pd.DataFrame:
    d = df.loc[df["model_id"].eq(model) & df["cell_line"].eq(cell)].copy()
    pivot = d.pivot_table(index="target_gene", columns="fine_axis", values="projected_mean_abs", aggfunc="mean").fillna(0)
    top_targets = pivot.sum(axis=1).sort_values(ascending=False).head(14).index
    top_axes = pivot.sum(axis=0).sort_values(ascending=False).head(8).index
    mat = pivot.loc[top_targets, top_axes]
    panel_heading(ax, letter, title)
    im = ax.imshow(mat, aspect="auto", cmap="viridis")
    ax.set_yticks(range(len(mat.index))); ax.set_yticklabels(mat.index, fontsize=5)
    ax.set_xticks(range(len(mat.columns))); ax.set_xticklabels(mat.columns, rotation=45, ha="right", fontsize=5)
    plt.colorbar(im, ax=ax, fraction=0.03, pad=0.01)
    return mat.reset_index().melt(id_vars="target_gene", var_name="fine_axis", value_name="projected_mean_abs")


def ed6() -> None:
    fig_id = 6
    metrics = read_tsv("reports/model_endpoint_recovery/source_data/model_endpoint_recovery_metrics.tsv")
    common = read_tsv("reports/model_endpoint_recovery/source_data/model_common_response_metrics.tsv")
    identity = read_tsv("reports/model_endpoint_recovery/source_data/model_target_identity_preservation.tsv")
    axis = read_tsv("reports/model_endpoint_recovery/axis_projection.tsv")
    panels = {"a": common, "b": identity, "d": identity}
    fig = plt.figure(figsize=(12, 9))
    gs = fig.add_gridspec(3, 3, hspace=0.55, wspace=0.45)
    ax = fig.add_subplot(gs[0, 0]); panel_heading(ax, "a", "Common-response metrics")
    display_models = ["scgen_hcc_formal_v1", "cpa_v0.8.8", "gears_hcc_formal_v1", "cellot_hcc_formal_v1", "shared_mean_baseline", "null_model"]
    d = common.loc[common["model_id"].isin(display_models)].copy()
    d["label"] = d["model_id"].map(MODEL_LABELS).fillna(d["model_id"]) + " " + d["cell_line"].str.replace("HCC","")
    mat = d.set_index("label")[["mean_stress_axis_share","mean_top_axis_share","mean_target_axis_cosine_proxy"]].head(22)
    im = ax.imshow(mat, aspect="auto", cmap="magma")
    ax.set_yticks(range(len(mat.index))); ax.set_yticklabels(mat.index, fontsize=5)
    ax.set_xticks(range(len(mat.columns))); ax.set_xticklabels(["stress","top-axis","target cosine"], rotation=35, ha="right", fontsize=6)
    plt.colorbar(im, ax=ax, fraction=0.03, pad=0.01)
    ax = fig.add_subplot(gs[0, 1]); panel_heading(ax, "b", "Observed target-identity reference")
    obs = identity.groupby("cell_line")["observed_target_similarity_mean"].mean().reset_index()
    ax.barh(obs["cell_line"], obs["observed_target_similarity_mean"], color=COLORS["gray"])
    ax.set_xlabel("Observed mean similarity"); clean(ax)
    ax = fig.add_subplot(gs[0, 2]); panel_heading(ax, "d", "Target-identity preservation")
    d = identity.loc[identity["target_identity_preservation_status"].eq("estimated")].copy()
    ax.scatter(d["target_identity_preservation_spearman"], d["target_identity_label_permutation_qvalue"], s=34, c=d["model_id"].map({m: i for i,m in enumerate(MODEL_ORDER)}), cmap="tab20", edgecolor="white", linewidth=0.4)
    ax.set_xlabel("Identity Spearman ρ"); ax.set_ylabel("label-permutation q"); clean(ax)
    panels["c"] = _axis_heat(fig.add_subplot(gs[1, 0]), axis, "scgen_hcc_formal_v1", "HCC1143", "c", "scGen HCC1143 axis profile")
    panels["e"] = _axis_heat(fig.add_subplot(gs[1, 1]), axis, "cpa_v0.8.8", "HCC1143", "e", "CPA HCC1143 axis profile")
    panels["f"] = _axis_heat(fig.add_subplot(gs[1, 2]), axis, "shared_mean_baseline", "HCC1143", "f", "Shared mean HCC1143 axis profile")
    ax = fig.add_subplot(gs[2, :]); panel_heading(ax, "g", "Alternative common-response score sensitivity")
    comp = metrics[["model_id","cell_line","mean_top_axis_share","mean_stress_axis_share","mean_target_axis_cosine_proxy","common_response_score","endpoint_recovery_score"]].copy()
    comp["label"] = comp["model_id"].map(MODEL_LABELS).fillna(comp["model_id"]) + " " + comp["cell_line"].str.replace("HCC","")
    comp = comp.head(20)
    ax.scatter(comp["endpoint_recovery_score"], comp["common_response_score"], s=45, color=COLORS["green"], alpha=0.8)
    for _, r in comp.iterrows():
        if r["model_id"] in ["scgen_hcc_formal_v1","cpa_v0.8.8","shared_mean_baseline"]:
            ax.text(r["endpoint_recovery_score"], r["common_response_score"], r["label"], fontsize=6)
    ax.set_xlabel("Endpoint recovery score"); ax.set_ylabel("Common-response score"); clean(ax)
    panels["g"] = comp
    save(fig, *[d / "Extended_Data_Figure_6" for d in (out_dirs(fig_id)[0], out_dirs(fig_id)[2])])
    finish_figure(fig_id, panels)
    for k, src in panels.items():
        figp = plt.figure(figsize=(5, 3)); axp = figp.add_subplot(111)
        table_panel(axp, src.head(12), k, f"ED6 panel {k}", font=5.0)
        save_panel(fig_id, k, figp, src)


def ed7() -> None:
    fig_id = 7
    qc = read_tsv("reports/category_response_pathway/contrasts/category_response_contrast_qc.tsv")
    hall = read_tsv("reports/category_response_pathway/contrasts/category_response_contrast_gsea_hallmark.tsv")
    react = read_tsv("reports/category_response_pathway/contrasts/category_response_contrast_gsea_reactome.tsv")
    gobp = read_tsv("reports/category_response_pathway/contrasts/category_response_contrast_gsea_gobp.tsv")
    ora = read_tsv("reports/category_response_pathway/target_set_ora_descriptive.tsv")
    hashes = read_tsv("reports/category_response_pathway/contrasts/artifact_hashes.tsv")
    panels = {"a": qc, "b": hall, "c": react, "d": gobp, "e": hall.loc[hall["contrast_id"].str.contains("Q4_low_information", na=False)].copy(), "f": hall.loc[hall["contrast_id"].str.contains("middle", na=False)].copy(), "g": ora, "h": hashes}
    fig = plt.figure(figsize=(12, 9))
    gs = fig.add_gridspec(3, 3, hspace=0.5, wspace=0.45)
    ax = fig.add_subplot(gs[0, 0]); panels["a_display"] = qc_availability_panel(ax, qc, "a", "Response-signature construction QC")
    for idx, (k, title, df) in enumerate([("b","Hallmark NES",hall),("c","Reactome sensitivity",react),("d","GO BP sensitivity",gobp)]):
        ax = fig.add_subplot(gs[(idx+1)//3, (idx+1)%3])
        panel_heading(ax, k, title)
        top = df.assign(absNES=lambda x: x["NES"].abs()).sort_values("absNES", ascending=False).head(12)
        ax.scatter(top["NES"], np.arange(len(top)), s=np.maximum(18, -np.log10(top["padj"].clip(lower=1e-6))*15), c=np.where(top["NES"] > 0, COLORS["orange"], COLORS["blue"]), alpha=0.85)
        ax.axvline(0, color="#BBBBBB", linewidth=0.8)
        ax.set_yticks(np.arange(len(top))); ax.set_yticklabels(top["pathway"].str.slice(0, 34), fontsize=5)
        ax.set_xlabel("NES"); clean(ax)
    for idx, (k, title) in enumerate([("e","Anchor vs low-information"),("f","Anchor vs middle")]):
        ax = fig.add_subplot(gs[1, idx+1])
        panel_heading(ax, k, title)
        d = panels[k].assign(absNES=lambda x: x["NES"].abs()).sort_values("absNES", ascending=False).head(10)
        ax.barh(d["pathway"].str.slice(0, 34), d["NES"], color=np.where(d["NES"] > 0, COLORS["orange"], COLORS["blue"]))
        ax.tick_params(axis="y", labelsize=5); ax.set_xlabel("NES"); clean(ax)
    ax = fig.add_subplot(gs[2, 0])
    panels["g_display"] = ora_dot_panel(ax, ora, "g", "Descriptive target-set ORA")
    ax = fig.add_subplot(gs[2, 1:])
    panels["h_display"] = hash_size_panel(ax, hashes, "h", "Gene-set/source-data provenance")
    save(fig, *[d / "Extended_Data_Figure_7" for d in (out_dirs(fig_id)[0], out_dirs(fig_id)[2])])
    finish_figure(fig_id, {k: v for k, v in panels.items() if k != "g_display"})
    for k, src in panels.items():
        if k.endswith("_display"):
            continue
        figp = plt.figure(figsize=(5, 3)); axp = figp.add_subplot(111)
        if k == "a":
            qc_availability_panel(axp, src, k, "Response-signature construction QC")
        elif k == "h":
            hash_size_panel(axp, src, k, "Gene-set/source-data provenance")
        else:
            table_panel(axp, src.head(12), k, f"ED7 panel {k}", font=5.0)
        save_panel(fig_id, k, figp, src)


def main() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.linewidth": 0.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    for fn in [ed1, ed2, ed3, ed4, ed5, ed6, ed7]:
        fn()
    print("Built Extended Data Figures 1-7")


if __name__ == "__main__":
    main()
