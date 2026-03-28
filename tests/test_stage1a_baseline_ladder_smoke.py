from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

from scripts.build_stage1a_main_aligned_baselines_nulls import compute_train_target_deltas
from scripts.stage1a.benchmark_invariant.scoring.run_baseline_ladder_smoke import (
    DEFAULT_BATCH_CONFIG,
    load_baseline_smoke_run_specs,
)


class ComputeTrainTargetDeltasTests(unittest.TestCase):
    def test_excludes_heldout_targets(self) -> None:
        adata = ad.AnnData(
            X=np.asarray(
                [
                    [1.0, 2.0],
                    [2.0, 4.0],
                    [4.0, 8.0],
                    [8.0, 16.0],
                ]
            ),
            obs=pd.DataFrame(
                {
                    "is_control": [True, False, False, False],
                    "target_gene": [pd.NA, "A", "B", "C"],
                }
            ),
            var=pd.DataFrame(index=["g1", "g2"]),
        )

        train_targets, deltas = compute_train_target_deltas(
            adata=adata,
            evaluable_genes=["g1", "g2"],
            heldout_targets={"C"},
        )

        self.assertEqual(train_targets, ["A", "B"])
        np.testing.assert_allclose(
            deltas,
            np.asarray(
                [
                    [1.0, 2.0],
                    [3.0, 6.0],
                ]
            ),
        )


class BaselineSmokeConfigTests(unittest.TestCase):
    def test_default_batch_config_covers_canonical_baselines_and_nulls(self) -> None:
        specs = load_baseline_smoke_run_specs(DEFAULT_BATCH_CONFIG)
        self.assertEqual(len(specs), 5)
        self.assertEqual(
            {spec.model_id for spec in specs},
            {
                "baseline_smoke_zero_shift_null",
                "baseline_smoke_mean_shift_baseline",
                "baseline_smoke_linear_delta_baseline_legacy",
                "baseline_smoke_label_shuffle",
                "baseline_smoke_random_pairing",
            },
        )
        self.assertEqual(
            {spec.dataset_id for spec in specs},
            {"replogle_2022_k562_essential"},
        )

    def test_rejects_non_baseline_prediction_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run_config_path = root / "bad_run.yaml"
            run_config_path.write_text(
                "\n".join(
                    [
                        "dataset_id: replogle_2022_k562_essential",
                        "model_id: baseline_smoke_bad_source",
                        "prediction_path: data/predictions/stage1a_main_aligned/bad/predicted_shift.tsv.gz",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            batch_config_path = root / "batch.yaml"
            batch_config_path.write_text(
                f"run_configs:\n  - {run_config_path}\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "prediction_path 必须位于"):
                load_baseline_smoke_run_specs(batch_config_path)


if __name__ == "__main__":
    unittest.main()
