from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, ListedColormap


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

PAPER_TEAL_CMAP = LinearSegmentedColormap.from_list(
    "paper_teal",
    ["#F9F7EE", "#E9F4F0", "#8DBAB2", "#3B827A"],
)

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

MODEL_COLORS = {
    "scgen_hcc_formal_v1": "#009E73",
    "cpa_v0.8.8": "#D55E00",
    "gears_hcc_formal_v1": "#0072B2",
    "cellot_hcc_formal_v1": "#E69F00",
    "scgpt_hcc_formal_v1": "#8C78B8",
    "geneformer_hcc_formal_v1": "#CC79A7",
    "lm_train_lowrank_hcc_formal_v1": "#8F8F8F",
    "lm_g_scgpt_ridge_hcc_formal_v1": "#B0B0B0",
    "lm_g_geneformer_ridge_hcc_formal_v1": "#6F6F6F",
    "shared_mean_baseline": "#333333",
    "null_model": "#D9D9D9",
}

MODEL_ORDER = list(MODEL_LABELS)


def read_tsv(path: str | Path, **kwargs) -> pd.DataFrame:
    kwargs.setdefault("comment", "#")
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
    fig.savefig(public_path.with_suffix(".svg"), bbox_inches="tight")
    shutil.copy2(public_path.with_suffix(".png"), build_path.with_suffix(".png"))
    shutil.copy2(public_path.with_suffix(".pdf"), build_path.with_suffix(".pdf"))
    shutil.copy2(public_path.with_suffix(".svg"), build_path.with_suffix(".svg"))
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


def format_p_value(value: float) -> str:
    p = float(value)
    return "P = 0.001" if p <= 0.001 else f"P = {p:.3f}"


