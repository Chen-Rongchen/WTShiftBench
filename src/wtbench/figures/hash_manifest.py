from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path: Path, *, root: Path | None = None) -> dict[str, str]:
    p = path.resolve()
    if root is None:
        display = str(p)
    else:
        try:
            display = str(p.relative_to(root.resolve()))
        except ValueError:
            display = str(p)
    return {"path": display, "sha256": sha256_file(p)}


def git_metadata(root: Path) -> dict[str, Any]:
    def run(args: list[str]) -> str:
        proc = subprocess.run(args, cwd=root, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            return proc.stderr.strip()
        return proc.stdout.strip()

    return {
        "commit": run(["git", "rev-parse", "HEAD"]),
        "status_short": run(["git", "status", "--short"]),
    }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def write_panel_manifest(
    *,
    manifest_path: Path,
    repo_root: Path,
    panel_id: str,
    panel_title: str,
    script_path: Path,
    input_paths: list[Path],
    source_data_path: Path,
    output_paths: list[Path],
    claim_boundary: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "panel_id": panel_id,
        "panel_title": panel_title,
        "generated_at_utc": utc_now_iso(),
        "script": str(script_path.resolve().relative_to(repo_root.resolve())),
        "inputs": [file_record(p, root=repo_root) for p in input_paths],
        "source_data": file_record(source_data_path, root=repo_root),
        "outputs": [file_record(p, root=repo_root) for p in output_paths],
        "claim_boundary": claim_boundary,
        "git": git_metadata(repo_root),
    }
    if extra:
        payload["extra"] = extra
    write_json(manifest_path, payload)
    return payload


def write_figure_manifest(
    *,
    manifest_path: Path,
    repo_root: Path,
    figure_id: str,
    figure_title: str,
    script_path: Path,
    panel_manifest_paths: list[Path],
    combined_source_data_path: Path,
    output_paths: list[Path],
    input_paths: list[Path],
    claim_boundary: str,
) -> dict[str, Any]:
    payload = {
        "figure_id": figure_id,
        "figure_title": figure_title,
        "generated_at_utc": utc_now_iso(),
        "script": str(script_path.resolve().relative_to(repo_root.resolve())),
        "inputs": [file_record(p, root=repo_root) for p in input_paths],
        "panel_manifests": [file_record(p, root=repo_root) for p in panel_manifest_paths],
        "combined_source_data": file_record(combined_source_data_path, root=repo_root),
        "outputs": [file_record(p, root=repo_root) for p in output_paths],
        "claim_boundary": claim_boundary,
        "git": git_metadata(repo_root),
    }
    write_json(manifest_path, payload)
    return payload

