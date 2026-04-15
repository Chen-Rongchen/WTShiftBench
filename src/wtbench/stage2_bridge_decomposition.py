from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AnalysisConfig:
    config_path: Path
    bridge_table_path: Path
    axis_membership_path: Path
    truth_contract_path: Path | None
    report_root: Path
    cell_lines: list[str]
    shift_metric: str
    depmap_metric: str
    quantile_low: float
    quantile_high: float
    anchor_min_cell_lines: int
    shared_anchor_min_mean_quantile: float
    axis_min_targets: int
    axis_min_targets_for_formal_call: int
    axis_shared_r2_min: float
    axis_skew_delta_min: float
    sensitivity_quantile_pairs: list[tuple[float, float]]
    axis_bootstrap_replicates: int
    random_seed: int


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload


def parse_config(config_path: Path) -> AnalysisConfig:
    payload = load_json(config_path)
    required = {"input", "analysis", "output"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"配置缺少字段: {missing}")

    input_block = payload["input"]
    analysis_block = payload["analysis"]
    output_block = payload["output"]
    if not isinstance(input_block, dict) or not isinstance(analysis_block, dict) or not isinstance(output_block, dict):
        raise ValueError("input / analysis / output 必须都是 JSON 对象。")

    return AnalysisConfig(
        config_path=config_path,
        bridge_table_path=resolve_path(str(input_block["bridge_table_path"])),
        axis_membership_path=resolve_path(str(input_block["axis_membership_path"])),
        truth_contract_path=resolve_path(str(input_block["truth_contract_path"]))
        if input_block.get("truth_contract_path")
        else None,
        report_root=resolve_path(str(output_block["report_root"])),
        cell_lines=[str(item) for item in analysis_block["cell_lines"]],
        shift_metric=str(analysis_block["shift_metric"]),
        depmap_metric=str(analysis_block["depmap_metric"]),
        quantile_low=float(analysis_block["quantile_low"]),
        quantile_high=float(analysis_block["quantile_high"]),
        anchor_min_cell_lines=int(analysis_block["anchor_min_cell_lines"]),
        shared_anchor_min_mean_quantile=float(analysis_block["shared_anchor_min_mean_quantile"]),
        axis_min_targets=int(analysis_block["axis_min_targets"]),
        axis_min_targets_for_formal_call=int(analysis_block.get("axis_min_targets_for_formal_call", analysis_block["axis_min_targets"])),
        axis_shared_r2_min=float(analysis_block["axis_shared_r2_min"]),
        axis_skew_delta_min=float(analysis_block["axis_skew_delta_min"]),
        sensitivity_quantile_pairs=[
            (float(item["low"]), float(item["high"]))
            for item in analysis_block.get(
                "sensitivity_quantile_pairs",
                [{"low": analysis_block["quantile_low"], "high": analysis_block["quantile_high"]}],
            )
        ],
        axis_bootstrap_replicates=int(analysis_block.get("axis_bootstrap_replicates", 200)),
        random_seed=int(analysis_block.get("random_seed", 7)),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 Stage 2 两层 bridge decomposition 分析。")
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "configs/stage2/truth_bridge_decomposition_v1.json"),
        help="bridge decomposition 配置 JSON 路径。",
    )
    return parser


