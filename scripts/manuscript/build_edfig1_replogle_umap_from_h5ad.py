#!/usr/bin/env python3
"""Rebuild Replogle K562 essential ED Fig 1 UMAP tables from AnnData (data-driven).

Uses the same cell filtering and log1p normalization as
``truth_driven_bridge_replogle_k562_essential_day7`` (``prepare_bridge_inputs``),
then:
  - one row = mean normalized expression of all control cells (aggregate);
  - one row per eligible target = mean normalized expression of that target's cells;
  - UMAP on this (n_targets+1) × n_genes matrix (umap-learn).

Writes:
  - ``replogle_k562_essential_umap.tsv`` — columns ``target_gene``, ``umap1``, ``umap2`` (perturbations only);
  - ``replogle_k562_essential_umap_control.tsv`` — one row ``umap1``, ``umap2`` for the control aggregate.

Run from repo root:
    PYTHONPATH=src python scripts/manuscript/build_edfig1_replogle_umap_from_h5ad.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import umap

from wtbench.manuscript.figure_io import ensure_dir, repo_root, write_tsv
from wtbench.stage2_truth_bridge import (
    build_dataset_specs,
    load_config,
    load_depmap_endpoint,
    mean_vector,
    prepare_bridge_inputs,
)

CONFIG_REL = Path("configs/stage2/truth_driven_bridge_replogle_k562_essential_day7_v1.json")
OUT_DIR_REL = Path("reports/manuscript_extended_data_v1/edfig1_replogle_panels")
OUT_UMAP = OUT_DIR_REL / "replogle_k562_essential_umap.tsv"
OUT_CONTROL = OUT_DIR_REL / "replogle_k562_essential_umap_control.tsv"


def build_profile_matrix(
    normalized,
    calls: pd.DataFrame,
    *,
    min_target_cells: int,
) -> tuple[np.ndarray, list[str]]:
    """Stack [control_mean, target1_mean, ...] in sorted target_gene order."""
    control_mask = calls["is_control"].to_numpy(dtype=bool)
    control_idx = np.flatnonzero(control_mask)
    profiles: list[np.ndarray] = [mean_vector(normalized[control_idx])]
    labels: list[str] = ["control"]

    for target_gene, target_calls in calls.loc[~calls["is_control"]].groupby("target_gene", sort=True):
        if len(target_calls) < min_target_cells:
            continue
        idx = target_calls.index.to_numpy()
        profiles.append(mean_vector(normalized[idx]))
        labels.append(str(target_gene))

    return np.stack(profiles, axis=0), labels


def main() -> None:
    root = repo_root()
    cfg_path = root / CONFIG_REL
    config = load_config(cfg_path)
    spec = build_dataset_specs(config)[0]

    dep_effect = load_depmap_endpoint(root / config["depmap"]["gene_effect_path"])
    dep_dep = load_depmap_endpoint(root / config["depmap"]["gene_dependency_path"])

    normalized, _emb, calls, _gene_meta, _e, _d = prepare_bridge_inputs(
        spec, config, dep_effect, dep_dep
    )
    min_t = int(config["filters"]["min_target_cells"])
    mat, labels = build_profile_matrix(normalized, calls, min_target_cells=min_t)

    n_samples = mat.shape[0]
    n_neighbors = min(50, max(5, n_samples // 50))
    reducer = umap.UMAP(
        n_neighbors=n_neighbors,
        n_components=2,
        random_state=42,
        min_dist=0.3,
        verbose=False,
    )
    emb = reducer.fit_transform(mat)

    ctrl_row = emb[0]
    rest_emb = emb[1:]
    rest_labels = labels[1:]

    out_umap = pd.DataFrame(
        {"target_gene": rest_labels, "umap1": rest_emb[:, 0], "umap2": rest_emb[:, 1]}
    )
    out_ctrl = pd.DataFrame([{"umap1": ctrl_row[0], "umap2": ctrl_row[1]}])

    d = ensure_dir(root / OUT_DIR_REL)
    write_tsv(out_umap, root / OUT_UMAP)
    write_tsv(out_ctrl, root / OUT_CONTROL)
    print(f"[OK] profiles={n_samples} (1 control + {len(rest_labels)} targets), UMAP neighbors={n_neighbors}")
    print(f"     wrote {root / OUT_UMAP}")
    print(f"     wrote {root / OUT_CONTROL}")


if __name__ == "__main__":
    main()
