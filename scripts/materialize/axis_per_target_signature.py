from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from wtbench.truth_bridge import (
    build_dataset_specs,
    load_config as load_truth_bridge_config,
    load_depmap_endpoint,
    mean_vector,
    prepare_bridge_inputs,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/axis_per_target_signature_v1.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="物化 Stage 2 axis per-target signature。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="per-target signature 配置 JSON 路径。")
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload


def load_axis_membership(axis_analysis_config: dict[str, object]) -> pd.DataFrame:
    input_objects = dict(axis_analysis_config["input_objects"])
    membership_path = resolve_path(str(input_objects["axis_membership_path"]))
    membership = pd.read_csv(membership_path, sep="\t")
    membership = membership.rename(columns={"fine_axis": "axis_id"}).loc[:, ["axis_id", "target_gene"]]
    if membership.empty:
        raise ValueError("axis membership 为空，无法物化 per-target signature。")
    return membership.drop_duplicates().sort_values(["axis_id", "target_gene"]).reset_index(drop=True)


def build_target_delta_frame(
    *,
    cell_line: str,
    normalized,
    calls: pd.DataFrame,
    gene_names: pd.Index,
    min_target_cells: int,
    selected_targets: set[str],
) -> pd.DataFrame:
    control_positions = np.flatnonzero(calls["is_control"].to_numpy(dtype=bool))
    control_mean = mean_vector(normalized[control_positions])

    records: list[pd.DataFrame] = []
    non_control = calls.loc[~calls["is_control"].astype(bool)].copy()
    for target_gene, target_calls in non_control.groupby("target_gene", sort=True):
        target_gene = str(target_gene)
        if target_gene not in selected_targets:
            continue
        n_cells_target = int(len(target_calls))
        if n_cells_target < min_target_cells:
            continue
        target_index = target_calls.index.to_numpy()
        target_mean = mean_vector(normalized[target_index])
        signed_delta = target_mean - control_mean
        frame = pd.DataFrame(
            {
                "cell_line": cell_line,
                "target_gene": target_gene,
                "gene": gene_names.astype(str),
                "signed_score": signed_delta.astype(float),
                "n_cells_target": n_cells_target,
            }
        )
        frame = (
            frame.groupby(["cell_line", "target_gene", "gene", "n_cells_target"], as_index=False)["signed_score"]
            .mean()
            .sort_values(["target_gene", "gene"])
            .reset_index(drop=True)
        )
        records.append(frame)

    if not records:
        return pd.DataFrame(columns=["cell_line", "target_gene", "gene", "signed_score", "n_cells_target"])
    return pd.concat(records, ignore_index=True)


def main() -> None:
    args = build_parser().parse_args()
    config = load_json(resolve_path(args.config))

    truth_bridge_config = load_truth_bridge_config(resolve_path(str(config["input"]["truth_bridge_config_path"])))
    axis_analysis_config = load_json(resolve_path(str(config["input"]["axis_analysis_config_path"])))
    output_path = resolve_path(str(config["output"]["table_path"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    membership = load_axis_membership(axis_analysis_config)
    selected_targets = set(membership["target_gene"].astype(str))

    dataset_role = str(config["analysis"]["dataset_role"])
    selected_cell_lines = {str(item) for item in config["analysis"]["cell_lines"]}
    require_all_cell_lines = bool(config["analysis"]["require_all_cell_lines"])
    score_mode = str(config["analysis"]["score_mode"])
    if score_mode != "abs_of_mean_signed_delta":
        raise ValueError(f"当前不支持的 score_mode: {score_mode}")

    depmap_cfg = truth_bridge_config["depmap"]
    depmap_effect = load_depmap_endpoint(resolve_path(str(depmap_cfg["gene_effect_path"])))
    depmap_dependency = load_depmap_endpoint(resolve_path(str(depmap_cfg["gene_dependency_path"])))

    specs = [
        spec
        for spec in build_dataset_specs(truth_bridge_config)
        if spec.dataset_role == dataset_role and spec.cell_line in selected_cell_lines
    ]
    if not specs:
        raise ValueError("没有匹配到任何 Stage 2 truth bridge dataset spec。")

    min_target_cells = int(truth_bridge_config["filters"]["min_target_cells"])
    per_line_frames: list[pd.DataFrame] = []
    for spec in specs:
        normalized, _embeddings, calls, gene_meta, effect_series, dependency_series = prepare_bridge_inputs(
            spec,
            truth_bridge_config,
            depmap_effect,
            depmap_dependency,
        )
        frame = build_target_delta_frame(
            cell_line=spec.cell_line,
            normalized=normalized,
            calls=calls,
            gene_names=pd.Index(gene_meta["feature_name"].astype(str)),
            min_target_cells=min_target_cells,
            selected_targets=selected_targets,
        )
        per_line_frames.append(frame)

    if not per_line_frames:
        raise ValueError("没有生成任何 per-target gene delta。")
    combined = pd.concat(per_line_frames, ignore_index=True)
    if combined.empty:
        raise ValueError("per-target gene delta 结果为空。")

    combined = membership.merge(combined, on="target_gene", how="inner")
    if combined.empty:
        raise ValueError("axis membership 与 per-target delta 没有交集。")

    aggregated = (
        combined.groupby(["axis_id", "target_gene", "gene"], as_index=False)
        .agg(
            signed_score=("signed_score", "mean"),
            n_cell_lines=("cell_line", "nunique"),
            present_cell_lines=("cell_line", lambda x: "|".join(sorted({str(item) for item in x}))),
            n_cells_target_min=("n_cells_target", "min"),
            n_cells_target_mean=("n_cells_target", "mean"),
        )
        .sort_values(["axis_id", "target_gene", "gene"])
        .reset_index(drop=True)
    )

    if require_all_cell_lines:
        expected_count = len(specs)
        aggregated = aggregated.loc[aggregated["n_cell_lines"].eq(expected_count)].copy()
        if aggregated.empty:
            raise ValueError("要求所有 cell lines 同时存在后，per-target signature 为空。")

    aggregated["score"] = aggregated["signed_score"].abs()
    aggregated["rank"] = (
        aggregated.groupby(["axis_id", "target_gene"])["score"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    result = aggregated.loc[
        :,
        [
            "axis_id",
            "target_gene",
            "gene",
            "score",
            "signed_score",
            "rank",
            "n_cell_lines",
            "present_cell_lines",
            "n_cells_target_min",
            "n_cells_target_mean",
        ],
    ].sort_values(["axis_id", "target_gene", "rank", "gene"]).reset_index(drop=True)
    result.to_csv(output_path, sep="\t", index=False)

    print(
        json.dumps(
            {
                "status": "completed",
                "output_path": str(output_path.relative_to(PROJECT_ROOT)),
                "n_rows": int(len(result)),
                "n_targets": int(result.loc[:, ["axis_id", "target_gene"]].drop_duplicates().shape[0]),
                "cell_lines": sorted(spec.cell_line for spec in specs),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
