# WTKO

环境管理使用 `pixi`。

## 项目一句话

**WT Benchmark**：用统一、可审计的 black-box 框架评估各 entrant 是否产出可信的 `predicted_shift`。当前最近一批工作的重点是先冻结 `benchmark-invariant layer`，再在冻结边界上推进 `Stage 1A` entrant benchmarking 与解释边界审计。

## 当前真实状态

| 状态 | 内容 |
|---|---|
| 已具备 | `core` / `gears` / `scgpt` / `geneformer` 四套 Pixi 环境 |
| 已具备 | benchmark-invariant 的 contract validation / ingest / alignment 主线 |
| 已具备 | 本地 checkpoint：`models/pretrained/scgpt_human` |
| 已具备 | 本地 checkpoint：`models/pretrained/geneformer_gf_12l_95m_i4096` |
| 已具备 | 三个 smoke yaml、runtime defaults、checkpoint registry |
| 已具备 | 三模型 × 三数据集 × seed101 的 formal adapter / ingest / evaluate 主线配置 |
| 已完成 | `tian_2019_day7neuron` 的 formal filtering 与 formal 统计回填 |
| 已完成 | `Stage 1A` admission manifest 与 formal freeze gating |
| 已完成 | `1 seed × 3 entrants × 3 datasets` 的 formal trial run（预测、对齐、评分、pass skeleton） |
| 暂不进行 | formal multi-dataset × multi-seed adjudication（`3 datasets × 5 seeds`） |

## 当前收口范围

- 当前固定顺序：`harmonized resource layer -> dataset admission layer -> entrant benchmarking layer`
- 正式主线使用 `replogle_2022_k562_essential / replogle_2022_rpe1 / tian_2019_day7neuron`
- 当前数据集治理改为 `3 + 4 + 1`：
  - official formal：`replogle_2022_k562_essential`、`replogle_2022_rpe1`、`tian_2019_day7neuron`
  - next formal-admission batch：`tian_2019_ipsc`、`tian_2021_crispri`、`replogle_2022_k562_gwps`、`dixit_2016_raw`
  - side formal / annex：`norman_2019_raw`
- 在不改变 raw `3 + 4 + 1` 分层的前提下，允许从 raw 数据集中切出更接近主线问题定义的派生 formalization candidates：
  - `norman_2019_raw__single_target`
  - `dixit_2016_raw__control_context`
- next formal-admission batch 只做 admission audit，不提前升格
- `norman_2019_raw` 明确作为 activation / combinatorial side track，不并入 current official formal
- 本轮固定 `split_seed: 101`
- `signal adequacy` 与 `model fidelity` 明确分离：adequacy diagnostics 不替代 `predicted_shift` formal scoring
- `support floor` 具有 admission 语义，至少显式追踪 `cells per perturbation`、`cells per control`、`UMI depth`
- formal 主榜裁决只消费 official formal 的 3 个主线数据集
- 正式评分按 `dataset-local + four-lane + cross-lane summary`
- `common intersection` 仅保留 audit 用途
- 当前 trial run 固定 `model/adaptor seed: 123`，与 formal split seed `101` 分离
- `GEARS` 是当前唯一训练型 entrant；其试运行配置当前为 `epochs=30`、`lr=1e-3`、`weight_decay=1e-6`、`train_val_fraction=0.8`、`device=auto`
- `scGPT / Geneformer` 当前接入方式是 `embedding + cosine kernel regression` adapter，不走训练型 inner validation 主线
- 设备策略统一为 `gpu_if_available_else_cpu`：GPU 可用时默认且优先使用 GPU，只在 CUDA 不可用时回退 CPU

## 当前数据集状态

- `replogle_2022_k562_essential`：已在 formal 主线中
- `replogle_2022_rpe1`：已在 formal 主线中
- `tian_2019_day7neuron`：已完成 formal filtering，admission=`pass`
- `tian_2019_ipsc`：候选 admission batch，重新按 raw source 审计，不写入 formal registry
- `tian_2021_crispri`：候选 admission batch，重新按 raw source 审计，不写入 formal registry
- `replogle_2022_k562_gwps`：候选 admission batch，raw audit 已完成，建议 `admit`
- `dixit_2016_raw`：候选 admission batch，raw audit 已完成，但整包语义不单一，建议 `reject`
- `norman_2019_raw`：annex side track，制度定位成立；raw 文件已复核通过
- `norman_2019_raw__single_target`：派生 candidate，single-target 子集已切出，建议继续送审
- `dixit_2016_raw__control_context`：派生 candidate，`Control + MOI==1` 子集已切出，建议继续送审

