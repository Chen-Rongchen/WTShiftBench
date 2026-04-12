# 项目完成路线图 v2

## 1. 文档定位

这份文档只回答一个问题：

**从现在开始，最近需要完成什么，一直到项目完成，应该按什么顺序推进？**

它是当前唯一的 completion roadmap，不再把“下一步”“收口”“主文稿同步”分散在多份清单里。

这份文档不再新增分析主线，只负责：

- 固定最近优先级
- 说明什么叫“项目完成”
- 把从现在到完成的步骤压成一条单路径

## 2. 当前起点

进入这份路线图时，默认以下状态已经成立：

- `HCC` 仍是 primary mainline
- `GEARS` 已正式收口为 `architecture trade-off diagnosis`
- `truth–DepMap bridge` 可保留，但必须按 evidence tier 书写
- `PFDN5 = primary_but_qualified`
- `PMF1 / PRPF6 / ZNF131 = supporting_only`
- `transcription / chromatin = primary_axis_but_qualified`
- `Dixit/K562` 已固定为基于 `GSE90063 K562 13d-only` 的 `supplementary external structure replication`
- `K562 13d` 当前最稳的分层是：`A0 architecture form confirmed / A1 bridge form supporting / B not eligible`
- `discovery = gated_downstream_layer`
- 统一口径源已形成：[`reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv)

## 3. 项目完成的定义

当前“项目完成”不等于：

- 新 entrant 继续扩完
- covariate 风险彻底消失
- discovery 正式启动
- 所有 biological explanation 都被完全证明

当前更准确的“完成”定义是：

1. 主文稿已经收成 manuscript-ready wording
2. `final claim matrix` 已稳定同步到主文稿和仓库入口
3. sensitivity / covariate / discovery gating 的边界已经冻结且不再摇摆
4. `Dixit/K562` 的 supplementary 证据层级已经固定，不再被误写成 primary
5. `Stage 1A / 1B` 已完成 failure decomposition 的正式解释归位
6. 图稿与总入口文档已经和上述边界一致

只要这 6 条成立，项目就应视为当前阶段 formal complete。

## 4. 最近先做什么

最近只优先做下面 3 件事：

1. `final claim matrix -> manuscript wording`
2. `covariate balance closure`
3. `sensitivity full closure`

这三件事完成前：

- 不继续扩 entrant
- 不回头重做 truth object
- 不把 discovery 提前升级
- 不再把“为什么模型没赢 baseline”保留为开放式泛问题

## 5. 从现在到完成的固定顺序

### 5.1 第一步：主张矩阵压入主文稿

目标：

- 把当前分层后的 allowed wording / disallowed wording 压进主文稿正文

完成标准：

- narrative draft 与 results draft 对 `GEARS`、anchors、axes、`Dixit/K562` 的写法完全一致
- 不再残留旧的 strongest-anchor 写法
- 不再残留会把 `Dixit/K562` 抬成 primary co-pillar 的句子
- baseline gap 的后续解释已固定为两个更小问题

直接入口：

- [`docs/main_manuscript_integrated_narrative_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_integrated_narrative_draft_v1.md)
- [`docs/main_manuscript_results_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_results_draft_v1.md)
- [`docs/why_models_do_not_stably_beat_baseline_v1.md`](/home/data/gz0705/WTKO/docs/why_models_do_not_stably_beat_baseline_v1.md)
- [`docs/model_vs_baseline_next_step_breakdown_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_next_step_breakdown_v1.md)

### 5.2 第二步：混杂边界正式收口

目标：

- 结束对 covariate 线“是否还能继续追”的摇摆

完成标准：

- 五条 covariate 轴继续保留为正式审计入口
- `barcode_gem_group` 固定写成 `design-proxy axis`
- 不再继续追写单个 `MH00x`
- 相关文稿统一承认：风险已治理进边界，但不是 `fully deconfounded`

直接入口：

- [`docs/stage2_covariate_balance_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_covariate_balance_closure_note_v1.md)
- [`reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv)
- [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)

### 5.3 第三步：敏感性边界正式收口

目标：

- 把 sensitivity 的“已完成什么、没完成什么”写成可引用边界

完成标准：

- `formal interval` 可引用这件事已明确写入主文稿和边界文档
- `full closure` 未完成的原因被明确收缩到 covariate closure 未 fully closed
- `DEG burden` 继续停留在辅助层，不被误升为 headline

直接入口：

- [`docs/stage2_sensitivity_full_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_sensitivity_full_closure_note_v1.md)
- [`reports/stage2_truth_driven_bridge/sensitivity/sensitivity_report.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/sensitivity_report.md)

### 5.4 第四步：固定 supplementary 与 primary 的边界

目标：

- 把 `Dixit/K562` 的最终位置彻底钉死

完成标准：

