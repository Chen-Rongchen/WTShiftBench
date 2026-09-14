#!/usr/bin/env python3
"""Run a small scGen HCC perturbation-response smoke.

The script trains one scGen model per cell line, predicts control -> target
counterfactual cells for a small target subset by default, and writes a raw
target_gene x gene predicted_shift matrix. Full runs can be requested by
setting --max-targets 0 and a larger --max-epochs after GPU capacity is free.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AXIS_MEMBERSHIP_PATH = (
    PROJECT_ROOT / "reports/truth_driven_bridge/master_atlas/shared_target_axis_membership.tsv"
)
DEFAULT_INPUT_ROOT = PROJECT_ROOT / "data/processed/cpa_hcc_formal"
DEFAULT_OUTDIR = PROJECT_ROOT / "reports/model_eligibility/scgen_hcc_smoke"


def project_relative(path: Path) -> str:
    resolved = path.resolve()
    return str(resolved.relative_to(PROJECT_ROOT)) if resolved.is_relative_to(PROJECT_ROOT) else str(resolved)


def axis_targets_and_genes(path: Path) -> tuple[list[str], list[str]]:
    frame = pd.read_csv(path, sep="\t")
    genes = frame["target_gene"].astype(str).drop_duplicates().sort_values().tolist()
    return genes, genes


def mean_vector(x) -> np.ndarray:
    value = x.mean(axis=0)
    if sparse.issparse(value):
        value = value.A1
    return np.asarray(value).ravel().astype(np.float64)


def matrix_to_numpy(x) -> np.ndarray:
    if sparse.issparse(x):
        return x.toarray()
    return np.asarray(x)


def encode_latent_mean(model, adata) -> tuple[np.ndarray, np.ndarray]:
    import torch

    device = next(model.module.parameters()).device
    x = torch.as_tensor(matrix_to_numpy(adata.X), dtype=torch.float32, device=device)
    model.module.eval()
    with torch.no_grad():
        qz_m, _qz_v, _z = model.module.z_encoder(x)
    latent = qz_m.detach().cpu().numpy().astype(np.float64, copy=False)
    return latent.mean(axis=0), latent


def decode_latent(model, latent: np.ndarray) -> np.ndarray:
    import torch

    device = next(model.module.parameters()).device
    z = torch.as_tensor(latent, dtype=torch.float32, device=device)
    model.module.eval()
    with torch.no_grad():
        decoded = model.module.generative(z)["px"]
    return decoded.detach().cpu().numpy().astype(np.float64, copy=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run scGen HCC smoke prediction.")
    parser.add_argument("--cell-line", required=True, choices=["HCC38", "HCC1143"])
    parser.add_argument("--input-root", default=str(DEFAULT_INPUT_ROOT))
    parser.add_argument("--axis-membership-path", default=str(DEFAULT_AXIS_MEMBERSHIP_PATH))
    parser.add_argument("--outdir", default=str(DEFAULT_OUTDIR))
    parser.add_argument("--max-targets", type=int, default=3, help="0 means all axis targets.")
    parser.add_argument("--max-epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--early-stopping-patience", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1)
    return parser


def main() -> None:
    args = build_parser().parse_args()

    import scgen
    import torch

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    input_path = Path(args.input_root) / f"{args.cell_line}.h5ad"
    target_order, output_genes = axis_targets_and_genes(Path(args.axis_membership_path))
    adata = ad.read_h5ad(input_path)
    adata.var_names_make_unique()

    missing_genes = [gene for gene in output_genes if gene not in set(adata.var_names.astype(str))]
    if missing_genes:
        raise ValueError(f"{args.cell_line} missing output genes: {missing_genes}")

    present = set(adata.obs["cpa_perturbation"].astype(str))
    targets = [target for target in target_order if target in present]
    if args.max_targets > 0:
        targets = targets[: args.max_targets]
    if not targets:
        raise ValueError(f"{args.cell_line} has no target overlap with axis membership.")

    keep_mask = adata.obs["cpa_perturbation"].astype(str).isin(["control", *targets]).to_numpy()
    gene_positions = pd.Series(np.arange(adata.n_vars), index=adata.var_names.astype(str)).loc[output_genes].to_numpy()
    work = adata[keep_mask, gene_positions].copy()
    work.obs["condition"] = work.obs["cpa_perturbation"].astype(str)
    work.obs["cell_type"] = args.cell_line
    work.obs_names_make_unique()

    control = work[work.obs["condition"].astype(str).eq("control")].copy()
    control_mean = mean_vector(control.X)
    if control.n_obs == 0:
        raise ValueError(f"{args.cell_line} has no control cells after filtering.")

    scgen.SCGEN.setup_anndata(work, batch_key="condition", labels_key="cell_type")
    model = scgen.SCGEN(work)

    t0 = time.time()
    model.train(
        max_epochs=args.max_epochs,
        batch_size=args.batch_size,
        early_stopping=True,
        early_stopping_patience=args.early_stopping_patience,
    )
    train_wall = time.time() - t0

    rows: list[dict[str, object]] = []
    per_target: dict[str, object] = {}
    latent_control_mean, latent_control_cells = encode_latent_mean(model, control)
    for target in targets:
        target_adata = work[work.obs["condition"].astype(str).eq(target)].copy()
        latent_target_mean, _latent_target_cells = encode_latent_mean(model, target_adata)
        latent_delta = latent_target_mean - latent_control_mean
        pred_x = decode_latent(model, latent_control_cells + latent_delta[np.newaxis, :])
        pred = ad.AnnData(
            X=pred_x,
            obs=control.obs.copy(),
            var=control.var.copy(),
        )
        pred_mean = mean_vector(pred.X)
        shift = pred_mean - control_mean
        rows.append({"target_gene": target, **dict(zip(output_genes, shift.tolist()))})
        per_target[target] = {
            "predicted_cells": int(pred.n_obs),
            "target_cells": int(target_adata.n_obs),
            "latent_delta_l2": float(np.linalg.norm(latent_delta)),
        }

    outdir = Path(args.outdir) / args.cell_line
    outdir.mkdir(parents=True, exist_ok=True)
    prediction_path = outdir / "predicted_shift.tsv.gz"
    pd.DataFrame(rows).to_csv(prediction_path, sep="\t", index=False)

    report = {
        "stage": "scgen_hcc_smoke",
        "cell_line": args.cell_line,
        "input_path": project_relative(input_path),
        "prediction_path": project_relative(prediction_path),
        "n_targets": len(targets),
        "targets": targets,
        "n_genes": len(output_genes),
        "n_cells": int(work.n_obs),
        "n_control_cells": int(control.n_obs),
        "max_epochs": args.max_epochs,
        "batch_size": args.batch_size,
        "early_stopping_patience": args.early_stopping_patience,
        "train_wall_seconds": round(train_wall, 2),
        "device_cuda_available": bool(torch.cuda.is_available()),
        "per_target": per_target,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    report_path = outdir / "smoke_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"scGen smoke prediction: {prediction_path}")
    print(f"scGen smoke report: {report_path}")


if __name__ == "__main__":
    main()
