# Geneformer Stage 1A Entrant Card

## 当前身份

- `entrant_name: geneformer_gf_12l_95m_i4096`
- `entrant_taxonomy: foundation_model_plus_adapter`
- 使用本地已有 `geneformer_gf_12l_95m_i4096`
- checkpoint provenance 统一引用 `configs/entrants/checkpoint_registry.yaml`
- 进入 Stage 1A 前具备 `predicted_shift` 能力，指的是 recipe 已固定，且在给定 train split 下存在从模型原生输入走到 benchmark contract `predicted_shift` 的明确、可复现路径；不等于进入 1A 前已经用 formal 数据全量训练完成

## preprocessing_identity

- `tokenizer`
- `gene mapping`
- `model-native feature preparation`

本轮 smoke 只先实现 target-side embedding lookup，不把 held-out perturbation cells 当作训练输入。

## adapter_recipe

- 当前 smoke 首选 `embedding_plus_adapter`

## stage1a_trainable_components

- adapter/head trainable
- backbone 默认冻结

## predicted_shift_export_recipe

- 原始输出不能直接当 formal `predicted_shift`
- 必须经过 projection/export step
- 当前 smoke 统一为 `embedding_plus_adapter -> adapter/head -> predicted_shift`

## Candidate Workflow Types

- `candidate_workflow_A: embedding_plus_adapter`
- `candidate_workflow_B: in_silico_perturbation_plus_adapter`
- `preferred_current_candidate: embedding_plus_adapter`

## current_readiness_status

- `environment_ready_recipe_not_frozen`

## blocking_issues_before_formal_1a

- checkpoint identity 需在 registry 中冻结
- workflow type 尚未冻结为最终版
- export recipe 尚未冻结为最终版

## Admission Judgment Before Formal Stage 1A

Geneformer 尚未达到 formal Stage 1A entrant 状态；需先冻结 checkpoint、workflow type 与 predicted_shift export recipe。
