#!/usr/bin/env python3
"""GEARS K562/Dixit local training test: checks architecture replication on K562 data.

Output goes to tests/test_gears_dixit/ for review before deciding data tiering.
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
TEST_ROOT = PROJECT_ROOT / "tests" / "test_gears_dixit"


def log_stage(stage: str, **fields: object) -> None:
    suffix = ""
    if fields:
        suffix = " | " + ", ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[stage2-gears-dixit] {stage}{suffix}", flush=True)


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


def build_dixit_formal_adata(
    input_h5ad_path: Path,
    cell_type_label: str,
    frozen_genes: set[str],
) -> tuple[ad.AnnData, list[str]]:
    """Build GEARS-compatible formal AnnData from candidate_formal_like h5ad.

    Adds missing columns:
    - cell_barcode  <- cell_id
    - feature_call  <- sgRNA
    - num_features  <- 1 (single perturbation)
    - num_umis      <- UMI_count

    Filters genes to frozen_genes to avoid CUDA OOM (same as HCC materialize).
    """
    log_stage("load_h5ad_start", path=str(input_h5ad_path))
    raw = ad.read_h5ad(input_h5ad_path)

    # Gene filtering: keep only frozen genes (same as HCC GEARS formal h5ad)
    all_genes = raw.var.index.astype(str).tolist()
    gene_mask = pd.Series(all_genes).isin(frozen_genes).to_numpy()
    raw = raw[:, gene_mask].copy()
    log_stage("gene_filtered", n_vars=int(raw.n_vars), frozen_genes=len(frozen_genes))

    # Build obs
    obs = pd.DataFrame({
        "cell_barcode": raw.obs["cell_id"].astype(str).values,
        "feature_call": raw.obs["sgRNA"].astype(str).values,
        "target_gene": raw.obs["target_gene"].astype(str).fillna("").values,
        "is_control": raw.obs["is_control"].astype(bool).values,
        "num_features": 1,
        "num_umis": raw.obs["UMI_count"].astype(float).values,
    })
    obs.index = obs["cell_barcode"]
    obs.index.name = "obs_id"

    # Build var
    gene_names = raw.var.index.astype(str).tolist()
    var = pd.DataFrame(index=gene_names)
    var["gene_name"] = var.index.astype(str)

    # Build X (log-normalized)
    normalized = log_normalize_csr(raw.X, target_sum=10000.0).tocsr()

    formal_adata = ad.AnnData(X=normalized, obs=obs, var=var)
    formal_adata.obs["is_control"] = formal_adata.obs["is_control"].astype(bool)

    # Perturbation target list
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
        cell_type=cell_type_label,
    )
    return formal_adata, train_targets


def run_dixit_gears(recipe: dict) -> dict:
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
    formal_adata, perturbation_genes = build_dixit_formal_adata(
        input_h5ad_path=resolve_path(str(recipe["input_h5ad_path"])),
        cell_type_label=cell_type_label,
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

    # Prediction: restrict to genes the model was actually trained on (pert_list).
    # predict_transcriptomes internally uses gears_model.pert_list as gene_names for
    # index lookups, so only genes in pert_list can be predicted successfully.
    predict_targets = [g for g in train_targets if g in set(output_genes)]
    log_stage("predict_start", target_count=len(predict_targets), total=len(target_order))
    transcriptome_predictions = predict_transcriptomes(
        gears_model=gears_model,
        target_order=predict_targets,
        num_samples=int(runtime["prediction_num_samples"]),
        device=device,
    )
    log_stage("predict_done")

    # Assemble predicted_shift matrix
    gene_names = pd.Index(train_adata.var["gene_name"].astype(str).to_numpy())
    gene_position_index = pd.Series(
        np.arange(train_adata.n_vars, dtype=np.int64),
        index=gene_names,
    ).loc[~pd.Index(gene_names).duplicated(keep="first")]

    # output_gene_positions: positions of all atlas output genes in the model's gene dimension
    output_gene_positions = gene_position_index.loc[output_genes].to_numpy(dtype=np.int64)

    delta_rows = []
    for target_gene in predict_targets:
        predicted_expression = transcriptome_predictions[target_gene].astype(np.float64, copy=False)
        predicted_delta = predicted_expression - control_values
        delta_rows.append(predicted_delta[output_gene_positions])

    predicted_shift = pd.DataFrame(delta_rows, columns=output_genes)
    predicted_shift.insert(0, "target_gene", predict_targets)

    prediction_path = output_root / "predicted_shift.tsv.gz"
    write_matrix(predicted_shift, prediction_path)
    log_stage("write_prediction_done", path=str(prediction_path))

    # Provenance
    provenance_path = output_root / "provenance.json"
    provenance = {
        "stage": "k562_gears_test",
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
            "stage": "k562_gears_test_recipe_run",
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
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="GEARS K562/Dixit local training test.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/gears_dixit_test_v1.json"),
    )
    args = parser.parse_args()
    recipe = load_recipe(resolve_path(args.config))
    result = run_dixit_gears(recipe)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
