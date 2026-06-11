from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from umap import UMAP


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "reports/manuscript_extended_data_v1/edfig1_dataset_familiarization/materialized"

DATASETS = {
    "Replogle K562 essential": {
        "path": ROOT / "data/processed/replogle_k562_essential/essential_processed.h5ad",
        "label_col": "perturbation",
        "control": "control",
        "total_col": "ncounts",
        "min_cells": 20,
        "max_cells_per_profile": 20,
        "materialize_expression": False,
    },
    "Replogle K562 GWPS": {
        "path": ROOT / "data/processed/replogle_gwps_k562/replogle_2022_k562_gwps_processed.h5ad",
        "label_col": "perturbation",
        "control": "control",
        "total_col": "ncounts",
        "min_cells": 20,
        "max_cells_per_profile": 20,
        "bridge": ROOT / "data/processed/truth_driven_bridge_replogle_k562_gwps_day8/combined_target_level_bridge_table.tsv.gz",
        "materialize_expression": True,
    },
    "HepG2 day 7": {
        "path": ROOT / "data/raw/gse264667/series/GSE264667_hepg2_raw_singlecell_01.h5ad",
        "label_col": "gene",
        "control": "non-targeting",
        "total_col": "UMI_count",
        "min_cells": 50,
        "max_cells_per_profile": 30,
        "bridge": ROOT / "reports/gse264667_endpoint_extension/gse264667_hepg2_day7/target_level_bridge_table.tsv.gz",
        "materialize_expression": True,
    },
    "Jurkat day 7": {
        "path": ROOT / "data/raw/gse264667/series/GSE264667_jurkat_raw_singlecell_01.h5ad",
        "label_col": "gene",
        "control": "non-targeting",
        "total_col": "UMI_count",
        "min_cells": 50,
        "max_cells_per_profile": 30,
        "bridge": ROOT / "reports/gse264667_endpoint_extension/gse264667_jurkat_day7/target_level_bridge_table.tsv.gz",
        "materialize_expression": True,
    },
}


def dense(value) -> np.ndarray:
    if sparse.issparse(value):
        return value.toarray()
    return np.asarray(value)


def gene_names(adata: ad.AnnData) -> np.ndarray:
    if "gene_name" in adata.var.columns:
        return adata.var["gene_name"].astype(str).to_numpy()
    return adata.var_names.astype(str).to_numpy()


def select_feature_indices(adata: ad.AnnData, n_features: int) -> np.ndarray:
    if "fano" in adata.var.columns:
        score = pd.to_numeric(adata.var["fano"], errors="coerce").fillna(-np.inf).to_numpy()
    elif "std" in adata.var.columns:
        score = pd.to_numeric(adata.var["std"], errors="coerce").fillna(-np.inf).to_numpy()
    else:
        score = np.arange(adata.n_vars, dtype=float)
    width = min(n_features, adata.n_vars)
    # Backed HDF5 matrices are much faster for a contiguous column block than
    # for hundreds of scattered column indices. Choose the contiguous block
    # with the highest aggregate variability score.
    finite = np.where(np.isfinite(score), score, 0.0)
    rolling = np.convolve(finite, np.ones(width, dtype=float), mode="valid")
    start = int(np.argmax(rolling))
    return np.arange(start, start + width, dtype=int)


