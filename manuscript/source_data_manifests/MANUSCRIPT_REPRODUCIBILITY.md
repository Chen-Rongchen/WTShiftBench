# 手稿复现入口

## 用途

本文档是 Genome Biology 投稿包的单一复现入口，面向 reviewer 和编辑。它只汇总已经冻结的 source data、manifest、配置和重跑入口，不新增 claim。

当前主线：

- 目标期刊：Genome Biology。
- 文章类型：framework / resource / benchmark Research article。
- 主叙事：truth-first fitness-bridge architecture 与 architecture-aware adjudication。
- 禁止重解释：不把 K562 写成 co-primary，不把 RNAi DEMETER2 写成 matched primary endpoint，不把 GEARS 写成 HCC primary winner。

## 手稿与投稿清单

- 主文投稿稿：`docs/main_manuscript_submission_draft_v2.md`
- Genome Biology 正文草案：`docs/genome_biology_manuscript_draft_v1.md`
- Cover letter 草案：`docs/genome_biology_cover_letter_v1.md`
- Genome Biology 投稿清单：`docs/genome_biology_submission_checklist_v1.md`
- 投稿执行计划：`docs/genome_biology_submission_execution_plan_v1.md`
- 投稿收口 handoff：`docs/genome_biology_finalization_handoff_v1.md`
- references 整理队列：`docs/genome_biology_reference_formatting_queue_v1.md`
- Additional files 说明：`docs/genome_biology_additional_files_v1.md`
- 图文一致性审计：`docs/genome_biology_figure_text_audit_v1.md`
- Final wording audit：`docs/genome_biology_final_wording_audit_v1.md`
- Word count：`docs/genome_biology_word_count_v1.md`
- Preprint role audit：`docs/genome_biology_preprint_role_audit_v1.md`
- Submission final index：`docs/genome_biology_submission_final_index_v1.md`
- Shared anchor role note：`docs/shared_anchor_role_note_v1.md`
- 投稿 readiness checklist：`docs/submission_readiness_checklist_v1.md`
- Availability 与复现说明：`docs/main_manuscript_availability_and_reproducibility_v1.md`

## 主图 source data 与 manifest

主图目录：`reports/manuscript_figures_v2/`

| 图 | 目录 | source data | panel manifest |
|---|---|---|---|
| Fig. 1 | `reports/manuscript_figures_v2/fig1_truth_object/` | `reports/manuscript_figures_v2/fig1_truth_object/figure1_source_data.tsv` | `reports/manuscript_figures_v2/fig1_truth_object/figure1_panel_manifest.json` |
| Fig. 2 | `reports/manuscript_figures_v2/fig2_anchor_tiering/` | `reports/manuscript_figures_v2/fig2_anchor_tiering/figure2_source_data.tsv` | `reports/manuscript_figures_v2/fig2_anchor_tiering/figure2_panel_manifest.json` |
| Fig. 3 | `reports/manuscript_figures_v2/fig3_model_tradeoff/` | `reports/manuscript_figures_v2/fig3_model_tradeoff/figure3_source_data.tsv` | `reports/manuscript_figures_v2/fig3_model_tradeoff/figure3_panel_manifest.json` |
| Fig. 4 | `reports/manuscript_figures_v2/fig4_sweep_controls/` | `reports/manuscript_figures_v2/fig4_sweep_controls/figure4_source_data.tsv` | `reports/manuscript_figures_v2/fig4_sweep_controls/figure4_panel_manifest.json` |
| Fig. 5 | `reports/manuscript_figures_v2/fig6_boundary/` | `reports/manuscript_figures_v2/fig6_boundary/figure6_source_data.tsv` | `reports/manuscript_figures_v2/fig6_boundary/figure6_panel_manifest.json` |

每个主图 panel 还有独立 PNG、PDF、source data TSV 和 manifest JSON，位于对应图目录的 `panels/` 子目录。

## Extended Data source data 与 manifest

Extended Data 目录：`reports/manuscript_extended_data_v1/`

