# Extended Data 执行计划 v1

## 定位

Extended Data 的职责不是重复主图，而是解决审稿人会追问的完整性问题：

- 主图有没有隐藏全量对象。
- cutoff、covariate、endpoint、temporal 和模型 recipe 是否可追溯。
- 哪些结论被降级，降级依据是什么。

当前计划固定为 10 张 Extended Data 图。所有 ED 图也应沿用主图生产规范：panel PNG/PDF、source data、manifest、整图 source data 和整图 manifest。

## Extended Data Fig. 1：Dataset And Endpoint Admission

目的：说明 HCC、K562、DepMap CRISPR、DEMETER2 RNAi 的数据准入与 endpoint 映射。

建议 panels：

- a. HCC38/HCC1143 primary context admission。
- b. GSE90063 K562 7d/13d supplementary admission。
- c. DepMap CRISPR endpoint mapping。
- d. DEMETER2 RNAi endpoint conversion summary。
- e. Primary / supplementary / sensitivity endpoint hierarchy。
- f. Not-admitted external expansion candidates。

主要源表：

- `reports/stage2_truth_driven_bridge/HCC38/correlation_summary.tsv`
- `reports/stage2_truth_driven_bridge/HCC1143/correlation_summary.tsv`
- `reports/stage2_gse90063_qc/dixit_2016_k562_tf_7d_summary.tsv`
- `reports/stage2_gse90063_qc/dixit_2016_k562_tf_13d_summary.tsv`
- `reports/stage2_rnai_demeter2_conversion/summary.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`

## Extended Data Fig. 2：Full Target-Level Joint Grid

目的：展示主图 Fig. 1 压缩掉的全量 target-level grid 和标签。

建议 panels：

- a. HCC38 full target grid。
- b. HCC1143 full target grid。
- c. Grid category counts。
- d. All Q1 anchors。
- e. Transcriptomic-excess targets。
- f. Dependency-excess targets。

主要源表：

- `reports/stage2_truth_bridge_decomposition/target_level_joint_grid.tsv`
- `reports/stage2_truth_bridge_decomposition/target_level_grid_summary.tsv`
- `reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv`

## Extended Data Fig. 3：Anchor Sensitivity And Claim Tiering

目的：支持主图 Fig. 2 的 anchor tiering，展示 cutoff sensitivity 和降级依据。

建议 panels：

- a. Shared canonical anchor summary full table plot。
- b. Anchor cutoff stability。
- c. Control subsample sensitivity。
- d. PFDN5 tier rationale。
- e. PMF1/PRPF6/ZNF131 downgrade rationale。
- f. Cutoff-sensitive supporting objects。

主要源表：

- `reports/stage2_truth_bridge_decomposition/shared_canonical_anchor_summary.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/control_subsample_summary.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`

## Extended Data Fig. 4：Full HCC Model Recovery Detail

目的：展示主图 Fig. 3 压缩掉的模型、cell-line 和 per-target recovery 细节。

建议 panels：

- a. Full model comparison。
- b. Per-cell-line backbone recovery。
- c. Per-cell-line shift-excess identification。
- d. Per-cell-line structure/context separation。
- e. Baseline target metrics。
- f. GEARS target metrics。
- g. Foundation model target metrics。
- h. Null model reference。

主要源表：

- `reports/stage2_real_hcc_smoke/model_comparison.tsv`
- `reports/stage2_real_hcc_smoke/smoke_summary.tsv`
- `reports/stage2_real_hcc_smoke/details/**/target_expression_metrics.tsv`
- `reports/stage2_real_hcc_smoke/details/**/structure_scores.tsv`

## Extended Data Fig. 5：GEARS Sweep And Stop Rule

目的：支持主图 Fig. 4 的 recipe-control 结论，展示 sweep candidate、batch status 和 final adjudication。

建议 panels：

- a. Candidate manifest。
- b. Batch status。
- c. Sweep candidate backbone scores。
- d. Sweep candidate separation scores。
- e. Formal GEARS versus sweep candidates。
- f. Final stop-rule adjudication。

主要源表：

- `reports/stage2_gears_backbone_sweep/candidate_manifest.tsv`
- `reports/stage2_gears_backbone_sweep/batch_run/batch_status.tsv`
- `reports/stage2_gears_backbone_sweep/final_adjudication.md`
- `reports/stage2_real_hcc_smoke/model_comparison.tsv`

## Extended Data Fig. 6：Full Axis Annotation And Bootstrap