def display_endpoint_text(value: object) -> str:
    text = str(value)
    replacements = {
        "Q1_anchor": "endpoint anchors",
        "Q4_low_information": "low-information",
        "Q4_low_info": "low-information",
        "Q2_transcriptomic_excess": "shift-excess",
        "Q3_dependency_excess": "dependency-excess",
        "Q1 anchor": "endpoint anchors",
        "Q4 low info": "low-information",
        "Q4 low-information": "low-information",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


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
    columns = ["Spearman ρ", "AUC", "permutation", "q-value"]
    rows = []
    for fam in families:
        sub = df.loc[df["metric_family"].eq(fam)]
        row = {"metric_family": fam}
        joined = " ".join(sub.astype(str).to_numpy().ravel().tolist()).lower()
        row["Spearman ρ"] = float("rho" in joined or "spearman" in joined)
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
    d["label"] = (
        d["context"].astype(str).map(display_endpoint_text)
        + " "
        + d["endpoint_category"].astype(str).map(display_endpoint_text)
        + " / "
        + d["pathway"].astype(str).map(display_endpoint_text).str.slice(0, 22)
    )
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
    d["label"] = d["context"].map(display_endpoint_text) + "\n" + d["contrast_id"].map(display_endpoint_text).str.replace("_", " ")
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
    a_legacy = read_tsv("reports/manuscript_extended_data_v1/edfig1_dataset_familiarization/panels/edfig1_panela_source_data.tsv")
    bridge_summary = read_tsv("reports/external_bridge_form_robustness/observed_shift_depmap_bridge_summary.tsv")
    hepg2_jurkat_qc = read_tsv("reports/external_bridge_form_robustness/candidate_endpoint_extension_eligibility.tsv")
    emb = []
    for letter in "bcdef":
        p = ROOT / f"reports/manuscript_extended_data_v1/edfig1_dataset_familiarization/panels/edfig1_panel{letter}_source_data.tsv"
        if p.exists():
            d = pd.read_csv(p, sep="\t")
            if "context" not in d.columns:
                d["context"] = "Replogle K562"
            emb.append(d)
    b = pd.concat(emb, ignore_index=True)
    expr = []
    for letter, context in zip("ghijk", ["HCC38", "HCC1143", "K562 7d", "K562 13d", "Replogle essential"]):
        p = ROOT / f"reports/manuscript_extended_data_v1/edfig1_dataset_familiarization/panels/edfig1_panel{letter}_source_data.tsv"
        if p.exists():
            d = pd.read_csv(p, sep="\t")
            d["context"] = context
            d["delta"] = d["expression_perturbed"] - d["expression_control"]
            expr.append(d)
    c = pd.concat(expr, ignore_index=True)

    qc_lookup = {row.context: row for row in hepg2_jurkat_qc.itertuples()}
    role_label_map = {
        "primary_model_audit": "Primary",
        "candidate_secondary_endpoint_extension": "Secondary extension",
        "external_bridge_form_boundary": "Temporal boundary",
    }
    rows = []
    for row in bridge_summary.itertuples():
        role = role_label_map.get(row.evidence_layer, row.evidence_layer)
        if "Replogle" in row.context or "CRISPRi" in row.context:
            role = "Scale/modality boundary"
        cells = f"{int(row.n_targets_matched_depmap)} matched targets"
        if row.context in qc_lookup:
            qc = qc_lookup[row.context]
            cells = f"{int(qc.n_obs)} cells"
            features = f"{int(qc.n_vars)} genes"
            use = f"{int(row.n_targets_matched_depmap)} matched targets"
        else:
            features = str(row.shift_metric).replace("_", " ")
            use = f"{int(row.n_targets_matched_depmap)} matched targets"
        rows.append(
            {
                "dataset_label": row.context,
                "role": role,
                "cells_or_models": cells,
                "features": features,
                "benchmark_use": use,
            }
        )
    endpoint_rows = (
        a_legacy.loc[a_legacy["dataset_kind"].eq("endpoint_dataset"), ["dataset_label", "role", "cells_or_models", "features", "benchmark_use"]]
        .copy()
        .assign(role=lambda d: d["role"].map({"primary endpoint": "Endpoint", "sensitivity endpoint": "Sensitivity endpoint"}).fillna(d["role"]))
    )
    a = pd.concat([pd.DataFrame(rows), endpoint_rows], ignore_index=True)

    role_map = {
        "Primary": "Primary",
        "Secondary extension": "Secondary extension",
        "Temporal boundary": "Temporal boundary",
        "Scale/modality boundary": "Scale/modality boundary",
        "Endpoint": "Endpoint",
        "Sensitivity endpoint": "Sensitivity endpoint",
    }
    role_colors = {
        "Primary": COLORS["green"],
        "Secondary extension": COLORS["yellow"],
        "Temporal boundary": COLORS["blue"],
        "Scale/modality boundary": COLORS["purple"],
        "Endpoint": COLORS["orange"],
        "Sensitivity endpoint": COLORS["gray"],
    }
    role_cols = ["Primary", "Secondary extension", "Temporal boundary", "Scale/modality boundary", "Endpoint", "Sensitivity endpoint"]
    context_order = ["HCC38", "HCC1143", "K562 7d", "K562 13d", "Replogle K562"]
    context_labels = {
        "HCC38": "HCC38",
        "HCC1143": "HCC1143",
        "K562 7d": "K562 TF day 7",
        "K562 13d": "K562 TF day 13",
        "Replogle K562": "Replogle K562\nessential",
    }
    expr_order = ["HCC38", "HCC1143", "K562 7d", "K562 13d", "Replogle essential"]
    expr_labels = {
        "HCC38": "HCC38",
        "HCC1143": "HCC1143",
        "K562 7d": "K562 TF day 7",
        "K562 13d": "K562 TF day 13",
        "Replogle essential": "Replogle K562\nessential",
    }

    def draw_dataset_inventory(ax: plt.Axes, source: pd.DataFrame) -> None:
        ax.set_axis_off()
        panel_heading(ax, "a", "Dataset inventory")
        work = source.copy()
        work["display_role"] = work["role"].map(role_map).fillna(work["role"])
        y = np.arange(len(work))[::-1]
        x_lookup = {name: i for i, name in enumerate(role_cols)}
        for row_idx, row in enumerate(work.itertuples()):
            ypos = y[row_idx]
            role = row.display_role
            xpos = x_lookup.get(role, 0)
            ax.scatter(
                xpos,
                ypos,
                s=52,
                color=role_colors.get(role, COLORS["gray"]),
                edgecolor="white",
                linewidth=0.6,
                zorder=3,
            )
            ax.text(-0.55, ypos, row.dataset_label, ha="right", va="center", fontsize=6.5)
            size_text = str(row.cells_or_models).replace(",", "")
            use_text = str(row.benchmark_use).replace(",", "")
            if len(use_text) > 42:
                use_text = use_text[:39] + "..."
            detail = size_text if size_text == use_text else f"{size_text}; {use_text}"
            ax.text(len(role_cols) - 0.05, ypos, detail, ha="left", va="center", fontsize=6.0, color="#4A4A4A")
        for i, col in enumerate(role_cols):
            ax.text(i, len(work) + 0.15, col, ha="center", va="bottom", fontsize=6.1, fontweight="bold", rotation=18)
        for ypos in y:
            ax.plot([-0.2, len(role_cols) - 0.8], [ypos, ypos], color="#EFEFEF", lw=0.6, zorder=1)
        ax.set_xlim(-1.25, len(role_cols) + 3.0)
        ax.set_ylim(-0.8, len(work) + 0.75)

    def draw_umap_facet(ax: plt.Axes, source: pd.DataFrame, context: str, *, show_y: bool) -> None:
        d = source.loc[source["context"].eq(context)].copy()
        if d.empty and context == "Replogle K562":
            d = source.loc[source["context"].isna() | source["context"].eq("")].copy()
        controls = d.loc[d["is_control"].astype(bool)]
        pert = d.loc[~d["is_control"].astype(bool)]
        ax.scatter(
            pert["umap1"],
            pert["umap2"],
            s=9 if len(pert) < 500 else 3,
            color="#A9C8C0",
            alpha=0.58,
            edgecolor="none",
            rasterized=len(pert) > 2000,
        )
        hi = pert.loc[pert.get("is_highlight", False).astype(bool)] if "is_highlight" in pert else pd.DataFrame()
        if not hi.empty:
            ax.scatter(hi["umap1"], hi["umap2"], s=20, color=COLORS["green"], alpha=0.9, edgecolor="white", linewidth=0.35, zorder=4)
        if not controls.empty:
            ax.scatter(controls["umap1"], controls["umap2"], s=30, color="#E58D7C", edgecolor="white", linewidth=0.45, zorder=5)
        ax.set_title(context_labels.get(context, context), fontsize=6.8, pad=2)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_box_aspect(1)
        for spine in ax.spines.values():
            spine.set_visible(False)
        if show_y:
            ax.set_ylabel("UMAP", fontsize=6.5)

    def draw_expression_facet(ax: plt.Axes, source: pd.DataFrame, context: str, *, show_y: bool, xlim: tuple[float, float]) -> None:
        d = source.loc[source["context"].eq(context)].copy()
        color = COLORS["blue"] if d["delta"].median() < 0 else COLORS["orange"]
        ax.hist(d["delta"], bins=24, color=color, alpha=0.78, edgecolor="white", linewidth=0.25)
        ax.axvline(0, color="#9E9E9E", lw=0.7, ls=(0, (2, 2)))
        ax.axvline(d["delta"].median(), color="#222222", lw=0.8)
        ax.set_xlim(*xlim)
        ax.set_title(expr_labels.get(context, context), fontsize=6.8, pad=2)
        ax.set_yticks([])
        ax.tick_params(axis="x", labelsize=5.5)
        clean(ax)
        ax.grid(False)
        if show_y:
            ax.set_ylabel("Targets", fontsize=6.3)

    def draw_panel_a_only(source: pd.DataFrame) -> plt.Figure:
        pf = plt.figure(figsize=(7.0, 2.0))
        draw_dataset_inventory(pf.add_subplot(111), source)
        return pf

    def draw_panel_b_only(source: pd.DataFrame) -> plt.Figure:
        pf = plt.figure(figsize=(8.4, 2.0))
        sub = pf.add_gridspec(1, 5, wspace=0.22, left=0.06, right=0.995, bottom=0.10, top=0.78)
        first_ax = pf.add_subplot(sub[0, 0])
        panel_heading(first_ax, "b", "Perturbation-level embeddings")
        draw_umap_facet(first_ax, source, context_order[0], show_y=True)
        for idx, context in enumerate(context_order[1:], start=1):
            draw_umap_facet(pf.add_subplot(sub[0, idx]), source, context, show_y=False)
        handles = [
            plt.Line2D([0], [0], marker="o", color="none", markerfacecolor="#A9C8C0", markeredgecolor="none", markersize=4, label="perturbation"),
            plt.Line2D([0], [0], marker="o", color="none", markerfacecolor="#E58D7C", markeredgecolor="white", markeredgewidth=0.4, markersize=5, label="control"),
        ]
        pf.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.52, -0.005), ncol=2, frameon=False, fontsize=6)
        return pf

    def draw_panel_c_only(source: pd.DataFrame) -> plt.Figure:
        pf = plt.figure(figsize=(8.4, 2.1))
        xlim = (float(source["delta"].quantile(0.01)), float(source["delta"].quantile(0.99)))
        pad = (xlim[1] - xlim[0]) * 0.05
        xlim = (xlim[0] - pad, xlim[1] + pad)
        sub = pf.add_gridspec(1, 5, wspace=0.25, left=0.06, right=0.995, bottom=0.20, top=0.76)
        first_ax = pf.add_subplot(sub[0, 0])
        panel_heading(first_ax, "c", "Target-expression readout")
        draw_expression_facet(first_ax, source, expr_order[0], show_y=True, xlim=xlim)
        for idx, context in enumerate(expr_order[1:], start=1):
            draw_expression_facet(pf.add_subplot(sub[0, idx]), source, context, show_y=False, xlim=xlim)
        pf.text(0.52, 0.04, "Perturbed − control target-gene expression", ha="center", va="center", fontsize=6.6)
        handles = [
            plt.Line2D([0], [0], color="#222222", lw=0.8, label="median"),
            plt.Line2D([0], [0], color="#9E9E9E", lw=0.7, ls=(0, (2, 2)), label="zero change"),
        ]
        pf.legend(handles=handles, loc="lower right", bbox_to_anchor=(0.99, 0.005), frameon=False, fontsize=5.8, ncol=2)
        return pf

    fig = plt.figure(figsize=(11, 7.3))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.05, 1.0, 1.0], hspace=0.38)
    draw_dataset_inventory(fig.add_subplot(gs[0]), a[["dataset_label", "role", "cells_or_models", "features", "benchmark_use"]])
    b_grid = gs[1].subgridspec(1, 5, wspace=0.22)
    ax_b0 = fig.add_subplot(b_grid[0, 0])
    panel_heading(ax_b0, "b", "Perturbation-level embeddings")
    draw_umap_facet(ax_b0, b, context_order[0], show_y=True)
    for idx, context in enumerate(context_order[1:], start=1):
        draw_umap_facet(fig.add_subplot(b_grid[0, idx]), b, context, show_y=False)
    fig.legend(
        handles=[
            plt.Line2D([0], [0], marker="o", color="none", markerfacecolor="#A9C8C0", markeredgecolor="none", markersize=4, label="perturbation"),
            plt.Line2D([0], [0], marker="o", color="none", markerfacecolor="#E58D7C", markeredgecolor="white", markeredgewidth=0.4, markersize=5, label="control"),
        ],
        loc="center",
        bbox_to_anchor=(0.82, 0.415),
        ncol=2,
        frameon=False,
        fontsize=6,
    )
    c_grid = gs[2].subgridspec(1, 5, wspace=0.25)
    xlim = (float(c["delta"].quantile(0.01)), float(c["delta"].quantile(0.99)))
    pad = (xlim[1] - xlim[0]) * 0.05
    xlim = (xlim[0] - pad, xlim[1] + pad)
    ax_c0 = fig.add_subplot(c_grid[0, 0])
    panel_heading(ax_c0, "c", "Target-expression readout")
    draw_expression_facet(ax_c0, c, expr_order[0], show_y=True, xlim=xlim)
    for idx, context in enumerate(expr_order[1:], start=1):
        draw_expression_facet(fig.add_subplot(c_grid[0, idx]), c, context, show_y=False, xlim=xlim)
    fig.text(0.53, 0.035, "Perturbed − control target-gene expression", ha="center", va="center", fontsize=6.8)
    fig.legend(
        handles=[
            plt.Line2D([0], [0], color="#222222", lw=0.8, label="median"),
            plt.Line2D([0], [0], color="#9E9E9E", lw=0.7, ls=(0, (2, 2)), label="zero change"),
        ],
        loc="lower right",
        bbox_to_anchor=(0.98, 0.018),
        ncol=2,
        frameon=False,
        fontsize=5.9,
    )
    save(fig, *[d / "Extended_Data_Figure_1" for d in (out_dirs(fig_id)[0], out_dirs(fig_id)[2])])
    panels = {"a": a, "b": b, "c": c}
    finish_figure(fig_id, panels)
    panel_figures = {
        "a": draw_panel_a_only(a[["dataset_label", "role", "cells_or_models", "features", "benchmark_use"]]),
        "b": draw_panel_b_only(b),
        "c": draw_panel_c_only(c),
    }
    for k, pf in panel_figures.items():
        save_panel(fig_id, k, pf, panels[k])


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
    ax.set_yticks(y); ax.set_yticklabels(d["cell_line"].astype(str), fontsize=6); ax.set_xlabel("Spearman ρ"); clean(ax)
    ax = fig.add_subplot(gs[1, 0]); panel_heading(ax, "d", "Anchor-influence jackknife")
    for ctx, g in leave.groupby("context"):
        ax.plot(g["spearman_rho"], np.arange(len(g)) + (0.08 if ctx == "HCC1143" else -0.08), "o", label=ctx)
    ax.set_yticks(np.arange(len(leave["removed"].unique()))); ax.set_yticklabels(leave["removed"].drop_duplicates(), fontsize=6); ax.set_xlabel("Spearman ρ after removal"); ax.legend(frameon=False, fontsize=6); clean(ax)
    ax = fig.add_subplot(gs[1, 1]); panel_heading(ax, "e", "Category cutoff sensitivity")
    q1 = cutoff.loc[cutoff["joint_grid"].eq("Q1_anchor")]
    for cell, g in q1.groupby("cell_line"):
        ax.plot(g["quantile_high"], g["fraction_targets"], marker="o", label=cell)
    ax.set_xlabel("High quantile cutoff"); ax.set_ylabel("Fraction endpoint anchors"); ax.legend(frameon=False, fontsize=6); clean(ax)
    ax = fig.add_subplot(gs[1, 2]); panel_heading(ax, "f", "Covariate TVD audit")
    cov2 = cov.copy()
    cov2["label"] = cov2["cell_line"] + " " + cov2["strat_column"].str.replace("_", " ").str.slice(0, 18)
    cov2 = cov2.sort_values("mean_tvd").tail(12)
    ax.barh(cov2["label"], cov2["mean_tvd"], color=np.where(cov2["n_targets_tvd_gt_0.25"] > 0, COLORS["orange"], COLORS["gray"]))
    ax.set_xlabel("Mean target-control TVD"); clean(ax)
    save(fig, *[d / "Extended_Data_Figure_2" for d in (out_dirs(fig_id)[0], out_dirs(fig_id)[2])])
    finish_figure(fig_id, panels)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/manuscript/build_extended_data_figure2_active.py"),
        ],
        cwd=ROOT,
        check=True,
    )


