"""
Draw NES heatmap for pathway-response exploratory layer (P4).

Rows = selected context x target pairs
Columns = selected response-axis gene sets
Color = fgsea NES
Marker = FDR < 0.10

When --with-cross-context-strip is enabled (default), two annotation columns
are appended on the right:
  - "Sign agree %" : fraction of all 50 Hallmark pathways whose NES sign
                     agrees with the same target in the partner context.
  - "Spearman ρ"   : Spearman rank correlation of NES across all 50 pathways
                     between the row's context and its partner context.
Partner mapping: HCC38 ↔ HCC1143, K562_7d ↔ K562_13d.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy as np
import pandas as pd
import seaborn as sns


PARTNER_CONTEXT = {
    "HCC38": "HCC1143",
    "HCC1143": "HCC38",
    "K562_7d": "K562_13d",
    "K562_13d": "K562_7d",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draw pathway response NES heatmap")
    parser.add_argument("--output-dir", default="reports/pathway_response", help="Output directory")
    parser.add_argument("--output", default="pathway_response_nes_heatmap.png", help="Output filename")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--fig-width", type=float, default=16)
    parser.add_argument("--fig-height", type=float, default=10)
    parser.add_argument(
        "--no-cross-context-strip",
        action="store_true",
        help="Disable the cross-context consistency annotation columns.",
    )
    return parser.parse_args()


def load_data(output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame] | None:
    """Load fgsea results, selected targets, and selected pathways."""
    # Exclude aggregate files like fgsea_hallmark_all_targets.tsv to prevent
    # double-counting if a concatenated copy is written alongside.
    fgsea_files = sorted(
        f for f in output_dir.glob("fgsea_hallmark_*.tsv")
        if "all_targets" not in f.name and "aggregate" not in f.name
    )
    if not fgsea_files:
        print("ERROR: No fgsea results found.")
        return None

    fgsea_dfs = [pd.read_csv(f, sep="\t") for f in fgsea_files]
    fgsea_df = pd.concat(fgsea_dfs, ignore_index=True)

    targets_file = output_dir / "selected_targets_for_display.tsv"
    pathways_file = output_dir / "selected_response_gene_set_panel.tsv"

    if not targets_file.exists():
        print(f"ERROR: {targets_file} not found. Run select_display.py first.")
        return None
    if not pathways_file.exists():
        print(f"ERROR: {pathways_file} not found. Run select_display.py first.")
        return None

    targets_df = pd.read_csv(targets_file, sep="\t")
    pathways_df = pd.read_csv(pathways_file, sep="\t")

    return fgsea_df, targets_df, pathways_df


def _compute_cross_context_strip(
    fgsea_df: pd.DataFrame,
    sorted_labels: list[str],
) -> pd.DataFrame:
    """For each (context, target) row, compute sign-agreement % and Spearman ρ
    against the same target in the partner context, using all 50 Hallmark
    pathways.
    """
    rows = []
    for label in sorted_labels:
        ctx, tg = label.split(" / ", 1)
        partner = PARTNER_CONTEXT.get(ctx)
        if partner is None:
            rows.append({"display_label": label, "sign_agree_pct": np.nan, "spearman_rho": np.nan})
            continue
        a = fgsea_df[(fgsea_df["context"] == ctx) & (fgsea_df["target"] == tg)].set_index("pathway")["NES"]
        b = fgsea_df[(fgsea_df["context"] == partner) & (fgsea_df["target"] == tg)].set_index("pathway")["NES"]
        joined = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
        if joined.empty:
            rows.append({"display_label": label, "sign_agree_pct": np.nan, "spearman_rho": np.nan})
            continue
        sign_agree = ((joined["a"] >= 0) == (joined["b"] >= 0)).sum()
        rho = joined.corr(method="spearman").iloc[0, 1]
        rows.append({
            "display_label": label,
            "sign_agree_pct": float(sign_agree / len(joined) * 100.0),
            "spearman_rho": float(rho),
            "n_pathways": int(len(joined)),
            "partner_context": partner,
        })
    return pd.DataFrame(rows).set_index("display_label")


def draw_nes_heatmap(
    fgsea_df: pd.DataFrame,
    targets_df: pd.DataFrame,
    pathways_df: pd.DataFrame,
    output_path: Path,
    fig_width: float,
    fig_height: float,
    dpi: int,
    with_cross_context_strip: bool = True,
) -> None:
    """Draw NES heatmap with significance markers and (optionally) a
    cross-context consistency strip on the right."""
    # Build display label for each target-context pair
    targets_df["display_label"] = targets_df["context"] + " / " + targets_df["target"]
    selected_pair_set = {(row["context"], row["target"]) for _, row in targets_df.iterrows()}

    # Filter fgsea to selected pairs and pathways
    display_pathways = pathways_df["exact_gs_name"].tolist()
    filtered = fgsea_df[
        fgsea_df.apply(lambda r: (r["context"], r["target"]) in selected_pair_set, axis=1)
        & fgsea_df["pathway"].isin(display_pathways)
    ].copy()

    if filtered.empty:
        print("WARNING: No data to plot after filtering.")
        return

    # Pivot to matrix: rows = display_label, columns = pathway, values = NES
    filtered["display_label"] = filtered["context"] + " / " + filtered["target"]
    nes_matrix = filtered.pivot_table(
        index="display_label",
        columns="pathway",
        values="NES",
        aggfunc="first",
    )
    sig_matrix = filtered.pivot_table(
        index="display_label",
        columns="pathway",
        values="padj",
        aggfunc="first",
    )

    # Reorder rows by context then target
    order_map = {
        label: (label.split(" / ")[0], label.split(" / ")[1])
        for label in nes_matrix.index
    }
    context_order = {"HCC38": 0, "HCC1143": 1, "K562_7d": 2, "K562_13d": 3}
    sorted_labels = sorted(
        nes_matrix.index,
        key=lambda x: (context_order.get(order_map[x][0], 99), order_map[x][1])
    )
    nes_matrix = nes_matrix.reindex(sorted_labels)
    sig_matrix = sig_matrix.reindex(sorted_labels)

    # Reorder columns by display group
    pathway_order_map = {
        row["exact_gs_name"]: (row["display_group"], row["exact_gs_name"])
        for _, row in pathways_df.iterrows()
        if row["exact_gs_name"] in nes_matrix.columns
    }
    sorted_cols = sorted(
        nes_matrix.columns,
        key=lambda x: pathway_order_map.get(x, ("", x))
    )
    nes_matrix = nes_matrix[sorted_cols]
    sig_matrix = sig_matrix[sorted_cols]

    # Shorten column names
    short_names = {col: col.replace("HALLMARK_", "").replace("_", " ").title() for col in sorted_cols}
    nes_matrix.columns = [short_names[c] for c in nes_matrix.columns]
    sig_matrix.columns = [short_names[c] for c in sig_matrix.columns]

    n_rows, n_cols = nes_matrix.shape
    if n_rows == 0 or n_cols == 0:
        print("WARNING: Empty matrix after filtering.")
        return

    # Compute cross-context strip BEFORE creating axes (uses full fgsea_df)
    strip_df = (
        _compute_cross_context_strip(fgsea_df, sorted_labels)
        if with_cross_context_strip
        else None
    )

    # Create figure with gridspec
    if with_cross_context_strip and strip_df is not None and not strip_df.empty:
        fig = plt.figure(figsize=(fig_width, fig_height), constrained_layout=True)
        gs = gridspec.GridSpec(
            1, 4,
            width_ratios=[n_cols, 1.0, 1.0, 0.25],
            wspace=0.08,
            figure=fig,
        )
        ax_main = fig.add_subplot(gs[0, 0])
        ax_sign = fig.add_subplot(gs[0, 1])
        ax_rho = fig.add_subplot(gs[0, 2])
        ax_cb = fig.add_subplot(gs[0, 3])
    else:
        fig, ax_main = plt.subplots(figsize=(fig_width, fig_height), constrained_layout=True)
        ax_sign = ax_rho = ax_cb = None

    # Draw main NES heatmap
    vmax = max(abs(nes_matrix.min().min()), abs(nes_matrix.max().max()), 1.0)
    sns.heatmap(
        nes_matrix,
        cmap="RdBu_r",
        center=0,
        vmin=-vmax,
        vmax=vmax,
        annot=True,
        fmt=".2f",
        annot_kws={"size": 6},
        linewidths=0.5,
        linecolor="white",
        cbar=ax_cb is None,
        cbar_kws={"label": "NES", "shrink": 0.6} if ax_cb is None else None,
        cbar_ax=ax_cb if ax_cb is not None else None,
        ax=ax_main,
    )
    if ax_cb is not None:
        ax_cb.set_ylabel("NES", fontsize=9)

    # Add significance markers (asterisks for FDR < 0.10)
    for i in range(n_rows):
        for j in range(n_cols):
            padj = sig_matrix.iloc[i, j]
            if pd.notna(padj) and padj < 0.10:
                ax_main.text(
                    j + 0.85,
                    i + 0.15,
                    "*",
                    fontsize=10,
                    color="black",
                    ha="center",
                    va="center",
                    fontweight="bold",
                )

    ax_main.set_xlabel("Pathway", fontsize=10)
    ax_main.set_ylabel("Context / Target", fontsize=10)
    ax_main.set_title(
        "Exploratory pathway-level summaries of target-versus-control perturbation responses",
        fontsize=11,
        pad=15,
        loc="left",
    )
    ax_main.set_xticklabels(ax_main.get_xticklabels(), rotation=45, ha="right", fontsize=8)
    ax_main.set_yticklabels(ax_main.get_yticklabels(), rotation=0, fontsize=8)

    # Draw cross-context strip (if enabled)
    if ax_sign is not None and ax_rho is not None and strip_df is not None:
        strip_df = strip_df.reindex(sorted_labels)

        sign_vals = strip_df[["sign_agree_pct"]].astype(float)
        sns.heatmap(
            sign_vals,
            cmap="Greens",
            vmin=0,
            vmax=100,
            annot=True,
            fmt=".0f",
            annot_kws={"size": 7},
            linewidths=0.5,
            linecolor="white",
            cbar=False,
            ax=ax_sign,
        )
        ax_sign.set_xticklabels(["Sign\nagree %"], rotation=0, fontsize=8)
        ax_sign.set_yticklabels([])
        ax_sign.set_ylabel("")
        ax_sign.set_xlabel("")
        ax_sign.tick_params(left=False)

        rho_vals = strip_df[["spearman_rho"]].astype(float)
        sns.heatmap(
            rho_vals,
            cmap="RdBu_r",
            center=0,
            vmin=-1,
            vmax=1,
            annot=True,
            fmt="+.2f",
            annot_kws={"size": 7},
            linewidths=0.5,
            linecolor="white",
            cbar=False,
            ax=ax_rho,
        )
        ax_rho.set_xticklabels(["Spearman\nρ"], rotation=0, fontsize=8)
        ax_rho.set_yticklabels([])
        ax_rho.set_ylabel("")
        ax_rho.set_xlabel("")
        ax_rho.tick_params(left=False)

        # Sub-title above the strip
        ax_sign.set_title(
            "Cross-context consistency\n(same target, partner context,\nall 50 Hallmark pathways)",
            fontsize=8,
            pad=10,
            loc="left",
        )

    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved heatmap to {output_path}")
    print(f"  Shape: {n_rows} rows x {n_cols} columns")
    print(f"  NES range: [{nes_matrix.min().min():.2f}, {nes_matrix.max().max():.2f}]")
    print(f"  Significant cells (FDR<0.10): {(sig_matrix < 0.10).sum().sum()}")
    if strip_df is not None and not strip_df.empty:
        print(f"  Cross-context sign agree % range: "
              f"[{strip_df['sign_agree_pct'].min():.0f}, {strip_df['sign_agree_pct'].max():.0f}]")
        print(f"  Cross-context Spearman ρ range: "
              f"[{strip_df['spearman_rho'].min():+.2f}, {strip_df['spearman_rho'].max():+.2f}]")


def run_visualization(
    output_dir: str,
    output_file: str,
    fig_width: float,
    fig_height: float,
    dpi: int,
    with_cross_context_strip: bool = True,
) -> None:
    output_path = Path(output_dir)
    data = load_data(output_path)
    if data is None:
        return

    fgsea_df, targets_df, pathways_df = data
    draw_nes_heatmap(
        fgsea_df,
        targets_df,
        pathways_df,
        output_path / output_file,
        fig_width,
        fig_height,
        dpi,
        with_cross_context_strip=with_cross_context_strip,
    )


if __name__ == "__main__":
    args = parse_args()
    run_visualization(
        args.output_dir,
        args.output,
        args.fig_width,
        args.fig_height,
        args.dpi,
        with_cross_context_strip=not args.no_cross_context_strip,
    )
