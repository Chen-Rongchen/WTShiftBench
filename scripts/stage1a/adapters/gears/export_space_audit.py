from __future__ import annotations

from scripts.cuda_env_probe import emit_cuda_env_probe

emit_cuda_env_probe("gears/export_space_audit.py:pre_import")

import argparse
import math
import time
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import torch

from gears import GEARS, PertData

from scripts.stage1a.adapters.common.runtime import (
    coalesce_arg,
    load_run_config,
    mean_expression,
    resolve_path,
)
from scripts.stage1a.adapters.gears.build_predictions import (
    DEFAULT_MODEL_ID,
    build_dataset_cache_signature,
    build_gears_input_adata,
    build_identity_graph,
    build_local_perturbation_graph,
    build_split_file,
    cached_dataset_matches_signature,
    predict_transcriptomes,
    set_random_seed,
    write_dataset_cache_signature,
    write_fake_gene2go,
    write_gene_set,
)
from scripts.stage1a.benchmark_invariant.catalog import get_formal_dataset_contract
from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    align_prediction_to_truth,
    json_dump,
    load_main_aligned_truth_entry,
    read_matrix,
    resolve_project_relative,
    write_matrix,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_AUDIT_ROOT = PROJECT_ROOT / "reports/stage1a_audit/gears_export_space"
TRUTH_PSEUDOBULK_ROOT = PROJECT_ROOT / "data/truth/stage1a_pseudobulk_delta"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="导出 GEARS export/truth space 审计矩阵与 summary。")
    parser.add_argument("--run-config", required=True)
    parser.add_argument("--audit-root")
    return parser


def log_stage(stage: str, **fields: object) -> None:
    suffix = ""
    if fields:
        suffix = " | " + ", ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[gears-export-audit] {stage}{suffix}", flush=True)


def wait_for_cuda(attempts: int, sleep_seconds: float) -> bool:
    for attempt in range(1, attempts + 1):
        available = torch.cuda.is_available()
        log_stage(
            "cuda_probe",
            attempt=attempt,
            attempts=attempts,
            cuda_available=bool(available),
        )
        if available:
            return True
        if attempt < attempts:
            time.sleep(sleep_seconds)
    return False


def read_control_truth(dataset_id: str) -> pd.DataFrame:
    truth_root = TRUTH_PSEUDOBULK_ROOT / dataset_id
    control_path = truth_root / "control_pseudobulk.tsv.gz"
    return pd.read_csv(control_path, sep="\t", index_col=0)


def read_perturbed_truth(dataset_id: str) -> pd.DataFrame:
    truth_root = TRUTH_PSEUDOBULK_ROOT / dataset_id
    return pd.read_csv(truth_root / "perturbed_pseudobulk.tsv.gz", sep="\t").set_index("target_gene")


def stats_from_frame(frame: pd.DataFrame) -> dict[str, float | None]:
    values = frame.to_numpy(dtype=np.float64, copy=False).ravel()
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "std": None,
            "abs_median": None,
            "abs_p95": None,
        }
    abs_values = np.abs(finite)
    return {
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
        "median": float(np.median(finite)),
        "std": float(np.std(finite)),
        "abs_median": float(np.median(abs_values)),
        "abs_p95": float(np.quantile(abs_values, 0.95)),
    }


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    if not math.isfinite(numerator) or not math.isfinite(denominator):
        return None
    if denominator == 0.0:
        return None
    return float(numerator / denominator)


