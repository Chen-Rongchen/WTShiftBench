# 模型为何打不过 baseline：深一层解释 note v1

## 1. 文档定位

这份 note 只回答一个问题：

**如果已经接受“复杂模型当前打不过 `shared_mean_baseline`”这一事实，我们还能再往下怎样解释，而且哪些解释当前是证据支持，哪些还只是 plausibility？**

它不重跑分析，也不把现有结果夸大成单一 root cause proof。

它做三件事：

- 把当前最稳的 **方法学解释** 与 **生物学解释** 明确拆开
- 固定哪些表述当前可以写成 defendable explanation，哪些只能写成 plausible interpretation
- 告诉下次进来的人：如果还想继续推进，应该优先补什么，而不是继续空泛讨论“模型为什么不行”

## 2. 一句话结论

当前最稳的总解释不是“模型没学到 biology”，而是：

**在这个 HCC Stage 2 contract 下，`shared_mean_baseline` 已经抓住了很强的 shared canonical backbone；复杂模型学到的额外能力更多落在 `separation / deviation / context-sensitive structure` 上，但这些优势没有稳定转化成更强的 backbone recovery。**

这是一条非对称 trade-off：baseline 不是“全方位更好”，GEARS 也不是“整体更强”。当前更稳的分工是 `shared_mean_baseline = backbone primary reference`，`GEARS = deviation / separation-biased entrant`。

因此，当前 backbone gap 更像是：

- 任务结构与裁决目标偏向 baseline
- 复杂模型的归纳偏置与 primary winner 方向不完全对齐
- 一部分 biological structure 被模型捕捉到，但不位于当前 frozen architecture 中最强、最共享、最可重复的 backbone 上

## 3. 先把两类解释分开

下次讨论这个问题时，必须先把两类解释拆开：

### 3.1 方法学解释

回答的是：

- 当前 benchmark / contract 奖励的到底是什么
- baseline 为什么在这个目标上天然强
- 复杂模型学到的东西为什么没有转化成当前主裁决胜利

### 3.2 生物学解释

回答的是：

- HCC 当前被冻结的主 backbone 在 biology 上可能代表什么
- 为什么更细、更 context-specific 的结构即使真实存在，也不一定帮助模型赢当前主裁决
- foundation-model embedding 所带来的 gene-level prior，为什么不自动等于 perturbation backbone recovery

这两类解释不能混成一句“因为 biology 太复杂”，也不能混成一句“因为 objective 没对齐”。

## 4. 当前证据已经支持的方法学解释

这一层是当前最稳、最可防守的 explanation layer。

### 4.1 任务目标本身偏向 shared backbone estimator

当前 primary adjudication 最难超越的对象，是 `canonical backbone recovery`。

而现有结果已经显示：

- `shared_mean_baseline` 的 backbone recovery 明显高于所有 entrant
- `shared_mean_baseline` 的 backbone cosine 也显著更高
- 这一优势在 `HCC38 / HCC1143` 上都存在

因此，当前更像是：

- HCC truth 中的 `canonical backbone` 本身具有很强的 shared component
- `shared_mean_baseline` 已经是一个很强的 backbone estimator

换句话说，复杂模型若想胜出，要求不是“学到额外结构”即可，而是必须同时做到：

1. 不丢掉 shared backbone
2. 再额外学到 deviation / context-specific structure

当前多数 entrant 更像只稳定做到了第 2 点，而没有稳定做稳第 1 点。

### 4.2 模型优化方向与主裁决方向错位

`GEARS` 当前最能说明这个问题：

- 它没有赢 backbone
- 但它赢了 `structure_vs_context_separation`
- 并且在部分 cell line 上更能识别 `shift-excess`

这里的 `shift-excess` 不等于 shared trend / overall displacement，而是超出 backbone 可解释部分的过度偏移或 context-specific deviation。

这说明它学到的不是“错误结构”，而是另一类结构：

- `shared structure vs context deviation` 的分离
- 一部分 `shift-excess`
- 更偏 context-sensitive 的 deviation

因此当前更稳的说法不是“复杂模型没学到东西”，而是：

**复杂 entrant 的优势方向，与当前 primary adjudication 最奖励的 backbone winner 方向不完全一致。**

### 4.3 backbone gap 更像方向失败，不像幅度失败

这一点由 ridge controls 支持得最清楚。

当前看到的是：

- `backbone_diagnosis.tsv` 中，多条 control 更接近 `direction`
- `top20_overlap` 没有全线崩掉
- 但 backbone cosine 很低、L2 很大

这说明：

- 模型不是完全碰不到相关基因
- 但恢复出来的表达变化主方向，与 frozen canonical backbone 不一致

因此更稳的解释是：

**当前主问题更像 `direction-level mismatch`，不是单纯的 amplitude insufficiency。**

### 4.4 这不是接入失败造成的假象

当前已经进入同一份 HCC comparison 的对象包括：

- `GEARS`
- `scGPT`
- `Geneformer`
- `lm_train_lowrank`
- `lm_G_scgpt_ridge`
- `lm_G_geneformer_ridge`

并且：

- export 已统一到 `stage2_truth_aligned_log_shift`
- contract validation 已跑通
- ridge coverage 已达到 `1.000`

因此当前 backbone gap 不再适合被解释为：

- entrant 还没正式接好
- export space 不一致
- target coverage 缺口

## 5. 当前只能写成 plausible biological interpretation 的解释

这一层可以写，但必须保持 lower-confidence boundary。

