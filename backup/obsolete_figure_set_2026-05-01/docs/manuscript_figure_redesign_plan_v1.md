# Manuscript figure redesign plan v1

## 文档定位

本文档记录当前主稿文字和图注收口之后的下一阶段工作：重新用代码绘制 Figure 1-5 与 Extended Data Fig. 1-11。

本阶段不是新增分析，也不是重开 claim boundary。目标是让图像视觉设计、panel 组织和图中文字匹配已经收口的 manuscript grammar。

## 对标结论

本轮对标材料分为两类：

- 视觉基调：`s41592-025-02772-6.pdf`。只参考其 benchmark 图版语法：白底、低装饰、数据优先、少量功能性色彩、每个 panel 回答一个明确问题。
- 投稿完整度：`Genome Biology/s13059-026-04070-6_reference.pdf` 与 `Genome Biology/s13059-026-04063-5_reference.pdf`。这两篇提示当前稿件的主要差距不在新增分析，而在图版成熟度、公开资源、Additional files 和 submission metadata。

当前稿件最接近的类型是 Genome Biology benchmark/resource paper，而不是纯 model/method paper。因此 redraw 阶段应优先服务 framework/resource identity：object definition、model adjudication、boundary governance 和 reproducibility。

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
- 每张主图只回答一个 benchmark 问题，不做海报式总览。
- panel 文字优先使用定义性短语和证据层级短语，不使用 discovery rhetoric。
- 色彩用于区分证据层级、endpoint 或模型类别，不作为装饰。

## 当前 redraw 状态

| 图 | 状态 | 当前输出 |
|----|------|----------|
| Fig. 1 | 定版 6-panel data-forward：(a) truth-first flow strip + 三列 object 定义；(b) 25/75 joint-grid 示意，四象限标签为统一字号的 Q1/Q2/Q3/Q4 tag + 统一小字号 descriptor，Q1 绿色、其余深灰；(c) HCC38 target-level joint grid（共享 0/0.25/0.5/0.75/1 刻度、只保留 25/75 虚线阈值、右侧 Q1 标签"贴近真实 y + 仅向下挤"以减少引线交叉）；(d) HCC1143 同结构；(e) grid composition，底边轴线精确截断在 100% 不越到 panel f；(f) bridge strength headline，aligned Spearman rho 点 + Fisher z 95% CI + 1000 次 target→DepMap permutation null 95% envelope，两行统计说明统一小号浅灰置于 x 轴下居中。旧 8-panel 版本已彻底替换，投稿目录只留 a–f。 | 投稿：`manuscript/figures/Figure_1.pdf`，`manuscript/figures/Figure_1/Figure_1.{png,pdf}`，`manuscript/figures/Figure_1/panels/Figure_1_panel_{a..f}.{png,pdf}`；开发版：`reports/manuscript_figures_v2/fig1_truth_object/figure1.{png,pdf}` |
| Fig. 2 | 已定版 6-panel evidence-first 结构，投稿目录已同步替换（a/b 行 + c/d 行 + e TVD evidence + f claim matrix）；TVD matrix 已由原 Extended Data Fig. 9 Panel i 提升为主图 Panel e，ED9 回到 8 panel | 投稿：`manuscript/figures/Figure_2/Figure_2.{png,pdf}`，`manuscript/figures/Figure_2/panels/Figure_2_panel_{a..f}.{png,pdf}`；开发版：`reports/manuscript_figures_v2/fig2_anchor_tiering/figure2.{png,pdf}` |
| Fig. 3 | 已定版 **3-panel** data-forward 结构：(a) three-metric overview heatmap / (b) baseline-vs-GEARS paired-dot headline / (c) backbone-separation trade-off space（all entrants，共享坐标语法与 Fig 4b）。原 main-figure (d) per-cell-line 读数已不放在此图，**Extended Data Fig. 4** 承接 per-context 与全矩阵。caption、source data 与 `manuscript/text/figure_legends_v1.md` §Fig. 3 口径一致。 | 投稿：`manuscript/figures/Figure_3/Figure_3.{png,pdf}`，`manuscript/figures/Figure_3/panels/Figure_3_panel_{a..c}.{png,pdf}`；开发版：`reports/manuscript_figures_v2/fig3_model_tradeoff/figure3.{png,pdf}` |
| Fig. 4 | 已定版 3-panel data-forward 结构：(a) pre-specified finite-budget GEARS sweep schematic（3×3×2 grid / max_candidates=6 / nearest_to_base）；(b) unified rebuttal trade-off map（backbone recovery × structure/context separation，10 个对象同度量同 pipeline，共享坐标语法与 Fig. 3c）；(c) reference-anchored gap plot（linear controls 对比 shared-mean baseline，Δ 标注，无 CI）。旧 d-h panel 已彻底删除。L1–L4 硬冻结语言、caption、source data 与 `manuscript/text/figure_legends_v1.md` §Fig. 4 口径一致。 | 投稿：`manuscript/figures/Figure_4/Figure_4.{png,pdf}`，`manuscript/figures/Figure_4/panels/Figure_4_panel_{a..c}.{png,pdf}`；开发版：`reports/manuscript_figures_v2/fig4_sweep_controls/figure4.{png,pdf}` |
| Fig. 5 | 已前移为 claim-boundary adjudication 结构（原 Fig. 6）：(a) boundary architecture schematic（三层 boundary 概念图）；(b) covariate boundary compact evidence（mean TVD 对比，TVD>0.25 标记）；(c) temporal and endpoint hierarchy boundary（K562 7d/13d temporal stratification + CRISPR vs RNAi 四 context 对比）；(d) final claim boundary（Primary readout / Supplementary evidence / Sensitivity endpoint / Not claimed）。旧 Fig. 6 目录已从投稿主图目录移除。 | 投稿：`manuscript/figures/Figure_5/Figure_5.{png,pdf}`，`manuscript/figures/Figure_5/panels/Figure_5_panel_{a..d}.{png,pdf}`；开发版：`reports/manuscript_figures_v2/fig6_boundary/figure6.{png,pdf}` |
| Extended Data Fig. 11 | 原主文 Fig. 5 下放为 2-panel axis adjudication： (a) axis-level explanatory balance scatter；(b) axis adjudication profile。用于支持 transcription/chromatin 仅能写作 qualified axis，而不作为主文强生物学发现图。 | 投稿：`manuscript/extended_data/Extended_Data_Figure_11/Extended_Data_Figure_11.{png,pdf}`；开发版：`reports/manuscript_figures_v2/fig5_axis_interpretation/figure5.{png,pdf}` |
| Extended Data Fig. 1-11 | ED6 保持原 full axis annotation / bootstrap support；ED11 承接原 Fig. 5 的精简 axis adjudication 图。 | 待最终 package refresh |

