"""
Display selection for pathway-response exploratory layer (P3).

Selects targets and pathways for visualization based on pre-specified rules.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


PRE_SPECIFIED_PANEL = {
    "HALLMARK_APOPTOSIS": "Cell death / stress",
    "HALLMARK_P53_PATHWAY": "Cell death / stress",
    "HALLMARK_TNFA_SIGNALING_VIA_NFKB": "Cell death / stress",
    "HALLMARK_E2F_TARGETS": "Proliferation / cell cycle",
    "HALLMARK_G2M_CHECKPOINT": "Proliferation / cell cycle",
    "HALLMARK_MYC_TARGETS_V1": "Proliferation / cell cycle",
    "HALLMARK_UNFOLDED_PROTEIN_RESPONSE": "Proteostasis / stress",
    # Note: MSigDB Hallmark uses the historical spelling "OXIGEN" (sic)
    # in the gene set name; preserve it here so the lookup matches the GMT.
    "HALLMARK_REACTIVE_OXIGEN_SPECIES_PATHWAY": "Proteostasis / stress",
    "HALLMARK_HYPOXIA": "Proteostasis / stress",
    "HALLMARK_MTORC1_SIGNALING": "Metabolic state",
    "HALLMARK_GLYCOLYSIS": "Metabolic state",
    "HALLMARK_OXIDATIVE_PHOSPHORYLATION": "Metabolic state",
    "HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION": "State remodeling",
    "HALLMARK_WNT_BETA_CATENIN_SIGNALING": "State remodeling",
    "HALLMARK_NOTCH_SIGNALING": "State remodeling",
    "HALLMARK_INTERFERON_ALPHA_RESPONSE": "Inflammatory / interferon",
    "HALLMARK_INTERFERON_GAMMA_RESPONSE": "Inflammatory / interferon",
}

# Tier 1 anchor targets (per plan Section 10)
TIER1_ANCHORS = {"PFDN5", "PMF1", "PRPF6", "ZNF131"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Display selection for pathway response")
    parser.add_argument("--output-dir", default="reports/pathway_response", help="Output directory")
    return parser.parse_args()


def load_fgsea_results(output_dir: Path) -> pd.DataFrame:
    """Load all fgsea result TSVs (excluding aggregate files like *_all_targets.tsv
    to avoid double-counting if someone writes a concatenated copy alongside)."""
    files = sorted(
        f for f in output_dir.glob("fgsea_hallmark_*.tsv")
        if "all_targets" not in f.name and "aggregate" not in f.name
    )
    dfs = []
    for f in files:
        df = pd.read_csv(f, sep="\t")
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def load_target_inclusion_qc(output_dir: Path) -> pd.DataFrame:
    """Load all target inclusion QC files."""
    files = sorted(output_dir.glob("target_inclusion_qc_*.tsv"))
    dfs = []
    for f in files:
        df = pd.read_csv(f, sep="\t")
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def get_shift_from_bridge(context: str, target: str) -> float | None:
    """Read shift value from existing bridge table if available."""
    if context.startswith("HCC"):
        bridge_file = Path(f"reports/stage2_truth_driven_bridge/{context}/bridge_audit.tsv")
        if not bridge_file.exists():
            return None
        # bridge_audit doesn't have per-target shifts, need correlation_summary or other
        return None
    return None


def select_display_targets(
    fgsea_df: pd.DataFrame,
    qc_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Select display targets by tier rules.
    Returns DataFrame with columns: context, target, selection_tier, selection_reason.
    """
    selected = []

    for context in fgsea_df["context"].unique():
        ctx_fgsea = fgsea_df[fgsea_df["context"] == context]
        ctx_qc = qc_df[qc_df["context"] == context]
        eligible_targets = ctx_qc.loc[ctx_qc["included"], "target"].tolist()

        if not eligible_targets:
            continue

        # Tier 1: anchor targets
        tier1 = [t for t in eligible_targets if t in TIER1_ANCHORS]
        for t in tier1:
            selected.append({
                "context": context,
                "target": t,
                "selection_tier": "Tier 1",
                "selection_reason": "benchmark-relevant anchor",
            })

        # Tier 2: top 3 targets by |NES| variance across pathways (proxy for shift)
        remaining = [t for t in eligible_targets if t not in tier1]
        if remaining:
            target_variance = []
            for t in remaining:
                sub = ctx_fgsea[ctx_fgsea["target"] == t]
                if not sub.empty:
                    var = sub["NES"].abs().var()
                    target_variance.append((t, var))

            if target_variance:
                target_variance.sort(key=lambda x: x[1], reverse=True)
                n_top = min(3, len(target_variance))
                for t, var in target_variance[:n_top]:
                    selected.append({
                        "context": context,
                        "target": t,
                        "selection_tier": "Tier 2",
                        "selection_reason": f"top by NES variance ({var:.3f})",
                    })

    return pd.DataFrame(selected)


