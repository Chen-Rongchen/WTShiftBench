from __future__ import annotations

from scripts.cuda_env_probe import emit_cuda_env_probe

emit_cuda_env_probe("gears/build_predictions.py:pre_import")

import argparse
import hashlib
import json
import pickle
import random
import time
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from torch_geometric.data import DataLoader

from gears import GEARS, PertData
from gears.utils import create_cell_graph_dataset_for_prediction

from scripts.stage1a.adapters.common.runtime import (
    PROJECT_ROOT,
    coalesce_arg,
    load_frozen_prediction_space,
    load_run_config,
    mean_expression,
    resolve_path,
)
from scripts.stage1a.benchmark_invariant.catalog import get_formal_dataset_contract
from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    json_dump,
    resolve_project_relative,
    write_matrix,
)


DEFAULT_RAW_PREDICTION_ROOT = PROJECT_ROOT / "data/predictions/stage1a_gears_raw"
DEFAULT_GEARS_CACHE_ROOT = PROJECT_ROOT / "tmp/stage1a_gears"
DEFAULT_MODEL_ID = "gears_stage1a_formal"
GEARS_DATASET_CACHE_SIGNATURE = "adapter_cache_signature.json"


def log_stage(stage: str, **fields: object) -> None:
    suffix = ""
    if fields:
        rendered = ", ".join(f"{key}={value}" for key, value in fields.items())
        suffix = f" | {rendered}"
    print(f"[gears-stage] {stage}{suffix}", flush=True)


def log_stage_timing(stage: str, started_at: float, **fields: object) -> None:
    log_stage(stage, elapsed_seconds=round(time.perf_counter() - started_at, 3), **fields)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="为 Stage 1A formal dataset 构造 GEARS predicted_shift.tsv.gz。"
    )
    parser.add_argument("--run-config")
    parser.add_argument("--dataset-id")
    parser.add_argument("--model-id")
    parser.add_argument("--formal-h5ad-path")
    parser.add_argument("--prediction-path")
    parser.add_argument("--metadata-path")
    parser.add_argument("--gears-cache-dir")
    parser.add_argument("--device")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--lr", type=float)
    parser.add_argument("--weight-decay", type=float)
    parser.add_argument("--train-val-fraction", type=float)
    parser.add_argument("--max-control-cells", type=int)
    parser.add_argument("--max-cells-per-train-condition", type=int)
    parser.add_argument("--prediction-num-samples", type=int)
    parser.add_argument("--perturbation-graph-k", type=int)
    return parser


def set_random_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def sample_indices(indices: np.ndarray, max_cells: int | None, rng: np.random.Generator) -> np.ndarray:
    if max_cells is None or len(indices) <= max_cells:
        return indices
    chosen = rng.choice(indices, size=max_cells, replace=False)
    return np.sort(chosen)


def build_gears_input_adata(
    formal_adata,
    heldout_targets: set[str],
    rng: np.random.Generator,
    max_control_cells: int | None,
    max_cells_per_train_condition: int | None,
    cell_type_label: str,
):
    obs = formal_adata.obs.copy()
    obs["target_gene"] = obs["target_gene"].astype("string").fillna("")
    obs["is_control"] = obs["is_control"].astype(bool)

    controls_idx = np.flatnonzero(obs["is_control"].to_numpy())
    train_pert_idx: list[int] = []

    non_control = obs.loc[~obs["is_control"], "target_gene"].astype("string")
    observed_targets = sorted(target for target in non_control.unique().tolist() if target)
    train_targets = [target for target in observed_targets if target not in heldout_targets]
    if not train_targets:
        raise ValueError("held-out target 集合覆盖了所有 perturbation，GEARS 无训练目标。")

    for target in train_targets:
        target_idx = np.flatnonzero((~obs["is_control"]).to_numpy() & obs["target_gene"].eq(target).to_numpy())
        sampled = sample_indices(target_idx, max_cells_per_train_condition, rng)
        train_pert_idx.extend(sampled.tolist())

    sampled_controls = sample_indices(controls_idx, max_control_cells, rng)
    selected_idx = np.sort(np.concatenate([sampled_controls, np.asarray(train_pert_idx, dtype=int)]))
    train_adata = formal_adata[selected_idx, :].copy()

    train_obs = train_adata.obs.copy()
    condition = np.where(
        train_obs["is_control"].to_numpy(),
        "ctrl",
        train_obs["target_gene"].astype("string").to_numpy() + "+ctrl",
    )
    train_obs["condition"] = pd.Categorical(condition)
    train_obs["cell_type"] = pd.Categorical([cell_type_label] * train_adata.n_obs)
    train_adata.obs = train_obs
    train_adata.var = train_adata.var.copy()
    train_adata.var["gene_name"] = train_adata.var.index.astype(str)
    if not sparse.issparse(train_adata.X):
        train_adata.X = sparse.csr_matrix(train_adata.X)

    return train_adata, train_targets


