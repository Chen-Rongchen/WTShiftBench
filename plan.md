# WT Benchmark — Active Plan（Truth-First Architecture and Model Recovery）

## 1. 项目状态一句话

本项目没有放弃原有 `Stage 1A / 1B / 2 / 3` 路线，但当前主线已经重排为 **truth-first fitness-bridge architecture**：先在真实 genetic perturbation transcriptomic truth 中定义可桥接到 cellular fitness / dependency（DepMap）的结构化对象，再评估模型能否恢复这套 structure，再把 `Stage 1A / 1B` 重新解释为 failure decomposition track，最后才进入 discovery。当前最重要的已完成项是 **HCC truth bridge architecture contract freeze + GEARS entrant-qualified HCC smoke closure + GEARS 有限 backbone sweep 收口 + `scGPT / Geneformer` 第一轮 HCC formal integration + `lm_train_lowrank / lm_G_scgpt_ridge / lm_G_geneformer_ridge` 第一轮 HCC formal integration + frozen axis 第一轮 annotation / validation 闭环 + truth bridge decomposition evidence tiering（含 cutoff sensitivity / bootstrap stability）+ SCP542 boundary / Dixit supplement 刷新 + `GSE90063 K562 13d-only` supplementary architecture-form / bridge-form support 收口 + Dixit supplementary startup packet 补齐 + GEARS / truth bridge / axis / Dixit supplement / Stage 1A / 1B failure decomposition 的主文档口径收束**；当前最重要的未完成项是 **把这组结果系统压进 final claim matrix、covariate / sensitivity closure 与 manuscript wording，并完成 `Stage 1A / 1B` failure decomposition 的正式解释层**。新增数据口径警报：`data/raw/stage1a/candidates/dixit_2016_raw.h5ad` 与 GSE90063 K562 TF pool 描述不匹配，当前按 Frangieh-like legacy object 处理，不再作为有效 Dixit 输入引用。

## 2. 下次进来先做什么

如果你只看一段，这一段就是当前执行口径。

当前不要无边界继续扩到 `challengers`，也不要回到 HCC truth-side 重做 contract。`scGPT / Geneformer` 已完成第一轮 HCC entrant 接入；当前近端主线已经进一步收紧为：**先把论文核心主张固定为 transcriptomic perturbation structure 能否桥接 DepMap fitness/dependency，并把 `GSE90063 K562 13d-only` 已得到的 supplementary-level architecture-form / bridge-form support 压进正式 wording；随后继续收口 HCC covariate / sensitivity / final claim boundary，discovery 继续 gated。**

如果下次进来只想知道“先看哪里就够”，固定只看这三个入口：

1. `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv`
2. `README.md`
3. `plan.md`

默认先用这三个入口刷新状态，不再从更长的结果清单开始。

下次进来应直接做：

1. 先看当前最近一次 covariate 正式产物：
   - `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv`
   - `docs/stage2_covariate_balance_closure_note_v1.md`
   - `docs/stage2_sensitivity_full_closure_note_v1.md`
2. 先记住当前 5 条已落盘 covariate 轴：
   - `barcode_gem_group`
   - `num_umis_quantile_bin`
   - `num_umis_over_threshold_bin`
   - `transcriptome_total_signal_quantile_bin`
   - `transcriptome_detected_genes_quantile_bin`
3. 当前方法学结论先固定为：
   - `barcode_gem_group` 是更接近实验设计 aggregation 结构的代理轴
   - 它整体更轻，但没有改写 anchor tier
   - 当前仍不能写成 `fully deconfounded`
4. 如果继续推进实现，按这个顺序做：
   - 当前这一步已完成收口：可确认 `HCC38 -> aggrMH001-3`、`HCC1143 -> aggrMH004-6`
   - 当前仍不能把 `-1/-2/-3` 唯一映射到单个 `MH001...MH006`
   - 因此从现在起直接把 `barcode_gem_group` 固定写成 design-proxy axis
   - 再继续同步 `final claim matrix -> manuscript wording`
   - `discovery 继续 gated`
