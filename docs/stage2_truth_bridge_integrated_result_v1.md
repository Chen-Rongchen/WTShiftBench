# Stage 2 Truth Bridge Integrated Result v1

## 1. 文档定位

这份文档用于把当前 `Stage 2` 已经冻结并已刷新的四层结果压成一个统一入口：

1. `truth–DepMap bridge decomposition`
2. `axis annotation / validation`
3. `SCP542 explanation boundary`
4. `Dixit/K562 supplementary structure replication`

它不重新定义 truth object，也不把 supplementary 层提升为 HCC 主结论。

## 2. 当前主线结论

当前最稳的项目表述是：

`truth–DepMap bridge` 不应再被表述成“整体相关性存在”这么单薄的现象，而应被表述成一个具有双层结构的 truth-side object：第一层是由少数 `target-level canonical anchors` 支撑的 joint bridge，第二层是由更有限的 `axis-level shared / skewed explanatory structure` 支撑的功能框架。

按当前更保守的 formal 口径：

- 第一层采用 `high / middle / low` 三段分层，只有四个 corner states 被定义为 `Q1-Q4`
- 第二层要求 `n_targets >= 2` 的 axis 才进入 formal call；单 target axis 只记为 `preliminary`

在此约束下，bridge 仍然成立，但它的结构比单个 `Pearson` 更稀疏、更可解释，也更符合当前项目主线。

## 3. 第一层：Target-Level Bridge Decomposition

### 3.1 当前正式定义

在 `target-level joint-priority grid` 中：

- 每个 target 分别在 transcriptomic real shift 与 aligned DepMap dependency 上被划为 `high / middle / low`
- 只有 `high-high`、`high-low`、`low-high`、`low-low` 四个角点被定义为 `Q1-Q4`
- 只要任一侧处于 `middle`，该 target 就保留在 `middle band`

这一口径避免了把中间态 target 误判成 bridge anchor 或 deviation structure。

### 3.2 当前结果

在 `HCC38` 与 `HCC1143` 中，当前仍可识别一组稳定的 `Q1` canonical bridge anchors。当前 shared canonical anchors 主要包括：

- `PRPF6`
- `PMF1`
- `ZNF131`
- `RUVBL2`
- `ZBTB17`
- `RPS3`
- `PFDN5`

更稳的写法不是“证明这些基因变化大而且细胞依赖”，而是：

这些 target **支持**在 transcriptomic impact 与 cellular dependency 上同时处于高位。

### 3.3 推荐图表

- `reports/stage2_truth_bridge_decomposition/HCC38_target_level_joint_grid.png`
- `reports/stage2_truth_bridge_decomposition/HCC1143_target_level_joint_grid.png`
- `reports/stage2_truth_bridge_decomposition/truth_bridge_decomposition_overview_mockup.png`

## 4. 第二层：Axis-Level Shared Explanatory Structure

### 4.1 当前正式定义

axis-level 层不采用教科书式 ANOVA，而采用更保守、可审计的 explanatory 近似：

- 对每个 frozen axis 分别计算它对 transcriptomic side 的 explanatory `R²`
- 对每个 frozen axis 分别计算它对 DepMap side 的 explanatory `R²`
- 以两侧解释度与 lift 的组合区分：
  - `shared_backbone_axis`
  - `transcriptomic_heavy_axis`
  - `dependency_heavy_axis`
  - `mixed_or_low_signal_axis`

为避免把单基因现象误写成模块级结论，这里额外加入：

- `n_targets >= 2` 才能进入 `formal axis call`
- `n_targets = 1` 只记为 `preliminary`

### 4.2 当前结果

按当前 formal 门槛，axis-level 结果比之前更保守：

- 当前 formal shared backbone axis 非常有限
- `transcription / chromatin` 目前表现为较清楚的 `transcriptomic-heavy` formal axis
- 多条单 target axis 虽然有强信号，但只保留为 `preliminary`

这意味着：

- bridge 的第二层不是“大量 axis 同时封顶成立”
- 而是“少数 formal axes + 多个 preliminary lines of evidence”

这比直接把单 target axis 提升为正式 backbone/module 结论更稳。

### 4.3 与 annotation / validation 的关系

当前 axis 层已经完成第一轮：

- `axis enrichment`
- `per-target consistency audit`
- `validation summary`

因此第二层不再只是结构命名，而已经进入“结构 + 注释 + 一致性”的保守闭环。

## 5. GSEA-like / Annotation / Validation 当前状态

当前这条线已经刷新完成，但要明确边界：

