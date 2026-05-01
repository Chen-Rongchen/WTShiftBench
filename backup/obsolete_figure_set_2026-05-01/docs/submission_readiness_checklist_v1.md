# 投稿前 readiness checklist v1

## 当前执行口径更新（2026-04-20）

Genome Biology reviewer-risk reduction 已完成并版本化。执行入口为：

- `manuscript/README.md`
- `docs/manuscript_hardening_plan_v1.md`
- `docs/genome_biology_submission_execution_plan_v1.md`
- `manuscript/source_data_manifests/MANUSCRIPT_REPRODUCIBILITY.md`

`manuscript/` 已整理为投稿前单入口工作区，包含 610 个文件，约 22 MB；主图、Extended Data 和 panel a-h 的 PDF/PNG/source data/manifest 均已集中复制到该目录。

已完成 A1-A12：

1. 重写 Title / Abstract / Cover letter framing。
2. prior-art literature scan。
3. prior-art positioning 段落。
4. GEARS sweep budget sanity check。
5. GEARS sweep / stop-rule 透明化写作。
6. metric orthogonality quick check。
7. metric diagnostic 最终呈现。
8. shared_mean_baseline leakage / artifact appendix。
9. dixit legacy 澄清。
10. Discussion Limitations 四条重写。
11. `MANUSCRIPT_REPRODUCIBILITY.md` 单入口整理。
12. Top-10 anticipated reviewer questions。

已完成 B13-B16：

13. 三指标 permutation null。
14. `barcode_gem_group` design-proxy residualization check。
15. relaxed cutoff sensitivity for shared anchors。
16. Frangieh / Replogle revision-round admission readiness。

已完成 C17：

17. 最小 community adjudication kit。

当前不再需要新增分析来支撑第一版投稿。剩余事项是作者元信息、references、declarations、公开归档 DOI、Additional files 编号与最终人工确认。

新增 hardening 风险：HCC38 和 HCC1143 是乳腺癌细胞系，不能把 `HCC` 定义为 hepatocellular carcinoma；投稿文本应优先写成 `HCC38/HCC1143 breast-cancer cell-line contexts` 或 `the two primary breast-cancer contexts`。

## 当前执行口径更新（2026-04-21）

主稿文本与图注已经完成本轮 boundary / grammar audit。当前唯一正文 source of truth 为：

- `manuscript/text/manuscript_draft_v1.md`
- `manuscript/text/figure_legends_v1.md`

版本管理说明见：

- `docs/manuscript_version_control_note_v1.md`

下一阶段工作已经从文字 hardening 转入 figure redesign：

- `docs/manuscript_figure_redesign_plan_v1.md`

该阶段只重画图，不新增分析、不改变 source data、不改变 claim boundary。

## 已完成

### 手稿文本

- 主文投稿稿 v2：`docs/main_manuscript_submission_draft_v2.md`
- Genome Biology 正文草案：`docs/genome_biology_manuscript_draft_v1.md`
- Genome Biology cover letter：`docs/genome_biology_cover_letter_v1.md`
- Genome Biology 投稿清单：`docs/genome_biology_submission_checklist_v1.md`
- Genome Biology 投稿收口 handoff：`docs/genome_biology_finalization_handoff_v1.md`
- Genome Biology figure legends：`docs/genome_biology_figure_legends_v1.md`
- Baseline 与投稿策略说明：`docs/baseline_model_interpretation_and_journal_strategy_v1.md`
- 主文 figure legends：`docs/main_manuscript_figure_legends_v1.md`
- Extended Data figure legends：`docs/extended_data_figure_legends_v1.md`
- Data / Code availability 与复现说明：`docs/main_manuscript_availability_and_reproducibility_v1.md`
- 投稿前单入口副本：`manuscript/text/`

### 图版

- 主图 Fig. 1-5 已生成当前版本：`reports/manuscript_figures_v2/`
- Extended Data Fig. 1-10 已生成上一轮版本；Extended Data Fig. 11 由 `reports/manuscript_figures_v2/fig5_axis_interpretation/` 生成。
- 投稿前整理副本：`manuscript/figures/` 与 `manuscript/extended_data/`
- 每张图均为 8 panel。
- 每个 panel 均有 PNG、PDF、source data TSV、manifest JSON。
- 每张整图均有 PNG、PDF、combined source data TSV、figure-level manifest JSON。
- 当前图像视觉设计未冻结为最终投稿版，需按当前正文和图注重新用代码绘制。

