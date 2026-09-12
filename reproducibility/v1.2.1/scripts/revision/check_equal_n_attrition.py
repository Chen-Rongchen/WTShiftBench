"""按用户指定的 equal-n 门槛，核对排除组与保留组的 shift 和 dependency。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from wtbench.revision_bridge_sensitivity import sha256_file


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/revision_equal_n_attrition"
DEPTHS = (20, 25, 50, 100)
M1 = "reports/revision/m1_bridge_confounding/target_level_covariates_and_corrected_shift.tsv"
COHORTS = "docs/revision_external_cell_count/cohort_sources.tsv"
METRICS = {
    "raw_shift": "原始 mean-absolute shift",
    "depmap_gene_dependency": "DepMap dependency probability（越高越强）",
    "noise_corrected_shift": "已有 matched-size noise-corrected shift",
    "equal_n_20_expected_shift": "已有 equal-n=20 的 target 期望 shift",
}


def compare_groups(excluded: np.ndarray, retained: np.ndarray) -> dict:
    result = {"n_excluded": len(excluded), "n_retained": len(retained)}
    for name, values in [("excluded", excluded), ("retained", retained)]:
        # 当前实际队列在若干门槛下没有排除项，不能把空组结果写成零。
        for stat, function in [("mean", np.mean), ("median", np.median), ("min", np.min), ("max", np.max)]:
            result[f"{name}_{stat}"] = float(function(values)) if len(values) else np.nan
    if len(excluded) and len(retained):
        ranks = rankdata(np.concatenate([excluded, retained]))
        u = ranks[:len(excluded)].sum() - len(excluded) * (len(excluded) + 1) / 2
        result.update(
            mean_difference=float(excluded.mean() - retained.mean()),
            median_difference=float(np.median(excluded) - np.median(retained)),
            rank_superiority=float(u / (len(excluded) * len(retained))),
            fraction_excluded_above_retained_median=float(np.mean(excluded > np.median(retained))),
            every_excluded_above_every_retained=bool(excluded.min() > retained.max()),
        )
    return result


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cohorts = pd.read_csv(ROOT / COHORTS, sep="\t")
    hcc = pd.read_csv(ROOT / M1, sep="\t").rename(columns={
        "observed_shift_mean_abs": "raw_shift", "equal_n_primary_shift": "equal_n_20_expected_shift",
    })
    frames = {c: hcc.loc[hcc.cell_line.eq(c)].copy() for c in ["HCC38", "HCC1143"]}
    for row in cohorts.itertuples():
        source = pd.read_csv(ROOT / row.source, sep="\t").rename(columns={"real_shift_mean_abs": "raw_shift"})
        complete = np.isfinite(source[["n_cells_target", "raw_shift", "depmap_gene_dependency"]].to_numpy(float)).all(axis=1)
        frames[row.context] = source.loc[complete].copy()
        assert len(frames[row.context]) == row.analyzed_targets

    records, targets = [], []
    for context, frame in frames.items():
        metrics = [m for m in METRICS if m in frame]
        target = frame[["target_gene", "n_cells_target", *metrics]].copy()
        target.insert(0, "context", context)
        for depth in DEPTHS:
            excluded = frame.n_cells_target.lt(depth)
            target[f"excluded_at_n{depth}"] = excluded.to_numpy()
            for metric in metrics:
                records.append(dict(context=context, depth=depth, metric=metric,
                                    **compare_groups(frame.loc[excluded, metric].to_numpy(float),
                                                     frame.loc[~excluded, metric].to_numpy(float))))
        targets.append(target)
    comparison = pd.DataFrame(records)
    comparison.to_csv(OUT / "group_comparison.tsv", sep="\t", index=False, na_rep="NA")
    pd.concat(targets, ignore_index=True).to_csv(
        OUT / "target_membership.tsv.gz", sep="\t", index=False, na_rep="NA", compression={"method": "gzip", "mtime": 0},
    )

    def pair(row: pd.Series, stat: str) -> str:
        values = [row[f"{group}_{stat}"] for group in ["excluded", "retained"]]
        return " / ".join(f"{v:.6g}" if np.isfinite(v) else "NA" for v in values)

    lines = ["# equal-n 门槛排除 targets 的 shift 与 dependency 核查", "",
             "## 核查结论", "",
             "- HCC38/HCC1143 在发生排除的各门槛下，排除组 raw shift 和 dependency 的均值、中位数均高于保留组；HCC38 在 n=25 没有排除项。这是组间倾向，不是逐 target 完全分离。",
             "- 两套 Replogle 数据在 n=25/50/100、Jurkat 在 n=100 也有相同方向；HepG2 在 n=100 的排除组 raw shift 更高，但 dependency 略低。现有可比较的 13 个 context×门槛组合中，raw shift 均值/中位数 13/13 较高，dependency 12/13 较高；嵌套门槛不能算作独立重复。",
             "- sampling correction 后并非普遍保留组间差异。Replogle essential 在 n=50/100 排除组 corrected shift 均值较低，中位数略高，排序优势仅 0.507/0.504。HCC38 在 n=50 唯一排除的 PRPF6，corrected shift 和已有 equal-n=20 shift 都低于保留组均值/中位数。",
             "- 全队列 count–dependency Spearman 接近零与某个低-count 尾部的组均值偏高可以共存；前者衡量整体单调关系，后者是特定门槛的组间比较，不能互相替代。", "",
             "## 问题与口径", "",
             "本次为用户要求的探索性队列构成核查，不改变冻结的 endpoint object、qualification 或模型评分。固定核对 n=20/25/50/100。", "",
             "排除组为 recovered target cell count < n，保留组为 ≥ n；先沿用上一轮测试的 DepMap 完整 eligible cohort，再比较门槛引起的排除。每个 target 等权，不能按 cell count 加权。", "",
             "raw shift 是每个 target 的平均绝对基因表达变化；下表的均值/中位数是在 targets 间汇总。dependency 使用 probability，数值越大依赖越强，不是符号相反的 gene effect。", "",
             "这里比较的是门槛改变后的 target 组成，没有对外部数据新跑 equal-n 抽样，也没有给已被排除的 targets 估计 n 大于其可用细胞数时的 shift。HCC 已有 equal-n=20 与 corrected shift 另列。", "",
             "## 原始 shift 与 dependency：均值", "",
             "所有数值对均为 **排除组 / 保留组**；NA 表示没有排除 targets，不能作组间比较。", "",
             "| Context | 门槛 n | targets 排除/保留 | raw shift 均值 | dependency 均值 |",
             "| --- | ---: | ---: | --- | --- |"]
    for (context, depth), group in comparison.groupby(["context", "depth"], sort=False):
        indexed = group.set_index("metric")
        raw, dep = indexed.loc["raw_shift"], indexed.loc["depmap_gene_dependency"]
        lines.append(f"| {context} | {depth} | {int(raw.n_excluded)}/{int(raw.n_retained)} | {pair(raw, 'mean')} | {pair(dep, 'mean')} |")
    lines += ["", "## 中位数与逐 target 超越比例", "",
              "优势比例 = P(排除组 target 的值 > 保留组 target 的值) + 0.5 × P(相等)，用秩和计算，等价于比较全部跨组 target 对；0.5 表示无排序优势，1 表示每个排除项严格超过每个保留项。它是描述性效应量，不是 P 值，也不是因果证据。", "",
              "| Context | n | raw shift 中位数 排除/保留 | dependency 中位数 排除/保留 | raw 优势比例 | dependency 优势比例 | raw 全部严格超过 | dependency 全部严格超过 |",
              "| --- | ---: | --- | --- | ---: | ---: | --- | --- |"]
    for (context, depth), group in comparison.groupby(["context", "depth"], sort=False):
        indexed = group.set_index("metric")
        raw, dep = indexed.loc["raw_shift"], indexed.loc["depmap_gene_dependency"]
        if raw.n_excluded == 0:
            continue
        lines.append(f"| {context} | {depth} | {pair(raw, 'median')} | {pair(dep, 'median')} | {raw.rank_superiority:.3f} | {dep.rank_superiority:.3f} | {'是' if raw.every_excluded_above_every_retained else '否'} | {'是' if dep.every_excluded_above_every_retained else '否'} |")
    lines += ["", "## 已有采样处理结果的同组比较", "",
              "这里只换 shift 统计量，门槛定义的 target 分组不变。equal-n=20 是 M1 中各 target 的 1,000 次抽样 shift 均值，而不是在 n=25/50/100 下重新抽样。", "",
              "| Context | 门槛 n | shift 统计量 | 均值 排除/保留 | 中位数 排除/保留 | 优势比例 |",
              "| --- | ---: | --- | --- | --- | ---: |"]
    for row in comparison.loc[~comparison.metric.isin(["raw_shift", "depmap_gene_dependency"]) & comparison.n_excluded.gt(0)].itertuples():
        series = pd.Series(row._asdict())
        lines.append(f"| {row.context} | {row.depth} | {METRICS[row.metric]} | {pair(series, 'mean')} | {pair(series, 'median')} | {row.rank_superiority:.3f} |")
    lines += ["", "## 范围与解释边界", "",
              "- HepG2/Jurkat 源表已按至少 50 cells 过滤；n=25/50 的零排除不代表原始实验没有低细胞数 targets。n=100 只比较 50–99 与 ≥100 cells 的现有 targets。",
              "- K562 TF 两个时间点的所有 eligible targets 都超过 100 cells，这几个门槛下无法比较排除组。",
              "- 各门槛下排除集合嵌套，不能把它们当独立重复；各 context 的 gene space 和 target universe 不同，不能横向直接比较 shift 绝对量。",
              "- 组均值或中位数较高不代表每个被排除 target 都超过每个保留 target；逐 target 数值、门槛归属、范围和严格分离标志均保存在结果表。",
              "- 低细胞数组 raw shift 偏高，本身也符合有限采样下 mean-absolute estimator 的幅度偏差，不能单凭此证明生物学响应更强。dependency 若同时偏高，可描述为与 fitness-related reduced cell recovery 一致，但不等于已证明细胞死亡或因果耗竭。",
              "- 这是对现有 eligible targets 的描述性全表比较，不因某个门槛的结果更好而选择主结论；不另外增加显著性筛选或 qualification 门槛。", "",
              "## 复现与来源", "", "```bash", "pixi run --environment core python scripts/revision/check_equal_n_attrition.py", "```", "",
              "复用上一轮 cohort_sources.tsv 的六个外部来源及 M1 HCC 冻结表。run_manifest.json 记录完整输入/输出 SHA256；本次不训练模型，不修改 Pixi 依赖。", ""]
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    inputs = [M1, COHORTS, *cohorts.source, "scripts/revision/check_equal_n_attrition.py", "pixi.toml", "pixi.lock"]
    manifest = dict(status="完成", completed_utc=datetime.now(timezone.utc).isoformat(),
                    depth_thresholds=DEPTHS, comparison="count < n 与 count >= n；targets 等权；描述性比较",
                    new_equal_n_subsampling=False, new_significance_tests=False,
                    input_sha256={p: sha256_file(ROOT / p) for p in inputs},
                    output_sha256={str(p.relative_to(ROOT)): sha256_file(p) for p in sorted(OUT.iterdir()) if p.name != "run_manifest.json"})
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已保存：{OUT.relative_to(ROOT)}")
    print(comparison.loc[comparison.n_excluded.gt(0) & comparison.metric.isin(["raw_shift", "depmap_gene_dependency"]),
                         ["context", "depth", "metric", "n_excluded", "n_retained", "excluded_mean", "retained_mean", "excluded_median", "retained_median", "rank_superiority"]].to_string(index=False))


if __name__ == "__main__":
    main()
