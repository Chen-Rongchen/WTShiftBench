# 主文稿整合叙事草案 v1

## 1. 文档定位

这份文档不是新 protocol，也不是新结果生成脚本说明。

它只做一件事：

**把当前已经分别收口的 `GEARS adjudication`、`truth bridge`、`axis annotation / validation`、`Dixit supplementary replication` 与 `Stage 1A / 1B failure decomposition`，压成一份可继续进入主文写作的统一叙事草案。**

当前文档坚持三个原则：

- 不重写已经冻结的 truth object
- 不把 supplementary 对象升格为 HCC primary conclusion
- 不把 supporting / preliminary evidence 上升为与 primary evidence 同等级的结构性主张

## 2. 当前总括性结论

当前最稳的总体结论是：本项目已经完成从“现象级相关”到“分层化结构证据”的第一轮收口，但尚未完成对 model recovery 的最终证明。

更具体地说，当前阶段已经形成一组边界清晰、层级分明的主张：

- 在模型侧，`GEARS` 已完成 HCC primary adjudication，其结果应被写成 `architecture trade-off diagnosis`，而不是继续优化的主推进对象。
- 在 truth-side bridge 层，`truth–DepMap bridge` 已不再只是整体相关现象，而是由少数结构上稳定的 `target-level anchors` 与有限 `formal axis evidence` 共同支撑的结构化 bridge。
- 在 axis 层，第一轮 `annotation + validation + tiering` 已完成，但整体仍应保持 `partially supported axes`，而不是 `fully established shared explanatory architecture`。
- 在 supplementary 层，`Dixit/K562` 支持 architecture existence 在外部 context 中具有一定可复制性，但其 dominant macro-class remains context-specific。
- 在 benchmark 解释层，`Stage 1A / 1B` 不再只承担 leaderboard / stress test 角色，而应被重写为 frozen truth architecture 下的 `failure decomposition track`。

因此，当前阶段最重要的进展不是信号数量继续增加，而是 `evidence tier` 与 `claim strength` 已经被明确对齐。

## 3. HCC primary adjudication：GEARS 作为 architecture trade-off diagnosis

在当前 HCC primary 路线中，`GEARS` 已完成 entrant-qualified smoke、contract validation 与有限预算 backbone sweep。

当前最稳的结论不是“GEARS 还可以继续调到更好”，而是：

> GEARS 展现出选择性结构优势：它更擅长把 structure 和 context deviation 分开，并在部分 cell line 上更能识别 shift-excess；但在当前 HCC primary adjudication 中，canonical backbone recovery 仍落后于 `shared_mean_baseline`。

这意味着，`GEARS` 当前更适合作为一个 `architecture-level trade-off diagnosis` 对象：

- 它能够恢复部分 backbone-related structure
- 它在 `structure/context separation` 上表现出选择性优势
- 但其收益与 `canonical_backbone recovery` 的代价并不对称
- 当前证据不足以支持重新开启无停止规则的 entrant sweep

因此，`GEARS` 在本阶段应被定位为“已完成诊断的代表性 entrant”，而不是“待继续优化的主推进对象”。

需要进一步强调的是，当前更复杂的 entrant 之所以不能稳定胜过 `shared_mean_baseline`，并不应被简单解释为“模型没有正式接入”或“export / coverage 出错”。截至当前版本，`GEARS / scGPT / Geneformer / lm_train_lowrank / lm_G_scgpt_ridge / lm_G_geneformer_ridge` 都已经进入同一份 HCC formal comparison；其中，两条 ridge control 的 target coverage 也均已达到 `1.000`。因此，更稳的解释是：当前 HCC task 中的 `canonical backbone` 本身具有很强的 shared component，而 `shared_mean_baseline` 已能有效捕获这部分主结构。相比之下，复杂 entrant 学到的额外能力更倾向于 `structure/context separation`、`shift-excess identification` 或 context-sensitive deviation，而这些优势并未稳定转化为更强的 backbone recovery。进一步地，pretrained target embedding 的线性 ablation control 表明，冻结 embedding 单独拿出来并不足以稳定恢复 backbone 主方向，因此当前 backbone gap 更像是 `direction-level mismatch`，而不是单纯的 amplitude insufficiency。换句话说，当前最稳的结论不是“复杂模型没有结构价值”，而是“它们的结构优势方向，与当前 adjudication 中最难超越的 shared canonical backbone 并不完全对齐”。