def load_inputs(config: AnalysisConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
    bridge = pd.read_csv(config.bridge_table_path, sep="\t")
    membership = pd.read_csv(config.axis_membership_path, sep="\t")
    truth_contract = None
    if config.truth_contract_path is not None and config.truth_contract_path.exists():
        truth_contract = pd.read_csv(config.truth_contract_path, sep="\t")
    return bridge, membership, truth_contract


def aligned_depmap_strength(series: pd.Series, metric_name: str) -> pd.Series:
    if metric_name == "depmap_gene_effect":
        return -series.astype(float)
    if metric_name == "depmap_gene_dependency":
        return series.astype(float)
    raise ValueError(f"不支持的 DepMap 指标: {metric_name}")


def safe_quantile_rank(series: pd.Series) -> pd.Series:
    mask = series.notna()
    ranks = pd.Series(np.nan, index=series.index, dtype=float)
    if int(mask.sum()) == 0:
        return ranks
    ranks.loc[mask] = series.loc[mask].rank(method="average", pct=True).astype(float)
    return ranks


def assign_band(value: float, low: float, high: float) -> str:
    if np.isnan(value):
        return "insufficient"
    if value >= high:
        return "high"
    if value <= low:
        return "low"
    return "middle"


def assign_joint_grid(shift_band: str, dep_band: str) -> str:
    if shift_band == "insufficient" or dep_band == "insufficient":
        return "insufficient"
    if shift_band == "high" and dep_band == "high":
        return "Q1_anchor"
    if shift_band == "high" and dep_band == "low":
        return "Q2_transcriptomic_excess"
    if shift_band == "low" and dep_band == "high":
        return "Q3_dependency_excess"
    if shift_band == "low" and dep_band == "low":
        return "Q4_low_information"
    return "middle"


def classify_grid_role(label: str) -> str:
    mapping = {
        "Q1_anchor": "canonical_bridge_anchor",
        "Q2_transcriptomic_excess": "deviation_transcriptomic_excess",
        "Q3_dependency_excess": "deviation_dependency_excess",
        "Q4_low_information": "low_information_background",
        "middle": "middle_band",
        "insufficient": "insufficient",
    }
    return mapping[label]


def prepare_target_level_table(bridge: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    working = bridge.copy()
    working = working.loc[working["dataset_role"].eq("primary")]
    working = working.loc[working["cell_line"].isin(config.cell_lines)]
    working = working.loc[working["depmap_join_status"].eq("both")].copy()
    working["shift_value"] = working[config.shift_metric].astype(float)
    working["depmap_value_raw"] = working[config.depmap_metric].astype(float)
    working["depmap_strength"] = aligned_depmap_strength(working[config.depmap_metric], config.depmap_metric)

    pieces: list[pd.DataFrame] = []
    for cell_line, group in working.groupby("cell_line", sort=True):
        group = group.copy()
        group["shift_quantile"] = safe_quantile_rank(group["shift_value"])
        group["depmap_quantile"] = safe_quantile_rank(group["depmap_strength"])
        group["shift_band"] = group["shift_quantile"].map(
            lambda value: assign_band(float(value), config.quantile_low, config.quantile_high) if pd.notna(value) else "insufficient"
        )
        group["depmap_band"] = group["depmap_quantile"].map(
            lambda value: assign_band(float(value), config.quantile_low, config.quantile_high) if pd.notna(value) else "insufficient"
        )
        group["joint_grid"] = [
            assign_joint_grid(shift_band, dep_band)
            for shift_band, dep_band in zip(group["shift_band"], group["depmap_band"])
        ]
        group["grid_role"] = group["joint_grid"].map(classify_grid_role)
        group["is_q1_anchor"] = group["joint_grid"].eq("Q1_anchor")
        group["is_q2_transcriptomic_excess"] = group["joint_grid"].eq("Q2_transcriptomic_excess")
        group["is_q3_dependency_excess"] = group["joint_grid"].eq("Q3_dependency_excess")
        group["is_q4_low_information"] = group["joint_grid"].eq("Q4_low_information")
        pieces.append(group)

    if not pieces:
        raise ValueError("没有可用于 bridge decomposition 的 primary/both targets。")
    return pd.concat(pieces, ignore_index=True)


def assign_grid_for_cutoffs(
    frame: pd.DataFrame,
    *,
    quantile_low: float,
    quantile_high: float,
) -> pd.DataFrame:
    group = frame.copy()
    group["shift_quantile"] = safe_quantile_rank(group["shift_value"])
    group["depmap_quantile"] = safe_quantile_rank(group["depmap_strength"])
    group["shift_band"] = group["shift_quantile"].map(
        lambda value: assign_band(float(value), quantile_low, quantile_high) if pd.notna(value) else "insufficient"
    )
    group["depmap_band"] = group["depmap_quantile"].map(
        lambda value: assign_band(float(value), quantile_low, quantile_high) if pd.notna(value) else "insufficient"
    )
    group["joint_grid"] = [
        assign_joint_grid(shift_band, dep_band)
        for shift_band, dep_band in zip(group["shift_band"], group["depmap_band"])
    ]
    group["grid_role"] = group["joint_grid"].map(classify_grid_role)
    group["is_q1_anchor"] = group["joint_grid"].eq("Q1_anchor")
    return group


def build_target_grid_summary(target_level: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for cell_line, group in target_level.groupby("cell_line", sort=True):
        total = int(len(group))
        for grid_label, subgroup in group.groupby("joint_grid", sort=False):
            rows.append(
                {
                    "cell_line": cell_line,
                    "joint_grid": grid_label,
                    "grid_role": classify_grid_role(str(grid_label)),
                    "n_targets": int(len(subgroup)),
                    "fraction_targets": float(len(subgroup) / total if total else np.nan),
                    "median_shift_value": float(subgroup["shift_value"].median()),
                    "median_depmap_strength": float(subgroup["depmap_strength"].median()),
                    "quantile_low": config.quantile_low,
                    "quantile_high": config.quantile_high,
                }
            )
    return pd.DataFrame(rows).sort_values(["cell_line", "joint_grid"]).reset_index(drop=True)


def build_shared_anchor_table(target_level: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    grouped = (
        target_level.groupby("target_gene", sort=True)
        .agg(
            n_cell_lines=("cell_line", "nunique"),
            q1_anchor_count=("is_q1_anchor", "sum"),
            q2_count=("is_q2_transcriptomic_excess", "sum"),
            q3_count=("is_q3_dependency_excess", "sum"),
            q4_count=("is_q4_low_information", "sum"),
            shift_quantile_mean=("shift_quantile", "mean"),
            depmap_quantile_mean=("depmap_quantile", "mean"),
            shift_value_mean=("shift_value", "mean"),
            depmap_strength_mean=("depmap_strength", "mean"),
        )
        .reset_index()
    )
    grouped["shared_anchor_call"] = np.where(
        (grouped["q1_anchor_count"] >= config.anchor_min_cell_lines)
        & (grouped["shift_quantile_mean"] >= config.shared_anchor_min_mean_quantile)
        & (grouped["depmap_quantile_mean"] >= config.shared_anchor_min_mean_quantile),
        "shared_canonical_anchor",
        "not_shared_canonical_anchor",
    )
    return grouped.sort_values(
        ["shared_anchor_call", "q1_anchor_count", "shift_quantile_mean", "depmap_quantile_mean", "target_gene"],
        ascending=[True, False, False, False, True],
    ).reset_index(drop=True)


def build_anchor_sensitivity_tables(
    target_level: pd.DataFrame,
    config: AnalysisConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    sensitivity_rows: list[dict[str, Any]] = []
    per_target_rows: list[pd.DataFrame] = []
    for quantile_low, quantile_high in config.sensitivity_quantile_pairs:
        pieces: list[pd.DataFrame] = []
        for cell_line, group in target_level.groupby("cell_line", sort=True):
            subgroup = assign_grid_for_cutoffs(
                group.loc[:, ["cell_line", "target_gene", "shift_value", "depmap_strength"]].copy(),
                quantile_low=quantile_low,
                quantile_high=quantile_high,
            )
            subgroup["quantile_low"] = quantile_low
            subgroup["quantile_high"] = quantile_high
            pieces.append(subgroup)
            summary_counts = subgroup["joint_grid"].value_counts()
            for joint_grid, count in summary_counts.items():
                sensitivity_rows.append(
                    {
                        "cell_line": cell_line,
                        "quantile_low": quantile_low,
                        "quantile_high": quantile_high,
                        "joint_grid": str(joint_grid),
                        "n_targets": int(count),
                        "fraction_targets": float(count / len(subgroup) if len(subgroup) else np.nan),
                    }
                )
        run_frame = pd.concat(pieces, ignore_index=True)
        anchor_counts = (
            run_frame.groupby("target_gene", sort=True)
            .agg(
                n_cell_lines=("cell_line", "nunique"),
                q1_anchor_count=("is_q1_anchor", "sum"),
                shift_quantile_mean=("shift_quantile", "mean"),
                depmap_quantile_mean=("depmap_quantile", "mean"),
            )
            .reset_index()
        )
        anchor_counts["is_shared_anchor_under_cutoff"] = (
            (anchor_counts["q1_anchor_count"] >= config.anchor_min_cell_lines)
            & (anchor_counts["shift_quantile_mean"] >= config.shared_anchor_min_mean_quantile)
            & (anchor_counts["depmap_quantile_mean"] >= config.shared_anchor_min_mean_quantile)
        )
        anchor_counts["quantile_low"] = quantile_low
        anchor_counts["quantile_high"] = quantile_high
        per_target_rows.append(anchor_counts)

    sensitivity = pd.DataFrame(sensitivity_rows).sort_values(
        ["quantile_low", "quantile_high", "cell_line", "joint_grid"]
    ).reset_index(drop=True)
    per_target = pd.concat(per_target_rows, ignore_index=True)
    stability = (
        per_target.groupby("target_gene", sort=True)
        .agg(
            n_cutoff_pairs=("is_shared_anchor_under_cutoff", "size"),
            n_shared_anchor_calls=("is_shared_anchor_under_cutoff", "sum"),
            min_shift_quantile_mean=("shift_quantile_mean", "min"),
            min_depmap_quantile_mean=("depmap_quantile_mean", "min"),
            max_shift_quantile_mean=("shift_quantile_mean", "max"),
            max_depmap_quantile_mean=("depmap_quantile_mean", "max"),
        )
        .reset_index()
    )
    stability["shared_anchor_stability_fraction"] = (
        stability["n_shared_anchor_calls"] / stability["n_cutoff_pairs"]
    )
    stability["stability_call"] = np.where(
        stability["shared_anchor_stability_fraction"] >= 0.80,
        "stable_shared_anchor",
        np.where(
            stability["shared_anchor_stability_fraction"] > 0.0,
            "cutoff_sensitive_shared_anchor",
            "not_shared_anchor",
        ),
    )
    stability = stability.sort_values(
        ["stability_call", "shared_anchor_stability_fraction", "n_shared_anchor_calls", "target_gene"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)
    return sensitivity, stability


def add_axis_annotations(
    target_level: pd.DataFrame,
    membership: pd.DataFrame,
    truth_contract: pd.DataFrame | None,
) -> pd.DataFrame:
    membership_view = membership.rename(
        columns={
            "fine_axis": "axis_id",
            "macro_axis": "axis_family",
            "annotation_confidence": "axis_annotation_confidence",
            "evidence_note": "axis_evidence_note",
        }
    ).copy()
    required = {"target_gene", "axis_id", "axis_family"}
    missing = sorted(required - set(membership_view.columns))
    if missing:
        raise ValueError(f"axis_membership 缺少字段: {missing}")

    merged = target_level.merge(
        membership_view.loc[:, [c for c in membership_view.columns if c in {
            "target_gene", "axis_id", "axis_family", "axis_annotation_confidence", "axis_evidence_note"
        }]],
        on="target_gene",
        how="left",
    )
    if truth_contract is not None:
        merged = merged.merge(
            truth_contract.loc[:, [c for c in truth_contract.columns if c in {
                "fine_axis", "architecture_role", "confidence", "consistency_class"
            }]].rename(columns={"fine_axis": "axis_id", "confidence": "axis_contract_confidence"}),
            on="axis_id",
            how="left",
        )
    return merged


def binary_axis_r2(mask: pd.Series, values: pd.Series) -> float:
    valid = mask.notna() & values.notna()
    if int(valid.sum()) < 3:
        return np.nan
    x = mask.loc[valid].astype(float).to_numpy()
    y = values.loc[valid].astype(float).to_numpy()
    if float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return 0.0
    corr = np.corrcoef(x, y)[0, 1]
    return float(corr * corr)


def build_axis_level_summary(
    annotated_target_level: pd.DataFrame,
    config: AnalysisConfig,
) -> pd.DataFrame:
    annotated = annotated_target_level.loc[annotated_target_level["axis_id"].notna()].copy()
    rows: list[dict[str, Any]] = []

    for axis_id, axis_targets in annotated.groupby("axis_id", sort=True):
        genes = sorted(axis_targets["target_gene"].astype(str).unique().tolist())
        axis_family = str(axis_targets["axis_family"].dropna().iloc[0]) if axis_targets["axis_family"].notna().any() else ""
        architecture_role = (
            str(axis_targets["architecture_role"].dropna().iloc[0])
            if "architecture_role" in axis_targets.columns and axis_targets["architecture_role"].notna().any()
            else ""
        )
        consistency_class = (
            str(axis_targets["consistency_class"].dropna().iloc[0])
            if "consistency_class" in axis_targets.columns and axis_targets["consistency_class"].notna().any()
            else ""
        )
        axis_annotation_confidence = (
            str(axis_targets["axis_annotation_confidence"].dropna().iloc[0])
            if axis_targets["axis_annotation_confidence"].notna().any()
            else ""
        )

        cell_line_records: list[dict[str, Any]] = []
        for cell_line in config.cell_lines:
            cell_df = annotated.loc[annotated["cell_line"].eq(cell_line)].copy()
            if cell_df.empty:
                continue
            membership_mask = cell_df["axis_id"].eq(axis_id)
            axis_df = cell_df.loc[membership_mask].copy()
            if axis_df.empty:
                continue
            shift_mean = float(axis_df["shift_value"].mean())
            dep_mean = float(axis_df["depmap_strength"].mean())
            shift_global = float(cell_df["shift_value"].mean())
            dep_global = float(cell_df["depmap_strength"].mean())
            shift_lift = shift_mean - shift_global
            dep_lift = dep_mean - dep_global
            shift_r2 = binary_axis_r2(membership_mask, cell_df["shift_value"])
            dep_r2 = binary_axis_r2(membership_mask, cell_df["depmap_strength"])
            cell_line_records.append(
                {
                    "cell_line": cell_line,
                    "n_targets_cell_line": int(len(axis_df)),
                    "fraction_q1": float(axis_df["is_q1_anchor"].mean()),
                    "fraction_q2": float(axis_df["is_q2_transcriptomic_excess"].mean()),
                    "fraction_q3": float(axis_df["is_q3_dependency_excess"].mean()),
                    "shift_mean": shift_mean,
                    "depmap_mean": dep_mean,
                    "shift_lift": shift_lift,
                    "depmap_lift": dep_lift,
                    "shift_r2": shift_r2,
                    "depmap_r2": dep_r2,
                }
            )

        if not cell_line_records:
            continue
        cell_line_frame = pd.DataFrame(cell_line_records)
        n_targets = int(len(genes))
        shift_r2_mean = float(cell_line_frame["shift_r2"].mean())
        dep_r2_mean = float(cell_line_frame["depmap_r2"].mean())
        shift_lift_mean = float(cell_line_frame["shift_lift"].mean())
        dep_lift_mean = float(cell_line_frame["depmap_lift"].mean())
        sharedness_delta = shift_r2_mean - dep_r2_mean

        preliminary_prefix = ""
        if n_targets < config.axis_min_targets:
            explanatory_call = "insufficient_axis_size"
        elif n_targets < config.axis_min_targets_for_formal_call:
            preliminary_prefix = "preliminary_"
            if (
                shift_r2_mean >= config.axis_shared_r2_min
                and dep_r2_mean >= config.axis_shared_r2_min
                and shift_lift_mean > 0
                and dep_lift_mean > 0
            ):
                explanatory_call = "preliminary_shared_signal_axis"
            elif shift_r2_mean - dep_r2_mean >= config.axis_skew_delta_min and shift_lift_mean > 0:
                explanatory_call = "preliminary_transcriptomic_heavy_axis"
            elif dep_r2_mean - shift_r2_mean >= config.axis_skew_delta_min and dep_lift_mean > 0:
                explanatory_call = "preliminary_dependency_heavy_axis"
            else:
                explanatory_call = "preliminary_mixed_or_low_signal_axis"
        elif (
            shift_r2_mean >= config.axis_shared_r2_min
            and dep_r2_mean >= config.axis_shared_r2_min
            and shift_lift_mean > 0
            and dep_lift_mean > 0
        ):
            explanatory_call = "shared_backbone_axis"
        elif shift_r2_mean - dep_r2_mean >= config.axis_skew_delta_min and shift_lift_mean > 0:
            explanatory_call = "transcriptomic_heavy_axis"
        elif dep_r2_mean - shift_r2_mean >= config.axis_skew_delta_min and dep_lift_mean > 0:
            explanatory_call = "dependency_heavy_axis"
        else:
            explanatory_call = "mixed_or_low_signal_axis"

        rows.append(
            {
                "axis_id": axis_id,
                "axis_family": axis_family,
                "architecture_role": architecture_role,
                "consistency_class": consistency_class,
                "axis_annotation_confidence": axis_annotation_confidence,
                "n_targets": n_targets,
                "targets": "; ".join(genes),
                "fraction_q1_mean": float(cell_line_frame["fraction_q1"].mean()),
                "fraction_q2_mean": float(cell_line_frame["fraction_q2"].mean()),
                "fraction_q3_mean": float(cell_line_frame["fraction_q3"].mean()),
                "shift_lift_mean": shift_lift_mean,
                "depmap_lift_mean": dep_lift_mean,
                "shift_r2_mean": shift_r2_mean,
                "depmap_r2_mean": dep_r2_mean,
                "sharedness_delta": sharedness_delta,
                "explanatory_call": explanatory_call,
                "formal_call_eligible": bool(n_targets >= config.axis_min_targets_for_formal_call),
                "call_tier": "formal" if n_targets >= config.axis_min_targets_for_formal_call else "preliminary",
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["explanatory_call", "fraction_q1_mean", "shift_r2_mean", "depmap_r2_mean", "axis_id"],
        ascending=[True, False, False, False, True],
    ).reset_index(drop=True)


def classify_axis_call_from_stats(
    *,
    n_targets: int,
    shift_r2_mean: float,
    dep_r2_mean: float,
    shift_lift_mean: float,
    dep_lift_mean: float,
    config: AnalysisConfig,
) -> tuple[str, bool, str]:
    if n_targets < config.axis_min_targets:
        return "insufficient_axis_size", False, "preliminary"
    if n_targets < config.axis_min_targets_for_formal_call:
        if (
            shift_r2_mean >= config.axis_shared_r2_min
            and dep_r2_mean >= config.axis_shared_r2_min
            and shift_lift_mean > 0
            and dep_lift_mean > 0
        ):
            return "preliminary_shared_signal_axis", False, "preliminary"
        if shift_r2_mean - dep_r2_mean >= config.axis_skew_delta_min and shift_lift_mean > 0:
            return "preliminary_transcriptomic_heavy_axis", False, "preliminary"
        if dep_r2_mean - shift_r2_mean >= config.axis_skew_delta_min and dep_lift_mean > 0:
            return "preliminary_dependency_heavy_axis", False, "preliminary"
        return "preliminary_mixed_or_low_signal_axis", False, "preliminary"
    if (
        shift_r2_mean >= config.axis_shared_r2_min
        and dep_r2_mean >= config.axis_shared_r2_min
        and shift_lift_mean > 0
        and dep_lift_mean > 0
    ):
        return "shared_backbone_axis", True, "formal"
    if shift_r2_mean - dep_r2_mean >= config.axis_skew_delta_min and shift_lift_mean > 0:
        return "transcriptomic_heavy_axis", True, "formal"
    if dep_r2_mean - shift_r2_mean >= config.axis_skew_delta_min and dep_lift_mean > 0:
        return "dependency_heavy_axis", True, "formal"
    return "mixed_or_low_signal_axis", True, "formal"


def build_axis_bootstrap_stability(
    annotated_target_level: pd.DataFrame,
    axis_summary: pd.DataFrame,
    config: AnalysisConfig,
) -> pd.DataFrame:
    annotated = annotated_target_level.loc[annotated_target_level["axis_id"].notna()].copy()
    rng = np.random.default_rng(config.random_seed)
    base_targets = {
        cell_line: cell_df.reset_index(drop=True)
        for cell_line, cell_df in annotated.groupby("cell_line", sort=True)
    }
    rows: list[dict[str, Any]] = []
    if not base_targets:
        return pd.DataFrame()

    for axis_row in axis_summary.itertuples(index=False):
        axis_id = str(axis_row.axis_id)
        bootstrap_shift_r2: list[float] = []
        bootstrap_dep_r2: list[float] = []
        bootstrap_calls: list[str] = []
        for _ in range(config.axis_bootstrap_replicates):
            per_line_records: list[dict[str, float]] = []
            for cell_line, cell_df in base_targets.items():
                n = len(cell_df)
                if n < 3:
                    continue
                sampled_idx = rng.integers(0, n, size=n)
                sampled = cell_df.iloc[sampled_idx].reset_index(drop=True)
                membership_mask = sampled["axis_id"].eq(axis_id)
                axis_df = sampled.loc[membership_mask]
                if axis_df.empty:
                    continue
                per_line_records.append(
                    {
                        "shift_r2": binary_axis_r2(membership_mask, sampled["shift_value"]),
                        "dep_r2": binary_axis_r2(membership_mask, sampled["depmap_strength"]),
                        "shift_lift": float(axis_df["shift_value"].mean() - sampled["shift_value"].mean()),
                        "dep_lift": float(axis_df["depmap_strength"].mean() - sampled["depmap_strength"].mean()),
                    }
                )
            if not per_line_records:
                continue
            per_line = pd.DataFrame(per_line_records)
            shift_r2_mean = float(per_line["shift_r2"].mean())
            dep_r2_mean = float(per_line["dep_r2"].mean())
            shift_lift_mean = float(per_line["shift_lift"].mean())
            dep_lift_mean = float(per_line["dep_lift"].mean())
            bootstrap_shift_r2.append(shift_r2_mean)
            bootstrap_dep_r2.append(dep_r2_mean)
            bootstrap_calls.append(
                classify_axis_call_from_stats(
                    n_targets=int(axis_row.n_targets),
                    shift_r2_mean=shift_r2_mean,
                    dep_r2_mean=dep_r2_mean,
                    shift_lift_mean=shift_lift_mean,
                    dep_lift_mean=dep_lift_mean,
                    config=config,
                )[0]
            )

        if not bootstrap_calls:
            continue
        call_counts = pd.Series(bootstrap_calls).value_counts()
        dominant_call = str(call_counts.index[0])
        dominant_fraction = float(call_counts.iloc[0] / len(bootstrap_calls))
        rows.append(
            {
                "axis_id": axis_id,
                "bootstrap_replicates_completed": int(len(bootstrap_calls)),
                "bootstrap_shift_r2_mean": float(np.mean(bootstrap_shift_r2)),
                "bootstrap_shift_r2_p10": float(np.quantile(bootstrap_shift_r2, 0.10)),
                "bootstrap_shift_r2_p90": float(np.quantile(bootstrap_shift_r2, 0.90)),
                "bootstrap_dep_r2_mean": float(np.mean(bootstrap_dep_r2)),
                "bootstrap_dep_r2_p10": float(np.quantile(bootstrap_dep_r2, 0.10)),
                "bootstrap_dep_r2_p90": float(np.quantile(bootstrap_dep_r2, 0.90)),
                "bootstrap_dominant_call": dominant_call,
                "bootstrap_dominant_call_fraction": dominant_fraction,
                "bootstrap_stability_call": (
                    "stable_axis_call" if dominant_fraction >= 0.80
                    else "moderately_stable_axis_call" if dominant_fraction >= 0.50
                    else "unstable_axis_call"
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["bootstrap_stability_call", "bootstrap_dominant_call_fraction", "axis_id"],
        ascending=[True, False, True],
    ).reset_index(drop=True)


def build_evidence_tier_summary(
    shared_anchor_stability: pd.DataFrame,
    axis_summary: pd.DataFrame,
    axis_bootstrap: pd.DataFrame,
) -> pd.DataFrame:
    anchor_rows = shared_anchor_stability.rename(
        columns={
            "target_gene": "object_id",
            "shared_anchor_stability_fraction": "stability_fraction",
            "stability_call": "stability_call",
        }
    ).copy()
    anchor_rows["object_type"] = "target_anchor"
    anchor_rows["primary_call"] = anchor_rows["stability_call"]
    anchor_rows["evidence_tier"] = np.where(
        anchor_rows["stability_call"].eq("stable_shared_anchor"),
        "primary_evidence",
        np.where(
            anchor_rows["stability_call"].eq("cutoff_sensitive_shared_anchor"),
            "supporting_but_sensitive",
            "background_or_negative",
        ),
    )
    anchor_rows = anchor_rows.loc[:, ["object_type", "object_id", "primary_call", "stability_fraction", "evidence_tier"]]

    axis_rows = axis_summary.merge(axis_bootstrap, on="axis_id", how="left").copy()
    axis_rows["object_type"] = "axis"
    axis_rows["object_id"] = axis_rows["axis_id"]
    axis_rows["primary_call"] = axis_rows["explanatory_call"]
    axis_rows["stability_fraction"] = axis_rows["bootstrap_dominant_call_fraction"]
    positive_formal_calls = {
        "shared_backbone_axis",
        "transcriptomic_heavy_axis",
        "dependency_heavy_axis",
    }
    axis_rows["evidence_tier"] = np.where(
        axis_rows["call_tier"].eq("formal")
        & axis_rows["primary_call"].isin(positive_formal_calls)
        & axis_rows["bootstrap_stability_call"].eq("stable_axis_call"),
        "primary_evidence",
        np.where(
            axis_rows["call_tier"].eq("formal")
            & axis_rows["primary_call"].isin(positive_formal_calls),
            "supporting_but_unstable",
            np.where(
                axis_rows["call_tier"].eq("formal"),
                "stable_but_nonpositive_formal",
                "preliminary_only",
            ),
        ),
    )
    axis_rows = axis_rows.loc[:, ["object_type", "object_id", "primary_call", "stability_fraction", "evidence_tier"]]
    combined = pd.concat([anchor_rows, axis_rows], ignore_index=True)
    return combined.sort_values(["evidence_tier", "object_type", "object_id"]).reset_index(drop=True)


def plot_target_level_joint_grid(target_level: pd.DataFrame, config: AnalysisConfig) -> list[str]:
    written: list[str] = []
    palette = {
        "Q1_anchor": "#b22222",
        "Q2_transcriptomic_excess": "#e69f00",
        "Q3_dependency_excess": "#0072b2",
        "Q4_low_information": "#7f7f7f",
        "middle": "#c8c8c8",
        "insufficient": "#efefef",
    }
    for cell_line, group in target_level.groupby("cell_line", sort=True):
        fig, ax = plt.subplots(figsize=(7.2, 6.0))
        for label, subgroup in group.groupby("joint_grid", sort=False):
            ax.scatter(
                subgroup["depmap_strength"],
                subgroup["shift_value"],
                s=42,
                alpha=0.85,
                color=palette.get(str(label), "#c8c8c8"),
                edgecolors="white",
                linewidths=0.4,
                label=str(label),
            )
        dep_low = float(group["depmap_strength"].quantile(config.quantile_low))
        dep_high = float(group["depmap_strength"].quantile(config.quantile_high))
        shift_low = float(group["shift_value"].quantile(config.quantile_low))
        shift_high = float(group["shift_value"].quantile(config.quantile_high))
        x_min = float(group["depmap_strength"].min())
        x_max = float(group["depmap_strength"].max())
        y_min = float(group["shift_value"].min())
        y_max = float(group["shift_value"].max())
        ax.axvspan(dep_high, x_max, ymin=max((shift_high - y_min) / (y_max - y_min if y_max > y_min else 1.0), 0), ymax=1.0, color="#f8d7da", alpha=0.35)
        ax.axvspan(x_min, dep_low, ymin=max((shift_high - y_min) / (y_max - y_min if y_max > y_min else 1.0), 0), ymax=1.0, color="#fdecc8", alpha=0.35)
        ax.axvspan(dep_high, x_max, ymin=0.0, ymax=min((shift_low - y_min) / (y_max - y_min if y_max > y_min else 1.0), 1.0), color="#dbeafe", alpha=0.35)
        ax.axvspan(x_min, dep_low, ymin=0.0, ymax=min((shift_low - y_min) / (y_max - y_min if y_max > y_min else 1.0), 1.0), color="#e5e7eb", alpha=0.45)
        ax.axvline(dep_low, color="#999999", linestyle="--", linewidth=1.0)
        ax.axvline(dep_high, color="#555555", linestyle="--", linewidth=1.0)
        ax.axhline(shift_low, color="#999999", linestyle="--", linewidth=1.0)
        ax.axhline(shift_high, color="#555555", linestyle="--", linewidth=1.0)
        dx = x_max - x_min if x_max > x_min else 1.0
        dy = y_max - y_min if y_max > y_min else 1.0

        annotations = [
            ("Q1\nhigh/high", dep_high + dx * 0.02, shift_high + dy * 0.03, "#b22222"),
            ("Q2\nhigh/low", x_min + dx * 0.03, shift_high + dy * 0.03, "#e69f00"),
            ("Q3\nlow/high", dep_high + dx * 0.02, y_min + dy * 0.05, "#0072b2"),
            ("Q4\nlow/low", x_min + dx * 0.03, y_min + dy * 0.05, "#6f6f6f"),
        ]
        for text, x, y, color in annotations:
            ax.text(
                x,
                y,
                text,
                fontsize=8,
                fontweight="bold",
                color=color,
                ha="left",
                va="bottom",
                bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": color, "alpha": 0.9},
            )
        ax.text(
            dep_low + (dep_high - dep_low) * 0.5,
            shift_low + (shift_high - shift_low) * 0.5,
            "middle band",
            fontsize=9,
            color="#666666",
            ha="center",
            va="center",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#bbbbbb", "alpha": 0.9},
        )
        ax.set_title(f"{cell_line} Target-Level Joint Grid")
        ax.set_xlabel("Aligned DepMap strength")
        ax.set_ylabel(config.shift_metric)
        ax.legend(frameon=False, fontsize=8, loc="best")
        fig.tight_layout()
        output_name = f"{cell_line}_target_level_joint_grid.png"
        fig.savefig(config.report_root / output_name, dpi=180)
        plt.close(fig)
        written.append(output_name)
    return written


def plot_axis_sharedness(axis_summary: pd.DataFrame, config: AnalysisConfig) -> str:
    fig, ax = plt.subplots(figsize=(7.2, 6.0))
    palette = {
        "shared_backbone_axis": "#b22222",
        "transcriptomic_heavy_axis": "#e69f00",
        "dependency_heavy_axis": "#0072b2",
        "mixed_or_low_signal_axis": "#7f7f7f",
        "preliminary_shared_signal_axis": "#f4a6a6",
        "preliminary_transcriptomic_heavy_axis": "#f3c97a",
        "preliminary_dependency_heavy_axis": "#7db7de",
        "preliminary_mixed_or_low_signal_axis": "#cfcfcf",
        "insufficient_axis_size": "#ebebeb",
    }
    for label, subgroup in axis_summary.groupby("explanatory_call", sort=False):
        ax.scatter(
            subgroup["depmap_r2_mean"],
            subgroup["shift_r2_mean"],
            s=np.maximum(subgroup["n_targets"].astype(float).to_numpy() * 45.0, 45.0),
            alpha=0.9,
            color=palette.get(str(label), "#c8c8c8"),
            edgecolors="white",
            linewidths=0.4,
            label=str(label),
        )
    ax.axvline(config.axis_shared_r2_min, color="#555555", linestyle="--", linewidth=1.0)
    ax.axhline(config.axis_shared_r2_min, color="#555555", linestyle="--", linewidth=1.0)
    ax.set_xlabel("DepMap-side explanatory R²")
    ax.set_ylabel("Transcriptomic-side explanatory R²")
    ax.set_title("Axis-Level Shared Explanatory Structure")

    label_candidates = axis_summary.loc[
        axis_summary["explanatory_call"].isin(
            [
                "shared_backbone_axis",
                "transcriptomic_heavy_axis",
                "dependency_heavy_axis",
                "preliminary_shared_signal_axis",
            ]
        )
    ].copy()
    for row in label_candidates.itertuples(index=False):
        ax.text(
            float(row.depmap_r2_mean) + 0.002,
            float(row.shift_r2_mean) + 0.002,
            str(row.axis_id),
            fontsize=7,
            color="#333333",
        )
    ax.legend(frameon=False, fontsize=8, loc="best")
    fig.tight_layout()
    output_name = "axis_level_shared_explanatory_structure.png"
    fig.savefig(config.report_root / output_name, dpi=180)
    plt.close(fig)
    return output_name


def write_markdown_report(
    config: AnalysisConfig,
    target_grid_summary: pd.DataFrame,
    shared_anchors: pd.DataFrame,
    axis_summary: pd.DataFrame,
    shared_anchor_stability: pd.DataFrame,
    axis_bootstrap: pd.DataFrame,
    evidence_tier_summary: pd.DataFrame,
) -> None:
    shared_anchor_rows = shared_anchors.loc[
        shared_anchors["shared_anchor_call"].eq("shared_canonical_anchor")
    ].head(10)
    shared_axis_rows = axis_summary.loc[axis_summary["explanatory_call"].eq("shared_backbone_axis")].head(10)
    transcriptomic_heavy_rows = axis_summary.loc[
        axis_summary["explanatory_call"].eq("transcriptomic_heavy_axis")
    ].head(5)
    dependency_heavy_rows = axis_summary.loc[
        axis_summary["explanatory_call"].eq("dependency_heavy_axis")
    ].head(5)
    preliminary_rows = axis_summary.loc[
        axis_summary["explanatory_call"].str.startswith("preliminary_", na=False)
    ].head(10)
    stable_anchor_rows = shared_anchor_stability.loc[
        shared_anchor_stability["stability_call"].eq("stable_shared_anchor")
    ].head(10)
    stable_axis_rows = axis_bootstrap.loc[
        axis_bootstrap["bootstrap_stability_call"].eq("stable_axis_call")
    ].head(10)
    evidence_counts = evidence_tier_summary["evidence_tier"].value_counts()

    lines = [
        "# Stage 2 Truth Bridge Decomposition v1",
        "",
        "## 定位",
        "",
        "- 本分析把 truth–DepMap bridge 明确拆成两层：`target-level joint-priority grid` 与 `axis-level shared explanatory structure`。",
        f"- 第一层使用 `{config.shift_metric}` 与 `{config.depmap_metric}`；DepMap 侧统一转成“数值越大表示 dependency/liability 越强”的 aligned strength。",
        f"- 第二层不把 `Pearson` 当作主结论，而是看哪些 axis 同时对 transcriptomic side 与 DepMap side 提供较强解释。",
        "",
        "## 第一层：Target-Level Joint Grid",
        "",
        f"- 先对两侧分别做 `high / middle / low` 三段分层：`<= {config.quantile_low:.2f}` 记为 `low`，`>= {config.quantile_high:.2f}` 记为 `high`，其余记为 `middle`。",
        "- 只有落在四个角点的 target 才进入 `Q1-Q4`；只要任一侧落在 `middle`，就统一保留在 `middle band`。",
        f"- `Q1_anchor`：shift 高、dependency 高。",
        f"- `Q2_transcriptomic_excess`：shift 高、dependency 低。",
        f"- `Q3_dependency_excess`：shift 低、dependency 高。",
        f"- `Q4_low_information`：shift 低、dependency 低。",
        "",
        "### 每条 cell line 的 grid 分布",
        "",
    ]
    for row in target_grid_summary.itertuples(index=False):
        lines.append(
            f"- `{row.cell_line}` / `{row.joint_grid}`：`n={row.n_targets}`，占比 `{row.fraction_targets:.1%}`，"
            f"median shift=`{row.median_shift_value:.4f}`，median dep strength=`{row.median_depmap_strength:.4f}`。"
        )

    lines.extend(
        [
            "",
            "### shared canonical anchors（前 10）",
            "",
        ]
    )
    if shared_anchor_rows.empty:
        lines.append("- 当前没有 target 同时满足 shared canonical anchor 条件。")
    else:
        for row in shared_anchor_rows.itertuples(index=False):
            lines.append(
                f"- `{row.target_gene}`：Q1 命中 `{row.q1_anchor_count}/{row.n_cell_lines}` 条 cell line，"
                f"mean shift quantile=`{row.shift_quantile_mean:.3f}`，mean dep quantile=`{row.depmap_quantile_mean:.3f}`。"
            )
    lines.extend(
        [
            "",
            "### anchor stability（跨 cutoff）",
            "",
        ]
    )
    if stable_anchor_rows.empty:
        lines.append("- 当前没有跨 cutoff 稳定的 shared anchors。")
    else:
        for row in stable_anchor_rows.itertuples(index=False):
            lines.append(
                f"- `{row.target_gene}`：shared anchor stability=`{row.shared_anchor_stability_fraction:.2f}`，"
                f"调用次数 `{row.n_shared_anchor_calls}/{row.n_cutoff_pairs}`。"
            )

    lines.extend(
        [
            "",
            "## 第二层：Axis-Level Shared Explanatory Structure",
            "",
            f"- 这里的 `R²` 不是教科书式全局方差分解，而是对每个 axis 做 one-vs-rest explanatory strength 近似。",
            f"- `shared_backbone_axis` 的判定要求两侧 `R²` 均不低于 `{config.axis_shared_r2_min:.3f}`，且 axis 对两侧均呈正向 lift。",
            f"- 只有 `n_targets >= {config.axis_min_targets_for_formal_call}` 的 axis 才进入 formal axis call；更小的 axis 只记为 `preliminary`。",
            f"- `transcriptomic_heavy_axis` / `dependency_heavy_axis` 用两侧 `R²` 差值超过 `{config.axis_skew_delta_min:.3f}` 来定义偏斜结构。",
            "",
            "### shared backbone axes",
            "",
        ]
    )
    if shared_axis_rows.empty:
        lines.append("- 当前没有 axis 满足 shared backbone axis 条件。")
    else:
        for row in shared_axis_rows.itertuples(index=False):
            lines.append(
                f"- `{row.axis_id}`：shift R²=`{row.shift_r2_mean:.3f}`，dep R²=`{row.depmap_r2_mean:.3f}`，"
                f"Q1 fraction=`{row.fraction_q1_mean:.2f}`，targets=`{row.targets}`。"
            )

    lines.extend(
        [
            "",
            "### transcriptomic-heavy axes",
            "",
        ]
    )
    if transcriptomic_heavy_rows.empty:
        lines.append("- 当前没有 axis 被判为 transcriptomic-heavy。")
    else:
        for row in transcriptomic_heavy_rows.itertuples(index=False):
            lines.append(
                f"- `{row.axis_id}`：shift R²=`{row.shift_r2_mean:.3f}` > dep R²=`{row.depmap_r2_mean:.3f}`，targets=`{row.targets}`。"
            )

    lines.extend(
        [
            "",
            "### dependency-heavy axes",
            "",
        ]
    )
    if dependency_heavy_rows.empty:
        lines.append("- 当前没有 axis 被判为 dependency-heavy。")
    else:
        for row in dependency_heavy_rows.itertuples(index=False):
            lines.append(
                f"- `{row.axis_id}`：dep R²=`{row.depmap_r2_mean:.3f}` > shift R²=`{row.shift_r2_mean:.3f}`，targets=`{row.targets}`。"
            )

    lines.extend(
        [
            "",
            "### preliminary axes",
            "",
        ]
    )
    if preliminary_rows.empty:
        lines.append("- 当前没有 axis 被标记为 preliminary shared/skewed signal。")
    else:
        for row in preliminary_rows.itertuples(index=False):
            lines.append(
                f"- `{row.axis_id}`：当前仅有 `{row.n_targets}` 个 target，先记为 `{row.explanatory_call}`，"
                f"shift R²=`{row.shift_r2_mean:.3f}`，dep R²=`{row.depmap_r2_mean:.3f}`。"
            )
    lines.extend(
        [
            "",
            "### axis bootstrap stability",
            "",
        ]
    )
    if stable_axis_rows.empty:
        lines.append("- 当前没有 axis 在 bootstrap 下达到稳定 formal call。")
    else:
        for row in stable_axis_rows.itertuples(index=False):
            lines.append(
                f"- `{row.axis_id}`：dominant bootstrap call=`{row.bootstrap_dominant_call}`，"
                f"稳定度=`{row.bootstrap_dominant_call_fraction:.2f}`。"
            )

    lines.extend(
        [
            "",
            "## 证据分层摘要",
            "",
            f"- `primary_evidence`：`{int(evidence_counts.get('primary_evidence', 0))}` 个对象。",
            f"- `supporting_but_sensitive/supporting_but_unstable`：`{int(evidence_counts.get('supporting_but_sensitive', 0) + evidence_counts.get('supporting_but_unstable', 0))}` 个对象。",
            f"- `preliminary_only`：`{int(evidence_counts.get('preliminary_only', 0))}` 个对象。",
            "",
            "## 解释边界",
            "",
            "- 这里的结果支持 `target` 或 `axis` 上 transcriptomic impact 与 cellular dependency 的共定位，不构成因果证明。",
            "- `Q2/Q3` 在这里被保留为 deviation structure，而不是被当作噪音丢弃。",
            "- 若后续需要 formal 写作，应优先引用 shared anchors 与 shared backbone axes，而不是把单个整体相关系数当作主叙事。",
        ]
    )

    (config.report_root / "bridge_decomposition_report.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def run_from_config(config_path: Path) -> dict[str, Any]:
    config = parse_config(resolve_path(config_path))
    config.report_root.mkdir(parents=True, exist_ok=True)

    bridge, membership, truth_contract = load_inputs(config)
    target_level = prepare_target_level_table(bridge, config)
    target_grid_summary = build_target_grid_summary(target_level, config)
    shared_anchors = build_shared_anchor_table(target_level, config)
    anchor_sensitivity, shared_anchor_stability = build_anchor_sensitivity_tables(target_level, config)
    annotated_target_level = add_axis_annotations(target_level, membership, truth_contract)
    axis_summary = build_axis_level_summary(annotated_target_level, config)
    axis_bootstrap = build_axis_bootstrap_stability(annotated_target_level, axis_summary, config)
    evidence_tier_summary = build_evidence_tier_summary(shared_anchor_stability, axis_summary, axis_bootstrap)
    plot_outputs = plot_target_level_joint_grid(target_level, config)
    axis_plot_output = plot_axis_sharedness(axis_summary, config)

    target_level.to_csv(config.report_root / "target_level_joint_grid.tsv", sep="\t", index=False)
    target_grid_summary.to_csv(config.report_root / "target_level_grid_summary.tsv", sep="\t", index=False)
    shared_anchors.to_csv(config.report_root / "shared_canonical_anchor_summary.tsv", sep="\t", index=False)
    anchor_sensitivity.to_csv(config.report_root / "anchor_cutoff_sensitivity.tsv", sep="\t", index=False)
    shared_anchor_stability.to_csv(config.report_root / "shared_anchor_stability.tsv", sep="\t", index=False)
    axis_summary.to_csv(config.report_root / "axis_level_shared_explanatory_summary.tsv", sep="\t", index=False)
    axis_bootstrap.to_csv(config.report_root / "axis_bootstrap_stability.tsv", sep="\t", index=False)
    evidence_tier_summary.to_csv(config.report_root / "evidence_tier_summary.tsv", sep="\t", index=False)

    write_markdown_report(
        config,
        target_grid_summary,
        shared_anchors,
        axis_summary,
        shared_anchor_stability,
        axis_bootstrap,
        evidence_tier_summary,
    )

    run_summary = {
        "config_path": str(config.config_path.relative_to(PROJECT_ROOT)),
        "report_root": str(config.report_root.relative_to(PROJECT_ROOT)),
        "cell_lines": config.cell_lines,
        "shift_metric": config.shift_metric,
        "depmap_metric": config.depmap_metric,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "outputs": [
            "target_level_joint_grid.tsv",
            "target_level_grid_summary.tsv",
            "shared_canonical_anchor_summary.tsv",
            "anchor_cutoff_sensitivity.tsv",
            "shared_anchor_stability.tsv",
            "axis_level_shared_explanatory_summary.tsv",
            "axis_bootstrap_stability.tsv",
            "evidence_tier_summary.tsv",
            "bridge_decomposition_report.md",
            *plot_outputs,
            axis_plot_output,
        ],
    }
    (config.report_root / "run_summary.json").write_text(
        json.dumps(run_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "report_root": config.report_root,
        "run_summary": config.report_root / "run_summary.json",
        "outputs": [config.report_root / item for item in run_summary["outputs"]],
    }


def main() -> None:
    args = build_parser().parse_args()
    outputs = run_from_config(Path(args.config))
    print(f"bridge decomposition 已写出到 {outputs['report_root'].relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
