# Stage 2 Truth Bridge Decomposition v1

## 定位

- 本分析把 truth–DepMap bridge 明确拆成两层：`target-level joint-priority grid` 与 `axis-level shared explanatory structure`。
- 第一层使用 `real_shift_mean_abs` 与 `depmap_gene_dependency`；DepMap 侧统一转成“数值越大表示 dependency/liability 越强”的 aligned strength。
- 第二层不把 `Pearson` 当作主结论，而是看哪些 axis 同时对 transcriptomic side 与 DepMap side 提供较强解释。

## 第一层：Target-Level Joint Grid

- 先对两侧分别做 `high / middle / low` 三段分层：`<= 0.25` 记为 `low`，`>= 0.75` 记为 `high`，其余记为 `middle`。
- 只有落在四个角点的 target 才进入 `Q1-Q4`；只要任一侧落在 `middle`，就统一保留在 `middle band`。
- `Q1_anchor`：shift 高、dependency 高。
- `Q2_transcriptomic_excess`：shift 高、dependency 低。
- `Q3_dependency_excess`：shift 低、dependency 高。
- `Q4_low_information`：shift 低、dependency 低。

### 每条 cell line 的 grid 分布

- `HCC1143` / `Q1_anchor`：`n=10`，占比 `20.8%`，median shift=`0.0106`，median dep strength=`0.9804`。
- `HCC1143` / `Q4_low_information`：`n=6`，占比 `12.5%`，median shift=`0.0044`，median dep strength=`0.0081`。
- `HCC1143` / `middle`：`n=32`，占比 `66.7%`，median shift=`0.0054`，median dep strength=`0.0337`。
- `HCC38` / `Q1_anchor`：`n=9`，占比 `19.1%`，median shift=`0.0097`，median dep strength=`0.8555`。
- `HCC38` / `Q4_low_information`：`n=6`，占比 `12.8%`，median shift=`0.0041`，median dep strength=`0.0071`。
- `HCC38` / `middle`：`n=32`，占比 `68.1%`，median shift=`0.0052`，median dep strength=`0.0431`。

### shared canonical anchors（前 10）

- `PRPF6`：Q1 命中 `2/2` 条 cell line，mean shift quantile=`0.990`，mean dep quantile=`0.952`。
- `PMF1`：Q1 命中 `2/2` 条 cell line，mean shift quantile=`0.915`，mean dep quantile=`0.916`。
- `ZNF131`：Q1 命中 `2/2` 条 cell line，mean shift quantile=`0.905`，mean dep quantile=`0.853`。
- `RUVBL2`：Q1 命中 `2/2` 条 cell line，mean shift quantile=`0.862`，mean dep quantile=`0.942`。
- `ZBTB17`：Q1 命中 `2/2` 条 cell line，mean shift quantile=`0.841`，mean dep quantile=`0.800`。
- `RPS3`：Q1 命中 `2/2` 条 cell line，mean shift quantile=`0.832`，mean dep quantile=`0.979`。
- `PFDN5`：Q1 命中 `2/2` 条 cell line，mean shift quantile=`0.832`，mean dep quantile=`0.884`。

### anchor stability（跨 cutoff）

- `PFDN5`：shared anchor stability=`1.00`，调用次数 `3/3`。
- `PMF1`：shared anchor stability=`1.00`，调用次数 `3/3`。
- `PRPF6`：shared anchor stability=`1.00`，调用次数 `3/3`。
- `ZNF131`：shared anchor stability=`1.00`，调用次数 `3/3`。

## 第二层：Axis-Level Shared Explanatory Structure

- 这里的 `R²` 不是教科书式全局方差分解，而是对每个 axis 做 one-vs-rest explanatory strength 近似。
- `shared_backbone_axis` 的判定要求两侧 `R²` 均不低于 `0.050`，且 axis 对两侧均呈正向 lift。
- 只有 `n_targets >= 2` 的 axis 才进入 formal axis call；更小的 axis 只记为 `preliminary`。
- `transcriptomic_heavy_axis` / `dependency_heavy_axis` 用两侧 `R²` 差值超过 `0.030` 来定义偏斜结构。

### shared backbone axes

- 当前没有 axis 满足 shared backbone axis 条件。