如果后续还要继续推进这条解释线，当前也不应再把问题写回泛泛的“模型为什么打不过 baseline”。更稳的下一步拆法是只追问两个更小的问题：第一，`baseline winner` 是否主要由 shared backbone objective 决定；第二，entrant 的额外能力是否稳定落在 `separation / deviation` 而不是 backbone 上。在这两个方法学问题进一步收紧前，biology-facing interpretation 仍只应保留为 plausible layer。

若需要将这一步进一步压成 manuscript-ready wording，可直接写成：后续工作不再把 baseline-vs-model gap 保留为开放式泛问题，而是优先收紧为两个方法学问题，即 `baseline winner` 是否主要由 shared backbone objective 决定，以及 entrant 的额外能力是否稳定落在 `structure/context separation` 与 deviation-related structure，而非更强的 backbone recovery；在此之前，biology-facing interpretation 仍应停留在 plausible layer。

## 4. Truth–DepMap bridge：stable anchors 与 limited formal axis evidence

当前 `truth–DepMap bridge` 的最稳写法，已经不应停留在“整体相关性存在”这一层，而应被表述为一个具有双层结构的 truth-side object。

第一层是 `target-level joint bridge`。在这一层，当前最稳的结构性 shared anchors 包括：

- `PFDN5`
- `PMF1`
- `PRPF6`
- `ZNF131`

这些 anchors 的意义不在于“单个基因变化大”，而在于它们在 transcriptomic impact 与 cellular dependency 上共同保持高位，并且在 cutoff sensitivity 审计下维持相对稳定的 anchor 身份。

需要补充的是，当前 covariate audit 已经进一步表明：`structural stability` 与 `covariate cleanliness` 不能混写。也就是说，这四个对象当前更准确的角色是 `structurally stable anchors`，而不是已经 fully deconfounded 的最强对象级证据。其中，`PFDN5` 最多只能写成 `primary_but_qualified`；`PMF1`、`PRPF6` 与 `ZNF131` 则应明确写成 `supporting_only`，不再承担 anchor-level strongest wording。

更重要的是，当前混杂线的正式状态应被写成：**已完成第一轮多轴 covariate audit，并据此完成对象级降级治理，但 full closure 仍受实验设计元数据上限约束。** 这一步支持的是 claim governance 的稳定化，而不是把 stable anchors 升级回 fully deconfounded objects。

第二层是 `axis-level explanatory structure`。这一层当前证据明显更保守：

- `formal axis evidence` 总体仍然有限
- `transcription / chromatin` 是目前唯一同时满足 formal criteria 且在 bootstrap 下保持稳定的正向 axis
- 多数其余 axis 仍应停留在 supporting、unstable 或 preliminary 层级

因此，当前结果支持的是“存在可治理、可分层的 truth–DepMap bridge structure”，而不是“shared explanatory architecture 已全面建立”。

## 5. Axis interpretation：partially supported axes，而非 fully closed architecture

当前 frozen axis 已完成第一轮 `annotation + validation + tiering`，这是这一阶段非常关键的收口动作。

但这一步的价值不应被误写成“所有轴都已经 fully closed”。更稳的写法是：

- 多数 frozen axes 已获得部分支持
- 支持强度并不均匀
- 少数 axis 可以进入更强的 formal / primary 层级
- 其余 axis 仍应保持 supporting 或 preliminary 状态

