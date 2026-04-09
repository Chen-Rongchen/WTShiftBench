# Stage 2 Truth Bridge Decomposition v1

## 目标

把 `truth–DepMap bridge` 从“整体上是否相关”进一步拆成两个递进层面：

1. `target-level joint-priority grid`
2. `axis-level shared explanatory structure`

第一层回答：哪些 `target` 是 canonical bridge anchors，哪些是偏离结构。  
第二层回答：这些 bridge anchors 是否来自共同的功能 backbone，还是来自 transcriptomic-heavy / dependency-heavy 的偏斜 axis。

## 为什么不只报 Pearson

单个 `Pearson` 或 `Spearman` 只能回答：

- 整体上是否有正相关

但它回答不了：

- 是不是少数极端点在拉动
- 哪些 `target` 在支撑 bridge
- 哪些 `target` 在偏离 bridge
- 哪些 `axis/module` 同时支撑 transcriptomic truth 与 DepMap truth

因此这里不把 global correlation 当成主结论，而把它降回 existence-level evidence。

## 第一层：Target-Level Joint Grid

### 定义

- 横轴：aligned `DepMap` strength
- 纵轴：real shift metric

默认配置：

- `shift_metric = real_shift_mean_abs`
- `depmap_metric = depmap_gene_dependency`
- `quantile_low = 0.25`
- `quantile_high = 0.75`

其中 aligned `DepMap` strength 的方向约定为：

- 若使用 `depmap_gene_dependency`，直接取原值
- 若使用 `depmap_gene_effect`，则乘以 `-1`，统一为“越大表示 dependency / liability 越强”

### Grid 解释

这里推荐的 formal 定义不是粗糙的二维四象限，而是：

- 先在每一轴分别分成 `high / middle / low`
- 再只把四个角点定义为 `Q1-Q4`
- 任何一轴落在 `middle` 的 target，都不进入 `Q1-Q4`

也就是一个 `3 × 3` grid，但只有四个 corner cells 被赋予 `Q1-Q4` 正式含义。

- `Q1_anchor`
  同时高 shift / 高 dependency。它是 formal bridge anchor 的主定义。
- `Q2_transcriptomic_excess`
  shift 高、dependency 低。它表示 transcriptomic-heavy 的偏离结构。
- `Q3_dependency_excess`
  dependency 高、shift 低。它表示 phenotype-heavy / dependency-heavy 的偏离结构。
- `Q4_low_information`
  两侧都低，更接近低信息背景。
- `middle band`
  只要任一轴落在 `middle`，就留在中间带，不硬塞进 `Q1-Q4`。

### 输出

- `target_level_joint_grid.tsv`
- `target_level_grid_summary.tsv`
- `shared_canonical_anchor_summary.tsv`

其中 shared canonical anchor 的默认条件是：

- 至少在 `anchor_min_cell_lines` 条 cell line 中命中 `Q1`
- 且跨线平均 `shift_quantile` 与 `depmap_quantile` 均不低于 `shared_anchor_min_mean_quantile`

### 解释边界

这里支持的是：

- 某个 `target` 同时具有高 transcriptomic impact 与高 cellular dependency

这里**不支持**的是：

- 该 `target` 的 transcriptomic shift 导致 dependency
- 或 dependency 导致 transcriptomic shift

它是共定位 / 耦联证据，不是因果证明。

## 第二层：Axis-Level Shared Explanatory Structure

### 定义

将 `target` 映射到 frozen `axis` 后，对每个 axis 分别评估：

- 它对 transcriptomic side 的解释强度
- 它对 DepMap side 的解释强度

当前实现采用极简、可审计的近似：

- 对每个 axis 做 `one-vs-rest` 二元 membership
- 分别计算该 membership 与 `shift_value`、`depmap_strength` 的相关平方，记为 axis-level `R²`

它不是教科书式 ANOVA，也不是要给出唯一正确的 variance decomposition；它的用途只是保守地衡量：

- 某个 axis 是否对两侧都具有可观解释度

### Axis 结果分类

- `shared_backbone_axis`
  两侧 `R²` 都不低，且 axis 对两侧均呈正向 lift。
- `transcriptomic_heavy_axis`
  transcriptomic side 的解释度显著高于 DepMap side。
- `dependency_heavy_axis`
  DepMap side 的解释度显著高于 transcriptomic side。
- `mixed_or_low_signal_axis`
  不能被稳定归为上述任一类。
- `insufficient_axis_size`
  axis 规模不足，不做正式判断。

### 正式口径收紧

为了避免单基因 axis 被直接写成正式 backbone，这里增加一层治理边界：

- `n_targets < axis_min_targets_for_formal_call` 的 axis，即使出现 shared / skewed signal，也只记为 `preliminary`
- 主文档中的 formal axis call，优先只引用达到最小 target 数要求的 axis

这意味着：

- 单 target axis 仍可保留为线索
- 但不应与 multi-target frozen backbone axis 处于同一证据等级

### 输出

- `axis_level_shared_explanatory_summary.tsv`
- `bridge_decomposition_report.md`

## 与现有 Stage 2 对象的关系

这个 decomposition layer 不是替代原有：

- `truth_architecture_contract`
- `master_atlas`
- `axis annotation / validation`

而是站在这些 frozen objects 之上，补出一个更适合主文档叙事的中间层：

- 第一层把 `target` 分成 anchor / deviation / background
- 第二层把 `axis` 分成 shared backbone / transcriptomic-heavy / dependency-heavy

因此它与当前项目主线是递进关系，不是平行重复。

## 默认入口

- 配置：`configs/stage2/truth_bridge_decomposition_v1.json`
- CLI：`scripts/run_stage2_truth_bridge_decomposition.py --config <config>`

## 渐进披露

默认先看：

1. `reports/stage2_truth_bridge_decomposition/bridge_decomposition_report.md`
2. `reports/stage2_truth_bridge_decomposition/shared_canonical_anchor_summary.tsv`
3. `reports/stage2_truth_bridge_decomposition/axis_level_shared_explanatory_summary.tsv`

需要更细时，再下钻到：

- `target_level_joint_grid.tsv`
- `target_level_grid_summary.tsv`
