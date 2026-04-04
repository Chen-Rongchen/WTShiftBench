from __future__ import annotations

import argparse
import json
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

from scripts.stage1a.adapters.common.runtime import (
    coalesce_arg,
    compute_train_target_deltas,
    load_frozen_prediction_space,
    load_run_config,
    resolve_path,
)
from scripts.stage1a.benchmark_invariant.catalog import get_formal_dataset_contract
from scripts.stage1a.benchmark_invariant.prediction_eval_common import json_dump, resolve_project_relative, write_matrix
from scripts.stage1a.challengers.common import (
    DEFAULT_CHALLENGER_REGISTRY_PATH,
    DEFAULT_FEATURE_REGISTRY_PATH,
    get_challenger_entry,
    get_feature_entry,
    read_feature_matrix,
)
from wtbench.baselines.linear_utils import (
    build_gene_embedding_from_shift_pca,
    predict_shift_from_gwp,
    solve_bilinear_ridge_closed_form,
)


DEFAULT_MODEL_ID = "residual_over_mean__lm_train_lowrank"
DEFAULT_PREDICTION_ROOT = Path("data/predictions/stage1a_challengers_raw")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="为 Stage 1A challenger residual_over_mean__lm_train_lowrank 构建 predicted_shift.tsv.gz。"
    )
    parser.add_argument("--run-config", required=True)
    parser.add_argument("--feature-registry", default=str(DEFAULT_FEATURE_REGISTRY_PATH))
    parser.add_argument("--challenger-registry", default=str(DEFAULT_CHALLENGER_REGISTRY_PATH))
    return parser


def require_feature_rows(feature_frame: pd.DataFrame, targets: list[str], label: str) -> pd.DataFrame:
    missing = [target for target in targets if target not in feature_frame.index]
    if missing:
        raise ValueError(f"{label} 缺少 feature rows: {missing[:20]}")
    return feature_frame.loc[targets].copy()


def project_feature_frame(feature_frame: pd.DataFrame, n_components: int) -> tuple[pd.DataFrame, int]:
    values = feature_frame.to_numpy(dtype=np.float64, copy=False)
    effective_n_components = min(n_components, values.shape[0], values.shape[1])
    if effective_n_components < 1:
        raise ValueError("无法为 residual challenger 生成有效的投影维度。")
    if values.shape[1] == effective_n_components:
        return feature_frame.copy(), effective_n_components

    centered = values - values.mean(axis=0, keepdims=True)
    u, s, _ = np.linalg.svd(centered, full_matrices=False)
    projected = u[:, :effective_n_components] * s[:effective_n_components]
    frame = pd.DataFrame(
        projected,
        index=feature_frame.index,
        columns=[f"pc_{idx:03d}" for idx in range(effective_n_components)],
    )
    return frame, effective_n_components


def build_residual_predictions(
    train_deltas: np.ndarray,
    train_targets: list[str],
    test_targets: list[str],
    evaluable_genes: list[str],
    projected_feature_frame: pd.DataFrame,
    ridge_lambda: float,
) -> tuple[pd.DataFrame, dict[str, object]]:
    mean_delta = train_deltas.mean(axis=0)
    residual_train = (train_deltas - mean_delta).T
    G, explained_variance = build_gene_embedding_from_shift_pca(
        residual_train,
        n_components=projected_feature_frame.shape[1],
    )
    P_train = projected_feature_frame.loc[train_targets].to_numpy(dtype=np.float64, copy=False)
    P_test = projected_feature_frame.loc[test_targets].to_numpy(dtype=np.float64, copy=False)
    W = solve_bilinear_ridge_closed_form(
        residual_train,
        G,
        P_train,
        ridge_lambda,
    )
    predicted_values = predict_shift_from_gwp(
        G,
        W,
        P_test,
        bias=mean_delta,
    )
    predicted_shift = pd.DataFrame(predicted_values, index=test_targets, columns=evaluable_genes)
    predicted_shift.index.name = "target_gene"
    model_params = {
        "n_components": int(projected_feature_frame.shape[1]),
        "ridge_lambda": float(ridge_lambda),
        "G_shape": list(G.shape),
        "W_shape": list(W.shape),
        "P_train_shape": list(P_train.shape),
        "P_test_shape": list(P_test.shape),
        "mean_delta_shape": list(mean_delta.shape),
        "residual_train_shape": list(residual_train.shape),
    }
    provenance = {
        "baseline_type": "residual_over_mean_linear_external_p_shift_baseline",
        "base_anchor": "train_mean_delta",
        "model_formula": "Y ≈ mean_delta + G W P^T",
        "G_source": "PCA of residual_train",
        "P_source": "external_p_embeddings (provided externally, not learned from training data)",
        "explained_variance_ratio": explained_variance.tolist(),
    }
    return predicted_shift, {"model_params": model_params, "provenance": provenance, "mean_delta": mean_delta}


