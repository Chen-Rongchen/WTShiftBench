# WTKO / WT Benchmark

**Phase（2026-04-22 更新）：Genome Biology manuscript workspace ready — analysis closure 完成，figure/source-data/reproducibility package 完成，claim boundary 冻结，`manuscript/` 单入口整理完成；主图 redraw 进度：Figure 1 / Figure 2 / Figure 3 已按新节奏定版并同步到投稿目录，下一步进入 Figure 4 redraw，再依次 Figure 5 / Figure 6，之后统一处理 Extended Data Fig. 1-10；remaining submission work = 作者元信息、declarations、公开归档 DOI 与最终人工确认。**

WT Benchmark 是一个 **truth-first** 的 virtual perturbation benchmark 与分析框架：先在真实 perturbation transcriptomic truth 中定义可桥接到 cellular fitness / dependency（DepMap）的结构化对象，再评估模型能否恢复这些 bridge architecture，最后才进入 discovery。

## 1. 这个仓库现在在做什么

这个仓库最初围绕 `Stage 1A / 1B / 2 / 3` 设计。当前 active framing 已经重排为 truth-first fitness-bridge architecture：先做 transcriptomic perturbation structure 到 DepMap fitness / dependency 的 bridge discovery，再做 model recovery adjudication，再把 `Stage 1A / 1B` 重新解释为 failure decomposition，discovery 则后置为 downstream layer。

因此，这个仓库现在主要承载两类东西：

- `Stage 2` 的 truth-driven bridge、master atlas、structure replication 与 explanation boundary 产物
- 论文主文与补充图的 evidence governance / claim boundary 文档

当前已经冻结的是 **HCC38/HCC1143 breast-cancer cell-line truth-side bridge architecture objects**；当前已经闭环的是 **GEARS strongest formal entrant 的真实 HCC38/HCC1143 smoke adjudication 与有限 backbone sweep**；`scGPT / Geneformer / lm_train_lowrank / lm_G_scgpt_ridge / lm_G_geneformer_ridge` 已正式接入 HCC38/HCC1143 Stage 2，并完成双 cell line raw output、export、contract validation 与 smoke comparison。与此同时，truth-side 结果层已经收束为：**truth-DepMap bridge decomposition + cutoff sensitivity / bootstrap stability + evidence tiering + covariate boundary + K562 temporal and endpoint sensitivity + figure-level reproducibility package**。当前主文投稿目标已固定为 **Genome Biology Research**，定位为 truth-anchored functional-genomics framework/resource；Science Advances 仅作为需要大幅 broad-impact 改写的冲刺备选，Advanced Science 不作为优先目标。

旧 Stage 1A smoke / freeze / scoring 顶层流程、旧 entrant registry 与旧处理后数据已经从当前工作树清理；原始下载数据仍保留在 `data/raw`。`scripts/stage1a/` 仅保留 Stage 2 入口仍复用的少量 helper，不再作为独立主流程入口维护。

### 数据身份警报（2026-04）

- `data/raw/stage1a/candidates/dixit_2016_raw.h5ad` 与 Dixit 2016 / GSE90063 K562 TF pool 的公开描述不匹配，当前更接近 Frangieh 2021 风格对象（`~218k` cells、`IFNγ/Co-culture/Control`、20 蛋白通道）。
- 它不是 `norman_2019_raw`，但也不能继续作为 `Dixit/K562` supplementary replication 的有效输入。
- 基于该对象派生的 `data/processed/stage1a/candidate_formal_like/dixit_2016_raw__control_context.h5ad` 当前统一按 **legacy / 暂停引用** 处理；Dixit 相关 bridge 结论以 `GSE90063 K562 13d/7d temporal panel` 为准，其中 `13d` 是 primary formal supplementary bridge test，`7d` 是 temporal sensitivity / early-bridge probe。

## 2. 一眼先看这里

