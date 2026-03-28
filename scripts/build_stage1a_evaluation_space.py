from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from stage1a_catalog import (
    LEGACY_TRUTH_REGISTRY_PATH,
    PROJECT_ROOT,
    load_stage1a_truth_registry,
)

FROZEN_TRUTH_DIR = PROJECT_ROOT / "data/frozen/stage1a_truth"
EVALUATION_SPACE_REPORT_DIR = PROJECT_ROOT / "reports/stage1a/evaluation_space"
ALIGNED_TRUTH_REGISTRY_PATH = FROZEN_TRUTH_DIR / "aligned_truth_registry.tsv"
FULLSPACE_TRUTH_REGISTRY_PATH = FROZEN_TRUTH_DIR / "fullspace_truth_registry.tsv"
ALIGNMENT_SUMMARY_PATH = EVALUATION_SPACE_REPORT_DIR / "alignment_summary.tsv"
ALIGNMENT_MANIFEST_PATH = EVALUATION_SPACE_REPORT_DIR / "alignment_manifest.json"
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
MIN_EVALUABLE_GENES_PER_TRUTH = 1


def resolve_project_relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def load_legacy_truth_registry_frame() -> pd.DataFrame:
    rows = []
    for entry in load_stage1a_truth_registry(LEGACY_TRUTH_REGISTRY_PATH):
        rows.append(
            {
                "dataset_id": entry.dataset_id,
                "truth_path": resolve_project_relative(entry.path),
                "n_targets_expected": entry.n_targets_expected,
                "n_targets_built": entry.n_targets_built,
                "n_genes": entry.n_genes,
                "control_definition": entry.control_definition,
                "freeze_status": entry.freeze_status,
                "matrix_source": entry.matrix_source,
                "log_normalization_applied_in_truth_build": entry.log_normalization_applied_in_truth_build,
                "delta_space": entry.delta_space,
            }
        )
    if not rows:
        return pd.DataFrame(
            columns=[
                "dataset_id",
                "truth_path",
                "n_targets_expected",
                "n_targets_built",
                "n_genes",
                "control_definition",
                "freeze_status",
            ]
        )
    return pd.DataFrame(rows).sort_values("dataset_id").reset_index(drop=True)


def read_truth_columns(truth_path: Path) -> list[str]:
    frame = pd.read_csv(truth_path, sep="\t", nrows=0)
    columns = [str(column) for column in frame.columns]
    if not columns or columns[0] != "target_gene":
        raise ValueError(f"{truth_path} 首列不是 target_gene。")
    return columns


