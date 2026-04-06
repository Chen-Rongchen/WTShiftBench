from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT


DEFAULT_FEATURE_REGISTRY_PATH = PROJECT_ROOT / "configs/stage1a/challengers/feature_registry.json"
DEFAULT_CHALLENGER_REGISTRY_PATH = PROJECT_ROOT / "configs/stage1a/challengers/challenger_registry.json"
DEFAULT_ALL_DATASETS_EVAL_MATRIX_PATH = PROJECT_ROOT / "configs/stage1a/runs/all_datasets_eval_matrix.json"


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


@dataclass(frozen=True)
class ChallengerRegistryEntry:
    challenger_id: str
    method_family: str
    feature_dependencies: tuple[str, ...]
    train_inputs: tuple[str, ...]
    output_contract: str
    status: str
    current_scope: str
    unlock_prerequisite: str
    notes: str
    implemented: bool
    wired_to_eval: bool
    executed_on_smoke: bool
    eligible_for_next_step: bool


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload


def resolve_dataset_formal_h5ad_path(
    dataset_id: str,
    matrix_config_path: Path = DEFAULT_ALL_DATASETS_EVAL_MATRIX_PATH,
) -> Path:
    payload = load_json_mapping(matrix_config_path)
    datasets = payload.get("datasets", [])
    if not isinstance(datasets, list):
        raise ValueError(f"{matrix_config_path} 的 datasets 必须是列表。")
    for row in datasets:
        if isinstance(row, dict) and str(row.get("dataset_id", "")) == dataset_id:
            formal_h5ad_path = row.get("formal_h5ad_path")
            if not formal_h5ad_path:
                break
            return resolve_path(str(formal_h5ad_path))
    raise ValueError(f"dataset_id={dataset_id} 未在 {matrix_config_path} 中登记 formal_h5ad_path。")


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


def load_challenger_registry(path: Path = DEFAULT_CHALLENGER_REGISTRY_PATH) -> list[ChallengerRegistryEntry]:
    payload = load_json_mapping(path)
    rows = payload.get("challengers")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path} 缺少非空 challengers 列表。")
    entries: list[ChallengerRegistryEntry] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("challenger registry entry 必须是对象。")
        entries.append(
            ChallengerRegistryEntry(
                challenger_id=str(row["challenger_id"]),
                method_family=str(row["method_family"]),
                feature_dependencies=tuple(str(item) for item in row["feature_dependencies"]),
                train_inputs=tuple(str(item) for item in row["train_inputs"]),
                output_contract=str(row["output_contract"]),
                status=str(row["status"]),
                current_scope=str(row["current_scope"]),
                unlock_prerequisite=str(row["unlock_prerequisite"]),
                notes=str(row["notes"]),
                implemented=bool(row["implemented"]),
                wired_to_eval=bool(row["wired_to_eval"]),
                executed_on_smoke=bool(row["executed_on_smoke"]),
                eligible_for_next_step=bool(row["eligible_for_next_step"]),
            )
        )
    return entries


def get_challenger_entry(
    challenger_id: str,
    path: Path = DEFAULT_CHALLENGER_REGISTRY_PATH,
) -> ChallengerRegistryEntry:
    matches = [entry for entry in load_challenger_registry(path) if entry.challenger_id == challenger_id]
    if len(matches) != 1:
        raise ValueError(f"challenger_id={challenger_id} 在 registry 中不存在或不唯一。")
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
