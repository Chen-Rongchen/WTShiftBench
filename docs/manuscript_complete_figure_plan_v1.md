# 主文完整图版规划 v1

## 定位

本文件固定当前手稿的完整图版方案：**6 张主图 + 10 张 Extended Data**。

当前不再沿用旧版 4 张主图方案，也不再复用旧 `reports/manuscript_figures/figure1/` 产物。所有主图默认从源数据重新渲染。

参考模板为：

- `/home/data/gz0705/WTKO/s41592-025-02772-6.pdf`

借鉴模板的不是主图数量，而是图内逻辑：每张图都需要形成一个小闭环，即 **总览结果 -> 代表例 -> 定义/分解 -> 边界**。

## 主图总逻辑

1. 先定义 truth object。
2. 再证明 anchors 是分层证据。
3. 再展示模型没有真正恢复 backbone，而是出现 trade-off。
4. 再排除 recipe / coverage / embedding control 这些简单反驳。
5. 再解释 axis 层到哪里为止。
6. 最后用 covariate、K562 temporal panel、endpoint hierarchy 收住边界。

## 当前生成状态

截至本轮作图，6 张主图已经全部按 panel 级别重新生成；旧 `reports/manuscript_figures/figure1/` 产物不再作为图版来源。

主图产物目录：

- Fig. 1：`reports/manuscript_figures_v2/fig1_truth_object/`
- Fig. 2：`reports/manuscript_figures_v2/fig2_anchor_tiering/`
- Fig. 3：`reports/manuscript_figures_v2/fig3_model_tradeoff/`
- Fig. 4：`reports/manuscript_figures_v2/fig4_sweep_controls/`
- Fig. 5：`reports/manuscript_figures_v2/fig5_axis_interpretation/`
- Fig. 6：`reports/manuscript_figures_v2/fig6_boundary/`

每张图当前均包含：

- 8 个 panel PNG。
- 8 个 panel PDF。
- 8 个 panel source-data TSV。
- 8 个 panel manifest JSON。
- 1 个整图 PNG。
- 1 个整图 PDF。
- 1 个整图 source-data TSV。
- 1 个整图 panel-manifest JSON。

因此每张主图 36 个可追溯文件，6 张主图合计 216 个图版/源数据/manifest 文件。

## Fig. 1

**标题**

`A truth-first benchmark defines the fitness-relevant transcriptomic bridge object`

**核心问题**

我们到底在评估什么 truth object？

**Panels**

- a. 研究框架示意：真实扰动转录组 -> truth-DepMap bridge -> frozen architecture -> model recovery adjudication -> gated discovery。
- b. 数据和 endpoint 总览：HCC38、HCC1143、`real_shift_mean_abs`、CRISPR DepMap dependency、bridgeable targets。
- c. Q1-Q4 joint grid 定义：shift high/low 与 dependency high/low 如何划分。
- d. HCC38 target-level joint grid。
- e. HCC1143 target-level joint grid。
- f. 两条 cell line 的 grid composition：Q1_anchor、Q4_low_information、middle band 比例。
- g. 两条 HCC cell line 的 CRISPR bridge strength summary。
- h. 本图边界：truth object exists，但不是 fully deconfounded causal proof。

## Fig. 2

**标题**

`Shared anchors form a tiered target-level bridge rather than clean primary objects`

**核心问题**

哪些 target 是 anchor？这些 anchor 能写多强？

**Panels**

- a. Shared canonical anchor ranking：PFDN5、PMF1、PRPF6、ZNF131 等的 shift quantile / dependency quantile。
- b. Anchor recurrence heatmap：每个 anchor 是否在 HCC38 和 HCC1143 都进入 Q1。
- c. Anchor cutoff stability：PFDN5、PMF1、PRPF6、ZNF131 的 stability = 1.00。
- d. Representative anchor mini-panels：PFDN5 与 PMF1/PRPF6/ZNF131 的 shift-dependency 对照。
- e. Sensitive supporting objects：ENY2、NPM1、RPS3、RUVBL2、ZBTB17 等只能作为 `supporting_but_sensitive`。
- f. Evidence tier bar：`primary_but_qualified`、`supporting_only`、`supporting_but_sensitive`、`preliminary_only`。
- g. Anchor claim matrix：PFDN5 = `primary_but_qualified`；PMF1/PRPF6/ZNF131 = `supporting_only`。
- h. 禁写边界：不能写 fully deconfounded anchors，也不能写某个单基因 anchor 证明整个 bridge。

