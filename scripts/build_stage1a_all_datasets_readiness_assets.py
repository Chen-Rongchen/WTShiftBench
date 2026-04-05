from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for candidate in (PROJECT_ROOT, SCRIPTS_DIR):
    text = str(candidate)
    if text not in sys.path:
        sys.path.insert(0, text)

from scripts.build_stage1a_candidate_formalization import build_standard_obs
from scripts.build_stage1a_main_aligned_baselines_nulls import (
    build_label_shuffle,
    build_mean_shift_baseline,
    build_random_pairing,
    build_zero_shift_null,
    dataset_seed,
)
from scripts.stage1a_split_plan_b import filter_eligible_to_heldout, load_split_governance


DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/stage1a/runs/all_datasets_readiness_fill.json"
DEFAULT_REPORT_ROOT = PROJECT_ROOT / "reports/stage1a/eval_matrix/readiness_fill"
REGISTRY_COLUMNS = [
    "dataset_id",
    "truth_path",
    "n_targets_expected",
    "n_targets_built",
    "n_genes",
    "control_definition",
    "freeze_status",
    "matrix_source",
    "log_normalization_applied_in_truth_build",
    "delta_space",
    "evaluation_space",
    "source_truth_path",
]
REQUIRED_FORMAL_OBS_COLUMNS = ("dataset_id", "is_control", "target_gene")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="补齐 all-datasets 评测矩阵的 candidate readiness 资产。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument(
        "--dataset-id",
        action="append",
        default=[],
        help="仅处理指定 dataset_id，可重复传入。",
    )
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


