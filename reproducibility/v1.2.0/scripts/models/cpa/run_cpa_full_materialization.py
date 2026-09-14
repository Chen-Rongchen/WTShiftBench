#!/usr/bin/env python3
"""CPA full materialization: max_epochs=400 (upper bound), early stopping, checkpoint best.

Trains CPA on the full gene universe with the agreed parameter policy:
  - endpoint_blind: True (no DepMap metrics for hyperparameter selection)
  - max_epochs: 400 (auto-calculated upper bound; early stopping may halt sooner)
  - early_stopping_patience: 10-15
  - checkpoint: best validation ELBO / loss
  - seeds: fixed for reproducibility
  - hvg_subset: False (full gene universe required for WTShiftBench scoring)

Output: predicted_shift.tsv.gz per cell line, plus training_cost_report.json.
"""

from __future__ import annotations

import argparse
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


def project_relative(path: Path) -> str:
    resolved = path.resolve()
    return str(resolved.relative_to(PROJECT_ROOT)) if resolved.is_relative_to(PROJECT_ROOT) else str(resolved)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CPA full materialization runner.")
    parser.add_argument("--cell-line", required=True, choices=["HCC38", "HCC1143"])
    parser.add_argument("--max-epochs", type=int, default=400)
    parser.add_argument("--early-stopping-patience", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--n-latent", type=int, default=64)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--outdir", default="reports/model_eligibility/cpa_full_materialization")
    return parser


def run_training(
    *,
    cell_line: str,
    max_epochs: int,
    early_stopping_patience: int,
    batch_size: int,
    n_latent: int,
    seed: int,
    outdir: Path,
) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    h5ad_path = PROJECT_ROOT / f"data/processed/cpa_hcc_formal/{cell_line}.h5ad"
    print(f"[{cell_line}] Loading CPA-ready H5AD...")
    adata = ad.read_h5ad(h5ad_path)
    adata.var_names_make_unique()
    print(f"  Shape: {adata.shape}")

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

    gpu_mem_peak = None
    if use_gpu:
        torch.cuda.reset_peak_memory_stats()

    print(f"Initializing CPA (n_latent={n_latent})...")
    model = cpa.CPA(
        adata,
        n_latent=n_latent,
        recon_loss="gauss",
        doser_type="logsigm",
        n_hidden_encoder=128,
        n_layers_encoder=2,
        n_hidden_decoder=128,
        n_layers_decoder=2,
    )
    print(f"  Model device: {model.device}")

    print(f"Training (max_epochs={max_epochs}, early_stopping_patience={early_stopping_patience})...")
    t0 = time.time()
    model.train(
        max_epochs=max_epochs,
        batch_size=batch_size,
        use_gpu=use_gpu,
        early_stopping_patience=early_stopping_patience,
        save_path=str(outdir / f"checkpoint_{cell_line}"),
    )
    train_wall = time.time() - t0
    print(f"  Training wall time: {train_wall:.1f}s")

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
    out_path = outdir / f"predicted_shift_{cell_line}.tsv.gz"
    shift_df.to_csv(out_path, sep="\t", index=False, compression="gzip")
    print(f"  Shift matrix saved: {out_path} ({shift_df.shape})")

    report = {
        "stage": "cpa_full_materialization",
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
        "max_epochs": max_epochs,
        "early_stopping_patience": early_stopping_patience,
        "batch_size": batch_size,
        "n_latent": n_latent,
        "output_path": project_relative(out_path),
        "endpoint_blind": True,
        "early_stopping_used": True,
        "hvg_subset": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    (outdir / f"training_cost_report_{cell_line}.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("[Done] Full materialization complete.")
    return report


def main():
    args = build_parser().parse_args()
    outdir = PROJECT_ROOT / args.outdir
    run_training(
        cell_line=args.cell_line,
        max_epochs=args.max_epochs,
        early_stopping_patience=args.early_stopping_patience,
        batch_size=args.batch_size,
        n_latent=args.n_latent,
        seed=args.seed,
        outdir=outdir,
    )


if __name__ == "__main__":
    main()
