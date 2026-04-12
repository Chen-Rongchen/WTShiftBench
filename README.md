# WTKO / WT Benchmark

WT Benchmark 是一个 **truth-first** 的 virtual perturbation benchmark 与分析框架：先在真实 perturbation transcriptomic truth 中定义可桥接到 cellular fitness / dependency（DepMap）的结构化对象，再评估模型能否恢复这些 bridge architecture，最后才进入 discovery。

## 1. 这个仓库现在在做什么

这个仓库最初围绕 `Stage 1A / 1B / 2 / 3` 设计。当前 active framing 已经重排为 truth-first fitness-bridge architecture：先做 transcriptomic perturbation structure 到 DepMap fitness / dependency 的 bridge discovery，再做 model recovery adjudication，再把 `Stage 1A / 1B` 重新解释为 failure decomposition，discovery 则后置为 downstream layer。

因此，这个仓库现在主要承载两类东西：

- `Stage 2` 的 truth-driven bridge、master atlas、structure replication 与 explanation boundary 产物
- 论文主文与补充图的 evidence governance / claim boundary 文档

当前已经冻结的是 **HCC truth-side bridge architecture objects**；当前已经闭环的是 **GEARS strongest formal entrant 的真实 HCC smoke adjudication 与有限 backbone sweep**；当前最近一步是 **把 `scGPT / Geneformer / lm_train_lowrank / lm_G_scgpt_ridge / lm_G_geneformer_ridge` 都正式接入 HCC Stage 2，完成双 cell line raw output、export、contract validation 与 smoke comparison，并把 Dixit supplementary 入口补成 config-driven startup packet**。与此同时，truth-side 结果层已经进一步收束为：**truth–DepMap bridge decomposition + cutoff sensitivity / bootstrap stability + evidence tiering + SCP542 boundary + Dixit supplementary external structure replication**。下一步需要把核心主张从“转录组内部有结构”明确收紧为：**长期扰动转录组结构中是否存在能桥接 DepMap fitness/dependency 的 architecture**。

旧 Stage 1A smoke / freeze / scoring 顶层流程、旧 entrant registry 与旧处理后数据已经从当前工作树清理；原始下载数据仍保留在 `data/raw`。`scripts/stage1a/` 仅保留 Stage 2 入口仍复用的少量 helper，不再作为独立主流程入口维护。

### 数据身份警报（2026-04）

- `data/raw/stage1a/candidates/dixit_2016_raw.h5ad` 与 Dixit 2016 / GSE90063 K562 TF pool 的公开描述不匹配，当前更接近 Frangieh 2021 风格对象（`~218k` cells、`IFNγ/Co-culture/Control`、20 蛋白通道）。
- 它不是 `norman_2019_raw`，但也不能继续作为 `Dixit/K562` supplementary replication 的有效输入。
- 基于该对象派生的 `data/processed/stage1a/candidate_formal_like/dixit_2016_raw__control_context.h5ad` 当前统一按 **legacy / 暂停引用** 处理；Dixit 相关 bridge 结论以 `GSE90063` 重建后的 `K562 13d-only` 为准。

## 2. 一眼先看这里

如果你是下一次进来的人，先看这三句：

- `GEARS` 已经作为 strongest formal entrant 跑完 `HCC38 / HCC1143` 的真实 HCC smoke
- `Geneformer` 与三条 linear controls 都已完成第一轮 HCC formal comparison
- 当前最核心未关闭问题不是再接 entrant，而是先把 `transcriptomic perturbation structure -> DepMap fitness/dependency` 的 bridge 主张、Dixit K562 13d-only admission wording freeze、混杂边界与 `final claim matrix -> manuscript wording` 写成统一收口

如果你下次进来只想知道“先看哪里就够”，固定只看这三个入口：

1. `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv`
2. `README.md`
3. `plan.md`

这三个入口之外，当前不需要先扩读其他材料；默认先用它们刷新方法学状态，再决定是否继续下钻。

如果你是为了审查“整个项目现在是否合理”，按这个顺序读：

1. `plan.md`
2. `docs/protocol_blueprint.md`
3. `docs/project_state_summary_v1.md`
4. `docs/main_manuscript_results_draft_v1.md`
5. `docs/manuscript_figure_blueprint_v1.md`
6. `docs/final_claim_boundary_and_discovery_gating_note_v1.md`
7. `docs/stage2_fuller_hcc_model_comparison_note_v1.md`
8. `docs/stage2_covariate_balance_closure_note_v1.md`
9. `docs/stage2_dixit_supplementary_evidence_tier_v1.md`
10. `scripts/README.md` 与 `configs/README.md`

