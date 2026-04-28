# Genome Biology figure-text audit v1

## 状态

更新日期：2026-04-18。

用途：记录 Nature Methods 风格重绘后，主文、figure legends、source data 与投稿包之间的图文一致性检查。

## 检查范围

- 正文：`docs/genome_biology_manuscript_draft_v1.md`
- GB legends：`docs/genome_biology_figure_legends_v1.md`
- 主图目录：`reports/manuscript_figures_v2/`
- Extended Data 目录：`reports/manuscript_extended_data_v1/`
- Submission package：`reports/manuscript_submission_package_v1/`
- Additional files staging：`reports/genome_biology_submission_upload_v1/`

## 图文件存在性

主图 PNG 均存在：

- Fig. 1：`reports/manuscript_figures_v2/fig1_truth_object/figure1.png`
- Fig. 2：`reports/manuscript_figures_v2/fig2_anchor_tiering/figure2.png`
- Fig. 3：`reports/manuscript_figures_v2/fig3_model_tradeoff/figure3.png`
- Fig. 4：`reports/manuscript_figures_v2/fig4_sweep_controls/figure4.png`
- Fig. 5：`reports/manuscript_figures_v2/fig6_boundary/figure6.png`

Extended Data PNG 均存在：

- Extended Data Fig. 1-5：`reports/manuscript_extended_data_v1/edfig*/edfig*.png`

## 重建校验

已通过：

```bash
MPLCONFIGDIR=/tmp/matplotlib_wtko_nmstyle PYTHONPATH=src pixi run --environment core python scripts/manuscript/build_all_main_figures.py
MPLCONFIGDIR=/tmp/matplotlib_wtko_nmstyle PYTHONPATH=src pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py
MPLCONFIGDIR=/tmp/matplotlib_wtko_nmstyle PYTHONPATH=src pixi run --environment core python scripts/manuscript/build_submission_package.py
```

主图输出校验：

- Fig. 1-5 均通过脚本内输出数量检查。

Extended Data 输出校验：

- Extended Data Fig. 1-5 通过脚本内输出数量检查。

## 关键数字核对

正文、Fig. 3 legend 与当前 source-data 叙事一致：

- shared-mean baseline backbone recovery：0.807。
- formal GEARS backbone recovery：0.660。
- formal GEARS structure-versus-context separation：0.428。
- shared-mean baseline structure-versus-context separation：0.353。
- best GEARS sweep backbone recovery：0.643。

正文、Fig. 5 legend 与 endpoint hierarchy 叙事一致：

- HCC38 CRISPR vs RNAi bridge Spearman：0.726 vs 0.276。
- HCC1143 CRISPR vs RNAi bridge Spearman：0.779 vs 0.384。
- K562 7d CRISPR vs RNAi bridge Spearman：0.733 vs 0.333。
- K562 13d CRISPR vs RNAi bridge Spearman：0.515 vs 0.300。

## Wording 边界核对

未发现越界 wording：

- GEARS 仍写成 architecture trade-off diagnosis，不写成 HCC primary winner。
- shared-mean baseline 仍写成 backbone reference，不写成 deployable model。
- K562 仍写成 supplementary architecture-form / bridge-form support，不写成 content-level replication 或 co-primary。
- RNAi DEMETER2 仍写成 weaker cross-platform sensitivity endpoint，不写成 matched primary endpoint。
- `barcode_gem_group` 仍写成 design-proxy axis，不写成 run-level resolved covariate。

## 风格核对

已按 `s41592-025-02772-6.pdf` 的可迁移视觉规则调整：

- 移除主图和 Extended Data 组合图内部的大号 narrative title。
- 保留 panel-first 布局。
- 使用白底、细轴线、浅灰网格。
- 降低配色饱和度。
- panel label 使用小写、加粗、适中字号。

## 剩余人工检查

- 正式投稿系统是否允许 `Extended Data Fig.` 作为命名；若系统只接受 supplementary figures，需要在上传阶段改名，不改变当前图内容。
- Figure source data 是逐图上传还是作为 manifest/additional file 上传，取决于投稿系统界面。