def select_display_pathways(
    fgsea_df: pd.DataFrame,
    selected_targets_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Select display pathways from pre-specified panel.
    Rule: FDR < 0.10 in >= 2 selected target-context pairs,
    OR top 12-15 by NES variance among selected target-context pairs.
    """
    # Filter to selected targets only
    selected_pairs = set(
        (row["context"], row["target"])
        for _, row in selected_targets_df.iterrows()
    )
    selected_fgsea = fgsea_df[
        fgsea_df.apply(lambda r: (r["context"], r["target"]) in selected_pairs, axis=1)
    ].copy()

    if selected_fgsea.empty:
        return pd.DataFrame()

    panel_pathways = set(PRE_SPECIFIED_PANEL.keys())
    panel_fgsea = selected_fgsea[selected_fgsea["pathway"].isin(panel_pathways)].copy()

    if panel_fgsea.empty:
        return pd.DataFrame()

    # Rule 1: FDR < 0.10 in >= 2 pairs
    sig_counts = panel_fgsea[panel_fgsea["padj"] < 0.10].groupby("pathway").size()
    rule1_pathways = set(sig_counts[sig_counts >= 2].index)

    # Rule 2: top 12 by NES variance among selected pairs
    nes_var = panel_fgsea.groupby("pathway")["NES"].var().sort_values(ascending=False)
    rule2_pathways = set(nes_var.head(12).index)

    display_pathways = rule1_pathways | rule2_pathways

    records = []
    for pathway in sorted(display_pathways):
        if pathway in PRE_SPECIFIED_PANEL:
            records.append({
                "display_group": PRE_SPECIFIED_PANEL[pathway],
                "display_name": pathway.replace("HALLMARK_", "").replace("_", " ").title(),
                "exact_gs_name": pathway,
                "n_sig_pairs": int(sig_counts.get(pathway, 0)),
                "nes_variance": float(nes_var.get(pathway, np.nan)),
                "rule": "FDR>=2" if pathway in rule1_pathways else "NES_var",
            })

    return pd.DataFrame(records)


def run_selection(output_dir: str) -> None:
    output_path = Path(output_dir)

    fgsea_df = load_fgsea_results(output_path)
    qc_df = load_target_inclusion_qc(output_path)

    if fgsea_df.empty:
        print("WARNING: No fgsea results found. Run P1-P2 first.")
        return

    print(f"Loaded fgsea results: {len(fgsea_df)} rows across {fgsea_df['context'].nunique()} contexts")

    # Select targets
    selected_targets = select_display_targets(fgsea_df, qc_df)
    selected_targets.to_csv(output_path / "selected_targets_for_display.tsv", sep="\t", index=False)
    print(f"Selected {len(selected_targets)} target-context pairs for display")
    for _, row in selected_targets.iterrows():
        print(f"  {row['context']} / {row['target']} ({row['selection_tier']})")

    # Select pathways
    selected_pathways = select_display_pathways(fgsea_df, selected_targets)
    if not selected_pathways.empty:
        selected_pathways.to_csv(
            output_path / "selected_response_gene_set_panel.tsv", sep="\t", index=False
        )
        print(f"Selected {len(selected_pathways)} pathways for display")
        for _, row in selected_pathways.iterrows():
            print(f"  {row['exact_gs_name']} ({row['display_group']}) - sig={row['n_sig_pairs']}")
    else:
        print("WARNING: No pathways selected. Check fgsea results.")

    # Save display selection log
    log = {
        "n_target_context_pairs": int(len(selected_targets)),
        "n_pathways": int(len(selected_pathways)) if not selected_pathways.empty else 0,
        "pre_specified_panel_size": len(PRE_SPECIFIED_PANEL),
        "tier1_anchors": list(TIER1_ANCHORS),
    }
    with open(output_path / "qc" / "pathway_display_selection_log.json", "w") as f:
        json.dump(log, f, indent=2)

    print("Done.")


if __name__ == "__main__":
    args = parse_args()
    run_selection(args.output_dir)
