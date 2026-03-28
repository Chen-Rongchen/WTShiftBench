from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wtbench.entrants.base import load_yaml_mapping, resolve_project_path


@dataclass(frozen=True)
class CheckpointRegistryEntry:
    entrant_name: str
    checkpoint_vendor_type: str
    checkpoint_vendor_uri: str
    checkpoint_version_tag: str
    checkpoint_artifact_identity: str
    local_resolved_path: str | None
    upstream_vendor_uri: str | None
    upstream_version_tag: str | None
    status: str


def _coerce_entry(payload: dict[str, Any]) -> CheckpointRegistryEntry:
    required = [
        "entrant_name",
        "checkpoint_vendor_type",
        "checkpoint_vendor_uri",
        "checkpoint_version_tag",
        "checkpoint_artifact_identity",
        "local_resolved_path",
        "upstream_vendor_uri",
        "upstream_version_tag",
        "status",
    ]
    missing = [field for field in required if field not in payload]
    if missing:
        raise ValueError(f"checkpoint registry 条目缺少字段: {missing}")
    return CheckpointRegistryEntry(
        entrant_name=str(payload["entrant_name"]),
        checkpoint_vendor_type=str(payload["checkpoint_vendor_type"]),
        checkpoint_vendor_uri=str(payload["checkpoint_vendor_uri"]),
        checkpoint_version_tag=str(payload["checkpoint_version_tag"]),
        checkpoint_artifact_identity=str(payload["checkpoint_artifact_identity"]),
        local_resolved_path=None if payload["local_resolved_path"] is None else str(payload["local_resolved_path"]),
        upstream_vendor_uri=None if payload["upstream_vendor_uri"] is None else str(payload["upstream_vendor_uri"]),
        upstream_version_tag=None if payload["upstream_version_tag"] is None else str(payload["upstream_version_tag"]),
        status=str(payload["status"]),
    )


def load_checkpoint_registry(registry_path: Path) -> dict[str, CheckpointRegistryEntry]:
    payload = load_yaml_mapping(registry_path)
    entries = payload.get("checkpoints", {})
    if not isinstance(entries, dict):
        raise ValueError("checkpoint_registry.yaml 的 checkpoints 必须是映射。")
    return {str(key): _coerce_entry(value) for key, value in entries.items()}


def resolve_checkpoint_entry(registry_path: Path, checkpoint_key: str) -> CheckpointRegistryEntry:
    registry = load_checkpoint_registry(registry_path)
    try:
        entry = registry[checkpoint_key]
    except KeyError as exc:
        raise KeyError(f"checkpoint registry 中不存在 key={checkpoint_key}") from exc
    if entry.local_resolved_path is None:
        raise FileNotFoundError(f"checkpoint_key={checkpoint_key} 尚未确认 local_resolved_path。")
    resolved_path = resolve_project_path(entry.local_resolved_path)
    if resolved_path is None or not resolved_path.exists():
        raise FileNotFoundError(
            f"checkpoint_key={checkpoint_key} 的 local_resolved_path 不存在: {entry.local_resolved_path}"
        )
    return entry


def load_resolved_checkpoint_path(registry_path: Path, checkpoint_key: str) -> tuple[CheckpointRegistryEntry, Path]:
    entry = resolve_checkpoint_entry(registry_path, checkpoint_key)
    resolved_path = resolve_project_path(entry.local_resolved_path)
    if resolved_path is None or not resolved_path.exists():
        raise FileNotFoundError(
            f"checkpoint_key={checkpoint_key} 的 local_resolved_path 不存在: {entry.local_resolved_path}"
        )
    return entry, resolved_path


def build_checkpoint_manifest(
    *,
    registry_path: Path,
    checkpoint_key: str,
    resolved_path: Path,
    entry: CheckpointRegistryEntry,
) -> dict[str, Any]:
    return {
        "checkpoint_key": checkpoint_key,
        "registry_path": str(registry_path),
        "entrant_name": entry.entrant_name,
        "checkpoint_vendor_type": entry.checkpoint_vendor_type,
        "checkpoint_vendor_uri": entry.checkpoint_vendor_uri,
        "checkpoint_version_tag": entry.checkpoint_version_tag,
        "checkpoint_artifact_identity": entry.checkpoint_artifact_identity,
        "local_resolved_path": str(resolved_path),
        "upstream_vendor_uri": entry.upstream_vendor_uri,
        "upstream_version_tag": entry.upstream_version_tag,
        "status": entry.status,
        "path_exists": resolved_path.exists(),
        "path_is_dir": resolved_path.is_dir(),
        "path_is_file": resolved_path.is_file(),
    }