def coverage_summary(frame: pd.DataFrame, truth_frame: pd.DataFrame) -> dict[str, object]:
    frame_targets = frame.index.astype(str)
    frame_genes = frame.columns.astype(str)
    truth_targets = truth_frame.index.astype(str)
    truth_genes = truth_frame.columns.astype(str)
    frame_target_set = set(frame_targets)
    frame_gene_set = set(frame_genes)
    truth_target_set = set(truth_targets)
    truth_gene_set = set(truth_genes)
    overlap_targets = [target for target in truth_targets if target in frame_target_set]
    overlap_genes = [gene for gene in truth_genes if gene in frame_gene_set]
    return {
        "n_targets_input": int(len(frame_targets)),
        "n_targets_truth": int(len(truth_targets)),
        "n_targets_overlap_truth": int(len(overlap_targets)),
        "target_coverage_fraction_vs_truth": float(len(overlap_targets) / len(truth_targets))
        if len(truth_targets)
        else None,
        "n_genes_input": int(len(frame_genes)),
        "n_genes_truth": int(len(truth_genes)),
        "n_genes_overlap_truth": int(len(overlap_genes)),
        "gene_coverage_fraction_vs_truth": float(len(overlap_genes) / len(truth_genes))
        if len(truth_genes)
        else None,
    }


def negative_fraction(frame: pd.DataFrame) -> float:
    values = frame.to_numpy(dtype=np.float64, copy=False)
    return float(np.mean(values < 0.0))


def reconstructed_negative_fraction(shift_frame: pd.DataFrame, control_frame: pd.DataFrame) -> float:
    aligned_control = control_frame.loc[:, shift_frame.columns]
    reconstructed = shift_frame.add(aligned_control.iloc[0], axis=1)
    return negative_fraction(reconstructed)


def build_layer_summary(
    *,
    layer_name: str,
    frame: pd.DataFrame,
    truth_reference: pd.DataFrame,
    matrix_path: Path,
    negative_fraction_value: float,
) -> dict[str, object]:
    frame_stats = stats_from_frame(frame)
    truth_overlap = truth_reference.loc[
        [target for target in truth_reference.index.astype(str) if target in set(frame.index.astype(str))],
        [gene for gene in truth_reference.columns.astype(str) if gene in set(frame.columns.astype(str))],
    ].copy()
    truth_stats = stats_from_frame(truth_overlap)
    return {
        "layer_name": layer_name,
        "matrix_path": resolve_project_relative(matrix_path),
        **coverage_summary(frame, truth_reference),
        **frame_stats,
        "scale_ratio_vs_truth": safe_ratio(frame_stats["abs_p95"], truth_stats["abs_p95"]),
        "truth_abs_median_on_overlap": truth_stats["abs_median"],
        "truth_abs_p95_on_overlap": truth_stats["abs_p95"],
        "reconstructed_expression_negative_fraction": negative_fraction_value,
    }


