# Stage 2 fuller HCC model comparison note v1

## 1. 文档定位

这份文档只做一件事：

**把当前 HCC primary adjudication 中已经存在的模型比较结果，压成一份更清楚的解释层说明。**

它不引入新 entrant，不重开新一轮 sweep，也不升级辅助指标为新的主裁决层。
它服务的是当前 manuscript wording 的比较层同步，而不是把比较层重新扩成独立 discovery 任务。

## 2. 当前为什么需要 fuller model comparison

当前 `GEARS` 的主裁决已经收口为 `architecture trade-off diagnosis`。但如果只保留一句“GEARS 没赢 backbone”，仍然不足以解释：

- 它到底输在什么维度
- 它到底赢在什么维度
- sweep 候选的改善为什么没有转化为 primary winner

因此需要一个更 fuller 的比较层，把现有 `model_comparison.tsv` 中已经存在的结果解释清楚，并把 `shared_mean_baseline = primary reference` 与 `GEARS = architecture trade-off diagnosis` 这两条正式口径钉死。

## 3. 当前比较对象

当前最重要的比较对象不是“所有可能模型”，而是当前 HCC primary 路线中已经正式出现的这些对象：

- `shared_mean_baseline`
- `gears_hcc_formal_v1`
- `scgpt_hcc_formal_v1`
- `geneformer_hcc_formal_v1`
- `lm_train_lowrank_hcc_formal_v1`
- `lm_g_scgpt_ridge_hcc_formal_v1`
- `lm_g_geneformer_ridge_hcc_formal_v1`
- 若干有限预算 `GEARS` backbone sweep 候选
- `null_model`

这个比较层当前回答的是：

1. `shared_mean_baseline` 为什么仍是 primary reference
2. `GEARS` 为什么仍值得保留为结构诊断对象
3. foundation-model entrant 与线性 control 各自保住了什么、丢掉了什么
4. sweep 候选为什么不能被解释成“只差一轮就能赢”

## 4. 当前最稳的比较结论

### 4.1 primary reference 仍然是 `shared_mean_baseline`

跨细胞系均值上，`shared_mean_baseline` 的 `backbone_recovery_score = 0.8067`，而正式 `GEARS` recipe 为 `0.6600`。同时，在辅助解释层，`shared_mean_baseline` 也表现出更高的 `cosine_similarity_mean = 0.1580`、更低的 `l2_distance_mean = 0.4883` 以及更高的 `top20_overlap_mean = 0.5697`。

这说明：如果问题是“谁在整体上更接近当前 truth backbone”，那么 `shared_mean_baseline` 仍然是更强的 primary reference。

### 4.2 `GEARS` 的价值在于 structure/context separation，而不是整体贴近度

正式 `GEARS` recipe 的 `structure_vs_context_separation_score = 0.4284`，高于 `shared_mean_baseline` 的 `0.3526`。在 cell-line level 上，这一优势在 `HCC38` 和 `HCC1143` 上都存在。与此同时，`GEARS` 在 `HCC1143` 上表现出更强的 `shift-excess identification`。

因此，`GEARS` 的价值不在于“整体更接近 truth”，而在于它更容易把 shared backbone 与 context deviation 分开，并在部分 context 中更能识别 shift-excess。也正因如此，`GEARS` 不能被简单写成“比 baseline 差”，而应被写成 `architecture-level trade-off diagnosis`。

### 4.3 sweep 候选暴露出的是 trade-off frontier，而不是 hidden winner

有限 sweep 中，一些候选在 `shift_excess_identification_score` 或 `structure_vs_context_separation_score` 上继续上升。例如：

- `gears_hcc_formal_v1_e30_lr2e-03_wd1e-06`
  - `shift_excess_identification_score = 0.8333`
  - `structure_vs_context_separation_score = 0.4485`
  - 但 `backbone_recovery_score = 0.6433`
- `gears_hcc_formal_v1_e30_lr1e-03_wd1e-05`
  - `shift_excess_identification_score = 0.9167`
  - 但 `backbone_recovery_score = 0.6133`
- `gears_hcc_formal_v1_e40_lr1e-03_wd1e-06`
  - `structure_vs_context_separation_score = 0.4684`
  - 但 `backbone_recovery_score = 0.4933`

这类结果说明的不是“再调一轮就会赢”，而是：当前 sweep 更像是在同一条 trade-off frontier 上移动。也就是说，某些 recipe 可以进一步强化 `shift-excess identification` 或 `structure/context separation`，但这种改善没有转化为对 backbone recovery 的补强，反而经常伴随 backbone 表现的下降。

