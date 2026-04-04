"""Paper-aligned Linear Baseline with External P Embedding.

根据 Ahlmann-Eltze et al. 2025 Nature Methods 的线性模型:
    Y ≈ G W P^T + b

其中:
- Y: perturbation-level shift matrix (genes x perturbations)
- G: gene embedding from PCA of Y (n_genes, K)
- P: external perturbation embedding (n_targets, K) - 从外部来源提供
- W: linear mapping (K, K)
- b: bias = row_mean(Y_train)

此 baseline 与 linear_pca_shift_baseline 的区别在于:
- P embedding 不是从 training data 学习，而是使用外部提供的 embedding
- 适用于有预训练 embedding 的场景（如 scGPT embeddings, Geneformer embeddings）
"""

from __future__ import annotations

import json
import numpy as np
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wtbench.baselines.linear_utils import (
    build_gene_embedding_from_shift_pca,
    solve_bilinear_ridge_closed_form,
    predict_shift_from_gwp,
)


# 默认参数
DEFAULT_N_COMPONENTS = 10
DEFAULT_RIDGE_LAMBDA = 0.1


@dataclass(frozen=True)
class LinearExternalPConfig:
    n_components: int = DEFAULT_N_COMPONENTS
    ridge_lambda: float = DEFAULT_RIDGE_LAMBDA
    p_embedding_source: str = "external"  # 标记 P 来源


@dataclass(frozen=True)
class LinearExternalPResult:
    predicted_shift: pd.DataFrame
    model_params: dict[str, Any]
    target_coverage: dict[str, Any]
    provenance: dict[str, Any]


def compute_train_shifts(
    adata,
    train_targets: list[str],
    evaluable_genes: list[str],
):
    """计算训练数据的 shift matrix。

    Args:
        adata: AnnData 对象
        train_targets: 训练目标基因列表
        evaluable_genes: 可评估的基因列表（scoring space）

    Returns:
        Y_train: 形状 (n_evaluable_genes, n_train_targets) 的 shift matrix
        gene_names: 对应的基因名列表
    """
    from scipy import sparse

    obs = adata.obs.copy()
    obs["is_control"] = obs["is_control"].astype(bool)
    obs["target_gene"] = obs["target_gene"].astype("string")

    gene_names = adata.var.index.astype(str)
    gene_index = pd.Index(gene_names)
    gene_positions = gene_index.get_indexer(evaluable_genes)

    if (gene_positions < 0).any():
        missing = [evaluable_genes[i] for i, pos in enumerate(gene_positions) if pos < 0][:10]
        raise ValueError(f"缺少 evaluable gene: {missing}")

    # 计算 control baseline
    control_mask = obs["is_control"].to_numpy()
    if sparse.issparse(adata.X):
        control_values = np.asarray(adata.X[control_mask].mean(axis=0)).ravel()
    else:
        control_values = np.asarray(adata.X[control_mask].mean(axis=0)).ravel()
    control_values = control_values.astype(np.float64)

    # 计算每个 train target 的 delta
    Y_train_rows = []
    valid_train_targets = []

    for target in train_targets:
        target_mask = (
            (~obs["is_control"]).to_numpy()
            & obs["target_gene"].eq(target).to_numpy()
        )
        if not target_mask.any():
            continue

        if sparse.issparse(adata.X):
            perturbed_values = np.asarray(adata.X[target_mask].mean(axis=0)).ravel()
        else:
            perturbed_values = np.asarray(adata.X[target_mask].mean(axis=0)).ravel()
        perturbed_values = perturbed_values.astype(np.float64)
        delta = perturbed_values - control_values
        Y_train_rows.append(delta[gene_positions])
        valid_train_targets.append(target)

    if not valid_train_targets:
        raise ValueError("没有可用的训练目标。")

    Y_train = np.array(Y_train_rows, dtype=np.float64).T  # (n_genes, n_targets)

    return Y_train, valid_train_targets


