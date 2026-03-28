# GEARS Stage 1A Entrant Card

## 当前身份

- `entrant_name: GEARS`
- `entrant_taxonomy: native_perturbation_model`
- 无外部 foundation checkpoint 依赖
- 进入 Stage 1A 前具备 `predicted_shift` 能力，指的是 recipe 已固定，且在给定 train split 下存在从模型原生输入走到 benchmark contract `predicted_shift` 的明确、可复现路径；不等于进入 1A 前已经用 formal 数据全量训练完成

## Stage 1A 训练边界

- 允许在 `Stage 1A train split` 上训练原生模型参数
- 本轮 smoke 只针对 `replogle_2022_k562_essential`
- 本轮 smoke 只针对 `split_seed: 101`
- 不引入 held-out targets 到训练

## preprocessing_identity

- 以 GEARS 原生 perturbation graph、gene graph、训练输入矩阵与 condition 组织方式为准
- `shared control pseudobulk` 只写“与协议一致”，不在本卡内二次定义

## adapter_recipe

- `native_gears_training`
- 不额外引入 foundation backbone 或外接 adapter 主干

## predicted_shift_export_recipe

1. 读取 GEARS 的扰动级预测表达输出
2. 在 perturbation-level 粒度聚合
3. 按协议一致的 control/reference subtraction 执行共享 control subtraction
4. 统一导出 benchmark contract 的 `predicted_shift`

## current_readiness_status

- `pipeline_proven_under_audit`
- `2026-03-28` 已完成 `3 datasets formal batch` 实现跑通；当前新增证据支持“工程链路已稳定”，但不改变 audit 边界

## blocking_issues_before_formal_1a

- `space audit`
- `target-space mismatch`
- `export-space consistency`

## Admission Judgment Before Formal Stage 1A

GEARS 最接近 formal entrant，但需先完成 `space/export audit`，再进入稳定 formal adjudication。

## latest_implementation_note

- 本轮实际修复的是 processed GEARS cache 复用缺失
- 修复后，formal batch 可复用已有 processed cache，不再重复重建 `cell_graphs.pkl`
- 当前正式主线目标数据集已更新为 `replogle_2022_k562_essential`、`replogle_2022_rpe1`、`tian_2019_day7neuron`
- 辅助鲁棒性数据集为 `tian_2021_crispri`，默认不进入 formal 主流程
- `render_pass_skeleton` 也已成功完成
- 上述结果应先按 `audit / exploratory` 边界解释，不直接上升为最终 formal adjudication
