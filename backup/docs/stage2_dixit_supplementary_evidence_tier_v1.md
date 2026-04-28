# Stage 2 Dixit/K562 supplementary evidence tier v1

## 1. 文档定位

这份文档只做一件事：

**把 `Dixit/K562` 这条 supplementary external structure replication 线，压成当前可直接进入主文档的 evidence-tiered interpretation。**

当前 primary supplementary bridge test 固定为 `GSE90063 K562 TF pool 13d-only`；`GSE90063 K562 TF pool 7d` 已作为同一外部 context 下的 temporal sensitivity / early-bridge probe 进入 `GSE90063 K562 13d/7d temporal panel`。准入边界看 `docs/stage2_dixit_admission_contract_v1.md`。

## 2. 当前最稳的总体结论

`Dixit/K562` 当前最稳的角色不是“第二主战场”，而是：

**在 supplementary 层面确认 architecture existence，并提供一个 context-specific 的 architecture-to-DepMap bridge supporting context；7d/13d temporal panel 进一步支持同一外部 context 下 architecture form 的时间稳定性与 bridge readout 的 temporal stratification。**

按当前 `13d` 结果，最稳的结构结论是：

- `canonical backbone present = True`
- `shift-excess present = True`
- `architecture class = backbone_plus_shift_excess`
- `backbone macro class = transcription regulation`
- `shift-excess macro class = translation / chromatin machinery`

因此，`Dixit/K562` 当前支持的是：

- `architecture-level replication`
- `structure-level transferability`
- context-specific supplementary bridge form

而不是：

- broad cross-context validation
- object-level one-to-one anchor replication
- model generalization proved

## 3. 当前 evidence tiers

当前建议采用下面这组补充性证据分层。

### 3.1 supplementary_confirmed

这一层只保留当前最稳、最直接的 supplementary 结论：

- `architecture_existence`
  `canonical backbone present = True` 且 `shift-excess present = True`
- `canonical_backbone_present`
  外部 context 中存在 backbone-like 结构，而不是只剩散乱高 shift target

这两条的价值在于确认：HCC 中看到的 backbone / deviation 二元结构，并非完全局限于 HCC。

### 3.2 supplementary_supporting

这一层用于保留“方向清楚，但还不宜升格为 shared architecture claim”的结果：

- `shift_excess_present`
  `K562 13d` 中可见 shift-excess 结构成分，但这仍只支持存在性
- `backbone_macro_class = transcription regulation`
  支持 context-specific backbone replication，不支持与 HCC backbone macro class 对齐
- `architecture_class = backbone_plus_shift_excess`
  支持 K562 architecture composition 与 HCC 一样都含 backbone 与 shift-excess 成分，但不支持跨 context 同构
- `unresolved_2`
  当前是最稳的 supplementary_supporting axis-level object

### 3.3 preliminary

以下对象当前仍应保留为 preliminary，而不是被写成正式 supplementary claim：

- `shift_excess_macro_class = translation / chromatin machinery`
  当前不足以写成稳定、可命名的 supplementary positive program
- `unresolved_5`
  `n_genes=1`，只能作 preliminary supportive line
- `unresolved_4`
  支持 K562 含 shift-excess 成分，但不足以稳定命名 macro class
- `fine-axis correspondence to HCC`
  当前没有证据支持 K562 与 HCC 在 fine-axis 层面一一对应

## 4. 当前最值得点名的 supplementary objects

如果主文档只点少数对象，建议只保留下面这些：

- 数据集层面：
  `canonical backbone present`
  `shift-excess present`
  `backbone macro class = transcription regulation`
  `architecture class = backbone_plus_shift_excess`
- 轴层面：
  `unresolved_2`

更稳的写法是：`GSE90063` 重建的 `K562 13d-only` 当前最稳地支持 supplementary-level 的 architecture-form / bridge-form support：A0 architecture form 已 confirmed，A1 bridge form 当前为 supporting / partial-support。它在结构构成上重现了 `backbone + shift-excess` 这类 architecture form，并在 `n=10` 个可桥接 targets 上呈现出与 DepMap 方向一致、时间尺度兼容的 bridge 信号；但由于当前 target 数仍有限、主导宏观类别仍带有明显的 context specificity，因此它补的是外部 context 下的 bridge form，而不是 HCC content。

temporal panel 口径固定为：在当前项目对象层与现行 admission/bridgeability 规则下，`7d` 与 `13d` 目前各有 10 个正式 bridgeable targets 进入 DepMap 对接；这一数字不应与原始实验设计中的 target / guide 数直接等同。`7d` 只能写成 temporal sensitivity / early-bridge probe，不能写成 primary closure、matched endpoint 或 external model-side generalization proved。

temporal panel 的正式解释只保留三点：

