# Stage 2 Truth Bridge Integrated Result v1

## 1. 文档定位

这份文档用于把当前 `Stage 2` 已经冻结并已刷新的四层结果压成一个统一入口：

1. `truth–DepMap bridge decomposition`
2. `axis annotation / validation`
3. `SCP542 explanation boundary`
4. `Dixit/K562 supplementary external structure replication`

它不重新定义 truth object，也不把 supplementary 层提升为 HCC 主结论。

> 数据身份更新（2026-04）：`Dixit/K562 supplementary` 的默认正式入口现已切换到 `GSE90063` 重建的 `K562 13d-only`；历史 `dixit_2016_raw__control_context` 仅保留为 `legacy / 暂停引用` lineage。具体准入边界与默认执行链见 `docs/stage2_dixit_admission_contract_v1.md` 与 `docs/stage2_dixit_supplementary_startup_packet_v1.md`。

## 2. 当前主线结论

综合当前 `Stage 2` 结果，我们已经完成了从“现象级相关”到“分层化结构证据”的第一轮收口。

但这不能被误读成方法学已经 fully closed。当前更准确的状态是：主文稿可保留的结构化结果边界已经基本稳定，而 sensitivity / covariate / final claim wording 仍需继续按正式边界同步。

当前最稳的主文档结论框架应写成三条并列主张：

- `GEARS` 在当前 HCC primary adjudication 中应被定位为 `architecture trade-off diagnosis`，而不是待继续优化的主推进对象。
- `truth–DepMap bridge` 已不再只是整体相关现象，而是由少数稳定 `target-level anchors` 与有限 `formal axis evidence` 共同支撑的结构化 bridge。
- frozen axis 已完成第一轮 `annotation + validation + tiering`，但当前仍应保持 `partially supported axes`，而不是 `fully closed architecture`。

当前最稳的项目表述是：

`truth–DepMap bridge` 不应再被表述成“整体相关性存在”这么单薄的现象，而应被表述成一个具有双层结构的 truth-side object：第一层是由少数 `target-level canonical anchors` 支撑的 joint bridge，第二层是由更有限的 `axis-level shared / skewed explanatory structure` 支撑的功能框架。

按当前更保守的 formal 口径：

- 第一层采用 `high / middle / low` 三段分层，只有四个 corner states 被定义为 `Q1-Q4`
- 第二层要求 `n_targets >= 2` 的 axis 才进入 formal call；单 target axis 只记为 `preliminary`

在此约束下，bridge 仍然成立，但它的结构比单个 `Pearson` 更稀疏、更可解释，也更符合当前项目主线。

## 3. GEARS adjudication：architecture trade-off diagnosis

`GEARS` 在当前框架下已完成必要的 backbone sweep 与 adjudication，其结果更适合被解释为一类 `architecture-level trade-off diagnosis`，而非继续通过无停止规则的参数搜索追求单次性能改善。

现阶段证据支持：

- `GEARS` 能恢复部分 backbone-related structure
- `GEARS` 在 `structure/context separation` 上表现出选择性优势
- 这类收益与 `canonical_backbone recovery` 的代价并不对称
- 当前证据不足以推动新一轮主线扩模或重新开启 entrant sweep

因此，`GEARS` 在本阶段的角色应定位为“已完成诊断的代表性 entrant”，而不是“待继续优化的主推进对象”。

## 4. 第一层：Target-Level Bridge Decomposition

### 4.1 当前正式定义

在 `target-level joint-priority grid` 中：

- 每个 target 分别在 transcriptomic real shift 与 aligned DepMap dependency 上被划为 `high / middle / low`
- 只有 `high-high`、`high-low`、`low-high`、`low-low` 四个角点被定义为 `Q1-Q4`
- 只要任一侧处于 `middle`，该 target 就保留在 `middle band`

这一口径避免了把中间态 target 误判成 bridge anchor 或 deviation structure。

### 4.2 当前结果

