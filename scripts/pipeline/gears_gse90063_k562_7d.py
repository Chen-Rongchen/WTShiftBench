#!/usr/bin/env python3
"""GEARS GSE90063 K562/7d local training test: checks architecture replication on K562 TF pool data.

Output goes to tests/test_gears_gse90063/ for review before deciding data tiering.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import torch
from gears import GEARS, PertData

from scripts.stage1a.adapters.gears.build_predictions import (
    build_gears_input_adata,
    build_identity_graph,
    build_local_perturbation_graph,
    build_split_file,
    predict_transcriptomes,
    write_fake_gene2go,
    write_gene_set,
)
from wtbench.hcc_prediction_export import expected_target_and_gene_order
from wtbench.truth_bridge import log_normalize_csr


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = PROJECT_ROOT / "tests" / "test_gears_gse90063"


def log_stage(stage: str, **fields: object) -> None:
    suffix = ""
    if fields:
        suffix = " | " + ", ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[stage2-gears-gse90063] {stage}{suffix}", flush=True)


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_recipe(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_matrix(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, sep="\t", index=False, compression="gzip")


def write_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extract_gene_symbol(ensg_symbol: str) -> str:
    """Extract gene symbol from ENSGxxxxxx_symbol format."""
    s = str(ensg_symbol)
    if "_" in s:
        return s.split("_", 1)[1]
    return s


def build_gse90063_formal_adata(
    input_h5ad_path: Path,
    frozen_genes: set[str],
) -> tuple[ad.AnnData, list[str]]:
    """Build GEARS-compatible formal AnnData from GSE90063 h5ad.

    The h5ad uses ENSGxxxxxx_symbol format for var index. We extract gene symbols
    for atlas matching and use extracted symbols in the formal AnnData.

    Missing columns needed by GEARS are computed here:
    - cell_barcode  <- obs index (cell_id)
    - feature_call  <- sgRNA
    - num_features  <- already present
    - num_umis     <- computed from expression matrix (X.sum(axis=1))

    Gene filtering: keep only frozen genes to avoid CUDA OOM.
    """
    log_stage("load_h5ad_start", path=str(input_h5ad_path))
    raw = ad.read_h5ad(input_h5ad_path)

    # Map ENSG_symbol to gene symbol and filter to frozen genes
    all_var_names = raw.var.index.astype(str).tolist()
    extracted_symbols = [extract_gene_symbol(g) for g in all_var_names]
    symbol_to_ensg = {extract_gene_symbol(g): g for g in all_var_names}

    gene_mask = pd.Series(extracted_symbols).isin(frozen_genes).to_numpy()
    raw = raw[:, gene_mask].copy()
    log_stage("gene_filtered", n_vars=int(raw.n_vars), frozen_genes=len(frozen_genes))

    # Recompute extracted symbols after filtering
    filtered_var_names = raw.var.index.astype(str).tolist()
    filtered_symbols = [extract_gene_symbol(g) for g in filtered_var_names]

    # Compute num_umis from expression matrix
    num_umis = np.asarray(raw.X.sum(axis=1)).ravel()

    # Build obs
    obs = pd.DataFrame({
        "cell_barcode": raw.obs.index.astype(str).values,
        "feature_call": raw.obs["sgRNA"].astype(str).values,
        "target_gene": raw.obs["target_gene"].astype(str).fillna("").values,
        "is_control": raw.obs["is_control"].astype(bool).values,
        "num_features": raw.obs["num_features"].astype(int).values,
        "num_umis": num_umis,
    })
    obs.index = obs["cell_barcode"]
    obs.index.name = "obs_id"

    # Build var with extracted gene symbols (not ENSG IDs)
    var = pd.DataFrame(index=filtered_symbols)
    var["gene_name"] = var.index.astype(str)

    # Build X (log-normalized)
    normalized = log_normalize_csr(raw.X, target_sum=10000.0).tocsr()

    formal_adata = ad.AnnData(X=normalized, obs=obs, var=var)
    formal_adata.obs["is_control"] = formal_adata.obs["is_control"].astype(bool)

    # Perturbation target list (these are already gene symbols from obs)
    train_targets = sorted(
        formal_adata.obs.loc[~formal_adata.obs["is_control"].astype(bool), "target_gene"]
        .astype(str)
        .unique()
        .tolist()
    )
    log_stage(
        "formal_adata_ready",
        n_obs=int(formal_adata.n_obs),
        n_vars=int(formal_adata.n_vars),
        train_targets=len(train_targets),
        cell_type=raw.obs["dataset_id"].iloc[0] if "dataset_id" in raw.obs.columns else "unknown",
    )
    return formal_adata, train_targets


def run_gse90063_gears(recipe: dict) -> dict:
    runtime = dict(recipe["runtime"])
    model_id = str(recipe["model_id"])
    cell_type_label = str(recipe["cell_type_label"])

    output_root = resolve_path(str(recipe["output_root"])) / model_id / cell_type_label
    report_root = resolve_path(str(recipe["report_root"])) / cell_type_label
    cache_dir = TEST_ROOT / "tmp" / model_id / cell_type_label
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Load axis membership for output gene ordering
    axis_membership_path = resolve_path(str(recipe["axis_membership_path"]))
    axis_membership = pd.read_csv(axis_membership_path, sep="\t")
    target_order, output_genes = expected_target_and_gene_order(axis_membership)
    frozen_genes = set(output_genes)
    log_stage("axis_membership_loaded", output_genes=len(output_genes), targets=len(target_order))

    # Build formal AnnData with gene filtering
    formal_adata, perturbation_genes = build_gse90063_formal_adata(
        input_h5ad_path=resolve_path(str(recipe["input_h5ad_path"])),
        frozen_genes=frozen_genes,
    )

    # Control baseline
    control_values = np.asarray(
        formal_adata.X[formal_adata.obs["is_control"].to_numpy()].mean(axis=0)
    ).ravel().astype(np.float64)

    # Prepare GEARS input
    rng = np.random.default_rng(int(runtime["training_seed"]))
    train_adata, train_targets = build_gears_input_adata(
        formal_adata=formal_adata,
        heldout_targets=set(),
        rng=rng,
        max_control_cells=runtime.get("max_control_cells"),
        max_cells_per_train_condition=runtime.get("max_cells_per_train_condition"),
        cell_type_label=cell_type_label,
    )
    log_stage(
        "build_gears_input_done",
        train_cells=int(train_adata.n_obs),
        train_targets=len(train_targets),
    )

    # PertData init
    write_fake_gene2go(cache_dir, perturbation_genes)
    gene_set_path = write_gene_set(cache_dir, perturbation_genes)
    split_path = cache_dir / "custom_split.pkl"
    train_conditions = sorted(train_adata.obs["condition"].astype(str).unique().tolist())
    split_payload = build_split_file(
        split_path,
        train_conditions,
        int(runtime["training_seed"]),
        float(runtime["train_val_fraction"]),
    )

    pert_data = PertData(str(cache_dir), gene_set_path=str(gene_set_path), default_pert_graph=False)
    log_stage("new_data_process_start")
    pert_data.new_data_process(
        dataset_name=f"{cell_type_label}_{model_id}",
        adata=train_adata,
        skip_calc_de=False,
    )
    pert_data.prepare_split(split="custom", split_dict_path=str(split_path))
    effective_batch_size = min(int(runtime["batch_size"]), max(1, train_adata.n_obs))
    pert_data.get_dataloader(batch_size=effective_batch_size, test_batch_size=effective_batch_size)
    pert_data.dataloader.pop("test_loader", None)
    log_stage("dataloader_ready", effective_batch_size=effective_batch_size)

    # Graph building
    requested_device = str(runtime.get("device", "auto"))
    device = "cuda" if requested_device == "auto" and torch.cuda.is_available() else "cpu"
    log_stage("device_selected", device=device)

    perturbation_edge_index, perturbation_edge_weight = build_local_perturbation_graph(
        control_matrix=train_adata.X[train_adata.obs["condition"].astype(str).eq("ctrl").to_numpy()],
        control_gene_names=train_adata.var["gene_name"].astype(str).tolist(),
        perturbation_genes=pert_data.pert_names.astype(str).tolist(),
        k=int(runtime["perturbation_graph_k"]),
    )
    gene_edge_index, gene_edge_weight = build_identity_graph(train_adata.n_vars)

    # Model init and training
    gears_model = GEARS(pert_data, device=device, weight_bias_track=False)
    gears_model.model_initialize(
        G_go=perturbation_edge_index,
        G_go_weight=perturbation_edge_weight,
        G_coexpress=gene_edge_index,
        G_coexpress_weight=gene_edge_weight,
    )
    log_stage("train_start", epochs=int(runtime["epochs"]))
    gears_model.train(
        epochs=int(runtime["epochs"]),
        lr=float(runtime["lr"]),
        weight_decay=float(runtime["weight_decay"]),
    )
    log_stage("train_done")

    # Prediction: all train_targets are predictable (they are in pert_list).
    # Note: GSE90063 TF pool (10 genes) does NOT overlap with the 47-gene atlas,
    # so output uses model's actual output genes as columns.
    predict_targets = list(train_targets)
    log_stage("predict_start", target_count=len(predict_targets), total=len(target_order))
    transcriptome_predictions = predict_transcriptomes(
        gears_model=gears_model,
        target_order=predict_targets,
        num_samples=int(runtime["prediction_num_samples"]),
        device=device,
    )
    log_stage("predict_done")

    # Assemble predicted_shift matrix
    # Columns = all frozen genes in model's output vocabulary (45 genes)
    gene_names = pd.Index(train_adata.var["gene_name"].astype(str).to_numpy())
    gene_position_index = pd.Series(
        np.arange(train_adata.n_vars, dtype=np.int64),
        index=gene_names,
    ).loc[~pd.Index(gene_names).duplicated(keep="first")]

    # output_genes_for_columns: use all frozen genes present in model
    model_output_genes = [g for g in output_genes if g in gene_position_index.index]
    output_gene_positions = gene_position_index.loc[model_output_genes].to_numpy(dtype=np.int64)

    delta_rows = []
    for target_gene in predict_targets:
        predicted_expression = transcriptome_predictions[target_gene].astype(np.float64, copy=False)
        predicted_delta = predicted_expression - control_values
        delta_rows.append(predicted_delta[output_gene_positions])

    predicted_shift = pd.DataFrame(delta_rows, columns=model_output_genes)
    predicted_shift.insert(0, "target_gene", predict_targets)

    prediction_path = output_root / "predicted_shift.tsv.gz"
    write_matrix(predicted_shift, prediction_path)
    log_stage("write_prediction_done", path=str(prediction_path))

    # Provenance
    provenance_path = output_root / "provenance.json"
    provenance = {
        "stage": "gse90063_k562_gears_test",
        "dataset_role": str(recipe.get("dataset_role", "supplementary_test")),
        "cell_line": cell_type_label,
        "entrant_id": str(recipe["entrant_id"]),
        "entrant_version": str(recipe["entrant_version"]),
        "model_id": model_id,
        "prediction_space": "normalized_log1p_internal_then_predicted_shift",
        "normalization_target_sum": 10000.0,
        "raw_input_source": str(resolve_path(str(recipe["input_h5ad_path"])).relative_to(PROJECT_ROOT)),
        "runtime": runtime,
        "training_summary": {
            "requested_device": requested_device,
            "device": device,
            "train_cells": int(train_adata.n_obs),
            "train_targets": len(train_targets),
            "all_frozen_targets": len(target_order),
            "control_cells_before_sampling": int(formal_adata.obs["is_control"].sum()),
            "frozen_target_cells_before_sampling": int((~formal_adata.obs["is_control"]).sum()),
            "split_train_conditions": len(split_payload["train"]),
            "split_val_conditions": len(split_payload["val"]),
        },
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    write_json(provenance, provenance_path)

    write_json(
        {
            "stage": "gse90063_k562_gears_test_recipe_run",
            "cell_line": cell_type_label,
            "prediction_path": str(prediction_path.relative_to(PROJECT_ROOT)),
            "provenance_path": str(provenance_path.relative_to(PROJECT_ROOT)),
        },
        report_root / "run_summary.json",
    )
    log_stage("run_complete", prediction_path=str(prediction_path))

    return {
        "cell_line": cell_type_label,
        "prediction_path": str(prediction_path.relative_to(PROJECT_ROOT)),
        "provenance_path": str(provenance_path.relative_to(PROJECT_ROOT)),
        "device": device,
        "train_cells": int(train_adata.n_obs),
        "target_count": len(target_order),
        "predicted_genes": len(predict_targets),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="GEARS GSE90063 K562/7d local training test.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/gears_gse90063_k562_tf_7d_v1.json"),
    )
    args = parser.parse_args()
    recipe = load_recipe(resolve_path(args.config))
    result = run_gse90063_gears(recipe)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
