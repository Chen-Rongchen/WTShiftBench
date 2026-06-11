import numpy as np
import pandas as pd

from wtbench.model_endpoint_recovery import _output_geometry_diagnostics


def test_identical_target_outputs_are_maximally_homogeneous() -> None:
    matrix = pd.DataFrame(
        np.tile(np.array([1.0, -2.0, 0.5]), (4, 1)),
        index=["A", "B", "C", "D"],
    )

    result = _output_geometry_diagnostics(matrix)

    assert np.isclose(result["predicted_target_similarity_mean"], 1.0)
    assert np.isclose(result["leading_singular_energy_share"], 1.0)
    assert np.isclose(result["normalized_inverse_effective_rank"], 1.0)


def test_orthogonal_target_outputs_are_not_mean_similarity_homogeneous() -> None:
    matrix = pd.DataFrame(np.eye(4), index=["A", "B", "C", "D"])

    result = _output_geometry_diagnostics(matrix)

    assert np.isclose(result["predicted_target_similarity_mean"], 0.0)
    assert np.isclose(result["leading_singular_energy_share"], 0.25)
    assert np.isclose(result["normalized_inverse_effective_rank"], 0.0)
