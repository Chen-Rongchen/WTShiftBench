# WT Benchmark 长期协议蓝图（Truth-First Reframing）

## 1. 文档定位

这份文档定义长期蓝图与制度边界，不等同于当前实现状态，也不是近期执行清单。

它的目标不是废弃原有 `Stage 1A / 1B / 2 / 3` 路线，而是把项目主线重排为一个更准确的 **truth-first fitness-bridge architecture framework**。当前执行顺序看 `plan.md`；仓库入口看 `README.md`。

**Phase（2026-04-15 冻结）：pre-submission editorial convergence ready — analysis closure 基本完成，infrastructure closure 完成，claim boundary 冻结，wording audit clean，四敏感位置终审 clean，remaining work = 编辑性压缩与投稿准备。**

当前近端执行口径已经从”分析执行”推进到”编辑收敛”：

- `GEARS` 已经完成 HCC primary mainline 的 entrant smoke，并已按 stop rule 收口为 `architecture trade-off diagnosis`
- frozen axis 已完成第一轮 `annotation + per-target consistency + validation summary`
- `scGPT / Geneformer / lm_train_lowrank / lm_G_scgpt_ridge / lm_G_geneformer_ridge` 已完成第一轮 HCC 正式接入与比较层归位
- `GSE90063 K562 13d/7d temporal panel` 已作为 formal supplementary external evidence 纳入项目正式证据体系；`13d` 是 primary formal supplementary bridge test，`7d` 是 temporal sensitivity / early-bridge probe，二者共同支持 architecture form 的时间稳定性与 bridge readout 的 temporal stratification
- 数据身份警报：历史 `data/raw/stage1a/candidates/dixit_2016_raw.h5ad` 与 GSE90063 K562 TF pool 公开描述不匹配，当前按 Frangieh-like legacy object 处理；由其派生的 `dixit_2016_raw__control_context` 不再作为可引用 Dixit 证据
- **K562 infrastructure closure 已完成**：gene ID mapping（24,000 ENSG↔HGNC 条目）、scorer alignment policy、prediction contract（13d/7d）、GEARS 13d formal config 均已冻结
- **wording audit 与四敏感位置终审均已通过**
- 当前不需要新的分析执行；remaining work = 编辑性压缩与投稿准备

如果只是为了继续当前近端主线，而不是看长期制度，直接回到这些入口即可：

- 计划入口：`plan.md`
- 当前 GEARS 裁决：`reports/stage2_gears_backbone_sweep/final_adjudication.md`
- 当前 axis 结果：`docs/stage2_axis_annotation_result_v1.md`
- 当前 axis summary：`reports/stage2_axis_analysis/axis_validation_summary.md`

## 2. 重排原则（不是替换原则）

本项目仍保留原有 stage 编号：

- `Stage 1A`
- `Stage 1B`
- `Stage 2`
- `Stage 3`

但当前 governing storyline 不再采用线性的：

`Stage 1A/1B benchmark -> Stage 2 bridge -> Stage 3 discovery`

而改为：

1. truth architecture discovery
2. model recovery adjudication
3. failure decomposition
4. discovery / phenotype shifter

这是一种 **reframing / reordering**，不是 **abandoning the original roadmap**。

## 3. 长期主问题

本项目长期不只是评估“模型是否大致拟合 perturbation response”，而是回答五类问题：

1. 真实 perturbation transcriptomic truth 中是否存在可冻结、可压缩、可复现的 architecture form
2. 这套 transcriptomic architecture form 是否能桥接到 cellular fitness / dependency（DepMap）这一类长期表型读数
3. 模型预测能否恢复这套 fitness-relevant frozen architecture
4. 若不能恢复，失败机制属于哪一类结构性 failure mode
5. 只有在前述闭环成立后，是否存在可以进入 downstream discovery 的 phenotype shifter / candidate layer

为避免主张层级混淆，长期主线固定为三层：

- A0. Transcriptomic architecture form：扰动转录组内部是否存在 `backbone + shift-excess / context deviation` 结构分解。
- A1. Fitness-relevant bridge architecture：这套结构是否能以时间尺度兼容的方式桥接 DepMap fitness / dependency。论文主卖点应锚定在这一层。
- B. Bridge content：具体哪些 genes 是 anchors、哪条 axis 最强、哪些 biological labels 可写成主结论。这一层需要 target identity 层面的更强复现和更严格混杂控制，不能替代 A1 层主张。

## 4. 四层主线

### 4.1 Truth Architecture Discovery

这是当前主线的起点。

这一层先回答：

- 真实 genetic perturbation transcriptomic truth 中，到底存在什么稳定结构
- 这些结构是否能桥接到 downstream cellular fitness / dependency object，尤其是 DepMap gene effect / dependency readout
- 这些结构是否能在外部 context 中复现

当前冻结对象包括：

- HCC primary truth-driven bridge
- HCC master atlas
- HCC fine axes
- SCP542 explanation boundary
- Dixit/K562 supplementary external structure replication

