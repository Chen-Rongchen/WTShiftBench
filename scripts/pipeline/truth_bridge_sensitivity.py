#!/usr/bin/env python3
"""Stage 2 truth bridge 敏感性分析：control 子抽样、DEG 阈值扫描、可选协变量分层审计。"""
from __future__ import annotations

import argparse
from pathlib import Path

from wtbench.truth_bridge import load_config, load_depmap_endpoint, resolve_path
from wtbench.truth_sensitivity import load_sensitivity_config, run_all_sensitivity_analyses
from scripts.pipeline.covariate_audit import write_covariate_outputs


def write_sensitivity_report(report_root: Path, summary) -> None:
    configured = int(summary["configured_replicates"].max()) if not summary.empty else 0
    completed = int(summary["completed_replicates"].max()) if not summary.empty else 0
    formal = bool(summary["formal_interval_citable"].all()) if not summary.empty else False
    claim_status = (
        "formal_interval_citable"
        if formal
        else "partial_preliminary_snapshot"
    )
    lines = [
        "# Stage 2 Truth Bridge Sensitivity",
        "",
        "## 状态",
        "",
        f"- configured_replicates = `{configured}`",
        f"- completed_replicates = `{completed}`",
        f"- formal_interval_citable = `{str(formal).lower()}`",
        f"- sensitivity_claim_status = `{claim_status}`",
        "",
        "## 解释边界",
        "",
    ]
    if formal:
        lines.append("- 当前 control subsampling 已达到配置重复次数，可正式引用区间/分位数结果。")
    else:
        lines.append("- 当前仅为 partial / preliminary sensitivity snapshot。")
        lines.append("- 未跑满 configured replicates 前，禁止输出正式 interval claim。")
        lines.append("- 未跑满 configured replicates 前，禁止写 robustness range established。")
    (report_root / "sensitivity_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_sensitivity_from_config(config_path: Path) -> tuple[Path, dict]:
    sens = load_sensitivity_config(config_path)
    base = load_config(resolve_path(sens["base_config"]))

    depmap_effect = load_depmap_endpoint(resolve_path(base["depmap"]["gene_effect_path"]))
    depmap_dependency = load_depmap_endpoint(resolve_path(base["depmap"]["gene_dependency_path"]))

    report_root = resolve_path(sens["output"]["report_root"])
    report_root.mkdir(parents=True, exist_ok=True)

    out = run_all_sensitivity_analyses(
        base,
        sens,
        depmap_effect=depmap_effect,
        depmap_dependency=depmap_dependency,
    )

    out["control_subsample_replicates"].to_csv(
        report_root / "control_subsample_replicates.tsv", sep="\t", index=False
    )
    out["control_subsample_summary"].to_csv(
        report_root / "control_subsample_summary.tsv", sep="\t", index=False
    )
    out["rank_stability"].to_csv(report_root / "control_subsample_rank_stability.tsv", sep="\t", index=False)

    deg_df = out["deg_threshold_sweep"]
    if deg_df is not None and not deg_df.empty:
        deg_df.to_csv(report_root / "deg_threshold_sweep.tsv", sep="\t", index=False)

    cov = out["covariate_balance"]
    if cov:
        cov_dir = report_root / "covariate_balance"
        cov_dir.mkdir(parents=True, exist_ok=True)
        write_covariate_outputs(cov_dir, cov)

    write_sensitivity_report(report_root, out["control_subsample_summary"])
    return report_root, out


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 2 truth-driven bridge 敏感性分析。")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/truth_bridge_sensitivity_v1.json"),
        help="敏感性分析配置 JSON。",
    )
    args = parser.parse_args()

    report_root, _ = run_sensitivity_from_config(args.config)

    print("Stage 2 truth bridge 敏感性分析完成。")
    print(f"- {report_root}")


if __name__ == "__main__":
    main()
