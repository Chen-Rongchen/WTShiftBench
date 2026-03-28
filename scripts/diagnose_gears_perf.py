from __future__ import annotations

import argparse
import json
import pickle
import os
import resource
import time
from pathlib import Path

import anndata as ad
import numpy as np
import torch
from gears import GEARS, PertData
from gears.inference import compute_metrics, evaluate
from gears.utils import loss_fct, uncertainty_loss_fct
from torch.optim import Adam
from torch.optim.lr_scheduler import StepLR

from scripts.stage1a.adapters.common.runtime import (
    coalesce_arg,
    load_frozen_prediction_space,
    load_run_config,
    resolve_path,
)
from scripts.stage1a.adapters.gears.build_predictions import (
    build_gears_input_adata,
    build_identity_graph,
    build_local_perturbation_graph,
    build_split_file,
    set_random_seed,
    write_fake_gene2go,
    write_gene_set,
)
from scripts.stage1a.benchmark_invariant.catalog import get_formal_dataset_contract


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="诊断 GEARS formal 训练性能。")
    parser.add_argument("--run-config", required=True)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--device")
    parser.add_argument("--output-json", required=True)
    return parser


def get_nvml_snapshot() -> dict[str, float | int | str | None]:
    try:
        import pynvml  # type: ignore

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return {
            "gpu_util_percent": int(util.gpu),
            "gpu_mem_util_percent": int(util.memory),
            "gpu_mem_used_mb": round(mem.used / (1024**2), 2),
            "gpu_mem_total_mb": round(mem.total / (1024**2), 2),
            "gpu_name": pynvml.nvmlDeviceGetName(handle).decode("utf-8"),
        }
    except Exception as exc:
        return {
            "gpu_util_percent": None,
            "gpu_mem_util_percent": None,
            "gpu_mem_used_mb": None,
            "gpu_mem_total_mb": None,
            "gpu_name": None,
            "gpu_monitor_error": str(exc),
        }


def cpu_mem_mb() -> float:
    rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(rss_kb / 1024.0, 2)


