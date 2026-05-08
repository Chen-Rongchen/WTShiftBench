from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/dixit_k562_temporal_panel_gse90063_v1.json"


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_recipe(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_metric_summary(path: Path) -> dict[str, str]:
    table = pd.read_csv(path, sep="\t")
    return dict(zip(table["metric"].astype(str), table["value"].astype(str), strict=True))


def aligned_endpoint_values(frame: pd.DataFrame, endpoint: str) -> pd.Series:
    if endpoint == "depmap_gene_effect":
        return -frame[endpoint]
    return frame[endpoint]


def summarize_bridge(
    label: str,
    role: str,
    bridge: pd.DataFrame,
    qc_summary: dict[str, str],
    truth_metrics: list[str],
    endpoints: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base = {
        "timepoint": label,
        "role": role,
        "dataset_label": str(bridge["cell_line"].iloc[0]),
        "n_formal_bridgeable_targets": int(len(bridge)),
        "target_genes": "/".join(sorted(bridge["target_gene"].astype(str))),
        "n_cells_with_single_feature": int(bridge["truth_source_cell_count"].iloc[0]),
        "n_control_cells": int(bridge["n_cells_control"].iloc[0]),
        "qc_guide_rows": int(qc_summary["guide_rows"]),
        "qc_sg_guides": int(qc_summary["sg_guides"]),
        "qc_intergenic_guides": int(qc_summary["intergenic_guides"]),
    }
    for truth_metric in truth_metrics:
        for endpoint in endpoints:
            subset = bridge.loc[:, ["target_gene", truth_metric, endpoint]].dropna()
            aligned_endpoint = aligned_endpoint_values(subset, endpoint)
            rows.append(
                {
                    **base,
                    "truth_metric": truth_metric,
                    "depmap_endpoint": endpoint,
                    "aligned_spearman": float(subset[truth_metric].corr(aligned_endpoint, method="spearman")),
                    "mean_truth_metric": float(subset[truth_metric].mean()),
                    "median_truth_metric": float(subset[truth_metric].median()),
                }
            )
    return rows


def build_target_delta(
    bridges: dict[str, pd.DataFrame],
    primary_truth_metric: str,
    primary_endpoint: str,
) -> pd.DataFrame:
    frames = []
    for label, bridge in bridges.items():
        part = bridge.loc[:, ["target_gene", primary_truth_metric, primary_endpoint]].copy()
        part = part.rename(
            columns={
                primary_truth_metric: f"{label}_{primary_truth_metric}",
                primary_endpoint: f"{label}_{primary_endpoint}",
            }
        )
        frames.append(part)

    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="target_gene", how="outer")

    labels = list(bridges)
    if labels == ["7d", "13d"]:
        merged[f"delta_13d_minus_7d_{primary_truth_metric}"] = (
            merged[f"13d_{primary_truth_metric}"] - merged[f"7d_{primary_truth_metric}"]
        )
        merged[f"ratio_13d_over_7d_{primary_truth_metric}"] = (
            merged[f"13d_{primary_truth_metric}"] / merged[f"7d_{primary_truth_metric}"]
        )
    return merged.sort_values("target_gene").reset_index(drop=True)


def build_structure_summary(timepoints: list[dict[str, Any]]) -> pd.DataFrame:
    frames = []
    for item in timepoints:
        path = resolve_path(str(item["axis_summary_path"]))
        frame = pd.read_csv(path, sep="\t")
        frame.insert(0, "role", str(item["role"]))
        frame.insert(0, "timepoint", str(item["label"]))
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def build_panel_calls(summary: pd.DataFrame, primary_truth_metric: str, primary_endpoint: str) -> pd.DataFrame:
    focused = summary.loc[
        summary["truth_metric"].eq(primary_truth_metric) & summary["depmap_endpoint"].eq(primary_endpoint)
    ].copy()
    focused = focused.sort_values("timepoint").reset_index(drop=True)
    call = "not_evaluable"
    if set(focused["timepoint"]) == {"7d", "13d"}:
        values = dict(zip(focused["timepoint"], focused["aligned_spearman"], strict=True))
        means = dict(zip(focused["timepoint"], focused["mean_truth_metric"], strict=True))
        if values["13d"] > values["7d"]:
            call = "rank_bridge_stronger_at_13d"
        elif values["13d"] < values["7d"]:
            call = "rank_bridge_not_stronger_at_13d"
        else:
            call = "rank_bridge_tied"
        magnitude_call = "mean_shift_stronger_at_13d" if means["13d"] > means["7d"] else "mean_shift_not_stronger_at_13d"
        return pd.DataFrame(
            [
                {
                    "panel_question": "same_context_temporal_bridge",
                    "primary_truth_metric": primary_truth_metric,
                    "primary_depmap_endpoint": primary_endpoint,
                    "rank_bridge_call": call,
                    "mean_shift_call": magnitude_call,
                    "interpretation_boundary": "13d is the primary formal supplementary bridge test; 7d is a temporal sensitivity / early-bridge probe.",
                }
            ]
        )
    return pd.DataFrame(
        [
            {
                "panel_question": "same_context_temporal_bridge",
                "primary_truth_metric": primary_truth_metric,
                "primary_depmap_endpoint": primary_endpoint,
                "rank_bridge_call": call,
                "mean_shift_call": "not_evaluable",
                "interpretation_boundary": "13d is the primary formal supplementary bridge test; 7d is a temporal sensitivity / early-bridge probe.",
            }
        ]
    )


def write_report(
    path: Path,
    summary: pd.DataFrame,
    calls: pd.DataFrame,
    target_delta: pd.DataFrame,
    structure: pd.DataFrame,
) -> None:
    primary = summary.loc[
        summary["truth_metric"].eq("real_shift_mean_abs")
        & summary["depmap_endpoint"].eq("depmap_gene_dependency")
    ].sort_values("timepoint")
    call = calls.iloc[0]
    lines = [
        "# GSE90063 K562 13d/7d temporal panel",
        "",
        "## 定位",
        "",
        "`13d` 是 primary formal supplementary bridge test；`7d` 是 temporal sensitivity / early-bridge probe。该 panel 只回答同一 K562 TF pool 外部 context 下，早期与后期接同一 DepMap endpoint 时 bridge / architecture 轮廓如何变化；它不支持 primary closure 或 external model-side generalization proved。",
        "",
        "## 项目对象层 target 口径",
        "",
        "在当前项目对象层与现行 admission/bridgeability 规则下，`7d` 与 `13d` 目前各有 10 个正式 bridgeable targets 进入 DepMap 对接；这一数字不应与原始实验设计中的 target / guide 数直接等同。",
        "",
        "正式 bridgeable targets：`" + " / ".join(sorted(target_delta["target_gene"].astype(str))) + "`。",
        "",
        "## Primary temporal readout",
        "",
    ]
    for row in primary.to_dict("records"):
        lines.append(
            f"- `{row['timepoint']}`：`real_shift_mean_abs` vs `depmap_gene_dependency` aligned Spearman = `{row['aligned_spearman']:.3f}`；mean shift = `{row['mean_truth_metric']:.6f}`；n targets = `{row['n_formal_bridgeable_targets']}`。"
        )
    lines.extend(
        [
            "",
            "## Panel call",
            "",
            f"- rank bridge call: `{call['rank_bridge_call']}`",
            f"- mean shift call: `{call['mean_shift_call']}`",
            "",
            "## Architecture form",
            "",
        ]
    )
    for row in structure.loc[structure["comparison_field"].isin(["canonical backbone present", "shift-excess present", "architecture class"])].to_dict("records"):
        lines.append(
            f"- `{row['timepoint']}` `{row['comparison_field']}`: `{row['K562_Dixit']}` (`{row['replication_status']}`)"
        )
    lines.append("")
    lines.append("## 产物")
    lines.append("")
    lines.append("- `temporal_bridge_summary.tsv`")
    lines.append("- `temporal_target_delta.tsv`")
    lines.append("- `temporal_structure_summary.tsv`")
    lines.append("- `temporal_panel_calls.tsv`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="构建 GSE90063 K562 13d/7d temporal panel 汇总。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    return parser


def run_from_config(config_path: Path) -> dict[str, Path]:
    recipe = load_recipe(resolve_path(config_path))
    output_dir = resolve_path(str(recipe["output"]["report_root"]))
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics = dict(recipe["metrics"])
    truth_metrics = [str(value) for value in metrics["truth_metrics"]]
    endpoints = [str(value) for value in metrics["depmap_endpoints"]]
    primary_truth_metric = str(metrics["primary_truth_metric"])
    primary_endpoint = str(metrics["primary_depmap_endpoint"])

    bridges: dict[str, pd.DataFrame] = {}
    summary_rows: list[dict[str, Any]] = []
    for item in recipe["timepoints"]:
        label = str(item["label"])
        role = str(item["role"])
        bridge = pd.read_csv(resolve_path(str(item["bridge_table_path"])), sep="\t")
        qc_summary = read_metric_summary(resolve_path(str(item["qc_summary_path"])))
        bridges[label] = bridge
        summary_rows.extend(summarize_bridge(label, role, bridge, qc_summary, truth_metrics, endpoints))

    summary = pd.DataFrame(summary_rows)
    target_delta = build_target_delta(bridges, primary_truth_metric, primary_endpoint)
    structure = build_structure_summary(list(recipe["timepoints"]))
    calls = build_panel_calls(summary, primary_truth_metric, primary_endpoint)

    summary.to_csv(output_dir / "temporal_bridge_summary.tsv", sep="\t", index=False)
    target_delta.to_csv(output_dir / "temporal_target_delta.tsv", sep="\t", index=False)
    structure.to_csv(output_dir / "temporal_structure_summary.tsv", sep="\t", index=False)
    calls.to_csv(output_dir / "temporal_panel_calls.tsv", sep="\t", index=False)
    write_report(output_dir / "temporal_panel_report.md", summary, calls, target_delta, structure)
    (output_dir / "run_manifest.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "report_root": output_dir,
        "summary": output_dir / "temporal_bridge_summary.tsv",
        "target_delta": output_dir / "temporal_target_delta.tsv",
        "structure": output_dir / "temporal_structure_summary.tsv",
        "calls": output_dir / "temporal_panel_calls.tsv",
        "report": output_dir / "temporal_panel_report.md",
        "manifest": output_dir / "run_manifest.json",
    }


def main() -> None:
    args = build_parser().parse_args()
    paths = run_from_config(Path(args.config))
    output_dir = paths["report_root"]
    print(f"[OK] wrote GSE90063 K562 temporal panel outputs to {output_dir}")


if __name__ == "__main__":
    main()
