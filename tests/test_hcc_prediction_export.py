from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from wtbench.hcc_prediction_export import (
    RawPredictionSource,
    export_external_stage2_hcc_prediction,
)


class Stage2HccPredictionExportTests(unittest.TestCase):
    def test_export_external_prediction_aligns_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            axis_membership_path = root / "axis_membership.tsv"
            contract_path = root / "contract.json"
            raw_input_path = root / "incoming.tsv"
            raw_output_root = root / "data" / "predictions" / "stage2_hcc_raw"
            aligned_root = root / "data" / "predictions" / "stage2_hcc_aligned"
            scorer_ready_root = root / "data" / "predictions" / "stage2_hcc_scorer_ready"
            manifest_root = root / "reports" / "stage2_hcc_prediction_contract"
            validation_root = root / "reports" / "stage2_hcc_prediction_validation"

            axis_membership = pd.DataFrame(
                {
                    "target_gene": ["A", "B"],
                    "fine_axis": ["axis_backbone", "axis_shift"],
                }
            )
            axis_membership.to_csv(axis_membership_path, sep="\t", index=False)

            contract_path.write_text(
                json.dumps(
                    {
                        "required_first_column": "target_gene",
                        "prediction_space": "stage2_truth_aligned_log_shift",
                        "normalization_applied_in_export": True,
                        "log1p_applied_in_export": True,
                        "target_universe_source": "axis_membership.tsv",
                        "gene_space_source": "axis_membership.tsv",
                        "missing_target_policy": {"allow_missing_targets": False},
                        "missing_gene_policy": {"allow_missing_genes": False},
                        "required_manifest_fields": [
                            "stage",
                            "cell_line",
                            "model_id",
                            "model_version",
                            "prediction_space",
                            "normalization_applied_in_export",
                            "log1p_applied_in_export",
                            "source_kind",
                            "object_role",
                            "export_script",
                            "export_timestamp",
                            "input_prediction_path",
                            "aligned_prediction_path",
                            "scorer_ready_prediction_path",
                            "target_universe_source",
                            "gene_space_source",
                            "allow_missing_targets",
                            "allow_missing_genes",
                            "contract_pass",
                        ],
                        "output_paths": {
                            "raw_prediction_root": str(raw_output_root / "<model_id>" / "<cell_line>"),
                            "aligned_prediction_path": str(
                                aligned_root / "<model_id>" / "<cell_line>" / "predicted_shift_aligned.tsv.gz"
                            ),
                            "scorer_ready_prediction_path": str(
                                scorer_ready_root / "<model_id>" / "<cell_line>" / "predicted_shift.tsv.gz"
                            ),
                            "manifest_path": str(
                                manifest_root / "<model_id>" / "<cell_line>" / "prediction_manifest.json"
                            ),
                            "validation_summary_path": str(
                                validation_root / "<model_id>" / "<cell_line>" / "validation_summary.json"
                            ),
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            pd.DataFrame(
                {
                    "target_gene": ["B", "A", "EXTRA"],
                    "B": [2.0, 4.0, 9.0],
                    "A": [1.0, 3.0, 8.0],
                    "EXTRA": [5.0, 6.0, 7.0],
                }
            ).to_csv(raw_input_path, sep="\t", index=False)

            result = export_external_stage2_hcc_prediction(
                cell_line="HCC38",
                model_id="strongest_candidate",
                model_version="vtest",
                object_role="entrant",
                export_timestamp="2026-04-09T00:00:00+00:00",
                raw_source=RawPredictionSource(
                    prediction_path=raw_input_path,
                    source_kind="test_input",
                    export_script="tests",
                    extra_manifest_fields={"source_checkpoint": "local-test"},
                ),
                contract_path=contract_path,
                axis_membership_path=axis_membership_path,
            )

            self.assertTrue(result["contract_pass"])
            scorer_ready_path = root / result["scorer_ready_prediction_path"]
            manifest_path = root / result["manifest_path"]
            validation_path = root / result["validation_summary_path"]

            scorer_ready = pd.read_csv(scorer_ready_path, sep="\t")
            self.assertEqual(scorer_ready.columns.tolist(), ["target_gene", "A", "B"])
            self.assertEqual(scorer_ready["target_gene"].tolist(), ["A", "B"])

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["object_role"], "entrant")
            self.assertEqual(manifest["source_checkpoint"], "local-test")
            self.assertEqual(manifest["export_status"], "contract_validated")
            self.assertEqual(manifest["raw_alignment_summary"]["raw_extra_targets"], ["EXTRA"])
            self.assertEqual(manifest["raw_alignment_summary"]["raw_extra_genes"], ["EXTRA"])

            validation = json.loads(validation_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["contract_pass"])

    def test_export_external_prediction_rejects_non_target_gene_first_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            axis_membership_path = root / "axis_membership.tsv"
            contract_path = root / "contract.json"
            raw_input_path = root / "incoming.tsv"
            pd.DataFrame({"target_gene": ["A"], "fine_axis": ["axis_a"]}).to_csv(
                axis_membership_path,
                sep="\t",
                index=False,
            )
            contract_path.write_text(
                json.dumps(
                    {
                        "required_first_column": "target_gene",
                        "prediction_space": "stage2_truth_aligned_log_shift",
                        "normalization_applied_in_export": True,
                        "log1p_applied_in_export": True,
                        "target_universe_source": "axis_membership.tsv",
                        "gene_space_source": "axis_membership.tsv",
                        "missing_target_policy": {"allow_missing_targets": False},
                        "missing_gene_policy": {"allow_missing_genes": False},
                        "required_manifest_fields": [
                            "stage",
                            "cell_line",
                            "model_id",
                            "model_version",
                            "prediction_space",
                            "normalization_applied_in_export",
                            "log1p_applied_in_export",
                            "source_kind",
                            "object_role",
                            "export_script",
                            "export_timestamp",
                            "input_prediction_path",
                            "aligned_prediction_path",
                            "scorer_ready_prediction_path",
                            "target_universe_source",
                            "gene_space_source",
                            "allow_missing_targets",
                            "allow_missing_genes",
                            "contract_pass",
                        ],
                        "output_paths": {
                            "raw_prediction_root": str(root / "raw" / "<model_id>" / "<cell_line>"),
                            "aligned_prediction_path": str(root / "aligned" / "<model_id>" / "<cell_line>" / "x.tsv.gz"),
                            "scorer_ready_prediction_path": str(root / "ready" / "<model_id>" / "<cell_line>" / "x.tsv.gz"),
                            "manifest_path": str(root / "manifest" / "<model_id>" / "<cell_line>" / "manifest.json"),
                            "validation_summary_path": str(root / "validation" / "<model_id>" / "<cell_line>" / "summary.json"),
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            pd.DataFrame({"gene_name": ["A"], "A": [1.0]}).to_csv(raw_input_path, sep="\t", index=False)

            with self.assertRaisesRegex(ValueError, "首列必须是 target_gene"):
                export_external_stage2_hcc_prediction(
                    cell_line="HCC38",
                    model_id="bad_input",
                    model_version="vtest",
                    object_role="entrant",
                    export_timestamp="2026-04-09T00:00:00+00:00",
                    raw_source=RawPredictionSource(
                        prediction_path=raw_input_path,
                        source_kind="test_input",
                        export_script="tests",
                    ),
                    contract_path=contract_path,
                    axis_membership_path=axis_membership_path,
                )


if __name__ == "__main__":
    unittest.main()
