# 完整手稿草案 v1

## 题目

Truth-first architecture-aware benchmarking reveals a backbone-separation trade-off in transcriptomic perturbation model recovery

中文工作题目：基于 truth-first 架构评估揭示扰动转录组模型恢复中的 backbone-separation trade-off

## 摘要

扰动应答转录组模型通常以表达拟合或扰动间相似性作为主要评估对象，但这些指标未必能回答一个更直接的问题：模型是否恢复了与细胞适应度或依赖性相关的转录组结构。我们建立了一个 truth-first、architecture-aware 的评估框架，先在真实扰动转录组中冻结可桥接到 DepMap 依赖性终点的 truth object，再评估模型能否恢复该结构。我们在 HCC38/HCC1143 两条 HCC 细胞系中发现，truth-DepMap bridge 不是松散相关，而是由 target-level anchors 与有限 axis-level evidence 共同构成的分层对象。PFDN5 可保留为 primary_but_qualified anchor，PMF1、PRPF6 与 ZNF131 保留为 supporting_only anchors；transcription/chromatin 是当前唯一更稳的 primary_axis_but_qualified axis。模型侧结果显示，shared_mean_baseline 在 backbone recovery 上持续强于正式 GEARS recipe（0.807 vs 0.660），而 GEARS 在 structure-vs-context separation 上更强（0.428 vs 0.353），说明当前 entrants 更适合被写成 architecture trade-off diagnosis，而不是 model recovery proved。GSE90063 K562 13d/7d temporal panel 在外部 context 中支持 backbone_plus_shift_excess architecture form 的时间稳定性，但只能作为 supplementary-level evidence（A0 confirmed/A1 supporting/B not eligible）。跨 HCC38、HCC1143、K562 7d 与 K562 13d 四个 context，CRISPR DepMap bridge Spearman（0.515-0.779）一致强于 RNAi DEMETER2（0.276-0.384），确立 CRISPR 为 formal primary bridge readout，RNAi 为 weaker cross-platform sensitivity endpoint。整体而言，本研究提出的 benchmark 不证明当前模型已经恢复生物机制，而是给出一套可审计的证据层级：fitness-relevant transcriptomic bridge architecture 可以被定义、分解和部分复现，但当前模型恢复仍受 backbone 与 separation 之间的结构性 trade-off 限制。

## 引言

大规模单细胞扰动数据为训练 virtual perturbation model 提供了基础，但模型评估仍面临一个核心问题：如果一个模型能较好预测表达变化，它是否也恢复了与细胞适应度、依赖性或功能脆弱性相关的结构。传统 leaderboard 往往聚焦均方误差、相关系数或 top-gene overlap，这些指标能衡量表达层面的局部拟合，却不一定区分 shared backbone、context-specific deviation 与真正能桥接 fitness endpoint 的结构。

本项目采用相反顺序：不是先比较模型，再从最高分模型中寻找生物解释，而是先冻结 truth object。我们首先在真实扰动转录组中定义 target-level transcriptomic impact，并将其与 DepMap dependency endpoint 对齐，构建 truth-DepMap bridge。随后，该 bridge 被分解为 target-level anchors、axis-level explanatory structure、covariate boundary 与 endpoint hierarchy。只有在这一 truth object 固定之后，模型才进入 recovery adjudication。

这个框架的关键假设是，模型评估应回答结构恢复问题，而不是只回答表达拟合问题。具体地，我们将模型恢复拆成三个主裁决指标：canonical backbone recovery、shift-excess identification 与 structure-vs-context separation。这样可以避免把不同类型的结构优势混成单一分数，也可以解释为什么某些复杂模型在局部结构上有价值，却仍不能整体胜过简单 baseline。

当前手稿的主要结论有四点。第一，HCC truth-DepMap bridge 在整体与结构层面成立，但对象级证据需要分层书写。第二，GEARS、scGPT、Geneformer 与多个 linear controls 的 formal comparison 没有推翻 shared_mean_baseline 作为 backbone primary reference 的地位；GEARS 的相对优势更偏向 separation/deviation。第三，axis 解释层已经完成第一轮 annotation、validation 与 tiering，但不是 fully established shared explanatory architecture。第四，K562 temporal panel 与 RNAi endpoint sensitivity 支持 framework-level boundary，而不是 HCC primary conclusion 的对称复现。

## 结果

### 1. Truth-DepMap bridge 定义了结构化 truth object

我们首先在 HCC38 与 HCC1143 中将真实扰动转录组 shift 与 DepMap gene dependency 对齐，构建 target-level joint-priority grid。每个 target 按 transcriptomic impact 与 dependency strength 分别划分为 high/middle/low，并据此定义 Q1_anchor、Q2_transcriptomic_excess、Q3_dependency_excess 与 Q4_low_information。HCC1143 中 Q1_anchor 包含 10 个 target，占 20.8%；HCC38 中 Q1_anchor 包含 9 个 target，占 19.1%。这说明 bridge signal 不是由全局相关系数单独驱动，而是富集在一组可解释的高 shift/高 dependency target 上。

跨两条 cell line 的 shared canonical anchors 包括 PFDN5、PMF1、PRPF6 与 ZNF131。这些 target 在 cutoff sensitivity 下保持 shared anchor stability = 1.00，说明它们的结构身份稳定。然而，结构稳定不等于混杂完全关闭。五轴 covariate audit 覆盖 barcode_gem_group、两条 protospacer 轴与两条 transcriptome 轴后，anchor-level strongest wording 被正式降级：PFDN5 可保留为 primary_but_qualified；PMF1、PRPF6 与 ZNF131 只能写成 supporting_only。

Axis-level 证据更保守。当前没有 axis 满足 shared backbone axis 的正式条件；transcription/chromatin 表现为 transcriptomic-heavy axis，shift R2 = 0.092，dep R2 = 0.000，targets = ENY2/TADA3。结合 bootstrap 与 annotation evidence，transcription/chromatin 是当前唯一可写成 primary_axis_but_qualified 的 formal positive axis。其它 axes 包括 chromatin remodeling、TGF-beta/BMP signaling、ER stress/UPR、RNA processing/spliceosome、ribosome biogenesis/nucleolar 与 ribosomal/translation，均应保留为 partially supported、supporting 或 preliminary。

