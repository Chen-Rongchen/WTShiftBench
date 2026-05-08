# LEGACY NOTICE — dixit_2016_raw__control_context

**状态（2026-04-17 冻结）：legacy / 暂停引用。**

本目录是基于 `data/raw/candidates/dixit_2016_raw.h5ad` 派生的早期 Dixit/K562 supplementary bridge 产物。后续核查发现该 `.h5ad` 与 Dixit 2016 / GSE90063 K562 TF pool 的公开描述不匹配（更接近 Frangieh 2021 风格对象，含 IFNγ/Co-culture/Control 条件与 20 蛋白通道），因此它不再作为可引用的 Dixit supplementary replication 输入。

## 口径

- 本目录下的 `bridge_audit.tsv`、`correlation_summary.tsv`、`group_comparison_summary.tsv` 保留为 legacy lineage，不作为可引用的 bridge 证据。
- 当前 Dixit/K562 supplementary 正式入口为 `GSE90063 K562 13d/7d temporal panel`：
  - `13d` 是 primary formal supplementary bridge test
  - `7d` 是 temporal sensitivity / early-bridge probe
- 参见：
  - `reports/truth_driven_bridge/dixit_axis_compression_gse90063_13d/`
  - `reports/truth_driven_bridge/dixit_axis_compression_gse90063_7d/`
  - `reports/truth_driven_bridge/dixit_temporal_panel_gse90063/`

## 相关文档

- `docs/dixit_admission_contract_v1.md`
- `docs/truth_bridge_integrated_result_v1.md`
- `plan.md`（§1 数据身份警报、§6 frozen objects）
- `README.md`（§1.1 数据身份警报）

## 不允许的用法

- 把本目录产物写进主文、补充表或 figure legend
- 把 `dixit_2016_raw__control_context` 当成 Dixit 或 GSE90063 K562 supplementary replication 的有效证据
- 基于本目录产物重新启动 bridge / axis / claim 更新