最短审查路径是：`plan.md`、`docs/protocol_blueprint.md`、`docs/main_manuscript_results_draft_v1.md`、`docs/final_claim_boundary_and_discovery_gating_note_v1.md`。这四个读下来如果闭环，项目主体就基本稳定；其余文档用于审查具体证据边界。

当前最稳的项目表述是：

> GEARS 展现出选择性结构优势：它更擅长把 structure 和 context deviation 分开，并在部分 cell line 上更能识别 shift-excess；但在当前 HCC primary adjudication 中，canonical backbone recovery 仍落后于 `shared_mean_baseline`。

因此，`GEARS` 在本阶段的角色应定位为“已完成诊断的代表性 entrant”，而不是“待继续优化的主推进对象”。

当前若只想把项目状态看懂，再补看一份：

- `docs/project_state_summary_v1.md`
- `docs/finalization_punchlist_v1.md`

如果你下次进来只想知道“直接做什么”，固定顺序就是：

1. `docs/formal_closeout_single_entry_v1.md`
2. `docs/project_state_summary_v1.md`
3. `docs/final_claim_boundary_and_discovery_gating_note_v1.md`
4. `docs/why_models_do_not_stably_beat_baseline_v1.md`
5. `docs/model_vs_baseline_deeper_explanation_note_v1.md`
6. `docs/model_vs_baseline_next_step_breakdown_v1.md`
7. `docs/manuscript_figure_blueprint_v1.md`
8. `docs/main_manuscript_integrated_narrative_draft_v1.md`
9. `docs/main_manuscript_results_draft_v1.md`
10. `docs/current_closeout_commit_note_v1.md`

如果你下次进来只想知道“方法学本体下一步做什么”，直接记这一版：

1. 先打开 `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv`
2. 确认当前已落盘 5 条 covariate 轴：
   - `barcode_gem_group`
   - `num_umis_quantile_bin`
   - `num_umis_over_threshold_bin`
   - `transcriptome_total_signal_quantile_bin`
   - `transcriptome_detected_genes_quantile_bin`
3. 当前默认判断：
   - `barcode_gem_group` 是更接近实验设计 aggregation 结构的代理轴，且整体更轻
   - 但它没有改写 anchor tier
   - 当前仍不能写成 `fully deconfounded`
4. 因此，下一步只优先做一件事：
   - 这条追查现已收口：当前能确认 `HCC38 -> aggrMH001-3`、`HCC1143 -> aggrMH004-6`，但仍不能把 `-1/-2/-3` 唯一写成单个 `MH00x`
5. 如果要推进 Dixit/K562，不再做 feasibility（已通过），而是做 wording freeze 与 manuscript sync：
  - `GSE90063 K562 13d-only` 已作为 formal supplementary external evidence 纳入正式证据体系
  - 定位是 `formal supplementary, not formal primary`：A0 architecture form 已 confirmed，A1 bridge form 当前为 supporting / partial-support
   - 剩余工作：冻结 admission note、positive/partial/negative 判据 wording，同步进 `final claim matrix`
   - `13d` 只写成与 DepMap `~14-21d` fitness screen 的 `time-scale compatible`，不写成 matched endpoint
   - Dixit 2016 可作为 CRISPR knockout perturbation 处理，但必须标注 TF-enriched target library 的边界
6. 在这件事完成前，不继续扩 discovery，不新增 entrant
7. 因此当前正式口径固定为：
   - `barcode_gem_group = design-proxy axis`
   - 不是已确认到单个 `MH00x` 的 run-level label
   - `Dixit 7d` 与 `Replogle 7d CRISPRi` 暂时只作为 temporal / cross-modality exploration，不作为 primary closure

## 3. 当前项目结构

### Stage 1A

当前不再作为独立执行主线维护。它在主文叙事中保留为 short-horizon failure decomposition 的解释层，工程上只保留 Stage 2 仍直接复用的少量 helper。

### Stage 1B

long-horizon generalization / stress test 的概念层仍保留在 roadmap 中，但当前不作为近端执行入口。它更适合被理解为 temporal structure degradation 与 failure decomposition 的延伸层。

### Stage 2

truth-driven bridge。当前概念上分成两部分：

- fitness-relevant truth architecture discovery
- model recovery adjudication

其中 HCC truth-side 已冻结了一批 bridge architecture object；model-side 的 contract / scorer / 真实 HCC input bridge 与 GEARS entrant smoke 已跑通，`GEARS` 的有限 backbone sweep 也已按 stop rule 收口，但整个 `Stage 2` 仍未因为此而“全部完成”，因为当前还处在结果收束、Dixit K562 13d-only supplementary wording / claim tiering 收紧与 failure decomposition 解释层。