### transcriptomic-heavy axes

- `transcription / chromatin`：shift R²=`0.092` > dep R²=`0.000`，targets=`ENY2; TADA3`。

### dependency-heavy axes

- 当前没有 axis 被判为 dependency-heavy。

### preliminary axes

- `proteostasis / chaperone`：当前仅有 `1` 个 target，先记为 `preliminary_dependency_heavy_axis`，shift R²=`0.035`，dep R²=`0.087`。
- `ribosomal / translation`：当前仅有 `1` 个 target，先记为 `preliminary_dependency_heavy_axis`，shift R²=`0.024`，dep R²=`0.116`。
- `RNA processing / transcription`：当前仅有 `1` 个 target，先记为 `preliminary_dependency_heavy_axis`，shift R²=`0.005`，dep R²=`0.115`。
- `ribosome biogenesis / nucleolar`：当前仅有 `1` 个 target，先记为 `preliminary_mixed_or_low_signal_axis`，shift R²=`0.049`，dep R²=`0.039`。
- `nuclear receptor / co-activator`：当前仅有 `1` 个 target，先记为 `preliminary_mixed_or_low_signal_axis`，shift R²=`0.018`，dep R²=`0.007`。
- `cytoskeleton / cell motility`：当前仅有 `1` 个 target，先记为 `preliminary_mixed_or_low_signal_axis`，shift R²=`0.017`，dep R²=`0.004`。
- `ER stress / UPR`：当前仅有 `1` 个 target，先记为 `preliminary_mixed_or_low_signal_axis`，shift R²=`0.016`，dep R²=`0.009`。
- `NF-κB / copper signaling`：当前仅有 `1` 个 target，先记为 `preliminary_mixed_or_low_signal_axis`，shift R²=`0.015`，dep R²=`0.005`。
- `metabolism / transcription`：当前仅有 `1` 个 target，先记为 `preliminary_mixed_or_low_signal_axis`，shift R²=`0.015`，dep R²=`0.008`。
- `peroxisome / metabolism`：当前仅有 `1` 个 target，先记为 `preliminary_mixed_or_low_signal_axis`，shift R²=`0.014`，dep R²=`0.009`。

### axis bootstrap stability

- `ER stress / UPR`：dominant bootstrap call=`preliminary_mixed_or_low_signal_axis`，稳定度=`1.00`。
- `JAK-STAT signaling`：dominant bootstrap call=`preliminary_mixed_or_low_signal_axis`，稳定度=`1.00`。
- `NF-κB / MAPK signaling`：dominant bootstrap call=`preliminary_mixed_or_low_signal_axis`，稳定度=`1.00`。
- `NF-κB / copper signaling`：dominant bootstrap call=`preliminary_mixed_or_low_signal_axis`，稳定度=`1.00`。
- `RNA processing / spliceosome`：dominant bootstrap call=`preliminary_shared_signal_axis`，稳定度=`1.00`。
- `RNA processing / transcription`：dominant bootstrap call=`preliminary_dependency_heavy_axis`，稳定度=`1.00`。
- `TGF-beta / BMP signaling`：dominant bootstrap call=`mixed_or_low_signal_axis`，稳定度=`1.00`。
- `cell cycle / replication`：dominant bootstrap call=`preliminary_mixed_or_low_signal_axis`，稳定度=`1.00`。
- `cytoskeleton / cell motility`：dominant bootstrap call=`preliminary_mixed_or_low_signal_axis`，稳定度=`1.00`。
- `growth / proliferation`：dominant bootstrap call=`preliminary_mixed_or_low_signal_axis`，稳定度=`1.00`。

## 证据分层摘要

- `primary_evidence`：`5` 个对象。
- `supporting_but_sensitive/supporting_but_unstable`：`5` 个对象。
- `preliminary_only`：`21` 个对象。

## 解释边界

- 这里的结果支持 `target` 或 `axis` 上 transcriptomic impact 与 cellular dependency 的共定位，不构成因果证明。
- `Q2/Q3` 在这里被保留为 deviation structure，而不是被当作噪音丢弃。
- 若后续需要 formal 写作，应优先引用 shared anchors 与 shared backbone axes，而不是把单个整体相关系数当作主叙事。