其中：

- `tian_2019_day7neuron` 当前 raw 统计为 `182790 x 33752`，formal 统计为 `85290 x 33752`，`n_controls=15580`，`n_perturbed=69710`，`n_unique_targets=26`
- `replogle_2022_rpe1` 当前 formal 统计为 `247914 x 8749`；有 458 行 source `gene_id` 为空，但 formal 主键仍可稳定落在 `target_gene`
- `tian_2019_ipsc` 的受审来源继续使用 Zenodo `TianKampmann2019_iPSC.h5ad`，不采用 pertpy 稳定版源码中的可疑 `iPad` URL
- `tian_2021_crispri` raw audit 已证明 control / single-target / target closure 可以闭合，但当前仍只保留 candidate 身份
- `replogle_2022_k562_gwps` raw audit 已证明 `gene == non-targeting` 可稳定定义 control，按 gene-level target 聚合后有 `9863` 个 perturbations 满足 support floor `>= 5`
- `dixit_2016_raw` 本地 raw audit 证明整包横跨多个 context；即使 `MOI == 1` 下可解析出 `248` 个 support `>= 5` 的 target，也不能把整包直接当成一个 formal 数据集
- `norman_2019_raw` 当前已切回正确 raw 文件：`111445 x 33694`，其中 `guide_ids == ''` 可作为 control-like 空扰动，single-target support floor `>= 5` 后保留 `105` 个 eligible targets
- `norman_2019_raw__single_target` 已落盘 formal-like 子集：`69408` cells、`104` 个 eligible targets；它应作为从 annex raw 派生出的独立 candidate，而不是把原始 Norman 整集升格
- `dixit_2016_raw__control_context` 已落盘 formal-like 子集：`30486` cells、`244` 个 eligible targets；`IFNγ / Co-culture` 子集不进入当前主线

当前 official formal admission 结果：

- `replogle_2022_k562_essential`：`pass`
- `replogle_2022_rpe1`：`pass`
- `tian_2019_day7neuron`：`pass`

当前 formal 主榜仍只由 3 个 mainline `pass` 数据集构成：

- `replogle_2022_k562_essential`
- `replogle_2022_rpe1`
- `tian_2019_day7neuron`

当前数据集选择的唯一准据文件是：

- `dataset_tiering.md`
- `admission_matrix.tsv`
- `short_summary.md`

说明：

- 下文若仍出现旧的 `supplementary / auxiliary / norman_2019` 叙述，应视为历史运行记录，不再代表当前数据集治理口径

## 当前 trial run 状态

本轮已完成 `1 seed × 3 entrants × 3 datasets` 的 formal 试运行：

- entrants：`gears_stage1a_formal`、`scgpt_embedding_kernel_formal`、`geneformer_embedding_kernel_formal`
- datasets：`replogle_2022_k562_essential`、`replogle_2022_rpe1`、`tian_2019_day7neuron`
- split seed：`101`
- model/adaptor seed：`123`

本轮已落地产物：

- 9 份 dataset-level score summary：`reports/stage1a/model_eval/*/*/dataset_score_summary.json`
- 9 份 lane-level summary：`reports/stage1a/model_eval_lanes/*/*/lane_summary.tsv`
- 9 份 aligned predictions：`data/predictions/stage1a_main_aligned/*/*/predicted_shift_aligned.tsv.gz`
- 3 份 entrant-level pass skeleton：
  - `reports/stage1a/model_eval/gears_stage1a_formal/stage1a_pass_skeleton_official_leaderboard.tsv`
  - `reports/stage1a/model_eval/scgpt_embedding_kernel_formal/stage1a_pass_skeleton_official_leaderboard.tsv`
  - `reports/stage1a/model_eval/geneformer_embedding_kernel_formal/stage1a_pass_skeleton_official_leaderboard.tsv`

说明：

- 这次运行是 single-seed trial run，不等同于正式 `3 datasets × 5 seeds` adjudication
- 当前结果可用于 runtime 审计、lane-wise 诊断与解释边界核查，不自动等同于 entrant version 已获得 formal downstream admission

本轮新增解释审计：

