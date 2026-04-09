# scripts 目录说明

## 1. 目录职责

`scripts/` 仍是仓库的主执行层。当前 active framing 已经改为 truth-first：先冻结 truth-side architecture object，再推进 model-side structure adjudication；`Stage 1A / 1B` 仍保留，但其角色已不只是 benchmark leaderboard。

从执行层看，当前最重要的两条链路是：

- `Stage 1A / 1B` benchmark-invariant + adapter 主线
- `Stage 2` truth-driven bridge / truth architecture 主线

其中 `Stage 2` 新增了一个更靠近主文档叙事的 decomposition 入口：

- `scripts/run_stage2_truth_bridge_decomposition.py`

它不替代已有 truth bridge / axis freeze，而是把现有 frozen objects 收束成：

- `target-level joint-priority grid`
- `axis-level shared explanatory structure`

因此这里不再把脚本层单纯描述成“只服务 Stage 1A”。

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
- `run_stage1a_supplement_entrants.py`
- `summarize_stage1a_supplement_entrants.py`
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

`run_stage1a_supplement_entrants.py` / `summarize_stage1a_supplement_entrants.py`
则用于当前 supplement entrant 池的默认单 seed 分析：

- 默认数据集范围固定为 `3 formal + 4 supplement/runnable`
- 默认不包含 `replogle_2022_k562_gwps`
- 汇总输出拆成 dataset-level、entrant-level、dataset leader 三层

## 4. 维护原则

- benchmark-invariant 层不引入模型特定假设
- adapter 层只负责模型原生输入、模型推理、统一输出 `predicted_shift`
- 旧顶层包装不再新增业务逻辑
- truth-side freeze 与 model-side adjudication 的脚本边界应保持清楚
- 不把 supplementary replication 脚本表述成与 HCC primary mainline 并列的主结论入口