def main() -> None:
    args = build_parser().parse_args()
    run_config = load_run_config(args.run_config)

    challenger_id = str(coalesce_arg(None, run_config, "challenger_id", DEFAULT_MODEL_ID))
    dataset_id = str(coalesce_arg(None, run_config, "dataset_id", "replogle_2022_k562_essential"))
    model_id = str(coalesce_arg(None, run_config, "model_id", DEFAULT_MODEL_ID))
    feature_id = str(coalesce_arg(None, run_config, "feature_id", "gene_symbol_chargram_v1"))
    formal_h5ad_path = resolve_path(
        str(coalesce_arg(None, run_config, "formal_h5ad_path", get_formal_dataset_contract(dataset_id).path))
    )
    prediction_path = resolve_path(
        str(
            coalesce_arg(
                None,
                run_config,
                "prediction_path",
                DEFAULT_PREDICTION_ROOT / model_id / dataset_id / "predicted_shift.tsv.gz",
            )
        )
    )
    metadata_path = resolve_path(
        str(coalesce_arg(None, run_config, "metadata_path", prediction_path.with_name("adapter_metadata.json")))
    )
    n_components_requested = int(coalesce_arg(None, run_config, "n_components", 32))
    ridge_lambda = float(coalesce_arg(None, run_config, "ridge_lambda", 1.0))

    challenger_entry = get_challenger_entry(challenger_id, resolve_path(args.challenger_registry))
    if not challenger_entry.implemented or not challenger_entry.wired_to_eval:
        raise ValueError(f"{challenger_id} 尚未处于可运行状态。")
    if feature_id not in challenger_entry.feature_dependencies:
        raise ValueError(f"{challenger_id} 当前不允许引用 feature_id={feature_id}")

    feature_entry = get_feature_entry(feature_id, resolve_path(args.feature_registry))
    if not feature_entry.is_frozen:
        raise ValueError(f"feature_id={feature_id} 尚未冻结。")

    feature_frame = read_feature_matrix(feature_entry.source_path)
    heldout_targets, evaluable_genes = load_frozen_prediction_space(dataset_id)
    heldout_set = set(heldout_targets)

    formal_adata = ad.read_h5ad(formal_h5ad_path)
    try:
        train_targets, train_deltas = compute_train_target_deltas(formal_adata, evaluable_genes, heldout_set)
    finally:
        del formal_adata

    train_targets = [str(target) for target in train_targets]
    test_targets = [str(target) for target in heldout_targets]
    train_feature_frame = require_feature_rows(feature_frame, train_targets, "train targets")
    test_feature_frame = require_feature_rows(feature_frame, test_targets, "heldout targets")
    effective_n_components = min(
        n_components_requested,
        max(1, len(train_targets) - 1),
        len(train_targets) + len(test_targets),
        train_feature_frame.shape[1],
    )
    combined_features = pd.concat([train_feature_frame, test_feature_frame], axis=0)
    combined_features, effective_n_components = project_feature_frame(combined_features, effective_n_components)
    predicted_shift, residual_artifacts = build_residual_predictions(
        train_deltas=train_deltas,
        train_targets=train_targets,
        test_targets=test_targets,
        evaluable_genes=evaluable_genes,
        projected_feature_frame=combined_features,
        ridge_lambda=ridge_lambda,
    )

    write_matrix(predicted_shift, prediction_path)
    json_dump(
        {
            "challenger_id": challenger_id,
            "model_id": model_id,
            "dataset_id": dataset_id,
            "feature_id": feature_id,
            "feature_path": resolve_project_relative(feature_entry.source_path),
            "prediction_path": resolve_project_relative(prediction_path),
            "n_components_requested": n_components_requested,
            "n_components_effective": effective_n_components,
            "ridge_lambda": ridge_lambda,
            "residual_anchor": "train_mean_delta",
            "claim_scope": "当前仅作为 non-formal single-seed challenger；在 exploratory override 下实现/运行，不构成 formal superiority 或 entrant ready。",
            "model_params": residual_artifacts["model_params"],
            "target_coverage": {
                "n_train_targets": len(train_targets),
                "n_test_targets": len(test_targets),
                "train_coverage": 1.0,
                "test_coverage": 1.0,
                "unmapped_train_targets": [],
                "unmapped_test_targets": [],
            },
            "provenance": residual_artifacts["provenance"],
        },
        metadata_path,
    )

    print(f"已写出: {resolve_project_relative(prediction_path)}")
    print(f"已写出: {resolve_project_relative(metadata_path)}")
    print(
        json.dumps(
            {
                "challenger_id": challenger_id,
                "dataset_id": dataset_id,
                "model_id": model_id,
                "feature_id": feature_id,
                "n_components_requested": n_components_requested,
                "n_components_effective": effective_n_components,
                "ridge_lambda": ridge_lambda,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
