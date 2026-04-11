from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scripts.stage1a.adapters.geneformer.build_predictions import (
    load_geneformer_word_embedding_weight,
    resolve_geneformer_checkpoint_dir,
)
from wtbench.stage2_hcc_prediction_export import expected_target_and_gene_order, load_axis_membership
from wtbench.stage2_truth_bridge import (
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
    print(f"[stage2-lm-g-geneformer-ridge] {stage}{suffix}", flush=True)


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


def load_geneformer_feature_lookup(recipe: dict[str, object]) -> tuple[dict[str, np.ndarray], dict[str, object]]:
    import yaml

    registry_path = resolve_path(str(recipe["checkpoint_registry_ref"]))
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    checkpoint_key = str(recipe["checkpoint_key"])
    entry = dict(registry["checkpoints"][checkpoint_key])
    checkpoint_root = resolve_path(str(entry["local_resolved_path"]))
    checkpoint_dir = resolve_geneformer_checkpoint_dir(checkpoint_root)
    asset_root = resolve_path(str(recipe["asset_root"]))
    token_dict_path = asset_root / "token_dictionary_gc104M.pkl"
    gene_mapping_path = asset_root / "gene_name_id_dict_gc104M.pkl"
    token_dict = pd.read_pickle(token_dict_path)
    gene_name_to_ensembl = pd.read_pickle(gene_mapping_path)
    emb_weight = load_geneformer_word_embedding_weight(checkpoint_dir).detach().cpu().numpy().astype(np.float64, copy=False)

    lookup: dict[str, np.ndarray] = {}
    for gene_name, ensembl_id in gene_name_to_ensembl.items():
        token_id = token_dict.get(ensembl_id)
        if token_id is None:
            continue
        token_id = int(token_id)
        if 0 <= token_id < emb_weight.shape[0]:
            lookup[str(gene_name)] = emb_weight[token_id]

    manifest = {
        "feature_id": str(recipe["feature_id"]),
        "checkpoint_key": checkpoint_key,
        "checkpoint_root": str(checkpoint_root),
        "checkpoint_dir": str(checkpoint_dir),
        "asset_root": str(asset_root),
        "token_dict_path": str(token_dict_path),
        "gene_mapping_path": str(gene_mapping_path),
        "embedding_shape": list(emb_weight.shape),
    }
    return lookup, manifest


def build_target_delta_matrix(
    *,
    spec,
    truth_config: dict[str, object],
    axis_membership: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, object]]:
    target_order, output_genes = expected_target_and_gene_order(axis_membership)
    frozen_targets = set(target_order)
    calls = load_single_feature_calls(spec, control_prefix=str(truth_config["filters"]["control_target_prefix"]))
    expression, calls, gene_meta = load_expression_for_called_cells(spec, calls)

    target_mask = calls["is_control"].to_numpy(dtype=bool) | calls["target_gene"].astype(str).isin(frozen_targets).to_numpy(dtype=bool)
    filtered_calls = calls.loc[target_mask].reset_index(drop=True)
    filtered_expression = expression[target_mask].tocsr()
    normalized = log_normalize_csr(
        filtered_expression,
        target_sum=float(truth_config["metrics"]["normalization_target_sum"]),
    ).tocsr()

    gene_index = pd.Series(np.arange(len(gene_meta), dtype=np.int64), index=gene_meta["feature_name"].astype(str))
    missing_genes = [gene for gene in output_genes if gene not in gene_index.index]
    if missing_genes:
        raise ValueError(f"{spec.cell_line} 缺少 frozen output genes: {missing_genes[:20]}")
    output_gene_positions = gene_index.loc[output_genes].to_numpy(dtype=np.int64)

    control_mask = filtered_calls["is_control"].to_numpy(dtype=bool)
    if not control_mask.any():
        raise ValueError(f"{spec.cell_line} 没有 control cells。")
    control_mean = np.asarray(normalized[:, output_gene_positions][control_mask].mean(axis=0)).ravel().astype(np.float64)

    records: list[dict[str, object]] = []
    target_cell_counts: dict[str, int] = {}
    for target_gene in target_order:
        current_target_mask = (~filtered_calls["is_control"]).to_numpy() & filtered_calls["target_gene"].astype(str).eq(target_gene).to_numpy()
        target_cell_counts[target_gene] = int(current_target_mask.sum())
        if not current_target_mask.any():
            raise ValueError(f"{spec.cell_line} 缺少 frozen target: {target_gene}")
        target_mean = np.asarray(normalized[:, output_gene_positions][current_target_mask].mean(axis=0)).ravel().astype(np.float64)
        delta = target_mean - control_mean
        records.append({"target_gene": target_gene, **dict(zip(output_genes, delta.tolist()))})

    return pd.DataFrame(records), {
        "target_cell_counts": target_cell_counts,
        "control_cells": int(control_mask.sum()),
        "output_gene_count": len(output_genes),
    }


