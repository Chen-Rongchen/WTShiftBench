# 最终 claim boundary 与 discovery gating 说明 v1

## 1. 文档定位

这份文档只做两件事：

1. 固定当前项目的终局 claim boundary
2. 固定 discovery / phenotype shifter 何时才有资格进入正式交付

它不引入新结果，只收口边界。

当前这份边界文档还承担一项 manuscript-ready 职责：把 `final_claim_matrix.tsv` 持续同步到主文稿、摘要式写法与仓库入口文档，确保 `allowed / disallowed wording` 始终一致。

这不是一次性结束的动作；后续只要方法学结果继续推进，`final claim matrix -> manuscript wording` 就需要继续同步。

当前对象级与全局级的统一口径表，见：

- [`reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv)

需要补充的是：最新版 covariate audit 已补齐 `summary.tsv`、combined TSV 与 per-axis TSV，并把审计轴扩展到一条 `barcode_gem_group` 设计层代理轴、两条 protospacer 轴加两条 transcriptome 轴；后续追查已进一步确认 `HCC38 -> aggrMH001-3`、`HCC1143 -> aggrMH004-6`，但仍不能把 `-1/-2/-3` 唯一映射到单个 `MH00x`。因此，这次推进坐实的是“`barcode_gem_group` 应固定写成 design-proxy axis，且风险仍未 fully closed”这条边界，而不是对象级 tier 的再次改写。

本阶段还需额外固定一条接受原则：

- 接受 `design-proxy` 是当前最终口径，不再等待升级为单个 `MH00x` 的 resolved run label
- 接受 covariate 线当前不会到 `fully clean`
- 接受论文必须带着这条 limitation 写，而不是等待它消失
- 因此，开始写论文的门槛应改为“文稿与边界是否稳定”，而不是“数据是否完美”

## 2. 当前可以写成什么

当前最稳、可以进入主文稿 primary conclusion 的主张，包括：

- `GEARS` 在 HCC primary adjudication 中应被定位为 `architecture trade-off diagnosis`
- `shared_mean_baseline` 仍是 backbone 更强的 primary reference
- 这是一条非对称 trade-off，不是“GEARS 和 baseline 各赢一半”：`shared_mean_baseline` 是更稳定、更主导的 backbone primary reference，`GEARS` 是 deviation / separation-biased entrant
- 复杂 entrant 当前不能稳定胜过 baseline，最稳的解释是：shared canonical backbone 本身较强，而 entrant 的额外优势更偏 separation / `shift-excess` / context-specific deviation，尚未稳定转化为 backbone superiority
- `GSE90063 K562 13d-only` 的 model-side 最小审计只能写成 `partial recurrence / partial-support`：backbone-vs-separation 主方向复现，但 `shift-excess` 分量未复现
- `truth–DepMap bridge` 由少数分层书写的 shared anchors 与有限 formal axis evidence 共同支撑
- `PFDN5` 最多只能写成 `primary_but_qualified`
- `transcription / chromatin` 最多只能写成 `primary_axis_but_qualified`
- frozen axis 已完成第一轮 `annotation + validation + tiering`，但整体仍应保持 `partially supported axes`
- `barcode_gem_group` 可作为正式 design-proxy covariate 写入方法学边界，但不能写成已解析到单个 `MH00x` 的 run-level 标签

## 3. 当前只能写成什么

以下内容当前只能保留在 supporting / preliminary / supplementary 层级：

- `PMF1`、`PRPF6`、`ZNF131` 这类结构上稳定但已暴露 covariate 风险的 anchor-level strongest wording，它们当前只能保留为 `supporting_only`
- 多数其余 axis 的功能解释
- `Dixit/K562` 的更多 context-specific 细节
- 更细的 shift-excess macro class 命名
- discovery / phenotype shifter 的下游应用想象

更准确地说，这些对象并不是“没有价值”，而是当前不应与 HCC primary 主结论处于同一层级。

## 4. 当前明确不能写什么

当前必须继续避免以下 overclaim：

- “model recovery has been demonstrated”
- “GEARS 已整体压过 shared_mean_baseline”
- “GEARS 和 shared_mean_baseline 只是对称各赢一半”
- “K562 13d 完整复现了 HCC model-side trade-off 的三个分量”
- “K562 13d 已证明 external model-side generalization”
- “复杂模型没赢 baseline 只是因为没正式接入、coverage 不足或 export 失配”
- “当前已经证明了复杂模型不稳定胜过 baseline 的唯一根因”
- “shared explanatory architecture 已全面建立”
- “stable shared anchors 已被 fully deconfounded”
- “`barcode_gem_group` 已被唯一解析到单个 `MH001...MH006`”
- “多数 axis 已完成同等级正式闭环”
- “Dixit/K562 与 HCC 构成对称 primary conclusion”
- “phenotype shifter discovery 已成为当前正式主交付”

## 5. discovery 为什么当前仍必须保持 gated

discovery 当前仍不是 formal mainline，而且当前默认动作不是“决定是否转正”，而是“继续保持 gated，直到前置条件足够稳定”。

更明确地说，它现在还不能被写成 formal deliverable。

它要进入正式交付，至少需要满足以下前置条件：

1. 比较层已并入主文稿，并固定 `baseline vs GEARS` 的正式解释
2. sensitivity 已完成正式收口，至少主支柱与 limitation 已明确分层
3. covariate balance 已有正式审计结果，混杂风险已降到可写、可防守的程度
4. 最终 claim boundary 已固定，不再摇摆 primary / supporting / preliminary 的层级

这里的第 3 条应按当前仓库口径理解为：

- 已完成第一轮多轴 covariate audit，并已形成 summary / combined TSV / per-axis TSV
- 主张强度已据此完成必要降级
- 但它仍不等于“covariate closure fully closed”

在这些条件满足前，discovery 更稳的角色仍然是：

- downstream application layer
- potential deliverable under gating

而不是：

- 当前阶段 primary deliverable

## 6. discovery 当前最稳的写法

如果当前必须提到 discovery，更稳的写法是：

当前 discovery / phenotype shifter 仍处于 `gated_downstream_layer`。现阶段的主任务不是扩展 discovery 对象，也不是提前决定其 formal deliverable 形态，而是先完成比较、敏感性、混杂与最终 claim boundary 的正式收口。只有在这些前置条件足够清楚后，discovery 才有资格被重新评估是否进入正式交付物边界。

## 7. 推荐主文稿收口段

当前最稳的终局边界可写成：

本阶段已经完成从现象级相关到分层化结构证据的第一轮收口，但仍未完成对 model recovery 的最终证明。当前 primary conclusion 应保留在 `GEARS` 的 architecture trade-off diagnosis、`shared_mean_baseline` 仍是 backbone 更强的 primary reference、复杂 entrant 未能稳定胜过 baseline 的正式 explanation layer、`PFDN5 = primary_but_qualified`、`transcription / chromatin = primary_axis_but_qualified`，以及有限 formal axis evidence 这一层级；其中，`PMF1 / PRPF6 / ZNF131` 等对象仍只能作为 `supporting_only`，anchor-level strongest wording 必须继续受到 covariate audit 边界约束。baseline-vs-GEARS 必须写成非对称 trade-off：`shared_mean_baseline` 是 shared backbone winner，GEARS 是 deviation / separation-biased entrant；shared trend / overall displacement 不能和超出 backbone 可解释部分的 `shift-excess` 混成一层。K562 13d 的 model-side 最小审计只能写成 partial recurrence：backbone-vs-separation 主方向复现，但 `shift-excess` 分量未复现，因此 full three-component recurrence 与 external model-side generalization 均未建立。`Dixit/K562` 固定写成：`GSE90063 K562 13d-only` provides formal supplementary external support for architecture form, with bridge-form support remaining supporting / partial-support; bridge content is not eligible. 因此这些结果不能升级为 primary conclusion、shared mainline architecture content 或 broad cross-context validation。多数 axis 解释、supplementary replication 的 context-specific 细节，以及 discovery / phenotype shifter 的下游应用，则应继续保留在 supporting、preliminary 或 `gated_downstream_layer`。因而，当前项目最重要的任务不是继续扩模型或提前交付 discovery，而是先把比较、敏感性、混杂与最终边界收成一套可防守的正式口径，并持续把 `final claim matrix` 同步到 manuscript wording。

如果要回答“何时开始写论文”，当前更稳的标准是：

- 不是等待 run-level metadata 奇迹般补齐
- 不是等待 covariate 风险完全消失
- 而是确认当前 limitation 已被接受为本阶段不可消除边界，且 manuscript wording 已与这一边界稳定一致

## 8. 渐进披露

默认先看：

1. [`docs/main_manuscript_integrated_narrative_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_integrated_narrative_draft_v1.md)
2. [`docs/main_manuscript_results_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_results_draft_v1.md)
3. [`docs/stage2_sensitivity_full_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_sensitivity_full_closure_note_v1.md)
4. [`docs/stage2_covariate_balance_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_covariate_balance_closure_note_v1.md)
5. [`reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv)
6. [`reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv)
7. [`docs/why_models_do_not_stably_beat_baseline_v1.md`](/home/data/gz0705/WTKO/docs/why_models_do_not_stably_beat_baseline_v1.md)

## 9. 一句话收口

当前终局边界的核心，不是把更多对象硬写进结论，而是把哪些能写、哪些只能保留、哪些还不能交付，彻底钉死。