因此，truth-DepMap bridge 的正式写法是：整体与结构层面成立，但对象级与 axis 级证据必须分层；当前结果不支持 fully deconfounded bridge，也不支持 fully established shared explanatory architecture。

### 2. 当前 entrants 暴露 backbone 与 separation 的 architecture trade-off

在冻结 truth object 后，我们评估模型是否恢复该 architecture。HCC formal comparison 纳入 shared_mean_baseline、GEARS、scGPT、Geneformer、lm_train_lowrank、lm_G_scgpt_ridge 与 lm_G_geneformer_ridge。主裁决指标包括 backbone_recovery_score、shift_excess_identification_score 与 structure_vs_context_separation_score。

结果显示，shared_mean_baseline 在 backbone recovery 上仍是最强 primary reference，得分为 0.807；正式 GEARS recipe 为 0.660。相对地，GEARS 在 structure-vs-context separation 上高于 baseline（0.428 vs 0.353）。这不是对称胜负，而是非对称 trade-off：baseline 更稳地恢复 shared canonical backbone，GEARS 更偏向 separation/deviation。shift-excess identification 在 formal GEARS 与 baseline 中均为 0.333，但部分 sweep candidate 可提升 shift-excess 或 separation，却不能补上 backbone gap。

有限预算 GEARS backbone sweep 进一步支持该结论。最优 backbone sweep candidate 为 gears_hcc_formal_v1_e30_lr2e-03_wd1e-06，backbone recovery = 0.643，仍低于正式 GEARS 的 0.660，更远低于 shared_mean_baseline 的 0.807；其 separation = 0.449，高于 formal GEARS。没有任何 sweep candidate 接近或追平 baseline backbone recovery，也没有任何 candidate 超过正式 GEARS 的 backbone recovery。预先冻结的 stop rule 因此被触发：GEARS 应收口为 architecture trade-off diagnosis，而非 HCC primary winner。

其它 entrants 与 controls 也没有改变结论。Geneformer 强于 scGPT，但 backbone recovery 仍低于 baseline；lm_G_geneformer_ridge 保住一部分 embedding-related signal，但也不能恢复 backbone 主方向。ridge controls coverage 已达到 1.000，因此当前 gap 不宜归因于接入错误或 target coverage 缺口。更稳的解释是 HCC task 中 shared canonical backbone 本身很强，简单 baseline 已能捕获主方向，而复杂 entrants 的额外能力更偏向 context deviation、structure/context separation 或 shift-excess。

### 3. Axis interpretation 已分层，但仍是 partial closure

Frozen axes 已完成第一轮 annotation、validation 与 tiering。该步骤的贡献不是证明所有 axes 形成完整机制图谱，而是建立了哪些解释可以保留、哪些必须降级的证据边界。

从 enrichment 与 per-target consistency 看，多个 axes 获得部分支持：transcription/chromatin、chromatin remodeling、TGF-beta/BMP signaling、ER stress/UPR、RNA processing/spliceosome、ribosome biogenesis/nucleolar、ribosomal/translation、cell cycle/replication、growth/proliferation 与 JAK-STAT signaling 等均显示不同程度的 annotation support 或 consistency support。但这些支持强度不均，且许多 axes 的 formal target 数不足或 signal 类型偏 preliminary。

因此主文不能写成 fully closed architecture。更准确的结果是，axis interpretation 已进入可写作状态，但 evidence tier 是不均匀的：transcription/chromatin 是当前最强 formal positive axis，但仍需加 qualified；其它 axes 用于解释 broader partially supported architecture，不能与 primary axis 同级。

### 4. Covariate audit 将 strongest claims 降级到 limitation-bounded closure

为了避免把 structural stability 误写为 deconfounded causal evidence，我们对 truth-side bridge 做了多轴 covariate audit。当前五条 covariate 轴已经落盘：barcode_gem_group、两条 protospacer 轴、num_umis/transcriptome signal 相关轴与 detected genes 相关轴。该审计支持保留 global truth-DepMap bridge，但不支持 fully deconfounded closure。

barcode_gem_group 的正式定位是 design-proxy axis。当前只能确认 HCC38 对应 aggrMH001-3、HCC1143 对应 aggrMH004-6，不能写成已解析到单个 MH001-MH006 run label。由此产生的 claim boundary 是方法学层面的：我们可以说 covariate risk 已被显式量化并纳入主张治理，但不能说混杂风险已经完全消除。

这一步直接改变对象级写法。PFDN5 保留为相对更低风险的 stable anchor，但必须带方法学谨慎；PMF1、PRPF6 与 ZNF131 保持 structural anchor 身份，但只能作为 supporting evidence。cutoff-sensitive anchors 如 ENY2、NPM1、RPS3、RUVBL2 与 ZBTB17 只能写成 supporting but sensitive objects。

### 5. K562 temporal panel 支持 architecture-form recurrence，而非 content-level replication

我们使用 GSE90063 K562 TF perturbation temporal panel 作为 external supplementary evidence。当前正式版本固定为 13d/7d temporal panel：13d 是 primary formal supplementary bridge test，7d 是 temporal sensitivity/early-bridge probe。历史的 dixit_2016_raw__control_context 输入因数据身份不匹配被暂停引用，K562 结论以 GSE90063 13d/7d 为准。

两个时间点均支持 backbone_plus_shift_excess architecture class，说明 architecture form 在外部 context 中具有时间稳定性。7d 的 rank alignment 更强，13d 的 mean shift 更大，提示 bridge readout 存在 temporal stratification，而不是 later timepoint 单调更强。按 formal supplementary tiering，architecture existence 与 canonical backbone present 属于 A0 confirmed；shift-excess present、backbone_plus_shift_excess class 与 context-specific backbone macro class 属于 A1 supporting；shift-excess macro class 与多数单条 K562 axis 属于 B not eligible。

