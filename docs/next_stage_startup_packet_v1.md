# 下一阶段启动包 v1

## 1. 文档定位

这份文档只回答一个问题：

**如果当前阶段已经结束，下一阶段第一周最应该先做什么？**

它不展开全部路线，只给一个最小启动包。

## 2. 推荐启动方式

下一阶段建议分成两条互不打架的启动线：

### 线 A：方法学闭环

目标：

- 完成比较 / sensitivity / covariate / final boundary 的剩余缺口
- 明确 discovery 继续保持 `gated_downstream_layer`

直接入口：

- [`docs/next_phase_execution_note_v1.md`](/home/data/gz0705/WTKO/docs/next_phase_execution_note_v1.md)
- [`docs/next_phase_execution_checklist_v1.md`](/home/data/gz0705/WTKO/docs/next_phase_execution_checklist_v1.md)
- [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)

### 线 B：linear controls

目标：

- 不再继续扩新的 foundation-model entrant
- 回收 `GEARS / scGPT / Geneformer / linear controls` 已完成的比较结果
- 如无明确新问题，不再新增 control family

直接入口：

- [`docs/entrant_family_execution_packet_v1.md`](/home/data/gz0705/WTKO/docs/entrant_family_execution_packet_v1.md)
- [`docs/stage2_linear_controls_execution_checklist_v1.md`](/home/data/gz0705/WTKO/docs/stage2_linear_controls_execution_checklist_v1.md)

## 3. 最推荐的第一任务

如果下一阶段只能先做一个任务，最推荐的是：

**先把比较、敏感性、混杂与最终边界的统一口径压稳，并明确 discovery 继续保持 gated，而不是继续扩新的 entrant。**

原因：

- 这是当前真正决定项目能否进入 formal closeout 的主线
- 它能直接把 `final claim matrix` 同步成 manuscript-ready wording
- 这一步不会阻碍后续对 entrant family 的归档性整理

## 4. 方法学闭环第一任务包

### 4.1 目标

把下面这些内容钉死成一份统一启动包：

- 当前比较层正式解释
- sensitivity / covariate 的 manuscript-ready 边界
- `final claim matrix -> manuscript wording` 的同步口径
- discovery 继续保持 gated 的统一写法

### 4.2 输入文档

先读：

1. [`docs/next_phase_execution_note_v1.md`](/home/data/gz0705/WTKO/docs/next_phase_execution_note_v1.md)
2. [`docs/next_phase_execution_checklist_v1.md`](/home/data/gz0705/WTKO/docs/next_phase_execution_checklist_v1.md)
3. [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)
4. [`docs/project_state_summary_v1.md`](/home/data/gz0705/WTKO/docs/project_state_summary_v1.md)

### 4.3 最小产出

第一任务完成后，至少应新增或明确：

- 一份比较层的最终并稿口径
- 一份 sensitivity / covariate / final boundary 的统一摘要
- 一份 discovery 继续保持 `gated_downstream_layer` 的更新入口

当前 entrant family / control 相关文档应继续保留为次级参考入口，而不是默认第一任务：

- [`docs/stage2_scgpt_hcc_recipe_freeze_v1.md`](/home/data/gz0705/WTKO/docs/stage2_scgpt_hcc_recipe_freeze_v1.md)
- [`docs/stage2_geneformer_hcc_recipe_freeze_v1.md`](/home/data/gz0705/WTKO/docs/stage2_geneformer_hcc_recipe_freeze_v1.md)
- [`docs/stage2_linear_controls_execution_checklist_v1.md`](/home/data/gz0705/WTKO/docs/stage2_linear_controls_execution_checklist_v1.md)
- [`configs/stage1a/challengers/lm_train_lowrank_batch.json`](/home/data/gz0705/WTKO/configs/stage1a/challengers/lm_train_lowrank_batch.json)
- [`scripts/stage1a/challengers/run_lm_train_lowrank_batch.py`](/home/data/gz0705/WTKO/scripts/stage1a/challengers/run_lm_train_lowrank_batch.py)

### 4.4 完成标准

只有满足下面条件，才算第一任务完成：

- 比较、敏感性、混杂、最终边界的顺序已固定
- `final claim matrix` 已同步到主文稿与入口文档
- discovery 已明确继续保持 `gated_downstream_layer`
- 没有把 entrant expansion 重新写回默认主线

## 5. 当前不建议的启动方式

- 不建议跳过比较 / sensitivity / covariate / final boundary，直接回到 entrant family 写作
- 不建议把 `lm_train_lowrank / lm_G_scgpt_ridge / lm_G_geneformer_ridge` 一起推进
- 不建议 contract 未冻结就直接开 `HCC38 / HCC1143` 批量预测
- 不建议跳过 coverage audit 直接进 `run_stage2_real_hcc_smoke.py`

## 6. 一句话收口

下一阶段最稳的启动方式是：**先把比较、敏感性、混杂、最终边界收成统一正式口径，并继续保持 discovery gated；entrant family 与 linear controls 只作为次级归档与解释层资产保留。**
