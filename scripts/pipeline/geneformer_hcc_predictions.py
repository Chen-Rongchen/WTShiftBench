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
from wtbench.hcc_prediction_export import expected_target_and_gene_order, load_axis_membership
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
    print(f"[stage2-geneformer-hcc] {stage}{suffix}", flush=True)


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


def load_geneformer_assets(recipe: dict[str, object]) -> tuple[dict[object, object], dict[str, str], np.ndarray, dict[str, object]]:
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
    emb_weight = load_geneformer_word_embedding_weight(checkpoint_dir).detach().cpu().numpy().astype(np.float32, copy=False)
    manifest = {
        "checkpoint_key": checkpoint_key,
        "checkpoint_root": str(checkpoint_root),
        "checkpoint_dir": str(checkpoint_dir),
        "asset_root": str(asset_root),
        "token_dict_path": str(token_dict_path),
        "gene_mapping_path": str(gene_mapping_path),
        "embedding_shape": list(emb_weight.shape),
    }
    return token_dict, gene_name_to_ensembl, emb_weight, manifest


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

    gene_index = pd.Series(
        np.arange(len(gene_meta), dtype=np.int64),
        index=gene_meta["feature_name"].astype(str),
    )
    missing_genes = [gene for gene in output_genes if gene not in gene_index.index]
    if missing_genes:
        raise ValueError(f"{spec.cell_line} 缺少 frozen output genes: {missing_genes[:20]}")
    output_gene_positions = gene_index.loc[output_genes].to_numpy(dtype=np.int64)

    control_mask = filtered_calls["is_control"].to_numpy(dtype=bool)
    if not control_mask.any():
        raise ValueError(f"{spec.cell_line} 没有 control cells。")
    control_mean = np.asarray(normalized[:, output_gene_positions][control_mask].mean(axis=0)).ravel().astype(np.float64)

    records: list[dict[str, object]] = []
    missing_targets: list[str] = []
    target_cell_counts: dict[str, int] = {}
    for target_gene in target_order:
        current_target_mask = (~filtered_calls["is_control"]).to_numpy() & filtered_calls["target_gene"].astype(str).eq(target_gene).to_numpy()
        target_cell_counts[target_gene] = int(current_target_mask.sum())
        if not current_target_mask.any():
            missing_targets.append(target_gene)
            continue
        target_mean = np.asarray(normalized[:, output_gene_positions][current_target_mask].mean(axis=0)).ravel().astype(np.float64)
        delta = target_mean - control_mean
        records.append({"target_gene": target_gene, **dict(zip(output_genes, delta.tolist()))})
    if missing_targets:
        raise ValueError(f"{spec.cell_line} 缺少 frozen targets: {missing_targets[:20]}")
    return pd.DataFrame(records), {
        "target_cell_counts": target_cell_counts,
        "control_cells": int(control_mask.sum()),
        "output_gene_count": len(output_genes),
    }


def predict_leave_one_out_deltas(
    truth_deltas: pd.DataFrame,
    *,
    token_dict: dict[object, object],
    gene_name_to_ensembl: dict[str, str],
    emb_weight: np.ndarray,
    top_k: int,
    fallback_policy: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    output_genes = truth_deltas.columns.tolist()[1:]
    target_order = truth_deltas["target_gene"].astype(str).tolist()
    delta_by_target = truth_deltas.set_index("target_gene")
    n_vocab = int(emb_weight.shape[0])

    mapped_targets: list[str] = []
    mapped_token_ids: list[int] = []
    unmapped_targets: list[str] = []
    for target in target_order:
        ensembl_id = gene_name_to_ensembl.get(target)
        token_id = token_dict.get(ensembl_id) if ensembl_id is not None else None
        if token_id is None:
            unmapped_targets.append(target)
            continue
        token_id = int(token_id)
        if not 0 <= token_id < n_vocab:
            raise ValueError(f"Geneformer token id 越界: target={target}, token_id={token_id}")
        mapped_targets.append(target)
        mapped_token_ids.append(token_id)
    if len(mapped_targets) < 2:
        raise ValueError("Geneformer 可映射 targets 少于 2 个，无法执行 leave-one-target-out 预测。")

    fallback_delta = delta_by_target.loc[mapped_targets].mean(axis=0).to_numpy(dtype=np.float64)
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

        token_id = int(token_id)
        ref_targets = [ref for ref in mapped_targets if ref != target]
        ref_token_ids = [int(token_dict[gene_name_to_ensembl[ref]]) for ref in ref_targets]
        ref_values = delta_by_target.loc[ref_targets].to_numpy(dtype=np.float64)
        query_embedding = emb_weight[token_id]
        ref_embeddings = emb_weight[np.asarray(ref_token_ids, dtype=np.int64)]
        effective_top_k = min(max(1, top_k), len(ref_targets))
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
        "fallback_targets": fallback_targets,
        "leave_one_out_policy": True,
        "top_k": int(min(max(1, top_k), max(1, len(mapped_targets) - 1))),
    }


def run_one_cell_line(
    *,
    spec,
    recipe: dict[str, object],
    truth_config: dict[str, object],
    axis_membership: pd.DataFrame,
    token_dict: dict[object, object],
    gene_name_to_ensembl: dict[str, str],
    emb_weight: np.ndarray,
    checkpoint_manifest: dict[str, object],
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
    predicted_shift, prediction_manifest = predict_leave_one_out_deltas(
        truth_deltas,
        token_dict=token_dict,
        gene_name_to_ensembl=gene_name_to_ensembl,
        emb_weight=emb_weight,
        top_k=int(runtime.get("top_k", 4)),
        fallback_policy=str(recipe["fallback_policy"]["unmapped_heldout_target"]),
    )
    log_stage(
        "predict_leave_one_out_done",
        cell_line=spec.cell_line,
        target_vocab_coverage=f"{prediction_manifest['target_vocab_coverage']:.4f}",
    )

    write_matrix(predicted_shift, prediction_path)
    write_json(
        {
            "stage": "stage2_hcc_geneformer_raw_output",
            "cell_line": spec.cell_line,
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
            "cell_line": spec.cell_line,
            "model_id": model_id,
            "checkpoint_key": checkpoint_manifest["checkpoint_key"],
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
    parser = argparse.ArgumentParser(description="生成 Stage 2 Geneformer HCC raw prediction。")
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "configs/geneformer_hcc_formal_v1.json"),
    )
    parser.add_argument("--cell-line", choices=["HCC38", "HCC1143"])
    return parser


def main() -> None:
    args = build_parser().parse_args()
    recipe = load_recipe(resolve_path(args.config))
    truth_config = load_config(resolve_path(str(recipe["stage2_truth_config_path"])))
    axis_membership = load_axis_membership(resolve_path(str(recipe["axis_membership_path"])))
    token_dict, gene_name_to_ensembl, emb_weight, checkpoint_manifest = load_geneformer_assets(recipe)
    selected_cell_lines = {args.cell_line} if args.cell_line else set(str(x) for x in recipe["cell_lines"])

    specs = [
        spec
        for spec in build_dataset_specs(truth_config)
        if spec.cell_line in selected_cell_lines
    ]
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
                token_dict=token_dict,
                gene_name_to_ensembl=gene_name_to_ensembl,
                emb_weight=emb_weight,
                checkpoint_manifest=checkpoint_manifest,
            )
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
