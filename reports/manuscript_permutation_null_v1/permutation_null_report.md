# 三指标 permutation null v1

## 状态

该报告使用既有 `axis_projection.tsv` 产物，不重跑模型。Permutation 随机打乱每个 context 内 target 到 expected axis 的映射，保留 projection values 与 axis gene sets，用于检验三指标是否在随机 architecture assignment 下仍能达到 observed score。

## 参数

- iterations: 1000
- seed: 12345
- aggregation: HCC38/HCC1143 context scores averaged to model-level mean
- empirical p: `(null >= observed + 1) / (N + 1)`

## 输出

- `reports/manuscript_permutation_null_v1/observed_context_scores.tsv`
- `reports/manuscript_permutation_null_v1/observed_model_mean_scores.tsv`
- `reports/manuscript_permutation_null_v1/permutation_null_context_scores.tsv.gz`
- `reports/manuscript_permutation_null_v1/permutation_null_model_mean_scores.tsv.gz`
- `reports/manuscript_permutation_null_v1/permutation_null_summary.tsv`

## baseline / GEARS 摘要

| model_id | metric | observed | null_mean | null_q025 | null_q975 | empirical_p_ge_observed | observed_percentile |
|---|---|---:|---:|---:|---:|---:|---:|
| gears_hcc_formal_v1 | backbone_recovery_score | 0.660 | 0.545 | 0.407 | 0.677 | 0.0430 | 0.963 |
| gears_hcc_formal_v1 | shift_excess_identification_score | 0.333 | 0.545 | 0.000 | 1.000 | 0.8252 | 0.250 |
| gears_hcc_formal_v1 | structure_vs_context_separation_score | 0.428 | 0.402 | 0.374 | 0.429 | 0.0300 | 0.971 |
| shared_mean_baseline | backbone_recovery_score | 0.807 | 0.807 | 0.807 | 0.807 | 0.9640 | 0.965 |
| shared_mean_baseline | shift_excess_identification_score | 0.333 | 0.333 | 0.333 | 0.333 | 1.0000 | 1.000 |
| shared_mean_baseline | structure_vs_context_separation_score | 0.353 | 0.353 | 0.353 | 0.353 | 0.0010 | 1.000 |

## 解释边界

该 null 检验打乱的是 architecture assignment，不是模型训练过程。它支持判断 observed architecture scores 是否高于随机 target-axis assignment，但不能证明模型全局最优，也不能替代外部 cell-line validation。

## baseline gene-label permutation null

target-to-axis permutation 对 `shared_mean_baseline` 基本不敏感，因为该 reference 对所有 targets 使用同一个 backbone vector。因此额外补充 gene-label permutation：随机打乱 prediction matrix 中 gene values 与 gene labels 的对应关系，再按同一 architecture scorer 逻辑重算三指标。

| model_id | null_type | metric | observed | null_mean | null_q025 | null_q975 | empirical_p_ge_observed | observed_percentile |
|---|---|---|---:|---:|---:|---:|---:|---:|
| shared_mean_baseline | gene_label_permutation | backbone_recovery_score | 0.807 | 0.522 | 0.333 | 0.703 | 0.0030 | 0.998 |
| shared_mean_baseline | gene_label_permutation | shift_excess_identification_score | 0.333 | 0.467 | 0.000 | 1.000 | 0.7293 | 0.372 |
| shared_mean_baseline | gene_label_permutation | structure_vs_context_separation_score | 0.353 | 0.431 | 0.373 | 0.499 | 0.9990 | 0.002 |