因此，当前最稳的解释不是存在一个被漏掉的 hidden winner，而是当前 entrant family 确实表现出相对稳定的 `backbone vs separation` trade-off。

### 4.4 foundation-model entrant 与线性 control 提供了解释层，而不是新的 winner

当前 supplementary entrant/control 层显示出一个更清楚的分层：

- `Geneformer` 本体：`backbone_recovery = 0.5333`，`shift_excess_identification = 0.7500`，`structure_vs_context_separation = 0.4012`
- `scGPT` 本体：`backbone_recovery = 0.4467`，`shift_excess_identification = 0.3333`，`structure_vs_context_separation = 0.2948`
- `lm_train_lowrank`：`backbone_recovery = 0.5367`，`shift_excess_identification = 0.5833`，`structure_vs_context_separation = 0.2862`
- `lm_g_geneformer_ridge`：`backbone_recovery = 0.6267`，`shift_excess_identification = 0.1667`，`structure_vs_context_separation = 0.3257`
- `lm_g_scgpt_ridge`：`backbone_recovery = 0.4667`，`shift_excess_identification = 0.1667`，`structure_vs_context_separation = 0.2590`

这组结果最重要的解释不是谁形成了新 winner，而是：

- `Geneformer` 本体比 `scGPT` 本体更强，但 backbone 仍明显弱于 baseline
- `lm_g_geneformer_ridge` 能保住一部分 backbone，但几乎丢掉了 shift-excess 识别
- `lm_g_scgpt_ridge` 与 `lm_train_lowrank` 都没有形成 stronger backbone winner

因此当前更稳的 entrant family 解释是：

- backbone 更强的仍然是 `shared_mean_baseline`
- separation 更强的代表仍然是 `GEARS`
- foundation-model 本体与其 embedding ablation control 之间存在明显 trade-off
- 这些 control 的价值在于解释 entrant family 的行为，而不是改写 primary adjudication

## 5. 当前不应如何解读这些比较结果

以下几种写法当前都不稳：

- “GEARS 整体输给 baseline，所以没有结构价值”
- “某个 sweep 候选在 shift-excess 上更强，因此应该成为新 primary winner”
- “某个 linear control 在某一项不差，因此 foundation-model 已不再有解释价值”
- “辅助指标一度改善，因此 backbone gap 已接近关闭”
- “现有模型比较已经证明 model recovery 成立”

当前更稳的理解是：

- `shared_mean_baseline` 仍是 backbone 更强的 primary reference
- `GEARS` 仍是 structure/context separation 更强的代表性 entrant
- foundation-model entrant 与 linear controls 暴露的是 entrant family 内部 trade-off
- sweep 暴露的是 trade-off frontier，而不是可立即翻盘的 recipe

## 6. 推荐写法

如果要把 fuller HCC model comparison 压成一段主文档解释，最稳的说法是：

当前 HCC primary adjudication 显示，`shared_mean_baseline` 仍然是 backbone recovery 更强的 primary reference，而 `GEARS` 则表现出更明显的 `structure/context separation` 优势，并在部分 context 中更能识别 `shift-excess`。有限预算 sweep 进一步表明，现有 `GEARS` entrant family 的主要变化更像是在同一条 `backbone vs separation` trade-off frontier 上移动：若干候选可以继续提高 shift-excess identification 或 separation，但这些改善并未转化为 backbone recovery 的补强。因此，当前 fuller model comparison 支持的不是“GEARS 只差一轮调参即可胜出”，而是“不同 entrant behavior 所揭示的 architecture-level trade-off 已经具有足够稳定的解释价值”。

## 7. 渐进披露

默认先看：

1. [`reports/stage2_real_hcc_smoke/adjudication_summary.md`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/adjudication_summary.md)
2. [`reports/stage2_real_hcc_smoke/model_comparison.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/model_comparison.tsv)
3. [`reports/stage2_gears_backbone_sweep/final_adjudication.md`](/home/data/gz0705/WTKO/reports/stage2_gears_backbone_sweep/final_adjudication.md)

若要解释为什么当前阶段不继续扩 entrant，或下一阶段如何恢复 entrant expansion，再看：

4. [`docs/model_expansion_deferral_note_v1.md`](/home/data/gz0705/WTKO/docs/model_expansion_deferral_note_v1.md)
5. [`docs/next_stage_model_entrant_inventory_v1.md`](/home/data/gz0705/WTKO/docs/next_stage_model_entrant_inventory_v1.md)
6. [`docs/next_stage_model_entrant_execution_checklist_v1.md`](/home/data/gz0705/WTKO/docs/next_stage_model_entrant_execution_checklist_v1.md)
