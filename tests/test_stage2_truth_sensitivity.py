from __future__ import annotations

import unittest

import pandas as pd

from wtbench.stage2_truth_sensitivity import audit_covariate_balance, rank_stability_vs_baseline


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


if __name__ == "__main__":
    unittest.main()