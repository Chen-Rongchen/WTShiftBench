# Stage 2 Dixit supplementary startup packet v1

## 1. 文档定位

这份文档只回答一个问题：

**如果下次进入仓库要把 `Dixit/K562` supplementary external structure replication 与 `13d/7d` temporal panel 一次执行完，当前应该按什么顺序直接跑？**

它不重讲 HCC 主线，也不把 `Dixit` 抬成 primary evidence。准入边界固定看 `docs/stage2_dixit_admission_contract_v1.md`。

## 2. 当前先固定什么

当前默认先启动：

- `GSE90063 K562 TF pool 13d-only`

角色固定为：

- supplementary external structure replication
- architecture-level replication
- architecture-to-DepMap bridge candidate context

从 temporal panel 入口看，当前还应显式启动：

- `GSE90063 K562 TF pool 7d`

角色固定为：

- temporal sensitivity
- early-bridge probe
- 同一 K562 TF pool 外部 context 下的 cross-timescale 对照

当前不能写成：

- `model generalization proved`
- 与 `HCC38 / HCC1143` 对称的 primary conclusion
- 同一 frozen axis 或同一 anchors 已完成严格跨 context replication
- `7d` 是新的 primary closure

## 3. 直接执行顺序

只按这个顺序：

1. 先看 `13d` QC 与 admission 状态
2. 刷新 `13d` truth bridge 输入
3. 显式刷新 `7d` truth bridge 输入
4. 视需要刷新 `SCP542` explanation boundary
5. 刷新 `13d` axis compression
6. 显式刷新 `7d` axis compression
7. 构建 `GSE90063 K562 13d/7d temporal panel`
8. 如需 cross-platform sensitivity，运行 `7d/13d CRISPR KO truth -> DEMETER2 RNAi endpoint`
9. 汇总 `CRISPR DepMap vs DEMETER2 RNAi endpoint consistency`
10. 回读 supplementary evidence tier、temporal panel report 与 endpoint consistency report

## 4. 直接运行入口

### 4.1 先看 admission 与 QC

- `docs/stage2_dixit_admission_contract_v1.md`
- `reports/stage2_gse90063_qc/dixit_2016_k562_tf_13d_summary.tsv`

### 4.2 Dixit truth bridge

```bash
PYTHONPATH=src python scripts/build_stage2_truth_driven_bridge.py \
  --config configs/stage2/truth_driven_bridge_dixit_k562_supplement.json
PYTHONPATH=src python scripts/build_stage2_truth_driven_bridge.py \
  --config configs/stage2/truth_driven_bridge_dixit_k562_tf_7d_gse90063_v1.json
```

### 4.3 SCP542 boundary

```bash
PYTHONPATH=src python scripts/stage2_freeze_scp542_explanation_boundaries.py
```

### 4.4 Dixit axis compression

```bash
PYTHONPATH=src python scripts/run_stage2_dixit_axis_compression.py \
  --config configs/stage2/dixit_axis_compression_v1.json
PYTHONPATH=src python scripts/run_stage2_dixit_axis_compression.py \
  --config configs/stage2/dixit_k562_tf_7d_structure_replication_gse90063_v1.json
```

### 4.5 Dixit temporal panel

```bash
PYTHONPATH=src python scripts/run_stage2_dixit_temporal_panel.py \
  --config configs/stage2/dixit_k562_temporal_panel_gse90063_v1.json
```

### 4.6 RNAi endpoint sensitivity

这一节只用于 cross-platform sensitivity。固定口径是：`CRISPR DepMap = matched primary endpoint`；`RNAi DEMETER2 = cross-platform sensitivity endpoint`；`RNAi` 不替代 CRISPR 主线，也不提供等价 primary evidence。

```bash
pixi run --environment core build-stage2-truth-driven-bridge-k562-7d-rnai-demeter2
pixi run --environment core build-stage2-truth-driven-bridge-k562-13d-rnai-demeter2
pixi run --environment core run-stage2-k562-rnai-endpoint-consistency
```

## 5. 核心输入

- [`configs/stage2/truth_driven_bridge_dixit_k562_supplement.json`](/home/data/gz0705/WTKO/configs/stage2/truth_driven_bridge_dixit_k562_supplement.json)
- [`configs/stage2/truth_driven_bridge_dixit_k562_tf_7d_gse90063_v1.json`](/home/data/gz0705/WTKO/configs/stage2/truth_driven_bridge_dixit_k562_tf_7d_gse90063_v1.json)
- [`configs/stage2/truth_driven_bridge_dixit_k562_tf_7d_gse90063_rnai_demeter2_v1.json`](/home/data/gz0705/WTKO/configs/stage2/truth_driven_bridge_dixit_k562_tf_7d_gse90063_rnai_demeter2_v1.json)
- [`configs/stage2/truth_driven_bridge_dixit_k562_tf_13d_gse90063_rnai_demeter2_v1.json`](/home/data/gz0705/WTKO/configs/stage2/truth_driven_bridge_dixit_k562_tf_13d_gse90063_rnai_demeter2_v1.json)
- [`configs/stage2/k562_rnai_endpoint_consistency_v1.json`](/home/data/gz0705/WTKO/configs/stage2/k562_rnai_endpoint_consistency_v1.json)
- [`configs/stage2/dixit_axis_compression_v1.json`](/home/data/gz0705/WTKO/configs/stage2/dixit_axis_compression_v1.json)
- [`configs/stage2/dixit_k562_tf_7d_structure_replication_gse90063_v1.json`](/home/data/gz0705/WTKO/configs/stage2/dixit_k562_tf_7d_structure_replication_gse90063_v1.json)
- [`configs/stage2/dixit_k562_temporal_panel_gse90063_v1.json`](/home/data/gz0705/WTKO/configs/stage2/dixit_k562_temporal_panel_gse90063_v1.json)
- [`docs/stage2_dixit_admission_contract_v1.md`](/home/data/gz0705/WTKO/docs/stage2_dixit_admission_contract_v1.md)

## 6. 关键产物

默认先看：

1. [`reports/stage2_truth_driven_bridge_gse90063_13d/stage2_truth_driven_bridge_report.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge_gse90063_13d/stage2_truth_driven_bridge_report.md)
2. [`reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_structure_replication_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_structure_replication_summary.tsv)
3. [`reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_evidence_tier_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_evidence_tier_summary.tsv)
4. [`reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_claim_tiering.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_claim_tiering.tsv)
5. [`reports/stage2_truth_driven_bridge_gse90063_7d/stage2_truth_driven_bridge_report.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge_gse90063_7d/stage2_truth_driven_bridge_report.md)
6. [`reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_7d/dixit_structure_replication_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_7d/dixit_structure_replication_summary.tsv)
7. `reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_panel_report.md`
8. `reports/stage2_truth_driven_bridge/k562_rnai_endpoint_consistency/endpoint_consistency_report.md`

## 7. 备用入口

- legacy 只用于 historical replay：
  `configs/stage2/truth_driven_bridge_dixit_k562_legacy_v1.json`
  `configs/stage2/dixit_axis_compression_legacy_v1.json`

## 8. 一句话收口

`Dixit/K562` 这条线当前不是“继续凭记忆拼历史路径”，而是“固定 `GSE90063 K562 13d/7d temporal panel`：`13d` 是 primary formal supplementary bridge test，`7d` 是同一外部 context 下的 temporal sensitivity / early-bridge probe；legacy 只能显式进入 historical replay；DEMETER2 RNAi 只作为 cross-platform sensitivity endpoint，不替代 CRISPR DepMap 主线”。
