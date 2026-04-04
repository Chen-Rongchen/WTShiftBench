from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from scipy import sparse

from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT
from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    load_supplementary_common_genes,
    load_main_aligned_truth_entry,
    read_matrix,
)


def load_run_config(run_config_path: str | None) -> dict[str, object]:
    if not run_config_path:
        return {}
    return yaml.safe_load(Path(run_config_path).read_text(encoding="utf-8")) or {}


def coalesce_arg(cli_value, config: dict[str, object], key: str, default=None):
    if cli_value is not None:
        return cli_value
    if key in config:
        return config[key]
    return default


def resolve_path(path_value: str | Path | None) -> Path | None:
    if path_value is None:
        return None
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def mean_expression(matrix) -> np.ndarray:
    if getattr(matrix, "shape", None) is not None and matrix.shape[0] == 0:
        raise ValueError("收到空细胞集合，无法计算 pseudobulk。")
    if sparse.issparse(matrix):
        values = np.asarray(matrix.mean(axis=0)).ravel()
    else:
        values = np.asarray(matrix.mean(axis=0)).ravel()
    return values.astype(np.float64, copy=False)


def audit_input_matrix_semantics(adata, sample_rows: int = 256, sample_cols: int = 256) -> dict[str, object]:
    sample = adata.X[: min(sample_rows, adata.n_obs), : min(sample_cols, adata.n_vars)]
    if sparse.issparse(sample):
        sample_values = sample.toarray()
    else:
        sample_values = np.asarray(sample)
    max_nonint_abs = float(np.abs(sample_values - np.round(sample_values)).max()) if sample_values.size else 0.0
    looks_like_raw_counts = bool(max_nonint_abs < 1e-8 and float(sample_values.min(initial=0.0)) >= 0.0)
    return {
        "input_matrix_source": "adata.X",
        "looks_like_log_normalized_or_transformed": not looks_like_raw_counts,
        "raw_counts_available": looks_like_raw_counts,
        "matrix_sample_max_nonint_abs": max_nonint_abs,
    }


def load_truth_target_order(dataset_id: str) -> list[str]:
    truth_entry = load_main_aligned_truth_entry(dataset_id)
    truth = read_matrix(truth_entry.path)
    return truth.index.astype(str).tolist()


def load_frozen_prediction_space(dataset_id: str) -> tuple[list[str], list[str]]:
    """返回 (heldout_targets, evaluable_genes)。

    evaluable_genes 现在是 dataset-local 的，不是跨数据集共同交集。
    根据 protocol_blueprint.md 4.3 节，Stage 1A formal main evaluation
    使用 dataset-specific evaluation space。
    """
    truth_entry = load_main_aligned_truth_entry(dataset_id)
    truth = read_matrix(truth_entry.path)
    return truth.index.astype(str).tolist(), list(truth.columns)

def compute_train_target_deltas(
    formal_adata,
    common_genes: list[str],
    heldout_targets: set[str],
):
    obs = formal_adata.obs.copy()
    obs["is_control"] = obs["is_control"].astype(bool)
    obs["target_gene"] = obs["target_gene"].astype("string")
    gene_names = formal_adata.var.index.astype(str)
    gene_index = pd.Index(gene_names)
    gene_positions = gene_index.get_indexer(common_genes)
    if (gene_positions < 0).any():
        missing = [common_genes[i] for i, pos in enumerate(gene_positions) if pos < 0][:10]
        raise ValueError(f"缺少 common gene: {missing}")

    control_mask = obs["is_control"].to_numpy()
    control_values = mean_expression(formal_adata.X[control_mask])
    train_targets = sorted(
        target
        for target in obs.loc[~obs["is_control"], "target_gene"].dropna().unique().tolist()
        if target not in heldout_targets
    )
    if not train_targets:
        raise ValueError("没有可用的非 held-out train targets。")

    delta_rows = []
    for target in train_targets:
        target_mask = (~obs["is_control"]).to_numpy() & obs["target_gene"].eq(target).to_numpy()
        perturbed_values = mean_expression(formal_adata.X[target_mask])
        delta_rows.append((perturbed_values - control_values)[gene_positions])
    return train_targets, np.asarray(delta_rows, dtype=np.float64)


def resolve_torch_device(device: str | None) -> torch.device:
    if device is None or device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    d = torch.device(device)
    if d.type == "cuda" and not torch.cuda.is_available():
        raise ValueError(f"请求 device={device}，但当前环境 CUDA 不可用。")
    return d


def cosine_kernel_predict(
    query_embedding: np.ndarray,
    ref_embeddings: np.ndarray,
    ref_values: np.ndarray,
    top_k: int,
    *,
    compute_device: torch.device | None = None,
) -> np.ndarray:
    if compute_device is not None and compute_device.type == "cuda":
        q = (
            query_embedding.to(device=compute_device, dtype=torch.float32)
            if isinstance(query_embedding, torch.Tensor)
            else torch.as_tensor(query_embedding, dtype=torch.float32, device=compute_device)
        )
        r = (
            ref_embeddings.to(device=compute_device, dtype=torch.float32)
            if isinstance(ref_embeddings, torch.Tensor)
            else torch.as_tensor(ref_embeddings, dtype=torch.float32, device=compute_device)
        )
        v = (
            ref_values.to(device=compute_device, dtype=torch.float64)
            if isinstance(ref_values, torch.Tensor)
            else torch.as_tensor(ref_values, dtype=torch.float64, device=compute_device)
        )
        qn = torch.linalg.norm(q)
        rn = torch.linalg.norm(r, dim=1)
        denom = torch.clamp(qn * rn, min=1e-12)
        sim = (r @ q) / denom
        sim = torch.nan_to_num(sim, nan=0.0)
        k = max(1, min(top_k, int(sim.shape[0])))
        top_sim, top_idx = torch.topk(sim, k)
        top_sim = torch.clamp(top_sim, min=0.0).to(dtype=torch.float64)
        if float(top_sim.sum().item()) == 0.0:
            w = torch.full((k,), 1.0 / k, dtype=torch.float64, device=compute_device)
        else:
            w = top_sim / top_sim.sum()
        return (w @ v[top_idx]).cpu().numpy()

    query_norm = np.linalg.norm(query_embedding)
    ref_norm = np.linalg.norm(ref_embeddings, axis=1)
    denom = np.maximum(query_norm * ref_norm, 1e-12)
    similarity = (ref_embeddings @ query_embedding) / denom
    similarity = np.nan_to_num(similarity, nan=0.0)
    k = max(1, min(top_k, similarity.shape[0]))
    top_idx = np.argpartition(similarity, -k)[-k:]
    top_sim = np.maximum(similarity[top_idx], 0.0)
    if float(top_sim.sum()) == 0.0:
        weights = np.full(k, 1.0 / k, dtype=np.float64)
    else:
        weights = top_sim / top_sim.sum()
    return weights @ ref_values[top_idx]
