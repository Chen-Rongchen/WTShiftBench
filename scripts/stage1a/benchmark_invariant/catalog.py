from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_STAGE1A_DIR = PROJECT_ROOT / "data/raw/stage1a"
STAGE1A_BACKUP_DIR = RAW_STAGE1A_DIR / "backups"
FORMAL_FILTERED_DIR = PROJECT_ROOT / "data/processed/stage1a/formal_filtered"
FORMAL_REGISTRY_PATH = PROJECT_ROOT / "configs/stage1a_formal_datasets.yaml"
FORMAL_CONTRACT_TSV_PATH = PROJECT_ROOT / "reports/stage1a/formal_contract/formal_dataset_registry.tsv"
LEGACY_TRUTH_REGISTRY_PATH = PROJECT_ROOT / "data/frozen/stage1a_truth/truth_registry.tsv"
ALIGNED_TRUTH_REGISTRY_PATH = PROJECT_ROOT / "data/frozen/stage1a_truth/aligned_truth_registry.tsv"
FULLSPACE_TRUTH_REGISTRY_PATH = PROJECT_ROOT / "data/frozen/stage1a_truth/fullspace_truth_registry.tsv"


@dataclass(frozen=True)
class SourceDataset:
    name: str
    loader_name: str
    file_name: str
    role: str = "mainline"
    default_in_mainline: bool = True

    @property
    def path(self) -> Path:
        return RAW_STAGE1A_DIR / self.file_name


@dataclass(frozen=True)
class FormalDatasetContract:
    dataset_id: str
    cell_line: str
    control_definition: str
    perturbation_unit: str
    n_cells_raw: int
    n_cells_formal: int
    n_controls: int
    n_perturbed: int
    n_unique_targets: int
    stage: str
    status: str
    output_path: str
    notes: str
    role: str = "mainline"
    default_in_mainline: bool = True
    source_loader: str = ""
    source_origin: str = ""
    source_download_url: str = ""

    @property
    def path(self) -> Path:
        output_path = Path(self.output_path)
        if output_path.is_absolute():
            return output_path
        return PROJECT_ROOT / output_path


@dataclass(frozen=True)
class Stage1ATruthRegistryEntry:
    dataset_id: str
    truth_path: str
    n_targets_expected: int
    n_targets_built: int
    n_genes: int
    control_definition: str
    freeze_status: str
    matrix_source: str = ""
    log_normalization_applied_in_truth_build: bool | str = ""
    delta_space: str = ""
    evaluation_space: str = ""
    source_truth_path: str = ""

    @property
    def path(self) -> Path:
        truth_path = Path(self.truth_path)
        if truth_path.is_absolute():
            return truth_path
        return PROJECT_ROOT / truth_path


MAINLINE_SOURCE_DATASETS = [
    SourceDataset(
        name="replogle_2022_k562_essential",
        loader_name="replogle_2022_k562_essential",
        file_name="replogle_2022_k562_essential.h5ad",
        role="mainline",
        default_in_mainline=True,
    ),
    SourceDataset(
        name="replogle_2022_rpe1",
        loader_name="replogle_2022_rpe1",
        file_name="replogle_2022_rpe1.h5ad",
        role="mainline",
        default_in_mainline=True,
    ),
    SourceDataset(
        name="tian_2019_day7neuron",
        loader_name="tian_2019_day7neuron",
        file_name="tian_2019_day7neuron.h5ad",
        role="mainline",
        default_in_mainline=True,
    ),
]

# 当前 formal source catalog 只登记 official formal 主线。
# candidate admission batch 与 annex side track 单独在 dataset_tiering.md 管理，
# 不写入 formal registry / formal source catalog。
AUXILIARY_SOURCE_DATASETS: list[SourceDataset] = []

ALL_SOURCE_DATASETS = [*MAINLINE_SOURCE_DATASETS]

# 兼容旧导出名。当前语义收紧为“当前 official formal source datasets”。
FORMAL_SOURCE_DATASETS = MAINLINE_SOURCE_DATASETS


def load_formal_dataset_contracts(
    registry_path: Path = FORMAL_REGISTRY_PATH,
    *,
    include_auxiliary: bool = False,
) -> list[FormalDatasetContract]:
    if not registry_path.exists():
        return []

    payload = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    datasets = payload.get("datasets", [])
    contracts = [FormalDatasetContract(**dataset) for dataset in datasets]
    if include_auxiliary:
        return contracts
    return [contract for contract in contracts if contract.default_in_mainline]


