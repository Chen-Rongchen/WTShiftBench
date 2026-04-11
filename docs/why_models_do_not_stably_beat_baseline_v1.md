# 为什么模型不能稳定胜过 baseline v1

## 1. 文档定位

这份文档只回答一个问题：

**在当前 HCC Stage 2 contract 下，为什么更复杂的 entrant 不能稳定胜过 `shared_mean_baseline`？**

它要做的是：

- 给出可防守的正式 explanation layer
- 说明当前已经排除了哪些简单解释
- 固定哪些解释当前只能写成 plausible mechanism，而不能写成 fully proved root cause

它不把这条解释线写成已经完成的终局证明；这条线当前服务于比较层正式收口，而不是替代 sensitivity / covariate / final boundary 的未闭环事项。

它不把这件事写成“模型完全没学到东西”，也不把当前证据夸大成唯一根因已经被证明。

如果需要把这件事继续拆成“方法学解释”与“生物学解释”两层，请继续看：

- [`docs/model_vs_baseline_deeper_explanation_note_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_deeper_explanation_note_v1.md)
- [`docs/model_vs_baseline_next_step_breakdown_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_next_step_breakdown_v1.md)

## 2. 先固定现象

当前现象不是单次偶然波动，而是已经在统一 contract 下重复出现的稳定模式：

- [`reports/stage2_real_hcc_smoke/model_comparison.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/model_comparison.tsv)
- [`reports/stage2_real_hcc_smoke/backbone_diagnosis.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/backbone_diagnosis.tsv)

当前跨细胞系均值中：

- `shared_mean_baseline`
  - `backbone_recovery = 0.807`
  - `structure_vs_context_separation = 0.353`
- `GEARS`
  - `backbone_recovery = 0.660`
  - `structure_vs_context_separation = 0.428`
- `geneformer_hcc_formal_v1`
  - `backbone_recovery = 0.533`
  - `structure_vs_context_separation = 0.401`
- `scgpt_hcc_formal_v1`
  - `backbone_recovery = 0.447`
  - `structure_vs_context_separation = 0.295`
- `lm_train_lowrank_hcc_formal_v1`
  - `backbone_recovery = 0.537`
  - `structure_vs_context_separation = 0.286`
- `lm_g_geneformer_ridge_hcc_formal_v1`
  - `backbone_recovery = 0.627`
  - `structure_vs_context_separation = 0.326`
- `lm_g_scgpt_ridge_hcc_formal_v1`
  - `backbone_recovery = 0.467`
  - `structure_vs_context_separation = 0.259`

这说明两件事：

1. `shared_mean_baseline` 的 backbone 优势是真实存在的，而不是“模型还没完全接入”造成的假象。
2. 复杂模型并非没有结构能力，但这些能力没有稳定转化为更强的 `canonical backbone recovery`。

## 3. 当前已经排除的简单解释

### 3.1 不是因为 entrant 没有正式接入

当前进入同一份 HCC formal comparison 的对象已经包括：

- `GEARS`
- `scGPT`
- `Geneformer`
- `lm_train_lowrank`
- `lm_G_scgpt_ridge`
- `lm_G_geneformer_ridge`

因此，“只有一种模型所以不知道能不能赢”当前已不成立。

### 3.2 不是因为 export / contract 出错

这些对象都已经走完：

- raw output
- `stage2_truth_aligned_log_shift` export
- contract validation
- real HCC smoke

因此当前 backbone gap 不能解释为 export space 不一致或 scorer-ready contract 没对齐。

### 3.3 不是因为 pretrained ridge coverage 不足

两条 embedding ablation control 当前都已经实现运行时 checkpoint lookup，并且 coverage 达到 `1.000`：

- [`reports/stage2_lm_g_scgpt_ridge_hcc_recipe/HCC38/coverage_audit.json`](/home/data/gz0705/WTKO/reports/stage2_lm_g_scgpt_ridge_hcc_recipe/HCC38/coverage_audit.json)
- [`reports/stage2_lm_g_scgpt_ridge_hcc_recipe/HCC1143/coverage_audit.json`](/home/data/gz0705/WTKO/reports/stage2_lm_g_scgpt_ridge_hcc_recipe/HCC1143/coverage_audit.json)
- [`reports/stage2_lm_g_geneformer_ridge_hcc_recipe/HCC38/coverage_audit.json`](/home/data/gz0705/WTKO/reports/stage2_lm_g_geneformer_ridge_hcc_recipe/HCC38/coverage_audit.json)
- [`reports/stage2_lm_g_geneformer_ridge_hcc_recipe/HCC1143/coverage_audit.json`](/home/data/gz0705/WTKO/reports/stage2_lm_g_geneformer_ridge_hcc_recipe/HCC1143/coverage_audit.json)

