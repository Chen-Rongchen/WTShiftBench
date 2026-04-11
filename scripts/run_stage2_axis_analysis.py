from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/stage2/axis_analysis_template_v1.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="初始化 Stage 2 axis annotation / validation 标准输出目录。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="axis analysis 配置 JSON 路径。")
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload


def require_fields(payload: dict[str, object], key: str, required_fields: list[str]) -> None:
    block = payload.get(key)
    if not isinstance(block, dict):
        raise ValueError(f"{key} 必须是 JSON 对象。")
    missing = [field for field in required_fields if field not in block]
    if missing:
        raise ValueError(f"{key} 缺少字段: {missing}")


def validate_config(config: dict[str, object]) -> None:
    required_top_level = [
        "stage",
        "version",
        "purpose",
        "input_objects",
        "analysis_scope",
        "required_intermediate_objects",
        "annotation",
        "validation",
        "final_summary",
        "governance",
        "output",
    ]
    missing = [field for field in required_top_level if field not in config]
    if missing:
        raise ValueError(f"配置缺少字段: {missing}")

    require_fields(
        config,
        "input_objects",
        [
            "truth_bridge_report_root",
            "truth_bridge_data_root",
            "axis_membership_path",
            "axis_loading_path",
            "target_level_bridge_table_path",
            "axis_summary_fine_path",
            "axis_summary_macro_path",
            "axis_crossline_consistency_path",
        ],
    )
    require_fields(config, "analysis_scope", ["dataset_role", "cell_lines", "axis_families"])
    require_fields(config, "required_intermediate_objects", ["axis_membership", "axis_gene_signature", "per_target_signature"])
    require_fields(config, "annotation", ["databases", "output_fields"])
    require_fields(config, "validation", ["methods", "output_fields"])
    require_fields(config, "final_summary", ["required_fields", "allowed_final_calls"])
    require_fields(config, "governance", ["disallowed_practices", "recommended_execution_order"])
    require_fields(config, "output", ["report_root", "expected_tables"])


