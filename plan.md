# WT Benchmark — Active Plan（Truth-First Architecture and Model Recovery）

**Phase label（2026-04-17 更新）：Genome Biology Reviewer-Risk Reduction Phase — analysis closure 完成，infrastructure closure 完成，main figures / Extended Data / source data / supplementary workbook / submission manifest 已生成，claim boundary 已冻结；正式投稿前新增 A/B/C 三档 17 项执行清单。**

**当前不再假设只剩作者元信息和格式项。正式投稿前必须先完成 `docs/genome_biology_submission_execution_plan_v1.md` 中 A1-A12；B13-B16 强烈建议完成；C17 仅在 5-7 天内可干净闭环时执行，否则留到 revision。**

## 1. 项目状态一句话

本项目没有放弃原有 `Stage 1A / 1B / 2 / 3` 路线，但当前主线已经重排为 **truth-first fitness-bridge architecture**：先在真实 genetic perturbation transcriptomic truth 中定义可桥接到 cellular fitness / dependency（DepMap）的结构化对象，再评估模型能否恢复这套 structure，再把 `Stage 1A / 1B` 重新解释为 failure decomposition track，最后才进入 discovery。当前最重要的已完成项是 **HCC truth bridge architecture contract freeze + GEARS entrant-qualified HCC smoke closure + GEARS 有限 backbone sweep 收口 + `scGPT / Geneformer` 第一轮 HCC formal integration + `lm_train_lowrank / lm_G_scgpt_ridge / lm_G_geneformer_ridge` 第一轮 HCC formal integration + frozen axis annotation / validation 闭环 + truth bridge decomposition evidence tiering（含 cutoff sensitivity / bootstrap stability）+ covariate boundary + K562 temporal and endpoint sensitivity + final claim matrix + Genome Biology 专版手稿 + 6 张主图 + 10 张 Extended Data + supplementary workbook + submission package manifest**。当前最重要的未完成项是 **Genome Biology reviewer-risk reduction 清单、作者元信息、references、declarations、公开归档 DOI、Additional files 编号与最终人工确认**。新增数据口径警报：`data/raw/stage1a/candidates/dixit_2016_raw.h5ad` 与 GSE90063 K562 TF pool 描述不匹配，当前按 Frangieh-like legacy object 处理，不再作为有效 Dixit 输入引用。

## 2. 下次进来先做什么

如果你只看一段，这一段就是当前执行口径。

当前不要无边界继续扩到 `challengers`，也不要回到 HCC truth-side 重做 contract。`scGPT / Geneformer` 已完成第一轮 HCC entrant 接入；Genome Biology 专版材料已经生成。当前近端主线已经进一步收紧为：**主投 Genome Biology；Science Advances 仅作为需要 broad-impact 改写的冲刺备选；Advanced Science 不作为优先目标；后续先完成 reviewer-risk reduction 清单，再补作者元信息、references、declarations、公开归档 DOI 和最终人工确认。**

如果下次进来只想知道“先看哪里就够”，固定先看这四个入口：

1. `docs/genome_biology_submission_execution_plan_v1.md`
2. `docs/genome_biology_manuscript_draft_v1.md`
3. `docs/submission_readiness_checklist_v1.md`
4. `reports/manuscript_submission_package_v1/submission_package_manifest.json`

默认先用这四个入口刷新状态，不再从更长的结果清单开始。

下次进来应直接做：

0. 先按 `docs/genome_biology_submission_execution_plan_v1.md` 完成 A1-A12，并尽量完成 B13-B16：
   - A 类：framing、prior art、GEARS sweep 透明化、metric diagnostic、baseline artifact appendix、legacy 澄清、limitations、复现入口、reviewer Q&A
   - B 类：三指标 permutation null、design-proxy residualization、relaxed cutoff sensitivity、revision round admission contract confirmation
   - C 类：adjudication kit 仅在 5-7 天内能干净闭环时执行

