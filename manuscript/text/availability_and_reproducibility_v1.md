# 主文 Availability 与复现说明 v1

## Data Availability

本项目的主文图版均从仓库内冻结产物重新生成。主图 source data 位于：

- `reports/manuscript_figures_v2/fig1_truth_object/figure1_source_data.tsv`
- `reports/manuscript_figures_v2/fig2_anchor_tiering/figure2_source_data.tsv`
- `reports/manuscript_figures_v2/fig3_model_tradeoff/figure3_source_data.tsv`
- `reports/manuscript_figures_v2/fig4_sweep_controls/figure4_source_data.tsv`
- `reports/manuscript_figures_v2/fig5_axis_interpretation/figure5_source_data.tsv`
- `reports/manuscript_figures_v2/fig6_boundary/figure6_source_data.tsv`

每个 panel 的 source data 位于对应图目录的 `panels/` 子目录，文件名格式为：

- `figureX_panelY_source_data.tsv`

每个 source data 文件对应一个 manifest，记录输入文件路径、SHA256、输出图版 SHA256、生成脚本、生成时间和 git 状态。

## Code Availability

主图生成代码位于：

- `src/wtbench/manuscript/`

主图 CLI 位于：

- `scripts/manuscript/`

主图配置位于：

- `configs/manuscript/main_figures_v2.json`

单图重跑入口：

- `pixi run --environment core python scripts/manuscript/build_figure1_truth_object.py`
- `pixi run --environment core python scripts/manuscript/build_figure2_anchor_tiering.py`
- `pixi run --environment core python scripts/manuscript/build_figure3_model_tradeoff.py`
- `pixi run --environment core python scripts/manuscript/build_figure4_sweep_controls.py`
- `pixi run --environment core python scripts/manuscript/build_figure5_axis_interpretation.py`
- `pixi run --environment core python scripts/manuscript/build_figure6_boundary.py`

全部主图重跑入口：

- `pixi run --environment core python scripts/manuscript/build_all_main_figures.py`

全部 Extended Data 重跑入口：

- `pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py`

补充表索引重跑入口：

- `pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py`

补充表索引配置：

- `configs/manuscript/supplementary_tables_v1.json`

补充表索引输出：

- `reports/manuscript_supplementary_tables_v1/supplementary_table_summary.tsv`
- `reports/manuscript_supplementary_tables_v1/supplementary_table_file_index.tsv`
- `reports/manuscript_supplementary_tables_v1/supplementary_table_manifest.json`

投稿包总清单与补充表 workbook 重跑入口：

- `pixi run --environment core python scripts/manuscript/build_submission_package.py`

投稿包配置：

- `configs/manuscript/submission_package_v1.json`

投稿包输出：

- `reports/manuscript_submission_package_v1/submission_package_file_manifest.tsv`
- `reports/manuscript_submission_package_v1/submission_package_summary.tsv`
- `reports/manuscript_submission_package_v1/submission_package_manifest.json`
- `reports/manuscript_submission_package_v1/supplementary_tables_v1.xlsx`

## Reproducibility Boundary

主图作图阶段重跑 source-data 生成和渲染，不重跑 GEARS 训练。GEARS 训练成本过高，因此 GEARS 相关 panel 读取冻结预测、评分和 sweep 产物，并在 manifest 中记录这些输入文件的 SHA256。

若关键 headline 数字、排序或 evidence tier 发生足以改变结论的漂移，对应脚本会停止生成，而不是覆盖当前图版。

当前停机检查覆盖：

- Fig. 1：Q1 anchor 数和 joint-grid 来源。
- Fig. 2：PFDN5、PMF1、PRPF6、ZNF131 的 claim tier。
- Fig. 3：baseline 和 formal GEARS 的 backbone/separation headline 数字。
- Fig. 4：baseline、formal GEARS、GEARS sweep 和 linear-control coverage。
- Fig. 5：CRISPR/RNAi endpoint hierarchy、K562 temporal stratification 和最终 claim boundary。
- Extended Data Fig. 4：descriptive axis-level signal space，用于展示 shift R² 与 dependency R² 的轴层分布。
- Extended Data Fig. 5：display targets 在 HCC38/HCC1143/K562 中的 pathway-response polarity 差异。
