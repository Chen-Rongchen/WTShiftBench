# Manuscript submission workspace

## 一句话入口

当前最新主稿只看这里：

- 正文：`manuscript/text/manuscript_draft_v1.md`
- 图注：`manuscript/text/figure_legends_v1.md`

这两个文件是当前投稿前唯一正文 source of truth。文件名里的 `v1` 表示 `manuscript/` 投稿工作区里的第一个正式整理版，不表示旧版。

## 当前状态

当前正文和图注已经完成 boundary / grammar audit：

- Abstract、Background、Results、Methods、Discussion、Conclusions 已围绕同一套 benchmark grammar 同步。
- Figure 1-5 主图图注已同步。
- Extended Data Fig. 1-11 图注已同步。
- CRISPR DepMap 是 primary bridge readout。
- RNAi DEMETER2 是 weaker cross-platform sensitivity endpoint。
- K562 temporal panel 是 supplementary architecture-form / bounded bridge-form evidence。
- GEARS 是 architecture trade-off diagnosis，不是 HCC38/HCC1143 primary winner。

Figure 1-5 主图全部已定版并同步到投稿目录：
- Figure 1：6-panel（a–f）data-forward truth object
- Figure 2：6-panel（a–f）evidence-first anchor tiering
- Figure 3：4-panel（a–d）model adjudication triad
- Figure 4：3-panel（a–c）prespecified local rebuttal test
- Figure 5：4-panel（a–d）boundary architecture + claim ledger（原 Figure 6 前移）
- Extended Data Fig. 11：2-panel（a–b）axis adjudication（原 Figure 5 下放）

`manuscript/extended_data/` 中的 Extended Data Fig. 1-10 保持原收束计划；Extended Data Fig. 11 承接原主文 Figure 5 的 axis-level adjudication。

## 下一步工作

## 当前阶段

**Figure 1-5 主图已全部定版**，下一步是 Extended Data Fig. 1-10 的收束 redraw 与 Extended Data Fig. 11 的索引打包确认。

原则不变：不改 source data、不新增分析、不改 claim boundary。

### Extended Data 收束计划

- 计划文档：`docs/extended_data_redesign_plan_v1.md`
- 目标：80 panel → 49 panel（每张 ED 从 8 panel 收束至 3–6 panel）
- 收束策略：合并重复 panel、删除主图已覆盖内容、整合主图下放内容

### 执行顺序建议

1. ED Fig. 5（已冻结，最先执行）
2. ED Fig. 6（保留 full axis annotation / bootstrap support）
3. ED Fig. 9（接收当前 Fig. 5 / 原 Fig. 6 下放内容）
4. ED Fig. 7 / ED Fig. 8（接收当前 Fig. 5 / 原 Fig. 6 下放内容，可并行）
5. ED Fig. 1-4 / ED Fig. 10（独立，任意顺序）
6. ED Fig. 11（原主文 Fig. 5 下放的 axis adjudication）

投稿前仍需作者人工补齐作者信息、单位、通讯邮箱、funding、competing interests、author contributions、acknowledgements、public repository / archive DOI。

## 不再作为当前稿的文件

`docs/` 下的早期 manuscript draft 文件只作为历史草稿或路线记录，不再作为当前投稿稿同步源，包括：

- `docs/main_manuscript_submission_draft_v1.md`
- `docs/main_manuscript_submission_draft_v2.md`
- `docs/genome_biology_manuscript_draft_v1.md`

不要从这些文件继续复制正文或图注到当前稿。后续正文修改只落在 `manuscript/text/manuscript_draft_v1.md`；图注修改只落在 `manuscript/text/figure_legends_v1.md`。

## 版本管理文档

- 版本说明：`docs/manuscript_version_control_note_v1.md`
- 图版重画计划：`docs/manuscript_figure_redesign_plan_v1.md`
- 投稿状态：`docs/submission_prep_status_v1.md`

最近一次文本收口提交：

- `5a9bc65 Harden manuscript grammar and define figure redraw plan`