`README.md` 只承担仓库入口职责：说明当前 active framing、主张边界和最短定位路径。近端执行顺序以 `plan.md` 为准；阶段性状态裁决以 `docs/project_state_summary_v1.md` 为准；最终 wording 边界以 `docs/final_claim_boundary_and_discovery_gating_note_v1.md` 与 `final_claim_matrix.tsv` 为准。

如果你是下一次进来的人，先看这三句：

- `GEARS` 已经作为 strongest formal entrant 跑完 `HCC38 / HCC1143` 的真实 HCC smoke
- `Geneformer` 与三条 linear controls 都已完成第一轮 HCC formal comparison；Geneformer 保留 partial deviation/separation signal，但没有超过 shared-mean baseline 的 primary backbone recovery
- **当前项目状态：Genome Biology manuscript workspace ready（2026-04-22 更新）；`manuscript/` 已整理为投稿前单入口，包含初稿、cover letter、figure legends、6 张主图、10 张 Extended Data、所有 panel a-h、小图 source data / manifest、Additional files、source-data manifests 与 audit 文档**
- **主图 redraw 进度（2026-04-22）：Figure 1（6-panel truth-object）、Figure 2（6-panel evidence-first：a/b + c/d + e 协变量 TVD evidence + f claim matrix；TVD matrix 已由 Extended Data Fig. 9 Panel i 提升至主图 (e)，ED9 回到 8 panel）与 Figure 3（4-panel headline：a three-metric adjudication overview heatmap → b baseline vs GEARS headline dumbbell → c backbone–separation trade-off scatter 作为全图中心 → d per-context paired dots；GEARS sweep 下放至已存在的 Extended Data Fig. 5，主图 caption 显式 cross-reference）均已定版并同步到 `manuscript/figures/`；Figure 4 → Figure 5 → Figure 6 按同节奏依序 redraw，之后统一处理 Extended Data Fig. 1-10；主图与 Extended Data 的最终配色（color palette）等全部 redraw 完成后再统一冻结，当前各图沿用 `src/wtbench/manuscript/_palette.py`，不写入 frozen language**
- 详细状态记录见 `docs/submission_readiness_checklist_v1.md`、`docs/submission_package_index_v1.md` 与 `docs/baseline_model_interpretation_and_journal_strategy_v1.md`

如果你下次进来只想知道“先看哪里就够”，固定只看这三个入口：

1. `manuscript/README.md`
2. `manuscript/text/manuscript_draft_v1.md`
3. `manuscript/source_data_manifests/submission_package_manifest.json`

这三个入口之外，当前不需要先扩读其他材料；默认先用 `manuscript/` 刷新投稿对象，再决定是否回到 `docs/` 或 `reports/` 查看生成来源。

如果你是为了审查“整个项目现在是否合理”，按这个顺序读：

1. `plan.md`
2. `docs/protocol_blueprint.md`
3. `docs/project_state_summary_v1.md`
4. `docs/main_manuscript_results_draft_v1.md`
5. `docs/manuscript_complete_figure_plan_v1.md`（6 主图 + 10 Extended Data 结构 of record；旧 4 图版 `docs/manuscript_figure_blueprint_v1.md` 仅保留为 truth-first 讲述方法论模板）
6. `docs/final_claim_boundary_and_discovery_gating_note_v1.md`
7. `docs/stage2_fuller_hcc_model_comparison_note_v1.md`
8. `docs/stage2_covariate_balance_closure_note_v1.md`
9. `docs/stage2_dixit_supplementary_evidence_tier_v1.md`
10. `scripts/README.md` 与 `configs/README.md`

最短审查路径是：`plan.md`、`docs/protocol_blueprint.md`、`docs/main_manuscript_results_draft_v1.md`、`docs/final_claim_boundary_and_discovery_gating_note_v1.md`。这四个读下来如果闭环，项目主体就基本稳定；其余文档用于审查具体证据边界。

