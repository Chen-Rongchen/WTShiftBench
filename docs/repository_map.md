# 仓库目录说明

## 1. 设计原则

当前仓库仍以“先把 `Stage 1A` 主线跑稳”为第一优先级，但 Stage 1A 代码边界已经显式分层：

- `benchmark-invariant`
- `model-specific adapter`

这次分层只覆盖 Stage 1A，不向 Stage 1B/2/3 扩散。

## 2. 顶层目录职责

- `README.md`：当前仓库现状与分层入口
- `plan.md`：当前可执行计划
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

如果你要理解主链路，建议按下面顺序看：

1. `configs/`
2. `scripts/stage1a/`
3. `data/`
4. `reports/`

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

本次重构不主动搬动这两部分目录。

## 6. 当前优化结论

仓库仍保持“脚本驱动 + YAML 入口 + 文档收束”的风格，但 Stage 1A 不再是一个平铺脚本集合，而是已经显式表达为：

```text
formal source shared
-> model-native adapter
-> predicted_shift contract
-> benchmark-invariant scoring
```
