# 当前阶段暂不扩模型说明 v1

## 1. 文档定位

这份文档只回答一个问题：

**为什么“当前阶段收口时”不继续把更多模型拉进 HCC Stage 2 primary mainline？**

它不否认多模型比较的重要性，也不把长期 entrant expansion 直接取消。它只固定“当前阶段收口时”的停止规则与延期理由。当前仓库状态已进一步推进到：`scGPT` 已完成正式接入，下一位候选 entrant 固定为 `Geneformer`。

## 2. 一句话结论

**当前阶段不继续无边界扩模型，不是因为仓库里只有 `GEARS`，而是因为当前主线瓶颈已经从 entrant engineering 转成了 claim governance、sensitivity 与 covariate closure。**

换句话说：

- 长期应继续做多模型比较
- 但当前阶段不应在 `scGPT` 已完成首轮接入后继续把 `Geneformer` 或其他 challenger 强行插回 HCC primary mainline

## 3. 当前为什么不适合继续扩模型

### 3.1 当前主线瓶颈不在 entrant 数量

当前项目已经进入“主张治理稳定化阶段”。

现在最需要关闭的缺口是：

- `fuller HCC model comparison` 的正式解释层
- `sensitivity full closure`
- `covariate balance closure`
- `final claim boundary`
- `discovery gating`

这些缺口决定的是当前结果能不能写成可防守的正式结论，而不是“再接一个 entrant 会不会更热闹”。

### 3.2 现在强行扩模型，测到的往往不是 architecture recovery

Stage 2 HCC adjudication 当前要求所有 entrant 都满足同一套 formal contract：

- `HCC38 / HCC1143` 各自有 scorer-ready prediction
- `prediction_space = stage2_truth_aligned_log_shift`
- target universe 与 gene space 通过 contract validation
- provenance 完整

若这些条件没有先冻结，那么新 entrant 进入 HCC 主线后，比较结果往往会混入：

- target coverage 不足
- gene mapping / tokenizer coverage 不足
- export recipe 不一致
- fallback 行为过强
- recipe 未冻结

这样比较出来的不是 architecture recovery，而是接入质量。

### 3.3 当前已经有足够回答主问题的核心比较

当前 HCC primary mainline 已经完成：

- `shared_mean_baseline`
- `GEARS`
- `null_model`
- 有限预算 `GEARS backbone sweep`

这已经足够回答一个关键问题：

**复杂 entrant 是否已经在 frozen architecture recovery 上压过简单强基线？**

当前答案是：

- `GEARS` 在 `structure/context separation` 上更强
- 但 `shared_mean_baseline` 在 `canonical_backbone recovery` 上仍更强

因此，当前不是“只测了一种模型所以什么都不知道”，而是“已经知道 entrant family 与简单强基线之间存在稳定 trade-off，但还没到需要把 entrant family 无限扩写的阶段”。

## 4. 为什么 `scGPT / Geneformer` 当前不该直接并入 HCC 主线

仓库里确实已经有：

- `scGPT` 的 Stage 1A smoke / adapter / runtime 资产
- `Geneformer` 的 Stage 1A smoke / adapter / runtime 资产

但这不等于它们已经具备 HCC Stage 2 primary adjudication 的 formal readiness。

当前更准确的状态是：

- 它们在 `Stage 1A` 语义下属于 `environment_ready_recipe_not_frozen`
- 已有本地 checkpoint、adapter/head 与 `predicted_shift` smoke 路径
- 但尚未冻结为 `HCC38 / HCC1143` 双 cell line、同一 scorer contract、同一 export contract 的 Stage 2 entrant

因此，当前不把它们拉回 HCC 主线，不是因为它们“不重要”，而是因为：

- 当前问题不是 foundation model 有没有可能有价值
- 当前问题是把不同 entrant 放到同一条可比路径上之前，必须先完成 contract freeze

## 5. 当前阶段不扩模型的正式收益

把 entrant expansion 延后，当前能带来三个直接收益：

1. 避免把项目重新拖回 entrant integration 泥潭
2. 避免用 coverage / export 问题污染 architecture adjudication
3. 让现有 `GEARS vs shared_mean_baseline` 的 trade-off 解释先稳定进入主文稿

## 6. 这不等于以后不做多模型

当前阶段暂不扩模型，不等于长期放弃多模型比较。

更稳的正式口径应是：

**多模型比较仍然重要，但应被后移到下一阶段，以“同 contract、同 scorer、同 target universe、同 provenance”的方式作为独立工作包推进。**

## 7. 什么时候才适合恢复 entrant expansion

只有当以下条件基本满足时，继续扩模型才是稳的：

1. `fuller HCC model comparison` 已并入主文稿
2. `sensitivity` 已完成 closed / risk / limitation 分层
3. `covariate balance` 已从“已有审计”推进到“正式边界已固定”
4. `final claim boundary` 已钉死 allowed / disallowed wording
5. 新 entrant 能复用同一套 HCC Stage 2 contract，而不是临时例外接入

## 8. 推荐写法

如果需要在主文或执行说明中压成一句话，最稳的写法是：

当前阶段暂不继续扩模型，并非因为仓库缺少其他 entrant 候选，而是因为当前主线瓶颈已经转向 claim governance、sensitivity 与 covariate closure。现阶段若在 HCC primary mainline 中继续强并 `scGPT / Geneformer` 或其他 challenger，更可能测到 coverage、export 与 contract 不一致，而不是 architecture recovery 本身。因此，多模型扩展应后移到下一阶段，在统一的 HCC Stage 2 contract 下作为独立工作包推进。

## 9. 渐进披露

默认先看：

1. [`docs/stage2_fuller_hcc_model_comparison_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_fuller_hcc_model_comparison_note_v1.md)
2. [`docs/next_phase_execution_note_v1.md`](/home/data/gz0705/WTKO/docs/next_phase_execution_note_v1.md)
3. [`docs/stage2_hcc_prediction_contract.md`](/home/data/gz0705/WTKO/docs/stage2_hcc_prediction_contract.md)
4. [`docs/project_state_summary_v1.md`](/home/data/gz0705/WTKO/docs/project_state_summary_v1.md)

若要继续 entrant 盘点，再看：

- [`docs/next_stage_model_entrant_inventory_v1.md`](/home/data/gz0705/WTKO/docs/next_stage_model_entrant_inventory_v1.md)