def _external_data(context: str) -> pd.DataFrame:
    summary = read_tsv("reports/external_bridge_form_robustness/observed_shift_depmap_bridge_summary.tsv")
    row = summary.loc[summary["context"].eq(context)].iloc[0]
    df = pd.read_csv(ROOT / row["source_path"], sep="\t")
    df = df.loc[df["depmap_gene_dependency"].notna() & df["real_shift_mean_abs"].notna()].copy()
    df["context"] = context
    return df


def ed3() -> None:
    fig_id = 3
    reset_out_dirs(fig_id)
    contexts = ["K562 TF day 7", "K562 TF day 13", "K562 essential CRISPRi day 6", "K562 genome-scale CRISPRi day 8", "HepG2 day 7", "Jurkat day 7"]
    summary = read_tsv("reports/external_bridge_form_robustness/observed_shift_depmap_bridge_summary.tsv")
    panels = {chr(97+i): _external_data(ctx) for i, ctx in enumerate(contexts)}
    fig = plt.figure(figsize=(12, 6.3))
    gs = fig.add_gridspec(2, 3, hspace=0.45, wspace=0.35)
    for i, ctx in enumerate(contexts):
        ax = fig.add_subplot(gs[i//3, i%3])
        letter = chr(97+i)
        panel_heading(ax, letter, ctx)
        d = panels[letter]
        plot = d.sample(min(len(d), 2500), random_state=1) if len(d) > 2500 else d
        ax.scatter(plot["depmap_gene_dependency"], plot["real_shift_mean_abs"], s=8, color=COLORS["blue"], alpha=0.35, edgecolors="none")
        r = summary.loc[summary["context"].eq(ctx)].iloc[0]
        ax.text(0.04, 0.96, f"Spearman ρ = {r['spearman_rho']:.3f}\nn={int(r['n_targets_matched_depmap'])}; {format_p_value(r['spearman_permutation_pvalue'])}", transform=ax.transAxes, va="top", fontsize=7)
        ax.set_xlabel("CRISPR dependency strength")
        ax.set_ylabel("Observed shift mean abs")
        clean(ax)
    save(fig, *[d / "Extended_Data_Figure_3" for d in (out_dirs(fig_id)[0], out_dirs(fig_id)[2])])
    finish_figure(fig_id, panels)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/manuscript/build_extended_data_figure3_active.py"),
        ],
        cwd=ROOT,
        check=True,
    )


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
    q_long = []
    for metric, rho_col, q_col in [
        ("total-shift endpoint", "total_shift_depmap_spearman", "total_shift_depmap_qvalue"),
        ("axis-aligned endpoint", "axis_aligned_depmap_spearman", "axis_aligned_depmap_qvalue"),
    ]:
        cols = ["model_id", "cell_line", rho_col, q_col]
        d = metrics.loc[:, cols].rename(columns={rho_col: "spearman_rho", q_col: "q_value"}).copy()
        d["metric_family"] = metric
        q_long.append(d)
    q_long_df = pd.concat(q_long, ignore_index=True)
    auc_null = metrics[["model_id", "cell_line", "anchor_vs_low_information_axis_auc"]].copy()
    auc_null["distance_from_chance"] = auc_null["anchor_vs_low_information_axis_auc"] - 0.5
    panels = {
        "a": q_long_df,
        "b": auc_null,
        "c": gears,
        "d": bridge.loc[bridge["evidence_layer"].eq("primary_model_audit")].copy(),
        "source_fdr_family": pq,
        "source_null_reference": target.loc[target["model_id"].isin(["null_model","shared_mean_baseline"])].copy(),
    }
    fig = plt.figure(figsize=(11, 7.4))
    gs = fig.add_gridspec(2, 2, hspace=0.48, wspace=0.36)

    ax = fig.add_subplot(gs[0, 0])
    panel_heading(ax, "a", "Endpoint-alignment q-value calibration")
    d = panels["a"].dropna(subset=["spearman_rho"]).copy()
    d = d.loc[d["model_id"].isin(["scgen_hcc_formal_v1", "cpa_v0.8.8", "gears_hcc_formal_v1", "cellot_hcc_formal_v1", "scgpt_hcc_formal_v1", "geneformer_hcc_formal_v1", "shared_mean_baseline"])].copy()
    metric_pos = {"total-shift endpoint": -0.11, "axis-aligned endpoint": 0.11}
    context_marker = {"HCC38": "o", "HCC1143": "s"}
    for i, (model, g) in enumerate(d.groupby("model_id", sort=False)):
        label = MODEL_LABELS.get(model, model)
        for row in g.itertuples():
            x = i + metric_pos[row.metric_family]
            color = COLORS["green"] if row.q_value <= 0.1 else COLORS["gray"]
            ax.scatter(x, -np.log10(max(float(row.q_value), 1e-6)), marker=context_marker.get(row.cell_line, "o"), s=32, color=color, edgecolor="white", linewidth=0.35)
    ax.axhline(-np.log10(0.1), color="#BDBDBD", lw=0.8, ls=(0, (2, 2)))
    ax.set_xticks(range(d["model_id"].nunique()))
    ax.set_xticklabels([MODEL_LABELS.get(m, m) for m in d["model_id"].drop_duplicates()], rotation=35, ha="right", fontsize=6)
    ax.set_ylabel("−log10(q)")
    ax.set_ylim(bottom=0)
    clean(ax, light_grid=True, grid_axis="y")

    ax = fig.add_subplot(gs[0, 1])
    panel_heading(ax, "b", "Anchor-separation calibration")
    d = panels["b"].dropna(subset=["anchor_vs_low_information_axis_auc"]).copy()
    d = d.loc[d["model_id"].isin(["scgen_hcc_formal_v1", "cpa_v0.8.8", "gears_hcc_formal_v1", "cellot_hcc_formal_v1", "scgpt_hcc_formal_v1", "geneformer_hcc_formal_v1", "shared_mean_baseline", "null_model"])].copy()
    d["label"] = d["model_id"].map(MODEL_LABELS).fillna(d["model_id"]) + " " + d["cell_line"].str.replace("HCC", "")
    d = d.sort_values("anchor_vs_low_information_axis_auc")
    ax.barh(d["label"], d["anchor_vs_low_information_axis_auc"], color=np.where(d["model_id"].eq("null_model"), COLORS["gray"], COLORS["blue"]), alpha=0.82)
    ax.axvline(0.5, color="#888888", lw=0.8, ls=(0, (2, 2)))
    ax.set_xlabel("Anchor vs low-information AUC")
    ax.tick_params(axis="y", labelsize=5.5)
    clean(ax, light_grid=True, grid_axis="x")

    ax = fig.add_subplot(gs[1, 0])
    panel_heading(ax, "c", "Expanded GEARS sweep detail")
    d = panels["c"].dropna(subset=["axis_aligned_depmap_spearman", "anchor_vs_low_information_axis_auc"]).copy()
    formal = d["model_id"].eq("gears_hcc_formal_v1")
    ax.scatter(d.loc[~formal, "axis_aligned_depmap_spearman"], d.loc[~formal, "anchor_vs_low_information_axis_auc"], color=COLORS["orange"], s=28, alpha=0.78, label="finite-budget")
    ax.scatter(d.loc[formal, "axis_aligned_depmap_spearman"], d.loc[formal, "anchor_vs_low_information_axis_auc"], color=COLORS["green"], s=45, edgecolor="white", linewidth=0.4, label="formal")
    ax.set_xlabel("Axis-aligned Spearman ρ")
    ax.set_ylabel("Anchor vs low-information AUC")
    ax.legend(frameon=False, fontsize=6)
    clean(ax, light_grid=True)

    ax = fig.add_subplot(gs[1, 1])
    panel_heading(ax, "d", "Observed-shift oracle")
    d = panels["d"].sort_values("spearman_rho")
    y = np.arange(len(d))
    xerr = np.vstack([d["spearman_rho"] - d["spearman_bootstrap_ci_low"], d["spearman_bootstrap_ci_high"] - d["spearman_rho"]])
    ax.errorbar(d["spearman_rho"], y, xerr=xerr, fmt="o", color=COLORS["green"], ecolor=COLORS["green"], elinewidth=1.2, capsize=2)
    ax.set_yticks(y); ax.set_yticklabels(d["context"], fontsize=6)
    ax.set_xlabel("Observed-shift Spearman ρ with 95% CI")
    ax.axvline(0, color="#BBBBBB", linewidth=0.8)
    clean(ax, light_grid=True, grid_axis="x")
    save(fig, *[d / "Extended_Data_Figure_5" for d in (out_dirs(fig_id)[0], out_dirs(fig_id)[2])])
    finish_figure(fig_id, {k: v for k, v in panels.items() if not k.startswith("source_")})
    for k, src in panels.items():
        if k.startswith("source_"):
            continue
        figp = plt.figure(figsize=(5, 3)); axp = figp.add_subplot(111)
        if k == "d":
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
            table_panel(axp, src.head(12), k, {"a":"Endpoint q calibration","b":"Anchor AUC calibration","c":"GEARS sweep detail","d":"Oracle ceiling"}[k], font=5.2)
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
    for idx, (k, title) in enumerate([("e","Endpoint anchors vs low-information"),("f","Endpoint anchors vs middle-band")]):
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
            display = src.head(12).copy()
            for column in display.columns:
                if display[column].dtype == object:
                    display[column] = display[column].map(display_endpoint_text)
            table_panel(axp, display, k, f"ED7 panel {k}", font=5.0)
        save_panel(fig_id, k, figp, src)