目的：支持主图 Fig. 5，展示 axis enrichment、validation、bootstrap 和 per-axis boundary。

建议 panels：

- a. Full axis explanatory scatter。
- b. Full bootstrap stability。
- c. Axis validation summary。
- d. Enrichment hit count。
- e. Database support count。
- f. Top recurrent terms。
- g. Formal versus preliminary axes。
- h. Axis claim boundary。

主要源表：

- `reports/stage2_truth_bridge_decomposition/axis_level_shared_explanatory_summary.tsv`
- `reports/stage2_truth_bridge_decomposition/axis_bootstrap_stability.tsv`
- `reports/stage2_axis_analysis/axis_summary.tsv`
- `reports/stage2_axis_analysis/axis_validation_summary.tsv`
- `reports/stage2_axis_analysis/axis_enrichment.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`

## Extended Data Fig. 7：K562 Temporal Evidence Detail

目的：支持主图 Fig. 6d-f，展示 K562 7d/13d temporal panel 的完整 A0/A1/B 分层。

建议 panels：

- a. 7d bridge summary。
- b. 13d bridge summary。
- c. Temporal bridge comparison。
- d. Temporal structure summary。
- e. 7d evidence tiers。
- f. 13d evidence tiers。
- g. Temporal panel calls。
- h. K562 claim boundary。

主要源表：

- `reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_bridge_summary.tsv`
- `reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_structure_summary.tsv`
- `reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_panel_calls.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_7d/dixit_evidence_tier_summary.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_evidence_tier_summary.tsv`

## Extended Data Fig. 8：CRISPR Versus RNAi Endpoint Detail

目的：支持主图 Fig. 6g，展示 CRISPR/RNAi endpoint hierarchy 的完整上下文。

建议 panels：

- a. HCC CRISPR/RNAi bridge Spearman。
- b. K562 CRISPR/RNAi bridge Spearman。
- c. CRISPR-RNAi endpoint agreement。
- d. Endpoint conversion summary。
- e. Context-specific endpoint hierarchy。
- f. RNAi sensitivity boundary。

主要源表：

- `reports/stage2_truth_driven_bridge/hcc38_hcc1143_rnai_endpoint_consistency/endpoint_consistency_summary.tsv`
- `reports/stage2_truth_driven_bridge/k562_rnai_endpoint_consistency/endpoint_consistency_summary.tsv`
- `reports/stage2_rnai_demeter2_conversion/summary.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`

## Extended Data Fig. 9：Covariate Audit Detail

目的：支持主图 Fig. 6a-c，展示 covariate audit 每个轴的影响和不能 fully deconfound 的原因。

建议 panels：

- a. Covariate balance summary。
- b. Barcode gem group mapping。
- c. Protospacer axis boundary。
- d. UMI/transcriptome signal axis boundary。
- e. Detected gene axis boundary。
- f. Anchor-tier impact of covariate audit。
- g. Allowed wording。
- h. Disallowed wording。

主要源表：

- `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/barcode_gem_group_mapping_note.md`
- `reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`

## Extended Data Fig. 10：Reproducibility And Claim Governance

目的：把主图 source data、manifest、supplementary tables 和 claim boundary 统一收口。

建议 panels：

- a. Main figure manifest overview。
- b. Supplementary table group overview。
- c. Source-data hash coverage。
- d. Claim matrix overview。
- e. Allowed wording matrix。
- f. Disallowed wording matrix。
- g. Rebuild entrypoints。
- h. GEARS training exemption boundary。

主要源表：

- `reports/manuscript_figures_v2/fig*/figure*_panel_manifest.json`
- `reports/manuscript_supplementary_tables_v1/supplementary_table_summary.tsv`
- `reports/manuscript_supplementary_tables_v1/supplementary_table_file_index.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`
- `configs/manuscript/main_figures_v2.json`
- `configs/manuscript/supplementary_tables_v1.json`

## 执行顺序

建议按以下顺序执行：

1. ED Fig. 10：先建立 reproducibility / claim governance 总览。
2. ED Fig. 3、6、9：补审稿最容易追问的 anchor、axis、covariate。
3. ED Fig. 4、5：补模型与 GEARS sweep 细节。
4. ED Fig. 7、8：补 K562 temporal 和 endpoint hierarchy。
5. ED Fig. 1、2：补 dataset admission 和 full target grid。

这个顺序优先锁定边界和复现，再补全量对象。
