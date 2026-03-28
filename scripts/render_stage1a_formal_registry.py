from __future__ import annotations

import csv

from stage1a_catalog import FORMAL_CONTRACT_TSV_PATH, load_formal_dataset_contracts


FIELDNAMES = [
    "dataset_id",
    "cell_line",
    "control_definition",
    "perturbation_unit",
    "n_cells_raw",
    "n_cells_formal",
    "n_controls",
    "n_perturbed",
    "n_unique_targets",
    "stage",
    "status",
    "output_path",
    "notes",
]


def main() -> None:
    datasets = load_formal_dataset_contracts()
    FORMAL_CONTRACT_TSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    with FORMAL_CONTRACT_TSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, delimiter="\t")
        writer.writeheader()
        for dataset in datasets:
            writer.writerow(
                {
                    "dataset_id": dataset.dataset_id,
                    "cell_line": dataset.cell_line,
                    "control_definition": dataset.control_definition,
                    "perturbation_unit": dataset.perturbation_unit,
                    "n_cells_raw": dataset.n_cells_raw,
                    "n_cells_formal": dataset.n_cells_formal,
                    "n_controls": dataset.n_controls,
                    "n_perturbed": dataset.n_perturbed,
                    "n_unique_targets": dataset.n_unique_targets,
                    "stage": dataset.stage,
                    "status": dataset.status,
                    "output_path": dataset.output_path,
                    "notes": dataset.notes,
                }
            )

    print(f"已写出: {FORMAL_CONTRACT_TSV_PATH}")
    print(f"共渲染 {len(datasets)} 个数据集。")


if __name__ == "__main__":
    main()