5. 如果继续推进 Dixit / K562，不再做 feasibility（已通过），而是直接做 wording freeze 与 manuscript sync：
   - 历史 `dixit_2016_raw__control_context` 入口当前按 `legacy / 暂停引用` 处理，不再作为可写入主文的 Dixit 证据
  - `GSE90063 K562 13d-only` 已作为 formal supplementary external evidence 纳入项目正式证据体系
  - 定位是 `formal supplementary, not formal primary`：A0 architecture form 已 confirmed，A1 bridge form 当前为 supporting / partial-support，但不是与 HCC 对称的 co-primary
   - 剩余工作：冻结 admission note、positive/partial/negative 判据 wording，同步进 `final claim matrix` 与 `manuscript wording`
   - `13d` 只能写成与 DepMap `~14-21d` fitness screen 的 `time-scale compatible`，不能写成 `matched endpoint`
   - `Dixit 7d` 与 `Replogle 7d CRISPRi` 暂时只作为 temporal / cross-modality exploration，不进入 primary closure
6. 如果继续推进写作，只优先做：
   - 把 design-proxy / design-mapping 的新状态压进主文稿与边界文档
   - 继续维持 `PFDN5 = primary_but_qualified`、`PMF1 / PRPF6 / ZNF131 = supporting_only`
   - 把 `PFDN5` 等具体 anchor / axis 明确放在 bridge content 层，不让它们承载 architecture-to-DepMap bridge 的主卖点
7. 如果继续推进论文图片，只优先做：
   - 先打开 `docs/manuscript_figure_blueprint_v1.md`
   - 主图顺序固定为 `truth bridge -> model trade-off -> axis validation -> covariate boundary + Dixit`
   - 风格参考固定为 `s41592-025-02772-6.pdf`
8. 如果目标是一次性收口当前项目：
   - `docs/finalization_punchlist_v1.md`
   - `docs/current_closeout_commit_note_v1.md`
9. 仍然明确不做：
   - 新 entrant
   - 无判据、无 feasibility check 的新 truth object
   - 新评分体系
   - 回头继续为 `GEARS backbone sweep` 开第二轮无限调参
   - 在 design-layer mapping 仍不清楚时提前放开发现层

### 现在优先打开的文件

下次进来先看这些结果：

- `reports/stage2_gears_backbone_sweep/final_adjudication.md`
- `docs/stage2_truth_bridge_integrated_result_v1.md`
- `reports/stage2_truth_bridge_decomposition/bridge_decomposition_report.md`
- `reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv`
- `reports/stage2_real_hcc_smoke/model_comparison.tsv`
- `docs/stage2_axis_annotation_result_v1.md`
- `reports/stage2_axis_analysis/axis_validation_summary.md`
- `reports/stage2_axis_analysis/axis_annotation_brief.md`
- `reports/stage2_axis_analysis/README.md`
- `docs/stage2_dixit_supplementary_evidence_tier_v1.md`
- `docs/stage1_failure_decomposition_note_v1.md`
- `docs/next_phase_execution_note_v1.md`
- `docs/project_state_summary_v1.md`
- `docs/finalization_punchlist_v1.md`
- `docs/current_closeout_commit_note_v1.md`

## 3. 当前正式裁决

当前最稳的项目表述不是“GEARS 已整体胜出”，而是：

> GEARS 展现出选择性结构优势：它更擅长把 structure 和 context deviation 分开，并在部分 cell line 上更能识别 shift-excess；但在当前 HCC primary adjudication 中，canonical backbone recovery 仍落后于 `shared_mean_baseline`。

这条线当前已经按 stop rule 收口，因此它现在决定的不是“下一步继续怎么调”，而是：

- `GEARS` 应固定写成 `architecture trade-off diagnosis`
- 不再把“再跑一轮 sweep”当默认动作
- 不把辅助指标升级成新的主裁决层
- 不再为“为什么模型没稳定赢 baseline”继续扩对象

## 4. 当前 stop rule

