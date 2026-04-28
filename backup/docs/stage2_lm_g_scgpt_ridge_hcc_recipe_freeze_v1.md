# Stage 2 lm_G_scgpt_ridge HCC recipe freeze v1

## 1. 文档定位

这份文档只回答一个问题：

**如果下一阶段要把 `lm_G_scgpt_ridge` 接入 HCC Stage 2 linear control 比较，第一版正式 recipe 应如何冻结？**

它当前冻结的是 control identity、feature source、closed-form 线性解与 export contract；并且 `HCC38 / HCC1143` raw output、export、contract validation 与 real HCC smoke 已完成。

## 2. 当前冻结结论

当前最稳的第一版 freeze 应固定为：

- `entrant_id = lm_G_scgpt_ridge`
- `entrant_version = lm_g_scgpt_ridge_hcc_formal_v1`
- `feature_id = scgpt_gene_embedding_human`
- `checkpoint_key = scgpt_human`
- `model_family = linear_ridge_external_feature`
- `trainable_components = closed_form_linear_map_only`

也就是说，`lm_G_scgpt_ridge` 的 HCC Stage 2 身份当前应固定为：

- explanation-oriented embedding ablation control
- runtime checkpoint embedding lookup
- closed-form linear ridge map

## 3. recipe 冻结的最小对象

### 3.1 control identity

必须固定：

- `model_id = lm_g_scgpt_ridge_hcc_formal_v1`
- `model_version = lm_g_scgpt_ridge_hcc_formal_v1`
- `feature_id = scgpt_gene_embedding_human`
- `checkpoint_key = scgpt_human`

### 3.2 preprocessing identity

当前第一版固定写成：

- 运行时从 `scGPT` checkpoint 解析 target embedding
- 不把 held-out target 的 truth delta 直接并入训练输入
- raw output 之后统一导出到 `stage2_truth_aligned_log_shift`

### 3.3 trainable components

当前第一版固定写成：

- `backbone = frozen`
- `linear_map = closed_form`

## 4. 当前已完成状态

以下对象当前已完成：

- `HCC38` raw output 正式落盘
- `HCC1143` raw output 正式落盘
- export / validation / smoke comparison

当前跨细胞系均值已进入：

- [`reports/stage2_real_hcc_smoke/model_comparison.tsv`](/home/data/gz0705/WTKO/reports/stage2_real_hcc_smoke/model_comparison.tsv)

当前结果为：

- `backbone_recovery = 0.467`
- `shift_excess_identification = 0.167`
- `structure_vs_context_separation = 0.259`

因此它当前应被视为：

- 已正式接入的 `scGPT` embedding ablation control
- 弱 control
- `direction` 型 backbone failure 的例子

## 5. 推荐 machine-readable 配置

对应配置骨架：

- [`configs/stage2/lm_g_scgpt_ridge_hcc_formal_v1.json`](/home/data/gz0705/WTKO/configs/stage2/lm_g_scgpt_ridge_hcc_formal_v1.json)

## 6. 当前已固定的运行入口

当前对应的 raw output producer 入口已经固定为：

- [`scripts/run_stage2_lm_g_scgpt_ridge_hcc_predictions.py`](/home/data/gz0705/WTKO/scripts/run_stage2_lm_g_scgpt_ridge_hcc_predictions.py)

最小运行命令模板：

```bash
PYTHONPATH=src python scripts/run_stage2_lm_g_scgpt_ridge_hcc_predictions.py \
  --config configs/stage2/lm_g_scgpt_ridge_hcc_formal_v1.json \
  --cell-line HCC38
```

## 7. 一句话收口

`lm_G_scgpt_ridge` 的 HCC Stage 2 第一版 freeze 已经从“等待接入”推进到“正式完成同一条 HCC contract 裁决”；当前结论不是它能赢，而是它已证明单独冻结 `scGPT` target embedding 加线性头不足以恢复 stronger backbone。