## Fig. 3

**标题**

`Current entrants do not outperform the backbone baseline but reveal a recovery trade-off`

**核心问题**

模型有没有恢复 frozen truth object？

**Panels**

- a. HCC formal model comparison：所有 entrants 的 `backbone_recovery_score`。
- b. 三指标 heatmap：backbone recovery、shift-excess identification、structure-vs-context separation。
- c. Baseline vs GEARS headline comparison：baseline backbone 0.807 vs GEARS 0.660；GEARS separation 0.428 vs baseline 0.353。
- d. Trade-off scatter：x = backbone recovery，y = structure/context separation。
- e. Representative recovery panel：baseline 与 GEARS 在一个 shared backbone target set 上的恢复对照。
- f. Shift-excess panel：显示 GEARS/sweep candidates 的 deviation/separation 优势没有转化为 backbone superiority。
- g. Model family grouping：baseline、GEARS、scGPT、Geneformer、linear controls 分组比较。
- h. 主结论边界：GEARS = architecture trade-off diagnosis；`shared_mean_baseline` = backbone primary reference；不写 model recovery proved。

## Fig. 4

**标题**

`Recipe and embedding controls do not close the backbone gap`

**核心问题**

模型没赢是不是因为 recipe 没调好、coverage 不够、embedding 没用对？

**Panels**

- a. GEARS backbone sweep candidate plot：所有 sweep candidate 的 backbone recovery，baseline dashed line = 0.807。
- b. Sweep trade-off scatter：backbone recovery vs structure/context separation。
- c. Shift-excess across sweep：部分 candidate 可提升 shift-excess，但仍不能成为 backbone winner。
- d. Stop-rule schematic：这轮 sweep 只动 epoch/checkpoint、learning rate、weight decay，没有换 truth object 或 scoring system。
- e. Linear-control schematic：`lm_train_lowrank`、`lm_G_scgpt_ridge`、`lm_G_geneformer_ridge` 的控制逻辑。
- f. Linear-control ranking：`lm_G_geneformer_ridge > lm_train_lowrank > lm_G_scgpt_ridge`，但均低于 baseline backbone。
- g. Coverage/control panel：ridge controls target coverage = 1.000，排除 coverage 缺口作为主解释。
- h. 解释边界：gap 更像 task-structure / direction-level mismatch，不是“再调一个 recipe 就能赢”。

## Fig. 5

**标题**

`Axis-level interpretation is informative but remains partially supported`

**核心问题**

truth object 的 biological axis 解释到哪里为止？

**Panels**

- a. Axis-level explanatory scatter：shift R2 vs dependency R2，标出 transcription/chromatin。
- b. Formal axis call summary：shared backbone axis、transcriptomic-heavy axis、dependency-heavy axis、preliminary axes。
- c. Bootstrap stability heatmap：各 axis dominant call 与 stability。
- d. Axis validation dot plot：enrichment hits、database support、per-target consistency。
- e. Transcription/chromatin focus：shift R2 = 0.092，dep R2 = 0.000，targets = ENY2/TADA3。
- f. Broader partially supported axes：chromatin remodeling、TGF-beta/BMP、ER stress/UPR、RNA processing、ribosome/nucleolar。
- g. Preliminary/mixed axes：显示多数 axes 不是同级 formal evidence。
- h. 解释边界：transcription/chromatin = `primary_axis_but_qualified`；不写 fully established shared explanatory architecture。

## Fig. 6

**标题**

`Covariate, temporal and endpoint analyses define the final claim boundary`

**核心问题**

