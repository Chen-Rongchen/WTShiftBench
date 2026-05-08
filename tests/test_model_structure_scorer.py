from __future__ import annotations

import unittest

import pandas as pd

from wtbench.model_structure_scorer import (
    build_axis_gene_sets,
    compute_backbone_recovery_score,
    compute_shift_excess_identification_score,
    compute_structure_vs_context_separation_score,
    project_prediction_to_axes,
    summarize_structure_scores,
)


class Stage2ModelStructureScorerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.axis_membership = pd.DataFrame(
            {
                "target_gene": ["A", "B", "C", "D"],
                "fine_axis": ["axis_backbone", "axis_backbone", "axis_shift", "axis_context"],
            }
        )
        self.truth_contract = pd.DataFrame(
            {
                "fine_axis": ["axis_backbone", "axis_shift", "axis_context"],
                "architecture_role": [
                    "canonical_backbone",
                    "shift_excess",
                    "context_deviation",
                ],
                "confidence": ["high", "moderate", "provisional"],
            }
        )
        self.prediction = pd.DataFrame(
            {
                "target_gene": ["A", "B", "C", "D"],
                "A": [4.0, 3.5, 1.0, 0.5],
                "B": [3.0, 4.5, 1.2, 0.4],
                "C": [0.5, 0.3, 6.0, 1.0],
                "D": [0.2, 0.4, 0.8, 3.0],
            }
        )

    def test_build_axis_gene_sets(self) -> None:
        axis_gene_sets = build_axis_gene_sets(self.axis_membership)
        self.assertEqual(axis_gene_sets["axis_backbone"], ["A", "B"])
        self.assertEqual(axis_gene_sets["axis_shift"], ["C"])

    def test_project_prediction_to_axes_marks_expected_axis(self) -> None:
        projected = project_prediction_to_axes(
            prediction=self.prediction,
            axis_membership=self.axis_membership,
            truth_contract=self.truth_contract,
        )
        a_expected = projected.loc[
            projected["target_gene"].eq("A") & projected["is_expected_axis"]
        ].iloc[0]
        self.assertEqual(a_expected["fine_axis"], "axis_backbone")
        self.assertAlmostEqual(a_expected["projected_mean_abs"], 3.5)
        self.assertAlmostEqual(a_expected["gene_coverage"], 1.0)

    def test_structure_scores_are_high_for_well_separated_example(self) -> None:
        projected = project_prediction_to_axes(
            prediction=self.prediction,
            axis_membership=self.axis_membership,
            truth_contract=self.truth_contract,
        )
        self.assertGreater(compute_backbone_recovery_score(projected), 0.95)
        self.assertGreater(compute_shift_excess_identification_score(projected), 0.95)
        self.assertGreater(compute_structure_vs_context_separation_score(projected), 0.70)

    def test_summarize_structure_scores_returns_three_scores(self) -> None:
        projected = project_prediction_to_axes(
            prediction=self.prediction,
            axis_membership=self.axis_membership,
            truth_contract=self.truth_contract,
        )
        summary = summarize_structure_scores(projected)
        self.assertEqual(summary["score_name"].tolist(), [
            "backbone_recovery_score",
            "shift_excess_identification_score",
            "structure_vs_context_separation_score",
        ])


if __name__ == "__main__":
    unittest.main()