这一步必须有停止规则，避免 endless tuning。

如果一轮有限预算 sweep 后，`canonical_backbone recovery` 仍不能接近或追平 `shared_mean_baseline`，且任何改进都以明显损失 `structure/context separation` 为代价，则停止继续把 `GEARS` 推为 HCC primary winner，并将当前结果收口为 architecture trade-off diagnosis。

到那时，最稳的正式结论应写成：

- `shared_mean_baseline` 仍是 backbone 更强的 primary reference
- `GEARS` 代表一种 structure/context separation-biased entrant
- 它的价值在于揭示 architecture trade-off，而不是整体胜出

## 5. Governing Roadmap（重排，不是替换）

### Layer A. Truth Architecture Discovery

这一层先回答“真实扰动转录组结构能否桥接到 fitness / dependency readout”，而不是只回答“转录组内部有没有结构”，也不是“模型表现如何”。

- `HCC` truth bridge layer：在 `HCC38 / HCC1143` 的 14d truth 中定义 primary truth-driven bridge object。
- axis compression layer：把可桥接结构压缩为可冻结、可审计的 axis / backbone object。
- SCP542 explanation boundary：作为 calibration / explanation layer，而不是主 biological conclusion。
- Dixit/K562 external structure replication：`GSE90063 K562 13d-only` 已完成 feasibility check，作为 architecture-to-DepMap bridge 的 formal supplementary external context；剩余工作是 wording freeze 与 manuscript sync。它复现的是 bridge architecture form（A0 confirmed / A1 supporting），不是 HCC anchor gene identity overlap（B 层 not eligible）。

这一层的目标是冻结“真实 perturbation transcriptomic structure 中哪些成分能以时间尺度兼容的方式桥接 DepMap fitness/dependency”，不是给模型打分。

### Layer A/B 主张分层

- Architecture-to-DepMap bridge form：主卖点。问题是 `backbone + shift-excess / context deviation` 这类扰动转录组结构能否桥接 cellular fitness / dependency。跨 context 复现的是结构形式，不要求同一批 gene identity 重叠。
- Bridge content：次级、受限主张。问题是具体哪些 genes 是 anchors、哪条 axis 最强。这一层需要 target identity 复现、更多 anchor 与更严格混杂控制；当前 HCC 中仍应维持 `PFDN5 = primary_but_qualified`，`PMF1 / PRPF6 / ZNF131 = supporting_only`。

**主裁决三指标**（必须同场，共同定义 architecture-aware adjudication）：

- `backbone_recovery_score`：模型是否恢复 frozen canonical backbone
- `shift_excess_identification_score`：模型是否能识别超出 backbone 预测的过度偏移
- `structure_vs_context_separation_score`：模型是否把 backbone 与 context deviation 分开

**补充审计四模块**（降位使用，是解释层，不是主裁决层）：

- `Spearman(E, ΔT)`：rank-based scalar association，bridge-form 主关联指标
- `E-distance`：embedding-space state displacement audit，与 Spearman 为互补维度，不是竞争指标
- Essentiality stratification（tier 1–4）：解释 bridge 为什么非线性；是可解释性 scaffold，不是 orthogonal validation
- Stress-removed sensitivity：判断 bridge 是否只是"濒死程序"驱动

**两处禁止表述**（已写入 governance 文档）：

- 禁止：`essentiality stratification independently validates the architecture-level adjudication`
- 禁止：`E-distance underperforms Spearman as a headline metric`

### Layer B. Model Recovery Adjudication

这是当前最近一步，也是当前 active mainline。

核心问题不是单基因拟合，而是 architecture recovery：

- Backbone recovery：模型能否恢复 frozen canonical backbone。
- Shift-excess identification：模型能否识别 shift-excess 对象，而不是只学到 shared mean trend。
- Structure vs context separation：模型能否把 shared backbone 与 context deviation 分开。
- Architecture-level evaluation：主问题是 structure recovery，而不是用 global Pearson 代替 architecture adjudication。

