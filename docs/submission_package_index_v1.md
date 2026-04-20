# 投稿包索引 v1

## 当前单入口工作区

当前投稿前整理入口为：

- `manuscript/README.md`
- `manuscript/file_index.txt`

该目录已把正文草案、cover letter、figure legends、主图、Extended Data、panel a-h、小图 source data / manifest、Additional files、source-data manifests 与 audit 文档集中到一个工作区。`docs/` 与 `reports/` 保留为生成来源、审计来源和可重跑来源。

## 当前主入口

主文正文草案：

- `manuscript/text/manuscript_draft_v1.md`
- `docs/main_manuscript_submission_draft_v1.md`
- `docs/main_manuscript_submission_draft_v2.md`
- `docs/genome_biology_manuscript_draft_v1.md`

Genome Biology 专用投稿材料：

- `manuscript/text/cover_letter_v1.md`
- `manuscript/text/figure_legends_v1.md`
- `manuscript/text/availability_and_reproducibility_v1.md`
- `docs/genome_biology_cover_letter_v1.md`
- `docs/genome_biology_submission_checklist_v1.md`
- `docs/genome_biology_figure_legends_v1.md`
- `docs/baseline_model_interpretation_and_journal_strategy_v1.md`

项目入口与执行计划：

- `README.md`
- `plan.md`
- `scripts/README.md`
- `configs/README.md`

主文 figure legends：

- `docs/main_manuscript_figure_legends_v1.md`

Extended Data figure legends：

- `docs/extended_data_figure_legends_v1.md`

Data / Code availability 与复现说明：

- `docs/main_manuscript_availability_and_reproducibility_v1.md`

完整图版规划：

- `docs/manuscript_complete_figure_plan_v1.md`

图版生成记录：

- `docs/manuscript_figure_generation_record_v1.md`

投稿前 readiness checklist：

- `docs/submission_readiness_checklist_v1.md`

补充表索引：

- `configs/manuscript/supplementary_tables_v1.json`
- `reports/manuscript_supplementary_tables_v1/supplementary_table_summary.tsv`
- `reports/manuscript_supplementary_tables_v1/supplementary_table_file_index.tsv`
- `reports/manuscript_supplementary_tables_v1/supplementary_table_manifest.json`

投稿包总清单与补充表 workbook：

- `manuscript/source_data_manifests/submission_package_file_manifest.tsv`
- `manuscript/source_data_manifests/submission_package_manifest.json`
- `manuscript/additional_files/Additional_file_1_supplementary_tables_v1.xlsx`
- `manuscript/additional_files/Additional_file_2_submission_package_manifest.json`
- `manuscript/additional_files/Additional_file_3_submission_package_file_manifest.tsv`
- `configs/manuscript/submission_package_v1.json`
- `reports/manuscript_submission_package_v1/submission_package_file_manifest.tsv`
- `reports/manuscript_submission_package_v1/submission_package_summary.tsv`
- `reports/manuscript_submission_package_v1/submission_package_manifest.json`
- `reports/manuscript_submission_package_v1/supplementary_tables_v1.xlsx`

Extended Data 执行计划：

- `docs/extended_data_execution_plan_v1.md`

已生成 Extended Data：

- ED Fig. 1：`reports/manuscript_extended_data_v1/edfig1_dataset_endpoint_admission/`
- ED Fig. 2：`reports/manuscript_extended_data_v1/edfig2_full_target_grid/`
- ED Fig. 3：`reports/manuscript_extended_data_v1/edfig3_anchor_sensitivity/`
- ED Fig. 4：`reports/manuscript_extended_data_v1/edfig4_model_detail/`
- ED Fig. 5：`reports/manuscript_extended_data_v1/edfig5_gears_sweep/`
- ED Fig. 6：`reports/manuscript_extended_data_v1/edfig6_axis_annotation/`
- ED Fig. 7：`reports/manuscript_extended_data_v1/edfig7_k562_temporal/`
- ED Fig. 8：`reports/manuscript_extended_data_v1/edfig8_endpoint_hierarchy/`
- ED Fig. 9：`reports/manuscript_extended_data_v1/edfig9_covariate_audit/`
- ED Fig. 10：`reports/manuscript_extended_data_v1/edfig10_reproducibility/`

## 主图产物

主图目录：

- 投稿前整理目录：`manuscript/figures/`
- Fig. 1：`reports/manuscript_figures_v2/fig1_truth_object/`
- Fig. 2：`reports/manuscript_figures_v2/fig2_anchor_tiering/`
- Fig. 3：`reports/manuscript_figures_v2/fig3_model_tradeoff/`
- Fig. 4：`reports/manuscript_figures_v2/fig4_sweep_controls/`
- Fig. 5：`reports/manuscript_figures_v2/fig5_axis_interpretation/`
- Fig. 6：`reports/manuscript_figures_v2/fig6_boundary/`

每张主图均有：

- 8 个 panel PNG。
- 8 个 panel PDF。
- 8 个 panel source-data TSV。
- 8 个 panel manifest JSON。
- 1 个整图 PNG。
- 1 个整图 PDF。
- 1 个整图 source-data TSV。
- 1 个整图 panel-manifest JSON。

`manuscript/figures/Figure_*/panels/` 中另存了每张主图的 panel a-h，包含 PNG、PDF、source data TSV 和 manifest JSON，便于逐 panel 审稿或上传系统要求拆分时使用。

