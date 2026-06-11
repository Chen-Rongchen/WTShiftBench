#!/usr/bin/env python3
"""CPA reduced probe on HCC38 — minimal training to verify pipeline viability."""

from pathlib import Path
import anndata as ad
import scanpy as sc
import cpa
import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTDIR = PROJECT_ROOT / "reports/model_eligibility/cpa_hcc38_reduced_probe"


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)

    print("[1/5] Loading CPA-ready HCC38 H5AD...")
    adata = ad.read_h5ad(PROJECT_ROOT / "data/processed/cpa_hcc_formal/HCC38.h5ad")
    print(f"  Original shape: {adata.shape}")

    # Deduplicate var names to prevent scVI warnings
    adata.var_names_make_unique()

    # Subset to HVG for reduced probe speed (2000 genes)
    print("[2/5] Selecting HVG subset...")
    sc.pp.highly_variable_genes(adata, n_top_genes=2000, subset=True)
    print(f"  HVG subset shape: {adata.shape}")

    # Setup CPA anndata
    print("[3/5] CPA.setup_anndata...")
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
    print(f"  Perturbation encoder: {n_perts} labels")

    # Initialize model with small architecture for speed
    print("[4/5] Initializing CPA model (n_latent=64, gauss, logsigm)...")
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
    print(f"  Model device: {model.device}")

    # Reduced probe: 10 epochs, large batch
    print("[5/5] Training (max_epochs=10, batch_size=256)...")
    model.train(
        max_epochs=10,
        batch_size=256,
        use_gpu=torch.cuda.is_available(),
        early_stopping_patience=5,
        save_path=str(OUTDIR / "checkpoint"),
    )
    print("  Training complete.")

    # Validate predict API
    print("[Validate] Running predict() on first 100 cells...")
    subset = adata[:100].copy()
    model.predict(subset, n_samples=1, return_mean=True)
    pred_key = f"{model.__class__.__name__}_pred"
    assert pred_key in subset.obsm, f"Expected {pred_key} in obsm"
    print(f"  Predict output shape: {subset.obsm[pred_key].shape}")
    print(f"  Predict output dtype: {subset.obsm[pred_key].dtype}")

    # Save a lightweight report
    report = {
        "status": "success",
        "original_shape": (14175, 36601),
        "hvg_shape": list(adata.shape),
        "n_perts": n_perts,
        "n_latent": 64,
        "epochs": 10,
        "batch_size": 256,
        "device": str(model.device),
        "predict_shape": list(subset.obsm[pred_key].shape),
    }
    import json
    (OUTDIR / "reduced_probe_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(f"[Done] Report saved to {OUTDIR / 'reduced_probe_report.json'}")


if __name__ == "__main__":
    main()
