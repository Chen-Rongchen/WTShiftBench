# Manuscript version control note v1

## 当前唯一正文源

当前投稿前主稿以以下文件为唯一正文 source of truth：

- `manuscript/text/manuscript_draft_v1.md`
- `manuscript/text/figure_legends_v1.md`

`docs/` 下的早期 manuscript draft 文件保留为历史草稿或路线记录，不再作为当前投稿稿的同步源。

## 当前版本状态

当前主稿已完成本轮 boundary / grammar audit：

- Abstract、Background、Results、Methods、Discussion、Conclusions 已围绕同一套 benchmark grammar 同步。
- Figure 1-5 主图图注已完成 claim-boundary 同步。
- Extended Data Fig. 1-11 图注已完成 support / sensitivity / boundary 层级同步。
- CRISPR DepMap 保留为 primary bridge readout。
- RNAi DEMETER2 保留为 weaker cross-platform sensitivity endpoint。
- K562 temporal panel 保留为 supplementary architecture-form / bounded bridge-form evidence。
- GEARS 保留为 architecture trade-off diagnosis，不是 HCC38/HCC1143 primary winner。

## 当前图版状态

当前 `manuscript/figures/` 和 `manuscript/extended_data/` 中的图像文件是上一轮生成产物。图注和正文已经收口，但图像视觉设计尚未进入最终投稿版。

下一阶段工作是按当前正文和图注重新设计并重画 Figure 1-5 与 Extended Data Fig. 1-11。该阶段只允许修改绘图代码、图中文字、panel 布局和导出文件，不新增分析、不改变 source data、不改变 claim boundary。

## 仍需作者补齐

以下内容由作者人工补齐，不从仓库内容推断：

- 作者姓名和排序。
- 作者单位。
- 通讯作者姓名和邮箱。
- Funding。
- Competing interests。
- Authors' contributions。
- Acknowledgements。
- Public repository URL。
- Archive DOI。
- 最终 Data / Code availability 中的公开访问链接。

## 后续版本规则

- 正文修改优先落在 `manuscript/text/manuscript_draft_v1.md`。
- 图注修改优先落在 `manuscript/text/figure_legends_v1.md`。
- 图像重画优先通过 `scripts/manuscript/` 与 `configs/manuscript/` 中的配置化入口完成。
- 旧版 `docs/*draft*.md` 不再全文同步，除非明确需要生成新的历史快照。
- 若需要提交 git，建议将主稿文本更新与作者元信息更新分开提交。
- 图像重画建议单独提交，不与本文字 hardening 提交混在一起。