def sampled_rows_by_group(
    labels: np.ndarray,
    groups: list[str],
    *,
    control: str,
    max_cells_per_profile: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    selected_rows: list[np.ndarray] = []
    selected_codes: list[np.ndarray] = []
    for code, group in enumerate(groups):
        idx = np.flatnonzero(labels == group)
        budget = 200 if group == control else max_cells_per_profile
        if len(idx) > budget:
            idx = np.sort(rng.choice(idx, size=budget, replace=False))
        selected_rows.append(idx)
        selected_codes.append(np.full(len(idx), code, dtype=np.int32))
    rows = np.concatenate(selected_rows)
    codes = np.concatenate(selected_codes)
    order = np.argsort(rows)
    return rows[order], codes[order]


def normalize_selected(x: np.ndarray, totals: np.ndarray) -> np.ndarray:
    x = x.astype(np.float32, copy=False)
    totals = np.asarray(totals, dtype=np.float32)
    totals = np.where(totals > 0, totals, 1.0)
    return np.log1p(x / totals[:, None] * 10000.0)


def materialize_umap(
    context: str,
    spec: dict[str, object],
    *,
    n_features: int,
    chunk_size: int,
    seed: int,
) -> pd.DataFrame:
    adata = ad.read_h5ad(spec["path"], backed="r")
    try:
        labels = adata.obs[str(spec["label_col"])].astype(str).to_numpy()
        counts = pd.Series(labels).value_counts()
        control = str(spec["control"])
        targets = sorted(
            label
            for label, count in counts.items()
            if label != control and int(count) >= int(spec["min_cells"])
        )
        groups = [control] + targets
        rows, codes = sampled_rows_by_group(
            labels,
            groups,
            control=control,
            max_cells_per_profile=int(spec["max_cells_per_profile"]),
            seed=seed,
        )
        feature_idx = select_feature_indices(adata, n_features)
        totals_all = pd.to_numeric(adata.obs[str(spec["total_col"])], errors="coerce").fillna(0).to_numpy(np.float32)
        sums = np.zeros((len(groups), len(feature_idx)), dtype=np.float64)
        group_counts = np.zeros(len(groups), dtype=np.int64)

        cursor = 0
        for start in range(0, adata.n_obs, chunk_size):
            stop = min(start + chunk_size, adata.n_obs)
            end_cursor = int(np.searchsorted(rows, stop, side="left"))
            if end_cursor <= cursor:
                continue
            local_rows = rows[cursor:end_cursor] - start
            local_codes = codes[cursor:end_cursor]
            block = dense(adata.X[start:stop, feature_idx])
            values = normalize_selected(block[local_rows], totals_all[rows[cursor:end_cursor]])
            for code in np.unique(local_codes):
                mask = local_codes == code
                sums[code] += values[mask].sum(axis=0, dtype=np.float64)
                group_counts[code] += int(mask.sum())
            cursor = end_cursor

        profiles = sums / np.maximum(group_counts[:, None], 1)
        scaled = StandardScaler().fit_transform(profiles)
        n_components = min(30, scaled.shape[0] - 1, scaled.shape[1])
        latent = PCA(n_components=n_components, random_state=seed).fit_transform(scaled)
        n_neighbors = min(30, max(5, int(np.sqrt(len(groups)))))
        coords = UMAP(
            n_components=2,
            n_neighbors=n_neighbors,
            min_dist=0.25,
            metric="euclidean",
            random_state=seed,
            n_jobs=1,
        ).fit_transform(latent)
        return pd.DataFrame(
            {
                "context": context,
                "profile": ["control" if x == control else x for x in groups],
                "umap1": coords[:, 0],
                "umap2": coords[:, 1],
                "is_control": [x == control for x in groups],
                "n_cells_profile": group_counts,
                "n_features_umap": len(feature_idx),
                "umap_method": "target-level sampled pseudobulk; log1p CPM; PCA; UMAP",
            }
        )
    finally:
        adata.file.close()


def materialize_expression_arrows(
    context: str,
    spec: dict[str, object],
    *,
    chunk_size: int,
) -> pd.DataFrame:
    adata = ad.read_h5ad(spec["path"], backed="r")
    try:
        labels = adata.obs[str(spec["label_col"])].astype(str).to_numpy()
        control = str(spec["control"])
        totals = pd.to_numeric(adata.obs[str(spec["total_col"])], errors="coerce").fillna(0).to_numpy(np.float32)
        names = gene_names(adata)
        gene_to_col: dict[str, int] = {}
        for i, name in enumerate(names):
            gene_to_col.setdefault(str(name), i)

        label_counts = pd.Series(labels).value_counts()
        targets = sorted(
            target
            for target, count in label_counts.items()
            if target != control
            and int(count) >= int(spec["min_cells"])
            and target in gene_to_col
        )
        target_to_code = {target: i for i, target in enumerate(targets)}
        target_cols = np.asarray([gene_to_col[target] for target in targets], dtype=np.int64)
        target_sums = np.zeros(len(targets), dtype=np.float64)
        target_counts = np.zeros(len(targets), dtype=np.int64)
        control_sums = np.zeros(adata.n_vars, dtype=np.float64)
        n_control = 0

        for start in range(0, adata.n_obs, chunk_size):
            stop = min(start + chunk_size, adata.n_obs)
            chunk_labels = labels[start:stop]
            block = adata.X[start:stop]
            if not sparse.issparse(block):
                block = sparse.csr_matrix(np.asarray(block))
            else:
                block = block.tocsr()
            denom = np.where(totals[start:stop] > 0, totals[start:stop], 1.0)
            normalized = block.multiply((10000.0 / denom)[:, None]).tocsr()
            normalized.data = np.log1p(normalized.data)

            control_mask = chunk_labels == control
            if np.any(control_mask):
                control_sums += np.asarray(normalized[control_mask].sum(axis=0)).ravel()
                n_control += int(control_mask.sum())

            pert_rows: list[int] = []
            pert_cols: list[int] = []
            pert_codes: list[int] = []
            for row, label in enumerate(chunk_labels):
                code = target_to_code.get(label)
                if code is not None:
                    pert_rows.append(row)
                    pert_cols.append(int(target_cols[code]))
                    pert_codes.append(code)
            if pert_rows:
                values = np.asarray(normalized[np.asarray(pert_rows), np.asarray(pert_cols)]).reshape(-1)
                codes = np.asarray(pert_codes, dtype=np.int64)
                target_sums += np.bincount(codes, weights=values, minlength=len(targets))
                target_counts += np.bincount(codes, minlength=len(targets))

        control_means = control_sums / max(n_control, 1)
        perturbed_means = target_sums / np.maximum(target_counts, 1)
        expression_control = control_means[target_cols]
        return pd.DataFrame(
            {
                "context": context,
                "target": targets,
                "expression_control": expression_control,
                "expression_perturbed": perturbed_means,
                "delta": perturbed_means - expression_control,
                "n_cells_control": n_control,
                "n_cells_target": target_counts,
                "normalization": "log1p(raw_counts_per_cell_total * 10000)",
            }
        )
    finally:
        adata.file.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-features", type=int, default=256)
    parser.add_argument("--chunk-size", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--force-expression", action="store_true")
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for offset, (context, spec) in enumerate(DATASETS.items()):
        slug = context.lower().replace(" ", "_")
        umap_path = OUT_DIR / f"{slug}_umap.tsv"
        expression_path = OUT_DIR / f"{slug}_target_expression.tsv"
        if umap_path.exists():
            print(f"[ED1] reusing UMAP: {context}", flush=True)
        else:
            print(f"[ED1] materializing UMAP: {context}", flush=True)
            materialize_umap(
                context,
                spec,
                n_features=args.n_features,
                chunk_size=args.chunk_size,
                seed=args.seed + offset,
            ).to_csv(umap_path, sep="\t", index=False)
        if bool(spec.get("materialize_expression", True)):
            if expression_path.exists() and not args.force_expression:
                print(f"[ED1] reusing target expression: {context}", flush=True)
            else:
                print(f"[ED1] materializing target expression: {context}", flush=True)
                materialize_expression_arrows(
                    context,
                    spec,
                    chunk_size=args.chunk_size,
                ).to_csv(expression_path, sep="\t", index=False)

    pd.concat(
        [pd.read_csv(OUT_DIR / f"{context.lower().replace(' ', '_')}_umap.tsv", sep="\t") for context in DATASETS],
        ignore_index=True,
    ).to_csv(
        OUT_DIR / "edfig1_missing_umap_source_data.tsv", sep="\t", index=False
    )
    pd.concat(
        [
            pd.read_csv(OUT_DIR / f"{context.lower().replace(' ', '_')}_target_expression.tsv", sep="\t")
            for context, spec in DATASETS.items()
            if bool(spec.get("materialize_expression", True))
        ],
        ignore_index=True,
    ).to_csv(
        OUT_DIR / "edfig1_missing_target_expression_source_data.tsv", sep="\t", index=False
    )


if __name__ == "__main__":
    main()
