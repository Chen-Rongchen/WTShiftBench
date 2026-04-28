# Stage 2 Dixit Admission Contract v1

## 1. 文档定位

这份文档只冻结一件事：

**`Dixit/K562` 相关对象在当前 truth-first 主线里，哪些可以进入正式 supplementary / temporal panel path，哪些只能保留为 exploratory 或 historical-only。**

它不重讲 HCC 主线，也不把 `Dixit` 升格为与 `HCC38 / HCC1143` 并列的 primary pillar。

## 2. 准入分层

当前固定采用三层准入：

- `formal_candidate_bridge_context`
  `GSE90063 K562 TF pool 13d-only`
- `temporal_sensitivity_probe`
  `GSE90063 K562 TF pool 7d`
- `historical_only`
  `dixit_2016_raw__control_context`

从本版本起，`GSE90063 K562 TF pool 13d/7d` 正式升级为下一阶段明确执行项：同一外部 K562 TF pool context 下，对同一 DepMap endpoint 的 temporal panel。该升级不改变主张层级：`13d` 是 primary formal supplementary bridge test；`7d` 是 temporal sensitivity / early-bridge probe，不承担 primary closure，也不能写成 external model-side generalization proved。

## 3. 当前冻结结论

### 3.1 Formal candidate bridge context

当前唯一可进入正式 supplementary path 的对象是：

- `dixit_2016_k562_tf_13d_gse90063`

它满足当前最小 admission 条件：

- 已有可物化的 count matrix、gene names、cell barcodes 与 guide assignment
- 已能生成 `h5ad_obs` 输入并进入 Stage 2 truth bridge
- 已能输出独立的 truth bridge report 与 axis compression report
- 时间尺度只能写成与 DepMap `~14-21d` fitness screen `time-scale compatible`
- 其职责是补 `architecture-to-DepMap bridge form` 的外部 context，而不是承担 HCC anchor content replication

当前对应配置：

- `configs/stage2/truth_driven_bridge_dixit_k562_supplement.json`
- `configs/stage2/dixit_axis_compression_v1.json`
- `configs/stage2/truth_driven_bridge_dixit_k562_tf_13d_gse90063_v1.json`
- `configs/stage2/dixit_k562_tf_13d_structure_replication_gse90063_v1.json`

### 3.2 Temporal sensitivity probe

`dixit_2016_k562_tf_7d_gse90063` 当前只保留为：

- temporal sensitivity
- early-bridge probe
- 同一 K562 TF pool 外部 context 下的 cross-timescale 对照

它当前**不承担**：

- primary closure
- matched endpoint
- formal supplementary headline path
- full external model-side generalization

当前对应配置：

- `configs/stage2/truth_driven_bridge_dixit_k562_tf_7d_gse90063_v1.json`
- `configs/stage2/dixit_k562_tf_7d_structure_replication_gse90063_v1.json`

当前项目对象层结论固定为：

- 在当前项目对象层与现行 admission/bridgeability 规则下，`7d` 与 `13d` 目前各有 10 个正式 bridgeable targets 进入 DepMap 对接。
- 这 10 个 targets 是 `CREB1 / E2F4 / EGR1 / ELF1 / ELK1 / ETS1 / GABPA / IRF1 / NR2C2 / YY1`。
- 这一数字不应与原始实验设计中的 target / guide 数直接等同；当前 QC 层显示 `7d` 与 `13d` 都是 `guide_rows=30`、`sg_guides=26`、`intergenic_guides=4`。

### 3.3 RNAi endpoint sensitivity

`DEMETER2 RNAi` 当前只作为 `GSE90063 K562 13d/7d` 的 cross-platform sensitivity endpoint。它不改变 `13d / 7d` 的 CRISPR KO truth 身份，也不替代 matched primary endpoint。

固定口径：

- `CRISPR DepMap = matched primary endpoint`
- `RNAi DEMETER2 = cross-platform sensitivity endpoint`
- `RNAi` 不替代 CRISPR 主线，也不提供等价 primary evidence

当前对应配置：