K562 不能升级为 HCC 的 primary co-pillar。原因是 K562 formal bridgeable targets 约为 9-10 个，且 K562 TF targets 与 HCC atlas genes 不重叠；其 dominant macro-class 更偏 transcription regulation。它支持 architecture-form recurrence 与 bridge-form support，但不支持 content-level convergence、broad cross-context validation 或 external model-side generalization proved。

### 6. Endpoint hierarchy：CRISPR 是 primary bridge readout，RNAi 是 weaker sensitivity endpoint

我们在 HCC38、HCC1143、K562 7d 与 K562 13d 四个 context 中比较 CRISPR DepMap 与 RNAi DEMETER2 作为 dependency endpoint 的 bridge strength。结果完全一致：CRISPR bridge Spearman 在四个 context 中均高于 RNAi。HCC38 为 0.726 vs 0.276；HCC1143 为 0.779 vs 0.384；K562 7d 为 0.733 vs 0.333；K562 13d 为 0.515 vs 0.300。所有 call 均为 rnai_bridge_weaker_than_crispr_sensitivity。

CRISPR 与 RNAi endpoint 本身的一致性具有 context dependence。HCC 中 CRISPR vs RNAi endpoint Spearman 为 0.141/0.231，而 K562 为 0.450/0.450。这说明 endpoint substitution 不能假定在不同 context 中保留 bridge strength 或 target ranking。正式写法应固定为：CRISPR DepMap 是 formal primary bridge readout；RNAi DEMETER2 是 weaker cross-platform sensitivity endpoint。RNAi 不替代 CRISPR 主线，也不提供等价 primary evidence。

### 7. Stage 1A/1B 应重写为 failure decomposition track

在 truth-first framing 下，Stage 1A/1B 不再是独立 leaderboard 或泛化压力测试主线。它们应服务于 frozen truth architecture 的 failure decomposition。Stage 1A 可用于分析 short-horizon 中模型首先丢失的是 backbone、shift-excess 还是 context-specific deviation。Stage 1B 可用于分析这些 failure mode 是否在更长时间尺度上放大为 temporal structure degradation。

这一定义避免了两个错误方向：一是把 Stage 1A/1B 重新写回脱离结构语义的模型排名；二是把它们提升为新的 truth-discovery layer。当前 discovery 仍是 gated downstream layer，不进入主文 primary deliverable。

## 讨论

本研究的核心贡献不是证明某个模型胜出，而是提出并执行了一套更严格的评估顺序：先定义 fitness-relevant transcriptomic truth architecture，再裁决模型是否恢复该结构。这个顺序改变了 benchmark 的解释方式。若只看表达拟合，复杂模型与 baseline 的差异容易被压成单一分数；若看 architecture recovery，则可以看到 shared_mean_baseline 与 GEARS 分别占据不同结构位置：前者更强于 shared backbone，后者更强于 structure/context separation。

这一结果对 perturbation foundation model 的解释有两层含义。方法学上，当前 HCC task 的 canonical backbone 可能由强 shared component 主导，简单 baseline 已经构成很强的参考系。复杂 entrants 的优势并非不存在，而是没有稳定转化为 backbone recovery superiority。生物学上，canonical backbone 也可能部分反映实验系统、细胞状态或 shared stress-like response，而不是单一可命名通路。当前数据不足以区分这些解释，因此 biology-facing interpretation 必须停留在 plausible layer。

Truth-side 结果同样要求保守书写。PFDN5、PMF1、PRPF6 与 ZNF131 的价值在于它们共同显示 transcriptomic impact 与 dependency strength 的高位共定位，并在 cutoff sensitivity 下保持 structural stability。但 covariate audit 表明，anchor identity 与 deconfounded evidence 不能混写。当前最稳的结论是 limitation-bounded closure：global bridge 可保留，对象级 strongest wording 必须降级。

K562 temporal panel 与 RNAi endpoint sensitivity 扩展了 framework 的可解释边界。K562 说明 architecture form 可在外部 context 中观察到，且 7d/13d 呈现 temporal stratification；RNAi 对照说明 CRISPR endpoint choice 不是任意后处理，而是 benchmark 设计的一部分。但这两条线都不能被提升为 broad generalization claim。K562 不是 HCC 的对称主线，RNAi 不是 primary endpoint。

本研究的主要限制来自实验设计元数据与对象规模。covariate audit 已从单轴提示推进到五轴正式审计，但 barcode_gem_group 仍只能写成 design-proxy axis，而不是 fully resolved run-level covariate。K562 bridgeable targets 数量有限，且与 HCC gene set 不重叠。Axis-level evidence 也不是完整机制闭环，transcription/chromatin 之外多数 axes 仍为 partial support。最后，当前模型侧结果不证明 perturbation foundation model 无用，只说明在这个 frozen truth architecture 下，现有 entrants 的结构优势与 backbone recovery 主目标并不完全对齐。

综上，WT Benchmark 当前最稳的主张是：fitness-relevant transcriptomic bridge architecture 可以被定义、分解、审计和 supplementary-level 复现；但当前模型恢复该 architecture 仍是部分的、trade-off bounded 的，并且受到 covariate 与 endpoint hierarchy 的明确限制。

## 方法概述

### Truth object 构建

在 HCC38/HCC1143 中，使用真实 perturbation transcriptomic shift 作为 transcriptomic truth metric，主指标为 real_shift_mean_abs。DepMap 侧使用 depmap_gene_dependency，并将方向统一为数值越大表示 dependency/liability 越强。每个 target 在 transcriptomic side 与 dependency side 分别按 quantile 分层，并构建 target-level joint grid。

### Target-level anchors

Q1_anchor 定义为 transcriptomic impact 与 dependency strength 同时处于高分位的 target。Shared anchor 要求在两条 HCC cell line 中保持 Q1 命中，并通过 cutoff sensitivity 检查。Anchor claim tier 由 structural stability、cutoff stability 与 covariate audit 共同决定。

### Axis-level analysis

