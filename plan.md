# WT Benchmark — Active Plan（Truth-First Architecture and Model Recovery）

## 1. 项目状态一句话

本项目没有放弃原有 `Stage 1A / 1B / 2 / 3` 路线，但当前主线已经重排为 **truth-first**：先在真实 genetic perturbation transcriptomic truth 中冻结可桥接的 architecture contract，再评估模型能否恢复这套 structure，再把 `Stage 1A / 1B` 重新解释为 failure decomposition track，最后才进入 discovery。当前最重要的已完成项是 **truth architecture contract freeze + GEARS entrant-qualified HCC smoke closure + GEARS 有限 backbone sweep 收口 + frozen axis 第一轮 annotation / validation 闭环 + truth bridge decomposition evidence tiering（含 cutoff sensitivity / bootstrap stability）+ SCP542 boundary / Dixit supplement 刷新**；当前最重要的未完成项是 **把现有 bridge tiering 与 axis validation 收束成更正式的主文档结论，并决定后续是进入 failure decomposition 写作，还是给 Dixit/K562 补一版 supplementary evidence tiering**。

## 2. 下次进来先做什么

如果你只看一段，这一段就是当前执行口径。

当前不要扩到 `scGPT / Geneformer`，也不要回到 truth-side 重做 contract。下次进来应直接做：

1. 先读当前已经收口的三个主结果：
   - `reports/stage2_gears_backbone_sweep/final_adjudication.md`
   - `docs/stage2_truth_bridge_integrated_result_v1.md`
   - `docs/stage2_axis_annotation_result_v1.md`
2. 把这三条线压成更正式的主文档段落：
   - `GEARS`：明确写成 `architecture trade-off diagnosis`
   - `truth bridge`：明确写成 `stable target anchors + limited formal axis evidence + evidence tiers aligned to claim strength`
   - `axis`：明确写成 `partially supported axes`
3. 如果进入实现而不是写作，优先只做：
   - 给 `Dixit/K562` 补一版 supplementary evidence tiering
   - 提炼更稳定的 axis 命名说明
   - 继续区分 `supported mechanism` 与 `generic collapse / mixed program risk`
4. 仍然明确不做：
   - 新 entrant
   - 新 truth object
   - 新评分体系
   - 回头继续为 `GEARS backbone sweep` 开第二轮无限调参

### 现在优先打开的文件

下次进来先看这些结果：

- `reports/stage2_gears_backbone_sweep/final_adjudication.md`
- `docs/stage2_truth_bridge_integrated_result_v1.md`
- `reports/stage2_truth_bridge_decomposition/bridge_decomposition_report.md`
- `reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv`
- `reports/stage2_real_hcc_smoke/model_comparison.tsv`
- `docs/stage2_axis_annotation_result_v1.md`
- `reports/stage2_axis_analysis/axis_validation_summary.md`
- `reports/stage2_axis_analysis/axis_annotation_brief.md`
- `reports/stage2_axis_analysis/README.md`

## 3. 当前正式裁决

当前最稳的项目表述不是“GEARS 已整体胜出”，而是：

> GEARS 展现出选择性结构优势：它更擅长把 structure 和 context deviation 分开，并在部分 cell line 上更能识别 shift-excess；但在当前 HCC primary adjudication 中，canonical backbone recovery 仍落后于 `shared_mean_baseline`。

这条线当前已经按 stop rule 收口，因此它现在决定的不是“下一步继续怎么调”，而是：

- `GEARS` 应固定写成 `architecture trade-off diagnosis`
- 不再把“再跑一轮 sweep”当默认动作
- 不把辅助指标升级成新的主裁决层

## 4. 当前 stop rule

这一步必须有停止规则，避免 endless tuning。

如果一轮有限预算 sweep 后，`canonical_backbone recovery` 仍不能接近或追平 `shared_mean_baseline`，且任何改进都以明显损失 `structure/context separation` 为代价，则停止继续把 `GEARS` 推为 HCC primary winner，并将当前结果收口为 architecture trade-off diagnosis。

