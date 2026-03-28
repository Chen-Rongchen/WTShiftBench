# scGPT Stage 1A Entrant Card

## 当前身份

- `entrant_name: scgpt_human`
- `entrant_taxonomy: foundation_model_plus_adapter`
- 使用本地已有 `scgpt_human`
- checkpoint provenance 统一引用 `configs/entrants/checkpoint_registry.yaml`
- 进入 Stage 1A 前具备 `predicted_shift` 能力，指的是 recipe 已固定，且在给定 train split 下存在从模型原生输入走到 benchmark contract `predicted_shift` 的明确、可复现路径；不等于进入 1A 前已经用 formal 数据全量训练完成

## preprocessing_identity

- `gene vocabulary`
- `gene mapping`
- `model-native matrix preparation`

本轮 smoke 的 model-native 输入路径为 target-side gene feature / gene embedding lookup，不把 held-out perturbation cells 当作训练输入。

## adapter_recipe

- `fixed backbone + trainable adapter/head`

## stage1a_trainable_components

- adapter/head trainable
- backbone 默认冻结

## predicted_shift_export_recipe

- 原始模型输出不能直接当 formal `predicted_shift`
- 必须经过 projection/export step
- control subtraction 位置固定在 recipe 中：train-target `real_shift` 作为监督目标，adapter/head 输出直接对齐到 benchmark contract

## current_readiness_status

- `environment_ready_recipe_not_frozen`

## blocking_issues_before_formal_1a

- checkpoint identity 需在 registry 中冻结
- adapter recipe 尚未冻结为最终版
- export recipe 尚未冻结为最终版

## Admission Judgment Before Formal Stage 1A

scGPT 尚未达到 formal Stage 1A entrant 状态；需先冻结 checkpoint、adapter recipe 与 predicted_shift export recipe。
