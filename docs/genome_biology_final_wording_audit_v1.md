# Genome Biology final wording audit v1

## 状态

更新日期：2026-04-18。

用途：记录 submission-ready 前的越界措辞检查。本文档不新增分析，不改变 frozen claim boundary。

## 审计范围

- `docs/genome_biology_manuscript_draft_v1.md`
- `docs/genome_biology_cover_letter_v1.md`
- `docs/genome_biology_figure_legends_v1.md`
- `docs/main_manuscript_figure_legends_v1.md`
- `docs/extended_data_figure_legends_v1.md`
- `docs/genome_biology_submission_checklist_v1.md`
- `docs/genome_biology_finalization_handoff_v1.md`
- `docs/genome_biology_figure_text_audit_v1.md`
- `MANUSCRIPT_REPRODUCIBILITY.md`

## 高风险词组

扫描词组：

- `proved`
- `validated`
- `validation`
- `fully deconfounded`
- `external generalization`
- `primary winner`
- `baseline beats`
- `deep models fail`
- `content-level replication`
- `co-primary`
- `matched endpoint`
- `established`
- `causal proof`

## 处理结果

### 已保留但属于边界性否定用法

以下词组只出现在禁止、否定或边界语境中，未构成 overclaim：

- `co-primary`
- `matched endpoint`
- `primary winner`
- `content-level replication`
- `fully deconfounded`
- `causal proof`
- `discovery`

示例口径：

- K562 is not a primary co-pillar。
- RNAi DEMETER2 is not a matched primary endpoint。
- GEARS is not the HCC primary winner。
- No individual anchor is interpreted as fully deconfounded causal evidence。

### 已修正

- AI use statement 从 `[To be confirmed]` 占位改为可提交的保守 disclosure。
- 正式 References 草案移除了两个非必要 preprint，降低 background citation 风险。

### 不建议修改

- `architecture-form confirmation` 保留。它是 A0 tier 的正式内部术语，且用于 supplementary K562 architecture-form 层，不等同于 content-level validation。
- `validation summary` 保留在 Extended Data axis legend 中。这里指 axis annotation / validation summary 表，不承担主 claim。

## 当前结论

未发现需要停止投稿或重开分析的越界措辞。剩余风险主要来自作者信息、declarations、repository / DOI 和最终上传系统格式，而不是 science claim wording。