最终主张能保留到哪里，哪里必须降级？

**Panels**

- a. 五轴 covariate audit overview：barcode_gem_group、protospacer axes、UMI/transcriptome signal axes、detected genes axes。
- b. Anchor claim tier before/after covariate audit：PFDN5 保留 `primary_but_qualified`；PMF1/PRPF6/ZNF131 降为 `supporting_only`。
- c. barcode_gem_group boundary：HCC38 -> aggrMH001-3；HCC1143 -> aggrMH004-6；design-proxy not run-resolved。
- d. K562 temporal panel overview：GSE90063 7d/13d；13d 是 primary supplementary bridge test，7d 是 early-bridge probe。
- e. Temporal stratification：7d rank alignment stronger；13d mean shift larger；两者均为 backbone_plus_shift_excess。
- f. A0/A1/B supplementary tier matrix：A0 confirmed；A1 supporting；B not eligible。
- g. Endpoint hierarchy：HCC38、HCC1143、K562 7d、K562 13d 中 CRISPR bridge Spearman 均强于 RNAi DEMETER2。
- h. Final boundary matrix：CRISPR = primary bridge readout；RNAi = weaker sensitivity endpoint；K562 not primary co-pillar；discovery gated。

## Extended Data

1. Extended Data Fig. 1：dataset overview、HCC/K562 target admission、DepMap endpoint mapping。
2. Extended Data Fig. 2：完整 target-level joint grid 和所有 target 标签。
3. Extended Data Fig. 3：anchor cutoff sensitivity、control subsampling、formal interval。
4. Extended Data Fig. 4：full HCC entrant comparison、per-cell-line model metrics、alternative recovery summaries。
5. Extended Data Fig. 5：GEARS backbone sweep 全候选、recipe summary、batch status。
6. Extended Data Fig. 6：full axis enrichment、bootstrap、per-target consistency。
7. Extended Data Fig. 7：K562 13d/7d temporal panel 细节与 A0/A1/B tier evidence。
8. Extended Data Fig. 8：CRISPR DepMap vs RNAi DEMETER2 endpoint consistency 细节。
9. Extended Data Fig. 9：covariate audit per-axis/per-target detail。
10. Extended Data Fig. 10：final claim matrix、allowed/disallowed wording、reproducibility/runtime entrypoints。

## 作图生产规范

每张主图必须按 panel 级别生产和保存，不能只输出最终 combined figure。

### Panel 级输出

每个 panel 单独保存：

- `figureX_panelY.pdf`
- `figureX_panelY.png`
- `figureX_panelY_source_data.tsv`
- `figureX_panelY_manifest.json`

最终整图再额外保存：

- `figureX.pdf`
- `figureX.png`
- `figureX_source_data.tsv`
- `figureX_panel_manifest.json`

### 代码必须可重跑

除已明确豁免的 GEARS 训练外，每个 panel 对应的计算与 source-data 生成代码必须可以从当前仓库产物重跑。

每张图的脚本需要包含两个阶段：

1. build source data：从 `reports/**/*.tsv`、`reports/**/*.json`、`reports/**/*.md` 或其它冻结产物生成 panel source data。
2. render panel / assemble figure：从 panel source data 生成 panel 图和整图。

不允许手工改图后只保存图片而不保存对应 source data。

### 数据偏差停机规则

作图脚本必须对关键 headline 数字做 sanity check。若从冻结产物重算出的 source data 与当前手稿/报告中已经冻结的 headline 数字发生足以改变结论的偏差，脚本应停止，不继续覆盖图版产物。

默认规则：

- 只属于显示精度的四舍五入差异可以继续，但必须进入 source data 和 manifest。
- 若关键指标偏差超过预设 tolerance，或排序/claim tier 发生变化，停止并人工确认。
- 对 Fig. 3/Fig. 4，必须检查 `shared_mean_baseline`、formal `GEARS`、GEARS sweep candidate 的 backbone/separation/shift-excess headline 数字。
- 对 Fig. 1/Fig. 2，必须检查 Q1 anchor 数、shared anchor set 和 anchor claim tier。
- 对 Fig. 5，必须检查 `transcription / chromatin` 仍为唯一 formal positive axis，且 `shift R2`、`dependency R2`、bootstrap stability 和 claim tier 没有改变结论。
- 对 Fig. 6，必须检查 CRISPR vs RNAi endpoint hierarchy、K562 A0/A1/B tier 和 covariate boundary。

