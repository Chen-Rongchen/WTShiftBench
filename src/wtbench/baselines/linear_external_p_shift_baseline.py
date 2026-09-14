"""Paper-aligned Linear Baseline with External P Embedding.

Following the linear model in Ahlmann-Eltze et al.2025, Nature Methods:
    Y ≈ G W P^T + b

where:
- Y: perturbation-level shift matrix (genes x perturbations)
- G: gene embedding from PCA of Y (n_genes, K)
- P: external perturbation embeddings(n_targets,K), provided from external sources
- W: linear mapping (K, K)
- b: bias = row_mean(Y_train)

Unlike linear_pca_shift_baseline:
- P embeddings are externally supplied, not learned from training data
- Suitable for pretrained embeddings such as scGPT or Geneformer
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


# Default parameters
DEFAULT_N_COMPONENTS = 10
DEFAULT_RIDGE_LAMBDA = 0.1


@dataclass(frozen=True)
class LinearExternalPConfig:
    n_components: int = DEFAULT_N_COMPONENTS
    ridge_lambda: float = DEFAULT_RIDGE_LAMBDA
    p_embedding_source: str = "external"  # P provenance


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
    """Compute the training-data shift matrix.

    Args:
        adata: AnnData object
        train_targets: training target gene names
        evaluable_genes: evaluable gene names(scoring space)

    Returns:
        Y_train: shift matrix of shape(n_evaluable_genes,n_train_targets)
        gene_names: corresponding gene names
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
        raise ValueError(f"Missing evaluable genes: {missing}")

    # Compute the control baseline.
    control_mask = obs["is_control"].to_numpy()
    if sparse.issparse(adata.X):
        control_values = np.asarray(adata.X[control_mask].mean(axis=0)).ravel()
    else:
        control_values = np.asarray(adata.X[control_mask].mean(axis=0)).ravel()
    control_values = control_values.astype(np.float64)

    # Compute deltas for each training target.
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
        raise ValueError("No available training targets.")

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
    """Build a paper-aligned linear baseline with external P embeddings.

    Args:
        adata: AnnData object
        train_targets: training target gene names
        test_targets: test target gene names
        evaluable_genes: evaluable gene names
        external_p_embeddings: externally provided target embeddings {gene_name:embedding}
        n_components: number K of PCA components
        ridge_lambda: ridge regularization parameter

    Returns:
        LinearExternalPResult: predictions and metadata
    """
    # Step1: Compute the training shift matrix.
    Y_train, valid_train_targets = compute_train_shifts(
        adata, train_targets, evaluable_genes
    )
    n_genes, n_train = Y_train.shape

    # Step2: Compute row-mean bias.
    bias = Y_train.mean(axis=1)  # (n_genes,)
    Y_centered = Y_train - bias[:, np.newaxis]  # (n_genes, n_train)

    # Step3: Build gene embeddings G using PCA on Y_train.
    G, explained_variance = build_gene_embedding_from_shift_pca(Y_centered, n_components)

    # Step4: Collect valid training-target embeddings.
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
        raise ValueError("No training-target embeddings available in external_p_embeddings.")

    P_train = np.array(P_train_rows, dtype=np.float64)  # (n_valid_train, K)
    valid_Y_centered = Y_centered[:, valid_train_indices]

    # Step5: Solve W.
    W = solve_bilinear_ridge_closed_form(
        valid_Y_centered, G, P_train, ridge_lambda
    )

    # Step6: Predict test targets using external embeddings.
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
        raise ValueError("No test-target embeddings available in external_p_embeddings.")

    P_test = np.array(P_test_rows, dtype=np.float64)  # (n_valid_test, K)

    # Predict.
    Y_pred = predict_shift_from_gwp(G, W, P_test, bias)  # (n_test, n_genes)

    # Build the DataFrame.
    predicted_shift = pd.DataFrame(
        Y_pred,
        index=[test_targets[i] for i in test_valid_indices],
        columns=evaluable_genes,
    )
    predicted_shift.index.name = "target_gene"

    # Target coverage statistics.
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
    """Load external embeddings from a file.

    Supported formats:
    - .npy: NumPy array assumed to have shape(n_targets,K)
    - .tsv/.csv: DataFrame indexed by target name, with embedding dimensions as columns

    Args:
        embeddings_path: path to embeddings

    Returns:
        Dictionary {target_name:embedding_array}
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
        raise ValueError(f"Unsupported embedding format: {suffix}")


def main():
    """Command-line entry point."""
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

    # Load data.
    adata = ad.read_h5ad(args.formal_h5ad_path)

    # Load evaluable genes.
    evaluable_genes = [
        line.strip()
        for line in Path(args.evaluable_genes_path).read_text().splitlines()
        if line.strip()
    ]

    # Load external P embeddings.
    external_p_embeddings = load_external_embeddings_from_file(Path(args.external_p_embeddings_path))

    # Load training targets, inferring from formal filtered H5AD if unspecified.
    if args.train_targets is None:
        obs = adata.obs
        obs["is_control"] = obs["is_control"].astype(bool)
        obs["target_gene"] = obs["target_gene"].astype("string")
        all_obs_targets = obs.loc[~obs["is_control"], "target_gene"].dropna().unique().tolist()
        train_targets = [t for t in all_obs_targets if t not in args.test_targets]
    else:
        train_targets = args.train_targets

    # Build baseline.
    result = build_linear_external_p_baseline(
        adata=adata,
        train_targets=train_targets,
        test_targets=args.test_targets,
        evaluable_genes=evaluable_genes,
        external_p_embeddings=external_p_embeddings,
        n_components=args.n_components,
        ridge_lambda=args.ridge_lambda,
    )

    # Write predictions.
    result.predicted_shift.to_csv(
        args.output_path,
        sep="\t",
        compression="gzip",
        index=True,
        index_label="target_gene",
    )

    # Write metadata.
    if args.metadata_path:
        metadata = {
            "model_params": result.model_params,
            "target_coverage": result.target_coverage,
            "provenance": result.provenance,
        }
        Path(args.metadata_path).write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2)
        )

    print(f"Written: {args.output_path}")
    print(f"n_test_targets: {len(result.predicted_shift)}")
    print(f"n_genes: {len(result.predicted_shift.columns)}")
    print(f"test_coverage: {result.target_coverage['test_coverage']:.4f}")


if __name__ == "__main__":
    main()
