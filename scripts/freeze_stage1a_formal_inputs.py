from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from stage1a_catalog import PROJECT_ROOT, load_formal_dataset_contracts

FROZEN_DIR = PROJECT_ROOT / "data/frozen/stage1a_formal"
FREEZE_REPORT_DIR = PROJECT_ROOT / "reports/stage1a/freeze"
DEFAULT_COMBINED_ELIGIBILITY_PATH = (
    PROJECT_ROOT / "reports/stage1a/pseudobulk_eligibility/combined_eligibility.tsv"
)
FREEZE_METADATA_PATH = FREEZE_REPORT_DIR / "freeze_manifest.metadata.json"
FREEZE_README_PATH = FREEZE_REPORT_DIR / "README.md"
ELIGIBILITY_COLUMNS = [
    "dataset_id",
    "target_gene",
    "n_cells_perturbed",
    "n_cells_control",
    "eligible_for_pseudobulk",
    "eligible_reason",
]


def find_combined_eligibility_path() -> Path:
    matches = sorted(PROJECT_ROOT.rglob("combined_eligibility.tsv"))
    if not matches:
        raise FileNotFoundError("未找到 combined_eligibility.tsv。")
    if DEFAULT_COMBINED_ELIGIBILITY_PATH in matches:
        return DEFAULT_COMBINED_ELIGIBILITY_PATH
    if len(matches) > 1:
        raise RuntimeError(
            "发现多个 combined_eligibility.tsv，无法唯一确定输入："
            + ", ".join(str(path.relative_to(PROJECT_ROOT)) for path in matches)
        )
    return matches[0]


def load_current_formal_pass_dataset_ids() -> set[str]:
    """只消费当前 catalog 中的 official formal pass datasets。

    不再依赖磁盘上的 admission manifest，避免被过期快照污染 formal freeze gating。
    """
    return {
        contract.dataset_id
        for contract in load_formal_dataset_contracts(include_auxiliary=False)
        if contract.default_in_mainline and contract.status == "pass"
    }


def build_frozen_registry(allowed_dataset_ids: set[str]) -> pd.DataFrame:
    rows = [
        {
            "dataset_id": contract.dataset_id,
            "cell_line": contract.cell_line,
            "control_definition": contract.control_definition,
            "perturbation_unit": contract.perturbation_unit,
            "n_cells_raw": contract.n_cells_raw,
            "n_cells_formal": contract.n_cells_formal,
            "n_controls": contract.n_controls,
            "n_perturbed": contract.n_perturbed,
            "n_unique_targets": contract.n_unique_targets,
            "stage": contract.stage,
            "role": contract.role,
            "default_in_mainline": contract.default_in_mainline,
            "status": contract.status,
            "output_path": str(contract.output_path),
            "notes": contract.notes,
        }
        for contract in load_formal_dataset_contracts(include_auxiliary=True)
        if contract.status in {"pass"} and contract.dataset_id in allowed_dataset_ids
    ]
    return pd.DataFrame(rows).sort_values("dataset_id").reset_index(drop=True)


def load_and_filter_eligible_targets(
    combined_eligibility_path: Path, allowed_dataset_ids: set[str]
) -> pd.DataFrame:
    eligibility = pd.read_csv(combined_eligibility_path, sep="\t")
    missing = [column for column in ELIGIBILITY_COLUMNS if column not in eligibility.columns]
    if missing:
        raise ValueError(f"combined_eligibility.tsv 缺少字段: {missing}")

    eligible = eligibility.loc[:, ELIGIBILITY_COLUMNS].copy()
    eligible["eligible_for_pseudobulk"] = eligible["eligible_for_pseudobulk"].astype(str).str.lower().eq("true")
    eligible = eligible[
        eligible["dataset_id"].isin(allowed_dataset_ids)
        & eligible["eligible_for_pseudobulk"]
    ].copy()
    return eligible.sort_values(
        ["dataset_id", "n_cells_perturbed", "target_gene"],
        ascending=[True, False, True],
    ).reset_index(drop=True)