到那时，最稳的正式结论应写成：

- `shared_mean_baseline` 仍是 backbone 更强的 primary reference
- `GEARS` 代表一种 structure/context separation-biased entrant
- 它的价值在于揭示 architecture trade-off，而不是整体胜出

## 5. Governing Roadmap（重排，不是替换）

### Layer A. Truth Architecture Discovery

这一层先回答“真实结构是什么”，而不是“模型表现如何”。

- `HCC` truth bridge layer：在 `HCC38 / HCC1143` 的 14d truth 中定义 primary truth-driven bridge object。
- axis compression layer：把可桥接结构压缩为可冻结、可审计的 axis / backbone object。
- SCP542 explanation boundary：作为 calibration / explanation layer，而不是主 biological conclusion。
- Dixit/K562 external structure replication：作为 supplementary external structure replication，复现的是 architecture / structure，不是 gene identity overlap，也不是与 HCC 并列的 primary conclusion。

这一层的目标是冻结“真实 biology 中存在什么稳定结构”，不是给模型打分。

### Layer B. Model Recovery Adjudication

这是当前最近一步，也是当前 active mainline。

核心问题不是单基因拟合，而是 architecture recovery：

- Backbone recovery：模型能否恢复 frozen canonical backbone。
- Shift-excess identification：模型能否识别 shift-excess 对象，而不是只学到 shared mean trend。
- Structure vs context separation：模型能否把 shared backbone 与 context deviation 分开。
- Architecture-level evaluation：主问题是 structure recovery，而不是用 global Pearson 代替 architecture adjudication。

### Layer C. Failure Decomposition Across Stage 1A / 1B

`Stage 1A / 1B` 仍然有效，但角色已经改变。

- `Stage 1A` 不再只是 leaderboard，而是 short-horizon failure decomposition 的第一层。
- `Stage 1B` 不再只是时间外推 stress test，而是 long-horizon / temporal structure degradation 的诊断层。
- 二者当前要回答的问题是：模型丢掉的是 backbone、shift-excess、context specificity，还是出现了 temporal degradation / context averaging。

因此 `Stage 1A / 1B` 不是废弃，而是被重新解释为 frozen truth architecture 下的 failure decomposition track。

### Layer D. Discovery / Phenotype Shifter

discovery 仍然保留，但当前应后置。

- 它必须建立在 truth-side 与 model-side 都闭环之后。
- 当前不能把它写成 primary active deliverable。
- 当前阶段只可将其保留为 downstream application layer，而不是 formal near-term mainline。

## 6. Frozen Objects（已冻结对象）

- Truth Architecture Contract：冻结 truth-side bridge object 的主定义与边界，是当前 architecture adjudication 的上位对象。
- HCC Master Atlas：冻结 HCC 主线 shared structure 的主 atlas，用于后续 model-side 投影与 adjudication。
- HCC Fine Axes：冻结 HCC 内部更细的 axis / subtype-like structure，用于区分 backbone、shift-excess 与 context deviation。
- Dixit Master Atlas：冻结 supplementary external structure replication object，用于检验 architecture 是否在外部 context 中可复现。
- Structure Replication Summary：冻结 HCC 与 supplementary structure replication 的摘要对象，回答“复现的是 architecture，而不是 gene identity overlap”。
- SCP542 Boundaries：冻结 SCP542 的 explanation / calibration 边界，明确其不是主 biological conclusion。

## 7. What Is Actually Closed vs Not Yet Closed

### Closed / Frozen

