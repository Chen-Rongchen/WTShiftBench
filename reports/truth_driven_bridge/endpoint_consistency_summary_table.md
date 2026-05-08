# Cross-Context Endpoint Consistency Summary

## 定位

- **CRISPR DepMap = formal primary bridge readout**（所有四个 context 中均强）
- **RNAi DEMETER2 = weaker cross-platform sensitivity endpoint**（所有四个 context 中均弱）
- 这不是 K562 特例，而是跨 HCC + K562 的 framework-level observation

## Endpoint Consistency Table

| Context | Role | CRISPR bridge Spearman | RNAi bridge Spearman | CRISPR vs RNAi endpoint Spearman | Bridgeable targets | Call |
|---------|------|------------------------|---------------------|--------------------------------|---------------------|------|
| HCC38 | primary | 0.726 | 0.276 | 0.141 | 47–48 | rnai_bridge_weaker_than_crispr_sensitivity |
| HCC1143 | primary | 0.779 | 0.384 | 0.231 | 47–48 | rnai_bridge_weaker_than_crispr_sensitivity |
| K562 7d | temporal_sensitivity_early_bridge_probe | 0.733 | 0.333 | 0.450 | 9–10 | rnai_bridge_weaker_than_crispr_sensitivity |
| K562 13d | primary_formal_supplementary_bridge_test | 0.515 | 0.300 | 0.450 | 9–10 | rnai_bridge_weaker_than_crispr_sensitivity |

Primary truth metric: `real_shift_mean_abs`; primary DepMap endpoint: `depmap_gene_dependency`.

## 解读

### 1. CRISPR endpoint 更强且更稳定

CRISPR bridge Spearman 在四个 context 中均明显高于 RNAi（0.51–0.78 vs 0.28–0.38），说明 matched CRISPR endpoint 是更可靠的 truth–dependency bridge readout。

### 2. HCC 的 CRISPR–RNAi 平台间一致性比 K562 更差

| Context group | CRISPR vs RNAi endpoint Spearman |
|---------------|----------------------------------|
| HCC (38/1143) | 0.141 / 0.231 |
| K562 (7d/13d) | 0.450 / 0.450 |

这意味着：
- K562 中 CRISPR 与 RNAi 的平台间一致性是 moderate（0.45）
- HCC 中这种平台间一致性更弱（0.14–0.23）

提示 **cross-platform robustness 本身是 context-dependent 的**，endpoint 替换不能在不同 context 中一致保留 bridge strength 或 target ranking。

### 3. Endpoint hierarchy 已钉实

四个 context 的 call 全部一致为 `rnai_bridge_weaker_than_crispr_sensitivity`，说明：

- 不是事后挑选的特例
- 不是针对某一个 dataset 的特判
- 而是跨多个 context 重复出现的 framework-level observation

## 正式措辞

**Results 层**（建议）：

> Across HCC38, HCC1143, K562 7d, and K562 13d, matched CRISPR dependency endpoints consistently retained stronger truth–dependency bridge signals than RNAi DEMETER2 endpoints. This supports the use of CRISPR endpoints as the formal primary bridge readouts, while positioning RNAi as a weaker cross-platform sensitivity endpoint.

**Discussion 层**（建议）：

> Cross-platform agreement between CRISPR and RNAi endpoints was context-dependent and notably weaker in HCC than in K562 (Spearman = 0.14–0.23 vs 0.45), indicating that endpoint substitution cannot be assumed to preserve bridge strength or target ranking uniformly across settings.

## 产物

- HCC endpoint consistency: `reports/truth_driven_bridge/hcc38_hcc1143_rnai_endpoint_consistency/`
- K562 endpoint consistency: `reports/truth_driven_bridge/k562_rnai_endpoint_consistency/`
- 汇总表: `reports/truth_driven_bridge/endpoint_consistency_summary_table.md`
