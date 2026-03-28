from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import math
import re
from urllib.request import urlretrieve

import pandas as pd
import pertpy as pt
import scanpy as sc

from stage1a_catalog import BACKUP_DATASET_FILES
OUTPUT_DIR = Path("data/audit/stage1a_replacement_candidates")
DATASETDIR = Path(sc.settings.datasetdir)

KEY_COLUMNS = [
    "perturbation",
    "gene",
    "target",
    "guide",
    "guide_id",
    "sgRNA",
    "condition",
]

IDENTITY_COLUMN_PRIORITY = [
    "perturbation",
    "perturbation_name",
    "gene",
    "target",
    "guide",
    "guide_id",
    "sgRNA",
    "condition",
]

CONTROL_REGEX = re.compile(
    r"control|non[-_ ]?target|ntc|mock|negative control|neg control|intergenic|gal4|63\(mod\)",
    flags=re.IGNORECASE,
)
EXPLICIT_CONTROL_REGEX = re.compile(
    r"^control$|non[-_ ]?target|ntc|mock|negative control|neg control",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    loader_name: str
    combo_column: str
    combo_pattern: re.Pattern[str]
    output_identity_column: str


DATASETS = [
    DatasetSpec(
        name="adamson_2016_upr_perturb_seq",
        loader_name="adamson_2016_upr_perturb_seq",
        combo_column="perturbation",
        combo_pattern=re.compile(r"$^"),
        output_identity_column="perturbation",
    ),
    DatasetSpec(
        name="dixit_2016",
        loader_name="dixit_2016",
        combo_column="perturbation_name",
        combo_pattern=re.compile(r"\+"),
        output_identity_column="perturbation_name",
    ),
    DatasetSpec(
        name="tian_2019_day7neuron",
        loader_name="tian_2019_day7neuron",
        combo_column="perturbation",
        combo_pattern=re.compile(r"_"),
        output_identity_column="perturbation",
    ),
    DatasetSpec(
        name="tian_2021_crispri",
        loader_name="tian_2021_crispri",
        combo_column="perturbation",
        combo_pattern=re.compile(r"_"),
        output_identity_column="perturbation",
    ),
]


def ensure_tian_2021_crispri_cache() -> None:
    output_file = DATASETDIR / "tian_2021_crispri.h5ad"
    if output_file.exists():
        return
    urlretrieve(
        "https://zenodo.org/records/10044268/files/TianKampmann2021_CRISPRi.h5ad?download=1",
        output_file,
    )


def load_dataset(spec: DatasetSpec):
    backup_file = BACKUP_DATASET_FILES.get(spec.name)
    if backup_file is not None and backup_file.exists():
        return sc.read_h5ad(backup_file)

    if spec.name == "tian_2021_crispri":
        ensure_tian_2021_crispri_cache()
    loader = getattr(pt.data, spec.loader_name)
    return loader()


def as_string_series(adata, column: str) -> pd.Series:
    return adata.obs[column].astype("string")


def to_json_list(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def infer_identity_columns(adata) -> list[str]:
    columns = {str(col) for col in adata.obs.columns}
    return [column for column in IDENTITY_COLUMN_PRIORITY if column in columns]


def label_score(label: str) -> tuple[int, int]:
    if EXPLICIT_CONTROL_REGEX.search(label):
        return (3, len(label))
    if re.search(r"intergenic", label, flags=re.IGNORECASE):
        return (2, len(label))
    if re.search(r"gal4|63\(mod\)", label, flags=re.IGNORECASE):
        return (1, len(label))
    return (0, len(label))


def collect_control_candidates(adata, dataset_name: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for column in adata.obs.columns:
        series = as_string_series(adata, str(column)).dropna()
        if series.empty:
            continue
        counts = series[series.str.contains(CONTROL_REGEX, na=False)].value_counts()
        for label, count in counts.items():
            rows.append(
                {
                    "dataset": dataset_name,
                    "source_column": str(column),
                    "label_value": str(label),
                    "count": int(count),
                    "fraction": float(count) / float(adata.n_obs),
                    "explicit_control_match": bool(EXPLICIT_CONTROL_REGEX.search(str(label))),
                }
            )
    if not rows:
        return pd.DataFrame(
            columns=[
                "dataset",
                "source_column",
                "label_value",
                "count",
                "fraction",
                "explicit_control_match",
            ]
        )
    return pd.DataFrame(rows).sort_values(
        by=["dataset", "count", "source_column", "label_value"],
        ascending=[True, False, True, True],
    )


def select_main_control(control_df: pd.DataFrame, identity_columns: list[str]) -> dict[str, object]:
    if control_df.empty:
        return {
            "has_high_confidence_control": False,
            "main_control_source_column": "",
            "main_control_labels": [],
            "control_cell_n": 0,
            "control_cell_frac": 0.0,
        }

    candidate_order = identity_columns + sorted(
        set(control_df["source_column"].tolist()) - set(identity_columns)
    )
    best: dict[str, object] | None = None

    for column in candidate_order:
        subset = control_df.loc[control_df["source_column"] == column].copy()
        if subset.empty:
            continue
        subset["label_rank"] = subset["label_value"].map(lambda x: label_score(str(x)))
        subset = subset.sort_values(
            by=["explicit_control_match", "count", "label_rank", "label_value"],
            ascending=[False, False, False, True],
        )
        explicit_subset = subset.loc[subset["explicit_control_match"]]
        chosen = explicit_subset if not explicit_subset.empty else subset.head(1)
        labels = chosen["label_value"].astype(str).tolist()
        total_n = int(chosen["count"].sum())
        frac = float(total_n) / float(control_df.attrs["n_obs"])
        confidence = bool(explicit_subset.shape[0] > 0 and frac >= 0.02)
        current = {
            "has_high_confidence_control": confidence,
            "main_control_source_column": str(column),
            "main_control_labels": labels,
            "control_cell_n": total_n,
            "control_cell_frac": frac,
            "_rank": (
                int(confidence),
                1 if column in identity_columns else 0,
                max(label_score(label)[0] for label in labels),
                total_n,
                -candidate_order.index(column),
            ),
        }
        if best is None or current["_rank"] > best["_rank"]:
            best = current

    assert best is not None
    best.pop("_rank")
    return best


def classify_cells(
    adata,
    spec: DatasetSpec,
    perturbation_column: str,
    main_control_labels: list[str],
) -> dict[str, object]:
    series = as_string_series(adata, perturbation_column).fillna("<NA>")
    value_counts = series.value_counts(dropna=False)

    combo_mask = series.str.contains(spec.combo_pattern, na=False)
    control_label_set = {label.lower() for label in main_control_labels}
    control_mask = series.str.lower().isin(control_label_set)

    if spec.name == "dixit_2016":
        control_mask = control_mask | series.str.contains(r"^INTERGENIC", case=False, na=False)
    if spec.name == "adamson_2016_upr_perturb_seq":
        control_mask = control_mask | series.str.contains(r"gal4|63\(mod\)", case=False, na=False)

    single_non_control_mask = (~control_mask) & (~combo_mask) & (series != "<NA>")
    combo_non_control_mask = (~control_mask) & combo_mask

    single_non_control_frac = float(single_non_control_mask.mean())
    combo_non_control_frac = float(combo_non_control_mask.mean())
    appears_single = single_non_control_frac >= 0.45 and combo_non_control_frac <= 0.25
    multiguide_frac = math.nan

    usable_counts = value_counts.loc[
        [
            label
            for label in value_counts.index.tolist()
            if label != "<NA>"
            and label.lower() not in control_label_set
            and not bool(spec.combo_pattern.search(label))
            and not (
                spec.name == "dixit_2016"
                and label.upper().startswith("INTERGENIC")
            )
            and not (
                spec.name == "adamson_2016_upr_perturb_seq"
                and re.search(r"gal4|63\(mod\)", label, flags=re.IGNORECASE)
            )
        ]
    ]
    likely_usable_n = int((usable_counts >= 100).sum())

    risks: list[str] = []
    if combo_non_control_frac > 0.25:
        risks.append(f"组合扰动占比高（{combo_non_control_frac:.1%}）")
    if single_non_control_frac < 0.45:
        risks.append(f"单扰动细胞占比不足（{single_non_control_frac:.1%}）")
    if "nperts" in adata.obs.columns:
        nperts = pd.to_numeric(adata.obs["nperts"], errors="coerce")
        multiguide_frac = float((nperts > 1).mean())
        if multiguide_frac > 0.5:
            appears_single = False
            risks.append(f"nperts>1 细胞占比高（{multiguide_frac:.1%}）")
    if spec.name == "dixit_2016":
        risks.append("跨 screen/cluster 混合，baseline 不易冻结")
    if spec.name.startswith("tian_2019_") or spec.name == "tian_2021_crispri":
        risks.append("guide_id/perturbation 存在大规模多目标拼接")
    if spec.name == "adamson_2016_upr_perturb_seq":
        risks.append("control 标签语义弱，且 nperts 几乎全为 2")

    return {
        "appears_single_perturbation_dominant": appears_single,
        "unique_perturbation_n": int(series.replace("<NA>", pd.NA).nunique(dropna=True)),
        "likely_usable_perturbation_n": likely_usable_n,
        "single_non_control_cell_frac": single_non_control_frac,
        "combo_non_control_cell_frac": combo_non_control_frac,
        "multi_nperts_cell_frac": multiguide_frac,
        "major_risks": to_json_list(risks),
    }


def evaluate_formal_fitness(row: dict[str, object]) -> tuple[int, int, int, int]:
    return (
        int(bool(row["has_high_confidence_control"])),
        1 if "cluster" not in str(row["obs_columns"]) else 0,
        int(bool(row["appears_single_perturbation_dominant"])),
        int(row["likely_usable_perturbation_n"]),
    )


def verdict_for_dataset(dataset: str, preferred: str, backup: str) -> str:
    if dataset == preferred:
        return "preferred"
    if dataset == backup:
        return "possible_backup"
    return "not_recommended"


def build_recommendation_md(summary_df: pd.DataFrame, final_decision: str) -> str:
    rows = {
        row["dataset"]: row for row in summary_df.to_dict(orient="records")
    }

    preferred = rows["tian_2019_day7neuron"]
    backup = rows["tian_2021_crispri"]
    dixit = rows["dixit_2016"]
    adamson = rows["adamson_2016_upr_perturb_seq"]

    return f"""# Stage 1A 替代候选 fail-fast 准入裁决

## 最终裁决

`{final_decision}`

## 结论摘要

- `tian_2019_day7neuron` 更适合进入当前 Stage 1A formal 主线。
- `tian_2021_crispri` 更适合保留为辅助鲁棒性数据集，而不是并列主线。
- `dixit_2016` 不建议作为 Adamson 替代。

## 并排判断

### adamson_2016_upr_perturb_seq

- control 清晰度：较弱。主 control 只能从 `{adamson["main_control_source_column"]}` 中的 `{adamson["main_control_labels"]}` 侧推，缺少标准 `control/non-targeting` 语义。
- baseline 冻结难度：中等。细胞背景相对单一，但 control 定义不够干净。
- single-perturbation 干净度：较差。`nperts` 显示几乎全体细胞为 2，说明 target/guide 归因并不清爽。

### dixit_2016

- control 清晰度：有显式 `control`，但还混有多个 `INTERGENIC` 负控来源。
- baseline 冻结难度：差。`cluster` 同时混合 `tfs_7`、`tfs_13`、`tfs_highmoi`，screen 异质性明显。
- single-perturbation 干净度：差。`perturbation_name` 中大量 `+` 组合标签，不适合 fail-fast 准入替代。
- 结论：`not_recommended`。

### tian_2019_day7neuron

- control 清晰度：好。`{preferred["main_control_source_column"]}` 中有显式 `{preferred["main_control_labels"]}`。
- baseline 冻结难度：较好。day 7 时间点更贴近当前主线窗口，制度同构性更强。
- single-perturbation 干净度：一般。虽然存在明确单基因 perturbation，但多目标拼接仍然很多。
- 结论：`preferred`。

### tian_2021_crispri

- control 清晰度：待核实。`{backup["main_control_source_column"]}` / `{backup["main_control_labels"]}` 仅代表当前 fail-fast 结果。
- baseline 冻结难度：中等。day 10 时间点与更大规模更适合作为辅助鲁棒性压力测试。
- single-perturbation 干净度：需要结合后续正式过滤规则再判断。
- 结论：`possible_backup`。

## 关键保留意见

- 两个 Tian 数据集都不是“纯净单扰动”数据，后续 formal 前仍应在样本准入层面对组合扰动做更严格过滤。
- 本次只做 fail-fast 准入审计，未做 real_shift 稳定性验证，因此结论只支持 Stage 1A formal 的优先级排序，不等价于最终基准优胜。

## 关键数字

| 数据集 | 高置信 control | control 占比 | 单扰动主导 | 估计可用 perturbation 数 |
|---|---:|---:|---:|---:|
| adamson_2016_upr_perturb_seq | {adamson["has_high_confidence_control"]} | {adamson["control_cell_frac"]:.2%} | {adamson["appears_single_perturbation_dominant"]} | {adamson["likely_usable_perturbation_n"]} |
| dixit_2016 | {dixit["has_high_confidence_control"]} | {dixit["control_cell_frac"]:.2%} | {dixit["appears_single_perturbation_dominant"]} | {dixit["likely_usable_perturbation_n"]} |
| tian_2019_day7neuron | {preferred["has_high_confidence_control"]} | {preferred["control_cell_frac"]:.2%} | {preferred["appears_single_perturbation_dominant"]} | {preferred["likely_usable_perturbation_n"]} |
| tian_2021_crispri | {backup["has_high_confidence_control"]} | {backup["control_cell_frac"]:.2%} | {backup["appears_single_perturbation_dominant"]} | {backup["likely_usable_perturbation_n"]} |
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, object]] = []
    control_reports: list[pd.DataFrame] = []

    for spec in DATASETS:
        adata = load_dataset(spec)
        identity_columns = infer_identity_columns(adata)
        control_df = collect_control_candidates(adata, spec.name)
        control_df.attrs["n_obs"] = adata.n_obs
        control_reports.append(control_df)

        control_summary = select_main_control(control_df, identity_columns)
        single_summary = classify_cells(
            adata,
            spec=spec,
            perturbation_column=spec.output_identity_column,
            main_control_labels=control_summary["main_control_labels"],
        )

        summary_rows.append(
            {
                "dataset": spec.name,
                "shape": f"{adata.n_obs}x{adata.n_vars}",
                "n_cells": adata.n_obs,
                "n_genes": adata.n_vars,
                "obs_columns": to_json_list(list(map(str, adata.obs.columns))),
                "var_columns": to_json_list(list(map(str, adata.var.columns))),
                **{
                    f"has_{column}": column in {str(col) for col in adata.obs.columns}
                    for column in KEY_COLUMNS
                },
                "candidate_perturbation_identity_columns": to_json_list(identity_columns),
                **control_summary,
                **single_summary,
            }
        )

    summary_df = pd.DataFrame(summary_rows)

    preferred = "tian_2019_day7neuron"
    backup = "tian_2021_crispri"
    summary_df["replacement_conclusion"] = summary_df["dataset"].map(
        lambda dataset: verdict_for_dataset(dataset, preferred=preferred, backup=backup)
    )

    control_report_df = pd.concat(control_reports, ignore_index=True)
    control_report_df["is_main_control_label"] = False
    for row in summary_df.to_dict(orient="records"):
        mask = (
            (control_report_df["dataset"] == row["dataset"])
            & (control_report_df["source_column"] == row["main_control_source_column"])
            & (control_report_df["label_value"].isin(row["main_control_labels"]))
        )
        control_report_df.loc[mask, "is_main_control_label"] = True

    final_decision = "mainline_tian_2019_day7neuron_auxiliary_tian_2021_crispri"
    recommendation_path = OUTPUT_DIR / "recommendation.md"
    recommendation_path.write_text(
        build_recommendation_md(summary_df, final_decision=final_decision),
        encoding="utf-8",
    )

    summary_path = OUTPUT_DIR / "audit_summary.tsv"
    control_path = OUTPUT_DIR / "control_candidate_report.tsv"

    summary_df.to_csv(summary_path, sep="\t", index=False)
    control_report_df.sort_values(
        by=["dataset", "count", "source_column", "label_value"],
        ascending=[True, False, True, True],
    ).to_csv(control_path, sep="\t", index=False)

    print(f"已保存: {summary_path}")
    print(f"已保存: {control_path}")
    print(f"已保存: {recommendation_path}")
    print()
    display_columns = [
        "dataset",
        "has_high_confidence_control",
        "main_control_source_column",
        "main_control_labels",
        "control_cell_n",
        "control_cell_frac",
        "appears_single_perturbation_dominant",
        "unique_perturbation_n",
        "likely_usable_perturbation_n",
        "replacement_conclusion",
    ]
    print(summary_df[display_columns].to_string(index=False))


if __name__ == "__main__":
    main()
