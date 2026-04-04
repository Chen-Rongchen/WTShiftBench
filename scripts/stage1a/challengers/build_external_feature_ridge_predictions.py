from __future__ import annotations

import argparse
import json

import anndata as ad
import numpy as np
import pandas as pd

from scripts.stage1a.adapters.common.runtime import (
    audit_input_matrix_semantics,
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
from wtbench.baselines.linear_external_p_shift_baseline import build_linear_external_p_baseline


DEFAULT_PREDICTION_ROOT = "data/predictions/stage1a_challengers_raw"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="使用冻结 pretrained target feature 构建外部 feature ridge challenger 预测。")
    parser.add_argument("--run-config", required=True)
    parser.add_argument("--feature-registry", default=str(DEFAULT_FEATURE_REGISTRY_PATH))
    parser.add_argument("--challenger-registry", default=str(DEFAULT_CHALLENGER_REGISTRY_PATH))
    return parser


def project_feature_frame(feature_frame: pd.DataFrame, n_components: int) -> tuple[pd.DataFrame, int]:
    values = feature_frame.to_numpy(dtype=np.float64, copy=False)
    effective_n_components = min(n_components, values.shape[0], values.shape[1])
    if effective_n_components < 1:
        raise ValueError("无法为 pretrained ridge challenger 生成有效投影维度。")
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


def main() -> None:
    args = build_parser().parse_args()
    run_config = load_run_config(args.run_config)

    challenger_id = str(run_config["challenger_id"])
    dataset_id = str(run_config["dataset_id"])
    model_id = str(run_config["model_id"])
    feature_id = str(run_config["feature_id"])
    n_components_requested = int(run_config["n_components"])
    ridge_lambda = float(run_config["ridge_lambda"])
    formal_h5ad_path = resolve_path(
        str(coalesce_arg(None, run_config, "formal_h5ad_path", get_formal_dataset_contract(dataset_id).path))
    )
    prediction_path = resolve_path(
        str(
            coalesce_arg(
                None,
                run_config,
                "prediction_path",
                f"{DEFAULT_PREDICTION_ROOT}/{model_id}/{dataset_id}/predicted_shift.tsv.gz",
            )
        )
    )
    metadata_path = resolve_path(
        str(coalesce_arg(None, run_config, "metadata_path", prediction_path.with_name("adapter_metadata.json")))
    )

    challenger_entry = get_challenger_entry(challenger_id, resolve_path(args.challenger_registry))
    feature_entry = get_feature_entry(feature_id, resolve_path(args.feature_registry))
    if feature_id not in challenger_entry.feature_dependencies:
        raise ValueError(f"{challenger_id} 不允许引用 feature_id={feature_id}")

    feature_frame = read_feature_matrix(feature_entry.source_path)
    heldout_targets, common_genes = load_frozen_prediction_space(dataset_id)
    heldout_set = set(heldout_targets)

    formal_adata = ad.read_h5ad(formal_h5ad_path)
    try:
        input_audit = audit_input_matrix_semantics(formal_adata)
        train_targets, train_deltas = compute_train_target_deltas(
            formal_adata,
            common_genes,
            heldout_set,
        )
    finally:
        del formal_adata

    train_targets = [str(target) for target in train_targets]
    test_targets = [str(target) for target in heldout_targets]

    mapped_train_targets = [target for target in train_targets if target in feature_frame.index]
    mapped_train_mask = np.asarray([target in feature_frame.index for target in train_targets], dtype=bool)
    if mapped_train_mask.sum() == 0:
        raise ValueError(f"{challenger_id}::{feature_id} 没有可映射 train targets。")
    mapped_train_deltas = train_deltas[mapped_train_mask]

    mapped_test_targets = [target for target in test_targets if target in feature_frame.index]
    unmapped_test_targets = [target for target in test_targets if target not in feature_frame.index]
    heldout_coverage = float(len(mapped_test_targets) / len(test_targets))
    coverage_floor = float(feature_entry.heldout_coverage_floor or 1.0)
    if heldout_coverage < coverage_floor:
        raise ValueError(
            f"{challenger_id}::{feature_id} heldout coverage 低于冻结阈值: "
            f"coverage={heldout_coverage:.4f}, floor={coverage_floor:.4f}"
        )

    combined_targets = [*mapped_train_targets, *mapped_test_targets]
    combined_features = feature_frame.loc[combined_targets].copy()
    effective_n_components_cap = min(
        n_components_requested,
        max(1, len(mapped_train_targets) - 1),
        combined_features.shape[0],
        combined_features.shape[1],
    )
    combined_features, effective_n_components = project_feature_frame(
        combined_features,
        n_components=effective_n_components_cap,
    )
    external_embeddings = {
        target: combined_features.loc[target].to_numpy(dtype=float, copy=False)
        for target in combined_features.index
    }

    result = build_linear_external_p_baseline(
        adata=ad.read_h5ad(formal_h5ad_path),
        train_targets=mapped_train_targets,
        test_targets=mapped_test_targets,
        evaluable_genes=common_genes,
        external_p_embeddings=external_embeddings,
        n_components=effective_n_components,
        ridge_lambda=ridge_lambda,
    )

    fallback_delta = mapped_train_deltas.mean(axis=0)
    prediction_rows: list[np.ndarray] = []
    mapped_prediction = result.predicted_shift
    for target in test_targets:
        if target in mapped_prediction.index:
            prediction_rows.append(mapped_prediction.loc[target].to_numpy(dtype=np.float64, copy=False))
        else:
            prediction_rows.append(fallback_delta)

    predicted_shift = pd.DataFrame(prediction_rows, index=test_targets, columns=common_genes)
    predicted_shift.index.name = "target_gene"
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
            "input_matrix_source": input_audit["input_matrix_source"],
            "raw_counts_available": bool(input_audit["raw_counts_available"]),
            "looks_like_log_normalized_or_transformed": bool(input_audit["looks_like_log_normalized_or_transformed"]),
            "train_targets_total": len(train_targets),
            "train_targets_mapped": len(mapped_train_targets),
            "heldout_targets_total": len(test_targets),
            "heldout_targets_mapped": len(mapped_test_targets),
            "heldout_coverage": heldout_coverage,
            "heldout_coverage_floor": coverage_floor,
            "unmapped_heldout_targets_sample": unmapped_test_targets[:20],
            "missing_policy": feature_entry.missing_policy,
            "fallback_policy": feature_entry.fallback_policy,
            "claim_scope": "当前仅作为 non-formal single-seed challenger；不构成 formal superiority 或 entrant ready。",
            "model_params": result.model_params,
            "target_coverage": result.target_coverage,
            "provenance": result.provenance,
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
                "heldout_coverage": heldout_coverage,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
