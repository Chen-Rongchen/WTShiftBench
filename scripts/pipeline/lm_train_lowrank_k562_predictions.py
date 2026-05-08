#!/usr/bin/env python3
"""lm_train_lowrank K562 predictions for Stage 2. Uses gene symbol chargram features.

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

from wtbench.truth_bridge import (
    load_config,
    log_normalize_csr,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def log_stage(stage: str, **fields: object) -> None:
    suffix = ""
    if fields:
        suffix = " | " + ", ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[stage2-lm-lowrank-k562] {stage}{suffix}", flush=True)


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


def build_chargram_features(gene_names: list[str], n_components: int = 32) -> np.ndarray:
    """Build character n-gram features for gene names using truncated SVD."""
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.decomposition import TruncatedSVD

    # Character n-grams from gene symbols
    vectorizer = CountVectorizer(analyzer='char', ngram_range=(2, 4), min_df=1)
    try:
        char_matrix = vectorizer.fit_transform(gene_names)
    except ValueError:
        # Fallback to simple character features
        char_matrix = np.zeros((len(gene_names), 64), dtype=np.float32)
        for i, name in enumerate(gene_names):
            vec = np.zeros(64, dtype=np.float32)
            for j, c in enumerate(name[:min(len(name), 64)]):
                vec[j * 8 + (ord(c) % 8)] = 1.0
            char_matrix[i] = vec
        char_matrix = sparse.csr_matrix(char_matrix)

    svd = TruncatedSVD(n_components=min(n_components, char_matrix.shape[1] - 1), random_state=42)
    features = svd.fit_transform(char_matrix)
    return features.astype(np.float64)


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
        raise ValueError(f"K562 perturbed targets 少于 2 个。")

    return pd.DataFrame(records), {
        "target_cell_counts": target_cell_counts,
        "control_cells": int(control_mask.sum()),
        "output_gene_count": len(output_genes),
        "perturbed_target_count": len(perturbed_targets),
    }


def predict_leave_one_out_lowrank(
    truth_deltas: pd.DataFrame,
    *,
    target_features: np.ndarray,
    n_components: int,
    ridge_lambda: float,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Leave-one-out prediction using low-rank linear model with target gene features.

    Each perturbed TF has a genome-wide delta vector. We SVD-reduce the output gene
    dimension, then ridge-regress the reduced deltas from target gene chargram features.
    """
    from sklearn.decomposition import TruncatedSVD
    from sklearn.linear_model import Ridge

    output_genes = truth_deltas.columns.tolist()[1:]
    target_order = truth_deltas["target_gene"].astype(str).tolist()
    delta_by_target = truth_deltas.set_index("target_gene")

    n_targets = len(target_order)
    n_outputs = len(output_genes)

    # SVD on output gene dimension for dimensionality reduction
    svd = TruncatedSVD(n_components=min(n_components, n_outputs - 1, n_targets - 1), random_state=42)
    delta_svd = svd.fit_transform(delta_by_target.values.astype(np.float64))

    # target_features should be (n_targets, n_feat) - chargram features for each target gene
    if target_features.shape[0] != n_targets:
        raise ValueError(f"target_features shape {target_features.shape} doesn't match n_targets={n_targets}")

    # Ridge regression: predict each target's SVD-reduced delta from its feature vector
    predicted_rows: list[np.ndarray] = []

    for i, target in enumerate(target_order):
        # Leave-one-out: train on all other targets
        mask = np.ones(n_targets, dtype=bool)
        mask[i] = False

        X_train = target_features[mask]
        y_train = delta_svd[mask]

        # Ridge regression
        ridge = Ridge(alpha=ridge_lambda, fit_intercept=True)
        ridge.fit(X_train, y_train)

        # Predict for held-out target
        y_pred = ridge.predict(target_features[i:i+1])[0]

        # Inverse SVD transform
        predicted_delta = svd.inverse_transform(y_pred.reshape(1, -1)).ravel()
        predicted_rows.append(predicted_delta.astype(np.float64))

    frame = pd.DataFrame(predicted_rows, columns=output_genes)
    frame.insert(0, "target_gene", target_order)
    return frame, {
        "n_components": n_components,
        "ridge_lambda": ridge_lambda,
        "total_targets": len(target_order),
        "output_gene_count": n_outputs,
    }


def run_one_timepoint(
    *,
    timepoint: str,
    recipe: dict[str, object],
    truth_config: dict[str, object],
    target_features: np.ndarray,
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
    predicted_shift, prediction_manifest = predict_leave_one_out_lowrank(
        truth_deltas,
        target_features=target_features,
        n_components=int(runtime.get("n_components", 32)),
        ridge_lambda=float(runtime.get("ridge_lambda", 0.1)),
    )
    log_stage("predict_leave_one_out_done", timepoint=timepoint)

    prediction_path = output_root / model_id / timepoint / "predicted_shift.tsv.gz"
    metadata_path = output_root / model_id / timepoint / "raw_prediction_metadata.json"
    coverage_path = report_root / timepoint / "coverage_audit.json"

    write_matrix(predicted_shift, prediction_path)
    write_json(
        {
            "stage": "stage2_k562_lm_train_lowrank_raw_output",
            "timepoint": timepoint,
            "model_id": model_id,
            "model_version": str(recipe["entrant_version"]),
            "entrant_id": str(recipe["entrant_id"]),
            "source_kind": "lm_train_lowrank_chargram_kernel",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "prediction_path": str(prediction_path),
            "truth_delta_manifest": truth_manifest,
            "prediction_manifest": prediction_manifest,
        },
        metadata_path,
    )
    write_json(
        {
            "timepoint": timepoint,
            "model_id": model_id,
            "n_components": prediction_manifest["n_components"],
            "ridge_lambda": prediction_manifest["ridge_lambda"],
            "total_targets": prediction_manifest["total_targets"],
        },
        coverage_path,
    )
    return {
        "timepoint": timepoint,
        "prediction_path": str(prediction_path),
        "metadata_path": str(metadata_path),
        "coverage_path": str(coverage_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成 Stage 2 lm_train_lowrank K562 raw prediction。")
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "configs/lm_train_lowrank_k562_tf_13d_formal_v1.json"),
    )
    parser.add_argument("--timepoint", choices=["13d", "7d"])
    return parser


def main() -> None:
    args = build_parser().parse_args()
    recipe = load_recipe(resolve_path(args.config))
    truth_config = load_config(resolve_path(str(recipe["stage2_truth_config_path"])))

    # Get the 10 perturbed TF targets from the truth config to build features
    # (all K562 configs have the same 10 targets: CREB1, E2F4, EGR1, ELF1, ELK1, ETS1, GABPA, IRF1, NR2C2, YY1)
    K562_TARGETS = ["CREB1", "E2F4", "EGR1", "ELF1", "ELK1", "ETS1", "GABPA", "IRF1", "NR2C2", "YY1"]

    runtime = dict(recipe["runtime"])
    n_components = int(runtime.get("n_components", 32))
    target_features = build_chargram_features(K562_TARGETS, n_components=n_components)

    selected_timepoints = {args.timepoint} if args.timepoint else {"13d", "7d"}

    summary = []
    for tp in sorted(selected_timepoints):
        summary.append(
            run_one_timepoint(
                timepoint=tp,
                recipe=recipe,
                truth_config=truth_config,
                target_features=target_features,
            )
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
