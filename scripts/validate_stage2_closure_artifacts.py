#!/usr/bin/env python3
"""校验 Stage 2 closure 相关关键产物的结构与固定边界。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from wtbench.stage2_truth_bridge import resolve_path


def load_validation_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "artifacts" not in payload:
        raise ValueError("validation 配置缺少 artifacts。")
    return payload


def ensure_required_columns(frame: pd.DataFrame, required_columns: list[str], *, path: Path) -> None:
    missing = sorted(set(required_columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{path} 缺少列: {missing}")


def ensure_allowed_values(frame: pd.DataFrame, allowed_values: dict[str, list[str]], *, path: Path) -> None:
    for column, allowed in allowed_values.items():
        if column not in frame.columns:
            raise ValueError(f"{path} 缺少枚举校验列: {column}")
        observed = {str(value) for value in frame[column].dropna().unique()}
        unexpected = sorted(observed - set(allowed))
        if unexpected:
            raise ValueError(f"{path} 列 {column} 出现未允许值: {unexpected}")


def ensure_required_rows(frame: pd.DataFrame, required_rows: list[dict[str, dict[str, str]]], *, path: Path) -> None:
    for row in required_rows:
        match = row.get("match", {})
        if not match:
            continue
        mask = pd.Series([True] * len(frame))
        for column, expected in match.items():
            if column not in frame.columns:
                raise ValueError(f"{path} 缺少 required_rows 所需列: {column}")
            mask = mask & frame[column].astype("string").eq(str(expected))
        if not bool(mask.any()):
            raise ValueError(f"{path} 缺少要求行: {match}")


def ensure_required_substrings(text: str, required_substrings: list[str], *, path: Path) -> None:
    missing = [value for value in required_substrings if value not in text]
    if missing:
        raise ValueError(f"{path} 缺少关键短语: {missing}")


def validate_one_artifact(artifact: dict[str, Any]) -> Path:
    path = resolve_path(str(artifact["path"]))
    if not path.exists():
        raise FileNotFoundError(f"缺少校验产物: {path}")

    required_substrings = artifact.get("required_substrings")
    if required_substrings:
        text = path.read_text(encoding="utf-8")
        ensure_required_substrings(text, list(required_substrings), path=path)
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
    parser = argparse.ArgumentParser(description="校验 Stage 2 closure 相关关键产物。")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/stage2/closure_artifact_validation_v1.json"),
        help="closure artifact validation 配置 JSON。",
    )
    args = parser.parse_args()

    validated = validate_artifacts_from_config(args.config)
    print("Stage 2 closure 关键产物校验通过。")
    for path in validated:
        print(f"- {path}")


if __name__ == "__main__":
    main()
