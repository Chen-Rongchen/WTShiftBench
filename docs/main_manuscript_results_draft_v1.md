# 主文稿 Results 草案 v1

## Abstract

我们提出一个 truth-first architecture-aware 框架，用于评估扰动应答转录组模型能否恢复可桥接到 DepMap CRISPR 适应度的结构化 truth object。核心发现是：当前 entrants 在 canonical backbone recovery 上尚未稳定胜过 `shared_mean_baseline`，而是暴露出非对称 architecture trade-off：`shared_mean_baseline` 更强地恢复 backbone，复杂模型的相对优势更偏向 structure/context separation 与 deviation。HCC38/HCC1143 中，`shared_mean_baseline` 的 backbone recovery 均值为 0.807，高于正式 GEARS recipe 的 0.660；GEARS 的 structure-vs-context separation 为 0.428，高于 baseline 的 0.353。truth-side bridge 由分层证据支撑：`PFDN5` 只能写成 `primary_but_qualified`，`PMF1 / PRPF6 / ZNF131` 只能写成 `supporting_only`，`transcription / chromatin` 是当前唯一更稳的 formal positive axis。`GSE90063 K562 13d/7d temporal panel` 支持 `backbone + shift-excess` architecture form 的时间稳定性，分层为 A0 confirmed / A1 supporting / B not eligible；`7d` rank alignment 更强，`13d` mean shift 更大。跨 HCC38/HCC1143/K562 7d/K562 13d 四个 context，CRISPR DepMap bridge Spearman（0.51-0.78）一致强于 RNAi DEMETER2（0.28-0.38），确立 CRISPR 为 formal primary bridge readout，RNAi 为 weaker cross-platform sensitivity endpoint。当前结果不支持 "model recovery proved"，不支持 GEARS 整体压过共享均值基线，也不支持 K562 作为 HCC 对称的 primary co-pillar 或 content-level replication。

## 1. GEARS 是 architecture trade-off diagnosis，而非 primary winner

我们首先评估 strongest formal entrant `GEARS` 在 HCC38/HCC1143 真实 HCC mainline 中对 frozen architecture 的恢复能力。结果不支持把 GEARS 写成 primary winner：两个 cell line 上，`canonical_backbone recovery` 均仍落后于 `shared_mean_baseline`。跨细胞系均值上，baseline backbone recovery 为 0.807，正式 GEARS recipe 为 0.660；相对地，GEARS 在 structure-vs-context separation 上更强（0.428 vs 0.353）。

这一结论在有限 backbone sweep 后保持稳定。若干 sweep 候选提升了 `shift-excess identification` 或 separation，但没有候选接近或追平 baseline 的 backbone recovery，也没有候选超过当前正式 GEARS recipe 的 backbone 表现。因此，冻结 stop rule 被触发：GEARS 在本阶段应收口为 architecture trade-off diagnosis，而不是继续 sweep 的默认起点。

该 gap 也不能再归因于 entrant 尚未正式接入。`GEARS / scGPT / Geneformer / lm_train_lowrank / lm_G_scgpt_ridge / lm_G_geneformer_ridge` 均已进入同一份 HCC formal comparison，ridge controls 的 target coverage 已达到 1.000。更稳的解释是：HCC task 中 shared canonical backbone 本身较强，baseline 已能有效估计主方向；复杂 entrant 的额外能力更偏 separation、shift-excess 或 context-sensitive deviation，尚未稳定转化为 backbone superiority。

K562 13d 最小 model-side 审计支持同一方向的 partial recurrence：baseline 再次在 backbone recovery 上占优，GEARS 仍在 structure-vs-context separation 上更强，但 `shift-excess` 分量未复现。因此，这只能写成 partial recurrence / partial-support，不能写成 full three-component recurrence 或 external model-side generalization established。K562 7d/13d 的 6 entrant leave-one-target-out 评估进一步显示 embedding-based entrants 在 7d 的平均 bridge Spearman（0.476-0.520）高于 13d（0.349-0.373），而 GEARS 在两个时间点均最弱；这一 pattern 支持 temporal stratification，而不把 7d 升级为第二个 primary external replication。

## 2. truth-DepMap bridge 分解为 anchors 与有限 axis evidence

Truth-side bridge 不应只写成整体相关，而应写成分层结构。第一层是 target-level joint bridge：`PFDN5 / PMF1 / PRPF6 / ZNF131` 在 transcriptomic impact 与 aligned dependency 上共同保持高位，并在 cutoff sensitivity 下维持结构稳定。

