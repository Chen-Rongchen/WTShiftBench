from __future__ import annotations

import json
from pathlib import Path
import re

import anndata as ad
import pandas as pd

from stage1a_catalog import FORMAL_SOURCE_DATASETS, RAW_STAGE1A_DIR

CONTROL_PATTERNS = [
    r"^control$",
    r"non[-_ ]?target",
    r"\bntc\b",
    r"mock",
    r"negative control",
    r"neg(?:ative)?(?: |_)?control",
    r"neutral",
    r"intergenic",
    r"gal4",
    r"63\(mod\)",
]
CONTROL_REGEX = re.compile("|".join(CONTROL_PATTERNS), flags=re.IGNORECASE)

OBS_KEY_PRIORITY = [
    "perturbation",
    "gene",
    "gene_id",
    "target",
    "guide_id",
    "guide",
    "sgRNA",
    "sgRNA_read_count",
    "sgRNA_umi_count",
    "nperts",
    "ngenes",
    "batch",
    "celltype",
    "cell_line",
    "perturbation_type",
]
VAR_KEY_PRIORITY = [
    "ensemble_id",
    "ensembl_id",
    "gene_name",
    "ncounts",
    "ncells",
    "chr",
    "start",
    "end",
]
RELATED_COLUMN_PATTERNS = {
    "perturbation": re.compile(r"perturb", flags=re.IGNORECASE),
    "target": re.compile(r"^gene$|gene_id|target|transcript", flags=re.IGNORECASE),
    "guide": re.compile(r"guide|sgrna|grna", flags=re.IGNORECASE),
}
CONTROL_COLUMN_PRIORITY = [
    "perturbation",
    "gene",
    "target",
    "condition",
    "guide_id",
]
GENE_SYMBOL_ALIASES = {
    "ATP5C1": "ATP5F1C",
    "ATP5H": "ATP5PD",
    "TMEM55A": "PIP4P2",
}

def stringify(series: pd.Series) -> pd.Series:
    return series.astype("string")


def json_ready(value):
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_ready(v) for v in value]
    if isinstance(value, tuple):
        return [json_ready(v) for v in value]
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return str(value)
    return value


def pick_key_columns(columns: pd.Index, priority: list[str]) -> list[str]:
    column_set = {str(col) for col in columns}
    return [column for column in priority if column in column_set]


def collect_related_columns(columns: pd.Index) -> dict[str, list[str]]:
    names = [str(col) for col in columns]
    return {
        group: [column for column in names if pattern.search(column)]
        for group, pattern in RELATED_COLUMN_PATTERNS.items()
    }


def value_counts_table(series: pd.Series, limit: int = 10) -> list[dict[str, object]]:
    counts = stringify(series).fillna("<NA>").value_counts(dropna=False).head(limit)
    total = max(int(series.shape[0]), 1)
    rows: list[dict[str, object]] = []
    for label, count in counts.items():
        rows.append(
            {
                "label": str(label),
                "count": int(count),
                "fraction": round(float(count) / float(total), 6),
            }
        )
    return rows


