#!/usr/bin/env python3
"""CPA Stage 2.5 smoke test: full gene set, short epochs, one seed.

Goal: verify that CPA can train on the full gene universe without OOM,
produce a valid predicted_shift matrix, and that the output schema is
compatible with WTShiftBench scoring before committing to 400-epoch full runs.

Parameters:
  - cells: full dataset (no subset)
  - genes: full gene universe (NO HVG subset)
  - epochs: 25-50 (smoke test, not performance evaluation)
  - seed: 1 (fixed for reproducibility)
  - early_stopping: enabled (patience=5)
  - checkpoint: best validation loss

Does NOT evaluate endpoint recovery; only checks stability and output format.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from datetime import datetime, timezone

import anndata as ad
import numpy as np
import pandas as pd
import scanpy as sc
import cpa
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTDIR = PROJECT_ROOT / "reports/model_eligibility/cpa_full_smoke"


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    seed = 1
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    cell_line = "HCC38"
    h5ad_path = PROJECT_ROOT / f"data/processed/cpa_hcc_formal/{cell_line}.h5ad"

    print(f"[{cell_line}] Loading CPA-ready H5AD...")
    adata = ad.read_h5ad(h5ad_path)
    adata.var_names_make_unique()
    print(f"  Shape: {adata.shape}")

    # NO HVG subset — full gene universe for smoke test
    gene_names = adata.var_names.tolist()
    print(f"  Gene universe: {len(gene_names)}")

    print("CPA.setup_anndata...")
    cpa.CPA.setup_anndata(
        adata,
        perturbation_key="cpa_perturbation",
        control_group="control",
        dosage_key="cpa_dosage",
        batch_key="cpa_batch",
        categorical_covariate_keys=["cpa_context"],
        is_count_data=False,
    )
    n_perts = len(cpa.CPA.pert_encoder)
    print(f"  Perturbation labels: {n_perts}")

    use_gpu = torch.cuda.is_available()
    device = "cuda:0" if use_gpu else "cpu"
    print(f"  Device: {device}")

    # Memory check before training
    if use_gpu:
        torch.cuda.reset_peak_memory_stats()
        mem_before = torch.cuda.memory_allocated() / 1e9
        print(f"  GPU memory before model init: {mem_before:.2f} GB")

    print("Initializing CPA model...")
    model = cpa.CPA(
        adata,
        n_latent=64,
        recon_loss="gauss",
        doser_type="logsigm",
        n_hidden_encoder=128,
        n_layers_encoder=2,
        n_hidden_decoder=128,
        n_layers_decoder=2,
    )
    print(f"  Model on device: {model.device}")

    print("Training (smoke test: max 50 epochs, early stopping patience=5)...")
    t0 = time.time()
    model.train(
        max_epochs=50,
        batch_size=256,
        use_gpu=use_gpu,
        early_stopping_patience=5,
        save_path=str(OUTDIR / f"checkpoint_{cell_line}"),
    )
    train_wall = time.time() - t0
    print(f"  Training wall time: {train_wall:.1f}s")

    # Memory check after training
    gpu_mem_peak = None
    if use_gpu:
        gpu_mem_peak = torch.cuda.max_memory_allocated() / 1e9
        print(f"  GPU memory peak: {gpu_mem_peak:.2f} GB")

    # Counterfactual prediction
    print("Counterfactual prediction per target...")
    control_mask = adata.obs["cpa_perturbation"] == "control"
    control_cells = adata[control_mask].copy()
    control_mean = control_cells.X.mean(axis=0)
    if hasattr(control_mean, "A1"):
        control_mean = control_mean.A1
    control_mean = np.asarray(control_mean).flatten()
    print(f"  Control cells: {control_cells.n_obs}")

    targets = sorted([t for t in adata.obs["cpa_perturbation"].unique() if t != "control"])
    print(f"  Targets: {len(targets)}")

    shift_records = []
    for target in targets:
        cf_adata = control_cells.copy()
        cf_adata.obs["cpa_perturbation"] = target
        cf_adata.obs["cpa_dosage"] = "1.0"
        cpa.CPA.setup_anndata(
            cf_adata,
            perturbation_key="cpa_perturbation",
            control_group="control",
            dosage_key="cpa_dosage",
            batch_key="cpa_batch",
            categorical_covariate_keys=["cpa_context"],
            is_count_data=False,
        )
        model.predict(cf_adata, n_samples=1, return_mean=True)
        pred_key = f"{model.__class__.__name__}_pred"
        pred = cf_adata.obsm[pred_key]
        pred_mean = pred.mean(axis=0)
        shift = pred_mean - control_mean
        record = {"target_gene": target}
        record.update({g: float(v) for g, v in zip(gene_names, shift)})
        shift_records.append(record)

    shift_df = pd.DataFrame(shift_records)
    out_path = OUTDIR / f"predicted_shift_{cell_line}_smoke.tsv.gz"
    shift_df.to_csv(out_path, sep="\t", index=False, compression="gzip")
    print(f"  Shift matrix saved: {out_path} ({shift_df.shape})")

    # Training cost report
    report = {
        "stage": "cpa_smoke_test",
        "cell_line": cell_line,
        "seed": seed,
        "n_cells": int(adata.n_obs),
        "n_genes": len(gene_names),
        "n_targets": len(targets),
        "n_control_cells": int(control_cells.n_obs),
        "shift_shape": list(shift_df.shape),
        "device": str(model.device),
        "train_wall_seconds": round(train_wall, 2),
        "gpu_memory_peak_gb": round(gpu_mem_peak, 3) if gpu_mem_peak else None,
        "output_path": str(out_path.relative_to(PROJECT_ROOT)),
        "endpoint_blind": True,
        "early_stopping_used": True,
        "hvg_subset": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUTDIR / f"smoke_report_{cell_line}.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(f"[Done] Smoke test report saved.")


if __name__ == "__main__":
    main()