当前相对更稳的 axis 包括：

- `transcription / chromatin`
- `chromatin remodeling`
- `TGF-beta / BMP signaling`
- `ER stress / UPR`
- `RNA processing / spliceosome`
- `ribosome biogenesis / nucleolar`
- `ribosomal / translation`

其中，`transcription / chromatin` 是当前最稳的一条 formal positive axis，但最多只能写成 `primary_axis_but_qualified`；其它 axis 虽然获得了方向一致的注释或一致性支持，但多数还不足以升级为 fully established functional axes。

因此，当前 axis 层最重要的成果不是“闭合了一个完整模块架构”，而是完成了第一轮 `annotation`、`validation` 与 `evidence tiering`，使哪些轴可以写得更强、哪些轴必须保持保守，已经具备清晰边界。

## 6. SCP542 与 Dixit/K562：解释边界与 supplementary replication

当前 `SCP542` 与 `Dixit/K562` 已经分别被明确压到各自合适的位置，二者不能混写。

`SCP542` 的角色是 `explanation boundary`：

- 它支持 distributed / high-plasticity basal program 的解释边界
- 它不支持把某条 backbone 轴锚定为单一 global program
- 它也不能被用来解释 `K562` 的结构复现

`Dixit/K562` 的角色则是 `supplementary external structure replication`：

- `K562` 中同样可以观察到 `canonical backbone`
- `K562` 中同样可以观察到 `shift-excess`
- 但其 dominant backbone 更偏 `biosynthetic support / mitochondrial metabolism`
- 因而它支持的是 architecture existence 的外部复现，而不是与 HCC 对称的主线 architecture

按当前更正式的 supplementary tiering 口径：

- `architecture existence` 与 `canonical backbone present` 可保留为 `supplementary_confirmed`
- `shift-excess present` 与 context-specific backbone macro class 更适合保留为 `supplementary_supporting`
- `shift-excess macro class` 以及多数单条 K562 axis 仍应保持 `preliminary`

因此，当前最稳的写法应始终是：

**supplementary replication supports architecture existence, but the dominant macro-class remains context-specific.**

## 7. Stage 1A / 1B：failure decomposition track

在当前 truth-first 主线下，`Stage 1A / 1B` 的解释角色已经改变。

`Stage 1A` 不再只是 leaderboard，而应被理解为 `short-horizon failure decomposition`：

- 模型是否连短期 backbone 都无法稳定恢复
- 模型是否能拟合 shared mean trend，却丢掉 `shift-excess`
- 模型是否把 context-specific deviation 平均化抹平

`Stage 1B` 不再只是 time-aligned stress test，而应被理解为 `long-horizon / temporal failure decomposition`：

- short-horizon 中已出现的 failure mode 是否在 long horizon 进一步放大
- 是否出现 `temporal structure degradation`
- backbone、shift-excess 与 context specificity 中哪一部分最先失稳

因此，`Stage 1A / 1B` 当前最重要的价值，不是继续提供脱离结构语义的排名，而是为 `Stage 2` 的 architecture adjudication 提供失败类型解释层。

## 8. 当前主张边界

当前主文稿必须明确避免以下 overclaim：

- 把 `GEARS` 写成已经整体压过 `shared_mean_baseline`
- 把 `truth–DepMap bridge` 写成已经全面建立的 shared explanatory architecture
- 把 stable shared anchors 写成已经 fully deconfounded 的 strongest evidence
- 把多数 frozen axes 写成同等级、同稳健性的正式闭环
- 把 `Dixit/K562` 写成与 HCC 并列的 primary biological conclusion
- 把 `Stage 1A / 1B` 写回只服务 leaderboard / stress test，或反过来写成新的 truth-discovery 层
- 把 global Pearson 或单次分数波动替代 architecture-level adjudication

当前结果支持的是：

