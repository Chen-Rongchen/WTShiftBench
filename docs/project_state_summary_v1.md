# 项目阶段状态摘要 v1

## 1. 当前项目处于什么阶段

当前项目已经不再处在“分析还没收住”的阶段，而是进入了：

**主张治理稳定化阶段。**

更准确地说：

- 写作收口主线：第一轮基本完成
- 方法学闭环主线：仍未 fully closed
- `global / structural bridge claim` 已可保留
- `object-level strongest claims` 已完成正式分级与必要降级
- `discovery` 已被成功压回 `gated_downstream_layer`
- 后续若想继续推进 full closure，主要瓶颈不再是分析框架不足，而是可用实验设计元数据的上限

## 2. 当前最稳的项目状态标签

当前最稳的一句话状态是：

**当前项目已进入“主张治理稳定化”阶段：写作收口主线第一轮基本完成，全局 bridge 主张可保留，对象级最强主张已完成正式分级与降级治理；后续闭环的主要瓶颈不再是分析框架不足，而是实验设计元数据的可用性上限。**

## 3. 当前已经完成到位的

- `bridge exists`：保住
- `GEARS trade-off diagnosis`：保住
- `scGPT` entrant-qualified HCC smoke：已完成第一轮接入与裁决
- `Geneformer` entrant-qualified HCC smoke：已完成第一轮接入与裁决
- `lm_train_lowrank` linear control：已完成第一轮接入与裁决
- `lm_G_scgpt_ridge` linear control：已完成第一轮接入与裁决
- `lm_G_geneformer_ridge` linear control：已完成第一轮接入与裁决
- anchor strongest wording：完成正式降级治理
- `PFDN5 = primary_but_qualified`：固定
- `PMF1 / PRPF6 / ZNF131 = supporting_only`：固定
- `transcription / chromatin = primary_axis_but_qualified`：固定
- `claim matrix`：已成形，并已接回主文稿与 boundary 文档
- discovery：已明确 `gated`
- `Dixit/K562`：已固定为 `supplementary external structure replication`
- foundation-model entrant family：已形成 `Geneformer > scGPT`
- 第一层 linear controls：已形成 `lm_g_geneformer_ridge > lm_train_lowrank > lm_g_scgpt_ridge`
- 禁写边界：`model recovery proved` / `Stage 2 complete` / `Stage 3 complete` 已固定

## 4. 当前还没有 fully closed 的

- `covariate closure` 仍不是最终闭环
- `sensitivity full closure` 仍不是最终闭环
- `final claim matrix -> manuscript wording` 仍需持续同步到所有入口文档
- 这不是因为缺少分析框架
- 而是因为缺少更深层实验设计元数据来继续做 deconfounding

需要补充的是，sensitivity 线当前已不再停留在“formal interval 不可引用”的阶段。`control subsampling` 已完成 `24/24` 配置重复数并达到 `formal_interval_citable = true`；因此 sensitivity 当前剩余的主缺口，已主要收缩到 covariate closure 仍未 fully closed 这一点。

当前混杂线已经从“单轴提示性审计”推进到“多轴、配置驱动、可汇总输出”的状态：`num_umis_quantile_bin` 与 `num_umis_over_threshold_bin` 都已经进入正式 covariate audit 入口。但这一步解决的是**把风险显式量化并纳入边界治理**，不是把混杂风险宣布为 fully closed。

这两件事必须分开理解：

- 前者是“方法没做到”
- 后者是“证据天花板到了”

当前项目更接近后者。

与此同时，model-side entrant 状态也已经从“只有 `GEARS` 进入正式 HCC 裁决”推进到“`GEARS + scGPT + Geneformer + 三条 linear controls` 已进入同一份 HCC comparison”。当前新增 entrant / control 并没有推翻主结论，只是把 entrant family 的第一轮位置明确出来：`Geneformer` 强于 `scGPT`，`lm_g_geneformer_ridge` 能保住一部分 backbone，但当前没有任何对象改写 `shared_mean_baseline` 仍是 backbone primary reference 这一点。

这也意味着，后续如果继续推进“为什么模型打不过 baseline”，默认不该再以泛问题形式展开，而应先拆成两个更小的问题：

- `baseline winner` 是否主要由 shared backbone objective 决定
- entrant 的额外能力是否稳定落在 `separation / deviation` 而不是 backbone 上

在这两个问题更清楚之前，biology-facing explanation 仍应停留在 plausible interpretation 层。

## 5. 当前最稳的三层边界

### 5.1 全局层

当前证据支持 `truth–DepMap bridge` 在整体与结构层面上成立，且该结论在现有 covariate audit 下仍可保留。

### 5.2 对象层

当前 covariate audit 表明 anchor-level strongest wording 需要收紧。现阶段仅 `PFDN5` 可保留为 `primary_but_qualified`；`PMF1`、`PRPF6` 与 `ZNF131` 虽保持结构稳定的 anchor 身份，但目前仅能作为 `supporting_only`，而不足以被表述为 fully deconfounded primary anchors。与此同时，`transcription / chromatin` 当前最多只能写成 `primary_axis_but_qualified`。

### 5.3 方法学边界层

现有 covariate closure 受限于仓库中可用的实验设计元数据范围。若无新增元数据源，后续最合理的推进方向应是完成 `claim matrix`、`evidence tier synchronization` 与 manuscript-ready wording，而非无停止规则地继续扩展 covariate 审计轴。当前更准确的口径应是：**混杂风险已完成第一轮多轴治理，但仍受元数据上限约束。**

`Dixit/K562` 在这一边界下也应固定写成 `supplementary external structure replication`：它支持 architecture-level / structure-level replication，但不支持 `model generalization proved`，也不支持与 HCC 对称的 primary conclusion。

## 6. 当前最该守住的四条纪律

- 不把 `primary_but_qualified` 偷偷写成 `primary`
- 不把 `supporting_only` 借叙事语气抬升
- 不把 `retainable_global_claim` 延伸成 `recovery proved`
- 不把 `gated_downstream_layer` 提前写成主 deliverable

## 7. 当前统一口径源

默认先看：

1. [`reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv)
2. [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)
3. [`docs/why_models_do_not_stably_beat_baseline_v1.md`](/home/data/gz0705/WTKO/docs/why_models_do_not_stably_beat_baseline_v1.md)
4. [`docs/model_vs_baseline_deeper_explanation_note_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_deeper_explanation_note_v1.md)
5. [`docs/model_vs_baseline_next_step_breakdown_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_next_step_breakdown_v1.md)
6. [`docs/main_manuscript_integrated_narrative_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_integrated_narrative_draft_v1.md)
7. [`docs/main_manuscript_results_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_results_draft_v1.md)

## 8. 一句话收口

当前主线已经不是“缺结果”，而是“结果边界已经被治理清楚；剩下要做的是把 claim matrix 同步成 manuscript-ready wording，并承认再往上能不能闭环，取决于未来是否拿得到更高质量实验设计元数据”。