而如果继续推进 baseline-vs-model explanation，默认要再收缩成两个更小的问题：

- `baseline winner` 是否主要由 shared backbone objective 决定
- entrant 的额外能力是否稳定落在 `separation / deviation` 而不是 backbone 上

### Layer C. Failure Decomposition Across Stage 1A / 1B

`Stage 1A / 1B` 仍然有效，但角色已经改变。

- `Stage 1A` 不再只是 leaderboard，而是 short-horizon failure decomposition 的第一层。
- `Stage 1B` 不再只是时间外推 stress test，而是 long-horizon / temporal structure degradation 的诊断层。
- 二者当前要回答的问题是：模型丢掉的是 backbone、shift-excess、context specificity，还是出现了 temporal degradation / context averaging。

因此 `Stage 1A / 1B` 不是废弃，而是被重新解释为 frozen truth architecture 下的 failure decomposition track。

### Layer D. Discovery / Phenotype Shifter

discovery 仍然保留，但当前应后置。

- 它必须建立在 truth-side 与 model-side 都闭环之后。
- 当前不能把它写成 primary active deliverable。
- 当前阶段只可将其保留为 downstream application layer，而不是 formal near-term mainline。

## 6. Frozen Objects（已冻结对象与历史对象）

- Truth Architecture Contract：冻结 truth-side bridge object 的主定义与边界，是当前 architecture adjudication 的上位对象。
- HCC Master Atlas：冻结 HCC 主线 shared structure 的主 atlas，用于后续 model-side 投影与 adjudication。
- HCC Fine Axes：冻结 HCC 内部更细的 axis / subtype-like structure，用于区分 backbone、shift-excess 与 context deviation。
- Dixit Master Atlas：历史对象来自 `dixit_2016_raw__control_context` 输入，当前按 `legacy / 暂停引用` 处理；后续需由 `GSE90063` 重建后再恢复为可冻结对象。
- Structure Replication Summary：冻结 HCC 与 supplementary external structure replication 的摘要对象，回答”复现的是 architecture，而不是 gene identity overlap”。
- SCP542 Boundaries：冻结 SCP542 的 explanation / calibration 边界，明确其不是主 biological conclusion。
- Dixit K562 13d Supplementary Bridge：truth-side bridge 与 axis compression 已完成第一轮运行，当前作为 formal supplementary external evidence（A0 architecture form confirmed；A1 bridge form supporting / partial-support；B 层 not eligible）；剩余工作是 admission note wording freeze、positive / partial / negative 判据冻结与 manuscript sync。

## 7. What Is Actually Closed vs Not Yet Closed

### Closed / Frozen

- truth-side architecture contract
- HCC primary structure definition
- HCC master atlas / fine axes
- SCP542 explanation boundaries
- truth-driven bridge 的主报告边界、dataset role 与 evidence tier governance
- GEARS HCC38 / HCC1143 real raw output
- GEARS export to `stage2_truth_aligned_log_shift`
- GEARS contract validation on HCC38 / HCC1143
- GEARS entrant-qualified HCC smoke adjudication
- GEARS 有限预算 backbone sweep 与 stop-rule 裁决
- HCC 辅助裁决层：`cosine`、`L2`、`top-20 overlap`
- frozen axis 的第一轮 annotation / validation 闭环
- truth bridge decomposition 的 cutoff sensitivity / bootstrap stability / evidence tiering

### Not Yet Closed

- 比较：fuller HCC model comparison 的最终主文稿整合
- 敏感性：sensitivity full closure（当前主支柱与 formal interval 已基本到位，但仍未 fully closed）
- 混杂：covariate balance closure
  - 当前已完成 5 条轴的正式审计，并已补到 `barcode_gem_group` 这条设计层代理轴
  - 当前已确认 `HCC38 -> aggrMH001-3`、`HCC1143 -> aggrMH004-6`
  - 但 `-1/-2/-3` 仍不能唯一写成单个 `MH00x`
  - 因此当前正式口径固定为 `design-proxy axis`，仍是“风险已治理进边界”，不是“fully deconfounded”
