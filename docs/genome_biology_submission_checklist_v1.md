# Genome Biology 投稿清单 v1

## 目标定位

- 目标期刊：Genome Biology。
- 文章类型：Research。
- 主线：truth-anchored benchmark / functional genomics resource。
- 不采用的定位：新 SOTA 模型、软件-only 文章、drug target discovery 文章。

## 已整理文件

- Genome Biology 正文草案：`docs/genome_biology_manuscript_draft_v1.md`
- Cover letter 草案：`docs/genome_biology_cover_letter_v1.md`
- 投稿清单：`docs/genome_biology_submission_checklist_v1.md`
- 投稿收口 handoff：`docs/genome_biology_finalization_handoff_v1.md`
- 主图 legends：`docs/main_manuscript_figure_legends_v1.md`
- Extended Data legends：`docs/extended_data_figure_legends_v1.md`
- 投稿包总清单：`reports/manuscript_submission_package_v1/submission_package_manifest.json`
- Supplementary Tables workbook：`reports/manuscript_submission_package_v1/supplementary_tables_v1.xlsx`

## Genome Biology 格式核对

- 100 词以内非结构化 Abstract：已满足。
- Keywords 3-10 个：已满足。
- Background / Results / Discussion / Conclusions / Methods：已满足。
- Methods 放在 Conclusions 后：已满足。
- Abbreviations：已加入。
- Declarations：已加入全部必需小标题。
- Figures 按文中首次出现顺序编号：当前满足。
- 多 panel 图作为单个 composite file：当前整图 PDF/PNG 已生成。
- Additional files 需要按 Additional file 1 等命名：待最终导出。

## 投稿前必须补齐

1. 作者姓名、单位、通讯作者邮箱。
2. Competing interests。
3. Funding。
4. Authors' contributions。
5. Acknowledgements。
6. Public repository 链接、数据 accession、代码 archive DOI。
7. 是否保留 Methods 中的 AI use statement，以及具体措辞。
8. References 正式列表。
9. Additional files 的最终命名和文件说明。

## 投稿前 reviewer-risk reduction 必做

执行入口：`docs/genome_biology_submission_execution_plan_v1.md`。

状态：已完成并提交为 `174c809 Prepare Genome Biology submission readiness docs`。

已完成：

1. Title / Abstract / Cover letter 重新定位为 framework/resource/adjudication。
2. 2024-2026 prior-art literature scan。
3. prior-art positioning 段落。
4. GEARS sweep budget sanity check。
5. GEARS finite-budget / stop-rule 透明化写作。
6. 三指标相关性 quick check。
7. metric diagnostic 图或补充呈现。
8. shared_mean_baseline leakage / artifact appendix。
9. dixit legacy 一次性澄清。
10. Discussion Limitations 四条正面写入。
11. 顶层 `MANUSCRIPT_REPRODUCIBILITY.md`。
12. 内部 Top-10 reviewer questions 文档。

已完成：

13. 三指标 permutation null。
14. `barcode_gem_group` design-proxy residualization check。
15. relaxed cutoff sensitivity for shared anchors。
16. Frangieh / Replogle revision-round admission contract confirmation。

已完成：

17. 最小 community adjudication kit。

## 建议 Additional files

- Additional file 1：Supplementary Tables workbook，`supplementary_tables_v1.xlsx`。
- Additional file 2：Submission package manifest，`submission_package_manifest.json`。
- Additional file 3：Main and Extended Data figure source-data manifest index，来自总 manifest。
- Additional file 4：Code and configuration manifest，来自总 manifest 中 `figure_code` 和 `configs` 类别。

## 当前不需要重做的部分

- 不需要重跑 GEARS 训练。
- 不需要保留旧图。
- 不需要把论文包装成 SOTA 模型文章。
- 不需要把 K562 写成 primary co-pillar。
- 不需要把 RNAi 写成主 endpoint。

## 当前核心边界

- GEARS 不是 HCC primary winner。
- shared-mean baseline 是 backbone recovery primary reference。
- PFDN5 是 `primary_but_qualified`。
- PMF1、PRPF6、ZNF131 是 `supporting_only`。
- transcription/chromatin 是 `primary_axis_but_qualified`。
- K562 是 supplementary architecture-form evidence。
- CRISPR DepMap 是 primary bridge readout。
- RNAi DEMETER2 是 weaker sensitivity endpoint。
