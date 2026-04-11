from __future__ import annotations

import unittest

import pandas as pd

from wtbench.stage2_truth_sensitivity import (
    add_sensitivity_run_state,
    audit_covariate_balance,
    get_covariate_strat_columns,
    rank_stability_vs_baseline,
    run_covariate_audits,
)


class Stage2SensitivityHelpersTests(unittest.TestCase):
    def test_rank_stability_perfect_when_identical(self) -> None:
        base = pd.DataFrame(
            {
                "target_gene": ["A", "B", "C"],
                "real_shift_L2": [1.0, 2.0, 3.0],
            }
        )
        rep = pd.DataFrame(
            {
                "target_gene": ["A", "B", "C"],
                "real_shift_L2": [1.0, 2.0, 3.0],
            }
        )
        out = rank_stability_vs_baseline(base, rep, ["real_shift_L2"])
        self.assertAlmostEqual(float(out["spearman_rank_vs_baseline"].iloc[0]), 1.0)

    def test_audit_covariate_balance_tv(self) -> None:
        calls = pd.DataFrame(
            {
                "cell_barcode": ["c1", "c2", "t1", "t2"],
                "target_gene": ["x", "x", "T", "T"],
                "is_control": [True, True, False, False],
            }
        )
        cov = pd.DataFrame(
            {
                "cell_barcode": ["c1", "c2", "t1", "t2"],
                "lane": ["L1", "L1", "L2", "L2"],
            }
        )
        out = audit_covariate_balance(calls, cov, barcode_col="cell_barcode", strat_col="lane")
        row = out.loc[out["target_gene"].eq("T")].iloc[0]
        self.assertEqual(row["n_target_cells"], 2)
        self.assertEqual(row["n_control_cells"], 2)
        self.assertGreater(row["total_variation_distance"], 0.0)

    def test_run_covariate_audits_supports_multiple_strat_columns(self) -> None:
        calls = pd.DataFrame(
            {
                "cell_barcode": ["c1", "c2", "t1", "t2"],
                "target_gene": ["x", "x", "T", "T"],
                "is_control": [True, True, False, False],
            }
        )
        cov = pd.DataFrame(
            {
                "cell_barcode": ["c1", "c2", "t1", "t2"],
                "lane": ["L1", "L1", "L2", "L2"],
                "umi_bin": ["low", "high", "low", "high"],
            }
        )
        out = run_covariate_audits(
            calls,
            cov,
            barcode_col="cell_barcode",
            strat_columns=["lane", "umi_bin"],
        )
        self.assertEqual(set(out["strat_column"]), {"lane", "umi_bin"})
        self.assertTrue((out["n_strata"] >= 2).all())

    def test_get_covariate_strat_columns_supports_legacy_and_multi_axis(self) -> None:
        self.assertEqual(
            get_covariate_strat_columns({"strat_column": "lane"}),
            ["lane"],
        )
        self.assertEqual(
            get_covariate_strat_columns({"strat_columns": ["lane", "umi_bin"]}),
            ["lane", "umi_bin"],
        )

    def test_add_sensitivity_run_state_marks_incomplete_runs_non_citable(self) -> None:
        summary = pd.DataFrame(
            {
                "cell_line": ["HCC38"],
                "truth_metric": ["real_shift_L2"],
                "depmap_endpoint": ["depmap_gene_effect"],
                "n_replicates": [2],
                "spearman_aligned_mean": [0.7],
                "spearman_aligned_std": [0.01],
                "spearman_aligned_q025": [0.68],
                "spearman_aligned_q50": [0.70],
                "spearman_aligned_q975": [0.72],
            }
        )
        out = add_sensitivity_run_state(summary, configured_replicates=24)
        row = out.iloc[0]
        self.assertEqual(int(row["configured_replicates"]), 24)
        self.assertEqual(int(row["completed_replicates"]), 2)
        self.assertFalse(bool(row["formal_interval_citable"]))
        self.assertEqual(row["sensitivity_claim_status"], "partial_preliminary_snapshot")


if __name__ == "__main__":
    unittest.main()