1. 再按 Genome Biology 投稿闭环补齐人工信息：
   - 作者姓名、单位、通讯作者邮箱
   - Funding
   - Competing interests
   - Authors' contributions
   - Acknowledgements
   - References
   - Public repository / archive DOI
   - AI use statement 是否保留与最终措辞
   - Additional files 编号与上传命名

2. 先看当前最近一次 covariate 正式产物：
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
5. Dixit / K562 feasibility 与 `GSE90063 K562 13d/7d temporal panel` 第一轮结果组织已完成；现在只做 wording sync 与 claim matrix 同步：
   - 历史 `dixit_2016_raw__control_context` 入口当前按 `legacy / 暂停引用` 处理，不再作为可写入主文的 Dixit 证据
   - 固定模板：`GSE90063 K562 13d/7d temporal panel` 是同一外部 K562 TF pool context 下、对同一 DepMap endpoint 的 temporal sensitivity panel
   - `13d` 固定为 primary formal supplementary bridge test；`7d` 固定为 temporal sensitivity / early-bridge probe
   - 它不是与 HCC 对称的 co-primary，也不能写成 shared mainline architecture content、broad cross-context validation 或 external model-side generalization proved
   - 冻结解释：`7d` 和 `13d` 均确认 `backbone_plus_shift_excess`，支持同一外部 K562 context 下 architecture form 的时间稳定性
   - 冻结解释：`7d` rank alignment 更强，而 `13d` mean shift 更大，支持 bridge readout 的 temporal stratification，而不是 later timepoint 单调更强
   - 冻结解释：K562 与 HCC 的 macro class 仍为 `CONTEXT_SPECIFIC`，因此该 panel 支持的是 form-level recurrence，不支持 content-level convergence 或 external model-side generalization proved
   - 剩余工作：同步进 `final claim matrix` 与 `manuscript wording`
   - `13d` 只能写成与 DepMap `~14-21d` fitness screen 的 `time-scale compatible`，不能写成 `matched endpoint`
   - `7d` 只能写成同 context 下的 temporal sensitivity / early-bridge probe，不进入 primary closure
   - 在当前项目对象层与现行 admission/bridgeability 规则下，`7d` 与 `13d` 目前各有 10 个正式 bridgeable targets 进入 DepMap 对接；这一数字不应与原始实验设计中的 target / guide 数直接等同
   - `DEMETER2 RNAi` 现在只作为 `GSE90063 K562 7d/13d` 的 cross-platform sensitivity endpoint：`CRISPR DepMap = matched primary endpoint`；`RNAi DEMETER2 = cross-platform sensitivity endpoint`；`RNAi` 不替代 CRISPR 主线，也不提供等价 primary evidence
   - 推荐补充：运行 `13d CRISPR KO truth -> DEMETER2 RNAi endpoint`，再汇总 `CRISPR DepMap vs DEMETER2 RNAi endpoint consistency table`；这不是主线成立的前提条件
   - `Replogle 7d CRISPRi` 只作为另一个后续 short-horizon / modality-compatible external expansion 候选；正式写论文和作图前应先按 `docs/stage2_replogle_rnai_expansion_admission_contract_v1.md` 完成 admission contract 与 metadata check
6. 如果继续推进 Replogle / external 7d 扩展，先做 admission contract 与 metadata check，不直接下载大数据：
   - 默认入口：`docs/stage2_replogle_rnai_expansion_admission_contract_v1.md`
   - DepMap 侧只预设为 `RNAi/shRNA-derived dependency endpoint`，不写成 `siRNA matched endpoint`
   - 先检查 cell line mapping、gene namespace、target overlap 与 endpoint 身份
   - 若 metadata check 通过，再由用户下载 Replogle 7d CRISPRi 与 DepMap DEMETER2 / RNAi dependency 数据
   - 现有 entrant 只能在 truth-side admission 后接入，不新增 entrant family
