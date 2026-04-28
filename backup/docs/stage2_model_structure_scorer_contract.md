# Stage 2 Model-Side Structure Scorer Contract

## 文档定位

这份文档只定义 **model-side structure scorer** 的 contract，不等同于完整 HCC adjudication 报告。

它要先回答三件事：

1. scorer 的输入是什么
2. prediction 如何投影回 frozen architecture
3. 当前 smoke adjudication 先输出哪三个主裁决分数

当前目标是先把规则定死，再做 HCC smoke adjudication；因此本文档优先定义 **最小可执行 contract**，而不是一次性铺开全部衍生分析。

## 输入 contract

scorer 当前依赖四类输入：

1. `aligned prediction matrix`
   - 行：`target_gene`
   - 列：gene space
   - 值：aligned predicted shift
   - 当前优先复用既有 `stage1a prediction_alignment` 产物，而不是新发明一套 prediction ingest 流程

2. `truth architecture contract`
   - 文件：`reports/stage2_truth_driven_bridge/truth_architecture_contract/truth_architecture_contract.tsv`
   - 用途：提供 `fine_axis -> architecture_role -> confidence`

3. `axis membership`
   - 文件：`reports/stage2_truth_driven_bridge/master_atlas/shared_target_axis_membership.tsv`
   - 用途：提供 `target_gene -> fine_axis -> macro_axis`

4. `shared target master atlas`
   - 文件：`reports/stage2_truth_driven_bridge/master_atlas/shared_target_master_atlas.tsv`
   - 用途：保留后续 adjudication 扩展所需的 truth-side target annotation
   - 但在当前 smoke scorer contract 中，不作为最小必需输入

## Projection contract

projection layer 的职责不是重新定义 truth，而是把模型输出映射到已经冻结的 axis。

当前最小投影规则如下：

1. 以 `shared_target_axis_membership.tsv` 中的 `fine_axis` 作为唯一 axis 集合
2. 对每个 `target_gene × fine_axis`，取该 axis 成员基因在 prediction 中的列交集
3. 计算三个 axis-level projection 指标：
   - `projected_signed_mean`
   - `projected_mean_abs`
   - `projected_l2`
4. 同时写出 coverage 字段：
   - `n_axis_genes`
   - `n_projected_genes`
   - `gene_coverage`
5. 把 `truth_architecture_contract.tsv` 中的 `architecture_role` 与 `confidence` 回填到 projection 表

这一步的目标是让任何 aligned prediction 都能被稳定映射回 frozen architecture，而不是先做复杂统计裁决。

## 三个主裁决分数

当前 smoke adjudication 只要求 scorer 稳定回答三个问题。

### 1. Backbone Recovery Score

问题：模型是否把 canonical backbone target 投影回其期望 axis，而不是把 backbone 信号打散到别的 axis。

当前最小定义：

- 对 `architecture_role == canonical_backbone` 的 target
- 在其所有 axis projection 中，计算期望 axis 的 `projected_mean_abs` 排名百分位
- 对所有 backbone target 取平均

解释边界：

- 它衡量的是 **expected-axis concentration**
- 不是 global fit，也不是单基因 Pearson

### 2. Shift-Excess Identification Score

问题：模型能否把 `shift_excess` target 与 shared backbone 区分开，而不是只学到 shared mean trend。

当前最小定义：

- 取期望 axis 上的 `projected_mean_abs`
- 比较 `shift_excess` targets 与 `canonical_backbone` targets
- 用 pairwise superiority 概率表示分数

解释边界：

- 分数越高，说明 shift-excess target 在其 expected axis 上更容易被分离出来
- 这一步是 **smoke separation test**
- 不是完整生物学裁决

### 3. Structure-vs-Context Separation Score

问题：模型能否把 expected structure 与 off-axis context deviation 分开。

当前最小定义：

- 对每个 target，比较 expected axis 的 `projected_mean_abs` 与 off-axis 平均 `projected_mean_abs`
- 计算 `expected / (expected + off_axis_mean)`
- 再对 target 取平均

解释边界：

- 分数越高，说明结构更集中在 expected axis
- 分数越低，说明模型更像在做 context averaging 或 broad blur

## 当前不做的事

当前 contract 明确不做：

- 不把 global Pearson 当成 architecture recovery 的替代
- 不在 scorer contract 未定前做全量 HCC comparison
- 不把 Dixit supplementary object 并入主 smoke 裁决
- 不在 smoke 阶段一次性引入 sensitivity / covariate closure

## Smoke gate

只有当下列条件成立，才进入 HCC smoke adjudication：

1. aligned prediction 可以稳定投影到全部 frozen axes
2. 三个主裁决分数都能稳定计算
3. baseline / null / strongest entrant 三者能被 scorer 区分

若这一步区分不出来，就停在 scorer 层回改，不进入更大范围 comparison。
