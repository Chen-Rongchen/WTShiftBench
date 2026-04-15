# 主文稿 Results 草案 v1

## Abstract

我们提出并验证了一个 truth-first architecture-aware 框架，用于评估扰动应答转录组模型能否恢复可桥接到 DepMap CRISPR 适应度的结构化 truth object。核心发现是：当前的 perturbation foundation model 在 canonical backbone recovery 上尚未稳定胜过共享均值基线，暴露了一种非对称 architecture trade-off——模型的优势更偏向于 structure/context separation 而非 backbone 主方向的精确拟合。在 HCC38/HCC1143 两条 primary cell line 中，共享均值基线的 backbone recovery（ρ̄=0.807）持续优于正式 GEARS recipe（ρ̄=0.660），而 GEARS 在 structure-vs-context separation 上反超（0.428 vs 0.353）。HCC 主线 anchors（PFDN5、PMF1、PRPF6、ZNF131）在 transcriptomic shift 与 DepMap dependency 上共同维持高位，但经五轴 covariate audit 后仅 PFDN5 可保留为 `primary_but_qualified`；`transcription / chromatin` 是 bootstrap 下唯一稳定的 formal positive axis。GSE90063 K562 13d/7d temporal panel 在外部 context 下确认了 `backbone + shift-excess` architecture form 的时间稳定性（7d rank alignment 更强；13d mean shift 更大），提供了 supplementary-level architecture-form support（A0 confirmed / A1 supporting / B not eligible）。跨四个 context（HCC38/HCC1143/K562 7d/K562 13d）的 endpoint hierarchy 显示 CRISPR DepMap（bridge Spearman 0.51–0.78）一致强于 RNAi DEMETER2（0.28–0.38），确立 CRISPR 为 formal primary bridge readout，RNAi 为 weaker cross-platform sensitivity endpoint。当前结果不支持 "model recovery proved"，不支持 GEARS 整体压过共享均值基线，也不支持 K562 作为 HCC 对称的 primary co-pillar 或 content-level replication。

## 1. Result 1：GEARS 在 HCC primary adjudication 中表现为 architecture trade-off diagnosis，而非 primary winner

我们首先评估了当前 strongest formal entrant `GEARS` 在 `HCC38 / HCC1143` 真实 HCC mainline 中对 frozen architecture 的恢复能力。当前结果不支持将 `GEARS` 写成 HCC primary 路线上的整体胜者。相反，更稳的解释是：`GEARS` 展现出选择性结构优势，但其主要价值在于揭示 architecture-level trade-off，而不是整体压过 `shared_mean_baseline`。

具体来说，`GEARS` 在 `structure vs context separation` 上稳定优于 `shared_mean_baseline`，并在 `HCC1143` 上表现出更强的 `shift-excess identification`；然而，在两个 cell line 上，`canonical_backbone recovery` 均仍落后于 `shared_mean_baseline`。跨细胞系均值上，`shared_mean_baseline` 的 backbone recovery 为 `0.807`，而正式 `GEARS` recipe 为 `0.660`；相对地，`GEARS` 的 structure-vs-context separation 为 `0.428`，高于 `shared_mean_baseline` 的 `0.353`。因此，`GEARS` 当前更像一个 `structure/context separation` 偏置的 entrant，而不是 backbone recovery 更强的主胜者。

在外部 `K562 13d` 最小 model-side 审计中，这一模型侧架构 trade-off 只得到部分复现：`shared_mean_baseline` 再次在 backbone recovery 上占优，而 `GEARS` 仍在 structure-vs-context separation 上更强；但 `shift-excess` 分量未得到复现。因此，当前外部结果可写成 `partial recurrence / partial-support`，而不能写成 full three-component recurrence 或 external model-side generalization 已建立。在 `K562 13d` 与 `K562 7d` 两个时间点对全部 6 个 entrant（`GEARS`、`scGPT`、`Geneformer`、`lm_train_lowrank`、`lm_g_scgpt_ridge`、`lm_g_geneformer_ridge`）的 leave-one-target-out bridge 评估进一步显示（Supplementary Table S7）：所有 embedding-based entrants 在 7d 的平均 bridge Spearman（0.476–0.520）一致高于 13d（0.349–0.373），而 `GEARS` 在两个时间点均表现最弱（13d ρ̄=0.127，7d ρ̄=0.093）；这一 temporal 模式与 Result 4 中 bridge readout 的 temporal stratification 解释一致。因此，`GSE90063 K562 13d/7d temporal panel` 的 entrant 层同时支持 architecture form 的时间稳定性与 bridge readout 的 temporal stratification，但同样不应把 `7d` 升级为第二个 primary external replication。

