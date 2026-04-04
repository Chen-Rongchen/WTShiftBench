from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import urlretrieve

import anndata as ad
import pandas as pd
try:
    import pertpy as pt
except ModuleNotFoundError:
    pt = None

try:
    from scripts.stage1a.benchmark_invariant.catalog import (
        BACKUP_DATASET_FILES,
        PROJECT_ROOT,
    )
    from scripts.stage1a.dataset_semantics import (
        canonicalize_gene_series,
        is_adamson_control_target,
        parse_adamson_target_series,
    )
except ModuleNotFoundError:
    from stage1a_catalog import BACKUP_DATASET_FILES, PROJECT_ROOT
    from stage1a.dataset_semantics import (
        canonicalize_gene_series,
        is_adamson_control_target,
        parse_adamson_target_series,
    )


DEFAULT_CONFIG_PATH = (
    PROJECT_ROOT / "configs/stage1a/candidate_audits/single_perturbation_candidates.json"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports/stage1a/candidate_single_perturbation_audit"
DEFAULT_RAW_DIR = PROJECT_ROOT / "data/raw/stage1a/candidates"
DEFAULT_CONTROL_REGEX = re.compile(
    r"^control$|non[-_ ]?target|ntc|mock|negative control|neg(?:ative)?(?: |_)?control",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class DatasetConfig:
    dataset_id: str
    loader_name: str
    perturbation_columns: tuple[str, ...]
    target_columns: tuple[str, ...]
    control_columns: tuple[str, ...]
    combo_separators: tuple[str, ...]
    singleton_min_cells_per_target: int
    singleton_min_control_cells: int
    target_min_unique: int
    direct_download_url: str = ""
    local_file_name: str = ""
    notes: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计候选数据集的单扰动子集可用性。")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="JSON 配置路径。",
    )
    parser.add_argument(
        "--dataset-id",
        action="append",
        dest="dataset_ids",
        help="仅审计指定 dataset_id；可重复传入。",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="输出目录。",
    )
    return parser.parse_args()


def load_config(path: Path) -> list[DatasetConfig]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    dataset_payloads = payload.get("datasets", [])
    if not dataset_payloads:
        raise ValueError(f"{path} 未定义 datasets。")
    return [
        DatasetConfig(
            dataset_id=str(item["dataset_id"]),
            loader_name=str(item["loader_name"]),
            perturbation_columns=tuple(item.get("perturbation_columns", [])),
            target_columns=tuple(item.get("target_columns", [])),
            control_columns=tuple(item.get("control_columns", [])),
            combo_separators=tuple(item.get("combo_separators", [])),
            singleton_min_cells_per_target=int(item.get("singleton_min_cells_per_target", 30)),
            singleton_min_control_cells=int(item.get("singleton_min_control_cells", 100)),
            target_min_unique=int(item.get("target_min_unique", 50)),
            direct_download_url=str(item.get("direct_download_url", "")),
            local_file_name=str(item.get("local_file_name", "")),
            notes=str(item.get("notes", "")),
        )
        for item in dataset_payloads
    ]


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_ready(v) for v in value]
    if isinstance(value, tuple):
        return [json_ready(v) for v in value]
    if pd.isna(value):
        return None
    return value