def build_freeze_manifest(
    frozen_registry: pd.DataFrame,
    eligible_targets: pd.DataFrame,
) -> dict[str, object]:
    manifest_datasets: list[dict[str, object]] = []

    eligible_counts = (
        eligible_targets.groupby("dataset_id").size().rename("n_targets_eligible")
        if not eligible_targets.empty
        else pd.Series(dtype="int64", name="n_targets_eligible")
    )

    for row in frozen_registry.itertuples(index=False):
        n_targets_eligible = int(eligible_counts.get(row.dataset_id, 0))
        manifest_datasets.append(
            {
                "dataset_id": row.dataset_id,
                "output_path": row.output_path,
                "n_targets_total": int(row.n_unique_targets),
                "n_targets_eligible": n_targets_eligible,
                "role": row.role,
                "default_in_mainline": bool(row.default_in_mainline),
                "control_definition": row.control_definition,
                "perturbation_unit": row.perturbation_unit,
                "freeze_status": "frozen",
            }
        )

    return {
        "stage": "stage1a_formal",
        "freeze_status": "frozen",
        "snapshot_status": "historical_snapshot_pending_migration",
        "status_note": (
            "该 freeze manifest 由 legacy formal freeze 链路生成，但 gating 已直接消费当前 catalog 中的 official formal pass datasets。"
        ),
        "migration_policy": "pending_migration_to_current_dataset_naming",
        "authoritative_current_sources": [
            "configs/stage1a_formal_datasets.yaml",
            "dataset_tiering.md",
            "admission_matrix.tsv",
            "configs/stage1a/dataset_governance.json",
        ],
        "datasets": manifest_datasets,
    }


def main() -> None:
    FROZEN_DIR.mkdir(parents=True, exist_ok=True)
    FREEZE_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    allowed_dataset_ids = load_current_formal_pass_dataset_ids()
    frozen_registry = build_frozen_registry(allowed_dataset_ids)
    combined_eligibility_path = find_combined_eligibility_path()
    eligible_targets = load_and_filter_eligible_targets(
        combined_eligibility_path=combined_eligibility_path,
        allowed_dataset_ids=allowed_dataset_ids,
    )

    eligible_targets_path = FROZEN_DIR / "eligible_targets.tsv"
    frozen_registry_path = FROZEN_DIR / "formal_dataset_registry_frozen.tsv"
    freeze_manifest_path = FREEZE_REPORT_DIR / "freeze_manifest.json"

    eligible_targets.to_csv(eligible_targets_path, sep="\t", index=False)
    frozen_registry.to_csv(frozen_registry_path, sep="\t", index=False)

    freeze_manifest = build_freeze_manifest(
        frozen_registry=frozen_registry,
        eligible_targets=eligible_targets,
    )
    freeze_manifest_path.write_text(
        json.dumps(freeze_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    freeze_metadata = {
        "manifest_id": "freeze_manifest",
        "snapshot_status": "historical_snapshot_pending_migration",
        "status_note": (
            "该 freeze manifest 属于 legacy formal freeze 报告产物；当前 gating 直接消费 configs/stage1a_formal_datasets.yaml 中的 official formal pass datasets。"
        ),
        "migration_policy": "pending_migration_to_current_dataset_naming",
        "authoritative_current_sources": [
            "configs/stage1a_formal_datasets.yaml",
            "dataset_tiering.md",
            "admission_matrix.tsv",
            "configs/stage1a/dataset_governance.json",
        ],
    }
    FREEZE_METADATA_PATH.write_text(json.dumps(freeze_metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    FREEZE_README_PATH.write_text(
        "\n".join(
            [
                "# freeze 目录说明",
                "",
                "- `freeze_manifest.json` 属于 legacy formal freeze 报告产物。",
                "- formal freeze gating 当前直接消费 `configs/stage1a_formal_datasets.yaml` 中的 official formal pass datasets，不再依赖磁盘上的 admission manifest。",
                "- 该目录不负责表达当前 `formal + supplement` 全量治理口径。",
                "- 当前数据集命名与分层应以 `dataset_tiering.md`、`admission_matrix.tsv`、`configs/stage1a/dataset_governance.json` 为准。",
                "- 后续若继续使用该 freeze 目录，应迁移到新命名体系，而不是继续与现行口径混用。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"combined_eligibility 输入: {combined_eligibility_path}")
    print(f"已写出: {eligible_targets_path}")
    print(f"已写出: {frozen_registry_path}")
    print(f"已写出: {freeze_manifest_path}")
    print(f"已写出: {FREEZE_METADATA_PATH}")
    print(f"已写出: {FREEZE_README_PATH}")


if __name__ == "__main__":
    main()