def project_feature_frame(feature_frame: pd.DataFrame, n_components: int) -> tuple[pd.DataFrame, int]:
    values = feature_frame.to_numpy(dtype=np.float64, copy=False)
    effective_n_components = min(n_components, values.shape[0], values.shape[1])
    if effective_n_components < 1:
        raise ValueError("无法生成有效投影维度。")
    if values.shape[1] == effective_n_components:
        return feature_frame.copy(), effective_n_components
    centered = values - values.mean(axis=0, keepdims=True)
    u, s, _ = np.linalg.svd(centered, full_matrices=False)
    projected = u[:, :effective_n_components] * s[:effective_n_components]
    projected_frame = pd.DataFrame(
        projected,
        index=feature_frame.index,
        columns=[f"pc_{idx:03d}" for idx in range(effective_n_components)],
    )
    return projected_frame, effective_n_components


def predict_leave_one_out_external_ridge(
    truth_deltas: pd.DataFrame,
    *,
    feature_lookup: dict[str, np.ndarray],
    n_components: int,
    ridge_lambda: float,
    coverage_floor: float,
) -> tuple[pd.DataFrame, dict[str, object]]:
    from wtbench.baselines.linear_utils import (
        build_gene_embedding_from_shift_pca,
        predict_shift_from_gwp,
        solve_bilinear_ridge_closed_form,
    )

    output_genes = truth_deltas.columns.tolist()[1:]
    target_order = truth_deltas["target_gene"].astype(str).tolist()
    truth_indexed = truth_deltas.set_index("target_gene")

    mapped_targets = [target for target in target_order if target in feature_lookup]
    target_coverage = float(len(mapped_targets) / len(target_order))
    if target_coverage < coverage_floor:
        raise ValueError(
            f"Geneformer embedding 对 HCC targets coverage 低于阈值: coverage={target_coverage:.4f}, floor={coverage_floor:.4f}"
        )

    feature_frame = pd.DataFrame.from_dict(
        {target: feature_lookup[target] for target in mapped_targets},
        orient="index",
    )
    feature_frame.index.name = "target_gene"
    projected_features, effective_n_components = project_feature_frame(feature_frame, n_components=n_components)

    fallback_delta = truth_indexed.loc[mapped_targets].mean(axis=0).to_numpy(dtype=np.float64)
    predicted_rows: list[np.ndarray] = []
    fallback_targets: list[str] = []

    for target in target_order:
        train_targets = [ref for ref in mapped_targets if ref != target]
        if target in mapped_targets:
            train_matrix = truth_indexed.loc[train_targets, output_genes].to_numpy(dtype=np.float64)
            y_train = train_matrix.T
            bias = y_train.mean(axis=1)
            y_centered = y_train - bias[:, np.newaxis]
            g, _ = build_gene_embedding_from_shift_pca(y_centered, min(effective_n_components, len(train_targets) - 1))
            p_train = projected_features.loc[train_targets].to_numpy(dtype=np.float64)
            w = solve_bilinear_ridge_closed_form(Y_centered=y_centered, G=g, P_train=p_train, ridge_lambda=ridge_lambda)
            p_test = projected_features.loc[[target]].to_numpy(dtype=np.float64)
            pred = predict_shift_from_gwp(G=g, W=w, P_test=p_test, bias=bias)[0]
            predicted_rows.append(pred.astype(np.float64, copy=False))
        else:
            predicted_rows.append(fallback_delta)
            fallback_targets.append(target)

    frame = pd.DataFrame(predicted_rows, columns=output_genes)
    frame.insert(0, "target_gene", target_order)
    return frame, {
        "mapped_targets": len(mapped_targets),
        "total_targets": len(target_order),
        "target_vocab_coverage": target_coverage,
        "fallback_targets": fallback_targets,
        "leave_one_out_policy": True,
        "n_components_requested": int(n_components),
        "n_components_effective": int(effective_n_components),
        "ridge_lambda": float(ridge_lambda),
    }