def build_linear_external_p_baseline(
    adata,
    train_targets: list[str],
    test_targets: list[str],
    evaluable_genes: list[str],
    external_p_embeddings: dict[str, np.ndarray],
    n_components: int = DEFAULT_N_COMPONENTS,
    ridge_lambda: float = DEFAULT_RIDGE_LAMBDA,
) -> LinearExternalPResult:
    """构建使用外部 P embedding 的 paper-aligned linear baseline。

    Args:
        adata: AnnData 对象
        train_targets: 训练目标基因列表
        test_targets: 测试目标基因列表
        evaluable_genes: 可评估的基因列表
        external_p_embeddings: 外部提供的 target embedding 字典 {gene_name: embedding}
        n_components: PCA 分量数 K
        ridge_lambda: Ridge 正则化参数

    Returns:
        LinearExternalPResult: 包含预测结果和元数据
    """
    # Step 1: 计算训练数据的 shift matrix
    Y_train, valid_train_targets = compute_train_shifts(
        adata, train_targets, evaluable_genes
    )
    n_genes, n_train = Y_train.shape

    # Step 2: 计算 bias (行均值)
    bias = Y_train.mean(axis=1)  # (n_genes,)
    Y_centered = Y_train - bias[:, np.newaxis]  # (n_genes, n_train)

    # Step 3: 构建 gene embedding G (从 Y_train 的 PCA)
    G, explained_variance = build_gene_embedding_from_shift_pca(Y_centered, n_components)

    # Step 4: 收集有效的 training target embeddings
    P_train_rows = []
    valid_train_indices = []
    unmapped_train = []

    for idx, target in enumerate(valid_train_targets):
        if target in external_p_embeddings:
            P_train_rows.append(external_p_embeddings[target])
            valid_train_indices.append(idx)
        else:
            unmapped_train.append(target)

    if not P_train_rows:
        raise ValueError("没有可用的 training target embedding (来自 external_p_embeddings)。")

    P_train = np.array(P_train_rows, dtype=np.float64)  # (n_valid_train, K)
    valid_Y_centered = Y_centered[:, valid_train_indices]

    # Step 5: 求解 W
    W = solve_bilinear_ridge_closed_form(
        valid_Y_centered, G, P_train, ridge_lambda
    )

    # Step 6: 对 test targets 使用外部 embedding 并预测
    P_test_rows = []
    test_valid_indices = []
    test_unmapped = []

    for idx, target in enumerate(test_targets):
        if target in external_p_embeddings:
            P_test_rows.append(external_p_embeddings[target])
            test_valid_indices.append(idx)
        else:
            test_unmapped.append(target)

    if not P_test_rows:
        raise ValueError("没有可用的 test target embedding (来自 external_p_embeddings)。")

    P_test = np.array(P_test_rows, dtype=np.float64)  # (n_valid_test, K)

    # 预测
    Y_pred = predict_shift_from_gwp(G, W, P_test, bias)  # (n_test, n_genes)

    # 构建 DataFrame
    predicted_shift = pd.DataFrame(
        Y_pred,
        index=[test_targets[i] for i in test_valid_indices],
        columns=evaluable_genes,
    )
    predicted_shift.index.name = "target_gene"

    # Target coverage 统计
    coverage = {
        "n_train_targets": len(train_targets),
        "n_test_targets": len(test_targets),
        "n_valid_train": len(valid_train_indices),
        "n_valid_test": len(test_valid_indices),
        "train_coverage": len(valid_train_indices) / len(train_targets) if train_targets else 0.0,
        "test_coverage": len(test_valid_indices) / len(test_targets) if test_targets else 0.0,
        "unmapped_train_targets": unmapped_train,
        "unmapped_test_targets": test_unmapped,
    }

    # Provenance
    provenance = {
        "baseline_type": "linear_external_p_shift_baseline",
        "paper_reference": "Ahlmann-Eltze et al. 2025 Nature Methods",
        "model_formula": "Y ≈ G W P^T + b",
        "G_source": "PCA of Y_train (gene embedding)",
        "P_source": "external_p_embeddings (provided externally, not learned from training data)",
        "n_components": n_components,
        "ridge_lambda": ridge_lambda,
        "explained_variance_ratio": explained_variance.tolist(),
    }

    # Model params
    model_params = {
        "n_components": n_components,
        "ridge_lambda": ridge_lambda,
        "G_shape": list(G.shape),
        "W_shape": list(W.shape),
        "P_train_shape": list(P_train.shape),
        "P_test_shape": list(P_test.shape),
        "bias_shape": list(bias.shape),
        "Y_train_shape": list(Y_train.shape),
    }

    return LinearExternalPResult(
        predicted_shift=predicted_shift,
        model_params=model_params,
        target_coverage=coverage,
        provenance=provenance,
    )