Axis analysis 使用 frozen axis annotation，将每个 axis 的 transcriptomic side 与 dependency side explanatory strength 分开估计。Formal axis call 要求 n_targets >= 2，并结合 bootstrap stability、enrichment evidence 与 per-target consistency。Axis 结果不替代 target-level evidence，也不将单一 Pearson 作为主结论。

### Model recovery adjudication

模型侧以 frozen truth architecture 为裁决对象。主指标为 backbone_recovery_score、shift_excess_identification_score 与 structure_vs_context_separation_score。Entrants 包括 GEARS、scGPT、Geneformer、lm_train_lowrank、lm_G_scgpt_ridge 与 lm_G_geneformer_ridge；shared_mean_baseline 与 null_model 作为 reference。

### Covariate audit

Covariate audit 覆盖 barcode_gem_group、protospacer 相关轴、UMI/transcriptome signal 相关轴与 detected genes 相关轴。barcode_gem_group 被定位为 design-proxy axis；当前不解析为单个 run-level label。Covariate audit 用于 claim governance，而不是宣称 fully deconfounded closure。

### Supplementary K562 temporal panel

GSE90063 K562 13d/7d temporal panel 用于 formal supplementary external evidence。13d 是 primary formal supplementary bridge test；7d 是 temporal sensitivity/early-bridge probe。A0/A1/B tiering 分别对应 architecture form confirmation、bridge-form support 与 content-level not eligible。

### Endpoint sensitivity

在 HCC38、HCC1143、K562 7d 与 K562 13d 中，比较 CRISPR DepMap 与 RNAi DEMETER2 endpoint 的 bridge Spearman，并计算 CRISPR vs RNAi endpoint Spearman。Endpoint hierarchy 由跨 context 一致性决定。

## 主图设计

参考模板 `s41592-025-02772-6.pdf` 的核心不是“主图数量”，而是每张图内部的论证闭环：先给总体 benchmark 结果，再给代表例，再给定义/分解示意，最后用补充分析说明为什么结论不是单一指标偶然。模板论文只有 2 张主图，是因为故事线主要围绕 double perturbation 与 single perturbation 两个 benchmark；本项目同时有 truth object、model recovery、axis interpretation、covariate boundary、temporal replication 与 endpoint hierarchy 六条必要证据层，因此建议主文使用 6 张主图。每张主图都固定 a-h 八个 panel，逻辑上对应模板中的“总览 + 代表例 + 分解 + 边界”。

### Fig. 1. A truth-first benchmark defines the fitness-relevant transcriptomic bridge object

这一图承担模板 Fig. 1 开头的角色：先让读者知道 benchmark 评估的对象是什么，而不是先看模型分数。

- a. Study design schematic：真实扰动转录组 -> truth-DepMap bridge -> frozen architecture -> model recovery adjudication -> gated discovery。
- b. Dataset/endpoint overview table：HCC38、HCC1143、DepMap CRISPR dependency、主 truth metric real_shift_mean_abs、bridgeable targets。
- c. Truth object construction schematic：transcriptomic shift 与 aligned dependency strength 分位分层，定义 Q1-Q4。
- d. HCC38 target-level joint grid：real_shift_mean_abs vs aligned dependency strength，标出 Q1_anchor、Q2、Q3、Q4。
- e. HCC1143 target-level joint grid，同 d。
- f. Grid composition bar：HCC38 与 HCC1143 的 Q1_anchor、Q4_low_information、middle band 比例。
- g. Shared bridge strength summary：两条 cell line 的 CRISPR bridge Spearman 与 target 数。
- h. Take-home boundary strip：truth object exists；不是 loose correlation；不是 fully deconfounded causal proof。

### Fig. 2. Shared anchors form a tiered target-level bridge rather than clean primary objects

这一图对应模板中“代表例 + 类别分解”的逻辑，把 Fig. 1 的 truth object 下钻到 anchor 层，并立刻给出 evidence tier。

- a. Shared canonical anchor ranking：PFDN5、PMF1、PRPF6、ZNF131 与其它 Q1-like targets 的 mean shift quantile、mean dependency quantile。
- b. Anchor recurrence heatmap：每个 target 在 HCC38/HCC1143 是否命中 Q1_anchor。
- c. Anchor cutoff stability：PFDN5、PMF1、PRPF6、ZNF131 stability = 1.00，显示 cutoff sensitivity 下的保留情况。
- d. Representative anchor mini-panels：PFDN5 与 PMF1/PRPF6/ZNF131 的 shift/dependency pair。
- e. Sensitive supporting objects panel：ENY2、NPM1、RPS3、RUVBL2、ZBTB17 作为 supporting_but_sensitive。
- f. Evidence-tier bar：primary_but_qualified、supporting_only、supporting_but_sensitive、preliminary_only。
- g. Anchor claim matrix：PFDN5 = primary_but_qualified；PMF1/PRPF6/ZNF131 = supporting_only。
- h. Disallowed wording strip：不写 fully deconfounded strongest anchors；不写单个 anchor nails down the bridge。

### Fig. 3. Current entrants do not outperform the backbone baseline but reveal a recovery trade-off

这一图是主文的模型侧核心图，对应模板 Fig. 1a-c：总体 benchmark 结果、代表性对照、性能曲线/散点。

- a. Formal HCC model comparison beeswarm/bar：所有 entrants 的 backbone_recovery_score。
- b. 三指标 heatmap：backbone recovery、shift-excess identification、structure/context separation。
- c. Baseline vs GEARS headline comparison：backbone 0.807 vs 0.660；separation 0.353 vs 0.428。
- d. Trade-off scatter：x = backbone recovery，y = structure/context separation，突出 shared_mean_baseline、GEARS formal、Geneformer、scGPT、linear controls。
- e. Representative prediction/recovery panel：一个 shared backbone target set 上 baseline 与 GEARS 的 recovered structure 对照。
- f. Shift-excess panel：显示 GEARS/sweep candidates 的 deviation/separation 相关优势没有稳定转化为 backbone superiority。
- g. Model family grouping：baseline、foundation models、GEARS、linear controls 分组，标注 Geneformer > scGPT 与 lm_G_geneformer_ridge 的相对位置。
- h. Main adjudication strip：GEARS = architecture trade-off diagnosis；shared_mean_baseline = backbone primary reference；禁止 model recovery proved。