def collect_control_candidates(obs: pd.DataFrame, n_obs: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for column in obs.columns:
        series = stringify(obs[column]).dropna()
        if series.empty:
            continue
        matches = series[series.str.contains(CONTROL_REGEX, na=False)]
        if matches.empty:
            continue
        counts = matches.value_counts()
        for label, count in counts.items():
            rows.append(
                {
                    "source_column": str(column),
                    "label": str(label),
                    "count": int(count),
                    "fraction": round(float(count) / float(n_obs), 6),
                    "is_exact_control": bool(re.fullmatch(r"control", str(label), flags=re.IGNORECASE)),
                    "is_non_targeting": bool(
                        re.search(r"non[-_ ]?target", str(label), flags=re.IGNORECASE)
                    ),
                }
            )
    rows.sort(
        key=lambda row: (
            CONTROL_COLUMN_PRIORITY.index(row["source_column"])
            if row["source_column"] in CONTROL_COLUMN_PRIORITY
            else len(CONTROL_COLUMN_PRIORITY),
            0 if row["is_exact_control"] else 1,
            0 if row["is_non_targeting"] else 1,
            -row["count"],
            row["label"],
        )
    )
    return rows


def select_control(candidates: list[dict[str, object]]) -> dict[str, object]:
    if not candidates:
        return {
            "status": "hold",
            "source_column": "",
            "labels": [],
            "count": 0,
            "fraction": 0.0,
            "note": "未发现高置信 control 标签候选。",
        }

    best = candidates[0]
    status = "pass" if best["count"] > 0 else "hold"
    return {
        "status": status,
        "source_column": best["source_column"],
        "labels": [best["label"]],
        "count": int(best["count"]),
        "fraction": float(best["fraction"]),
        "note": f"优先采用 `{best['source_column']}` 中的 `{best['label']}` 作为 control。",
    }


def infer_control_mask(obs: pd.DataFrame, control: dict[str, object]) -> pd.Series:
    mask = pd.Series(False, index=obs.index)
    labels = {str(label).lower() for label in control.get("labels", [])}
    for column in ["perturbation", "gene", "target", "condition", "guide_id"]:
        if column not in obs.columns:
            continue
        series = stringify(obs[column]).fillna("")
        if labels:
            mask = mask | series.str.lower().isin(labels)
        mask = mask | series.str.contains(CONTROL_REGEX, na=False)
    return mask


def assess_single_perturbation(
    dataset_name: str, obs: pd.DataFrame, control_mask: pd.Series
) -> dict[str, object]:
    if "nperts" in obs.columns:
        nperts = pd.to_numeric(obs["nperts"], errors="coerce")
        non_control = ~control_mask
        single_mask = nperts.eq(1)
        single_non_control = int((single_mask & non_control).sum())
        multi_non_control = int((nperts.gt(1) & non_control).sum())
        zero_non_control = int((nperts.eq(0) & non_control).sum())

        separator_ok = True
        if "perturbation" in obs.columns:
            perturbation = stringify(obs["perturbation"]).fillna("")
            if multi_non_control > 0:
                separator_ok = bool(
                    perturbation.loc[nperts.gt(1) & non_control]
                    .str.contains("_", na=False)
                    .all()
                )
            if single_non_control > 0:
                separator_ok = separator_ok and bool(
                    (~perturbation.loc[single_mask & non_control].str.contains("_", na=False)).all()
                )

        status = "pass" if zero_non_control == 0 and separator_ok and single_non_control > 0 else "hold"
        if dataset_name.startswith("tian_2019_") or dataset_name == "tian_2021_crispri":
            filter_expr = "nperts == 1"
            note = (
                "可用 `nperts == 1` 可靠筛选单基因扰动；部分单扰动细胞含 `gene+control` 双 guide，"
                "但 target 仍为单基因。"
            )
        else:
            filter_expr = "nperts == 1"
            note = "可用 `nperts == 1` 可靠筛选单扰动。"

        return {
            "status": status,
            "filter_expr": filter_expr,
            "single_non_control_cells": single_non_control,
            "multi_non_control_cells": multi_non_control,
            "zero_non_control_cells": zero_non_control,
            "note": note if status == "pass" else "单扰动筛选规则存在歧义，建议人工复核。",
        }

    if "perturbation" in obs.columns:
        perturbation = stringify(obs["perturbation"]).fillna("")
        non_control = perturbation.loc[~control_mask]
        has_combo = bool(non_control.str.contains(r"_|\+|;", na=False).any())
        status = "pass" if not has_combo else "hold"
        return {
            "status": status,
            "filter_expr": "perturbation not in control_labels",
            "single_non_control_cells": int((~control_mask).sum()),
            "multi_non_control_cells": int(has_combo),
            "zero_non_control_cells": 0,
            "note": "非 control 标签均为原子 label，可直接作为单扰动。"
            if status == "pass"
            else "缺少 `nperts` 且发现组合 label，无法可靠筛选单扰动。",
        }

    return {
        "status": "hold",
        "filter_expr": "",
        "single_non_control_cells": 0,
        "multi_non_control_cells": 0,
        "zero_non_control_cells": 0,
        "note": "缺少可用于判定单扰动的关键列。",
    }


def assess_gene_cleaning(
    dataset_name: str, adata, obs: pd.DataFrame, control_mask: pd.Series
) -> dict[str, object]:
    if {"gene", "gene_id"}.issubset(obs.columns):
        df = obs[["gene", "gene_id"]].astype("string")
        non_control = df.loc[~control_mask]
        gene_to_id = non_control.groupby("gene")["gene_id"].nunique()
        id_to_gene = non_control.groupby("gene_id")["gene"].nunique()
        perturbation_match_n = None
        if "perturbation" in obs.columns:
            perturbation = stringify(obs["perturbation"])
            perturbation_match_n = int(
                (
                    (df["gene"].eq("non-targeting") & perturbation.eq("control"))
                    | (df["gene"].ne("non-targeting") & perturbation.eq(df["gene"]))
                ).sum()
            )

        status = (
            "pass"
            if int((gene_to_id > 1).sum()) == 0 and int((id_to_gene > 1).sum()) == 0
            else "hold"
        )
        note = (
            "可直接用 `gene` 清洗 gene-level target，control 用 `non-targeting/control` 归一化；"
            "如需稳定标识可同时保留 `gene_id`。"
            if status == "pass"
            else "gene 与 gene_id 不是一一映射，建议人工复核。"
        )
        return {
            "status": status,
            "target_column": "gene",
            "target_id_column": "gene_id",
            "cleaning_rule": "gene == 'non-targeting' -> control; else target_gene = gene",
            "non_control_unique_targets": int(non_control["gene"].nunique()),
            "gene_to_id_conflicts": int((gene_to_id > 1).sum()),
            "id_to_gene_conflicts": int((id_to_gene > 1).sum()),
            "perturbation_match_rows": perturbation_match_n,
            "note": note,
        }

    if "perturbation" in obs.columns:
        perturbation = stringify(obs["perturbation"]).dropna()
        non_control = perturbation.loc[~control_mask]
        all_tokens = sorted(
            {
                token
                for label in non_control.unique().tolist()
                for token in str(label).split("_")
                if token
            }
        )
        var_names = set(map(str, adata.var_names.tolist()))
        resolved_aliases = {
            token: GENE_SYMBOL_ALIASES[token]
            for token in all_tokens
            if token not in var_names and GENE_SYMBOL_ALIASES.get(token, "") in var_names
        }
        missing_tokens = [
            token
            for token in all_tokens
            if token not in var_names and token not in resolved_aliases
        ]
        status = "pass" if not missing_tokens else "hold"
        return {
            "status": status,
            "target_column": "perturbation",
            "target_id_column": "",
            "cleaning_rule": "control -> control; 单扰动 target_gene = perturbation; 组合扰动按 `_` 拆分",
            "non_control_unique_targets": len(all_tokens),
            "resolved_aliases_in_var_names": resolved_aliases,
            "missing_tokens_in_var_names": missing_tokens[:20],
            "note": "可直接从 `perturbation` 提取 gene-level target；部分旧符号已按受控别名映射闭合。"
            if status == "pass" and resolved_aliases
            else "可直接从 `perturbation` 提取 gene-level target。"
            if status == "pass"
            else "部分 target token 无法在 var_names 中确认，建议人工复核。",
        }

    return {
        "status": "fail",
        "target_column": "",
        "target_id_column": "",
        "cleaning_rule": "",
        "non_control_unique_targets": 0,
        "missing_tokens_in_var_names": [],
        "note": "缺少可清洗 gene-level target 的关键列。",
    }


def overall_status(
    control_status: str, single_status: str, gene_status: str
) -> str:
    if gene_status == "fail":
        return "fail"
    if control_status != "pass" or single_status != "pass" or gene_status != "pass":
        return "hold"
    return "pass"


def audit_dataset(dataset_name: str, dataset_path: Path) -> tuple[dict[str, object], dict[str, object]]:
    adata = ad.read_h5ad(dataset_path, backed="r")
    try:
        obs = adata.obs.copy()
        var = adata.var.copy()

        obs_key_columns = pick_key_columns(obs.columns, OBS_KEY_PRIORITY)
        var_key_columns = pick_key_columns(var.columns, VAR_KEY_PRIORITY)
        related_obs_columns = collect_related_columns(obs.columns)
        control_candidates = collect_control_candidates(obs, adata.n_obs)
        selected_control = select_control(control_candidates)
        control_mask = infer_control_mask(obs, selected_control)
        single_result = assess_single_perturbation(dataset_name, obs, control_mask)
        gene_result = assess_gene_cleaning(dataset_name, adata, obs, control_mask)
        decision = overall_status(
            selected_control["status"],
            single_result["status"],
            gene_result["status"],
        )

        summary = {
            "dataset": dataset_name,
            "dataset_path": str(dataset_path),
            "shape": [int(adata.n_obs), int(adata.n_vars)],
            "obs_key_columns": obs_key_columns,
            "var_key_columns": var_key_columns,
            "perturbation_related_obs_columns": related_obs_columns,
            "obs_top_values": {
                column: value_counts_table(obs[column], limit=8)
                for column in obs_key_columns
                if column in {"perturbation", "gene", "gene_id", "guide_id", "nperts"}
            },
            "control_label_candidates": control_candidates[:20],
            "selected_control": selected_control,
            "single_perturbation_filterability": single_result,
            "gene_level_target_cleaning": gene_result,
            "final_status": decision,
            "final_note": (
                "满足 raw audit 要求，可继续进入 formal 下游。"
                if decision == "pass"
                else "存在关键判定未完全闭合，建议先 hold。"
            ),
        }

        row = {
            "dataset": dataset_name,
            "shape": f"{adata.n_obs}x{adata.n_vars}",
            "obs_key_columns": json.dumps(obs_key_columns, ensure_ascii=False),
            "var_key_columns": json.dumps(var_key_columns, ensure_ascii=False),
            "control_source_column": selected_control["source_column"],
            "control_labels": json.dumps(selected_control["labels"], ensure_ascii=False),
            "control_status": selected_control["status"],
            "single_perturbation_status": single_result["status"],
            "single_perturbation_filter_expr": single_result["filter_expr"],
            "gene_level_target_status": gene_result["status"],
            "gene_level_target_column": gene_result["target_column"],
            "guide_columns": json.dumps(related_obs_columns["guide"], ensure_ascii=False),
            "perturbation_columns": json.dumps(
                related_obs_columns["perturbation"], ensure_ascii=False
            ),
            "target_columns": json.dumps(related_obs_columns["target"], ensure_ascii=False),
            "final_status": decision,
            "final_note": summary["final_note"],
        }
        return summary, row
    finally:
        adata.file.close()


def main() -> None:
    output_dir = RAW_STAGE1A_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    combined_rows: list[dict[str, object]] = []

    for dataset in FORMAL_SOURCE_DATASETS:
        summary, row = audit_dataset(dataset.name, dataset.path)
        combined_rows.append(row)

        output_path = output_dir / f"{dataset.name}.audit_summary.json"
        output_path.write_text(
            json.dumps(json_ready(summary), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"已写出: {output_path}")

    combined_df = pd.DataFrame(combined_rows).sort_values("dataset").reset_index(drop=True)
    combined_path = output_dir / "combined_audit.tsv"
    combined_df.to_csv(combined_path, sep="\t", index=False)
    print(f"已写出: {combined_path}")
    print(combined_df.to_string(index=False))


if __name__ == "__main__":
    main()
