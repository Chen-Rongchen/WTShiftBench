"""Bootstrap target-resampling uncertainty for model adjudication scores.

Analysis 3: quantify the stability of the "asymmetric recovery pattern"
(backbone recovery favours baseline, separation favours GEARS, shift-excess
tied) by bootstrapping targets with replacement and recomputing the three
structure scores for shared_mean_baseline and gears_hcc_formal_v1.

Output
------
reports/truth_driven_bridge/sensitivity/bootstrap_score_uncertainty.tsv
reports/truth_driven_bridge/sensitivity/bootstrap_delta_summary.tsv
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wtbench.model_structure_scorer import (  # noqa: E402
    compute_backbone_recovery_score,
    compute_shift_excess_identification_score,
    compute_structure_vs_context_separation_score,
)

OUTDIR = PROJECT_ROOT / "reports/truth_driven_bridge/sensitivity"
OUTDIR.mkdir(parents=True, exist_ok=True)

DETAILS_DIR = PROJECT_ROOT / "reports/real_hcc_smoke/details"
CELL_LINES = ("HCC38", "HCC1143")
MODELS = {
    "shared_mean_baseline": "baseline",
    "gears_hcc_formal_v1": "entrant",
}
N_BOOTSTRAP = 1000
RANDOM_SEED = 20260420
QUANTILES = [0.025, 0.975]

SCORE_FUNCTIONS = {
    "backbone_recovery": compute_backbone_recovery_score,
    "shift_excess_identification": compute_shift_excess_identification_score,
    "structure_vs_context_separation": compute_structure_vs_context_separation_score,
}


# ---------------------------------------------------------------------------
# Load projection data
# ---------------------------------------------------------------------------
def load_all_projections() -> dict[str, dict[str, pd.DataFrame]]:
    """Return {model_id: {cell_line: projected_df}}."""
    data: dict[str, dict[str, pd.DataFrame]] = {}
    for model_id in MODELS:
        data[model_id] = {}
        for cl in CELL_LINES:
            path = DETAILS_DIR / model_id / cl / "axis_projection.tsv"
            df = pd.read_csv(path, sep="\t")
            data[model_id][cl] = df
    return data


def get_target_universe(projections: dict[str, dict[str, pd.DataFrame]]) -> list[str]:
    """Return the sorted list of target genes common to all model/cell-line combos."""
    sets = []
    for model_data in projections.values():
        for df in model_data.values():
            sets.append(set(df["target_gene"].unique()))
    common = sets[0]
    for s in sets[1:]:
        common = common & s
    return sorted(common)


# ---------------------------------------------------------------------------
# Bootstrap helpers
# ---------------------------------------------------------------------------
def build_bootstrapped_projection(
    original: pd.DataFrame,
    resampled_targets: list[str],
) -> pd.DataFrame:
    """Create a projection DataFrame for a single bootstrap draw.

    Each element of *resampled_targets* is a target gene name (may contain
    duplicates for genes drawn multiple times).  We assign a unique synthetic
    ``target_gene`` to each occurrence so that scorer functions which group
    by target treat them as independent draws.
    """
    seen: dict[str, int] = {}
    rows: list[pd.DataFrame] = []
    for orig_gene in resampled_targets:
        count = seen.get(orig_gene, 0)
        synthetic = f"{orig_gene}#b{count}" if count > 0 else orig_gene
        seen[orig_gene] = count + 1
        chunk = original[original["target_gene"] == orig_gene].copy()
        chunk["target_gene"] = synthetic
        rows.append(chunk)

    return pd.concat(rows, ignore_index=True)


def compute_scores_for_resample(
    projections: dict[str, dict[str, pd.DataFrame]],
    target_pool: list[str],
    rng: np.random.Generator,
) -> dict[str, dict[str, float]]:
    """Compute bootstrapped scores for one iteration.

    Returns {model_id: {score_name: cell_line_averaged_score}}.
    """
    n = len(target_pool)
    resampled = rng.choice(target_pool, size=n, replace=True).tolist()

    scores: dict[str, dict[str, float]] = {}
    for model_id in MODELS:
        scores[model_id] = {}
        cl_scores: dict[str, dict[str, float]] = {}
        for cl in CELL_LINES:
            boot_df = build_bootstrapped_projection(projections[model_id][cl], resampled)
            cl_scores[cl] = {}
            for score_name, score_fn in SCORE_FUNCTIONS.items():
                cl_scores[cl][score_name] = score_fn(boot_df)

        # Average across cell lines (skipping NaN cells)
        for score_name in SCORE_FUNCTIONS:
            vals = [cl_scores[cl][score_name] for cl in CELL_LINES]
            # If all cell-line scores are NaN, the average is NaN
            if all(np.isnan(v) for v in vals):
                scores[model_id][score_name] = float("nan")
            else:
                scores[model_id][score_name] = float(np.nanmean(vals))
    return scores


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------
def bootstrap_stats(draws: np.ndarray) -> dict:
    """Compute summary statistics for a bootstrap distribution, ignoring NaN."""
    valid = draws[~np.isnan(draws)]
    n_total = len(draws)
    n_valid = len(valid)
    if n_valid == 0:
        return {
            "mean": float("nan"),
            "ci_lower": float("nan"),
            "ci_upper": float("nan"),
            "n_valid": 0,
            "n_total": n_total,
        }
    return {
        "mean": float(np.mean(valid)),
        "ci_lower": float(np.quantile(valid, QUANTILES[0])),
        "ci_upper": float(np.quantile(valid, QUANTILES[1])),
        "n_valid": n_valid,
        "n_total": n_total,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    rng = np.random.default_rng(RANDOM_SEED)

    # Suppress the "Mean of empty slice" warnings that come from nanmean
    # when all cell-line scores are NaN for a bootstrap draw.
    warnings.filterwarnings("ignore", category=RuntimeWarning, message="Mean of empty slice")

    print("Loading projection data ...")
    projections = load_all_projections()
    target_pool = get_target_universe(projections)
    print(f"  Target universe: {len(target_pool)} genes")

    # Storage for bootstrap draws (raw values, may contain NaN)
    score_draws: dict[str, dict[str, list[float]]] = {
        sn: {mid: [] for mid in MODELS} for sn in SCORE_FUNCTIONS
    }
    delta_draws: dict[str, list[float]] = {sn: [] for sn in SCORE_FUNCTIONS}

    print(f"Running {N_BOOTSTRAP} bootstrap iterations ...")
    for i in range(N_BOOTSTRAP):
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{N_BOOTSTRAP}")
        iter_scores = compute_scores_for_resample(projections, target_pool, rng)
        for sn in SCORE_FUNCTIONS:
            for mid in MODELS:
                score_draws[sn][mid].append(iter_scores[mid][sn])
            baseline_val = iter_scores["shared_mean_baseline"][sn]
            gears_val = iter_scores["gears_hcc_formal_v1"][sn]
            delta_draws[sn].append(
                baseline_val - gears_val
                if not (np.isnan(baseline_val) or np.isnan(gears_val))
                else float("nan")
            )

    # -----------------------------------------------------------------------
    # Summarise: per-model bootstrap stats
    # -----------------------------------------------------------------------
    rows_score: list[dict] = []
    baseline_id = "shared_mean_baseline"
    for sn in SCORE_FUNCTIONS:
        baseline_arr = np.array(score_draws[sn][baseline_id])
        gears_arr = np.array(score_draws[sn]["gears_hcc_formal_v1"])
        # Valid comparisons (both non-NaN)
        valid_mask = ~np.isnan(baseline_arr) & ~np.isnan(gears_arr)
        n_valid_cmp = int(valid_mask.sum())

        for mid in MODELS:
            draws = np.array(score_draws[sn][mid])
            stats = bootstrap_stats(draws)
            # sign stability: % of VALID draws where baseline > GEARS
            if n_valid_cmp > 0:
                sign_stab = float(
                    np.mean(
                        baseline_arr[valid_mask] > gears_arr[valid_mask]
                    )
                    * 100
                )
            else:
                sign_stab = float("nan")

            rows_score.append(
                {
                    "metric": sn,
                    "model": mid,
                    "mean": stats["mean"],
                    "ci_lower": stats["ci_lower"],
                    "ci_upper": stats["ci_upper"],
                    "n_valid_draws": stats["n_valid"],
                    "n_total_draws": stats["n_total"],
                    "sign_stability_pct": sign_stab,
                    "n_valid_comparisons": n_valid_cmp,
                }
            )

    score_df = pd.DataFrame(rows_score)
    out_score = OUTDIR / "bootstrap_score_uncertainty.tsv"
    score_df.to_csv(out_score, sep="\t", index=False, float_format="%.6f", na_rep="nan")
    print(f"\nSaved: {out_score}")

    # -----------------------------------------------------------------------
    # Summarise: delta (baseline - GEARS) stats
    # -----------------------------------------------------------------------
    rows_delta: list[dict] = []
    for sn in SCORE_FUNCTIONS:
        draws = np.array(delta_draws[sn])
        stats = bootstrap_stats(draws)
        # sign stability among valid deltas
        valid = draws[~np.isnan(draws)]
        if len(valid) > 0:
            sign_stab = float(np.mean(valid > 0) * 100)
        else:
            sign_stab = float("nan")
        rows_delta.append(
            {
                "metric": sn,
                "delta_mean": stats["mean"],
                "delta_ci_lower": stats["ci_lower"],
                "delta_ci_upper": stats["ci_upper"],
                "sign_stability_pct": sign_stab,
                "n_valid_draws": stats["n_valid"],
                "n_total_draws": stats["n_total"],
            }
        )

    delta_df = pd.DataFrame(rows_delta)
    out_delta = OUTDIR / "bootstrap_delta_summary.tsv"
    delta_df.to_csv(out_delta, sep="\t", index=False, float_format="%.6f", na_rep="nan")
    print(f"Saved: {out_delta}")

    # -----------------------------------------------------------------------
    # Print key findings
    # -----------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Key bootstrap findings (baseline - GEARS delta)")
    print("=" * 72)
    for row in rows_delta:
        sn = row["metric"]
        n_valid = row["n_valid_draws"]
        n_total = row["n_total_draws"]
        direction = (
            "baseline > GEARS (stable)"
            if row["sign_stability_pct"] > 90
            else (
                "GEARS > baseline (stable)"
                if row["sign_stability_pct"] < 10
                else "unstable / tied"
            )
        )
        print(f"  {sn}:")
        print(
            f"    delta = {row['delta_mean']:+.4f}  "
            f"[{row['delta_ci_lower']:+.4f}, {row['delta_ci_upper']:+.4f}]"
        )
        print(
            f"    sign_stability (baseline > GEARS) = {row['sign_stability_pct']:.1f}%"
            f"  ({n_valid}/{n_total} valid draws)"
        )
        print(f"    interpretation: {direction}")


if __name__ == "__main__":
    main()