- `7d` 和 `13d` 均确认 `backbone_plus_shift_excess`，支持同一外部 K562 context 下 architecture form 的时间稳定性。
- `7d` rank alignment 更强，而 `13d` mean shift 更大，支持 bridge readout 的 temporal stratification，而不是 later timepoint 单调更强。
- K562 与 HCC 的 macro class 仍为 `CONTEXT_SPECIFIC`，因此该 panel 支持的是 form-level recurrence，不支持 content-level convergence 或 external model-side generalization proved。

RNAi endpoint sensitivity 的正式解释另起一层：在 HCC38、HCC1143、K562 7d、K562 13d 四个 context 中，CRISPR DepMap 的 truth–dependency bridge Spearman（0.51–0.78）一致强于 RNAi DEMETER2（0.28–0.38），且四个 context 的 call 全部为 `rnai_bridge_weaker_than_crispr_sensitivity`。CRISPR vs RNAi endpoint Spearman 在 HCC（0.14/0.23）显著低于 K562（0.45），说明 cross-platform robustness 是 context-dependent 的。这将 RNAi endpoint 的定位从"K562 单点观察"升级为跨 HCC + K562 的 framework-level observation：`CRISPR DepMap = formal primary bridge readout`；`RNAi DEMETER2 = weaker cross-platform sensitivity endpoint`；`RNAi` 不替代 CRISPR 主线，也不提供等价 primary evidence。允许写成 endpoint robustness / sensitivity support，不允许写成 matched endpoint、primary evidence、primary closure 或 CRISPR 主线替代。

## 5. 主张边界

`Dixit/K562` 当前**不支持**以下写法：

- `K562` 与 `HCC38 / HCC1143` 共享同一个 frozen mainline architecture
- `K562` 已完成与 HCC 对称的 axis-level formal closure
- `K562` 的 dominant shift-excess program 已获得稳定机制命名
- `K562` 的结构复现可由 `SCP542` 解释
- 虚拟扰动模型的跨 context generalization 已被证明
- HCC 中的 stable anchors 已在 Dixit 中逐一严格复现
- DEMETER2 RNAi 可以替代 CRISPR DepMap 主线
- DEMETER2 RNAi 提供等价 primary evidence
- GSE90063 7d/13d 是 CRISPRi truth
- HCC endpoint consistency 代表与 K562 等价的跨平台一致性（实际：HCC CRISPR vs RNAi = 0.14/0.23，K562 = 0.45）
- RNA iendpoint 的跨 context 一致性可作为 primary evidence（实际：仅为 framework-level sensitivity observation）

因此，这条线最稳的主文档口径应始终是：

**`K562 13d` supports supplementary-level architecture-form / bridge-form support, while the dominant macro-class remains context-specific and does not justify shared mainline content claims.**

## 6. 推荐写法

如果要把 `Dixit/K562` 写成一段正式结果，最稳的说法是：

`Dixit/K562` 提供了基于 `GSE90063 K562 TF pool 13d-only` 的 supplementary external structure replication。当前结果显示，`K562 13d` 中同样可以观察到 `canonical backbone` 与 `shift-excess` 两类结构成分，并且整体 architecture class 仍可写成 `backbone_plus_shift_excess`，因此支持 architecture form 在外部 context 中具有一定可复制性。与此同时，该对象在 `n=10` 个可桥接 targets 上与 DepMap readout 呈现出方向一致、时间尺度兼容的 bridge signal，因此也为 bridge form 提供了 supplementary-level supporting evidence。`7d/13d` temporal panel 进一步显示：两个时间点均确认 `backbone_plus_shift_excess`，但 `7d` 的 rank alignment 更强，而 `13d` 的 mean shift 更大；因此更稳的解释是 bridge readout 存在 temporal stratification，而不是 `13d` 全面强于 `7d`。这种复现仍主要停留在结构层，而非内容层：相较于 HCC 中以 `gene expression machinery` 为主的 backbone，`K562` 的 dominant macro class 仍为 `CONTEXT_SPECIFIC`。因而当前最稳的结论是：`K562 13d/7d` 支持 supplementary-level 的 architecture-form / bridge-form support（A0 confirmed / A1 supporting / B not eligible），但由于 target 数仍有限且 dominant macro-class remains context-specific，尚不足以将 `K562` 升格为与 HCC 并列的 primary shared architecture evidence，也不能写成 broad cross-context validation、content-level convergence 或 external model-side generalization proved。

## 7. 渐进披露

默认先看：

1. `reports/stage2_truth_driven_bridge_gse90063_13d/stage2_truth_driven_bridge_report.md`
2. `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_structure_replication_summary.tsv`
3. `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_evidence_tier_summary.tsv`
4. `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_claim_tiering.tsv`

若要下钻，再看：

- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_axis_membership.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_master_atlas.tsv`
- `reports/stage2_truth_driven_bridge/k562_rnai_endpoint_consistency/endpoint_consistency_report.md`
