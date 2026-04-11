from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT


DEFAULT_FEATURE_REGISTRY_PATH = PROJECT_ROOT / "configs/stage2/feature_registry_v1.json"


@dataclass(frozen=True)
class FeatureRegistryEntry:
    feature_id: str
    feature_family: str
    source_path: Path
    entity_type: str
    coverage_on_current_smoke: float
    missing_policy: str
    is_frozen: bool
    notes: str
    heldout_coverage_floor: float | None = None
    fallback_policy: str = ""


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json_mapping(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload

def load_feature_registry(path: Path = DEFAULT_FEATURE_REGISTRY_PATH) -> list[FeatureRegistryEntry]:
    payload = load_json_mapping(path)
    rows = payload.get("features")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path} 缺少非空 features 列表。")
    entries: list[FeatureRegistryEntry] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("feature registry entry 必须是对象。")
        entries.append(
            FeatureRegistryEntry(
                feature_id=str(row["feature_id"]),
                feature_family=str(row["feature_family"]),
                source_path=resolve_path(str(row["source_path"])),
                entity_type=str(row["entity_type"]),
                coverage_on_current_smoke=float(row["coverage_on_current_smoke"]),
                missing_policy=str(row["missing_policy"]),
                is_frozen=bool(row["is_frozen"]),
                notes=str(row["notes"]),
                heldout_coverage_floor=(
                    None if row.get("heldout_coverage_floor") is None else float(row["heldout_coverage_floor"])
                ),
                fallback_policy=str(row.get("fallback_policy", "")),
            )
        )
    return entries


def get_feature_entry(feature_id: str, path: Path = DEFAULT_FEATURE_REGISTRY_PATH) -> FeatureRegistryEntry:
    matches = [entry for entry in load_feature_registry(path) if entry.feature_id == feature_id]
    if len(matches) != 1:
        raise ValueError(f"feature_id={feature_id} 在 registry 中不存在或不唯一。")
    return matches[0]


def read_feature_matrix(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep="\t")
    if frame.empty:
        raise ValueError(f"{path} 为空。")
    if frame.columns[0] != "target_gene":
        raise ValueError(f"{path} 首列必须是 target_gene。")
    frame = frame.set_index("target_gene")
    frame.index = frame.index.astype(str)
    feature_columns = [str(column) for column in frame.columns]
    frame.columns = feature_columns
    frame = frame.apply(pd.to_numeric, errors="raise")
    if frame.isna().any().any():
        raise ValueError(f"{path} 含 NaN。")
    if not np.isfinite(frame.to_numpy(dtype=np.float64, copy=False)).all():
        raise ValueError(f"{path} 含非有限数。")
    return frame


def hashed_chargram_vector(target: str, dim: int) -> list[float]:
    normalized = f"^{target.lower()}$"
    grams = [normalized[idx : idx + 3] for idx in range(max(1, len(normalized) - 2))]
    vector = [0.0] * dim
    for gram in grams:
        digest = hashlib.sha256(gram.encode("utf-8")).digest()
        position = int.from_bytes(digest[:4], byteorder="little", signed=False) % dim
        vector[position] += 1.0
    norm = sum(value * value for value in vector) ** 0.5
    if norm > 0.0:
        vector = [value / norm for value in vector]
    return vector
