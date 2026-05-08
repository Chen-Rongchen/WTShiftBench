# LEGACY NOTICE — dixit_axis_compression

**状态（2026-04-17 冻结）：legacy / 暂停引用。**

本目录的 axis compression / claim tiering / structure replication 产物是基于历史 `dixit_2016_raw__control_context` bridge table（见 `run_manifest.json` 中的 `k562_dataset_label`）。该上游输入已因数据身份警报被标记为 legacy（详见 `../dixit_2016_raw__control_context/LEGACY_NOTICE.md`）。

## 口径

- 本目录下的 `dixit_axis_*.tsv`、`dixit_claim_tiering.tsv`、`dixit_evidence_tier_summary.tsv`、`dixit_master_atlas.tsv`、`dixit_structure_replication_summary.tsv` 保留为 legacy lineage，不作为 Dixit/K562 supplementary axis / replication 的正式证据。
- 当前 K562 TF pool 正式 axis compression 入口：
  - `reports/truth_driven_bridge/dixit_axis_compression_gse90063_13d/`
  - `reports/truth_driven_bridge/dixit_axis_compression_gse90063_7d/`
- 当前 temporal panel 入口：
  - `reports/truth_driven_bridge/dixit_temporal_panel_gse90063/`

## 相关文档

- `docs/stage2_dixit_admission_contract_v1.md`
- `docs/stage2_truth_bridge_integrated_result_v1.md`
- `plan.md`（§1 / §6）
- `README.md`（§1.1）

## 不允许的用法

- 把本目录产物写进主文、补充表或 figure legend
- 以本目录产物更新 `final_claim_matrix` / anchor tiering
- 将本目录与 `dixit_axis_compression_gse90063_13d / 7d` 同级并列引用
