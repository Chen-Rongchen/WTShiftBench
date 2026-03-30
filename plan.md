# WT Benchmark 当前计划

## 文档定位

本文件只写当前最近一批、可以直接开始执行的工作，不写长期制度展开。

- 长期制度看 `docs/protocol_blueprint.md`
- 当前真实状态看 `README.md`

## 当前主任务

先补 `benchmark-invariant layer` 的地基，再推进 entrant benchmarking。

当前固定顺序：

1. `harmonized resource layer`
2. `dataset admission layer`
3. `entrant benchmarking layer`

## 本轮目标

把 `Stage 1A` 从“已有数据与 adapter 骨架”推进到“benchmark-invariant layer 已冻结、随后可稳定进入 entrant benchmarking”的状态。

## 本轮不做

- 不新增 formal 主线数据池
- 不直接展开 `3 datasets × 5 seeds` formal adjudication
- 不在 admission 未闭合的数据集上产出 formal entrant 结论
- 不把 adequacy 诊断指标替代 `predicted_shift` formal scoring

## 当前执行批次

### 1. harmonized resource layer 收口

- 固化 `Stage 1A` 数据资源登记、来源、下载口径与 provenance
- 明确 raw / processed level 边界
- 保持 formal dataset registry、raw audit 产物、admission manifest 与 README 叙述一致

### 2. dataset admission layer 收口

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

### 3. 当前数据集决议收口

#### `tian_2019_day7neuron`

- 已完成 raw audit
- 已完成 formal filtering
- formal 统计已回填：`85290 x 33752`，`n_controls=15580`，`n_perturbed=69710`，`n_unique_targets=26`
- 已在 admission manifest 中标记为 `pass`

#### `tian_2021_crispri`

- 已完成下载与 raw audit
- `ATP5C1`、`ATP5H`、`TMEM55A` 三个 token 的 target mapping closure 已闭合
- 已完成 refetch 与 formal filtering
- 当前状态更新为 `auxiliary_pass`
- 已在 admission manifest 中标记为 `auxiliary_pass`
- 默认仍不进入 formal 主裁决，但可进入 supplementary / auxiliary benchmarking

### 4. entrant benchmarking 进入条件

只有在以下条件满足后，才继续推进 entrant benchmarking：

- harmonized resource layer 已稳定
- dataset admission 规则已明确
- 主线数据集 formal filtering 与 truth 输入边界已冻结
- adequacy diagnostics 与 fidelity scoring 的解释边界已写清

## 你接下来先做什么

按优先级：

1. 生成三模型 mainline adapter 预测产物
2. 跑 batch scoring 并产出 lane-wise formal outputs
3. 汇总 cross-lane summary，形成单 seed 的 formal adjudication 草案
4. 视结果决定是否启动 `tian_2021_crispri` 的 supplementary / auxiliary benchmarking

## 本轮验收口径

- `README.md`、`plan.md`、`configs/stage1a_formal_datasets.yaml`、`reports/stage1a/admission/stage1a_admission_manifest.tsv` 对当前数据集状态描述一致
- `harmonized resource layer -> dataset admission layer -> entrant benchmarking layer` 的顺序在文档中明确
- `signal adequacy` 与 `model fidelity` 的边界在文档中明确
- `support floor` 至少显式绑定 `cells per perturbation`、`cells per control`、`UMI depth`
- `tian_2019_day7neuron` 与 `tian_2021_crispri` 的 admission 决议明确，不再混成“统一待重跑”
- 4 个 Stage 1A 数据集均已完成统一口径的完整性检查
- formal freeze 仅冻结 mainline `pass` 数据集
