# stage2_k562_rnai_endpoint_consistency RNAi endpoint consistency

## 定位

- CRISPR DepMap = matched primary endpoint。
- RNAi DEMETER2 = cross-platform sensitivity endpoint。
- RNAi 不替代 CRISPR 主线，也不提供等价 primary evidence。

## Primary readout

- `7d`：CRISPR bridge Spearman = `0.7333333333333332`；RNAi bridge Spearman = `0.33333333333333337`；CRISPR vs RNAi endpoint Spearman = `0.45`；call = `rnai_bridge_weaker_than_crispr_sensitivity`。
- `13d`：CRISPR bridge Spearman = `0.5151515151515151`；RNAi bridge Spearman = `0.3`；CRISPR vs RNAi endpoint Spearman = `0.45`；call = `rnai_bridge_weaker_than_crispr_sensitivity`。

## 产物

- `endpoint_consistency_summary.tsv`
- `endpoint_consistency_calls.tsv`
- `endpoint_consistency_target_table.tsv`
