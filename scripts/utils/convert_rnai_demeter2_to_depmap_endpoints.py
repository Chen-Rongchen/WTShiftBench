#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/rnai_demeter2_conversion_v1.json"


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_config(config_path: Path) -> dict[str, Any]:
    return json.loads(config_path.read_text(encoding="utf-8"))


def clean_gene_name(label: str) -> str:
    text = str(label)
    if " (" in text and text.endswith(")"):
        return text.split(" (", 1)[0]
    return text


def load_ccle_model_mapping(config: dict[str, Any]) -> pd.DataFrame:
    inputs = config["inputs"]
    conversion = config["conversion"]
    sample_info = pd.read_csv(resolve_path(str(inputs["sample_info_path"])))
    model = pd.read_csv(resolve_path(str(inputs["depmap_model_path"])), usecols=[
        str(conversion["model_id_column"]),
        str(conversion["model_ccle_column"]),
    ])

    ccle_col = str(conversion["cell_line_id_column"])
    model_id_col = str(conversion["model_id_column"])
    model_ccle_col = str(conversion["model_ccle_column"])
    known_ccle_ids = sample_info[[ccle_col]].drop_duplicates()
    joined = known_ccle_ids.merge(model, left_on=ccle_col, right_on=model_ccle_col, how="left")
    return joined.drop_duplicates(subset=[ccle_col])


def convert_score_matrix(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    inputs = config["inputs"]
    conversion = config["conversion"]
    score_path = resolve_path(str(inputs["score_matrix_path"]))
    score_direction = str(conversion["score_direction"])
    if score_direction != "lower_is_more_dependent":
        raise ValueError(f"不支持的 RNAi 分数方向: {score_direction}")

    ccle_col = str(conversion["cell_line_id_column"])
    model_id_col = str(conversion["model_id_column"])
    mapping = load_ccle_model_mapping(config)
    mapped = mapping.dropna(subset=[model_id_col]).set_index(ccle_col)[model_id_col]
    scores = pd.read_csv(score_path, index_col=0)
    matched_ccle_ids = [column for column in scores.columns if column in mapped.index]
    if not matched_ccle_ids:
        raise ValueError("RNAi score matrix 中没有细胞系能映射到 DepMap ModelID。")

    effect = scores.loc[:, matched_ccle_ids].transpose()
    effect.index = mapped.loc[matched_ccle_ids].astype(str).to_numpy()
    effect.index.name = "ModelID"
    effect.columns = [clean_gene_name(column) for column in effect.columns]
    effect = effect.reset_index()

    dependency = effect.copy()
    value_columns = [column for column in dependency.columns if column != "ModelID"]
    dependency.loc[:, value_columns] = -dependency.loc[:, value_columns]

    summary = pd.DataFrame(
        [
            {"metric": "input_score_matrix_path", "value": str(score_path)},
            {"metric": "input_cell_lines", "value": str(scores.shape[1])},
            {"metric": "mapped_cell_lines", "value": str(len(matched_ccle_ids))},
            {"metric": "missing_model_id_mappings", "value": str(scores.shape[1] - len(matched_ccle_ids))},
            {"metric": "genes", "value": str(scores.shape[0])},
            {"metric": "score_direction", "value": score_direction},
            {"metric": "gene_effect_output", "value": str(resolve_path(str(config["outputs"]["gene_effect_path"])))},
            {"metric": "gene_dependency_output", "value": str(resolve_path(str(config["outputs"]["gene_dependency_path"])))},
        ]
    )
    missing = pd.DataFrame(
        {
            ccle_col: [column for column in scores.columns if column not in mapped.index],
            "reason": "not_found_in_depmap_model_csv",
        }
    )
    return effect, dependency, summary, missing


def write_outputs(config: dict[str, Any]) -> dict[str, Path]:
    outputs = config["outputs"]
    effect, dependency, summary, missing = convert_score_matrix(config)
    effect_path = resolve_path(str(outputs["gene_effect_path"]))
    dependency_path = resolve_path(str(outputs["gene_dependency_path"]))
    summary_path = resolve_path(str(outputs["summary_path"]))
    missing_mapping_path = resolve_path(str(outputs["missing_mapping_path"]))

    effect_path.parent.mkdir(parents=True, exist_ok=True)
    dependency_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    missing_mapping_path.parent.mkdir(parents=True, exist_ok=True)
    effect.to_csv(effect_path, index=False)
    dependency.to_csv(dependency_path, index=False)
    summary.to_csv(summary_path, sep="\t", index=False)
    missing.to_csv(missing_mapping_path, sep="\t", index=False)
    return {
        "gene_effect": effect_path,
        "gene_dependency": dependency_path,
        "summary": summary_path,
        "missing_mapping": missing_mapping_path,
    }


def run_from_config(config_path: Path) -> dict[str, Path]:
    config = load_config(resolve_path(config_path))
    return write_outputs(config)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert DEMETER2 RNAi scores to DepMap-style endpoint tables.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    args = parser.parse_args()

    paths = run_from_config(Path(args.config))
    for label, path in paths.items():
        print(f"{label}\t{path}")


if __name__ == "__main__":
    main()
