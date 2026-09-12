from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import numpy as np
import pandas as pd

from scripts.stage1a.challengers.common import get_feature_entry, hashed_chargram_vector, read_feature_matrix
from wtbench.baselines.linear_utils import (
    build_gene_embedding_from_shift_pca,
    predict_shift_from_gwp,
    solve_bilinear_ridge_closed_form,
)
from wtbench.hcc_prediction_export import expected_target_and_gene_order, load_axis_membership
from wtbench.truth_bridge import (
    build_dataset_specs,
    load_config,
    load_expression_for_called_cells,
    load_single_feature_calls,
    log_normalize_csr,
)


def log_stage(stage: str, **fields: object) -> None:
    suffix = ""
    if fields:
        suffix = " | " + ", ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[stage2-lm-train-lowrank] {stage}{suffix}", flush=True)


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


def load_feature_assets(recipe: dict[str, object]) -> tuple[pd.DataFrame, dict[str, object]]:
    feature_entry = get_feature_entry(
        str(recipe["feature_id"]),
        resolve_path(str(recipe["feature_registry_ref"])),
    )
    feature_frame = read_feature_matrix(feature_entry.source_path)
    manifest = {
        "feature_id": feature_entry.feature_id,
        "feature_family": feature_entry.feature_family,
        "source_path": str(feature_entry.source_path),
        "coverage_on_current_smoke": float(feature_entry.coverage_on_current_smoke),
        "missing_policy": feature_entry.missing_policy,
        "is_frozen": bool(feature_entry.is_frozen),
    }
    return feature_frame, manifest


def ensure_hcc_target_feature_rows(
    feature_frame: pd.DataFrame,
    *,
    feature_id: str,
    target_order: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    missing_targets = [target for target in target_order if target not in feature_frame.index]
    if not missing_targets:
        return feature_frame, []
    if feature_id != "gene_symbol_chargram_v1":
        return feature_frame, missing_targets

    dim = feature_frame.shape[1]
    generated = pd.DataFrame(
        [hashed_chargram_vector(target, dim) for target in missing_targets],
        index=missing_targets,
        columns=feature_frame.columns,
    )
    generated.index.name = "target_gene"
    combined = pd.concat([feature_frame, generated], axis=0)
    combined = combined.loc[~combined.index.duplicated(keep="first")]
    return combined, missing_targets


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


def predict_leave_one_out_linear_lowrank(
    truth_deltas: pd.DataFrame,
    *,
    feature_frame: pd.DataFrame,
    n_components: int,
    ridge_lambda: float,
) -> tuple[pd.DataFrame, dict[str, object]]:
    output_genes = truth_deltas.columns.tolist()[1:]
    target_order = truth_deltas["target_gene"].astype(str).tolist()
    truth_indexed = truth_deltas.set_index("target_gene")

    missing_targets = [target for target in target_order if target not in feature_frame.index]
    if missing_targets:
        raise ValueError(f"feature 缺少 targets: {missing_targets[:20]}")

    projected_features, effective_n_components = project_feature_frame(
        feature_frame.loc[target_order].copy(),
        n_components=n_components,
    )

    predicted_rows: list[np.ndarray] = []
    for target in target_order:
        train_targets = [ref for ref in target_order if ref != target]
        Y_train = truth_indexed.loc[train_targets, output_genes].to_numpy(dtype=np.float64).T
        bias = Y_train.mean(axis=1)
        Y_centered = Y_train - bias[:, np.newaxis]
        G, explained_variance = build_gene_embedding_from_shift_pca(Y_centered, effective_n_components)
        P_train = projected_features.loc[train_targets].to_numpy(dtype=np.float64)
        W = solve_bilinear_ridge_closed_form(
            Y_centered=Y_centered,
            G=G,
            P_train=P_train,
            ridge_lambda=ridge_lambda,
        )
        P_test = projected_features.loc[[target]].to_numpy(dtype=np.float64)
        pred = predict_shift_from_gwp(G=G, W=W, P_test=P_test, bias=bias)[0]
        predicted_rows.append(pred.astype(np.float64, copy=False))

    frame = pd.DataFrame(predicted_rows, columns=output_genes)
    frame.insert(0, "target_gene", target_order)
    return frame, {
        "mapped_targets": len(target_order),
        "total_targets": len(target_order),
        "target_vocab_coverage": 1.0,
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
    feature_frame: pd.DataFrame,
    feature_manifest: dict[str, object],
) -> dict[str, object]:
    runtime = dict(recipe["runtime"])
    model_id = str(recipe["model_id"])
    output_root = resolve_path(str(recipe["output_roots"]["raw_prediction_root"]))
    report_root = resolve_path(str(recipe["output_roots"]["report_root"]))
    prediction_path = output_root / model_id / spec.cell_line / "predicted_shift.tsv.gz"
    metadata_path = output_root / model_id / spec.cell_line / "raw_prediction_metadata.json"
    coverage_path = report_root / spec.cell_line / "coverage_audit.json"

    target_order, _ = expected_target_and_gene_order(axis_membership)
    feature_frame, generated_targets = ensure_hcc_target_feature_rows(
        feature_frame,
        feature_id=str(recipe["feature_id"]),
        target_order=target_order,
    )

    log_stage("build_truth_deltas_start", cell_line=spec.cell_line)
    truth_deltas, truth_manifest = build_target_delta_matrix(
        spec=spec,
        truth_config=truth_config,
        axis_membership=axis_membership,
    )
    log_stage("build_truth_deltas_done", cell_line=spec.cell_line, n_targets=int(len(truth_deltas)))

    log_stage("predict_leave_one_out_start", cell_line=spec.cell_line)
    predicted_shift, prediction_manifest = predict_leave_one_out_linear_lowrank(
        truth_deltas,
        feature_frame=feature_frame,
        n_components=int(runtime.get("n_components", 32)),
        ridge_lambda=float(runtime.get("ridge_lambda", 0.1)),
    )
    log_stage(
        "predict_leave_one_out_done",
        cell_line=spec.cell_line,
        n_components=prediction_manifest["n_components_effective"],
    )

    write_matrix(predicted_shift, prediction_path)
    write_json(
        {
            "stage": "hcc_lm_train_lowrank_raw_output",
            "cell_line": spec.cell_line,
            "model_id": model_id,
            "model_version": str(recipe["entrant_version"]),
            "entrant_id": str(recipe["entrant_id"]),
            "source_kind": "linear_lowrank_external_feature_leave_one_out",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "prediction_path": str(prediction_path),
            "feature_manifest": feature_manifest,
            "truth_delta_manifest": truth_manifest,
            "prediction_manifest": prediction_manifest,
            "generated_feature_targets": generated_targets,
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
            "fallback_policy": str(recipe["fallback_policy"]["unmapped_heldout_target"]),
            "leave_one_out_policy": True,
            "generated_feature_targets": generated_targets,
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
    parser = argparse.ArgumentParser(description="生成 Stage 2 lm_train_lowrank HCC raw prediction。")
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "configs/lm_train_lowrank_hcc_formal_v1.json"),
    )
    parser.add_argument("--cell-line", choices=["HCC38", "HCC1143"])
    return parser


def main() -> None:
    args = build_parser().parse_args()
    recipe = load_recipe(resolve_path(args.config))
    truth_config = load_config(resolve_path(str(recipe["truth_config_path"])))
    axis_membership = load_axis_membership(resolve_path(str(recipe["axis_membership_path"])))
    feature_frame, feature_manifest = load_feature_assets(recipe)
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
                feature_frame=feature_frame,
                feature_manifest=feature_manifest,
            )
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
