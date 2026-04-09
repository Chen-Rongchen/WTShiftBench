# configs 目录说明

## 1. 目录职责

`configs/` 保存当前仓库的 machine-readable 入口配置。

当前 active framing 已经改为 truth-first，但配置层仍保留原有 `Stage 1A / 1B / 2 / 3` 编号。就当前近端执行而言，`configs/` 主要承载两类入口：

- `Stage 1A / 1B` 的 benchmark-invariant 与 adapter 运行配置
- `Stage 2` truth-driven bridge 与 truth-side architecture 相关配置

其中当前最近一步不再是继续扩写 leaderboard，而是从 frozen truth architecture 出发推进 model-side adjudication。

除 model-side adjudication 外，`configs/stage2/*.json` 也开始承载 frozen axis 的 annotation / validation 配置骨架；这类配置只定义 machine-readable 字段与治理边界，不等于 axis discovery 已由 enrichment 取代。

Stage 1A 相关配置目前按职责分成三类：

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
- `stage1a/runs/supplement_entrants_single_seed_analysis.json`（6 个 supplement entrants 的默认 `7 datasets × seed101` 分析范围）

## 3. 维护原则

- Stage 1A benchmark-invariant 与旧 adapter 仍以 YAML 为主；entrant **recipe 参数**统一为 `configs/**/*.json`（见下节）
- 跨数据集批量运行的参数矩阵优先写入 `configs/**/*.json`；脚本只负责物化 run-config 与执行
- contract 与 run instance 分开表达
- adapter config 可以包含模型专属字段，但不改变公共 contract 字段语义
- 修改字段语义前先更新文档，再改实现
- 不把 supplementary dataset role 写成 primary mainline
- 不把 discovery 提前写成当前配置层的 primary deliverable
- 不把 `GSEA / enrichment` 单独写成 axis discovery 的主证据；若出现 axis analysis 配置，默认只服务于 annotation 与 validation

## 5. Stage 2 truth-first configs

- `stage2/truth_driven_bridge_hcc38_hcc1143_v1.json`：HCC 主线 truth-driven bridge 配置
- `stage2/truth_bridge_sensitivity_v1.json`：truth bridge 敏感性分析配置
- `stage2/truth_bridge_decomposition_v1.json`：truth–DepMap bridge 两层分解配置；第一层输出 target-level joint grid，第二层输出 axis-level shared explanatory summary
- `stage2/hcc_prediction_contract_v1.json`：真实 HCC 预测 contract
- `stage2/gears_hcc_formal_v1.json`：GEARS HCC formal recipe
- `stage2/gears_backbone_diagnostic_v1.json`：GEARS backbone 诊断配置
- `stage2/gears_hcc_backbone_sweep_v1.json`：GEARS 有限 sweep 配置
- `stage2/axis_analysis_template_v1.json`：功能轴 annotation / validation 的 machine-readable 配置骨架
- `stage2/axis_enrichment_template_v1.json`：功能轴 enrichment 的最小配置骨架（依赖本地 GMT）
- `stage2/axis_target_consistency_template_v1.json`：功能轴 per-target consistency audit 的最小配置骨架（要求真实 per_target_signature 输入）
- `stage2/per_target_signature_materialization_v1.json`：从 frozen HCC truth 输入物化 `per_target_signature` 的配置
- `stage2/axis_validation_summary_v1.json`：汇总 enrichment 与 consistency 结果的保守 summary 配置
- `stage2/per_target_signature_materialization_v1.json`：从真实 HCC truth 输入物化 per_target_signature 的配置

## 4. entrant recipe configs

- `configs/entrants/registry.yaml`：已弃用的历史 registry 样稿，不是当前有效入口
- `configs/entrants/gears/gears_k562_smoke.json`
- `configs/entrants/scgpt/scgpt_k562_smoke.json`
- `configs/entrants/geneformer/geneformer_k562_smoke.json`
- `configs/entrants/stage1a_inner_split_3datasets_seed101.json`
- `configs/entrants/stage1a_smoke_matrix_3datasets_5seeds.json`
- `configs/entrants/stage1a_smoke_matrix_3datasets_seed101.json`

当前有效入口是各 `configs/entrants/**/*.json` recipe 文件。

`configs/entrants/registry.yaml` 仅保留为历史样稿：

- 已在文件头显式标记 `deprecated: true`
- 不应再被表述为当前 smoke 或 supplement 编排入口
- 若未来恢复 registry-driven orchestration，应重建设计，而不是继续复用该文件
