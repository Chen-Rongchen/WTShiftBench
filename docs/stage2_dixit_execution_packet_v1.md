# Stage 2 Dixit/K562 执行包 v1

## 1. 文档定位

这份文档只回答一个问题：

**如果下次进来要把 Dixit/K562 supplementary replication 直接重跑并收口，最短执行链是什么？**

它不重讲 claim governance，只固定可执行入口、配置和最小验收产物。

## 2. 当前定位

`Dixit/K562` 当前不是 primary mainline evidence，而是：

- `supplementary external structure replication`
- `architecture-level replication`
- `structure-level transferability`

它支持：

- external architecture existence
- context-specific backbone replication
- stable anchor-like structure recurrence

它不支持：

- `model generalization proved`
- 与 HCC 对称的 primary conclusion
- fine-axis 一一对应复现

## 3. 直接运行入口

配置：

- [`configs/stage2/dixit_k562_structure_replication_v1.json`](/home/data/gz0705/WTKO/configs/stage2/dixit_k562_structure_replication_v1.json)

CLI：

- [`scripts/stage2_dixit_axis_compression.py`](/home/data/gz0705/WTKO/scripts/stage2_dixit_axis_compression.py)

最小命令：

```bash
python scripts/stage2_dixit_axis_compression.py \
  --config configs/stage2/dixit_k562_structure_replication_v1.json
```

## 4. 最小验收产物

至少要看到这些文件被刷新：

- `reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_master_atlas.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_axis_membership.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_axis_summary.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_structure_replication_summary.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_evidence_tier_summary.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_claim_tiering.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression/run_manifest.json`

## 5. 下次先读什么

先看：

1. [`reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_structure_replication_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_structure_replication_summary.tsv)
2. [`reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_evidence_tier_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_evidence_tier_summary.tsv)
3. [`reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_claim_tiering.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression/dixit_claim_tiering.tsv)

再看：

- [`docs/stage2_dixit_supplementary_evidence_tier_v1.md`](/home/data/gz0705/WTKO/docs/stage2_dixit_supplementary_evidence_tier_v1.md)
- [`docs/stage2_truth_bridge_integrated_result_v1.md`](/home/data/gz0705/WTKO/docs/stage2_truth_bridge_integrated_result_v1.md)

## 6. 一句话收口

`Dixit/K562` 这条线当前已经不只是“有一批历史产物”，而是有了 config-driven 的重跑入口；下次进入仓库时，可以直接重跑 supplementary replication，而不用再凭记忆拼路径。
