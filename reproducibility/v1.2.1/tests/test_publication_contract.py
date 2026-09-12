"""检查本轮实际发生过的遗漏：D40、完整seed集合、矩阵轴与源hash。"""

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_all_reported_outputs_and_cellot_seeds_present():
    runs = pd.read_csv(ROOT / "provenance/run_registry.tsv", sep="\t")
    assert len(runs) == 87 and runs.run_id.is_unique
    selected = runs[runs.model.str.contains("cellot")]
    assert set(zip(selected.context, selected.training_seed.astype(int))) == {
        (context, seed) for context in ["HCC38", "HCC1143"] for seed in range(123, 128)
    }
    assert set(selected[selected.role == "formal"].training_seed.astype(int)) == {123}


def test_all_46_source_tables_and_d40_present():
    index = pd.read_csv(ROOT / "presentation/INDEX.tsv", sep="\t")
    assert set(index.sheet) == {f"D{i:02d}" for i in range(1, 47)}
    for row in index.itertuples():
        assert hashlib.sha256((ROOT / row.path).read_bytes()).hexdigest() == row.sha256


def test_output_axes_are_unique_and_have_declared_lengths():
    outputs = pd.read_csv(ROOT / "manifests/outputs.tsv", sep="\t")
    assert set(outputs.n_genes) == {47, 1024}
    for row in outputs.itertuples():
        for kind, path, expected in [("target", row.target_axis, row.n_targets), ("gene", row.gene_axis, row.n_genes)]:
            axis = pd.read_csv(ROOT / path, sep="\t", dtype=str)[kind]
            assert len(axis) == expected and axis.is_unique


def test_copied_scientific_files_match_recorded_bytes():
    provenance = json.loads((ROOT / "manifests/source_provenance.json").read_text())
    for row in provenance["files"]:
        assert hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"]