- single-seed trial run 总结：`reports/stage1a/trial_run_interpretation_2026-03-30.md`
- `GEARS` prediction space 审计：`reports/stage1a/gears_prediction_space_audit_2026-03-30.md`
- `GEARS × day7neuron` export-space 分层矩阵：
  - `reports/stage1a_audit/gears_export_space/gears_stage1a_formal/tian_2019_day7neuron/predicted_expression_raw.tsv.gz`
  - `reports/stage1a_audit/gears_export_space/gears_stage1a_formal/tian_2019_day7neuron/control_values_full.tsv.gz`
  - `reports/stage1a_audit/gears_export_space/gears_stage1a_formal/tian_2019_day7neuron/predicted_shift_pre_align.tsv.gz`
  - `reports/stage1a_audit/gears_export_space/gears_stage1a_formal/tian_2019_day7neuron/predicted_shift_aligned.tsv.gz`

当前可确认的解释边界：

- `scGPT / Geneformer` 当前 adapter 版本未见明显结构性错误，四条 lane 表现整体稳定
- `GEARS` 当前 version 在 `tian_2019_day7neuron` 上存在明确的 prediction-space instability
- 四条 lanes 在数据层都可稳定产生产物；当前不稳定主要来自 entrant 表现，而不是 lane 机制本身

## 当前 challenger 方向

- 当前只在不改变 `Stage 1A smoke` 制度的前提下，探索是否存在任何 challenger 能在 non-formal `single-seed` 设置下初步接近或超过 `mean_shift_baseline`
- 该探索只用于：
  - 工程接线验证
  - 可运行性验证
  - 初步信号筛查
- 不用于：
  - formal 通过
  - stable superiority
  - entrant ready
- 方法学上允许逐步补齐 `A/B/C` 三层 challenger，但运行上仍坚持“先少后多”
- 若使用线性 / low-rank challenger，必须先明确并冻结 held-out target 的合法 `target-side features` 来源；不能只在 training targets 上分解后，缺失 held-out target 输入表示
- 当前协议已接受一个明确的 exploratory override：
  - 即使尚未出现“一致正向信号”，也允许继续把 `B/C` 以及 `A` 层后续方法做成 exploratory backlog
  - 该 override 只放宽“是否继续实现/运行”的门槛，不放宽 formal 解释边界
- 因此后续新增 challenger 仍不得被写成：
  - formal 通过
  - stable superiority
  - entrant ready
  - 可直接触发 `3 datasets × 5 seeds` adjudication

当前 exploratory backlog 已全部跑完，当前结果收口如下：

- `lm_train_lowrank`：初步正向信号
- `lm_G_scgpt_ridge`：mixed signal
- `lm_G_geneformer_ridge`：close-or-worse
- `residual_over_mean__lm_train_lowrank`：当前实现下与 `lm_train_lowrank` 等价，不应单独计作独立正向证据
- `fixed_late_fusion_v1`：exploratory override 下的 mixed signal
- `elasticnet_targetfeat`：exploratory override 下的 mixed signal
- `knn_kernel_targetfeat`：exploratory override 下的初步正向信号
- `rf_targetfeat_lowrank`：exploratory override 下的 mixed signal

当前最值得关注的补充结论：

- `residual_over_mean__lm_train_lowrank` 当前在主线与 supplementary 上都与 `lm_train_lowrank` 产出完全相同的 aligned prediction；现阶段更应视为实现等价，而不是独立 challenger
- `knn_kernel_targetfeat` 是当前 `B` 层里最干净的一条：`K562 / RPE1` 达到 `ran_and_better_than_mean`，`day7neuron` 维持 `ran_and_close_to_mean`
- `elasticnet_targetfeat` 与 `rf_targetfeat_lowrank` 都在 `day7neuron` 上明显劣于 `mean_shift_baseline`
- `fixed_late_fusion_v1` 在 `K562 / RPE1` 有效，但 `day7neuron` 明显变差

历史 exploratory benchmarking 曾覆盖以下 3 个非 official formal 数据集：

- `tian_2019_ipsc`
- `tian_2021_crispri`
- `norman_2019_raw` 的前序 processed 口径

这些历史 exploratory 结果当前只作背景记录，不代表现行 formal 分层：

