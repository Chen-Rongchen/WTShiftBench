# WT Benchmark 当前计划

## 文档定位

本文件只写当前最近一批、可以立刻开始编码执行的工作。

- 长期制度看 `docs/protocol_blueprint.md`
- 当前真实可运行事实看 `README.md`

## 本轮目标

推进 `Stage 1A` 的 `3 datasets × split_seed 101` 收口，实现与蓝图一致的 formal scoring 与 entrant 训练边界。

本轮不做：

- 不新增任何预训练数据集
- 不改 formal Stage 1A 数据池
- 不展开 formal `3 datasets × 5 seeds`
- 不输出正式 benchmark 结论
- 不改 `protocol_blueprint.md`

## 当前执行批次

### 1. checkpoint registry 冻结

- 建立 `configs/entrants/checkpoint_registry.yaml`
- 优先解析本地 `scgpt_human` 与 `geneformer_gf_12l_95m_i4096`
- 若无法解析则保留 `to_be_confirmed`，但不阻断其余骨架

### 2. entrant identity 与 runtime spec 文档冻结

- 三张 entrant card
- 三份 smoke 级 runtime spec
- 一份 readiness summary

### 3. 统一接口与 export 主线

- `BaseEntrant`
- `checkpoints.py`
- `export.py`
- target-level split manifest 生成与落盘

### 4. 当前实现重点

1. 正式 scoring 按 `dataset-local + four-lane + cross-lane summary` 收口
2. canonical baseline/null family 先冻结到当前已实现且语义清晰的集合
3. 三个 entrant 的 train-side 终点选择统一使用 target-level inner validation
4. smoke 入口继续保留，作为 entrant 接线与最小回归入口
5. 三个 entrant 的外层训练上限字段统一使用 `max_epochs`，当前 single-seed 收口版固定为 `30`

## 本轮验收口径

- 三个 entrant 在 `split_seed 101` 下都使用统一的 outer split 与 inner split
- inner split 必须是 target-level，固定 `inner_seed=11`、`inner_val_fraction=0.2`
- outer heldout 仅用于最终正式评估，不参与 epoch / checkpoint 选型
- README / plan / runtime spec 对 `max_epochs` 的命名约定一致
- 正式结果包含 lane-wise outputs 与 cross-lane summary
- baseline legacy 命名与 formal comparator 语义不再混淆
