# Stage 1A exploratory input transform 轨道草案

## 文档定位

本文档只定义一条严格隔离的 `exploratory / nonformal` 工程轨道，用于预审 `normalize`、`log1p` 等输入变换在训练型 perturbation adapter 上是否具备工程可行性。

本文档不是：

- formal `A-space` 协议变更
- official baseline / null / scoring 重定义
- stage admission、方法解锁或 formal 结论依据

## 为什么需要单独轨道

当前 `README.md` 与 `plan.md` 已明确关闭对三条 frozen-feature challenger 的 normalize 审计。关闭原因不是效果差，而是这些方法一旦在 train delta 构造处插入 `normalize+log1p`，监督目标就会从 formal benchmark `A-space` 改到变换空间，因此越界。

这意味着：

- 不能把该方向作为 formal `A-space` 内的“继续补实验”
- 若未来仍要检验 `normalize/log1p` 是否可能带来工程收益，只能新增一条显式平行的 exploratory 轨道
- 该轨道的结果必须承认自己与当前 formal `A-space truth` 不严格同义

## 适用范围

当前只允许把这条轨道用于确实存在以下结构的模型家族：

- `single-cell input -> encoder / perturbation model -> predicted output`

当前最贴近的候选是：

- `GEARS`

当前不在适用范围内的方法：

- `lm_train_lowrank`
- `lm_G_scgpt_ridge`
- `lm_G_geneformer_ridge`

原因很简单：它们没有可单独替换、且不改变监督目标语义的输入编码层。

## 硬边界

### 1. 不改 formal 主线

以下对象一律不得被修改、覆盖或复写：

- formal truth
- official baselines
- official nulls
- official scoring
- official leaderboard
- stage admission manifest
- 方法解锁与 formal adjudication 结论

### 2. 强制 `exploratory / nonformal` 标记

所有配置、产物、报告、表头、summary 都必须显式带上 `exploratory` 或 `nonformal` 标识。

至少包括：

- config id
- run id
- output 目录名
- summary 标题
- comparison 表中的 `scope`

禁止复用以下容易造成串线的命名：

- `official`
- `formal`
- `official_leaderboard`
- `pass_skeleton`

### 3. 不得进入 official 结论链

该轨道的任何结果都不得作为以下事项的依据：

- official leaderboard
- stage admission
- entrant readiness
- formal protocol conclusion
- formal `3 datasets × 5 seeds` adjudication 解锁

### 4. summary 必须写明语义边界

每份 summary 都必须出现等价含义的固定声明：

`本分支输出与当前 formal A-space truth 不严格同义，只用于工程探索与方向预审，不构成 official baseline、formal scoring 或 formal 协议结论。`

### 5. 只允许同空间比较

比较规则必须满足：

- exploratory output 只能与同一 exploratory 语义空间内的 truth / baseline / null / score 比较
- 如果要比较 `relative-to-mean baseline`，必须重建同空间的 exploratory `mean baseline`
- 禁止直接引用 formal `mean_shift_baseline`
- 禁止把 exploratory score 与 formal score 并排解释成“谁更好”

## 工程隔离要求

### 1. 独立 registry

即使实现层复用同一批脚本，也必须在 registry 层单独登记：

- exploratory truth / target space
- exploratory baseline / null
- exploratory scoring scope

建议最少新增一个 `scope` 字段：

- `formal`
- `exploratory_nonformal`

### 2. 独立命名空间

建议统一使用以下前缀：

- `stage1a_exploratory_input_transform`
- `nonformal_input_transform`

建议目录隔离到：

- `data/predictions/stage1a_exploratory_input_transform/...`
- `data/baselines/stage1a_exploratory_input_transform/...`
- `reports/stage1a/exploratory_input_transform/...`

### 3. 渲染保护

render / summarize 脚本必须满足：

- exploratory 结果不能输出为 `official_leaderboard` 文件名
- exploratory 结果不能生成 official pass skeleton
- exploratory 结果若进入统一汇总页，必须单列为 `exploratory / nonformal`

## 最小 smoke 方案

第一轮只允许跑最小组合验证链路，不做矩阵扩张。

建议默认组合：

- dataset：`replogle_2022_k562_essential`
- method family：`GEARS`
- transform：`normalize_log1p`
- split seed：沿用当前 smoke `101`
- model seed：沿用当前单 seed trial 配置

最小 smoke 的目的只有三个：

- 验证数据读取、训练、导出、对齐、比较主线是否可跑通
- 验证 exploratory truth / baseline / scoring 是否与 formal 主线完成物理隔离
- 验证 summary 能否稳定回答本轨道最关心的三个问题

在第一轮 smoke 之前，不做：

- 多数据集批量
- 多 seed 扩张
- 多 transform 网格
- 多模型家族并行

## summary 最少回答的问题

每份 exploratory summary 至少要回答以下三件事：

1. 同一数据集内，变换后相对同空间基线与同空间 truth，性能是否变化。
2. 跨数据集时，指标方差是否缩小。
3. 相对同空间 `mean baseline` 的优势是否变化。

如果当前只跑单数据集 smoke，第 2 条应诚实写为：

- 当前 smoke 只覆盖单数据集，因此还不能回答跨数据集方差是否缩小；本轮只验证工程链路与单数据集方向性。

## go / no-go 判据

第一轮 smoke 后只做以下决策，不做 formal 外推：

- `go`：链路可稳定跑通，语义隔离无误，且单数据集内至少未明显劣于同空间 `mean baseline`
- `hold`：链路可跑通，但结果没有方向性优势，先停在 exploratory 结论
- `no-go`：链路语义不自洽、产物与 formal 串线，或单数据集内明显劣于同空间 `mean baseline`

无论结果如何，都不得写成：

- formal superiority
- entrant ready
- protocol upgraded
- 可直接解锁 formal adjudication

## 当前建议的下一步

如果要真的执行这条轨道，建议按以下顺序推进：

1. 先冻结 exploratory 命名空间、目录与 summary 模板。
2. 再为 `GEARS` 补一个最小 `normalize_log1p` exploratory recipe。
3. 重建同空间 exploratory `mean baseline`。
4. 只跑 `K562 × GEARS × normalize_log1p × seed101` 一条 smoke。
5. 先审读 summary 是否满足本文档的语义边界，再决定是否扩到更多数据集。
