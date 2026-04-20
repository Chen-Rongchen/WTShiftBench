# Manuscript figure redesign plan v1

## 文档定位

本文档记录当前主稿文字和图注收口之后的下一阶段工作：重新用代码绘制 Figure 1-6 与 Extended Data Fig. 1-10。

本阶段不是新增分析，也不是重开 claim boundary。目标是让图像视觉设计、panel 组织和图中文字匹配已经收口的 manuscript grammar。

## 当前输入源

当前 redraw 的唯一文字输入源为：

- 正文：`manuscript/text/manuscript_draft_v1.md`
- 图注：`manuscript/text/figure_legends_v1.md`
- 版本说明：`docs/manuscript_version_control_note_v1.md`

当前图像文件位于：

- 主图：`manuscript/figures/`
- Extended Data：`manuscript/extended_data/`

这些图像文件可作为数据完整性和 panel coverage 参考，但不视为最终视觉版。

## Redraw 原则

- 不新增分析。
- 不改变 source data。
- 不改变 claim boundary。
- 不升级 K562、RNAi、axis 或 anchor 的证据层级。
- 不把附图写成新的主结果。
- 图中文字必须跟 `manuscript/text/figure_legends_v1.md` 的当前 wording 一致。
- 每张图仍保留 source data TSV 和 panel manifest JSON。

## 主图 redraw 任务

| 图 | 当前功能 | Redraw 目标 |
|----|----------|-------------|
| Fig. 1 | truth object / operational benchmark definition | 更明确呈现 object-first workflow、CRISPR DepMap primary bridge 和 adjudication grammar |
| Fig. 2 | shared anchor tiering | 强化 recurrence 与 target-proof 的边界，避免 anchor 被读成 causal validation |
| Fig. 3 | model adjudication triad | 清楚呈现 backbone / shift-excess / separation 三指标和 baseline-GEARS 非对称 trade-off |
| Fig. 4 | GEARS finite-budget sweep | 突出 prespecified local rebuttal test 和 stop rule，而不是一般调参失败 |
| Fig. 5 | axis-level interpretation | 将 transcription/chromatin 显示为 qualified interpretive axis，不显示为 formal closure |
| Fig. 6 | boundary machinery | 将 covariate、K562、RNAi 组织为 claim boundary，而不是额外验证阶梯 |

## Extended Data redraw 任务

Extended Data Fig. 1-10 的 redraw 目标是支持主图，不升级主张。当前图注已经完成 wording 同步，重画时应保留以下身份：

- ED1：dataset and endpoint admission。
- ED2：full target-level joint grid。
- ED3：anchor sensitivity and claim tiering。
- ED4：full HCC38/HCC1143 model recovery detail。
- ED5：GEARS finite-budget sweep and prespecified stop rule。
- ED6：full axis annotation and bootstrap support。
- ED7：K562 temporal supplementary evidence detail。
- ED8：CRISPR versus RNAi endpoint detail。
- ED9：covariate audit and wording boundary。
- ED10：reproducibility and claim governance。

## 建议提交粒度

建议将版本控制拆成三个提交：

1. Manuscript text and legend hardening。
2. Figure redraw code and configs。
3. Regenerated figure artifacts and manifests。

作者元信息、funding、competing interests、contributions、acknowledgements 和 DOI 建议另起提交。
