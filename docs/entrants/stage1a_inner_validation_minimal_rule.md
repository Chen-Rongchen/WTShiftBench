# Stage 1A 最简 Inner Validation 规则

## 1. 适用范围

- datasets:
  - `replogle_2022_k562_essential`
  - `replogle_2022_rpe1`
  - `tian_2019_day7neuron`
- 辅助鲁棒性数据集：`tian_2021_crispri`（默认不进入本规则）
- `split_seed: 101`
- entrants:
  - `GEARS`
  - `scGPT`
  - `Geneformer`

## 2. 目标

- 为三个 entrant 增加 train-side inner validation
- inner validation 只用于选择 `epoch/checkpoint`
- `outer_heldout_targets` 绝不参与模型选型

## 3. split 规则

- 保持现有 outer split 不变：
  - `outer_train_targets`
  - `outer_heldout_targets`
- 仅从 `outer_train_targets` 内再切：
  - `inner_train_targets`
  - `inner_val_targets`
- 固定：
  - `inner_seed = 11`
  - `inner_val_fraction = 0.2`
- 必须按 `target-level` 切，不按 `cell-level` 切
- 三个 entrant 共享同一份 inner split manifest

## 4. 训练与选型规则

- 本轮只做“训练终点选择”，不做大规模超参搜索
- 所有 entrant 的外层配置统一使用 `max_epochs`
- `max_epochs` 表示本项目 runtime / adapter 层允许训练的最大 epoch 上限
- 这是 benchmark 外层统一字段，不要求它等于各模型官方原生参数名
- 每个 epoch 都在 `inner_val` 上评估：
  - `pearson_mean`
  - `top50_jaccard_mean`
  - `rmse_mean`
- 选型优先级固定为：
  1. `pearson_mean` 高
  2. 若接近，看 `top50_jaccard_mean` 高
  3. 若仍接近，看 `rmse_mean` 低
- 保存 best checkpoint / best epoch
- 仅用选中的 checkpoint / epoch 在 `outer_heldout_targets` 上做一次正式评估

## 5. 公平性定义

- 同一 inner split
- 同一信息边界
- 同类有限搜索规则
- 不要求相同 wall-clock
- 不要求相同最终 epoch

## 6. entrant 内部映射与当前统一上限

- `GEARS`：外层读取 `max_epochs`，内部映射到官方训练接口 `epochs`
- `scGPT`：当前走 frozen-backbone + adapter head 路线，`max_epochs` 是本项目 adapter trainer 的训练上限
- `Geneformer`：当前走 embedding / adapter 路线，`max_epochs` 是本项目 adapter trainer 的训练上限
- 当前 single-seed Stage 1A 收口版统一采用：`max_epochs = 30`
- 该设置属于工程收口方案，不代表三者原生训练语义完全等价

## 7. 输出物

- `inner_val_epoch_grid.tsv`
- `selected_recipe.json`

## 8. 实现说明

- 当前仓库实现中，inner split manifest 由 outer train targets 派生并固化到 `artifacts/splits/.../inner_seed11/`
- 三个 entrant 都读取同一 outer split 和同一 inner split manifest
- `selected_recipe.json` 记录：
  - outer split seed
  - inner split 参数
  - selection rule
  - selected epoch / checkpoint
  - inner split manifest 路径

## 9. 当前运行入口

先物化共享 split：

```bash
pixi run --environment core python scripts/materialize_stage1a_inner_splits.py \
  --config configs/entrants/stage1a_inner_split_3datasets_seed101.json
```

再运行本轮 `3 datasets × seed101`：

```bash
pixi run --environment core python scripts/run_stage1a_smoke_matrix.py \
  --config configs/entrants/stage1a_smoke_matrix_3datasets_seed101.json
```
