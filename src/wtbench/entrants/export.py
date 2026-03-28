from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT
from scripts.stage1a.benchmark_invariant.prediction_eval_common import write_matrix


def format_predicted_shift(
    *,
    target_order: list[str] | tuple[str, ...],
    gene_names: list[str],
    values: Any,
) -> pd.DataFrame:
    frame = pd.DataFrame(values, index=list(target_order), columns=gene_names)
    frame.index.name = "target_gene"
    return frame


def export_predicted_shift(*, output_dir: Path, predicted_shift: pd.DataFrame) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = output_dir / "predicted_shift.tsv.gz"
    write_matrix(predicted_shift, prediction_path)
    return prediction_path


def _run_json_command(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "benchmark hook 执行失败。\n"
            f"command={' '.join(command)}\n"
            f"stdout={result.stdout}\n"
            f"stderr={result.stderr}"
        )
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


def _run_text_command(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "benchmark hook 执行失败。\n"
            f"command={' '.join(command)}\n"
            f"stdout={result.stdout}\n"
            f"stderr={result.stderr}"
        )
    return {"stdout": result.stdout, "stderr": result.stderr}


def run_benchmark_postprocess(
    *,
    dataset_id: str,
    model_id: str,
    prediction_path: Path,
    output_dir: Path,
    do_validate_contract: bool,
    do_ingest: bool,
    do_align: bool,
) -> dict[str, Any]:
    hooks: dict[str, Any] = {}
    if do_validate_contract:
        hooks["validation"] = _run_json_command(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/stage1a/benchmark_invariant/scoring/validate_prediction_contract.py"),
                "--dataset-id",
                dataset_id,
                "--model-id",
                model_id,
                "--prediction-path",
                str(prediction_path),
            ]
        )
    if do_ingest or do_align:
        aligned_dir = output_dir / "benchmark_invariant"
        hooks["ingest_alignment"] = _run_text_command(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/stage1a/benchmark_invariant/scoring/ingest_predictions.py"),
                "--dataset-id",
                dataset_id,
                "--model-id",
                model_id,
                "--prediction-path",
                str(prediction_path),
                "--prediction-space",
                "X_pseudobulk_delta",
                "--output-path",
                str(aligned_dir / "predicted_shift_aligned.tsv.gz"),
                "--summary-path",
                str(aligned_dir / "alignment_summary.json"),
                "--manifest-path",
                str(aligned_dir / "alignment_manifest.json"),
            ]
        )
    return hooks
