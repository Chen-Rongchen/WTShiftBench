from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class FeatureRegistryEntry:
    feature_id: str
    feature_family: str
    source_path: Path
    entity_type: str
    coverage_on_current_smoke: float
    missing_policy: str
    is_frozen: bool


def resolve_path(path: str | Path, *, base: Path = PROJECT_ROOT) -> Path:
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved
    return base / resolved


def get_feature_entry(feature_id: str, registry_path: str | Path) -> FeatureRegistryEntry:
    registry_path = resolve_path(registry_path)
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    for raw_entry in payload.get("features", []):
        entry = dict(raw_entry)
        if str(entry.get("feature_id")) != feature_id:
            continue
        return FeatureRegistryEntry(
            feature_id=str(entry["feature_id"]),
            feature_family=str(entry.get("feature_family", "")),
            source_path=resolve_path(entry["source_path"], base=registry_path.parent.parent),
            entity_type=str(entry.get("entity_type", "")),
            coverage_on_current_smoke=float(entry.get("coverage_on_current_smoke", np.nan)),
            missing_policy=str(entry.get("missing_policy", "")),
            is_frozen=bool(entry.get("is_frozen", False)),
        )
    raise KeyError(f"feature_id not found in registry: {feature_id}")


def read_feature_matrix(path: str | Path) -> pd.DataFrame:
    path = resolve_path(path)
    frame = pd.read_csv(path, sep="\t", compression="infer")
    if frame.empty:
        raise ValueError(f"Feature matrix is empty: {path}")
    index_column = "target_gene" if "target_gene" in frame.columns else frame.columns[0]
    frame[index_column] = frame[index_column].astype(str)
    frame = frame.set_index(index_column)
    frame.index.name = "target_gene"
    frame = frame.apply(pd.to_numeric, errors="raise")
    return frame


def hashed_chargram_vector(gene_symbol: str, dim: int, *, ngram_min: int = 2, ngram_max: int = 4) -> np.ndarray:
    """Return a deterministic normalized char n-gram vector for one gene symbol."""
    if dim < 1:
        raise ValueError("dim must be positive")
    text = f"^{str(gene_symbol).upper()}$"
    vector = np.zeros(dim, dtype=np.float64)
    for ngram_size in range(ngram_min, ngram_max + 1):
        if len(text) < ngram_size:
            continue
        for start in range(0, len(text) - ngram_size + 1):
            token = text[start : start + ngram_size]
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:8], byteorder="little", signed=False) % dim
            vector[bucket] += 1.0
    norm = float(np.linalg.norm(vector))
    if norm > 0.0:
        vector /= norm
    return vector
