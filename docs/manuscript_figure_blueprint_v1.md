# 论文主图蓝图 v1

## 1. 文档定位

这份文档只做一件事：

**把当前项目的主文投稿图片方案固定成一套可直接执行的 truth-first 蓝图。**

它不是结果报告，也不是绘图脚本说明；它负责回答：

- 主图需要几张
- 每张图讲什么
- panel 怎么拼
- 用哪些现有产物
- 讲故事的方法如何向 `s41592-025-02772-6.pdf` 靠齐

## 2. 总体原则

当前主图必须遵循四条原则：

1. 先讲 truth object，再讲 entrant recovery
2. 每张图都要完成一个完整论证，而不是只摆一个结论
3. 风格向 `Nature Methods Brief Communication` 靠齐：高密度、低装饰、强分组、强层次
4. limitation 必须进入主图体系，不能只藏在正文

因此，当前正式主图顺序固定为：

1. `truth object exists`
2. `entrant recovery is limited / trade-off bounded`
3. `axis interpretation is partial`
4. `boundary is explicit`

## 3. 图版风格参考

当前统一参考：

- [`s41592-025-02772-6.pdf`](/home/data/gz0705/WTKO/s41592-025-02772-6.pdf)

需要对齐的不是单纯审美，而是：

- 单页高密度 panel 论证
- “总体图 + 代表例子 + 拆分图 + 组成图”的闭环结构
- 灰色主体 + 少量强调色的克制配色
- 小字号、紧凑布局、清晰分组
- 每张图只服务一个中心判断

## 4. 主图方案

### Fig. 1

**标题**

`Truth–DepMap bridge forms a structured truth object rather than a loose correlation phenomenon`

**这一图只回答**

当前 benchmark 想恢复的 truth object 是否真的存在，而且是否具有可分解的结构。

**建议 panel**

- `a` `HCC38` target-level joint grid
- `b` `HCC1143` target-level joint grid
- `c` shared anchors 的 tier 摘要
- `d` evidence-tier summary
- `e` shared anchors 的对象级 write-up 层级

**建议数据源**

- [`reports/stage2_truth_bridge_decomposition/HCC38_target_level_joint_grid.png`](/home/data/gz0705/WTKO/reports/stage2_truth_bridge_decomposition/HCC38_target_level_joint_grid.png)
- [`reports/stage2_truth_bridge_decomposition/HCC1143_target_level_joint_grid.png`](/home/data/gz0705/WTKO/reports/stage2_truth_bridge_decomposition/HCC1143_target_level_joint_grid.png)
- [`reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv)
- [`reports/stage2_truth_bridge_decomposition/shared_canonical_anchor_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_bridge_decomposition/shared_canonical_anchor_summary.tsv)
- [`reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv)

**唯一判断**

当前 truth–DepMap bridge 不是松散相关，而是一个可进入 adjudication 的结构化 truth object。

### Fig. 2

**标题**

`Current entrants only partially recover the frozen truth object and expose an architecture trade-off`

**这一图只回答**

在已经定义好的 truth object 上，模型恢复到了什么程度。

**建议 panel**

- `a` entrant 与 baseline 的三指标总览
- `b` `backbone_recovery` vs `structure_vs_context_separation` trade-off scatter
- `c` GEARS backbone sweep 候选分布
- `d` baseline winner / entrant gain 的方法学分解
- `e` 代表性 entrant 小面板对照

**建议数据源**

- [`reports/stage2_real_hcc_smoke/model_comparison.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/model_comparison.tsv)
- [`reports/stage2_gears_backbone_sweep/final_adjudication.md`](/home/data/gz0705/WTKO/reports/stage2_gears_backbone_sweep/final_adjudication.md)
- [`reports/stage2_real_hcc_smoke/backbone_diagnosis.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/backbone_diagnosis.tsv)
- [`reports/stage2_real_hcc_smoke/gears_backbone_diagnostic_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/gears_backbone_diagnostic_summary.tsv)

**唯一判断**

