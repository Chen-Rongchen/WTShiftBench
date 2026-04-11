# Stage 2 HCC Prediction Contract

## 文档定位

本文档只定义 **真实 HCC model-side adjudication** 所需的 prediction object contract / export path。

它不证明任何 biology，也不替代 adjudication report。

当前目标只有一个：

把 `raw model output -> aligned prediction -> scorer-ready prediction` 三层边界定死，避免在真实 HCC smoke 时重新引入 contract drift。

## 当前结论

当前正式输入对象应使用：

- `predicted_shift`
- `prediction_space = stage2_truth_aligned_log_shift`
- `normalized + log1p` 定义的 shift

当前**不**使用：

- `Stage 1A` 的 `X_pseudobulk_delta` 作为 Stage 2 formal input
- `predicted expression` 直接进入 scorer

原因很简单：

1. 当前冻结的 `Stage 2 truth bridge object / master atlas / fine axes / structure contract` 都定义在 `normalized + log1p` shift 空间
2. `real_shift_L2`、`real_shift_mean_abs`、`real_DEG_burden`、`real_Edistance` 都以这套空间为本体
3. `Stage 1A X_pseudobulk_delta` 仍是它自己的 formal benchmark space，不反向支配 `Stage 2`

因此，真实 HCC smoke 若要 formal 化，必须和 `Stage 2 truth-side` 保持同构，而不是强行复用 `Stage 1A` 的数值空间。

## 三层对象边界

### Layer 1. Raw Model Output

这是模型原始导出对象。

允许形式可以不同，例如：

- raw predicted expression
- latent decode 后的 expression-like matrix
- model-native target embedding output

但这些对象**不能直接**喂给 scorer。

这一层必须记录 provenance：

- `model_id`
- `model_version`
- `source_checkpoint`
- `export_script`
- `export_timestamp`
- `cell_line`

### Layer 2. Aligned Prediction

这是已经对齐到 HCC formal target / gene contract 的中间层。

它的职责是：

- target 行集合固定
- gene 列集合固定
- 顺序固定
- 缺失、额外、重名、非数值等 contract 风险在这里被显式审计

这一层仍属于 alignment object，不等于 scorer-ready。

### Layer 3. Scorer-Ready Prediction

这是唯一允许进入 Stage 2 structure scorer 的正式输入对象。

最小正式对象固定为：

- 文件名：`predicted_shift.tsv.gz`
- 首列：`target_gene`
- 其余列：gene columns
- 值语义：`stage2_truth_aligned_log_shift`

如果不是 `predicted_shift`，就不应宣称自己是 scorer-ready。

## Dataset 粒度

HCC 预测对象必须按 cell line 分开冻结：

1. `HCC38`
2. `HCC1143`

当前不允许先混成 pooled HCC object 再交给 scorer。

原因：

- truth-side 主线本来就是 `HCC38` / `HCC1143` 分线冻结
- 后续 adjudication 需要分别看 backbone / shift-excess / context deviation 是否跨线稳定

## Target Universe

当前 `scorer-ready` target universe 固定为：

- `reports/stage2_truth_driven_bridge/master_atlas/shared_target_axis_membership.tsv`
  中出现的 `target_gene` 去重集合

也就是 frozen architecture contract 中可投影、可裁决的 target 集。

当前不允许：

- 模型各自导出不同 target 集后再在 adjudication 时临时取交集
- 把 frozen contract 之外的 target 混入主裁决对象

若缺 target，可作为 degraded 输入记录，但不得直接上升为 formal HCC adjudication。

## Gene Space

当前 `scorer-ready` gene space 固定为：

- `shared_target_axis_membership.tsv` 中出现过的 axis-member genes 去重集合

这是当前 v1 scorer 的最小正式 gene space。

原因：

- 现有 structure scorer 的 projection layer 只对 frozen axes 的成员基因做投影
- 在真实 HCC smoke 阶段，先冻结最小可裁决 gene space，比假装要覆盖更大但未治理的 gene universe 更稳

因此当前 formal 要求是：

- gene columns 必须至少覆盖全部 axis-member genes
- gene 顺序应按 contract 固定
- 不允许把 gene symbol 映射、列补零、别名合并这些逻辑推迟到 scorer 现场处理

## Prediction Space

当前 formal `prediction_space` 固定为：

- `stage2_truth_aligned_log_shift`

写入 manifest 时必须同时写清：

- `prediction_space = stage2_truth_aligned_log_shift`
- `normalization_applied_in_export = true`
- `log1p_applied_in_export = true`
- `reference_definition = in-dataset pooled control baseline`

若未来要增加 raw-space 的 supplementary 平行轨道，必须显式改成另一条 contract，不能复用当前 formal HCC path。

## Provenance 最小字段

每份 scorer-ready prediction manifest 至少必须包含：

- `stage`
- `cell_line`
- `model_id`
- `model_version`
- `prediction_space`
- `source_kind`
- `export_script`
- `export_timestamp`
- `input_prediction_path`
- `aligned_prediction_path`
- `scorer_ready_prediction_path`
- `target_universe_source`
- `gene_space_source`
- `allow_missing_targets`
- `allow_missing_genes`
- `contract_pass`

并明确标记对象类型：

- `null`
- `baseline`
- `entrant`

## 输出路径

建议固定输出路径如下：

- raw output
  `data/predictions/stage2_hcc_raw/<model_id>/<cell_line>/...`

- aligned prediction
  `data/predictions/stage2_hcc_aligned/<model_id>/<cell_line>/predicted_shift_aligned.tsv.gz`

- scorer-ready prediction
  `data/predictions/stage2_hcc_scorer_ready/<model_id>/<cell_line>/predicted_shift.tsv.gz`

- manifest
  `reports/stage2_hcc_prediction_contract/<model_id>/<cell_line>/prediction_manifest.json`

- validation summary
  `reports/stage2_hcc_prediction_validation/<model_id>/<cell_line>/validation_summary.json`

## 当前 gate

只有同时满足下面条件，真实 HCC smoke adjudication 才能开始：

1. `HCC38` 与 `HCC1143` 各自都有 scorer-ready prediction
2. target universe 与 gene space 都通过 contract validation
3. provenance 完整
4. 至少三类对象到位：
   - `null`
   - `shared mean baseline`
   - `strongest entrant`

在这之前，不进入真实 entrant adjudication。

## 与 Stage 1A 的关系

当前正式口径应明确写成：

- `Stage 2 HCC model-side adjudication` follows the `Stage 2 truth-side` bridge definition
- formal evaluation space is `normalized + log1p` shift space
- `Stage 1A X_pseudobulk_delta` remains a separate formal benchmark space
- `Stage 1A` 的 space governance 不直接覆盖 `Stage 2`

## 新 entrant 最小落地路径

如果下一阶段要把新 entrant 接回 HCC Stage 2，最小落地顺序应固定为：

1. 先冻结 entrant identity 与 Stage 2 HCC recipe
2. 再分别产出 `HCC38 / HCC1143` raw output
3. 再导出到 `stage2_truth_aligned_log_shift`
4. 再做 contract validation
5. 最后才进入 real HCC smoke comparison

若缺少其中任一步，就不应直接进入正式 HCC primary adjudication。

直接执行清单见：

- [`docs/next_stage_model_entrant_execution_checklist_v1.md`](/home/data/gz0705/WTKO/docs/next_stage_model_entrant_execution_checklist_v1.md)

候选 entrant 盘点见：

- [`docs/next_stage_model_entrant_inventory_v1.md`](/home/data/gz0705/WTKO/docs/next_stage_model_entrant_inventory_v1.md)
