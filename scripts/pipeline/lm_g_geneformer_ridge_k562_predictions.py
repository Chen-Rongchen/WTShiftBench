#!/usr/bin/env python3
"""lm_g_geneformer_ridge K562 predictions: ridge regression from Geneformer embeddings to deltas.

For K562: the 10 perturbed TFs form the leave-one-out target set.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

from scripts.stage1a.adapters.geneformer.build_predictions import (
    load_geneformer_word_embedding_weight,
    resolve_geneformer_checkpoint_dir,
)
from wtbench.truth_bridge import load_config, log_normalize_csr


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSET_ROOT = PROJECT_ROOT / "models/pretrained/geneformer_assets/geneformer"
DEFAULT_MODEL_ROOT = PROJECT_ROOT / "models/pretrained/geneformer_gf_12l_95m_i4096"


def log_stage(stage: str, **fields: object) -> None:
    suffix = ""
    if fields:
        suffix = " | " + ", ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[stage2-lm-geneformer-ridge-k562] {stage}{suffix}", flush=True)


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


def load_geneformer_assets(recipe: dict[str, object]):
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
    return token_dict, gene_name_to_ensembl, emb_weight


def extract_gene_symbol(ensg_symbol: str) -> str:
    s = str(ensg_symbol)
    if "_" in s:
        return s.split("_", 1)[1]
    return s


def load_h5ad_data(truth_config, timepoint):
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
    if hasattr(adata.X, 'toarray'):
        full_matrix = adata.X.toarray()
    else:
        full_matrix = np.asarray(adata.X)
    matrix = sparse.csr_matrix(full_matrix[np.ix_(cell_positions, unique_indices)])
    normalized = log_normalize_csr(matrix, target_sum=10000.0)
    return calls.reset_index(drop=True), pd.DataFrame({"feature_name": unique_gene_names}), normalized


def build_target_delta_matrix_k562(*, calls, gene_meta, normalized_expression, truth_config):
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
        raise ValueError("K562 没有 control cells。")
    normalized = normalized_expression[:, output_gene_positions]
    control_mean = np.asarray(normalized[control_mask].mean(axis=0)).ravel().astype(np.float64)
    records = []
    target_cell_counts = {}
    for target_gene in perturbed_targets:
        target_mask = (~calls["is_control"]).to_numpy() & calls["target_gene"].astype(str).eq(target_gene).to_numpy()
        target_cell_counts[target_gene] = int(target_mask.sum())
        if not target_mask.any():
            continue
        target_mean = np.asarray(normalized[target_mask].mean(axis=0)).ravel().astype(np.float64)
        delta = target_mean - control_mean
        records.append({"target_gene": target_gene, **dict(zip(output_genes, delta.tolist()))})
    if len(records) < 2:
        raise ValueError("K562 perturbed targets 少于 2 个。")
    return pd.DataFrame(records), {
        "target_cell_counts": target_cell_counts,
        "control_cells": int(control_mask.sum()),
        "output_gene_count": len(output_genes),
        "perturbed_target_count": len(perturbed_targets),
    }


def predict_leave_one_out_geneformer_ridge(
    truth_deltas: pd.DataFrame,
    *,
    token_dict, gene_name_to_ensembl, emb_weight,
    n_components: int, ridge_lambda: float,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Leave-one-out ridge regression from Geneformer embeddings to deltas."""
    from sklearn.decomposition import TruncatedSVD
    from sklearn.linear_model import Ridge

    output_genes = truth_deltas.columns.tolist()[1:]
    target_order = truth_deltas["target_gene"].astype(str).tolist()
    delta_by_target = truth_deltas.set_index("target_gene")
    n_targets = len(target_order)
    n_outputs = len(output_genes)
    n_vocab = int(emb_weight.shape[0])

    # Map targets to Geneformer embeddings via token dict
    target_embeddings = []
    mapped_targets = []
    unmapped_targets = []
    target_to_token = {}
    for target in target_order:
        ensembl_id = gene_name_to_ensembl.get(target)
        token_id = token_dict.get(ensembl_id) if ensembl_id is not None else None
        if token_id is None or not (0 <= int(token_id) < n_vocab):
            unmapped_targets.append(target)
            target_embeddings.append(None)
        else:
            tid = int(token_id)
            target_embeddings.append(emb_weight[tid])
            mapped_targets.append(target)
            target_to_token[target] = tid

    if len(mapped_targets) < 2:
        raise ValueError("Geneformer 可映射 targets 少于 2 个。")

    # SVD on output gene dimension
    svd = TruncatedSVD(n_components=min(n_components, n_outputs - 1, n_targets - 1), random_state=42)
    delta_svd = svd.fit_transform(delta_by_target.values.astype(np.float64))

    predicted_rows = []
    fallback_delta = delta_svd.mean(axis=0)

    for i, target in enumerate(target_order):
        if target not in target_to_token:
            pred_svd = fallback_delta
        else:
            # Leave-one-out: train ridge on other mapped targets
            other_targets = [t for t in mapped_targets if t != target]
            if len(other_targets) < 2:
                pred_svd = fallback_delta
            else:
                X_train = emb_weight[[target_to_token[t] for t in other_targets]]
                y_train = delta_svd[[target_order.index(t) for t in other_targets]]
                ridge = Ridge(alpha=ridge_lambda, fit_intercept=True)
                ridge.fit(X_train, y_train)
                pred_svd = ridge.predict(emb_weight[target_to_token[target]].reshape(1, -1))[0]

        predicted_delta = svd.inverse_transform(pred_svd.reshape(1, -1)).ravel()
        predicted_rows.append(predicted_delta.astype(np.float64))

    frame = pd.DataFrame(predicted_rows, columns=output_genes)
    frame.insert(0, "target_gene", target_order)
    return frame, {
        "n_components": n_components,
        "ridge_lambda": ridge_lambda,
        "total_targets": len(target_order),
        "mapped_targets": len(mapped_targets),
        "output_gene_count": n_outputs,
        "unmapped_targets": unmapped_targets,
    }


