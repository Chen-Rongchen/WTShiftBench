# Stage 2 Anchor Covariate Screen

## 定位

这份摘要只回答一个问题：

**当前 stable shared anchors 在已有五条 covariate 轴与 `barcode_gem_group` design-proxy 边界下，哪些还能保留，哪些必须降级？**

当前基于五条已落盘的 covariate 轴：

- `barcode_gem_group`
- `num_umis_quantile_bin`
- `num_umis_over_threshold_bin`
- `transcriptome_total_signal_quantile_bin`
- `transcriptome_detected_genes_quantile_bin`

它不代表 full deconfounding 已完成。

## 当前 stable shared anchors

结构稳定层面，当前仍保留四个 `stable_shared_anchor`：

- `PFDN5`
- `PMF1`
- `PRPF6`
- `ZNF131`

## 五条 covariate 轴下的当前结果

### PFDN5

- `num_umis`
  - `HCC38 = 0.1578`
  - `HCC1143 = 0.1202`
- `threshold_ratio`
  - `HCC38 = 0.1471`
  - `HCC1143 = 0.1901`

当前判断：

- 风险相对较轻
- 但仍不能写成 fully deconfounded
- 当前更适合保留为 `retain_with_caution`

### PMF1

- `num_umis`
  - `HCC38 = 0.4914`
  - `HCC1143 = 0.1714`
- `threshold_ratio`
  - `HCC38 = 0.4809`
  - `HCC1143 = 0.2133`

当前判断：

- `HCC38` 上暴露出明显 covariate imbalance
- 不能继续作为 strongest wording 的主支柱
- 当前应降级为 `supporting_but_covariate_exposed`

### PRPF6

- `num_umis`
  - `HCC38 = 0.3078`
  - `HCC1143 = 0.1923`
- `threshold_ratio`
  - `HCC38 = 0.1974`
  - `HCC1143 = 0.3438`

当前判断：

- 多条 covariate 轴下都存在不可忽略风险
- 当前应降级为 `supporting_but_covariate_exposed`

### ZNF131

- `num_umis`
  - `HCC38 = 0.3145`
  - `HCC1143 = 0.3976`
- `threshold_ratio`
  - `HCC38 = 0.2321`
  - `HCC1143 = 0.3549`

当前判断：

- 两个 cell line 都持续暴露较强 covariate imbalance
- 当前不宜继续作为 strongest wording
- 当前应降级为 `supporting_but_covariate_exposed`

## 当前可直接用于写作的结论

当前最稳的写法是：

- stable shared anchors 仍然存在
- 但它们代表的是 `structurally stable anchors`
- 而不是 `fully deconfounded anchors`

更具体地说：

- `PFDN5` 可暂时保留为相对更轻风险的 anchor
- `PMF1`、`PRPF6`、`ZNF131` 当前应明确保留方法学谨慎，不再承担 strongest wording
- `barcode_gem_group` 可作为更接近实验设计 aggregation 结构的 design-proxy axis 写入边界，但不能写成单个 `MH00x` 已确认的 run-level covariate

## 对主线的含义

这不会直接推翻 `bridge exists`。

但它会推翻一种更强写法：

- “bridge 已被少数最稳、最干净的 anchors 明确钉死”

当前更稳的写法应改为：

- bridge 由分层化结构证据支撑
- 其中少数 anchors 在结构上稳定
- 但 anchor-level strongest wording 仍受 covariate audit 边界约束