def main() -> None:
    emit_cuda_env_probe("gears/export_space_audit.py:entry")
    args = build_parser().parse_args()
    run_config = load_run_config(args.run_config)

    dataset_id = str(coalesce_arg(None, run_config, "dataset_id", "replogle_2022_k562_essential"))
    model_id = str(coalesce_arg(None, run_config, "model_id", DEFAULT_MODEL_ID))
    dataset_contract = get_formal_dataset_contract(dataset_id)

    formal_h5ad_path = resolve_path(
        coalesce_arg(None, run_config, "formal_h5ad_path", dataset_contract.path)
    )
    existing_prediction_path = resolve_path(
        coalesce_arg(None, run_config, "prediction_path", None)
    )
    gears_cache_dir = resolve_path(coalesce_arg(None, run_config, "gears_cache_dir", None))
    device = str(coalesce_arg(None, run_config, "device", "cuda" if torch.cuda.is_available() else "cpu"))
    seed = int(coalesce_arg(None, run_config, "seed", 123))
    epochs = int(coalesce_arg(None, run_config, "epochs", 1))
    batch_size = int(coalesce_arg(None, run_config, "batch_size", 32))
    lr = float(coalesce_arg(None, run_config, "lr", 1e-3))
    weight_decay = float(coalesce_arg(None, run_config, "weight_decay", 5e-4))
    train_val_fraction = float(coalesce_arg(None, run_config, "train_val_fraction", 0.875))
    max_control_cells = coalesce_arg(None, run_config, "max_control_cells", 2048)
    max_cells_per_train_condition = coalesce_arg(None, run_config, "max_cells_per_train_condition", None)
    prediction_num_samples = int(coalesce_arg(None, run_config, "prediction_num_samples", 64))
    perturbation_graph_k = int(coalesce_arg(None, run_config, "perturbation_graph_k", 8))
    cuda_probe_attempts = int(coalesce_arg(None, run_config, "cuda_probe_attempts", 8))
    cuda_probe_sleep_seconds = float(coalesce_arg(None, run_config, "cuda_probe_sleep_seconds", 2.0))
    reuse_existing_prediction = bool(coalesce_arg(None, run_config, "reuse_existing_prediction", True))

    if gears_cache_dir is None and not (reuse_existing_prediction and existing_prediction_path and existing_prediction_path.exists()):
        raise ValueError("run-config 缺少 gears_cache_dir。")
    requested_device = device
    if device.startswith("cuda") and not wait_for_cuda(cuda_probe_attempts, cuda_probe_sleep_seconds):
        log_stage(
            "cuda_unavailable_fallback_cpu",
            requested_device=requested_device,
            fallback_device="cpu",
        )
        device = "cpu"

    audit_root_base = resolve_path(
        coalesce_arg(args.audit_root, run_config, "audit_root", DEFAULT_AUDIT_ROOT)
    )
    assert audit_root_base is not None
    audit_root = audit_root_base / model_id / dataset_id
    audit_root.mkdir(parents=True, exist_ok=True)

    predicted_expression_raw_path = audit_root / "predicted_expression_raw.tsv.gz"
    control_values_full_path = audit_root / "control_values_full.tsv.gz"
    predicted_shift_pre_align_path = audit_root / "predicted_shift_pre_align.tsv.gz"
    predicted_shift_aligned_path = audit_root / "predicted_shift_aligned.tsv.gz"
    summary_path = audit_root / "export_space_audit_summary.json"

    set_random_seed(seed)
    rng = np.random.default_rng(seed)

    log_stage("dataset_load_start", dataset_id=dataset_id, model_id=model_id)
    started_at = time.perf_counter()
    formal_adata = ad.read_h5ad(formal_h5ad_path)
    log_stage(
        "dataset_load_done",
        elapsed_seconds=round(time.perf_counter() - started_at, 3),
        n_obs=int(formal_adata.n_obs),
        n_vars=int(formal_adata.n_vars),
    )
    try:
        truth = read_matrix(load_main_aligned_truth_entry(dataset_id).path)
        control_truth = read_control_truth(dataset_id)
        perturbed_truth = read_perturbed_truth(dataset_id)
        heldout_target_order = truth.index.astype(str).tolist()
        truth_genes = truth.columns.astype(str).tolist()
        heldout_targets = set(heldout_target_order)

        obs = formal_adata.obs.copy()
        obs["is_control"] = obs["is_control"].astype(bool)
        obs["target_gene"] = obs["target_gene"].astype("string").fillna("")
        perturbation_genes = sorted(set(obs.loc[~obs["is_control"], "target_gene"].tolist()))

        control_mask_full = obs["is_control"].to_numpy()
        control_values_full = mean_expression(formal_adata.X[control_mask_full])
        control_gene_names = formal_adata.var.index.astype(str).tolist()
        control_gene_index = pd.Index(control_gene_names)

        observed_targets = sorted(
            target
            for target in obs.loc[~obs["is_control"], "target_gene"].dropna().astype(str).unique().tolist()
            if target
        )
        train_targets = [target for target in observed_targets if target not in heldout_targets]
        train_cells_estimate = int(
            control_mask_full.sum()
            + obs.loc[~obs["is_control"], "target_gene"].isin(train_targets).sum()
        )
    finally:
        del formal_adata

    control_values_full_frame = pd.DataFrame(
        [control_values_full.astype(np.float64, copy=False)],
        index=["control"],
        columns=control_gene_names,
    )
    control_values_full_frame.index.name = "target_gene"
    split_payload = {"train": [], "val": []}

    if reuse_existing_prediction and existing_prediction_path and existing_prediction_path.exists():
        log_stage(
            "reuse_existing_prediction_start",
            prediction_path=resolve_project_relative(existing_prediction_path),
        )
        predicted_shift_pre_align = read_matrix(existing_prediction_path)
        predicted_expression_raw = predicted_shift_pre_align.add(control_values_full_frame.iloc[0], axis=1)
        predicted_expression_raw.index.name = "target_gene"
        audit_execution_mode = "reuse_existing_prediction_plus_control_reconstruction"
        log_stage("reuse_existing_prediction_done", heldout_targets=len(predicted_shift_pre_align.index))
    else:
        formal_adata = ad.read_h5ad(formal_h5ad_path)
        try:
            train_adata, train_targets = build_gears_input_adata(
                formal_adata=formal_adata,
                heldout_targets=heldout_targets,
                rng=rng,
                max_control_cells=max_control_cells,
                max_cells_per_train_condition=max_cells_per_train_condition,
                cell_type_label=dataset_contract.cell_line,
            )
            train_cells_estimate = int(train_adata.n_obs)
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
            log_stage("reuse_processed_cache_start", dataset_dir=resolve_project_relative(gears_dataset_dir))
            pert_data.load(data_path=str(gears_dataset_dir))
            write_dataset_cache_signature(gears_dataset_dir, expected_cache_signature)
            log_stage("reuse_processed_cache_done", pert_count=len(pert_data.pert_names))
        else:
            log_stage("new_data_process_start", dataset_name=gears_dataset_name)
            pert_data.new_data_process(dataset_name=gears_dataset_name, adata=train_adata, skip_calc_de=False)
            write_dataset_cache_signature(gears_dataset_dir, expected_cache_signature)
            log_stage("new_data_process_done", pert_count=len(pert_data.pert_names))

        pert_data.prepare_split(split="custom", split_dict_path=str(split_path))
        effective_batch_size = min(batch_size, max(1, train_adata.n_obs))
        pert_data.get_dataloader(batch_size=effective_batch_size, test_batch_size=effective_batch_size)
        pert_data.dataloader.pop("test_loader", None)

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
        log_stage("train_start", epochs=epochs, lr=lr, weight_decay=weight_decay)
        gears_model.train(epochs=epochs, lr=lr, weight_decay=weight_decay)
        log_stage("train_done", epochs=epochs)

        transcriptome_predictions = predict_transcriptomes(
            gears_model=gears_model,
            target_order=heldout_target_order,
            num_samples=prediction_num_samples,
            device=device,
        )

        predicted_expression_raw = pd.DataFrame.from_dict(
            {
                target: transcriptome_predictions[target].astype(np.float64, copy=False)
                for target in heldout_target_order
            },
            orient="index",
            columns=control_gene_names,
        )
        predicted_expression_raw.index.name = "target_gene"
        predicted_shift_pre_align = predicted_expression_raw.subtract(control_values_full_frame.iloc[0], axis=1)
        predicted_shift_pre_align.index.name = "target_gene"
        audit_execution_mode = "full_model_rerun"

    aligned_prediction, alignment_summary, _ = align_prediction_to_truth(
        prediction=predicted_shift_pre_align,
        truth=truth,
        dataset_id=dataset_id,
        model_id=model_id,
        prediction_path=predicted_shift_pre_align_path,
        output_path=predicted_shift_aligned_path,
        prediction_space=str(coalesce_arg(None, run_config, "prediction_space", "X_pseudobulk_delta")),
        allow_missing_targets=bool(coalesce_arg(None, run_config, "allow_missing_targets", True)),
        allow_missing_genes=bool(coalesce_arg(None, run_config, "allow_missing_genes", True)),
    )

    write_matrix(predicted_expression_raw, predicted_expression_raw_path)
    write_matrix(control_values_full_frame, control_values_full_path)
    write_matrix(predicted_shift_pre_align, predicted_shift_pre_align_path)
    write_matrix(aligned_prediction, predicted_shift_aligned_path)

    truth_gene_positions = control_gene_index.get_indexer(truth.columns)
    if (truth_gene_positions < 0).any():
        missing = [truth.columns[i] for i, pos in enumerate(truth_gene_positions) if pos < 0][:10]
        raise ValueError(f"formal source 缺少 truth genes: {missing}")
    control_values_truth_frame = pd.DataFrame(
        [control_values_full[truth_gene_positions].astype(np.float64, copy=False)],
        index=["control"],
        columns=truth.columns.astype(str),
    )
    control_values_truth_frame.index.name = "target_gene"

    layer_summaries = {
        "predicted_expression_raw": build_layer_summary(
            layer_name="predicted_expression_raw",
            frame=predicted_expression_raw,
            truth_reference=perturbed_truth,
            matrix_path=predicted_expression_raw_path,
            negative_fraction_value=negative_fraction(predicted_expression_raw),
        ),
        "control_values_full": build_layer_summary(
            layer_name="control_values_full",
            frame=control_values_full_frame,
            truth_reference=control_truth,
            matrix_path=control_values_full_path,
            negative_fraction_value=negative_fraction(control_values_full_frame),
        ),
        "predicted_shift_pre_align": build_layer_summary(
            layer_name="predicted_shift_pre_align",
            frame=predicted_shift_pre_align,
            truth_reference=truth,
            matrix_path=predicted_shift_pre_align_path,
            negative_fraction_value=reconstructed_negative_fraction(
                predicted_shift_pre_align.loc[:, truth.columns.astype(str)],
                control_values_truth_frame,
            ),
        ),
        "predicted_shift_aligned": build_layer_summary(
            layer_name="predicted_shift_aligned",
            frame=aligned_prediction,
            truth_reference=truth,
            matrix_path=predicted_shift_aligned_path,
            negative_fraction_value=reconstructed_negative_fraction(
                aligned_prediction,
                control_values_truth_frame,
            ),
        ),
    }

    overlap_pre_align = predicted_shift_pre_align.loc[truth.index.astype(str), truth.columns.astype(str)]
    alignment_delta = aligned_prediction - overlap_pre_align
    alignment_delta_values = np.abs(alignment_delta.to_numpy(dtype=np.float64, copy=False))

    summary = {
        "stage": "gears_export_space_audit",
        "dataset_id": dataset_id,
        "model_id": model_id,
        "device": device,
        "requested_device": requested_device,
        "seed": seed,
        "epochs": epochs,
        "train_cells": int(train_cells_estimate),
        "train_targets": int(len(train_targets)),
        "heldout_targets": int(len(heldout_target_order)),
        "split_train_conditions": int(len(split_payload["train"])),
        "split_val_conditions": int(len(split_payload["val"])),
        "formal_h5ad_path": resolve_project_relative(formal_h5ad_path),
        "truth_path": resolve_project_relative(load_main_aligned_truth_entry(dataset_id).path),
        "control_truth_path": resolve_project_relative(TRUTH_PSEUDOBULK_ROOT / dataset_id / "control_pseudobulk.tsv.gz"),
        "perturbed_truth_path": resolve_project_relative(TRUTH_PSEUDOBULK_ROOT / dataset_id / "perturbed_pseudobulk.tsv.gz"),
        "alignment_summary": alignment_summary,
        "audit_execution_mode": audit_execution_mode,
        "alignment_introduced_change_max_abs": float(np.max(alignment_delta_values)),
        "alignment_introduced_change_mean_abs": float(np.mean(alignment_delta_values)),
        "layer_summaries": layer_summaries,
        "judgment_boundary": {
            "entrant_status": "runnable_entrant",
            "export_space_consistency": "still_under_audit",
            "formal_adjudication_eligible": False,
            "freeze_eligible": False,
            "formal_downstream_admission_eligible": False,
        },
    }
    json_dump(summary, summary_path)
    log_stage("write_outputs_done", summary_path=resolve_project_relative(summary_path))


if __name__ == "__main__":
    main()