def run_one_timepoint(*, timepoint, recipe, truth_config, token_dict, gene_name_to_ensembl, emb_weight):
    runtime = dict(recipe["runtime"])
    model_id = str(recipe["model_id"])
    output_root = resolve_path(str(recipe["output_roots"]["raw_prediction_root"]))
    report_root = resolve_path(str(recipe["output_roots"]["report_root"]))

    log_stage("load_h5ad_start", timepoint=timepoint)
    calls, gene_meta, normalized = load_h5ad_data(truth_config, timepoint)
    log_stage("build_truth_deltas_start", timepoint=timepoint, n_calls=len(calls))

    truth_deltas, truth_manifest = build_target_delta_matrix_k562(
        calls=calls, gene_meta=gene_meta,
        normalized_expression=normalized, truth_config=truth_config,
    )
    log_stage("build_truth_deltas_done", timepoint=timepoint, n_targets=int(len(truth_deltas)),
              output_genes=truth_manifest['output_gene_count'])

    log_stage("predict_leave_one_out_start", timepoint=timepoint)
    predicted_shift, prediction_manifest = predict_leave_one_out_geneformer_ridge(
        truth_deltas,
        token_dict=token_dict, gene_name_to_ensembl=gene_name_to_ensembl, emb_weight=emb_weight,
        n_components=int(runtime.get("n_components", 32)),
        ridge_lambda=float(runtime.get("ridge_lambda", 0.1)),
    )
    log_stage("predict_leave_one_out_done", timepoint=timepoint)

    prediction_path = output_root / model_id / timepoint / "predicted_shift.tsv.gz"
    metadata_path = output_root / model_id / timepoint / "raw_prediction_metadata.json"
    coverage_path = report_root / timepoint / "coverage_audit.json"

    write_matrix(predicted_shift, prediction_path)
    write_json({
        "stage": "stage2_k562_lm_g_geneformer_ridge_raw_output",
        "timepoint": timepoint,
        "model_id": model_id,
        "model_version": str(recipe["entrant_version"]),
        "entrant_id": str(recipe["entrant_id"]),
        "source_kind": "lm_geneformer_embedding_ridge_regression",
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "prediction_path": str(prediction_path),
        "truth_delta_manifest": truth_manifest,
        "prediction_manifest": prediction_manifest,
    }, metadata_path)
    write_json({
        "timepoint": timepoint,
        "model_id": model_id,
        "n_components": prediction_manifest["n_components"],
        "ridge_lambda": prediction_manifest["ridge_lambda"],
        "total_targets": prediction_manifest["total_targets"],
        "mapped_targets": prediction_manifest["mapped_targets"],
    }, coverage_path)
    return {"timepoint": timepoint, "prediction_path": str(prediction_path)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="lm_g_geneformer_ridge K562 predictions.")
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "configs/lm_g_geneformer_ridge_k562_tf_13d_formal_v1.json"),
    )
    parser.add_argument("--timepoint", choices=["13d", "7d"])
    return parser


def main() -> None:
    args = build_parser().parse_args()
    recipe = load_recipe(resolve_path(args.config))
    truth_config = load_config(resolve_path(str(recipe["stage2_truth_config_path"])))
    token_dict, gene_name_to_ensembl, emb_weight = load_geneformer_assets(recipe)

    selected_timepoints = {args.timepoint} if args.timepoint else {"13d", "7d"}
    summary = []
    for tp in sorted(selected_timepoints):
        summary.append(run_one_timepoint(
            timepoint=tp, recipe=recipe, truth_config=truth_config,
            token_dict=token_dict, gene_name_to_ensembl=gene_name_to_ensembl, emb_weight=emb_weight,
        ))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