### Fig. 4. GEARS sweep and linear controls show the gap is structural, not a missing recipe or coverage artifact

这一图对应模板 Fig. 2 的逻辑：把“深度模型没赢 baseline”进一步拆解，检验是不是 embedding、recipe 或资源问题。

- a. GEARS backbone sweep candidate plot：所有 sweep candidate 的 backbone recovery，baseline dashed line = 0.807。
- b. Sweep trade-off scatter：backbone recovery vs structure/context separation，显示 separation 可升而 backbone 不追平。
- c. Shift-excess identification across sweep：部分 candidate 可升至 0.833/0.917，但不形成 backbone winner。
- d. Stop-rule schematic：有限 recipe 变化范围 epoch/checkpoint、learning rate、weight decay；未引入新 truth object 或新评分体系。
- e. Linear-control architecture schematic：lm_train_lowrank、lm_G_scgpt_ridge、lm_G_geneformer_ridge 如何测试 frozen embedding/linear decoder。
- f. Linear-control ranking：lm_G_geneformer_ridge > lm_train_lowrank > lm_G_scgpt_ridge，但均低于 baseline backbone。
- g. Coverage/control panel：ridge controls target coverage = 1.000，排除 coverage 缺口作为主解释。
- h. Interpretation strip：gap 更像 direction-level/task-structure mismatch，而不是“还差一个 recipe”。

### Fig. 5. Axis-level interpretation is informative but remains partially supported

这一图对应模板中 interaction-class decomposition 的作用：把总体结果拆成结构类别，但不把类别解释抬升为过强机制主张。

- a. Axis-level explanatory scatter：shift R2 vs dependency R2，标出 transcription/chromatin。
- b. Formal axis call summary：shared backbone axis、transcriptomic-heavy axis、dependency-heavy axis、preliminary axes。
- c. Bootstrap stability heatmap：各 axis dominant call 与 stability。
- d. Axis validation dot plot：enrichment hits、database support、per-target consistency。
- e. Transcription/chromatin focus：shift R2 = 0.092，dep R2 = 0.000，targets = ENY2/TADA3。
- f. Broader partially supported axes：chromatin remodeling、TGF-beta/BMP、ER stress/UPR、RNA processing、ribosome/nucleolar。
- g. Preliminary/mixed axis panel：显示多数 axes 为 supporting/preliminary/mixed，而非同级 formal。
- h. Axis boundary strip：transcription/chromatin = primary_axis_but_qualified；禁止 fully established shared explanatory architecture。

### Fig. 6. Covariate, temporal and endpoint analyses define the final claim boundary

这一图承担模板 Discussion 前的收口作用：把 robustness、外部 context 与 limitation 放到主图，而不是只藏进补充材料。

- a. Covariate audit overview：barcode_gem_group、protospacer axes、UMI/transcriptome signal axes、detected genes axes。
- b. Anchor claim tier before/after covariate audit：PFDN5 保留 primary_but_qualified；PMF1/PRPF6/ZNF131 降为 supporting_only。
- c. barcode_gem_group boundary：HCC38 -> aggrMH001-3；HCC1143 -> aggrMH004-6；design-proxy not run-resolved。
- d. K562 temporal panel overview：GSE90063 7d/13d、formal bridgeable targets、13d primary supplementary test、7d early-bridge probe。
- e. Temporal architecture panel：7d 与 13d 均为 backbone_plus_shift_excess；7d rank alignment stronger，13d mean shift larger。
- f. A0/A1/B supplementary tier matrix：A0 confirmed；A1 supporting；B not eligible。
- g. Endpoint hierarchy plot：HCC38、HCC1143、K562 7d、K562 13d 中 CRISPR bridge Spearman 均强于 RNAi DEMETER2。
- h. Final boundary strip：CRISPR = primary bridge readout；RNAi = weaker sensitivity endpoint；K562 not primary co-pillar；discovery gated。

## 主文 Results 与主图对应关系

这个版本的 Results 不应按“分析执行时间线”写，而应按模板式图版推进：

1. Fig. 1 对应 Results 1 的前半段：先定义 benchmark object，证明问题不是模型榜单，而是 fitness-relevant bridge architecture。
2. Fig. 2 对应 Results 1 的后半段：把 truth object 下钻到 anchor 层，并立即完成 evidence tiering。
3. Fig. 3 对应 Results 2 的主结论：当前 entrants 没有赢 backbone baseline，但 reveal trade-off。
4. Fig. 4 对应 Results 2 的解释收口：GEARS sweep 与 linear controls 排除“缺 recipe/缺 coverage”作为最简单解释。
5. Fig. 5 对应 Results 3：axis interpretation 是 partial/tiered，而不是 fully closed mechanism。
6. Fig. 6 对应 Results 4-6：covariate、K562 temporal panel 与 endpoint hierarchy 共同定义 final claim boundary。

因此，正文顺序建议调整为：

1. A truth-first benchmark defines a structured bridge object.
2. Shared anchors support the bridge but require tiered claim strength.
3. Entrants expose a backbone-separation trade-off rather than model recovery.
4. Recipe and embedding controls do not close the backbone gap.
5. Axis-level interpretation remains partial and tiered.
6. Covariate, temporal and endpoint analyses bound the final claim.

## 模板对齐说明

`s41592-025-02772-6.pdf` 的主线是：简单 baseline 挑战深度模型，然后用两张主图完成 double perturbation 与 single perturbation 的证据闭环。它的 Fig. 1 不是单纯画分数，而是在同一张图中放入 prediction error、representative example、interaction definition、interaction class composition 与 prediction class decomposition。它的 Fig. 2 则进一步用 single perturbation、linear model schematic 与 pretrained embedding controls 检查“深度模型为什么没有赢”。

