from __future__ import annotations

import unittest

import pandas as pd

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for path in (PROJECT_ROOT, SCRIPTS_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from scripts.formal_filter_stage1a import build_standard_obs
from scripts.stage1a.dataset_semantics import (
    canonicalize_gene_symbol,
    is_adamson_control_target,
    parse_adamson_target_series,
)


class DatasetSemanticsTests(unittest.TestCase):
    def test_canonicalize_norman_legacy_symbols(self) -> None:
        self.assertEqual(canonicalize_gene_symbol("C19orf26"), "CBARP")
        self.assertEqual(canonicalize_gene_symbol("C3orf72"), "FOXL2NB")
        self.assertEqual(canonicalize_gene_symbol("KIAA1804"), "MAP3K21")

    def test_parse_adamson_target_series(self) -> None:
        parsed = parse_adamson_target_series(
            pd.Series(["ASCC3_pDS052", "63(mod)_pBA580", "*", "", pd.NA], dtype="string")
        )
        self.assertEqual(parsed.tolist(), ["ASCC3", "63(mod)", "", "", ""])

    def test_adamson_control_family(self) -> None:
        mask = is_adamson_control_target(
            pd.Series(["63(mod)", "Gal4-4(mod)", "ASCC3"], dtype="string")
        )
        self.assertEqual(mask.tolist(), [True, True, False])


class FormalFilterStandardizationTests(unittest.TestCase):
    def test_norman_standardization_applies_aliases(self) -> None:
        obs = pd.DataFrame(
            {
                "perturbation": ["control", "C19orf26", "KIAA1804"],
                "nperts": [0, 1, 1],
            },
            index=["c1", "c2", "c3"],
        )
        standardized = build_standard_obs("norman_2019", obs)
        self.assertEqual(standardized.loc["c1", "perturbation_label_clean"], "control")
        self.assertEqual(standardized.loc["c2", "target_gene"], "CBARP")
        self.assertEqual(standardized.loc["c3", "target_gene"], "MAP3K21")

    def test_adamson_standardization_uses_parsed_target_and_control_family(self) -> None:
        obs = pd.DataFrame(
            {
                "perturbation": ["63(mod)_pBA580", "ASCC3_pDS052", "*", pd.NA],
                "nperts": [2, 2, 1, 0],
            },
            index=["c1", "c2", "c3", "c4"],
        )
        standardized = build_standard_obs("adamson_2016_upr_perturb_seq", obs)
        self.assertTrue(bool(standardized.loc["c1", "is_control"]))
        self.assertTrue(bool(standardized.loc["c2", "formal_keep"]))
        self.assertFalse(bool(standardized.loc["c3", "formal_keep"]))
        self.assertEqual(standardized.loc["c2", "target_gene"], "ASCC3")


if __name__ == "__main__":
    unittest.main()
