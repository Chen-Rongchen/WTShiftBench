from __future__ import annotations

import numpy as np


def cosine_kernel_predict(
    query_embedding: np.ndarray,
    ref_embeddings: np.ndarray,
    ref_values: np.ndarray,
    top_k: int,
) -> np.ndarray:
    # Restore the CPU branch used by all four legacy runners from the same file at505ee45.
    # Historical weights normalize nonnegative cosine values, not the later batch-softmax rewrite.
    # Preserve original zero-norm/all-nonpositive similarity rules to avoid changing existing predictions.
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
