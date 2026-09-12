"""BIB major revision M5: sampling-aware independent-context qualification."""

from __future__ import annotations

import gc
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse, stats

from wtbench.revision_bridge_sensitivity import (
    infer_association,
    load_context,
)
from wtbench.revision_endpoint_object import categorize_statistic
from wtbench.truth_bridge import build_dataset_specs, load_config


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def closed_form_matched_null(
    mean_control_sd: float,
    n_control: int,
    n_target: np.ndarray | int,
) -> np.ndarray:
    """Expected mean-absolute split under the frozen finite-population null."""
    n_target_array = np.asarray(n_target, dtype=float)
    if n_control < 2 or np.any(n_target_array <= 0) or np.any(n_target_array >= n_control):
        raise ValueError("Require 0 < n_target < n_control and at least two controls.")
    scale = np.sqrt(n_control / (n_target_array * (n_control - n_target_array)))
    return math.sqrt(2.0 / math.pi) * float(mean_control_sd) * scale


def normalized_control_moments_backed(
    matrix: Any,
    positions: np.ndarray,
    *,
    target_sum: float,
    chunk_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Mean and sample SD after cell-wise total-count normalization and log1p."""
    positions = np.asarray(positions, dtype=np.int64)
    if len(positions) < 2:
        raise ValueError("At least two control cells are required.")
    total: np.ndarray | None = None
    total_square: np.ndarray | None = None
    for start in range(0, len(positions), chunk_size):
        index = positions[start : start + chunk_size]
        block = matrix[index]
        if sparse.issparse(block):
            block = block.toarray()
        values = np.asarray(block, dtype=np.float64)
        library = values.sum(axis=1)
        if np.any(library <= 0):
            raise ValueError("Control cells with zero total counts are not supported.")
        values *= (float(target_sum) / library)[:, None]
        np.log1p(values, out=values)
        block_total = values.sum(axis=0, dtype=np.float64)
        block_square = np.square(values).sum(axis=0, dtype=np.float64)
        if total is None:
            total = block_total
            total_square = block_square
        else:
            total += block_total
            total_square += block_square
    assert total is not None and total_square is not None
    n = float(len(positions))
    mean = total / n
    variance = (total_square - n * np.square(mean)) / (n - 1.0)
    sd = np.sqrt(np.maximum(variance, 0.0))
    return mean, sd


def normalized_sparse_sample_sd(matrix: sparse.csr_matrix) -> np.ndarray:
    """Column-wise sample SD for an already normalized sparse matrix."""
    matrix = matrix.tocsr()
    n = matrix.shape[0]
    if n < 2:
        raise ValueError("At least two rows are required.")
    mean = np.asarray(matrix.mean(axis=0)).ravel()
    mean_square = np.asarray(matrix.multiply(matrix).mean(axis=0)).ravel()
    variance = (mean_square - np.square(mean)) * (n / (n - 1.0))
    return np.sqrt(np.maximum(variance, 0.0))


def validate_closed_form_null(config: dict[str, Any]) -> pd.DataFrame:
    validation = config["validation"]
    base_config_path = PROJECT_ROOT / validation["hcc_truth_config"]
    base_config = load_config(base_config_path)
    exact = pd.read_csv(PROJECT_ROOT / validation["m1_exact_null_table"], sep="\t")
    rows: list[dict[str, Any]] = []
    for spec in build_dataset_specs(base_config):
        bridge_path = (
            PROJECT_ROOT
            / "data/processed/truth_driven_bridge"
            / spec.cell_line
            / "target_level_bridge_table.tsv.gz"
        )
        context = load_context(spec, base_config, bridge_path)
        control = context.normalized[context.control_positions].tocsr()
        mean_sd = float(normalized_sparse_sample_sd(control).mean())
        subset = exact.loc[exact["cell_line"].eq(spec.cell_line)].copy()
        predicted = closed_form_matched_null(
            mean_sd,
            control.shape[0],
            subset["n_cells_target"].to_numpy(int),
        )
        observed = subset["matched_null_shift_mean"].to_numpy(float)
        relative = np.abs(predicted - observed) / np.maximum(np.abs(observed), 1e-15)
        pearson = float(stats.pearsonr(predicted, observed).statistic)
        median_error = float(np.median(relative))
        maximum_error = float(np.max(relative))
        passed = (
            median_error <= float(validation["median_relative_error_maximum"])
            and maximum_error <= float(validation["maximum_relative_error_maximum"])
            and pearson >= float(validation["pearson_minimum"])
        )
        rows.append(
            {
                "cell_line": spec.cell_line,
                "n_targets": len(subset),
                "n_control_cells": control.shape[0],
                "n_genes": control.shape[1],
                "mean_gene_control_sd": mean_sd,
                "closed_form_coefficient": float(
                    math.sqrt(2.0 / math.pi) * mean_sd
                ),
                "median_relative_error": median_error,
                "maximum_relative_error": maximum_error,
                "pearson_with_m1_monte_carlo": pearson,
                "validation_pass": bool(passed),
            }
        )
        del context, control
        gc.collect()
    return pd.DataFrame(rows)


def control_and_target_masks(
    obs: pd.DataFrame,
    candidate: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    rule_control = candidate["control_rule"]
    rule_perturbation = candidate["perturbation_rule"]
    if rule_control == "nperts_eq_0" and rule_perturbation == "nperts_eq_1":
        nperts = pd.to_numeric(obs["nperts"], errors="raise")
        return nperts.eq(0).to_numpy(), nperts.eq(1).to_numpy()
    if (
        rule_control == "gene_eq_non-targeting"
        and rule_perturbation == "gene_ne_non-targeting"
    ):
        target = obs[candidate["target_column"]].astype(str)
        return target.eq("non-targeting").to_numpy(), target.ne("non-targeting").to_numpy()
    raise ValueError(f"Unsupported control/perturbation rules: {rule_control}/{rule_perturbation}")


def gene_symbols(adata: ad.AnnData, source: str) -> np.ndarray:
    if source == "var_names":
        values = adata.var_names.astype(str).to_numpy()
    else:
        values = adata.var[source].astype(str).to_numpy()
    return values


def select_response_genes(
    symbols: np.ndarray,
    variances: np.ndarray,
    count: int,
) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "gene_symbol": np.asarray(symbols, dtype=str),
            "control_variance": np.asarray(variances, dtype=float),
            "source_position": np.arange(len(symbols), dtype=int),
        }
    )
    frame = frame.loc[frame["gene_symbol"].ne("") & frame["gene_symbol"].ne("nan")]
    frame = frame.sort_values(
        ["control_variance", "gene_symbol", "source_position"],
        ascending=[False, True, True],
        kind="mergesort",
    ).drop_duplicates("gene_symbol", keep="first")
    frame = frame.head(int(count)).reset_index(drop=True)
    frame.insert(0, "response_rank", np.arange(1, len(frame) + 1, dtype=int))
    return frame


def load_geneformer_mapping(asset_root: Path) -> tuple[dict[Any, Any], dict[str, str]]:
    token_path = asset_root / "token_dictionary_gc104M.pkl"
    name_path = asset_root / "gene_name_id_dict_gc104M.pkl"
    if not token_path.is_file() or not name_path.is_file():
        raise FileNotFoundError(
            "Geneformer dictionaries are missing; run the Pixi materialization task first."
        )
    return pd.read_pickle(token_path), pd.read_pickle(name_path)


def geneformer_target_mask(
    targets: Iterable[str],
    token_dict: dict[Any, Any],
    gene_name_to_ensembl: dict[str, str],
    vocab_size: int,
) -> np.ndarray:
    flags = []
    for target in targets:
        ensembl = gene_name_to_ensembl.get(str(target))
        token = token_dict.get(ensembl) if ensembl is not None else None
        flags.append(token is not None and 0 <= int(token) < int(vocab_size))
    return np.asarray(flags, dtype=bool)


def qualification_pass(row: dict[str, Any], selection: dict[str, Any]) -> bool:
    return bool(
        int(row["n_eligible_targets"]) >= int(selection["minimum_depmap_matched_targets"])
        and float(row["corrected_spearman_rho"]) >= float(selection["minimum_corrected_spearman_rho"])
        and (
            not bool(selection["require_bootstrap_ci_low_above_zero"])
            or float(row["bootstrap_ci_low"]) > 0.0
        )
        and float(row["permutation_pvalue_two_sided"])
        <= float(selection["maximum_permutation_pvalue"])
        and int(row["supported_real_entrants"]) >= int(selection["minimum_real_entrants"])
        and float(row["common_target_coverage"])
        >= float(row["minimum_common_target_coverage"])
    )


def qualify_candidate(
    candidate: dict[str, Any],
    config: dict[str, Any],
    *,
    token_dict: dict[Any, Any],
    gene_name_to_ensembl: dict[str, str],
    vocab_size: int,
    candidate_index: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    h5ad_path = PROJECT_ROOT / candidate["h5ad_path"]
    bridge_path = PROJECT_ROOT / candidate["bridge_table"]
    bridge = pd.read_csv(bridge_path, sep="\t")
    bridge = bridge.loc[
        bridge["depmap_gene_dependency"].notna()
        & bridge["n_cells_target"].ge(int(config["selection"]["minimum_target_cells"]))
    ].drop_duplicates("target_gene").copy()
    bridge["target_gene"] = bridge["target_gene"].astype(str)
    bridge = bridge.sort_values("target_gene").reset_index(drop=True)

    adata = ad.read_h5ad(h5ad_path, backed="r")
    control_mask, perturbation_mask = control_and_target_masks(adata.obs, candidate)
    control_positions = np.flatnonzero(control_mask)
    observed_counts = (
        adata.obs.loc[perturbation_mask, candidate["target_column"]]
        .astype(str)
        .value_counts()
    )
    expected_counts = bridge.set_index("target_gene")["n_cells_target"].astype(int)
    count_match = expected_counts.eq(observed_counts.reindex(expected_counts.index).fillna(0).astype(int))
    if not bool(count_match.all()):
        mismatched = count_match.index[~count_match].tolist()[:10]
        raise ValueError(f"Target-cell counts disagree with the bridge table: {mismatched}")

    control_mean, control_sd = normalized_control_moments_backed(
        adata.X,
        control_positions,
        target_sum=float(config["sampling_null"]["normalization_target_sum"]),
        chunk_size=int(config["sampling_null"]["chunk_size"]),
    )
    mean_sd = float(control_sd.mean())
    bridge["matched_null_shift_closed_form"] = closed_form_matched_null(
        mean_sd,
        len(control_positions),
        bridge["n_cells_target"].to_numpy(int),
    )
    bridge["noise_corrected_shift"] = (
        bridge["real_shift_mean_abs"] - bridge["matched_null_shift_closed_form"]
    )
    inference_cfg = config["inference"]
    inference = infer_association(
        analysis_id="noise_corrected_shift",
        cell_line=candidate["context"],
        x=bridge["noise_corrected_shift"].to_numpy(float),
        y=bridge["depmap_gene_dependency"].to_numpy(float),
        bootstrap_replicates=int(inference_cfg["target_bootstrap_replicates"]),
        permutation_replicates=int(inference_cfg["endpoint_label_permutations"]),
        bootstrap_seed=int(inference_cfg["bootstrap_seed"]) + candidate_index,
        permutation_seed=int(inference_cfg["permutation_seed"]) + candidate_index,
    )

    technical = config["technical_feasibility"]
    mapped = geneformer_target_mask(
        bridge["target_gene"],
        token_dict,
        gene_name_to_ensembl,
        vocab_size,
    )
    bridge["geneformer_target_mappable"] = mapped
    common_coverage = float(mapped.mean())
    supported = len(technical["formal_entrants"]) if common_coverage >= float(
        technical["minimum_common_target_coverage"]
    ) else 1

    category_cfg = config["endpoint_categories"]
    endpoint = categorize_statistic(
        bridge.rename(columns={"context": "cell_line"}).assign(cell_line=candidate["context"]),
        shift_column="noise_corrected_shift",
        prefix="corrected",
        low=float(category_cfg["low_quantile"]),
        high=float(category_cfg["high_quantile"]),
    ).rename(columns={"corrected_category": "endpoint_category"})

    symbols = gene_symbols(adata, candidate["gene_symbol_source"])
    response = select_response_genes(
        symbols,
        np.square(control_sd),
        int(technical["response_gene_count"]),
    )
    adata.file.close()

    raw_rho = float(
        stats.spearmanr(bridge["real_shift_mean_abs"], bridge["depmap_gene_dependency"]).statistic
    )
    row: dict[str, Any] = {
        "candidate_rank": candidate_index + 1,
        "dataset_id": candidate["dataset_id"],
        "context": candidate["context"],
        "status": "evaluated",
        "n_cells_total": int(len(control_mask)),
        "n_control_cells": int(len(control_positions)),
        "n_single_perturbation_cells": int(perturbation_mask.sum()),
        "n_assayed_targets": int(observed_counts.size),
        "n_eligible_targets": int(len(bridge)),
        "n_expression_genes": int(len(symbols)),
        "mean_gene_control_sd": mean_sd,
        "raw_spearman_rho": raw_rho,
        "corrected_spearman_rho": float(inference["spearman_rho"]),
        "bootstrap_ci_low": float(inference["bootstrap_ci_low"]),
        "bootstrap_ci_high": float(inference["bootstrap_ci_high"]),
        "permutation_pvalue_two_sided": float(inference["permutation_pvalue_two_sided"]),
        "geneformer_mapped_targets": int(mapped.sum()),
        "common_target_coverage": common_coverage,
        "minimum_common_target_coverage": float(technical["minimum_common_target_coverage"]),
        "supported_real_entrants": int(supported),
        "response_gene_count": int(len(response)),
    }
    row["qualified"] = qualification_pass(row, config["selection"])
    return endpoint, response, row


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_table(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        path,
        sep="\t",
        index=False,
        compression="gzip" if path.suffix == ".gz" else None,
    )


def run_candidate_qualification(config_path: Path, output_root: Path | None = None) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_root = output_root or PROJECT_ROOT / config["outputs"]["output_root"]
    output_root.mkdir(parents=True, exist_ok=True)

    validation = validate_closed_form_null(config)
    write_table(validation, output_root / config["outputs"]["validation_table"])
    if not bool(validation["validation_pass"].all()):
        raise RuntimeError("Closed-form null failed the frozen HCC validation thresholds.")

    technical = config["technical_feasibility"]
    asset_root = PROJECT_ROOT / technical["geneformer_asset_root"]
    token_dict, gene_name_to_ensembl = load_geneformer_mapping(asset_root)
    checkpoint_root = PROJECT_ROOT / technical["geneformer_checkpoint_path"]
    checkpoint_files = sorted(checkpoint_root.glob("**/model.safetensors"))
    if len(checkpoint_files) != 1:
        raise FileNotFoundError(f"Expected one Geneformer model.safetensors under {checkpoint_root}")
    model_config = json.loads((checkpoint_files[0].parent / "config.json").read_text())
    vocab_size = int(model_config["vocab_size"])

    summary_rows: list[dict[str, Any]] = []
    selected_endpoint: pd.DataFrame | None = None
    selected_response: pd.DataFrame | None = None
    selected_candidate: dict[str, Any] | None = None
    for index, candidate in enumerate(config["candidate_order"]):
        if selected_candidate is not None and bool(config["selection"]["stop_after_first_qualified_candidate"]):
            summary_rows.append(
                {
                    "candidate_rank": index + 1,
                    "dataset_id": candidate["dataset_id"],
                    "context": candidate["context"],
                    "status": "not_evaluated_after_first_qualified_candidate",
                    "qualified": False,
                }
            )
            continue
        endpoint, response, row = qualify_candidate(
            candidate,
            config,
            token_dict=token_dict,
            gene_name_to_ensembl=gene_name_to_ensembl,
            vocab_size=vocab_size,
            candidate_index=index,
        )
        summary_rows.append(row)
        if bool(row["qualified"]):
            selected_candidate = candidate
            selected_endpoint = endpoint
            selected_response = response

    summary = pd.DataFrame(summary_rows)
    write_table(summary, output_root / config["outputs"]["candidate_summary"])
    if selected_candidate is not None:
        assert selected_endpoint is not None and selected_response is not None
        write_table(
            selected_endpoint,
            output_root / config["outputs"]["selected_endpoint_object"],
        )
        write_table(selected_response, output_root / "selected_response_gene_space.tsv")

    decision = {
        "analysis_id": config["analysis_id"],
        "selected_dataset_id": None if selected_candidate is None else selected_candidate["dataset_id"],
        "selected_context": None if selected_candidate is None else selected_candidate["context"],
        "selection_succeeded": selected_candidate is not None,
        "candidate_order": [item["dataset_id"] for item in config["candidate_order"]],
        "selection_rule": config["selection"],
        "formal_entrants": technical["formal_entrants"],
        "independent_model_scores_inspected_before_selection": False,
        "endpoint_categories_frozen_on_full_eligible_context": selected_candidate is not None,
    }
    decision_path = output_root / config["outputs"]["selected_context_decision"]
    decision_path.write_text(json.dumps(decision, indent=2, ensure_ascii=False) + "\n")

    report_lines = [
        "# M5 independent-context candidate qualification",
        "",
        "本阶段只使用 endpoint 与技术可行性信息；selection 前未计算或查看 independent-context model score。",
        "",
        f"- closed-form null validation: {'PASS' if validation['validation_pass'].all() else 'FAIL'}",
        f"- selected context: {decision['selected_context'] or 'none'}",
        f"- formal entrants frozen: {', '.join(technical['formal_entrants'])}",
        "",
    ]
    for row in summary_rows:
        if row["status"] != "evaluated":
            report_lines.append(f"- {row['context']}: {row['status']}")
        else:
            report_lines.append(
                f"- {row['context']}: corrected rho={row['corrected_spearman_rho']:.3f}, "
                f"95% CI [{row['bootstrap_ci_low']:.3f}, {row['bootstrap_ci_high']:.3f}], "
                f"permutation P={row['permutation_pvalue_two_sided']:.4g}, "
                f"n={row['n_eligible_targets']}, qualified={row['qualified']}"
            )
    report_path = output_root / config["outputs"]["report"]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    input_paths = [
        config_path,
        PROJECT_ROOT / config["amendment"],
        PROJECT_ROOT / config["validation"]["m1_exact_null_table"],
        PROJECT_ROOT / config["validation"]["m1_truth_validation"],
        PROJECT_ROOT / config["validation"]["hcc_truth_config"],
        checkpoint_files[0],
        checkpoint_files[0].parent / "config.json",
        asset_root / "token_dictionary_gc104M.pkl",
        asset_root / "gene_name_id_dict_gc104M.pkl",
    ]
    hcc_config = json.loads(
        (PROJECT_ROOT / config["validation"]["hcc_truth_config"]).read_text(encoding="utf-8")
    )
    for dataset in hcc_config["datasets"]:
        for key in (
            "matrix_path",
            "barcodes_path",
            "features_path",
            "protospacer_calls_path",
        ):
            input_paths.append(PROJECT_ROOT / dataset[key])
        input_paths.append(
            PROJECT_ROOT
            / "data/processed/truth_driven_bridge"
            / dataset["cell_line"]
            / "target_level_bridge_table.tsv.gz"
        )
    evaluated_ids = set(summary.loc[summary["status"].eq("evaluated"), "dataset_id"])
    for candidate in config["candidate_order"]:
        if candidate["dataset_id"] in evaluated_ids:
            input_paths.extend(
                [PROJECT_ROOT / candidate["h5ad_path"], PROJECT_ROOT / candidate["bridge_table"]]
            )
    output_paths = [
        output_root / config["outputs"]["validation_table"],
        output_root / config["outputs"]["candidate_summary"],
        decision_path,
        report_path,
    ]
    if selected_candidate is not None:
        output_paths.extend(
            [
                output_root / config["outputs"]["selected_endpoint_object"],
                output_root / "selected_response_gene_space.tsv",
            ]
        )
    manifest = {
        "analysis_id": config["analysis_id"],
        "selected_dataset_id": decision["selected_dataset_id"],
        "validation_pass": bool(validation["validation_pass"].all()),
        "independent_model_scores_inspected_before_selection": False,
        "inputs": [file_record(path) for path in input_paths],
        "outputs": [file_record(path) for path in output_paths],
    }
    manifest_path = output_root / config["outputs"]["run_manifest"]
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest
