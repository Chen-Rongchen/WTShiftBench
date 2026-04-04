# WT Benchmark 当前计划

## 文档定位

本文件只写当前最近一批、可以直接开始执行的工作，不写长期制度展开。

- 长期制度看 `docs/protocol_blueprint.md`
- 当前真实状态看 `README.md`

## 当前主任务

先冻结 `benchmark-invariant layer`，再在冻结边界上推进 entrant benchmarking 与版本解释审计。

当前固定顺序：

1. `harmonized resource layer`
2. `dataset admission layer`
3. `entrant benchmarking layer`

## 本轮目标

把 `Stage 1A` 的数据集治理收紧到 `3 + 4 + 1`，并在不改变 official formal 主线的前提下，尽可能把候选数据集补齐到接近 formal admission 的标准。

## 本轮不做

- 不新增 formal 主线数据池
- 不直接展开 `3 datasets × 5 seeds` formal adjudication
- 不在 admission 未闭合的数据集上产出 formal entrant 结论
- 不把 next formal-admission batch 或 annex side track 预写成 `auxiliary_pass` 或其他变相升格状态
- 不把 adequacy 诊断指标替代 `predicted_shift` formal scoring
- 不把“single-seed smoke 可运行”直接写成“formal superiority”或“entrant ready”

## 当前执行批次

### 1. harmonized resource layer 已收口

- 固化 `Stage 1A` 数据资源登记、来源、下载口径与 provenance
- 明确 raw / processed level 边界
- 保持 formal dataset registry、raw audit 产物、admission manifest 与 README 叙述一致

### 2. dataset admission layer 已收口

- 把 `signal adequacy` 与 `model fidelity` 分开
- 把 `support floor` 明确为 admission 规则，而不是事后调分规则
- admission 至少显式追踪：
  - `cells per perturbation`
  - `cells per control`
  - `UMI depth`
- 前置审计并记录：
  - `single-target vs multi-target`
  - `MOI`
  - `control definition`
  - `barcode assignment reliability`
  - `processed/raw level`
  - `target mapping closure`
- 统一产出 `reports/stage1a/admission/stage1a_admission_manifest.tsv`
- 让 formal freeze 仅消费 `admission_decision=pass` 的主线数据集

### 3. single-seed entrant trial run 已完成

- 已完成 `1 seed × 3 entrants × 3 datasets` 的 formal trial run
- entrants：`GEARS`、`scGPT embedding-kernel`、`Geneformer embedding-kernel`
- datasets：`replogle_2022_k562_essential`、`replogle_2022_rpe1`、`tian_2019_day7neuron`
- `split_seed=101`
- `model/adaptor seed=123`
- 已落地 aligned prediction、lane summary、dataset score summary 与 entrant-level pass skeleton
- 已落地 single-seed trial run 解释审计报告
- 已落地 `GEARS × day7neuron` prediction-space / export-space 审计矩阵
### 4. 当前数据集分层与 admission 目标

#### `tian_2019_day7neuron`

- 已完成 raw audit
- 已完成 formal filtering
- formal 统计已回填：`85290 x 33752`，`n_controls=15580`，`n_perturbed=69710`，`n_unique_targets=26`
- 已在 admission manifest 中标记为 `pass`

#### official formal（保持不变）

- `replogle_2022_k562_essential`
- `replogle_2022_rpe1`
- `tian_2019_day7neuron`
- 这 3 个数据集继续作为 formal 主锚点，不因新候选加入而重写既有结论

#### next formal-admission batch（逐个 admission audit，不提前升格）

- `tian_2019_ipsc`
- `tian_2021_crispri`
- `replogle_2022_k562_gwps`
- `dixit_2016_raw`
- 对每个数据集统一回答：
  - perturbation identity 是否清晰
  - control 语义是否清晰
  - 是否能限制到 single-guide / single-target 主线
  - support floor `>=5` 后还剩多少 eligible perturbations
  - 是否能构建 perturbation-level pseudobulk delta truth
  - 是否适合进入 official formal

