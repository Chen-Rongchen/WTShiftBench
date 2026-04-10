# 下一阶段执行清单 v1

## 1. 文档定位

这份文档只做一件事：

**把“比较、敏感性、混杂、最终边界、discovery 交付物”五个缺口，压成一页可直接执行的清单。**

它不重写已有结果；entrant expansion 若继续，只能作为 frozen contract 下的次级执行线。

## 2. 当前执行原则

- 不做无 contract freeze 的扩模型
- 不回头重做 truth object
- 不升级辅助指标为新的主裁决层
- 先把现有结果收成可写、可防守、可继续 formal closure 的口径

## 3. 五项缺口的当前状态

### 3.1 比较

当前状态：**已有正式解释层文档，可并入主文稿。**

现有入口：

- [`docs/stage2_fuller_hcc_model_comparison_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_fuller_hcc_model_comparison_note_v1.md)
- [`docs/why_models_do_not_stably_beat_baseline_v1.md`](/home/data/gz0705/WTKO/docs/why_models_do_not_stably_beat_baseline_v1.md)
- [`docs/model_vs_baseline_deeper_explanation_note_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_deeper_explanation_note_v1.md)
- [`docs/model_vs_baseline_next_step_breakdown_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_next_step_breakdown_v1.md)
- [`reports/stage2_real_hcc_smoke/model_comparison.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/model_comparison.tsv)
- [`reports/stage2_gears_backbone_sweep/final_adjudication.md`](/home/data/gz0705/WTKO/reports/stage2_gears_backbone_sweep/final_adjudication.md)

当前结论：

- `shared_mean_baseline` 仍是 backbone 更强的 primary reference
- `GEARS` 保留为 `architecture trade-off diagnosis`
- 有限 sweep 暴露的是 `trade-off frontier`，不是 hidden winner

当前动作：

- 直接把比较层并入主文稿叙事
- 若继续追问“为什么 baseline 仍赢”，先用 deeper note 固定解释边界，再用 next-step breakdown 把问题拆成两个更小的问题
- 比较线若继续推进，优先回答：
  - `baseline winner` 是否主要由 shared backbone objective 决定
  - entrant 的额外能力是否稳定落在 `separation / deviation` 而非 backbone 上
- 不再把“再跑一轮 GEARS”当默认下一步

### 3.2 敏感性

当前状态：**已有大半材料，但 formal closure 仍未完成。**

现有入口：

- [`docs/stage2_sensitivity_full_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_sensitivity_full_closure_note_v1.md)
- [`reports/stage2_truth_driven_bridge/sensitivity/sensitivity_report.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/sensitivity_report.md)
- [`reports/stage2_truth_bridge_decomposition/axis_bootstrap_stability.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_bridge_decomposition/axis_bootstrap_stability.tsv)
- [`reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv)

当前判断：

- `anchor cutoff stability` 已足够支持主支柱锚点的保守写法
- `axis bootstrap stability` 已足够支持“formal axis evidence 很有限”的边界
- `control subsampling` 对多数 shift-based 指标给出正向稳定信号
- `DEG burden` 仍更敏感，应继续保留为辅助层
- 未跑满 sensitivity replicates 前，禁止写 formal interval claim

当前动作：

- 先按“已关闭 / 剩余风险 / limitation”三分法写入主文稿
- 继续把 sensitivity repeat 跑满到配置重复数
- 未完成前，不升级为 robustness fully established

### 3.3 混杂

当前状态：**第一轮审计产物已存在，但 full closure 仍未完成。**

现有入口：

- [`docs/stage2_covariate_balance_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_covariate_balance_closure_note_v1.md)
- [`reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.md)
- [`src/wtbench/stage2_truth_sensitivity.py`](/home/data/gz0705/WTKO/src/wtbench/stage2_truth_sensitivity.py)
- [`scripts/run_stage2_truth_bridge_sensitivity.py`](/home/data/gz0705/WTKO/scripts/run_stage2_truth_bridge_sensitivity.py)
- [`configs/stage2/truth_bridge_sensitivity_covariate_template_v1.json`](/home/data/gz0705/WTKO/configs/stage2/truth_bridge_sensitivity_covariate_template_v1.json)
- [`scripts/materialize_stage2_covariates.py`](/home/data/gz0705/WTKO/scripts/materialize_stage2_covariates.py)
- [`scripts/run_stage2_covariate_audit.py`](/home/data/gz0705/WTKO/scripts/run_stage2_covariate_audit.py)