| 图 | 目录 | source data | panel manifest |
|---|---|---|---|
| Extended Data Fig. 1 | `reports/manuscript_extended_data_v1/edfig1_dataset_endpoint_admission/` | `reports/manuscript_extended_data_v1/edfig1_dataset_endpoint_admission/edfig1_source_data.tsv` | `reports/manuscript_extended_data_v1/edfig1_dataset_endpoint_admission/edfig1_panel_manifest.json` |
| Extended Data Fig. 2 | `reports/manuscript_extended_data_v1/edfig2_full_target_grid/` | `reports/manuscript_extended_data_v1/edfig2_full_target_grid/edfig2_source_data.tsv` | `reports/manuscript_extended_data_v1/edfig2_full_target_grid/edfig2_panel_manifest.json` |
| Extended Data Fig. 3 | `reports/manuscript_extended_data_v1/edfig3_anchor_sensitivity/` | `reports/manuscript_extended_data_v1/edfig3_anchor_sensitivity/edfig3_source_data.tsv` | `reports/manuscript_extended_data_v1/edfig3_anchor_sensitivity/edfig3_panel_manifest.json` |
| Extended Data Fig. 4 | `reports/manuscript_extended_data_v1/edfig4_model_detail/` | `reports/manuscript_extended_data_v1/edfig4_model_detail/edfig4_source_data.tsv` | `reports/manuscript_extended_data_v1/edfig4_model_detail/edfig4_panel_manifest.json` |
| Extended Data Fig. 5 | `reports/manuscript_extended_data_v1/edfig5_gears_sweep/` | `reports/manuscript_extended_data_v1/edfig5_gears_sweep/edfig5_source_data.tsv` | `reports/manuscript_extended_data_v1/edfig5_gears_sweep/edfig5_panel_manifest.json` |
| Extended Data Fig. 6 | `reports/manuscript_extended_data_v1/edfig6_axis_annotation/` | `reports/manuscript_extended_data_v1/edfig6_axis_annotation/edfig6_source_data.tsv` | `reports/manuscript_extended_data_v1/edfig6_axis_annotation/edfig6_panel_manifest.json` |
| Extended Data Fig. 7 | `reports/manuscript_extended_data_v1/edfig7_k562_temporal/` | `reports/manuscript_extended_data_v1/edfig7_k562_temporal/edfig7_source_data.tsv` | `reports/manuscript_extended_data_v1/edfig7_k562_temporal/edfig7_panel_manifest.json` |
| Extended Data Fig. 8 | `reports/manuscript_extended_data_v1/edfig8_endpoint_hierarchy/` | `reports/manuscript_extended_data_v1/edfig8_endpoint_hierarchy/edfig8_source_data.tsv` | `reports/manuscript_extended_data_v1/edfig8_endpoint_hierarchy/edfig8_panel_manifest.json` |
| Extended Data Fig. 9 | `reports/manuscript_extended_data_v1/edfig9_covariate_audit/` | `reports/manuscript_extended_data_v1/edfig9_covariate_audit/edfig9_source_data.tsv` | `reports/manuscript_extended_data_v1/edfig9_covariate_audit/edfig9_panel_manifest.json` |
| Extended Data Fig. 10 | `reports/manuscript_extended_data_v1/edfig10_reproducibility/` | `reports/manuscript_extended_data_v1/edfig10_reproducibility/edfig10_source_data.tsv` | `reports/manuscript_extended_data_v1/edfig10_reproducibility/edfig10_panel_manifest.json` |
| Extended Data Fig. 11 | `reports/manuscript_figures_v2/fig5_axis_interpretation/` | `reports/manuscript_figures_v2/fig5_axis_interpretation/figure5_source_data.tsv` | `reports/manuscript_figures_v2/fig5_axis_interpretation/figure5_panel_manifest.json` |

## Supplementary tables 与投稿包 manifest

- Supplementary table summary：`reports/manuscript_supplementary_tables_v1/supplementary_table_summary.tsv`
- Supplementary table file index：`reports/manuscript_supplementary_tables_v1/supplementary_table_file_index.tsv`
- Supplementary table manifest：`reports/manuscript_supplementary_tables_v1/supplementary_table_manifest.json`
- Supplementary workbook：`reports/manuscript_submission_package_v1/supplementary_tables_v1.xlsx`
- Submission package summary：`reports/manuscript_submission_package_v1/submission_package_summary.tsv`
- Submission package file manifest：`reports/manuscript_submission_package_v1/submission_package_file_manifest.tsv`
- Submission package manifest：`reports/manuscript_submission_package_v1/submission_package_manifest.json`
- Genome Biology upload staging directory：`reports/genome_biology_submission_upload_v1/`

## 投稿前补充诊断

