"""Regression guard for ED Fig. 3 panel b Replogle bridge statistics (seeded permutation).

Run: PYTHONPATH=src python tests/test_extended_data_figure3_replogle_bridge.py
"""

from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
REPLOGLE_JOINT_GRID = (
    REPO_ROOT
    / "reports/manuscript_extended_data_v1/edfig3_k562_replogle_joint_grid/replogle_k562_essential_joint_grid.tsv"
)


@unittest.skipUnless(REPLOGLE_JOINT_GRID.is_file(), "Replogle joint grid report missing")
class ReplogleBridgeSummaryTests(unittest.TestCase):
    def test_compute_summary_reproducible(self) -> None:
        from wtbench.manuscript.extended_data_figure3_v2 import (
            REPLOGLE_PERM_ITERATIONS,
            REPLOGLE_PERM_SEED,
            compute_replogle_bridge_summary,
        )

        raw = pd.read_csv(REPLOGLE_JOINT_GRID, sep="\t")
        summary = compute_replogle_bridge_summary(raw)

        self.assertEqual(summary["bridge_truth_metric"], "real_shift_mean_abs")
        self.assertEqual(summary["bridge_depmap_endpoint"], "depmap_gene_dependency")
        self.assertEqual(summary["bridge_perm_iterations"], REPLOGLE_PERM_ITERATIONS)
        self.assertEqual(summary["bridge_perm_seed"], REPLOGLE_PERM_SEED)
        self.assertGreaterEqual(summary["bridge_n_targets"], 100)

        self.assertAlmostEqual(summary["bridge_spearman_rho_aligned"], 0.4018413096087801, places=12)
        self.assertAlmostEqual(summary["bridge_ci_lo_fisher95"], 0.36325171556244534, places=12)
        self.assertAlmostEqual(summary["bridge_ci_hi_fisher95"], 0.43905452871832784, places=12)
        self.assertAlmostEqual(summary["bridge_empirical_p_two_sided_shuffle"], 0.000999001, places=9)

    def test_build_panel_b_has_summary_row(self) -> None:
        from wtbench.manuscript.extended_data_figure3_v2 import build_panel_b_source

        tbl = build_panel_b_source(REPO_ROOT)
        self.assertGreaterEqual(tbl["record_type"].eq("joint_grid_target").sum(), 100)
        self.assertEqual((tbl["record_type"] == "replogle_bridge_correlation_summary").sum(), 1)
        summ = tbl.loc[tbl["record_type"].eq("replogle_bridge_correlation_summary")].iloc[0]
        self.assertFalse(pd.isna(summ["bridge_spearman_rho_aligned"]))


if __name__ == "__main__":
    unittest.main()
