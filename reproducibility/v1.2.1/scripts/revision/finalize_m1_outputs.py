#!/usr/bin/env python
"""合并既有 robustness 资产并冻结 M1_FINAL 报告。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_combined_robustness(output_root: Path) -> pd.DataFrame:
    inference_path = output_root / "bridge_inference_summary.tsv"
    control_path = PROJECT_ROOT / "reports/truth_driven_bridge/sensitivity/control_subsample_summary.tsv"
    anchor_path = PROJECT_ROOT / "reports/truth_driven_bridge/sensitivity/leave_anchor_out_summary.tsv"
    inference = pd.read_csv(inference_path, sep="\t")
    control = pd.read_csv(control_path, sep="\t")
    anchor = pd.read_csv(anchor_path, sep="\t", comment="#")

    rows: list[dict[str, object]] = []
    shift_rows = inference.loc[
        inference["analysis_id"].eq("raw_observed_shift")
        | inference["analysis_id"].str.startswith("alternative_")
    ]
    for _, row in shift_rows.iterrows():
        rows.append(
            {
                "evidence_type": "shift_metric_definition",
                "cell_line": row["cell_line"],
                "analysis": row["analysis_id"],
                "n_targets": int(row["n_targets"]),
                "estimate": row["spearman_rho"],
                "interval_low": row["bootstrap_ci_low"],
                "interval_high": row["bootstrap_ci_high"],
                "interval_type": "target_bootstrap_95pct",
                "source_file": str(inference_path.relative_to(PROJECT_ROOT)),
                "note": "dependency-probability endpoint",
            }
        )

    control = control.loc[control["depmap_endpoint"].eq("depmap_gene_dependency")]
    target_counts = {"HCC38": 47, "HCC1143": 48}
    for _, row in control.iterrows():
        rows.append(
            {
                "evidence_type": "control_cell_subsampling",
                "cell_line": row["cell_line"],
                "analysis": row["truth_metric"],
                "n_targets": target_counts[str(row["cell_line"])],
                "estimate": row["spearman_aligned_mean"],
                "interval_low": row["spearman_aligned_q025"],
                "interval_high": row["spearman_aligned_q975"],
                "interval_type": "24_replicate_interval",
                "source_file": str(control_path.relative_to(PROJECT_ROOT)),
                "note": f"control subsample n={int(row['n_replicates'])} replicates",
            }
        )

    anchor = anchor.loc[
        anchor["removed"].isin(["none", "all_four_anchors", "jackknife_min", "jackknife_max"])
    ]
    for _, row in anchor.iterrows():
        rows.append(
            {
                "evidence_type": "anchor_influence",
                "cell_line": row["context"],
                "analysis": row["removed"],
                "n_targets": int(row["n_targets"]),
                "estimate": row["spearman_rho"],
                "interval_low": np.nan,
                "interval_high": np.nan,
                "interval_type": "not_applicable",
                "source_file": str(anchor_path.relative_to(PROJECT_ROOT)),
                "note": f"rho_delta={row['rho_delta']:.6f}",
            }
        )

    combined = pd.DataFrame(rows).sort_values(
        ["evidence_type", "cell_line", "analysis"]
    )
    combined.to_csv(output_root / "combined_robustness_summary.tsv", sep="\t", index=False)
    return combined


def build_attrition_tables(output_root: Path) -> None:
    targets = pd.read_csv(
        output_root / "target_level_covariates_and_corrected_shift.tsv",
        sep="\t",
    )
    rows: list[dict[str, object]] = []
    for cell_line, context in targets.groupby("cell_line"):
        for depth in [20, 25, 50, 100]:
            for status, subset in [
                ("retained", context.loc[context["n_cells_target"].ge(depth)]),
                ("excluded", context.loc[context["n_cells_target"].lt(depth)]),
            ]:
                rows.append(
                    {
                        "cell_line": cell_line,
                        "depth": depth,
                        "status": status,
                        "n_targets": len(subset),
                        "target_genes": ",".join(sorted(subset["target_gene"])),
                        "median_observed_shift": subset["observed_shift_mean_abs"].median(),
                        "min_observed_shift": subset["observed_shift_mean_abs"].min(),
                        "max_observed_shift": subset["observed_shift_mean_abs"].max(),
                        "median_dependency": subset["depmap_gene_dependency"].median(),
                        "min_dependency": subset["depmap_gene_dependency"].min(),
                        "max_dependency": subset["depmap_gene_dependency"].max(),
                    }
                )
    pd.DataFrame(rows).to_csv(
        output_root / "equal_n_attrition_summary.tsv",
        sep="\t",
        index=False,
    )
    fixed = targets.loc[targets["n_cells_target"].ge(100), [
        "cell_line",
        "target_gene",
        "n_cells_target",
        "observed_shift_mean_abs",
        "noise_corrected_shift",
        "depmap_gene_dependency",
    ]].sort_values(["cell_line", "target_gene"])
    fixed.to_csv(output_root / "fixed_cohort_targets.tsv", sep="\t", index=False)


def write_final_report(output_root: Path, combined: pd.DataFrame) -> Path:
    core_report = (output_root / "m1_report.md").read_text(encoding="utf-8")
    control = combined.loc[
        combined["evidence_type"].eq("control_cell_subsampling")
        & combined["analysis"].eq("real_shift_mean_abs")
    ]
    anchors = combined.loc[
        combined["evidence_type"].eq("anchor_influence")
        & combined["analysis"].eq("all_four_anchors")
    ]
    lines = [
        "# BIB 大修 M1_FINAL",
        "",
        "状态：`FINAL`。A002 是初次结果后的实现修正，已公开记录 outcome awareness。",
        "",
        core_report,
        "## 回收的既有 robustness 证据",
        "",
        "| evidence | context | estimate | interval/change |",
        "| --- | --- | ---: | --- |",
    ]
    for _, row in control.sort_values("cell_line").iterrows():
        lines.append(
            f"| 500-control subsampling | {row['cell_line']} | {row['estimate']:.3f} | "
            f"[{row['interval_low']:.3f}, {row['interval_high']:.3f}] across 24 replicates |"
        )
    for _, row in anchors.sort_values("cell_line").iterrows():
        lines.append(
            f"| remove all four original anchors | {row['cell_line']} | {row['estimate']:.3f} | "
            f"{row['note']} |"
        )
    lines.extend(
        [
            "",
            "完整 alternative-shift、control-subsampling 与 anchor-influence 数值见 `combined_robustness_summary.tsv`。",
            "各 equal-n threshold 的 retained/excluded 名单与分布见 `equal_n_attrition_summary.tsv`；固定 cohort 成员见 `fixed_cohort_targets.tsv`。",
            "",
            "## M1_FINAL 决策",
            "",
            "- raw association 明显受到 cell-count structure 放大；不能继续作为未经 qualification 的 primary endpoint statistic。",
            "- 在预设 equal-n 与 matched-control null 下，finite-sampling artifact 未完全重现 raw association。",
            "- HCC38 的 partial-rank 和 OLS/HC3 不支持控制 log cell count 后仍存在独立 association；HCC1143 的证据较强但不同模型形式并不完全一致。",
            "- 冻结的 dual-context Gate 结论为 `STOP_AND_REASSESS`；下一步先选择并冻结 corrected endpoint object，不直接进入 model scoring。",
            "- low recovered cell count 仅解释为与 depletion/reduced recovery 一致，不写成已证明的 cell death 或因果机制。",
            "",
        ]
    )
    path = output_root / "M1_FINAL.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_manifest(output_root: Path, final_report: Path) -> None:
    input_paths = [
        PROJECT_ROOT / "src/wtbench/revision_bridge_sensitivity.py",
        PROJECT_ROOT / "scripts/revision/run_m1_bridge_sensitivity.py",
        PROJECT_ROOT / "scripts/revision/finalize_m1_outputs.py",
        PROJECT_ROOT / "configs/revision/revision_analysis_registry_v1.json",
        PROJECT_ROOT / "configs/revision/amendment_001_m1_statistical_clarifications.json",
        PROJECT_ROOT / "configs/revision/amendment_002_m1_code_audit.json",
        PROJECT_ROOT / "reports/truth_driven_bridge/sensitivity/control_subsample_summary.tsv",
        PROJECT_ROOT / "reports/truth_driven_bridge/sensitivity/leave_anchor_out_summary.tsv",
        output_root / "run_manifest.json",
    ]
    output_paths = sorted(
        path
        for path in output_root.iterdir()
        if path.is_file() and path.name != "m1_final_manifest.json"
    )
    payload = {
        "status": "M1_FINAL",
        "date": "2026-09-04",
        "final_report": str(final_report.relative_to(PROJECT_ROOT)),
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": sha256_file(path)}
            for path in input_paths
        ],
        "outputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": sha256_file(path)}
            for path in output_paths
        ],
    }
    (output_root / "m1_final_manifest.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        default="reports/revision/m1_bridge_confounding",
    )
    args = parser.parse_args()
    output_root = PROJECT_ROOT / args.output_root
    combined = build_combined_robustness(output_root)
    build_attrition_tables(output_root)
    final_report = write_final_report(output_root, combined)
    write_manifest(output_root, final_report)
    print(f"M1_FINAL 已生成：{final_report}")


if __name__ == "__main__":
    main()