- `K562 13d` 统一写成 `formal supplementary external evidence`
- 统一保留 `A0 confirmed / A1 supporting / B not eligible`
- 明确 `n=10` 个可桥接 targets 只支撑 bridge-form support
- 不再残留任何 shared mainline content、broad cross-context validation、primary co-pillar 写法

直接入口：

- [`docs/stage2_dixit_supplementary_evidence_tier_v1.md`](/home/data/gz0705/WTKO/docs/stage2_dixit_supplementary_evidence_tier_v1.md)
- [`docs/stage2_dixit_admission_contract_v1.md`](/home/data/gz0705/WTKO/docs/stage2_dixit_admission_contract_v1.md)
- [`docs/stage2_truth_bridge_integrated_result_v1.md`](/home/data/gz0705/WTKO/docs/stage2_truth_bridge_integrated_result_v1.md)

### 5.5 第五步：完成 `Stage 1A / 1B` 的解释归位

目标：

- 把 `Stage 1A / 1B` 从旧 benchmark 叙事，彻底改写成 failure decomposition track

完成标准：

- 主文稿里不再把 `Stage 1A / 1B` 当成独立 leaderboard 主线
- 已明确它们回答的是 short-horizon / long-horizon failure mode
- 它们与 `Stage 2` 的关系变成解释层，而不是竞争主结论层

直接入口：

- [`docs/stage1_failure_decomposition_note_v1.md`](/home/data/gz0705/WTKO/docs/stage1_failure_decomposition_note_v1.md)
- [`docs/main_manuscript_integrated_narrative_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_integrated_narrative_draft_v1.md)

### 5.6 第六步：仓库入口与总入口统一

目标：

- 保证用户从仓库入口读到的就是当前最终口径

完成标准：

- `README.md`、`plan.md`、`docs/project_state_summary_v1.md`、`docs/formal_closeout_single_entry_v1.md` 相互一致
- 不再引用过期文件名或过期路径
- 默认运行入口和默认叙事入口已经稳定

直接入口：

- [`README.md`](/home/data/gz0705/WTKO/README.md)
- [`plan.md`](/home/data/gz0705/WTKO/plan.md)
- [`docs/project_state_summary_v1.md`](/home/data/gz0705/WTKO/docs/project_state_summary_v1.md)
- [`docs/formal_closeout_single_entry_v1.md`](/home/data/gz0705/WTKO/docs/formal_closeout_single_entry_v1.md)

### 5.7 第七步：论文图稿与提交包同步

目标：

- 让图、正文、边界三者一致

完成标准：

- figure blueprint 不再和正文 claim strength 冲突
- figure ordering 与当前主线一致：`truth bridge -> model trade-off -> axis validation -> covariate boundary + Dixit`
- 当前阶段的提交说明已能独立解释这一轮完成了什么

直接入口：

- [`docs/manuscript_figure_blueprint_v1.md`](/home/data/gz0705/WTKO/docs/manuscript_figure_blueprint_v1.md)
- [`docs/current_closeout_commit_note_v1.md`](/home/data/gz0705/WTKO/docs/current_closeout_commit_note_v1.md)

## 6. 完成前不要再做什么

- 不再扩 entrant
- 不再新增 truth object
- 不再把 `Dixit/K562` 接回模型主线
- 不再为 covariate closure 无停止规则地继续加审计轴
- 不提前写 `model recovery proved`
- 不把 `Stage 2 complete` 或 `Stage 3 complete` 提前写进正文
- 不把 discovery 提前写成 formal deliverable

## 7. 默认阅读顺序

如果下次进来只想按“离完成最近”的顺序看，固定读：

1. [`reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv)
2. [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)
3. [`docs/main_manuscript_integrated_narrative_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_integrated_narrative_draft_v1.md)
4. [`docs/main_manuscript_results_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_results_draft_v1.md)
5. [`docs/stage2_covariate_balance_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_covariate_balance_closure_note_v1.md)
6. [`docs/stage2_sensitivity_full_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_sensitivity_full_closure_note_v1.md)
7. [`docs/stage2_dixit_supplementary_evidence_tier_v1.md`](/home/data/gz0705/WTKO/docs/stage2_dixit_supplementary_evidence_tier_v1.md)
8. [`docs/stage1_failure_decomposition_note_v1.md`](/home/data/gz0705/WTKO/docs/stage1_failure_decomposition_note_v1.md)
9. [`docs/manuscript_figure_blueprint_v1.md`](/home/data/gz0705/WTKO/docs/manuscript_figure_blueprint_v1.md)

## 8. 一句话收口

从现在到项目完成，不再是继续找新结果，而是按 `claim matrix -> 主文稿 -> covariate / sensitivity 边界 -> Dixit supplementary 边界 -> Stage 1A / 1B 解释归位 -> 仓库入口统一 -> 图稿与提交包同步` 这条固定链，把当前结果收成一套 manuscript-ready、边界稳定、可防守的正式交付。