该提交之后，`manuscript/README.md` 与 Figure 1 redraw 代码已有新的未提交工作；提交前需要先确认是否把这些 redraw 相关改动单独成 commit。

## 用途和原则

这是 Genome Biology 投稿前的人可读工作目录。这里的文件从 `docs/` 和 `reports/` 复制而来，方便集中查看、打包和上传。

原则：

- 原始 source data 和 manifest 仍以 `reports/` 中的冻结产物为准。
- 本目录不改变任何分析结果或 claim boundary。
- 每张整图和每个 panel 小图都已单独整理。
- 下一阶段只重画图，不新增分析、不改变 source data、不改变 claim boundary。

## Text

目录：`manuscript/text/`

- `manuscript_draft_v1.md`：Genome Biology 正文草案。
- `cover_letter_v1.md`：cover letter 草案。
- `figure_legends_v1.md`：GB 合并 figure legends。
- `availability_and_reproducibility_v1.md`：Data / Code availability 与复现说明。

仍需作者补齐：作者姓名、单位、通讯邮箱、funding、competing interests、author contributions、acknowledgements、public repository / archive DOI。

## Main Figures

目录：`manuscript/figures/`

根目录保留投稿时最常用的整图 PDF：

- `Figure_1.pdf`
- `Figure_2.pdf`
- `Figure_3.pdf`
- `Figure_4.pdf`
- `Figure_5.pdf`

每张图也有独立子目录，例如：

- `manuscript/figures/Figure_1/`

每个 Figure 子目录包含：

- 整图 PDF：`Figure_N.pdf`
- 整图 PNG：`Figure_N.png`
- 整图 source data：`Figure_N_source_data.tsv`
- 整图 panel manifest：`Figure_N_panel_manifest.json`
- panel 小图目录：`panels/`

每个 panel 小图目录包含对应图版的 panel 小图。当前投稿目录中的上一轮主图多为 a-h；Figure 1 redraw prototype 已改为 a-e：

- `Figure_N_panel_a.pdf`
- `Figure_N_panel_a.png`
- `Figure_N_panel_a_source_data.tsv`
- `Figure_N_panel_a_manifest.json`

同样结构适用于 panel b-h。

## Extended Data Figures

目录：`manuscript/extended_data/`

每张 Extended Data figure 有独立子目录：

- `Extended_Data_Figure_1/`
- `Extended_Data_Figure_2/`
- ...
- `Extended_Data_Figure_10/`

每个目录包含：

- 整图 PDF。
- 整图 PNG。
- 整图 source data。
- 整图 panel manifest。
- `panels/` 中的 a-h 小图 PDF / PNG / source data / manifest。

## Additional Files

目录：`manuscript/additional_files/`

- `Additional_file_1_supplementary_tables_v1.xlsx`
- `Additional_file_2_submission_package_manifest.json`
- `Additional_file_3_submission_package_file_manifest.tsv`
- `README.md`：Additional files 的标题、说明、大小和 SHA256。

## Source Data And Manifests

目录：`manuscript/source_data_manifests/`

- `MANUSCRIPT_REPRODUCIBILITY.md`
- `submission_package_manifest.json`
- `submission_package_file_manifest.tsv`

## Audits

目录：`manuscript/audits/`

- `genome_biology_final_wording_audit_v1.md`
- `genome_biology_figure_text_audit_v1.md`
- `genome_biology_word_count_v1.md`
- `genome_biology_preprint_role_audit_v1.md`
- `shared_anchor_role_note_v1.md`

## File Index

完整文件索引：

- `manuscript/file_index.txt`

当前内容规模：

- 主图目录：5 张整图，每张含 panel 小图、source data 和 manifest。
  - Figure 1：6 panel（a-f）
  - Figure 2：6 panel（a-f）
  - Figure 3：4 panel（a-d）
  - Figure 4：3 panel（a-c）
  - Figure 5：4 panel（a-d）
  - Extended Data Fig. 11：2 panel（a-b），由原 Figure 5 下放。
- Extended Data：11 张整图，其中 ED1-10 保持原补充结构，ED11 为 axis adjudication。
- Additional files：3 个上传候选文件。
