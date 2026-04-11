# Stage 2 Dixit supplementary startup packet v1

## 1. 文档定位

这份文档只回答一个问题：

**如果下次进入仓库要把 `Dixit/K562` supplementary external structure replication 一次执行完，应该按什么顺序直接跑？**

它不重讲 HCC 主线，也不把 `Dixit` 抬成 primary evidence。它只固定可重跑入口、产物路径与允许写法。

## 2. 当前结论先固定

`Dixit/K562` 当前只用于：

- supplementary external structure replication
- architecture-level replication
- structure-level transferability

当前不能写成：

- `model generalization proved`
- 与 `HCC38 / HCC1143` 对称的 primary conclusion
- 同一 frozen axis 或同一 anchors 已完成严格跨 context replication

## 3. 直接执行顺序

只按这个顺序：

1. 刷新 Dixit truth bridge 输入
2. 刷新 SCP542 explanation boundary
3. 刷新 Dixit axis compression
4. 回读 supplementary evidence tier

## 4. 直接运行入口

### 4.1 Dixit truth bridge

```bash
PYTHONPATH=src python scripts/run_stage2_truth_bridge.py \
  --config configs/stage2/truth_driven_bridge_dixit_k562_supplement.json
```

### 4.2 SCP542 boundary

```bash
PYTHONPATH=src python scripts/stage2_freeze_scp542_explanation_boundaries.py
```

### 4.3 Dixit axis compression

```bash
PYTHONPATH=src python scripts/run_stage2_dixit_axis_compression.py \
  --config configs/stage2/dixit_axis_compression_v1.json
```

## 5. 核心输入

- [`configs/stage2/truth_driven_bridge_dixit_k562_supplement.json`](/home/data/gz0705/WTKO/configs/stage2/truth_driven_bridge_dixit_k562_supplement.json)
- [`configs/stage2/dixit_axis_compression_v1.json`](/home/data/gz0705/WTKO/configs/stage2/dixit_axis_compression_v1.json)

## 6. 关键产物

默认先看：

1. [`reports/stage2_truth_driven_bridge_dixit/stage2_truth_driven_bridge_report.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge_dixit/stage2_truth_driven_bridge_report.md)
2. [`reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_structure_replication_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_structure_replication_summary.tsv)
3. [`reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_evidence_tier_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_evidence_tier_summary.tsv)
4. [`reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_claim_tiering.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_claim_tiering.tsv)

## 7. 一句话收口

`Dixit/K562` 这条线当前不是“还没做完结果”，而是“结果已经在，现已补成可重跑、可交接、可直接执行的 supplementary packet”。
