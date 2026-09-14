"""Linear baseline utilities for paper-aligned PCA shift models.

Following the linear-model architecture in Ahlmann-Eltze et al.2025, Nature Methods:
    Y ≈ G W P^T + b

where:
- Y: perturbation-level shift matrix (genes x perturbations)
- G: gene embedding from PCA of Y (n_genes x K)
- P: perturbation embedding (n_targets x K)
- W: linear mapping matrix
- b: bias (row mean of Y_train)

Important:
- Y represents predicted_shift versus real_shift, not raw expression
- G/P come from low-rank decomposition of training data, not foundation-model embeddings
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Literal


def build_gene_embedding_from_shift_pca(
    Y_train: np.ndarray,
    n_components: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Build gene embeddings(G) from the training shift matrix.

    Args:
        Y_train: shift matrix of shape(n_genes,n_train_targets)
        n_components: number K of PCA components

    Returns:
        G: gene embeddings of shape(n_genes,K)
        explained_variance_ratio: variance fraction explained by each component
    """
    from sklearn.decomposition import PCA

    n_genes = Y_train.shape[0]
    k_eff = min(n_components, min(n_genes, Y_train.shape[1]) - 1)

    pca = PCA(n_components=k_eff, random_state=42)
    G = pca.fit_transform(Y_train.T).T  # Fit after transposing, then transpose back
    # pca.fit_transform(Y_train.T) yields(n_train_targets,K); transpose to(K,n_genes)
    # Transpose again to(n_genes,K)

    # Reimplement to ensure the required orientation
    G = pca.components_.T  # (n_components, n_genes) -> (n_genes, n_components)
    explained_variance_ratio = pca.explained_variance_ratio_

    return G, explained_variance_ratio


def build_target_embedding_from_lookup(
    target_gene_names: list[str],
    target_lookup: dict[str, np.ndarray],
) -> tuple[np.ndarray, list[int], list[str]]:
    """Build target embeddings(P) from the target lookup space.

    Args:
        target_gene_names: target gene names
        target_lookup: dictionary mapping gene names to embedding vectors

    Returns:
        P: target embeddings of shape(n_targets,K)
        mapped_indices: successfully mapped target indices
        unmapped_targets: unmapped target names
    """
    P_rows = []
    mapped_indices = []
    unmapped_targets = []

    for idx, target in enumerate(target_gene_names):
        if target in target_lookup:
            P_rows.append(target_lookup[target])
            mapped_indices.append(idx)
        else:
            unmapped_targets.append(target)

    if not P_rows:
        raise ValueError(f"No target has a representation in the lookup space.")

    P = np.array(P_rows, dtype=np.float64)
    return P, mapped_indices, unmapped_targets


def solve_bilinear_ridge_closed_form(
    Y_centered: np.ndarray,
    G: np.ndarray,
    P_train: np.ndarray,
    ridge_lambda: float,
) -> np.ndarray:
    """Solve bilinear ridge regression in closed form.

    Objective: Y_centered approximately equals G W P^T
    where Y_centered = Y_train - b (centered)

    Closed-form solution:
    W = (G^T G + λI)^(-1) G^T Y_centered P (P^T P + λI)^(-1)

    Args:
        Y_centered: centered shift matrix of shape(n_genes,n_train_targets)
        G: gene embeddings of shape(n_genes,K)
        P_train: training-target embeddings of shape(n_train_targets,K)
        ridge_lambda: ridge regularization parameter

    Returns:
        W: linear mapping matrix of shape(K,K)
    """
    n_genes, n_train = Y_centered.shape
    k = G.shape[1]

    # (G^T G + λI)
    GtG = G.T @ G
    GtG_reg = GtG + ridge_lambda * np.eye(k)

    # G^T Y_centered: (K, n_genes) @ (n_genes, n_train) = (K, n_train)
    GtY = G.T @ Y_centered

    # (P^T P + λI)
    PtP = P_train.T @ P_train
    PtP_reg = PtP + ridge_lambda * np.eye(k)

    # W = GtG_reg^(-1) @ GtY @ P_train @ PtP_reg^(-1)
    # First solve GtG_reg W = GtY, giving W_tmp = GtG_reg^(-1) @ GtY.
    # Then solve W_tmp @ PtP_reg = W_tmp @ (P_train @ PtP_reg^(-1)).
    # Equivalently: W = GtG_reg^(-1) @ GtY @ P_train @ PtP_reg^(-1).

    # Use sequential solves for numerical stability.
    W = np.linalg.solve(GtG_reg, GtY @ P_train @ np.linalg.inv(PtP_reg))

    return W


