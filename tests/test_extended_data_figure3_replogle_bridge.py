"""Regression guards for the active Extended Data Figure 3 source table."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from scipy.stats import spearmanr


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = REPO_ROOT / "scripts/figures/build_extended_data_figure3.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_extended_data_figure3", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExternalBridgeSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_builder()
        cls.source = cls.builder.build_source(REPO_ROOT)

    def test_active_source_covers_all_external_contexts(self) -> None:
        expected_counts = {
            "K562 TF day 7": 10,
            "K562 TF day 13": 10,
            "K562 essential CRISPRi day 6": 1882,
            "K562 genome-wide CRISPRi day 8": 9261,
            "HepG2 day 7": 1000,
            "Jurkat day 7": 1687,
        }
        self.assertEqual(self.source.groupby("context").size().to_dict(), expected_counts)

    def test_replogle_bridge_statistics_are_reproducible(self) -> None:
        expected = {
            "K562 essential CRISPRi day 6": 0.4018413096087801,
            "K562 genome-wide CRISPRi day 8": 0.2516792653082492,
        }
        for context, expected_rho in expected.items():
            subset = self.source.loc[self.source["context"].eq(context)]
            rho = spearmanr(
                subset["depmap_gene_dependency"],
                subset["real_shift_mean_abs"],
            ).statistic
            self.assertAlmostEqual(float(rho), expected_rho, places=12)


if __name__ == "__main__":
    unittest.main()
