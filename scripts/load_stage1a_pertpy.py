from __future__ import annotations

from pathlib import Path
import shutil
from urllib.request import urlretrieve

import anndata as ad
import pandas as pd

try:
    import pertpy as pt
except ModuleNotFoundError:
    pt = None

from stage1a_catalog import FORMAL_SOURCE_DATASETS, RAW_STAGE1A_DIR

PERTURBATION_CANDIDATES = ["perturbation", "gene", "target", "guide"]
CONTROL_CANDIDATES = ["condition", "control"]
KEY_CANDIDATES = PERTURBATION_CANDIDATES + CONTROL_CANDIDATES
DIRECT_DOWNLOAD_URLS = {
    "replogle_2022_k562_essential": "https://exampledata.scverse.org/pertpy/replogle_2022_k562_essential.h5ad",
    "replogle_2022_rpe1": "https://zenodo.org/record/10044268/files/ReplogleWeissman2022_rpe1.h5ad?download=1",
    "norman_2019": "https://zenodo.org/record/10044268/files/NormanWeissman2019_filtered.h5ad?download=1",
    "adamson_2016_upr_perturb_seq": "https://zenodo.org/record/10044268/files/AdamsonWeissman2016_GSM2406681_10X010.h5ad?download=1",
    "tian_2019_day7neuron": "https://zenodo.org/records/10044268/files/TianKampmann2019_day7neuron.h5ad?download=1",
    "tian_2019_ipsc": "https://zenodo.org/records/10044268/files/TianKampmann2019_iPSC.h5ad?download=1",
    "tian_2021_crispri": "https://zenodo.org/records/10044268/files/TianKampmann2021_CRISPRi.h5ad?download=1",
}


def format_columns(columns) -> str:
    return ",".join(map(str, columns))


def get_column_set(columns) -> set[str]:
    return {str(col) for col in columns}


def has_any(obs_columns, var_columns, candidates: list[str]) -> bool:
    combined_columns = get_column_set(obs_columns) | get_column_set(var_columns)
    return any(candidate in combined_columns for candidate in candidates)


def describe_presence(obs_columns, var_columns, candidate: str) -> str:
    in_obs = candidate in get_column_set(obs_columns)
    in_var = candidate in get_column_set(var_columns)

    if in_obs and in_var:
        return "obs,var"
    if in_obs:
        return "obs"
    if in_var:
        return "var"
    return "不存在"


def print_presence(obs_columns, var_columns) -> None:
    for candidate in KEY_CANDIDATES:
        print(f"  - {candidate}: {describe_presence(obs_columns, var_columns, candidate)}")

def load_or_download_dataset(name: str, loader, output_path: Path):
    if output_path.exists():
        print(f"检测到本地文件，跳过下载: {output_path}")
        return ad.read_h5ad(output_path)

    if name in DIRECT_DOWNLOAD_URLS:
        print(f"开始下载 {name} 正式文件。")
        print(f"下载地址: {DIRECT_DOWNLOAD_URLS[name]}")
        urlretrieve(DIRECT_DOWNLOAD_URLS[name], output_path)
        return ad.read_h5ad(output_path)

    if loader is None:
        raise ModuleNotFoundError(
            "当前环境缺少 pertpy，且该数据集未配置 direct-download URL。"
        )

    print("开始通过 pertpy 加载，并直接复用下载后的原始文件。")
    adata = loader()
    downloaded_path = output_path.parent / output_path.name

    if downloaded_path.exists() and downloaded_path != output_path:
        print(f"移动原始文件到正式目录: {downloaded_path} -> {output_path}")
        shutil.move(downloaded_path, output_path)

    return adata


def main() -> None:
    output_dir = RAW_STAGE1A_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    audit_rows = []

    for dataset in FORMAL_SOURCE_DATASETS:
        name = dataset.name
        output_path = dataset.path
        loader = None
        if pt is not None:
            loader = getattr(pt.data, dataset.loader_name, None)

        print(f"=== {name} ===")
        adata = load_or_download_dataset(name, loader, output_path)

        print(f"shape: {adata.shape}")
        print(f"obs.columns: {list(map(str, adata.obs.columns))}")
        print(f"var.columns: {list(map(str, adata.var.columns))}")
        print("关键列检查:")
        print_presence(adata.obs.columns, adata.var.columns)

        print(f"已保存: {output_path}")
        print()

        audit_rows.append(
            {
                "dataset": name,
                "n_cells": adata.n_obs,
                "n_genes": adata.n_vars,
                "obs_columns": format_columns(adata.obs.columns),
                "var_columns": format_columns(adata.var.columns),
                "has_perturbation_label": has_any(
                    adata.obs.columns, adata.var.columns, PERTURBATION_CANDIDATES
                ),
                "has_control_or_condition": has_any(
                    adata.obs.columns, adata.var.columns, CONTROL_CANDIDATES
                ),
            }
        )

    audit_path = output_dir / "audit_summary.tsv"
    audit_df = pd.DataFrame(audit_rows)
    audit_df.to_csv(audit_path, sep="\t", index=False)
    print(f"audit_summary 已保存: {audit_path}")
    print(audit_df.to_string(index=False))


if __name__ == "__main__":
    main()
