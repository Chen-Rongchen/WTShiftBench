"""Linear baseline utilities for paper-aligned PCA shift models.

根据 Ahlmann-Eltze et al. 2025 Nature Methods 的线性模型架构:
    Y ≈ G W P^T + b

其中:
- Y: perturbation-level shift matrix (genes x perturbations)
- G: gene embedding from PCA of Y (n_genes x K)
- P: perturbation embedding (n_targets x K)
- W: linear mapping matrix
- b: bias (row mean of Y_train)

重要：
- 这里 Y 是 predicted_shift vs real_shift，不是 raw expression
- G/P 来自训练数据的低秩分解，不是 foundation model embeddings
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
    """从训练数据的 shift matrix 构建 gene embedding (G)。

    Args:
        Y_train: 形状为 (n_genes, n_train_targets) 的 shift matrix
        n_components: PCA 分量数 K

    Returns:
        G: 形状 (n_genes, K) 的 gene embedding
        explained_variance_ratio: 各分量解释的方差比例
    """
    from sklearn.decomposition import PCA

    n_genes = Y_train.shape[0]
    k_eff = min(n_components, min(n_genes, Y_train.shape[1]) - 1)

    pca = PCA(n_components=k_eff, random_state=42)
    G = pca.fit_transform(Y_train.T).T  # 转置后 fit，再转置回来
    # pca.fit_transform(Y_train.T) 给出 (n_train_targets, K)，转置为 (K, n_genes)
    # 再转置为 (n_genes, K)

    # 重新实现以确保正确性
    G = pca.components_.T  # (n_components, n_genes) -> (n_genes, n_components)
    explained_variance_ratio = pca.explained_variance_ratio_

    return G, explained_variance_ratio


def build_target_embedding_from_lookup(
    target_gene_names: list[str],
    target_lookup: dict[str, np.ndarray],
) -> tuple[np.ndarray, list[int], list[str]]:
    """从 target lookup space 构建 target embedding (P)。

    Args:
        target_gene_names: 目标基因名称列表
        target_lookup: 从基因名到 embedding 向量的字典

    Returns:
        P: 形状 (n_targets, K) 的 target embedding
        mapped_indices: 成功映射的 target 索引
        unmapped_targets: 无法映射的 target 列表
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
        raise ValueError(f"没有任何 target 在 lookup space 中找到对应表示。")

    P = np.array(P_rows, dtype=np.float64)
    return P, mapped_indices, unmapped_targets


def solve_bilinear_ridge_closed_form(
    Y_centered: np.ndarray,
    G: np.ndarray,
    P_train: np.ndarray,
    ridge_lambda: float,
) -> np.ndarray:
    """求解双线性 Ridge 回归的闭式解。

    目标: Y_centered ≈ G W P^T
    其中 Y_centered = Y_train - b (已去中心化)

    闭式解:
    W = (G^T G + λI)^(-1) G^T Y_centered P (P^T P + λI)^(-1)

    Args:
        Y_centered: 已去中心化的 shift matrix，形状 (n_genes, n_train_targets)
        G: gene embedding，形状 (n_genes, K)
        P_train: training target embedding，形状 (n_train_targets, K)
        ridge_lambda: Ridge 正则化参数

    Returns:
        W: 线性映射矩阵，形状 (K, K)
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
    # 先解 GtG_reg W = GtY，得到 W_tmp = GtG_reg^(-1) @ GtY
    # 然后解 W_tmp @ PtP_reg = W_tmp @ (P_train @ PtP_reg^(-1))
    # 或者直接: W = GtG_reg^(-1) @ GtY @ P_train @ PtP_reg^(-1)

    # 使用稳定性更高的方式：分步求解
    W = np.linalg.solve(GtG_reg, GtY @ P_train @ np.linalg.inv(PtP_reg))

    return W


def predict_shift_from_gwp(
    G: np.ndarray,
    W: np.ndarray,
    P_test: np.ndarray,
    bias: np.ndarray,
) -> np.ndarray:
    """使用 G, W, P 计算预测的 shift。

    Y_pred = G W P^T + b

    Args:
        G: gene embedding，形状 (n_genes, K)
        W: 线性映射，形状 (K, K)
        P_test: test target embedding，形状 (n_test_targets, K)
        bias: 行均值 b，形状 (n_genes,)

    Returns:
        Y_pred: 预测的 shift matrix，形状 (n_test_targets, n_genes)
    """
    # Y = G W P^T + b
    # G @ W: (n_genes, K)
    # (G @ W) @ P_test.T: (n_genes, n_test)
    # 转置使输出为 (n_test, n_genes)
    Y_pred = (G @ W @ P_test.T).T + bias
    return Y_pred


def validate_target_lookup_coverage(
    train_targets: list[str],
    test_targets: list[str],
    target_lookup: dict[str, np.ndarray],
) -> dict:
    """验证 target lookup space 的覆盖情况。

    Returns:
        包含覆盖统计的字典
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
    """Target lookup space 管理器。

    负责管理 target embedding 空间，与 scoring space 解耦。
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
        """从训练数据的 shift matrix 构建 target embedding。

        使用 PCA 从 Y_train 学习 target 的低维表示。
        """
        if self.lookup_type != "training_derived":
            raise ValueError(f"lookup_type={self.lookup_type} 与 training_derived 不匹配。")

        from sklearn.decomposition import PCA

        n_train = Y_train.shape[1]
        k_eff = min(self.embedding_dim, n_train - 1)

        pca = PCA(n_components=k_eff, random_state=42)
        # Y_train: (n_genes, n_targets)，每列是一个 target 的 shift
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