在完成有限预算 backbone sweep 后，这一判断进一步稳定。虽然若干 sweep 候选继续提升了 `shift-excess identification` 或 `structure vs context separation`，但没有任何候选接近或追平 `shared_mean_baseline` 的 backbone recovery，也没有候选超过当前正式 `GEARS` recipe 的 backbone 表现。预先冻结的 stop rule 因而被触发，使 `GEARS` 在本阶段的最合理定位收敛为 `architecture trade-off diagnosis`。

更重要的是，这一 backbone gap 当前不能再简单归因于 entrant 尚未正式接入。到目前为止，`GEARS / scGPT / Geneformer / lm_train_lowrank / lm_G_scgpt_ridge / lm_G_geneformer_ridge` 均已进入同一份 HCC formal comparison，两条 embedding ablation control 也已经实现 `1.000` target coverage。当前更稳的解释是：HCC task 中的 `canonical backbone` 本身具有很强的 shared component，因此 `shared_mean_baseline` 已经是一个很强的 backbone estimator；相比之下，复杂 entrant 所学习到的额外能力更倾向于 `structure/context separation`、`shift-excess identification` 或 context-sensitive deviation，而这些优势并未稳定转化为更强的 backbone recovery。与此一致，`lm_G_scgpt_ridge` 与 `lm_G_geneformer_ridge` 的 backbone failure 都更接近 `direction`，说明当前 gap 更像是 backbone 主方向恢复偏弱，而不是单纯的幅度不足。

因此，若后续仍要继续推进这条解释线，更稳的默认口径也不再是重复问“模型为什么打不过 baseline”，而是先把两个更小的问题钉死：`baseline winner` 是否主要由 shared backbone objective 决定，以及 entrant 的额外能力是否稳定落在 `separation / deviation` 而不是 backbone 上。在这两点没有进一步收紧前，biology-facing explanation 仍不应升级成主结论。

更短的 Results-style 写法可以直接固定为：后续对 baseline-vs-model gap 的推进应优先聚焦于两个方法学问题，即 `baseline winner` 是否主要由 shared backbone objective 决定，以及 entrant gain 是否主要落在 `separation / deviation` 而非 backbone；在此之前，biology-facing explanation 仍只应保留为 plausible interpretation。

## 2. Result 2：truth–DepMap bridge 可分解为 stable target-level anchors 与 limited formal axis evidence

在 truth-side，我们将原先较粗的整体 bridge 现象进一步分解为两个递进层次。第一层是 `target-level joint bridge`，即 transcriptomic impact 与 aligned dependency 同时处于高位的少数结构上稳定 anchors。当前最稳的 shared anchors 包括 `PFDN5`、`PMF1`、`PRPF6` 与 `ZNF131`。这些对象的重要性不在于单基因幅度本身，而在于它们在多组 cutoff 设定下持续保持 anchor 身份，并支持 transcriptomic impact 与 cellular dependency 之间存在结构化耦合。需要同时强调的是，当前 covariate audit 已显示：`structural stability` 与 `covariate cleanliness` 不能简单等同，因此这些对象当前更适合作为分层化 bridge evidence，而不是统一意义上的 fully deconfounded strongest anchors；其中，`PFDN5` 最多只能写成 `primary_but_qualified`，而 `PMF1 / PRPF6 / ZNF131` 当前只能写成 `supporting_only`。与此同时，混杂线当前更准确的状态应写成：已完成第一轮多轴 covariate audit，并已据此完成对象级降级治理；当前五条已落盘 covariate 轴覆盖一条 `barcode_gem_group` 设计层代理轴、两条 protospacer 轴与两条 transcriptome 轴，风险已治理进边界，但 full closure 仍受实验设计元数据上限约束。对这条 design-layer 代理轴的进一步追查已经收口：当前只可确认 `HCC38 -> aggrMH001-3` 与 `HCC1143 -> aggrMH004-6`，不能继续写成单个 `MH00x` 已确认的 run-level covariate。最新版正式重跑并没有进一步改写这些 anchor 的 tier；新增设计层代理轴与 transcriptome 轴整体更轻，但没有把这些对象升级为 fully deconfounded strongest anchors，它坐实的是当前边界，而不是新的对象级升级。

