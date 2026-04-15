from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/stage2/k562_rnai_endpoint_consistency_v1.json"


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_recipe(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def aligned_endpoint_values(frame: pd.DataFrame, column: str) -> pd.Series:
    if column.endswith("depmap_gene_effect"):
        return -frame[column]
    return frame[column]


def require_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"缺少输入文件: {path}")


def load_bridge(path: Path, prefix: str, truth_metrics: list[str], endpoints: list[str]) -> pd.DataFrame:
    require_path(path)
    columns = ["target_gene", *truth_metrics, *endpoints, "depmap_join_status"]
    frame = pd.read_csv(path, sep="\t", usecols=columns)
    return frame.rename(
        columns={
            **{metric: f"{prefix}_{metric}" for metric in truth_metrics},
            **{endpoint: f"{prefix}_{endpoint}" for endpoint in endpoints},
            "depmap_join_status": f"{prefix}_depmap_join_status",
        }
    )


def build_target_table(
    label: str,
    role: str,
    crispr: pd.DataFrame,
    rnai: pd.DataFrame,
    truth_metrics: list[str],
    endpoints: list[str],
) -> pd.DataFrame:
    merged = crispr.merge(rnai, on="target_gene", how="outer", indicator="platform_join_status")
    merged.insert(0, "role", role)
    merged.insert(0, "timepoint", label)
    for endpoint in endpoints:
        crispr_col = f"crispr_{endpoint}"
        rnai_col = f"rnai_{endpoint}"
        merged[f"crispr_aligned_{endpoint}"] = aligned_endpoint_values(merged, crispr_col)
        merged[f"rnai_aligned_{endpoint}"] = aligned_endpoint_values(merged, rnai_col)
        merged[f"delta_rnai_minus_crispr_aligned_{endpoint}"] = (
            merged[f"rnai_aligned_{endpoint}"] - merged[f"crispr_aligned_{endpoint}"]
        )
    for metric in truth_metrics:
        crispr_metric = f"crispr_{metric}"
        rnai_metric = f"rnai_{metric}"
        merged[f"delta_rnai_minus_crispr_{metric}"] = merged[rnai_metric] - merged[crispr_metric]
    return merged.sort_values(["timepoint", "target_gene"]).reset_index(drop=True)


