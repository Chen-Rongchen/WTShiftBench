# 下一阶段执行口径 v1

## 1. 文档定位

这份文档只回答一个问题：

**当前这一轮主线结果收口之后，下一阶段到底该做什么，不该做什么？**

它不重写已有结果。它只把当前项目从“结果收口阶段”切到“缺口补齐阶段”的执行口径固定下来；若未来恢复 entrant expansion，也应以当前已完成的 `GEARS + scGPT + Geneformer + linear controls` 为冻结参照，而不是回到单模型起点。

## 2. 一句话执行口径

**下一阶段仍应优先补“比较、敏感性、混杂、最终边界、discovery 继续 gated”这五个缺口；entrant expansion 只在 frozen contract 下作为次级并行线推进。**

这五项是当前真正决定项目能否进入更稳 formal closure 的主线，而不是再接一个 entrant 或再开一轮 sweep。

但其中“比较”这条线现在必须继续细分。若还要追问“模型为什么打不过 baseline”，默认不再保留为泛问题，而应拆成：

1. `baseline winner` 是否主要由 shared backbone objective 决定
2. entrant 的额外能力是否稳定落在 `separation / deviation` 而不是 backbone 上

对应入口见：

- [`docs/model_vs_baseline_deeper_explanation_note_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_deeper_explanation_note_v1.md)
- [`docs/model_vs_baseline_next_step_breakdown_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_next_step_breakdown_v1.md)

## 3. 当前明确不做什么

下一阶段仍然明确不做：

- 无 contract freeze 的新 entrant
- 新 truth object
- 新评分体系
- 无停止规则的继续调 `GEARS`
- 在 `scGPT` 已完成首轮接入后，继续无停止规则地把 `Geneformer / challengers` 拉回 HCC primary mainline

原因很简单：这些动作不会关闭当前真正剩余的主线缺口，反而会把项目重新拖回 entrant engineering。

## 4. 下一阶段的五个正式缺口

### 4.1 比较

目标不是再多做几张比较表，而是把已有的 `fuller HCC model comparison` 真正并入最终主文稿叙事。

当前最需要补的是：

- 为什么 `shared_mean_baseline` 仍是 primary reference
- 为什么 `GEARS` 仍保留 architecture trade-off 的解释价值
- 为什么有限 sweep 暴露的是 `trade-off frontier`，而不是 hidden winner
- 为什么后续推进要收缩成两个更小的问题，而不是继续泛谈“模型为什么不行”

这一步的目标是把“模型比较”从局部结果说明，提升为主文中的正式解释层。

### 4.2 敏感性

当前 sensitivity 已不再只是 partial snapshot；主支柱与 control subsampling formal interval 已基本到位，但 full closure 仍未完成。

下一阶段需要做的不是再泛泛提“敏感性存在”，而是决定：

- 哪些 sensitivity 已经足够关闭并可正式引用
- 哪些 sensitivity 仍是实质风险
- 哪些 sensitivity 只能降级写成 remaining limitation

换句话说，这一步要把 sensitivity 从“待补”变成“已处理或已定性”。

### 4.3 混杂

当前剩余的主要方法学风险集中在 `covariate balance closure`。

下一阶段需要回答：

- 当前结构信号有多少可能被 covariate imbalance 放大或扭曲
- 哪些主张在混杂审计后仍然稳
- 哪些对象必须因为混杂风险而降级表述

这一步的目标不是追求“完全无风险”，而是把混杂风险治理到可写、可防守的程度。

当前这条线已经具备多轴、配置驱动、可汇总输出的正式入口，因此下一阶段的重点不再是“补脚本”，而是判断在现有元数据上限下，哪些主张还能保留、哪些必须继续降级。

### 4.4 最终边界

当前已经有一批中间边界文档，但还需要一个更终局的 claim boundary 收口。

下一阶段需要把这些问题彻底钉死：

- 哪些能写成 primary conclusion
- 哪些只能保留为 supporting / preliminary
- 哪些必须明确写成 supplementary / downstream
- 哪些仍然不能写成“model recovery has been demonstrated”

这一项决定的是整篇主文稿最后能写到哪里为止；当前更具体的动作，是把 `final claim matrix` 持续同步到 manuscript-ready wording、摘要式写法与入口文档。

### 4.5 discovery 继续 gated

discovery / phenotype shifter 现在仍不能直接写成 formal deliverable。

下一阶段需要固定的是：

- discovery 当前仍不满足进入正式交付的最低条件
- 在比较、敏感性、混杂、最终边界都足够稳定前，继续保持后置
- 当前只能写成 `gated_downstream_layer`，而不是待立即转正的 deliverable

也就是说，这一步要解决的不是“马上做 discovery”，而是“继续明确 discovery 还不能进入主线交付物”。

## 5. 推荐执行顺序

下一阶段建议按下面顺序推进：

1. 比较
2. 敏感性
3. 混杂
4. 最终边界
5. discovery 继续 gated

原因是：

- `比较` 决定当前结果怎样被解释
- `敏感性` 与 `混杂` 决定这些解释能不能站住
- `最终边界` 决定主文稿能写到哪里
- `discovery 继续 gated` 则确保下游应用想象不提前挤进 formal deliverable

## 6. 下次进来先做什么

如果下次只做一件事，先做：

**先确认当前阶段是否已经提交；若未提交，先按收口清单完成提交，再进入下一阶段。**

如果下次只读文件，按这个顺序看：

1. [`docs/finalization_punchlist_v1.md`](/home/data/gz0705/WTKO/docs/finalization_punchlist_v1.md)
2. [`docs/current_closeout_commit_note_v1.md`](/home/data/gz0705/WTKO/docs/current_closeout_commit_note_v1.md)
3. [`plan.md`](/home/data/gz0705/WTKO/plan.md)
4. [`docs/stage2_fuller_hcc_model_comparison_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_fuller_hcc_model_comparison_note_v1.md)
5. [`docs/why_models_do_not_stably_beat_baseline_v1.md`](/home/data/gz0705/WTKO/docs/why_models_do_not_stably_beat_baseline_v1.md)
6. [`docs/model_vs_baseline_deeper_explanation_note_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_deeper_explanation_note_v1.md)
7. [`docs/model_vs_baseline_next_step_breakdown_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_next_step_breakdown_v1.md)
8. [`docs/main_manuscript_results_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_results_draft_v1.md)
9. 当前 sensitivity / covariate 相关产物

如果后续决定继续 entrant expansion，不要直接回到 HCC 主线开跑；先看：

1. [`docs/model_expansion_deferral_note_v1.md`](/home/data/gz0705/WTKO/docs/model_expansion_deferral_note_v1.md)

## 7. 一句话收口

下一阶段的目标不是继续扩模型，而是把当前已经拿到的结构化结果真正补齐成一套可防守、可持续同步、但仍承认部分方法学缺口尚未 fully closed 的项目结论。
