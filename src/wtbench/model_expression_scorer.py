from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from wtbench.hcc_prediction_export import (
    DEFAULT_AXIS_MEMBERSHIP_PATH,
    DEFAULT_TRUTH_CONFIG_PATH,
    DEFAULT_TRUTH_CONTRACT_PATH,
    compute_truth_aligned_log_shift_matrix,
    expected_target_and_gene_order,
    load_prediction_matrix,
)
from wtbench.truth_bridge import build_dataset_specs, load_config


ROLE_ORDER = ["canonical_backbone", "shift_excess", "context_deviation"]


def load_tsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t")


def _safe_cosine(left: np.ndarray, right: np.ndarray) -> float:
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm == 0.0 and right_norm == 0.0:
        return 1.0
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def _top_k_overlap_fraction(left: np.ndarray, right: np.ndarray, top_k: int) -> float:
    effective_k = min(int(top_k), int(left.shape[0]), int(right.shape[0]))
    if effective_k <= 0:
        return float("nan")
    left_top = set(np.argsort(np.abs(left))[-effective_k:].tolist())
    right_top = set(np.argsort(np.abs(right))[-effective_k:].tolist())
    return float(len(left_top & right_top) / effective_k)


@lru_cache(maxsize=8)
def _load_truth_for_cell_line(
    cell_line: str,
    truth_config_path: str,
    axis_membership_path: str,
) -> pd.DataFrame:
    truth_config = load_config(Path(truth_config_path))
    axis_membership = load_tsv(Path(axis_membership_path))
    specs = {spec.cell_line: spec for spec in build_dataset_specs(truth_config)}
    if cell_line not in specs:
        raise ValueError(f"未知 cell_line: {cell_line}")
    truth = compute_truth_aligned_log_shift_matrix(
        specs[cell_line],
        truth_config,
        axis_membership,
    )
    return truth


def build_target_role_table(
    axis_membership: pd.DataFrame,
    truth_contract: pd.DataFrame,
) -> pd.DataFrame:
    target_axis = (
        axis_membership.loc[:, ["target_gene", "fine_axis"]]
        .drop_duplicates()
        .rename(columns={"fine_axis": "expected_axis"})
    )
    role_table = target_axis.merge(
        truth_contract.loc[:, ["fine_axis", "architecture_role"]]
        .drop_duplicates()
        .rename(columns={"fine_axis": "expected_axis"}),
        on="expected_axis",
        how="left",
        validate="many_to_one",
    )
    return role_table


def summarize_target_expression_metrics(
    target_metrics: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for group_key in ["all_targets", *ROLE_ORDER]:
        if group_key == "all_targets":
            subset = target_metrics.copy()
        else:
            subset = target_metrics.loc[target_metrics["architecture_role"].eq(group_key)].copy()
        if subset.empty:
            continue
        rows.append(
            {
                "group_key": group_key,
                "target_count": int(len(subset)),
                "cosine_similarity_mean": float(subset["cosine_similarity"].mean()),
                "l2_distance_mean": float(subset["l2_distance"].mean()),
                "top20_overlap_mean": float(subset["top20_overlap_fraction"].mean()),
            }
        )
    return pd.DataFrame(rows)


def score_prediction_against_truth_expression(
    prediction_path: Path,
    *,
    cell_line: str,
    top_k: int = 20,
    truth_config_path: Path = DEFAULT_TRUTH_CONFIG_PATH,
    axis_membership_path: Path = DEFAULT_AXIS_MEMBERSHIP_PATH,
    truth_contract_path: Path = DEFAULT_TRUTH_CONTRACT_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prediction = load_prediction_matrix(prediction_path)
    axis_membership = load_tsv(axis_membership_path)
    truth_contract = load_tsv(truth_contract_path)
    truth = _load_truth_for_cell_line(
        cell_line,
        str(truth_config_path),
        str(axis_membership_path),
    )

    target_order, gene_order = expected_target_and_gene_order(axis_membership)
    prediction_aligned = prediction.set_index("target_gene").loc[target_order, gene_order]
    truth_aligned = truth.set_index("target_gene").loc[target_order, gene_order]

    target_roles = build_target_role_table(axis_membership, truth_contract).set_index("target_gene")
    rows: list[dict[str, object]] = []
    for target_gene in target_order:
        predicted_vec = prediction_aligned.loc[target_gene].to_numpy(dtype=np.float64)
        truth_vec = truth_aligned.loc[target_gene].to_numpy(dtype=np.float64)
        rows.append(
            {
                "target_gene": target_gene,
                "expected_axis": str(target_roles.loc[target_gene, "expected_axis"]),
                "architecture_role": str(target_roles.loc[target_gene, "architecture_role"]),
                "cosine_similarity": _safe_cosine(predicted_vec, truth_vec),
                "l2_distance": float(np.linalg.norm(predicted_vec - truth_vec)),
                "top20_overlap_fraction": _top_k_overlap_fraction(predicted_vec, truth_vec, top_k),
            }
        )
    target_metrics = pd.DataFrame(rows)
    summary = summarize_target_expression_metrics(target_metrics)
    return target_metrics, summary