第二层是 `axis-level explanatory structure`。与 target-level anchors 相比，这一层当前证据明显更保守。按照 `n_targets >= 2` 的 formal call 约束以及 bootstrap stability 审计，当前 formal axis evidence 总体仍然有限。其中，`transcription / chromatin` 是目前唯一同时满足 formal criteria 且在 bootstrap 下保持稳定的正向 axis，但当前最多只能写成 `primary_axis_but_qualified`；其余 axis 多数仍应保留为 supporting、unstable 或 preliminary lines of evidence。因而，当前结果支持的是“存在可治理、可分层的 truth–DepMap bridge structure”，而不是“多数 axis 已完成正式闭环”或“shared explanatory architecture 已全面建立”。

## 3. Result 3：frozen axis 已完成第一轮 annotation 与 validation，但整体仍应保持 partially supported axes

在 axis 层，我们完成了第一轮 `annotation + validation + tiering`，使当前 frozen structure 不再只是未命名的几何对象，而具备了可进入主文写作的解释边界。当前更稳的 axis 包括 `transcription / chromatin`、`chromatin remodeling`、`TGF-beta / BMP signaling`、`ER stress / UPR`、`RNA processing / spliceosome`、`ribosome biogenesis / nucleolar` 与 `ribosomal / translation`。其中，`transcription / chromatin` 是当前最稳的一条 formal positive axis，但最多只能写成 `primary_axis_but_qualified`；其他 axis 虽获得了方向一致的 enrichment 或 per-target consistency 支持，但多数仍未达到 fully established functional axis 的主张上限。

因此，当前 axis 结果最合适的总体表述是：多数 frozen axes 已获得部分支持，但支持强度不均匀；现阶段更适合将其写成 `partially supported axes`，而不是 fully closed architecture。换句话说，当前工作的主要贡献，不在于证明一个已经完全闭合的模块架构，而在于完成了第一轮 annotation、validation 与 evidence tiering，使哪些 axis 可以进入更强层级、哪些 axis 必须保守表述，已经具备清晰边界。

## 4. Result 4：Dixit/K562 作为 formal supplementary external evidence 与 temporal panel（A0 confirmed / A1 supporting / B not eligible）

为检验 architecture 是否具有跨 context 的可复制性，我们进一步考察了基于 `GSE90063 K562 13d/7d temporal panel` 的 `Dixit/K562` supplementary external structure replication 对象；其中 `13d` 是 primary formal supplementary bridge test，`7d` 是 temporal sensitivity / early-bridge probe。当前结果表明，两个时间点均可观察到 `canonical backbone` 与 `shift-excess` 两类结构成分，因此支持 `backbone + shift-excess` 这类 architecture form 在外部 context 中具有一定可复制性。与此同时，在当前项目对象层，`13d` 与 `7d` 各有 `n=10` 个 formal bridgeable targets 进入 DepMap 对接，并呈现方向一致、时间尺度兼容的 bridge signal，因此可为 bridge form 提供 supplementary-level supporting evidence。然而，这种复现主要停留在结构层，而非主导功能类别层：相较于 HCC 中以 `gene expression machinery` 为主的 backbone，`K562` 的 dominant backbone 更偏 `transcription regulation`，其 shift-excess macro class 也仍应保持 preliminary。

`7d` 的作用不是提供第二个 primary supplementary headline，而是在同一外部 context 下检验 bridge 与 architecture adjudication 在较早时间点的轮廓。按现行 admission / bridgeability 规则，`7d` 与 `13d` 目前各有 10 个正式 bridgeable targets 进入 DepMap 对接；这一数字不应与原始实验设计中的 target / guide 数直接等同。`7d/13d` temporal panel 的关键结果是：两时间点均确认 `backbone_plus_shift_excess`，支持同一外部 K562 context 下 architecture form 的时间稳定性；但 `7d` rank alignment 更强，而 `13d` mean shift 更大，支持 bridge readout 的 temporal stratification，而不是 later timepoint 单调更强。因而更稳的写法是：`13d` 是 primary formal supplementary bridge test，`7d` 是 temporal sensitivity / early-bridge probe；二者共同构成 `GSE90063 K562 13d/7d temporal panel`，但不支持把 `7d` 写成 primary closure、matched endpoint 或 external model-side generalization proved。