## 重跑入口

全部主图：

- `pixi run --environment core python scripts/manuscript/build_all_main_figures.py`

补充表索引：

- `pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py`

投稿包总清单与补充表 workbook：

- `pixi run --environment core python scripts/manuscript/build_submission_package.py`

已实现的 Extended Data：

- `pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py`
- `pixi run --environment core python scripts/manuscript/build_extended_data_figure1.py`
- `pixi run --environment core python scripts/manuscript/build_extended_data_figure2.py`
- `pixi run --environment core python scripts/manuscript/build_extended_data_figure3.py`
- `pixi run --environment core python scripts/manuscript/build_extended_data_figure4.py`
- `pixi run --environment core python scripts/manuscript/build_extended_data_figure5.py`
- `pixi run --environment core python scripts/manuscript/build_extended_data_figure6.py`
- `pixi run --environment core python scripts/manuscript/build_extended_data_figure7.py`
- `pixi run --environment core python scripts/manuscript/build_extended_data_figure8.py`
- `pixi run --environment core python scripts/manuscript/build_extended_data_figure9.py`
- `pixi run --environment core python scripts/manuscript/build_extended_data_figure10.py`

配置：

- `configs/manuscript/main_figures_v2.json`

单图入口：

- `scripts/manuscript/build_figure1_truth_object.py`
- `scripts/manuscript/build_figure2_anchor_tiering.py`
- `scripts/manuscript/build_figure3_model_tradeoff.py`
- `scripts/manuscript/build_figure4_sweep_controls.py`
- `scripts/manuscript/build_figure5_axis_interpretation.py`
- `scripts/manuscript/build_figure6_boundary.py`

共用代码：

- `src/wtbench/manuscript/`

## 当前验证状态

已通过：

- `pixi run --environment core python scripts/manuscript/build_all_main_figures.py`
- `pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py`
- `pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py`
- `pixi run --environment core python scripts/manuscript/build_submission_package.py`
- `pixi run --environment core python scripts/manuscript/build_extended_data_figure10.py`
- `pixi run --environment core python -m compileall src/wtbench/manuscript scripts/manuscript`

完整性核对结果：

| 图 | panel PNG | panel PDF | panel source | panel manifest | 整图 PNG | 整图 PDF | 整图 source | 整图 manifest |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fig. 1 | 8 | 8 | 8 | 8 | 1 | 1 | 1 | 1 |
| Fig. 2 | 8 | 8 | 8 | 8 | 1 | 1 | 1 | 1 |
| Fig. 3 | 8 | 8 | 8 | 8 | 1 | 1 | 1 | 1 |
| Fig. 4 | 8 | 8 | 8 | 8 | 1 | 1 | 1 | 1 |
| Fig. 5 | 8 | 8 | 8 | 8 | 1 | 1 | 1 | 1 |
| Fig. 6 | 8 | 8 | 8 | 8 | 1 | 1 | 1 | 1 |

补充表索引当前覆盖 10 个 supplementary table group、55 个冻结文件或 manifest，均已记录 SHA256、文件大小和 TSV 行列数。

ED Fig. 1-10 当前均采用同一完整性规范：每张 8 个 panel PNG、8 个 panel PDF、8 个 panel source-data TSV、8 个 panel manifest JSON、1 个整图 PNG、1 个整图 PDF、1 个整图 source-data TSV、1 个整图 panel-manifest JSON。10 张 ED 图合计 360 个可追溯文件。

投稿包总清单当前覆盖 9 个类别、639 个文件；补充表 workbook 当前包含 31 个 TSV 数据 sheet，并保留 table summary、file index 和 sheet index。

## Claim Boundary 索引

主文不得越界写法已经集中记录在：

- `docs/main_manuscript_submission_draft_v1.md`
- `docs/manuscript_complete_figure_plan_v1.md`
- `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`

当前核心边界：

- GEARS 不是 overall HCC primary winner。
- shared-mean baseline 是 backbone primary reference。
- PFDN5 是 `primary_but_qualified`，不是 fully deconfounded strongest anchor。
- PMF1、PRPF6、ZNF131 是 `supporting_only`。
- transcription/chromatin 是 `primary_axis_but_qualified`，不是 fully established shared explanatory architecture。
- K562 是 supplementary architecture-form evidence，不是 primary co-pillar。
- CRISPR DepMap 是 primary bridge readout，RNAi DEMETER2 是 weaker sensitivity endpoint。
- discovery / phenotype shifter 仍然是 gated downstream layer。

## 剩余人工选择

当前代码、图版、补充表索引、补充表 workbook 和投稿包总清单已经形成 Genome Biology 可审阅版本。目标期刊当前固定为 Genome Biology；Science Advances 仅作为需 broad-impact 改写的冲刺备选，Advanced Science 不作为优先目标。剩余工作主要是投稿元信息和期刊上传格式：

1. 是否保留 6 张主图，或按期刊版面把 Fig. 5 移入 Extended Data。
2. 是否把 Methods 保留在主文末尾，或拆成 Online Methods / Supplementary Methods。
3. 是否按目标期刊模板补齐 references、author contribution、competing interests 和 acknowledgements。
4. 是否按目标期刊最终字号与宽度做全图版式微调。