def write_fake_gene2go(cache_dir: Path, perturbation_genes: list[str]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    gene2go_path = cache_dir / "gene2go_all.pkl"
    if gene2go_path.exists():
        return
    payload = {gene: [f"local_fake_go::{gene}"] for gene in perturbation_genes}
    with gene2go_path.open("wb") as handle:
        pickle.dump(payload, handle)


def write_gene_set(cache_dir: Path, perturbation_genes: list[str]) -> Path:
    gene_set_path = cache_dir / "perturbation_genes.pkl"
    with gene_set_path.open("wb") as handle:
        pickle.dump(sorted(set(perturbation_genes)), handle)
    return gene_set_path


def build_identity_graph(node_count: int) -> tuple[torch.Tensor, torch.Tensor]:
    indices = torch.arange(node_count, dtype=torch.long)
    edge_index = torch.stack([indices, indices], dim=0)
    edge_weight = torch.ones(node_count, dtype=torch.float32)
    return edge_index, edge_weight


def build_local_perturbation_graph(
    control_matrix,
    control_gene_names: list[str],
    perturbation_genes: list[str],
    k: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    gene_to_index = {gene: idx for idx, gene in enumerate(control_gene_names)}
    present_genes = [gene for gene in perturbation_genes if gene in gene_to_index]
    node_map = {gene: idx for idx, gene in enumerate(perturbation_genes)}
    if not present_genes:
        return build_identity_graph(len(perturbation_genes))

    target_indices = [gene_to_index[gene] for gene in present_genes]
    if sparse.issparse(control_matrix):
        target_values = control_matrix[:, target_indices].toarray()
    else:
        target_values = np.asarray(control_matrix[:, target_indices])

    corr = np.corrcoef(target_values, rowvar=False)
    corr = np.nan_to_num(np.abs(corr), nan=0.0)
    np.fill_diagonal(corr, 1.0)
    neighbor_count = max(1, min(k, corr.shape[0]))

    edge_rows: list[int] = []
    edge_cols: list[int] = []
    edge_weights: list[float] = []

    for target_pos, target_gene in enumerate(present_genes):
        neighbor_idx = np.argpartition(corr[:, target_pos], -neighbor_count)[-neighbor_count:]
        for source_pos in neighbor_idx.tolist():
            edge_rows.append(node_map[present_genes[source_pos]])
            edge_cols.append(node_map[target_gene])
            edge_weights.append(float(corr[source_pos, target_pos]))

    for perturbation_gene in perturbation_genes:
        node_id = node_map[perturbation_gene]
        edge_rows.append(node_id)
        edge_cols.append(node_id)
        edge_weights.append(1.0)

    edge_index = torch.tensor([edge_rows, edge_cols], dtype=torch.long)
    edge_weight = torch.tensor(edge_weights, dtype=torch.float32)
    return edge_index, edge_weight


def build_split_file(
    split_path: Path,
    train_conditions: list[str],
    seed: int,
    train_val_fraction: float,
    val_conditions: list[str] | None = None,
) -> dict[str, list[str]]:
    train_only = [condition for condition in train_conditions if condition != "ctrl"]
    if len(train_only) < 2:
        raise ValueError("可用于训练的 perturbation condition 少于 2，无法稳定构造 train/val split。")

    if val_conditions is None:
        rng = np.random.default_rng(seed)
        shuffled = np.asarray(train_only, dtype=object)
        rng.shuffle(shuffled)
        val_count = max(1, int(round(len(shuffled) * (1.0 - train_val_fraction))))
        val_conditions = shuffled[:val_count].tolist()
        actual_train_conditions = shuffled[val_count:].tolist()
        if not actual_train_conditions:
            actual_train_conditions = val_conditions[:1]
            val_conditions = val_conditions[1:] or actual_train_conditions[:1]
    else:
        explicit_val = [condition for condition in val_conditions if condition in train_only]
        actual_train_conditions = [condition for condition in train_only if condition not in set(explicit_val)]
        if not explicit_val or not actual_train_conditions:
            raise ValueError("显式 val_conditions 必须在 train_conditions 内，且 inner_train/inner_val 都不能为空。")
        val_conditions = explicit_val

    payload = {
        "train": ["ctrl", *actual_train_conditions],
        "val": val_conditions,
        "test": [],
    }
    split_path.parent.mkdir(parents=True, exist_ok=True)
    with split_path.open("wb") as handle:
        pickle.dump(payload, handle)
    return payload


def stable_digest(values: list[str]) -> str:
    payload = "\n".join(values).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_dataset_cache_signature(
    *,
    dataset_id: str,
    model_id: str,
    formal_h5ad_path: Path,
    seed: int,
    max_control_cells: int | None,
    max_cells_per_train_condition: int | None,
    train_adata,
    train_targets: list[str],
    heldout_target_order: list[str],
) -> dict[str, object]:
    condition_values = train_adata.obs["condition"].astype(str)
    ctrl_mask = condition_values.eq("ctrl")
    return {
        "dataset_id": dataset_id,
        "model_id": model_id,
        "formal_h5ad_path": resolve_project_relative(formal_h5ad_path),
        "seed": seed,
        "max_control_cells": max_control_cells,
        "max_cells_per_train_condition": max_cells_per_train_condition,
        "train_n_obs": int(train_adata.n_obs),
        "train_n_vars": int(train_adata.n_vars),
        "train_condition_count": int(condition_values.nunique()),
        "train_ctrl_cells": int(ctrl_mask.sum()),
        "train_targets_sha256": stable_digest(train_targets),
        "heldout_targets_sha256": stable_digest(heldout_target_order),
    }


def read_dataset_cache_signature(signature_path: Path) -> dict[str, object] | None:
    if not signature_path.exists():
        return None
    payload = json.loads(signature_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{signature_path} 必须是 JSON object。")
    return payload


def cached_dataset_matches_signature(
    dataset_dir: Path,
    expected_signature: dict[str, object],
) -> bool:
    cached_h5ad_path = dataset_dir / "perturb_processed.h5ad"
    cached_pyg_path = dataset_dir / "data_pyg" / "cell_graphs.pkl"
    if not cached_h5ad_path.exists() or not cached_pyg_path.exists():
        return False

    signature_path = dataset_dir / GEARS_DATASET_CACHE_SIGNATURE
    cached_signature = read_dataset_cache_signature(signature_path)
    if cached_signature is not None:
        return cached_signature == expected_signature

    cached_adata = ad.read_h5ad(cached_h5ad_path, backed="r")
    try:
        cached_condition_values = cached_adata.obs["condition"].astype(str)
        cached_ctrl_cells = int(cached_condition_values.eq("ctrl").sum())
        cached_condition_count = int(cached_condition_values.nunique())
        return (
            int(cached_adata.n_obs) == int(expected_signature["train_n_obs"])
            and int(cached_adata.n_vars) == int(expected_signature["train_n_vars"])
            and cached_condition_count == int(expected_signature["train_condition_count"])
            and cached_ctrl_cells == int(expected_signature["train_ctrl_cells"])
        )
    finally:
        cached_adata.file.close()


def write_dataset_cache_signature(dataset_dir: Path, signature: dict[str, object]) -> None:
    json_dump(signature, dataset_dir / GEARS_DATASET_CACHE_SIGNATURE)


def predict_transcriptomes(
    gears_model: GEARS,
    target_order: list[str],
    num_samples: int,
    device: str,
) -> dict[str, np.ndarray]:
    gears_model.best_model = gears_model.best_model.to(device)
    gears_model.best_model.eval()
    predictions: dict[str, np.ndarray] = {}

    for target_gene in target_order:
        cell_graphs = create_cell_graph_dataset_for_prediction(
            [target_gene],
            gears_model.ctrl_adata,
            gears_model.pert_list,
            device,
            num_samples=num_samples,
        )
        loader = DataLoader(cell_graphs, batch_size=min(num_samples, 64), shuffle=False)
        batches: list[np.ndarray] = []
        for batch in loader:
            batch.to(device)
            with torch.no_grad():
                pred = gears_model.best_model(batch)
            batches.append(pred.detach().cpu().numpy())
        predictions[target_gene] = np.concatenate(batches, axis=0).mean(axis=0)
    return predictions


def main() -> None:
    emit_cuda_env_probe("gears/build_predictions.py:entry")
    args = build_parser().parse_args()
    run_config = load_run_config(args.run_config)
    emit_cuda_env_probe("gears/build_predictions.py:after_run_config")
    log_stage("config_load", run_config=args.run_config or "<inline>", has_run_config=bool(args.run_config))

    dataset_id = str(
        coalesce_arg(args.dataset_id, run_config, "dataset_id", "replogle_2022_k562_essential")
    )
    dataset_contract = get_formal_dataset_contract(dataset_id)

    model_id = str(coalesce_arg(args.model_id, run_config, "model_id", DEFAULT_MODEL_ID))
    formal_h5ad_path = resolve_path(
        coalesce_arg(
            args.formal_h5ad_path,
            run_config,
            "formal_h5ad_path",
            dataset_contract.path,
        )
    )
    prediction_path = resolve_path(
        coalesce_arg(
            args.prediction_path,
            run_config,
            "prediction_path",
            DEFAULT_RAW_PREDICTION_ROOT / model_id / dataset_id / "predicted_shift.tsv.gz",
        )
    )
    metadata_path = resolve_path(
        coalesce_arg(
            args.metadata_path,
            run_config,
            "metadata_path",
            prediction_path.with_name("adapter_metadata.json"),
        )
    )
    gears_cache_dir = resolve_path(
        coalesce_arg(
            args.gears_cache_dir,
            run_config,
            "gears_cache_dir",
            DEFAULT_GEARS_CACHE_ROOT / model_id / dataset_id,
        )
    )
    device = str(
        coalesce_arg(
            args.device,
            run_config,
            "device",
            "cuda" if torch.cuda.is_available() else "cpu",
        )
    )
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise ValueError(f"请求 device={device}，但当前环境不可用 CUDA。")
    seed = int(coalesce_arg(args.seed, run_config, "seed", 123))
    epochs = int(coalesce_arg(args.epochs, run_config, "epochs", 1))
    batch_size = int(coalesce_arg(args.batch_size, run_config, "batch_size", 32))
    lr = float(coalesce_arg(args.lr, run_config, "lr", 1e-3))
    weight_decay = float(coalesce_arg(args.weight_decay, run_config, "weight_decay", 5e-4))
    train_val_fraction = float(
        coalesce_arg(args.train_val_fraction, run_config, "train_val_fraction", 0.875)
    )
    max_control_cells = coalesce_arg(args.max_control_cells, run_config, "max_control_cells", 2048)
    max_cells_per_train_condition = coalesce_arg(
        args.max_cells_per_train_condition,
        run_config,
        "max_cells_per_train_condition",
        None,
    )
    prediction_num_samples = int(
        coalesce_arg(args.prediction_num_samples, run_config, "prediction_num_samples", 64)
    )
    perturbation_graph_k = int(
        coalesce_arg(args.perturbation_graph_k, run_config, "perturbation_graph_k", 8)
    )

    set_random_seed(seed)
    rng = np.random.default_rng(seed)
    dataset_load_started_at = time.perf_counter()
    formal_adata = ad.read_h5ad(formal_h5ad_path)
    log_stage(
        "dataset_load",
        elapsed_seconds=round(time.perf_counter() - dataset_load_started_at, 3),
        dataset_id=dataset_id,
        model_id=model_id,
        n_obs=int(formal_adata.n_obs),
        n_vars=int(formal_adata.n_vars),
        device=device,
        seed=seed,
        epochs=epochs,
    )
    try:
        heldout_target_order, common_genes = load_frozen_prediction_space(dataset_id)
        heldout_targets = set(heldout_target_order)
        obs = formal_adata.obs.copy()
        obs["is_control"] = obs["is_control"].astype(bool)
        obs["target_gene"] = obs["target_gene"].astype("string").fillna("")
        non_control_targets = obs.loc[~obs["is_control"], "target_gene"]
        if non_control_targets.eq("").any():
            raise ValueError("formal h5ad 中存在非 control 细胞的空 target_gene。")

        perturbation_genes = sorted(set(non_control_targets.loc[non_control_targets.ne("")].tolist()))
        control_mask_full = formal_adata.obs["is_control"].astype(bool).to_numpy()
        control_values_full = mean_expression(formal_adata.X[control_mask_full])
        control_gene_names = formal_adata.var.index.astype(str).tolist()
        build_gears_input_started_at = time.perf_counter()
        train_adata, train_targets = build_gears_input_adata(
            formal_adata=formal_adata,
            heldout_targets=heldout_targets,
            rng=rng,
            max_control_cells=max_control_cells,
            max_cells_per_train_condition=max_cells_per_train_condition,
            cell_type_label=dataset_contract.cell_line,
        )
        log_stage_timing(
            "build_gears_input_done",
            build_gears_input_started_at,
            train_cells=int(train_adata.n_obs),
            train_targets=len(train_targets),
            heldout_targets=len(heldout_targets),
        )
        overlap_targets = sorted(set(train_targets) & heldout_targets)
        if overlap_targets:
            raise ValueError(f"heldout targets 与 train targets 存在交集: {overlap_targets[:10]}")
    finally:
        del formal_adata

    write_fake_gene2go(gears_cache_dir, perturbation_genes)
    gene_set_path = write_gene_set(gears_cache_dir, perturbation_genes)
    split_path = gears_cache_dir / "custom_split.pkl"
    train_conditions = sorted(train_adata.obs["condition"].astype(str).unique().tolist())
    split_payload = build_split_file(split_path, train_conditions, seed, train_val_fraction)

    pert_data = PertData(str(gears_cache_dir), gene_set_path=str(gene_set_path), default_pert_graph=False)
    gears_dataset_name = f"{dataset_id}_{model_id}"
    gears_dataset_dir = gears_cache_dir / gears_dataset_name
    expected_cache_signature = build_dataset_cache_signature(
        dataset_id=dataset_id,
        model_id=model_id,
        formal_h5ad_path=formal_h5ad_path,
        seed=seed,
        max_control_cells=max_control_cells,
        max_cells_per_train_condition=max_cells_per_train_condition,
        train_adata=train_adata,
        train_targets=train_targets,
        heldout_target_order=heldout_target_order,
    )
    if cached_dataset_matches_signature(gears_dataset_dir, expected_cache_signature):
        reuse_cache_started_at = time.perf_counter()
        log_stage("reuse_processed_cache_start", dataset_dir=gears_dataset_dir)
        pert_data.load(data_path=str(gears_dataset_dir))
        write_dataset_cache_signature(gears_dataset_dir, expected_cache_signature)
        log_stage_timing(
            "reuse_processed_cache_done",
            reuse_cache_started_at,
            pert_count=len(pert_data.pert_names),
            gene_count=int(train_adata.n_vars),
        )
    else:
        new_data_process_started_at = time.perf_counter()
        log_stage("new_data_process_start", cache_dir=gears_cache_dir, dataset_name=gears_dataset_name)
        pert_data.new_data_process(dataset_name=gears_dataset_name, adata=train_adata, skip_calc_de=False)
        write_dataset_cache_signature(gears_dataset_dir, expected_cache_signature)
        log_stage_timing(
            "new_data_process_done",
            new_data_process_started_at,
            pert_count=len(pert_data.pert_names),
            gene_count=int(train_adata.n_vars),
        )
    prepare_split_started_at = time.perf_counter()
    log_stage("prepare_split_start", split_path=split_path)
    pert_data.prepare_split(split="custom", split_dict_path=str(split_path))
    log_stage_timing(
        "prepare_split_done",
        prepare_split_started_at,
        split_train_conditions=len(split_payload["train"]),
        split_val_conditions=len(split_payload["val"]),
    )
    effective_batch_size = min(batch_size, max(1, train_adata.n_obs))
    get_dataloader_started_at = time.perf_counter()
    log_stage("get_dataloader_start", effective_batch_size=effective_batch_size)
    pert_data.get_dataloader(batch_size=effective_batch_size, test_batch_size=effective_batch_size)
    pert_data.dataloader.pop("test_loader", None)
    emit_cuda_env_probe("gears/build_predictions.py:after_dataloader")
    train_loader = pert_data.dataloader["train_loader"]
    val_loader = pert_data.dataloader["val_loader"]
    log_stage(
        "dataloader",
        elapsed_seconds=round(time.perf_counter() - get_dataloader_started_at, 3),
        effective_batch_size=effective_batch_size,
        train_batches=len(train_loader),
        val_batches=len(val_loader),
        train_cells=int(train_adata.n_obs),
        train_targets=len(train_targets),
    )

    perturbation_edge_index, perturbation_edge_weight = build_local_perturbation_graph(
        control_matrix=train_adata.X[train_adata.obs["condition"].astype(str).eq("ctrl").to_numpy()],
        control_gene_names=train_adata.var["gene_name"].astype(str).tolist(),
        perturbation_genes=pert_data.pert_names.astype(str).tolist(),
        k=perturbation_graph_k,
    )
    gene_edge_index, gene_edge_weight = build_identity_graph(train_adata.n_vars)

    model_initialize_started_at = time.perf_counter()
    gears_model = GEARS(pert_data, device=device, weight_bias_track=False)
    emit_cuda_env_probe("gears/build_predictions.py:before_model_initialize")
    gears_model.model_initialize(
        G_go=perturbation_edge_index,
        G_go_weight=perturbation_edge_weight,
        G_coexpress=gene_edge_index,
        G_coexpress_weight=gene_edge_weight,
    )
    log_stage(
        "model_init",
        elapsed_seconds=round(time.perf_counter() - model_initialize_started_at, 3),
        hidden_size=gears_model.config["hidden_size"],
        uncertainty=gears_model.config["uncertainty"],
        device=device,
    )
    log_stage("train_start", epochs=epochs, lr=lr, weight_decay=weight_decay)
    train_started_at = time.perf_counter()
    gears_model.train(epochs=epochs, lr=lr, weight_decay=weight_decay)
    log_stage_timing("train_done", train_started_at, epochs=epochs)

    prediction_started_at = time.perf_counter()
    transcriptome_predictions = predict_transcriptomes(
        gears_model=gears_model,
        target_order=heldout_target_order,
        num_samples=prediction_num_samples,
        device=device,
    )
    log_stage_timing(
        "predict_transcriptomes_done",
        prediction_started_at,
        heldout_targets=len(heldout_target_order),
        prediction_num_samples=prediction_num_samples,
    )

    missing_common_genes = [gene for gene in common_genes if gene not in control_gene_names]
    if missing_common_genes:
        raise ValueError(f"formal h5ad 缺少 common evaluable genes: {missing_common_genes[:10]}")

    gene_index = pd.Index(control_gene_names)
    common_gene_positions = gene_index.get_indexer(common_genes)
    delta_rows = []
    for target_gene in heldout_target_order:
        predicted_expression = transcriptome_predictions[target_gene].astype(np.float64, copy=False)
        predicted_delta = predicted_expression - control_values_full
        delta_rows.append(predicted_delta[common_gene_positions])

    predicted_shift = pd.DataFrame(delta_rows, index=heldout_target_order, columns=common_genes)
    predicted_shift.index.name = "target_gene"
    write_output_started_at = time.perf_counter()
    write_matrix(predicted_shift, prediction_path)
    json_dump(
        {
            "adapter_name": "gears",
            "adapter_method": "GEARS Stage 1A formal perturbation adapter",
            "dataset_id": dataset_id,
            "model_id": model_id,
            "cell_type": dataset_contract.cell_line,
            "prediction_path": resolve_project_relative(prediction_path),
            "device": device,
            "seed": seed,
            "epochs": epochs,
            "batch_size": batch_size,
            "prediction_num_samples": prediction_num_samples,
            "train_targets": len(train_targets),
            "heldout_targets": len(heldout_target_order),
            "train_cells": int(train_adata.n_obs),
        },
        metadata_path,
    )
    log_stage_timing(
        "write_outputs_done",
        write_output_started_at,
        prediction_path=resolve_project_relative(prediction_path),
        metadata_path=resolve_project_relative(metadata_path),
    )

    print(f"已写出: {resolve_project_relative(prediction_path)}")
    print(f"已写出: {resolve_project_relative(metadata_path)}")
    print(f"device: {device}")
    print(f"seed: {seed}")
    print(f"dataset_id: {dataset_id}")
    print(f"cell_type: {dataset_contract.cell_line}")
    print(f"train_targets: {len(train_targets)}")
    print(f"heldout_targets: {len(heldout_target_order)}")
    print(f"train_cells: {train_adata.n_obs}")
    print(f"split_train_conditions: {len(split_payload['train'])}")
    print(f"split_val_conditions: {len(split_payload['val'])}")


if __name__ == "__main__":
    main()