7. 如果继续推进写作，只优先做：
   - 把 design-proxy / design-mapping 的新状态压进主文稿与边界文档
   - 继续维持 `PFDN5 = primary_but_qualified`、`PMF1 / PRPF6 / ZNF131 = supporting_only`
   - 把 `PFDN5` 等具体 anchor / axis 明确放在 bridge content 层，不让它们承载 architecture-to-DepMap bridge 的主卖点
8. 如果继续推进论文图片，只优先做：
   - 先打开 `docs/manuscript_complete_figure_plan_v1.md`（当前主图方案 of record：6 主图 + 10 Extended Data）
   - 旧 4 图版蓝图 `docs/manuscript_figure_blueprint_v1.md` 仅作 truth-first 讲述方法论模板，不再作为图版结构入口
   - 主图顺序固定为 `truth object -> anchor tiering -> model trade-off -> sweep/controls -> axis interpretation -> boundary`
   - 风格参考固定为 `s41592-025-02772-6.pdf`
9. 如果目标是一次性收口当前项目：
   - `docs/finalization_punchlist_v1.md`
   - `docs/current_closeout_commit_note_v1.md`
10. 仍然明确不做：
   - 无 admission contract 的新 entrant
   - 无判据、无 feasibility check 的新 truth object
   - 新评分体系
   - 回头继续为 `GEARS backbone sweep` 开第二轮无限调参
   - 在 design-layer mapping 仍不清楚时提前放开发现层

### 二线展开入口（仅在三个入口之外还需要下钻时使用）

本节不是"默认先看这些"。默认入口仍固定为 §2 开头的三个：`docs/genome_biology_manuscript_draft_v1.md`、`docs/submission_readiness_checklist_v1.md`、`reports/manuscript_submission_package_v1/submission_package_manifest.json`。只有当这三个入口不足以回答当前问题，才按对象类别从下面展开：

- 模型侧裁决与 backbone sweep：
  - `reports/stage2_gears_backbone_sweep/final_adjudication.md`
  - `reports/stage2_real_hcc_smoke/model_comparison.tsv`
- truth bridge decomposition 与 evidence tier：
  - `docs/stage2_truth_bridge_integrated_result_v1.md`
  - `reports/stage2_truth_bridge_decomposition/bridge_decomposition_report.md`
  - `reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv`
- axis 解释层：
  - `docs/stage2_axis_annotation_result_v1.md`
  - `reports/stage2_axis_analysis/axis_validation_summary.md`
  - `reports/stage2_axis_analysis/axis_annotation_brief.md`
  - `reports/stage2_axis_analysis/README.md`
- Dixit/K562 supplementary：
  - `docs/stage2_dixit_supplementary_evidence_tier_v1.md`
- Stage 1 failure decomposition 解释层：
  - `docs/stage1_failure_decomposition_note_v1.md`
- 阶段性状态与收口清单：
  - `docs/next_phase_execution_note_v1.md`
  - `docs/project_state_summary_v1.md`
  - `docs/finalization_punchlist_v1.md`
  - `docs/current_closeout_commit_note_v1.md`

## 3. 当前正式裁决

当前最稳的项目表述不是“GEARS 已整体胜出”，而是：

> GEARS 展现出选择性结构优势：它更擅长把 structure 和 context deviation 分开，并在部分 cell line 上更能识别 shift-excess；但在当前 HCC primary adjudication 中，canonical backbone recovery 仍落后于 `shared_mean_baseline`。

这条 trade-off 必须写成非对称：`shared_mean_baseline` 是当前更稳定、更主导的 backbone primary reference；`GEARS` 是 deviation / separation-biased entrant。不要把它写成“GEARS 和 baseline 各赢一半”，也不要把 `shift` 混成一层：shared trend / overall displacement 与超出 backbone 可解释部分的 `shift-excess` 是两件事，GEARS 的相对强项更接近后者。