#### side formal / annex

- `norman_2019_raw`
- 明确作为 activation / combinatorial side track
- 单独审计其 annex 价值，不并入 current official formal

#### 派生 formalization candidates

- `norman_2019_raw__single_target`
- `dixit_2016_raw__control_context`
- 原则：
  - 派生 candidate 只表示“从 raw 数据中切出了更接近 current single-target formal 主线的问题定义”
  - 不等于把原始 raw 数据集整体升格
  - 原始 `norman_2019_raw` 继续保留 annex 定位
  - 原始 `dixit_2016_raw` 整包继续保持 `reject`

### 5. 当前 entrant benchmarking 边界
- 当前 trial run 已满足 entrant benchmarking 的运行闭环，但还不等同于 entrant version-level formal adjudication
- 进入正式多 seed adjudication 前，仍需先完成：
  - 固化 `GEARS` current version 的 `under audit` explanation boundary
  - `scGPT / Geneformer` adapter taxonomy 的声明边界确认
  - 单 seed 结果的 lane-wise 解释与异常排查

### 6. 当前 challenger 探索边界

- 当前只允许在不改变 `Stage 1A smoke` 制度的前提下，检查是否存在任何 challenger 能在 non-formal `single-seed` 设置下初步接近或超过 `mean_shift_baseline`
- 本轮 challenger 结果仅用于：
  - 工程接线验证
  - 可运行性验证
  - 初步信号筛查
- 本轮不输出：
  - formal 通过
  - stable superiority
  - entrant ready
- 方法学路线允许按 `A/B/C` 三层逐步补齐，但当前这一轮 exploratory backlog 已经全部补齐
- held-out target 的合法 `target-side feature` 来源已经冻结；后续不再需要为 challenger 补基础接线
- 不接受仅基于训练 targets 的低秩分解、但无法为 held-out targets 提供输入表示的 challenger 定义
- 当前协议新增一个明确的 exploratory override：
  - 即使尚未出现“一致正向信号”，也允许继续把 `A` 层后续、`B` 层、`C` 层做成 exploratory backlog
  - 该 override 只影响“是否继续实现/运行”
  - 不影响 formal 解释边界，也不自动解锁 adjudication 或 entrant ready 叙述

当前 exploratory challenger 已执行完成，结果收口如下：

- `lm_train_lowrank`：正向信号
- `lm_G_scgpt_ridge`：mixed signal
- `lm_G_geneformer_ridge`：close-or-worse
- `residual_over_mean__lm_train_lowrank`：当前实现下与 `lm_train_lowrank` 等价
- `fixed_late_fusion_v1`：exploratory override 下的 mixed signal
- `elasticnet_targetfeat`：exploratory override 下的 mixed signal
- `knn_kernel_targetfeat`：exploratory override 下的正向信号
- `rf_targetfeat_lowrank`：exploratory override 下的 mixed signal

当前结论边界：

- `lm_train_lowrank` 与 `knn_kernel_targetfeat` 仍是最值得继续审计的正向线索
- `residual_over_mean__lm_train_lowrank` 当前不能再视为独立证据，因为它与 `lm_train_lowrank` 的 aligned prediction 完全一致
- `elasticnet_targetfeat`、`rf_targetfeat_lowrank`、`fixed_late_fusion_v1` 都没有跨过“可支撑 formal 下一步”的边界
- 当前没有任何 challenger 结果足以直接触发 formal `3 datasets × 5 seeds` adjudication

### 7. 当前数据集治理交付

- 新增 `dataset_tiering.md`，明确 `3 + 4 + 1` 分层
- 新增 `admission_matrix.tsv`，只输出当前分层所需 admission 结论，不预写主协议升格
- 新增 `short_summary.md`，简述为何采用 `3 + 4 + 1`
- 删除不符合当前分层的旧 auxiliary / supplementary formal 叙述与衍生产物

### 8. 输入侧 normalize 审计已关闭

- 本轮曾尝试对以下三条 challenger 做 `raw-input vs normalize_log1p-input` 的最小反事实审计：
  - `lm_train_lowrank`
  - `lm_G_scgpt_ridge`
  - `lm_G_geneformer_ridge`
- 当前该审计已经正式关闭
- 关闭原因不是“normalize 结果不佳”，而是这三条方法在结构上 `not_applicable`

关闭理由：

- `lm_train_lowrank` 没有独立的单细胞输入特征层；若在 train delta 构造处加入 `normalize+log1p`，会把监督目标从 benchmark `A-space` 改到变换空间，因此越界
- `lm_G_scgpt_ridge` 与 `lm_G_geneformer_ridge` 当前只使用冻结 target embedding + `A-space` train pseudobulk delta；它们同样没有可单独修改、且不改变监督目标语义的输入编码层
- 因此这三条方法都不满足“只改输入侧、保持监督目标与最终 `predicted_shift` 仍在 `A-space`”的必要条件

当前应保留的结论：

- 这三条方法统一记为 `not_applicable`
- 不再继续扩到 `18` 个组合
- 不再引用先前那组越界的 `K562` normalize exploratory 结果

如果未来要重开 normalize 审计，前提是：

- 必须改用真正存在“单细胞输入 -> 编码层 -> `A-space` 输出”的模型家族
- 更接近的候选是训练型 perturbation adapter，而不是当前这三条 frozen-feature / low-rank challenger
- 且只能作为独立 `exploratory / nonformal` 轨道执行，不能修改 formal truth、official baselines/nulls/scoring；当前草案见 `docs/protocols/stage1a_exploratory_input_transform_track.md`

当前 challenger 执行补充约束：

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
- `target-side feature source` 必须通过 `feature registry` 冻结，而不是散落在方法脚本里
- 任一 challenger 的输入依赖必须通过 `challenger registry.feature_dependencies` 显式指向 `feature registry.feature_id`
- 所有 challenger 必须复用当前 smoke 的：
  - dataset 选择
  - split seed
  - frozen truth
  - aligned evaluable genes
  - scoring contract
- 所有 challenger 的工程接口应统一为：
  - 读取当前 train split
  - 产出统一 `predicted_shift.tsv.gz`
  - 直接接入当前 ingest / evaluate / render 主线
- 结果记录必须区分：
  - `ran_and_better_than_mean`
  - `ran_and_close_to_mean`
  - `ran_and_worse_than_mean`
  - `failed_runtime`
  - `unavailable`
- `接近 mean` 的工作阈值必须在运行前冻结，不能看到结果后再解释
- 必须显式区分：
  - `implemented`
  - `wired_to_eval`
  - `executed_on_smoke`
  - `eligible_for_next_step`

当前方法池与解锁顺序：

- 以下“解锁顺序”只保留作 formal 边界记录，不再表示当前待执行事项

- `A` 层：embedding + linear model 家族，为当前主线
  - `lm_train_lowrank`
  - `lm_G_scgpt_ridge`
  - `lm_G_geneformer_ridge`
  - `residual_over_mean__lm_train_lowrank`
- `B` 层：传统 ML 家族，只保留最小 exploratory 版本
  - `elasticnet_targetfeat`
  - `knn_kernel_targetfeat`
  - `rf_targetfeat_lowrank`
- `C` 层：组合方法家族，必须预注册成员与固定规则，禁止事后挑权重
  - `fixed_late_fusion_v1`