按当前 formal supplementary tiering（A0/A1/B 三层），`architecture existence` 与 `canonical backbone present` 属于 **A0 architecture form → confirmed**；`shift-excess present`、`architecture class = backbone_plus_shift_excess` 与 context-specific backbone macro class 属于 **A1 bridge form → supporting / partial-support**；而 `shift-excess macro class` 及多数单条 K562 axis 属于 **B 层 content-level replication → not eligible**。因此，`Dixit/K562` 当前支持的是 **formal supplementary external evidence**：A0 已 confirmed，A1 当前为 supporting / partial-support，而不是与 HCC 对称的 primary co-pillar，也不能写成 content-level replication confirmed、content-level convergence、broad cross-context validation 或 external model-side generalization proved。

进一步地，K562 7d/13d 的 parallel endpoint 对照显示：CRISPR DepMap bridge Spearman（0.52–0.73）一致强于 RNAi DEMETER2（0.30–0.33），CRISPR vs RNAi endpoint Spearman 为 0.45。结合 HCC38/1143 的平行结果，四个 context 的 call 全部一致为 `rnai_bridge_weaker_than_crispr_sensitivity`，且 HCC 的 CRISPR vs RNAi 一致性（0.14/0.23）显著低于 K562（0.45），说明这一 endpoint hierarchy 是跨 HCC + K562 的 framework-level observation，而非 K562 特例。

## 5. Result 5：CRISPR DepMap 是 formal primary bridge readout，RNAi DEMETER2 是跨 context 一致的 weaker sensitivity endpoint

为建立 endpoint hierarchy 并评估跨平台 robustness，我们系统在 HCC38、HCC1143、K562 7d 和 K562 13d 四个 context 中对 CRISPR DepMap 与 RNAi DEMETER2 两种 endpoint 进行了 parallel bridge 对接。结果在所有四个 context 中高度一致：CRISPR DepMap 的 truth–dependency bridge Spearman（0.51–0.78）均明显强于 RNAi DEMETER2（0.28–0.38），且所有 call 均为 `rnai_bridge_weaker_than_crispr_sensitivity`。这一 pattern 并非 K562 的偶然，而是跨 HCC + K562 的 framework-level observation。

关键发现是：CRISPR vs RNAi endpoint Spearman 在 HCC 中（0.14 / 0.23）显著低于 K562（0.45 / 0.45），说明 cross-platform robustness 本身是 context-dependent 的。在 K562 中 CRISPR 与 RNAi 平台间一致性为 moderate；但在 HCC 中这种一致性更弱，提示 RNAi 在 HCC 语境下与 CRISPR 的 divergence 更大，不能将 RNAi 当成等价 primary evidence。

因此，**CRISPR DepMap = formal primary bridge readout**；**RNAi DEMETER2 = weaker cross-platform sensitivity endpoint**。这一层级定位已在四个 context 中稳定复现，不是事后挑选，也不是单一 dataset 特判。它支持的是 architecture-aware evaluation framework 的 proof-of-concept，而不是 broad external generalization proved。RNAi 不替代 CRISPR 主线，也不提供等价 primary evidence；其在 HCC 中更弱的平台间一致性进一步说明 endpoint 替换不能在不同 context 中一致保留 bridge strength 或 target ranking。

## 6. Result 6：Stage 1A / 1B 在 truth-first 主线下应被重写为 failure decomposition track

在 truth-first 主线下，`Stage 1A / 1B` 的作用也需要被重新解释。`Stage 1A` 不再只是 short-horizon leaderboard，而应被理解为 `short-horizon failure decomposition`：它更适合回答模型丢掉的是 backbone、shift-excess，还是 context-specific deviation，并判断这些 failure mode 是否在 formal held-out / multi-split 下稳定存在。相应地，`Stage 1B` 不再只是 long-horizon stress test，而应被理解为 `long-horizon / temporal failure decomposition`：它更适合判断 short-horizon 中已出现的 failure mode 是否在 external time-aligned truth 中进一步放大为 `temporal structure degradation`。

因此，`Stage 1A / 1B` 当前最重要的价值，不是提供一组脱离结构语义的排名，而是为 `Stage 2` 的 architecture adjudication 提供结构化失败解释层。它们解释的是 model failure，而不是新 truth object，也不应与 truth-side discovery 或 HCC primary biological conclusion 竞争同一层级。

## 7. Result Summary