当前最稳的项目表述是：

> GEARS 展现出选择性结构优势：它更擅长把 structure 和 context deviation 分开，并在部分 cell line 上更能识别 shift-excess；但在当前 HCC38/HCC1143 primary adjudication 中，canonical backbone recovery 仍落后于 `shared_mean_baseline`。

与此同时，endpoint hierarchy 已跨 HCC38/HCC1143/K562 7d/K562 13d 四个 context 稳定验证：CRISPR DepMap = formal primary bridge readout，RNAi DEMETER2 = weaker cross-platform sensitivity endpoint，cross-platform robustness 本身是 context-dependent 的（HCC38/HCC1143 CRISPR vs RNAi = 0.14/0.23，K562 = 0.45）。

这不是“GEARS 和 baseline 各赢一半”的对称竞争。更准确地说，`shared_mean_baseline` 是当前更稳定、更主导的 backbone primary reference；`GEARS` 是 deviation / separation-biased entrant。`shift` 也必须拆开：整体位移大小或 shared trend 这一层 baseline 并不差，GEARS 的相对强项更接近超出 backbone 可解释部分的 `shift-excess` / context-specific deviation。

因此，`GEARS` 在本阶段的角色应定位为“已完成诊断的代表性 entrant”，而不是“待继续优化的主推进对象”。

当前若只想把项目状态看懂，再补看一份：

- `docs/project_state_summary_v1.md`
- `docs/finalization_punchlist_v1.md`

如果你下次进来只想知道”直接做什么”，固定顺序就是：

1. `manuscript/README.md`
2. `manuscript/text/manuscript_draft_v1.md`
3. `manuscript/text/cover_letter_v1.md`
4. `manuscript/text/figure_legends_v1.md`
5. `manuscript/source_data_manifests/submission_package_manifest.json`
6. `docs/genome_biology_submission_checklist_v1.md`
7. `docs/baseline_model_interpretation_and_journal_strategy_v1.md`

当前 manuscript hardening 的新增入口：

- `docs/manuscript_hardening_plan_v1.md`

这份文档固定最后一轮文字治理顺序：先修 HCC38/HCC1143 乳腺癌细胞系身份和 `HCC` 缩写风险，再补 submission blocker，再把 Introduction、Results 和 Methods 压到 framework/resource 与 operational definition 级别。

如果你下次进来只想知道“方法学本体下一步做什么”，直接记这一版：

1. 先打开 `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv`。
2. 当前五条 covariate 轴已落盘：`barcode_gem_group`、两条 protospacer 轴、两条 transcriptome 轴。
3. `barcode_gem_group` 固定写成 design-proxy axis；当前只能确认 `HCC38 -> aggrMH001-3`、`HCC1143 -> aggrMH004-6`，不能写成单个 `MH00x` run label。
4. `GSE90063 K562 13d/7d temporal panel` 已完成第一轮组织：`13d` 是 primary formal supplementary bridge test，`7d` 是 temporal sensitivity / early-bridge probe，bridge content is not eligible。
5. `DEMETER2 RNAi` 只作为 cross-platform sensitivity endpoint；`CRISPR DepMap` 仍是 matched primary endpoint。
6. 当前不扩 discovery，不新增 entrant；只同步 `final claim matrix -> manuscript wording`。

## 3. 当前项目结构

### Stage 1A

当前不再作为独立执行主线维护。它在主文叙事中保留为 short-horizon failure decomposition 的解释层，工程上只保留 Stage 2 仍直接复用的少量 helper。

### Stage 1B

long-horizon generalization / stress test 的概念层仍保留在 roadmap 中，但当前不作为近端执行入口。它更适合被理解为 temporal structure degradation 与 failure decomposition 的延伸层。

### Stage 2

truth-driven bridge。当前概念上分成两部分：

- fitness-relevant truth architecture discovery
- model recovery adjudication

