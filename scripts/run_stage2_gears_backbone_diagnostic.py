from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/stage2/gears_backbone_diagnostic_v1.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成 GEARS HCC backbone 失败分解摘要。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="诊断配置 JSON 路径。")
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


def load_structure_score(detail_root: Path, model_id: str, cell_line: str) -> dict[str, float]:
    frame = pd.read_csv(detail_root / model_id / cell_line / "structure_scores.tsv", sep="\t")
    return frame.set_index("score_name")["score_value"].astype(float).to_dict()


def load_expression_summary(detail_root: Path, model_id: str, cell_line: str) -> dict[str, dict[str, float]]:
    frame = pd.read_csv(detail_root / model_id / cell_line / "expression_summary.tsv", sep="\t")
    summaries: dict[str, dict[str, float]] = {}
    for row in frame.to_dict(orient="records"):
        group_key = str(row["group_key"])
        summaries[group_key] = {
            "target_count": int(row["target_count"]),
            "cosine_similarity_mean": float(row["cosine_similarity_mean"]),
            "l2_distance_mean": float(row["l2_distance_mean"]),
            "top20_overlap_mean": float(row["top20_overlap_mean"]),
        }
    return summaries


def classify_failure_mode(
    *,
    backbone_cosine_gap: float,
    backbone_l2_gap: float,
    backbone_top20_gap: float,
    separation_gain: float,
    shift_excess_gain: float,
    thresholds: dict[str, object],
) -> tuple[str, bool, bool, bool]:
    direction_issue = backbone_cosine_gap >= float(thresholds["direction_cosine_gap_min"])
    amplitude_issue = (
        backbone_l2_gap >= float(thresholds["amplitude_l2_gap_min"])
        or backbone_top20_gap >= float(thresholds["amplitude_top20_gap_min"])
    )
    tradeoff_signal = (
        separation_gain >= float(thresholds["tradeoff_separation_gain_min"])
        or shift_excess_gain >= float(thresholds["tradeoff_shift_excess_gain_min"])
    )
    if tradeoff_signal and (direction_issue or amplitude_issue):
        return "tradeoff", direction_issue, amplitude_issue, tradeoff_signal
    if direction_issue and amplitude_issue:
        return "mixed", direction_issue, amplitude_issue, tradeoff_signal
    if direction_issue:
        return "direction", direction_issue, amplitude_issue, tradeoff_signal
    if amplitude_issue:
        return "amplitude", direction_issue, amplitude_issue, tradeoff_signal
    return "mixed", direction_issue, amplitude_issue, tradeoff_signal


def build_diagnostic_rows(config: dict[str, object]) -> pd.DataFrame:
    detail_root = resolve_path(str(config["detail_root"]))
    entrant_model_id = str(config["entrant_model_id"])
    reference_model_id = str(config["reference_model_id"])
    thresholds = dict(config["thresholds"])

    rows: list[dict[str, object]] = []
    for cell_line in config["cell_lines"]:
        cell_line = str(cell_line)
        entrant_scores = load_structure_score(detail_root, entrant_model_id, cell_line)
        reference_scores = load_structure_score(detail_root, reference_model_id, cell_line)
        entrant_expression = load_expression_summary(detail_root, entrant_model_id, cell_line)["canonical_backbone"]
        reference_expression = load_expression_summary(detail_root, reference_model_id, cell_line)["canonical_backbone"]

        backbone_cosine_gap = (
            reference_expression["cosine_similarity_mean"] - entrant_expression["cosine_similarity_mean"]
        )
        backbone_l2_gap = (
            entrant_expression["l2_distance_mean"] - reference_expression["l2_distance_mean"]
        )
        backbone_top20_gap = (
            reference_expression["top20_overlap_mean"] - entrant_expression["top20_overlap_mean"]
        )
        separation_gain = (
            entrant_scores["structure_vs_context_separation_score"]
            - reference_scores["structure_vs_context_separation_score"]
        )
        shift_excess_gain = (
            entrant_scores["shift_excess_identification_score"]
            - reference_scores["shift_excess_identification_score"]
        )
        failure_mode_call, direction_issue, amplitude_issue, tradeoff_signal = classify_failure_mode(
            backbone_cosine_gap=backbone_cosine_gap,
            backbone_l2_gap=backbone_l2_gap,
            backbone_top20_gap=backbone_top20_gap,
            separation_gain=separation_gain,
            shift_excess_gain=shift_excess_gain,
            thresholds=thresholds,
        )
        rows.append(
            {
                "cell_line": cell_line,
                "backbone_recovery_score": entrant_scores["backbone_recovery_score"],
                "backbone_cosine": entrant_expression["cosine_similarity_mean"],
                "backbone_L2": entrant_expression["l2_distance_mean"],
                "backbone_top20": entrant_expression["top20_overlap_mean"],
                "failure_mode_call": failure_mode_call,
                "direction_issue": direction_issue,
                "amplitude_issue": amplitude_issue,
                "tradeoff_signal": tradeoff_signal,
                "reference_backbone_recovery_score": reference_scores["backbone_recovery_score"],
                "reference_backbone_cosine": reference_expression["cosine_similarity_mean"],
                "reference_backbone_L2": reference_expression["l2_distance_mean"],
                "reference_backbone_top20": reference_expression["top20_overlap_mean"],
                "backbone_recovery_gap_vs_reference": (
                    entrant_scores["backbone_recovery_score"] - reference_scores["backbone_recovery_score"]
                ),
                "backbone_cosine_gap_vs_reference": -backbone_cosine_gap,
                "backbone_L2_gap_vs_reference": -backbone_l2_gap,
                "backbone_top20_gap_vs_reference": -backbone_top20_gap,
                "shift_excess_gain_vs_reference": shift_excess_gain,
                "separation_gain_vs_reference": separation_gain,
            }
        )
    return pd.DataFrame(rows)