def load_stage1a_truth_registry(
    registry_path: Path = ALIGNED_TRUTH_REGISTRY_PATH,
) -> list[Stage1ATruthRegistryEntry]:
    if not registry_path.exists():
        return []

    registry = pd.read_csv(registry_path, sep="\t")
    required_columns = [
        "dataset_id",
        "truth_path",
        "n_targets_expected",
        "n_targets_built",
        "n_genes",
        "control_definition",
        "freeze_status",
    ]
    missing_columns = sorted(set(required_columns) - set(registry.columns))
    if missing_columns:
        raise ValueError(f"truth_registry.tsv 缺少列: {missing_columns}")

    optional_columns = [
        column
        for column in [
            "matrix_source",
            "log_normalization_applied_in_truth_build",
            "delta_space",
            "evaluation_space",
            "source_truth_path",
        ]
        if column in registry.columns
    ]
    registry = registry.loc[:, [*required_columns, *optional_columns]].copy()
    registry["dataset_id"] = registry["dataset_id"].astype("string")
    registry["truth_path"] = registry["truth_path"].astype("string")
    registry["control_definition"] = registry["control_definition"].astype("string")
    registry["freeze_status"] = registry["freeze_status"].astype("string")
    if "matrix_source" in registry.columns:
        registry["matrix_source"] = registry["matrix_source"].astype("string")
    else:
        registry["matrix_source"] = ""
    if "log_normalization_applied_in_truth_build" in registry.columns:
        registry["log_normalization_applied_in_truth_build"] = (
            registry["log_normalization_applied_in_truth_build"]
        )
    else:
        registry["log_normalization_applied_in_truth_build"] = ""
    if "delta_space" in registry.columns:
        registry["delta_space"] = registry["delta_space"].astype("string")
    else:
        registry["delta_space"] = ""
    if "evaluation_space" in registry.columns:
        registry["evaluation_space"] = registry["evaluation_space"].astype("string")
    else:
        registry["evaluation_space"] = ""
    if "source_truth_path" in registry.columns:
        registry["source_truth_path"] = registry["source_truth_path"].astype("string")
    else:
        registry["source_truth_path"] = ""
    for column in ["n_targets_expected", "n_targets_built", "n_genes"]:
        registry[column] = pd.to_numeric(registry[column], errors="raise").astype(int)

    return [
        Stage1ATruthRegistryEntry(**row)
        for row in registry.to_dict(orient="records")
    ]


def load_stage1a_aligned_truth_registry() -> list[Stage1ATruthRegistryEntry]:
    return load_stage1a_truth_registry(ALIGNED_TRUTH_REGISTRY_PATH)


def load_stage1a_fullspace_truth_registry() -> list[Stage1ATruthRegistryEntry]:
    return load_stage1a_truth_registry(FULLSPACE_TRUTH_REGISTRY_PATH)


def get_formal_dataset_contracts() -> tuple[FormalDatasetContract, ...]:
    return tuple(load_formal_dataset_contracts())


def get_formal_dataset_index() -> dict[str, FormalDatasetContract]:
    return {
        dataset.dataset_id: dataset
        for dataset in load_formal_dataset_contracts(include_auxiliary=True)
    }


def get_formal_dataset_contract(dataset_id: str) -> FormalDatasetContract:
    dataset_index = get_formal_dataset_index()
    try:
        return dataset_index[dataset_id]
    except KeyError as exc:
        raise KeyError(f"未在 formal dataset registry 中找到 dataset_id={dataset_id}") from exc


def get_source_dataset_index() -> dict[str, SourceDataset]:
    return {dataset.name: dataset for dataset in FORMAL_SOURCE_DATASETS}


def get_source_dataset(dataset_id: str) -> SourceDataset:
    dataset_index = get_source_dataset_index()
    try:
        return dataset_index[dataset_id]
    except KeyError as exc:
        raise KeyError(f"未在 source dataset catalog 中找到 dataset_id={dataset_id}") from exc

BACKUP_DATASET_FILES = {
    "dixit_2016": STAGE1A_BACKUP_DIR / "dixit_2016.h5ad",
    "tian_2019_day7neuron": STAGE1A_BACKUP_DIR / "tian_2019_day7neuron.h5ad",
}
