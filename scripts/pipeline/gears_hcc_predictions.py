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
from wtbench.truth_bridge import (
    build_dataset_specs,
    load_config,
    load_expression_for_called_cells,
    load_single_feature_calls,
    log_normalize_csr,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def log_stage(stage: str, **fields: object) -> None:
    suffix = ""
    if fields:
        suffix = " | " + ", ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[stage2-gears-hcc] {stage}{suffix}", flush=True)


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_recipe(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_matrix(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, sep="\t", index=False)


def write_json(payload: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_stage2_hcc_formal_adata(
    *,
    spec,
    truth_config: dict[str, object],
    frozen_targets: set[str],
) -> tuple[ad.AnnData, list[str], np.ndarray]:
    log_stage("load_calls_start", cell_line=spec.cell_line)
    calls = load_single_feature_calls(spec, control_prefix=str(truth_config["filters"]["control_target_prefix"]))
    log_stage("load_calls_done", cell_line=spec.cell_line, n_calls=int(len(calls)))
    log_stage("load_expression_start", cell_line=spec.cell_line)
    expression, calls, gene_meta = load_expression_for_called_cells(spec, calls)
    log_stage("load_expression_done", cell_line=spec.cell_line, n_obs=int(expression.shape[0]), n_vars=int(expression.shape[1]))
    target_mask = calls["is_control"].to_numpy(dtype=bool) | calls["target_gene"].astype(str).isin(frozen_targets).to_numpy(dtype=bool)
    filtered_calls = calls.loc[target_mask].reset_index(drop=True)
    filtered_expression = expression[target_mask].tocsr()
    log_stage(
        "filter_frozen_targets_done",
        cell_line=spec.cell_line,
        filtered_obs=int(filtered_expression.shape[0]),
        control_cells=int(filtered_calls["is_control"].sum()),
    )

    log_stage("normalize_start", cell_line=spec.cell_line)
    normalized = log_normalize_csr(
        filtered_expression,
        target_sum=float(truth_config["metrics"]["normalization_target_sum"]),
    ).tocsr()
    log_stage("normalize_done", cell_line=spec.cell_line, nnz=int(normalized.nnz))
    obs = filtered_calls.loc[:, ["cell_barcode", "feature_call", "target_gene", "is_control", "num_features", "num_umis"]].copy()
    obs["cell_barcode"] = obs["cell_barcode"].astype(str)
    obs["feature_call"] = obs["feature_call"].astype(str)
    obs["target_gene"] = obs["target_gene"].astype(str)
    obs["is_control"] = obs["is_control"].astype(bool)
    obs.index = obs["cell_barcode"]
    obs.index.name = "obs_id"
    var = pd.DataFrame(index=gene_meta["feature_name"].astype(str))
    var["gene_name"] = var.index.astype(str)
    formal_adata = ad.AnnData(X=normalized, obs=obs, var=var)
    control_values = np.asarray(formal_adata.X[formal_adata.obs["is_control"].to_numpy()].mean(axis=0)).ravel().astype(np.float64)
    target_order = sorted(filtered_calls.loc[~filtered_calls["is_control"], "target_gene"].astype(str).unique().tolist())
    return formal_adata, target_order, control_values


def run_one_cell_line(
    *,
    spec,
    recipe: dict[str, object],
    truth_config: dict[str, object],
    axis_membership: pd.DataFrame,
) -> dict[str, object]:
    runtime = dict(recipe["runtime"])
    model_id = str(recipe["model_id"])
    formal_h5ad_root = resolve_path(str(recipe["formal_h5ad_root"]))
    output_root = resolve_path(str(recipe["output_root"]))
    report_root = resolve_path(str(recipe["report_root"]))
    prediction_path = output_root / model_id / spec.cell_line / "predicted_shift.tsv.gz"
    provenance_path = output_root / model_id / spec.cell_line / "provenance.json"
    cache_dir = PROJECT_ROOT / "tmp" / "stage2_gears_hcc" / model_id / spec.cell_line
    cache_dir.mkdir(parents=True, exist_ok=True)

    target_order, output_genes = expected_target_and_gene_order(axis_membership)
    frozen_targets = set(target_order)
    prebuilt_h5ad_path = formal_h5ad_root / f"{spec.cell_line}.h5ad"
    if prebuilt_h5ad_path.exists():
        log_stage("load_prebuilt_h5ad_start", cell_line=spec.cell_line, path=prebuilt_h5ad_path)
        formal_adata = ad.read_h5ad(prebuilt_h5ad_path)
        train_targets_full = sorted(
            formal_adata.obs.loc[~formal_adata.obs["is_control"].astype(bool), "target_gene"].astype(str).unique().tolist()
        )
        control_values_full = np.asarray(
            formal_adata.X[formal_adata.obs["is_control"].to_numpy()].mean(axis=0)
        ).ravel().astype(np.float64)
        log_stage("load_prebuilt_h5ad_done", cell_line=spec.cell_line, n_obs=int(formal_adata.n_obs), n_vars=int(formal_adata.n_vars))
    else:
        formal_adata, train_targets_full, control_values_full = build_stage2_hcc_formal_adata(
            spec=spec,
            truth_config=truth_config,
            frozen_targets=frozen_targets,
        )
    log_stage(
        "build_formal_adata_done",
        cell_line=spec.cell_line,
        n_obs=int(formal_adata.n_obs),
        n_vars=int(formal_adata.n_vars),
        frozen_targets=len(target_order),
        train_targets_full=len(train_targets_full),
    )

    requested_device = str(runtime.get("device", "auto"))
    device = "cuda" if requested_device == "auto" and torch.cuda.is_available() else "cpu" if requested_device == "auto" else requested_device
    rng = np.random.default_rng(int(runtime["training_seed"]))
    train_adata, train_targets = build_gears_input_adata(
        formal_adata=formal_adata,
        heldout_targets=set(),
        rng=rng,
        max_control_cells=runtime.get("max_control_cells"),
        max_cells_per_train_condition=runtime.get("max_cells_per_train_condition"),
        cell_type_label=spec.cell_line,
    )
    log_stage(
        "build_gears_input_done",
        cell_line=spec.cell_line,
        train_cells=int(train_adata.n_obs),
        train_targets=len(train_targets),
        device=device,
    )
    perturbation_genes = sorted(train_adata.obs.loc[~train_adata.obs["is_control"].astype(bool), "target_gene"].astype(str).unique().tolist())
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
    log_stage(
        "split_ready",
        cell_line=spec.cell_line,
        split_train_conditions=len(split_payload["train"]),
        split_val_conditions=len(split_payload["val"]),
    )

    pert_data = PertData(str(cache_dir), gene_set_path=str(gene_set_path), default_pert_graph=False)
    log_stage("new_data_process_start", cell_line=spec.cell_line, cache_dir=cache_dir)
    pert_data.new_data_process(
        dataset_name=f"{spec.cell_line}_{model_id}",
        adata=train_adata,
        skip_calc_de=False,
    )
    log_stage("new_data_process_done", cell_line=spec.cell_line)
    pert_data.prepare_split(split="custom", split_dict_path=str(split_path))
    effective_batch_size = min(int(runtime["batch_size"]), max(1, train_adata.n_obs))
    pert_data.get_dataloader(batch_size=effective_batch_size, test_batch_size=effective_batch_size)
    pert_data.dataloader.pop("test_loader", None)
    log_stage("dataloader_ready", cell_line=spec.cell_line, effective_batch_size=effective_batch_size)

    perturbation_edge_index, perturbation_edge_weight = build_local_perturbation_graph(
        control_matrix=train_adata.X[train_adata.obs["condition"].astype(str).eq("ctrl").to_numpy()],
        control_gene_names=train_adata.var["gene_name"].astype(str).tolist(),
        perturbation_genes=pert_data.pert_names.astype(str).tolist(),
        k=int(runtime["perturbation_graph_k"]),
    )
    gene_edge_index, gene_edge_weight = build_identity_graph(train_adata.n_vars)
    gears_model = GEARS(pert_data, device=device, weight_bias_track=False)
    log_stage("model_initialize_start", cell_line=spec.cell_line, device=device)
    gears_model.model_initialize(
        G_go=perturbation_edge_index,
        G_go_weight=perturbation_edge_weight,
        G_coexpress=gene_edge_index,
        G_coexpress_weight=gene_edge_weight,
    )
    log_stage("model_initialize_done", cell_line=spec.cell_line)
    log_stage("train_start", cell_line=spec.cell_line, epochs=int(runtime["epochs"]))
    gears_model.train(
        epochs=int(runtime["epochs"]),
        lr=float(runtime["lr"]),
        weight_decay=float(runtime["weight_decay"]),
    )
    log_stage("train_done", cell_line=spec.cell_line)

    log_stage("predict_start", cell_line=spec.cell_line, target_count=len(target_order))
    transcriptome_predictions = predict_transcriptomes(
        gears_model=gears_model,
        target_order=target_order,
        num_samples=int(runtime["prediction_num_samples"]),
        device=device,
    )
    log_stage("predict_done", cell_line=spec.cell_line)
    gene_names = pd.Index(train_adata.var["gene_name"].astype(str).to_numpy())
    gene_position_index = pd.Series(
        np.arange(train_adata.n_vars, dtype=np.int64),
        index=gene_names,
    )
    gene_position_index = gene_position_index[~gene_position_index.index.duplicated(keep="first")]
    missing = [gene for gene in output_genes if gene not in gene_position_index.index]
    if missing:
        raise ValueError(f"{spec.cell_line} 缺少 frozen output genes: {missing}")
    output_gene_positions = gene_position_index.loc[output_genes].to_numpy(dtype=np.int64)

    delta_rows = []
    for target_gene in target_order:
        predicted_expression = transcriptome_predictions[target_gene].astype(np.float64, copy=False)
        predicted_delta = predicted_expression - control_values_full
        delta_rows.append(predicted_delta[output_gene_positions])
    predicted_shift = pd.DataFrame(delta_rows, columns=output_genes)
    predicted_shift.insert(0, "target_gene", target_order)
    write_matrix(predicted_shift, prediction_path)
    log_stage("write_prediction_done", cell_line=spec.cell_line, prediction_path=prediction_path)

    provenance = {
        "stage": "stage2_hcc_gears_raw_output",
        "dataset_role": "primary",
        "cell_line": spec.cell_line,
        "entrant_id": str(recipe["entrant_id"]),
        "entrant_version": str(recipe["entrant_version"]),
        "model_id": model_id,
        "prediction_space": "normalized_log1p_internal_then_predicted_shift",
        "normalization_target_sum": float(truth_config["metrics"]["normalization_target_sum"]),
        "raw_input_source_kind": "mtx_protospacer_single_feature_calls",
        "raw_prediction_path": str(prediction_path.relative_to(PROJECT_ROOT)),
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
            "stage": "stage2_hcc_gears_recipe_run",
            "cell_line": spec.cell_line,
            "prediction_path": str(prediction_path.relative_to(PROJECT_ROOT)),
            "provenance_path": str(provenance_path.relative_to(PROJECT_ROOT)),
        },
        report_root / spec.cell_line / "run_summary.json",
    )
    log_stage("run_complete", cell_line=spec.cell_line)
    return {
        "cell_line": spec.cell_line,
        "prediction_path": str(prediction_path.relative_to(PROJECT_ROOT)),
        "provenance_path": str(provenance_path.relative_to(PROJECT_ROOT)),
        "device": device,
        "train_cells": int(train_adata.n_obs),
        "target_count": len(target_order),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="为 Stage 2 HCC primary mainline 生成 GEARS raw predicted_shift。")
    parser.add_argument("--config", default="configs/gears_hcc_formal_v1.json")
    parser.add_argument("--cell-line", action="append", choices=["HCC38", "HCC1143"])
    return parser


def main() -> None:
    args = build_parser().parse_args()
    recipe = load_recipe(resolve_path(args.config))
    truth_config = load_config(resolve_path(str(recipe["stage2_truth_config_path"])))
    axis_membership = pd.read_csv(resolve_path(str(recipe["axis_membership_path"])), sep="\t")
    selected = set(args.cell_line or [])
    rows: list[dict[str, object]] = []
    for spec in build_dataset_specs(truth_config):
        if selected and spec.cell_line not in selected:
            continue
        rows.append(
            run_one_cell_line(
                spec=spec,
                recipe=recipe,
                truth_config=truth_config,
                axis_membership=axis_membership,
            )
        )
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