- `GEARS` 的 architecture trade-off diagnosis
- 少数结构上稳定、但需分层书写的 anchors
- 有限 formal axis evidence
- 部分得到支持的 axis 解释框架
- supplementary-level architecture replication
- architecture-aware failure decomposition framing

而不是更强版本的“model recovery 已被证明”。

## 9. 可直接进入主文的总收口段

综合当前结果，我们认为本项目已经完成从“现象级相关”到“分层化结构证据”的第一轮收口。首先，在模型侧，`GEARS` 已完成 HCC primary adjudication，其结果更适合被解释为 `architecture trade-off diagnosis`，而不是继续扩模或继续调参的起点；同时，`scGPT / Geneformer / linear controls` 的并入进一步表明，当前 backbone gap 更像是 task structure 与 entrant inductive bias 之间的错位，而不是接入错误或 coverage 缺口。其次，在 truth-side bridge 层，`truth–DepMap bridge` 已不再只是整体相关现象，而是可进一步分解为少数跨 cutoff 稳定的 `target-level anchors` 与有限的 `axis-level formal evidence`；其中，当前可进入更强写法的对象只包括 `PFDN5 = primary_but_qualified` 与 `transcription / chromatin = primary_axis_but_qualified`，而 `PMF1 / PRPF6 / ZNF131` 以及多数其余 axis 仍应保留在 `supporting_only`、supporting、unstable 或 preliminary 层级。当前 covariate audit 进一步提示，这些 anchor 代表的是 `structural stability`，而不是统一意义上的 `fully deconfounded strongest evidence`。第三，frozen axis 已完成第一轮 `annotation + validation + tiering`，从而形成了一套部分得到支持的轴级解释框架，但当前证据仍不足以支撑 `fully established shared explanatory architecture` 的更强主张。第四，`Dixit/K562` 提供了 supplementary external structure replication，支持 architecture existence 在外部 context 中具有一定可复制性，但其 dominant macro-class remains context-specific，因而不能被提升为与 HCC 并列的 primary conclusion。最后，`Stage 1A / 1B` 当前不再只是 leaderboard 与时间外推 stress test，而应被重新解释为 frozen truth architecture 下的 failure decomposition track，用于说明模型究竟丢掉了哪类结构、这些 failure mode 是否在更长时间尺度上进一步放大。整体而言，本阶段最重要的进展不是信号数量的增加，而是 evidence tier、claim strength 与 model-failure explanation 的成功对齐，从而使主结论更加清晰、可信且可防守。

## 10. 渐进披露

默认先看：

1. [`plan.md`](/home/data/gz0705/WTKO/plan.md)
2. [`docs/stage2_truth_bridge_integrated_result_v1.md`](/home/data/gz0705/WTKO/docs/stage2_truth_bridge_integrated_result_v1.md)
3. [`docs/stage2_dixit_supplementary_evidence_tier_v1.md`](/home/data/gz0705/WTKO/docs/stage2_dixit_supplementary_evidence_tier_v1.md)
4. [`docs/stage1_failure_decomposition_note_v1.md`](/home/data/gz0705/WTKO/docs/stage1_failure_decomposition_note_v1.md)

若要下钻，再看：

- [`reports/stage2_gears_backbone_sweep/final_adjudication.md`](/home/data/gz0705/WTKO/reports/stage2_gears_backbone_sweep/final_adjudication.md)
- [`reports/stage2_truth_bridge_decomposition/bridge_decomposition_report.md`](/home/data/gz0705/WTKO/reports/stage2_truth_bridge_decomposition/bridge_decomposition_report.md)
- [`reports/stage2_axis_analysis/axis_validation_summary.md`](/home/data/gz0705/WTKO/reports/stage2_axis_analysis/axis_validation_summary.md)
- [`reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_evidence_tier_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_evidence_tier_summary.tsv)
- [`docs/model_vs_baseline_next_step_breakdown_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_next_step_breakdown_v1.md)
