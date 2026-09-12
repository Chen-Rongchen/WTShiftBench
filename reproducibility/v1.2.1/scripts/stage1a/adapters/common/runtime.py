from __future__ import annotations

import numpy as np


def cosine_kernel_predict(
    query_embedding: np.ndarray,
    ref_embeddings: np.ndarray,
    ref_values: np.ndarray,
    top_k: int,
) -> np.ndarray:
    # 从505ee45的同文件恢复实际四个legacy runner使用的CPU分支。
    # 历史权重是非负cosine归一化，不是后来重写的batch-softmax；
    # 零范数/全非正相似度规则保留原实现，避免改变已有预测。
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
