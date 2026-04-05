# scripts 目录说明

## 1. 目录职责

`scripts/` 仍是仓库的主执行层，但 Stage 1A 现在已经显式拆成两层。

## 2. Stage 1A 分层

### benchmark-invariant

主目录：`scripts/stage1a/benchmark_invariant/`

- `formal/`：formal source 相关冻结入口
- `truth_space/`：truth、evaluation space、baseline/null 主线
- `scoring/`：`predicted_shift -> ingest -> evaluate -> render`
- `catalog.py`
- `prediction_eval_common.py`

### model-specific adapters

主目录：`scripts/stage1a/adapters/`

- `common/runtime.py`：极小共享 helper
- `gears/`
- `scgpt/`
- `geneformer/`

## 3. 顶层旧脚本

以下顶层脚本仍保留，但现在主要是兼容包装：

- `run_stage1a_formal_freeze_mainline.py`
- `run_stage1a_truth_to_render_mainline.py`
- `run_stage1a_batch_truth_to_render_mainline.py`
- `build_stage1a_all_datasets_eval_matrix.py`
- `build_stage1a_all_datasets_readiness_assets.py`
- `run_stage1a_all_datasets_pipeline.py`
- `summarize_stage1a_all_datasets_vs_baseline.py`
- `ingest_stage1a_model_predictions.py`
- `evaluate_stage1a_predictions.py`
- `render_stage1a_pass_skeleton.py`
- `validate_stage1a_prediction_contract.py`
- `build_stage1a_*_k562_predictions.py`
- `run_stage1a_smoke_matrix.py`

新的首选入口应优先使用 `scripts.stage1a.*` 包路径或 `pixi.toml` 中对应的新 task。

其中 `run_stage1a_smoke_matrix.py` 用于批量驱动 entrant smoke / inner-validation 回归；
它读取 `configs/entrants/stage1a_smoke_matrix_3datasets_5seeds.json`，生成临时 smoke 配置并顺序执行，不直接替代 formal truth/scoring 主线。

`build_stage1a_all_datasets_readiness_assets.py` / `build_stage1a_all_datasets_eval_matrix.py` / `run_stage1a_all_datasets_pipeline.py` / `summarize_stage1a_all_datasets_vs_baseline.py`
则用于当前的 `3 + 3 + 2` 数据集评测矩阵：

- 先补 candidate readiness 资产
- 再做 readiness 审计
- 再按环境批量驱动三模型
- 最后统一汇总 `vs_mean_shift_baseline`

## 4. 维护原则

- benchmark-invariant 层不引入模型特定假设
- adapter 层只负责模型原生输入、模型推理、统一输出 `predicted_shift`
- 旧顶层包装不再新增业务逻辑