当前判断：

- `covariate_balance` 是当前剩余的主要方法学风险
- 第一轮 `num_umis_quantile_bin` 审计已经落盘
- 但 stable anchors 中已有对象表现出不可忽略的 target-control 分布差异
- 因此这条线当前仍不能写成“已关闭”，只能写成“已完成第一轮审计，但仍待更完整 closure”

当前动作：

- 继续补更贴近实验设计的 covariates TSV
- 在现有 `num_umis` 审计基础上增加新的分层轴
- 再判断哪些主张可保留，哪些要降级

### 3.4 最终边界

当前状态：**边界文档与 claim matrix 已成形，可作为统一口径源。**

现有入口：

- [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)
- [`reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv)
- [`docs/main_manuscript_integrated_narrative_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_integrated_narrative_draft_v1.md)
- [`docs/main_manuscript_results_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_results_draft_v1.md)

当前判断：

- 可写成 primary conclusion 的，是 trade-off diagnosis、stable anchors、limited formal axis evidence
- 只能保留为 supporting / preliminary 的，是多数 axis、supplementary replication 的 context-specific 细节
- 当前仍不能写成“model recovery has been demonstrated”

当前动作：

- 以 claim matrix 为统一口径源继续压主文稿
- 后续若有新方法学结果，先更新 claim matrix，再改正文措辞

### 3.5 discovery 交付物

当前状态：**仍处于 gating，而不是正式 mainline。**

现有入口：

- [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)

当前判断：

- discovery 现在还不能直接写成 formal deliverable
- 只有在比较、敏感性、混杂、最终边界都足够清楚后，才有资格决定是否进入主线交付

当前动作：

- 暂时固定为 downstream application layer
- 不提前升级为当前阶段 primary deliverable

## 4. 推荐执行顺序

1. 把比较并入主文稿
2. 把敏感性收成正式 closure note
3. 完成 covariate balance 审计与混杂收口
4. 固定最终 claim boundary
5. 再决定 discovery 是否进入正式交付

## 5. 现在直接看什么

默认先看：

1. [`docs/stage2_fuller_hcc_model_comparison_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_fuller_hcc_model_comparison_note_v1.md)
2. [`docs/why_models_do_not_stably_beat_baseline_v1.md`](/home/data/gz0705/WTKO/docs/why_models_do_not_stably_beat_baseline_v1.md)
3. [`docs/model_vs_baseline_deeper_explanation_note_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_deeper_explanation_note_v1.md)
4. [`docs/model_vs_baseline_next_step_breakdown_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_next_step_breakdown_v1.md)
5. [`docs/stage2_sensitivity_full_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_sensitivity_full_closure_note_v1.md)
6. [`docs/stage2_covariate_balance_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_covariate_balance_closure_note_v1.md)
7. [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)
8. [`reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv)

如果后续决定恢复 entrant expansion，先看：

1. [`docs/model_expansion_deferral_note_v1.md`](/home/data/gz0705/WTKO/docs/model_expansion_deferral_note_v1.md)
2. [`docs/next_stage_model_entrant_inventory_v1.md`](/home/data/gz0705/WTKO/docs/next_stage_model_entrant_inventory_v1.md)
3. [`docs/next_stage_model_entrant_execution_checklist_v1.md`](/home/data/gz0705/WTKO/docs/next_stage_model_entrant_execution_checklist_v1.md)

## 6. 一句话收口

下一阶段真正要做的，不是继续扩模型，而是把已有结构化结果压成一套对主文稿、方法学风险与 discovery 入口都可防守的正式边界。