def run_one_cell_line(
    *,
    spec,
    recipe: dict[str, object],
    truth_config: dict[str, object],
    axis_membership: pd.DataFrame,
    feature_lookup: dict[str, np.ndarray],
    feature_manifest: dict[str, object],
) -> dict[str, object]:
    runtime = dict(recipe["runtime"])
    model_id = str(recipe["model_id"])
    output_root = resolve_path(str(recipe["output_roots"]["raw_prediction_root"]))
    report_root = resolve_path(str(recipe["output_roots"]["report_root"]))
    prediction_path = output_root / model_id / spec.cell_line / "predicted_shift.tsv.gz"
    metadata_path = output_root / model_id / spec.cell_line / "raw_prediction_metadata.json"
    coverage_path = report_root / spec.cell_line / "coverage_audit.json"

    log_stage("build_truth_deltas_start", cell_line=spec.cell_line)
    truth_deltas, truth_manifest = build_target_delta_matrix(
        spec=spec,
        truth_config=truth_config,
        axis_membership=axis_membership,
    )
    log_stage("build_truth_deltas_done", cell_line=spec.cell_line, n_targets=int(len(truth_deltas)))

    log_stage("predict_leave_one_out_start", cell_line=spec.cell_line)
    predicted_shift, prediction_manifest = predict_leave_one_out_external_ridge(
        truth_deltas,
        feature_lookup=feature_lookup,
        n_components=int(runtime.get("n_components", 32)),
        ridge_lambda=float(runtime.get("ridge_lambda", 0.1)),
        coverage_floor=float(recipe["fallback_policy"].get("coverage_floor", 0.8)),
    )
    log_stage(
        "predict_leave_one_out_done",
        cell_line=spec.cell_line,
        target_vocab_coverage=f"{prediction_manifest['target_vocab_coverage']:.4f}",
    )

    write_matrix(predicted_shift, prediction_path)
    write_json(
        {
            "stage": "stage2_hcc_lm_g_geneformer_ridge_raw_output",
            "cell_line": spec.cell_line,
            "model_id": model_id,
            "model_version": str(recipe["entrant_version"]),
            "entrant_id": str(recipe["entrant_id"]),
            "source_kind": "linear_ridge_geneformer_embedding_leave_one_out",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "prediction_path": str(prediction_path),
            "feature_manifest": feature_manifest,
            "truth_delta_manifest": truth_manifest,
            "prediction_manifest": prediction_manifest,
        },
        metadata_path,
    )
    write_json(
        {
            "cell_line": spec.cell_line,
            "model_id": model_id,
            "feature_id": feature_manifest["feature_id"],
            "target_vocab_coverage": prediction_manifest["target_vocab_coverage"],
            "mapped_targets": prediction_manifest["mapped_targets"],
            "total_targets": prediction_manifest["total_targets"],
            "fallback_targets": prediction_manifest["fallback_targets"],
            "fallback_policy": str(recipe["fallback_policy"]["unmapped_heldout_target"]),
            "leave_one_out_policy": True,
        },
        coverage_path,
    )
    return {
        "cell_line": spec.cell_line,
        "prediction_path": str(prediction_path),
        "metadata_path": str(metadata_path),
        "coverage_path": str(coverage_path),
        "target_vocab_coverage": prediction_manifest["target_vocab_coverage"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成 Stage 2 lm_G_geneformer_ridge HCC raw prediction。")
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "configs/stage2/lm_g_geneformer_ridge_hcc_formal_v1.json"),
    )
    parser.add_argument("--cell-line", choices=["HCC38", "HCC1143"])
    return parser


def main() -> None:
    args = build_parser().parse_args()
    recipe = load_recipe(resolve_path(args.config))
    truth_config = load_config(resolve_path(str(recipe["stage2_truth_config_path"])))
    axis_membership = load_axis_membership(resolve_path(str(recipe["axis_membership_path"])))
    feature_lookup, feature_manifest = load_geneformer_feature_lookup(recipe)
    selected_cell_lines = {args.cell_line} if args.cell_line else set(str(x) for x in recipe["cell_lines"])

    specs = [spec for spec in build_dataset_specs(truth_config) if spec.cell_line in selected_cell_lines]
    if not specs:
        raise ValueError("没有匹配到任何 cell line。")

    summary = []
    for spec in specs:
        summary.append(
            run_one_cell_line(
                spec=spec,
                recipe=recipe,
                truth_config=truth_config,
                axis_membership=axis_membership,
                feature_lookup=feature_lookup,
                feature_manifest=feature_manifest,
            )
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
