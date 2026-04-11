# WT Benchmark 长期协议蓝图（Truth-First Reframing）

## 1. 文档定位

这份文档定义长期蓝图与制度边界，不等同于当前实现状态，也不是近期执行清单。

它的目标不是废弃原有 `Stage 1A / 1B / 2 / 3` 路线，而是把项目主线重排为一个更准确的 **truth-first architecture framework**。当前执行顺序看 `plan.md`；仓库入口看 `README.md`。

当前近端执行口径已经从“让 strongest entrant 接入 HCC”推进到下一步：

- `GEARS` 已经完成 HCC primary mainline 的 entrant smoke
- `GEARS` 的有限预算 backbone sweep 已完成，并已按 stop rule 收口为 `architecture trade-off diagnosis`
- frozen axis 已完成第一轮 `annotation + per-target consistency + validation summary`
- `scGPT / Geneformer / lm_train_lowrank / lm_G_scgpt_ridge / lm_G_geneformer_ridge` 已完成第一轮 HCC 正式接入与比较层归位

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

本项目长期不只是评估“模型是否大致拟合 perturbation response”，而是回答四类问题：

1. 真实 perturbation transcriptomic truth 中是否存在可冻结、可压缩、可复现的 bridge architecture
2. 模型预测能否恢复这套 frozen architecture
3. 若不能恢复，失败机制属于哪一类结构性 failure mode
4. 只有在前述闭环成立后，是否存在可以进入 downstream discovery 的 phenotype shifter / candidate layer

## 4. 四层主线

### 4.1 Truth Architecture Discovery

这是当前主线的起点。

这一层先回答：

- 真实 genetic perturbation transcriptomic truth 中，到底存在什么稳定结构
- 这些结构是否能桥接到 downstream phenotype / dependency object
- 这些结构是否能在外部 context 中复现

当前冻结对象包括：

- HCC primary truth-driven bridge
- HCC master atlas
- HCC fine axes
- SCP542 explanation boundary
- Dixit/K562 supplementary external structure replication

其中：

- `HCC` 是 primary mainline
- `Dixit/K562` 是 supplementary external structure replication
- 复现的是 architecture / structure，而不是 gene identity overlap
- `SCP542` 是 explanation / calibration layer，不是主 biological conclusion

这一层的职责是定义“真实 structure 是什么”，不是评模型。

### 4.2 Model Recovery Adjudication

在 truth-side architecture 冻结之后，下一步才问：

> 模型能否恢复这套 frozen structure？

这一层的核心问题不是单一相关系数，而是 architecture recovery：

- backbone recovery
- shift-excess identification
- structure vs context separation
- architecture-level recovery，而不是单基因相似度替代

正式裁决对象应是模型输出在 frozen architecture 上的恢复程度，而不是简单把 global Pearson 当成主结论。

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

- truth architecture discovery
- model recovery adjudication

目前 truth-side grounding / architecture contract freeze 已完成；`GEARS` entrant smoke 与有限 sweep 也已完成，但 `Stage 2` 仍不能写成 fully complete，因为当前还处在结果收束与 failure decomposition 的解释层。

### Stage 3

保留为 discovery / phenotype shifter layer，但当前尚未达到 formal execution 阶段。因此不能写成 complete，也不能写成当前 primary active deliverable。

## 6. Frozen Objects 与 Claim Boundaries

### 已冻结对象

- Truth Architecture Contract
- HCC Master Atlas
- HCC Fine Axes
- Dixit Master Atlas
- Structure Replication Summary
- SCP542 Boundaries

### 当前可以稳妥主张的内容

- 项目主线已经重排为 truth-first, structure-aware benchmark
- truth-side architecture contract 已冻结
- HCC 是 primary truth-driven bridge mainline
- Dixit/K562 是 supplementary external structure replication
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
- Dixit 是 HCC 主 biological conclusion 的并列主柱
- global Pearson 已经足以替代 architecture recovery
- phenotype shifter 已经成为当前 formal primary deliverable

## 7. 当前未闭环项

以下对象当前仍未关闭：

- GEARS trade-off diagnosis 的主文档收束
- frozen axis annotation / validation 的主文档收束
- fuller HCC model comparison
- `Stage 1A / 1B` failure decomposition 的正式解释层
- sensitivity full closure
- covariate balance closure
- `final claim matrix -> manuscript wording` 的持续同步
- discovery formalization 仍保持 gated

这些未闭环项意味着：

- truth-side grounding 已冻结
- 但 model-side primary closure 仍未完成
- 因而不能把 `Stage 2 / 3` 写成已完成阶段

## 8. 与仓库文档的关系

- `README.md`：仓库入口，只写当前 active framing 与最近一步
- `plan.md`：当前执行计划，只写最近优先级
- `docs/stage1_failure_decomposition_note_v1.md`：`Stage 1A / 1B` failure decomposition 的正式解释层
- `docs/stage2_truth_driven_bridge_v1.md`：truth-driven bridge 的 protocol、边界、敏感性与解释约束
- `reports/stage2_truth_driven_bridge/`：truth-side 冻结输出与后续 adjudication 所依赖的资产
