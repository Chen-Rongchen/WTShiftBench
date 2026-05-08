#!/usr/bin/env python3
"""Geneformer K562 predictions for Stage 2. Supports both 13d and 7d timepoints from h5ad input.

For K562: the 10 perturbed TFs form both train and heldout target sets (leave-one-out).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.stage1a.adapters.common.runtime import cosine_kernel_predict
from scripts.stage1a.adapters.geneformer.build_predictions import (
    load_geneformer_word_embedding_weight,
    resolve_geneformer_checkpoint_dir,
)
from wtbench.truth_bridge import (
    load_config,
    log_normalize_csr,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSET_ROOT = PROJECT_ROOT / "models/pretrained/geneformer_assets/geneformer"
DEFAULT_MODEL_ROOT = PROJECT_ROOT / "models/pretrained/geneformer_gf_12l_95m_i4096"


def log_stage(stage: str, **fields: object) -> None:
    suffix = ""
    if fields:
        suffix = " | " + ", ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[stage2-geneformer-k562] {stage}{suffix}", flush=True)


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


def load_geneformer_assets(recipe: dict[str, object]) -> tuple[dict, dict[str, str], np.ndarray, dict[str, object]]:
    import yaml
    import pickle

    registry_path = resolve_path(str(recipe["checkpoint_registry_ref"]))
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    checkpoint_key = str(recipe["checkpoint_key"])
    entry = dict(registry["checkpoints"][checkpoint_key])
    checkpoint_root = resolve_path(str(entry["local_resolved_path"]))
    checkpoint_dir = resolve_geneformer_checkpoint_dir(checkpoint_root)
    asset_root = resolve_path(str(recipe.get("asset_root", DEFAULT_ASSET_ROOT)))

    token_dict_path = asset_root / "token_dictionary_gc104M.pkl"
    gene_mapping_path = asset_root / "gene_name_id_dict_gc104M.pkl"
    token_dict = pd.read_pickle(token_dict_path)
    gene_name_to_ensembl = pd.read_pickle(gene_mapping_path)
    emb_weight = load_geneformer_word_embedding_weight(checkpoint_dir).detach().cpu().numpy().astype(np.float32, copy=False)

    manifest = {
        "checkpoint_key": checkpoint_key,
        "checkpoint_root": str(checkpoint_root),
        "checkpoint_dir": str(checkpoint_dir),
        "asset_root": str(asset_root),
        "embedding_shape": list(emb_weight.shape),
    }
    return token_dict, gene_name_to_ensembl, emb_weight, manifest


def extract_gene_symbol(ensg_symbol: str) -> str:
    s = str(ensg_symbol)
    if "_" in s:
        return s.split("_", 1)[1]
    return s


def load_h5ad_data(truth_config: dict[str, object], timepoint: str) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    """Load expression and calls from K562 h5ad for a specific timepoint."""
    datasets = truth_config["datasets"]
    dataset = next((d for d in datasets if timepoint in d["cell_line"]), None)
    if dataset is None:
        raise ValueError(f"No dataset found for timepoint {timepoint}")

    h5ad_path = resolve_path(str(dataset["h5ad_path"]))
    import anndata as ad
    adata = ad.read_h5ad(h5ad_path)
    obs = adata.obs.copy()

    obs["target_gene"] = obs["target_gene"].astype(str).fillna("")
    obs["is_control"] = obs["is_control"].astype(bool)

    single_mask = (
        ("is_single_perturbation" in obs.columns and obs["is_single_perturbation"].astype(bool)) |
        (obs.get("num_features", pd.Series(1, index=obs.index)).eq(1))
    )
    obs = obs.loc[single_mask].copy()

    if "formal_like_keep" in obs.columns:
        obs = obs.loc[obs["formal_like_keep"].astype(bool)]

    obs = obs.loc[obs["target_gene"].ne("") | obs["is_control"]]

    calls = pd.DataFrame({
        "cell_barcode": obs.index.astype(str).values,
        "target_gene": obs["target_gene"].values,
        "is_control": obs["is_control"].values,
        "num_features": obs.get("num_features", pd.Series(1, index=obs.index)).values,
    })
    if "sgRNA" in obs.columns:
        calls["feature_call"] = obs["sgRNA"].astype(str).values
    else:
        calls["feature_call"] = obs["target_gene"].values

    calls = calls.loc[calls["num_features"] == 1].copy()

    adata_obs_idx = adata.obs.index
    barcode_to_pos = {bc: i for i, bc in enumerate(adata_obs_idx)}
    cell_positions = [barcode_to_pos[bc] for bc in calls["cell_barcode"]]

    var_names = adata.var.index.astype(str).tolist()
    gene_symbols = [extract_gene_symbol(g) for g in var_names]

    seen = set()
    unique_indices = []
    unique_gene_names = []
    for i, g in enumerate(gene_symbols):
        if g not in seen:
            seen.add(g)
            unique_indices.append(i)
            unique_gene_names.append(g)

    from scipy import sparse
    if hasattr(adata.X, 'toarray'):
        full_matrix = adata.X.toarray()
    else:
        full_matrix = np.asarray(adata.X)
    matrix = sparse.csr_matrix(full_matrix[np.ix_(cell_positions, unique_indices)])

    normalized = log_normalize_csr(matrix, target_sum=10000.0)

    return calls.reset_index(drop=True), pd.DataFrame({"feature_name": unique_gene_names}), normalized


def build_target_delta_matrix_k562(
    *,
    calls: pd.DataFrame,
    gene_meta: pd.DataFrame,
    normalized_expression,
    truth_config: dict[str, object],
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Build target delta matrix for K562 using the 10 perturbed TFs as targets."""
    perturbed_targets = sorted(set(
        calls.loc[~calls["is_control"], "target_gene"].astype(str).tolist()
    ))
    log_stage("k562_perturbed_targets", targets=perturbed_targets)

    gene_index = pd.Series(
        np.arange(len(gene_meta), dtype=np.int64),
        index=gene_meta["feature_name"].astype(str),
    )
    output_genes = list(gene_index.index)
    output_gene_positions = gene_index.loc[output_genes].to_numpy(dtype=np.int64)

    control_mask = calls["is_control"].to_numpy(dtype=bool)
    if not control_mask.any():
        raise ValueError(f"K562 没有 control cells。")

    normalized = normalized_expression[:, output_gene_positions]
    control_mean = np.asarray(normalized[control_mask].mean(axis=0)).ravel().astype(np.float64)

    records: list[dict[str, object]] = []
    target_cell_counts: dict[str, int] = {}

    for target_gene in perturbed_targets:
        target_mask = (~calls["is_control"]).to_numpy() & calls["target_gene"].astype(str).eq(target_gene).to_numpy()
        target_cell_counts[target_gene] = int(target_mask.sum())
        if not target_mask.any():
            continue
        target_mean = np.asarray(normalized[target_mask].mean(axis=0)).ravel().astype(np.float64)
        delta = target_mean - control_mean
        records.append({"target_gene": target_gene, **dict(zip(output_genes, delta.tolist()))})

    if len(records) < 2:
        raise ValueError(f"K562 perturbed targets 少于 2 个，无法执行 leave-one-out。")

    return pd.DataFrame(records), {
        "target_cell_counts": target_cell_counts,
        "control_cells": int(control_mask.sum()),
        "output_gene_count": len(output_genes),
        "perturbed_target_count": len(perturbed_targets),
    }