- `configs/stage2/rnai_demeter2_conversion_v1.json`
- `configs/stage2/truth_driven_bridge_dixit_k562_tf_7d_gse90063_rnai_demeter2_v1.json`
- `configs/stage2/truth_driven_bridge_dixit_k562_tf_13d_gse90063_rnai_demeter2_v1.json`
- `configs/stage2/k562_rnai_endpoint_consistency_v1.json`

当前允许写成：

- `7d CRISPR KO truth vs DEMETER2 RNAi endpoint`
- `13d CRISPR KO truth vs DEMETER2 RNAi endpoint`
- `CRISPR DepMap vs DEMETER2 RNAi endpoint consistency`
- cross-platform sensitivity / endpoint robustness

当前不能写成：

- `RNAi` 是 matched primary endpoint
- `RNAi` 替代 `CRISPR DepMap` 主线
- `RNAi` 证明等价 primary evidence
- `GSE90063 7d/13d` 是 CRISPRi truth

### 3.4 Historical only

`dixit_2016_raw__control_context` 当前固定为：

- 历史对象
- 数据身份纠偏后的 legacy lineage
- historical replay only

它当前**不能**再承担：

- 可引用的 Dixit supplementary 证据
- README 默认命令
- startup packet 默认执行链

当前对应历史配置：

- `configs/stage2/truth_driven_bridge_dixit_k562_legacy_v1.json`
- `configs/stage2/dixit_axis_compression_legacy_v1.json`
- `configs/stage2/dixit_k562_structure_replication_legacy_v1.json`

## 4. Formal admission 条件

`Dixit/K562` 对象若要进入 formal supplementary path，至少要满足：

1. 原始输入身份清楚，且与公开数据描述一致
2. 可恢复单扰动判定证据、guide-cell assignment 与 target gene mapping
3. 能形成独立的 truth bridge 报告与 structure replication 报告
4. 在写作上能保持 `A0 / A1 / B` 分层，不把 content-level claim 误写成 bridge headline
5. 能明确声明时间尺度边界，只写 `time-scale compatible`，不写 `matched endpoint`

## 5. 当前 admission 结果

按当前仓库状态，固定写成：

- `13d`：admitted as primary formal supplementary bridge test
- `7d`：admitted as temporal sensitivity / early-bridge probe within the GSE90063 K562 temporal panel
- `legacy`：demoted to historical-only replay path

## 6. 默认阅读与执行

默认先看：

1. `reports/stage2_gse90063_qc/dixit_2016_k562_tf_13d_summary.tsv`
2. `reports/stage2_gse90063_qc/dixit_2016_k562_tf_7d_summary.tsv`
3. `reports/stage2_truth_driven_bridge_gse90063_13d/stage2_truth_driven_bridge_report.md`
4. `reports/stage2_truth_driven_bridge_gse90063_7d/stage2_truth_driven_bridge_report.md`
5. `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_structure_replication_summary.tsv`
6. `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_7d/dixit_structure_replication_summary.tsv`

默认执行链固定为：

```bash
PYTHONPATH=src python scripts/build_stage2_truth_driven_bridge.py \
  --config configs/stage2/truth_driven_bridge_dixit_k562_supplement.json
PYTHONPATH=src python scripts/run_stage2_dixit_axis_compression.py \
  --config configs/stage2/dixit_axis_compression_v1.json
```

`7d` 不进入默认 13d headline path；若执行 temporal panel，对应显式入口为：

```bash
PYTHONPATH=src python scripts/build_stage2_truth_driven_bridge.py \
  --config configs/stage2/truth_driven_bridge_dixit_k562_tf_7d_gse90063_v1.json
PYTHONPATH=src python scripts/run_stage2_dixit_axis_compression.py \
  --config configs/stage2/dixit_k562_tf_7d_structure_replication_gse90063_v1.json
```

若执行 RNAi endpoint sensitivity，对应显式 pixi 入口为：

```bash
pixi run --environment core build-stage2-truth-driven-bridge-k562-7d-rnai-demeter2
pixi run --environment core build-stage2-truth-driven-bridge-k562-13d-rnai-demeter2
pixi run --environment core run-stage2-k562-rnai-endpoint-consistency
```