但 structural stability 不能等同于 covariate cleanliness。五轴 covariate audit 已覆盖 `barcode_gem_group`、两条 protospacer 轴与两条 transcriptome 轴，并据此完成对象级降级治理。当前只能确认 `HCC38 -> aggrMH001-3`、`HCC1143 -> aggrMH004-6`，不能把 `barcode_gem_group` 写成单个 `MH00x` run-level covariate。因此，`PFDN5` 最多写成 `primary_but_qualified`，`PMF1 / PRPF6 / ZNF131` 只能写成 `supporting_only`；新增 covariate 轴没有把这些对象升级为 fully deconfounded strongest anchors。

第二层是 axis-level explanatory structure。按照 `n_targets >= 2` 的 formal call 约束和 bootstrap stability，axis evidence 总体有限；`transcription / chromatin` 是当前唯一更稳的 formal positive axis，但也最多只能写成 `primary_axis_but_qualified`。其余 axes 应保留为 supporting、unstable 或 preliminary。当前结果支持的是可治理、可分层的 truth-DepMap bridge structure，而不是多数 axis 已完成正式闭环。

## 3. Axis interpretation 是 partially supported，而非 fully closed

Frozen axis 已完成第一轮 annotation、validation 与 tiering，使 truth object 具备可进入主文写作的解释边界。相对更稳的 axes 包括 `transcription / chromatin`、`chromatin remodeling`、`TGF-beta / BMP signaling`、`ER stress / UPR`、`RNA processing / spliceosome`、`ribosome biogenesis / nucleolar` 与 `ribosomal / translation`。

这一步的结论必须保守：多数 axes 获得部分支持，但支持强度不均。`transcription / chromatin` 是当前唯一更稳的 formal positive axis；其他 axes 虽有方向一致的 enrichment 或 per-target consistency 支持，但不足以升级为 fully established functional axes。主文应写成 `partially supported axes`，而不是 fully closed architecture。

## 4. Dixit/K562 提供 supplementary external evidence 与 temporal panel

为检验 architecture form 是否能在外部 context 中复现，我们考察了 `GSE90063 K562 13d/7d temporal panel`。其中 `13d` 是 primary formal supplementary bridge test，`7d` 是 temporal sensitivity / early-bridge probe。两个时间点均可观察到 `canonical backbone` 与 `shift-excess`，支持 `backbone + shift-excess` architecture form 的时间稳定性。

在当前 admission / bridgeability 规则下，`13d` 与 `7d` 各有 n=10 个 formal bridgeable targets 进入 DepMap 对接。`7d` rank alignment 更强，`13d` mean shift 更大，支持 bridge readout temporal stratification，而不是 later timepoint 单调更强。按 formal supplementary tiering：`architecture existence` 与 `canonical backbone present` 属于 A0；`shift-excess present`、`architecture class = backbone_plus_shift_excess` 与 context-specific backbone macro class 属于 A1；`shift-excess macro class` 和多数单条 K562 axis 属于 B 层 not eligible。因此，K562 panel 的固定写法是 A0 confirmed / A1 supporting / B not eligible。

这些结果不能升级为与 HCC 对称的 primary co-pillar。K562 的 10 个 perturbed TF 与 HCC atlas 的 47 个 genes 不重叠，dominant backbone macro-class 也更偏 `transcription regulation`；它支持的是 architecture form recurrence 和 bridge-form support，不是 content-level convergence、broad cross-context validation 或 external model-side generalization proved。

## 5. CRISPR DepMap 是 primary bridge readout，RNAi 是 weaker sensitivity endpoint

Endpoint hierarchy 在 HCC38、HCC1143、K562 7d 和 K562 13d 四个 context 中保持一致：CRISPR DepMap 的 truth-dependency bridge Spearman（0.51-0.78）均强于 RNAi DEMETER2（0.28-0.38），所有 call 均为 `rnai_bridge_weaker_than_crispr_sensitivity`。

CRISPR vs RNAi endpoint Spearman 在 HCC 中（0.14/0.23）低于 K562（0.45），说明 cross-platform robustness 是 context-dependent 的。RNAi 不替代 CRISPR 主线，也不提供等价 primary evidence。该结果支持 endpoint hierarchy 的 framework-level observation，而不是 broad external generalization proved。

## 6. Stage 1A / 1B 应重写为 failure decomposition track

在 truth-first 主线下，`Stage 1A / 1B` 不再只是 leaderboard 或 long-horizon stress test。`Stage 1A` 应解释 short-horizon failure decomposition：模型丢掉的是 backbone、shift-excess，还是 context-specific deviation。`Stage 1B` 应解释 temporal failure decomposition：这些 failure modes 是否在更长时间尺度上放大为 temporal structure degradation。