def predict_leave_one_out_geneformer(
    truth_deltas: pd.DataFrame,
    *,
    token_dict: dict,
    gene_name_to_ensembl: dict,
    emb_weight: np.ndarray,
    top_k: int,
    fallback_policy: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Leave-one-out prediction using Geneformer gene embeddings.

    For K562: all 10 perturbed TFs are used as both train and heldout targets (leave-one-out).
    """
    all_output_genes = truth_deltas.columns.tolist()[1:]
    target_order = truth_deltas["target_gene"].astype(str).tolist()
    delta_by_target = truth_deltas.set_index("target_gene")
    n_vocab = int(emb_weight.shape[0])

    # Filter output genes to those in Geneformer vocab
    output_genes = [g for g in all_output_genes if g in gene_name_to_ensembl]
    missing_output_genes = [g for g in all_output_genes if g not in gene_name_to_ensembl]

    # Map targets to Geneformer tokens via Ensembl ID
    mapped_targets = []
    mapped_token_ids = []
    for target in target_order:
        ensembl_id = gene_name_to_ensembl.get(target)
        token_id = token_dict.get(ensembl_id) if ensembl_id is not None else None
        if token_id is None:
            continue
        token_id = int(token_id)
        if 0 <= token_id < n_vocab:
            mapped_targets.append(target)
            mapped_token_ids.append(token_id)

    if len(mapped_targets) < 2:
        raise ValueError("Geneformer 可映射 targets 少于 2 个，无法执行 leave-one-target-out 预测。")

    # Build train reference: all mapped targets (for leave-one-out)
    train_targets = mapped_targets
    train_token_ids = mapped_token_ids
    train_deltas = delta_by_target.loc[train_targets, output_genes].to_numpy(dtype=np.float64)
    fallback_delta = train_deltas.mean(axis=0)

    predicted_rows: list[np.ndarray] = []
    fallback_targets: list[str] = []

    for target in target_order:
        ensembl_id = gene_name_to_ensembl.get(target)
        token_id = token_dict.get(ensembl_id) if ensembl_id is not None else None
        if token_id is None:
            if fallback_policy != "mean_train_real_shift":
                raise ValueError(f"不支持的 fallback_policy: {fallback_policy}")
            predicted_rows.append(fallback_delta)
            fallback_targets.append(target)
            continue

        # Leave-one-out: exclude this target from reference
        ref_indices = [i for i, t in enumerate(train_targets) if t != target]
        if len(ref_indices) == 0:
            predicted_rows.append(fallback_delta)
            fallback_targets.append(target)
            continue

        ref_token_ids = [train_token_ids[i] for i in ref_indices]
        ref_values = train_deltas[ref_indices]
        query_embedding = emb_weight[int(token_id)]
        ref_embeddings = emb_weight[np.asarray(ref_token_ids, dtype=np.int64)]
        effective_top_k = min(max(1, top_k), len(ref_indices))
        predicted = cosine_kernel_predict(
            query_embedding=query_embedding,
            ref_embeddings=ref_embeddings,
            ref_values=ref_values,
            top_k=effective_top_k,
        )
        predicted_rows.append(predicted.astype(np.float64, copy=False))

    frame = pd.DataFrame(predicted_rows, columns=output_genes)
    frame.insert(0, "target_gene", target_order)
    return frame, {
        "mapped_targets": len(mapped_targets),
        "total_targets": len(target_order),
        "target_vocab_coverage": float(len(mapped_targets) / max(1, len(target_order))),
        "output_genes_total": len(all_output_genes),
        "output_genes_in_vocab": len(output_genes),
        "fallback_targets": fallback_targets,
        "missing_output_genes_sample": missing_output_genes[:5],
        "leave_one_out_policy": True,
        "top_k": int(min(max(1, top_k), max(1, len(mapped_targets) - 1))),
    }


def run_one_timepoint(
    *,
    timepoint: str,
    recipe: dict[str, object],
    truth_config: dict[str, object],
    token_dict: dict,
    gene_name_to_ensembl: dict,
    emb_weight: np.ndarray,
    checkpoint_manifest: dict[str, object],
) -> dict[str, object]:
    runtime = dict(recipe["runtime"])
    model_id = str(recipe["model_id"])
    output_root = resolve_path(str(recipe["output_roots"]["raw_prediction_root"]))
    report_root = resolve_path(str(recipe["output_roots"]["report_root"]))

    log_stage("load_h5ad_start", timepoint=timepoint)
    calls, gene_meta, normalized = load_h5ad_data(truth_config, timepoint)
    log_stage("build_truth_deltas_start", timepoint=timepoint, n_calls=len(calls))

    truth_deltas, truth_manifest = build_target_delta_matrix_k562(
        calls=calls,
        gene_meta=gene_meta,
        normalized_expression=normalized,
        truth_config=truth_config,
    )
    log_stage("build_truth_deltas_done", timepoint=timepoint, n_targets=int(len(truth_deltas)),
              output_genes=truth_manifest['output_gene_count'])

    log_stage("predict_leave_one_out_start", timepoint=timepoint)
    predicted_shift, prediction_manifest = predict_leave_one_out_geneformer(
        truth_deltas,
        token_dict=token_dict,
        gene_name_to_ensembl=gene_name_to_ensembl,
        emb_weight=emb_weight,
        top_k=int(runtime.get("top_k", 4)),
        fallback_policy=str(recipe["fallback_policy"]["unmapped_heldout_target"]),
    )
    log_stage(
        "predict_leave_one_out_done",
        timepoint=timepoint,
        target_vocab_coverage=f"{prediction_manifest['target_vocab_coverage']:.4f}",
        output_genes_in_vocab=prediction_manifest['output_genes_in_vocab'],
    )

    prediction_path = output_root / model_id / timepoint / "predicted_shift.tsv.gz"
    metadata_path = output_root / model_id / timepoint / "raw_prediction_metadata.json"
    coverage_path = report_root / timepoint / "coverage_audit.json"

    write_matrix(predicted_shift, prediction_path)
    write_json(
        {
            "stage": "k562_geneformer_raw_output",
            "timepoint": timepoint,
            "model_id": model_id,
            "model_version": str(recipe["entrant_version"]),
            "entrant_id": str(recipe["entrant_id"]),
            "source_kind": "geneformer_target_embedding_leave_one_out_kernel",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "prediction_path": str(prediction_path),
            "checkpoint_manifest": checkpoint_manifest,
            "truth_delta_manifest": truth_manifest,
            "prediction_manifest": prediction_manifest,
        },
        metadata_path,
    )
    write_json(
        {
            "timepoint": timepoint,
            "model_id": model_id,
            "checkpoint_key": checkpoint_manifest["checkpoint_key"],
            "target_vocab_coverage": prediction_manifest["target_vocab_coverage"],
            "mapped_targets": prediction_manifest["mapped_targets"],
            "total_targets": prediction_manifest["total_targets"],
            "output_genes_in_vocab": prediction_manifest["output_genes_in_vocab"],
            "fallback_targets": prediction_manifest["fallback_targets"],
            "fallback_policy": str(recipe["fallback_policy"]["unmapped_heldout_target"]),
            "leave_one_out_policy": True,
        },
        coverage_path,
    )
    return {
        "timepoint": timepoint,
        "prediction_path": str(prediction_path),
        "metadata_path": str(metadata_path),
        "coverage_path": str(coverage_path),
        "target_vocab_coverage": prediction_manifest["target_vocab_coverage"],
        "output_genes_in_vocab": prediction_manifest["output_genes_in_vocab"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成 Stage 2 Geneformer K562 raw prediction。")
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "configs/geneformer_k562_tf_13d_formal_v1.json"),
    )
    parser.add_argument("--timepoint", choices=["13d", "7d"])
    return parser


def main() -> None:
    args = build_parser().parse_args()
    recipe = load_recipe(resolve_path(args.config))
    truth_config = load_config(resolve_path(str(recipe["truth_config_path"])))
    token_dict, gene_name_to_ensembl, emb_weight, checkpoint_manifest = load_geneformer_assets(recipe)

    selected_timepoints = {args.timepoint} if args.timepoint else {"13d", "7d"}

    summary = []
    for tp in sorted(selected_timepoints):
        summary.append(
            run_one_timepoint(
                timepoint=tp,
                recipe=recipe,
                truth_config=truth_config,
                token_dict=token_dict,
                gene_name_to_ensembl=gene_name_to_ensembl,
                emb_weight=emb_weight,
                checkpoint_manifest=checkpoint_manifest,
            )
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