本手稿应借鉴这三个结构，而不是照搬图数：

- 总览图必须有强对照：本稿中对应 Fig. 3 的 baseline vs GEARS/entrants。
- 代表例必须服务主结论：本稿中对应 Fig. 2 的 anchor mini-panels 与 Fig. 3 的 recovery example。
- 分解图必须解释失败模式：本稿中对应 Fig. 4 的 sweep/linear controls 与 Fig. 5 的 axis tiering。
- robustness 和 limitation 要进入主图：本稿中对应 Fig. 6 的 covariate、K562 temporal、endpoint hierarchy。

与模板相比，本稿多出的必要层是 truth object。模板可以直接评估 prediction error，因为 ground truth 是 observed expression；本稿必须先证明 truth object 本身可定义、可分解、可审计。因此 Fig. 1 和 Fig. 2 是本稿不可省略的前置图。

## 主图图注草案

### Fig. 1 | A truth-first benchmark defines the fitness-relevant transcriptomic bridge object.

a, Overview of the truth-first architecture-aware benchmark. Real perturbation transcriptomic shifts are first aligned to DepMap dependency endpoints to define a frozen bridge object; models are then evaluated for recovery of this object, and discovery remains a gated downstream layer. b, Dataset and endpoint summary for the HCC primary analysis, including HCC38/HCC1143 truth data, the primary transcriptomic metric `real_shift_mean_abs`, and the matched CRISPR DepMap dependency endpoint. c, Definition of the target-level joint grid. Targets are stratified by transcriptomic shift and aligned dependency strength into Q1 anchor, Q2 transcriptomic excess, Q3 dependency excess and Q4 low-information regions, with middle-band targets retained rather than forced into quadrant calls. d,e, HCC38 and HCC1143 joint grids. f, Composition of the target-level grids across HCC38 and HCC1143. g, Summary of bridge strength and bridgeable target counts for the two HCC contexts. h, Claim boundary for the truth object: the bridge is retained at the global and structural level, but this does not establish fully deconfounded causal evidence.

### Fig. 2 | Shared anchors form a tiered target-level bridge rather than clean primary objects.

a, Ranking of shared canonical anchors by transcriptomic and dependency quantiles. b, Recurrence of Q1 anchor calls across HCC38 and HCC1143. c, Cutoff sensitivity of the stable shared anchors. PFDN5, PMF1, PRPF6 and ZNF131 retain shared-anchor status across the tested cutoffs. d, Representative anchor-level shift and dependency profiles for PFDN5 and supporting shared anchors. e, Cutoff-sensitive supporting objects that remain informative but are not eligible for primary anchor wording. f, Evidence-tier summary for target-level bridge objects. g, Final anchor-level claim matrix after covariate-aware tiering. h, Disallowed wording boundary: stable anchors must not be described as fully deconfounded strongest anchors, and no single anchor is sufficient to prove the bridge.

### Fig. 3 | Current entrants do not outperform the backbone baseline but reveal a recovery trade-off.

a, Backbone recovery scores for the HCC formal model comparison. b, Heatmap of the three adjudication metrics: backbone recovery, shift-excess identification and structure-vs-context separation. c, Headline comparison between the shared-mean baseline and the formal GEARS recipe. The baseline shows stronger backbone recovery, whereas GEARS shows stronger separation. d, Trade-off scatter of backbone recovery versus structure-vs-context separation across entrants and controls. e, Representative recovery panel contrasting baseline and GEARS behavior on the frozen structure. f, Shift-excess and deviation-oriented performance, showing that separation-related gains do not translate into backbone superiority. g, Entrant family summary, including foundation-model entrants and linear controls. h, Final model-side adjudication: GEARS is positioned as an architecture trade-off diagnosis, while the shared-mean baseline remains the backbone primary reference.

### Fig. 4 | Recipe and embedding controls do not close the backbone gap.

a, Backbone recovery across the finite-budget GEARS sweep, with the shared-mean baseline shown as the reference line. b, Sweep-level trade-off between backbone recovery and structure-vs-context separation. c, Shift-excess identification across sweep candidates. d, Frozen stop-rule schematic, indicating the limited recipe dimensions tested and the absence of a new truth object or scoring system. e, Linear-control schematic for testing whether pretrained target embeddings or low-rank controls alone recover the backbone direction. f, Ranking of linear controls relative to the shared-mean baseline. g, Coverage/control panel indicating that ridge controls have complete target coverage and that the gap is not explained by missing target coverage. h, Interpretation boundary: the remaining gap is most consistent with a task-structure or direction-level mismatch, not with a missing small recipe.

### Fig. 5 | Axis-level interpretation is informative but remains partially supported.

a, Axis-level explanatory strength for transcriptomic shift and dependency. b, Formal axis-call summary, distinguishing transcriptomic-heavy, dependency-heavy, shared and preliminary calls. c, Bootstrap stability of axis calls. d, Axis validation summary integrating enrichment, database support and per-target consistency. e, Focus panel for transcription/chromatin, the strongest qualified formal axis. f, Broader partially supported axes, including chromatin remodeling, TGF-beta/BMP signaling, ER stress/UPR, RNA processing and ribosome/nucleolar axes. g, Preliminary and mixed axes that remain below primary interpretation strength. h, Axis interpretation boundary: the axis layer supports a partial and tiered explanatory architecture, not a fully established shared mechanism.

### Fig. 6 | Covariate, temporal and endpoint analyses define the final claim boundary.

a, Overview of the five covariate audit axes used for claim governance. b, Anchor claim tiers before and after covariate-aware boundary setting. c, Barcode gem group interpretation as a design-proxy axis rather than a resolved run-level covariate. d, GSE90063 K562 7d/13d temporal panel overview. e, Temporal stratification of the K562 bridge: both time points retain a backbone-plus-shift-excess architecture form, with stronger rank alignment at 7d and larger mean shift at 13d. f, A0/A1/B supplementary evidence tiering for K562. g, Endpoint hierarchy across HCC38, HCC1143, K562 7d and K562 13d, showing consistently stronger CRISPR DepMap bridge signals than RNAi DEMETER2 signals. h, Final claim boundary: CRISPR DepMap is the formal primary bridge readout, RNAi DEMETER2 is a weaker cross-platform sensitivity endpoint, K562 is not a primary co-pillar and discovery remains gated.