- 最终边界：终局 claim boundary 与 `final claim matrix -> manuscript wording` 的持续同步
- discovery：继续保持 phenotype shifter 为 `gated_downstream_layer`
- Dixit K562 13d-only：
  - 历史 `dixit_2016_raw__control_context` 对象与 GSE90063 K562 TF pool 不一致，当前不能继续作为 Dixit 证据引用
  - 当前混合时间点版本不能直接升级为 primary
  - `GSE90063` 重建的 `K562 13d-only` 当前最稳地支持 supplementary-level 的 architecture-form / bridge-form support：A0 architecture form 已 confirmed，A1 bridge form 当前为 supporting / partial-support；它可复现 `backbone + shift-excess` 架构形式，并在 `n=10` 个可桥接 targets 上呈现与 DepMap 方向一致、时间尺度兼容的 bridge 信号
  - 但由于 target 数仍有限、主导 macro class 与 HCC 仍表现出明显的 context specificity，这些结果不能升级为 shared mainline architecture content、broad cross-context validation 或与 HCC 对称的 primary conclusion
  - `13d` 与 DepMap `~14-21d` 只能写成 `time-scale compatible`，不是 `matched endpoint`
  - 若结果为 negative，不能事后降级为“只是 supplement”；应按预冻结标准诚实报告 tested condition 下未复现 bridge

当前不能把这些未闭环项写成“Stage 2 complete”或“Stage 3 complete”。

## 8. Immediate Priorities

1. 主张层：把项目主卖点固定为 `transcriptomic perturbation structure -> DepMap fitness/dependency` 的 architecture-aware bridge，而不是单纯 transcriptomic clustering
2. 最终边界：持续同步 `final claim matrix -> manuscript wording`；这是当前最关键的近端收口动作
3. 混杂：停止继续追写单个 `MH00x` 映射，固定 `barcode_gem_group = design-proxy axis`，并同步到正式措辞
4. 敏感性：基于最新 5 轴 covariate 状态维持 `formal interval citable but not fully closed`
5. Dixit/K562：在完成历史对象数据身份纠偏（`dixit_2016_raw__control_context -> legacy / 暂停引用`）后，把 `GSE90063 K562 13d-only` 已得到的 supplementary-level architecture-form / bridge-form support 正式压进 manuscript wording，并继续冻结 positive / partial / negative 判据
6. 比较：推进 fuller HCC model comparison 的最终整合
7. `Stage 1A / 1B`：完成 failure decomposition 的正式解释层
8. discovery：继续保持 phenotype shifter 为 `gated_downstream_layer`，不提前进入 formal deliverable

### 8.0 当前默认执行入口

如果这一轮是为了把当前 completion roadmap 继续推进到可执行状态，而不是只改文稿，默认先跑：

```bash
pixi run --environment core run-stage2-closure-pipeline
pixi run --environment core validate-stage2-closure-artifacts
```

然后按需要再跑：

```bash
pixi run --environment core build-stage2-truth-bridge-decomposition
pixi run --environment core build-stage2-truth-driven-bridge-dixit-supplement
pixi run --environment core run-stage2-dixit-axis-compression
pixi run --environment core render-manuscript-figure1
```

其中 git 版本管理当前默认只跟踪代码、配置、文档与测试；`.gitignore` 已明确忽略 `reports/`、`data/processed/`、`results/` 等运行产物，因此本地重跑结果默认不进入提交范围。

### 8.1 当前推荐执行顺序

如果只按最近两天最值得做的顺序推进，固定为：

1. 先收口 `final claim matrix -> manuscript wording`
2. 再收口 `covariate balance closure`
3. 再收口 `sensitivity full closure`
4. 把 `GSE90063 K562 13d-only` 的 supplementary-level architecture-form / bridge-form support 压进总入口与主文稿
5. 推进 fuller HCC model comparison 的最终整合
6. 最后补齐 `Stage 1A / 1B` failure decomposition 的正式解释层

## 9. Explicit Non-Goals for the Current Phase

