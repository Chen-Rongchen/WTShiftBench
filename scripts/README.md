# scripts 目录说明

## 1. 当前职责

`scripts/` 是当前 truth-first 主线的 CLI 层。近端入口集中在三类任务：

- `run_stage2_*.py`：Stage 2 truth bridge、covariate audit、model-side recovery adjudication 与 supplementary Dixit 复制。
- `materialize_stage2_*.py`：Stage 2 输入或中间矩阵的物化。
- `convert_rnai_demeter2_to_depmap_endpoints.py`：把 DEMETER2 RNAi 分数转换成现有 truth bridge loader 可读取的 DepMap endpoint 宽表。
- `run_stage2_k562_rnai_endpoint_consistency.py`：汇总 GSE90063 K562 7d/13d 的 CRISPR DepMap 与 DEMETER2 RNAi endpoint consistency。
- `render_manuscript_figure*.py`：论文图生成入口。
- `scripts/manuscript/build_*.py`：当前主文 Fig. 1-Fig. 5 与 Extended Data Fig. 1-Fig. 5 的 panel 级图版生成入口。
- `scripts/manuscript/build_all_main_figures.py`：按 `configs/manuscript/main_figures_v2.json` 顺序重建全部主文图。
- `scripts/manuscript/build_all_extended_data_figures.py`：按 `configs/manuscript/extended_data_figures_v1.json` 顺序重建 Extended Data Fig. 1-10。
- `scripts/manuscript/build_supplementary_table_index.py`：按 `configs/manuscript/supplementary_tables_v1.json` 重建 supplementary table index。
- `scripts/manuscript/build_submission_package.py`：按 `configs/manuscript/submission_package_v1.json` 重建 submission package manifest 与 Supplementary Tables workbook。

当前为了配合 `pixi` 分阶段执行，还补了两条收口专用 CLI：

- `run_stage2_closure_pipeline.py`：按固定顺序串联 `covariates -> sensitivity -> covariate audit`。
- `validate_stage2_closure_artifacts.py`：校验 `claim/tier` 关键 TSV 与边界文档中的固定口径没有漂移。

其中，`materialize_stage2_gse90063_k562_h5ad.py` 用于把 `GSE90063` 的 K562 TF pool（7d/13d）原始矩阵物化为 Stage 2 可直接消费的 `h5ad_obs` 输入。当前 `Dixit/K562` supplementary 默认执行链固定指向 `GSE90063 K562 13d-only`；`run_stage2_dixit_temporal_panel.py` 负责把既有 `13d/7d` 产物汇总为同一外部 context 下的 temporal panel，其中 `13d` 是 primary formal supplementary bridge test，`7d` 是 temporal sensitivity / early-bridge probe。legacy lineage 只允许显式使用 historical-only 配置。

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
- `scripts/pipeline/dixit_axis_compression.py` 与 `scripts/pipeline/dixit_axis_compression.py` 的默认配置固定为 `GSE90063 K562 13d-only`。
- `scripts/pipeline/dixit_temporal_panel.py` 只汇总 `GSE90063 K562 13d/7d` temporal panel，不把 `7d` 升级为 primary closure。
- legacy Dixit replay 只能显式传入 `configs/*legacy_v1.json`，不能依赖脚本默认值。

## 4. 当前推荐的 pixi 入口

优先使用统一入口查看和调度当前注册 workflow：

- `pixi run --environment core wtbench list`
- `pixi run --environment core wtbench run stage2.closure`
- `pixi run --environment core wtbench run stage2.materialize_covariates`
- `pixi run --environment core wtbench run stage2.covariate_audit`
- `pixi run --environment core wtbench run stage2.validate_closure`
- `pixi run --environment core wtbench run stage2.dixit_temporal_panel`
- `pixi run --environment core wtbench run manuscript.figure1`
- `pixi run --environment core python scripts/manuscript/build_all_main_figures.py`
- `pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py`
- `pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py`
- `pixi run --environment core python scripts/manuscript/build_submission_package.py`

统一入口的注册表见 `configs/runtime/wtbench_cli_v1.json`；若需要临时替换配置，优先使用 `--config` 或命令专属环境变量，而不是改脚本默认值。

如果你是按当前 completion roadmap 逐步执行，优先使用：

- `pixi run --environment core run-stage2-closure-pipeline`
- `pixi run --environment core validate-stage2-closure-artifacts`
- `pixi run --environment core build-stage2-truth-bridge-decomposition`
- `pixi run --environment core convert-rnai-demeter2-depmap-endpoints`
- `pixi run --environment core build-stage2-truth-driven-bridge-k562-7d-rnai-demeter2`
- `pixi run --environment core build-stage2-truth-driven-bridge-k562-13d-rnai-demeter2`
- `pixi run --environment core run-stage2-k562-rnai-endpoint-consistency`
- `pixi run --environment core build-stage2-truth-driven-bridge-dixit-supplement`
- `pixi run --environment core run-stage2-dixit-axis-compression`
- `pixi run --environment core run-stage2-dixit-temporal-panel`
- `pixi run --environment core render-manuscript-figure1`

Genome Biology 当前投稿包已经生成，默认不再新增分析执行；若文档、图或补充表发生变化，重跑顺序固定为：

1. `pixi run --environment core python scripts/manuscript/build_all_main_figures.py`
2. `pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py`
3. `pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py`
4. `pixi run --environment core python scripts/manuscript/build_submission_package.py`

若只想单独刷新 HCC sensitivity / covariate 线，也可直接用：

- `pixi run --environment core run-stage2-truth-bridge-sensitivity-hcc-full`
- `pixi run --environment core materialize-stage2-covariates`
- `pixi run --environment core run-stage2-covariate-audit`