### Stage 3

discovery / phenotype shifter。它仍保留在 roadmap 中，但当前不是 primary active focus，也不应被写成已正式启动的主交付线。

## 4. 当前状态

- truth-side architecture contract：已冻结
- HCC mainline truth architecture：已冻结
- Dixit/K562：历史 `dixit_2016_raw__control_context` 输入当前按 **legacy / 暂停引用** 处理；`K562 13d-only`（`GSE90063`）当前最稳地支持 supplementary-level 的 architecture-form / bridge-form support：A0 architecture form 已 confirmed，A1 bridge form 当前为 supporting / partial-support。它复现了 `backbone + shift-excess` 架构形式，并在 `n=10` 个可桥接 targets 上呈现出与 DepMap 方向一致、时间尺度兼容的 bridge 信号；但由于当前 target 数仍有限、主导 macro class 与 HCC 仍表现出明显的 context specificity，这些结果不能升级为 shared mainline architecture content、broad cross-context validation 或与 HCC 对称的 primary conclusion
- SCP542：作为 explanation boundary 已冻结
- model-side structure scorer：已落地
- Stage 2 HCC prediction contract：已冻结为 `stage2_truth_aligned_log_shift`
- 真实 HCC adjudication input bridge：已跑通
- real HCC smoke（`null < shared_mean_baseline`）：已成立
- GEARS strongest formal entrant：已完成 `HCC38 / HCC1143` raw output、export、validation 与 real smoke
- 当前正式 blocker：不是“GEARS 还能不能再调一轮就赢”，而是如何把 `GEARS trade-off diagnosis`、`truth bridge evidence tiers`、`final claim matrix` 与 `frozen axis annotation / validation` 收成同一套正式主文档口径
- discovery：尚未成为当前 formal mainline，也还不能写成 formal deliverable

## 5. 当前 active question

当前最近一步不是“再接一个 entrant”，而是：

**在有限预算 sweep 已完成的前提下，将 GEARS 在 HCC primary 上正式收口为 architecture trade-off diagnosis，并把项目主卖点固定为 fitness-relevant transcriptomic bridge architecture：扰动转录组结构能否桥接 DepMap cellular fitness/dependency。**

当前最关键的三个问题是：

- backbone recovery
- shift-excess identification
- structure vs context separation
- transcriptomic architecture 是否能桥接 DepMap fitness/dependency

因此当前 benchmark 主问题已经从“整体拟合好不好”转成了“模型是否能恢复 fitness-relevant bridge architecture”。具体 anchor / axis 属于 bridge content 层，仍然要保持 HCC-specific 与 qualified。

而下一阶段的执行重点已经进一步收紧为：

- 比较
- 敏感性
- 混杂
- 最终边界
- discovery 继续 gated

其中，混杂线当前已经从“只有第一轮单轴提示”推进到“多轴、配置驱动、可汇总输出”的正式审计入口；但这不应被误写成 fully closed。更准确的说法是：**covariate risk 已完成第一轮治理并进入 claim boundary，同步受限于现有实验设计元数据上限。**

如果下一步还要继续追问“为什么模型打不过 baseline”，默认不再保留为泛问题，而是拆成两个更小的问题：

- `baseline winner` 是否主要由 shared backbone objective 决定
- entrant 的额外能力是否稳定落在 `separation / deviation` 而不是 backbone 上

对应的后续入口见：

- `docs/model_vs_baseline_deeper_explanation_note_v1.md`
- `docs/model_vs_baseline_next_step_breakdown_v1.md`

## 6. 当前下一步

当前不要回到 truth-side，也不要继续加模型。下次进来应直接做：

1. 先看当前最近一次方法学推进的正式产物：
   - `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv`
   - `docs/stage2_covariate_balance_closure_note_v1.md`
   - `docs/stage2_sensitivity_full_closure_note_v1.md`
2. 记住当前方法学状态：
   - 5 条 covariate 轴已落盘
   - `barcode_gem_group` 已作为设计层代理轴进入正式审计
   - `PFDN5 = primary_but_qualified`
   - `PMF1 / PRPF6 / ZNF131 = supporting_only`
   - `final_claim_matrix.tsv` 当前不改 tier，只继续同步 wording
