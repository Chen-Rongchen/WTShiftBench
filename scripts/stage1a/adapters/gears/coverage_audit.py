from __future__ import annotations

import argparse
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import yaml
from scipy import sparse

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from scripts.stage1a_split_plan_b import load_split_governance, plan_b_heldout_targets
from scripts.stage1a.benchmark_invariant.prediction_eval_common import json_dump, resolve_project_relative


DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "reports/stage1a_audit/gears_coverage_audit"
DEFAULT_ELIGIBILITY_PATH = PROJECT_ROOT / "reports/stage1a/pseudobulk_eligibility"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="审计 GEARS 在指定 dataset 上的 held-out coverage / support / abundance。")
    parser.add_argument("--run-config", required=True)
    return parser


def load_run_config(run_config_path: str) -> dict[str, object]:
    return yaml.safe_load(Path(run_config_path).read_text(encoding="utf-8")) or {}


def coalesce_arg(config: dict[str, object], key: str, default=None):
    if key in config:
        return config[key]
    return default


def resolve_path(path_value: str | Path | None) -> Path | None:
    if path_value is None:
        return None
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def tercile_labels(n: int) -> list[str]:
    base = n // 3
    remainder = n % 3
    low_n = base + (1 if remainder >= 1 else 0)
    mid_n = base + (1 if remainder >= 2 else 0)
    high_n = n - low_n - mid_n
    return ["low_support"] * low_n + ["mid_support"] * mid_n + ["high_support"] * high_n