- 不把现有混合时间点 Dixit/K562 写成与 HCC 并列的 primary biological conclusion
- 不把 `Dixit K562 13d` 写成 HCC anchor / axis content 复现；它最多检验 architecture-to-DepMap bridge form
- 不把 `13d` 写成与 DepMap `~14-21d` 的严格 matched endpoint，只写成 time-scale compatible
- 不把 `Dixit 7d` 或 `Replogle 7d CRISPRi` 提前纳入 primary closure；它们只适合作为 temporal / cross-modality exploration
- 不把 SCP542 写成强机制锚定或主结论层证据
- 不把 global Pearson 当成 architecture recovery 的替代
- 不把 phenotype shifter discovery 提前写成 formal deliverable
- 不把 `Stage 1A / 1B` 视为废弃
- 不把 model-side recovery 写成已经被证明
- 不把 `GEARS` 当前结果写成“整体压过 shared_mean_baseline”
- 不在 `scGPT` 已完成首轮接入后继续无边界并入 `Geneformer / challengers`
- 不把 `Stage 2 / 3` 写成 fully complete

## 10. Expected Near-Term Deliverables

- GEARS trade-off diagnosis note
- truth bridge integrated result note
- axis annotation / validation result note
- Dixit supplementary evidence tier note
- Dixit K562 13d-only admission wording / claim tiering note
- `Stage 1A / 1B` failure decomposition note
- refreshed report boundary text
- main-manuscript integrated narrative draft
- main-manuscript Results-style draft
- fuller HCC model comparison note
- sensitivity full closure note
- covariate balance closure note
- final claim boundary note
- discovery gating note

## 11. Document Map

