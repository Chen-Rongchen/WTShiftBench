"""
Lane 评估脚本：从 raw predictions 重新对齐并切 lane 评估。

用于测试：评估模型在 top500/top1000/top2000/full_gene lanes 上的表现。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr

from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    PROJECT_ROOT,
    read_matrix,
    load_main_aligned_truth_entry,
    json_dump,
)


def compute_metrics(pred_df: pd.DataFrame, truth_df: pd.DataFrame, topk: int = 50) -> dict:
    """计算相关性指标。"""
    common_targets = list(set(pred_df.index) & set(truth_df.index))
    common_genes = list(set(pred_df.columns) & set(truth_df.columns))

    pred_aligned = pred_df.loc[common_targets, common_genes]
    truth_aligned = truth_df.loc[common_targets, common_genes]

    pearson_scores = []
    spearman_scores = []
    cosine_scores = []
    rmse_scores = []
    topk_jaccard_scores = []
    topk_up_jaccard_scores = []
    topk_down_jaccard_scores = []

    for target in common_targets:
        pred_row = pred_aligned.loc[target].values.astype(np.float64)
        truth_row = truth_aligned.loc[target].values.astype(np.float64)

        if np.std(pred_row) > 1e-10 and np.std(truth_row) > 1e-10:
            p_corr, _ = pearsonr(pred_row, truth_row)
            s_corr, _ = spearmanr(pred_row, truth_row)
            cosine = np.dot(pred_row, truth_row) / (np.linalg.norm(pred_row) * np.linalg.norm(truth_row))
            rmse = np.sqrt(np.mean((pred_row - truth_row) ** 2))

            pearson_scores.append(p_corr)
            spearman_scores.append(s_corr)
            cosine_scores.append(cosine)
            rmse_scores.append(rmse)

        # Top-k Jaccard (基于 magnitude 的 top genes)
        pred_topk_idx = np.argsort(np.abs(pred_row))[-topk:]
        truth_topk_idx = np.argsort(np.abs(truth_row))[-topk:]
        pred_topk_genes = set(pred_topk_idx)
        truth_topk_genes = set(truth_topk_idx)
        intersection = len(pred_topk_genes & truth_topk_genes)
        union = len(pred_topk_genes | truth_topk_genes)
        jaccard = intersection / union if union > 0 else 0.0
        topk_jaccard_scores.append(jaccard)

        # Top-k Up Jaccard (上调基因 - 最大值前50)
        pred_up_idx = np.argsort(pred_row)[-topk:]
        truth_up_idx = np.argsort(truth_row)[-topk:]
        pred_up_genes = set(pred_up_idx)
        truth_up_genes = set(truth_up_idx)
        up_intersection = len(pred_up_genes & truth_up_genes)
        up_union = len(pred_up_genes | truth_up_genes)
        up_jaccard = up_intersection / up_union if up_union > 0 else 0.0
        topk_up_jaccard_scores.append(up_jaccard)

        # Top-k Down Jaccard (下调基因 - 最小值前50)
        pred_down_idx = np.argsort(pred_row)[:topk]
        truth_down_idx = np.argsort(truth_row)[:topk]
        pred_down_genes = set(pred_down_idx)
        truth_down_genes = set(truth_down_idx)
        down_intersection = len(pred_down_genes & truth_down_genes)
        down_union = len(pred_down_genes | truth_down_genes)
        down_jaccard = down_intersection / down_union if down_union > 0 else 0.0
        topk_down_jaccard_scores.append(down_jaccard)

    return {
        "n_targets": len(common_targets),
        "n_genes": len(common_genes),
        "pearson_mean": float(np.mean(pearson_scores)) if pearson_scores else 0.0,
        "pearson_median": float(np.median(pearson_scores)) if pearson_scores else 0.0,
        "spearman_mean": float(np.mean(spearman_scores)) if spearman_scores else 0.0,
        "spearman_median": float(np.median(spearman_scores)) if spearman_scores else 0.0,
        "cosine_similarity_mean": float(np.mean(cosine_scores)) if cosine_scores else 0.0,
        "cosine_similarity_median": float(np.median(cosine_scores)) if cosine_scores else 0.0,
        "rmse_mean": float(np.mean(rmse_scores)) if rmse_scores else 0.0,
        "rmse_median": float(np.median(rmse_scores)) if rmse_scores else 0.0,
        "top50_jaccard_mean": float(np.mean(topk_jaccard_scores)) if topk_jaccard_scores else 0.0,
        "top50_jaccard_median": float(np.median(topk_jaccard_scores)) if topk_jaccard_scores else 0.0,
        "top50_up_jaccard_mean": float(np.mean(topk_up_jaccard_scores)) if topk_up_jaccard_scores else 0.0,
        "top50_up_jaccard_median": float(np.median(topk_up_jaccard_scores)) if topk_up_jaccard_scores else 0.0,
        "top50_down_jaccard_mean": float(np.mean(topk_down_jaccard_scores)) if topk_down_jaccard_scores else 0.0,
        "top50_down_jaccard_median": float(np.median(topk_down_jaccard_scores)) if topk_down_jaccard_scores else 0.0,
    }


def load_lane_genes(dataset_id: str, lane: str) -> list[str]:
    """加载 lane gene list。"""
    lane_file_map = {
        "top500": f"top500_control_high_expr_genes.txt",
        "top1000": f"top1000_control_high_expr_genes.txt",
        "top2000": f"top2000_control_high_expr_genes.txt",
    }
    if lane not in lane_file_map:
        raise ValueError(f"Unknown lane: {lane}")

    lane_path = PROJECT_ROOT / "data/frozen/stage1a_supplementary_gene_subsets" / dataset_id / lane_file_map[lane]
    genes = lane_path.read_text().splitlines()
    return [g.strip() for g in genes if g.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lane 评估：从 raw predictions 切 lane 评分。")
    parser.add_argument("--dataset-id", default="replogle_2022_k562_essential")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--raw-prediction-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--lanes", nargs="+", default=["full_gene", "top500", "top1000", "top2000"])
    parser.add_argument("--topk", type=int, default=50)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # 读取 raw prediction
    raw_pred = read_matrix(Path(args.raw_prediction_path))
    print(f"Raw prediction: {raw_pred.shape[0]} targets x {raw_pred.shape[1]} genes")

    # 读取 truth
    truth_entry = load_main_aligned_truth_entry(args.dataset_id)
    truth = read_matrix(truth_entry.path)
    print(f"Truth: {truth.shape[0]} targets x {truth.shape[1]} genes")

    # 对齐到共同 targets
    common_targets = list(set(raw_pred.index) & set(truth.index))
    pred_aligned = raw_pred.loc[common_targets]
    truth_aligned = truth.loc[common_targets]
    print(f"Aligned on targets: {len(common_targets)} targets")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for lane in args.lanes:
        if lane == "full_gene":
            # 使用模型能预测的全部 genes
            lane_pred = pred_aligned
            lane_truth = truth_aligned
            lane_name = "full_gene_lane"
        else:
            # 切 lane
            lane_genes = load_lane_genes(args.dataset_id, lane)
            common_genes = list(set(lane_genes) & set(pred_aligned.columns))
            lane_pred = pred_aligned[common_genes]
            lane_truth = truth_aligned[common_genes]
            lane_name = f"{lane}_lane"
            print(f"{lane_name}: {len(common_genes)} genes")

        # 计算指标
        metrics = compute_metrics(lane_pred, lane_truth, topk=args.topk)
        metrics["lane"] = lane_name
        metrics["dataset_id"] = args.dataset_id
        metrics["model_id"] = args.model_id
        results[lane] = metrics

        print(f"{lane_name}: Pearson={metrics['pearson_mean']:.4f}, RMSE={metrics['rmse_mean']:.4f}")

    # 输出结果
    output_file = output_dir / f"{args.model_id}_{args.dataset_id}_lane_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n结果已写出: {output_file}")

    # 输出 TSV summary
    rows = []
    for lane, metrics in results.items():
        rows.append({
            "model_id": args.model_id,
            "dataset_id": args.dataset_id,
            "lane": metrics["lane"],
            "n_targets": metrics["n_targets"],
            "n_genes": metrics["n_genes"],
            "pearson_mean": metrics["pearson_mean"],
            "pearson_median": metrics["pearson_median"],
            "spearman_mean": metrics["spearman_mean"],
            "spearman_median": metrics["spearman_median"],
            "cosine_similarity_mean": metrics["cosine_similarity_mean"],
            "rmse_mean": metrics["rmse_mean"],
            "top50_jaccard_mean": metrics["top50_jaccard_mean"],
            "top50_jaccard_median": metrics["top50_jaccard_median"],
            "top50_up_jaccard_mean": metrics["top50_up_jaccard_mean"],
            "top50_down_jaccard_mean": metrics["top50_down_jaccard_mean"],
        })
    df = pd.DataFrame(rows)
    tsv_file = output_dir / f"{args.model_id}_{args.dataset_id}_lane_summary.tsv"
    df.to_csv(tsv_file, sep="\t", index=False)
    print(f"TSV 已写出: {tsv_file}")


if __name__ == "__main__":
    main()