- 三指标相关性诊断报告：`reports/manuscript_metric_diagnostic_v1/metric_diagnostic_report.md`
- 三指标 model-level 点表：`reports/manuscript_metric_diagnostic_v1/metric_diagnostic_model_level_points.tsv`
- 三指标 entrant-context 点表：`reports/manuscript_metric_diagnostic_v1/metric_diagnostic_entrant_context_points.tsv`
- 三指标相关性汇总：`reports/manuscript_metric_diagnostic_v1/metric_correlation_summary.tsv`
- 三指标 permutation null 报告：`reports/manuscript_permutation_null_v1/permutation_null_report.md`
- 三指标 permutation null 汇总：`reports/manuscript_permutation_null_v1/permutation_null_summary.tsv`
- baseline gene-label permutation null 汇总：`reports/manuscript_permutation_null_v1/baseline_gene_label_permutation_summary.tsv`
- `barcode_gem_group` rank residualization 报告：`reports/manuscript_covariate_residualization_v1/barcode_gem_group_rank_residualization_report.md`
- `barcode_gem_group` rank residualization 汇总：`reports/manuscript_covariate_residualization_v1/barcode_gem_group_rank_residualization_summary.tsv`
- relaxed cutoff sensitivity 报告：`reports/manuscript_relaxed_cutoff_sensitivity_v1/relaxed_cutoff_sensitivity_report.md`
- relaxed cutoff shared-anchor summary：`reports/manuscript_relaxed_cutoff_sensitivity_v1/relaxed_cutoff_shared_anchor_summary.tsv`
- revision-round admission readiness：`docs/revision_round_admission_readiness_v1.md`

## Community adjudication kit

- 使用说明：`docs/community_adjudication_kit_v1.md`
- 示例配置：`configs/manuscript/architecture_adjudication_example_v1.json`
- CLI 入口：`scripts/manuscript/run_architecture_adjudication.py`
- 示例输出目录：`reports/manuscript_architecture_adjudication_example_v1/`
- 示例三指标输出：`reports/manuscript_architecture_adjudication_example_v1/architecture_scores.tsv`
- 示例 axis projection 输出：`reports/manuscript_architecture_adjudication_example_v1/axis_projections.tsv.gz`
- 示例 manifest：`reports/manuscript_architecture_adjudication_example_v1/architecture_adjudication_manifest.json`

## 冻结 claim 与关键裁决产物

- Final claim boundary：`docs/final_claim_boundary_note_v1.md`
- Claim boundary and discovery gating：`docs/final_claim_boundary_and_discovery_gating_note_v1.md`
- Discovery gating：`docs/discovery_formal_gating_note_v1.md`
- Stage 3 discovery gating：`docs/stage3_discovery_gating_note_v1.md`
- Model-vs-baseline explanation：`docs/model_vs_baseline_deeper_explanation_note_v1.md`
- Why models do not stably beat baseline：`docs/why_models_do_not_stably_beat_baseline_v1.md`
- Model expansion deferral：`docs/model_expansion_deferral_note_v1.md`
- GEARS final adjudication：`reports/stage2_gears_backbone_sweep/final_adjudication.md`
- GEARS sweep candidate manifest：`reports/stage2_gears_backbone_sweep/candidate_manifest.tsv`
- HCC model comparison：`reports/stage2_real_hcc_smoke/model_comparison.tsv`

## 关键配置

- 主图配置：`configs/manuscript/main_figures_v2.json`
- Extended Data 配置：`configs/manuscript/extended_data_figures_v1.json`
- Supplementary tables 配置：`configs/manuscript/supplementary_tables_v1.json`
- Submission package 配置：`configs/manuscript/submission_package_v1.json`

工程约定：

- CLI 入口位于 `scripts/`。
- 可调参数集中在 `configs/**/*.json`。
- 脚本只负责加载配置并执行，不在脚本中维护长参数表。

## 重跑入口

主图：

```bash
pixi run --environment core python scripts/manuscript/build_all_main_figures.py
```

Extended Data：

```bash
pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py
```

Supplementary table index：

```bash
pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py
```

Submission package：

```bash
pixi run --environment core python scripts/manuscript/build_submission_package.py
```

Architecture adjudication kit example：

```bash
PYTHONPATH=src python scripts/manuscript/run_architecture_adjudication.py --config configs/manuscript/architecture_adjudication_example_v1.json
```

Python compile check：

```bash
pixi run --environment core python -m compileall src/wtbench/manuscript scripts/manuscript
```

## 冻结预测与不重跑边界

手稿图版生成阶段重跑 source data 生成和渲染，但不重跑 GEARS 训练。GEARS 相关 panel 读取冻结预测、评分和 sweep 产物，并在 manifest 中记录输入文件 SHA256。

当前不做：

- 不重训 GEARS。
- 不把 K562 升为 co-primary。
- 不新增 entrant family。
- 不扩 Stage 3 discovery。
- 不强行解决 run-level metadata。
- 不无限扩 axis。
- 不新增 Frangieh / Replogle 正式分析，除非 revision 明确要求。

## legacy 数据身份边界

`data/raw/stage1a/candidates/dixit_2016_raw.h5ad` 与 GSE90063 K562 TF-pool 描述不匹配，当前按 Frangieh-like legacy object 处理，不再作为有效 Dixit 输入引用。所有可写入手稿的 Dixit / K562 evidence 均来自重新整理的 GSE90063 7d / 13d temporal panel。