- truth-side architecture contract
- HCC primary structure definition
- HCC master atlas / fine axes
- Dixit supplementary structure replication object
- SCP542 explanation boundaries
- truth-driven bridge 的主报告边界、dataset role 与 evidence tier governance
- GEARS HCC38 / HCC1143 real raw output
- GEARS export to `stage2_truth_aligned_log_shift`
- GEARS contract validation on HCC38 / HCC1143
- GEARS entrant-qualified HCC smoke adjudication
- GEARS 有限预算 backbone sweep 与 stop-rule 裁决
- HCC 辅助裁决层：`cosine`、`L2`、`top-20 overlap`
- frozen axis 的第一轮 annotation / validation 闭环
- truth bridge decomposition 的 cutoff sensitivity / bootstrap stability / evidence tiering

### Not Yet Closed

- GEARS / axis 结果压成主文档正式段落
- fuller HCC model comparison 的长期解释层
- `Stage 1A / 1B` 作为 failure decomposition track 的正式解释产物
- sensitivity full closure（当前仍是 partial / preliminary snapshot）
- covariate balance closure（当前仍是剩余方法学风险）
- discovery / phenotype shifter formal deliverable

当前不能把这些未闭环项写成“Stage 2 complete”或“Stage 3 complete”。

## 8. Immediate Priorities

1. 固化 GEARS trade-off diagnosis 的正式文档口径
2. 固化 truth bridge evidence tiering 的正式文档口径
3. 给 `Dixit/K562` 补一版 supplementary evidence tiering
4. 固化 frozen axis annotation / validation 的正式文档口径
5. 把 `Stage 1A / 1B` failure decomposition 的写作入口接上
6. 明确 discovery 何时可以进入下一阶段

## 9. Explicit Non-Goals for the Current Phase

- 不把 Dixit/K562 写成与 HCC 并列的 primary biological conclusion
- 不把 SCP542 写成强机制锚定或主结论层证据
- 不把 global Pearson 当成 architecture recovery 的替代
- 不把 phenotype shifter discovery 提前写成 formal deliverable
- 不把 `Stage 1A / 1B` 视为废弃
- 不把 model-side recovery 写成已经被证明
- 不把 `GEARS` 当前结果写成“整体压过 shared_mean_baseline”
- 不把 `scGPT / Geneformer` 现在拉进 HCC primary mainline
- 不把 `Stage 2 / 3` 写成 fully complete

## 10. Expected Near-Term Deliverables

- GEARS trade-off diagnosis note
- truth bridge integrated result note
- axis annotation / validation result note
- Dixit supplementary evidence tier note
- `Stage 1A / 1B` failure decomposition note
- refreshed report boundary text

## 11. Document Map

- `README.md`：仓库入口，说明当前 active framing、最近一步与 claim boundaries。
- `plan.md`：当前执行优先级，不展开长期制度。
- `docs/protocol_blueprint.md`：truth-first 长期蓝图，保留 `Stage 1A / 1B / 2 / 3` 编号但重排主线。
- `docs/stage2_truth_driven_bridge_v1.md`：truth-driven bridge 的实现边界与敏感性说明。
- `docs/stage2_truth_bridge_decomposition_v1.md`：truth–DepMap bridge 两层分解与 evidence-tier 规则说明。
- `docs/stage2_truth_bridge_integrated_result_v1.md`：整合 decomposition、axis validation、SCP542 与 Dixit supplement 的统一结果入口。
- `reports/stage2_truth_driven_bridge/truth_architecture_contract/`：truth architecture contract 冻结产物。
- `reports/stage2_truth_driven_bridge/master_atlas/`：HCC master atlas 与 fine axes 冻结产物。
- `reports/stage2_truth_bridge_decomposition/`：target-level anchors、axis-level structure、cutoff sensitivity、bootstrap stability 与 evidence tiers。
- `reports/stage2_truth_driven_bridge/dixit_axis_compression/`：supplementary external structure replication 产物。
- `reports/stage2_truth_driven_bridge/scp542_calibration/`：SCP542 explanation boundary 产物。
- `reports/stage2_real_hcc_smoke/smoke_report.md`：当前 HCC 主裁决入口。
- `reports/stage2_real_hcc_smoke/adjudication_summary.md`：当前最稳的中文裁决摘要。
