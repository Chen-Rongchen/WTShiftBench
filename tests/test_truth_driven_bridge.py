from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from wtbench.truth_bridge import (
    DatasetSpec,
    assign_quantile_groups,
    build_cross_cell_line_outputs,
    classify_join_status,
    build_dataset_specs,
    mean_pairwise_distance,
    parse_target_gene,
    resolve_single_perturbation_status,
    resolve_edistance_pairwise_max_points,
    summarize_correlations,
    summarize_group_comparisons,
)


class Stage2TruthBridgeHelpersTests(unittest.TestCase):
    def test_parse_target_gene_strips_sgrna_suffix(self) -> None:
        self.assertEqual(parse_target_gene("ARID1A_sgRNA2"), "ARID1A")
        self.assertEqual(parse_target_gene("intergenic_chr_5_sgRNA1"), "intergenic_chr_5")

    def test_classify_join_status(self) -> None:
        self.assertEqual(classify_join_status(-0.5, -0.2), "both")
        self.assertEqual(classify_join_status(-0.5, np.nan), "effect_only")
        self.assertEqual(classify_join_status(np.nan, -0.2), "dependency_only")
        self.assertEqual(classify_join_status(np.nan, np.nan), "none")

    def test_assign_quantile_groups_produces_high_low_mid(self) -> None:
        values = pd.Series([1, 2, 3, 4, 5, 6], dtype=float)
        groups = assign_quantile_groups(values, q_low=1 / 3, q_high=2 / 3)
        self.assertEqual(groups.tolist().count("low"), 2)
        self.assertEqual(groups.tolist().count("high"), 2)
        self.assertEqual(groups.tolist().count("mid"), 2)

    def test_build_dataset_specs_accepts_h5ad_source(self) -> None:
        specs = build_dataset_specs(
            {
                "datasets": [
                    {
                        "cell_line": "dixit_2016_raw__control_context",
                        "depmap_model_id": "ACH-000551",
                        "source_kind": "h5ad_obs",
                        "h5ad_path": "data/processed/stage1a/candidate_formal_like/dixit_2016_raw__control_context.h5ad",
                    }
                ]
            }
        )
        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0].source_kind, "h5ad_obs")
        self.assertTrue(str(specs[0].h5ad_path).endswith("dixit_2016_raw__control_context.h5ad"))

    def test_resolve_single_perturbation_status_prefers_annotation(self) -> None:
        obs = pd.DataFrame(
            {
                "is_control": [False, True, False],
                "is_single_perturbation": [True, False, False],
            }
        )
        mask, status, evidence = resolve_single_perturbation_status(
            obs,
            allow_degraded_unverified=False,
        )
        self.assertEqual(status, "verified_single_perturbation")
        self.assertEqual(evidence, "is_single_perturbation")
        self.assertEqual(mask.tolist(), [True, True, False])

    def test_resolve_single_perturbation_status_fails_without_evidence(self) -> None:
        obs = pd.DataFrame({"is_control": [False, True]})
        with self.assertRaisesRegex(ValueError, "formal 模式要求显式单扰动证据"):
            resolve_single_perturbation_status(obs, allow_degraded_unverified=False)

    def test_edistance_pairwise_cap_is_configurable(self) -> None:
        self.assertEqual(resolve_edistance_pairwise_max_points({}), 5000)
        self.assertIsNone(resolve_edistance_pairwise_max_points({"edistance_pairwise_max_points": None}))
        values = np.arange(20, dtype=float).reshape(10, 2)
        capped = mean_pairwise_distance(values, max_points=4)
        exact = mean_pairwise_distance(values, max_points=None)
        self.assertNotEqual(capped, exact)


class Stage2TruthBridgeAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge_hcc38 = pd.DataFrame(
            {
                "cell_line": ["HCC38"] * 6,
                "target_gene": ["A", "B", "C", "D", "E", "F"],
                "real_shift_L2": [1, 2, 3, 4, 5, 6],
                "real_shift_mean_abs": [2, 3, 4, 5, 6, 7],
                "real_Edistance": [3, 4, 5, 6, 7, 8],
                "real_DEG_burden": [10, 20, 30, 40, 50, 60],
                "depmap_gene_effect": [-1, -2, -3, -4, -5, -6],
                "depmap_gene_dependency": [2, 3, 4, 5, 6, 7],
            }
        )
        self.bridge_hcc1143 = pd.DataFrame(
            {
                "cell_line": ["HCC1143"] * 6,
                "target_gene": ["A", "B", "C", "D", "E", "F"],
                "real_shift_L2": [1.2, 1.8, 3.1, 3.9, 5.2, 5.8],
                "real_shift_mean_abs": [1.9, 2.8, 4.2, 4.8, 6.1, 6.9],
                "real_Edistance": [2.9, 4.1, 5.2, 6.1, 6.8, 8.2],
                "real_DEG_burden": [11, 18, 29, 42, 49, 63],
                "depmap_gene_effect": [-1.1, -1.9, -3.2, -3.8, -5.1, -5.9],
                "depmap_gene_dependency": [2.1, 2.9, 4.1, 4.7, 6.2, 6.8],
            }
        )

    def test_summarize_correlations_reports_aligned_sign(self) -> None:
        summary = summarize_correlations(self.bridge_hcc38)
        effect_row = summary.loc[
            (summary["truth_metric"].eq("real_shift_L2"))
            & (summary["depmap_endpoint"].eq("depmap_gene_effect"))
        ].iloc[0]
        dependency_row = summary.loc[
            (summary["truth_metric"].eq("real_shift_L2"))
            & (summary["depmap_endpoint"].eq("depmap_gene_dependency"))
        ].iloc[0]
        self.assertLess(effect_row["spearman_rho_raw"], 0.0)
        self.assertGreater(effect_row["spearman_rho_aligned"], 0.0)
        self.assertGreater(dependency_row["spearman_rho_raw"], 0.0)
        self.assertGreater(dependency_row["spearman_rho_aligned"], 0.0)

    def test_summarize_group_comparisons_uses_aligned_effect_direction(self) -> None:
        summary = summarize_group_comparisons(
            self.bridge_hcc38,
            config={
                "group_comparison": {
                    "quantile_low": 1 / 3,
                    "quantile_high": 2 / 3,
                    "min_group_size": 1,
                }
            },
        )
        row = summary.loc[
            (summary["truth_metric"].eq("real_shift_L2"))
            & (summary["depmap_endpoint"].eq("depmap_gene_effect"))
        ].iloc[0]
        dependency_row = summary.loc[
            (summary["truth_metric"].eq("real_shift_L2"))
            & (summary["depmap_endpoint"].eq("depmap_gene_dependency"))
        ].iloc[0]
        self.assertGreater(row["aligned_effect_direction"], 0.0)
        self.assertGreater(dependency_row["aligned_effect_direction"], 0.0)

    def test_build_cross_cell_line_outputs_uses_shared_targets(self) -> None:
        shared, summary = build_cross_cell_line_outputs([self.bridge_hcc38, self.bridge_hcc1143])
        self.assertEqual(shared["target_gene"].nunique(), 6)
        self.assertNotIn("cell_line_pair", shared.columns)
        effect_row = summary.loc[summary["variable"].eq("depmap_gene_effect")].iloc[0]
        self.assertEqual(effect_row["n_shared_targets"], 6)
        self.assertGreater(effect_row["spearman_rho"], 0.0)


if __name__ == "__main__":
    unittest.main()