现有 entrant 的主要价值不是胜出，而是暴露 `backbone vs separation` 的结构 trade-off。

### Fig. 3

**标题**

`Axis interpretation remains tiered, with one stronger formal axis and a broader set of only partially supported axes`

**这一图只回答**

truth object 的解释层已经推进到哪里，哪里仍然只能保守写。

**建议 panel**

- `a` axis bootstrap stability scatter
- `b` axis validation summary bubble / dot plot
- `c` `transcription / chromatin` 重点 panel
- `d` 其余 axes 的 `partially_supported_axis` 组成
- `e` supporting / preliminary / nonpositive 的边界

**建议数据源**

- [`reports/stage2_truth_bridge_decomposition/axis_bootstrap_stability.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_bridge_decomposition/axis_bootstrap_stability.tsv)
- [`reports/stage2_axis_analysis/axis_validation_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_axis_analysis/axis_validation_summary.tsv)
- [`reports/stage2_axis_analysis/axis_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_axis_analysis/axis_summary.tsv)
- [`reports/stage2_axis_analysis/axis_enrichment.tsv`](/home/data/gz0705/WTKO/reports/stage2_axis_analysis/axis_enrichment.tsv)

**唯一判断**

axis 解释层不是 fully closed architecture，而是一套清楚分层后的 `partially supported axes`。

### Fig. 4

**标题**

`Covariate and supplementary analyses define a limitation-bounded closure rather than a fully deconfounded endpoint`

**这一图只回答**

当前主线最终能保留到哪里，不能保留到哪里。

**建议 panel**

- `a` 五条 covariate 轴在 `HCC38 / HCC1143` 的 summary
- `b` anchor-level covariate tier
- `c` `barcode_gem_group = design-proxy axis` 的边界 panel
- `d` Dixit/K562 supplementary replication summary
- `e` final claim boundary / allowed wording 小 panel

**建议数据源**

- [`reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv)
- [`reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv)
- [`reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv)
- [`reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/barcode_gem_group_mapping_note.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/barcode_gem_group_mapping_note.md)
- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/*.tsv`

**唯一判断**

当前项目的终点不是 `fully deconfounded closure`，而是 `limitation-bounded closure`。

## 5. 补充图方案

当前建议的扩展图为：

1. fuller entrant comparison
2. GEARS sweep candidates
3. anchor cutoff sensitivity
4. control subsampling / formal interval
5. full axis enrichment / consistency detail
6. Dixit/K562 detailed supplementary axes
7. per-axis / per-target covariate detail

## 6. 统一叙事顺序

主文 `Results` 顺序同步固定为：

1. truth–DepMap bridge defines a structured truth object
2. entrants only partially recover this object and expose a trade-off
3. axis interpretation remains partial and tiered
4. covariate and supplementary analyses define the final boundary
5. `Stage 1A / 1B` are reinterpreted as failure decomposition track

## 7. 执行建议

当前不建议一次性并行出完全部图片，而是按以下顺序推进：

1. 先做 `Fig. 1`
2. 再做 `Fig. 2`
3. 统一风格后补 `Fig. 3`
4. 最后做 `Fig. 4`

统一要求：

- 每张图输出 `PDF + PNG`
- 主文图优先保证论证密度，不追求装饰性
- 所有图片只读取现有 `reports/**/*.tsv` 与现成 PNG，不重新做主分析

## 8. 下次进来先看什么

如果下次进来是为了继续做论文图片，固定顺序就是：

1. [`docs/manuscript_figure_blueprint_v1.md`](/home/data/gz0705/WTKO/docs/manuscript_figure_blueprint_v1.md)
2. [`docs/main_manuscript_results_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_results_draft_v1.md)
3. [`reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv)
4. [`s41592-025-02772-6.pdf`](/home/data/gz0705/WTKO/s41592-025-02772-6.pdf)

## 9. 一句话收口

当前论文图片主线必须先证明 truth object 值得被恢复，再展示 entrant recovery 的有限性，最后把解释层与 limitation 一起画清楚。
