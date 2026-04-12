# 当前阶段收尾提交说明 v1

## 1. 文档定位

这份文档只回答一个问题：

**如果现在要把当前阶段正式提交收口，这一批改动应该如何描述？**

它不决定是否立刻提交，只提供推荐的提交范围与提交说明。

## 2. 推荐提交范围

这一批提交应聚焦于：

- 仓库入口统一
- claim governance 统一
- 主文稿草案收口
- 方法学边界冻结
- covariate audit 入口与汇总产物统一
- 下一阶段 entrant expansion 的文档化交接
- `pixi` 执行入口与 closure pipeline 收口
- claim / tier 关键产物的轻量校验工具

如果当前只想提交这一轮“正式口径同步”本身，建议优先采用**最小提交集**：

- [`README.md`](/home/data/gz0705/WTKO/README.md)
- [`plan.md`](/home/data/gz0705/WTKO/plan.md)
- [`docs/formal_closeout_single_entry_v1.md`](/home/data/gz0705/WTKO/docs/formal_closeout_single_entry_v1.md)
- [`docs/project_state_summary_v1.md`](/home/data/gz0705/WTKO/docs/project_state_summary_v1.md)
- [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)
- [`docs/why_models_do_not_stably_beat_baseline_v1.md`](/home/data/gz0705/WTKO/docs/why_models_do_not_stably_beat_baseline_v1.md)
- [`docs/main_manuscript_integrated_narrative_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_integrated_narrative_draft_v1.md)
- [`docs/main_manuscript_results_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_results_draft_v1.md)
- [`docs/stage2_sensitivity_full_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_sensitivity_full_closure_note_v1.md)
- [`docs/stage2_covariate_balance_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_covariate_balance_closure_note_v1.md)
- [`docs/stage2_truth_bridge_integrated_result_v1.md`](/home/data/gz0705/WTKO/docs/stage2_truth_bridge_integrated_result_v1.md)
- [`docs/next_phase_execution_note_v1.md`](/home/data/gz0705/WTKO/docs/next_phase_execution_note_v1.md)
- [`docs/next_phase_execution_checklist_v1.md`](/home/data/gz0705/WTKO/docs/next_phase_execution_checklist_v1.md)
- [`docs/finalization_punchlist_v1.md`](/home/data/gz0705/WTKO/docs/finalization_punchlist_v1.md)
- [`scripts/README.md`](/home/data/gz0705/WTKO/scripts/README.md)
- [`configs/README.md`](/home/data/gz0705/WTKO/configs/README.md)
- [`pixi.toml`](/home/data/gz0705/WTKO/pixi.toml)
- [`scripts/run_stage2_closure_pipeline.py`](/home/data/gz0705/WTKO/scripts/run_stage2_closure_pipeline.py)
- [`scripts/validate_stage2_closure_artifacts.py`](/home/data/gz0705/WTKO/scripts/validate_stage2_closure_artifacts.py)
- [`scripts/run_stage2_truth_bridge_sensitivity.py`](/home/data/gz0705/WTKO/scripts/run_stage2_truth_bridge_sensitivity.py)
- [`scripts/run_stage2_covariate_audit.py`](/home/data/gz0705/WTKO/scripts/run_stage2_covariate_audit.py)
- [`scripts/materialize_stage2_covariates.py`](/home/data/gz0705/WTKO/scripts/materialize_stage2_covariates.py)
- [`configs/stage2/truth_bridge_sensitivity_hcc_full_v1.json`](/home/data/gz0705/WTKO/configs/stage2/truth_bridge_sensitivity_hcc_full_v1.json)
- [`configs/stage2/stage2_closure_pipeline_v1.json`](/home/data/gz0705/WTKO/configs/stage2/stage2_closure_pipeline_v1.json)
- [`configs/stage2/closure_artifact_validation_v1.json`](/home/data/gz0705/WTKO/configs/stage2/closure_artifact_validation_v1.json)
- [`tests/test_stage2_closure_pipeline.py`](/home/data/gz0705/WTKO/tests/test_stage2_closure_pipeline.py)
- [`docs/current_closeout_commit_note_v1.md`](/home/data/gz0705/WTKO/docs/current_closeout_commit_note_v1.md)