def write_markdown_report(config: dict[str, object], summary: pd.DataFrame, output_path: Path) -> None:
    lines = [
        "# GEARS Backbone 诊断摘要",
        "",
        "## 定位",
        "",
        "- 这是 GEARS HCC primary mainline 在正式 recipe sweep 前的最小失败分解产物。",
        "- 它只服务于 `canonical_backbone recovery` 诊断，不引入新 entrant、新 truth object 或新评分体系。",
        "- sweep 必须基于这里的 `failure_mode_call` 才能启动。",
        "",
        "## 当前诊断",
        "",
    ]
    for row in summary.itertuples(index=False):
        lines.append(f"### {row.cell_line}")
        lines.append(
            f"- GEARS backbone：recovery = `{row.backbone_recovery_score:.3f}`；"
            f"cosine = `{row.backbone_cosine:.3f}`；"
            f"L2 = `{row.backbone_L2:.3f}`；"
            f"top-20 = `{row.backbone_top20:.3f}`。"
        )
        lines.append(
            f"- reference backbone：recovery = `{row.reference_backbone_recovery_score:.3f}`；"
            f"cosine = `{row.reference_backbone_cosine:.3f}`；"
            f"L2 = `{row.reference_backbone_L2:.3f}`；"
            f"top-20 = `{row.reference_backbone_top20:.3f}`。"
        )
        lines.append(
            f"- `failure_mode_call = {row.failure_mode_call}`；"
            f"`direction_issue = {str(bool(row.direction_issue)).lower()}`；"
            f"`amplitude_issue = {str(bool(row.amplitude_issue)).lower()}`；"
            f"`tradeoff_signal = {str(bool(row.tradeoff_signal)).lower()}`。"
        )
        lines.append("")
    lines.extend(
        [
            "## Sweep 边界",
            "",
            "- 允许变化：",
        ]
    )
    for item in config["allowed_sweep_axes"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "- 禁止变化：",
        ]
    )
    for item in config["disallowed_sweep_axes"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Stop Rule",
            "",
            "- 如果一轮有限 sweep 后，`canonical_backbone recovery` 仍不能接近或追平 `shared_mean_baseline`，且任何改进都以明显损失 `structure/context separation` 为代价，则停止继续把 `GEARS` 推为 HCC primary winner，并将当前结果收口为 architecture trade-off diagnosis。",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    config = load_json(resolve_path(args.config))
    output_root = resolve_path(str(config["output_root"]))
    output_root.mkdir(parents=True, exist_ok=True)

    summary = build_diagnostic_rows(config)
    summary.to_csv(output_root / "gears_backbone_diagnostic_summary.tsv", sep="\t", index=False)
    write_markdown_report(config, summary, output_root / "gears_backbone_diagnostic_summary.md")

    print(f"已写出: {output_root / 'gears_backbone_diagnostic_summary.tsv'}")
    print(f"已写出: {output_root / 'gears_backbone_diagnostic_summary.md'}")


if __name__ == "__main__":
    main()
