# Genome Biology 投稿清单 v1

## 目标定位

- 目标期刊：Genome Biology。
- 文章类型：Research。
- 主线：truth-anchored benchmark / functional genomics resource。
- 不采用的定位：新 SOTA 模型、软件-only 文章、drug target discovery 文章。

## 已整理文件

- 投稿前单入口工作区：`manuscript/README.md`
- 投稿前文件总索引：`manuscript/file_index.txt`
- 投稿前正文副本：`manuscript/text/manuscript_draft_v1.md`
- 投稿前 cover letter 副本：`manuscript/text/cover_letter_v1.md`
- 投稿前 figure legends 副本：`manuscript/text/figure_legends_v1.md`
- Genome Biology 正文草案：`docs/genome_biology_manuscript_draft_v1.md`
- Cover letter 草案：`docs/genome_biology_cover_letter_v1.md`
- 投稿清单：`docs/genome_biology_submission_checklist_v1.md`
- 投稿收口 handoff：`docs/genome_biology_finalization_handoff_v1.md`
- Additional files 说明：`docs/genome_biology_additional_files_v1.md`
- 图文一致性审计：`docs/genome_biology_figure_text_audit_v1.md`
- Final wording audit：`docs/genome_biology_final_wording_audit_v1.md`
- Word count：`docs/genome_biology_word_count_v1.md`
- Preprint role audit：`docs/genome_biology_preprint_role_audit_v1.md`
- Submission final index：`docs/genome_biology_submission_final_index_v1.md`
- 主图 legends：`docs/main_manuscript_figure_legends_v1.md`
- Extended Data legends：`docs/extended_data_figure_legends_v1.md`
- 投稿包总清单：`reports/manuscript_submission_package_v1/submission_package_manifest.json`
- Supplementary Tables workbook：`reports/manuscript_submission_package_v1/supplementary_tables_v1.xlsx`
- 投稿前主图与 panel 文件：`manuscript/figures/`
- 投稿前 Extended Data 与 panel 文件：`manuscript/extended_data/`
- 投稿前 Additional files：`manuscript/additional_files/`
- 投稿前 source-data manifests：`manuscript/source_data_manifests/`

## Genome Biology 格式核对

- 250 词以内结构化 Abstract，包含 Background / Results / Conclusions：已满足。
- Keywords 3-10 个：已满足。
- Background / Results / Discussion / Conclusions / Methods：已满足。
- Methods 放在 Conclusions 后：已满足。
- Abbreviations：已加入。
- Declarations：已加入全部必需小标题。
- Figures 按文中首次出现顺序编号：当前满足。
- 多 panel 图作为单个 composite file：当前整图 PDF/PNG 已生成。
- Additional files 需要按 Additional file 1 等命名，并在正文单独列出文件名、格式、标题和说明：正文已加入草案，待最终导出。

## 投稿前必须补齐

0. HCC38/HCC1143 身份 wording：二者是乳腺癌细胞系；投稿文本不得把 `HCC` 定义为 hepatocellular carcinoma，也不应单独写 `HCC context` 而不说明 HCC38/HCC1143。
1. 作者姓名、单位、通讯作者邮箱。
2. Competing interests。
3. Funding。
4. Authors' contributions。
5. Acknowledgements。
6. Public repository 链接、数据 accession、代码 archive DOI。
7. AI use statement 已给出可提交草案，仍需作者最终确认。
8. References 正式列表：草案已插入正文；两个非必要 preprint 已移除，仍需作者确认是否恢复。
9. Additional files 的最终命名和文件说明：已完成 staging 和 hash 说明，仍需按投稿系统最终上传方式确认。

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
- Additional file 3：Submission package file manifest，`submission_package_file_manifest.tsv`。

当前三个文件均小于 BMC Additional file 20 MB 单文件上限。若期刊系统要求 source data 逐图上传，则以 `reports/manuscript_figures_v2/` 与 `reports/manuscript_extended_data_v1/` 中的 panel-level source data / manifest 为准。

上传 staging 目录：优先使用 `manuscript/additional_files/`。`reports/genome_biology_submission_upload_v1/` 保留为生成来源副本。

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

## Manuscript hardening 入口

当前文字治理以 `manuscript/text/`、`manuscript/audits/` 和 `docs/genome_biology_final_wording_audit_v1.md` 为准。旧 hardening 计划已归档到 `backup/obsolete_figure_set_2026-05-01/`，不再作为当前投稿入口。