因此当前不能再把 ridge control 的弱势简单解释成“held-out target 根本没覆盖到”。

## 4. 当前最稳的三层解释

### 4.1 任务结构层：baseline 已经吃掉了大块 shared backbone

当前最强的事实是：

- `shared_mean_baseline` 在两个 cell line 上的 backbone cosine 都显著高于各 entrant
- `shared_mean_baseline` 在两个 cell line 上的 backbone recovery 也都更高

例如：

- HCC38 backbone cosine
  - baseline = `0.408`
  - `GEARS` = `0.179`
  - `Geneformer` = `0.148`
  - `lm_g_geneformer_ridge` = `0.089`
  - `lm_g_scgpt_ridge` = `0.078`
- HCC1143 backbone cosine
  - baseline = `0.409`
  - `GEARS` = `0.134`
  - `Geneformer` = `0.204`
  - `lm_g_geneformer_ridge` = `0.222`
  - `lm_g_scgpt_ridge` = `0.088`

这更像是在说：

- 当前 HCC truth 里的 `canonical backbone` 含有很强的 shared component
- `shared_mean_baseline` 本身已经是一个很强的 backbone estimator

因此复杂模型若想胜出，不是只要“有额外能力”就够了，而是必须同时保住 shared backbone，再额外学到更细结构。

### 4.2 目标不对齐层：复杂模型把容量放到了别的结构目标上

当前 `GEARS` 的结果最能说明这点：

- 它没有赢 backbone
- 但稳定赢了 `structure_vs_context_separation`
- 并且在 `HCC1143` 上对 `shift-excess` 更强

这说明它学到的不是“错误的东西”，而是：

- 更偏 `separation`
- 更偏 `deviation`
- 更偏 context-sensitive structure

也就是说，当前 entrant 的训练目标或 inductive bias 更像是在优化：

- 把 shared structure 和 context deviation 分开
- 识别一部分 shift-excess

但这不等于直接优化 `canonical backbone recovery`。

因此更稳的写法是：

**当前复杂 entrant 的优势方向，与当前 primary adjudication 最看重的 backbone winner 方向并不完全对齐。**

### 4.3 表征约束层：pretrained target embedding 单独拿出来并不能稳定恢复 backbone

这一步由两条 ridge control 说明得最清楚：

- `lm_g_geneformer_ridge` 的 backbone 比 `lm_g_scgpt_ridge` 好，但 shift-excess 很弱
- 两条 ridge control 在 `backbone_diagnosis.tsv` 中都被判成 `direction`

这意味着：

- 问题不只是“幅度没拉满”
- 更关键的是 canonical backbone 的方向恢复本身偏弱

换句话说：

- 冻结的 pretrained target embedding 不是完全没信息
- 但单独依赖这层 embedding，再接线性头，并不足以稳定把 backbone 方向对齐到 baseline 水平

这支持一个更稳的解释：

**foundation-model backbone 的一部分价值可能来自更复杂的上下文/非线性使用方式；而一旦压缩成 target embedding + 线性头，这部分能力就不能稳定转化成 stronger backbone recovery。**

## 5. 为什么当前更像“方向失败”而不是“幅度失败”

当前 `backbone_diagnosis.tsv` 给了一个很重要的信号：

- `scGPT`
  - `HCC38 = direction`
  - `HCC1143 = direction`
- `lm_train_lowrank`
  - `HCC38 = direction`
  - `HCC1143 = direction`
- `lm_g_scgpt_ridge`
  - `HCC38 = direction`
  - `HCC1143 = direction`
- `lm_g_geneformer_ridge`
  - `HCC38 = direction`
  - `HCC1143 = direction`

同时从 expression summary 看，ridge control 的 `top20_overlap` 并没有全线崩掉，但 backbone cosine 很低、L2 很大。例如：

- `lm_g_geneformer_ridge @ HCC38`
  - backbone cosine = `0.089`
  - backbone L2 = `0.672`
  - backbone top20 = `0.575`
- `lm_g_scgpt_ridge @ HCC38`
  - backbone cosine = `0.078`
  - backbone L2 = `0.838`
  - backbone top20 = `0.600`

这说明：

- 它们不是完全抓不到高变化基因
- 但抓到的方向与 canonical backbone 的主方向并不对齐

因此当前最稳的说法不是“模型只差一点幅度缩放”，而是：

