# Prior-art literature scan v1

## 状态

扫描日期：2026-04-17。

用途：支撑 Genome Biology 投稿前的 prior-art positioning。本文档不是 reference list 终稿，而是用于确认 manuscript 不能遗漏的相邻工作线。

## 结论

当前 manuscript 必须主动承认一条已有文献线：在 expression-level perturbation prediction 中，简单 baseline 可以匹配或超过 deep learning / foundation model entrants。本文的差异不能写成“首次发现 baseline 强”，而应写成：

- 评估对象从 expression reconstruction 改为 phenotype-relevant fitness bridge。
- recovery 被分解为 backbone recovery、shift-excess identification、structure-vs-context separation。
- 输出是 architecture-aware trade-off diagnosis，不是单一 leaderboard 或 unidirectional model failure claim。

## 关键 prior art

| 文献 | 类型 | 任务 / endpoint | 模型与 baseline | 与本文关系 |
|---|---|---|---|---|
| Ahlmann-Eltze, Huber and Anders, Nature Methods 2025 | perturbation prediction benchmark | single / double perturbation transcriptome prediction | GEARS、CPA、scGPT、scFoundation、Geneformer、UCE、scBERT 与 simple baselines / linear models | 必须引用。该文明确显示 deep-learning perturbation prediction 尚未稳定超过 simple linear / mean baselines。本文不能把 baseline 强作为 novelty。 |
| Wong, Bioinformatics 2025 | perturbation prediction benchmark / control study | post-perturbation RNA-seq prediction | simple controls vs deep learning / foundation-style approaches | 必须引用或至少纳入 prior-art scan。支撑“simple controls are necessary and often strong”的已有背景。 |
| Wei, Wang, Gao et al., Nature Methods 2026 | generalizable single-cell perturbation response benchmark | 29 datasets、27 methods、6 metrics，强调跨 context / perturbation generalization | 多方法 benchmark，覆盖 emerging foundation models | 必须引用或讨论。该文规模远大于本文；本文差异在 phenotype-aligned dependency endpoint 与 architecture-aware adjudication，不在 expression prediction scale。 |
| Peidli et al., scPerturb, Nature Methods 2024 | perturbation data resource | 44 harmonized single-cell perturbation-response datasets，含 E-statistics / E-distance | resource 与 effect-size quantification 工具 | 必须引用。本文使用 E-distance 作为补充审计时，需要说明与 scPerturb 的关系：本文不是构建通用 perturbation atlas，而是构建 phenotype-aligned truth object。 |
| Kedzierska / Crawford / Amini / Lu et al., Genome Biology 2025 | single-cell foundation model benchmark | zero-shot single-cell foundation model evaluation | scGPT、Geneformer 与 simpler methods | 建议引用。它是 GB 近年相关 benchmark，说明 GB 接受严谨 negative / bounded foundation-model evaluation。 |
| Li / You / Tian et al., 2024 preprint; PerturbArena site | systematic perturbation prediction benchmark | 12 models + 3 baselines across 25 datasets; 24 metrics; unseen perturbation / combinatorial / cell-state transfer | 多模型、多 metric expression-level benchmark | 可引用为 preprint 或在 Discussion 提及。本文差异同样在 dependency endpoint 与 architecture-aware recovery object。 |
| Cui et al., scGPT, Nature Methods 2024 | model paper | single-cell multi-omics foundation model，含 perturbation claims | scGPT | 模型背景引用。本文只评估其在 frozen fitness-bridge architecture 下的 recovery，不评价其全部用途。 |
| Theodoris et al., Geneformer, Nature 2023 | model paper | transfer learning for network biology | Geneformer | 模型背景引用。本文将其作为 entrant / embedding-control family，claim 不外推到 Geneformer 全部任务。 |
| Hao et al., scFoundation, Nature Methods 2024 | model paper | large-scale single-cell foundation model | scFoundation | 若正文讨论未纳入 entrant / future entrant，需要作为背景或 revision entrant 候选处理。 |
| Replogle et al., Cell 2022 | genome-scale Perturb-seq resource | CRISPRi Perturb-seq genotype-phenotype landscapes | not primarily a model benchmark | 外部 expansion / revision 弹药相关。第一版不新增正式 Replogle analysis，但 admission contract 需保持 ready。 |

## 建议写入 manuscript 的 positioning

建议放在 Introduction 第二段之后：

Prior perturbation-prediction benchmarks have already shown that expression-level recovery by deep learning or foundation-model entrants can be matched or exceeded by simple baselines. These studies are essential context for our model-side results, but they ask a different question. They evaluate transcriptome prediction accuracy, whereas the present benchmark first freezes a phenotype-relevant truth object by aligning perturbation transcriptomic shifts to cancer dependency endpoints. Model recovery is then decomposed into backbone recovery, shift-excess identification and structure-versus-context separation. The resulting claim is therefore not that complex models fail in a unidirectional sense, but that current entrants occupy different parts of a frozen fitness-bridge architecture, with a strong shared-backbone reference and a separation-biased GEARS profile.

## References to verify during final reference formatting

- Ahlmann-Eltze C, Huber W, Anders S. Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear baselines. Nature Methods. 2025.
- Wong DR, Hill AS, Moccia R. Simple controls exceed best deep learning algorithms and reveal foundation model effectiveness for predicting genetic perturbations. Bioinformatics. 2025.
- Wei Z, Wang Y, Gao Y, Wang S, et al. Benchmarking algorithms for generalizable single-cell perturbation response prediction. Nature Methods. 2026.
- Peidli S, Green TD, Shen C, et al. scPerturb: harmonized single-cell perturbation data. Nature Methods. 2024.
- Kedzierska KZ, Crawford L, Amini AP, Lu AX, et al. Zero-shot evaluation reveals limitations of single-cell foundation models. Genome Biology. 2025.
- Li L, You Y, Fu Y, Liao W, et al. A Systematic Comparison of Single-Cell Perturbation Response Prediction Models. bioRxiv. 2024.
- Cui H, Wang C, Maan H, et al. scGPT: toward building a foundation model for single-cell multi-omics using generative AI. Nature Methods. 2024.
- Theodoris CV, Xiao L, Chopra A, et al. Transfer learning enables predictions in network biology. Nature. 2023.
- Hao M, Gong J, Zeng X, et al. Large-scale foundation model on single-cell transcriptomics. Nature Methods. 2024.
- Replogle JM, Saunders RA, Pogson AN, et al. Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq. Cell. 2022.

## 未完成事项

- 最终 reference style 仍需按 Genome Biology 格式整理。
- 若正式引用 preprint，需要在 manuscript 中标注其 preprint status。
- 若最终正文不提 scFoundation，需要至少在 discussion / limitations 或 reviewer Q&A 中说明未纳入第一版 entrant expansion 的边界。
