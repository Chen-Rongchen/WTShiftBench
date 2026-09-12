from __future__ import annotations

import unittest

import numpy as np

from wtbench.revision_m5_audit import cosine_kernel_loo, ridge_press_loo
from wtbench.revision_metric_validity import (
    _safe_spearman,
    mean_off_diagonal_cosine,
)


class M5AuditTests(unittest.TestCase):
    def test_ridge_press_matches_explicit_leave_one_out(self) -> None:
        rng = np.random.default_rng(12)
        features = rng.normal(size=(9, 3))
        responses = rng.normal(size=(9, 4))
        observed = ridge_press_loo(features, responses, ridge_lambda=0.3)
        expected = []
        for heldout in range(len(features)):
            keep = np.arange(len(features)) != heldout
            design = np.column_stack([np.ones(keep.sum()), features[keep]])
            penalty = np.eye(design.shape[1]) * 0.3
            penalty[0, 0] = 0.0
            beta = np.linalg.pinv(design.T @ design + penalty) @ design.T @ responses[keep]
            expected.append(np.r_[1.0, features[heldout]] @ beta)
        self.assertTrue(np.allclose(observed, np.vstack(expected), atol=1e-10))

    def test_kernel_never_uses_heldout_response(self) -> None:
        features = np.eye(4)
        responses = np.eye(4)
        observed = cosine_kernel_loo(features, responses, top_k=1, temperature=1.0)
        self.assertTrue(np.all(np.diag(observed) == 0.0))
        self.assertTrue(np.allclose(observed.sum(axis=1), 1.0))

    def test_fast_off_diagonal_mean_matches_explicit_matrix(self) -> None:
        rng = np.random.default_rng(4)
        values = rng.normal(size=(13, 7))
        observed, n = mean_off_diagonal_cosine(values, tolerance=1e-12)
        unit = values / np.linalg.norm(values, axis=1, keepdims=True)
        rows, cols = np.tril_indices(len(values), k=-1)
        expected = (unit @ unit.T)[rows, cols].mean()
        self.assertEqual(n, len(values))
        self.assertAlmostEqual(observed, float(expected), places=14)

    def test_roundoff_only_score_is_non_estimable(self) -> None:
        score = np.ones(20) + np.linspace(-1e-15, 1e-15, 20)
        endpoint = np.arange(20, dtype=float)
        rho, status, n = _safe_spearman(score, endpoint)
        self.assertTrue(np.isnan(rho))
        self.assertEqual(status, "non_estimable_constant_score")
        self.assertEqual(n, 20)


if __name__ == "__main__":
    unittest.main()