- `README.md`：仓库入口，说明当前 active framing、最近一步与 claim boundaries。
- `plan.md`：当前执行优先级，不展开长期制度。
- `docs/protocol_blueprint.md`：truth-first 长期蓝图，保留 `Stage 1A / 1B / 2 / 3` 编号但重排主线。
- `docs/next_phase_execution_note_v1.md`：下一阶段“比较、敏感性、混杂、最终边界、discovery 继续 gated”五项缺口的正式执行口径。
- `docs/next_phase_execution_checklist_v1.md`：把比较、敏感性、混杂三条线压成一页可直接执行的清单。
- `docs/project_state_summary_v1.md`：当前项目已进入“主张治理稳定化”阶段的阶段性摘要。
- `docs/finalization_punchlist_v1.md`：下次一次性完成当前项目收口的最终执行清单。
- `docs/model_vs_baseline_deeper_explanation_note_v1.md`：将 baseline 胜出的解释拆成“当前证据支持的方法学解释”与“仍属 plausible 的生物学解释”两层。
- `docs/model_vs_baseline_next_step_breakdown_v1.md`：将后续推进固定成两个更小的问题，避免回到泛泛讨论“模型为什么打不过 baseline”。
- `docs/manuscript_figure_blueprint_v1.md`：当前投稿主图的固定蓝图，规定主图顺序、panel 结构、数据源与 truth-first 讲述方式。
- `docs/main_manuscript_integrated_narrative_draft_v1.md`：当前各条结果 note 的统一主文稿整合草案。
- `docs/main_manuscript_results_draft_v1.md`：更接近论文正文 `Results` 的压缩版草案。
- `docs/stage1_failure_decomposition_note_v1.md`：`Stage 1A / 1B` 作为 failure decomposition track 的正式解释入口。
- `docs/stage2_truth_driven_bridge_v1.md`：truth-driven bridge 的实现边界与敏感性说明。
- `docs/stage2_truth_bridge_decomposition_v1.md`：truth–DepMap bridge 两层分解与 evidence-tier 规则说明。
- `docs/stage2_truth_bridge_integrated_result_v1.md`：整合 decomposition、axis validation、SCP542 与 Dixit supplement 的统一结果入口。
- `docs/stage2_dixit_supplementary_evidence_tier_v1.md`：Dixit/K562 supplementary external structure replication 的 evidence-tier 入口。
- `docs/stage2_fuller_hcc_model_comparison_note_v1.md`：HCC primary adjudication fuller model comparison 的解释层说明。
- `docs/why_models_do_not_stably_beat_baseline_v1.md`：为什么复杂 entrant 不能稳定胜过 `shared_mean_baseline` 的正式 explanation layer。
- `docs/stage2_sensitivity_full_closure_note_v1.md`：Stage 2 sensitivity 当前完成状态、formal closure 条件与写作边界。
- `docs/stage2_covariate_balance_closure_note_v1.md`：Stage 2 混杂 / covariate balance closure 的现状、输入需求与正式口径。
- `docs/final_claim_boundary_and_discovery_gating_note_v1.md`：终局 claim boundary 与 discovery / phenotype shifter gating 的统一收口文档。
- `docs/model_expansion_deferral_note_v1.md`：为什么当前阶段不继续扩模型进入 HCC primary mainline 的正式说明。
- `docs/next_stage_model_entrant_inventory_v1.md`：下一阶段 entrant expansion 的候选模型盘点与最小接入清单。
- `docs/next_stage_model_entrant_execution_checklist_v1.md`：下一阶段 entrant expansion 的一页式执行清单。
- `docs/entrant_family_execution_packet_v1.md`：当前 entrant family 的已完成状态与下次继续执行的固定顺序。
- `docs/stage2_linear_controls_execution_checklist_v1.md`：`lm_train_lowrank -> lm_G_scgpt_ridge -> lm_G_geneformer_ridge` 的 Stage 2 接入清单。
- `docs/current_closeout_commit_note_v1.md`：当前阶段文档收尾提交的推荐范围与提交说明。
- `docs/next_stage_startup_packet_v1.md`：下一阶段第一周最小启动包。
- `docs/stage2_scgpt_hcc_recipe_freeze_v1.md`：`scGPT` 进入 HCC Stage 2 前的第一版 recipe freeze。
- `configs/stage2/scgpt_hcc_formal_v1.json`：`scGPT` HCC Stage 2 recipe 配置。
- `scripts/run_stage2_scgpt_hcc_predictions.py`：`scGPT` HCC Stage 2 raw output producer 入口。
- `docs/stage2_geneformer_hcc_recipe_freeze_v1.md`：`Geneformer` 进入 HCC Stage 2 前的第一版 recipe freeze。
- `configs/stage2/geneformer_hcc_formal_v1.json`：`Geneformer` HCC Stage 2 recipe 配置骨架。
- `scripts/run_stage2_geneformer_hcc_predictions.py`：`Geneformer` HCC Stage 2 raw output producer 入口。
- `docs/stage2_lm_train_lowrank_hcc_recipe_freeze_v1.md`：`lm_train_lowrank` 的 HCC Stage 2 linear control freeze 与当前接入状态。
- `configs/stage2/lm_train_lowrank_hcc_formal_v1.json`：`lm_train_lowrank` HCC Stage 2 control 配置。
- `scripts/run_stage2_lm_train_lowrank_hcc_predictions.py`：`lm_train_lowrank` HCC Stage 2 raw output producer 入口。
- `reports/stage2_truth_driven_bridge/truth_architecture_contract/`：truth architecture contract 冻结产物。
- `reports/stage2_truth_driven_bridge/master_atlas/`：HCC master atlas 与 fine axes 冻结产物。
- `reports/stage2_truth_bridge_decomposition/`：target-level anchors、axis-level structure、cutoff sensitivity、bootstrap stability 与 evidence tiers。
- `reports/stage2_truth_driven_bridge/dixit_axis_compression/`：supplementary external structure replication 产物。
- `reports/stage2_truth_driven_bridge/scp542_calibration/`：SCP542 explanation boundary 产物。
- `reports/stage2_real_hcc_smoke/smoke_report.md`：当前 HCC 主裁决入口。
- `reports/stage2_real_hcc_smoke/adjudication_summary.md`：当前最稳的中文裁决摘要。
