from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from wtbench.model_structure_scorer import (
    DEFAULT_AXIS_MEMBERSHIP_PATH,
    DEFAULT_TRUTH_CONTRACT_PATH,
    load_tsv,
    project_prediction_to_axes,
    summarize_structure_scores,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports/stage2_model_structure_smoke"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage 2 HCC structure scorer smoke。")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--truth-contract-path", default=str(DEFAULT_TRUTH_CONTRACT_PATH))
    parser.add_argument("--axis-membership-path", default=str(DEFAULT_AXIS_MEMBERSHIP_PATH))
    return parser


def build_smoke_prediction_matrices(axis_membership: pd.DataFrame) -> dict[str, pd.DataFrame]:
    target_order = sorted(axis_membership["target_gene"].astype(str).unique().tolist())
    gene_order = target_order
    membership = (
        axis_membership.loc[:, ["target_gene", "fine_axis"]]
        .drop_duplicates()
        .assign(value=1.0)
    )
    axis_targets = {
        fine_axis: sorted(group["target_gene"].astype(str).tolist())
        for fine_axis, group in membership.groupby("fine_axis", sort=True)
    }
    expected_axis = (
        axis_membership.loc[:, ["target_gene", "fine_axis"]]
        .drop_duplicates()
        .rename(columns={"fine_axis": "expected_axis"})
    )
    truth_contract = load_tsv(DEFAULT_TRUTH_CONTRACT_PATH)
    expected_axis = expected_axis.merge(
        truth_contract.loc[:, ["fine_axis", "architecture_role"]].rename(
            columns={"fine_axis": "expected_axis"}
        ),
        on="expected_axis",
        how="left",
        validate="many_to_one",
    )
    axis_templates: dict[str, pd.Series] = {}
    for fine_axis, targets in axis_targets.items():
        series = pd.Series(0.0, index=gene_order, dtype=float)
        series.loc[targets] = 1.0
        axis_templates[fine_axis] = series

    backbone_axes = truth_contract.loc[
        truth_contract["architecture_role"].eq("canonical_backbone"),
        "fine_axis",
    ].astype(str).tolist()
    if not backbone_axes:
        raise ValueError("smoke 需要至少一个 canonical_backbone axis。")
    backbone_template = pd.concat(
        [axis_templates[axis] for axis in backbone_axes],
        axis=1,
    ).mean(axis=1)

    null_records: list[dict[str, float | str]] = []
    mean_records: list[dict[str, float | str]] = []
    oracle_records: list[dict[str, float | str]] = []
    for row in expected_axis.itertuples(index=False):
        target_gene = str(row.target_gene)
        expected = str(row.expected_axis)
        role = str(row.architecture_role)
        null_record = {"target_gene": target_gene, **{gene: 0.0 for gene in gene_order}}
        mean_record = {"target_gene": target_gene, **backbone_template.to_dict()}
        oracle_scale = 2.0 if role == "shift_excess" else 1.0
        oracle_record = {
            "target_gene": target_gene,
            **(axis_templates[expected] * oracle_scale).to_dict(),
        }
        null_records.append(null_record)
        mean_records.append(mean_record)
        oracle_records.append(oracle_record)

    return {
        "null_model": pd.DataFrame(null_records),
        "shared_mean_baseline": pd.DataFrame(mean_records),
        "oracle_structure_positive_control": pd.DataFrame(oracle_records),
    }


def render_smoke_report(summary: pd.DataFrame, output_path: Path) -> None:
    ordered = summary.sort_values("model_rank", ascending=True).reset_index(drop=True)
    lines = [
        "# Stage 2 HCC Structure Scorer Smoke",
        "",
        "## 定位",
        "",
        "- 这是 scorer contract smoke，不是真实 entrant adjudication。",
        "- 本轮只验证 scorer 是否能稳定区分 `null`、`shared mean baseline`、`oracle structure positive control` 三类状态。",
        "- 真实 HCC entrant smoke 仍需等待 HCC aligned prediction 输入到位。",
        "",
        "## 结果",
        "",
    ]
    for row in ordered.itertuples(index=False):
        lines.append(f"### {row.model_id}")
        lines.append(
            f"- backbone recovery = `{row.backbone_recovery_score:.3f}`；"
            f"shift-excess identification = `{row.shift_excess_identification_score:.3f}`；"
            f"structure-vs-context separation = `{row.structure_vs_context_separation_score:.3f}`。"
        )
        lines.append(f"- composite score = `{row.composite_score:.3f}`；rank = `{int(row.model_rank)}`。")
        lines.append("")
    lines.extend(
        [
            "## 结论边界",
            "",
            "- 若 oracle 明显高于 shared mean，且 shared mean 明显高于 null，说明 scorer 至少具备基本区分力。",
            "- 这一步只关闭“scorer 是否可用”的 smoke 风险，不关闭真实 entrant 的 architecture recovery 结论。",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    truth_contract = load_tsv(Path(args.truth_contract_path))
    axis_membership = load_tsv(Path(args.axis_membership_path))
    smoke_predictions = build_smoke_prediction_matrices(axis_membership)

    summary_rows: list[dict[str, object]] = []
    for model_id, prediction in smoke_predictions.items():
        projected = project_prediction_to_axes(
            prediction=prediction,
            axis_membership=axis_membership,
            truth_contract=truth_contract,
        )
        scores = summarize_structure_scores(projected)
        score_map = dict(zip(scores["score_name"], scores["score_value"]))
        composite = float(np.nanmean(scores["score_value"].to_numpy(dtype=float)))
        model_dir = output_dir / model_id
        model_dir.mkdir(parents=True, exist_ok=True)
        prediction.to_csv(model_dir / "predicted_shift_smoke.tsv.gz", sep="\t", index=False)
        projected.to_csv(model_dir / "projected_architecture.tsv", sep="\t", index=False)
        scores.to_csv(model_dir / "structure_scores.tsv", sep="\t", index=False)
        summary_rows.append(
            {
                "model_id": model_id,
                **score_map,
                "composite_score": composite,
            }
        )

    summary = pd.DataFrame(summary_rows).sort_values("composite_score", ascending=False).reset_index(drop=True)
    summary["model_rank"] = np.arange(1, len(summary) + 1, dtype=int)
    summary.to_csv(output_dir / "smoke_summary.tsv", sep="\t", index=False)
    (output_dir / "smoke_summary.json").write_text(
        json.dumps(summary.to_dict(orient="records"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    render_smoke_report(summary, output_dir / "smoke_report.md")


if __name__ == "__main__":
    main()
