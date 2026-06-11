#!/usr/bin/env python3
"""CPA train + counterfactual shift extraction on HCC1143 (GPU accelerated).

Trains CPA on HCC1143 with reduced probe settings, then immediately runs
counterfactual prediction for each target to derive target-level predicted shift.

Output format: target_gene x gene predicted shift TSV,
compatible with WTShiftBench ModelStructureScorer.
"""

from pathlib import Path
import anndata as ad
import numpy as np
import pandas as pd
import scanpy as sc
import cpa
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTDIR = PROJECT_ROOT / "reports/model_eligibility/cpa_hcc1143_reduced_probe"


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)

    print("[1/5] Loading CPA-ready HCC1143 H5AD...")
    adata = ad.read_h5ad(PROJECT_ROOT / "data/processed/cpa_hcc_formal/HCC1143.h5ad")
    adata.var_names_make_unique()
    print(f"  Original shape: {adata.shape}")

    # HVG subset for speed
    print("[2/5] Selecting HVG subset...")
    sc.pp.highly_variable_genes(adata, n_top_genes=2000, subset=True)
    gene_names = adata.var_names.tolist()
    print(f"  HVG subset shape: {adata.shape}")

    # Setup CPA
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

    # Initialize + train
    print("[4/5] Training CPA (n_latent=64, gauss, logsigm, GPU)...")
    use_gpu = torch.cuda.is_available()
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
    model.train(
        max_epochs=10,
        batch_size=256,
        use_gpu=use_gpu,
        early_stopping_patience=5,
        save_path=str(OUTDIR / "checkpoint"),
    )
    print("  Training complete.")

    # Counterfactual prediction
    print("[5/5] Counterfactual prediction per target...")
    control_mask = adata.obs["cpa_perturbation"] == "control"
    control_cells = adata[control_mask].copy()
    control_mean = control_cells.X.mean(axis=0)
    if hasattr(control_mean, "A1"):
        control_mean = control_mean.A1
    control_mean = np.asarray(control_mean).flatten()
    print(f"  Control cells: {control_cells.n_obs}")

    targets = sorted([t for t in adata.obs["cpa_perturbation"].unique() if t != "control"])
    print(f"  Targets to predict: {len(targets)}")

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
    out_path = OUTDIR / "predicted_shift.tsv.gz"
    shift_df.to_csv(out_path, sep="\t", index=False, compression="gzip")
    print(f"[Done] Shift matrix saved: {out_path} ({shift_df.shape})")

    report = {
        "status": "success",
        "n_targets": len(targets),
        "n_genes": len(gene_names),
        "n_control_cells": int(control_cells.n_obs),
        "shift_shape": list(shift_df.shape),
        "device": str(model.device),
        "output_path": str(out_path.relative_to(PROJECT_ROOT)),
    }
    import json
    (OUTDIR / "train_predict_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
