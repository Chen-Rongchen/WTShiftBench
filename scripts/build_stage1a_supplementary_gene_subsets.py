"""
Stage 1A Supplementary Gene Subsets Builder.

用于构建 literature-aligned supplementary evaluation 所需的 gene subsets。

Gene ranking 规则：
- 在每个 dataset 内，使用 control condition 的 pseudobulk 表达
- 按 mean expression descending 排序
- 从当前 formal evaluable genes 中取前 N 个

输出：
- data/frozen/stage1a_supplementary_gene_subsets/<dataset_id>/top{500,1000,2000}_control_high_expr_genes.txt
- data/frozen/stage1a_supplementary_gene_subsets/<dataset_id>/summary.tsv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

from scripts.stage1a.benchmark_invariant.catalog import (
    PROJECT_ROOT,
    get_formal_dataset_contract,
    get_formal_dataset_index,
    load_stage1a_aligned_truth_registry,
)


SUBSET_SIZES = [500, 1000, 2000]
SUBSET_NAME_PREFIX = "top{size}_control_high_expr"

OUTPUT_ROOT = PROJECT_ROOT / "data/frozen/stage1a_supplementary_gene_subsets"


def mean_expression(matrix) -> np.ndarray:
    """Compute mean expression across cells (axis=0)."""
    if getattr(matrix, "shape", None) is not None and matrix.shape[0] == 0:
        raise ValueError("收到空细胞集合，无法计算 pseudobulk。")
    if sparse.issparse(matrix):
        values = np.asarray(matrix.mean(axis=0)).ravel()
    else:
        values = np.asarray(matrix.mean(axis=0)).ravel()
    return values.astype(np.float64, copy=False)


def load_frozen_evaluable_genes(dataset_id: str) -> list[str]:
    """Load current formal evaluable genes from frozen truth."""
    registry = load_stage1a_aligned_truth_registry()
    entry = next(e for e in registry if e.dataset_id == dataset_id)
    truth = pd.read_csv(entry.path, sep="\t", index_col=0)
    return list(truth.columns)


def compute_control_mean_ranking(
    adata: ad.AnnData,
    formal_evaluable_genes: list[str],
) -> list[str]:
    """Compute control mean expression and rank genes.

    Args:
        adata: Formal filtered AnnData
        formal_evaluable_genes: Current formal evaluable genes (from truth.columns)

    Returns:
        Genes ranked by control mean expression descending, filtered to formal evaluable set.
    """
    obs = adata.obs.copy()
    obs["is_control"] = obs["is_control"].astype(bool)

    if not obs["is_control"].any():
        raise ValueError("No control cells found in dataset.")

    control_mask = obs["is_control"].to_numpy()
    control_values = mean_expression(adata.X[control_mask])

    # Create DataFrame with gene names and control means
    gene_names = adata.var.index.astype(str)
    control_df = pd.DataFrame(
        {"gene": gene_names, "control_mean": control_values}
    )

    # Filter to formal evaluable genes only
    control_df = control_df.loc[control_df["gene"].isin(formal_evaluable_genes)]

    # Sort by control mean descending
    control_df = control_df.sort_values("control_mean", ascending=False)

    return control_df["gene"].tolist()


def build_dataset_subsets(dataset_id: str) -> dict[str, object]:
    """Build all supplementary gene subsets for a dataset.

    Args:
        dataset_id: Dataset identifier

    Returns:
        Dictionary with subset metadata and results
    """
    contract = get_formal_dataset_contract(dataset_id)
    formal_evaluable_genes = load_frozen_evaluable_genes(dataset_id)

    # Load formal h5ad
    adata = ad.read_h5ad(contract.path)

    # Compute control mean ranking within formal evaluable genes
    ranked_genes = compute_control_mean_ranking(adata, formal_evaluable_genes)

    n_available = len(ranked_genes)
    if n_available == 0:
        raise ValueError(f"{dataset_id}: 没有可用的 evaluable genes。")

    output_dir = OUTPUT_ROOT / dataset_id
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "dataset_id": dataset_id,
        "formal_evaluable_gene_count": len(formal_evaluable_genes),
        "control_mean_ranked_gene_count": n_available,
        "control_definition": contract.control_definition,
        "truth_space_reference": "aligned_truth_registry",
        "subsets": {},
    }

    rows = []
    for size in SUBSET_SIZES:
        subset_name = f"top{size}_control_high_expr"
        output_path = output_dir / f"{subset_name}_genes.txt"

        # Take min(size, n_available) genes
        selected_genes = ranked_genes[: min(size, n_available)]
        actual_n = len(selected_genes)

        # Write gene list
        output_path.write_text("\n".join(selected_genes) + "\n", encoding="utf-8")

        subset_info = {
            "subset_name": subset_name,
            "n_requested": size,
            "n_available": actual_n,
            "gene_rank_rule": "control_mean_expression_desc",
            "output_path": str(output_path.relative_to(PROJECT_ROOT)),
        }
        results["subsets"][subset_name] = subset_info

        rows.append({
            "dataset_id": dataset_id,
            "subset_name": subset_name,
            "n_requested": size,
            "n_available": actual_n,
            "gene_rank_rule": "control_mean_expression_desc",
            "control_definition": contract.control_definition,
            "truth_space_reference": "aligned_truth_registry",
            "output_path": str(output_path.relative_to(PROJECT_ROOT)),
        })

    # Write summary TSV
    summary_df = pd.DataFrame(rows)
    summary_path = output_dir / "summary.tsv"
    summary_df.to_csv(summary_path, sep="\t", index=False)

    results["summary_path"] = str(summary_path.relative_to(PROJECT_ROOT))

    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="构建 Stage 1A supplementary gene subsets。"
    )
    parser.add_argument(
        "--dataset-id",
        help="数据集 ID（如不指定则处理所有 formal datasets）",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.dataset_id:
        dataset_ids = [args.dataset_id]
    else:
        # Process all formal datasets
        contracts = get_formal_dataset_index()
        dataset_ids = list(contracts.keys())

    all_results = []
    for dataset_id in dataset_ids:
        print(f"\n处理数据集: {dataset_id}")
        try:
            result = build_dataset_subsets(dataset_id)
            all_results.append(result)

            for subset_name, info in result["subsets"].items():
                print(
                    f"  {subset_name}: n_requested={info['n_requested']}, "
                    f"n_available={info['n_available']}, "
                    f"output={info['output_path']}"
                )
        except Exception as e:
            print(f"  错误: {e}")
            continue

    # Write combined summary
    if all_results:
        combined_rows = []
        for r in all_results:
            for row in r["subsets"].values():
                combined_rows.append({
                    "dataset_id": r["dataset_id"],
                    **row,
                })

        combined_df = pd.DataFrame(combined_rows)
        combined_path = OUTPUT_ROOT / "combined_summary.tsv"
        combined_df.to_csv(combined_path, sep="\t", index=False)
        print(f"\n已写出: {combined_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