其中 HCC truth-side 已冻结了一批 bridge architecture object；model-side 的 contract / scorer / 真实 HCC input bridge 与 GEARS entrant smoke 已跑通，`GEARS` 的有限 backbone sweep 也已按 stop rule 收口，但整个 `Stage 2` 仍未因为此而“全部完成”，因为当前还处在结果收束、Dixit K562 13d/7d temporal panel wording / claim tiering 收紧与 failure decomposition 解释层。

### Stage 3

discovery / phenotype shifter。它仍保留在 roadmap 中，但当前不是 primary active focus，也不应被写成已正式启动的主交付线。

## 4. 当前状态

- **状态**：Genome Biology manuscript workspace ready（2026-04-20 更新）
- analysis closure：已完成
- infrastructure closure：**已完成**（含 K562 gene ID mapping、scorer alignment policy、prediction contract、GEARS 13d formal config、主图/Extended Data/source-data/manifest 生成链）
- claim boundary：已冻结
- wording audit：Clean
- 四敏感位置终审：Clean（Abstract 首句、Figure 标题 × 4、Abstract 结尾否定句、Discussion 结尾）
- truth-side architecture contract：已冻结
- HCC mainline truth architecture：已冻结
- Dixit/K562：历史 `dixit_2016_raw__control_context` 输入当前按 **legacy / 暂停引用** 处理；当前正式收口为 `GSE90063 K562 13d/7d temporal panel`，其中 `13d` 是 primary formal supplementary bridge test，`7d` 是 temporal sensitivity / early-bridge probe。当前结果显示两个时间点均确认 `backbone_plus_shift_excess`，`7d` rank alignment 更强，`13d` mean shift 更大。固定模板是：支持 architecture form 的时间稳定性与 bridge readout 的 temporal stratification；bridge content is not eligible. 因此它不能升级为 shared mainline architecture content、broad cross-context validation、content-level convergence 或与 HCC 对称的 primary conclusion
- K562 RNAi endpoint sensitivity：当前已作为可测试补充层接入；固定写成 `CRISPR DepMap = matched primary endpoint`、`RNAi DEMETER2 = cross-platform sensitivity endpoint`，不写成 CRISPR 主线替代或等价 primary evidence
- SCP542：作为 explanation boundary 已冻结
- model-side structure scorer：已落地
- K562 13d model-side 最小审计：`shared_mean_baseline` 再次在 backbone recovery 上占优，而 `GEARS` 在 structure-vs-context separation 上更强；但 `shift-excess` 分量未复现。因此只能写成 `partial recurrence / partial-support`，不能写成 full three-component recurrence 或 external model-side generalization 已建立；`7d` 在 temporal panel 中只用于同 context temporal sensitivity，不改变这条 model-side 边界
- Stage 2 HCC prediction contract：已冻结为 `stage2_truth_aligned_log_shift`
- 真实 HCC adjudication input bridge：已跑通
- real HCC smoke（`null < shared_mean_baseline`）：已成立
- GEARS strongest formal entrant：已完成 `HCC38 / HCC1143` raw output、export、validation 与 real smoke
- 当前剩余工作：**作者元信息、references、公开归档 DOI、declarations 与最终人工确认**（不再是新分析执行）
- discovery：尚未成为当前 formal mainline，也还不能写成 formal deliverable

## 5. 当前 active question

**当前 active question 已从”分析执行”转为”Genome Biology 投稿闭环”：wording synchronization 和图版/补充表/manifest package 已完成，remaining work = 作者元信息、references、公开归档 DOI、declarations 与最终人工确认。**

最近一步不是”再接一个 entrant”，而是：

**在有限预算 sweep 已完成的前提下，将 GEARS 在 HCC38/HCC1143 primary 上正式收口为 architecture trade-off diagnosis，并把项目主卖点固定为 fitness-relevant transcriptomic bridge architecture：扰动转录组结构能否桥接 DepMap cellular fitness/dependency。**

