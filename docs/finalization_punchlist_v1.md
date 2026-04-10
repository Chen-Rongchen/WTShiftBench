# 最终收口执行清单 v1

## 1. 文档定位

这份清单只回答一个问题：

**如果下次要一次性把当前项目收到可交付状态，应该按什么顺序做完最后几件事？**

它不再扩分析，只处理：

- 主文稿收口
- 仓库入口统一
- 方法学边界冻结

## 2. 当前已经完成的前提

入口统一工作已完成；这份清单当前更适合作为归档性的最终执行摘要，而不是提示这些入口问题仍未处理。

下次进来前，可以默认以下内容已经成立：

- `GEARS` 已正式收口为 `architecture trade-off diagnosis`
- `truth–DepMap bridge exists` 仍可保留
- stable anchors 已完成对象级降级治理：
  - `PFDN5 = primary_but_qualified`
  - `PMF1 / PRPF6 / ZNF131 = supporting_only`
- `transcription / chromatin = primary_axis_but_qualified`
- `Dixit/K562` 已固定为 `supplementary external structure replication`
- `discovery = gated_downstream_layer`
- 统一口径源已形成：
  - [`reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv)

## 3. 下次进来只做这四件事

### 3.1 主文稿最终压缩

目标：

- 把现有 narrative draft 与 results draft 压成最后一版 manuscript-ready wording

只处理：

- 将 `claim matrix` 全量同步到主文稿
- 将 `claim matrix` 全量同步到摘要式写法与入口文档
- 明确 `allowed wording / disallowed wording`
- 去掉任何旧的 strongest anchor 写法
- 去掉任何会把 Dixit 抬成 primary conclusion 的句子
- 把 baseline explanation 的后续推进固定成“两个更小问题”，不再保留泛问题写法

直接编辑入口：

- [`docs/main_manuscript_integrated_narrative_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_integrated_narrative_draft_v1.md)
- [`docs/main_manuscript_results_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_results_draft_v1.md)
- [`docs/why_models_do_not_stably_beat_baseline_v1.md`](/home/data/gz0705/WTKO/docs/why_models_do_not_stably_beat_baseline_v1.md)
- [`docs/model_vs_baseline_next_step_breakdown_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_next_step_breakdown_v1.md)

### 3.2 仓库入口统一清理

目标：

- 保证 README / plan / docs map 不再引用旧口径或旧文件名

重点检查：

- 是否仍出现旧的 `final_claim_boundary_note_v1`、`stage3_discovery_gating_note_v1` 等过期名称
- 是否仍把 stable anchors 写成 fully deconfounded primary anchors
- 是否仍暗示 Dixit 会进入模型主线对接

直接编辑入口：

- [`README.md`](/home/data/gz0705/WTKO/README.md)
- [`plan.md`](/home/data/gz0705/WTKO/plan.md)

### 3.3 方法学边界最终冻结

目标：

- 写出一段最终阶段摘要，明确哪些已完成，哪些未 fully closed，哪些不能写

这一步不再新增分析，只冻结边界：

- sensitivity 仍不是 formal full closure
- covariate closure 已完成治理，但仍受元数据上限约束
- discovery 继续保持 `gated_downstream_layer`
- `model recovery proved / Stage 2 complete / Stage 3 complete` 继续禁写
- biology-facing explanation 继续停留在 plausible interpretation 层，直到两个更小的方法学问题更清楚

直接确认入口：

- [`docs/project_state_summary_v1.md`](/home/data/gz0705/WTKO/docs/project_state_summary_v1.md)
- [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)
- [`docs/stage2_sensitivity_full_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_sensitivity_full_closure_note_v1.md)
- [`docs/stage2_covariate_balance_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_covariate_balance_closure_note_v1.md)

### 3.4 提交当前阶段

目标：

- 把这一轮“模型线 + Dixit packet + explanation layer + boundary 同步”作为一个阶段性提交收口

直接入口：

- [`docs/current_closeout_commit_note_v1.md`](/home/data/gz0705/WTKO/docs/current_closeout_commit_note_v1.md)

## 4. 下次进来先按这个顺序读

1. [`docs/project_state_summary_v1.md`](/home/data/gz0705/WTKO/docs/project_state_summary_v1.md)
2. [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)
3. [`docs/why_models_do_not_stably_beat_baseline_v1.md`](/home/data/gz0705/WTKO/docs/why_models_do_not_stably_beat_baseline_v1.md)
4. [`docs/model_vs_baseline_deeper_explanation_note_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_deeper_explanation_note_v1.md)
5. [`docs/model_vs_baseline_next_step_breakdown_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_next_step_breakdown_v1.md)
6. [`reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv)
7. [`docs/main_manuscript_integrated_narrative_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_integrated_narrative_draft_v1.md)
8. [`docs/main_manuscript_results_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_results_draft_v1.md)
9. [`docs/current_closeout_commit_note_v1.md`](/home/data/gz0705/WTKO/docs/current_closeout_commit_note_v1.md)

## 5. 下次进来不要再做什么

- 不再扩 entrant
- 不再把 Dixit 接到模型主线
- 不再把 stable anchor 写成 fully deconfounded strongest anchor
- 不再为 covariate closure 无停止规则地加审计轴
- 不提前写 `model recovery proved`
- 不再为“为什么模型没稳定赢 baseline”额外扩模型

## 6. 一句话收口

下次进来不是继续找新结果，而是按 `状态摘要 -> 最终边界 -> baseline explanation 边界 -> 两个更小问题 -> 主文稿 -> 提交说明` 这条固定链，一次性完成当前阶段收口。