- 当前默认方法学定义：
  - `lm_train_lowrank`：`target features -> low-rank shift factors -> full predicted_shift`
  - `lm_G_scgpt_ridge`：使用 `scGPT` gene embedding 作为 target representation 的 ridge challenger
  - `lm_G_geneformer_ridge`：使用 `Geneformer` gene embedding 作为 target representation 的 ridge challenger
  - `residual_over_mean__lm_train_lowrank`：先固定 `mean_shift_baseline`，再仅学习 residual
  - `elasticnet_targetfeat`：稀疏线性 exploratory challenger
  - `knn_kernel_targetfeat`：非参数 geometry exploratory challenger
  - `rf_targetfeat_lowrank`：非线性 low-rank exploratory challenger
  - `fixed_late_fusion_v1`：固定权重、预注册成员的 late-fusion challenger
- formal 解释边界下的解锁顺序固定为：
  1. 先冻结 `feature registry` 与 `challenger registry`
  2. 再实现并运行 `lm_train_lowrank`
  3. 只有在 `lm_train_lowrank` 跑通且出现正向信号时，再运行 `lm_G_scgpt_ridge` 与 `lm_G_geneformer_ridge`
  4. 只有前两步出现正向信号时，再运行 `residual_over_mean__lm_train_lowrank`
  5. 只有至少两个 challenger 显示互补或近似正向时，再运行 `fixed_late_fusion_v1`
  6. `elasticnet_targetfeat`、`knn_kernel_targetfeat`、`rf_targetfeat_lowrank` 放在最后
- exploratory override 生效后的执行口径：
  1. 仍优先完成 `A` 层最小主线
  2. 即使 `A` 层没有形成一致正向信号，仍允许继续实现并运行后续 backlog
  3. 这些结果统一记为 exploratory backlog，不作为 formal 解锁依据
  4. “继续实现” 与 “支持 formal 下一步” 必须分开记录
  5. 当前 backlog 已执行完成，因此后续重点不再是“能不能开做”，而是“如何解释与是否值得进入 supplementary benchmarking”

### 9. `正向信号` 的当前工作定义

- `正向信号` 只用于决定是否进入下一步 challenger，不构成 formal superiority 结论
- 在 exploratory override 生效后，`正向信号` 不再是“是否允许继续实现后续 backlog”的必要条件
- 但它仍然是“是否值得把后续结果上升为更强方法学主张”的唯一工作门槛
- 满足以下任一条，可记为出现初步正向信号：
  1. 至少一个主指标明确优于 `mean_shift_baseline`，且无灾难性退化指标
  2. 多个主指标整体接近 `mean_shift_baseline`，同时不存在明显退化
  3. 方法可稳定跑通，且参数网格呈现可解释的改善趋势，并且整体表现未明显劣于 `mean_shift_baseline`
- `稳定跑通` 是必要条件，不是充分条件
- `lm_train_lowrank` 当前最小参数网格固定为：
  - `K ∈ {16, 32, 64}`
  - `alpha ∈ {0.1, 1.0, 10.0}`

## 你接下来先做什么

按优先级：

1. 审查 challenger 的 `vs_mean` 汇总，形成一份正式的 exploratory / supplementary 审计结论
2. 在 registry 与文档中明确：`residual_over_mean__lm_train_lowrank` 当前与 `lm_train_lowrank` 等价，不再单独计数
3. 固化 supplementary 上的 `coverage-blocked` 口径，避免把 blocked 误写成“结果差”
4. 把 normalize 审计关闭结论保持为最终状态，不再在这三条 challenger 上继续消耗时间
5. 固化 `GEARS` current version 的 `under audit` 结论，不再把它描述成“暂时无问题”
6. 确认 `scGPT / Geneformer` 当前 adapter 的 taxonomy 与可声明范围
7. 整理四条 lanes 的稳定性结论，明确“lane 稳定”与“entrant 表现稳定”是两回事
8. 是否推进 formal `3 datasets × 5 seeds` adjudication 仍需单独判断
9. 是否需要调整 frozen feature coverage policy，需单独立项，不在当前文档里默认放宽

## 新窗口直接执行