## 主图源数据与渲染状态

当前所有主图默认从源数据重新渲染；旧的 `reports/manuscript_figures/figure1/` 产物不再作为设计输入，也不再作为可复用 panel。这样可以避免旧版 4 图逻辑污染当前 6 图主线。

### Fig. 1

- a 需要新画 schematic；来源于 `README.md`、`docs/project_state_summary_v1.md` 与 `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`。
- b 需要新画 overview table；来源于 `reports/stage2_truth_driven_bridge/cross_cell_line_consistency_summary.tsv`、`reports/stage2_truth_bridge_decomposition/run_summary.json`。
- c 可新画 schematic；规则来自 `reports/stage2_truth_bridge_decomposition/bridge_decomposition_report.md`。
- d 从 `reports/stage2_truth_bridge_decomposition/target_level_joint_grid.tsv` 重新渲染 HCC38 target-level joint grid。
- e 从 `reports/stage2_truth_bridge_decomposition/target_level_joint_grid.tsv` 重新渲染 HCC1143 target-level joint grid。
- f 需要从 `reports/stage2_truth_bridge_decomposition/target_level_grid_summary.tsv` 渲染。
- g 需要从 `reports/stage2_truth_driven_bridge/HCC38/correlation_summary.tsv`、`reports/stage2_truth_driven_bridge/HCC1143/correlation_summary.tsv` 渲染。
- h 需要从 `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv` 渲染。

### Fig. 2

- a 来源于 `reports/stage2_truth_bridge_decomposition/shared_canonical_anchor_summary.tsv`。
- b 来源于 `reports/stage2_truth_bridge_decomposition/target_level_joint_grid.tsv`。
- c 来源于 `reports/stage2_truth_bridge_decomposition/shared_anchor_stability.tsv` 与 `reports/stage2_truth_bridge_decomposition/anchor_cutoff_sensitivity.tsv`。
- d 来源于 `reports/stage2_truth_bridge_decomposition/target_level_joint_grid.tsv`。
- e 来源于 `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv` 与 anchor sensitivity 表。
- f 来源于 `reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv`。
- g 来源于 `reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv`。
- h 来源于 `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`。

### Fig. 3

- a 来源于 `reports/stage2_real_hcc_smoke/model_comparison.tsv`。
- b 来源于 `reports/stage2_real_hcc_smoke/model_comparison.tsv`。
- c 来源于 `reports/stage2_real_hcc_smoke/model_comparison.tsv` 与 `reports/stage2_gears_backbone_sweep/final_adjudication.md`。
- d 来源于 `reports/stage2_real_hcc_smoke/model_comparison.tsv`。
- e 来源于 `reports/stage2_real_hcc_smoke/details/*/*/structure_scores.tsv`、`axis_projection.tsv` 或 `target_expression_metrics.tsv`。
- f 来源于 `reports/stage2_real_hcc_smoke/model_comparison.tsv` 与 `reports/stage2_gears_backbone_sweep/batch_run/batch_status.tsv`。
- g 来源于 `reports/stage2_real_hcc_smoke/model_comparison.tsv`。
- h 来源于 `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`。

### Fig. 4

- a 来源于 `reports/stage2_gears_backbone_sweep/batch_run/batch_status.tsv` 与 `reports/stage2_real_hcc_smoke/model_comparison.tsv`。
- b 来源于 `reports/stage2_real_hcc_smoke/model_comparison.tsv`。
- c 来源于 `reports/stage2_real_hcc_smoke/model_comparison.tsv`。
- d 来源于 `reports/stage2_gears_backbone_sweep/final_adjudication.md` 与 `reports/stage2_gears_backbone_sweep/candidate_manifest.tsv`。
- e 需要新画 schematic；来源于 HCC formal entrant/control recipe 文档。
- f 来源于 `reports/stage2_real_hcc_smoke/model_comparison.tsv`。
- g 来源于 HCC prediction contract validation 与 `docs/stage2_fuller_hcc_model_comparison_note_v1.md`。
- h 来源于 `docs/model_vs_baseline_deeper_explanation_note_v1.md`、`docs/model_vs_baseline_next_step_breakdown_v1.md`。

### Fig. 5

- a 从 `reports/stage2_truth_bridge_decomposition/axis_level_shared_explanatory_summary.tsv` 重新渲染 axis-level explanatory scatter。
- b 来源于 `reports/stage2_truth_bridge_decomposition/axis_level_shared_explanatory_summary.tsv`。
- c 来源于 `reports/stage2_truth_bridge_decomposition/axis_bootstrap_stability.tsv`。
- d 来源于 `reports/stage2_axis_analysis/axis_validation_summary.tsv`。
- e 来源于 `reports/stage2_truth_bridge_decomposition/bridge_decomposition_report.md` 与 `reports/stage2_axis_analysis/axis_summary.tsv`。
- f 来源于 `reports/stage2_axis_analysis/axis_validation_summary.tsv`、`axis_summary.tsv` 与 `axis_enrichment.tsv`。
- g 来源于 `reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv` 与 `reports/stage2_axis_analysis/axis_validation_summary.tsv`。
- h 来源于 `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`。

### Fig. 6

- a 来源于 `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv`。
- b 来源于 `reports/stage2_truth_driven_bridge/sensitivity/anchor_claim_tiering.tsv` 与 `final_claim_matrix.tsv`。
- c 来源于 `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/barcode_gem_group_mapping_note.md`。
- d 来源于 `reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_bridge_summary.tsv`、`temporal_structure_summary.tsv`、`temporal_panel_report.md`。
- e 来源于 `reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_panel_calls.tsv` 与 `temporal_target_delta.tsv`。
- f 来源于 `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_evidence_tier_summary.tsv`、`reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_7d/dixit_evidence_tier_summary.tsv`。
- g 来源于 `reports/stage2_truth_driven_bridge/endpoint_consistency_summary_table.md`、`hcc38_hcc1143_rnai_endpoint_consistency/endpoint_consistency_summary.tsv`、`k562_rnai_endpoint_consistency/endpoint_consistency_summary.tsv`。
- h 来源于 `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`。