def reset_out_dirs(fig_id: int) -> None:
    for path in [
        ROOT / "figures" / f"Extended_Data_Figure_{fig_id}",
        ROOT / "figure_build" / "output" / f"Extended_Data_Figure_{fig_id}",
    ]:
        if path.exists():
            shutil.rmtree(path)
    out_dirs(fig_id)


def _model_label_frame(metrics: pd.DataFrame) -> pd.DataFrame:
    d = metrics.copy()
    d["model_label"] = d["model_id"].map(MODEL_LABELS).fillna(d["model_id"])
    d["context_label"] = d["cell_line"]
    d["label"] = d["model_label"] + " " + d["context_label"]
    return d


def ed4_active() -> None:
    """Model-audit fairness, calibration and finite-budget sensitivity."""
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/manuscript/build_extended_data_figure4_active.py"),
        ],
        cwd=ROOT,
        check=True,
    )


def ed5_active() -> None:
    """Model-behavior diagnostics underlying the Fig. 3 summaries."""
    fig_id = 5
    reset_out_dirs(fig_id)
    common = read_tsv("reports/model_endpoint_recovery/source_data/model_common_response_metrics.tsv")
    identity = read_tsv("reports/model_endpoint_recovery/source_data/model_target_identity_preservation.tsv")
    axis = read_tsv("reports/model_endpoint_recovery/axis_projection.tsv")
    formal_models = list(MODEL_LABELS)
    profile_models = ["scgen_hcc_formal_v1", "cpa_v0.8.8", "shared_mean_baseline"]
    panels: dict[str, pd.DataFrame] = {
        "a": common.loc[common["model_id"].isin(formal_models)].copy()
    }

    profile = axis.loc[
        axis["model_id"].isin(profile_models) & axis["cell_line"].eq("HCC1143")
    ].copy()
    profile_pivot = profile.pivot_table(
        index=["model_id", "target_gene"],
        columns="fine_axis",
        values="projected_mean_abs",
        aggfunc="mean",
        fill_value=0,
    )
    profile_share = profile_pivot.div(profile_pivot.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    profile_share_vmax = float(np.ceil(profile_share.to_numpy().max() * 20) / 20)
    axis_order = (
        profile_share.groupby(level="model_id")
        .mean()
        .mean(axis=0)
        .sort_values(ascending=False)
        .head(8)
        .index.tolist()
    )
    target_order = (
        profile_share.loc[:, axis_order]
        .groupby(level="target_gene")
        .var()
        .mean(axis=1)
        .sort_values(ascending=False)
        .head(14)
        .index.tolist()
    )

    def draw_a(ax: plt.Axes, src: pd.DataFrame) -> None:
        panel_heading(ax, "a", "Common-response metric components")
        d = _model_label_frame(src)
        d["model_order"] = d["model_id"].map({model: i for i, model in enumerate(formal_models)})
        d["context_order"] = d["cell_line"].map({"HCC38": 0, "HCC1143": 1})
        d = d.sort_values(["model_order", "context_order"])
        columns = [
            "mean_stress_axis_share",
            "mean_top_axis_share",
            "mean_target_axis_cosine_proxy",
        ]
        raw = d.set_index("label")[columns]
        scaled = raw.copy()
        for context in ["HCC38", "HCC1143"]:
            mask = d["cell_line"].eq(context).to_numpy()
            values = raw.iloc[mask]
            minimum = values.min(axis=0)
            span = values.max(axis=0) - minimum
            scaled.iloc[mask] = (values - minimum) / span.replace(0, np.nan)
        im = ax.imshow(scaled, aspect="auto", cmap=PAPER_TEAL_CMAP, vmin=0, vmax=1)
        ax.set_yticks(range(len(raw.index)))
        ax.set_yticklabels(raw.index, fontsize=5.1)
        ax.set_xticks(range(3))
        ax.set_xticklabels(
            ["stress-axis share", "top-axis share", "pairwise target-axis cosine"],
            rotation=27,
            ha="right",
            fontsize=5.4,
        )
        for row in range(raw.shape[0]):
            for col in range(raw.shape[1]):
                value = raw.iloc[row, col]
                if pd.notna(value):
                    color = "white" if scaled.iloc[row, col] >= 0.55 else "#222222"
                    ax.text(col, row, f"{value:.2f}", ha="center", va="center", fontsize=4.5, color=color)
                else:
                    ax.text(col, row, "NA", ha="center", va="center", fontsize=4.5, color="#777777")
        cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.015)
        cbar.set_label("higher = stronger common-response structure", fontsize=5.4)
        cbar.ax.tick_params(labelsize=5)
        for boundary in range(2, len(raw.index), 2):
            ax.axhline(boundary - 0.5, color="white", lw=0.5)

    def draw_axis(ax: plt.Axes, model: str, letter: str, title: str) -> pd.DataFrame:
        d = axis.loc[axis["model_id"].eq(model) & axis["cell_line"].eq("HCC1143")].copy()
        pivot = d.pivot_table(
            index="target_gene",
            columns="fine_axis",
            values="projected_mean_abs",
            aggfunc="mean",
            fill_value=0,
        )
        share = pivot.div(pivot.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
        mat = share.reindex(index=target_order, columns=axis_order, fill_value=0)
        panel_heading(ax, letter, title)
        im = ax.imshow(
            mat,
            aspect="auto",
            cmap=PAPER_TEAL_CMAP,
            vmin=0,
            vmax=profile_share_vmax,
        )
        ax.set_yticks(range(len(mat.index)))
        ax.set_yticklabels(mat.index, fontsize=5)
        ax.set_xticks(range(len(mat.columns)))
        ax.set_xticklabels(mat.columns, rotation=45, ha="right", fontsize=5)
        cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.01)
        cbar.set_label("within-target axis share", fontsize=5)
        cbar.ax.tick_params(labelsize=5)
        return mat.reset_index().melt(
            id_vars="target_gene",
            var_name="fine_axis",
            value_name="normalized_axis_share",
        )

    def draw_e(ax: plt.Axes, src: pd.DataFrame) -> None:
        panel_heading(ax, "e", "Target-similarity inflation versus identity preservation")
        d = _model_label_frame(
            src.loc[
                src["model_id"].isin(formal_models)
                & src["target_identity_preservation_status"].eq("estimated")
            ]
        )
        context_style = {"HCC38": "o", "HCC1143": "s"}
        estimable_models = [
            model
            for model in formal_models
            if model not in {"shared_mean_baseline", "null_model"}
        ]
        model_colors = {model: MODEL_COLORS[model] for model in estimable_models}
        for _, row in d.iterrows():
            ax.scatter(
                row["predicted_target_similarity_mean"],
                row["target_identity_preservation_spearman"],
                s=36,
                marker=context_style[row["cell_line"]],
                color=model_colors[row["model_id"]],
                edgecolor="white",
                linewidth=0.4,
            )
        ax.set_xlabel("Predicted mean target-target similarity (homogenization)")
        ax.set_ylabel("Target-identity Spearman ρ")
        clean(ax, light_grid=True)
        model_handles = [
            plt.Line2D(
                [0],
                [0],
                marker="o",
                linestyle="none",
                markerfacecolor=model_colors[model],
                markeredgecolor="white",
                markersize=5,
                label=MODEL_LABELS[model],
            )
            for model in estimable_models
        ]
        context_handles = [
            plt.Line2D(
                [0],
                [0],
                marker=marker,
                linestyle="none",
                markerfacecolor="#777777",
                markeredgecolor="white",
                markersize=5,
                label=context,
            )
            for context, marker in context_style.items()
        ]
        ax.legend(
            handles=model_handles + context_handles,
            frameon=False,
            fontsize=5.2,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.22),
            ncol=4,
            columnspacing=0.9,
            handletextpad=0.3,
        )

    fig = plt.figure(figsize=(11.0, 8.0))
    gs = fig.add_gridspec(2, 3, hspace=0.55, wspace=0.46)
    draw_a(fig.add_subplot(gs[0, 0]), panels["a"])
    panels["b"] = draw_axis(fig.add_subplot(gs[0, 1]), "scgen_hcc_formal_v1", "b", "scGen HCC1143 axis profile")
    panels["c"] = draw_axis(fig.add_subplot(gs[0, 2]), "cpa_v0.8.8", "c", "CPA HCC1143 axis profile")
    panels["d"] = draw_axis(fig.add_subplot(gs[1, 0]), "shared_mean_baseline", "d", "Shared mean HCC1143 axis profile")
    panels["e"] = identity.loc[identity["model_id"].isin(formal_models)].copy()
    draw_e(fig.add_subplot(gs[1, 1:]), panels["e"])
    save(fig, *[d / "Extended_Data_Figure_5" for d in (out_dirs(fig_id)[0], out_dirs(fig_id)[2])])
    finish_figure(fig_id, panels)
    for key, src in panels.items():
        pf, ax = plt.subplots(figsize=(5.0, 3.0))
        if key == "a":
            draw_a(ax, src)
        elif key == "e":
            draw_e(ax, src)
        else:
            model = {"b": "scgen_hcc_formal_v1", "c": "cpa_v0.8.8", "d": "shared_mean_baseline"}[key]
            title = {"b": "scGen HCC1143 axis profile", "c": "CPA HCC1143 axis profile", "d": "Shared mean HCC1143 axis profile"}[key]
            _axis_heat(ax, axis, model, "HCC1143", key, title)
        save_panel(fig_id, key, pf, src)


