# Stage 2 HCC Entrant Smoke 裁决摘要

## 结论

当前已经完成：

- `GEARS` 作为 `HCC primary mainline` strongest formal entrant 的 HCC38 / HCC1143 真实 raw output
- `Geneformer` 作为新增 entrant 的 HCC38 / HCC1143 真实 raw output
- `scGPT` 作为新增 entrant 的 HCC38 / HCC1143 真实 raw output
- `stage2_truth_aligned_log_shift` export
- contract validation
- 真实 HCC entrant smoke adjudication
- A/B/C 三层辅助裁决层

当前不能把结果写成“GEARS 已在 HCC primary mainline 上整体压过 shared_mean_baseline”。

更准确的判断是：

- `GEARS` 已经真实接入并完成正式 smoke
- 它在 `structure vs context separation` 上稳定优于 `shared_mean_baseline`
- 它在 `HCC1143` 上对 `shift-excess` 的恢复优于 `shared_mean_baseline`
- 但它在两个 cell line 上的 `backbone recovery` 都仍落后于 `shared_mean_baseline`
- 辅助数值层上，`cosine / L2 / top-20 overlap` 也没有形成对 `shared_mean_baseline` 的整体优势

因此，当前更稳的结论是：

`GEARS` 已证明自己不是只会 shared mean 的纯平均器，它带来了更强的结构-上下文分离信号；但截至本轮正式 HCC smoke，还不足以支持“GEARS 已成为 backbone recovery 更强的主胜者”。

同时，foundation-model entrant family 里已经可以分出强弱：`Geneformer` 已完成正式接入，且当前整体强于 `scGPT`；但它仍没有在 backbone recovery 上接近 `shared_mean_baseline`，因此也还不是新的主线胜者候选。`scGPT` 则更像一个已经被排除“只因未接入而未知”的弱 entrant。

## 主裁决结果

### HCC38

- `shared_mean_baseline`
  - backbone recovery = `0.773`
  - shift-excess identification = `0.500`
  - structure-vs-context separation = `0.357`
- `GEARS`
  - backbone recovery = `0.600`
  - shift-excess identification = `0.167`
  - structure-vs-context separation = `0.426`

判断：

- `GEARS` 在 HCC38 上赢的是 `structure vs context separation`
- `shared_mean_baseline` 在 HCC38 上仍明显更强于 `backbone recovery`
- `shared_mean_baseline` 在 HCC38 上也更强于 `shift-excess identification`

### HCC1143

- `shared_mean_baseline`
  - backbone recovery = `0.840`
  - shift-excess identification = `0.167`
  - structure-vs-context separation = `0.348`
- `GEARS`
  - backbone recovery = `0.720`
  - shift-excess identification = `0.500`
  - structure-vs-context separation = `0.431`

判断：

- `GEARS` 在 HCC1143 上赢的是 `shift-excess identification`
- `GEARS` 在 HCC1143 上也赢 `structure vs context separation`
- `shared_mean_baseline` 在 HCC1143 上仍更强于 `backbone recovery`

### 跨细胞系均值

- `shared_mean_baseline`
  - backbone recovery = `0.807`
  - shift-excess identification = `0.333`
  - structure-vs-context separation = `0.353`
- `GEARS`
  - backbone recovery = `0.660`
  - shift-excess identification = `0.333`
  - structure-vs-context separation = `0.428`
- `Geneformer`
  - backbone recovery = `0.533`
  - shift-excess identification = `0.750`
  - structure-vs-context separation = `0.401`
- `scGPT`
  - backbone recovery = `0.447`
  - shift-excess identification = `0.333`
  - structure-vs-context separation = `0.295`

跨细胞系主判断：

- `backbone recovery`：`shared_mean_baseline` 更强
- `shift-excess identification`：两者均值持平，但具体由 `GEARS@HCC1143` 拉起
- `structure vs context separation`：`GEARS` 更强
- `Geneformer`：当前是 foundation-model entrants 中更强的一个，尤其在 shift-excess 上强于 `scGPT`
- `scGPT`：三项都没有形成最优位置，整体弱于 `GEARS`，且 backbone 明显弱于 baseline