这里必须拆成两层，避免把 model recovery adjudication triad 与 A1 bridge-form 主问题混在一起。

**Model recovery adjudication triad** 回答“模型是否恢复 frozen architecture”：

- backbone recovery
- shift-excess identification
- structure vs context separation

**A1 bridge-form 主问题** 回答“真实扰动转录组结构能否桥接 DepMap fitness/dependency”：

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

**当前已明确不需要新的分析执行。** 下次进来只做 Genome Biology 投稿闭环：

1. 投稿前人工信息补齐（见 `docs/genome_biology_submission_checklist_v1.md`）：
   - Author list 与 affiliation 填写
   - Corresponding author 信息
   - Funding
   - Competing interests
   - Authors' contributions
   - Acknowledgements
   - References
   - Public repository / archive DOI
   - AI use statement 是否保留与最终措辞
2. 当前已完成的可重跑入口：
   - 主图：`pixi run --environment core python scripts/manuscript/build_all_main_figures.py`
   - Extended Data：`pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py`
   - Supplementary table index：`pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py`
   - Submission package：`pixi run --environment core python scripts/manuscript/build_submission_package.py`
3. 仍需人工确认：
   - 是否保留 6 张主图
   - 是否按 Genome Biology submission system 将 supplementary files 编号为 Additional file 1/2/3...
   - 是否按目标上传系统要求导出 Word/PDF 版本
4. 明确禁止：
   - 不新增分析结果
   - 不引入新 claim
   - 不改动 claim matrix 已冻结的 allowed/disallowed wording
   - 不把 supplementary 对象升格为主线
   - 不添加超越 architecture-level 的 mechanism recovery 表述

历史编辑检查项仍可参考：
   - Paper title 已有 Genome Biology 版本，但需作者确认
   - Author list 与 affiliation 填写
   - Abstract 末尾否定句保留
   - Discussion 结尾主动划界句保留
   - Figure 标题限制性修饰语保留
   - 各 figure legend 与正文 claim 强度一致
   - References 补入
   - Supplementary table / figure 编号体系统一
   - 正文图表交叉引用补入
   - 句式风格统一
   - 冗长句压缩（尤其是 Result Summary 段）
当前不要再把更多 entrant 无边界拉进主线。foundation-model entrant 与第一层 linear controls 都已完成接入；下一步是把 Genome Biology 投稿材料、公开归档和作者声明闭合。

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

如果一轮有限预算 sweep 后，`canonical_backbone recovery` 仍不能接近或追平 `shared_mean_baseline`，且任何改进都以明显损失 `structure/context separation` 为代价，则停止继续把 `GEARS` 推为 HCC38/HCC1143 primary winner，并将当前结果收口为 architecture trade-off diagnosis。

当前这条 stop rule 已经触发，相关正式产物见：

- `reports/stage2_gears_backbone_sweep/final_adjudication.md`

到那时最稳的正式结论应是：

- `shared_mean_baseline` 仍是 backbone 更强的 primary reference
- `GEARS` 是 structure/context separation-biased entrant
- 它的价值在于揭示 architecture trade-off，而不是整体胜出
- 它应被视为已完成 adjudication 的诊断对象，而不是继续 sweep 的默认起点

## 8. Repository Guide

只保留最短定位路径；更细文件见各目录 README。

