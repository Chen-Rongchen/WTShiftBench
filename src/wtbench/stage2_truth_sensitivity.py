from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from wtbench.stage2_truth_bridge import (
    TRUTH_METRIC_COLUMNS,
    build_bridge_records,
    build_dataset_specs,
    load_config,
    load_depmap_endpoint,
    prepare_bridge_inputs,
    resolve_path,
    summarize_correlations,
)


def load_sensitivity_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {"base_config", "output", "control_subsample"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"Stage 2 sensitivity 配置缺少字段: {missing}")
    return payload


def rank_stability_vs_baseline(
    baseline: pd.DataFrame,
    replicate: pd.DataFrame,
    truth_metrics: list[str],
) -> pd.DataFrame:
    """各 truth 指标在 target 上的秩，与 baseline 是否一致（Spearman）。"""
    merged = baseline.loc[:, ["target_gene", *truth_metrics]].merge(
        replicate.loc[:, ["target_gene", *truth_metrics]],
        on="target_gene",
        suffixes=("_base", "_rep"),
    )
    rows: list[dict[str, Any]] = []
    for m in truth_metrics:
        a = merged[f"{m}_base"]
        b = merged[f"{m}_rep"]
        if len(a) < 3 or a.nunique() < 2 or b.nunique() < 2:
            rho = np.nan
        else:
            rho, _ = spearmanr(a, b)
        rows.append(
            {
                "truth_metric": m,
                "n_targets": int(len(a)),
                "spearman_rank_vs_baseline": float(rho) if not pd.isna(rho) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def audit_covariate_balance(
    calls: pd.DataFrame,
    covariates: pd.DataFrame,
    *,
    barcode_col: str,
    strat_col: str,
) -> pd.DataFrame:
    """
    比较各 target 与 control 在 strat_col 上的分布；报告 total variation distance。
    covariates 至少含 barcode_col、strat_col。
    """
    merged = calls[[barcode_col, "target_gene", "is_control"]].merge(
        covariates[[barcode_col, strat_col]].drop_duplicates(subset=[barcode_col]),
        on=barcode_col,
        how="left",
    )
    merged[strat_col] = merged[strat_col].astype("string").fillna("__missing__")

    control_rows = merged.loc[merged["is_control"]]
    tgt_rows = merged.loc[~merged["is_control"]]

    strata = sorted(merged[strat_col].unique().tolist())
    records: list[dict[str, Any]] = []
    for target_gene, g in tgt_rows.groupby("target_gene", sort=True):
        n_t = len(g)
        n_c = len(control_rows)
        if n_t == 0 or n_c == 0:
            continue
        p_t = g[strat_col].value_counts(normalize=True).reindex(strata, fill_value=0.0)
        p_c = control_rows[strat_col].value_counts(normalize=True).reindex(strata, fill_value=0.0)
        tv = float(np.abs(p_t.to_numpy() - p_c.to_numpy()).sum() / 2.0)
        records.append(
            {
                "target_gene": str(target_gene),
                "n_target_cells": int(n_t),
                "n_control_cells": int(n_c),
                "total_variation_distance": tv,
            }
        )
    return pd.DataFrame(records).sort_values("target_gene").reset_index(drop=True)


def summarize_replicate_correlations(correlation_long: pd.DataFrame) -> pd.DataFrame:
    """replicate 维上汇总 spearman_rho_aligned（按 cell_line, truth_metric, depmap_endpoint）。"""
    gcols = ["cell_line", "truth_metric", "depmap_endpoint"]
    rows: list[dict[str, Any]] = []
    for key, grp in correlation_long.groupby(gcols, sort=False):
        s = grp["spearman_rho_aligned"].dropna()
        if s.empty:
            rows.append(
                {
                    "cell_line": key[0],
                    "truth_metric": key[1],
                    "depmap_endpoint": key[2],
                    "n_replicates": 0,
                    "spearman_aligned_mean": np.nan,
                    "spearman_aligned_std": np.nan,
                    "spearman_aligned_q025": np.nan,
                    "spearman_aligned_q50": np.nan,
                    "spearman_aligned_q975": np.nan,
                }
            )
            continue
        rows.append(
            {
                "cell_line": key[0],
                "truth_metric": key[1],
                "depmap_endpoint": key[2],
                "n_replicates": int(len(s)),
                "spearman_aligned_mean": float(s.mean()),
                "spearman_aligned_std": float(s.std(ddof=1)) if len(s) > 1 else 0.0,
                "spearman_aligned_q025": float(s.quantile(0.025)),
                "spearman_aligned_q50": float(s.quantile(0.5)),
                "spearman_aligned_q975": float(s.quantile(0.975)),
            }
        )
    return pd.DataFrame(rows)


def run_control_subsample_sensitivity(
    base_config: dict[str, Any],
    sensitivity: dict[str, Any],
    *,
    depmap_effect: pd.DataFrame,
    depmap_dependency: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    对 control 无放回子抽样，重复计算 bridge 与 summarize_correlations。
    返回 (replicate_long, summary, rank_stability_long)。
    """
    n_replicates = int(sensitivity["n_replicates"])
    rng_seed = int(sensitivity.get("random_seed", 0))
    subsample_size_cfg = sensitivity.get("subsample_size")

    specs = build_dataset_specs(base_config)
    filters = base_config["filters"]
    metrics_cfg = base_config["metrics"]
    min_control = int(filters["min_control_cells"])

    rep_rows: list[dict[str, Any]] = []
    rank_rows: list[dict[str, Any]] = []

    for spec_index, spec in enumerate(specs):
        rng = np.random.default_rng(rng_seed + 10_000 * spec_index)
        normalized, embeddings, calls, _, effect_series, dependency_series = prepare_bridge_inputs(
            spec, base_config, depmap_effect, depmap_dependency
        )
        control_mask = calls["is_control"].to_numpy(dtype=bool)
        all_control = np.flatnonzero(control_mask)

        baseline_table = build_bridge_records(
            spec=spec,
            filters=filters,
            metrics_cfg=metrics_cfg,
            normalized=normalized,
            embeddings=embeddings,
            calls=calls,
            control_positions=all_control,
            effect_series=effect_series,
            dependency_series=dependency_series,
        )

        if subsample_size_cfg is None:
            subsample_size = int(min(500, len(all_control)))
        else:
            subsample_size = int(subsample_size_cfg)
        subsample_size = max(subsample_size, min_control)
        subsample_size = min(subsample_size, len(all_control))

        for rep in range(n_replicates):
            sub = rng.choice(all_control, size=subsample_size, replace=False)
            table = build_bridge_records(
                spec=spec,
                filters=filters,
                metrics_cfg=metrics_cfg,
                normalized=normalized,
                embeddings=embeddings,
                calls=calls,
                control_positions=sub,
                effect_series=effect_series,
                dependency_series=dependency_series,
            )
            corr = summarize_correlations(table)
            for row in corr.itertuples(index=False):
                rep_rows.append(
                    {
                        "replicate": rep,
                        "cell_line": row.cell_line,
                        "truth_metric": row.truth_metric,
                        "depmap_endpoint": row.depmap_endpoint,
                        "n_targets": row.n_targets,
                        "spearman_rho_raw": row.spearman_rho_raw,
                        "spearman_rho_aligned": row.spearman_rho_aligned,
                        "n_control_subsample": subsample_size,
                    }
                )
            rs = rank_stability_vs_baseline(baseline_table, table, TRUTH_METRIC_COLUMNS)
            for rrow in rs.itertuples(index=False):
                rank_rows.append(
                    {
                        "replicate": rep,
                        "cell_line": spec.cell_line,
                        "truth_metric": rrow.truth_metric,
                        "n_targets": rrow.n_targets,
                        "spearman_rank_vs_baseline": rrow.spearman_rank_vs_baseline,
                    }
                )

    rep_df = pd.DataFrame(rep_rows)
    summary = summarize_replicate_correlations(rep_df)
    rank_df = pd.DataFrame(rank_rows)
    return rep_df, summary, rank_df


def run_deg_threshold_sweep(
    base_config: dict[str, Any],
    sweep: dict[str, Any],
    *,
    depmap_effect: pd.DataFrame,
    depmap_dependency: pd.DataFrame,
) -> pd.DataFrame:
    """仅改变 DEG 阈值，重算 bridge 与 depmap_gene_effect 的 Spearman（aligned）。"""
    thresholds = [float(x) for x in sweep["deg_abs_log1p_delta_thresholds"]]
    floor = float(sweep.get("deg_expression_floor", base_config["metrics"]["deg_expression_floor"]))
    specs = build_dataset_specs(base_config)
    filters = base_config["filters"]
    rows: list[dict[str, Any]] = []

    for spec in specs:
        normalized, embeddings, calls, _, effect_series, dependency_series = prepare_bridge_inputs(
            spec, base_config, depmap_effect, depmap_dependency
        )
        control_mask = calls["is_control"].to_numpy(dtype=bool)
        control_positions = np.flatnonzero(control_mask)
        for thr in thresholds:
            metrics_cfg = dict(base_config["metrics"])
            metrics_cfg["deg_abs_log1p_delta_threshold"] = thr
            metrics_cfg["deg_expression_floor"] = floor
            table = build_bridge_records(
                spec=spec,
                filters=filters,
                metrics_cfg=metrics_cfg,
                normalized=normalized,
                embeddings=embeddings,
                calls=calls,
                control_positions=control_positions,
                effect_series=effect_series,
                dependency_series=dependency_series,
            )
            subset = table.loc[:, ["real_DEG_burden", "depmap_gene_effect"]].dropna()
            if len(subset) < 3 or subset["real_DEG_burden"].nunique() < 2:
                rho_a = np.nan
            else:
                rho, _ = spearmanr(subset["real_DEG_burden"], subset["depmap_gene_effect"])
                rho_a = float(-rho) if not pd.isna(rho) else np.nan
            rows.append(
                {
                    "cell_line": spec.cell_line,
                    "deg_abs_log1p_delta_threshold": thr,
                    "deg_expression_floor": floor,
                    "n_targets": int(len(subset)),
                    "spearman_DEG_burden_vs_gene_effect_aligned": rho_a,
                }
            )
    return pd.DataFrame(rows)


def run_covariate_audit_if_configured(
    base_config: dict[str, Any],
    cov_cfg: dict[str, Any],
    *,
    depmap_effect: pd.DataFrame,
    depmap_dependency: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """按 cell_line 读取可选 covariates TSV，返回 {cell_line: audit_df}。"""
    out: dict[str, pd.DataFrame] = {}
    specs = build_dataset_specs(base_config)
    for spec in specs:
        block = cov_cfg.get(spec.cell_line)
        if not block:
            continue
        path = resolve_path(str(block["path"]))
        strat = str(block["strat_column"])
        barcode_col = str(block.get("barcode_column", "cell_barcode"))
        cov = pd.read_csv(path, sep="\t")
        if barcode_col not in cov.columns or strat not in cov.columns:
            raise ValueError(f"{path} 缺少 {barcode_col} 或 {strat}")
        _, _, calls, _, _, _ = prepare_bridge_inputs(spec, base_config, depmap_effect, depmap_dependency)
        out[spec.cell_line] = audit_covariate_balance(calls, cov, barcode_col=barcode_col, strat_col=strat)
    return out


def run_all_sensitivity_analyses(
    base_config: dict[str, Any],
    sens: dict[str, Any],
    *,
    depmap_effect: pd.DataFrame,
    depmap_dependency: pd.DataFrame,
) -> dict[str, Any]:
    """
    每个 cell line 仅调用一次 prepare_bridge_inputs（昂贵 SVD），再依次做：
    control 子抽样、DEG 阈值扫描、可选协变量审计。
    """
    specs = build_dataset_specs(base_config)
    filters = base_config["filters"]
    metrics_cfg_base = base_config["metrics"]
    min_control = int(filters["min_control_cells"])

    cs = sens["control_subsample"]
    n_replicates = int(cs["n_replicates"])
    rng_seed = int(cs.get("random_seed", 0))
    subsample_size_cfg = cs.get("subsample_size")

    rep_rows: list[dict[str, Any]] = []
    rank_rows: list[dict[str, Any]] = []
    deg_rows: list[dict[str, Any]] = []
    cov_out: dict[str, pd.DataFrame] = {}

    sweep_cfg = sens.get("deg_threshold_sweep")
    cov_cfg = sens.get("covariates") or {}

    for spec_index, spec in enumerate(specs):
        rng = np.random.default_rng(rng_seed + 10_000 * spec_index)
        normalized, embeddings, calls, _, effect_series, dependency_series = prepare_bridge_inputs(
            spec, base_config, depmap_effect, depmap_dependency
        )
        control_mask = calls["is_control"].to_numpy(dtype=bool)
        all_control = np.flatnonzero(control_mask)

        block = cov_cfg.get(spec.cell_line) if cov_cfg else None
        if block:
            path = resolve_path(str(block["path"]))
            strat = str(block["strat_column"])
            barcode_col = str(block.get("barcode_column", "cell_barcode"))
            cov = pd.read_csv(path, sep="\t")
            if barcode_col not in cov.columns or strat not in cov.columns:
                raise ValueError(f"{path} 缺少 {barcode_col} 或 {strat}")
            cov_out[spec.cell_line] = audit_covariate_balance(calls, cov, barcode_col=barcode_col, strat_col=strat)

        baseline_table = build_bridge_records(
            spec=spec,
            filters=filters,
            metrics_cfg=metrics_cfg_base,
            normalized=normalized,
            embeddings=embeddings,
            calls=calls,
            control_positions=all_control,
            effect_series=effect_series,
            dependency_series=dependency_series,
        )

        if subsample_size_cfg is None:
            subsample_size = int(min(500, len(all_control)))
        else:
            subsample_size = int(subsample_size_cfg)
        subsample_size = max(subsample_size, min_control)
        subsample_size = min(subsample_size, len(all_control))

        for rep in range(n_replicates):
            sub = rng.choice(all_control, size=subsample_size, replace=False)
            table = build_bridge_records(
                spec=spec,
                filters=filters,
                metrics_cfg=metrics_cfg_base,
                normalized=normalized,
                embeddings=embeddings,
                calls=calls,
                control_positions=sub,
                effect_series=effect_series,
                dependency_series=dependency_series,
            )
            corr = summarize_correlations(table)
            for row in corr.itertuples(index=False):
                rep_rows.append(
                    {
                        "replicate": rep,
                        "cell_line": row.cell_line,
                        "truth_metric": row.truth_metric,
                        "depmap_endpoint": row.depmap_endpoint,
                        "n_targets": row.n_targets,
                        "spearman_rho_raw": row.spearman_rho_raw,
                        "spearman_rho_aligned": row.spearman_rho_aligned,
                        "n_control_subsample": subsample_size,
                    }
                )
            rs = rank_stability_vs_baseline(baseline_table, table, TRUTH_METRIC_COLUMNS)
            for rrow in rs.itertuples(index=False):
                rank_rows.append(
                    {
                        "replicate": rep,
                        "cell_line": spec.cell_line,
                        "truth_metric": rrow.truth_metric,
                        "n_targets": rrow.n_targets,
                        "spearman_rank_vs_baseline": rrow.spearman_rank_vs_baseline,
                    }
                )

        if sweep_cfg:
            thresholds = [float(x) for x in sweep_cfg["deg_abs_log1p_delta_thresholds"]]
            floor = float(sweep_cfg.get("deg_expression_floor", metrics_cfg_base["deg_expression_floor"]))
            for thr in thresholds:
                metrics_cfg = dict(metrics_cfg_base)
                metrics_cfg["deg_abs_log1p_delta_threshold"] = thr
                metrics_cfg["deg_expression_floor"] = floor
                table = build_bridge_records(
                    spec=spec,
                    filters=filters,
                    metrics_cfg=metrics_cfg,
                    normalized=normalized,
                    embeddings=embeddings,
                    calls=calls,
                    control_positions=all_control,
                    effect_series=effect_series,
                    dependency_series=dependency_series,
                )
                subset = table.loc[:, ["real_DEG_burden", "depmap_gene_effect"]].dropna()
                if len(subset) < 3 or subset["real_DEG_burden"].nunique() < 2:
                    rho_a = np.nan
                else:
                    rho, _ = spearmanr(subset["real_DEG_burden"], subset["depmap_gene_effect"])
                    rho_a = float(-rho) if not pd.isna(rho) else np.nan
                deg_rows.append(
                    {
                        "cell_line": spec.cell_line,
                        "deg_abs_log1p_delta_threshold": thr,
                        "deg_expression_floor": floor,
                        "n_targets": int(len(subset)),
                        "spearman_DEG_burden_vs_gene_effect_aligned": rho_a,
                    }
                )

    rep_df = pd.DataFrame(rep_rows)
    summary = summarize_replicate_correlations(rep_df)
    rank_df = pd.DataFrame(rank_rows)
    deg_df = pd.DataFrame(deg_rows) if deg_rows else pd.DataFrame()
    return {
        "control_subsample_replicates": rep_df,
        "control_subsample_summary": summary,
        "rank_stability": rank_df,
        "deg_threshold_sweep": deg_df,
        "covariate_balance": cov_out,
    }