`GSE90063 K562 13d-only` 的 model-side 最小审计给出的是 `partial recurrence / partial-support`：`shared_mean_baseline` 再次在 backbone recovery 上占优，而 `GEARS` 仍在 structure-vs-context separation 上更强；但 `shift-excess` 分量未复现。因此它只加固 framework-level 的 backbone-vs-separation trade-off，不支持 full three-component recurrence 或 external model-side generalization。已经完成的 `GSE90063 K562 13d/7d temporal panel` 用于回答同一 K562 TF pool 外部 context 下，`7d` 与 `13d` 接同一 DepMap endpoint 时 bridge signal 与 backbone-vs-separation trade-off 是否随时间变清楚；这不是把 `7d` 升级为第二个 primary external replication。

这条线当前已经按 stop rule 收口，因此它现在决定的不是“下一步继续怎么调”，而是：

- `GEARS` 应固定写成 `architecture trade-off diagnosis`
- 这是一条非对称 trade-off：baseline 是 backbone winner，GEARS 是 deviation / separation-biased entrant
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
- Dixit/K562 external temporal panel：`GSE90063 K562 13d-only` 已完成 feasibility check，并固定为 primary formal supplementary bridge test；`GSE90063 K562 7d` 是同一外部 context 下的 temporal sensitivity / early-bridge probe。当前 temporal panel 已完成结果组织：`7d` 和 `13d` 均确认 `backbone_plus_shift_excess`，`7d` rank alignment 更强，`13d` mean shift 更大。固定模板是：支持 architecture form 的时间稳定性与 bridge readout 的 temporal stratification；不支持 `13d` 全面强于 `7d`、content-level convergence 或 external model-side generalization proved。该边界已同步进 final claim matrix、Genome Biology 正文和 Extended Data。

这一层的目标是冻结“真实 perturbation transcriptomic structure 中哪些成分能以时间尺度兼容的方式桥接 DepMap fitness/dependency”，不是给模型打分。

### Layer A/B 主张分层

- Architecture-to-DepMap bridge form：主卖点。问题是 `backbone + shift-excess / context deviation` 这类扰动转录组结构能否桥接 cellular fitness / dependency。跨 context 复现的是结构形式，不要求同一批 gene identity 重叠。
- Bridge content：次级、受限主张。问题是具体哪些 genes 是 anchors、哪条 axis 最强。这一层需要 target identity 复现、更多 anchor 与更严格混杂控制；当前 HCC 中仍应维持 `PFDN5 = primary_but_qualified`，`PMF1 / PRPF6 / ZNF131 = supporting_only`。

**主裁决三指标**（必须同场，共同定义 architecture-aware adjudication）：

- `backbone_recovery_score`：模型是否恢复 frozen canonical backbone
- `shift_excess_identification_score`：模型是否能识别超出 backbone 预测的过度偏移；这里的 `shift-excess` 不等同于 shared trend / overall displacement
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
- Dixit K562 13d/7d Temporal Panel：`13d` truth-side bridge 与 axis compression 已完成并固定为 primary formal supplementary bridge test；`7d` 作为同一 K562 TF pool context 下的 temporal sensitivity / early-bridge probe。当前项目对象层中，`7d` 与 `13d` 在现行 admission/bridgeability 规则下各有 10 个正式 bridgeable targets 进入 DepMap 对接；这一数字不等于原始实验设计中的 target / guide 数。该对象已进入 Genome Biology 正文、Extended Data 与 submission package。
- K562 RNAi endpoint sensitivity：`DEMETER2 RNAi` 已接为 cross-platform sensitivity endpoint；`7d/13d` 仍统一写成 CRISPR KO truth。执行链已验证：`build-stage2-truth-driven-bridge-k562-7d-rnai-demeter2` + `build-stage2-truth-driven-bridge-k562-13d-rnai-demeter2` + `run-stage2-k562-rnai-endpoint-consistency`。结果：四个 context（HCC38/HCC1143/K562 7d/K562 13d）call 全部一致为 `rnai_bridge_weaker_than_crispr_sensitivity`，CRISPR vs RNAi endpoint Spearman 在 HCC（0.14/0.23）显著低于 K562（0.45/0.45）。该层只增强 endpoint robustness，**不替代 CRISPR DepMap matched primary endpoint**。跨 HCC + K562 的 endpoint hierarchy 已冻结为 framework-level observation。

