# scripts 目录说明

## 1. 当前职责

`scripts/` 是当前 truth-first 主线的 CLI 层。近端入口集中在三类任务：

- `run_stage2_*.py`：Stage 2 truth bridge、covariate audit、model-side recovery adjudication 与 supplementary Dixit 复制。
- `materialize_stage2_*.py`：Stage 2 输入或中间矩阵的物化。
- `render_manuscript_figure*.py`：论文图生成入口。

旧 Stage 1A smoke / freeze / scoring 顶层 CLI 已清理。`scripts/stage1a/` 只保留 Stage 2 仍直接复用的轻量 helper，不再作为独立主流程入口维护。

## 2. 保留的 Stage 1A helper 边界

当前仍保留：

- `scripts/stage1a/adapters/common/runtime.py`
- `scripts/stage1a/adapters/gears/build_predictions.py`
- `scripts/stage1a/adapters/scgpt/build_predictions.py`
- `scripts/stage1a/adapters/geneformer/build_predictions.py`
- `scripts/stage1a/benchmark_invariant/catalog.py`
- `scripts/stage1a/benchmark_invariant/prediction_eval_common.py`
- `scripts/stage1a/challengers/common.py`

保留原因是 Stage 2 的 GEARS / scGPT / Geneformer / linear control 入口仍复用其中的 adapter、矩阵写出和 feature registry helper。后续若继续瘦身，应优先把这些 helper 迁到 `src/wtbench/` 或 `scripts/stage2_*` 专属模块，再删除 `scripts/stage1a/` 壳层。

## 3. 维护原则

- CLI 入口放在 `scripts/`。
- recipe、运行实例和可调参数放在 `configs/**/*.json`；脚本只加载配置并执行。
- 不再新增 Stage 1A 顶层兼容包装。
- supplementary replication 脚本不能被写成与 HCC primary mainline 并列的主结论入口。
