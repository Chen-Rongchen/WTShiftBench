# 仓库目录说明

## 1. 设计原则

当前仓库的 active framing 已经改为 **truth-first**：先冻结 truth-side architecture object，再推进 model-side structure adjudication；`Stage 1A / 1B` 仍保留，但其解释角色已从单纯 leaderboard 延伸为 failure decomposition track。

代码层仍保留清晰分层：

- `benchmark-invariant`
- `model-specific adapter`
- `truth-driven bridge / architecture` 产物与分析

## 2. 顶层目录职责

- `README.md`：当前仓库入口与 active framing
- `plan.md`：当前执行优先级
- `pixi.toml`：环境与任务入口
- `configs/`：machine-readable 配置入口
- `scripts/`：实际执行脚本
- `data/`：数据、中间产物、冻结产物与预测输入
- `reports/`：报告与评测结果
- `results/`：保留目录，当前内容较少
- `docs/`：文档层
- `envs/`：环境相关说明
- `vendor/`：本地 vendor 依赖

## 3. 当前推荐理解方式

如果你要理解当前主链路，建议按下面顺序看：

1. `README.md`
2. `plan.md`
3. `docs/project_state_summary_v1.md`
4. `docs/final_claim_boundary_and_discovery_gating_note_v1.md`
5. `docs/why_models_do_not_stably_beat_baseline_v1.md`
6. `docs/model_vs_baseline_deeper_explanation_note_v1.md`
7. `docs/model_vs_baseline_next_step_breakdown_v1.md`
8. `reports/stage2_gears_backbone_sweep/final_adjudication.md`
9. `docs/stage2_truth_bridge_integrated_result_v1.md`
10. `docs/stage2_axis_annotation_result_v1.md`
11. `reports/stage2_axis_analysis/axis_validation_summary.md`
12. `docs/current_closeout_commit_note_v1.md`
13. `docs/protocol_blueprint.md`
14. `docs/stage1_failure_decomposition_note_v1.md`
15. `reports/stage2_truth_driven_bridge/`

如果你要理解“为什么当前阶段不继续扩模型、下一阶段若恢复 entrant expansion 应怎么做”，建议再看：

- `docs/model_expansion_deferral_note_v1.md`
- `docs/next_stage_model_entrant_inventory_v1.md`
- `docs/next_stage_model_entrant_execution_checklist_v1.md`

axis annotation / validation 的机器入口当前补到了：

- `configs/stage2/axis_analysis_template_v1.json`
- `configs/stage2/axis_enrichment_template_v1.json`
- `configs/stage2/axis_target_consistency_template_v1.json`
- `configs/stage2/per_target_signature_materialization_v1.json`
- `configs/stage2/axis_validation_summary_v1.json`
- `scripts/run_stage2_axis_analysis.py`
- `scripts/run_stage2_axis_enrichment.py`
- `scripts/run_stage2_axis_target_consistency.py`
- `scripts/materialize_stage2_per_target_signature.py`
- `scripts/summarize_stage2_axis_validation.py`
- `reports/stage2_axis_analysis/`

混杂 closure 的机器入口当前统一为：

- `configs/stage2/hcc_covariates_v1.json`
- `configs/stage2/truth_bridge_covariate_audit_v1.json`
- `configs/stage2/truth_bridge_sensitivity_covariate_template_v1.json`
- `scripts/materialize_stage2_covariates.py`
- `scripts/run_stage2_covariate_audit.py`
- `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/`

## 4. Stage 1A 目录边界

### scripts

`scripts/stage1a/benchmark_invariant/`

- `formal/`
- `truth_space/`
- `scoring/`
- `catalog.py`
- `prediction_eval_common.py`

`scripts/stage1a/adapters/`

- `common/runtime.py`
- `gears/`
- `scgpt/`
- `geneformer/`

顶层旧脚本仍在 `scripts/` 下保留，但主要作为兼容包装。

### configs

`configs/` 中与 Stage 1A 相关的内容现在分三层：

- 顶层 invariant contract：`stage1a_formal_datasets.yaml`、`stage1a_prediction_contract.yaml`
- adapter configs：`configs/stage1a/adapters/`
- scoring run configs：`configs/stage1a/runs/`

## 5. data 与 reports

这两部分不按模型代码边界迁移，继续保持稳定：

- `data/`：raw、processed、frozen、truth、baseline、prediction 产物
- `reports/`：eligibility、truth、alignment、model evaluation 结果

truth-first 重排不主动搬动这两部分目录。

## 6. 当前优化结论

仓库仍保持“脚本驱动 + 配置入口 + 文档收束”的风格。当前对目录的推荐理解不是“只有 Stage 1A 主线”，而是：

```text
truth architecture freeze
-> model-side adjudication
-> stage1 failure decomposition
-> downstream discovery
```
