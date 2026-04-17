# Baseline 与投稿策略说明 v1

## 当前判断

当前项目最适合作为 Genome Biology 主投。Science Advances 可以作为冲刺目标，但需要更强的跨领域科学意义包装；Advanced Science 不建议作为优先目标，除非文章改写成更偏 biomedical innovation / translational life-science 的叙事。

## 为什么 baseline 强不是负面结果

正式 HCC truth-DepMap benchmark 中，shared-mean baseline 的 backbone recovery 为 0.807，高于 GEARS formal 的 0.660、Geneformer-ridge 的 0.627、Geneformer 的 0.533、scGPT-ridge 的 0.467 和 scGPT 的 0.447。

这不应写成“复杂模型失败”或“benchmark 失效”，而应写成：

> 当前 HCC perturbation-fitness truth object 的主成分是 shared canonical backbone；简单 baseline 强，说明 benchmark object 本身具有稳定的跨 context backbone。复杂模型的优势主要出现在 separation、deviation 或 shift-excess 维度，而不是 primary backbone recovery。

## 支撑这个解释的现有证据

1. Truth bridge 本身稳定。
   - HCC38 `real_shift_mean_abs` 与 DepMap dependency 的 control-subsample Spearman 均值为 0.725，95% 区间约为 0.706-0.741。
   - HCC1143 对应均值为 0.779，95% 区间约为 0.765-0.793。
   - 说明 baseline 捕获的不是随机噪声，而是强、稳定的 primary bridge backbone。

2. GEARS 有局部优势但不是 primary winner。
   - GEARS formal backbone recovery 为 0.660，低于 baseline。
   - GEARS structure-versus-context separation 为 0.428，高于 baseline 的 0.353。
   - 因此 GEARS 适合写成 architecture trade-off diagnosis。

3. Geneformer 有局部信号但未超过 baseline。
   - Geneformer-ridge backbone recovery 为 0.627，是非 GEARS、非 baseline 里相对较强的一组，但仍低于 baseline。
   - 原始 Geneformer shift-excess 为 0.750，高于 baseline 的 0.333；structure separation 为 0.401，高于 baseline 的 0.353。
   - 因此 Geneformer 可以写成 partial deviation/separation signal，而不是 backbone winner。

4. scGPT 在正式 HCC benchmark 中较弱。
   - scGPT backbone recovery 为 0.447，低于 null model 的 0.500。
   - scGPT-ridge backbone recovery 为 0.467，也低于 null model。
   - 因此 scGPT 不应被写成 positive entrant。

5. Embedding controls 覆盖率不是问题。
   - Geneformer-ridge、scGPT-ridge 和 low-rank controls 在 HCC38/HCC1143 均有 1.0 target coverage。
   - 这些 controls 仍未超过 baseline，说明 backbone gap 不能简单归因于 target mapping 或 coverage failure。

6. GEARS finite sweep 没有闭合 backbone gap。
   - 最好 sweep backbone recovery 为 0.643，仍低于 baseline 的 0.807。
   - 部分 sweep candidate 提高 shift-excess 或 separation，但没有转化为 backbone superiority。

## 建议写入 manuscript 的核心句式

推荐写法：

> The strength of the shared-mean baseline is informative rather than artifactual: it indicates that the dominant component of the HCC truth object is a cross-context canonical backbone. Model entrants add signal in separation or shift-excess dimensions, but do not displace the baseline for primary backbone recovery.

避免写法：

- foundation models failed completely。
- GEARS is worse。
- baseline proves the benchmark is trivial。
- model recovery has been demonstrated。

## Science Advances 判断

Science Advances 是 AAAS 的多学科开放获取期刊，强调对生命科学、物理科学、环境、工程、数学、计算和社会科学等领域有重要贡献的研究。它理论上可以投，因为本项目有 computational biology、functional genomics、single-cell perturbation 和 benchmark/resource 属性。

但当前稿件直接投 Science Advances 的风险较高：

- 文章主要贡献是领域内 benchmark/resource，而不是跨学科 broad breakthrough。
- 核心结论是 claim-bounded 和 negative/diagnostic，不是显著新的生物机制或新模型。
- 需要更强地强调“foundation perturbation models 的真实生物有效性评估范式”对整个 AI-for-biology 领域的意义。

若投 Science Advances，需要改写为：

> A generalizable truth-anchored framework showing that current AI perturbation models recover different components of phenotype-relevant biology, with simple baselines remaining strong for shared backbone recovery.

建议：可作为冲刺备选，但不作为当前主投。

## Advanced Science 判断

Advanced Science 是 Wiley 的 interdisciplinary premium open-access journal，覆盖 materials science、physics、chemistry、medical and life sciences、engineering 等。生命科学文章可以投，但该刊常见强项更偏 high-impact discovery、biomedical innovation、materials/engineering-linked biology 或 translational application。

当前稿件不优先建议投 Advanced Science：

- 文章不是治疗、材料、生物医学技术或机制突破。
- benchmark/resource 叙事更适合 Genome Biology、PLOS Computational Biology 或 Nature Computational Science。
- 若改投 Advanced Science，需要把叙事转向 cancer functional-genomics platform / biomedical AI validation framework，但这会弱化当前最稳的 genomics benchmark 逻辑。

建议：不作为第一或第二选择。

## 推荐投稿顺序

1. Genome Biology：主投。
2. Science Advances：可冲刺，但需大幅提升 broad-impact framing。
3. Nature Computational Science：若想走 AI/model evaluation general framework，可考虑 presubmission。
4. PLOS Computational Biology：稳妥 computational benchmark 备选。
5. npj Systems Biology and Applications：系统生物学和模型边界备选。
6. Advanced Science：不优先，除非改写成 biomedical innovation 叙事。
