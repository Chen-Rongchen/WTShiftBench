#!/usr/bin/env python3
"""只运行 Stage 2 covariate balance audit。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from wtbench.truth_bridge import build_dataset_specs, load_config, load_single_feature_calls, resolve_path
from wtbench.truth_sensitivity import get_covariate_strat_columns, run_covariate_audits


def load_covariate_config(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {"base_config", "output", "covariates"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"covariate audit 配置缺少字段: {missing}")
    return payload


def write_covariate_outputs(report_root: Path, outputs: dict[str, pd.DataFrame]) -> None:
    summary_rows: list[dict[str, object]] = []
    md_lines = [
        "# Stage 2 Covariate Balance Summary",
        "",
        "## 状态",
        "",
        f"- 已完成 `{len(outputs)}` 个 cell line 的 covariate balance 审计",
        "- 统计量：`total_variation_distance`",
        "",
    ]

    for cell_line in sorted(outputs):
        frame = outputs[cell_line].copy()
        frame.to_csv(report_root / f"{cell_line}_target_control_balance.tsv", sep="\t", index=False)
        md_lines.extend([f"## {cell_line}", ""])
        for strat_col, sub in frame.groupby("strat_column", sort=True):
            path = report_root / f"{cell_line}_{strat_col}_target_control_balance.tsv"
            sub.to_csv(path, sep="\t", index=False)
            mean_tvd = float(sub["total_variation_distance"].mean()) if not sub.empty else float("nan")
            median_tvd = float(sub["total_variation_distance"].median()) if not sub.empty else float("nan")
            n_gt_015 = int(sub["total_variation_distance"].gt(0.15).sum())
            n_gt_025 = int(sub["total_variation_distance"].gt(0.25).sum())
            n_strata = int(sub["n_strata"].iloc[0]) if not sub.empty else 0
            summary_rows.append(
                {
                    "cell_line": cell_line,
                    "strat_column": strat_col,
                    "n_targets": int(len(sub)),
                    "n_strata": n_strata,
                    "mean_tvd": mean_tvd,
                    "median_tvd": median_tvd,
                    "n_targets_tvd_gt_0.15": n_gt_015,
                    "n_targets_tvd_gt_0.25": n_gt_025,
                    "report_path": str(path),
                }
            )
            md_lines.extend(
                [
                    f"### {strat_col}",
                    "",
                    f"- `n_targets = {len(sub)}`",
                    f"- `n_strata = {n_strata}`",
                    f"- `mean_tvd = {mean_tvd:.4f}`",
                    f"- `median_tvd = {median_tvd:.4f}`",
                    f"- `n_targets_tvd_gt_0.15 = {n_gt_015}`",
                    f"- `n_targets_tvd_gt_0.25 = {n_gt_025}`",
                    "",
                ]
            )

    summary = pd.DataFrame(summary_rows).sort_values(["cell_line", "strat_column"]).reset_index(drop=True)
    summary.to_csv(report_root / "summary.tsv", sep="\t", index=False)
    (report_root / "summary.md").write_text("\n".join(md_lines), encoding="utf-8")


def run_covariate_audit_from_config(config_path: Path) -> tuple[Path, dict[str, pd.DataFrame]]:
    cfg = load_covariate_config(config_path)
    base = load_config(resolve_path(cfg["base_config"]))
    out_dir = resolve_path(cfg["output"]["report_root"])
    out_dir.mkdir(parents=True, exist_ok=True)

    out: dict[str, pd.DataFrame] = {}
    control_prefix = str(base["filters"]["control_target_prefix"])
    for spec in build_dataset_specs(base):
        block = cfg["covariates"].get(spec.cell_line)
        if not block:
            continue
        cov = pd.read_csv(resolve_path(block["path"]), sep="\t")
        barcode_col = str(block.get("barcode_column", "cell_barcode"))
        strat_columns = get_covariate_strat_columns(block)
        calls = load_single_feature_calls(spec, control_prefix=control_prefix)
        out[spec.cell_line] = run_covariate_audits(
            calls,
            cov,
            barcode_col=barcode_col,
            strat_columns=strat_columns,
        )
    write_covariate_outputs(out_dir, out)
    return out_dir, out


def main() -> None:
    parser = argparse.ArgumentParser(description="运行 Stage 2 covariate balance audit。")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/truth_bridge_covariate_audit_v1.json"),
        help="covariate audit 配置 JSON。",
    )
    args = parser.parse_args()

    out_dir, out = run_covariate_audit_from_config(args.config)

    print("Stage 2 covariate audit 完成。")
    for cell_line in sorted(out):
        print(f"- {out_dir / f'{cell_line}_target_control_balance.tsv'}")
    print(f"- {out_dir / 'summary.tsv'}")
    print(f"- {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