在 `HCC38` 与 `HCC1143` 中，当前仍可识别一组稳定的 `Q1` canonical bridge anchors。当前 shared canonical anchors 主要包括：

- `PFDN5`
- `PMF1`
- `PRPF6`
- `ZNF131`

更稳的写法不是“证明这些基因变化大而且细胞依赖”，而是：

这些 target **支持**在 transcriptomic impact 与 cellular dependency 上同时处于高位。

其中，`PFDN5`、`PMF1`、`PRPF6` 与 `ZNF131` 是当前最稳的 shared anchors，能够在多组 cutoff 设定下保持 anchor 身份。

但这里的“stable”当前只能写成 structural stability，而不能自动升级成 `fully deconfounded`。按当前 covariate audit 边界，`PFDN5` 最多只能写成 `primary_but_qualified`，而 `PMF1 / PRPF6 / ZNF131` 仍应保留为 `supporting_only`。

### 4.3 推荐图表

- `reports/stage2_truth_bridge_decomposition/HCC38_target_level_joint_grid.png`
- `reports/stage2_truth_bridge_decomposition/HCC1143_target_level_joint_grid.png`
- `reports/stage2_truth_bridge_decomposition/truth_bridge_decomposition_overview_mockup.png`

## 5. 第二层：Axis-Level Shared Explanatory Structure

### 5.1 当前正式定义

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

### 5.2 当前结果

按当前 formal 门槛，axis-level 结果比之前更保守：

- 当前 formal axis evidence 非常有限
- `transcription / chromatin` 目前是唯一同时满足 formal criteria 且在 bootstrap 下保持稳定的正向 axis
- 多条单 target axis 虽然有强信号，但只保留为 `preliminary`

这意味着：

- bridge 的第二层不是“大量 axis 同时封顶成立”
- 而是“有限 formal evidence + 多个 supporting / preliminary lines of evidence”

这比直接把单 target axis 提升为正式 backbone/module 结论更稳。

因此，当前结果支持“存在可治理、可分层的 truth–DepMap bridge structure”，但尚不足以升级为 `fully established shared explanatory architecture`。

与 sensitivity 线合并理解时，更稳的口径应是：当前 formal axis evidence 与 control subsampling formal interval 已可引用进主文稿，但 sensitivity full closure 仍不能被写成 fully closed，因为 covariate 线仍未闭环。

### 5.3 与 annotation / validation 的关系

当前 axis 层已经完成第一轮：

- `axis enrichment`
- `per-target consistency audit`
- `validation summary`

因此第二层不再只是结构命名，而已经进入“结构 + 注释 + 一致性”的保守闭环。

## 6. GSEA-like / Annotation / Validation 当前状态

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

更准确地说，当前 axis 分析的主要贡献，不在于证明一个已经完全闭合的模块架构，而在于完成了第一轮 `annotation`、`validation` 与 `evidence tiering`：哪些 axis 可以进入 formal 或 primary 层级，哪些仅能作为 supporting evidence，哪些仍应停留在 preliminary status，现已具备清晰边界。

## 7. 主张边界

需要强调的是，当前结果支持的是“存在少数稳定 anchors 与有限 formal axis evidence 的结构化 bridge”，而不是“多数 axis 已完成正式闭环”或“shared explanatory architecture 已全面建立”。

因此，现阶段主文档应坚持 `evidence-tiered interpretation`，避免将 supporting 或 preliminary 对象上升为与 primary evidence 同等级的结构性结论。

## 8. SCP542 当前应如何使用

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

## 9. Dixit/K562 当前应如何使用

`Dixit/K562` 这一层已经刷新，但应继续保持为：

- `supplementary external structure replication`

当前结果支持：

- K562 也存在 backbone 与 shift-excess 的结构成分
- 但其 dominant backbone 更偏 `transcription regulation`
- 与 HCC 的 `gene expression machinery` 主 backbone 不同