def summarize_timepoint(
    target_table: pd.DataFrame,
    truth_metrics: list[str],
    endpoints: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (label, role), group in target_table.groupby(["timepoint", "role"], sort=False):
        for endpoint in endpoints:
            endpoint_subset = group.loc[
                :, ["target_gene", f"crispr_aligned_{endpoint}", f"rnai_aligned_{endpoint}"]
            ].dropna()
            endpoint_corr = endpoint_subset[f"crispr_aligned_{endpoint}"].corr(
                endpoint_subset[f"rnai_aligned_{endpoint}"],
                method="spearman",
            )
            rows.append(
                {
                    "timepoint": label,
                    "role": role,
                    "summary_kind": "endpoint_consistency",
                    "truth_metric": "",
                    "depmap_endpoint": endpoint,
                    "platform_pair": "CRISPR_DepMap_vs_DEMETER2_RNAi",
                    "n_shared_targets": int(len(endpoint_subset)),
                    "spearman": float(endpoint_corr) if not pd.isna(endpoint_corr) else pd.NA,
                    "interpretation": "CRISPR DepMap 是 matched primary endpoint；DEMETER2 RNAi 是 cross-platform sensitivity endpoint。",
                }
            )
            for truth_metric in truth_metrics:
                for platform in ["crispr", "rnai"]:
                    truth_col = f"{platform}_{truth_metric}"
                    endpoint_col = f"{platform}_aligned_{endpoint}"
                    subset = group.loc[:, ["target_gene", truth_col, endpoint_col]].dropna()
                    rho = subset[truth_col].corr(subset[endpoint_col], method="spearman")
                    rows.append(
                        {
                            "timepoint": label,
                            "role": role,
                            "summary_kind": "truth_endpoint_bridge",
                            "truth_metric": truth_metric,
                            "depmap_endpoint": endpoint,
                            "platform_pair": platform,
                            "n_shared_targets": int(len(subset)),
                            "spearman": float(rho) if not pd.isna(rho) else pd.NA,
                            "interpretation": "RNAi 不替代 CRISPR 主线，也不提供等价 primary evidence。",
                        }
                    )
    return pd.DataFrame(rows)


def build_calls(summary: pd.DataFrame, primary_truth_metric: str, primary_endpoint: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for label, group in summary.groupby("timepoint", sort=False):
        endpoint = group.loc[
            group["summary_kind"].eq("endpoint_consistency")
            & group["depmap_endpoint"].eq(primary_endpoint)
        ]
        bridges = group.loc[
            group["summary_kind"].eq("truth_endpoint_bridge")
            & group["truth_metric"].eq(primary_truth_metric)
            & group["depmap_endpoint"].eq(primary_endpoint)
        ]
        values = dict(zip(bridges["platform_pair"], bridges["spearman"], strict=False))
        crispr = values.get("crispr", pd.NA)
        rnai = values.get("rnai", pd.NA)
        if pd.isna(rnai):
            bridge_call = "rnai_not_evaluable"
        elif pd.isna(crispr):
            bridge_call = "crispr_not_evaluable"
        elif rnai == crispr:
            bridge_call = "rnai_bridge_tied_with_crispr"
        elif rnai > crispr:
            bridge_call = "rnai_bridge_stronger_than_crispr_sensitivity"
        else:
            bridge_call = "rnai_bridge_weaker_than_crispr_sensitivity"
        rows.append(
            {
                "timepoint": label,
                "primary_truth_metric": primary_truth_metric,
                "primary_depmap_endpoint": primary_endpoint,
                "crispr_truth_endpoint_spearman": crispr,
                "rnai_truth_endpoint_spearman": rnai,
                "crispr_vs_rnai_endpoint_spearman": endpoint["spearman"].iloc[0] if not endpoint.empty else pd.NA,
                "sensitivity_call": bridge_call,
                "allowed_wording": "CRISPR DepMap = matched primary endpoint; RNAi DEMETER2 = cross-platform sensitivity endpoint.",
                "disallowed_wording": "RNAi 替代 CRISPR 主线；RNAi 提供等价 primary evidence。",
            }
        )
    return pd.DataFrame(rows)


def write_report(path: Path, summary: pd.DataFrame, calls: pd.DataFrame, stage_name: str = "K562") -> None:
    lines = [
        f"# {stage_name} RNAi endpoint consistency",
        "",
        "## 定位",
        "",
        "- CRISPR DepMap = matched primary endpoint。",
        "- RNAi DEMETER2 = cross-platform sensitivity endpoint。",
        "- RNAi 不替代 CRISPR 主线，也不提供等价 primary evidence。",
        "",
        "## Primary readout",
        "",
    ]
    for row in calls.to_dict("records"):
        lines.append(
            f"- `{row['timepoint']}`：CRISPR bridge Spearman = `{row['crispr_truth_endpoint_spearman']}`；RNAi bridge Spearman = `{row['rnai_truth_endpoint_spearman']}`；CRISPR vs RNAi endpoint Spearman = `{row['crispr_vs_rnai_endpoint_spearman']}`；call = `{row['sensitivity_call']}`。"
        )
    lines.extend(
        [
            "",
            "## 产物",
            "",
            "- `endpoint_consistency_summary.tsv`",
            "- `endpoint_consistency_calls.tsv`",
            "- `endpoint_consistency_target_table.tsv`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="汇总 K562 7d/13d CRISPR DepMap vs RNAi DEMETER2 endpoint consistency。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    return parser


def run_from_config(config_path: Path) -> dict[str, Path]:
    recipe = load_recipe(resolve_path(config_path))
    metrics = dict(recipe["metrics"])
    truth_metrics = [str(value) for value in metrics["truth_metrics"]]
    endpoints = [str(value) for value in metrics["depmap_endpoints"]]
    primary_truth_metric = str(metrics["primary_truth_metric"])
    primary_endpoint = str(metrics["primary_depmap_endpoint"])
    output_dir = resolve_path(str(recipe["output"]["report_root"]))
    output_dir.mkdir(parents=True, exist_ok=True)

    # 支持 timepoints（K562）和 cell_lines（HCC）两种结构
    items = recipe.get("timepoints", recipe.get("cell_lines"))

    target_tables = []
    for item in items:
        label = str(item["label"])
        role = str(item["role"])
        crispr = load_bridge(resolve_path(str(item["crispr_bridge_table_path"])), "crispr", truth_metrics, endpoints)
        rnai = load_bridge(resolve_path(str(item["rnai_bridge_table_path"])), "rnai", truth_metrics, endpoints)
        target_tables.append(build_target_table(label, role, crispr, rnai, truth_metrics, endpoints))

    target_table = pd.concat(target_tables, ignore_index=True)
    summary = summarize_timepoint(target_table, truth_metrics, endpoints)
    calls = build_calls(summary, primary_truth_metric, primary_endpoint)

    target_table.to_csv(output_dir / "endpoint_consistency_target_table.tsv", sep="\t", index=False)
    summary.to_csv(output_dir / "endpoint_consistency_summary.tsv", sep="\t", index=False)
    calls.to_csv(output_dir / "endpoint_consistency_calls.tsv", sep="\t", index=False)
    stage_name = str(recipe.get("stage", "K562"))
    write_report(output_dir / "endpoint_consistency_report.md", summary, calls, stage_name=stage_name)
    (output_dir / "run_manifest.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "report_root": output_dir,
        "target_table": output_dir / "endpoint_consistency_target_table.tsv",
        "summary": output_dir / "endpoint_consistency_summary.tsv",
        "calls": output_dir / "endpoint_consistency_calls.tsv",
        "report": output_dir / "endpoint_consistency_report.md",
        "manifest": output_dir / "run_manifest.json",
    }


def main() -> None:
    args = build_parser().parse_args()
    paths = run_from_config(Path(args.config))
    stage_name = load_recipe(resolve_path(args.config)).get("stage", "K562")
    output_dir = paths["report_root"]
    print(f"[OK] wrote {stage_name} RNAi endpoint consistency outputs to {output_dir}")


if __name__ == "__main__":
    main()