## 7. What Is Actually Closed vs Not Yet Closed

**Phase（2026-04-17 更新）：Genome Biology submission package ready。**

### Closed / Frozen

- truth-side architecture contract ✅
- HCC primary structure definition ✅
- HCC master atlas / fine axes ✅
- SCP542 explanation boundaries ✅
- truth-driven bridge 的主报告边界、dataset role 与 evidence tier governance ✅
- GEARS HCC38 / HCC1143 real raw output ✅
- GEARS export to `stage2_truth_aligned_log_shift` ✅
- GEARS contract validation on HCC38 / HCC1143 ✅
- GEARS entrant-qualified HCC smoke adjudication ✅
- GEARS 有限预算 backbone sweep 与 stop-rule 裁决 ✅
- GEARS trade-off diagnosis 主文档收束 ✅
- HCC 辅助裁决层：`cosine`、`L2`、`top-20 overlap` ✅
- frozen axis annotation / validation 闭环 ✅
- fuller HCC model comparison 第一轮 ✅
- truth bridge decomposition 的 cutoff sensitivity / bootstrap stability / evidence tiering ✅
- Endpoint hierarchy ✅：CRISPR DepMap = formal primary bridge readout；RNAi DEMETER2 = weaker cross-platform sensitivity endpoint。跨四个 context 一致。
- Stage 1A / 1B failure decomposition 正式解释层 ✅
- sensitivity formal interval（主支柱 citable but not fully closed）✅
- covariate balance 第一轮审计完成（design-proxy axis 已落盘）✅
- Dixit K562 13d/7d temporal panel wording freeze ✅
- K562 infrastructure closure ✅：gene ID mapping、scorer alignment policy、prediction contract、GEARS 13d formal config
- final claim matrix ✅（已冻结）
- wording audit ✅（Clean）
- 四敏感位置终审 ✅（Clean）
- Genome Biology manuscript draft / cover letter / figure legends / submission checklist ✅
- 主文 Fig. 1-6 ✅（每张 8 panel，panel-level source data 与 manifest 已生成）
- Extended Data Fig. 1-10 ✅（每张 8 panel，panel-level source data 与 manifest 已生成）
- Supplementary Tables workbook ✅
- Submission package manifest ✅（9 个类别，639 个文件）

### 仍需人工判断（不能自动完成）

- Paper title 已有 Genome Biology 版本，需作者确认
- Author list 与 affiliation 填写
- Corresponding author 信息
- Funding / competing interests / author contributions / acknowledgements
- References 补入
- Public repository / archive DOI
- AI use statement 是否保留与最终措辞
- Additional files 编号与上传命名

**analysis closure 完成，infrastructure closure 完成，claim boundary 冻结，remaining work = 投稿元信息、公开归档与最终人工确认。**

## 8. Immediate Priorities

**当前 phase：Genome Biology submission package ready。remaining work = 作者元信息、references、declarations、公开归档 DOI 与最终人工确认，不是新分析执行。**

1. Genome Biology 投稿闭环（见 `docs/genome_biology_submission_checklist_v1.md`）：
   - Paper title 已有 Genome Biology 版本，需作者确认
   - Author list 与 affiliation 填写
   - Corresponding author 信息
   - Funding
   - Competing interests
   - Authors' contributions
   - Acknowledgements
   - References 补入
   - Public repository / archive DOI
   - AI use statement 是否保留与最终措辞
   - Additional files 编号与上传命名
2. 已完成并可重跑的投稿包入口：
   - `pixi run --environment core python scripts/manuscript/build_all_main_figures.py`
   - `pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py`
   - `pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py`
   - `pixi run --environment core python scripts/manuscript/build_submission_package.py`