因此，`Stage 1A / 1B` 的价值是为 Stage 2 architecture adjudication 提供结构化失败解释层，而不是提供新的 truth object，也不应与 HCC primary biological conclusion 竞争层级。

## 7. Result Summary

本项目已经完成从现象级相关到分层化结构证据的第一轮收口。当前最稳的主张包括：GEARS 是 architecture trade-off diagnosis；`shared_mean_baseline` 仍是 backbone 更强的 primary reference；truth-DepMap bridge 由少数稳定但需降级书写的 anchors 与有限 formal axis evidence 共同支撑；`barcode_gem_group` 是 design-proxy axis，而不是 resolved run-level covariate；Dixit/K562 只能作为 supplementary external evidence；RNAi DEMETER2 只能作为 weaker cross-platform sensitivity endpoint；discovery 仍是 gated downstream layer。

这些结果共同说明，当前阶段最重要的进展不是得到更多信号，而是 evidence tier、claim strength、endpoint hierarchy 与 model-failure explanation 已对齐。后续若继续推进 baseline-vs-model explanation，应先回答两个更小的问题：baseline winner 是否主要由 shared backbone objective 决定，以及 entrant extra capability 是否主要落在 separation / deviation 而非 backbone。

## 8. Discussion

### 8.1 Architecture trade-off

本项目最重要的发现不是某个模型胜出，而是当前 perturbation foundation model 在 architecture level 上的系统性限制：在 canonical backbone recovery 上，冻结共享均值基线持续优于正式训练的 GEARS；模型的额外优势更偏向 structure/context separation 与 shift-excess，而非更精确地拟合 backbone 主方向。

这可以有方法学和生物学两层解释。方法学上，HCC task 的 canonical backbone 具有较强 shared component，baseline 已是强主方向估计；复杂 entrant 更适合处理 context deviation。生物学上，canonical backbone 也可能部分来自实验系统的系统性偏移，而不是模型可捕获的通用转录程序。当前数据不足以在两种解释间做裁决，因此 biology-facing interpretation 只能保留为 plausible layer。

### 8.2 为什么 K562 不能成为第二主战场

K562 temporal panel 的价值是检验 architecture form 是否能在外部 context 中复现，而不是提供与 HCC 对称的主线。原因有三：K562 TF targets 与 HCC atlas genes 不重叠；K562 dominant backbone 更偏 transcription regulation，而 HCC 更偏 gene expression machinery；7d/13d 的差异支持 temporal stratification，而不是 later timepoint 单调更强。因此，K562 只能支持 architecture-form recurrence 和 bridge-form support，不能支持 content-level replication。

### 8.3 Endpoint hierarchy

CRISPR DepMap 始终强于 RNAi DEMETER2 作为 bridge endpoint，说明 endpoint choice 是 benchmark 设计的一部分，而不是可互换的后处理。HCC 中 CRISPR vs RNAi 一致性低于 K562，进一步说明 cross-platform robustness 是 context-dependent 的；RNAi 应作为 sensitivity endpoint，而不是 primary evidence。

### 8.4 Limitations

**混杂控制**：五轴 covariate audit 已完成第一轮治理，但 `barcode_gem_group` 只能写成 design-proxy axis，不能唯一解析到单个 `MH00x` run label。Stable anchors 当前是 structural stability，不是 fully deconfounded strongest evidence。

**Sensitivity**：formal interval 已可引用，cutoff sensitivity 与 bootstrap stability 支持主支柱信号的保守稳健性；但 sensitivity full closure 仍受 covariate closure 未 fully closed 约束，DEG burden 不适合作为 headline metric。

**Architecture**：formal axis evidence 有限，`transcription / chromatin` 最多只能写成 `primary_axis_but_qualified`，其余 axes 多数为 preliminary 或 mixed signal。

**K562**：n=10 formal bridgeable targets 是当前 admission/bridgeability 规则下的正式数字，不等同于原始 target / guide 覆盖度。7d 的优势在 rank alignment，而非 mean shift，不能升级为 primary closure。

**Discovery**：phenotype shifter discovery 当前仍是 gated downstream layer，不得写成 primary 或 near-term formal deliverable。

**Generalization**：本项目不声称 perturbation foundation model 已能恢复 biological mechanism；只陈述当前 entrants 在 architecture-aware evaluation 下呈现 trade-off，shared canonical backbone 是当前 benchmark 中最强结构成分，architecture form 在外部 context 中有 supplementary-level recurrence。
