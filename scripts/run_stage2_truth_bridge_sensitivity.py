#!/usr/bin/env python3
"""Stage 2 truth bridge 敏感性分析：control 子抽样、DEG 阈值扫描、可选协变量分层审计。"""
from __future__ import annotations

import argparse
from pathlib import Path

from wtbench.stage2_truth_bridge import load_config, load_depmap_endpoint, resolve_path
from wtbench.stage2_truth_sensitivity import load_sensitivity_config, run_all_sensitivity_analyses


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 2 truth-driven bridge 敏感性分析。")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/stage2/truth_bridge_sensitivity_v1.json"),
        help="敏感性分析配置 JSON。",
    )
    args = parser.parse_args()

    sens = load_sensitivity_config(args.config)
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
        for cell_line, frame in cov.items():
            frame.to_csv(cov_dir / f"{cell_line}_target_control_balance.tsv", sep="\t", index=False)

    print("Stage 2 truth bridge 敏感性分析完成。")
    print(f"- {report_root}")


if __name__ == "__main__":
    main()