其中：

- `HCC` 是 primary mainline
- 现有历史 `Dixit/K562`（`dixit_2016_raw__control_context` 来源）当前只保留为 legacy 占位，不作为可冻结 supplementary 证据
- `GSE90063` K562 13d/7d temporal panel 已完成 feasibility check 与第一轮结果组织，当前作为 architecture-to-DepMap bridge 的 formal supplementary external context；剩余工作是 manuscript sync，不是继续可行性论证
- 复现的是 bridge architecture form，而不是 HCC anchor gene identity overlap
- `SCP542` 是 explanation / calibration layer，不是主 biological conclusion

这一层的职责是定义“真实 transcriptomic structure 中哪些成分能桥接 fitness / dependency”，不是单纯做转录组内部降维聚类，也不是评模型。

时间尺度边界必须显式写入这一层：

- `HCC38 / HCC1143 ~14d CRISPRko` 是当前 HCC primary bridge 的时间尺度基础。
- `Dixit K562 13d` 若可拆出，只能写成与 DepMap `~14-21d` fitness screen 的 `time-scale compatible`，不能写成 matched endpoint 或 same steady-state window。
- `Dixit 7d` 只能作为同一实验体系中的 temporal sensitivity / early-bridge probe。
- `Replogle 7d CRISPRi` 暂时只适合作为 shorter-horizon / cross-modality exploration，不承担 primary closure。
- Dixit K562 TF pool 属于 CRISPR knockout perturbation with TF-enriched target library；TF-enriched target composition 可能影响 observed architecture，不能写成与 HCC target space 完全一致。

### 4.2 Model Recovery Adjudication

在 truth-side fitness-bridge architecture 冻结之后，下一步才问：

> 模型能否恢复这套 frozen bridge structure？

这一层的核心问题不是单一相关系数，而是 architecture recovery：

- backbone recovery
- shift-excess identification
- structure vs context separation
- architecture-level recovery，而不是单基因相似度或 global Pearson 替代

正式裁决对象应是模型输出在 fitness-relevant frozen architecture 上的恢复程度，而不是简单把 global Pearson 当成主结论。

在当前近端执行上，这一层已经完成了一轮有限 sweep，并进入结果收口阶段：

1. `GEARS` 不再作为默认的继续调参对象
2. `canonical_backbone recovery` 当前仍以 `shared_mean_baseline` 为 primary reference
3. `GEARS` 当前更适合作为 `backbone vs separation` trade-off 的 entrant 诊断对象
4. `cosine / L2 / top-k overlap` 继续只作辅助解释

### 4.3 Failure Decomposition（Stage 1A / 1B 的新角色）

`Stage 1A / 1B` 保留原有 stage 编号与制度边界，但其解释角色需要被重写。

- `Stage 1A`：short-horizon failure decomposition
- `Stage 1B`：long-horizon / temporal failure decomposition

二者不再只是 leaderboard 层，而应回答：

- 模型丢掉的是 backbone 还是 shift-excess
- 是否把 context-specific deviation 平均化抹平
- long-horizon failure 是否本质上是 temporal structure degradation

因此，`Stage 1A / 1B` 当前更适合被理解为 frozen truth architecture 下的 failure decomposition track。

### 4.4 Discovery / Phenotype Shifter

`Stage 3` 仍然保留，但应明确后置。

它只在以下条件满足后才进入 formal mainline：

- truth-side architecture 已冻结
- model-side structure adjudication 已闭环
- failure decomposition 已足够清楚

因此，discovery 当前只能被写成 downstream application layer / `gated_downstream_layer`，而不是当前 active primary deliverable，更不能写成 formal deliverable。

## 5. Stage Mapping（保留原编号）

### Stage 1A

保留为 short-horizon formal benchmark layer，同时承担 short-horizon failure decomposition 入口。

### Stage 1B

保留为 long-horizon external validation / stress layer，同时承担 temporal failure decomposition 入口。

### Stage 2

保留为 truth-driven bridge layer，但当前应拆成两个子层理解：

- fitness-relevant truth architecture discovery
- model recovery adjudication

目前 HCC truth-side grounding / architecture contract freeze 已完成；`GEARS` entrant smoke 与有限 sweep 也已完成，但 `Stage 2` 仍不能写成 fully complete，因为当前还处在结果收束、Dixit K562 13d/7d temporal panel wording sync 与 failure decomposition 的解释层。

### Stage 3

保留为 discovery / phenotype shifter layer，但当前尚未达到 formal execution 阶段。因此不能写成 complete，也不能写成当前 primary active deliverable。

## 6. Frozen Objects 与 Claim Boundaries

### 已冻结对象与历史对象

- Truth Architecture Contract
- HCC Master Atlas
- HCC Fine Axes
- Dixit Master Atlas（legacy，暂停引用）
- Structure Replication Summary
- SCP542 Boundaries

