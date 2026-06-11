#!/usr/bin/env python3
"""Audit local availability and basic h5ad structure for candidate datasets."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = Path("configs/dataset_acquisition_registry_v1.json")


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def bool_count(series: Any) -> int:
    values = series.astype(str).str.lower()
    return int(values.isin(["true", "1", "yes", "control"]).sum())


def audit_h5ad(entry: dict[str, Any]) -> dict[str, str]:
    path = resolve_path(entry["path"])
    row = {
        "context": str(entry["context"]),
        "path": str(path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path),
        "exists": str(path.exists()).lower(),
        "n_cells": "",
        "n_genes": "",
        "label_column": str(entry.get("label_column", "")),
        "control_column": str(entry.get("control_column", "")),
        "n_perturbation_labels": "",
        "n_gene_targets": "",
        "n_control_labels": "",
        "top_labels": "",
        "status": "missing",
    }
    if not path.exists():
        return row
    try:
        import anndata as ad
    except ImportError:
        row["status"] = "anndata_missing"
        return row

    try:
        adata = ad.read_h5ad(path, backed="r")
        obs = adata.obs
        row["n_cells"] = str(int(adata.n_obs))
        row["n_genes"] = str(int(adata.n_vars))
        label_col = str(entry.get("label_column", ""))
        control_col = str(entry.get("control_column", ""))
        # Prefer precise label_stats from registry if available; fall back to auto-count
        label_stats = entry.get("label_stats", {})
        if label_stats:
            row["n_perturbation_labels"] = str(label_stats.get("n_perturbation_labels", ""))
            row["n_gene_targets"] = str(label_stats.get("n_gene_targets", ""))
            row["n_control_labels"] = str(label_stats.get("n_control_labels", ""))

        if label_col and label_col in obs.columns:
            labels = obs[label_col].astype(str)
            if not label_stats:
                # Auto-count fallback when precise stats are not pre-registered
                non_control = labels[
                    ~labels.str.lower().isin(["control", "non-targeting", "non_targeting", "ntc", "nan"])
                ]
                row["n_perturbation_labels"] = str(int(labels.nunique()))
                row["n_gene_targets"] = str(int(non_control.nunique()))
            row["top_labels"] = ";".join(labels.value_counts().head(10).index.astype(str))
        if control_col and control_col in obs.columns:
            if not label_stats:
                row["n_control_labels"] = str(bool_count(obs[control_col]))
        row["status"] = "ok"
        adata.file.close()
    except Exception as exc:
        row["status"] = f"error:{type(exc).__name__}:{exc}"
    return row


def build_rows(config: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    path_rows: list[dict[str, str]] = []
    h5ad_rows: list[dict[str, str]] = []
    for dataset in config["datasets"]:
        for local_path in dataset.get("local_paths", []):
            path = resolve_path(local_path)
            path_rows.append(
                {
                    "dataset_id": str(dataset["dataset_id"]),
                    "display_name": str(dataset["display_name"]),
                    "priority": str(dataset["priority"]),
                    "role": str(dataset["role"]),
                    "official_accession": str(dataset["official_accession"]),
                    "readout_day": str(dataset["readout_day"]),
                    "local_path": str(path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path),
                    "exists": str(path.exists()).lower(),
                    "kind": "dir" if path.is_dir() else ("file" if path.is_file() else "missing"),
                    "bytes": str(path.stat().st_size) if path.is_file() else "",
                }
            )
        for h5ad_entry in dataset.get("h5ad_audit", []):
            row = audit_h5ad(h5ad_entry)
            row.update(
                {
                    "dataset_id": str(dataset["dataset_id"]),
                    "display_name": str(dataset["display_name"]),
                    "priority": str(dataset["priority"]),
                    "role": str(dataset["role"]),
                    "official_accession": str(dataset["official_accession"]),
                    "readout_day": str(dataset["readout_day"]),
                }
            )
            h5ad_rows.append(row)
    return path_rows, h5ad_rows


def write_tsv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit local candidate dataset inventory.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Dataset acquisition config JSON")
    args = parser.parse_args()

    config = load_config(resolve_path(args.config))
    outdir = resolve_path(config["outdir"])
    path_rows, h5ad_rows = build_rows(config)
    write_tsv(path_rows, outdir / "local_path_inventory.tsv")
    write_tsv(h5ad_rows, resolve_path(config["local_inventory_path"]))
    print(f"wrote {outdir / 'local_path_inventory.tsv'}\t{len(path_rows)} rows")
    print(f"wrote {resolve_path(config['local_inventory_path'])}\t{len(h5ad_rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
