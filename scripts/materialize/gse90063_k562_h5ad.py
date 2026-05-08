#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
from scipy.io import mmread
from scipy import sparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_config(config_path: Path) -> dict[str, Any]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    required = {"dataset_label", "input", "mapping", "output"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"配置缺少字段: {missing}")
    return payload


def read_last_column(path: Path) -> pd.Series:
    frame = pd.read_csv(path)
    if frame.shape[1] == 0:
        raise ValueError(f"{path} 没有可读取列。")
    values = frame.iloc[:, -1].astype(str).str.strip()
    return values


def parse_target_gene(guide: str, control_prefix: str) -> tuple[str, bool]:
    text = str(guide).strip()
    upper = text.upper()

    if "INTERGENIC" in upper:
        match = re.search(r"INTERGENIC([A-Z0-9_-]+)", upper)
        suffix = (match.group(1) if match else "unknown").strip("_").lower()
        return f"{control_prefix}{suffix}", True

    match = re.search(r"(?:^P_)?SG([^_]+)_", upper)
    if match:
        return match.group(1), False

    return "", False


def load_guide_assignments(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, header=None, names=["guide", "cell_list"])
    frame["guide"] = frame["guide"].astype(str).str.strip()
    frame["cell_list"] = frame["cell_list"].astype(str)
    return frame


def build_cell_to_guides(assignments: pd.DataFrame) -> dict[str, set[str]]:
    cell_to_guides: dict[str, set[str]] = defaultdict(set)
    for row in assignments.itertuples(index=False):
        guide = str(row.guide).strip()
        if not guide:
            continue
        for token in str(row.cell_list).split(","):
            cell = token.strip()
            if not cell:
                continue
            cell_to_guides[cell].add(guide)
    return cell_to_guides


def main() -> None:
    parser = argparse.ArgumentParser(description="物化 GSE90063 K562 TF pool 为 Stage 2 可用 h5ad。")
    parser.add_argument("--config", required=True, help="配置文件路径")
    args = parser.parse_args()

    config = load_config(resolve_path(args.config))
    dataset_label = str(config["dataset_label"])
    control_prefix = str(config["mapping"]["control_target_prefix"])

    input_cfg = config["input"]
    matrix_path = resolve_path(str(input_cfg["matrix_path"]))
    gene_names_path = resolve_path(str(input_cfg["gene_names_path"]))
    cell_barcodes_path = resolve_path(str(input_cfg["cell_barcodes_path"]))
    guide_assignment_path = resolve_path(str(input_cfg["guide_assignment_path"]))

    output_cfg = config["output"]
    h5ad_path = resolve_path(str(output_cfg["h5ad_path"]))
    summary_json_path = resolve_path(str(output_cfg["summary_json_path"]))
    summary_tsv_path = resolve_path(str(output_cfg["summary_tsv_path"]))
    h5ad_path.parent.mkdir(parents=True, exist_ok=True)
    summary_json_path.parent.mkdir(parents=True, exist_ok=True)
    summary_tsv_path.parent.mkdir(parents=True, exist_ok=True)

    matrix_genes_by_cells = mmread(matrix_path).tocsr()
    gene_names = read_last_column(gene_names_path)
    cell_barcodes = read_last_column(cell_barcodes_path)
    assignments = load_guide_assignments(guide_assignment_path)
    cell_to_guides = build_cell_to_guides(assignments)

    if matrix_genes_by_cells.shape != (len(gene_names), len(cell_barcodes)):
        raise ValueError(
            "矩阵维度与基因/细胞注释不一致："
            f"{matrix_genes_by_cells.shape} vs ({len(gene_names)}, {len(cell_barcodes)})"
        )

    obs_records: list[dict[str, Any]] = []
    matrix_cells_set = set(cell_barcodes.tolist())
    for barcode in cell_barcodes.tolist():
        guides = sorted(cell_to_guides.get(barcode, set()))
        n_guides = len(guides)
        is_single = n_guides == 1
        sg = guides[0] if is_single else ""
        target_gene, is_control = parse_target_gene(sg, control_prefix=control_prefix) if is_single else ("", False)
        keep = bool(target_gene) and (is_control or is_single)
        obs_records.append(
            {
                "cell_barcode": barcode,
                "dataset_id": dataset_label,
                "cell_id": barcode,
                "condition": "Control",
                "MOI": "1",
                "sgRNA": sg,
                "perturbation_label_raw": sg,
                "perturbation_label_clean": "control" if is_control else target_gene,
                "target_gene": target_gene,
                "target_gene_id": target_gene,
                "is_control": bool(is_control),
                "is_single_perturbation": bool(is_single),
                "num_features": int(n_guides),
                "formal_like_keep": bool(keep),
            }
        )

    obs = pd.DataFrame(obs_records)
    keep_mask = obs["formal_like_keep"].to_numpy(dtype=bool)
    kept_obs = obs.loc[keep_mask].copy()
    kept_obs = kept_obs.set_index("cell_barcode")

    matrix_cells_by_genes = matrix_genes_by_cells.transpose().tocsr()
    kept_matrix: sparse.csr_matrix = matrix_cells_by_genes[keep_mask, :].tocsr()

    var = pd.DataFrame(index=gene_names.astype(str).tolist())
    adata = ad.AnnData(X=kept_matrix, obs=kept_obs, var=var)
    adata.var_names_make_unique()
    adata.write_h5ad(h5ad_path)

    assignment_cells_set = set(cell_to_guides.keys())
    guides_upper = assignments["guide"].astype(str).str.upper()
    summary = {
        "dataset_label": dataset_label,
        "matrix_path": str(matrix_path),
        "gene_names_path": str(gene_names_path),
        "cell_barcodes_path": str(cell_barcodes_path),
        "guide_assignment_path": str(guide_assignment_path),
        "matrix_genes": int(matrix_genes_by_cells.shape[0]),
        "matrix_cells": int(matrix_genes_by_cells.shape[1]),
        "guide_rows": int(len(assignments)),
        "unique_assignment_cells": int(len(assignment_cells_set)),
        "assignment_cells_not_in_matrix": int(len(assignment_cells_set - matrix_cells_set)),
        "matrix_cells_with_single_guide": int((obs["num_features"] == 1).sum()),
        "matrix_cells_with_multi_guide": int((obs["num_features"] > 1).sum()),
        "matrix_cells_unassigned": int((obs["num_features"] == 0).sum()),
        "controls_in_kept_cells": int(kept_obs["is_control"].sum()),
        "targets_in_kept_cells": int((~kept_obs["is_control"]).sum()),
        "kept_cells": int(len(kept_obs)),
        "kept_genes": int(adata.n_vars),
        "intergenic_guides": int(guides_upper.str.contains("INTERGENIC").sum()),
        "sg_guides": int(guides_upper.str.contains("SG").sum()),
        "output_h5ad": str(h5ad_path),
    }
    summary_json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary_tsv = pd.DataFrame(
        [{"metric": key, "value": value} for key, value in summary.items()]
    )
    summary_tsv.to_csv(summary_tsv_path, sep="\t", index=False)

    print(f"[ok] materialized h5ad -> {h5ad_path}")
    print(f"[ok] summary json    -> {summary_json_path}")
    print(f"[ok] summary tsv     -> {summary_tsv_path}")


if __name__ == "__main__":
    main()
