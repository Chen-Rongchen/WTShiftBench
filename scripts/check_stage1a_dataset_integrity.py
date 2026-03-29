from __future__ import annotations

import json
from pathlib import Path

import anndata as ad
import pandas as pd

try:
    from scripts.stage1a.benchmark_invariant.catalog import (
        FORMAL_SOURCE_DATASETS,
        PROJECT_ROOT,
        load_formal_dataset_contracts,
    )
except ModuleNotFoundError:
    from stage1a.benchmark_invariant.catalog import (  # type: ignore
        FORMAL_SOURCE_DATASETS,
        PROJECT_ROOT,
        load_formal_dataset_contracts,
    )


RAW_AUDIT_DIR = PROJECT_ROOT / "data/raw/stage1a"
FORMAL_FILTERED_DIR = PROJECT_ROOT / "data/processed/stage1a/formal_filtered"
OUTPUT_PATH = PROJECT_ROOT / "reports/stage1a/dataset_integrity/stage1a_dataset_integrity.tsv"


def sample_x_read(path: Path) -> tuple[bool, str]:
    try:
        adata = ad.read_h5ad(path, backed="r")
        try:
            sample_rows = sorted({0, max(0, adata.n_obs // 2), max(0, adata.n_obs - 1)})
            for row_idx in sample_rows:
                _ = adata.X[row_idx]
            return True, "ok"
        finally:
            adata.file.close()
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def read_audit_status(dataset_id: str) -> tuple[str, str]:
    path = RAW_AUDIT_DIR / f"{dataset_id}.audit_summary.json"
    if not path.exists():
        return "missing", "缺少 raw audit summary"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return str(payload.get("final_status", "missing")), str(payload.get("final_note", ""))


def read_formal_filter_report(dataset_id: str) -> tuple[bool, dict[str, object]]:
    path = FORMAL_FILTERED_DIR / f"{dataset_id}.filter_report.json"
    if not path.exists():
        return False, {}
    return True, json.loads(path.read_text(encoding="utf-8"))


def build_rows() -> list[dict[str, object]]:
    contract_index = {
        contract.dataset_id: contract
        for contract in load_formal_dataset_contracts(include_auxiliary=True)
    }
    rows: list[dict[str, object]] = []

    for dataset in FORMAL_SOURCE_DATASETS:
        contract = contract_index[dataset.name]
        raw_exists = dataset.path.exists()
        raw_x_ok, raw_x_note = sample_x_read(dataset.path) if raw_exists else (False, "raw 文件不存在")

        audit_status, audit_note = read_audit_status(dataset.name)

        formal_exists = contract.path.exists()
        formal_x_ok, formal_x_note = (
            sample_x_read(contract.path) if formal_exists else (False, "formal 文件不存在")
        )
        report_exists, report = read_formal_filter_report(dataset.name)

        formal_kept_cells = int(report.get("kept_cells", 0)) if report_exists else 0
        formal_target_count = int(report.get("unique_target_count", 0)) if report_exists else 0
        formal_status = str(report.get("final_status", "")) if report_exists else "missing"

        rows.append(
            {
                "dataset_id": dataset.name,
                "role": dataset.role,
                "default_in_mainline": dataset.default_in_mainline,
                "registry_status": contract.status,
                "raw_file_exists": raw_exists,
                "raw_x_readable": raw_x_ok,
                "raw_x_note": raw_x_note,
                "raw_audit_status": audit_status,
                "raw_audit_note": audit_note,
                "formal_file_exists": formal_exists,
                "formal_x_readable": formal_x_ok,
                "formal_x_note": formal_x_note,
                "formal_filter_report_exists": report_exists,
                "formal_filter_status": formal_status,
                "registry_n_cells_formal": int(contract.n_cells_formal),
                "report_kept_cells": formal_kept_cells,
                "registry_n_unique_targets": int(contract.n_unique_targets),
                "report_unique_target_count": formal_target_count,
                "formal_cells_match_registry": (
                    formal_exists and report_exists and int(contract.n_cells_formal) == formal_kept_cells
                ),
                "formal_targets_match_registry": (
                    report_exists and int(contract.n_unique_targets) == formal_target_count
                ),
            }
        )
    return rows


def main() -> None:
    rows = build_rows()
    frame = pd.DataFrame(rows).sort_values(["default_in_mainline", "dataset_id"], ascending=[False, True])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUT_PATH, sep="\t", index=False)
    print(f"已写出: {OUTPUT_PATH}")
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
