# scripts 目录说明

## 1. 当前职责

`scripts/` 是当前 truth-first 主线的 CLI 层。近端入口集中在三类任务：

- `run_stage2_*.py`：Stage 2 truth bridge、covariate audit、model-side recovery adjudication 与 supplementary Dixit 复制。
- `materialize_stage2_*.py`：Stage 2 输入或中间矩阵的物化。
- `render_manuscript_figure*.py`：论文图生成入口。

当前为了配合 `pixi` 分阶段执行，还补了两条收口专用 CLI：

- `run_stage2_closure_pipeline.py`：按固定顺序串联 `covariates -> sensitivity -> covariate audit`。
- `validate_stage2_closure_artifacts.py`：校验 `claim/tier` 关键 TSV 与边界文档中的固定口径没有漂移。

其中，`materialize_stage2_gse90063_k562_h5ad.py` 用于把 `GSE90063` 的 K562 TF pool（7d/13d）原始矩阵物化为 Stage 2 可直接消费的 `h5ad_obs` 输入。当前 `Dixit/K562` supplementary 默认执行链固定指向 `GSE90063 K562 13d-only`；`7d` 仅保留为 temporal exploration，legacy lineage 只允许显式使用 historical-only 配置。

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
- `scripts/stage2_dixit_axis_compression.py` 与 `scripts/run_stage2_dixit_axis_compression.py` 的默认配置固定为 `GSE90063 K562 13d-only`。
- legacy Dixit replay 只能显式传入 `configs/stage2/*legacy_v1.json`，不能依赖脚本默认值。

## 4. 当前推荐的 pixi 入口

如果你是按当前 completion roadmap 逐步执行，优先使用：

- `pixi run --environment core run-stage2-closure-pipeline`
- `pixi run --environment core validate-stage2-closure-artifacts`
- `pixi run --environment core build-stage2-truth-bridge-decomposition`
- `pixi run --environment core build-stage2-truth-driven-bridge-dixit-supplement`
- `pixi run --environment core run-stage2-dixit-axis-compression`
- `pixi run --environment core render-manuscript-figure1`

若只想单独刷新 HCC sensitivity / covariate 线，也可直接用：

- `pixi run --environment core run-stage2-truth-bridge-sensitivity-hcc-full`
- `pixi run --environment core materialize-stage2-covariates`
- `pixi run --environment core run-stage2-covariate-audit`