### 5.1 HCC 主 backbone 可能确实由强 shared program 主导

当前 frozen architecture 中最稳的一部分，可能确实更接近强 shared programs，例如：

- gene expression machinery
- transcription / chromatin
- RNA processing / translation

如果是这样，那么 baseline 能抓住很大一部分 backbone，不一定表示 baseline 更“懂 biology”，而更可能表示：

**当前主信号本身就很接近 cohort-level shared mean。**

这是一种 biological-facing interpretation，但当前还不是被独立证明的机制结论。

### 5.2 复杂模型可能更容易追逐 context deviation，而不是最共享的 backbone

从 biology 角度看，复杂模型可能更容易表达出：

- cell-line-specific rewiring
- nonlinear response
- local deviation
- shift-excess-like 结构

这些信号可能是真实 biological structure，但它们不一定是当前 truth-first freeze 后最主要、最稳定、最跨 context 可重复的 backbone。

因此会出现一种表面矛盾：

- 模型不是没有学到 biology
- 但模型学到的 biology，不是当前 primary adjudication 最奖励的那一部分 biology

### 5.3 gene-level semantic prior 不等于 perturbation backbone prior

foundation model embedding 可能编码了丰富的 gene-level prior。

但当前 Stage 2 需要恢复的，是：

- perturbation-induced
- context-constrained
- structure-level
- truth-aligned

的 backbone object。

因此：

- “embedding 很强”
- 不等于
- “target embedding + 线性头就能恢复 frozen backbone”

当前 ridge ablation 更像说明：

**gene semantic prior 存在，但它没有以当前使用方式稳定转成 backbone recovery。**

### 5.4 truth-first freeze 本身会压低一部分 biologically real 但更脆弱的信号

当前被冻结进入正式主张边界的对象，更偏：

- 跨 cutoff 稳定
- 跨 cell line 可桥接
- 能进入 evidence tier governance

因此，一些 biologically real 但更 context-specific、更脆弱、更不稳定的信号，会被有意压到：

- `supporting`
- `preliminary`
- `gated_downstream_layer`

如果复杂模型更擅长这类信号，也会导致：

- biology 上不是完全没价值
- 但 adjudication 上仍然输给 baseline

## 6. 当前明确不能写成什么

以下说法当前都不稳：

- 唯一 root cause 已经被证明
- 纯粹是 biology 原因
- 纯粹是 method 原因
- 只要改 training objective 就一定能超过 baseline
- 复杂模型学到的 deviation 一定比 baseline 更 biologically correct
- baseline 胜出说明复杂模型没有结构价值

## 7. 下次进来如果还想继续推进，先做什么

这部分最重要。下次不要空泛继续争论“模型到底为什么不行”，而应按下面顺序推进。

### 7.1 先固定解释边界

先读：

1. [`docs/why_models_do_not_stably_beat_baseline_v1.md`](/home/data/gz0705/WTKO/docs/why_models_do_not_stably_beat_baseline_v1.md)
2. [`docs/model_vs_baseline_deeper_explanation_note_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_deeper_explanation_note_v1.md)
3. [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)

目标不是再找新故事，而是先固定：

- 哪些属于 defendable methodological explanation
- 哪些只能保留为 plausible biological interpretation

### 7.2 再决定要补哪种验证

如果还想把解释往前推进，优先级应是：

1. **方法学验证优先**
   - 看看能否进一步确认 backbone gap 主要来自 `direction mismatch`
   - 看看 separation / deviation gain 与 backbone loss 是否形成稳定 trade-off frontier
2. **biology-facing interpretation 其次**
   - 把当前主 backbone 与 frozen axes / anchor tier 再对齐
   - 但不要把它升级成已证明机制

### 7.3 仍然不该做什么

- 不要为了“解释 baseline 为什么强”重新无限扩 entrant
- 不要回头重做 truth object
- 不要把 current note 写成 root-cause proof
- 不要在没有新增证据的前提下把 biology-facing interpretation 升成主结论

## 8. 推荐落点

如果要把这份 note 压成一句工作口径，最稳的版本是：

**下一步若继续推进，不是再问“模型为什么打不过 baseline”这个泛问题，而是把它拆成两个更小的问题：**

1. `baseline winner` 是否主要由 shared backbone objective 决定
2. entrant 的额外能力是否稳定落在 `separation / deviation` 而非 backbone 上

只有这两个问题都更清楚之后，biology-facing interpretation 才值得继续往前推进。

## 9. 渐进披露

默认先看：

1. [`docs/why_models_do_not_stably_beat_baseline_v1.md`](/home/data/gz0705/WTKO/docs/why_models_do_not_stably_beat_baseline_v1.md)
2. [`reports/stage2_real_hcc_smoke/model_comparison.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/model_comparison.tsv)
3. [`reports/stage2_real_hcc_smoke/backbone_diagnosis.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/backbone_diagnosis.tsv)
4. [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)

若要继续写作，再看：

- [`docs/main_manuscript_integrated_narrative_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_integrated_narrative_draft_v1.md)
- [`docs/main_manuscript_results_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_results_draft_v1.md)
- [`docs/project_state_summary_v1.md`](/home/data/gz0705/WTKO/docs/project_state_summary_v1.md)

## 10. 一句话收口

当前更稳的解释不是“模型不懂 biology”，而是“在一个 shared canonical backbone 很强的任务里，复杂模型学到的结构优势主要落在 backbone 以外，因此没有稳定转化成 primary winner”。