3. 明确禁止：
   - 不新增分析结果
   - 不引入新 claim
   - 不改动 claim matrix 已冻结的 allowed/disallowed wording
   - 不把 supplementary 对象升格为主线
   - 不添加超越 architecture-level 的 mechanism recovery 表述
4. discovery：继续保持 phenotype shifter 为 `gated_downstream_layer`，不提前进入 formal deliverable

### 8.0 当前默认执行入口

**当前 phase 已进入 Genome Biology 投稿闭环，不需要新的分析执行。**

如需查看当前已冻结的分析产物，直接打开：

- `docs/genome_biology_manuscript_draft_v1.md`（Genome Biology 正文草案）
- `docs/genome_biology_submission_checklist_v1.md`（Genome Biology 投稿清单）
- `docs/baseline_model_interpretation_and_journal_strategy_v1.md`（baseline 解释与期刊策略）
- `reports/manuscript_submission_package_v1/submission_package_manifest.json`（投稿包总 manifest）
- `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`（claim boundary 冻结矩阵）
- `reports/stage2_gears_backbone_sweep/final_adjudication.md`（GEARS trade-off diagnosis）

## 9. Explicit Non-Goals for the Current Phase

- 不把现有混合时间点 Dixit/K562 写成与 HCC 并列的 primary biological conclusion
- 不把 `Dixit K562 13d` 写成 HCC anchor / axis content 复现；它最多检验 architecture-to-DepMap bridge form
- 不把 `13d` 写成与 DepMap `~14-21d` 的严格 matched endpoint，只写成 time-scale compatible
- 不把 `K562 13d` 的 model-side partial recurrence 写成 full recurrence 或 external model-side generalization
- 不把 `Dixit 7d` 提前纳入 primary closure；它只能作为 `GSE90063 K562 13d/7d temporal panel` 中的 temporal sensitivity / early-bridge probe
- 不把 `Replogle 7d CRISPRi` 或其他 7d 数据无边界并入已收口的 GSE90063 temporal panel；后者只适合作为后续 short-horizon / modality-compatible external expansion panel，并且必须先走 admission contract
- 不把 SCP542 写成强机制锚定或主结论层证据
- 不把 global Pearson 当成 architecture recovery 的替代
- 不把 phenotype shifter discovery 提前写成 formal deliverable
- 不把 `Stage 1A / 1B` 视为废弃
- 不把 model-side recovery 写成已经被证明
- 不把 `GEARS` 当前结果写成“整体压过 shared_mean_baseline”
- 不在 `scGPT` 已完成首轮接入后继续无边界并入 `Geneformer / challengers`
- 不把 `Stage 2 / 3` 写成 fully complete

## 10. Expected Near-Term Deliverables

当前分析和图版 deliverables 已完成。近端只剩投稿侧人工 deliverables：

- 作者列表、单位、通讯作者信息
- Funding / competing interests / author contributions / acknowledgements
- References 正式列表
- Public repository 与 archive DOI
- Additional files 编号和上传命名
- Genome Biology submission system 所需的 Word/PDF/figure file 最终格式
- 最后一轮作者人工确认

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
- `docs/manuscript_complete_figure_plan_v1.md`：当前投稿主图结构 of record（6 主图 + 10 Extended Data），规定 figure id、panel 结构、数据源与可重跑入口。
- `docs/manuscript_figure_blueprint_v1.md`：旧 4 图版蓝图，仅保留为 truth-first 讲述方法论模板，不再作为当前图版结构入口。
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
- `docs/entrant_family_execution_packet_v1.md`：当前 entrant family 的已完成状态与下次继续执行的固定顺序。
- `docs/stage2_linear_controls_execution_checklist_v1.md`：`lm_train_lowrank -> lm_G_scgpt_ridge -> lm_G_geneformer_ridge` 的 Stage 2 接入清单。
- `docs/current_closeout_commit_note_v1.md`：当前阶段文档收尾提交的推荐范围与提交说明。
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