## 辅助裁决层

本轮固定使用：

- `cosine similarity`
- `L2 distance`
- `top-20 overlap`

它们只用于解释，不替代 architecture-level 主裁决。

### 全 targets 跨细胞系均值

- `shared_mean_baseline`
  - cosine = `0.158`
  - L2 = `0.488`
  - top-20 overlap = `0.570`
- `GEARS`
  - cosine = `0.132`
  - L2 = `0.627`
  - top-20 overlap = `0.509`
- `Geneformer`
  - cosine = `0.131`
  - L2 = `0.432`
  - top-20 overlap = `0.565`
- `scGPT`
  - cosine = `0.121`
  - L2 = `0.492`
  - top-20 overlap = `0.561`

解释：

- 从整体数值贴近度看，`shared_mean_baseline` 仍更像 truth
- `GEARS` 的优势不在“整体更接近 truth”，而在“某些结构层面更能把 expected axis 和 off-axis 分开”
- `Geneformer` 的整体贴近度优于 `GEARS`，且 shift-excess 信号比 `scGPT` 更强，但 backbone 仍显著弱于 baseline
- `scGPT` 的整体贴近度没有崩坏，但这没有转化成更强的 backbone / separation 主裁决

## A/B/C 三层解释

本轮固定映射为：

- `A = canonical_backbone`
- `B = shift_excess`
- `C = context_deviation`

当前最稳的解释是：

- A 层没有被 `GEARS` 稳定拿下，所以 backbone recovery 仍未关闭
- B 层在 `HCC1143` 上出现 `GEARS` 优势，但 `HCC38` 未复现，说明 shift-excess 识别仍有 context sensitivity
- C 层对应的 structure/context 分离，是本轮 `GEARS` 最明确的正向信号
- `Geneformer` 在 A 层的失败模式介于 `mixed / direction`，说明它比 `scGPT` 更接近可用 entrant，但 backbone 仍没有真正学到位
- `scGPT` 在 A 层的失败模式更接近 `direction`，说明它不是单纯幅度缩小，而是 canonical backbone 的方向恢复本身偏弱

## scGPT / Geneformer 处置

本轮状态已经变化：

- `scGPT` 已并入 HCC 主线运行
- `Geneformer` 已并入 HCC 主线运行

`Geneformer` 当前最稳的处置是：

- 技术状态：已完成正式接入
- 比较状态：已进入同一份 `model_comparison.tsv`
- 结果状态：当前强于 `scGPT`，但仍不构成 stronger entrant，也不改变现有主结论

`scGPT` 当前最稳的处置是：

- 技术状态：已完成正式接入
- 比较状态：已进入同一份 `model_comparison.tsv`
- 结果状态：当前不构成 stronger entrant，也不改变现有主结论

## 产物位置

- 主报告：`reports/real_hcc_smoke/smoke_report.md`
- 汇总表：`reports/real_hcc_smoke/smoke_summary.tsv`
- 模型比较：`reports/real_hcc_smoke/model_comparison.tsv`
- `GEARS` 细节：
  - `reports/real_hcc_smoke/details/gears_hcc_formal_v1/HCC38/`
  - `reports/real_hcc_smoke/details/gears_hcc_formal_v1/HCC1143/`
- `scGPT` 细节：
  - `reports/real_hcc_smoke/details/scgpt_hcc_formal_v1/HCC38/`
  - `reports/real_hcc_smoke/details/scgpt_hcc_formal_v1/HCC1143/`
- `Geneformer` 细节：
  - `reports/real_hcc_smoke/details/geneformer_hcc_formal_v1/HCC38/`
  - `reports/real_hcc_smoke/details/geneformer_hcc_formal_v1/HCC1143/`
