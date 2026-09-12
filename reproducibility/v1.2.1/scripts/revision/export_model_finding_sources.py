"""原样摘录冻结 M4/M5 数值，生成带来源行、定位键和版本哈希的引用表；不重新评分。"""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/revision_model_findings"
SOURCES = [
    ("M4", "reports/revision/m4_hcc_full_audit", "formal_and_diagnostic_context_metrics.tsv",
     "reports/revision/m2_endpoint_object/sampling_aware_endpoint_object.tsv"),
    ("M5", "reports/revision/m5_independent_full_audit", "formal_and_reference_context_metrics.tsv",
     "reports/revision/m5_candidate_qualification/selected_context_endpoint_object.tsv.gz"),
]
# 字段名保留原表拼写，展示名称按中文说明；空白的不确定性字段不补造。
METRICS = [
    ("endpoint_alignment_spearman", "dependency 排序关联", "endpoint_alignment_ci_low", "endpoint_alignment_ci_high", "endpoint_alignment_label_permutation_pvalue", "endpoint_alignment_permutation_qvalue_bh"),
    ("directional_recovery_median_signed_cosine", "方向恢复的 target 中位数", "directional_recovery_ci_low", "directional_recovery_ci_high", "", ""),
    ("anchor_separation_auc", "冻结 anchor 与低信息组的幅度 AUC", "anchor_separation_ci_low", "anchor_separation_ci_high", "", ""),
    ("target_identity_spearman", "target 间相似性结构的保留", "", "", "target_identity_label_permutation_pvalue", "target_identity_permutation_qvalue_bh"),
    ("predicted_homogenization_uncentered", "预测向量未中心化平均余弦", "", "", "", ""),
    ("observed_homogenization_uncentered", "实测向量未中心化平均余弦", "", "", "", ""),
    ("excess_homogenization_uncentered", "相对实测的未中心化同质化差值", "", "", "", ""),
    ("excess_homogenization_centered", "target 中心化后的同质化差值", "", "", "", ""),
    ("conventional_pearson_median", "共同基因空间 Pearson 的 target 中位数", "conventional_pearson_ci_low", "conventional_pearson_ci_high", "", ""),
    ("conventional_normalized_rmse_median", "共同基因空间 nRMSE 的 target 中位数", "conventional_normalized_rmse_ci_low", "conventional_normalized_rmse_ci_high", "", ""),
    ("secondary_absolute_projection_median", "次级绝对投影的 target 中位数", "secondary_absolute_projection_ci_low", "secondary_absolute_projection_ci_high", "", ""),
]


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def read_rows(path):
    with (ROOT / path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [(reader.line_num, row) for row in reader]


def render_main_table(rows):
    """由同一引用记录排版数值表；不重新计算任何指标或区间。"""
    contexts = {}
    for row in rows:
        # 三个 oracle/random-direction 对照在 Results 的控制段列出，不混入正式模型表。
        if row["entrant_kind"] == "reference" and row["entrant_id"] != "shared_mean_baseline":
            continue
        contexts.setdefault(row["context"], {}).setdefault(row["entrant_id"], {})[row["metric"]] = row

    def number(value):
        return "NA" if value == "NA" else f"{float(value):.3f}"

    def estimate(row, with_q=False):
        value = number(row["value"])
        if row["ci_low"] != "NA":
            value += f" [{number(row['ci_low'])}, {number(row['ci_high'])}]"
        if with_q and row["bh_q"] != "NA":
            value += f"；q={float(row['bh_q']):.3g}"
        return value

    def design(row):
        if row["entrant_kind"] != "formal":
            return "诊断参照"
        return "target LOO" if row["target_heldout"] == "True" else "非 target-held-out"

    lines = ["# 模型审计主表工作版", "",
             "正式稿件表号、页码和排版待回填。本表从 model_audit_citation_table.tsv 自动排版；未增加统计分析。覆盖全部 21 个正式 model-contexts，加三个 shared-mean 和两个 zero-output 诊断参照。Oracle/negated/random-direction 见配套 Results 控制段。", "",
             "括号内均为已有 95% CI。Endpoint 为 dependency 排序关联；direction 为 signed cosine 中位数；identity 为 target 间相似性结构的 rho；H 为 mean off-diagonal cosine。ΔH=H_pred−H_obs，centered ΔH 为跨 target 去均值后的对应差值。", "",
             "Endpoint、direction 和 AUC 的较高值表示对应维度恢复较强；正的 excess homogenization 是相对实测的偏高现象，不是性能奖励，也没有通用危险阈值。Identity 和 H 没有现成 CI；NA 是不可估计，不填成 0。", "",
             "Endpoint/identity 的 q 分别来自 M4 的两个 18-test families、M5 的两个 3-test families；这些是单输出检验，不是模型间差异检验。Shared-mean 使用实测响应，只作诊断，不是与 LOO 模型相同信息条件下的预测基线。", ""]
    for context, models in contexts.items():
        meta = next(iter(next(iter(models.values())).values()))
        observed = next(iter(models.values()))["observed_homogenization_uncentered"]
        lines += [f"## {context}", "",
                  f"角色：{meta['context_role']}。完整 endpoint targets={meta['full_endpoint_n_targets']}；评分 targets×genes={meta['contract_n_targets']}×{meta['contract_n_genes']}；anchors/low-information={meta['anchor_n']}/{meta['low_information_n']}。共同 observed H={number(observed['value'])}。", "",
                  "| 输出 | 设定 | Endpoint rho [95% CI]；q | Signed cosine [95% CI] | Anchor AUC [95% CI] | Identity rho；q | H_pred / ΔH / centered ΔH |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        for metrics in models.values():
            row = metrics["endpoint_alignment_spearman"]
            h = " / ".join(number(metrics[m]["value"]) for m in ["predicted_homogenization_uncentered", "excess_homogenization_uncentered", "excess_homogenization_centered"])
            cells = [row["display_name"], design(row), estimate(row, True),
                     estimate(metrics["directional_recovery_median_signed_cosine"]), estimate(metrics["anchor_separation_auc"]),
                     estimate(metrics["target_identity_spearman"], True), h]
            lines.append("| " + " | ".join(cells) + " |")
        lines += ["", "### 对应的共同空间 reconstruction", "",
                  "Pearson 越高、nRMSE 越低表示这两种 reconstruction 摘要表现较好；不是全转录组或跨 context 排名。", "",
                  "| 输出 | 设定 | Pearson 中位数 [95% CI] | nRMSE 中位数 [95% CI] |",
                  "| --- | --- | --- | --- |"]
        for metrics in models.values():
            row = metrics["endpoint_alignment_spearman"]
            cells = [row["display_name"], design(row), estimate(metrics["conventional_pearson_median"]), estimate(metrics["conventional_normalized_rmse_median"])]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    lines += ["## 来源与完整精度", "",
              "所有原始 P、q、CI、对象版本、训练设定、来源行/键/列和哈希保留于 [引用表](model_audit_citation_table.tsv)，表中仅按三位小数排版。HCC1143 的 SS18L2 仅因共同输出覆盖缺失而不评分，完整 48-target categories 不重算。", "",
              "HCC38 scGen 的小样本 anchors/low-information 在现有样本中完全分离，经验分层 bootstrap AUC 区间为 [1,1]；这不表示总体不确定性为零，也不是泛化保证。HCC 小样本 AUC 不用于点估计排名。", "",
              "HCC 的 shared-mean 是既有 canonical-backbone 实测均值参照；Replogle 的 shared-mean 为完整评分队列的实测平均响应。零向量的方向与 identity 不可估计；恒定幅度不能计算 endpoint Spearman。", ""]
    path = OUT / "model_audit_main_table.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs, checked, rows = {}, [], []
    for stage, folder, basename, endpoint_path in SOURCES:
        metrics_path = f"{folder}/{basename}"
        training_path = f"{folder}/model_training_evaluation_registry.tsv"
        manifest_path = f"{folder}/run_manifest.json"
        manifest = json.loads((ROOT / manifest_path).read_text())
        training = {
            (r["cell_line"] if stage == "M4" else r["context"], r["model_id"]): (line, r)
            for line, r in read_rows(training_path)
        }
        required = [metrics_path, training_path, endpoint_path, "configs/revision/revision_metric_spec_v1.json"]
        if stage == "M5":
            required.append("src/wtbench/revision_m5_audit.py")
        records = {r["path"]: r for r in manifest["inputs"] + manifest["outputs"]}
        for path in required:
            actual = digest(path)
            assert actual == records[path]["sha256"], path
            inputs[path] = actual
            checked.append(dict(stage=stage, path=path, matched_frozen_manifest=True))
        inputs[manifest_path] = digest(manifest_path)
        for line, source in read_rows(metrics_path):
            key = (source["cell_line"], source["entrant_id"])
            if stage == "M5" and source["entrant_kind"] == "reference":
                training_line = "NA"
                heldout = "不适用：由实测响应构造的诊断对照"
                design = "非独立预测模型；shared-mean 包含全队列实测均值"
            else:
                training_line, record = training[key]
                heldout = record["scored_target_held_out_from_fit" if stage == "M4" else "target_heldout"]
                design = record["evaluation_design" if stage == "M4" else "training_setting"]
            for metric, label, lo, hi, p, q in METRICS:
                uncertainty = "原结果未提供 CI 或检验；不得补写为零"
                if lo:
                    uncertainty = "5,000 次 target bootstrap 的 95% CI；AUC 按类别分层；不是模型差值 CI"
                if metric == "endpoint_alignment_spearman":
                    uncertainty += "; 10,000 次双侧 endpoint-label permutation"
                if metric == "target_identity_spearman":
                    uncertainty = f"正向单侧 target-label/Mantel permutation；{'10,000' if stage == 'M4' else '999'} 次；无 identity CI"
                if source["entrant_kind"] != "formal":
                    uncertainty += "; 诊断对照不进入 formal 置换/BH family，缺失 P/q 保留 NA"
                status_field = {
                    "endpoint_alignment_spearman": "endpoint_alignment_status",
                    "target_identity_spearman": "target_identity_status",
                }.get(metric)
                rows.append(dict(
                    stage=stage, context=source["cell_line"], context_role=source["context_role"],
                    entrant_id=source["entrant_id"], display_name=source["display_name"], entrant_kind=source["entrant_kind"],
                    metric=metric, display_metric_zh=label, value=source[metric],
                    ci_low=source[lo] if lo else "NA", ci_high=source[hi] if hi else "NA",
                    permutation_p=source[p] if p else "NA", bh_q=source[q] if q else "NA",
                    value_status=source[status_field] if status_field else ("NA" if source[metric] == "NA" else "已有数值"),
                    uncertainty_scope=uncertainty,
                    bh_family="不适用" if not q or source["entrant_kind"] != "formal" else ("M4 各维度独立的 18 项 family" if stage == "M4" else "M5 各维度独立的 3 项 family"),
                    full_endpoint_n_targets=source["full_endpoint_n_targets"],
                    contract_n_targets=source["contract_n_targets"], contract_n_genes=source["contract_n_genes"],
                    anchor_n=source["anchor_n"], low_information_n=source["low_information_n"],
                    target_heldout=heldout, evaluation_design=design,
                    source_file=metrics_path, source_line=line, source_sha256=inputs[metrics_path],
                    source_key=json.dumps(dict(cell_line=key[0], entrant_id=key[1]), ensure_ascii=False),
                    source_value_column=metric, source_ci_columns=f"{lo};{hi}" if lo else "NA",
                    source_p_column=p or "NA", source_q_column=q or "NA",
                    training_source=training_path if training_line != "NA" else "src/wtbench/revision_m5_audit.py:reference_predictions",
                    training_source_line=training_line, endpoint_object=endpoint_path, endpoint_sha256=inputs[endpoint_path],
                ))
    table_path = OUT / "model_audit_citation_table.tsv"
    with table_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    main_table_path = render_main_table(rows)
    inputs["scripts/revision/export_model_finding_sources.py"] = digest("scripts/revision/export_model_finding_sources.py")
    output = dict(status="完成：仅提取既有结果", completed_utc=datetime.now(timezone.utc).isoformat(),
                  n_metric_rows=len(rows), frozen_source_checks=checked, inputs_sha256=inputs,
                  output_sha256={str(p.relative_to(ROOT)): digest(p.relative_to(ROOT)) for p in [table_path, main_table_path]},
                  new_model_scoring=False, new_statistical_inference=False,
                  selection_scope="M4 全部 formal/diagnostic outputs 与 M5 全部 formal/reference outputs；不按得分筛选模型",
                  pairwise_inference="源结果没有模型间配对差值 CI 或等效性检验；不能补造")
    (OUT / "extraction_manifest.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已原样摘录 {len(rows)} 个指标记录；{len(checked)} 项冻结来源 hash 匹配。")


if __name__ == "__main__":
    main()