def predict_shift_from_gwp(
    G: np.ndarray,
    W: np.ndarray,
    P_test: np.ndarray,
    bias: np.ndarray,
) -> np.ndarray:
    """Predict shifts using G,W,P.

    Y_pred = G W P^T + b

    Args:
        G: gene embeddings of shape(n_genes,K)
        W: linear mapping of shape(K,K)
        P_test: test-target embeddings of shape(n_test_targets,K)
        bias: row means b of shape(n_genes,)

    Returns:
        Y_pred: predicted shift matrix of shape(n_test_targets,n_genes)
    """
    # Y = G W P^T + b
    # G @ W: (n_genes, K)
    # (G @ W) @ P_test.T: (n_genes, n_test)
    # Transpose output to(n_test,n_genes).
    Y_pred = (G @ W @ P_test.T).T + bias
    return Y_pred


def validate_target_lookup_coverage(
    train_targets: list[str],
    test_targets: list[str],
    target_lookup: dict[str, np.ndarray],
) -> dict:
    """Verify target lookup-space coverage.

    Returns:
        Dictionary containing coverage statistics
    """
    all_targets = sorted(set(train_targets) | set(test_targets))

    train_mapped = sum(1 for t in train_targets if t in target_lookup)
    test_mapped = sum(1 for t in test_targets if t in target_lookup)
    total_mapped = sum(1 for t in all_targets if t in target_lookup)

    return {
        "n_train_targets": len(train_targets),
        "n_test_targets": len(test_targets),
        "n_all_targets": len(all_targets),
        "train_coverage": train_mapped / len(train_targets) if train_targets else 0.0,
        "test_coverage": test_mapped / len(test_targets) if test_targets else 0.0,
        "overall_coverage": total_mapped / len(all_targets) if all_targets else 0.0,
        "n_train_unmapped": len(train_targets) - train_mapped,
        "n_test_unmapped": len(test_targets) - test_mapped,
        "unmapped_train_targets": [t for t in train_targets if t not in target_lookup],
        "unmapped_test_targets": [t for t in test_targets if t not in target_lookup],
    }


class TargetLookupSpace:
    """Target lookup-space manager.

    Manage target embeddings independently of the scoring space.
    """

    def __init__(
        self,
        lookup_type: Literal["training_derived", "go_spectral", "reference_perturbation_pca"],
        embedding_dim: int = 10,
    ):
        self.lookup_type = lookup_type
        self.embedding_dim = embedding_dim
        self._lookup: dict[str, np.ndarray] = {}
        self._source_info: dict = {}

    def build_from_training_shifts(
        self,
        Y_train: np.ndarray,
        train_target_names: list[str],
    ) -> None:
        """Build target embeddings from the training shift matrix.

        Use PCA on Y_train to learn low-dimensional target representations.
        """
        if self.lookup_type != "training_derived":
            raise ValueError(f"lookup_type={self.lookup_type} does not match training_derived.")

        from sklearn.decomposition import PCA

        n_train = Y_train.shape[1]
        k_eff = min(self.embedding_dim, n_train - 1)

        pca = PCA(n_components=k_eff, random_state=42)
        # Y_train:(n_genes,n_targets); each column is one target's shift.
        P_train = pca.fit_transform(Y_train.T)  # (n_targets, K)

        for i, target in enumerate(train_target_names):
            self._lookup[target] = P_train[i]

        self._source_info = {
            "type": "training_derived_pca",
            "n_components": k_eff,
            "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
            "source": "Y_train via PCA",
        }

    def get_lookup(self) -> dict[str, np.ndarray]:
        return self._lookup.copy()

    def get_source_info(self) -> dict:
        return self._source_info.copy()