**模型可以碰到一部分相关基因，但 canonical backbone 的主方向恢复仍然偏弱。**

## 6. 当前不应写成什么

以下几种说法当前都不稳：

- “复杂模型失败是因为实现有 bug”
- “复杂模型失败只是因为 target coverage 不够”
- “复杂模型完全没学到 biological structure”
- “我们已经证明唯一 root cause 是目标函数错了”
- “baseline 胜出说明所有复杂模型都没有价值”

## 7. 当前最稳的正式结论

如果把这件事压成一段正式 explanation，最稳的说法是：

在当前 HCC Stage 2 contract 下，`shared_mean_baseline` 之所以仍然稳定强于复杂 entrant，最主要不是因为 entrant 尚未正式接入，也不是因为 export / coverage 错配，而是因为当前任务中的 `canonical backbone` 本身具有很强的 shared component，baseline 已经能有效捕获这部分主结构。相比之下，复杂 entrant 所学习到的额外能力更倾向于 `structure/context separation`、`shift-excess identification` 或 context-sensitive deviation，而这些优势并未稳定转化为更强的 backbone recovery。进一步地，pretrained target embedding 的线性 ablation control 表明，冻结 embedding 单独拿出来并不足以稳定恢复 backbone 主方向，因此当前 backbone gap 更像是 direction-level mismatch，而不是单纯的 amplitude insufficiency。由此，当前最稳的解释不是“复杂模型没有结构价值”，而是“它们的结构优势方向，与当前 adjudication 中最难超越的 shared canonical backbone 并不完全对齐”。

## 8. 当前还没有 fully proved 的部分

当前还不能写成已经 fully proved 的对象包括：

- 唯一 root cause
- 哪一个具体训练目标最该负责
- 是否只要改训练目标就一定能超过 baseline
- 是否需要更多 context-specific supervision 才能关闭 backbone gap

因此，这份文档当前提供的是：

- formal explanation layer
- defendable reason framework

而不是：

- single-cause proof

## 9. 渐进披露

默认先看：

1. [`reports/stage2_real_hcc_smoke/model_comparison.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/model_comparison.tsv)
2. [`reports/stage2_real_hcc_smoke/backbone_diagnosis.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/backbone_diagnosis.tsv)
3. [`docs/stage2_fuller_hcc_model_comparison_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_fuller_hcc_model_comparison_note_v1.md)
4. [`docs/model_vs_baseline_deeper_explanation_note_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_deeper_explanation_note_v1.md)
5. [`docs/model_vs_baseline_next_step_breakdown_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_next_step_breakdown_v1.md)

若要下钻，再看：

- [`reports/stage2_real_hcc_smoke/details/shared_mean_baseline/HCC38/expression_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/details/shared_mean_baseline/HCC38/expression_summary.tsv)
- [`reports/stage2_real_hcc_smoke/details/shared_mean_baseline/HCC1143/expression_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/details/shared_mean_baseline/HCC1143/expression_summary.tsv)
- [`reports/stage2_real_hcc_smoke/details/geneformer_hcc_formal_v1/HCC38/expression_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/details/geneformer_hcc_formal_v1/HCC38/expression_summary.tsv)
- [`reports/stage2_real_hcc_smoke/details/geneformer_hcc_formal_v1/HCC1143/expression_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/details/geneformer_hcc_formal_v1/HCC1143/expression_summary.tsv)
- [`reports/stage2_real_hcc_smoke/details/lm_g_geneformer_ridge_hcc_formal_v1/HCC38/expression_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/details/lm_g_geneformer_ridge_hcc_formal_v1/HCC38/expression_summary.tsv)
- [`reports/stage2_real_hcc_smoke/details/lm_g_geneformer_ridge_hcc_formal_v1/HCC1143/expression_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/details/lm_g_geneformer_ridge_hcc_formal_v1/HCC1143/expression_summary.tsv)
- [`reports/stage2_real_hcc_smoke/details/lm_g_scgpt_ridge_hcc_formal_v1/HCC38/expression_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/details/lm_g_scgpt_ridge_hcc_formal_v1/HCC38/expression_summary.tsv)
- [`reports/stage2_real_hcc_smoke/details/lm_g_scgpt_ridge_hcc_formal_v1/HCC1143/expression_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/details/lm_g_scgpt_ridge_hcc_formal_v1/HCC1143/expression_summary.tsv)

## 10. 一句话收口

当前要解释的不是“为什么模型完全不行”，而是“为什么在一个 shared canonical backbone 很强的任务里，复杂模型学到的额外结构优势没有稳定转化为 backbone superiority”。 