def stringify(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("")


def mean_expression(matrix: object) -> np.ndarray:
    values = np.asarray(matrix.mean(axis=0)).ravel()
    return values.astype(np.float64, copy=False)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def ensure_formal_h5ad(item: dict[str, object]) -> tuple[Path, str]:
    dataset_id = str(item["dataset_id"])
    formal_h5ad_path = resolve_path(str(item["formal_h5ad_path"]))
    source_formal_h5ad_path = item.get("source_formal_h5ad_path")
    input_path = item.get("input_path")
    formalization_mode = item.get("formalization_mode")

    if source_formal_h5ad_path:
        source_path = resolve_path(str(source_formal_h5ad_path))
        if not source_path.exists():
            raise FileNotFoundError(f"{dataset_id}: 缺少 source_formal_h5ad_path={source_path}")
        adata = ad.read_h5ad(source_path)
        adata.obs = adata.obs.copy()
        adata.obs["dataset_id"] = dataset_id
        ensure_parent(formal_h5ad_path)
        adata.write_h5ad(formal_h5ad_path)
        return formal_h5ad_path, "copied_from_source_formal_h5ad"

    if input_path and formalization_mode:
        raw_path = resolve_path(str(input_path))
        if not raw_path.exists():
            raise FileNotFoundError(f"{dataset_id}: 缺少 input_path={raw_path}")
        adata = ad.read_h5ad(raw_path)
        standardized_obs, _ = build_standard_obs(
            adata,
            {
                "dataset_id": dataset_id,
                "mode": formalization_mode,
                **{
                    key: value
                    for key, value in item.items()
                    if key not in {"formal_h5ad_path", "input_path", "source_formal_h5ad_path"}
                },
            },
        )
        keep_mask = standardized_obs["formal_like_keep"].astype(bool).to_numpy()
        filtered = adata[keep_mask].copy()
        filtered.obs = standardized_obs.loc[keep_mask].copy()
        filtered.obs["dataset_id"] = dataset_id
        ensure_parent(formal_h5ad_path)
        filtered.write_h5ad(formal_h5ad_path)
        return formal_h5ad_path, "materialized_from_raw_input"

    if not formal_h5ad_path.exists():
        raise FileNotFoundError(f"{dataset_id}: 缺少 formal_h5ad_path={formal_h5ad_path}")
    return formal_h5ad_path, "reused_existing_formal_h5ad"


def validate_formal_h5ad(path: Path, dataset_id: str) -> None:
    adata = ad.read_h5ad(path, backed="r")
    try:
        missing = sorted(set(REQUIRED_FORMAL_OBS_COLUMNS) - set(adata.obs.columns))
        if missing:
            raise ValueError(f"{dataset_id}: {path} 缺少 formal obs 列 {missing}")
    finally:
        if getattr(adata, "isbacked", False):
            adata.file.close()


def load_existing_registry(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=REGISTRY_COLUMNS)
    frame = pd.read_csv(path, sep="\t")
    missing = sorted(set(REGISTRY_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"{path} 缺少 registry 列: {missing}")
    return frame.loc[:, REGISTRY_COLUMNS].copy()


def ensure_existing_aligned_truth_file(registry_row: dict[str, object]) -> str:
    truth_path = resolve_path(str(registry_row["truth_path"]))
    if truth_path.exists():
        return "reused_existing_aligned_truth_file"
    source_truth_path = resolve_path(str(registry_row.get("source_truth_path", "")))
    if not source_truth_path.exists():
        raise FileNotFoundError(
            f"{registry_row['dataset_id']}: aligned truth 缺失，且 source_truth_path 不存在: {source_truth_path}"
        )
    ensure_parent(truth_path)
    frame = pd.read_csv(source_truth_path, sep="\t")
    frame.to_csv(truth_path, sep="\t", index=False, compression="gzip")
    return "rebuilt_aligned_truth_from_source_truth"


def load_eligibility(item: dict[str, object]) -> pd.DataFrame:
    dataset_id = str(item["dataset_id"])
    eligibility_path = resolve_path(str(item["eligibility_path"]))
    if not eligibility_path.exists():
        raise FileNotFoundError(f"{dataset_id}: 缺少 eligibility_path={eligibility_path}")
    frame = pd.read_csv(eligibility_path, sep="\t")
    required = {"dataset_id", "target_gene", "n_cells_perturbed", "n_cells_control", "eligible_for_pseudobulk"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{eligibility_path} 缺少列: {missing}")
    source_dataset_id = str(item.get("eligibility_dataset_id", dataset_id))
    frame = frame.loc[frame["dataset_id"].astype("string").eq(source_dataset_id)].copy()
    frame["eligible_for_pseudobulk"] = frame["eligible_for_pseudobulk"].astype("string").str.lower().eq("true")
    frame = frame.loc[frame["eligible_for_pseudobulk"]].copy()
    if frame.empty:
        raise ValueError(f"{dataset_id}: eligibility 为空。")
    frame["dataset_id"] = source_dataset_id
    frame["target_gene"] = stringify(frame["target_gene"])
    frame["n_cells_perturbed"] = pd.to_numeric(frame["n_cells_perturbed"], errors="raise").astype(int)
    frame["n_cells_control"] = pd.to_numeric(frame["n_cells_control"], errors="raise").astype(int)
    return frame.loc[:, ["dataset_id", "target_gene", "n_cells_perturbed", "n_cells_control", "eligible_for_pseudobulk"]]


def build_truth_assets(
    *,
    item: dict[str, object],
    formal_h5ad_path: Path,
    config: dict[str, object],
) -> tuple[dict[str, object], str]:
    dataset_id = str(item["dataset_id"])
    split_seed = int(load_split_governance()["default_split_seed_for_truth_freeze"])
    eligible = load_eligibility(item)
    source_dataset_id = str(item.get("eligibility_dataset_id", dataset_id))
    heldout = filter_eligible_to_heldout(eligible, source_dataset_id, split_seed)
    heldout_targets = heldout["target_gene"].astype(str).tolist()
    if not heldout_targets:
        raise ValueError(f"{dataset_id}: 未得到 held-out targets。")

    truth_output_root = resolve_path(str(config["truth_output_root"]))
    frozen_truth_root = resolve_path(str(config["frozen_truth_root"]))
    dataset_truth_dir = truth_output_root / dataset_id
    dataset_truth_dir.mkdir(parents=True, exist_ok=True)
    frozen_truth_root.mkdir(parents=True, exist_ok=True)

    adata = ad.read_h5ad(formal_h5ad_path)
    obs = adata.obs.copy()
    obs["dataset_id"] = dataset_id
    obs["is_control"] = obs["is_control"].astype(bool)
    obs["target_gene"] = stringify(obs["target_gene"])
    if not obs["dataset_id"].astype("string").eq(dataset_id).all():
        raise ValueError(f"{dataset_id}: formal-like h5ad 中存在非本数据集记录。")

    control_mask = obs["is_control"].to_numpy()
    if control_mask.sum() == 0:
        raise ValueError(f"{dataset_id}: formal-like h5ad 中不存在 control。")
    control_values = mean_expression(adata.X[control_mask])
    gene_symbols = adata.var_names.astype(str)

    control_frame = pd.DataFrame([control_values], index=["control"], columns=gene_symbols)
    control_frame.index.name = "target_gene"

    perturbed_rows: list[np.ndarray] = []
    delta_rows: list[np.ndarray] = []
    metadata_rows: list[dict[str, object]] = []
    for row in heldout.itertuples(index=False):
        target_mask = (~control_mask) & obs["target_gene"].eq(str(row.target_gene)).fillna(False).to_numpy(dtype=bool)
        perturbed_cells = int(target_mask.sum())
        if perturbed_cells == 0:
            raise ValueError(f"{dataset_id}: held-out target {row.target_gene} 没有细胞。")
        perturbed_values = mean_expression(adata.X[target_mask])
        delta_values = perturbed_values - control_values
        perturbed_rows.append(perturbed_values)
        delta_rows.append(delta_values)
        metadata_rows.append(
            {
                "dataset_id": dataset_id,
                "target_gene": str(row.target_gene),
                "n_cells_perturbed": perturbed_cells,
                "n_cells_control": int(control_mask.sum()),
                "eligible_for_pseudobulk": True,
            }
        )

    perturbed_frame = pd.DataFrame(perturbed_rows, index=heldout_targets, columns=gene_symbols)
    perturbed_frame.index.name = "target_gene"
    delta_frame = pd.DataFrame(delta_rows, index=heldout_targets, columns=gene_symbols)
    delta_frame.index.name = "target_gene"
    metadata_frame = pd.DataFrame(metadata_rows).sort_values("target_gene").reset_index(drop=True)

    control_path = dataset_truth_dir / "control_pseudobulk.tsv.gz"
    perturbed_path = dataset_truth_dir / "perturbed_pseudobulk.tsv.gz"
    delta_path = dataset_truth_dir / "pseudobulk_delta.tsv.gz"
    metadata_path = dataset_truth_dir / "target_metadata.tsv"
    aligned_path = frozen_truth_root / f"{dataset_id}_pseudobulk_delta_aligned.tsv.gz"

    control_frame.reset_index().to_csv(control_path, sep="\t", index=False, compression="gzip")
    perturbed_frame.reset_index().to_csv(perturbed_path, sep="\t", index=False, compression="gzip")
    delta_frame.reset_index().to_csv(delta_path, sep="\t", index=False, compression="gzip")
    metadata_frame.to_csv(metadata_path, sep="\t", index=False)
    delta_frame.reset_index().to_csv(aligned_path, sep="\t", index=False, compression="gzip")

    registry_row = {
        "dataset_id": dataset_id,
        "truth_path": str(aligned_path.relative_to(PROJECT_ROOT)),
        "n_targets_expected": len(heldout_targets),
        "n_targets_built": len(heldout_targets),
        "n_genes": len(gene_symbols),
        "control_definition": "in-dataset control baseline",
        "freeze_status": "frozen",
        "matrix_source": "X",
        "log_normalization_applied_in_truth_build": False,
        "delta_space": "X_pseudobulk_delta",
        "evaluation_space": "main_aligned",
        "source_truth_path": str(delta_path.relative_to(PROJECT_ROOT)),
    }
    return registry_row, "built_truth_and_aligned_registry_entry"


def build_comparators_for_dataset(
    *,
    dataset_id: str,
    truth_entry: dict[str, object],
    baseline_root: Path,
    null_root: Path,
) -> list[str]:
    truth = pd.read_csv(resolve_path(str(truth_entry["truth_path"])), sep="\t").set_index("target_gene")
    truth.index = truth.index.astype(str)
    truth.columns = truth.columns.astype(str)

    baseline_dir = baseline_root / dataset_id
    null_dir = null_root / dataset_id
    baseline_dir.mkdir(parents=True, exist_ok=True)
    null_dir.mkdir(parents=True, exist_ok=True)

    actions: list[str] = []
    output_mapping = {
        baseline_dir / "zero_shift_null.tsv.gz": build_zero_shift_null(truth),
        baseline_dir / "mean_shift_baseline.tsv.gz": build_mean_shift_baseline(truth),
        null_dir / "label_shuffle.tsv.gz": build_label_shuffle(
            truth,
            seed=dataset_seed(dataset_id, "label_shuffle"),
        ),
        null_dir / "random_pairing.tsv.gz": build_random_pairing(
            truth,
            seed=dataset_seed(dataset_id, "random_pairing"),
        ),
    }
    for path, frame in output_mapping.items():
        frame.reset_index().to_csv(path, sep="\t", index=False, compression="gzip")
        actions.append(f"wrote:{path.relative_to(PROJECT_ROOT)}")
    return actions


def build_report_row(
    *,
    dataset_id: str,
    formal_h5ad_path: Path,
    formal_h5ad_action: str,
    truth_action: str,
    comparator_actions: list[str],
    truth_registry_path: Path,
) -> dict[str, object]:
    return {
        "dataset_id": dataset_id,
        "formal_h5ad_path": str(formal_h5ad_path.relative_to(PROJECT_ROOT)),
        "formal_h5ad_action": formal_h5ad_action,
        "truth_action": truth_action,
        "n_comparator_files_written": len(comparator_actions),
        "truth_registry_path": str(truth_registry_path.relative_to(PROJECT_ROOT)),
    }


def main() -> None:
    args = build_parser().parse_args()
    config = load_json(resolve_path(args.config))
    report_root = DEFAULT_REPORT_ROOT
    report_root.mkdir(parents=True, exist_ok=True)

    registry_input_path = resolve_path(str(config["truth_registry_input_path"]))
    registry_output_path = resolve_path(str(config["truth_registry_output_path"]))
    baseline_root = resolve_path(str(config["baseline_root"]))
    null_root = resolve_path(str(config["null_root"]))
    selected_dataset_ids = {dataset_id for dataset_id in args.dataset_id if dataset_id}

    existing_registry = load_existing_registry(registry_input_path)
    merged_registry = existing_registry.copy()
    report_rows: list[dict[str, object]] = []

    for item in list(config.get("datasets", [])):
        dataset_id = str(item["dataset_id"])
        if selected_dataset_ids and dataset_id not in selected_dataset_ids:
            continue

        formal_h5ad_path, formal_h5ad_action = ensure_formal_h5ad(item)
        validate_formal_h5ad(formal_h5ad_path, dataset_id)

        truth_action = "reused_existing_truth_registry_entry"
        registry_row: dict[str, object] | None = None
        if bool(item.get("include_existing_truth_entry", False)):
            match = existing_registry.loc[existing_registry["dataset_id"].astype("string").eq(dataset_id)]
            if match.empty:
                raise ValueError(f"{dataset_id}: 在 {registry_input_path} 中找不到现有 truth entry。")
            registry_row = match.iloc[0].to_dict()
            truth_action = ensure_existing_aligned_truth_file(registry_row)
        elif bool(item.get("build_truth", False)):
            registry_row, truth_action = build_truth_assets(
                item=item,
                formal_h5ad_path=formal_h5ad_path,
                config=config,
            )
        else:
            raise ValueError(f"{dataset_id}: 既未声明 include_existing_truth_entry，也未声明 build_truth。")

        merged_registry = merged_registry.loc[~merged_registry["dataset_id"].astype("string").eq(dataset_id)].copy()
        merged_registry = pd.concat(
            [merged_registry, pd.DataFrame([registry_row], columns=REGISTRY_COLUMNS)],
            ignore_index=True,
        )
        merged_registry = merged_registry.loc[:, REGISTRY_COLUMNS].sort_values("dataset_id").reset_index(drop=True)

        comparator_actions: list[str] = []
        if bool(item.get("build_comparators", False)):
            comparator_actions = build_comparators_for_dataset(
                dataset_id=dataset_id,
                truth_entry=registry_row,
                baseline_root=baseline_root,
                null_root=null_root,
            )

        report_rows.append(
            build_report_row(
                dataset_id=dataset_id,
                formal_h5ad_path=formal_h5ad_path,
                formal_h5ad_action=formal_h5ad_action,
                truth_action=truth_action,
                comparator_actions=comparator_actions,
                truth_registry_path=registry_output_path,
            )
        )

    ensure_parent(registry_output_path)
    merged_registry.to_csv(registry_output_path, sep="\t", index=False)

    report_path = report_root / "all_datasets_readiness_fill_summary.tsv"
    pd.DataFrame(report_rows).sort_values("dataset_id").to_csv(report_path, sep="\t", index=False)

    print(f"已写出: {registry_output_path.relative_to(PROJECT_ROOT)}")
    print(f"已写出: {report_path.relative_to(PROJECT_ROOT)}")
    if report_rows:
        print(pd.DataFrame(report_rows).sort_values("dataset_id").to_string(index=False))


if __name__ == "__main__":
    main()