综合以上结果，我们认为本项目已经完成从”现象级相关”到”分层化结构证据”的第一轮收口。当前最稳的主张包括：`GEARS` 在 HCC primary adjudication 中应被定位为 `architecture trade-off diagnosis`；`truth–DepMap bridge` 由少数结构上稳定、但需按 `PFDN5 = primary_but_qualified`、`PMF1 / PRPF6 / ZNF131 = supporting_only` 继续分层书写的 anchors 与有限 formal axis evidence 共同支撑；frozen axis 已完成第一轮 `annotation + validation + tiering`，但整体仍应保持 `partially supported axes`，其中 `transcription / chromatin` 最多只能写成 `primary_axis_but_qualified`；`barcode_gem_group` 当前可作为更接近实验设计 aggregation 结构的 design-proxy axis 写入方法学边界，但不能上写成单个 `MH00x` 已确认的 run-level covariate；`Dixit/K562` 基于 `GSE90063 K562 13d/7d temporal panel` 在 formal supplementary 层面支持 `backbone + shift-excess` 的 architecture form（A0 confirmed / A1 supporting / B not eligible），其中 `13d` 是 primary formal supplementary bridge test，`7d` 是 temporal sensitivity / early-bridge probe，二者在当前项目对象层各有 `n=10` 个 formal bridgeable targets 进入 DepMap 对接。该 panel 支持同一外部 context 下的 architecture form 时间稳定性与 bridge readout temporal stratification，但不能写成第二个 primary closure 或 external model-side generalization proved。endpoint hierarchy 已在 HCC38、HCC1143、K562 7d 和 K562 13d 四个 context 中稳定验证为 framework-level observation，CRISPR DepMap（0.51–0.78）一致强于 RNAi DEMETER2（0.28–0.38），且 HCC 的 CRISPR vs RNAi endpoint 一致性（0.14/0.23）显著低于 K562（0.45），说明 cross-platform robustness 是 context-dependent 的，RNAi 只能作为 weaker cross-platform sensitivity endpoint 而非 primary evidence。由于 target 数仍有限且 dominant macro-class remains context-specific，这些结果不能升级为 shared mainline architecture content、broad cross-context validation 或与 HCC 对称的 primary conclusion；`Stage 1A / 1B` 则应被重写为 frozen truth architecture 下的 `failure decomposition track`。同时，当前 entrant family comparison 还表明，复杂模型之所以不能稳定胜过 baseline，最主要不是接入错误或 coverage 缺口，而是 shared canonical backbone 本身较强，而 entrant 学到的额外结构优势更偏 separation / deviation 方向，尚未稳定转化为 backbone superiority。这些结果共同说明，当前阶段最重要的进展不是得到了更多信号，而是 evidence tier、claim strength、endpoint hierarchy 与 model-failure explanation 已被系统对齐，从而使整体叙事更加清晰、可信且可防守。

若继续向后推进，当前默认也不应再把 baseline-vs-model explanation 保留为开放式泛问题，而应先回答 `baseline winner 是否主要由 backbone objective 决定` 与 `entrant extra capability 是否主要落在 separation / deviation` 这两个更小的问题。

## 8. Discussion

### 8.1 Architecture trade-off 的含义

本项目最重要的发现不是"某个模型胜出"，而是暴露了 perturbation foundation model 当前在 architecture level 上的一种系统性限制：在 canonical backbone recovery 这件事上，冻结共享均值基线持续优于正式训练的 GEARS。这指向一个更基础的问题：当前模型学习到的额外结构优势更偏向于把不同 context 的扰动响应分开（structure/context separation）和识别超出 backbone 可解释范围的过度偏移（shift-excess），而非更精确地拟合 backbone 主方向。

这有两种互补解释。第一种是方法学解释：HCC task 中的 canonical backbone 具有较强的 shared component，均值基线已经是一个很强的主方向估计；复杂 entrant 的 inductive bias 更适合处理 context deviation 而非 backbone 本身，因此 backbone gap 本质上是 task structure 与模型能力的结构性错配。第二种是生物学解释：真实扰动应答中的 canonical backbone 可能主要由实验系统的系统性偏移（如 library composition 效应）驱动，而非能被模型捕获的通用转录程序。当前数据尚不足以在两种解释间做裁决。

无论哪种解释更接近真相，backbone gap 的方向在 HCC 与 K562 两个 context 中一致，说明这不是单个 cell line 的偶然结果。后续若要继续推进，最值得优先回答的问题不是"哪个模型更强"，而是：shared mean baseline winner 是否主要由 shared backbone objective 决定，以及 entrant 的额外能力是否稳定落在 separation/deviation 而非 backbone 上。