def build_empty_frame(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def build_axis_membership_frame(config: dict[str, object]) -> pd.DataFrame:
    input_objects = dict(config["input_objects"])
    membership_path = resolve_path(str(input_objects["axis_membership_path"]))
    frame = pd.read_csv(membership_path, sep="\t")
    renamed = frame.rename(
        columns={
            "fine_axis": "axis_id",
            "macro_axis": "axis_family",
            "annotation_confidence": "evidence_tier",
            "evidence_note": "annotation_note",
        }
    ).copy()
    renamed["membership_weight"] = 1.0
    renamed["cell_line_scope"] = "HCC38|HCC1143"
    return renamed.loc[
        :,
        [
            "axis_id",
            "axis_family",
            "target_gene",
            "membership_weight",
            "cell_line_scope",
            "evidence_tier",
        ],
    ].sort_values(["axis_family", "axis_id", "target_gene"]).reset_index(drop=True)


def build_axis_summary_frame(config: dict[str, object]) -> pd.DataFrame:
    input_objects = dict(config["input_objects"])
    fine = pd.read_csv(resolve_path(str(input_objects["axis_summary_fine_path"])), sep="\t")
    macro = pd.read_csv(resolve_path(str(input_objects["axis_summary_macro_path"])), sep="\t")
    consistency = pd.read_csv(resolve_path(str(input_objects["axis_crossline_consistency_path"])), sep="\t")

    summary = fine.merge(
        consistency.loc[:, ["fine_axis", "consistency_class"]],
        on="fine_axis",
        how="left",
    ).rename(
        columns={
            "fine_axis": "axis_id",
            "macro_axis": "axis_label",
            "dominant_tier": "structure_support",
            "consistency_class": "consistency_support",
        }
    )
    available_macro_axes = set(macro["macro_axis"].astype(str))
    summary["annotation_support"] = summary["axis_label"].astype(str).map(
        lambda axis_label: "macro_axis_summary_available" if axis_label in available_macro_axes else "missing_macro_axis_summary"
    )
    summary["external_knowledge_support"] = "frozen_annotation_note_available"
    summary["final_call"] = "partially_supported_axis"
    return summary.loc[
        :,
        [
            "axis_id",
            "axis_label",
            "structure_support",
            "annotation_support",
            "consistency_support",
            "external_knowledge_support",
            "final_call",
        ],
    ].sort_values(["axis_label", "axis_id"]).reset_index(drop=True)


def build_axis_gene_signature_seed_frame(config: dict[str, object]) -> pd.DataFrame:
    input_objects = dict(config["input_objects"])
    membership = build_axis_membership_frame(config)
    atlas_path = resolve_path(str(input_objects["truth_bridge_report_root"])) / "master_atlas" / "shared_target_master_atlas.tsv"
    atlas = pd.read_csv(atlas_path, sep="\t")
    merged = membership.merge(
        atlas.loc[:, ["target_gene", "shift_mean", "liability_mean", "residual_mean", "priority_tier"]],
        on="target_gene",
        how="left",
    )
    merged["axis_score"] = merged["shift_mean"].astype(float)
    merged["direction"] = "positive_shift_mean_seed"
    merged["rank"] = (
        merged.groupby("axis_id")["axis_score"]
        .rank(method="first", ascending=False)
        .astype(int)
    )
    return merged.rename(columns={"target_gene": "gene"}).loc[
        :,
        ["axis_id", "gene", "axis_score", "rank", "direction"],
    ].sort_values(["axis_id", "rank", "gene"]).reset_index(drop=True)


def write_tables(config: dict[str, object], report_root: Path) -> list[str]:
    intermediate = dict(config["required_intermediate_objects"])
    annotation = dict(config["annotation"])
    validation = dict(config["validation"])
    final_summary = dict(config["final_summary"])

    table_frames: dict[str, pd.DataFrame] = {
        "axis_membership.tsv": build_axis_membership_frame(config),
        "axis_gene_signature.tsv": build_axis_gene_signature_seed_frame(config).loc[
            :,
            list(intermediate["axis_gene_signature"]["required_fields"])
        ],
        "axis_target_consistency.tsv": build_empty_frame(list(validation["output_fields"])),
        "axis_enrichment.tsv": build_empty_frame(list(annotation["output_fields"])),
        "axis_summary.tsv": build_axis_summary_frame(config).loc[:, list(final_summary["required_fields"])],
    }
    written: list[str] = []
    for name in config["output"]["expected_tables"]:
        name = str(name)
        frame = table_frames.get(name, build_empty_frame([]))
        output_path = report_root / name
        if output_path.exists() and name in {"axis_enrichment.tsv", "axis_target_consistency.tsv"}:
            written.append(name)
            continue
        frame.to_csv(output_path, sep="\t", index=False)
        written.append(name)
    return written


def write_readme(config: dict[str, object], report_root: Path, written_tables: list[str]) -> None:
    lines = [
        "# Stage 2 Axis Analysis 输出说明",
        "",
        "## 定位",
        "",
        "- 这是 Stage 2 frozen axis 的 annotation / validation 标准输出目录。",
        "- 当前脚本负责读取配置、校验字段并物化基础表；后续 enrichment 或 consistency audit 可在此目录继续追加。",
        "- axis discovery 仍必须先于这里发生；这里不允许用 enrichment 单独定义 axis。",
        "",
        "## 当前配置范围",
        "",
        f"- dataset_role = `{config['analysis_scope']['dataset_role']}`",
        f"- cell_lines = `{', '.join(str(item) for item in config['analysis_scope']['cell_lines'])}`",
        f"- axis_families = `{', '.join(str(item) for item in config['analysis_scope']['axis_families'])}`",
        "",
        "## 推荐执行顺序",
        "",
    ]
    for item in config["governance"]["recommended_execution_order"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## 当前标准输出表",
            "",
        ]
    )
    for item in written_tables:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## 当前已自动物化的真实对象",
            "",
            "- `axis_membership.tsv`：已从 frozen `shared_target_axis_membership.tsv` 物化。",
            "- `axis_gene_signature.tsv`：已从 frozen `shared_target_master_atlas.tsv` 物化出第一版 target-seed ranking。",
            "- `axis_summary.tsv`：已从 frozen `axis_summary_fine.tsv`、`axis_summary_macro.tsv` 与 `axis_crossline_consistency.tsv` 物化。",
            "- 当前 `axis_gene_signature.tsv` 还是 target-seed 骨架，不等于最终 gene-level enrichment signature。",
            "",
            "## 当前解释边界",
            "",
            "- `axis_enrichment.tsv` 若已由独立 runner 生成，则它只提供第一版 annotation 线索，不单独充当 axis definition 证据。",
            "- `axis_target_consistency.tsv` 只有在真实 per-target signature 到位后才应物化，当前不应伪造。",
            "",
            "## 治理边界",
            "",
        ]
    )
    for item in config["governance"]["disallowed_practices"]:
        lines.append(f"- `{item}`")
    (report_root / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    config_path = resolve_path(args.config)
    config = load_json(config_path)
    validate_config(config)

    report_root = resolve_path(str(config["output"]["report_root"]))
    report_root.mkdir(parents=True, exist_ok=True)
    written_tables = write_tables(config, report_root)
    write_readme(config, report_root, written_tables)

    summary = {
        "stage": str(config["stage"]),
        "config_path": str(config_path.relative_to(PROJECT_ROOT)),
        "report_root": str(report_root.relative_to(PROJECT_ROOT)),
        "initialized_tables": written_tables,
        "initialized_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (report_root / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
