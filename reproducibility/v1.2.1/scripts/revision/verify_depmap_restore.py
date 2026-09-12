"""核对恢复的官方 DepMap 输入与历史端点；只导出核验记录，不覆盖分析结果。"""

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
    """按 ModelID/基因名比对；真实旧表存在缺失和 CSV 浮点往返，分别登记。"""
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
        ["缺失状态变化", "数值不一致", "完全一致", "仅浮点舍入差异"],
        default="两边均缺失",
    )
    summary = dict(
        context=group.cell_line.iloc[0], endpoint=endpoint,
        source_path=group.source_path.iloc[0], historical_rows=len(group),
        finite_compared=int(both.sum()), exact_matches=int((both & (absolute_error == 0)).sum()),
        tolerance_matches=int((both & ~changed).sum()),
        max_absolute_error=float(absolute_error[both].max()) if both.any() else None,
        value_mismatches=int(changed.sum()), missing_status_changes=int(missing_changed.sum()),
        both_missing=int((np.isnan(old) & np.isnan(restored)).sum()),
        status="历史端点不一致，保留待追溯" if changed.any() or missing_changed.any() else "核验通过",
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
        assert not matrix.columns.duplicated().any(), f"清洗后基因名重复：{path}"
        assert all(pd.api.types.is_numeric_dtype(dtype) for dtype in matrix.dtypes), path
        assert not np.isinf(matrix.to_numpy()).any(), path
        matrices[endpoint] = matrix
        file_checks.append(dict(endpoint=endpoint, path=path, size_bytes=(ROOT / path).stat().st_size,
                                sha256=initial[path], n_models=len(matrix), n_genes=len(matrix.columns),
                                missing_numeric_cells=int(matrix.isna().sum().sum())))
        print(f"已读取 {path}：{matrix.shape}", flush=True)
    effect, probability = [matrices[k] for k in ENDPOINTS]
    old = json.loads((ROOT / old_registry).read_text())
    primary_hash_matches = initial[ENDPOINTS["depmap_gene_dependency"]] == old["primary_endpoint"]["sha256"]
    assert primary_hash_matches, "primary dependency 文件不再匹配 M2 冻结哈希"

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

    # 用已有 manifest 核对来源；不重新进行 bootstrap/置换或模型评分。
    ext = json.loads((ROOT / external_manifest).read_text())
    source_checks = [dict(path=r["path"], matches=digest(r["path"]) == r["sha256"])
                     for r in ext["inputs"] if r["path"] in SOURCES]
    assert all(r["matches"] for r in source_checks), "旧表已偏离外部 cell-count 检验输入"
    frozen_checks = []
    extraction = json.loads((ROOT / "docs/revision_model_findings/extraction_manifest.json").read_text())
    # 该摘录记录覆盖 M4/M5 正式结果、对象与配置；保留冻结证据而不刷新旧 manifest。
    for path, sha in extraction["inputs_sha256"].items():
        frozen_checks.append(dict(path=path, matches=digest(path) == sha))
    for path, sha in extraction["output_sha256"].items():
        frozen_checks.append(dict(path=path, matches=digest(path) == sha))
    assert all(r["matches"] for r in frozen_checks), "M4/M5 摘录输入发生变化"

    git_paths = subprocess.check_output(
        ["git", "log", "--all", "--name-only", "--format=", "--", "*CRISPRGeneEffect*"], cwd=ROOT, text=True,
    ).splitlines()
    old_script = subprocess.check_output(["git", "show", f"d67951f:{pipeline}"], cwd=ROOT)
    archive = "WTShiftBench_repo_source_tables_for_BIB.zip"
    with ZipFile(ROOT / archive) as handle:
        archive_matches = [n for n in handle.namelist() if "crisprgeneeffect" in n.lower()]
    after = {path: digest(path) for path in sources}
    assert initial == after, "核验过程中输入改变"
    manifest = dict(
        completed_utc=datetime.now(timezone.utc).isoformat(),
        status="核验完成；HepG2/Jurkat 历史 gene-effect 来源尚未确定",
        official_file_provenance="用户于 2026-09-07 确认文件来自 DepMap 官方，按项目要求恢复 25Q3；不要求重新下载。",
        scope="数值、缺失状态和来源核验；未重训、重评分、覆盖旧表或修改冻结对象。",
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
            matching_logic="分别按 ModelID 选择各文件行，再按基因名取值；不依赖行号相同。",
            old_materialization_provenance="QC 保存表达原始文件/输出哈希，没有保存 DepMap gene-effect 输入的版本和哈希。",
            searched_archive=archive, archive_gene_effect_members=archive_matches,
            conclusion="现有 Git/投稿 ZIP 无旧原始 CSV；无法由记录确定旧 HepG2/Jurkat gene-effect 文件版本。",
        ),
        outputs=[dict(path=str(p.relative_to(ROOT)), sha256=digest(str(p.relative_to(ROOT))))
                 for p in [detail_path, summary_path]],
    )
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(summary[["context", "endpoint", "finite_compared", "value_mismatches", "missing_status_changes"]].to_string(index=False))


if __name__ == "__main__":
    main()