### 补充表与复现

- Supplementary table index：`reports/manuscript_supplementary_tables_v1/`
- Supplementary Tables workbook：`reports/manuscript_submission_package_v1/supplementary_tables_v1.xlsx`
- Submission package manifest：`reports/manuscript_submission_package_v1/submission_package_manifest.json`
- 投稿前 Additional files 副本：`manuscript/additional_files/`
- 投稿前 source-data manifest 副本：`manuscript/source_data_manifests/`
- 投稿前总索引：`manuscript/file_index.txt`
- 补充表配置：`configs/manuscript/supplementary_tables_v1.json`
- 投稿包配置：`configs/manuscript/submission_package_v1.json`
- 主图配置：`configs/manuscript/main_figures_v2.json`
- Extended Data 配置：`configs/manuscript/extended_data_figures_v1.json`

### 可重跑入口

- 主图：`pixi run --environment core python scripts/manuscript/build_all_main_figures.py`
- Extended Data：`pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py`
- Supplementary table index：`pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py`
- Submission package：`pixi run --environment core python scripts/manuscript/build_submission_package.py`

## 已验证

已通过：

- `pixi run --environment core python scripts/manuscript/build_all_main_figures.py`
- `pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py`
- `pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py`
- `pixi run --environment core python scripts/manuscript/build_submission_package.py`
- `pixi run --environment core python -m compileall src/wtbench/manuscript scripts/manuscript`

完整性：

- 5 张主图，按当前 panel 数保存整图、panel、source data 和 manifest。
- 11 张 Extended Data；ED1-10 保持原补充结构，ED11 为原主文 Fig. 5 下放的 2-panel axis adjudication。
- Supplementary table index 覆盖 10 个 table group、55 个冻结文件或 manifest。
- Submission package manifest 覆盖 9 个类别、639 个文件。
- Supplementary Tables workbook 包含 31 个 TSV 数据 sheet。

## 目标期刊策略

- 主投：Genome Biology。
- Science Advances：可作为冲刺备选，但需要把文章重写为 broad AI-for-biology / phenotype-relevant benchmark 叙事。
- Advanced Science：不作为优先目标，除非大幅改写成 biomedical innovation / translational life-science 叙事。

## 数据边界

当前未发现需要停机询问的数据偏差。

稳定结论：

- PFDN5：`primary_but_qualified`
- PMF1 / PRPF6 / ZNF131：`supporting_only`
- transcription/chromatin axis：`primary_axis_but_qualified`
- barcode_gem_group：design-proxy axis，不是 run-level resolved covariate
- K562 temporal panel：supplementary architecture-form support，不是 primary co-pillar
- CRISPR DepMap：primary bridge readout
- RNAi DEMETER2：weaker sensitivity endpoint
- GEARS：architecture trade-off diagnosis，不是 HCC primary winner

## 仍需人工决定

这些不是数据或代码缺口，而是投稿格式选择：

- 当前已采用 5 张主图；原 Fig. 5 已移到 Extended Data Fig. 11。
- Methods 是否放在主文末尾还是拆成 Online Methods / Supplementary Methods。
- 是否需要按目标期刊格式加入 references、author contribution、competing interests、acknowledgements。
- 是否需要统一图中文字大小到期刊最终版式。

## 当前建议

如果目标是先形成可审阅文字版本，当前主稿和图注已经足够内部审阅。

如果目标是正式投稿，当前主要剩余项是作者信息、references、declarations、公开归档 DOI、Additional files 编号，以及按当前图注重新绘制图版。

1. 选择目标期刊格式。
2. 按期刊模板整理 references 和 declarations。
3. 决定 Supplementary Tables 的提交格式。
4. 按 `docs/manuscript_figure_redesign_plan_v1.md` 重画 Figure 1-5 与 Extended Data Fig. 1-11。
5. 做一次全图版式审阅和最终导出。