### 8.2 为什么 K562 不能成为第二主战场

K562 temporal panel 是本项目的关键 external check，核心价值在于证明 architecture form 能在外部 context 中复现。但它不能被提升为与 HCC 对称的主线，理由有三：

第一，K562 的 10 个 perturbed TF 与 HCC atlas 的 47 个基因完全不重叠——这意味着 K562 检验的是 architecture form 的跨 context 复现，而不是具体 gene identity 的跨数据集 replication。第二，K562 的 dominant backbone macro-class 是 transcription regulation，而 HCC 的 dominant backbone macro-class 是 gene expression machinery——两个 context 在内容层面是 context-specific 的，不支持 convergence claim。第三，K562 13d/7d 的 bridge signal 在 embedding-based entrants 中呈现一致的 temporal pattern（7d rank alignment 强于 13d），这支持的是 bridge readout 存在 temporal stratification，而不是 later timepoint 单调更强。

因此，K562 panel 的正确角色是：在 formalism 层面检验 architecture form 是否跨 context 成立（supporting architecture-existence），在 bridge 层面检验 signal 是否在时间尺度上兼容（supporting temporal stratification），但不在 content 层面声称跨 context 一致收敛。

### 8.3 Endpoint hierarchy 的深层含义

CRISPR DepMap 始终强于 RNAi DEMETER2 作为 bridge endpoint，说明不同扰动 readout 平台对同一 transcriptomic signal 的响应是不同的。这不是 RNAi 本身"不准"，而是因为 RNAi 的扰动机制（转录后敲低）与 CRISPR（基因ko）不同，且 DEMETER2 整合了多种 shRNA 数据，本身存在更复杂的信号稀释。

更重要的是，CRISPR vs RNAi endpoint Spearman 在 HCC（0.14/0.23）显著低于 K562（0.45）——这说明 cross-platform robustness 是 context-dependent 的，而非普遍成立的跨平台规律。这一发现对未来的 perturbation benchmark 设计有直接启示：endpoint 的选择应当由 biological plausibility 和 data quality 共同决定，而非默认某种平台"更接近真相"。

### 8.4 Limitations

本研究存在以下明确 limitations：

**混杂控制层面**：当前 covariate audit 已覆盖五条轴（barcode_gem_group、num_umis_quantile_bin、num_umis_over_threshold_bin、transcriptome_total_signal_quantile_bin、transcriptome_detected_genes_quantile_bin），barcode_gem_group 已固定为 design-proxy axis（已确认 HCC38 对应 aggrMH001-3、HCC1143 对应 aggrMH004-6），但尚未唯一解析到单个 MH00x run label。Stable anchors 中，PFDN5 风险最轻，PMF1/PRPF6/ZNF131 均存在不可忽略的 target-control 分布差异。当前状态是"风险已治理进边界"，不是"混杂已完全排除"。

**Sensitivity 层面**：formal interval 已可引用（24 配置重复数全部完成），cutoff sensitivity 与 bootstrap stability 均已支持主支柱信号的保守稳健性。但 sensitivity full closure 仍被 covariate closure 未 fully closed 约束，DEG burden 对阈值敏感，不适合作为 headline metric。

**Architecture 层面**：正式 axis evidence 总体有限，transcription / chromatin 是 bootstrap 下唯一稳定的 formal positive axis，但最多只能写成 primary_axis_but_qualified。多数其余 axis 仍停留在 preliminary 或 mixed_signal 层。

**K562 层面**：K562 的 n=10 个 formal bridgeable targets 是现行 admission/bridgeability 规则下的正式数字，不等于原始实验设计中的 target/guide 覆盖度。7d 的早期时间点优势在 rank alignment 而非 mean shift，可能反映 temporal sensitivity 差异，但不应用于在 7d 上做更强的主张。

**Discovery 层面**： phenotype shifter discovery 当前为 gated downstream layer，不得作为 primary 或 near-term formal deliverable 写进正文。Discovery 需要在 truth-side 与 model-side 双双闭环后才能重新评估。

**Generalization 层面**：本项目的结论不声称" perturbation foundation model 已能恢复 biological mechanism"。它只陈述：当前最强 entrants 在 architecture-aware evaluation 下呈现一种系统性 trade-off，shared canonical backbone 在当前 benchmark 中是最强的结构成分，以及 architecture form 在外部 context 中有一定可复制性。