- 它是 `annotation / validation` 层
- 不是 `axis discovery` 主证据
- 当前实现以本地 `GMT` 的 `ORA-like enrichment` + `per-target consistency audit` 为主
- 它不是必须被写成“严格 fgsea 主分析”

当前刷新后：

- `axis_enrichment.tsv` 共 `531` 行
- 覆盖 `26` 条 axis
- `axis_target_consistency.tsv` 共 `8767` 行
- `axis_validation_summary.md` 已更新为最新汇总

当前相对更稳的 annotation 方向仍包括：

- `transcription / chromatin`
  命中 `Chromatin Modifying Enzymes`、`HATs Acetylate Histones`
- `chromatin remodeling`
  命中 `Chromatin Organization / Chromatin Remodeling`
- `TGF-beta / BMP signaling`
  命中 `Signaling By TGFB Family Members`
- `ER stress / UPR`
  命中 `Unfolded Protein Response`

总体上，当前最稳的写法仍然是：

`多数 frozen axes 已获得部分支持，但整体上仍应保持 partially supported axes 口径。`

## 6. SCP542 当前应如何使用

`SCP542` 这一层已经刷新，但它的角色仍然必须保持为：

- `explanation boundary`
- `basal program calibration layer`

它支持的是：

- backbone axes 处于 distributed / high-plasticity 的 basal program 空间
- Type A 与 Type B 在 basal placement 上存在方向性分离
- line-skewed 可获得 basal heterogeneity 的存在性支持

它不支持的是：

- 某 backbone 轴锚定到单一 SCP542 global program
- `HCC1143` basal state 已被解释
- `K562` 的结构复现可由 SCP542 解释

因此，`SCP542` 是解释边界，不是主 biological conclusion。

## 7. Dixit/K562 当前应如何使用

`Dixit/K562` 这一层已经刷新，但应继续保持为：

- `supplementary external structure replication`

当前结果支持：

- K562 也存在 backbone 与 shift-excess 的结构成分
- 但其 dominant backbone 更偏 `biosynthetic support / mitochondrial metabolism`
- 与 HCC 的 `gene expression machinery` 主 backbone 不同

因此它支持的是：

- bridge architecture 具有跨 context 的某种可复制性

而不是：

- K562 与 HCC 拥有同一个 frozen mainline architecture

更准确的写法是：

`Dixit confirms architecture existence at the supplementary level, but the dominant macro-class remains context-specific.`

## 8. 本轮需要重跑与不需要重跑的判断

### 已重跑

- `scripts/run_stage2_truth_bridge_decomposition.py`
- `scripts/run_stage2_axis_analysis.py`
- `scripts/run_stage2_axis_enrichment.py`
- `scripts/materialize_stage2_per_target_signature.py`
- `scripts/run_stage2_axis_target_consistency.py`
- `scripts/summarize_stage2_axis_validation.py`
- `scripts/stage2_freeze_scp542_explanation_boundaries.py`
- `scripts/stage2_dixit_axis_compression.py`

### 当前不需要重跑

- `scripts/build_stage2_truth_driven_bridge.py`
- 主线 HCC truth extraction
- 含 Dixit 的原始 truth bridge 重建

原因是这次修改发生在：

- decomposition 口径
- formal axis call 治理边界
- 下游 annotation / supplement interpretation

而不是发生在上游 truth matrix、filter 或 metric 定义。

## 9. 当前最推荐的正式收口

如果要把当前 `Stage 2` 写成一段项目主线结果，最稳的说法是：

我们将 truth–DepMap bridge 从单一整体相关性进一步分解为两个递进层面：第一层是由少数 canonical anchors 支撑的 target-level joint bridge，第二层是由更有限的 shared / skewed explanatory axes 支撑的结构框架。当前 axis annotation、per-target consistency、SCP542 explanation boundary 与 Dixit supplementary replication 已完成第一轮闭环；其中 HCC 主线结论最稳，SCP542 提供解释边界，Dixit 提供补充性结构复现，而整体 axis 结果仍应保持 `partially supported axes` 的保守口径。

## 10. 渐进披露

默认先看：

1. `reports/stage2_truth_bridge_decomposition/bridge_decomposition_report.md`
2. `reports/stage2_axis_analysis/axis_validation_summary.md`
3. `reports/stage2_truth_driven_bridge/scp542_calibration/scp542_explanation_boundaries.md`
4. `reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_structure_replication_summary.tsv`

若要进入图表与细表，再下钻到：

- `reports/stage2_truth_bridge_decomposition/*.png`
- `reports/stage2_axis_analysis/axis_enrichment.tsv`
- `reports/stage2_axis_analysis/axis_target_consistency.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression/*.tsv`