- `lm_train_lowrank`：在 `tian_2019_ipsc / tian_2021_crispri` 上都劣于 `mean_shift_baseline`
- `residual_over_mean__lm_train_lowrank`：与 `lm_train_lowrank` 完全等价，因此在 `tian_2019_ipsc / tian_2021_crispri` 上同样都劣于 `mean_shift_baseline`
- Norman side track 的历史结果显示 split realization 敏感，因此它应留在 annex 轨道解释，而不是并入 official formal
- `knn_kernel_targetfeat`：coverage-blocked
- `lm_G_scgpt_ridge`：coverage-blocked
- `lm_G_geneformer_ridge`：coverage-blocked
- `elasticnet_targetfeat`：coverage-blocked
- `rf_targetfeat_lowrank`：coverage-blocked
- `fixed_late_fusion_v1`：依赖项 blocked，无法构建

当前 next formal-admission batch 上的 frozen feature coverage 边界：

- `tian_2019_ipsc`：`scGPT / Geneformer` heldout coverage 都是 `0.8333`，共同缺 `ATP5B`
- `tian_2021_crispri`：`scGPT / Geneformer` heldout coverage 都是 `0.9487`，共同缺 `ATP5C1`、`TMEM55A`
- 当前 frozen floor=`0.95`，因此相关 challenger 应正式记为 `coverage-blocked`

因此当前仓库的正式口径应当是：

- challenger exploratory backlog 已补齐
- next formal-admission batch 的 exploratory 记录已覆盖 `tian_2019_ipsc / tian_2021_crispri`
- `norman_2019_raw` 当前更适合标记为 annex side track：raw audit 已闭合，但 benchmark 解释对 split realization 与 combinatorial 结构敏感
- 当前没有任何新增结果足以直接触发 formal `3 datasets × 5 seeds` adjudication
- 下一步优先做结果审计、等价方法去重与 coverage policy 说明，而不是继续扩 challenger 方法池

## 当前 normalize 审计状态

- 本轮对三条 frozen-feature challenger 的 `input-side normalize audit` 结论保持不变：`lm_train_lowrank`、`lm_G_scgpt_ridge`、`lm_G_geneformer_ridge` 仍记为 `not_applicable`。
- 原因不变：这些方法一旦在 train delta 构造中插入 `normalize+log1p`，监督目标就会从 `v1 formal A-space` 改到变换空间。

当前 challenger 的执行补充约束：

- 任何 challenger 在实现前都必须先落地并冻结两张 registry：
  - `feature registry`
  - `challenger registry`
- `feature registry` 是唯一允许被 challenger 引用的 feature 清单；脚本中不应各自硬编码 feature 路径
- `feature registry` 至少包含：
  - `feature_id`
  - `feature_family`
  - `source_path`
  - `entity_type`
  - `coverage_on_current_smoke`
  - `missing_policy`
  - `is_frozen`
  - `notes`
- `challenger registry` 是唯一允许被执行主线引用的 challenger 清单
- `challenger registry` 至少包含：
  - `challenger_id`
  - `method_family`
  - `feature_dependencies`
  - `train_inputs`
  - `output_contract`
  - `status`
  - `current_scope`
  - `unlock_prerequisite`
  - `notes`
- 所有 challenger 复用当前 single-seed smoke 的 dataset、split seed、frozen truth、aligned evaluable genes 与 scoring contract
- 所有 challenger 都应产出统一 `predicted_shift.tsv.gz`，再进入现有 ingest / evaluate / render 主线
- 结果记录至少区分：
  - `ran_and_better_than_mean`
  - `ran_and_close_to_mean`
  - `ran_and_worse_than_mean`
  - `failed_runtime`
  - `unavailable`
- `接近 mean` 的工作阈值需要在运行前冻结
- challenger 的 `implemented`、`wired_to_eval`、`executed_on_smoke`、`eligible_for_next_step` 需要分开记录

以下内容只保留作 formal 解释边界记录，不是当前执行清单。

formal 解释边界下的推荐解锁顺序：

1. 先冻结 `feature registry`
2. 再冻结 `challenger registry`
3. 只先实现并运行 `lm_train_lowrank`
4. 只有出现正向信号时，再运行 `lm_G_scgpt_ridge` 与 `lm_G_geneformer_ridge`
5. 只有前述步骤已有正向信号时，再运行 `residual_over_mean__lm_train_lowrank`
6. 只有至少两个 challenger 显示互补或近似正向时，再运行 `fixed_late_fusion_v1`
7. `elasticnet_targetfeat`、`knn_kernel_targetfeat`、`rf_targetfeat_lowrank` 放在最后

