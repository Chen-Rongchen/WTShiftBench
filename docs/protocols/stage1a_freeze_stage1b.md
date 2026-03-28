# Stage 1A → Freeze → Stage 1B 制度协议

本文档固化 **Stage 1A、Freeze、Stage 1B** 的制度边界与执行顺序，与 `docs/protocol_blueprint.md` 长期蓝图一致；**不**展开 Stage 2 全实现细节。

## 1. 模型能力形成层

本 benchmark **不要求**在 Stage 1A / 1B 内训练新模型。候选对象必须在评测外通过其原生方式具备 **`predicted_shift` 输出能力**，例如：

- 原生 perturbation predictor 的训练（在 benchmark 外完成）；
- foundation 模型预训练权重加载 + 任务适配；
- 已有黑盒 workflow / adapter。

**Stage 1A 与 Stage 1B 均为评测层，不是模型训练层。**

进入 Stage 1A 的对象，必须是 **已具备 `predicted_shift` 输出能力** 的黑盒模型 / adapter / workflow。

## 2. Stage 1A 的角色

Stage 1A 是基础 **fidelity gate**，并采用 `four-lane formal adjudication`；它回答：

> 该模型是否具备基础分子层预测能力，并且这种能力是否在 **formal held-out / split** 制度下表现出足够的 `cross-lane stability`？

因此 Stage 1A **可以**包含：

- formal held-out split；
- multi-split robustness；
- multi-seed robustness。

Stage 1A formal held-out 的 **具体比例与分层实现** 以 split registry / 方案 B 为准（见 `configs/stage1a_split_governance.yaml`、`docs/protocol_blueprint.md` §5.1A 及 `scripts/stage1a_split_plan_b.py`）；本文仅定义 formal held-out / multi-split 的制度角色，**不在此固定单一数值**。（讨论中常以「约 20% per stratum」表述，**正式实现与升级以 registry 为准**。）

若采用 **全部 perturbations / genes 的 in-sample** 评估，则该结果更接近 **开发内展示**（developmental / in-sample demonstration），**不应等同于** Stage 1A formal gate 下基于 held-out 的 **generalization 裁决**（formal adjudication）。

Stage 1A 的 `stable_formal_admissible` 裁决，表示该模型获得进入更高层正式验证的 **基础准入资格**；`exploratory_admissible` 仅保留探索性后续分析资格；**不是**在 Stage 1A 内完成「训练层」意义上的模型开发。

## 3. Freeze 的角色

**Freeze 只发生在 `Stage 1A adjudication outcome = stable_formal_admissible` 之后、`Stage 1B formal validation` 开始之前。**

Freeze **不是**禁止未来做任何改动，而是：对 **本次正式进入 Stage 1B（及后续 Stage 2 bridge）的模型版本** 进行制度封版。

### 3.1 至少应冻结的对象

至少包括：

| 类别 | 说明 |
|------|------|
| 身份与产物 | `model_id`；checkpoint / 权重路径；adapter / task head |
| 训练与推理 | 主要超参；`seed`；split 版本 |
| 数据与协议 | 输入预处理版本；control 定义；`predicted_shift` 导出 recipe |
| 评测空间 | `evaluation_space_id`；`frozen_gene_set_id`；`threshold_registry_version` |
| 可复现性 | `code_commit_hash` |

具体落盘建议使用仓库提供的 **`schemas/freeze_manifest.template.yaml`** 填写实例（复制为带版本号的 manifest 文件）。

### 3.2 Freeze 后的约束

Freeze 后，Stage 1B **只能**读取该版本并运行评估，**不得**因 Stage 1B 结果不理想而回改该冻结版本（权重、recipe、主阈值等）。

## 4. Stage 1B 的角色

Stage 1B 是 **14d human external time-aligned validation**，**默认不承担**模型开发职责。

它回答：

> **同一个**已通过 Stage 1A 且已 **Freeze** 的模型版本，在 14d human time-aligned truth 上是否仍能保持 **predicted shift vs real shift** 的一致性？

### 4.1 准入条件

进入 `Stage 1B formal validation` 的必须是 **`stable_formal_admissible` 后冻结的同一个模型版本**（与 Freeze manifest 一致）。

`exploratory_admissible` entrant version 可以进入 `Stage 1B exploratory analysis`，但不得视为冻结后进入 formal downstream 的版本。

### 4.2 默认制度：external、可不 split

默认制度下：

- Stage 1B 视为 **external time-aligned validation** 层；
- **不强制**内部 held-out split；

**前提**：Stage 1B **不参与**模型开发、模型选择、adapter 选择、超参调整或主流程回改。

仅当 Stage 1B 被用于上述 **开发决策** 时，才需要在 Stage 1B 内再划分 dev/test，或引入 **额外 external validation**。

## 5. Stage 1B 与 Stage 2 的关系（边界声明）

- `Stage 1B formal validation` 为进入 human 14d **Stage 2 formal bridge** 提供 **time-aligned fidelity** 背书；
- `Stage 1B exploratory analysis` 只可衔接 `Stage 2 exploratory bridge`；
- **Stage 2 不是训练层**，而是 **bridge evaluation** 层；
- **不允许**使用 Stage 2 **phenotype truth** 对模型做反向优化。

**Stage 2** 的完整 **dual-pillar**、NT/control 起点、DepMap bridge 等协议见 **`docs/protocol_blueprint.md` §7**；本文仅定义 **Stage 1A adjudication → Freeze → Stage 1B** 的准入与版本冻结边界，不展开 Stage 2 技术细节（工程实现亦不在本文档范围）。

## 6. 新版本定义与重新准入

若以下任一项发生变化，则视为 **新版本**，必须重新走 **Stage 1A → Freeze → Stage 1B**：

- 模型权重；
- adapter；
- 主要超参；
- 主预处理；
- `predicted_shift` 导出规则；
- evaluation space；
- **primary thresholds**（见 threshold registry 制度）。

## 7. 禁止事项（摘要）

- Stage 1A / 1B **不是**模型训练层。
- **不允许**把 Stage 2 phenotype truth 用于模型反向优化。
- **不允许**在看到 Stage 1B 结果后，修改同一冻结版本的主要 recipe，仍声称是「同一个模型」。
- 关键改动 → 新版本 → 必须重新走 **Stage 1A → Freeze → Stage 1B**。

## 8. 相关文件

- 长期蓝图：`docs/protocol_blueprint.md`
- Freeze 清单模板：`schemas/freeze_manifest.template.yaml`
