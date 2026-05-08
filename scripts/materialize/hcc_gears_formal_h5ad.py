from __future__ import annotations

import argparse
import json
from pathlib import Path

import anndata as ad
import pandas as pd

from wtbench.truth_bridge import (
    build_dataset_specs,
    load_config,
    load_expression_for_called_cells,
    load_single_feature_calls,
    log_normalize_csr,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_recipe(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="物化 Stage 2 HCC GEARS 使用的 normalized+log1p formal-like h5ad。")
    parser.add_argument("--config", default="configs/gears_hcc_formal_v1.json")
    parser.add_argument("--cell-line", action="append", choices=["HCC38", "HCC1143"])
    return parser


def main() -> None:
    args = build_parser().parse_args()
    recipe = load_recipe(resolve_path(args.config))
    truth_config = load_config(resolve_path(str(recipe["truth_config_path"])))
    axis_membership = pd.read_csv(resolve_path(str(recipe["axis_membership_path"])), sep="\t")
    frozen_targets = set(axis_membership["target_gene"].astype(str))
    output_root = resolve_path(str(recipe["formal_h5ad_root"]))
    selected = set(args.cell_line or [])

    rows: list[dict[str, object]] = []
    for spec in build_dataset_specs(truth_config):
        if selected and spec.cell_line not in selected:
            continue
        calls = load_single_feature_calls(spec, control_prefix=str(truth_config["filters"]["control_target_prefix"]))
        expression, calls, gene_meta = load_expression_for_called_cells(spec, calls)
        keep_mask = calls["is_control"].to_numpy(dtype=bool) | calls["target_gene"].astype(str).isin(frozen_targets).to_numpy(dtype=bool)
        filtered_calls = calls.loc[keep_mask].reset_index(drop=True)
        filtered_expression = expression[keep_mask].tocsr()
        normalized = log_normalize_csr(
            filtered_expression,
            target_sum=float(truth_config["metrics"]["normalization_target_sum"]),
        ).tocsr()
        obs = filtered_calls.loc[:, ["cell_barcode", "feature_call", "target_gene", "is_control", "num_features", "num_umis"]].copy()
        obs["cell_barcode"] = obs["cell_barcode"].astype(str)
        obs["feature_call"] = obs["feature_call"].astype(str)
        obs["target_gene"] = obs["target_gene"].astype(str)
        obs["is_control"] = obs["is_control"].astype(bool)
        obs.index = obs["cell_barcode"]
        obs.index.name = "obs_id"
        var = pd.DataFrame(index=gene_meta["feature_name"].astype(str))
        var["gene_name"] = var.index.astype(str)
        adata = ad.AnnData(X=normalized, obs=obs, var=var)
        output_path = output_root / f"{spec.cell_line}.h5ad"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        adata.write_h5ad(output_path)
        rows.append(
            {
                "cell_line": spec.cell_line,
                "output_path": str(output_path.relative_to(PROJECT_ROOT)),
                "n_obs": int(adata.n_obs),
                "n_vars": int(adata.n_vars),
                "control_cells": int(obs["is_control"].sum()),
                "target_cells": int((~obs["is_control"]).sum()),
            }
        )
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
