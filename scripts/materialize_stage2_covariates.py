#!/usr/bin/env python3
"""从 Stage 2 protospacer calls 物化 covariates TSV。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import mmread

from wtbench.stage2_truth_bridge import (
    is_control_target,
    load_feature_metadata,
    parse_target_gene,
    resolve_path,
    stringify,
)


def load_config(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "datasets" not in payload:
        raise ValueError("配置缺少 datasets。")
    return payload


def build_quantile_labels(n_bins: int) -> list[str]:
    return [f"q{i}" for i in range(1, n_bins + 1)]


def extract_barcode_gem_group(barcodes: pd.Series) -> pd.Series:
    groups = barcodes.astype("string").str.extract(r"-(\d+)$")[0]
    return groups.astype("string")


def load_transcriptome_covariates(dataset: dict, calls: pd.DataFrame) -> pd.DataFrame:
    matrix_path_raw = dataset.get("matrix_path")
    barcodes_path_raw = dataset.get("barcodes_path")
    features_path_raw = dataset.get("features_path")
    if not (matrix_path_raw and barcodes_path_raw and features_path_raw):
        raise ValueError("缺少 transcriptome covariates 所需的 matrix/barcodes/features 路径。")

    barcodes = pd.read_csv(
        resolve_path(str(barcodes_path_raw)),
        sep="\t",
        header=None,
        names=["cell_barcode"],
    )
    barcodes["cell_barcode"] = stringify(barcodes["cell_barcode"])
    barcode_index = pd.Series(np.arange(len(barcodes), dtype=np.int64), index=barcodes["cell_barcode"])

    calls = calls.loc[calls["cell_barcode"].isin(barcode_index.index), ["cell_barcode"]].copy()
    if calls.empty:
        raise ValueError("single-feature calls 无法与 transcriptome barcodes 对齐。")

    calls["matrix_col_index"] = calls["cell_barcode"].map(barcode_index).astype(int)
    calls = calls.sort_values("matrix_col_index").drop_duplicates(subset=["cell_barcode"])

    feature_meta = load_feature_metadata(resolve_path(str(features_path_raw)))
    gene_mask = feature_meta["feature_type"].eq("Gene Expression").to_numpy()
    matrix = mmread(resolve_path(str(matrix_path_raw))).tocsr()
    selected = matrix[gene_mask, :][:, calls["matrix_col_index"].to_numpy()].transpose().tocsr()

    total_signal = np.asarray(selected.sum(axis=1)).ravel().astype(float)
    detected_genes = np.asarray(selected.getnnz(axis=1)).ravel().astype(float)
    return pd.DataFrame(
        {
            "cell_barcode": calls["cell_barcode"].to_numpy(),
            "transcriptome_total_signal": total_signal,
            "transcriptome_detected_genes": detected_genes,
        }
    )


def materialize_one(dataset: dict, control_prefix: str, n_bins: int) -> Path:
    calls_path = resolve_path(dataset["protospacer_calls_path"])
    output_path = resolve_path(dataset["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    calls = pd.read_csv(calls_path)
    required = {"cell_barcode", "num_features", "feature_call", "num_umis"}
    missing = sorted(required - set(calls.columns))
    if missing:
        raise ValueError(f"{calls_path} 缺少列: {missing}")

    calls = calls.copy()
    calls["cell_barcode"] = calls["cell_barcode"].astype("string")
    calls["feature_call"] = calls["feature_call"].astype("string")
    calls["num_features"] = pd.to_numeric(calls["num_features"], errors="coerce")
    calls["num_umis"] = pd.to_numeric(calls["num_umis"], errors="coerce")
    calls["target_gene"] = calls["feature_call"].map(parse_target_gene).astype("string")
    calls["barcode_gem_group"] = extract_barcode_gem_group(calls["cell_barcode"])
    calls["is_control"] = calls["target_gene"].map(
        lambda x: is_control_target(str(x), control_prefix)
    )

    # 与 truth bridge 主线保持一致：只保留 single-feature called cells。
    calls = calls.loc[calls["num_features"].eq(1)].copy()
    if calls.empty:
        raise ValueError(f"{calls_path} 在 num_features == 1 过滤后为空。")

    if dataset.get("matrix_path") and dataset.get("barcodes_path") and dataset.get("features_path"):
        transcriptome = load_transcriptome_covariates(dataset, calls)
        calls = calls.merge(transcriptome, on="cell_barcode", how="left")

    threshold_path_raw = dataset.get("protospacer_thresholds_path")
    if threshold_path_raw:
        threshold_path = resolve_path(str(threshold_path_raw))
        thresholds = pd.read_csv(threshold_path)
        thresholds = thresholds.rename(columns={"Protospacer": "feature_call", "UMI threshold": "protospacer_umi_threshold"})
        thresholds["feature_call"] = thresholds["feature_call"].astype("string")
        thresholds["protospacer_umi_threshold"] = pd.to_numeric(
            thresholds["protospacer_umi_threshold"], errors="coerce"
        )
        calls = calls.merge(
            thresholds.loc[:, ["feature_call", "protospacer_umi_threshold"]],
            on="feature_call",
            how="left",
        )

    labels = build_quantile_labels(n_bins)
    calls["num_umis_quantile_bin"] = pd.qcut(
        calls["num_umis"],
        q=n_bins,
        labels=labels,
        duplicates="drop",
    ).astype("string")
    calls["num_umis_above_median"] = calls["num_umis"].ge(calls["num_umis"].median())
    if "transcriptome_total_signal" in calls.columns:
        calls["transcriptome_total_signal_quantile_bin"] = pd.qcut(
            calls["transcriptome_total_signal"],
            q=n_bins,
            labels=labels,
            duplicates="drop",
        ).astype("string")
    if "transcriptome_detected_genes" in calls.columns:
        calls["transcriptome_detected_genes_quantile_bin"] = pd.qcut(
            calls["transcriptome_detected_genes"],
            q=n_bins,
            labels=labels,
            duplicates="drop",
        ).astype("string")
    if "protospacer_umi_threshold" in calls.columns:
        calls["num_umis_minus_threshold"] = calls["num_umis"] - calls["protospacer_umi_threshold"]
        calls["num_umis_over_threshold_ratio"] = calls["num_umis"] / calls["protospacer_umi_threshold"]
        valid_ratio = calls["num_umis_over_threshold_ratio"].replace([pd.NA, float("inf")], pd.NA)
        calls["num_umis_over_threshold_bin"] = pd.qcut(
            valid_ratio,
            q=n_bins,
            labels=labels,
            duplicates="drop",
        ).astype("string")

    out = calls.loc[
        :,
        [
            "cell_barcode",
            "feature_call",
            "target_gene",
            "is_control",
            "num_features",
            "num_umis",
            "barcode_gem_group",
            "num_umis_quantile_bin",
            "num_umis_above_median",
            "transcriptome_total_signal",
            "transcriptome_total_signal_quantile_bin",
            "transcriptome_detected_genes",
            "transcriptome_detected_genes_quantile_bin",
            "protospacer_umi_threshold",
            "num_umis_minus_threshold",
            "num_umis_over_threshold_ratio",
            "num_umis_over_threshold_bin",
        ],
    ].sort_values("cell_barcode")
    out.to_csv(output_path, sep="\t", index=False)
    return output_path


def materialize_covariates_from_config(config_path: Path) -> list[Path]:
    config = load_config(config_path)
    control_prefix = str(config.get("control_target_prefix", "intergenic_chr_"))
    n_bins = int(config.get("quantile_bins", config.get("num_umis_quantile_bins", 4)))

    outputs: list[Path] = []
    for dataset in config["datasets"]:
        outputs.append(materialize_one(dataset, control_prefix=control_prefix, n_bins=n_bins))
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="物化 Stage 2 covariates TSV。")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/stage2/hcc_covariates_v1.json"),
        help="covariates 物化配置 JSON。",
    )
    args = parser.parse_args()

    outputs = materialize_covariates_from_config(args.config)

    print("Stage 2 covariates 物化完成。")
    for path in outputs:
        print(f"- {path}")


if __name__ == "__main__":
    main()