def as_string(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("")


def pick_first_present(obs: pd.DataFrame, candidates: tuple[str, ...]) -> str:
    for column in candidates:
        if column in obs.columns:
            return column
    return ""


def load_dataset(config: DatasetConfig) -> ad.AnnData:
    backup_path = BACKUP_DATASET_FILES.get(config.dataset_id)
    if backup_path is not None and backup_path.exists():
        return ad.read_h5ad(backup_path)

    candidate_raw_dir = DEFAULT_RAW_DIR
    candidate_raw_dir.mkdir(parents=True, exist_ok=True)
    local_file_name = config.local_file_name or f"{config.dataset_id}.h5ad"
    local_path = candidate_raw_dir / local_file_name
    if local_path.exists():
        return ad.read_h5ad(local_path)

    if pt is not None:
        loader = getattr(pt.data, config.loader_name)
        return loader()

    if not config.direct_download_url:
        raise ModuleNotFoundError(
            f"当前环境缺少 pertpy，且 {config.dataset_id} 未配置 direct_download_url。"
        )

    urlretrieve(config.direct_download_url, local_path)
    return ad.read_h5ad(local_path)


def build_combo_regex(separators: tuple[str, ...]) -> re.Pattern[str]:
    if not separators:
        return re.compile(r"$^")
    escaped = [re.escape(item) for item in separators]
    return re.compile("|".join(escaped))


def infer_control_column(obs: pd.DataFrame, config: DatasetConfig) -> tuple[str, list[str], pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    candidate_columns = list(config.control_columns or config.perturbation_columns)
    for column in candidate_columns:
        if column not in obs.columns:
            continue
        series = as_string(obs[column])
        matches = series[series.str.contains(DEFAULT_CONTROL_REGEX, na=False)]
        if matches.empty:
            continue
        counts = matches.value_counts(dropna=False)
        for label, count in counts.items():
            rows.append(
                {
                    "source_column": column,
                    "label": str(label),
                    "count": int(count),
                    "fraction": round(float(count) / float(max(obs.shape[0], 1)), 6),
                }
            )
    candidate_frame = pd.DataFrame(rows)
    if candidate_frame.empty:
        return "", [], candidate_frame

    candidate_frame = candidate_frame.sort_values(
        by=["count", "source_column", "label"],
        ascending=[False, True, True],
    ).reset_index(drop=True)
    best = candidate_frame.iloc[0]
    best_column = str(best["source_column"])
    best_labels = (
        candidate_frame.loc[candidate_frame["source_column"] == best_column, "label"]
        .astype("string")
        .drop_duplicates()
        .tolist()
    )
    return best_column, [str(label) for label in best_labels], candidate_frame


def build_singleton_mask(
    obs: pd.DataFrame,
    perturbation_column: str,
    combo_regex: re.Pattern[str],
) -> tuple[pd.Series, str]:
    if "nperts" in obs.columns:
        nperts = pd.to_numeric(obs["nperts"], errors="coerce")
        return nperts.eq(1).fillna(False), "nperts == 1"

    perturbation = as_string(obs[perturbation_column])
    singleton_mask = perturbation.ne("") & ~perturbation.str.contains(combo_regex, na=False)
    return singleton_mask, f"{perturbation_column} 不含组合分隔符"


def infer_target_gene(obs: pd.DataFrame, config: DatasetConfig, singleton_index: pd.Index) -> tuple[pd.Series, str]:
    target_column = pick_first_present(obs, config.target_columns)
    if not target_column:
        raise ValueError(f"{config.dataset_id} 缺少 target 候选列: {list(config.target_columns)}")
    target_gene = as_string(obs[target_column]).reindex(singleton_index).fillna("")
    return target_gene, target_column


def summarize_label_counts(series: pd.Series, limit: int = 10) -> list[dict[str, Any]]:
    counts = as_string(series).replace("", pd.NA).dropna().value_counts(dropna=False).head(limit)
    total = max(int(series.shape[0]), 1)
    return [
        {
            "label": str(label),
            "count": int(count),
            "fraction": round(float(count) / float(total), 6),
        }
        for label, count in counts.items()
    ]


def audit_dataset(config: DatasetConfig, output_dir: Path) -> dict[str, Any]:
    adata = load_dataset(config)
    obs = adata.obs.copy()
    perturbation_column = pick_first_present(obs, config.perturbation_columns)
    if not perturbation_column:
        raise ValueError(
            f"{config.dataset_id} 缺少 perturbation 候选列: {list(config.perturbation_columns)}"
        )

    combo_regex = build_combo_regex(config.combo_separators)
    perturbation = as_string(obs[perturbation_column])
    if config.dataset_id == "adamson_2016_upr_perturb_seq":
        parsed_target = canonicalize_gene_series(parse_adamson_target_series(perturbation))
        control_column = "perturbation_target"
        control_labels = sorted(set(parsed_target.loc[is_adamson_control_target(parsed_target)].dropna().astype(str).tolist()))
        control_mask = is_adamson_control_target(parsed_target)
        control_candidates = pd.DataFrame(
            [
                {
                    "source_column": control_column,
                    "label": label,
                    "count": int(parsed_target.eq(label).sum()),
                    "fraction": round(float(parsed_target.eq(label).mean()), 6),
                }
                for label in control_labels
            ]
        )
        singleton_mask = parsed_target.ne("")
        singleton_rule = "从 perturbation 的 `target_guide` 前缀解析单基因 target"
        singleton_non_control_mask = singleton_mask & ~control_mask
        singleton_obs = obs.loc[singleton_non_control_mask].copy()
        target_gene = parsed_target.reindex(singleton_obs.index).fillna("")
        target_source_column = "perturbation_target"
    else:
        control_column, control_labels, control_candidates = infer_control_column(obs, config)

        if control_column:
            control_mask = as_string(obs[control_column]).str.lower().isin(
                {label.lower() for label in control_labels}
            )
        else:
            control_mask = perturbation.str.contains(DEFAULT_CONTROL_REGEX, na=False)

        singleton_mask, singleton_rule = build_singleton_mask(
            obs=obs,
            perturbation_column=perturbation_column,
            combo_regex=combo_regex,
        )
        singleton_non_control_mask = singleton_mask & ~control_mask
        singleton_obs = obs.loc[singleton_non_control_mask].copy()
        target_gene, target_source_column = infer_target_gene(
            obs=obs,
            config=config,
            singleton_index=singleton_obs.index,
        )
    singleton_obs["target_gene"] = target_gene

    invalid_target_mask = singleton_obs["target_gene"].astype("string").str.strip().eq("")
    singleton_obs_valid = singleton_obs.loc[~invalid_target_mask].copy()

    target_counts = (
        singleton_obs_valid["target_gene"].astype("string").value_counts().rename_axis("target_gene").reset_index(name="n_cells")
    )
    sufficient_target_mask = target_counts["n_cells"] >= config.singleton_min_cells_per_target
    sufficient_targets = target_counts.loc[sufficient_target_mask, "target_gene"].astype(str).tolist()
    eligible_singleton_obs = singleton_obs_valid.loc[
        singleton_obs_valid["target_gene"].astype("string").isin(sufficient_targets)
    ].copy()

    singleton_target_n = int(target_counts.shape[0])
    eligible_target_n = int(len(sufficient_targets))
    control_cell_n = int(control_mask.sum())
    invalid_target_n = int(invalid_target_mask.sum())
    combo_frac = float(perturbation.str.contains(combo_regex, na=False).mean()) if config.combo_separators else 0.0

    decision = "pass_candidate"
    reasons: list[str] = []
    if not control_column and control_cell_n == 0:
        decision = "hold"
        reasons.append("未找到高置信 control 列或 control 标签。")
    if control_cell_n < config.singleton_min_control_cells:
        decision = "hold"
        reasons.append(
            f"control 细胞数不足：{control_cell_n} < {config.singleton_min_control_cells}。"
        )
    if invalid_target_n > 0:
        decision = "hold"
        reasons.append(f"单扰动子集中存在 {invalid_target_n} 个 target 为空的细胞。")
    if eligible_target_n < config.target_min_unique:
        decision = "auxiliary_only" if decision != "hold" else decision
        reasons.append(
            f"满足最小细胞数门槛的 target 数不足：{eligible_target_n} < {config.target_min_unique}。"
        )

    summary = {
        "dataset_id": config.dataset_id,
        "loader_name": config.loader_name,
        "n_cells_raw": int(adata.n_obs),
        "n_genes_raw": int(adata.n_vars),
        "perturbation_column": perturbation_column,
        "target_source_column": target_source_column,
        "control_source_column": control_column,
        "control_labels": control_labels,
        "control_cell_n": control_cell_n,
        "singleton_rule": singleton_rule,
        "singleton_non_control_cell_n": int(singleton_non_control_mask.sum()),
        "singleton_target_n": singleton_target_n,
        "eligible_singleton_target_n": eligible_target_n,
        "eligible_singleton_cell_n": int(eligible_singleton_obs.shape[0]),
        "invalid_target_cell_n": invalid_target_n,
        "combo_label_fraction": round(combo_frac, 6),
        "decision": decision,
        "reasons": reasons or ["通过最小单扰动候选准入。"],
        "notes": config.notes,
    }

    dataset_output_dir = output_dir / config.dataset_id
    dataset_output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = dataset_output_dir / "single_perturbation_audit_summary.json"
    target_counts_path = dataset_output_dir / "singleton_target_counts.tsv"
    control_candidates_path = dataset_output_dir / "control_candidates.tsv"
    labels_path = dataset_output_dir / "top_singleton_labels.json"

    summary_path.write_text(
        json.dumps(json_ready(summary), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    target_counts.to_csv(target_counts_path, sep="\t", index=False)
    if not control_candidates.empty:
        control_candidates.to_csv(control_candidates_path, sep="\t", index=False)
    labels_path.write_text(
        json.dumps(
            summarize_label_counts(perturbation.loc[singleton_non_control_mask]),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    args = parse_args()
    dataset_configs = load_config(args.config)
    selected = set(args.dataset_ids or [])
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, Any]] = []
    for config in dataset_configs:
        if selected and config.dataset_id not in selected:
            continue
        summaries.append(audit_dataset(config=config, output_dir=output_dir))

    if not summaries:
        raise ValueError("未匹配到任何待审计的数据集。")

    summary_frame = pd.DataFrame(summaries).sort_values("dataset_id").reset_index(drop=True)
    summary_frame.to_csv(output_dir / "summary.tsv", sep="\t", index=False)
    (output_dir / "summary.json").write_text(
        json.dumps(json_ready(summaries), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(summary_frame.to_string(index=False))


if __name__ == "__main__":
    main()