如果要把“下一阶段启动入口”和“entrant expansion 交接文档”也一起带上，再使用**扩展提交集**。扩展集可在最小提交集基础上继续加入：

- [`README.md`](/home/data/gz0705/WTKO/README.md)
- [`plan.md`](/home/data/gz0705/WTKO/plan.md)
- [`docs/formal_closeout_single_entry_v1.md`](/home/data/gz0705/WTKO/docs/formal_closeout_single_entry_v1.md)
- [`docs/model_vs_baseline_deeper_explanation_note_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_deeper_explanation_note_v1.md)
- [`docs/model_vs_baseline_next_step_breakdown_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_next_step_breakdown_v1.md)
- [`docs/model_expansion_deferral_note_v1.md`](/home/data/gz0705/WTKO/docs/model_expansion_deferral_note_v1.md)
- [`docs/next_stage_model_entrant_inventory_v1.md`](/home/data/gz0705/WTKO/docs/next_stage_model_entrant_inventory_v1.md)
- [`docs/next_stage_model_entrant_execution_checklist_v1.md`](/home/data/gz0705/WTKO/docs/next_stage_model_entrant_execution_checklist_v1.md)
- [`docs/next_stage_startup_packet_v1.md`](/home/data/gz0705/WTKO/docs/next_stage_startup_packet_v1.md)
- [`scripts/run_stage2_covariate_audit.py`](/home/data/gz0705/WTKO/scripts/run_stage2_covariate_audit.py)
- [`configs/stage2/truth_bridge_covariate_audit_v1.json`](/home/data/gz0705/WTKO/configs/stage2/truth_bridge_covariate_audit_v1.json)

## 3. 推荐提交标题

```text
docs: finalize closeout boundary and baseline gap next steps
```

## 4. 推荐提交正文

```text
- unify README/plan/manuscript/boundary docs to final claim matrix wording
- keep `final claim matrix -> manuscript wording` as an ongoing sync, not a one-shot closeout
- split baseline-vs-model follow-up into two smaller methodology-facing questions
- freeze anchor/axis/discovery/Dixit wording at the current claim boundary
- sync sensitivity/covariate limitations to the final closeout wording
- add manuscript-ready wording for the baseline gap follow-up path
- sync closeout/read-order docs to the new baseline explanation chain
```

如果想保留旧的 `covariate audit handoff` 强调，也可以使用这个备选标题：

```text
docs: finalize closeout boundary and covariate handoff
```

## 5. 提交前最后检查

提交前只需要再看四件事：

1. [`README.md`](/home/data/gz0705/WTKO/README.md)
   - 入口是否仍指向当前唯一主链
2. [`docs/formal_closeout_single_entry_v1.md`](/home/data/gz0705/WTKO/docs/formal_closeout_single_entry_v1.md)
   - 单页总入口是否与主文稿、boundary、execution note 保持同一顺序
3. [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)
   - claim boundary 是否仍与 final claim matrix 一致
4. [`docs/stage2_covariate_balance_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_covariate_balance_closure_note_v1.md)
   - covariate 线是否明确写成“已完成多轴审计，但仍受元数据上限约束”

以及一条工程纪律：

- `.gitignore` 当前已忽略 `reports/`、`data/processed/`、`results/`、`.pixi/` 等本地运行产物；这一轮提交不应把重跑结果或环境目录带入版本管理，只提交 `docs/`、`scripts/`、`configs/`、`tests/` 与必要源码改动。

## 6. 一句话收口

这批提交的目标不是再加新结果，而是把当前阶段已经形成的主张治理、主文稿收口、方法学边界与下一阶段入口一次性整理干净。