def load_external_embeddings_from_file(embeddings_path: Path) -> dict[str, np.ndarray]:
    """从文件加载外部 embeddings。

    支持格式:
    - .npy: 直接加载 numpy array，假设形状为 (n_targets, K)
    - .tsv/.csv: 加载为 DataFrame，行索引为 target name，列为 embedding 维度

    Args:
        embeddings_path: embeddings 文件路径

    Returns:
        {target_name: embedding_array} 字典
    """
    import pandas as pd

    suffix = embeddings_path.suffix.lower()

    if suffix == ".npy":
        data = np.load(embeddings_path)
        raise NotImplementedError(
            ".npy format requires target names to be provided separately. "
            "Use .tsv or .csv format with target names as index."
        )

    elif suffix in (".tsv", ".csv"):
        df = pd.read_csv(embeddings_path, sep="\t" if suffix == ".tsv" else ",", index_col=0)
        embeddings = {}
        for target_name in df.index:
            embeddings[str(target_name)] = df.loc[target_name].values.astype(np.float64)
        return embeddings

    else:
        raise ValueError(f"不支持的 embedding 文件格式: {suffix}")


def main():
    """命令行入口。"""
    import argparse
    import anndata as ad

    parser = argparse.ArgumentParser(description="External P embedding linear baseline")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--formal-h5ad-path", required=True)
    parser.add_argument("--evaluable-genes-path", required=True)
    parser.add_argument("--external-p-embeddings-path", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--train-targets", nargs="+", default=None)
    parser.add_argument("--test-targets", nargs="+", required=True)
    parser.add_argument("--n-components", type=int, default=DEFAULT_N_COMPONENTS)
    parser.add_argument("--ridge-lambda", type=float, default=DEFAULT_RIDGE_LAMBDA)
    parser.add_argument("--metadata-path", default=None)
    args = parser.parse_args()

    # 加载数据
    adata = ad.read_h5ad(args.formal_h5ad_path)

    # 加载 evaluable genes
    evaluable_genes = [
        line.strip()
        for line in Path(args.evaluable_genes_path).read_text().splitlines()
        if line.strip()
    ]

    # 加载外部 P embeddings
    external_p_embeddings = load_external_embeddings_from_file(Path(args.external_p_embeddings_path))

    # 加载 train targets (如果未指定，从 formal filtered h5ad 中推断)
    if args.train_targets is None:
        obs = adata.obs
        obs["is_control"] = obs["is_control"].astype(bool)
        obs["target_gene"] = obs["target_gene"].astype("string")
        all_obs_targets = obs.loc[~obs["is_control"], "target_gene"].dropna().unique().tolist()
        train_targets = [t for t in all_obs_targets if t not in args.test_targets]
    else:
        train_targets = args.train_targets

    # 构建 baseline
    result = build_linear_external_p_baseline(
        adata=adata,
        train_targets=train_targets,
        test_targets=args.test_targets,
        evaluable_genes=evaluable_genes,
        external_p_embeddings=external_p_embeddings,
        n_components=args.n_components,
        ridge_lambda=args.ridge_lambda,
    )

    # 写入预测结果
    result.predicted_shift.to_csv(
        args.output_path,
        sep="\t",
        compression="gzip",
        index=True,
        index_label="target_gene",
    )

    # 写入元数据
    if args.metadata_path:
        metadata = {
            "model_params": result.model_params,
            "target_coverage": result.target_coverage,
            "provenance": result.provenance,
        }
        Path(args.metadata_path).write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2)
        )

    print(f"已写出: {args.output_path}")
    print(f"n_test_targets: {len(result.predicted_shift)}")
    print(f"n_genes: {len(result.predicted_shift.columns)}")
    print(f"test_coverage: {result.target_coverage['test_coverage']:.4f}")


if __name__ == "__main__":
    main()
