# WTKO / WT Benchmark

WT Benchmark 是一个 **truth-first** 的 virtual perturbation benchmark 与分析框架：先在真实 perturbation transcriptomic truth 中冻结可桥接 phenotype 的 structure，再评估模型能否恢复这些 structure，最后才进入 discovery。

## 1. 这个仓库现在在做什么

这个仓库最初围绕 `Stage 1A / 1B / 2 / 3` 设计，原始路线并没有被废弃。但当前 active framing 已经重排为 truth-first：先做 truth architecture discovery，再做 model recovery adjudication，再把 `Stage 1A / 1B` 重新解释为 failure decomposition，discovery 则后置为 downstream layer。

因此，这个仓库现在同时承载两类东西：

- benchmark-invariant 的 `Stage 1A / 1B` 基础设施与 entrant evaluation 资产
- `Stage 2` 的 truth-driven bridge、master atlas、structure replication 与 explanation boundary 产物

当前已经冻结的是 **truth-side architecture objects**；当前已经闭环的是 **GEARS strongest formal entrant 的真实 HCC smoke adjudication 与有限 backbone sweep**；当前最近一步是 **将 sweep 结果正式收口为 architecture trade-off diagnosis，并继续推进 frozen axis 的 annotation / validation**。与此同时，truth-side 结果层已经进一步收束为：**truth–DepMap bridge decomposition + cutoff sensitivity / bootstrap stability + evidence tiering + SCP542 boundary + Dixit supplementary structure replication**。

## 2. 一眼先看这里

如果你是下一次进来的人，先看这三句：

- `GEARS` 已经作为 strongest formal entrant 跑完 `HCC38 / HCC1143` 的真实 HCC smoke
- 当前最核心未关闭问题不是 entrant 接入，而是 `GEARS` 的 `canonical_backbone recovery` 已完成有限 sweep 但仍落后于 `shared_mean_baseline`
- 下一步不要扩到 `scGPT / Geneformer`；GEARS 主线先按 `architecture trade-off diagnosis` 收口，再继续 frozen axis 的 annotation / validation

当前最稳的项目表述是：

> GEARS 展现出选择性结构优势：它更擅长把 structure 和 context deviation 分开，并在部分 cell line 上更能识别 shift-excess；但在当前 HCC primary adjudication 中，canonical backbone recovery 仍落后于 `shared_mean_baseline`。

## 3. 当前项目结构

### Stage 1A

short-horizon formal benchmark。它仍然负责 short-horizon 的 formal benchmark infrastructure，但当前更重要的角色是为后续 structure-aware failure decomposition 提供入口，而不只是给出 leaderboard。

### Stage 1B

long-horizon generalization / stress test。它保留原有编号与制度角色，但当前更适合被理解为 temporal structure degradation 与 failure decomposition 的延伸层。

### Stage 2

truth-driven bridge。当前概念上分成两部分：

- truth architecture discovery
- model recovery adjudication

其中 truth-side 已冻结了一批 architecture object；model-side 的 contract / scorer / 真实 HCC input bridge 与 GEARS entrant smoke 已跑通，`GEARS` 的有限 backbone sweep 也已按 stop rule 收口，但整个 `Stage 2` 仍未因为此而“全部完成”，因为当前还处在结果收束与 failure decomposition 解释层。

### Stage 3

discovery / phenotype shifter。它仍保留在 roadmap 中，但当前不是 primary active focus，也不应被写成已正式启动的主交付线。

## 4. 当前状态

- truth-side architecture contract：已冻结
- HCC mainline truth architecture：已冻结
- Dixit/K562：作为 supplementary external structure replication object 已冻结
- SCP542：作为 explanation boundary 已冻结
- model-side structure scorer：已落地
- Stage 2 HCC prediction contract：已冻结为 `stage2_truth_aligned_log_shift`
- 真实 HCC adjudication input bridge：已跑通
- real HCC smoke（`null < shared_mean_baseline`）：已成立
- GEARS strongest formal entrant：已完成 `HCC38 / HCC1143` raw output、export、validation 与 real smoke
- 当前正式 blocker：不是“GEARS 还能不能再调一轮就赢”，而是如何把 `GEARS trade-off diagnosis`、`truth bridge evidence tiers` 与 `frozen axis annotation / validation` 收成正式主文档口径
- discovery：尚未成为当前 formal mainline

## 5. 当前 active question

当前最近一步不是“再接一个 entrant”，而是：

**在有限预算 sweep 已完成的前提下，将 GEARS 在 HCC primary 上正式收口为 architecture trade-off diagnosis，并把主线切到 truth bridge evidence tiering + frozen axis 的 annotation / validation 结果收束。**

当前最关键的三个问题是：

- backbone recovery
- shift-excess identification
- structure vs context separation

因此当前 benchmark 主问题已经从“整体拟合好不好”转成了“architecture recovery 是否成立”。

## 6. 当前下一步

当前不要回到 truth-side，也不要继续加模型。下次进来应直接做：

