from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from wtbench.truth_bridge import (
    build_dataset_specs,
    load_config as load_truth_bridge_config,
    load_depmap_endpoint,
    mean_vector,
    prepare_bridge_inputs,
    resolve_path,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/per_target_signature_materialization_v1.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="物化 Stage 2 per_target_signature。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="per_target_signature 物化配置 JSON 路径。")
    return parser


def load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload


def build_axis_target_map(axis_membership: pd.DataFrame) -> pd.DataFrame:
    required = {"axis_id", "target_gene"}
    missing = sorted(required - set(axis_membership.columns))
    if missing:
        raise ValueError(f"axis_membership 缺少列：{missing}")
    return axis_membership.loc[:, ["axis_id", "target_gene"]].drop_duplicates().reset_index(drop=True)


def materialize_for_dataset(
    *,
    spec,
    truth_config: dict[str, object],
    axis_target_map: pd.DataFrame,
    depmap_effect: pd.DataFrame,
    depmap_dependency: pd.DataFrame,
    min_target_cells: int,
) -> pd.DataFrame:
    normalized, _embeddings, calls, gene_meta, _effect_series, _dependency_series = prepare_bridge_inputs(
        spec,
        truth_config,
        depmap_effect,
        depmap_dependency,
    )
    control_positions = calls.index[calls["is_control"].astype(bool)].to_numpy()
    control_mean = mean_vector(normalized[control_positions])

    target_calls = calls.loc[~calls["is_control"].astype(bool)].copy()
    target_sizes = target_calls.groupby("target_gene").size().rename("n_target_cells").reset_index()
    eligible = axis_target_map.merge(target_sizes, on="target_gene", how="inner")
    eligible = eligible.loc[eligible["n_target_cells"] >= min_target_cells].copy()
    if eligible.empty:
        return pd.DataFrame(
            columns=["cell_line", "axis_id", "target_gene", "gene", "score", "abs_score", "rank_abs", "n_target_cells"]
        )

    rows: list[pd.DataFrame] = []
    gene_names = gene_meta["feature_name"].astype(str).tolist()
    for row in eligible.itertuples(index=False):
        target_index = target_calls.index[target_calls["target_gene"].astype(str).eq(str(row.target_gene))].to_numpy()
        target_mean = mean_vector(normalized[target_index])
        delta = target_mean - control_mean
        frame = pd.DataFrame(
            {
                "cell_line": spec.cell_line,
                "axis_id": str(row.axis_id),
                "target_gene": str(row.target_gene),
                "gene": gene_names,
                "score": delta,
                "abs_score": abs(delta),
                "n_target_cells": int(row.n_target_cells),
            }
        )
        frame["rank_abs"] = frame["abs_score"].rank(method="first", ascending=False).astype(int)
        rows.append(frame)
    result = pd.concat(rows, ignore_index=True)
    return result.sort_values(["cell_line", "axis_id", "target_gene", "rank_abs", "gene"]).reset_index(drop=True)


def aggregate_across_cell_lines(detailed: pd.DataFrame) -> pd.DataFrame:
    if detailed.empty:
        return pd.DataFrame(columns=["axis_id", "target_gene", "gene", "score", "abs_score", "cell_line_count", "rank_abs"])
    aggregated = (
        detailed.groupby(["axis_id", "target_gene", "gene"], as_index=False)
        .agg(
            score=("score", "mean"),
            abs_score=("abs_score", "mean"),
            cell_line_count=("cell_line", "nunique"),
        )
    )
    aggregated["rank_abs"] = (
        aggregated.groupby(["axis_id", "target_gene"])["abs_score"]
        .rank(method="first", ascending=False)
        .astype(int)
    )
    return aggregated.sort_values(["axis_id", "target_gene", "rank_abs", "gene"]).reset_index(drop=True)


def main() -> None:
    args = build_parser().parse_args()
    config = load_json(resolve_path(args.config))

    truth_config = load_truth_bridge_config(resolve_path(str(config["input"]["truth_bridge_config_path"])))
    axis_membership = pd.read_csv(resolve_path(str(config["input"]["axis_membership_path"])), sep="\t")
    axis_target_map = build_axis_target_map(axis_membership)

    dataset_role = str(config["scope"]["dataset_role"])
    scope_cell_lines = {str(item) for item in config["scope"]["cell_lines"]}
    min_target_cells = int(config["filters"]["min_target_cells"])

    specs = [
        spec
        for spec in build_dataset_specs(truth_config)
        if spec.dataset_role == dataset_role and spec.cell_line in scope_cell_lines
    ]
    if not specs:
        raise ValueError("当前配置没有匹配到任何 dataset spec。")

    depmap_effect = load_depmap_endpoint(resolve_path(str(truth_config["depmap"]["gene_effect_path"])))
    depmap_dependency = load_depmap_endpoint(resolve_path(str(truth_config["depmap"]["gene_dependency_path"])))

    detailed_frames = [
        materialize_for_dataset(
            spec=spec,
            truth_config=truth_config,
            axis_target_map=axis_target_map,
            depmap_effect=depmap_effect,
            depmap_dependency=depmap_dependency,
            min_target_cells=min_target_cells,
        )
        for spec in specs
    ]
    detailed = pd.concat(detailed_frames, ignore_index=True) if detailed_frames else pd.DataFrame()
    aggregated = aggregate_across_cell_lines(detailed)

    detailed_path = resolve_path(str(config["output"]["detailed_table_path"]))
    aggregated_path = resolve_path(str(config["output"]["aggregated_table_path"]))
    detailed_path.parent.mkdir(parents=True, exist_ok=True)
    aggregated_path.parent.mkdir(parents=True, exist_ok=True)

    detailed.to_csv(detailed_path, sep="\t", index=False)
    aggregated.to_csv(aggregated_path, sep="\t", index=False)

    print(
        json.dumps(
            {
                "status": "completed",
                "detailed_path": str(detailed_path.relative_to(PROJECT_ROOT)),
                "aggregated_path": str(aggregated_path.relative_to(PROJECT_ROOT)),
                "n_rows_detailed": int(len(detailed)),
                "n_rows_aggregated": int(len(aggregated)),
                "n_cell_lines": len(specs),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