def mean_vector(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        return np.asarray(matrix.mean(axis=0)).ravel().astype(np.float64, copy=False)
    return np.asarray(matrix.mean(axis=0)).ravel().astype(np.float64, copy=False)


def detection_fraction(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        return np.asarray((matrix > 0).mean(axis=0)).ravel().astype(np.float64, copy=False)
    return np.mean(np.asarray(matrix) > 0, axis=0).astype(np.float64, copy=False)


def summarize_support(frame: pd.DataFrame) -> dict[str, float]:
    return {
        "n_targets": int(len(frame)),
        "min_n_cells_perturbed": int(frame["n_cells_perturbed"].min()),
        "median_n_cells_perturbed": float(frame["n_cells_perturbed"].median()),
        "max_n_cells_perturbed": int(frame["n_cells_perturbed"].max()),
    }


def main() -> None:
    args = build_parser().parse_args()
    run_config = load_run_config(args.run_config)

    dataset_id = str(coalesce_arg(run_config, "dataset_id", "tian_2019_day7neuron"))
    model_id = str(coalesce_arg(run_config, "model_id", "gears_stage1a_formal"))
    split_seed = int(
        coalesce_arg(
            run_config,
            "split_seed",
            load_split_governance()["default_split_seed_for_truth_freeze"],
        )
    )
    formal_h5ad_path = resolve_path(coalesce_arg(run_config, "formal_h5ad_path", None))
    if formal_h5ad_path is None:
        raise ValueError("run-config 缺少 formal_h5ad_path。")

    eligibility_root = resolve_path(coalesce_arg(run_config, "eligibility_root", DEFAULT_ELIGIBILITY_PATH))
    output_root = resolve_path(coalesce_arg(run_config, "output_root", DEFAULT_OUTPUT_ROOT))
    assert eligibility_root is not None
    assert output_root is not None

    eligibility_path = eligibility_root / dataset_id / "perturbation_eligibility.tsv"
    eligibility = pd.read_csv(eligibility_path, sep="\t")
    eligibility["eligible_for_pseudobulk"] = (
        eligibility["eligible_for_pseudobulk"].astype("string").str.lower().eq("true")
    )
    eligible = eligibility.loc[eligibility["eligible_for_pseudobulk"]].copy()
    eligible["target_gene"] = eligible["target_gene"].astype(str)
    eligible["n_cells_perturbed"] = pd.to_numeric(eligible["n_cells_perturbed"], errors="raise").astype(int)
    eligible["n_cells_control"] = pd.to_numeric(eligible["n_cells_control"], errors="raise").astype(int)
    eligible = eligible.sort_values(["n_cells_perturbed", "target_gene"], ascending=[True, True]).reset_index(drop=True)
    eligible["support_rank_ascending"] = np.arange(1, len(eligible) + 1, dtype=int)
    eligible["support_rank_descending"] = np.arange(len(eligible), 0, -1, dtype=int)
    eligible["support_percentile"] = eligible["support_rank_ascending"] / float(len(eligible))
    eligible["support_stratum"] = tercile_labels(len(eligible))

    heldout_targets = plan_b_heldout_targets(eligible, dataset_id, split_seed)
    heldout_set = set(heldout_targets)
    eligible["is_heldout"] = eligible["target_gene"].isin(heldout_set)
    eligible["is_train"] = ~eligible["is_heldout"]

    adata = ad.read_h5ad(formal_h5ad_path)
    obs = adata.obs.copy()
    obs["is_control"] = obs["is_control"].astype(bool)
    obs["target_gene"] = obs["target_gene"].astype("string").fillna("")

    var_names = adata.var.index.astype(str)
    gene_index = pd.Index(var_names)
    control_mask = obs["is_control"].to_numpy()
    control_mean = mean_vector(adata.X[control_mask])
    control_detect = detection_fraction(adata.X[control_mask])

    records: list[dict[str, object]] = []
    for row in eligible.itertuples(index=False):
        target = str(row.target_gene)
        pert_mask = (~obs["is_control"]).to_numpy() & obs["target_gene"].eq(target).to_numpy()
        pert_count_obs = int(pert_mask.sum())
        gene_pos = int(gene_index.get_loc(target)) if target in gene_index else -1

        target_control_mean = None
        target_perturbed_mean = None
        target_delta = None
        target_control_detect = None
        target_perturbed_detect = None
        if gene_pos >= 0:
            pert_mean = mean_vector(adata.X[pert_mask]) if pert_count_obs > 0 else None
            pert_detect = detection_fraction(adata.X[pert_mask]) if pert_count_obs > 0 else None
            target_control_mean = float(control_mean[gene_pos])
            target_control_detect = float(control_detect[gene_pos])
            if pert_mean is not None and pert_detect is not None:
                target_perturbed_mean = float(pert_mean[gene_pos])
                target_perturbed_detect = float(pert_detect[gene_pos])
                target_delta = float(target_perturbed_mean - target_control_mean)

        records.append(
            {
                "target_gene": target,
                "n_cells_perturbed_eligibility": int(row.n_cells_perturbed),
                "n_cells_perturbed_formal_h5ad": pert_count_obs,
                "n_cells_control": int(row.n_cells_control),
                "support_rank_ascending": int(row.support_rank_ascending),
                "support_rank_descending": int(row.support_rank_descending),
                "support_percentile": float(row.support_percentile),
                "support_stratum": str(row.support_stratum),
                "is_heldout": bool(row.is_heldout),
                "target_in_var_names": bool(gene_pos >= 0),
                "target_control_mean_expression": target_control_mean,
                "target_perturbed_mean_expression": target_perturbed_mean,
                "target_delta_expression": target_delta,
                "target_control_detection_fraction": target_control_detect,
                "target_perturbed_detection_fraction": target_perturbed_detect,
            }
        )

    target_df = pd.DataFrame.from_records(records)
    heldout_df = (
        target_df.loc[target_df["is_heldout"]]
        .copy()
        .sort_values(["support_rank_ascending", "target_gene"])
        .reset_index(drop=True)
    )
    train_df = (
        target_df.loc[~target_df["is_heldout"]]
        .copy()
        .sort_values(["support_rank_ascending", "target_gene"])
        .reset_index(drop=True)
    )

    summary = {
        "stage": "gears_coverage_audit",
        "dataset_id": dataset_id,
        "model_id": model_id,
        "split_seed": split_seed,
        "formal_h5ad_path": resolve_project_relative(formal_h5ad_path),
        "eligibility_path": resolve_project_relative(eligibility_path),
        "n_obs": int(adata.n_obs),
        "n_vars": int(adata.n_vars),
        "n_control_cells": int(control_mask.sum()),
        "n_non_control_cells": int((~control_mask).sum()),
        "n_eligible_targets": int(len(target_df)),
        "n_heldout_targets": int(len(heldout_df)),
        "n_train_targets": int(len(train_df)),
        "heldout_targets_in_order": heldout_targets,
        "heldout_support_summary": summarize_support(heldout_df.rename(columns={"n_cells_perturbed_eligibility": "n_cells_perturbed"})),
        "train_support_summary": summarize_support(train_df.rename(columns={"n_cells_perturbed_eligibility": "n_cells_perturbed"})),
        "heldout_stratum_counts": heldout_df["support_stratum"].value_counts().sort_index().to_dict(),
        "heldout_target_abundance": heldout_df[
            [
                "target_gene",
                "n_cells_perturbed_eligibility",
                "support_rank_ascending",
                "support_stratum",
                "target_control_mean_expression",
                "target_perturbed_mean_expression",
                "target_delta_expression",
                "target_control_detection_fraction",
                "target_perturbed_detection_fraction",
            ]
        ].to_dict(orient="records"),
    }

    dataset_output_root = output_root / model_id / dataset_id
    dataset_output_root.mkdir(parents=True, exist_ok=True)
    heldout_path = dataset_output_root / "heldout_targets.tsv"
    train_path = dataset_output_root / "train_targets.tsv"
    summary_path = dataset_output_root / "summary.json"
    heldout_df.to_csv(heldout_path, sep="\t", index=False)
    train_df.to_csv(train_path, sep="\t", index=False)
    json_dump(summary, summary_path)

    print(f"已写出: {resolve_project_relative(heldout_path)}")
    print(f"已写出: {resolve_project_relative(train_path)}")
    print(f"已写出: {resolve_project_relative(summary_path)}")
    print(heldout_df.to_string(index=False))


if __name__ == "__main__":
    main()
