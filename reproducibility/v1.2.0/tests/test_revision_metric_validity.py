from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from wtbench.revision_metric_validity import (
    build_random_direction_prediction,
    build_target_metrics,
    mean_off_diagonal_cosine,
    rank_auc,
    target_identity_mantel,
    validate_contract_matrix,
)


def _matrix(values: list[list[float]]) -> pd.DataFrame:
    return pd.DataFrame(values, index=[f"T{i}" for i in range(len(values))], columns=["G1", "G2", "G3"])


def _endpoint(n: int) -> pd.DataFrame:
    categories = ["endpoint_anchor", "low_information"] + ["middle"] * (n - 2)
    return pd.DataFrame(
        {
            "target_gene": [f"T{i}" for i in range(n)],
            "context_role": ["test"] * n,
            "depmap_gene_dependency": np.linspace(0.1, 0.9, n),
            "noise_corrected_shift": np.linspace(-0.1, 0.2, n),
            "endpoint_category": categories,
            "corrected_shift_percentile": np.linspace(0.1, 1.0, n),
            "corrected_dependency_percentile": np.linspace(0.1, 1.0, n),
        }
    )


def test_signed_cosine_separates_oracle_and_negated_while_absolute_projection_does_not() -> None:
    observed = _matrix([[1.0, 2.0, -1.0], [2.0, -1.0, 0.5], [-1.0, 0.5, 2.0]])
    endpoint = _endpoint(len(observed))
    oracle = build_target_metrics(
        prediction=observed,
        observed=observed,
        endpoint=endpoint,
        cell_line="X",
        entrant_id="oracle",
        reference_type="observed_shift_oracle",
        reference_seed=None,
        tolerance=1e-12,
    )
    negated = build_target_metrics(
        prediction=-observed,
        observed=observed,
        endpoint=endpoint,
        cell_line="X",
        entrant_id="negated",
        reference_type="negated_oracle",
        reference_seed=None,
        tolerance=1e-12,
    )
    assert np.allclose(oracle["signed_cosine"], 1.0)
    assert np.allclose(negated["signed_cosine"], -1.0)
    assert np.allclose(
        oracle["absolute_response_axis_projection"],
        negated["absolute_response_axis_projection"],
    )


def test_zero_prediction_direction_is_non_estimable_not_zero() -> None:
    observed = _matrix([[1.0, 2.0, -1.0], [2.0, -1.0, 0.5], [-1.0, 0.5, 2.0]])
    zero = observed * 0.0
    result = build_target_metrics(
        prediction=zero,
        observed=observed,
        endpoint=_endpoint(len(observed)),
        cell_line="X",
        entrant_id="zero",
        reference_type="zero",
        reference_seed=None,
        tolerance=1e-12,
    )
    assert result["signed_cosine"].isna().all()
    assert result["absolute_response_axis_projection"].isna().all()
    assert set(result["direction_status"]) == {"non_estimable_zero_norm"}


def test_random_direction_preserves_each_target_l2_norm() -> None:
    observed = _matrix([[1.0, 2.0, -1.0], [2.0, -1.0, 0.5], [-1.0, 0.5, 2.0]])
    random = build_random_direction_prediction(observed, seed=123)
    assert np.allclose(
        np.linalg.norm(random.to_numpy(), axis=1),
        np.linalg.norm(observed.to_numpy(), axis=1),
    )


def test_shared_identical_rows_have_max_uncentered_homogenization() -> None:
    values = np.repeat(np.array([[1.0, -2.0, 0.5]]), repeats=5, axis=0)
    estimate, n = mean_off_diagonal_cosine(values, tolerance=1e-12)
    assert n == 5
    assert estimate == pytest.approx(1.0)


def test_target_identity_uses_target_label_permutation() -> None:
    observed = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.9, 0.1],
            [0.0, 0.0, 1.0],
        ]
    )
    result = target_identity_mantel(
        observed,
        observed,
        tolerance=1e-12,
        permutations=199,
        seed=11,
    )
    assert result["rho"] == pytest.approx(1.0)
    assert result["n_pairs"] == 10
    assert result["pvalue"] <= 0.05


def test_rank_auc_counts_ties_as_half() -> None:
    score = np.array([2.0, 1.0, 1.0, 0.0])
    label = np.array([True, True, False, False])
    assert rank_auc(score, label) == pytest.approx(0.875)


def test_contract_validation_fails_on_missing_gene() -> None:
    frame = pd.DataFrame({"target_gene": ["T0"], "G1": [1.0]})
    with pytest.raises(ValueError, match="missing"):
        validate_contract_matrix(
            frame,
            target_order=["T0"],
            gene_order=["G1", "G2"],
            matrix_name="test",
        )
