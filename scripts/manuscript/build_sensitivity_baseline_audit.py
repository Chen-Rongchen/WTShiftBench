"""Shared-mean baseline non-oracle audit.

Analysis 1: the shared-mean baseline achieves backbone recovery = 0.807 vs
GEARS = 0.660.  Reviewers may ask: "is the baseline an oracle because it uses
the truth signal itself?"  We need to prove the baseline's advantage comes from
recurrent canonical-backbone structure, not from target self-information or
data leakage.

Part A: Leave-One-Target-Out (LOTO) over the backbone set.
  For each canonical_backbone target in HCC38 and HCC1143:
    1. Remove that target from the backbone set used to build the baseline.
    2. Recompute the shared-mean baseline (mean of remaining backbone targets).
    3. Score backbone recovery against the full frozen truth architecture.

Part B: Cross-context shared-mean baseline.
  1. Use HCC1143's backbone targets to build the baseline for HCC38 evaluation.
  2. Use HCC38's backbone targets to build the baseline for HCC1143 evaluation.

Output
------
reports/stage2_truth_driven_bridge/sensitivity/baseline_audit_summary.tsv

Columns
-------
- audit_type       : "loto", "cross_context", or "original_reference"
- variant          : description of the baseline variant
- context          : HCC38, HCC1143, or pooled
- backbone_recovery: score
- n_targets_used   : number of backbone targets used to construct baseline
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from wtbench.stage2_hcc_prediction_export import (
    compute_stage2_truth_aligned_log_shift_matrix,
    load_axis_membership,
    load_truth_contract,
)
from wtbench.stage2_model_structure_scorer import (
    project_prediction_to_axes,
    compute_backbone_recovery_score,
)
from wtbench.stage2_truth_bridge import (
    build_dataset_specs,
    load_config,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRUTH_CONFIG_PATH = PROJECT_ROOT / "configs/stage2/truth_driven_bridge_hcc38_hcc1143_v1.json"
TRUTH_CONTRACT_PATH = (
    PROJECT_ROOT
    / "reports/stage2_truth_driven_bridge/truth_architecture_contract/truth_architecture_contract.tsv"
)
AXIS_MEMBERSHIP_PATH = (
    PROJECT_ROOT
    / "reports/stage2_truth_driven_bridge/master_atlas/shared_target_axis_membership.tsv"
)
OUTDIR = PROJECT_ROOT / "reports/stage2_truth_driven_bridge/sensitivity"
OUTPATH = OUTDIR / "baseline_audit_summary.tsv"
MODEL_COMPARISON_PATH = PROJECT_ROOT / "reports/stage2_real_hcc_smoke/model_comparison.tsv"
SMOKE_SUMMARY_PATH = PROJECT_ROOT / "reports/stage2_real_hcc_smoke/smoke_summary.tsv"

CELL_LINES = ["HCC38", "HCC1143"]

# Per-cell-line original baseline scores from smoke_summary.tsv
# (verified 2026-05-01)
ORIGINAL_BASELINE_SCORES = {
    "HCC38": 0.773333,
    "HCC1143": 0.840000,
}


def get_backbone_targets(truth_contract: pd.DataFrame) -> list[str]:
    """Return sorted list of targets whose architecture_role is canonical_backbone."""
    backbone_axes = truth_contract.loc[
        truth_contract["architecture_role"] == "canonical_backbone"
    ]
    targets: list[str] = []
    for _, row in backbone_axes.iterrows():
        genes = str(row["genes"]).split(",")
        targets.extend([g.strip() for g in genes if g.strip()])
    return sorted(set(targets))


def build_baseline_prediction_matrix(
    truth_matrix: pd.DataFrame,
    backbone_targets: list[str],
) -> pd.DataFrame:
    """Build shared-mean baseline prediction using only the given backbone targets.

    The truth_matrix must have columns: target_gene + gene columns.
    The baseline prediction assigns the mean perturbation vector of the
    backbone targets to every target row.
    """
    truth_indexed = truth_matrix.set_index("target_gene")
    available = [t for t in backbone_targets if t in truth_indexed.index]
    if not available:
        raise ValueError(
            f"None of the backbone targets {backbone_targets} found in truth matrix "
            f"(index: {truth_indexed.index.tolist()})"
        )
    backbone_mean = truth_indexed.loc[available].mean(axis=0)
    records = []
    for target_gene in truth_indexed.index.astype(str).tolist():
        records.append({"target_gene": target_gene, **backbone_mean.to_dict()})
    return pd.DataFrame(records)


def score_prediction(
    prediction_matrix: pd.DataFrame,
    axis_membership: pd.DataFrame,
    truth_contract: pd.DataFrame,
) -> float:
    """Project prediction onto architecture and return backbone recovery score."""
    projected = project_prediction_to_axes(
        prediction=prediction_matrix,
        axis_membership=axis_membership,
        truth_contract=truth_contract,
    )
    return compute_backbone_recovery_score(projected)


def load_reference_baseline_scores() -> dict[str, float]:
    """Load per-cell-line baseline backbone recovery from smoke_summary.tsv."""
    if not SMOKE_SUMMARY_PATH.exists():
        return ORIGINAL_BASELINE_SCORES
    df = pd.read_csv(SMOKE_SUMMARY_PATH, sep="\t")
    baseline = df.loc[df["model_id"] == "shared_mean_baseline"]
    if baseline.empty:
        return ORIGINAL_BASELINE_SCORES
    result: dict[str, float] = {}
    for _, row in baseline.iterrows():
        cl = str(row["cell_line"])
        if cl in CELL_LINES:
            result[cl] = float(row["backbone_recovery_score"])
    if not result:
        return ORIGINAL_BASELINE_SCORES
    return result


def run_loto_audit(
    cell_line: str,
    truth_matrix: pd.DataFrame,
    backbone_targets: list[str],
    axis_membership: pd.DataFrame,
    truth_contract: pd.DataFrame,
) -> list[dict]:
    """Leave-One-Target-Out audit over the backbone set.

    For each backbone target, remove it from the backbone set, recompute
    the baseline, and record the resulting backbone recovery score.
    """
    results: list[dict] = []

    # Full baseline (all backbone targets)
    full_prediction = build_baseline_prediction_matrix(truth_matrix, backbone_targets)
    full_score = score_prediction(full_prediction, axis_membership, truth_contract)
    results.append({
        "audit_type": "loto",
        "variant": "full_baseline_all_backbone",
        "context": cell_line,
        "backbone_recovery": round(full_score, 6),
        "n_targets_used": len(backbone_targets),
    })

    # LOTO over backbone targets
    loto_scores: list[float] = []
    for held_out in backbone_targets:
        if held_out not in truth_matrix["target_gene"].values:
            continue
        subset = [t for t in backbone_targets if t != held_out]
        if not subset:
            continue
        prediction = build_baseline_prediction_matrix(truth_matrix, subset)
        score = score_prediction(prediction, axis_membership, truth_contract)
        loto_scores.append(score)
        results.append({
            "audit_type": "loto",
            "variant": f"remove_{held_out}",
            "context": cell_line,
            "backbone_recovery": round(score, 6),
            "n_targets_used": len(subset),
        })

    # Summary statistics
    if loto_scores:
        arr = np.array(loto_scores)
        results.append({
            "audit_type": "loto",
            "variant": "loto_mean",
            "context": cell_line,
            "backbone_recovery": round(float(arr.mean()), 6),
            "n_targets_used": len(backbone_targets) - 1,
        })
        results.append({
            "audit_type": "loto",
            "variant": "loto_min",
            "context": cell_line,
            "backbone_recovery": round(float(arr.min()), 6),
            "n_targets_used": len(backbone_targets) - 1,
        })
        results.append({
            "audit_type": "loto",
            "variant": "loto_max",
            "context": cell_line,
            "backbone_recovery": round(float(arr.max()), 6),
            "n_targets_used": len(backbone_targets) - 1,
        })
        results.append({
            "audit_type": "loto",
            "variant": "loto_std",
            "context": cell_line,
            "backbone_recovery": round(float(arr.std(ddof=1)), 6),
            "n_targets_used": len(backbone_targets) - 1,
        })

    return results


def build_baseline_from_mean_vector(
    eval_truth_matrix: pd.DataFrame,
    backbone_mean_vector: pd.Series,
) -> pd.DataFrame:
    """Apply a pre-computed backbone mean vector to every target in eval_truth_matrix.

    This is the true cross-context operation: the backbone mean comes from one
    cell line (source) and is applied to the target rows of another (eval).
    """
    truth_indexed = eval_truth_matrix.set_index("target_gene")
    # Align gene set to the eval matrix
    gene_cols = truth_indexed.columns.intersection(backbone_mean_vector.index)
    records = []
    for target_gene in truth_indexed.index.astype(str).tolist():
        row = {"target_gene": target_gene}
        for gene in truth_indexed.columns:
            row[gene] = float(backbone_mean_vector.get(gene, 0.0))
        records.append(row)
    return pd.DataFrame(records)


def get_backbone_mean_vector(
    truth_matrix: pd.DataFrame,
    backbone_targets: list[str],
) -> pd.Series:
    """Compute the backbone mean perturbation vector from a truth matrix."""
    truth_indexed = truth_matrix.set_index("target_gene")
    available = [t for t in backbone_targets if t in truth_indexed.index]
    if not available:
        raise ValueError(
            f"None of the backbone targets {backbone_targets} found in truth matrix"
        )
    return truth_indexed.loc[available].mean(axis=0)


def run_cross_context_audit(
    truth_matrices: dict[str, pd.DataFrame],
    backbone_targets: dict[str, list[str]],
    axis_membership: pd.DataFrame,
    truth_contract: pd.DataFrame,
) -> list[dict]:
    """Cross-context baseline audit.

    Build the backbone mean vector from the SOURCE cell line's truth data,
    then apply it as the prediction for every target in the EVAL cell line.
    This tests whether backbone structure is recurrent across cell contexts.
    """
    results: list[dict] = []
    pairs = [
        ("HCC38", "HCC1143"),
        ("HCC1143", "HCC38"),
    ]
    for source_cl, eval_cl in pairs:
        source_targets = backbone_targets.get(source_cl, [])
        source_matrix = truth_matrices.get(source_cl)
        eval_matrix = truth_matrices.get(eval_cl)
        if eval_matrix is None or source_matrix is None or not source_targets:
            continue
        # Compute backbone mean from SOURCE cell line
        backbone_mean = get_backbone_mean_vector(source_matrix, source_targets)
        # Apply to EVAL cell line's target rows
        prediction = build_baseline_from_mean_vector(eval_matrix, backbone_mean)
        score = score_prediction(prediction, axis_membership, truth_contract)
        results.append({
            "audit_type": "cross_context",
            "variant": f"backbone_from_{source_cl}",
            "context": eval_cl,
            "backbone_recovery": round(score, 6),
            "n_targets_used": len(source_targets),
        })
    return results


def build_reference_rows(ref_scores: dict[str, float]) -> list[dict]:
    """Build reference rows from original baseline scores."""
    rows: list[dict] = []
    for cl in CELL_LINES:
        score = ref_scores.get(cl)
        if score is not None:
            rows.append({
                "audit_type": "original_reference",
                "variant": "original_shared_mean_baseline",
                "context": cl,
                "backbone_recovery": round(score, 6),
                "n_targets_used": 6,  # canonical_backbone targets in contract
            })
    # Pooled reference (mean across HCC38 + HCC1143)
    scores = [ref_scores[cl] for cl in CELL_LINES if cl in ref_scores]
    if len(scores) == 2:
        rows.append({
            "audit_type": "original_reference",
            "variant": "original_shared_mean_baseline",
            "context": "pooled",
            "backbone_recovery": round(float(np.mean(scores)), 6),
            "n_targets_used": 6,
        })
    return rows


def compute_pooled_summary_rows(all_rows: list[dict]) -> list[dict]:
    """Add pooled (HCC38+HCC1143 averaged) rows for each variant.

    Skips original_reference audit_type since it already has its own pooled
    row from build_reference_rows.
    """
    df = pd.DataFrame(all_rows)
    pooled_rows: list[dict] = []
    for audit_type in df["audit_type"].unique():
        if audit_type == "original_reference":
            continue
        sub = df[df["audit_type"] == audit_type]
        for variant in sub["variant"].unique():
            var_rows = sub[sub["variant"] == variant]
            cl_scores = var_rows[var_rows["context"].isin(CELL_LINES)]
            if len(cl_scores) < 2:
                continue
            pooled_rows.append({
                "audit_type": audit_type,
                "variant": variant,
                "context": "pooled",
                "backbone_recovery": round(float(cl_scores["backbone_recovery"].mean()), 6),
                "n_targets_used": cl_scores["n_targets_used"].iloc[0],
            })
    return pooled_rows


def print_summary_table(all_rows: list[dict]) -> None:
    """Print a human-readable audit summary."""
    df = pd.DataFrame(all_rows)

    print("=" * 78)
    print("Shared-Mean Baseline Non-Oracle Audit")
    print("=" * 78)

    # Original reference
    print("\n--- Original Baseline Scores (from smoke_summary.tsv) ---")
    ref = df[df["audit_type"] == "original_reference"]
    for _, r in ref.iterrows():
        print(
            f"  {r['context']:<10s}  backbone_recovery={r['backbone_recovery']:.4f}"
        )

    # LOTO results
    print("\n--- Part A: Leave-One-Target-Out (LOTO) Audit ---")
    for cl in CELL_LINES:
        loto = df[(df["audit_type"] == "loto") & (df["context"] == cl)]
        if loto.empty:
            continue
        print(f"\n  Context: {cl}")
        full = loto[loto["variant"] == "full_baseline_all_backbone"]
        if not full.empty:
            print(
                f"    full baseline ({int(full['n_targets_used'].iloc[0])} backbone): "
                f"recovery={full['backbone_recovery'].iloc[0]:.4f}"
            )
        # Individual removals
        for _, r in loto[~loto["variant"].str.startswith("loto_")
                          & ~loto["variant"].str.startswith("full_")].iterrows():
            print(
                f"    {r['variant']:<30s}  "
                f"recovery={r['backbone_recovery']:.4f}  "
                f"(n={int(r['n_targets_used'])})"
            )
        # Summary stats
        for stat_label in ["loto_mean", "loto_min", "loto_max", "loto_std"]:
            stat_rows = loto[loto["variant"] == stat_label]
            if stat_rows.empty:
                continue
            r = stat_rows.iloc[0]
            print(
                f"    {stat_label:<30s}  "
                f"recovery={r['backbone_recovery']:.4f}  "
                f"(n={int(r['n_targets_used'])})"
            )

    # Cross-context results
    print("\n--- Part B: Cross-Context Baseline Audit ---")
    cc = df[df["audit_type"] == "cross_context"]
    for _, r in cc.iterrows():
        print(
            f"  {r['variant']:<30s}  eval_on={r['context']:<10s}  "
            f"recovery={r['backbone_recovery']:.4f}  "
            f"(n={int(r['n_targets_used'])})"
        )

    # Pooled comparison
    print("\n--- Pooled Comparison (HCC38 + HCC1143 mean) ---")
    for audit_type in ["original_reference", "loto", "cross_context"]:
        sub = df[(df["audit_type"] == audit_type) & (df["context"] == "pooled")]
        if sub.empty:
            continue
        # For loto, show the summary rows only
        if audit_type == "loto":
            sub = sub[sub["variant"].isin(
                ["full_baseline_all_backbone", "loto_mean", "loto_min", "loto_max"]
            )]
        for _, r in sub.iterrows():
            print(
                f"  [{audit_type}] {r['variant']:<35s}  "
                f"recovery={r['backbone_recovery']:.4f}"
            )

    print("\n" + "=" * 78)
    print("Interpretation:")
    print("  - LOTO mean close to original -> baseline is NOT oracle-driven by")
    print("    any single backbone target.")
    print("  - Cross-context scores > 0.5 (null expectation) -> backbone")
    print("    structure is recurrent across contexts, not context-overfitted.")
    print("=" * 78)


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    print("Loading architecture contracts...")
    truth_contract = load_truth_contract(TRUTH_CONTRACT_PATH)
    axis_membership = load_axis_membership(AXIS_MEMBERSHIP_PATH)

    backbone_targets_all = get_backbone_targets(truth_contract)
    print(f"Canonical backbone targets (from contract): {backbone_targets_all}")

    # Load reference baseline scores from smoke summary
    ref_scores = load_reference_baseline_scores()
    print(f"Reference baseline scores: {ref_scores}")

    # Compute truth log-shift matrices for each cell line
    print("\nLoading Stage 2 truth config and computing per-target shift matrices...")
    stage2_config = load_config(TRUTH_CONFIG_PATH)
    specs = {spec.cell_line: spec for spec in build_dataset_specs(stage2_config)}

    truth_matrices: dict[str, pd.DataFrame] = {}
    backbone_targets_by_cl: dict[str, list[str]] = {}

    for cell_line in CELL_LINES:
        if cell_line not in specs:
            raise RuntimeError(f"Cell line {cell_line} not found in config")
        spec = specs[cell_line]
        print(f"  Computing truth matrix for {cell_line}...")
        truth_matrix = compute_stage2_truth_aligned_log_shift_matrix(
            spec, stage2_config, axis_membership
        )
        truth_matrices[cell_line] = truth_matrix
        print(f"    Shape: {truth_matrix.shape}")

        # Backbone targets present in this cell line
        present = sorted(set(backbone_targets_all) & set(truth_matrix["target_gene"]))
        backbone_targets_by_cl[cell_line] = present
        print(f"    Present backbone targets: {present}")

    # Collect all result rows
    all_rows: list[dict] = []

    # Reference rows
    all_rows.extend(build_reference_rows(ref_scores))

    # Part A: LOTO audit
    print("\n--- Part A: Leave-One-Target-Out (LOTO) Audit ---")
    for cell_line in CELL_LINES:
        print(f"  Running LOTO for {cell_line}...")
        loto_rows = run_loto_audit(
            cell_line=cell_line,
            truth_matrix=truth_matrices[cell_line],
            backbone_targets=backbone_targets_by_cl[cell_line],
            axis_membership=axis_membership,
            truth_contract=truth_contract,
        )
        all_rows.extend(loto_rows)

    # Part B: Cross-context audit
    print("\n--- Part B: Cross-Context Audit ---")
    cc_rows = run_cross_context_audit(
        truth_matrices=truth_matrices,
        backbone_targets=backbone_targets_by_cl,
        axis_membership=axis_membership,
        truth_contract=truth_contract,
    )
    all_rows.extend(cc_rows)

    # Compute pooled summary rows
    pooled_rows = compute_pooled_summary_rows(all_rows)
    all_rows.extend(pooled_rows)

    # Save output
    result_df = pd.DataFrame(all_rows)
    # Sort: original_reference first, then loto, then cross_context
    audit_order = {"original_reference": 0, "loto": 1, "cross_context": 2}
    result_df["_sort"] = result_df["audit_type"].map(audit_order).fillna(99)
    result_df = result_df.sort_values(
        ["_sort", "context", "variant"]
    ).drop(columns=["_sort"])
    result_df.to_csv(OUTPATH, sep="\t", index=False)

    print(f"\nOutput written to {OUTPATH.resolve()}")
    print_summary_table(all_rows)


if __name__ == "__main__":
    main()
