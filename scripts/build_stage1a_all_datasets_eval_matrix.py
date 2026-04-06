from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import anndata as ad
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for candidate in (PROJECT_ROOT, SCRIPTS_DIR):
    text = str(candidate)
    if text not in sys.path:
        sys.path.insert(0, text)


DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/stage1a/runs/all_datasets_eval_matrix.json"
RAW_PREDICTION_ROOTS = {
    "gears": PROJECT_ROOT / "data/predictions/stage1a_gears_raw",
    "scgpt": PROJECT_ROOT / "data/predictions/stage1a_scgpt_raw",
    "geneformer": PROJECT_ROOT / "data/predictions/stage1a_geneformer_raw",
}
REQUIRED_FORMAL_OBS_COLUMNS = ("is_control", "target_gene")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="物化 Stage 1A 全数据集评测矩阵配置，并输出 readiness 审计。"
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="评测矩阵 JSON 配置路径。",
    )
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json_mapping(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload


def load_truth_registry_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    frame = pd.read_csv(path, sep="\t")
    if "dataset_id" not in frame.columns:
        raise ValueError(f"{path} 缺少 dataset_id 列。")
    return set(frame["dataset_id"].astype("string").tolist())


def h5ad_obs_audit(path: Path) -> tuple[bool, str, int | None, int | None]:
    if not path.exists():
        return False, "missing_h5ad", None, None
    adata = ad.read_h5ad(path, backed="r")
    try:
        missing = sorted(set(REQUIRED_FORMAL_OBS_COLUMNS) - set(adata.obs.columns))
        if missing:
            return False, f"missing_obs_columns:{','.join(missing)}", int(adata.n_obs), int(adata.n_vars)
        return True, "ok", int(adata.n_obs), int(adata.n_vars)
    finally:
        if getattr(adata, "isbacked", False):
            adata.file.close()


def dataset_readiness_row(
    dataset: dict[str, object],
    *,
    truth_registry_path: Path,
    truth_registry_ids: set[str],
    baseline_root: Path,
    null_root: Path,
) -> dict[str, object]:
    dataset_id = str(dataset["dataset_id"])
    tier = str(dataset.get("tier", dataset.get("benchmark_tier", "")))
    formal_h5ad_path = resolve_path(str(dataset["formal_h5ad_path"]))
    formal_h5ad_ready, obs_status, n_obs, n_vars = h5ad_obs_audit(formal_h5ad_path)
    truth_ready = dataset_id in truth_registry_ids
    mean_shift_ready = (baseline_root / dataset_id / "mean_shift_baseline.tsv.gz").exists()
    zero_shift_ready = (baseline_root / dataset_id / "zero_shift_null.tsv.gz").exists()
    label_shuffle_ready = (null_root / dataset_id / "label_shuffle.tsv.gz").exists()
    random_pairing_ready = (null_root / dataset_id / "random_pairing.tsv.gz").exists()
    scoring_ready = all(
        [
            truth_ready,
            mean_shift_ready,
            zero_shift_ready,
            label_shuffle_ready,
            random_pairing_ready,
        ]
    )
    end_to_end_ready = formal_h5ad_ready and scoring_ready
    if end_to_end_ready:
        note = "ready"
    elif not formal_h5ad_ready:
        note = obs_status
    elif not truth_ready:
        note = "missing_truth_registry_entry"
    else:
        missing = []
        if not mean_shift_ready:
            missing.append("mean_shift_baseline")
        if not zero_shift_ready:
            missing.append("zero_shift_null")
        if not label_shuffle_ready:
            missing.append("label_shuffle")
        if not random_pairing_ready:
            missing.append("random_pairing")
        note = "missing_comparators:" + ",".join(missing)
    return {
        "dataset_id": dataset_id,
        "tier": tier,
        "usage": str(dataset.get("usage", "runnable")),
        "review_status": str(dataset.get("review_status", "")),
        "source_kind": str(dataset.get("source_kind", "")),
        "formal_h5ad_path": str(formal_h5ad_path.relative_to(PROJECT_ROOT)),
        "formal_h5ad_ready": formal_h5ad_ready,
        "formal_obs_status": obs_status,
        "truth_registry_path": str(truth_registry_path.relative_to(PROJECT_ROOT)),
        "truth_entry_ready": truth_ready,
        "mean_shift_baseline_ready": mean_shift_ready,
        "zero_shift_null_ready": zero_shift_ready,
        "label_shuffle_ready": label_shuffle_ready,
        "random_pairing_ready": random_pairing_ready,
        "ready_for_adapter": formal_h5ad_ready,
        "ready_for_scoring": scoring_ready,
        "ready_end_to_end": end_to_end_ready,
        "n_obs": n_obs if n_obs is not None else "",
        "n_vars": n_vars if n_vars is not None else "",
        "readiness_note": note,
    }


def build_run_config_payload(
    *,
    model: dict[str, object],
    dataset: dict[str, object],
    truth_registry_path: Path,
    baseline_root: Path,
    null_root: Path,
) -> dict[str, object]:
    dataset_id = str(dataset["dataset_id"])
    adapter = str(model["adapter"])
    model_id = str(model["model_id"])
    raw_prediction_root = RAW_PREDICTION_ROOTS[adapter]
    payload: dict[str, object] = {
        "dataset_id": dataset_id,
        "model_id": model_id,
        "formal_h5ad_path": str(dataset["formal_h5ad_path"]),
        "prediction_path": str(
            (raw_prediction_root / model_id / dataset_id / "predicted_shift.tsv.gz").relative_to(PROJECT_ROOT)
        ),
        "prediction_space": "X_pseudobulk_delta",
        "output_path": f"data/predictions/stage1a_main_aligned/{model_id}/{dataset_id}/predicted_shift_aligned.tsv.gz",
        "summary_path": f"reports/stage1a/prediction_alignment/{model_id}/{dataset_id}/alignment_summary.json",
        "manifest_path": f"reports/stage1a/prediction_alignment/{model_id}/{dataset_id}/alignment_manifest.json",
        "allow_missing_targets": True,
        "allow_missing_genes": True,
        "truth_registry_path": str(truth_registry_path.relative_to(PROJECT_ROOT)),
        "baseline_root": str(baseline_root.relative_to(PROJECT_ROOT)),
        "null_root": str(null_root.relative_to(PROJECT_ROOT)),
    }
    if dataset.get("cell_line"):
        payload["cell_line"] = str(dataset["cell_line"])
    for key, value in dict(model.get("config_overrides", {})).items():
        payload[key] = value
    return payload


def main() -> None:
    args = build_parser().parse_args()
    config_path = resolve_path(args.config)
    config = load_json_mapping(config_path)

    matrix_id = str(config["matrix_id"])
    materialized_root = resolve_path(str(config.get("materialized_root", "artifacts/stage1a_eval_matrix")))
    report_root = resolve_path(str(config.get("report_root", "reports/stage1a/eval_matrix")))
    truth_registry_path = resolve_path(str(config["truth_registry_path"]))
    baseline_root = resolve_path(str(config["baseline_root"]))
    null_root = resolve_path(str(config["null_root"]))
    models = list(config.get("models", []))
    datasets = list(config.get("datasets", []))
    topk = [int(v) for v in list(config.get("topk", [50]))]
    if not models or not datasets:
        raise ValueError("matrix config 必须包含非空 models / datasets。")

    matrix_root = materialized_root / matrix_id
    run_config_root = matrix_root / "run_configs"
    batch_root = matrix_root / "batches"
    matrix_report_root = report_root / matrix_id
    run_config_root.mkdir(parents=True, exist_ok=True)
    batch_root.mkdir(parents=True, exist_ok=True)
    matrix_report_root.mkdir(parents=True, exist_ok=True)

    truth_registry_ids = load_truth_registry_ids(truth_registry_path)
    readiness_rows = [
        dataset_readiness_row(
            dataset,
            truth_registry_path=truth_registry_path,
            truth_registry_ids=truth_registry_ids,
            baseline_root=baseline_root,
            null_root=null_root,
        )
        for dataset in datasets
    ]
    readiness_frame = pd.DataFrame(readiness_rows).sort_values(["tier", "dataset_id"]).reset_index(drop=True)
    readiness_index = {
        str(row["dataset_id"]): bool(row["ready_end_to_end"])
        for row in readiness_frame.to_dict(orient="records")
    }
    readiness_path = matrix_report_root / "dataset_readiness.tsv"
    readiness_frame.to_csv(readiness_path, sep="\t", index=False)

    model_matrix_rows: list[dict[str, object]] = []
    all_run_configs: list[str] = []
    ready_run_configs: list[str] = []
    adapter_to_all: dict[str, list[str]] = {}
    adapter_to_ready: dict[str, list[str]] = {}

    for model in models:
        adapter = str(model["adapter"])
        model_id = str(model["model_id"])
        adapter_to_all.setdefault(adapter, [])
        adapter_to_ready.setdefault(adapter, [])
        for dataset in datasets:
            dataset_id = str(dataset["dataset_id"])
            payload = build_run_config_payload(
                model=model,
                dataset=dataset,
                truth_registry_path=truth_registry_path,
                baseline_root=baseline_root,
                null_root=null_root,
            )
            run_config_path = run_config_root / model_id / f"{dataset_id}.yaml"
            run_config_path.parent.mkdir(parents=True, exist_ok=True)
            run_config_path.write_text(
                yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            rel_run_config_path = str(run_config_path.relative_to(PROJECT_ROOT))
            all_run_configs.append(rel_run_config_path)
            adapter_to_all[adapter].append(rel_run_config_path)
            if readiness_index[dataset_id]:
                ready_run_configs.append(rel_run_config_path)
                adapter_to_ready[adapter].append(rel_run_config_path)
            model_matrix_rows.append(
                {
                    "dataset_id": dataset_id,
                    "tier": str(dataset.get("tier", dataset.get("benchmark_tier", ""))),
                    "usage": str(dataset.get("usage", "runnable")),
                    "review_status": str(dataset.get("review_status", "")),
                    "source_kind": str(dataset.get("source_kind", "")),
                    "adapter": adapter,
                    "environment": str(model["environment"]),
                    "model_id": model_id,
                    "run_config_path": rel_run_config_path,
                    "ready_end_to_end": readiness_index[dataset_id],
                }
            )

    for adapter, paths in adapter_to_all.items():
        (batch_root / f"{adapter}.all.yaml").write_text(
            yaml.safe_dump({"run_configs": paths}, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        (batch_root / f"{adapter}.ready.yaml").write_text(
            yaml.safe_dump({"run_configs": adapter_to_ready[adapter]}, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    (batch_root / "scoring.all.yaml").write_text(
        yaml.safe_dump({"run_configs": all_run_configs}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (batch_root / "scoring.ready.yaml").write_text(
        yaml.safe_dump({"run_configs": ready_run_configs}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    model_matrix_path = matrix_report_root / "model_dataset_matrix.tsv"
    pd.DataFrame(model_matrix_rows).sort_values(
        ["adapter", "dataset_id"]
    ).to_csv(model_matrix_path, sep="\t", index=False)

    manifest_path = matrix_root / "manifest.json"
    manifest = {
        "matrix_id": matrix_id,
        "config_path": str(config_path.relative_to(PROJECT_ROOT)),
        "truth_registry_path": str(truth_registry_path.relative_to(PROJECT_ROOT)),
        "baseline_root": str(baseline_root.relative_to(PROJECT_ROOT)),
        "null_root": str(null_root.relative_to(PROJECT_ROOT)),
        "topk": topk,
        "run_config_root": str(run_config_root.relative_to(PROJECT_ROOT)),
        "batch_root": str(batch_root.relative_to(PROJECT_ROOT)),
        "report_root": str(matrix_report_root.relative_to(PROJECT_ROOT)),
        "n_models": len(models),
        "n_datasets": len(datasets),
        "n_run_configs_all": len(all_run_configs),
        "n_run_configs_ready": len(ready_run_configs),
        "models": models,
        "datasets": datasets,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"已写出: {readiness_path.relative_to(PROJECT_ROOT)}")
    print(f"已写出: {model_matrix_path.relative_to(PROJECT_ROOT)}")
    print(f"已写出: {manifest_path.relative_to(PROJECT_ROOT)}")
    print(f"ready_run_configs={len(ready_run_configs)}/{len(all_run_configs)}")


if __name__ == "__main__":
    main()
