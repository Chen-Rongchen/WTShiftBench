from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.run_stage2_closure_pipeline import load_pipeline_config, validate_pipeline_outputs
from scripts.validate_stage2_closure_artifacts import validate_artifacts_from_config


class Stage2ClosurePipelineTests(unittest.TestCase):
    def test_load_pipeline_config_requires_all_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "pipeline.json"
            config_path.write_text(
                json.dumps({"materialize_covariates_config": "a.json"}),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_pipeline_config(config_path)

    def test_validate_pipeline_outputs_checks_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            materialized = root / "HCC38_covariates.tsv"
            materialized.write_text("cell_barcode\nc1\n", encoding="utf-8")

            sensitivity_root = root / "sensitivity"
            sensitivity_root.mkdir()
            for name in [
                "control_subsample_replicates.tsv",
                "control_subsample_summary.tsv",
                "control_subsample_rank_stability.tsv",
                "sensitivity_report.md",
            ]:
                (sensitivity_root / name).write_text("ok\n", encoding="utf-8")

            covariate_root = root / "covariate_balance"
            covariate_root.mkdir()
            for name in ["summary.tsv", "summary.md"]:
                (covariate_root / name).write_text("ok\n", encoding="utf-8")

            validated = validate_pipeline_outputs(
                [materialized],
                sensitivity_report_root=sensitivity_root,
                covariate_report_root=covariate_root,
            )
            self.assertIn(materialized, validated)
            self.assertIn(sensitivity_root / "sensitivity_report.md", validated)
            self.assertIn(covariate_root / "summary.tsv", validated)


class Stage2ClosureArtifactValidationTests(unittest.TestCase):
    def test_validate_artifacts_from_config_checks_tsv_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            final_claim = root / "final_claim_matrix.tsv"
            pd.DataFrame(
                [
                    {"object": "GEARS_tradeoff_diagnosis", "evidence_tier": "primary_conclusion"},
                    {"object": "PFDN5", "evidence_tier": "primary_but_qualified"},
                ]
            ).to_csv(final_claim, sep="\t", index=False)

            note = root / "boundary.md"
            note.write_text("A0 architecture form 已 confirmed\nn=10\ngated_downstream_layer\n", encoding="utf-8")

            config_path = root / "validation.json"
            config_path.write_text(
                json.dumps(
                    {
                        "artifacts": [
                            {
                                "path": str(final_claim),
                                "required_columns": ["object", "evidence_tier"],
                                "allowed_values": {
                                    "evidence_tier": [
                                        "primary_conclusion",
                                        "primary_but_qualified",
                                    ]
                                },
                                "required_rows": [
                                    {
                                        "match": {
                                            "object": "PFDN5",
                                            "evidence_tier": "primary_but_qualified",
                                        }
                                    }
                                ],
                            },
                            {
                                "path": str(note),
                                "required_substrings": [
                                    "A0 architecture form 已 confirmed",
                                    "n=10",
                                    "gated_downstream_layer",
                                ],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            validated = validate_artifacts_from_config(config_path)
            self.assertEqual(len(validated), 2)


if __name__ == "__main__":
    unittest.main()
