"""Bridge aligned-Spearman permutation null for Figure 1 panel (f).

This is a closed definition: for the HCC38/HCC1143 primary bridge pair
(real_shift_mean_abs, depmap_gene_dependency), we shuffle the target-to-DepMap
mapping within each cell line and recompute the aligned Spearman rho 1000 times.
The resulting percentile envelope is used as the null band in Figure 1(f).

It does not retrain any model, does not change any truth-object contract, and
does not change claim boundaries. It only formalizes the null reference that
Figure 1(f) currently approximates with a Fisher z-transform envelope.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


DEFAULT_SOURCE = Path("reports/stage2_truth_bridge_decomposition/target_level_joint_grid.tsv")
DEFAULT_OUTDIR = Path("reports/manuscript_permutation_null_v1")

PRIMARY_CONTEXTS = ("HCC38", "HCC1143")
TRUTH_METRIC_COLUMN = "real_shift_mean_abs"
DEPMAP_COLUMN = "depmap_gene_dependency"


def compute_bridge_rho_null(
    *,
    source: Path,
    outdir: Path,
    iterations: int,
    seed: int,
) -> dict[str, dict[str, float]]:
    df = pd.read_csv(source, sep="\t")
    missing = [c for c in (TRUTH_METRIC_COLUMN, DEPMAP_COLUMN, "cell_line", "target_gene") if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing columns in {source}: {missing}")

    rows: list[dict[str, float]] = []
    distributions: dict[str, np.ndarray] = {}
    rng_master = np.random.default_rng(seed)

    for context in PRIMARY_CONTEXTS:
        sub = df.loc[df["cell_line"].eq(context), [TRUTH_METRIC_COLUMN, DEPMAP_COLUMN]].dropna().copy()
        if sub.empty:
            raise RuntimeError(f"No valid rows for context {context}")
        truth = sub[TRUTH_METRIC_COLUMN].to_numpy()
        depmap = sub[DEPMAP_COLUMN].to_numpy()
        observed = float(spearmanr(truth, depmap).statistic)

        # Permutation: shuffle the target-to-DepMap mapping.
        context_seed = int(rng_master.integers(0, 2**31 - 1))
        rng = np.random.default_rng(context_seed)
        null = np.empty(iterations, dtype=float)
        depmap_shuffled = depmap.copy()
        for i in range(iterations):
            rng.shuffle(depmap_shuffled)
            null[i] = spearmanr(truth, depmap_shuffled).statistic
        distributions[context] = null

        q025, q975 = np.quantile(null, [0.025, 0.975])
        q005, q995 = np.quantile(null, [0.005, 0.995])
        null_abs_q95 = float(np.quantile(np.abs(null), 0.95))
        empirical_p = float(((np.abs(null) >= abs(observed)).sum() + 1) / (iterations + 1))
        rows.append(
            {
                "cell_line": context,
                "truth_metric": TRUTH_METRIC_COLUMN,
                "depmap_endpoint": DEPMAP_COLUMN,
                "n_targets": int(len(truth)),
                "observed_spearman_rho_aligned": observed,
                "null_iterations": int(iterations),
                "null_mean": float(null.mean()),
                "null_sd": float(null.std(ddof=1)),
                "null_q005": float(q005),
                "null_q025": float(q025),
                "null_q500": float(np.quantile(null, 0.5)),
                "null_q975": float(q975),
                "null_q995": float(q995),
                "null_abs_q95": null_abs_q95,
                "empirical_p_two_sided": empirical_p,
                "seed": context_seed,
            }
        )

    outdir.mkdir(parents=True, exist_ok=True)
    summary_path = outdir / "bridge_rho_permutation_summary.tsv"
    pd.DataFrame(rows).to_csv(summary_path, sep="\t", index=False)

    dist_path = outdir / "bridge_rho_permutation_distribution.tsv.gz"
    dist_rows: list[dict[str, float]] = []
    for context, arr in distributions.items():
        for i, v in enumerate(arr):
            dist_rows.append({"cell_line": context, "iteration": int(i), "null_rho": float(v)})
    pd.DataFrame(dist_rows).to_csv(dist_path, sep="\t", index=False, compression="gzip")

    meta_path = outdir / "bridge_rho_permutation_meta.json"
    meta_path.write_text(
        json.dumps(
            {
                "source": str(source),
                "iterations": int(iterations),
                "master_seed": int(seed),
                "truth_metric": TRUTH_METRIC_COLUMN,
                "depmap_endpoint": DEPMAP_COLUMN,
                "contexts": list(PRIMARY_CONTEXTS),
                "null_type": "target_to_depmap_permutation",
                "alignment_note": "For (real_shift_mean_abs, depmap_gene_dependency) the aligned Spearman equals the raw Spearman, so the empirical null is symmetric around zero and a two-sided envelope is used.",
            },
            indent=2,
        )
    )

    return {row["cell_line"]: row for row in rows}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Bridge aligned-Spearman permutation null for Figure 1 panel (f).")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260422)
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    source = args.source if args.source.is_absolute() else repo_root / args.source
    outdir = args.outdir if args.outdir.is_absolute() else repo_root / args.outdir

    summary = compute_bridge_rho_null(
        source=source,
        outdir=outdir,
        iterations=args.iterations,
        seed=args.seed,
    )
    for context, row in summary.items():
        print(
            f"{context}: observed={row['observed_spearman_rho_aligned']:.4f}, "
            f"null 95% envelope=[{row['null_q025']:.4f}, {row['null_q975']:.4f}], "
            f"empirical_p={row['empirical_p_two_sided']:.4f}"
        )


if __name__ == "__main__":
    main()
