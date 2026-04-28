# Stage 2 Dixit/K562 执行包 v1

## 1. 文档定位

这份文档只回答一个问题：

**如果下次进来要把 `Dixit/K562` supplementary path 直接重跑并收口，当前最短正式执行链是什么？**

它不重讲 HCC 主线，也不处理历史 lineage 纠偏；准入边界固定看 `docs/stage2_dixit_admission_contract_v1.md`。

## 2. 当前固定入口

当前唯一正式默认入口是：

- `GSE90063 K562 TF pool 13d-only`

角色固定为：

- `supplementary external structure replication`
- `architecture-to-DepMap bridge candidate context`
- `time-scale compatible` with DepMap `~14-21d`

当前**不**固定为：

- 与 `HCC38 / HCC1143` 对称的 co-primary pillar
- broad cross-context validation
- content-level anchor replication

## 3. 直接运行入口

### 3.1 默认 direct-script recipe

配置：

- [`configs/stage2/dixit_k562_structure_replication_v1.json`](/home/data/gz0705/WTKO/configs/stage2/dixit_k562_structure_replication_v1.json)

CLI：

- [`scripts/stage2_dixit_axis_compression.py`](/home/data/gz0705/WTKO/scripts/stage2_dixit_axis_compression.py)

最小命令：

```bash
python scripts/stage2_dixit_axis_compression.py \
  --config configs/stage2/dixit_k562_structure_replication_v1.json
```

### 3.2 显式冻结版 recipe

如果你想显式写出 `13d` provenance，使用：

```bash
python scripts/stage2_dixit_axis_compression.py \
  --config configs/stage2/dixit_k562_tf_13d_structure_replication_gse90063_v1.json
```

### 3.3 config-driven wrapper

如果你想统一走 wrapper，使用：

```bash
PYTHONPATH=src python scripts/run_stage2_dixit_axis_compression.py \
  --config configs/stage2/dixit_axis_compression_v1.json
```

## 4. 最小验收产物

至少要看到这些文件被刷新：

- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_master_atlas.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_axis_membership.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_axis_summary.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_structure_replication_summary.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_evidence_tier_summary.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_claim_tiering.tsv`
- `reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/run_manifest.json`

## 5. 下次先读什么

先看：

1. [`reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_structure_replication_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_structure_replication_summary.tsv)
2. [`reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_evidence_tier_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_evidence_tier_summary.tsv)
3. [`reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_claim_tiering.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/dixit_axis_compression_gse90063_13d/dixit_claim_tiering.tsv)

再看：

- [`docs/stage2_dixit_supplementary_evidence_tier_v1.md`](/home/data/gz0705/WTKO/docs/stage2_dixit_supplementary_evidence_tier_v1.md)
- [`docs/stage2_dixit_admission_contract_v1.md`](/home/data/gz0705/WTKO/docs/stage2_dixit_admission_contract_v1.md)

## 6. 历史与探索入口

- `7d` 只作为 temporal sensitivity / early-bridge probe，配置见 `configs/stage2/dixit_k562_tf_7d_structure_replication_gse90063_v1.json`
- legacy replay 只允许显式使用 `configs/stage2/dixit_k562_structure_replication_legacy_v1.json`

## 7. 一句话收口

`Dixit/K562` 这条线当前已经从“历史 supplementary 入口”收口为 `GSE90063 K562 13d/7d temporal panel`；`13d` 是 primary formal supplementary bridge test，`7d` 是 temporal sensitivity / early-bridge probe，legacy 仍保留但不再承担默认 recipe 身份。
