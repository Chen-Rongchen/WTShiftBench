"""复用冻结表，比较外部数据的原始与控制细胞数后的 shift–dependency 关联。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wtbench.revision_bridge_sensitivity import (
    bh_adjust,
    infer_association,
    partial_spearman_statistic,
    sha256_file,
    spearman_statistic,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/revision_external_cell_count"
M1 = "reports/revision/m1_bridge_confounding"
BOOTSTRAPS = 5000
PERMUTATIONS = 10000
BOOTSTRAP_SEED = 2026090511
PERMUTATION_SEED = 2026090512
SOURCES = [
    ("Replogle K562 essential day 6", "reports/revision/m5_candidate_qualification/selected_context_endpoint_object.tsv.gz", "M5 已冻结的 1882-target 对象；上游至少 20 cells"),
    ("HepG2 day 7", "reports/gse264667_endpoint_extension/gse264667_hepg2_day7/target_level_bridge_table.tsv.gz", "上游至少 50 cells；本次不恢复已被过滤的 targets"),
    ("Jurkat day 7", "reports/gse264667_endpoint_extension/gse264667_jurkat_day7/target_level_bridge_table.tsv.gz", "上游至少 50 cells；本次不恢复已被过滤的 targets"),
    ("Replogle K562 genome-wide day 8", "data/processed/truth_driven_bridge_replogle_k562_gwps_day8/K562_GWPS_day8/target_level_bridge_table.tsv.gz", "沿用既有 genome-wide 表的 target eligibility"),
    ("K562 TF day 7", "data/processed/truth_driven_bridge_gse90063_7d/dixit_2016_k562_tf_7d_gse90063/target_level_bridge_table.tsv.gz", "沿用既有 10-target temporal panel"),
    ("K562 TF day 13", "data/processed/truth_driven_bridge_gse90063_13d/dixit_2016_k562_tf_13d_gse90063/target_level_bridge_table.tsv.gz", "沿用既有 10-target temporal panel"),
]


def infer(frame: pd.DataFrame, context: str, outcome: str, adjusted: bool) -> dict:
    result = infer_association(
        analysis_id=outcome + ("_partial_log_n" if adjusted else "_unadjusted"),
        cell_line=context,
        x=frame[outcome].to_numpy(float),
        y=frame.depmap_gene_dependency.to_numpy(float),
        covariates=np.log(frame.n_cells_target.to_numpy(float)) if adjusted else None,
        bootstrap_replicates=BOOTSTRAPS,
        permutation_replicates=PERMUTATIONS,
        bootstrap_seed=BOOTSTRAP_SEED,
        permutation_seed=PERMUTATION_SEED,
    )
    result.update(context=context, outcome=outcome, adjusted=adjusted,
                  evidence_role="本次探索性补充", reused_m1=False)
    print(f"完成 {context} / {result['analysis_id']}: rho={result['spearman_rho']:.6f}", flush=True)
    return result


def input_record(path: str) -> dict:
    source = ROOT / path
    return dict(path=path, size_bytes=source.stat().st_size, sha256=sha256_file(source))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = list(dict.fromkeys([
        *(s[1] for s in SOURCES), f"{M1}/target_level_covariates_and_corrected_shift.tsv",
        f"{M1}/bridge_inference_summary.tsv", "src/wtbench/revision_bridge_sensitivity.py",
        "scripts/revision/test_external_cell_count.py", "pixi.toml", "pixi.lock",
    ]))
    manifest = dict(
        status="运行中", started_utc=datetime.now(timezone.utc).isoformat(),
        purpose="用户要求：其他数据中是否也出现 HCC38 的约 0.04 偏相关？",
        interpretation="细胞数条件下的排序增量分析；不作因果识别，不改变原有 qualification 或 context 选择",
        primary="raw shift 与 dependency 的 Spearman，以及控制 log cell count 的 partial Spearman",
        secondary="仅对已有 corrected shift 的 HCC38、HCC1143、Replogle essential 另算 corrected partial",
        scope=SOURCES, bootstraps=BOOTSTRAPS, permutations=PERMUTATIONS,
        bootstrap_seed=BOOTSTRAP_SEED, permutation_seed=PERMUTATION_SEED,
        inference="复用 M1；target bootstrap 时重新排名；partial 用双侧 rank-scale Freedman–Lane residual permutation",
        multiple_testing="六个外部 raw tests、六个外部 raw partial tests 分别 BH；三个 corrected partial tests 另成 BH family；HCC 参考沿用 M1",
        inputs=[input_record(p) for p in inputs],
    )
    manifest_path = OUT / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    frames = {}
    cohort_rows = []
    hcc = pd.read_csv(ROOT / M1 / "target_level_covariates_and_corrected_shift.tsv", sep="\t")
    for context in ["HCC38", "HCC1143"]:
        frames[context] = hcc.loc[hcc.cell_line.eq(context)].rename(columns={"observed_shift_mean_abs": "raw_shift"}).copy()
    for context, path, note in SOURCES:
        source = pd.read_csv(ROOT / path, sep="\t")
        columns = ["n_cells_target", "real_shift_mean_abs", "depmap_gene_dependency"]
        eligible = np.isfinite(source[columns].to_numpy(float)).all(axis=1)
        frame = source.loc[eligible].rename(columns={"real_shift_mean_abs": "raw_shift"}).copy()
        # 旧外部表含 DepMap 缺失 targets，本次只取同一完整行集合计算所有关联。
        assert frame.n_cells_target.gt(0).all()
        assert not frame.target_gene.duplicated().any()
        frames[context] = frame
        cohort_rows.append(dict(context=context, input_targets=len(source), analyzed_targets=len(frame),
                                excluded_nonfinite=int((~eligible).sum()),
                                minimum_observed_count=int(frame.n_cells_target.min()),
                                median_count=float(frame.n_cells_target.median()),
                                response_gene_count=int(frame.gene_universe_size.iloc[0]),
                                source=path, eligibility_note=note))

    associations = []
    frozen = pd.read_csv(ROOT / M1 / "bridge_inference_summary.tsv", sep="\t")
    for context in ["HCC38", "HCC1143"]:
        for old_id, outcome, adjusted in [("raw_observed_shift", "raw_shift", False),
                                          ("partial_model_a_log_n", "raw_shift", True),
                                          ("noise_corrected_shift", "noise_corrected_shift", False)]:
            row = frozen.loc[frozen.cell_line.eq(context) & frozen.analysis_id.eq(old_id)].iloc[0].to_dict()
            row.update(context=context, outcome=outcome, adjusted=adjusted,
                       evidence_role="M1 已冻结参考", reused_m1=True)
            associations.append(row)

    checks = []
    for context, frame in frames.items():
        x = frame.raw_shift.to_numpy(float)
        y = frame.depmap_gene_dependency.to_numpy(float)
        n = frame.n_cells_target.to_numpy(float)
        rxy = spearman_statistic(x, y)
        rxn = spearman_statistic(x, n)
        ryn = spearman_statistic(y, n)
        partial = partial_spearman_statistic(x, y, np.log(n))
        algebra = (rxy - rxn * ryn) / np.sqrt((1 - rxn**2) * (1 - ryn**2))
        np.testing.assert_allclose(partial, algebra, atol=1e-12)
        if context in ["HCC38", "HCC1143"]:
            old = frozen.loc[frozen.cell_line.eq(context) & frozen.analysis_id.eq("partial_model_a_log_n")].iloc[0]
            np.testing.assert_allclose(partial, old.spearman_rho, atol=1e-12)
        checks.append(dict(context=context, n_targets=len(frame), raw_rho=rxy,
                           count_shift_rho=rxn, count_dependency_rho=ryn,
                           raw_partial_rho=partial, algebra_partial_rho=algebra,
                           algebra_absolute_error=abs(partial - algebra)))
        if context not in ["HCC38", "HCC1143"]:
            associations.append(infer(frame, context, "raw_shift", False))
            associations.append(infer(frame, context, "raw_shift", True))
        if "noise_corrected_shift" in frame:
            if context not in ["HCC38", "HCC1143"]:
                associations.append(infer(frame, context, "noise_corrected_shift", False))
            associations.append(infer(frame, context, "noise_corrected_shift", True))

    results = pd.DataFrame(associations)
    results["q_bh_this_test"] = np.nan
    for outcome, adjusted in [("raw_shift", False), ("raw_shift", True), ("noise_corrected_shift", True)]:
        family = results.outcome.eq(outcome) & results.adjusted.eq(adjusted) & ~results.reused_m1
        results.loc[family, "q_bh_this_test"] = bh_adjust(results.loc[family, "permutation_pvalue_two_sided"])
    results.to_csv(OUT / "association_inference.tsv", sep="\t", index=False, na_rep="NA")
    pd.DataFrame(cohort_rows).to_csv(OUT / "cohort_sources.tsv", sep="\t", index=False)
    summary = pd.DataFrame(checks)
    summary.to_csv(OUT / "count_shift_dependency_summary.tsv", sep="\t", index=False)
    plotted = results.loc[results.outcome.eq("raw_shift")]
    plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False})
    fig, ax = plt.subplots(figsize=(12, 6.6))
    contexts = list(frames)
    for adjusted, offset, color, label in [(False, -0.12, "#167d9a", "原始相关"), (True, 0.12, "#d67732", "控制细胞数后的偏相关")]:
        sub = plotted.loc[plotted.adjusted.eq(adjusted)].set_index("context").loc[contexts]
        value = sub.spearman_rho.to_numpy(float)
        err = np.vstack([value - sub.bootstrap_ci_low, sub.bootstrap_ci_high - value])
        ax.errorbar(value, np.arange(len(contexts)) + offset, xerr=err, fmt="o", color=color, label=label, capsize=3)
    ax.set_yticks(np.arange(len(contexts)), [f"{c}  (targets={len(frames[c]):,})" for c in contexts])
    ax.invert_yaxis()
    ax.axvline(0, color="#777777", linewidth=0.8)
    ax.set_xlim(-1, 1)
    ax.set_xlabel("Spearman 相关系数及 target bootstrap 95% CI")
    ax.set_title("原始 shift 控制 target cell count 后的关联：跨 context 对照")
    ax.legend(loc="upper left")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUT / "raw_vs_partial.png", dpi=180)
    plt.close(fig)

    lines = ["# 外部数据中的 target cell count 偏相关测试", "",
             "这是按用户问题开展的探索性补充，未改变 M1–M6 的冻结对象、模型或 Gate。", "",
             "## 问题与口径", "",
             "比较各 context 的原始 mean-absolute shift 与 DepMap dependency probability 关联，以及给定 log target cell count 后的偏 Spearman。后者衡量条件排序关联，不识别细胞耗竭的因果路径。", "",
             "HCC38/HCC1143 的原始、偏相关和噪声校正相关/CI/P 复用 M1；外部数据采用同一个统计实现。所有原始与偏相关在各自 context 内使用完全相同的 targets。", "",
             "每个新测试使用 5,000 次 target bootstrap、10,000 次双侧置换；partial 使用 rank-scale Freedman–Lane。六个外部 raw tests 与六个外部 raw partial tests 分别进行 BH 校正。", "",
             "## 原始关联、细胞数关系与偏相关", "",
             "| Context | targets | raw rho | count–shift rho | count–dependency rho | partial rho [95% CI] | partial P | 本次 family BH q |",
             "| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |"]
    for row in checks:
        s = plotted.loc[plotted.context.eq(row["context"]) & plotted.adjusted].iloc[0]
        q = f"{s.q_bh_this_test:.4g}" if np.isfinite(s.q_bh_this_test) else "M1 参考"
        lines.append(f"| {row['context']} | {row['n_targets']} | {row['raw_rho']:.3f} | {row['count_shift_rho']:.3f} | {row['count_dependency_rho']:.3f} | {s.spearman_rho:.3f} [{s.bootstrap_ci_low:.3f}, {s.bootstrap_ci_high:.3f}] | {s.permutation_pvalue_two_sided:.4g} | {q} |")
    lines += ["", "![原始与条件相关对照](raw_vs_partial.png)", "", "## 已有 sampling-corrected shift 的补充", "",
              "这一表与上表的 raw partial 是不同统计量；仅纳入已有 corrected shift 的三个 context，不现场为其他数据估算噪声底。", "",
              "| Context | corrected rho | corrected partial rho [95% CI] | partial P | BH q（三项） |",
              "| --- | ---: | --- | ---: | ---: |"]
    for context in ["HCC38", "HCC1143", SOURCES[0][0]]:
        sub = results.loc[results.context.eq(context) & results.outcome.eq("noise_corrected_shift")]
        raw = sub.loc[~sub.adjusted].iloc[0]
        part = sub.loc[sub.adjusted].iloc[0]
        lines.append(f"| {context} | {raw.spearman_rho:.3f} | {part.spearman_rho:.3f} [{part.bootstrap_ci_low:.3f}, {part.bootstrap_ci_high:.3f}] | {part.permutation_pvalue_two_sided:.4g} | {part.q_bh_this_test:.4g} |")
    lines += ["", "## 适用范围", "",
              "- HepG2/Jurkat 上游已按至少 50 cells 过滤，本次结果只代表保留队列。详见 cohort_sources.tsv。",
              "- K562 TF 每个时间点只有 10 targets；两个时间点与多个 K562 数据集不是独立生物学重复。",
              "- 各 context 的 gene space、target universe、时间点和预处理不同；本表比较同类现象，不构成效应大小的直接排名。",
              "- 不对 cell count 或 shift 重新筛选有利子集；缺失 dependency 的 targets 明确计入排除表。",
              "- 等深度抽样和 matched-control noise correction 回答测量偏差，partial 回答额外排序关联；两者不能替代。",
              "- 偏相关公式在八个 context 均与三相关系数的解析公式一致，HCC 约 0.040/0.364 复现通过。", "",
              "## 复现", "", "```bash", "pixi run --environment core revision-test-external-count", "```", "",
              "输入表、统计实现、Pixi lock 与输出的 SHA256 保存在 run_manifest.json；本次不重训练模型。", ""]
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    manifest.update(status="完成", completed_utc=datetime.now(timezone.utc).isoformat(),
                    outputs=[input_record(str(p.relative_to(ROOT))) for p in sorted(OUT.iterdir()) if p != manifest_path])
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"结果已保存：{OUT.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
