# 主文图版生成记录 v1

## 生成范围

本轮已完成 6 张主图的重新生成：

- Fig. 1：truth object。
- Fig. 2：anchor tiering。
- Fig. 3：model recovery trade-off。
- Fig. 4：GEARS sweep and linear controls。
- Fig. 5：axis-level interpretation。
- Fig. 6：covariate / temporal / endpoint boundary。

同时已完成 Extended Data Fig. 10：

- ED Fig. 1：dataset and endpoint admission。
- ED Fig. 2：full target-level joint grid。
- ED Fig. 3：anchor sensitivity and claim tiering。
- ED Fig. 4：full HCC model recovery detail。
- ED Fig. 5：GEARS sweep and stop rule。
- ED Fig. 6：full axis annotation and bootstrap support。
- ED Fig. 7：K562 temporal evidence detail。
- ED Fig. 8：CRISPR versus RNAi endpoint detail。
- ED Fig. 9：covariate audit details and wording boundary。
- ED Fig. 10：reproducibility and claim governance。

旧 `reports/manuscript_figures/figure1/` 图版已按用户要求排除，不作为当前手稿图版来源。

## 输出位置

- Fig. 1：`reports/manuscript_figures_v2/fig1_truth_object/`
- Fig. 2：`reports/manuscript_figures_v2/fig2_anchor_tiering/`
- Fig. 3：`reports/manuscript_figures_v2/fig3_model_tradeoff/`
- Fig. 4：`reports/manuscript_figures_v2/fig4_sweep_controls/`
- Fig. 5：`reports/manuscript_figures_v2/fig5_axis_interpretation/`
- Fig. 6：`reports/manuscript_figures_v2/fig6_boundary/`
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

## 输出完整性

每张主图均有 8 个小图 panel。每个 panel 均保存：

- `figureX_panelY.png`
- `figureX_panelY.pdf`
- `figureX_panelY_source_data.tsv`
- `figureX_panelY_manifest.json`

每张整图均保存：

- `figureX.png`
- `figureX.pdf`
- `figureX_source_data.tsv`
- `figureX_panel_manifest.json`

当前完整性核对结果：

| 图 | panel PNG | panel PDF | panel source | panel manifest | 整图 PNG | 整图 PDF | 整图 source | 整图 manifest |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fig. 1 | 8 | 8 | 8 | 8 | 1 | 1 | 1 | 1 |
| Fig. 2 | 8 | 8 | 8 | 8 | 1 | 1 | 1 | 1 |
| Fig. 3 | 8 | 8 | 8 | 8 | 1 | 1 | 1 | 1 |
| Fig. 4 | 8 | 8 | 8 | 8 | 1 | 1 | 1 | 1 |
| Fig. 5 | 8 | 8 | 8 | 8 | 1 | 1 | 1 | 1 |
| Fig. 6 | 8 | 8 | 8 | 8 | 1 | 1 | 1 | 1 |

合计：6 张主图，每张 36 个可追溯文件，共 216 个图版、源数据和 manifest 文件。

ED Fig. 1-10 也采用同一规范，各包含 36 个可追溯文件，合计 360 个可追溯文件。

## 可重跑入口

全部主图：

- `pixi run --environment core python scripts/manuscript/build_all_main_figures.py`

已实现 Extended Data：

- `pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py`

单张主图：

- Fig. 1：`pixi run --environment core python scripts/manuscript/build_figure1_truth_object.py`
- Fig. 2：`pixi run --environment core python scripts/manuscript/build_figure2_anchor_tiering.py`
- Fig. 3：`pixi run --environment core python scripts/manuscript/build_figure3_model_tradeoff.py`
- Fig. 4：`pixi run --environment core python scripts/manuscript/build_figure4_sweep_controls.py`
- Fig. 5：`pixi run --environment core python scripts/manuscript/build_figure5_axis_interpretation.py`
- Fig. 6：`pixi run --environment core python scripts/manuscript/build_figure6_boundary.py`

GEARS 训练不在作图阶段重跑，只读取冻结评分、预测和 sweep 产物。

## 数据停机检查

各图脚本已加入关键 sanity check：

- Fig. 1：检查 HCC38/HCC1143 Q1 anchor 数和 joint-grid 来源。
- Fig. 2：检查 PFDN5、PMF1、PRPF6、ZNF131 的最终 claim tier。
- Fig. 3：检查 baseline、formal GEARS 的 backbone/separation headline 数字。
- Fig. 4：检查 baseline、formal GEARS、best sweep、max shift-excess sweep 和 coverage。
- Fig. 5：检查 `transcription / chromatin` 的 formal positive axis 身份、shift R2、dependency R2、bootstrap stability 和最终 tier。
- Fig. 6：检查 CRISPR endpoint hierarchy、K562 temporal stratification 和最终边界。

本轮生成未触发停机条件。

## 哈希追踪

所有输入文件、panel source data、panel PNG/PDF、整图 source data、整图 PNG/PDF 的 SHA256 已写入对应 manifest：

- panel 级：`reports/manuscript_figures_v2/fig*/panels/*_manifest.json`
- 整图级：`reports/manuscript_figures_v2/fig*/figure*_panel_manifest.json`

manifest 同时记录生成脚本路径、生成时间、git commit 和 `git status --short`，用于后续复现实验与提交前审计。