3. 下一步只优先做：
   - 不再继续追查 `barcode_gem_group -> MH00x` 的单个 run 映射
   - 直接把当前 `barcode_gem_group` 固定写成 design-proxy axis
   - 把这条边界持续同步到 `final claim matrix -> manuscript wording`
4. 然后再做：
   - `GSE90063` Dixit K562 13d-only admission wording freeze 与 positive / partial / negative 判据冻结
   - `最终边界`
   - `main manuscript wording` 持续同步
   - `discovery 继续 gated`
5. 直接执行入口：
   - `docs/next_phase_execution_checklist_v1.md`
   - `docs/final_claim_boundary_and_discovery_gating_note_v1.md`
   - `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.md`
6. 如果下次进来是为了直接推进论文图片，固定顺序是：
   - `docs/manuscript_figure_blueprint_v1.md`
   - `docs/main_manuscript_results_draft_v1.md`
   - `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`
   - `s41592-025-02772-6.pdf`
7. 明确仍不做：
   - 新 entrant
   - 无 feasibility check 与预冻结判据的新 truth object
   - 新评分体系
   - 无停止规则的继续调参
   - 在 design-layer mapping 未更清楚前继续扩 discovery

当前不要再把更多 entrant 无边界拉进主线。foundation-model entrant 与第一层 linear controls 都已完成接入；下一步是把核心主张、Dixit K562 13d-only admission wording freeze、covariate boundary 与 manuscript 入口维持在同一套边界上。

### 直接运行

如果你下次进来要按当前收口主线直接执行，默认先用 `pixi`：

```bash
pixi run --environment core run-stage2-closure-pipeline
pixi run --environment core validate-stage2-closure-artifacts
```

这两步的职责分别是：

- `run-stage2-closure-pipeline`：串联 `covariates -> sensitivity -> covariate audit`
- `validate-stage2-closure-artifacts`：校验 `claim/tier` 关键 TSV 与边界文档没有漂移

注意：运行产物默认落到 `reports/`、`data/processed/` 与 `data/stage2/`；这些路径受 `.gitignore` 约束，默认不作为版本管理对象提交。当前 git 版本管理应聚焦于 `scripts/`、`configs/`、`docs/` 与必要的 `tests/` 变更，而不是把本地重跑产物一并纳入仓库。

如果你下次进来要直接刷新当前 axis 主线，而不是回头重跑 GEARS sweep，按这个顺序执行：

```bash
PYTHONPATH=src python scripts/run_stage2_axis_analysis.py --config configs/stage2/axis_analysis_template_v1.json
PYTHONPATH=src python scripts/run_stage2_axis_enrichment.py --config configs/stage2/axis_enrichment_template_v1.json
PYTHONPATH=src python scripts/materialize_stage2_per_target_signature.py --config configs/stage2/per_target_signature_materialization_v1.json
PYTHONPATH=src python scripts/run_stage2_axis_target_consistency.py --config configs/stage2/axis_target_consistency_template_v1.json
PYTHONPATH=src python scripts/summarize_stage2_axis_validation.py --config configs/stage2/axis_validation_summary_v1.json
```

如果你下次进来要直接刷新当前 truth bridge evidence-tier 主线，按这个顺序执行：

```bash
PYTHONPATH=src python scripts/run_stage2_truth_bridge_decomposition.py --config configs/stage2/truth_bridge_decomposition_v1.json
PYTHONPATH=src python scripts/run_stage2_axis_analysis.py --config configs/stage2/axis_analysis_template_v1.json
PYTHONPATH=src python scripts/run_stage2_axis_enrichment.py --config configs/stage2/axis_enrichment_template_v1.json
PYTHONPATH=src python scripts/materialize_stage2_per_target_signature.py --config configs/stage2/per_target_signature_materialization_v1.json
PYTHONPATH=src python scripts/run_stage2_axis_target_consistency.py --config configs/stage2/axis_target_consistency_template_v1.json
PYTHONPATH=src python scripts/summarize_stage2_axis_validation.py --config configs/stage2/axis_validation_summary_v1.json
python scripts/stage2_freeze_scp542_explanation_boundaries.py
PYTHONPATH=src python scripts/run_stage2_dixit_axis_compression.py --config configs/stage2/dixit_axis_compression_v1.json
```

如果你只想先看当前主线结果，先打开：

- `reports/stage2_gears_backbone_sweep/final_adjudication.md`
- `docs/stage2_truth_bridge_integrated_result_v1.md`
- `reports/stage2_truth_bridge_decomposition/bridge_decomposition_report.md`
- `reports/stage2_real_hcc_smoke/model_comparison.tsv`
- `docs/stage2_axis_annotation_result_v1.md`
- `reports/stage2_axis_analysis/axis_validation_summary.md`
- `reports/stage2_axis_analysis/axis_annotation_brief.md`
- `docs/next_phase_execution_checklist_v1.md`

