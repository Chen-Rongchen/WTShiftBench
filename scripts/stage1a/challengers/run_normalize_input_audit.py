from __future__ import annotations

import argparse
import json
from pathlib import Path

import anndata as ad
import pandas as pd

from scripts.stage1a.adapters.common.runtime import audit_input_matrix_semantics, resolve_path
from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT, get_formal_dataset_contract


DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/stage1a/challengers/normalize_input_audit.json"
AUDIT_REPORT_ROOT = PROJECT_ROOT / "reports/stage1a/normalize_audit"
AUDIT_PREDICTION_ROOT = PROJECT_ROOT / "data/predictions/stage1a_normalize_audit_raw"
AUDIT_ALIGNED_ROOT = PROJECT_ROOT / "data/predictions/stage1a_normalize_audit_aligned"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 Stage 1A 输入侧 normalize 小范围审计。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--dataset-id", action="append", dest="dataset_ids")
    parser.add_argument("--model-family", action="append", dest="model_families")
    parser.add_argument("--input-preproc", action="append", dest="input_preprocs")
    return parser


def load_json_mapping(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(payload: dict[str, object], path: Path) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_model_id(model_id_base: str, input_preproc: str) -> str:
    suffix = "audit_raw" if input_preproc == "raw" else "audit_normlog1p"
    return f"{model_id_base}__{suffix}"


def load_dataset_input_audit(dataset_id: str) -> dict[str, object]:
    contract = get_formal_dataset_contract(dataset_id)
    adata = ad.read_h5ad(contract.path)
    try:
        audit = audit_input_matrix_semantics(adata)
    finally:
        del adata
    audit["dataset_id"] = dataset_id
    audit["formal_h5ad_path"] = str(contract.path.relative_to(PROJECT_ROOT))
    return audit


def summarize_results(rows: list[dict[str, object]], summary_path: Path) -> None:
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame = frame.sort_values(["dataset_id", "model_family", "input_preproc"]).reset_index(drop=True)
    ensure_parent(summary_path)
    frame.to_csv(summary_path, sep="\t", index=False)


def build_summary_markdown(rows: list[dict[str, object]], output_path: Path) -> None:
    frame = pd.DataFrame(rows)
    lines = ["# Stage 1A 输入 normalize 审计结论", ""]
    if frame.empty:
        lines.append("本轮没有可写入的结果。")
    else:
        lines.append("## 1. normalize 是否伤害了当前最强 challenger？")
        lines.append("- 无法做合法比较。`lm_train_lowrank` 没有独立的单细胞输入特征层；若在其 train delta 构造处加入 `normalize+log1p`，会把监督目标从 A-space 改成变换空间下的 delta。")
        lines.append("")

        lines.append("## 2. normalize 是否让 pretrained ridge 路线更稳定？")
        lines.append("- 无法做合法比较。`lm_G_scgpt_ridge` 与 `lm_G_geneformer_ridge` 当前只使用冻结 target embedding + A-space train pseudobulk delta；它们没有可单独插入的单细胞输入编码层。")
        lines.append("")

        lines.append("## 3. normalize 的收益是普遍的，还是数据集特异的？")
        lines.append("- 当前三条目标方法都不具备合法的输入侧 normalize 审计自由度，因此不存在可判读的跨数据集收益模式。")
        lines.append("")

        lines.append("## 4. normalize 是否提升了相对 mean baseline 的竞争力？")
        lines.append("- 无法判断。任何在当前三条方法里直接引入 `normalize+log1p` 的实现，都会把模型输出语义从 benchmark A-space 漂移到变换空间。")
        lines.append("")

        lines.append("## 5. 现阶段是否建议把 normalize 提升为 adapter 默认选项候选？")
        lines.append("- `not recommended now`")
        lines.append("")
        lines.append("补充说明：")
        lines.append("- 本轮先前产生过一组越界的 K562 exploratory 结果，但该实现已经被判定无效，不应继续引用。")
        lines.append("- 当前更合适的后续方向是：只在真正存在单细胞输入编码层的模型家族上重开同类审计。")

    ensure_parent(output_path)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    config = load_json_mapping(resolve_path(args.config))

    selected_datasets = set(args.dataset_ids or [])
    selected_models = set(args.model_families or [])
    selected_preprocs = set(args.input_preprocs or [])

    datasets = [str(item) for item in config["datasets"] if not selected_datasets or str(item) in selected_datasets]
    models = [
        item
        for item in config["models"]
        if not selected_models or str(item["model_family"]) in selected_models
    ]
    input_preprocs = [
        str(item)
        for item in config["input_preprocs"]
        if not selected_preprocs or str(item) in selected_preprocs
    ]
    split_seed = int(config["split_seed"])

    AUDIT_REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    dataset_audit_map = {dataset_id: load_dataset_input_audit(dataset_id) for dataset_id in datasets}
    write_json({"split_seed": split_seed, "datasets": list(dataset_audit_map.values())}, AUDIT_REPORT_ROOT / "input_matrix_audit.json")

    results: list[dict[str, object]] = []

    model_notes = {
        "lm_train_lowrank": "没有独立的单细胞输入特征层；若在 train delta 构造处加入 normalize+log1p，会改变监督目标语义，越出 A-space。",
        "lm_G_scgpt_ridge": "仅使用冻结 scGPT target embedding + A-space train pseudobulk delta；不存在可单独修改且不改变监督目标的输入编码层。",
        "lm_G_geneformer_ridge": "仅使用冻结 Geneformer target embedding + A-space train pseudobulk delta；不存在可单独修改且不改变监督目标的输入编码层。",
    }

    for model_cfg in models:
        model_family = str(model_cfg["model_family"])
        model_id_base = str(model_cfg["model_id_base"])
        note = model_notes.get(model_family, "当前方法缺少合法的输入侧 normalize 审计自由度。")
        for input_preproc in input_preprocs:
            model_id = build_model_id(model_id_base, input_preproc)
            for dataset_id in datasets:
                input_audit = dataset_audit_map[dataset_id]
                results.append(
                    {
                        "dataset_id": dataset_id,
                        "split_seed": split_seed,
                        "model_family": model_family,
                        "model_id": model_id,
                        "input_preproc": input_preproc,
                        "run_status": "not_applicable",
                        "unavailable_reason": note,
                        "input_matrix_source": input_audit["input_matrix_source"],
                        "raw_counts_available": bool(input_audit["raw_counts_available"]),
                        "prediction_export_ok": False,
                        "evaluation_ok": False,
                        "primary_metric_1": None,
                        "primary_metric_2": None,
                        "delta_vs_mean_baseline_metric_1": None,
                        "delta_vs_mean_baseline_metric_2": None,
                        "notes": "formal truth / scoring 保持不变；本轮不执行模型运行。",
                    }
                )

    summary_path = AUDIT_REPORT_ROOT / "normalize_audit_summary.tsv"
    summarize_results(results, summary_path)
    build_summary_markdown(results, AUDIT_REPORT_ROOT / "SUMMARY.md")


if __name__ == "__main__":
    main()