因此它支持的是：

- bridge architecture 具有跨 context 的某种可复制性

而不是：

- K562 与 HCC 拥有同一个 frozen mainline architecture

更准确的写法是：

`GSE90063` 重建的 `K562 TF pool 13d-only` 结果当前最稳地支持：`Dixit/K562` 可在 supplementary 层面复现 `backbone + shift-excess` 的架构形式，因此为外部 context 下的 architecture-form replication 提供支持。按当前 evidence tier，更准确的分层是：A0 architecture form 已 confirmed，A1 bridge form 当前为 supporting / partial-support。与此同时，该对象在 `n=10` 个可桥接 targets 上与 DepMap readout 呈现出方向一致、时间尺度兼容的 bridge 信号；但由于当前 target 数仍有限、主导 macro class 与 HCC 仍表现出明显的 context specificity，这些结果只能写成 supplementary-level 的 architecture-form / bridge-form support，而不能升级为 shared mainline architecture content、broad cross-context validation 或与 HCC 对称的 primary conclusion。

当前这一层现在也已经补上了更正式的 supplementary evidence-tier 口径：

- `architecture existence` 与 `canonical backbone present` 可保留为 `supplementary_confirmed`
- `shift-excess present` 与 context-specific backbone macro class 更适合保留为 `supplementary_supporting`
- `shift-excess macro class` 与多数单条 K562 axis 仍应保持 `preliminary`

## 10. 本轮需要重跑与不需要重跑的判断

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

## 11. 当前最推荐的正式收口

如果要把当前 `Stage 2` 写成一段项目主线结果，最稳的说法是：

综合当前 `Stage 2` 结果，我们认为本项目已经完成从“现象级相关”到“分层化结构证据”的第一轮收口。首先，`GEARS` 在当前框架中的角色应被定位为 `architecture trade-off diagnosis`：其 backbone sweep 与 adjudication 已足以支持结构性诊断，但现阶段不宜再以无停止规则的方式继续扩展 entrant 或开启新一轮调参主线。其次，`truth–DepMap bridge` 已不再只是整体相关现象，而是可进一步分解为 `target-level` 的稳定 anchors 与 `axis-level` 的有限 formal evidence。经过 cutoff sensitivity、bootstrap stability 与 evidence tier 治理后，当前 primary evidence 集中于少数跨 cutoff 稳定的 anchors，以及一条经 bootstrap 支撑的 formal positive axis；其余对象则被明确界定为 supporting、unstable 或 preliminary。需要同时强调的是，这里的 stable anchors 当前仍受 covariate audit 边界约束，只能按 `PFDN5 = primary_but_qualified`、`PMF1 / PRPF6 / ZNF131 = supporting_only` 继续分层书写。最后，axis `annotation / validation` 的第一轮工作已完成，并形成了一套部分得到支持的轴级解释框架，但当前证据仍不足以支持 `fully established shared explanatory architecture` 的更强主张。整体而言，本阶段最重要的进展不是信号数量的增加，而是 evidence tier 与 claim strength 的成功对齐，从而使主结论更加清晰、可信且可防守；与此同时，`final claim matrix -> manuscript wording` 仍需继续同步，这不是一次性结束的动作。

## 12. 渐进披露

默认先看：

1. `reports/stage2_truth_bridge_decomposition/bridge_decomposition_report.md`
2. `reports/stage2_axis_analysis/axis_validation_summary.md`
3. `reports/stage2_truth_driven_bridge/scp542_calibration/scp542_explanation_boundaries.md`
4. `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_structure_replication_summary.tsv`
5. `docs/stage2_dixit_supplementary_evidence_tier_v1.md`

若要进入图表与细表，再下钻到：

- `reports/stage2_truth_bridge_decomposition/*.png`
- `reports/stage2_axis_analysis/axis_enrichment.tsv`
- `reports/stage2_axis_analysis/axis_target_consistency.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/*.tsv`
