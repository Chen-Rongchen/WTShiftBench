# configs 目录说明

## 1. 目录职责

`configs/` 保存当前仓库的 machine-readable 入口配置。

Stage 1A 现在按职责分成三类：

- 顶层 invariant contract
- `configs/stage1a/adapters/`：模型 adapter 运行配置
- `configs/stage1a/runs/`：benchmark-invariant scoring 运行实例

## 2. 当前关键文件

### invariant contract

- `stage1a_formal_datasets.yaml`（当前只登记 3 个 official formal 数据集）
- `stage1a_prediction_contract.yaml`
- `stage1a_split_governance.yaml`（Stage 1A 方案 B、split seeds、eligibility floor）

### adapter run configs

- `stage1a/adapters/gears_k562_minimal.yaml`
- `stage1a/adapters/scgpt_k562_minimal.yaml`
- `stage1a/adapters/geneformer_k562_minimal.yaml`

### scoring run configs

- `stage1a/runs/prediction_run_config.yaml`
- `stage1a/runs/smoke_case_official.yaml`
- `stage1a/runs/smoke_case_degraded.yaml`
- `stage1a/runs/batch_run_configs.yaml`
- `stage1a/runs/baseline_smoke_zero_shift_null.yaml`
- `stage1a/runs/baseline_smoke_mean_shift_baseline.yaml`
- `stage1a/runs/baseline_smoke_linear_delta_baseline_legacy.yaml`
- `stage1a/runs/baseline_ladder_smoke.batch.yaml`
- `stage1a/runs/batch_scoring_three_models_formal.yaml`（三模型 × 三个主线数据集批量 scoring）
- `stage1a/runs/all_datasets_eval_matrix.json`（三模型 × `3 + 3 + 2` 数据集评测矩阵配置）

## 3. 维护原则

- Stage 1A benchmark-invariant 与旧 adapter 仍以 YAML 为主；entrant **recipe 参数**统一为 `configs/**/*.json`（见下节）
- 跨数据集批量运行的参数矩阵优先写入 `configs/**/*.json`；脚本只负责物化 run-config 与执行
- contract 与 run instance 分开表达
- adapter config 可以包含模型专属字段，但不改变公共 contract 字段语义
- 修改字段语义前先更新文档，再改实现

## 4. entrant recipe configs

- `configs/entrants/registry.yaml`：entrant 注册表（仍为 YAML）
- `configs/entrants/gears/gears_k562_smoke.json`
- `configs/entrants/scgpt/scgpt_k562_smoke.json`
- `configs/entrants/geneformer/geneformer_k562_smoke.json`
- `configs/entrants/stage1a_inner_split_3datasets_seed101.json`
- `configs/entrants/stage1a_smoke_matrix_3datasets_5seeds.json`
- `configs/entrants/stage1a_smoke_matrix_3datasets_seed101.json`

这些配置用于 `scripts/run_stage1a_entrant.py`，只覆盖 adapter recipe 层，不改 benchmark-invariant 公共协议。
