# Why the shared-mean baseline is a strong but non-endpoint-leaking backbone reference

## 状态

完成日期：2026-04-17。

用途：作为 Supplementary appendix 草案，回答 reviewer 可能提出的 baseline artifact / leakage 问题。

## 核心结论

`shared_mean_baseline` 不是一个外部可部署的 predictive model，也不应被写成 biology-aware SOTA。它是一个在 frozen architecture 内定义的 backbone reference，用来检验当前 recovery object 中有多少信号由 canonical shared backbone 主导。

它的强表现说明：当前 HCC truth object 的主 backbone 含有强 shared component。它不说明复杂模型无价值，也不说明 baseline 在所有 adjudication 维度胜出。

## baseline 使用了什么

根据 `src/wtbench/stage2_hcc_prediction_export.py` 中的 `build_builtin_shared_mean_baseline`，该 reference：

- 读取已冻结的 `axis_membership` 与 `truth_contract`。
- 找到 `architecture_role == canonical_backbone` 的 targets。
- 在 `truth_aligned_log_shift` 中对这些 canonical-backbone targets 的 transcriptomic shift 向量取均值。
- 将该 shared backbone mean vector 作为所有 targets 的 predicted shift。

因此它使用的是 frozen transcriptomic backbone reference，而不是 gene-specific model inference。

## baseline 没有使用什么

它没有使用：

- entrant 的训练数据、参数或 learned representation。
- DepMap dependency 数值来预测每个 target。
- RNAi DEMETER2 endpoint。
- K562 temporal panel。
- target-specific Q1 anchor identity 来为每个 target 定制预测。
- downstream model-side scoring result。

关键边界：它使用 frozen architecture role 来构建 reference，因此它不是 truth-free deployable model；但它不把 DepMap endpoint 数值或 target-specific dependency rank 注入预测矩阵。它更适合作为 backbone reference，而不是作为普通 entrant 与模型同义比较。

## 为什么这不是 trivial metric artifact

如果 scoring metric 只是机械奖励“所有 target 预测同一个均值”，那么 null / mean-like references 应在所有架构维度上同时占优。但当前结果不是这样：

- `shared_mean_baseline` 的优势集中在 `backbone_recovery_score`。
- GEARS 在 `structure_vs_context_separation_score` 上强于 baseline。
- GEARS sweep 候选可以提高 separation 或 shift-excess，但仍不能关闭 backbone gap。
- 三指标相关性诊断显示三指标是部分耦合但非重复信号，见 `reports/manuscript_metric_diagnostic_v1/metric_diagnostic_report.md`。

因此 baseline 的胜出不应解释成“metric 自动奖励 baseline”。更稳的解释是：当前 truth object 的 canonical backbone 确实被 shared transcriptomic component 主导，而复杂 entrants 的相对优势更多落在 separation / deviation 维度。

## 为什么不能写成 deep models useless

当前比较是非对称 trade-off：

- `shared_mean_baseline` 是 backbone primary reference。
- GEARS 是 separation-biased entrant。
- Geneformer / scGPT / ridge controls 提供额外 model-side context，但没有推翻 backbone reference。

复杂模型没有稳定胜过 backbone reference，并不等于没有学到任何 structure。它表示这些结构没有稳定转化为当前 frozen architecture 中最强的 primary component：canonical backbone recovery。

## 推荐 Supplementary wording

允许写：

> The shared-mean baseline was used as an architecture reference rather than as a deployable predictive model. It was constructed from the frozen canonical-backbone transcriptomic component and did not use DepMap dependency values, RNAi endpoints or model-side scoring outcomes to generate target-specific predictions. Its strong backbone recovery therefore indicates that the frozen HCC recovery object contains a dominant shared-backbone component. This does not imply that complex entrants are uninformative; GEARS retained a relative advantage in structure-versus-context separation.

允许写：

> The baseline result is not interpreted as a unidirectional model failure. It identifies the part of the frozen architecture that is most strongly shared across contexts, while the separation and shift-excess metrics capture different recovery dimensions.

禁止写：

- `shared_mean_baseline is a fully independent model`
- `shared_mean_baseline proves deep models are useless`
- `baseline victory proves all model-side structure is artifact`
- `baseline did not use any truth information`

更准确的写法是：

- `shared_mean_baseline is a frozen-architecture backbone reference`
- `shared_mean_baseline does not leak dependency endpoint values into target-specific predictions`
- `baseline strength reflects a shared-backbone-dominated recovery object`

## permutation null 补充结果

已完成 B13：

- target-to-axis permutation：`reports/manuscript_permutation_null_v1/permutation_null_report.md`
- baseline gene-label permutation：`reports/manuscript_permutation_null_v1/baseline_gene_label_permutation_summary.tsv`

关键解释：

- target-to-axis permutation 对 `shared_mean_baseline` 基本不敏感，因为该 reference 对所有 targets 使用同一个 backbone vector。
- 因此额外补充 gene-label permutation，用于打断 prediction vector 与 axis gene sets 的对应关系。
- 在 gene-label permutation null 下，baseline backbone observed = 0.807，高于 null 97.5% 分位 0.703，empirical p = 0.003。
- baseline shift-excess 不高于 null，separation 反而低于 null；这支持 baseline 优势集中在 backbone，而不是三指标被机械整体奖励。