def build_aligned_truths(
    registry: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build aligned truths using each dataset's full gene space (per Blueprint 4.3.4).

    Each dataset's aligned truth uses the dataset's own full gene space,
    not the cross-dataset common intersection.
    """
    aligned_registry_rows: list[dict[str, object]] = []
    fullspace_registry_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for row in registry.itertuples(index=False):
        full_truth_path = PROJECT_ROOT / row.truth_path
        aligned_truth_path = FROZEN_TRUTH_DIR / f"{row.dataset_id}_pseudobulk_delta_aligned.tsv.gz"

        full_truth = pd.read_csv(full_truth_path, sep="\t")
        # Use each dataset's own full gene space (Blueprint 4.3.4: dataset-local)
        # aligned_truth = full truth (no filtering by common intersection)
        aligned_truth = full_truth.copy()
        n_evaluable_genes = len(full_truth.columns) - 1  # exclude target_gene column
        if n_evaluable_genes < MIN_EVALUABLE_GENES_PER_TRUTH:
            raise ValueError(
                f"{row.dataset_id} 的 evaluable genes 数量过少: {n_evaluable_genes}"
            )
        aligned_truth.to_csv(aligned_truth_path, sep="\t", compression="gzip", index=False)

        aligned_registry_rows.append(
            {
                "dataset_id": row.dataset_id,
                "truth_path": resolve_project_relative(aligned_truth_path),
                "n_targets_expected": int(row.n_targets_expected),
                "n_targets_built": int(row.n_targets_built),
                "n_genes": n_evaluable_genes,
                "control_definition": row.control_definition,
                "freeze_status": "frozen",
                "matrix_source": row.matrix_source,
                "log_normalization_applied_in_truth_build": row.log_normalization_applied_in_truth_build,
                "delta_space": row.delta_space,
                "evaluation_space": "main_aligned",
                "source_truth_path": row.truth_path,
            }
        )
        fullspace_registry_rows.append(
            {
                "dataset_id": row.dataset_id,
                "truth_path": row.truth_path,
                "n_targets_expected": int(row.n_targets_expected),
                "n_targets_built": int(row.n_targets_built),
                "n_genes": int(row.n_genes),
                "control_definition": row.control_definition,
                "freeze_status": "frozen",
                "matrix_source": row.matrix_source,
                "log_normalization_applied_in_truth_build": row.log_normalization_applied_in_truth_build,
                "delta_space": row.delta_space,
                "evaluation_space": "supplementary_fullspace",
                "source_truth_path": row.truth_path,
            }
        )
        summary_rows.append(
            {
                "dataset_id": row.dataset_id,
                "fullspace_truth_path": row.truth_path,
                "aligned_truth_path": resolve_project_relative(aligned_truth_path),
                "n_targets_expected": int(row.n_targets_expected),
                "n_targets_built": int(row.n_targets_built),
                "n_genes_fullspace": int(row.n_genes),
                "n_genes_aligned": int(row.n_genes),  # aligned now uses full gene space
                "n_genes_dropped": 0,  # no genes dropped - aligned = fullspace
                "control_definition": row.control_definition,
                "freeze_status": "frozen",
                "matrix_source": row.matrix_source,
                "log_normalization_applied_in_truth_build": row.log_normalization_applied_in_truth_build,
                "delta_space": row.delta_space,
            }
        )

    aligned_registry = pd.DataFrame(aligned_registry_rows, columns=REGISTRY_COLUMNS)
    fullspace_registry = pd.DataFrame(fullspace_registry_rows, columns=REGISTRY_COLUMNS)
    alignment_summary = pd.DataFrame(summary_rows).sort_values("dataset_id").reset_index(drop=True)
    return aligned_registry, fullspace_registry, alignment_summary


def build_alignment_manifest(
    aligned_registry: pd.DataFrame,
    fullspace_registry: pd.DataFrame,
) -> dict[str, object]:
    return {
        "stage": "stage1a_truth",
        "freeze_status": "frozen",
        "main_evaluation_space": "main_aligned",
        "supplementary_evaluation_space": "supplementary_fullspace",
        "source_inputs": {
            "legacy_truth_registry_tsv": resolve_project_relative(LEGACY_TRUTH_REGISTRY_PATH),
            "truth_root": "data/truth/stage1a_pseudobulk_delta",
        },
        "truth_build_normalization": {
            "matrix_source": "frozen_per_dataset_in_registry",
            "log_normalization_applied_in_truth_build": False,
            "delta_space": "frozen_per_dataset_in_registry",
        },
        "outputs": {
            "aligned_truth_registry_tsv": resolve_project_relative(ALIGNED_TRUTH_REGISTRY_PATH),
            "fullspace_truth_registry_tsv": resolve_project_relative(FULLSPACE_TRUTH_REGISTRY_PATH),
            "alignment_summary_tsv": resolve_project_relative(ALIGNMENT_SUMMARY_PATH),
        },
        "n_datasets_aligned": int(len(aligned_registry)),
        "n_datasets_fullspace": int(len(fullspace_registry)),
        "main_datasets": aligned_registry.to_dict(orient="records"),
        "supplementary_datasets": fullspace_registry.to_dict(orient="records"),
    }


def main() -> None:
    FROZEN_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    EVALUATION_SPACE_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    legacy_registry = load_legacy_truth_registry_frame()
    if legacy_registry.empty:
        raise ValueError("legacy truth registry 为空，无法构建 stage1a evaluation space。")

    aligned_registry, fullspace_registry, alignment_summary = build_aligned_truths(
        registry=legacy_registry,
    )
    aligned_registry.to_csv(ALIGNED_TRUTH_REGISTRY_PATH, sep="\t", index=False)
    fullspace_registry.to_csv(FULLSPACE_TRUTH_REGISTRY_PATH, sep="\t", index=False)
    alignment_summary.to_csv(ALIGNMENT_SUMMARY_PATH, sep="\t", index=False)

    alignment_manifest = build_alignment_manifest(
        aligned_registry=aligned_registry,
        fullspace_registry=fullspace_registry,
    )
    ALIGNMENT_MANIFEST_PATH.write_text(
        json.dumps(alignment_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"已写出: {ALIGNED_TRUTH_REGISTRY_PATH}")
    print(f"已写出: {FULLSPACE_TRUTH_REGISTRY_PATH}")
    print(f"已写出: {ALIGNMENT_SUMMARY_PATH}")
    print(f"已写出: {ALIGNMENT_MANIFEST_PATH}")


if __name__ == "__main__":
    main()