## 主图渲染执行规格

### 输出目录

所有新版主图统一输出到：

`reports/manuscript_figures_v2/`

每张图单独一个目录：

- `reports/manuscript_figures_v2/fig1_truth_object/`
- `reports/manuscript_figures_v2/fig2_anchor_tiering/`
- `reports/manuscript_figures_v2/fig3_model_tradeoff/`
- `reports/manuscript_figures_v2/fig4_sweep_controls/`
- `reports/manuscript_figures_v2/fig5_axis_tiering/`
- `reports/manuscript_figures_v2/fig6_boundary/`

每张主图至少输出：

- `figureX.pdf`
- `figureX.png`
- `figureX_source_data.tsv`
- `figureX_panel_manifest.json`

其中 `panel_manifest.json` 记录每个 panel 的源文件、过滤条件、主要字段、claim boundary 与渲染函数。这样后续改图时不需要重新理解全项目。

### 统一视觉规则

参考模板的图版风格，当前建议：

- 主体使用灰色/黑色作为基础，不使用装饰性渐变。
- 只保留 2-3 个强调色：baseline、GEARS、qualified primary evidence。
- 所有主图 panel label 使用小写 `a-h`。
- 图内标题短句化，优先写判断，不写解释性长句。
- 图注承担方法细节，panel 内只放必要标签。
- 每张图底部保留一个 boundary strip，防止读者把结果读成 overclaim。
- 每个 quantitative panel 都要能追溯到 `figureX_source_data.tsv`。

推荐语义配色：

- `shared_mean_baseline`：深灰/黑。
- `GEARS`：蓝色。
- 其它 entrants：浅灰或淡蓝灰。
- `primary_but_qualified`：绿色。
- `supporting_only`：黄色/橄榄色。
- `not eligible / disallowed`：浅红或灰红。
- covariate/design-proxy boundary：紫灰或中性灰，不作为主强调色。

### 渲染顺序

1. 先重画 Fig. 3，因为它是模型侧主卖点，也是最像模板论文 headline benchmark 的图。
2. 再画 Fig. 1 和 Fig. 2，保证 truth object 与 anchor tier 能支撑 Fig. 3。
3. 画 Fig. 4，用来关闭“是不是 recipe/coverage 问题”。
4. 画 Fig. 5，作为 axis 解释层。
5. 最后画 Fig. 6，把 covariate、K562 与 endpoint hierarchy 收成 final boundary。

如果投稿篇幅必须压缩，优先压缩策略不是删掉 Fig. 6，而是：

- Fig. 1 与 Fig. 2 可合并为一个 truth-object figure。
- Fig. 3 与 Fig. 4 可合并为一个 model-adjudication figure。
- Fig. 5 可降为 Extended Data，前提是在主文 Fig. 1/2 中保留 transcription/chromatin 的 tier 信息。
- Fig. 6 必须保留，因为 limitation-bounded closure 是当前项目能防守的关键。

### 需要新画的 schematic

以下 panel 不是从单表直接画出来，需要手工/脚本化绘制 schematic：

- Fig. 1a：truth-first benchmark workflow。
- Fig. 1c：Q1-Q4 joint-grid definition。
- Fig. 3e：representative recovery panel，需从 detail tables 选一个稳定对象或 target subset。
- Fig. 4d：GEARS sweep stop-rule schematic。
- Fig. 4e：linear-control schematic。
- Fig. 4h：task-structure mismatch interpretation strip。
- Fig. 6h：final boundary matrix。

其余 panel 原则上都应由 TSV/JSON/MD 源数据直接渲染。

### 不再使用的旧产物

以下旧图版产物已经不再作为当前手稿输入：

- `reports/manuscript_figures/figure1/`
- 任何基于旧 4 图方案的 combined figure。
- 任何直接从 legacy `dixit_2016_raw__control_context` 得出的 Dixit/K562 figure。

K562 相关图只允许使用 `GSE90063 K562 13d/7d temporal panel` 的正式产物。

## 补充图建议

参考模板的 Extended Data 逻辑，补充图不承担新主张，只承担 robustness、alternative metrics、dataset overview、资源/流程透明化。

1. Extended Data Fig. 1：dataset overview、HCC/K562 target admission、DepMap endpoint mapping。
2. Extended Data Fig. 2：完整 target-level joint grid 与所有 target 标签。
3. Extended Data Fig. 3：anchor cutoff sensitivity、control subsampling 与 formal interval。
4. Extended Data Fig. 4：full HCC entrant comparison、per-cell-line model metrics 与 alternative recovery summaries。
5. Extended Data Fig. 5：GEARS backbone sweep 全候选、recipe summary 与 batch status。
6. Extended Data Fig. 6：full axis enrichment、bootstrap 与 per-target consistency。
7. Extended Data Fig. 7：K562 13d/7d temporal panel 细节与 A0/A1/B tier evidence。
8. Extended Data Fig. 8：CRISPR DepMap vs RNAi DEMETER2 endpoint consistency 细节。
9. Extended Data Fig. 9：covariate audit per-axis/per-target detail。
10. Extended Data Fig. 10：final claim matrix、allowed/disallowed wording 与 reproducibility/runtime entrypoints。

## 需要同步到投稿版本的禁写边界

- 不写 model recovery proved。
- 不写 GEARS overall winner。
- 不写 fully deconfounded anchors。
- 不写 fully established shared explanatory architecture。
- 不写 K562 primary co-pillar。
- 不写 content-level replication confirmed。
- 不写 broad cross-context validation。
- 不写 RNAi primary evidence。
- 不写 external model-side generalization proved。
- 不把 discovery 写成当前 formal primary deliverable。
