# hcc38_hcc1143_rnai_endpoint_consistency RNAi endpoint consistency

## 定位

- CRISPR DepMap = matched primary endpoint。
- RNAi DEMETER2 = cross-platform sensitivity endpoint。
- RNAi 不替代 CRISPR 主线，也不提供等价 primary evidence。

## Primary readout

- `HCC38`：CRISPR bridge Spearman = `0.7257957275155708`；RNAi bridge Spearman = `0.27637863656100736`；CRISPR vs RNAi endpoint Spearman = `0.14119279587294065`；call = `rnai_bridge_weaker_than_crispr_sensitivity`。
- `HCC1143`：CRISPR bridge Spearman = `0.7792497165337711`；RNAi bridge Spearman = `0.3844984802431611`；CRISPR vs RNAi endpoint Spearman = `0.2307558942118978`；call = `rnai_bridge_weaker_than_crispr_sensitivity`。

## 产物

- `endpoint_consistency_summary.tsv`
- `endpoint_consistency_calls.tsv`
- `endpoint_consistency_target_table.tsv`
