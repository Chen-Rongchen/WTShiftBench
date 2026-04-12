#!/usr/bin/env python3
"""按固定顺序运行 Stage 2 closure 主线。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from wtbench.stage2_truth_bridge import resolve_path

from scripts.materialize_stage2_covariates import materialize_covariates_from_config
from scripts.run_stage2_covariate_audit import run_covariate_audit_from_config
from scripts.run_stage2_truth_bridge_sensitivity import run_sensitivity_from_config


def load_pipeline_config(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "materialize_covariates_config",
        "sensitivity_config",
        "covariate_audit_config",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"closure pipeline 配置缺少字段: {missing}")
    return payload


def validate_pipeline_outputs(
    materialized_paths: list[Path],
    *,
    sensitivity_report_root: Path,
    covariate_report_root: Path,
) -> list[Path]:
    expected_paths = [
        *materialized_paths,
        sensitivity_report_root / "control_subsample_replicates.tsv",
        sensitivity_report_root / "control_subsample_summary.tsv",
        sensitivity_report_root / "control_subsample_rank_stability.tsv",
        sensitivity_report_root / "sensitivity_report.md",
        covariate_report_root / "summary.tsv",
        covariate_report_root / "summary.md",
    ]
    missing = [path for path in expected_paths if not path.exists()]
    if missing:
        rendered = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"closure pipeline 输出缺失: {rendered}")
    return expected_paths


def run_closure_pipeline_from_config(config_path: Path) -> dict[str, list[Path] | Path]:
    cfg = load_pipeline_config(config_path)

    materialized_paths = materialize_covariates_from_config(
        resolve_path(str(cfg["materialize_covariates_config"]))
    )
    sensitivity_report_root, _ = run_sensitivity_from_config(
        resolve_path(str(cfg["sensitivity_config"]))
    )
    covariate_report_root, _ = run_covariate_audit_from_config(
        resolve_path(str(cfg["covariate_audit_config"]))
    )

    expected_paths: list[Path] = []
    if bool(cfg.get("validate_outputs", True)):
        expected_paths = validate_pipeline_outputs(
            materialized_paths,
            sensitivity_report_root=sensitivity_report_root,
            covariate_report_root=covariate_report_root,
        )

    return {
        "materialized_paths": materialized_paths,
        "sensitivity_report_root": sensitivity_report_root,
        "covariate_report_root": covariate_report_root,
        "validated_paths": expected_paths,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="运行 Stage 2 closure pipeline。")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/stage2/stage2_closure_pipeline_v1.json"),
        help="closure pipeline 配置 JSON。",
    )
    args = parser.parse_args()

    outputs = run_closure_pipeline_from_config(args.config)

    print("Stage 2 closure pipeline 完成。")
    print("- materialized covariates:")
    for path in outputs["materialized_paths"]:
        print(f"  - {path}")
    print(f"- sensitivity reports: {outputs['sensitivity_report_root']}")
    print(f"- covariate audit reports: {outputs['covariate_report_root']}")
    if outputs["validated_paths"]:
        print("- validated outputs:")
        for path in outputs["validated_paths"]:
            print(f"  - {path}")


if __name__ == "__main__":
    main()
