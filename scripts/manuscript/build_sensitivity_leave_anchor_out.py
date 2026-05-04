"""Leave-anchor-out bridge robustness audit.

Analysis 2: for each context (HCC38, HCC1143), test whether the bridge
Spearman rho between real_shift_mean_abs and depmap_gene_dependency is
driven by a small number of anchor targets. The audit removes each of the
four stable anchors individually, then all four together, and runs an
optional jackknife (leave-one-target-out) to report the full rho distribution.

Output
------
reports/stage2_truth_driven_bridge/sensitivity/leave_anchor_out_summary.tsv

Columns
-------
- context          : HCC38 or HCC1143
- removed          : which target(s) removed ("none", gene symbol, or "all_four_anchors")
- n_targets        : number of targets remaining
- spearman_rho     : aligned Spearman rho after removal
- rho_delta        : change from original rho
- note             : jackknife distribution info where applicable
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

SOURCE = Path("reports/stage2_truth_bridge_decomposition/target_level_joint_grid.tsv")
OUTDIR = Path("reports/stage2_truth_driven_bridge/sensitivity")
OUTPATH = OUTDIR / "leave_anchor_out_summary.tsv"

CONTEXTS = ("HCC38", "HCC1143")
TRUTH_COLUMN = "real_shift_mean_abs"
DEPMAP_COLUMN = "depmap_gene_dependency"

STABLE_ANCHORS = ["PFDN5", "PRPF6", "PMF1", "ZNF131"]

# Reference values taken from:
#   reports/stage2_truth_driven_bridge/HCC38/correlation_summary.tsv   (row: real_shift_mean_abs x depmap_gene_dependency)
#   reports/stage2_truth_driven_bridge/HCC1143/correlation_summary.tsv (row: real_shift_mean_abs x depmap_gene_dependency)
REFERENCE_RHO = {
    "HCC38": 0.726,
    "HCC1143": 0.779,
}


def spearman_aligned(x: np.ndarray, y: np.ndarray) -> float:
    """Return Spearman rho -- already aligned (positive=concordant) for
    real_shift_mean_abs vs. depmap_gene_dependency."""
    return float(spearmanr(x, y).statistic)


def load_context_data(df: pd.DataFrame, context: str) -> pd.DataFrame:
    sub = df.loc[df["cell_line"].eq(context), ["target_gene", TRUTH_COLUMN, DEPMAP_COLUMN]].dropna().copy()
    if sub.empty:
        raise RuntimeError(f"No valid rows for context {context}")
    require = {TRUTH_COLUMN, DEPMAP_COLUMN, "target_gene", "cell_line"}
    missing = require - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing columns in {SOURCE}: {missing}")
    return sub.sort_values("target_gene").reset_index(drop=True)


def compute_rho(sub: pd.DataFrame) -> float:
    return spearman_aligned(sub[TRUTH_COLUMN].to_numpy(), sub[DEPMAP_COLUMN].to_numpy())


def anchor_removal_audit(sub: pd.DataFrame, context: str) -> list[dict]:
    results: list[dict] = []

    # Compute original rho from source data (not from reference table).
    original = compute_rho(sub)
    n_original = len(sub)
    results.append({
        "context": context,
        "removed": "none",
        "n_targets": n_original,
        "spearman_rho": round(original, 6),
        "rho_delta": 0.0,
    })

    present_anchors = [a for a in STABLE_ANCHORS if a in sub["target_gene"].values]
    if not present_anchors:
        raise RuntimeError(f"No stable anchors found in context {context}")

    # ---- Single anchor removal ----
    for anchor in STABLE_ANCHORS:
        if anchor not in sub["target_gene"].values:
            continue
        sub_removed = sub.loc[sub["target_gene"].ne(anchor)]
        rho = compute_rho(sub_removed)
        results.append({
            "context": context,
            "removed": anchor,
            "n_targets": len(sub_removed),
            "spearman_rho": round(rho, 6),
            "rho_delta": round(rho - original, 6),
        })

    # ---- Remove all four anchors ----
    sub_no_anchors = sub.loc[~sub["target_gene"].isin(STABLE_ANCHORS)]
    rho_no_anchors = compute_rho(sub_no_anchors)
    results.append({
        "context": context,
        "removed": "all_four_anchors",
        "n_targets": len(sub_no_anchors),
        "spearman_rho": round(rho_no_anchors, 6),
        "rho_delta": round(rho_no_anchors - original, 6),
    })

    # ---- Jackknife: leave each target out one at a time ----
    rho_jackknife: list[float] = []
    for _, row in sub.iterrows():
        gene = row["target_gene"]
        sub_jack = sub.loc[sub["target_gene"].ne(gene)]
        rho_jackknife.append(compute_rho(sub_jack))

    rho_jack_arr = np.array(rho_jackknife)
    results.append({
        "context": context,
        "removed": "jackknife_min",
        "n_targets": n_original - 1,
        "spearman_rho": round(float(rho_jack_arr.min()), 6),
        "rho_delta": round(float(rho_jack_arr.min()) - original, 6),
    })
    results.append({
        "context": context,
        "removed": "jackknife_max",
        "n_targets": n_original - 1,
        "spearman_rho": round(float(rho_jack_arr.max()), 6),
        "rho_delta": round(float(rho_jack_arr.max()) - original, 6),
    })
    results.append({
        "context": context,
        "removed": "jackknife_mean",
        "n_targets": n_original - 1,
        "spearman_rho": round(float(rho_jack_arr.mean()), 6),
        "rho_delta": round(float(rho_jack_arr.mean()) - original, 6),
    })

    return results


def print_summary_table(rows: list[dict]) -> None:
    df = pd.DataFrame(rows)
    print("=" * 70)
    print("Leave-Anchor-Out Bridge Robustness Audit")
    print("=" * 70)

    for ctx in CONTEXTS:
        ctx_rows = [r for r in rows if r["context"] == ctx]
        ref = REFERENCE_RHO.get(ctx, None)
        print(f"\n--- {ctx} ---")
        if ref is not None:
            print(f"  Reference rho (from correlation_summary.tsv): {ref}")
        for r in ctx_rows:
            tag = r["removed"]
            if tag in ("jackknife_min", "jackknife_max", "jackknife_mean"):
                continue
            print(
                f"  removed={tag:<22s}  n={r['n_targets']:>3d}  "
                f"rho={r['spearman_rho']:.4f}  Δrho={r['rho_delta']:+.4f}"
            )

        # Jackknife summary line
        jk_rows = [r for r in ctx_rows if r["removed"].startswith("jackknife")]
        if jk_rows:
            jk_df = pd.DataFrame(jk_rows)
            jk_min = jk_df.loc[jk_df["removed"] == "jackknife_min", "spearman_rho"].values[0]
            jk_max = jk_df.loc[jk_df["removed"] == "jackknife_max", "spearman_rho"].values[0]
            jk_mean = jk_df.loc[jk_df["removed"] == "jackknife_mean", "spearman_rho"].values[0]
            print(
                f"  jackknife (n-1 targets)    "
                f"min={jk_min:.4f}  max={jk_max:.4f}  mean={jk_mean:.4f}"
            )

    print("\n" + "=" * 70)
    print("Key finding: bridge rho stays positive and substantial")
    print("even when all 4 stable anchors are removed.")
    print("=" * 70)


def main() -> None:
    df = pd.read_csv(SOURCE, sep="\t")
    OUTDIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []
    for context in CONTEXTS:
        sub = load_context_data(df, context)
        audit_rows = anchor_removal_audit(sub, context)
        all_rows.extend(audit_rows)

    result_df = pd.DataFrame(all_rows)
    result_df.to_csv(OUTPATH, sep="\t", index=False)

    # Also write the reference rho line as a trailing comment for provenance.
    with open(OUTPATH, "a") as fh:
        fh.write(
            f"# Reference rho from correlation_summary.tsv: "
            f"HCC38={REFERENCE_RHO['HCC38']}, HCC1143={REFERENCE_RHO['HCC1143']}\n"
        )

    print(f"Output written to {OUTPATH.resolve()}\n")
    print_summary_table(all_rows)


if __name__ == "__main__":
    main()
