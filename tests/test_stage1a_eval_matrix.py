from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

import sys
import importlib.util

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for path in (PROJECT_ROOT, SCRIPTS_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    comparator_path,
    load_main_aligned_truth_entry,
)

if importlib.util.find_spec("torch") is not None:
    from scripts.stage1a.adapters.common.runtime import resolve_adapter_dataset_context
else:
    resolve_adapter_dataset_context = None


class EvalMatrixRuntimeTests(unittest.TestCase):
    @unittest.skipIf(resolve_adapter_dataset_context is None, "当前环境缺少 torch，跳过 adapter runtime helper 测试。")
    def test_resolve_adapter_dataset_context_accepts_nonformal_dataset_from_run_config(self) -> None:
        context = resolve_adapter_dataset_context(
            dataset_id="norman_2019_raw__single_target",
            run_config={
                "formal_h5ad_path": "data/processed/stage1a/candidate_formal_like/norman_2019_raw.h5ad",
                "cell_line": "norman_2019_raw__single_target",
            },
        )
        self.assertTrue(str(context.formal_h5ad_path).endswith("candidate_formal_like/norman_2019_raw.h5ad"))
        self.assertEqual(context.cell_line, "norman_2019_raw__single_target")

    def test_load_main_aligned_truth_entry_can_read_alternate_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "truth_registry.tsv"
            truth_path = PROJECT_ROOT / "data/frozen/stage1a_truth/tian_2019_ipsc_pseudobulk_delta_aligned.tsv.gz"
            frame = pd.DataFrame(
                [
                    {
                        "dataset_id": "toy_dataset",
                        "truth_path": str(truth_path),
                        "n_targets_expected": 1,
                        "n_targets_built": 1,
                        "n_genes": 1,
                        "control_definition": "in-dataset control baseline",
                        "freeze_status": "frozen",
                        "matrix_source": "X",
                        "log_normalization_applied_in_truth_build": False,
                        "delta_space": "X_pseudobulk_delta",
                        "evaluation_space": "main_aligned",
                        "source_truth_path": str(truth_path),
                    }
                ]
            )
            frame.to_csv(registry_path, sep="\t", index=False)
            entry = load_main_aligned_truth_entry("toy_dataset", registry_path)
            self.assertEqual(entry.dataset_id, "toy_dataset")

    def test_comparator_path_accepts_root_overrides(self) -> None:
        baseline_root = PROJECT_ROOT / "tmp" / "baseline_override"
        null_root = PROJECT_ROOT / "tmp" / "null_override"
        self.assertEqual(
            comparator_path(
                "toy_dataset",
                "mean_shift_baseline",
                baseline_root=baseline_root,
                null_root=null_root,
            ),
            baseline_root / "toy_dataset" / "mean_shift_baseline.tsv.gz",
        )
        self.assertEqual(
            comparator_path(
                "toy_dataset",
                "label_shuffle",
                baseline_root=baseline_root,
                null_root=null_root,
            ),
            null_root / "toy_dataset" / "label_shuffle.tsv.gz",
        )


if __name__ == "__main__":
    unittest.main()