## 主图 redraw 任务

| 图 | 当前功能 | Redraw 目标 |
|----|----------|-------------|
| Fig. 1 | truth object / operational benchmark definition | 固定为 6-panel data-forward 结构：(a) truth-first flow strip + pre-specified recovery-object 三列说明、(b) 25/75 joint-grid category schematic、(c/d) HCC38 与 HCC1143 的 target-level joint grid（共享 0/0.25/0.5/0.75/1 刻度、虚线 25/75 阈值、右边栏堆叠 Q1 gene 标签）、(e) grid composition summary（Q1 计数内嵌、Q2/Q3 零计数显式说明）、(f) bridge-strength headline（aligned Spearman rho + Fisher 95% CI + 1000 次 target→DepMap permutation null 95% envelope，empirical p=0.001）；不再把 endpoint table 或 allowed/not-allowed claim list 作为主图 panel。Bridge strength 升为独立 panel 是为了让 Fig 1 自洽承载 object definition 与 object 是否 above-null 两件事，而不用依赖 Extended Data Fig. 1 |
| Fig. 2 | shared anchor tiering | 固定为 6-panel evidence-first 结构：(a) paired shift/dependency dumbbell（默认按 shared rank 排序，可读性为先）、(b) 紧凑 recurrence / joint-quantile matrix（低墨水、含数值、Q1 绿色边框、PFDN5 行高亮）、(c) cutoff-stability bar（只区分 stable vs cutoff-sensitive，四个 stable anchor 统一绿色，不在此层预判 covariate）、(d) final stable-anchor shift/dependency detail（图例右上、不加 covariate `*`）、(e) per-anchor covariate TVD matrix（4 anchor × 10 axis，TVD>0.25 标 `*`，PFDN5 整行 clean）、(f) compact claim-tier matrix（wording 与颜色合并为 Claim tier 一列，顶/底横线闭合表格）。narrative 顺序为 a→d 结构证据 → e 协变量证据 → f 结论矩阵；`*` 仅在 (e) 使用，不在 a/c/d 中预告结论。旧 supporting-only detail / tier-count bar / allowed-not-allowed wording panel 已降级到图注或 Extended Data；TVD matrix 原先位于 ED9 Panel i，现已提升至主图 (e)，ED9 回到 8 panel |
| Fig. 3 | model adjudication triad | 清楚呈现 backbone / shift-excess / separation 三指标和 baseline-GEARS 非对称 trade-off |
| Fig. 4 | GEARS finite-budget sweep / prespecified local rebuttal test | 已定版 3-panel：(a) schematic design，(b) unified rebuttal trade-off map（同 TSV 同 pipeline，10 对象），(c) reference-anchored gap plot（linear controls vs baseline，Δ 标注）。冻结语言见 `manuscript/figures/Figure_4/figure4_redesign_freeze.md`。禁止 `tuning failure` / `hidden recipe winner` / `coverage explains the gap` / 代码名上图 / 红绿 tag。 |
| Fig. 5 | boundary machinery | 将 covariate、K562、RNAi 组织为主文 final claim boundary，而不是额外验证阶梯 |
| Extended Data Fig. 11 | axis-level interpretation | 将 transcription/chromatin 显示为 qualified interpretive axis，不显示为 formal closure |

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