如果你新开一个终端窗口，直接按下面顺序接手：

1. 先确认当前任务只剩“审计与文档收口”，不是继续扩模型
2. 先保留 normalize 审计关闭结论，不再在三条目标 challenger 上继续试验
3. 再围绕 `vs_mean` 汇总、等价方法去重、coverage-blocked 解释边界推进文档

建议直接执行：

```bash
sed -n '/## 当前 normalize 审计状态/,/当前 challenger 执行补充约束/p' README.md
sed -n '/## 你接下来先做什么/,/## 本轮验收口径/p' plan.md
```

接手时不要改动的结论：

- `residual_over_mean__lm_train_lowrank` 当前与 `lm_train_lowrank` 等价
- `tian_2019_ipsc / tian_2021_crispri` 当前属于 next formal-admission batch，不能写成 official formal
- `lm_train_lowrank / lm_G_scgpt_ridge / lm_G_geneformer_ridge` 的输入侧 normalize 审计已正式关闭，并统一记为 `not_applicable`

## 本轮验收口径

- `README.md`、`plan.md`、`configs/stage1a_formal_datasets.yaml`、`reports/stage1a/admission/stage1a_admission_manifest.tsv` 对当前数据集状态描述一致
- `harmonized resource layer -> dataset admission layer -> entrant benchmarking layer` 的顺序在文档中明确
- `signal adequacy` 与 `model fidelity` 的边界在文档中明确
- `support floor` 至少显式绑定 `cells per perturbation`、`cells per control`、`UMI depth`
- `tian_2019_day7neuron`、`tian_2019_ipsc` 与 `tian_2021_crispri` 的 admission 决议明确，不再混成“统一待重跑”
- 5 个 Stage 1A 数据集均已完成统一口径的完整性检查
- formal 主榜仍只消费 official formal 的 3 个主线数据集；其余数据集即使完成审计，也不得写成 `auxiliary_pass` 或变相 formal
- `1 seed × 3 entrants × 3 datasets` 的 trial run 已产出完整 aligned / lane / dataset / pass skeleton 结果
- `GEARS × day7neuron` 的 export-space 审计已证明：control 无误，但 `predicted_expression_raw` 已偏大，减 control 后放大成不可信 delta
- 若进入 challenger 探索，文档中已明确：`稳定跑通` 不等于 `正向信号`，`正向信号` 不等于 formal superiority
- 若进入 challenger 探索，文档中已明确：`feature registry` 与 `challenger registry` 已冻结，后续方法可在 exploratory override 下继续实现
- challenger 的实现状态、接线状态、smoke 运行状态与是否解锁下一步必须分开记录
- 若采用 exploratory override，文档中也已明确：“允许继续实现 backlog” 不等于 “允许提升 formal 结论”
- next formal-admission batch 的 exploratory benchmarking 已明确覆盖 `tian_2019_ipsc / tian_2021_crispri`
- `residual_over_mean__lm_train_lowrank` 的当前等价性与 candidate / annex 轨道上的 coverage-blocked 边界已在文档中明示
- 输入侧 normalize 审计已正式关闭，且当前三条目标 challenger 已明确定义为 `not_applicable`

## 你接下来先做什么

1. 先保持 current official formal 的 3 个主锚点不变，不做一次性扩桶。
2. 再围绕 `tian_2019_ipsc / tian_2021_crispri / replogle_2022_k562_gwps` 做制度升格前的最后复核，只处理“是否正式纳入 official formal”，不重写 admission 事实。
3. 对派生候选单独处理：
   - `norman_2019_raw__single_target`：按独立 candidate 送审
   - `dixit_2016_raw__control_context`：按独立 candidate 送审
4. 不把 `norman_2019_raw` 整集并入 official formal；它继续留在 annex。
5. 不把 `dixit_2016_raw` 整包并入 official formal；只保留 `control_context` 这条派生子集继续向 formal 靠近。