其中，`Dixit Master Atlas` 当前来自历史 `dixit_2016_raw__control_context` 输入，按 `legacy / 暂停引用` 处理，不再代表可引用的 supplementary external structure replication object。`GSE90063 K562 13d/7d temporal panel` 已通过 feasibility 并完成第一轮结果组织，当前是 architecture-form / bridge-form 的 formal supplementary support；剩余未完成项是 manuscript sync，不是可行性论证。

### 当前可以稳妥主张的内容

- 项目主线已经重排为 truth-first, fitness-bridge, structure-aware benchmark
- 核心主张应锚定在 transcriptomic perturbation structure 能否桥接 DepMap fitness / dependency，而不是单纯证明转录组内部有结构
- HCC truth-side architecture contract 已冻结
- HCC 是 primary truth-driven bridge mainline
- 现有历史 Dixit/K562（`dixit_2016_raw__control_context`）已降级为 legacy/暂停引用；`GSE90063 K562 13d/7d temporal panel` 当前最稳地支持 supplementary-level 的 architecture-form / bridge-form support：两个时间点均确认 `backbone_plus_shift_excess`，`7d` rank alignment 更强，`13d` mean shift 更大；但由于 target 数仍有限、主导 macro class 与 HCC 仍表现出明显的 context specificity，它仍不是 shared mainline architecture content、content-level convergence，也不是与 HCC 对称的 primary conclusion
- model-side structure scorer 已落地
- Stage 2 HCC prediction contract 已冻结为 truth-aligned log-shift space
- real HCC adjudication input bridge 已跑通
- `GEARS` strongest formal entrant 已完成 HCC38 / HCC1143 real smoke
- 当前最近一步是 GEARS backbone failure decomposition
- `Stage 1A / 1B` 将被解释为 failure decomposition tracks

### 当前不能主张的内容

- `Stage 2 and Stage 3 are complete`
- model recovery has already been demonstrated
- GEARS 已经整体压过 `shared_mean_baseline`
- 现有混合时间点 Dixit 是 HCC 主 biological conclusion 的并列主柱
- `Dixit K562 13d` 已经复现 HCC 的具体 anchor / axis content
- `13d` 与 DepMap `~14-21d` 是同一 endpoint 或严格 matched
- `Dixit 7d` / `Replogle 7d CRISPRi` 可以作为 primary closure 直接补强
- global Pearson 已经足以替代 architecture recovery
- phenotype shifter 已经成为当前 formal primary deliverable

## 7. 当前未闭环项

**Phase（2026-04-15 冻结）**：pre-submission editorial convergence ready — analysis closure 基本完成，infrastructure closure 完成，claim boundary 冻结，wording audit clean，四敏感位置终审 clean，remaining work = 编辑性压缩与投稿准备。

以下分析层对象已闭环：

- GEARS trade-off diagnosis ✅
- frozen axis annotation / validation ✅
- fuller HCC model comparison ✅（第一轮 HCC formal integration 完成）
- `Stage 1A / 1B` failure decomposition 的正式解释层 ✅
- sensitivity formal interval ✅（主支柱 citable but not fully closed）
- covariate balance 第一轮审计 ✅（design-proxy axis 已落盘）
- `GSE90063 K562 13d/7d temporal panel` 的 wording freeze ✅
- endpoint hierarchy（CRISPR vs RNAi）✅
- K562 infrastructure closure（gene ID mapping、scorer policy、contract、GEARS 13d formal config）✅
- final claim matrix ✅（已冻结）

仍需人工判断的事项（不能自动完成）：

- Paper title 拟定并确认
- Author list 与 affiliation 填写
- References 补入
- Supplementary table / figure numbering 与正文对齐
- Figure cross-references 补入 “(Fig. X)”
- 句式风格统一（中英文语气一致）
- 冗长句压缩

`GSE90063 K562 13d/7d temporal panel` 的判据（已冻结）：

- Positive：13d K562 中可观察到 canonical backbone + shift-excess / context deviation 的结构形式，且这些结构与 K562 DepMap gene effect / dependency 有预设阈值内的 bridge signal。
- Partial：结构形式存在，但 DepMap bridge 弱或不稳定；解释时只能写成 target class、时间尺度或 cell context 相关的有限证据。
- Negative：结构形式不明显，或结构存在但不能桥接 DepMap；不能事后降级为”只是 supplement”，应诚实报告 tested condition 下未复现。

## 8. 与仓库文档的关系

- `README.md`：仓库入口，只写当前 active framing 与最近一步
- `plan.md`：当前执行计划，只写最近优先级
- `docs/stage1_failure_decomposition_note_v1.md`：`Stage 1A / 1B` failure decomposition 的正式解释层
- `docs/stage2_truth_driven_bridge_v1.md`：truth-driven bridge 的 protocol、边界、敏感性与解释约束
- `reports/stage2_truth_driven_bridge/`：truth-side 冻结输出与后续 adjudication 所依赖的资产