## 7. 当前 stop rule

如果一轮有限预算 sweep 后，`canonical_backbone recovery` 仍不能接近或追平 `shared_mean_baseline`，且任何改进都以明显损失 `structure/context separation` 为代价，则停止继续把 `GEARS` 推为 HCC primary winner，并将当前结果收口为 architecture trade-off diagnosis。

当前这条 stop rule 已经触发，相关正式产物见：

- `reports/stage2_gears_backbone_sweep/final_adjudication.md`

到那时最稳的正式结论应是：

- `shared_mean_baseline` 仍是 backbone 更强的 primary reference
- `GEARS` 是 structure/context separation-biased entrant
- 它的价值在于揭示 architecture trade-off，而不是整体胜出
- 它应被视为已完成 adjudication 的诊断对象，而不是继续 sweep 的默认起点

## 8. Repository Guide

- `README.md`：仓库入口，说明现在在做什么、当前 active framing 是什么。
- `plan.md`：当前执行优先级，强调最近一步与未闭环项。
- `docs/protocol_blueprint.md`：长期蓝图，保留 `Stage 1A / 1B / 2 / 3` 编号，但按 truth-first 主线重排。
- `docs/manuscript_figure_blueprint_v1.md`：投稿主图蓝图，规定 truth-first 主图顺序、panel 结构、数据源与讲故事方法。
- `docs/main_manuscript_integrated_narrative_draft_v1.md`：把当前各条结果 note 压成统一主文稿叙事的整合草案。
- `docs/main_manuscript_results_draft_v1.md`：更接近论文正文 `Results` 风格的压缩版本。
- `docs/formal_closeout_single_entry_v1.md`：当前正式收口的单页总入口，压缩唯一主线、五项缺口、禁写边界与默认阅读顺序。
- `docs/next_phase_execution_note_v1.md`：下一阶段“比较、敏感性、混杂、最终边界、discovery 继续 gated”五项缺口的正式执行口径。
- `docs/next_phase_execution_checklist_v1.md`：把比较、敏感性、混杂三条线压成一页执行清单的近端入口。
- `docs/project_state_summary_v1.md`：当前项目已进入“主张治理稳定化”阶段的阶段性摘要。
- `docs/finalization_punchlist_v1.md`：下次一次性完成主文稿收口、入口统一与边界冻结的最终清单。
- `docs/model_vs_baseline_deeper_explanation_note_v1.md`：把“模型为什么打不过 baseline”继续拆成方法学解释与生物学解释两层的深一层 note。
- `docs/model_vs_baseline_next_step_breakdown_v1.md`：把后续推进固定成两个更小的问题，避免重新回到泛谈“模型为什么打不过 baseline”。
- `docs/stage1_failure_decomposition_note_v1.md`：`Stage 1A / 1B` 作为 failure decomposition track 的正式解释入口。
- `docs/stage2_truth_driven_bridge_v1.md`：truth-driven bridge 的 protocol、边界与敏感性说明。
- `docs/stage2_truth_bridge_decomposition_v1.md`：将 truth–DepMap bridge 分解为 `target-level joint grid` 与 `axis-level shared explanatory structure` 的正式说明。
- `docs/stage2_truth_bridge_decomposition_result_v1.md`：可直接进入主文写作的结果段落与图注草稿。
- `docs/stage2_truth_bridge_integrated_result_v1.md`：整合 decomposition、axis validation、SCP542 与 Dixit supplement 的统一结果入口。
- `docs/stage2_dixit_admission_contract_v1.md`：冻结 `Dixit/K562` 在当前主线里的 admission status，明确 `13d / 7d / legacy` 三层准入边界。
- `docs/stage2_dixit_supplementary_evidence_tier_v1.md`：Dixit/K562 supplementary external structure replication 的证据分层口径。
- `docs/stage2_dixit_supplementary_startup_packet_v1.md`：Dixit/K562 supplementary replication 的可重跑启动包。
- `docs/stage2_fuller_hcc_model_comparison_note_v1.md`：HCC primary adjudication 中 fuller model comparison 的解释层说明。
- `docs/why_models_do_not_stably_beat_baseline_v1.md`：为什么复杂 entrant 不能稳定胜过 `shared_mean_baseline` 的正式 explanation layer。
- `docs/stage2_sensitivity_full_closure_note_v1.md`：Stage 2 sensitivity 的 formal closure 条件与当前状态。
- `docs/stage2_covariate_balance_closure_note_v1.md`：Stage 2 covariate balance closure 的执行口径与剩余风险。
- `docs/final_claim_boundary_and_discovery_gating_note_v1.md`：当前终局 claim boundary 与 discovery gating 的统一收口文档。
- `docs/model_expansion_deferral_note_v1.md`：为什么当前阶段不继续扩模型进入 HCC primary mainline 的正式说明。
- `docs/next_stage_model_entrant_inventory_v1.md`：下一阶段 entrant expansion 的候选模型盘点与最小接入清单。
- `docs/next_stage_model_entrant_execution_checklist_v1.md`：下一阶段 entrant expansion 的一页式执行清单。
- `docs/entrant_family_execution_packet_v1.md`：当前 entrant family 的已完成状态与下次继续执行的固定顺序。
- `docs/stage2_linear_controls_execution_checklist_v1.md`：`lm_train_lowrank -> lm_G_scgpt_ridge -> lm_G_geneformer_ridge` 的 Stage 2 接入清单。
- `docs/current_closeout_commit_note_v1.md`：当前阶段文档收尾提交的推荐范围与提交说明。
- `docs/next_stage_startup_packet_v1.md`：下一阶段第一周最小启动包。
- `docs/stage2_scgpt_hcc_recipe_freeze_v1.md`：`scGPT` HCC Stage 2 recipe freeze 与当前接入状态。
- `configs/stage2/scgpt_hcc_formal_v1.json`：`scGPT` HCC Stage 2 recipe 配置。
- `scripts/run_stage2_scgpt_hcc_predictions.py`：`scGPT` HCC Stage 2 raw output producer 入口。
- `docs/stage2_geneformer_hcc_recipe_freeze_v1.md`：`Geneformer` 进入 HCC Stage 2 前的第一版 recipe freeze。
- `configs/stage2/geneformer_hcc_formal_v1.json`：`Geneformer` HCC Stage 2 recipe 配置骨架。
- `scripts/run_stage2_geneformer_hcc_predictions.py`：`Geneformer` HCC Stage 2 raw output producer 入口。
- `docs/stage2_lm_train_lowrank_hcc_recipe_freeze_v1.md`：`lm_train_lowrank` 的 HCC Stage 2 linear control freeze 与当前接入状态。
- `configs/stage2/lm_train_lowrank_hcc_formal_v1.json`：`lm_train_lowrank` HCC Stage 2 control 配置。
- `scripts/run_stage2_lm_train_lowrank_hcc_predictions.py`：`lm_train_lowrank` HCC Stage 2 raw output producer 入口。
- `docs/stage2_lm_g_scgpt_ridge_hcc_recipe_freeze_v1.md`：`lm_G_scgpt_ridge` 的 HCC Stage 2 linear control freeze 与当前接入状态。
- `configs/stage2/lm_g_scgpt_ridge_hcc_formal_v1.json`：`lm_G_scgpt_ridge` HCC Stage 2 control 配置。
- `scripts/run_stage2_lm_g_scgpt_ridge_hcc_predictions.py`：`lm_G_scgpt_ridge` HCC Stage 2 raw output producer 入口。
- `docs/stage2_lm_g_geneformer_ridge_hcc_recipe_freeze_v1.md`：`lm_G_geneformer_ridge` 的 HCC Stage 2 linear control freeze 与当前接入状态。
- `configs/stage2/lm_g_geneformer_ridge_hcc_formal_v1.json`：`lm_G_geneformer_ridge` HCC Stage 2 control 配置。
- `scripts/run_stage2_lm_g_geneformer_ridge_hcc_predictions.py`：`lm_G_geneformer_ridge` HCC Stage 2 raw output producer 入口。
- `configs/stage2/dixit_axis_compression_v1.json`：Dixit supplementary axis compression 的默认 machine-readable 配置，当前固定指向 `GSE90063 K562 13d-only`。
- `scripts/run_stage2_dixit_axis_compression.py`：Dixit supplementary axis compression 的 config-driven 运行入口。
- `docs/stage2_axis_annotation_and_validation_rule.md`：功能轴的发现、注释与验证规则。
- `docs/stage2_axis_analysis_minimal_template.md`：axis shared signature -> enrichment -> consistency audit 的最小执行模板。
- `docs/stage2_axis_annotation_result_v1.md`：当前 frozen axis 的正式结果口径与推荐写法。
- `configs/stage2/axis_analysis_template_v1.json`：Stage 2 axis annotation / validation 的 machine-readable 配置骨架。
- `configs/stage2/truth_bridge_decomposition_v1.json`：Stage 2 两层 bridge decomposition 的默认配置。
- `configs/stage2/axis_enrichment_template_v1.json`：Stage 2 axis-level enrichment 的最小配置骨架。
- `configs/stage2/axis_target_consistency_template_v1.json`：Stage 2 per-target consistency audit 的最小配置骨架。
- `configs/stage2/per_target_signature_materialization_v1.json`：Stage 2 per_target_signature 物化配置。
- `docs/stage2_model_structure_scorer_contract.md`：Stage 2 structure scorer contract。
- `docs/stage2_hcc_prediction_contract.md`：真实 HCC adjudication input contract。
- `configs/stage2/gears_backbone_diagnostic_v1.json`：GEARS backbone 诊断阈值与 sweep 边界。
- `configs/stage2/gears_hcc_backbone_sweep_v1.json`：GEARS 有限 sweep 的正式约束草案。
- `configs/`：machine-readable 配置入口。
- `scripts/`：CLI 与执行脚本入口。
- `src/`：核心实现。
- `reports/`：冻结输出、bridge summary、master atlas、supplementary external structure replication。

