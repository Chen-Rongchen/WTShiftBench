# Manuscript submission workspace

## 用途

这是 Genome Biology 投稿前的人可读工作目录。这里的文件从 `docs/` 和 `reports/` 复制而来，方便集中查看、打包和上传。

原则：

- 原始 source data 和 manifest 仍以 `reports/` 中的冻结产物为准。
- 本目录不改变任何分析结果或 claim boundary。
- 每张整图和每个 panel 小图都已单独整理。

## 当前版本管理

当前投稿前主稿以 `manuscript/text/manuscript_draft_v1.md` 和 `manuscript/text/figure_legends_v1.md` 为唯一正文 source of truth。`docs/` 下的早期 manuscript draft 文件保留为历史草稿或路线记录，不再作为当前投稿稿的同步源。

版本说明见：`docs/manuscript_version_control_note_v1.md`。

当前正文和图注已完成 boundary / grammar audit；现有图像文件仍是上一轮生成产物，后续需要按当前正文和图注重新用代码绘制。图版重画计划见：`docs/manuscript_figure_redesign_plan_v1.md`。

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
- `Figure_6.pdf`

每张图也有独立子目录，例如：

- `manuscript/figures/Figure_1/`

每个 Figure 子目录包含：

- 整图 PDF：`Figure_N.pdf`
- 整图 PNG：`Figure_N.png`
- 整图 source data：`Figure_N_source_data.tsv`
- 整图 panel manifest：`Figure_N_panel_manifest.json`
- panel 小图目录：`panels/`

每个 panel 小图目录包含 a-h：

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

- 主图目录：6 张整图，每张含 a-h panel 小图、source data 和 manifest。
- Extended Data：10 张整图，每张含 a-h panel 小图、source data 和 manifest。
- Additional files：3 个上传候选文件。
