from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class StructureScorerInputs:
    prediction: pd.DataFrame
    truth_contract: pd.DataFrame
    axis_membership: pd.DataFrame


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRUTH_CONTRACT_PATH = (
    PROJECT_ROOT
    / "reports/truth_driven_bridge/truth_architecture_contract/truth_architecture_contract.tsv"
)
DEFAULT_AXIS_MEMBERSHIP_PATH = (
    PROJECT_ROOT
    / "reports/truth_driven_bridge/master_atlas/shared_target_axis_membership.tsv"
)


def load_tsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t")


def _normalize_prediction_frame(prediction: pd.DataFrame) -> pd.DataFrame:
    frame = prediction.copy()
    if "target_gene" not in frame.columns:
        frame = frame.rename(columns={frame.columns[0]: "target_gene"})
    frame["target_gene"] = frame["target_gene"].astype("string")
    return frame.set_index("target_gene")


def build_axis_gene_sets(axis_membership: pd.DataFrame) -> dict[str, list[str]]:
    required = {"target_gene", "fine_axis"}
    missing = sorted(required - set(axis_membership.columns))
    if missing:
        raise ValueError(f"axis_membership 缺少列: {missing}")
    deduped = axis_membership.loc[:, ["target_gene", "fine_axis"]].drop_duplicates()
    axis_gene_sets: dict[str, list[str]] = {}
    for fine_axis, group in deduped.groupby("fine_axis", sort=True):
        axis_gene_sets[str(fine_axis)] = sorted(group["target_gene"].astype(str).tolist())
    return axis_gene_sets


def project_prediction_to_axes(
    prediction: pd.DataFrame,
    axis_membership: pd.DataFrame,
    truth_contract: pd.DataFrame,
) -> pd.DataFrame:
    aligned = _normalize_prediction_frame(prediction)
    axis_gene_sets = build_axis_gene_sets(axis_membership)
    contract = truth_contract.loc[:, ["fine_axis", "architecture_role", "confidence"]].drop_duplicates()
    expected_axis = (
        axis_membership.loc[:, ["target_gene", "fine_axis"]]
        .drop_duplicates()
        .rename(columns={"fine_axis": "expected_axis"})
    )
    rows: list[dict[str, object]] = []
    for target_gene, values in aligned.iterrows():
        for fine_axis, genes in axis_gene_sets.items():
            projected_genes = [gene for gene in genes if gene in aligned.columns]
            if not projected_genes:
                signed_mean = np.nan
                mean_abs = np.nan
                l2_norm = np.nan
            else:
                axis_values = values.loc[projected_genes].astype(float)
                signed_mean = float(axis_values.mean())
                mean_abs = float(axis_values.abs().mean())
                l2_norm = float(np.linalg.norm(axis_values.to_numpy(dtype=float)))
            rows.append(
                {
                    "target_gene": str(target_gene),
                    "fine_axis": fine_axis,
                    "projected_signed_mean": signed_mean,
                    "projected_mean_abs": mean_abs,
                    "projected_l2": l2_norm,
                    "n_axis_genes": len(genes),
                    "n_projected_genes": len(projected_genes),
                    "gene_coverage": len(projected_genes) / len(genes),
                }
            )
    projected = pd.DataFrame(rows)
    projected = projected.merge(contract, on="fine_axis", how="left", validate="many_to_one")
    projected = projected.merge(expected_axis, on="target_gene", how="left", validate="many_to_one")
    projected["is_expected_axis"] = projected["fine_axis"].eq(projected["expected_axis"])
    return projected


def _rank_percentile(series: pd.Series, target_axis: str) -> float:
    ranked = series.rank(method="average", ascending=False)
    axis_count = int(series.notna().sum())
    if axis_count <= 1:
        return np.nan
    target_rank = float(ranked.loc[target_axis])
    return 1.0 - ((target_rank - 1.0) / (axis_count - 1.0))


def compute_backbone_recovery_score(projected: pd.DataFrame) -> float:
    backbone_targets = (
        projected.loc[
            projected["is_expected_axis"] & projected["architecture_role"].eq("canonical_backbone"),
            "target_gene",
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    if not backbone_targets:
        return float("nan")
    per_target: list[float] = []
    for target_gene, group in projected.loc[projected["target_gene"].isin(backbone_targets)].groupby(
        "target_gene",
        sort=True,
    ):
        expected = group.loc[group["is_expected_axis"]]
        if expected.empty:
            continue
        score = _rank_percentile(
            group.set_index("fine_axis")["projected_mean_abs"],
            str(expected["fine_axis"].iloc[0]),
        )
        per_target.append(score)
    return float(np.nanmean(per_target)) if per_target else float("nan")


def _pairwise_superiority_probability(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0:
        return float("nan")
    comparisons = (a[:, None] > b[None, :]).mean()
    ties = (a[:, None] == b[None, :]).mean()
    return float(comparisons + 0.5 * ties)


def compute_shift_excess_identification_score(projected: pd.DataFrame) -> float:
    expected = projected.loc[projected["is_expected_axis"]].copy()
    shift_excess = expected.loc[
        expected["architecture_role"].eq("shift_excess"),
        "projected_mean_abs",
    ].dropna()
    backbone = expected.loc[
        expected["architecture_role"].eq("canonical_backbone"),
        "projected_mean_abs",
    ].dropna()
    return _pairwise_superiority_probability(
        shift_excess.to_numpy(dtype=float),
        backbone.to_numpy(dtype=float),
    )


def compute_structure_vs_context_separation_score(projected: pd.DataFrame) -> float:
    per_target: list[float] = []
    for target_gene, group in projected.groupby("target_gene", sort=True):
        expected = group.loc[group["is_expected_axis"], "projected_mean_abs"].dropna()
        off_axis = group.loc[~group["is_expected_axis"], "projected_mean_abs"].dropna()
        if expected.empty or off_axis.empty:
            continue
        expected_value = float(expected.iloc[0])
        off_axis_mean = float(off_axis.mean())
        denominator = expected_value + off_axis_mean
        if denominator <= 0.0:
            per_target.append(0.0)
            continue
        per_target.append(expected_value / denominator)
    return float(np.nanmean(per_target)) if per_target else float("nan")


def summarize_structure_scores(projected: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "score_name": "backbone_recovery_score",
                "score_value": compute_backbone_recovery_score(projected),
                "score_direction": "higher_is_better",
            },
            {
                "score_name": "shift_excess_identification_score",
                "score_value": compute_shift_excess_identification_score(projected),
                "score_direction": "higher_is_better",
            },
            {
                "score_name": "structure_vs_context_separation_score",
                "score_value": compute_structure_vs_context_separation_score(projected),
                "score_direction": "higher_is_better",
            },
        ]
    )


def load_prediction_matrix(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep="\t")
    if frame.empty:
        raise ValueError(f"{path} 为空。")
    if frame.columns[0] != "target_gene":
        raise ValueError(f"{path} 首列必须是 target_gene。")
    return frame


def score_prediction_against_frozen_architecture(
    prediction_path: Path,
    truth_contract_path: Path = DEFAULT_TRUTH_CONTRACT_PATH,
    axis_membership_path: Path = DEFAULT_AXIS_MEMBERSHIP_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prediction = load_prediction_matrix(prediction_path)
    truth_contract = load_tsv(truth_contract_path)
    axis_membership = load_tsv(axis_membership_path)
    projected = project_prediction_to_axes(
        prediction=prediction,
        axis_membership=axis_membership,
        truth_contract=truth_contract,
    )
    scores = summarize_structure_scores(projected)
    return projected, scores
