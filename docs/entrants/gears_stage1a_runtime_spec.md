# GEARS Stage 1A Runtime Spec

## 范围

- 本轮 inner-validation 收口范围是 `3 datasets × seed101`
- datasets:
  - `replogle_2022_k562_essential`
  - `replogle_2022_rpe1`
  - `tian_2019_day7neuron`
- 辅助鲁棒性数据集：`tian_2021_crispri`（默认不进入主线）
- GEARS 允许在 `train split` 上训练
- outer split 固定后，仅从 `outer_train_targets` 再切 `inner_train_targets / inner_val_targets`
- 当前不是 formal multi-seed
- 当前主阻断不是“epoch 够不够多”，而是 `space/export audit`

## runtime-level defaults

- 对外统一字段：`max_epochs`
- entrant 内部映射：`max_epochs -> GEARS official epochs`
- `optimizer: adam`
- `learning_rate: 1e-3`
- `weight_decay: 1e-6`
- `batch_size: 32`
- `max_epochs: 30`
- `early_stopping_enabled: true`
- `early_stopping_patience: 5`
- `validation_rule: train_only_internal_validation`
- `checkpoint_selection_rule: best_validation_checkpoint`
- `random_seed_policy: explicit_single_seed`
- `device_policy: gpu_if_available_else_cpu`
- `device_resolution_rule: use_gpu_when_available_else_fallback_to_cpu`
- `inner_seed: 11`
- `inner_val_fraction: 0.2`
