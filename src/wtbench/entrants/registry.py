"""
DEPRECATED: 此模块已被弃用。

当前 Stage 1A smoke 使用 scripts/smoke_stage1a_*.py 直连 entrant class，
不依赖此模块。详细原因见 configs/entrants/registry.yaml 的 deprecated 说明。

此模块仍保留以避免破坏已有引用，但不可用于实际 orchestration。
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

from wtbench.entrants.base import ensure_mapping, load_yaml_mapping, resolve_project_path

# 定义在此处而非从 base.py 导入，以避免 ImportError
DEFAULT_ENTRANT_REGISTRY_PATH = Path(__file__).resolve().parents[3] / "configs" / "entrants" / "registry.yaml"


@dataclass(frozen=True)
class EntrantRegistryEntry:
    entrant_id: str
    entrant_version: str
    model_family: str
    adapter_class: str
    default_config_path: Path
    status: str
    notes: str


def _coerce_entry(payload: dict[str, Any]) -> EntrantRegistryEntry:
    required = [
        "entrant_id",
        "entrant_version",
        "model_family",
        "adapter_class",
        "default_config_path",
        "status",
        "notes",
    ]
    missing = [field for field in required if field not in payload]
    if missing:
        raise ValueError(f"registry entry 缺少字段: {missing}")
    default_config_path = resolve_project_path(payload["default_config_path"])
    if default_config_path is None:
        raise ValueError("default_config_path 不能为空。")
    return EntrantRegistryEntry(
        entrant_id=str(payload["entrant_id"]),
        entrant_version=str(payload["entrant_version"]),
        model_family=str(payload["model_family"]),
        adapter_class=str(payload["adapter_class"]),
        default_config_path=default_config_path,
        status=str(payload["status"]),
        notes=str(payload["notes"]),
    )


def load_entrant_registry(
    registry_path: Path = DEFAULT_ENTRANT_REGISTRY_PATH,
) -> list[EntrantRegistryEntry]:
    warnings.warn(
        "wtbench.entrants.registry 模块已弃用，请使用 scripts/smoke_stage1a_*.py 直连 entrant class。",
        DeprecationWarning,
        stacklevel=2,
    )
    payload = load_yaml_mapping(registry_path)
    if payload.get("deprecated"):
        raise RuntimeError(
            f"registry.yaml 已标记为 deprecated: {payload.get('deprecated_reason', '见 configs/entrants/registry.yaml')}"
        )
    entries = payload.get("entrants", [])
    if not isinstance(entries, list):
        raise ValueError("configs/entrants/registry.yaml 的 entrants 必须是列表。")
    return [_coerce_entry(ensure_mapping(entry, "registry entry")) for entry in entries]


def get_registry_entry(
    entrant_id: str,
    registry_path: Path = DEFAULT_ENTRANT_REGISTRY_PATH,
) -> EntrantRegistryEntry:
    warnings.warn(
        "wtbench.entrants.registry 模块已弃用，请使用 scripts/smoke_stage1a_*.py 直连 entrant class。",
        DeprecationWarning,
        stacklevel=2,
    )
    matches = [entry for entry in load_entrant_registry(registry_path) if entry.entrant_id == entrant_id]
    if not matches:
        raise KeyError(f"registry 中不存在 entrant_id={entrant_id}")
    if len(matches) != 1:
        raise ValueError(f"registry 中 entrant_id={entrant_id} 不唯一。")
    return matches[0]


def instantiate_adapter(adapter_class: str):
    warnings.warn(
        "wtbench.entrants.registry 模块已弃用，请使用 scripts/smoke_stage1a_*.py 直连 entrant class。",
        DeprecationWarning,
        stacklevel=2,
    )
    module_name, class_name = adapter_class.rsplit(".", 1)
    module = import_module(module_name)
    adapter_cls = getattr(module, class_name)
    return adapter_cls()
