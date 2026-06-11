#!/usr/bin/env python3
"""CPA counterfactual shift extraction on HCC38.

Loads the reduced-probe trained CPA model, predicts expression for each
perturbation target starting from control cells, and derives the
target-level predicted shift (pred_mean - control_mean).

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
MODEL_DIR = PROJECT_ROOT / "reports/model_eligibility/cpa_hcc38_reduced_probe/checkpoint"
H5AD_PATH = PROJECT_ROOT / "data/processed/cpa_hcc_formal/HCC38.h5ad"
OUTDIR = PROJECT_ROOT / "reports/model_eligibility/cpa_hcc38_reduced_probe"


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)

    print("[1/4] Loading CPA-ready HCC38 H5AD...")
    adata = ad.read_h5ad(H5AD_PATH)
    adata.var_names_make_unique()

    # Same HVG subset as training
    sc.pp.highly_variable_genes(adata, n_top_genes=2000, subset=True)
    gene_names = adata.var_names.tolist()
    print(f"  HVG subset: {adata.shape}")

    # Re-run setup_anndata (same params as training)
    print("[2/4] CPA.setup_anndata...")
    cpa.CPA.setup_anndata(
        adata,
        perturbation_key="cpa_perturbation",
        control_group="control",
        dosage_key="cpa_dosage",
        batch_key="cpa_batch",
        categorical_covariate_keys=["cpa_context"],
        is_count_data=False,
    )

    # Load trained model
    print("[3/4] Loading trained CPA model...")
    model = cpa.CPA.load(
        MODEL_DIR,
        adata=adata,
        use_gpu=torch.cuda.is_available(),
        extend_categories=True,
    )
    print(f"  Model loaded from {MODEL_DIR}")

    # Extract control cells
    control_mask = adata.obs["cpa_perturbation"] == "control"
    control_cells = adata[control_mask].copy()
    control_mean = control_cells.X.mean(axis=0)
    if hasattr(control_mean, "A1"):
        control_mean = control_mean.A1
    control_mean = np.asarray(control_mean).flatten()
    print(f"  Control cells: {control_cells.n_obs}")

    # Get all non-control targets
    targets = sorted(
        [t for t in adata.obs["cpa_perturbation"].unique() if t != "control"]
    )
    print(f"  Targets to predict: {len(targets)}")

    # Counterfactual prediction for each target
    print("[4/4] Counterfactual prediction per target...")
    shift_records = []
    for target in targets:
        # Copy control cells and change their perturbation label
        cf_adata = control_cells.copy()
        cf_adata.obs["cpa_perturbation"] = target
        cf_adata.obs["cpa_dosage"] = "1.0"
        # Re-register so the data loader picks up the new label
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

    # Save a lightweight validation report
    report = {
        "n_targets": len(targets),
        "n_genes": len(gene_names),
        "n_control_cells": int(control_cells.n_obs),
        "shift_shape": list(shift_df.shape),
        "output_path": str(out_path.relative_to(PROJECT_ROOT)),
    }
    import json
    (OUTDIR / "counterfactual_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
