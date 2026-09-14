"""Check restored official DepMap inputs against historical endpoints, exporting verification records only."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

from wtbench.truth_bridge import load_depmap_endpoint


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/revision_depmap_restore"
ATOL = 1e-12
ENDPOINTS = {
    "depmap_gene_effect": "depmap/CRISPRGeneEffect.csv",
    "depmap_gene_dependency": "depmap/CRISPRGeneDependency.csv",
}
SOURCES = [
    "data/processed/truth_driven_bridge/combined_target_level_bridge_table.tsv.gz",
    "data/processed/truth_driven_bridge_replogle_k562_essential_day7/combined_target_level_bridge_table.tsv.gz",
    "data/processed/truth_driven_bridge_replogle_k562_gwps_day8/combined_target_level_bridge_table.tsv.gz",
    "reports/gse264667_endpoint_extension/gse264667_hepg2_day7/target_level_bridge_table.tsv.gz",
    "reports/gse264667_endpoint_extension/gse264667_jurkat_day7/target_level_bridge_table.tsv.gz",
    "data/processed/truth_driven_bridge_gse90063_7d/combined_target_level_bridge_table.tsv.gz",
    "data/processed/truth_driven_bridge_gse90063_13d/combined_target_level_bridge_table.tsv.gz",
]


def digest(path: str) -> str:
    result = hashlib.sha256()
    with (ROOT / path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def compare_endpoint(group: pd.DataFrame, matrix: pd.DataFrame, endpoint: str):
    """Match by ModelID/gene name and separately record historical missingness and CSV rounding differences."""
    restored = np.array([
        matrix.loc[row.depmap_model_id].get(row.target_gene, np.nan)
        for row in group.itertuples()
    ], dtype=float)
    old = group[endpoint].to_numpy(dtype=float)
    both = np.isfinite(old) & np.isfinite(restored)
    missing_changed = np.isnan(old) != np.isnan(restored)
    absolute_error = np.abs(old - restored)
    changed = both & (absolute_error > ATOL)
    result = group[["source_path", "source_line", "cell_line", "depmap_model_id", "target_gene"]].copy()
    result["endpoint"] = endpoint
    result["historical_value"] = old
    result["restored_value"] = restored
    result["absolute_error"] = absolute_error
    result["status"] = np.select(
        [missing_changed, changed, both & (absolute_error == 0), both],
        ["Missingness changed", "Numerical mismatch", "Exact match", "Floating-point rounding difference only"],
        default="Missing in both",
    )
    summary = dict(
        context=group.cell_line.iloc[0], endpoint=endpoint,
        source_path=group.source_path.iloc[0], historical_rows=len(group),
        finite_compared=int(both.sum()), exact_matches=int((both & (absolute_error == 0)).sum()),
        tolerance_matches=int((both & ~changed).sum()),
        max_absolute_error=float(absolute_error[both].max()) if both.any() else None,
        value_mismatches=int(changed.sum()), missing_status_changes=int(missing_changed.sum()),
        both_missing=int((np.isnan(old) & np.isnan(restored)).sum()),
        status="Historical endpoint mismatch; provenance unresolved" if changed.any() or missing_changed.any() else "Verification passed",
    )
    return result, summary


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    script = "scripts/revision/verify_depmap_restore.py"
    pipeline = "scripts/pipeline/materialize_gse264667_bridge.py"
    old_registry = "reports/revision/m2_attrition_audit/depmap_release_registry.json"
    external_manifest = "docs/revision_external_cell_count/run_manifest.json"
    sources = list(ENDPOINTS.values()) + SOURCES + [
        script, pipeline, "src/wtbench/truth_bridge.py", old_registry, external_manifest,
        "scripts/revision/test_external_cell_count.py", "scripts/revision/check_equal_n_attrition.py",
        "reports/gse264667_endpoint_extension/artifact_hashes.tsv",
        "reports/gse264667_endpoint_extension/gse264667_hepg2_day7/materialization_qc.tsv",
        "reports/gse264667_endpoint_extension/gse264667_jurkat_day7/materialization_qc.tsv",
        "docs/revision_model_findings/extraction_manifest.json",
        "pixi.toml", "pixi.lock",
    ]
    initial = {path: digest(path) for path in sources}
    matrices = {}
    file_checks = []
    for endpoint, path in ENDPOINTS.items():
        matrix = load_depmap_endpoint(ROOT / path).set_index("depmap_model_id", verify_integrity=True)
        assert not matrix.columns.duplicated().any(), f"Duplicate gene names after cleaning: {path}"
        assert all(pd.api.types.is_numeric_dtype(dtype) for dtype in matrix.dtypes), path
        assert not np.isinf(matrix.to_numpy()).any(), path
        matrices[endpoint] = matrix
        file_checks.append(dict(endpoint=endpoint, path=path, size_bytes=(ROOT / path).stat().st_size,
                                sha256=initial[path], n_models=len(matrix), n_genes=len(matrix.columns),
                                missing_numeric_cells=int(matrix.isna().sum().sum())))
        print(f"Loaded {path}: {matrix.shape}", flush=True)
    effect, probability = [matrices[k] for k in ENDPOINTS]
    old = json.loads((ROOT / old_registry).read_text())
    primary_hash_matches = initial[ENDPOINTS["depmap_gene_dependency"]] == old["primary_endpoint"]["sha256"]
    assert primary_hash_matches, "Primary dependency file no longer matches the M2 frozen hash"

    tables, summaries = [], []
    for path in SOURCES:
        historical = pd.read_csv(ROOT / path, sep="\t")
        historical["source_path"] = path
        historical["source_line"] = np.arange(len(historical)) + 2
        for _, group in historical.groupby("cell_line", sort=False):
            for endpoint, matrix in matrices.items():
                table, summary = compare_endpoint(group, matrix, endpoint)
                tables.append(table)
                summaries.append(summary)
                print(f"{summary['context']} / {endpoint}：{summary['status']}", flush=True)
    detail = pd.concat(tables, ignore_index=True)
    summary = pd.DataFrame(summaries)
    detail_path = OUT / "endpoint_comparison.tsv.gz"
    detail.to_csv(detail_path, sep="\t", index=False, na_rep="NA", compression={"method": "gzip", "mtime": 0})
    summary_path = OUT / "comparison_summary.tsv"
    summary.to_csv(summary_path, sep="\t", index=False, na_rep="NA")

    # Verify sources against existing manifests; do not rerun bootstrap/permutation or model scoring.
    ext = json.loads((ROOT / external_manifest).read_text())
    source_checks = [dict(path=r["path"], matches=digest(r["path"]) == r["sha256"])
                     for r in ext["inputs"] if r["path"] in SOURCES]
    assert all(r["matches"] for r in source_checks), "Historical tables differ from external cell-count test inputs"
    frozen_checks = []
    extraction = json.loads((ROOT / "docs/revision_model_findings/extraction_manifest.json").read_text())
    # This extraction covers formal M4/M5 results, objects, and configurations; retain frozen evidence without refreshing old manifests.
    for path, sha in extraction["inputs_sha256"].items():
        frozen_checks.append(dict(path=path, matches=digest(path) == sha))
    for path, sha in extraction["output_sha256"].items():
        frozen_checks.append(dict(path=path, matches=digest(path) == sha))
    assert all(r["matches"] for r in frozen_checks), "M4/M5 extraction inputs changed"

    git_paths = subprocess.check_output(
        ["git", "log", "--all", "--name-only", "--format=", "--", "*CRISPRGeneEffect*"], cwd=ROOT, text=True,
    ).splitlines()
    old_script = subprocess.check_output(["git", "show", f"d67951f:{pipeline}"], cwd=ROOT)
    archive = "WTShiftBench_repo_source_tables_for_BIB.zip"
    with ZipFile(ROOT / archive) as handle:
        archive_matches = [n for n in handle.namelist() if "crisprgeneeffect" in n.lower()]
    after = {path: digest(path) for path in sources}
    assert initial == after, "Inputs changed during verification"
    manifest = dict(
        completed_utc=datetime.now(timezone.utc).isoformat(),
        status="Verification complete; historical HepG2/Jurkat gene-effect sources remain unresolved",
        official_file_provenance="On2026-09-07, the user confirmed official DepMap provenance and restored25Q3 as requested; no additional download required.",
        scope="Numerical, missingness, and provenance checks only; no retraining, rescoring, overwriting old tables, or changing frozen objects.",
        tolerance_absolute=ATOL, file_checks=file_checks,
        gene_axis_identical=effect.columns.equals(probability.columns),
        model_id_set_identical=set(effect.index) == set(probability.index),
        model_row_order_identical=effect.index.equals(probability.index),
        primary_hash_matches_frozen_registry=primary_hash_matches,
        inputs=[dict(path=p, sha256=sha) for p, sha in initial.items()],
        external_source_checks=source_checks, frozen_model_source_checks=frozen_checks,
        inputs_unchanged=True,
        historical_trace=dict(
            git_paths_for_original_gene_effect=sorted(set(git_paths)),
            generating_script_commit="d67951f",
            generating_script_unchanged_since_commit=hashlib.sha256(old_script).hexdigest() == initial[pipeline],
            matching_logic="Select rows by ModelID independently in each file, then retrieve genes by name; do not rely on matching row numbers.",
            old_materialization_provenance="QC recorded raw-expression and output hashes, but not the DepMap gene-effect input version or hash.",
            searched_archive=archive, archive_gene_effect_members=archive_matches,
            conclusion="Available Git objects and submission ZIPs contain no historical raw CSV; existing records cannot identify the historical HepG2/Jurkat gene-effect version.",
        ),
        outputs=[dict(path=str(p.relative_to(ROOT)), sha256=digest(str(p.relative_to(ROOT))))
                 for p in [detail_path, summary_path]],
    )
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(summary[["context", "endpoint", "finite_compared", "value_mismatches", "missing_status_changes"]].to_string(index=False))


if __name__ == "__main__":
    main()