def ed6_active() -> None:
    """Pathway-detail sensitivity supporting Fig. 2 response annotations."""
    fig_id = 6
    reset_out_dirs(fig_id)
    react = read_tsv("reports/category_response_pathway/contrasts/category_response_contrast_gsea_reactome.tsv")
    gobp = read_tsv("reports/category_response_pathway/contrasts/category_response_contrast_gsea_gobp.tsv")
    median = read_tsv("reports/category_response_pathway/contrasts/category_response_contrast_gsea_hallmark_median_sensitivity.tsv")
    loo = read_tsv("reports/category_response_pathway/contrasts/category_response_contrast_gsea_hallmark_loo_summary.tsv")
    panels = {"a": react, "b": gobp, "c": median, "d": loo}

    def enrichment_dot(ax: plt.Axes, src: pd.DataFrame, letter: str, title: str) -> None:
        panel_heading(ax, letter, title)
        d = src.assign(absNES=lambda x: x["NES"].abs()).sort_values("absNES", ascending=False).head(12)
        ax.scatter(d["NES"], np.arange(len(d)), s=np.maximum(18, -np.log10(d["padj"].clip(lower=1e-6)) * 13), c=np.where(d["NES"] > 0, COLORS["orange"], COLORS["blue"]), alpha=0.82)
        ax.axvline(0, color="#BBBBBB", linewidth=0.8, ls=(0, (2, 2)))
        ax.set_yticks(np.arange(len(d))); ax.set_yticklabels(d["pathway"].str.slice(0, 38), fontsize=5.0)
        ax.set_xlabel("NES")
        clean(ax)

    def median_plot(ax: plt.Axes, src: pd.DataFrame) -> None:
        panel_heading(ax, "c", "Mean versus median Hallmark NES")
        for context, marker in [("HCC38", "o"), ("HCC1143", "s")]:
            d = src.loc[src["context"].eq(context)]
            ax.scatter(d["mean_NES"], d["median_NES"], marker=marker, s=28, color=COLORS["green"], alpha=0.78, edgecolor="white", linewidth=0.35, label=context)
        lim = (-2.1, 1.7)
        ax.plot(lim, lim, color="#BDBDBD", lw=0.8, ls=(0, (2, 2)))
        ax.set_xlim(*lim); ax.set_ylim(*lim)
        ax.set_xlabel("Mean-signature NES"); ax.set_ylabel("Median-signature NES")
        ax.legend(frameon=False, fontsize=5.8)
        clean(ax, light_grid=True)

    def loo_plot(ax: plt.Axes, src: pd.DataFrame) -> None:
        panel_heading(ax, "d", "Leave-one-target-out Hallmark stability")
        d = src.sort_values(["context", "full_NES"]).copy()
        d["label"] = d["context"] + " / " + d["pathway"]
        y = np.arange(len(d))
        ax.hlines(y, d["loo_NES_min"], d["loo_NES_max"], color="#A8A8A8", lw=1.1)
        ax.scatter(d["full_NES"], y, s=22, color=COLORS["green"], edgecolor="white", linewidth=0.35)
        ax.axvline(0, color="#BDBDBD", lw=0.7, ls=(0, (2, 2)))
        ax.set_yticks(y); ax.set_yticklabels(d["label"], fontsize=4.8)
        ax.set_xlabel("Hallmark NES; interval = LOO range")
        clean(ax, light_grid=True, grid_axis="x")

    gs = fig.add_gridspec(2, 2, hspace=0.55, wspace=0.46)
    enrichment_dot(fig.add_subplot(gs[0, 0]), react, "a", "Reactome response-program details")
    enrichment_dot(fig.add_subplot(gs[0, 1]), gobp, "b", "GO BP response-program details")
    median_plot(fig.add_subplot(gs[1, 0]), median)
    loo_plot(fig.add_subplot(gs[1, 1]), loo)
    save(fig, *[d / "Extended_Data_Figure_6" for d in (out_dirs(fig_id)[0], out_dirs(fig_id)[2])])
    finish_figure(fig_id, panels)
    drawers = {
        "a": lambda ax, src: enrichment_dot(ax, src, "a", "Reactome response-program details"),
        "b": lambda ax, src: enrichment_dot(ax, src, "b", "GO BP response-program details"),
        "c": median_plot,
        "d": loo_plot,
    }
    for key, src in panels.items():
        pf, ax = plt.subplots(figsize=(5.2, 3.3))
        drawers[key](ax, src)
        save_panel(fig_id, key, pf, src)


def main() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "axes.linewidth": 0.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })
    for fn in [ed1, ed2, ed3, ed4_active, ed5_active, ed6_active]:
        fn()
    for retired in [
        ROOT / "figures/Extended_Data_Figure_7",
        ROOT / "figure_build/output/Extended_Data_Figure_7",
    ]:
        if retired.exists():
            shutil.rmtree(retired)
    print("Built active Extended Data Figures 1–6")


if __name__ == "__main__":
    main()
