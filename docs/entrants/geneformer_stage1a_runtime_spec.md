# Geneformer Stage 1A Runtime Spec

## 范围

- 本轮 inner-validation 收口范围是 `3 datasets × seed101`
- datasets:
  - `replogle_2022_k562_essential`
  - `replogle_2022_rpe1`
  - `tian_2019_day7neuron`
- 辅助鲁棒性数据集：`tian_2021_crispri`（默认不进入主线）
- 使用本地已有 `geneformer_gf_12l_95m_i4096`
- 当前只先实现 `embedding_plus_adapter`
- `in_silico_perturbation_plus_adapter` 先保留为候选，不进入本轮主编码
- backbone 默认冻结
- 当前 smoke 目标是：
  - checkpoint 可载入
  - tokenizer / mapping 正常
  - embedding 路径可跑通
  - adapter 可训练
  - `predicted_shift` 可导出

## runtime-level defaults

- 对外统一字段：`max_epochs`
- 当前 `max_epochs` 属于本项目 adapter trainer，不是官方 backbone 原生参数名
- `preferred_workflow: embedding_plus_adapter`
- `backbone_freeze: true`
- `trainable_components: adapter_head_only`
- `optimizer: adamw`
- `learning_rate: 1e-4`
- `weight_decay: 1e-4`
- `batch_size: 16`
- `max_epochs: 30`
- `early_stopping_enabled: true`
- `early_stopping_patience: 3`
- `validation_rule: train_only_internal_validation`
- `checkpoint_selection_rule: best_validation_checkpoint`
- `random_seed_policy: explicit_single_seed`
- `device_policy: gpu_if_available_else_cpu`
- `device_resolution_rule: use_gpu_when_available_else_fallback_to_cpu`
- `inner_seed: 11`
- `inner_val_fraction: 0.2`