## 9. 当前先看哪些文件

如果你想一眼进入当前主线，按这个顺序看：

1. `plan.md`
2. `reports/stage2_gears_backbone_sweep/final_adjudication.md`
3. `docs/stage2_truth_bridge_integrated_result_v1.md`
4. `docs/stage2_axis_annotation_result_v1.md`
5. `reports/stage2_axis_analysis/axis_validation_summary.md`
6. `docs/protocol_blueprint.md`

如果你想直接进代码：

- `scripts/run_stage2_real_hcc_smoke.py`
- `src/wtbench/stage2_model_structure_scorer.py`
- `src/wtbench/stage2_model_expression_scorer.py`
- `scripts/run_stage2_gears_backbone_diagnostic.py`
- `scripts/run_stage2_axis_analysis.py`
- `scripts/run_stage2_truth_bridge_decomposition.py`
- `scripts/run_stage2_axis_enrichment.py`
- `scripts/run_stage2_axis_target_consistency.py`
- `scripts/materialize_stage2_per_target_signature.py`
- `scripts/materialize_stage2_gears_backbone_sweep.py`
- `scripts/run_stage2_gears_hcc_predictions.py`
- `configs/stage2/gears_backbone_diagnostic_v1.json`
- `configs/stage2/gears_hcc_backbone_sweep_v1.json`
- `configs/stage2/gears_hcc_formal_v1.json`

