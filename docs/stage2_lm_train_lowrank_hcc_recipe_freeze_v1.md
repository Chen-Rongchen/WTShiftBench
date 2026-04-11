# Stage 2 lm_train_lowrank HCC recipe freeze v1

## 1. 文档定位

这份文档只回答一个问题：

**如果下一阶段要把 `lm_train_lowrank` 接入 HCC Stage 2 linear control 比较，第一版正式 recipe 应如何冻结？**

它当前已经冻结 control identity、feature source、closed-form 线性解与 export contract，并且已经完成第一轮 `HCC38 / HCC1143` raw output、export、contract validation 与 real HCC smoke 接入。

## 2. 当前冻结结论

当前最稳的第一版 freeze 应固定为：

- `entrant_id = lm_train_lowrank`
- `entrant_version = lm_train_lowrank_hcc_formal_v1`
- `feature_id = gene_symbol_chargram_v1`
- `model_family = linear_lowrank_external_feature`
- `trainable_components = closed_form_linear_map_only`
- `backbone_freeze = true`

也就是说，`lm_train_lowrank` 的 HCC Stage 2 身份当前应固定为：

- explanation-oriented linear control
- frozen external target feature
- closed-form linear map

而不是：

- 新 entrant family
- 带训练循环的可调深模型
- 一边跑 HCC 一边改 feature source

## 3. recipe 冻结的最小对象

### 3.1 control identity

必须固定：

- `model_id = lm_train_lowrank_hcc_formal_v1`
- `model_version = lm_train_lowrank_hcc_formal_v1`
- `feature_id = gene_symbol_chargram_v1`
- `feature_registry_ref = configs/stage2/feature_registry_v1.json`

### 3.2 preprocessing identity

当前第一版固定写成：

- target-side symbolic chargram feature
- 不把 held-out target 的 truth delta 直接并入训练输入
- raw output 之后统一导出到 `stage2_truth_aligned_log_shift`

### 3.3 trainable components

当前第一版固定写成：

- `backbone = frozen`
- `linear_map = closed_form`

### 3.4 export recipe

当前第一版固定写成：

1. 先生成 model-native raw output
2. 再进入 `stage2_truth_aligned_log_shift` export
3. 再进入 scorer-ready prediction contract

## 4. 当前仍未完成的内容

以下对象当前仍未被视为已完成：

- 与 `scGPT / Geneformer / GEARS` 的最终解释层整合
- 是否继续做 `lm_G_scgpt_ridge`
- 是否继续做 `lm_G_geneformer_ridge`

## 5. 推荐 machine-readable 配置

对应配置骨架：

- [`configs/stage2/lm_train_lowrank_hcc_formal_v1.json`](/home/data/gz0705/WTKO/configs/stage2/lm_train_lowrank_hcc_formal_v1.json)

## 6. 当前实际运行状态

截至当前版本，`lm_train_lowrank` 这条线已经完成：

- `HCC38` raw output 落盘
- `HCC1143` raw output 落盘
- 双 cell line `coverage_audit.json` 生成
- 双 cell line export 到 `stage2_truth_aligned_log_shift`
- 双 cell line contract validation 通过
- `run_stage2_real_hcc_smoke.py` 自动纳入 entrant comparison

当前最关键的运行事实是：

- `target_vocab_coverage = 1.0000`，在 `HCC38 / HCC1143` 都成立
- `lm_train_lowrank` 已不再是“待接入的线性 control”，而是“已正式接入、当前 backbone 略高于 `Geneformer`、但 separation 明显较弱的 control”

## 7. 当前已固定的运行入口

当前对应的 raw output producer 入口已经固定为：

- [`scripts/run_stage2_lm_train_lowrank_hcc_predictions.py`](/home/data/gz0705/WTKO/scripts/run_stage2_lm_train_lowrank_hcc_predictions.py)

最小运行命令模板：

```bash
PYTHONPATH=src python scripts/run_stage2_lm_train_lowrank_hcc_predictions.py \
  --config configs/stage2/lm_train_lowrank_hcc_formal_v1.json \
  --cell-line HCC38
```

```bash
PYTHONPATH=src python scripts/run_stage2_lm_train_lowrank_hcc_predictions.py \
  --config configs/stage2/lm_train_lowrank_hcc_formal_v1.json \
  --cell-line HCC1143
```

## 8. 一句话收口

`lm_train_lowrank` 的 HCC Stage 2 第一版 freeze 已经从“待接入 control”推进到“真实 HCC control 已落地”；当前结论不是“它赢了”，而是“它已经被公平纳入同一裁决，并证明线性 low-rank control 也能在部分维度接近 foundation-model entrant，但仍不是 current winner”。