GEARS 训练不重跑；因此 GEARS 相关 sanity check 只比较冻结评分/预测产物与当前图版 source data。

### 哈希记录

每个 `figureX_panelY_manifest.json` 必须记录：

- panel id
- panel title
- 生成脚本路径
- 生成时间
- 输入文件路径列表
- 每个输入文件的 SHA256
- panel source data 的 SHA256
- panel PDF 的 SHA256
- panel PNG 的 SHA256
- 若该 panel 使用冻结模型预测产物，需要记录预测产物路径和 SHA256
- claim boundary / allowed wording

每张整图的 `figureX_panel_manifest.json` 需要汇总所有 panel manifest，并额外记录：

- assembled PDF SHA256
- assembled PNG SHA256
- source-data combined TSV SHA256
- git commit hash 或当前 `git rev-parse HEAD`
- 若工作树非 clean，需要记录 `git status --short`

### GEARS 训练豁免

GEARS 训练不作为作图阶段重跑项，因为训练成本过高。

GEARS 相关 panel 只允许引用已经冻结的训练/预测/评分产物，例如：

- `reports/stage2_real_hcc_smoke/model_comparison.tsv`
- `reports/stage2_real_hcc_smoke/details/**`
- `reports/stage2_gears_backbone_sweep/**`

这些冻结产物本身必须记录 SHA256。作图代码可以重跑评分汇总和渲染，但不重跑 GEARS training。

### 推荐目录结构

新版图版统一输出到：

```text
reports/manuscript_figures_v2/
  fig1_truth_object/
    panels/
      figure1_panela.pdf
      figure1_panela.png
      figure1_panela_source_data.tsv
      figure1_panela_manifest.json
    figure1.pdf
    figure1.png
    figure1_source_data.tsv
    figure1_panel_manifest.json
  fig2_anchor_tiering/
  fig3_model_tradeoff/
  fig4_sweep_controls/
  fig5_axis_tiering/
  fig6_boundary/
```

### 推荐脚本结构

```text
scripts/manuscript/
  manuscript_style.py
  figure_io.py
  hash_manifest.py
  build_figure1_truth_object.py
  build_figure2_anchor_tiering.py
  build_figure3_model_tradeoff.py
  build_figure4_sweep_controls.py
  build_figure5_axis_tiering.py
  build_figure6_boundary.py
```

其中 `hash_manifest.py` 负责统一计算 SHA256、写入 manifest、记录 git 状态。每个 figure script 只负责自己的 source data 和 plotting。

## 投稿压缩策略

如果投稿时只能放 5 张主图，优先把 **Fig. 5 axis-level interpretation** 降到 Extended Data。

不建议降级 Fig. 6。Fig. 6 是防止 overclaim 的关键，负责把 covariate boundary、K562 supplementary status 和 endpoint hierarchy 放在主文层面。

压缩版主图可以是：

1. Fig. 1 truth object。
2. Fig. 2 anchors。
3. Fig. 3 model trade-off。
4. Fig. 4 sweep / controls。
5. Fig. 5 final boundary。

其中原 Fig. 5 axis-level interpretation 进入 Extended Data。

## 禁写边界

- 不写 model recovery proved。
- 不写 GEARS overall winner。
- 不写 fully deconfounded anchors。
- 不写 fully established shared explanatory architecture。
- 不写 K562 primary co-pillar。
- 不写 content-level replication confirmed。
- 不写 broad cross-context validation。
- 不写 RNAi primary evidence。
- 不写 external model-side generalization proved。
- 不把 discovery 写成当前 formal primary deliverable。
