from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import sparse

from wtbench.truth_bridge import (
    DatasetSpec,
    build_dataset_specs,
    load_config,
    load_expression_for_called_cells,
    load_expression_from_h5ad,
    load_single_feature_calls,
    log_normalize_csr,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRUTH_CONFIG_PATH = PROJECT_ROOT / "configs/truth_driven_bridge_hcc38_hcc1143_v1.json"
DEFAULT_CONTRACT_PATH = PROJECT_ROOT / "configs/hcc_prediction_contract_v1.json"
DEFAULT_AXIS_MEMBERSHIP_PATH = (
    PROJECT_ROOT / "reports/truth_driven_bridge/master_atlas/shared_target_axis_membership.tsv"
)
DEFAULT_TRUTH_CONTRACT_PATH = (
    PROJECT_ROOT
    / "reports/truth_driven_bridge/truth_architecture_contract/truth_architecture_contract.tsv"
)

EXPORT_STATUS_EXPORT_READY = "export_ready"
EXPORT_STATUS_CONTRACT_VALIDATED = "contract_validated"
EXPORT_STATUS_MISSING_RAW_OUTPUT = "missing_raw_output"
EXPORT_STATUS_SPACE_MISMATCH = "space_mismatch"
EXPORT_STATUS_ALIGNMENT_FAILED = "alignment_failed"


@dataclass(frozen=True)
class ExportArtifacts:
    raw_prediction_path: Path
    aligned_prediction_path: Path
    scorer_ready_prediction_path: Path
    manifest_path: Path
    validation_summary_path: Path


@dataclass(frozen=True)
class RawPredictionSource:
    prediction_path: Path
    source_kind: str
    export_script: str
    extra_manifest_fields: dict[str, Any] | None = None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_output_path(template: str, *, model_id: str, cell_line: str) -> Path:
    return PROJECT_ROOT / (
        template.replace("<model_id>", model_id).replace("<cell_line>", cell_line)
    )


def _stringify_output_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def build_export_artifacts(contract: dict[str, Any], *, model_id: str, cell_line: str) -> ExportArtifacts:
    outputs = contract["output_paths"]
    return ExportArtifacts(
        raw_prediction_path=render_output_path(outputs["raw_prediction_root"], model_id=model_id, cell_line=cell_line)
        / "predicted_shift.tsv.gz",
        aligned_prediction_path=render_output_path(
            outputs["aligned_prediction_path"],
            model_id=model_id,
            cell_line=cell_line,
        ),
        scorer_ready_prediction_path=render_output_path(
            outputs["scorer_ready_prediction_path"],
            model_id=model_id,
            cell_line=cell_line,
        ),
        manifest_path=render_output_path(outputs["manifest_path"], model_id=model_id, cell_line=cell_line),
        validation_summary_path=render_output_path(
            outputs["validation_summary_path"],
            model_id=model_id,
            cell_line=cell_line,
        ),
    )


def load_axis_membership(axis_membership_path: Path = DEFAULT_AXIS_MEMBERSHIP_PATH) -> pd.DataFrame:
    frame = pd.read_csv(axis_membership_path, sep="\t")
    required = {"target_gene", "fine_axis"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"axis_membership 缺少列: {missing}")
    return frame


def load_truth_contract(truth_contract_path: Path = DEFAULT_TRUTH_CONTRACT_PATH) -> pd.DataFrame:
    frame = pd.read_csv(truth_contract_path, sep="\t")
    required = {"fine_axis", "architecture_role"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"truth_contract 缺少列: {missing}")
    return frame


def expected_target_and_gene_order(axis_membership: pd.DataFrame) -> tuple[list[str], list[str]]:
    target_order = (
        axis_membership["target_gene"].astype(str).drop_duplicates().sort_values().tolist()
    )
    gene_order = (
        axis_membership["target_gene"].astype(str).drop_duplicates().sort_values().tolist()
    )
    return target_order, gene_order


def _load_expression_and_calls(
    spec: DatasetSpec,
    config: dict[str, Any],
) -> tuple[sparse.csr_matrix, pd.DataFrame, pd.DataFrame]:
    filters = config["filters"]
    if spec.source_kind == "mtx_protospacer":
        calls = load_single_feature_calls(spec, control_prefix=str(filters["control_target_prefix"]))
        expression, calls, gene_meta = load_expression_for_called_cells(spec, calls)
        calls["single_perturbation_filter_status"] = "verified_via_num_features_eq_1"
        calls["single_perturbation_evidence_source"] = "num_features"
        return expression, calls, gene_meta
    if spec.source_kind == "h5ad_obs":
        return load_expression_from_h5ad(
            spec,
            control_prefix=str(filters["control_target_prefix"]),
            allow_degraded_unverified=bool(
                filters.get("allow_degraded_unverified_single_perturbation", False)
            ),
        )
    raise ValueError(f"不支持的 source_kind: {spec.source_kind}")


def compute_truth_aligned_log_shift_matrix(
    spec: DatasetSpec,
    truth_config: dict[str, Any],
    axis_membership: pd.DataFrame,
) -> pd.DataFrame:
    expression, calls, gene_meta = _load_expression_and_calls(spec, truth_config)
    normalized = log_normalize_csr(
        expression,
        target_sum=float(truth_config["metrics"]["normalization_target_sum"]),
    )
    target_order, gene_order = expected_target_and_gene_order(axis_membership)
    gene_index = pd.Series(
        np.arange(len(gene_meta), dtype=np.int64),
        index=gene_meta["feature_name"].astype(str),
    )
    missing_genes = [gene for gene in gene_order if gene not in gene_index.index]
    if missing_genes:
        raise ValueError(f"{spec.cell_line} 缺少 axis-member genes: {missing_genes}")
    selected_gene_positions = gene_index.loc[gene_order].to_numpy(dtype=np.int64)

    control_mask = calls["is_control"].to_numpy(dtype=bool)
    if int(control_mask.sum()) < int(truth_config["filters"]["min_control_cells"]):
        raise ValueError(f"{spec.cell_line} control cells 不足，无法导出 Stage 2 HCC prediction contract。")

    normalized_selected = normalized[:, selected_gene_positions]
    control_mean = np.asarray(normalized_selected[control_mask].mean(axis=0)).ravel().astype(np.float64)

    records: list[dict[str, object]] = []
    present_targets = set(calls.loc[~calls["is_control"], "target_gene"].astype(str).tolist())
    missing_targets = [target for target in target_order if target not in present_targets]
    if missing_targets:
        raise ValueError(f"{spec.cell_line} 缺少 frozen targets: {missing_targets}")

    for target_gene in target_order:
        target_mask = (~calls["is_control"]).to_numpy() & calls["target_gene"].astype(str).eq(target_gene).to_numpy()
        if not target_mask.any():
            raise ValueError(f"{spec.cell_line} target={target_gene} 没有单扰动细胞。")
        target_mean = np.asarray(normalized_selected[target_mask].mean(axis=0)).ravel().astype(np.float64)
        delta = target_mean - control_mean
        records.append({"target_gene": target_gene, **dict(zip(gene_order, delta.tolist()))})
    return pd.DataFrame(records)


def build_builtin_null_prediction(target_order: list[str], gene_order: list[str]) -> pd.DataFrame:
    records = [{"target_gene": target_gene, **{gene: 0.0 for gene in gene_order}} for target_gene in target_order]
    return pd.DataFrame(records)


def build_builtin_shared_mean_baseline(
    truth_aligned_log_shift: pd.DataFrame,
    axis_membership: pd.DataFrame,
    truth_contract: pd.DataFrame,
) -> pd.DataFrame:
    target_to_expected_axis = (
        axis_membership.loc[:, ["target_gene", "fine_axis"]]
        .drop_duplicates()
        .rename(columns={"fine_axis": "expected_axis"})
    )
    target_roles = target_to_expected_axis.merge(
        truth_contract.loc[:, ["fine_axis", "architecture_role"]].rename(
            columns={"fine_axis": "expected_axis"}
        ),
        on="expected_axis",
        how="left",
        validate="many_to_one",
    )
    backbone_targets = (
        target_roles.loc[target_roles["architecture_role"].eq("canonical_backbone"), "target_gene"]
        .astype(str)
        .tolist()
    )
    if not backbone_targets:
        raise ValueError("没有 canonical_backbone targets，无法构建 shared_mean_baseline。")
    truth_indexed = truth_aligned_log_shift.set_index("target_gene")
    backbone_mean = truth_indexed.loc[backbone_targets].mean(axis=0)
    records = []
    for target_gene in truth_indexed.index.astype(str).tolist():
        records.append({"target_gene": target_gene, **backbone_mean.to_dict()})
    return pd.DataFrame(records)


def align_prediction_to_contract(
    prediction: pd.DataFrame,
    axis_membership: pd.DataFrame,
) -> pd.DataFrame:
    target_order, gene_order = expected_target_and_gene_order(axis_membership)
    if prediction.columns[0] != "target_gene":
        raise ValueError("prediction 首列必须是 target_gene。")
    frame = prediction.copy()
    frame["target_gene"] = frame["target_gene"].astype(str)
    duplicate_targets = frame.loc[frame["target_gene"].duplicated(), "target_gene"].drop_duplicates().tolist()
    if duplicate_targets:
        raise ValueError(f"prediction 出现重复 target_gene: {duplicate_targets}")
    if any(target not in set(frame["target_gene"]) for target in target_order):
        missing_targets = [target for target in target_order if target not in set(frame["target_gene"])]
        raise ValueError(f"prediction 缺少 frozen targets: {missing_targets}")
    if any(gene not in frame.columns for gene in gene_order):
        missing_genes = [gene for gene in gene_order if gene not in frame.columns]
        raise ValueError(f"prediction 缺少 axis-member genes: {missing_genes}")
    aligned = frame.set_index("target_gene").loc[target_order, gene_order].reset_index()
    return aligned


def summarize_raw_prediction_alignment(
    prediction: pd.DataFrame,
    axis_membership: pd.DataFrame,
) -> dict[str, Any]:
    expected_targets, expected_genes = expected_target_and_gene_order(axis_membership)
    first_column = str(prediction.columns[0]) if len(prediction.columns) else ""
    actual_targets = prediction.iloc[:, 0].astype(str).tolist() if not prediction.empty else []
    actual_genes = [str(col) for col in prediction.columns[1:]]
    target_series = pd.Series(actual_targets, dtype="string")
    duplicate_targets = target_series.loc[target_series.duplicated()].drop_duplicates().astype(str).tolist()
    return {
        "first_column": first_column,
        "raw_target_count": len(actual_targets),
        "raw_gene_count": len(actual_genes),
        "raw_duplicate_targets": duplicate_targets,
        "raw_missing_targets": [target for target in expected_targets if target not in set(actual_targets)],
        "raw_missing_genes": [gene for gene in expected_genes if gene not in set(actual_genes)],
        "raw_extra_targets": [target for target in actual_targets if target not in set(expected_targets)],
        "raw_extra_genes": [gene for gene in actual_genes if gene not in set(expected_genes)],
    }


def write_prediction_matrix(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, sep="\t", index=False)


def load_prediction_matrix(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep="\t")
    if frame.empty:
        raise ValueError(f"{path} 为空。")
    return frame


def validate_prediction_contract(
    prediction: pd.DataFrame,
    contract: dict[str, Any],
    manifest: dict[str, Any],
    axis_membership: pd.DataFrame,
) -> dict[str, Any]:
    expected_targets, expected_genes = expected_target_and_gene_order(axis_membership)
    actual_targets = prediction["target_gene"].astype(str).tolist()
    actual_genes = [str(col) for col in prediction.columns[1:]]
    missing_targets = [target for target in expected_targets if target not in set(actual_targets)]
    missing_genes = [gene for gene in expected_genes if gene not in set(actual_genes)]
    extra_targets = [target for target in actual_targets if target not in set(expected_targets)]
    extra_genes = [gene for gene in actual_genes if gene not in set(expected_genes)]
    manifest_missing_fields = [
        field for field in contract["required_manifest_fields"] if field not in manifest
    ]
    prediction_space_matches = manifest.get("prediction_space") == contract.get("prediction_space")
    normalization_matches = (
        manifest.get("normalization_applied_in_export")
        == contract.get("normalization_applied_in_export")
    )
    log1p_matches = manifest.get("log1p_applied_in_export") == contract.get("log1p_applied_in_export")
    target_order_exact = actual_targets == expected_targets
    gene_order_exact = actual_genes == expected_genes
    contract_pass = (
        prediction.columns[0] == contract["required_first_column"]
        and not missing_targets
        and not missing_genes
        and target_order_exact
        and gene_order_exact
        and not manifest_missing_fields
        and prediction_space_matches
        and normalization_matches
        and log1p_matches
    )
    return {
        "stage": "hcc_prediction_contract_validation",
        "first_column_ok": prediction.columns[0] == contract["required_first_column"],
        "expected_target_count": len(expected_targets),
        "actual_target_count": len(actual_targets),
        "expected_gene_count": len(expected_genes),
        "actual_gene_count": len(actual_genes),
        "missing_targets": missing_targets,
        "missing_genes": missing_genes,
        "extra_targets": extra_targets,
        "extra_genes": extra_genes,
        "target_order_exact": target_order_exact,
        "gene_order_exact": gene_order_exact,
        "manifest_missing_fields": manifest_missing_fields,
        "manifest_checks": {
            "prediction_space": manifest.get("prediction_space"),
            "prediction_space_matches_contract": prediction_space_matches,
            "normalization_applied_in_export": manifest.get("normalization_applied_in_export"),
            "normalization_matches_contract": normalization_matches,
            "log1p_applied_in_export": manifest.get("log1p_applied_in_export"),
            "log1p_matches_contract": log1p_matches,
            "object_role": manifest.get("object_role"),
        },
        "contract_pass": contract_pass,
    }


def build_manifest(
    *,
    cell_line: str,
    model_id: str,
    model_version: str,
    object_role: str,
    source_kind: str,
    export_script: str,
    export_timestamp: str,
    contract: dict[str, Any],
    artifacts: ExportArtifacts,
    export_status: str,
    extra_manifest_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "stage": "hcc_prediction_contract",
        "cell_line": cell_line,
        "model_id": model_id,
        "model_version": model_version,
        "prediction_space": contract["prediction_space"],
        "normalization_applied_in_export": contract["normalization_applied_in_export"],
        "log1p_applied_in_export": contract["log1p_applied_in_export"],
        "source_kind": source_kind,
        "object_role": object_role,
        "export_script": export_script,
        "export_timestamp": export_timestamp,
        "input_prediction_path": _stringify_output_path(artifacts.raw_prediction_path),
        "aligned_prediction_path": _stringify_output_path(artifacts.aligned_prediction_path),
        "scorer_ready_prediction_path": _stringify_output_path(artifacts.scorer_ready_prediction_path),
        "target_universe_source": contract["target_universe_source"],
        "gene_space_source": contract["gene_space_source"],
        "allow_missing_targets": contract["missing_target_policy"]["allow_missing_targets"],
        "allow_missing_genes": contract["missing_gene_policy"]["allow_missing_genes"],
        "contract_pass": False,
        "export_status": export_status,
    }
    if extra_manifest_fields:
        payload.update(extra_manifest_fields)
    return payload


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _finalize_export(
    *,
    raw_prediction: pd.DataFrame,
    cell_line: str,
    model_id: str,
    model_version: str,
    object_role: str,
    source_kind: str,
    export_script: str,
    export_timestamp: str,
    contract: dict[str, Any],
    axis_membership: pd.DataFrame,
    artifacts: ExportArtifacts,
    extra_manifest_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    write_prediction_matrix(raw_prediction, artifacts.raw_prediction_path)
    manifest = build_manifest(
        cell_line=cell_line,
        model_id=model_id,
        model_version=model_version,
        object_role=object_role,
        source_kind=source_kind,
        export_script=export_script,
        export_timestamp=export_timestamp,
        contract=contract,
        artifacts=artifacts,
        export_status=EXPORT_STATUS_EXPORT_READY,
        extra_manifest_fields=extra_manifest_fields,
    )

    try:
        raw_alignment_summary = summarize_raw_prediction_alignment(raw_prediction, axis_membership)
        aligned = align_prediction_to_contract(raw_prediction, axis_membership)
    except Exception as exc:
        manifest["export_status"] = EXPORT_STATUS_ALIGNMENT_FAILED
        manifest["alignment_error"] = str(exc)
        write_json(manifest, artifacts.manifest_path)
        raise

    manifest["raw_alignment_summary"] = raw_alignment_summary
    write_prediction_matrix(aligned, artifacts.aligned_prediction_path)
    write_prediction_matrix(aligned, artifacts.scorer_ready_prediction_path)
    validation_summary = validate_prediction_contract(aligned, contract, manifest, axis_membership)
    manifest["contract_pass"] = bool(validation_summary["contract_pass"])
    manifest["export_status"] = (
        EXPORT_STATUS_CONTRACT_VALIDATED
        if validation_summary["contract_pass"]
        else EXPORT_STATUS_SPACE_MISMATCH
    )
    write_json(manifest, artifacts.manifest_path)
    write_json(validation_summary, artifacts.validation_summary_path)
    return {
        "cell_line": cell_line,
        "model_id": model_id,
        "object_role": object_role,
        "raw_prediction_path": _stringify_output_path(artifacts.raw_prediction_path),
        "aligned_prediction_path": _stringify_output_path(artifacts.aligned_prediction_path),
        "scorer_ready_prediction_path": _stringify_output_path(artifacts.scorer_ready_prediction_path),
        "manifest_path": _stringify_output_path(artifacts.manifest_path),
        "validation_summary_path": _stringify_output_path(artifacts.validation_summary_path),
        "export_status": manifest["export_status"],
        "contract_pass": bool(validation_summary["contract_pass"]),
    }


def export_builtin_hcc_prediction(
    *,
    cell_line: str,
    model_id: str,
    model_version: str,
    object_role: str,
    export_timestamp: str,
    truth_config_path: Path = DEFAULT_TRUTH_CONFIG_PATH,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
    axis_membership_path: Path = DEFAULT_AXIS_MEMBERSHIP_PATH,
    truth_contract_path: Path = DEFAULT_TRUTH_CONTRACT_PATH,
) -> dict[str, Any]:
    truth_config = load_config(truth_config_path)
    contract = load_json(contract_path)
    axis_membership = load_axis_membership(axis_membership_path)
    truth_contract = load_truth_contract(truth_contract_path)
    specs = {spec.cell_line: spec for spec in build_dataset_specs(truth_config)}
    if cell_line not in specs:
        raise ValueError(f"未在 Stage 2 truth config 中找到 cell_line={cell_line}")
    spec = specs[cell_line]

    artifacts = build_export_artifacts(contract, model_id=model_id, cell_line=cell_line)
    target_order, gene_order = expected_target_and_gene_order(axis_membership)
    source_kind = f"builtin_{object_role}"

    if object_role == "null":
        raw_prediction = build_builtin_null_prediction(target_order, gene_order)
    elif object_role == "baseline":
        truth_matrix = compute_truth_aligned_log_shift_matrix(spec, truth_config, axis_membership)
        raw_prediction = build_builtin_shared_mean_baseline(
            truth_aligned_log_shift=truth_matrix,
            axis_membership=axis_membership,
            truth_contract=truth_contract,
        )
    else:
        raise ValueError(f"当前 export skeleton 仅支持 builtin null/baseline，收到 object_role={object_role}")

    return _finalize_export(
        raw_prediction=raw_prediction,
        cell_line=cell_line,
        model_id=model_id,
        model_version=model_version,
        object_role=object_role,
        source_kind=source_kind,
        export_script="scripts/pipeline/hcc_prediction_export.py",
        export_timestamp=export_timestamp,
        contract=contract,
        axis_membership=axis_membership,
        artifacts=artifacts,
    )


def export_external_hcc_prediction(
    *,
    cell_line: str,
    model_id: str,
    model_version: str,
    object_role: str,
    export_timestamp: str,
    raw_source: RawPredictionSource,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
    axis_membership_path: Path = DEFAULT_AXIS_MEMBERSHIP_PATH,
) -> dict[str, Any]:
    contract = load_json(contract_path)
    axis_membership = load_axis_membership(axis_membership_path)
    artifacts = build_export_artifacts(contract, model_id=model_id, cell_line=cell_line)
    raw_prediction = load_prediction_matrix(raw_source.prediction_path)
    input_prediction_path = raw_source.prediction_path
    try:
        input_prediction_value = str(input_prediction_path.relative_to(PROJECT_ROOT))
    except ValueError:
        input_prediction_value = str(input_prediction_path)
    extra_manifest_fields = dict(raw_source.extra_manifest_fields or {})
    extra_manifest_fields["input_prediction_path"] = input_prediction_value
    return _finalize_export(
        raw_prediction=raw_prediction,
        cell_line=cell_line,
        model_id=model_id,
        model_version=model_version,
        object_role=object_role,
        source_kind=raw_source.source_kind,
        export_script=raw_source.export_script,
        export_timestamp=export_timestamp,
        contract=contract,
        axis_membership=axis_membership,
        artifacts=artifacts,
        extra_manifest_fields=extra_manifest_fields,
    )