## 10. 指标体系：主线定义 bridge，补充层解释 bridge

### 10.1 主裁决三指标（必须同场，不拆分）

这三个指标共同定义 architecture-aware adjudication，单独任何一个都不能完整概括模型表现：

| 指标 | 回答的问题 |
|------|-----------|
| `backbone_recovery_score` | 模型是否恢复了跨扰动最稳定的共享结构 |
| `shift_excess_identification_score` | 模型是否能识别超出 backbone 预测的过度偏移 |
| `structure_vs_context_separation_score` | 模型是否把 backbone 和 context deviation 分开，而不是混在一起 |

**三指标同时用，才能显式拆出 architecture trade-off**：
- `shared_mean_baseline` 在 backbone 上更强（0.807 vs 最高 0.660）
- GEARS 在 separation 上更强（0.468 vs baseline 0.353）
- 任何单一指标都会掩盖这个结构性 trade-off

### 10.2 补充审计四模块（降位使用，不抢主线）

这些指标仍然需要，但位置是补充解释层，不是 headline：

| 模块 | 定位 |
|------|------|
| `Spearman(E, ΔT)`（rank-based association）| bridge-form scalar association 主关联指标 |
| `E-distance`（embedding-space displacement）| embedding 层面的 state displacement 审计；与 Spearman 为**互补维度**，不是竞争关系 |
| Essentiality stratification（tier 1–4）| 解释 bridge 为什么非线性、分层；是**可解释性 scaffold**，不是 orthogonal validation |
| Stress-removed sensitivity | 判断 bridge 是否只是"濒死程序"驱动 |

**禁止表述**：
> `E-distance underperforms Spearman as a headline metric`

**正确表述**：
> E-distance is retained as an embedding-level scalar audit of state displacement, whereas Spearman(E, ΔT) is retained as the primary rank-based association summary. They are complementary rather than competing headline metrics.

**禁止表述**：
> essentiality stratification independently validates the architecture-level adjudication

