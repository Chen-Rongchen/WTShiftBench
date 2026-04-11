# Stage 2 Geneformer HCC recipe freeze v1

## 1. 文档定位

这份文档只回答一个问题：

**如果下一阶段要把 `Geneformer` 接入 HCC Stage 2 primary mainline，第一版正式 recipe 应如何冻结？**

它当前已经冻结 contract 与 recipe，并且已经完成第一轮 `HCC38 / HCC1143` raw output、export、contract validation 与 real HCC smoke 接入。

## 2. 当前冻结结论

当前最稳的第一版 freeze 应固定为：

- `entrant_id = geneformer`
- `entrant_version = geneformer_hcc_formal_v1`
- `checkpoint_key = geneformer_gf_12l_95m_i4096`
- `model_family = Geneformer`
- `workflow_type = embedding_plus_adapter`
- `trainable_components = adapter_head_only`
- `backbone_freeze = true`

也就是说，`Geneformer` 的 HCC Stage 2 entrant 身份，当前应继续保持：

- `foundation_model_plus_adapter`
- fixed backbone
- `embedding_plus_adapter`
- trainable adapter/head

而不是：

- backbone 全量微调
- `embedding_plus_adapter / in_silico_perturbation_plus_adapter` 两条 workflow 并行竞争
- 一边跑 HCC 一边改 workflow identity

## 3. recipe 冻结的最小对象

### 3.1 entrant identity

必须固定：

- `model_id = geneformer_hcc_formal_v1`
- `model_version = geneformer_hcc_formal_v1`
- `source_checkpoint = geneformer_gf_12l_95m_i4096`
- `checkpoint_registry_ref = configs/stage2/checkpoint_registry_v1.yaml`

### 3.2 preprocessing identity

当前第一版固定写成：

- gene symbol 先映射到 `Ensembl`
- 再映射到 `Geneformer token_dictionary_gc104M.pkl`
- target-side embedding lookup
- 不把 held-out perturbation cells 直接作为训练输入
- raw output 之后统一导出到 `stage2_truth_aligned_log_shift`

### 3.3 trainable components

当前第一版固定写成：

- `workflow_type = embedding_plus_adapter`
- `backbone = frozen`
- `adapter_head = trainable`

### 3.4 export recipe

当前第一版固定写成：

1. 先生成 model-native raw output
2. 再进入 `stage2_truth_aligned_log_shift` export
3. 再进入 scorer-ready prediction contract

当前明确不允许：

- 直接把 model-native embedding 当 scorer input
- 跳过 aligned prediction 层
- 跳过 contract validation

### 3.5 fallback policy

当前第一版固定沿用：

- unmapped held-out target 使用 `mean_train_real_shift` fallback

但必须把 fallback 覆盖率显式落盘，不能只在运行时隐式发生。

## 4. 当前仍未冻结的内容

以下对象当前仍未被视为已完成：

- 更强 recipe 变体比较
- 与 `scGPT / GEARS` 的 entrant family 解释层整合
- 基于 `Geneformer` 结果的正式写作归位

因此，这份 freeze 当前只关闭：

- entrant identity 漂移
- workflow identity 漂移
- export 语义漂移

而不关闭：

- entrant family 扩展完成
- HCC performance 的最终写作定稿

## 5. 当前实际运行状态

截至当前版本，`Geneformer` 这条线已经完成：

- `HCC38` raw output 落盘
- `HCC1143` raw output 落盘
- 双 cell line `coverage_audit.json` 生成
- 双 cell line export 到 `stage2_truth_aligned_log_shift`
- 双 cell line contract validation 通过
- `run_stage2_real_hcc_smoke.py` 自动纳入 entrant comparison

当前最关键的运行事实是：

- `target_vocab_coverage = 1.0000`，在 `HCC38 / HCC1143` 都成立
- `Geneformer` 已不再是“未接入 HCC 主线”的对象，而是“已正式接入，且当前强于 scGPT、但仍弱于 baseline 的 entrant”

## 6. 推荐 machine-readable 配置

对应配置骨架：

- [`configs/stage2/geneformer_hcc_formal_v1.json`](/home/data/gz0705/WTKO/configs/stage2/geneformer_hcc_formal_v1.json)

## 7. 当前已固定的运行入口

当前对应的 raw output producer 入口已经固定为：

- [`scripts/run_stage2_geneformer_hcc_predictions.py`](/home/data/gz0705/WTKO/scripts/run_stage2_geneformer_hcc_predictions.py)

最小运行命令模板：

```bash
PYTHONPATH=src python scripts/run_stage2_geneformer_hcc_predictions.py \
  --config configs/stage2/geneformer_hcc_formal_v1.json \
  --cell-line HCC38
```

```bash
PYTHONPATH=src python scripts/run_stage2_geneformer_hcc_predictions.py \
  --config configs/stage2/geneformer_hcc_formal_v1.json \
  --cell-line HCC1143
```

对应 raw output 路径固定为：

- `data/predictions/stage2_geneformer_raw/geneformer_hcc_formal_v1/<cell_line>/predicted_shift.tsv.gz`
- `data/predictions/stage2_geneformer_raw/geneformer_hcc_formal_v1/<cell_line>/raw_prediction_metadata.json`
- `reports/stage2_geneformer_hcc_recipe/<cell_line>/coverage_audit.json`

## 8. 下一步直接做什么

在当前这轮 `Geneformer` 接入已经完成后，最直接的下一步应是：

1. 把 `Geneformer` 的 HCC adjudication 结果写回项目级摘要
2. 决定 foundation-model entrant family 是否到此收口
3. 如果继续 entrant expansion，只在明确 stop rule 下考虑 challengers

直接执行清单见：

- [`docs/next_stage_model_entrant_execution_checklist_v1.md`](/home/data/gz0705/WTKO/docs/next_stage_model_entrant_execution_checklist_v1.md)

## 9. 一句话收口

`Geneformer` 的 HCC Stage 2 第一版 freeze 已经从“只钉 identity 与 contract”推进到“真实 HCC entrant 已落地”；当前结论不是“它能赢”，而是“它已经被公平纳入同一裁决，且当前强于 scGPT，但仍不是 stronger entrant”。
