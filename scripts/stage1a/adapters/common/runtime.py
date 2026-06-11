from __future__ import annotations

import numpy as np


def cosine_kernel_predict(
    train_features: np.ndarray,
    train_values: np.ndarray,
    query_features: np.ndarray,
    *,
    top_k: int = 5,
    temperature: float = 1.0,
) -> np.ndarray:
    train_features = np.asarray(train_features, dtype=np.float64)
    train_values = np.asarray(train_values, dtype=np.float64)
    query_features = np.asarray(query_features, dtype=np.float64)
    train_norm = np.linalg.norm(train_features, axis=1, keepdims=True)
    query_norm = np.linalg.norm(query_features, axis=1, keepdims=True)
    train_norm[train_norm == 0.0] = 1.0
    query_norm[query_norm == 0.0] = 1.0
    similarity = (query_features / query_norm) @ (train_features / train_norm).T
    k = max(1, min(int(top_k), train_features.shape[0]))
    predictions = []
    for row in similarity:
        idx = np.argsort(row)[-k:]
        logits = row[idx] / max(float(temperature), 1e-8)
        logits = logits - logits.max()
        weights = np.exp(logits)
        weights = weights / weights.sum()
        predictions.append(weights @ train_values[idx])
    return np.vstack(predictions)