def wait_for_cuda(attempts: int = 5, sleep_seconds: float = 2.0) -> bool:
    for attempt in range(1, attempts + 1):
        available = torch.cuda.is_available()
        print(
            json.dumps(
                {
                    "cuda_probe_attempt": attempt,
                    "cuda_available": bool(available),
                    "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                },
                ensure_ascii=True,
            ),
            flush=True,
        )
        if available:
            return True
        if attempt < attempts:
            time.sleep(sleep_seconds)
    return False


def main() -> None:
    args = build_parser().parse_args()
    run_config = load_run_config(args.run_config)

    dataset_id = str(coalesce_arg(None, run_config, "dataset_id", "replogle_2022_k562_essential"))
    model_id = str(coalesce_arg(None, run_config, "model_id", "gears_stage1a_formal"))
    formal_h5ad_path = resolve_path(coalesce_arg(None, run_config, "formal_h5ad_path", None))
    gears_cache_dir = resolve_path(coalesce_arg(None, run_config, "gears_cache_dir", None))
    device = str(coalesce_arg(args.device, run_config, "device", "cuda" if torch.cuda.is_available() else "cpu"))
    epochs = int(coalesce_arg(args.epochs, run_config, "epochs", 1))
    batch_size = int(coalesce_arg(args.batch_size, run_config, "batch_size", 32))
    seed = int(coalesce_arg(None, run_config, "seed", 123))
    lr = float(coalesce_arg(None, run_config, "lr", 1e-3))
    weight_decay = float(coalesce_arg(None, run_config, "weight_decay", 5e-4))
    train_val_fraction = float(coalesce_arg(None, run_config, "train_val_fraction", 0.875))
    max_control_cells = coalesce_arg(None, run_config, "max_control_cells", 2048)
    max_cells_per_train_condition = coalesce_arg(None, run_config, "max_cells_per_train_condition", None)
    perturbation_graph_k = int(coalesce_arg(None, run_config, "perturbation_graph_k", 8))

    if formal_h5ad_path is None or gears_cache_dir is None:
        raise ValueError("run-config 缺少 formal_h5ad_path 或 gears_cache_dir。")
    if device.startswith("cuda") and not wait_for_cuda():
        raise ValueError(f"请求 device={device}，但当前环境不可用 CUDA。")

    set_random_seed(seed)
    rng = np.random.default_rng(seed)
    dataset_contract = get_formal_dataset_contract(dataset_id)

    prep_start = time.perf_counter()
    formal_adata = ad.read_h5ad(formal_h5ad_path)
    try:
        heldout_target_order, _ = load_frozen_prediction_space(dataset_id)
        heldout_targets = set(heldout_target_order)
        obs = formal_adata.obs.copy()
        obs["is_control"] = obs["is_control"].astype(bool)
        obs["target_gene"] = obs["target_gene"].astype("string").fillna("")
        perturbation_genes = sorted(set(obs.loc[~obs["is_control"], "target_gene"].tolist()))
        train_adata, train_targets = build_gears_input_adata(
            formal_adata=formal_adata,
            heldout_targets=heldout_targets,
            rng=rng,
            max_control_cells=max_control_cells,
            max_cells_per_train_condition=max_cells_per_train_condition,
            cell_type_label=dataset_contract.cell_line,
        )
    finally:
        del formal_adata
    prep_seconds = round(time.perf_counter() - prep_start, 3)

    io_start = time.perf_counter()
    write_fake_gene2go(gears_cache_dir, perturbation_genes)
    gene_set_path = write_gene_set(gears_cache_dir, perturbation_genes)
    split_path = gears_cache_dir / "custom_split.pkl"
    train_conditions = sorted(train_adata.obs["condition"].astype(str).unique().tolist())
    split_payload = build_split_file(split_path, train_conditions, seed, train_val_fraction)
    with split_path.open("rb") as handle:
        pickle.load(handle)
    io_seconds = round(time.perf_counter() - io_start, 3)

    pert_data = PertData(str(gears_cache_dir), gene_set_path=str(gene_set_path), default_pert_graph=False)
    data_start = time.perf_counter()
    pert_data.new_data_process(dataset_name=f"{dataset_id}_{model_id}", adata=train_adata, skip_calc_de=False)
    pert_data.prepare_split(split="custom", split_dict_path=str(split_path))
    effective_batch_size = min(batch_size, max(1, train_adata.n_obs))
    pert_data.get_dataloader(batch_size=effective_batch_size, test_batch_size=effective_batch_size)
    pert_data.dataloader.pop("test_loader", None)
    dataloader_seconds = round(time.perf_counter() - data_start, 3)

    perturbation_edge_index, perturbation_edge_weight = build_local_perturbation_graph(
        control_matrix=train_adata.X[train_adata.obs["condition"].astype(str).eq("ctrl").to_numpy()],
        control_gene_names=train_adata.var["gene_name"].astype(str).tolist(),
        perturbation_genes=pert_data.pert_names.astype(str).tolist(),
        k=perturbation_graph_k,
    )
    gene_edge_index, gene_edge_weight = build_identity_graph(train_adata.n_vars)

    gears_model = GEARS(pert_data, device=device, weight_bias_track=False)
    gears_model.model_initialize(
        G_go=perturbation_edge_index,
        G_go_weight=perturbation_edge_weight,
        G_coexpress=gene_edge_index,
        G_coexpress_weight=gene_edge_weight,
    )
    gears_model.model = gears_model.model.to(device)

    optimizer = Adam(gears_model.model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = StepLR(optimizer, step_size=1, gamma=0.5)
    train_loader = pert_data.dataloader["train_loader"]
    val_loader = pert_data.dataloader["val_loader"]

    if device.startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()

    epoch_rows: list[dict[str, object]] = []
    train_start = time.perf_counter()
    for epoch in range(1, epochs + 1):
        epoch_start = time.perf_counter()
        batch_count = 0
        gears_model.model.train()
        for batch in train_loader:
            batch_count += 1
            batch.to(device)
            optimizer.zero_grad()
            y = batch.y
            if gears_model.config["uncertainty"]:
                pred, logvar = gears_model.model(batch)
                loss = uncertainty_loss_fct(
                    pred,
                    logvar,
                    y,
                    batch.pert,
                    reg=gears_model.config["uncertainty_reg"],
                    ctrl=gears_model.ctrl_expression,
                    dict_filter=gears_model.dict_filter,
                    direction_lambda=gears_model.config["direction_lambda"],
                )
            else:
                pred = gears_model.model(batch)
                loss = loss_fct(
                    pred,
                    y,
                    batch.pert,
                    ctrl=gears_model.ctrl_expression,
                    dict_filter=gears_model.dict_filter,
                    direction_lambda=gears_model.config["direction_lambda"],
                )
            loss.backward()
            optimizer.step()

        scheduler.step()
        train_res = evaluate(train_loader, gears_model.model, gears_model.config["uncertainty"], device)
        val_res = evaluate(val_loader, gears_model.model, gears_model.config["uncertainty"], device)
        train_metrics, _ = compute_metrics(train_res)
        val_metrics, _ = compute_metrics(val_res)

        gpu_stats = get_nvml_snapshot() if device.startswith("cuda") else {}
        if device.startswith("cuda"):
            gpu_stats.setdefault("torch_peak_mem_mb", round(torch.cuda.max_memory_allocated() / (1024**2), 2))
            gpu_stats.setdefault("torch_reserved_mem_mb", round(torch.cuda.max_memory_reserved() / (1024**2), 2))

        row = {
            "epoch": epoch,
            "epoch_seconds": round(time.perf_counter() - epoch_start, 3),
            "train_mse": float(train_metrics["mse"]),
            "val_mse": float(val_metrics["mse"]),
            "train_mse_de": float(train_metrics["mse_de"]),
            "val_mse_de": float(val_metrics["mse_de"]),
            "batch_count": batch_count,
            "cpu_max_rss_mb": cpu_mem_mb(),
            **gpu_stats,
        }
        print(json.dumps(row, ensure_ascii=True), flush=True)
        epoch_rows.append(row)

    summary = {
        "dataset_id": dataset_id,
        "model_id": model_id,
        "device": device,
        "seed": seed,
        "requested_batch_size": batch_size,
        "effective_batch_size": effective_batch_size,
        "epochs": epochs,
        "prep_seconds": prep_seconds,
        "dataloader_seconds": dataloader_seconds,
        "io_seconds": io_seconds,
        "train_total_seconds": round(time.perf_counter() - train_start, 3),
        "train_cells": int(train_adata.n_obs),
        "train_targets": len(train_targets),
        "split_train_conditions": len(split_payload["train"]),
        "split_val_conditions": len(split_payload["val"]),
        "epoch_rows": epoch_rows,
    }
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"wrote {output_path}", flush=True)


if __name__ == "__main__":
    main()