当前在 exploratory override 下的执行口径：

1. `A` 层仍优先，且其结果优先用于方法学判断
2. 即使 `A` 层没有形成一致正向信号，仍允许继续实现并运行后续 backlog
3. 这些结果一律只记为 exploratory backlog，不作为 formal 解锁依据
4. 因此“是否继续做”与“是否足以支持 formal 下一步”需要明确分开
5. 当前 backlog 已执行完成；registry 中保留 `unlock_prerequisite` 仅作为 formal 解释边界，不再作为“是否允许实现”的工程门槛

当前 challenger 方法池：

- `A` 层：embedding + linear model 家族
  - `lm_train_lowrank`
  - `lm_G_scgpt_ridge`
  - `lm_G_geneformer_ridge`
  - `residual_over_mean__lm_train_lowrank`
- `B` 层：传统 ML 家族
  - `elasticnet_targetfeat`
  - `knn_kernel_targetfeat`
  - `rf_targetfeat_lowrank`
- `C` 层：组合方法家族
  - `fixed_late_fusion_v1`

当前默认方法学定义：

- `lm_train_lowrank`：`target features -> low-rank shift factors -> full predicted_shift`
- `lm_G_scgpt_ridge`：使用 `scGPT` gene embedding 作为 target representation 的 ridge challenger
- `lm_G_geneformer_ridge`：使用 `Geneformer` gene embedding 作为 target representation 的 ridge challenger
- `residual_over_mean__lm_train_lowrank`：先固定 `mean_shift_baseline`，再仅学习 residual
- `elasticnet_targetfeat`：稀疏线性 exploratory challenger
- `knn_kernel_targetfeat`：非参数 geometry exploratory challenger
- `rf_targetfeat_lowrank`：非线性 low-rank exploratory challenger
- `fixed_late_fusion_v1`：固定权重、预注册成员的 late-fusion challenger

当前 `正向信号` 的工作定义：

- 只用于决定是否进入下一步 challenger，不构成 formal superiority 结论
- 在 exploratory override 生效后，`正向信号` 也不再是“是否允许继续实现后续 backlog”的必要条件
- 但它仍然是“是否值得把后续结果上升为更强方法学主张”的唯一工作门槛
- 满足以下任一条，可记为出现初步正向信号：
  1. 至少一个主指标明确优于 `mean_shift_baseline`，且无灾难性退化指标
  2. 多个主指标整体接近 `mean_shift_baseline`，同时不存在明显退化
  3. 方法可稳定跑通，且参数网格呈现可解释的改善趋势，并且整体表现未明显劣于 `mean_shift_baseline`
- `稳定跑通` 是必要条件，不是充分条件
- `lm_train_lowrank` 当前最小参数网格固定为：
  - `K ∈ {16, 32, 64}`
  - `alpha ∈ {0.1, 1.0, 10.0}`

## 关键文件

- 蓝图：`docs/protocol_blueprint.md`
- 当前计划：`plan.md`
- admission manifest：`reports/stage1a/admission/stage1a_admission_manifest.tsv`
- formal freeze manifest：`reports/stage1a/freeze/freeze_manifest.json`
- smoke 卡片与 runtime spec：`docs/entrants/`
- smoke 配置：`configs/entrants/*.yaml`
- checkpoint registry：`configs/entrants/checkpoint_registry.yaml`
- entrant 代码：`src/wtbench/entrants/`
- smoke 脚本：`scripts/smoke_stage1a_*.py`

## 推荐命令

先检查环境：

```bash
pixi run check-envs
```

GEARS smoke：

```bash
pixi run --environment gears python scripts/smoke_stage1a_gears.py
```

GEARS formal adapter：

```bash
python scripts/stage1a/adapters/gears/launch_build_predictions.py --run-config <path/to/run-config.yaml>
```

scGPT smoke：

```bash
pixi run --environment scgpt python scripts/smoke_stage1a_scgpt.py
```

Geneformer smoke：

```bash
pixi run --environment geneformer python scripts/smoke_stage1a_geneformer.py
```

三模型 × 三数据集 × 五个 seeds 的 smoke matrix：

```bash
python scripts/run_stage1a_smoke_matrix.py
```

## 输出边界