1. 先看当前已经收口的三个结果：
   - `reports/stage2_gears_backbone_sweep/final_adjudication.md`
   - `docs/stage2_truth_bridge_integrated_result_v1.md`
   - `docs/stage2_axis_annotation_result_v1.md`
2. 把 `GEARS` 这条线固定写成：
   - `architecture trade-off diagnosis`
   - 不再把“第二轮 sweep”当默认下一步
3. 把 `truth bridge` 这条线固定写成：
   - `stable target anchors`
   - `limited formal axis evidence`
   - `evidence tiers aligned to claim strength`
4. 把 `axis` 这条线固定写成：
   - `多数 frozen axes 已完成第一轮 annotation + validation`
   - 整体仍保持 `partially supported axes`
5. 如果继续做实现，只优先做：
   - 给 `Dixit/K562` 补一版 supplementary evidence tiering
   - axis annotation 的进一步收束
   - `Stage 1A / 1B` failure decomposition 文本化
6. 明确仍不做：
   - 新 entrant
   - 新 truth object
   - 新评分体系
   - 无停止规则的继续调参

当前不要优先开 `scGPT / Geneformer supplementary`，因为它们不会关闭这个 primary question。

### 直接运行

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
python scripts/stage2_dixit_axis_compression.py
```

如果你只想先看当前主线结果，先打开：

- `reports/stage2_gears_backbone_sweep/final_adjudication.md`
- `docs/stage2_truth_bridge_integrated_result_v1.md`
- `reports/stage2_truth_bridge_decomposition/bridge_decomposition_report.md`
- `reports/stage2_real_hcc_smoke/model_comparison.tsv`
- `docs/stage2_axis_annotation_result_v1.md`
- `reports/stage2_axis_analysis/axis_validation_summary.md`
- `reports/stage2_axis_analysis/axis_annotation_brief.md`

## 7. 当前 stop rule

如果一轮有限预算 sweep 后，`canonical_backbone recovery` 仍不能接近或追平 `shared_mean_baseline`，且任何改进都以明显损失 `structure/context separation` 为代价，则停止继续把 `GEARS` 推为 HCC primary winner，并将当前结果收口为 architecture trade-off diagnosis。

当前这条 stop rule 已经触发，相关正式产物见：

- `reports/stage2_gears_backbone_sweep/final_adjudication.md`

到那时最稳的正式结论应是：

- `shared_mean_baseline` 仍是 backbone 更强的 primary reference
- `GEARS` 是 structure/context separation-biased entrant
- 它的价值在于揭示 architecture trade-off，而不是整体胜出

## 8. Repository Guide

- `README.md`：仓库入口，说明现在在做什么、当前 active framing 是什么。
- `plan.md`：当前执行优先级，强调最近一步与未闭环项。
- `docs/protocol_blueprint.md`：长期蓝图，保留 `Stage 1A / 1B / 2 / 3` 编号，但按 truth-first 主线重排。
- `docs/stage2_truth_driven_bridge_v1.md`：truth-driven bridge 的 protocol、边界与敏感性说明。
- `docs/stage2_truth_bridge_decomposition_v1.md`：将 truth–DepMap bridge 分解为 `target-level joint grid` 与 `axis-level shared explanatory structure` 的正式说明。
- `docs/stage2_truth_bridge_decomposition_result_v1.md`：可直接进入主文写作的结果段落与图注草稿。
- `docs/stage2_truth_bridge_integrated_result_v1.md`：整合 decomposition、axis validation、SCP542 与 Dixit supplement 的统一结果入口。
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
- `reports/`：冻结输出、bridge summary、master atlas、supplementary structure replication。

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

## 10. Claim Boundaries

- 当前项目**尚未**证明 model predictions 能恢复 frozen architecture。
- 当前已完成的是 `GEARS` 的 entrant-qualified HCC smoke，不是“GEARS 已整体胜出”。
- Dixit/K562 是 supplementary support，不是与 HCC 并列的主 biological conclusion。
- architecture recovery 不等同于 single-gene correlation，也不等同于 global Pearson。
- discovery / phenotype shifter 仍然是 downstream layer，必须晚于 model-side closure。
- `cosine / L2 / top-20 overlap` 现在是辅助裁决层，不替代 backbone / shift-excess / separation 三个主裁决问题。
- `scGPT / Geneformer` 当前保持 supplementary / exploratory，不进入 HCC primary conclusion。
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
- `reports/stage2_truth_driven_bridge/dixit_axis_compression/`
- `reports/stage2_truth_driven_bridge/scp542_calibration/`

## 12. 当前一句话主线

本项目当前不再把自己表述为“先 benchmark，再 bridge，再 discovery”的线性流程，而是表述为：先在真实 perturbation truth 中识别并冻结可桥接 phenotype 的 architecture，再用已经跑通的 adjudication path 去裁决模型是否恢复该 architecture；当前最近一步不是再接 entrant，而是只围绕 `GEARS` 的 `canonical_backbone recovery` 做一次有限预算的定向优化，并检查它能否在不丢掉已有结构优势的前提下补上 A 层主裁决。
