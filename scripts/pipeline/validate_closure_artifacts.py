#!/usr/bin/env python3
"""Validate structure and fixed boundaries of key Stage2 closure artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from wtbench.truth_bridge import resolve_path


def load_validation_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "artifacts" not in payload:
        raise ValueError("Validation configuration lacks artifacts.")
    return payload


def ensure_required_columns(frame: pd.DataFrame, required_columns: list[str], *, path: Path) -> None:
    missing = sorted(set(required_columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{path} missing columns: {missing}")


def ensure_allowed_values(frame: pd.DataFrame, allowed_values: dict[str, list[str]], *, path: Path) -> None:
    for column, allowed in allowed_values.items():
        if column not in frame.columns:
            raise ValueError(f"{path} missing enumeration-validation column: {column}")
        observed = {str(value) for value in frame[column].dropna().unique()}
        unexpected = sorted(observed - set(allowed))
        if unexpected:
            raise ValueError(f"{path} column {column} contains disallowed values: {unexpected}")


def ensure_required_rows(frame: pd.DataFrame, required_rows: list[dict[str, dict[str, str]]], *, path: Path) -> None:
    for row in required_rows:
        match = row.get("match", {})
        if not match:
            continue
        mask = pd.Series([True] * len(frame))
        for column, expected in match.items():
            if column not in frame.columns:
                raise ValueError(f"{path} missing required_rows column: {column}")
            mask = mask & frame[column].astype("string").eq(str(expected))
        if not bool(mask.any()):
            raise ValueError(f"{path} missing required row: {match}")


def ensure_required_substrings(text: str, required_substrings: list[str], *, path: Path) -> None:
    missing = [value for value in required_substrings if value not in text]
    if missing:
        raise ValueError(f"{path} missing required phrases: {missing}")


def ensure_forbidden_substrings(text: str, forbidden_substrings: list[str], *, path: Path) -> None:
    observed = [value for value in forbidden_substrings if value in text]
    if observed:
        raise ValueError(f"{path} contains prohibited phrases: {observed}")


def validate_one_artifact(artifact: dict[str, Any]) -> Path:
    path = resolve_path(str(artifact["path"]))
    if not path.exists():
        raise FileNotFoundError(f"Missing validation artifact: {path}")

    required_substrings = artifact.get("required_substrings")
    forbidden_substrings = artifact.get("forbidden_substrings")
    if required_substrings or forbidden_substrings:
        text = path.read_text(encoding="utf-8")
        ensure_required_substrings(text, list(required_substrings or []), path=path)
        ensure_forbidden_substrings(text, list(forbidden_substrings or []), path=path)
        return path

    frame = pd.read_csv(path, sep="\t")
    ensure_required_columns(frame, list(artifact.get("required_columns", [])), path=path)
    ensure_allowed_values(frame, dict(artifact.get("allowed_values", {})), path=path)
    ensure_required_rows(frame, list(artifact.get("required_rows", [])), path=path)
    return path


def validate_artifacts_from_config(config_path: Path) -> list[Path]:
    cfg = load_validation_config(config_path)
    validated: list[Path] = []
    for artifact in cfg["artifacts"]:
        validated.append(validate_one_artifact(artifact))
    return validated


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate key Stage2 closure artifacts.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/closure_artifact_validation_v1.json"),
        help="Closure-artifact validation JSON configuration.",
    )
    args = parser.parse_args()

    validated = validate_artifacts_from_config(args.config)
    print("Stage2 key closure-artifact validation passed.")
    for path in validated:
        print(f"- {path}")


if __name__ == "__main__":
    main()