**正确表述**：
> Essentiality stratification provides an interpretable decomposition scaffold for why the truth–DepMap bridge is non-linear and tiered, and is retained as a supplementary explanation layer rather than an orthogonal validation layer.

### 10.3 K562 13d 的正式分层

`GSE90063 K562 13d-only` 的 formal tiering（三层）：

| 层 | 状态 | 含义 |
|----|------|------|
| A0 architecture form | **confirmed** | backbone + shift-excess 结构可复制 |
| A1 bridge form | **supporting / partial-support** | Spearman ~0.50，与 DepMap 方向一致但弱于 HCC primary |
| B bridge content | **not eligible** | macro class context-specific，target overlap 低 |

进入的是 `formal supplementary external evidence`，不是 `formal primary co-pillar`。

## 11. Claim Boundaries

- 当前项目**尚未**证明 model predictions 能恢复 frozen architecture。
- 当前已完成的是 `GEARS` 的 entrant-qualified HCC smoke，不是“GEARS 已整体胜出”。
- 当前结果支持的是“少数分层书写的 stable anchors 与有限 formal axis evidence 的结构化 bridge”，不是“多数 axis 已正式闭环”。
- `PFDN5` 当前最多只能写成 `primary_but_qualified`；`PMF1 / PRPF6 / ZNF131` 当前只能写成 `supporting_only`。
- `transcription / chromatin` 当前最多只能写成 `primary_axis_but_qualified`；其余多数 axis 继续停留在 `supporting_or_preliminary`。
- Dixit/K562 只支持 supplementary-level 的 architecture replication / structure-level transferability，不支持 `model generalization proved`，也不是与 HCC 并列的主 biological conclusion。
- architecture recovery 不等同于 single-gene correlation，也不等同于 global Pearson。
- discovery / phenotype shifter 仍然是 downstream layer，必须晚于 model-side closure。
- `cosine / L2 / top-20 overlap` 现在是辅助裁决层，不替代 backbone / shift-excess / separation 三个主裁决问题。
- `scGPT` 与 `Geneformer` 都已进入 HCC primary comparison；当前 `Geneformer` 强于 `scGPT`，但两者都不是 stronger entrant。
- sensitivity 当前是“主支柱保守稳健，但 formal full closure 尚未完成”，不是“robustness 已全面建立”。
- covariate audit 已形成正式治理产物，但受元数据上限约束，当前不能写成 `covariate closure complete`。
- 当前不能把 `Stage 2 / 3` 写成 fully complete。

## 11. Minimal Orientation

如果你想快速定位当前 truth-first 主线，建议按下面顺序看：

1. `plan.md`
2. `docs/protocol_blueprint.md`
3. `docs/stage2_truth_driven_bridge_v1.md`
4. `docs/stage2_truth_bridge_decomposition_v1.md`
5. `docs/stage2_truth_bridge_integrated_result_v1.md`
6. `docs/stage2_model_structure_scorer_contract.md`
7. `docs/stage2_hcc_prediction_contract.md`
8. `reports/stage2_real_hcc_smoke/smoke_report.md`

如果你想看代码位置：

- `src/wtbench/stage2_truth_bridge.py`
- `src/wtbench/stage2_bridge_decomposition.py`
- `src/wtbench/stage2_truth_sensitivity.py`
- `src/wtbench/stage2_model_structure_scorer.py`
- `src/wtbench/stage2_hcc_prediction_export.py`
- `scripts/build_stage2_truth_driven_bridge.py`
- `scripts/run_stage2_truth_bridge_decomposition.py`
- `scripts/run_stage2_truth_bridge_sensitivity.py`
- `scripts/run_stage2_hcc_prediction_export.py`
- `scripts/run_stage2_real_hcc_smoke.py`

如果你想看冻结 truth objects：

- `reports/stage2_truth_driven_bridge/truth_architecture_contract/`
- `reports/stage2_truth_driven_bridge/master_atlas/`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/`
- `reports/stage2_truth_driven_bridge/scp542_calibration/`

## 12. 当前一句话主线

本项目当前不再把自己表述为“先 benchmark，再 bridge，再 discovery”的线性流程，而是表述为：先在真实 perturbation truth 中识别并冻结可桥接 phenotype 的 architecture，再用已经跑通的 adjudication path 去裁决模型是否恢复该 architecture；当前最近一步不是再接 entrant，而是把 `GEARS` 正式收口为 `architecture trade-off diagnosis`，并将主线推进到 `claim governance` 已成形、但 sensitivity / covariate full closure 仍未完成的结果收束阶段。