| 目的 | 入口 |
|------|------|
| 投稿前单入口工作区 | `manuscript/README.md`、`manuscript/file_index.txt` |
| 当前任务与阶段状态 | `plan.md`、`docs/submission_readiness_checklist_v1.md`、`docs/submission_package_index_v1.md` |
| Genome Biology 投稿材料 | `manuscript/text/manuscript_draft_v1.md`、`manuscript/text/cover_letter_v1.md`、`manuscript/text/figure_legends_v1.md`、`docs/genome_biology_submission_checklist_v1.md` |
| 投稿包与补充表 | `manuscript/additional_files/`、`manuscript/source_data_manifests/submission_package_manifest.json` |
| 主图与小图 panel | `manuscript/figures/` |
| Extended Data 与小图 panel | `manuscript/extended_data/` |
| 终局边界与禁写口径 | `docs/final_claim_boundary_and_discovery_gating_note_v1.md`、`reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv` |
| 主图与 Extended Data 重跑 | `scripts/manuscript/build_all_main_figures.py`、`scripts/manuscript/build_all_extended_data_figures.py`、`configs/manuscript/main_figures_v2.json`、`configs/manuscript/extended_data_figures_v1.json` |
| HCC38/HCC1143 model-side adjudication | `reports/stage2_gears_backbone_sweep/final_adjudication.md`、`reports/stage2_real_hcc_smoke/model_comparison.tsv` |
| truth-side bridge 与 axis | `docs/stage2_truth_bridge_integrated_result_v1.md`、`docs/stage2_axis_annotation_result_v1.md`、`reports/stage2_axis_analysis/axis_validation_summary.md` |
| Dixit/K562 supplementary | `docs/stage2_dixit_admission_contract_v1.md`、`docs/stage2_dixit_supplementary_evidence_tier_v1.md`、`docs/stage2_dixit_supplementary_startup_packet_v1.md` |
| 执行入口 | `scripts/`、`configs/`、`src/wtbench/` |

如果要直接进代码，优先看：

- `src/wtbench/stage2_truth_bridge.py`
- `src/wtbench/stage2_model_structure_scorer.py`
- `src/wtbench/stage2_model_expression_scorer.py`
- `scripts/run_stage2_real_hcc_smoke.py`
- `scripts/run_stage2_truth_bridge_decomposition.py`
- `scripts/run_stage2_axis_analysis.py`
- `scripts/run_stage2_dixit_axis_compression.py`

## 9. 指标体系：主线定义 bridge，补充层解释 bridge

### 9.1 主裁决三指标（必须同场，不拆分）

这三个指标共同定义 architecture-aware adjudication，单独任何一个都不能完整概括模型表现：

| 指标 | 回答的问题 |
|------|-----------|
| `backbone_recovery_score` | 模型是否恢复了跨扰动最稳定的共享结构 |
| `shift_excess_identification_score` | 模型是否能识别超出 backbone 预测的过度偏移 |
| `structure_vs_context_separation_score` | 模型是否把 backbone 和 context deviation 分开，而不是混在一起 |

**三指标同时用，才能显式拆出 architecture trade-off**：
- `shared_mean_baseline` 在 backbone 上更强（0.807 vs 最高 0.660）
- GEARS 在 separation 上更强（0.468 vs baseline 0.353）
- 这个 trade-off 是非对称的：baseline 是 backbone primary reference，GEARS 是 deviation / separation-biased entrant
- `shift` 不能混成一层；shared trend / overall displacement 不等于 `shift-excess`，后者才是 GEARS 相对强项更可能出现的位置
- 任何单一总分都会掩盖这个结构性分工

### 9.2 补充审计四模块（降位使用，不抢主线）

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

### 9.3 K562 13d/7d 的正式分层

`GSE90063 K562 13d/7d temporal panel` 的固定模板是：`13d` provides formal supplementary external support for architecture form, with bridge-form support remaining supporting / partial-support；`7d` is a temporal sensitivity / early-bridge probe；bridge content is not eligible。当前 frozen interpretation 是：两个时间点均确认 `backbone_plus_shift_excess`，`7d` rank alignment 更强，`13d` mean shift 更大，因此支持 architecture form 的时间稳定性与 bridge readout 的 temporal stratification。

对应 formal tiering（三层）：