## 立即执行顺序

1. **Figure 1 已定版**：投稿目录 6-panel (a–f)、旧 8-panel 版本已彻底替换；legend（`manuscript/text/figure_legends_v1.md` §Fig. 1）、methods（`manuscript/text/manuscript_draft_v1.md` §Truth-DepMap bridge construction，新增 Fisher z 95% CI + 1000-perm null 段落）、source data（`manuscript/figures/Figure_1/panels/Figure_1_panel_f_source_data.tsv` 字段 `ci_method = fisher_z_transform`, `null_iterations = 1000`, `empirical_p_two_sided ≈ 0.001`, `null_type = target_to_depmap_permutation`）三者口径一致。
2. **Figure 2 已定版**：投稿目录 6-panel (a–f) evidence-first 结构已覆盖 `manuscript/figures/Figure_2/`；legend（`manuscript/text/figure_legends_v1.md` §Fig. 2）已按 a/b/c/d 结构层 → e TVD evidence → f claim matrix 的顺序重写，`*` 仅限 (e)。TVD matrix 已由 ED9 Panel i 提升至主图 (e)，ED9 同步回退到 8 panel（`extended_data_figure9.py`、`manuscript/figures/Extended_Data_Fig_9/` 与 `figure_legends_v1.md` §Extended Data Fig. 9 已同步）。panel source data 与 `submission_package_manifest.json` / `submission_package_file_manifest.tsv` 已重建，SHA256 一致。
3. 推进 Figure 3 redraw：审阅 `reports/manuscript_figures_v2/fig3_model_tradeoff/figure3.{png,pdf}` prototype，按 Fig. 1/Fig. 2 相同 data-forward 节奏打磨，再覆盖到 `manuscript/figures/Figure_3/`。
4. Figure 4 和 Figure 5 依序同方式处理，每图先审再覆盖投稿目录；不要让 prototype 与投稿并存。
5. Figure 1-5 全部确认后，再统一处理 Extended Data Fig. 1-11。
6. **配色（color palette）统一冻结时点**：Figure 1 与 Figure 2 当前已共享 `src/wtbench/manuscript/_palette.py` 定义的 sage-olive-sand 色系（primary green / supporting amber / sensitive amber / gray 中性），但正式冻结主图与 Extended Data 的最终配色要等 **5 张主图 + 11 张 Extended Data 全部 redraw 完成**后再统一 pass 一次，避免前后风格漂移。当前阶段 Figure 3-5 可继续沿用 `_palette.py`，但不要把任何配色细节写进 frozen language。
7. 最后再做 public repository / Zenodo DOI / Additional files / metadata 的投稿闭环。