- smoke 运行只证明 entrant identity、runtime spec、split governance、`predicted_shift` export 与 benchmark hooks 已接通
- smoke 结果不构成 formal Stage 1A adjudication 结论
- 正式记录以 `lane-wise outputs + cross-lane summary` 为中心，而不是单一 leaderboard
- `E-test` / `E-distance` 等 adequacy diagnostics 只用于资源层 / admission 层诊断，不替代 formal predicted-shift scoring
- 当前 `linear_delta_baseline` 的仓库实现仅保留 `legacy` 版本，不作为 canonical linear baseline formal 结论依据
- `scripts/run_stage1a_smoke_matrix.py` 当前用于 entrant smoke / inner-validation 批量回归，不等同于 formal `3 datasets × 5 seeds` adjudication 主线

## 数据集来源校验

- 当前主线 / 辅助位统一以 `pertpy.data.*` loader 名为准：
  - `pertpy.data.replogle_2022_rpe1()`
  - `pertpy.data.replogle_2022_k562_essential()`
  - `pertpy.data.tian_2019_day7neuron()`
  - `pertpy.data.tian_2021_crispri()`
- 该口径已按 pertpy 官方 datasets 文档与 `_datasets` 源码页核对；仓库配置中的 loader 名、文件名与下载 URL 应与官方实现一致
- `scPerturb` 或其他 dataset hub 只作为候选资源入口与预审计输入，不等同于本项目 formal benchmark protocol

## 下一步

按当前优先级：

1. 审查 challenger 的 `vs_mean` 汇总，形成一份正式的 exploratory / supplementary 审计结论
2. 在 registry 与文档中明确：`residual_over_mean__lm_train_lowrank` 当前与 `lm_train_lowrank` 等价，不再单独计数
3. 固化 supplementary 上的 `coverage-blocked` 口径，避免把 blocked 误写成“结果差”
4. 把 normalize 审计关闭结论保持为最终状态，不再在这三条 challenger 上继续消耗时间
5. 固化 `GEARS` current version 的 `under audit` 结论，不再把它描述成“暂时无问题”
6. 确认 `scGPT / Geneformer` 当前 adapter 的 taxonomy 与可声明范围
7. 整理四条 lanes 的稳定性结论，明确“lane 稳定”与“entrant 表现稳定”是两回事
8. 是否推进 formal `3 datasets × 5 seeds` adjudication 仍需单独判断
9. 是否需要调整 frozen feature coverage policy，需单独立项，不在当前文档里默认放宽

## 新窗口直接接手

新开一个窗口后，先做这三步：

1. 先读 `plan.md` 的“你接下来先做什么”
2. 再读 `README.md` 的“当前 challenger 方向”“当前 normalize 审计状态”“下一步”
3. 然后只做文档与审计收口，不再新增 challenger、不开 normalize 新实验

当前建议的直接执行顺序：

```bash
sed -n '/## 当前 challenger 方向/,/## 当前 normalize 审计状态/p' README.md
sed -n '/## 当前 normalize 审计状态/,/## 当前 challenger 的执行补充约束/p' README.md
sed -n '/## 你接下来先做什么/,/## 本轮验收口径/p' plan.md
```

接手时应保持以下结论不变：

- `residual_over_mean__lm_train_lowrank` 当前与 `lm_train_lowrank` 等价
- `tian_2019_ipsc / tian_2021_crispri` 当前属于 next formal-admission batch，不能误写成 official formal 或 supplementary 制度结论
- 输入侧 normalize 审计已关闭，且 `lm_train_lowrank / lm_G_scgpt_ridge / lm_G_geneformer_ridge` 都是 `not_applicable`

## Registry 层状态（已弃用）

`configs/entrants/registry.yaml` 与 `src/wtbench/entrants/registry.py` 已被**显式弃用**。

原因：
- `registry.yaml` 中 `adapter_class` 与实际类名不一致（`GEARSEntrantAdapter` → `GEARSEntrant` 等）
- `registry.yaml` 中 `default_config_path` 指向不存在的文件
- `registry.py` 曾引用 `base.py` 中不存在的 `DEFAULT_ENTRANT_REGISTRY_PATH`
- `scripts/run_stage1a_entrant.py` 引用了 `base.py` 中不存在的函数（`build_output_paths` 等）

**当前支持的入口**：使用 `scripts/smoke_stage1a_*.py` 直连 entrant class，不依赖 registry 层。