| 层 | 状态 | 含义 |
|----|------|------|
| A0 architecture form | **confirmed** | backbone + shift-excess 结构可复制 |
| A1 bridge form | **supporting / partial-support** | 与 DepMap 方向一致、时间尺度兼容，但弱于 HCC38/HCC1143 primary |
| B bridge content | **not eligible** | macro class context-specific，target overlap 低 |

进入的是 formal supplementary external support for architecture form，不是 `formal primary co-pillar`；A1 bridge form 只能保持 supporting / partial-support，B bridge content 不进入。

## 10. Claim Boundaries

详细 submission prep 状态见 `docs/submission_prep_status_v1.md`。

- 当前项目**尚未**证明 model predictions 能恢复 frozen architecture。
- 当前已完成的是 `GEARS` 的 entrant-qualified HCC smoke，不是”GEARS 已整体胜出”。
- 当前 `GEARS` 与 `shared_mean_baseline` 的差异不是对称各赢一半；`shared_mean_baseline` 仍是 backbone primary reference，`GEARS` 只可写成 deviation / separation-biased entrant。
- K562 13d 支持的是 model-side trade-off 的 partial recurrence：backbone-vs-separation 主方向复现，但 `shift-excess` 分量未复现；因此不能写成 full external validation 或 complete model-side generalization。
- 当前结果支持的是”少数分层书写的 stable anchors 与有限 formal axis evidence 的结构化 bridge”，不是”多数 axis 已正式闭环”。
- `PFDN5` 当前最多只能写成 `primary_but_qualified`；`PMF1 / PRPF6 / ZNF131` 当前只能写成 `supporting_only`。
- `transcription / chromatin` 当前最多只能写成 `primary_axis_but_qualified`；其余多数 axis 继续停留在 `supporting_or_preliminary`。
- Dixit/K562 固定写成 `GSE90063 K562 13d/7d temporal panel` supports architecture form 的时间稳定性与 bridge readout 的 temporal stratification；`13d` 是 primary formal supplementary bridge test，`7d` 是 temporal sensitivity / early-bridge probe，bridge content is not eligible；不支持 `13d` 全面强于 `7d`、`model generalization proved`、content-level convergence，也不是与 HCC 并列的主 biological conclusion。
- K562 RNAi endpoint sensitivity 只用于 endpoint robustness / cross-platform sensitivity；不写成 matched endpoint、primary closure、主线替代或等价 primary evidence。
- Replogle/RNAi 若推进，只能写成 short-horizon / modality-compatible external expansion；DepMap 侧是 RNAi/shRNA-derived dependency endpoint，不写成 siRNA matched endpoint、primary closure 或 external model-side generalization proved。
- architecture recovery 不等同于 single-gene correlation，也不等同于 global Pearson。
- discovery / phenotype shifter 仍然是 downstream layer，必须晚于 model-side closure。
- `cosine / L2 / top-20 overlap` 现在是辅助裁决层，不替代 backbone / shift-excess / separation 三个主裁决问题。
- `scGPT` 与 `Geneformer` 都已进入 HCC38/HCC1143 primary comparison；当前 `Geneformer` 强于 `scGPT`，但两者都不是 stronger entrant。
- sensitivity 当前是”主支柱保守稳健，但 formal full closure 尚未完成”，不是”robustness 已全面建立”。
- covariate audit 已形成正式治理产物，但受元数据上限约束，当前不能写成 `covariate closure complete`。
- 当前不能把 `Stage 2 / 3` 写成 fully complete。

## 11. 当前一句话主线

本项目当前不再把自己表述为“先 benchmark，再 bridge，再 discovery”的线性流程，而是表述为：先在真实 perturbation truth 中识别并冻结可桥接 phenotype 的 architecture，再用已经跑通的 adjudication path 去裁决模型是否恢复该 architecture；当前最近一步不是再接 entrant，而是把 `GEARS` 正式收口为 `architecture trade-off diagnosis`，并将主线推进到 `claim governance` 已成形、但 sensitivity / covariate full closure 仍未完成的结果收束阶段。
