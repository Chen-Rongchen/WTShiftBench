"""BIB major revision M5: full audit in the selected independent context."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
import yaml
from scipy import sparse
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer

from wtbench.revision_hcc_audit import (
    bh_qvalues,
    build_metric_long,
    endpoint_label_permutation_pvalue,
)
from wtbench.revision_metric_validity import score_context, sha256_file


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def normalize_count_block(values: Any, target_sum: float) -> np.ndarray:
    if sparse.issparse(values):
        values = values.toarray()
    normalized = np.asarray(values, dtype=np.float64)
    library = normalized.sum(axis=1)
    if np.any(library <= 0):
        raise ValueError("Zero-count cells are not supported in the M5 contract.")
    normalized *= (float(target_sum) / library)[:, None]
    np.log1p(normalized, out=normalized)
    return normalized


def materialize_observed_contract(
    h5ad_path: Path,
    endpoint: pd.DataFrame,
    response: pd.DataFrame,
    contract: dict[str, Any],
) -> pd.DataFrame:
    adata = ad.read_h5ad(h5ad_path, backed="r")
    targets = endpoint["target_gene"].astype(str).tolist()
    genes = response.sort_values("response_rank")["gene_symbol"].astype(str).tolist()
    positions = response.sort_values("response_rank")["source_position"].to_numpy(int)
    if adata.var_names.astype(str).to_numpy()[positions].tolist() != genes:
        raise ValueError("Frozen response-gene positions no longer match the h5ad var axis.")

    target_lookup = {target: index for index, target in enumerate(targets)}
    obs_target = adata.obs[contract["target_column"]].astype(str)
    nperts = pd.to_numeric(adata.obs["nperts"], errors="raise").to_numpy()
    codes = np.full(adata.n_obs, -2, dtype=np.int32)
    codes[nperts == 0] = -1
    single_positions = np.flatnonzero(nperts == 1)
    mapped = obs_target.iloc[single_positions].map(target_lookup)
    keep = mapped.notna().to_numpy()
    codes[single_positions[keep]] = mapped.loc[mapped.notna()].to_numpy(dtype=np.int32)

    target_sum = np.zeros((len(targets), len(genes)), dtype=np.float64)
    target_counts = np.zeros(len(targets), dtype=np.int64)
    control_sum = np.zeros(len(genes), dtype=np.float64)
    control_count = 0
    chunk_size = int(contract["matrix_chunk_size"])
    for start in range(0, adata.n_obs, chunk_size):
        stop = min(start + chunk_size, adata.n_obs)
        chunk_codes = codes[start:stop]
        relevant = chunk_codes >= -1
        if not relevant.any():
            continue
        normalized = normalize_count_block(
            adata.X[start:stop],
            float(contract["normalization_target_sum"]),
        )[:, positions]
        control = chunk_codes == -1
        if control.any():
            control_sum += normalized[control].sum(axis=0)
            control_count += int(control.sum())
        perturbed = chunk_codes >= 0
        if perturbed.any():
            selected_codes = chunk_codes[perturbed]
            np.add.at(target_sum, selected_codes, normalized[perturbed])
            np.add.at(target_counts, selected_codes, 1)
    adata.file.close()

    expected = endpoint.set_index("target_gene").loc[targets, "n_cells_target"].to_numpy(int)
    if not np.array_equal(target_counts, expected):
        raise ValueError("Observed-contract target counts do not match the frozen endpoint object.")
    if control_count <= 0:
        raise ValueError("No control cells were materialized.")
    observed = target_sum / target_counts[:, None] - control_sum[None, :] / control_count
    return pd.DataFrame(observed, index=pd.Index(targets, name="target_gene"), columns=genes)


def save_contract_npz(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        values=frame.to_numpy(dtype=np.float32),
        targets=frame.index.to_numpy(dtype=str),
        genes=frame.columns.to_numpy(dtype=str),
    )


def load_contract_npz(path: Path) -> pd.DataFrame:
    with np.load(path, allow_pickle=False) as payload:
        return pd.DataFrame(
            payload["values"].astype(np.float64),
            index=pd.Index(payload["targets"].astype(str), name="target_gene"),
            columns=payload["genes"].astype(str),
        )


def load_geneformer_features(config: dict[str, Any], targets: list[str]) -> np.ndarray:
    from scripts.stage1a.adapters.geneformer.build_predictions import (
        load_geneformer_word_embedding_weight,
        resolve_geneformer_checkpoint_dir,
    )

    inputs = config["inputs"]
    registry = yaml.safe_load((PROJECT_ROOT / inputs["checkpoint_registry"]).read_text())
    entry = registry["checkpoints"][inputs["checkpoint_key"]]
    checkpoint_dir = resolve_geneformer_checkpoint_dir(
        PROJECT_ROOT / entry["local_resolved_path"]
    )
    weight = load_geneformer_word_embedding_weight(checkpoint_dir).numpy().astype(np.float64)
    asset_root = PROJECT_ROOT / inputs["geneformer_asset_root"]
    token_dict = pd.read_pickle(asset_root / "token_dictionary_gc104M.pkl")
    name_to_ensembl = pd.read_pickle(asset_root / "gene_name_id_dict_gc104M.pkl")
    token_ids = []
    for target in targets:
        ensembl = name_to_ensembl.get(target)
        token = token_dict.get(ensembl) if ensembl is not None else None
        if token is None or not 0 <= int(token) < len(weight):
            raise ValueError(f"Geneformer target is not mappable: {target}")
        token_ids.append(int(token))
    return weight[np.asarray(token_ids, dtype=np.int64)]


def cosine_kernel_loo(
    features: np.ndarray,
    responses: np.ndarray,
    *,
    top_k: int,
    temperature: float,
) -> np.ndarray:
    features = np.asarray(features, dtype=np.float64)
    responses = np.asarray(responses, dtype=np.float64)
    unit = features / np.maximum(np.linalg.norm(features, axis=1, keepdims=True), 1e-15)
    similarity = unit @ unit.T
    np.fill_diagonal(similarity, -np.inf)
    k = min(max(1, int(top_k)), len(features) - 1)
    indices = np.argpartition(similarity, -k, axis=1)[:, -k:]
    selected = np.take_along_axis(similarity, indices, axis=1)
    logits = selected / max(float(temperature), 1e-12)
    logits -= logits.max(axis=1, keepdims=True)
    weights = np.exp(logits)
    weights /= weights.sum(axis=1, keepdims=True)
    return np.einsum("ik,ikg->ig", weights, responses[indices], optimize=True)


def ridge_press_loo(
    features: np.ndarray,
    responses: np.ndarray,
    *,
    ridge_lambda: float,
) -> np.ndarray:
    """Exact LOO predictions for a fixed-feature multivariate ridge smoother."""
    features = np.asarray(features, dtype=np.float64)
    responses = np.asarray(responses, dtype=np.float64)
    design = np.column_stack([np.ones(len(features)), features])
    penalty = np.eye(design.shape[1], dtype=np.float64) * float(ridge_lambda)
    penalty[0, 0] = 0.0
    inverse = np.linalg.pinv(design.T @ design + penalty)
    coefficients = inverse @ design.T @ responses
    fitted = design @ coefficients
    leverage = np.einsum("ij,jk,ik->i", design, inverse, design, optimize=True)
    denominator = 1.0 - leverage
    if np.any(np.abs(denominator) <= 1e-10):
        raise ValueError("Ridge PRESS denominator is numerically zero.")
    return (fitted - leverage[:, None] * responses) / denominator[:, None]


def geneformer_ridge_features(
    features: np.ndarray,
    *,
    n_components: int,
    seed: int,
) -> np.ndarray:
    return PCA(
        n_components=int(n_components),
        svd_solver="randomized",
        random_state=int(seed),
    ).fit_transform(features)


def chargram_features(
    targets: list[str],
    *,
    ngram_min: int,
    ngram_max: int,
    n_components: int,
    seed: int,
) -> np.ndarray:
    matrix = CountVectorizer(
        analyzer="char",
        ngram_range=(int(ngram_min), int(ngram_max)),
        min_df=1,
    ).fit_transform(targets)
    return TruncatedSVD(
        n_components=int(n_components),
        random_state=int(seed),
    ).fit_transform(matrix)


def build_predictions(
    config: dict[str, Any],
    observed: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    targets = observed.index.astype(str).tolist()
    responses = observed.to_numpy(dtype=np.float64)
    geneformer = load_geneformer_features(config, targets)
    predictions: dict[str, pd.DataFrame] = {}
    completion_rows: list[dict[str, Any]] = []
    for entrant in config["formal_entrants"]:
        model_id = entrant["model_id"]
        if entrant["method"] == "cosine_kernel_loo":
            values = cosine_kernel_loo(
                geneformer,
                responses,
                top_k=int(entrant["top_k"]),
                temperature=float(entrant["temperature"]),
            )
            feature_shape = list(geneformer.shape)
        elif entrant["feature_source"] == "geneformer_embedding_pca":
            features = geneformer_ridge_features(
                geneformer,
                n_components=int(entrant["n_components"]),
                seed=int(entrant["feature_seed"]),
            )
            values = ridge_press_loo(
                features,
                responses,
                ridge_lambda=float(entrant["ridge_lambda"]),
            )
            feature_shape = list(features.shape)
        else:
            features = chargram_features(
                targets,
                ngram_min=int(entrant["ngram_min"]),
                ngram_max=int(entrant["ngram_max"]),
                n_components=int(entrant["n_components"]),
                seed=int(entrant["feature_seed"]),
            )
            values = ridge_press_loo(
                features,
                responses,
                ridge_lambda=float(entrant["ridge_lambda"]),
            )
            feature_shape = list(features.shape)
        if not np.isfinite(values).all() or values.shape != responses.shape:
            raise ValueError(f"Invalid prediction contract for {model_id}")
        predictions[model_id] = pd.DataFrame(values, index=observed.index, columns=observed.columns)
        completion_rows.append(
            {
                "model_id": model_id,
                "display_name": entrant["display_name"],
                "model_family": entrant["model_family"],
                "completion_call": "valid_for_full_audit",
                "target_heldout": True,
                "heldout_response_used_for_own_prediction": False,
                "n_targets": len(observed),
                "n_genes": observed.shape[1],
                "feature_shape": "x".join(map(str, feature_shape)),
            }
        )
    return predictions, pd.DataFrame(completion_rows)


def reference_predictions(
    observed: pd.DataFrame,
    seed: int,
) -> dict[str, pd.DataFrame]:
    values = observed.to_numpy(dtype=np.float64)
    rng = np.random.default_rng(seed)
    random = rng.normal(size=values.shape)
    random /= np.maximum(np.linalg.norm(random, axis=1, keepdims=True), 1e-15)
    random *= np.linalg.norm(values, axis=1, keepdims=True)
    shared = np.repeat(values.mean(axis=0, keepdims=True), len(values), axis=0)
    return {
        "observed_shift_oracle": observed.copy(),
        "negated_oracle": pd.DataFrame(-values, index=observed.index, columns=observed.columns),
        "observed_magnitude_random_direction": pd.DataFrame(
            random, index=observed.index, columns=observed.columns
        ),
        "shared_mean_baseline": pd.DataFrame(
            shared, index=observed.index, columns=observed.columns
        ),
    }


def _derived_seed(base: int, text: str) -> int:
    offset = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16) % 1_000_000
    return int(base + offset)


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def run_m5_full_audit(config_path: Path, output_root: Path | None = None) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    decision = json.loads((PROJECT_ROOT / config["selection_decision"]).read_text())
    if decision["selected_dataset_id"] != "replogle_k562_essential_day6":
        raise ValueError("M5 full-audit config does not match the frozen selection decision.")
    output_root = output_root or PROJECT_ROOT / config["outputs"]["root"]
    matrix_root = PROJECT_ROOT / config["outputs"]["matrix_root"]
    output_root.mkdir(parents=True, exist_ok=True)
    matrix_root.mkdir(parents=True, exist_ok=True)

    endpoint = pd.read_csv(PROJECT_ROOT / config["inputs"]["endpoint_object"], sep="\t")
    endpoint["context_role"] = config["contract"]["context_role"]
    response = pd.read_csv(PROJECT_ROOT / config["inputs"]["response_gene_space"], sep="\t")
    if len(endpoint) != int(config["contract"]["target_count"]) or len(response) != int(
        config["contract"]["response_gene_count"]
    ):
        raise ValueError("Frozen M5 target/gene counts do not match the full-audit contract.")

    observed = materialize_observed_contract(
        PROJECT_ROOT / config["inputs"]["h5ad"], endpoint, response, config["contract"]
    )
    observed_path = matrix_root / config["outputs"]["observed_matrix"]
    save_contract_npz(observed, observed_path)
    predictions, completion = build_predictions(config, observed)
    matrix_paths: list[Path] = [observed_path]
    for model_id, frame in predictions.items():
        name = config["outputs"]["prediction_template"].replace("<model_id>", model_id)
        path = matrix_root / name
        save_contract_npz(frame, path)
        matrix_paths.append(path)
        restored = load_contract_npz(path)
        if not restored.index.equals(frame.index) or not restored.columns.equals(frame.columns):
            raise ValueError(f"NPZ contract axes changed for {model_id}")

    metric_spec = json.loads((PROJECT_ROOT / config["metric_spec"]).read_text())
    formal_spec = copy.deepcopy(metric_spec)
    formal_spec["inference"].update(
        {
            "bootstrap_replicates": config["inference"]["bootstrap_replicates"],
            "bootstrap_seed": config["inference"]["bootstrap_seed"],
            "target_identity_permutations": config["inference"]["target_identity_permutations"],
            "target_identity_seed": config["inference"]["target_identity_seed"],
        }
    )
    reference_spec = copy.deepcopy(formal_spec)
    reference_spec["inference"]["target_identity_permutations"] = 0

    entrant_lookup = {item["model_id"]: item for item in config["formal_entrants"]}
    target_frames: list[pd.DataFrame] = []
    context_rows: list[dict[str, Any]] = []
    for model_id, prediction in predictions.items():
        target, summary = score_context(
            prediction=prediction,
            observed=observed,
            endpoint=endpoint,
            cell_line=config["contract"]["context"],
            entrant_id=model_id,
            reference_type="",
            reference_seed=None,
            config=formal_spec,
        )
        entrant = entrant_lookup[model_id]
        target["entrant_kind"] = "formal"
        target["display_name"] = entrant["display_name"]
        target["model_family"] = entrant["model_family"]
        summary.update(
            {
                "entrant_role": "formal",
                "entrant_kind": "formal",
                "display_name": entrant["display_name"],
                "model_family": entrant["model_family"],
                "endpoint_alignment_label_permutation_pvalue": endpoint_label_permutation_pvalue(
                    target["predicted_shift_mean_abs"].to_numpy(float),
                    target["depmap_gene_dependency"].to_numpy(float),
                    permutations=int(config["inference"]["endpoint_label_permutations"]),
                    seed=_derived_seed(int(config["inference"]["endpoint_label_seed"]), model_id),
                ),
            }
        )
        target_frames.append(target)
        context_rows.append(summary)

    references = reference_predictions(observed, int(config["references"]["random_direction_seed"]))
    for reference_id, prediction in references.items():
        reference_seed = (
            int(config["references"]["random_direction_seed"])
            if reference_id == "observed_magnitude_random_direction"
            else None
        )
        target, summary = score_context(
            prediction=prediction,
            observed=observed,
            endpoint=endpoint,
            cell_line=config["contract"]["context"],
            entrant_id=reference_id,
            reference_type=reference_id,
            reference_seed=reference_seed,
            config=reference_spec,
        )
        target["entrant_kind"] = "reference"
        target["display_name"] = reference_id
        target["model_family"] = "reference"
        summary.update(
            {
                "entrant_role": "reference",
                "entrant_kind": "reference",
                "display_name": reference_id,
                "model_family": "reference",
                "endpoint_alignment_label_permutation_pvalue": np.nan,
            }
        )
        target_frames.append(target)
        context_rows.append(summary)

    target_metrics = pd.concat(target_frames, ignore_index=True)
    context_metrics = pd.DataFrame(context_rows)
    formal = context_metrics["entrant_role"].eq("formal")
    context_metrics["endpoint_alignment_permutation_qvalue_bh"] = np.nan
    context_metrics.loc[formal, "endpoint_alignment_permutation_qvalue_bh"] = bh_qvalues(
        context_metrics.loc[formal, "endpoint_alignment_label_permutation_pvalue"]
    )
    context_metrics["target_identity_permutation_qvalue_bh"] = np.nan
    context_metrics.loc[formal, "target_identity_permutation_qvalue_bh"] = bh_qvalues(
        context_metrics.loc[formal, "target_identity_label_permutation_pvalue"]
    )
    metric_long = build_metric_long(context_metrics)

    oracle = context_metrics.set_index("entrant_id")
    random_target = target_metrics.loc[
        target_metrics["entrant_id"].eq("observed_magnitude_random_direction")
    ]
    observed_l2 = random_target["observed_contract_shift_l2"].to_numpy(float)
    l2_relative = np.abs(
        random_target["predicted_shift_l2"].to_numpy(float) - observed_l2
    ) / np.maximum(observed_l2, 1e-15)
    validation = pd.DataFrame(
        [
            {
                "check": "oracle_direction",
                "observed": oracle.loc["observed_shift_oracle", "directional_recovery_median_signed_cosine"],
                "expected": 1.0,
                "pass": abs(oracle.loc["observed_shift_oracle", "directional_recovery_median_signed_cosine"] - 1.0) <= 1e-10,
            },
            {
                "check": "negated_direction",
                "observed": oracle.loc["negated_oracle", "directional_recovery_median_signed_cosine"],
                "expected": -1.0,
                "pass": abs(oracle.loc["negated_oracle", "directional_recovery_median_signed_cosine"] + 1.0) <= 1e-10,
            },
            {
                "check": "magnitude_only_l2",
                "observed": float(l2_relative.max()),
                "expected": 0.0,
                "pass": float(l2_relative.max()) <= 1e-10,
            },
            {
                "check": "shared_mean_homogenization",
                "observed": oracle.loc["shared_mean_baseline", "predicted_homogenization_uncentered"],
                "expected": 1.0,
                "pass": oracle.loc["shared_mean_baseline", "predicted_homogenization_uncentered"] >= 0.999999,
            },
        ]
    )
    if not validation["pass"].all():
        raise RuntimeError("M5 reference validation failed.")

    outputs = config["outputs"]
    target_path = output_root / outputs["target_metrics"]
    context_path = output_root / outputs["context_metrics"]
    metric_path = output_root / outputs["metric_long"]
    validation_path = output_root / outputs["reference_validation"]
    completion_path = output_root / outputs["completion"]
    training_path = output_root / outputs["training_registry"]
    target_metrics.to_csv(target_path, sep="\t", index=False, compression="gzip")
    context_metrics.to_csv(context_path, sep="\t", index=False, na_rep="NA")
    metric_long.to_csv(metric_path, sep="\t", index=False, na_rep="NA")
    validation.to_csv(validation_path, sep="\t", index=False, na_rep="NA")
    completion.to_csv(completion_path, sep="\t", index=False, na_rep="NA")
    training = completion.assign(
        context=config["contract"]["context"],
        training_setting="same-context target-level responses with exact leave-one-target-out",
        checkpoint_or_feature_source=[
            "Geneformer gf-12L-95M-i4096 target embedding",
            "Geneformer gf-12L-95M-i4096 target embedding PCA-32",
            "gene-symbol character 2-4 grams TruncatedSVD-32",
        ],
    )
    training.to_csv(training_path, sep="\t", index=False, na_rep="NA")

    formal_table = context_metrics.loc[formal].sort_values("entrant_id")
    report_lines = [
        "# M5 independent-context full audit",
        "",
        f"Context: {config['contract']['context']} ({len(observed)} targets × {observed.shape[1]} genes).",
        "All three formal entrants use target-held-out predictions; the held-out target response is not used for its own prediction.",
        "",
        "| Entrant | endpoint rho [95% CI] (P/q) | signed cosine [95% CI] | anchor AUC [95% CI] | identity rho (P/q) | delta H | centered delta H | Pearson | nRMSE |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in formal_table.iterrows():
        report_lines.append(
            f"| {row['display_name']} | {row['endpoint_alignment_spearman']:.3f} "
            f"[{row['endpoint_alignment_ci_low']:.3f}, {row['endpoint_alignment_ci_high']:.3f}] "
            f"({row['endpoint_alignment_label_permutation_pvalue']:.4f}/{row['endpoint_alignment_permutation_qvalue_bh']:.4f}) | "
            f"{row['directional_recovery_median_signed_cosine']:.3f} "
            f"[{row['directional_recovery_ci_low']:.3f}, {row['directional_recovery_ci_high']:.3f}] | "
            f"{row['anchor_separation_auc']:.3f} [{row['anchor_separation_ci_low']:.3f}, {row['anchor_separation_ci_high']:.3f}] | "
            f"{row['target_identity_spearman']:.3f} "
            f"({row['target_identity_label_permutation_pvalue']:.4f}/{row['target_identity_permutation_qvalue_bh']:.4f}) | "
            f"{row['excess_homogenization_uncentered']:.3f} | "
            f"{row['excess_homogenization_centered']:.3f} | {row['conventional_pearson_median']:.3f} | "
            f"{row['conventional_normalized_rmse_median']:.3f} |"
        )
    report_lines.extend(
        [
            "",
            "Endpoint P values use two-sided label permutation; identity P values use one-sided full-pair target-label/Mantel permutation.",
            "Geneformer ridge and chargram ridge have similar reconstruction summaries but disagree in endpoint ordering and target identity, providing an independent-context audit-discordance example.",
            "Uncentered excess homogenization is interpreted together with the observed reference and target-centered sensitivity; no universal cutoff is used.",
            "No composite ranking is recommended.",
        ]
    )
    report_path = output_root / outputs["report"]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    input_paths = [
        config_path,
        PROJECT_ROOT / config["amendment"],
        *(PROJECT_ROOT / path for path in config.get("implementation_amendments", [])),
        PROJECT_ROOT / config["metric_spec"],
        PROJECT_ROOT / config["selection_decision"],
        PROJECT_ROOT / config["inputs"]["endpoint_object"],
        PROJECT_ROOT / config["inputs"]["response_gene_space"],
        PROJECT_ROOT / config["inputs"]["h5ad"],
        PROJECT_ROOT / config["inputs"]["checkpoint_registry"],
        PROJECT_ROOT / config["inputs"]["geneformer_asset_root"] / "token_dictionary_gc104M.pkl",
        PROJECT_ROOT / config["inputs"]["geneformer_asset_root"] / "gene_name_id_dict_gc104M.pkl",
        PROJECT_ROOT / "src/wtbench/revision_m5_audit.py",
        PROJECT_ROOT / "src/wtbench/revision_metric_validity.py",
    ]
    registry = yaml.safe_load((PROJECT_ROOT / config["inputs"]["checkpoint_registry"]).read_text())
    checkpoint_root = PROJECT_ROOT / registry["checkpoints"][config["inputs"]["checkpoint_key"]]["local_resolved_path"]
    checkpoint_file = next(checkpoint_root.glob("**/model.safetensors"))
    input_paths.extend([checkpoint_file, checkpoint_file.parent / "config.json"])
    output_paths = [
        *matrix_paths,
        target_path,
        context_path,
        metric_path,
        validation_path,
        completion_path,
        training_path,
        report_path,
    ]
    manifest = {
        "audit_id": config["audit_id"],
        "context": config["contract"]["context"],
        "formal_entrants_completed": int(completion["completion_call"].eq("valid_for_full_audit").sum()),
        "reference_checks_passed": int(validation["pass"].sum()),
        "independent_model_scores_seen_before_context_selection": False,
        "inputs": [file_record(path) for path in input_paths],
        "outputs": [file_record(path) for path in output_paths],
    }
    manifest_path = output_root / outputs["manifest"]
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest
