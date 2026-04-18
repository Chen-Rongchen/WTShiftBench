# Genome Biology reference formatting queue v1

## 状态

更新日期：2026-04-18。

本文档是正式 references 列表的整理队列，不是最终排版版本。最终提交前需要按 Genome Biology / BMC reference style 统一格式、排序和编号。

## 必须引用

### Perturbation prediction benchmark / baseline prior art

1. Ahlmann-Eltze C, Huber W, Anders S. Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear baselines. Nature Methods. 2025;22:1657-1661. doi:10.1038/s41592-025-02772-6.

用途：Background prior-art positioning；说明 simple baseline 强不是本文 novelty。

2. Wong DR. Simple controls exceed best deep learning algorithms and reveal foundation model effectiveness for predicting genetic perturbations. Bioinformatics. 2025;41(6):btaf317. doi:10.1093/bioinformatics/btaf317.

用途：Background / Discussion；支撑 simple controls are necessary and often strong。

3. Wei Z, Wang Y, Gao Y, Wang S, et al. Benchmarking algorithms for generalizable single-cell perturbation response prediction. Nature Methods. 2026;23:451-464. doi:10.1038/s41592-025-02980-0.

用途：Discussion；承认大规模 expression-level generalization benchmark，并区分本文的 phenotype-aligned endpoint。

4. Li L, You Y, Fu Y, Liao W, et al. A systematic comparison of single-cell perturbation response prediction models. bioRxiv. 2024.

用途：可选 preprint prior-art。若正文引用，必须标注 preprint status。

### Perturbation data resource / perturbation assay

5. Peidli S, Green TD, Shen C, et al. scPerturb: harmonized single-cell perturbation data. Nature Methods. 2024;21:531-540. doi:10.1038/s41592-023-02144-y.

用途：resource / E-distance 背景；区分本文不是通用 perturbation atlas，而是 dependency-aligned truth object。

6. Dixit A, Parnas O, Li B, et al. Perturb-Seq: dissecting molecular circuits with scalable single-cell RNA profiling of pooled genetic screens. Cell. 2016;167:1853-1866.e17. doi:10.1016/j.cell.2016.11.038.

用途：GSE90063 / Perturb-seq assay 背景。

7. Replogle JM, Saunders RA, Pogson AN, et al. Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq. Cell. 2022;185:2559-2575.e28. doi:10.1016/j.cell.2022.05.013.

用途：Perturb-seq / revision external panel 背景。

### Model background

8. Roohani Y, Huang K, Leskovec J. Predicting transcriptional outcomes of novel multigene perturbations with GEARS. Nature Biotechnology. 2024;42:927-935. doi:10.1038/s41587-023-01905-6.

用途：GEARS 方法背景。

9. Cui H, Wang C, Maan H, et al. scGPT: toward building a foundation model for single-cell multi-omics using generative AI. Nature Methods. 2024;21:1470-1480. doi:10.1038/s41592-024-02201-0.

用途：scGPT entrant 背景。

10. Theodoris CV, Xiao L, Chopra A, et al. Transfer learning enables predictions in network biology. Nature. 2023;618:616-624. doi:10.1038/s41586-023-06139-9.

用途：Geneformer entrant 背景。

11. Hao M, Gong J, Zeng X, et al. Large-scale foundation model on single-cell transcriptomics. Nature Methods. 2024;21:1481-1491. doi:10.1038/s41592-024-02305-7.

用途：scFoundation / foundation-model background；若正文不讨论 scFoundation，可保留在 prior-art discussion。

12. Kedzierska KZ, Crawford L, Amini AP, et al. Zero-shot evaluation reveals limitations of single-cell foundation models. Genome Biology. 2025;26:101. doi:10.1186/s13059-025-03574-x.

用途：Genome Biology 近邻 benchmark；支撑 bounded negative / foundation-model evaluation 在目标期刊中的适配性。

### Dependency endpoints

13. Meyers RM, Bryan JG, McFarland JM, et al. Computational correction of copy-number effect improves specificity of CRISPR-Cas9 essentiality screens in cancer cells. Nature Genetics. 2017;49:1779-1784. doi:10.1038/ng.3984.

用途：CERES / DepMap CRISPR gene effect 背景。

14. Dempster JM, Rossen J, Kazachkova M, et al. Extracting biological insights from the Project Achilles genome-scale CRISPR screens in cancer cell lines. bioRxiv / publication status to verify.

用途：DepMap / Project Achilles 背景。提交前确认是否引用预印本或后续正式版本。

15. McFarland JM, Ho ZV, Kugener G, et al. Improved estimation of cancer dependencies from large-scale RNAi screens using model-based normalization and data integration. Nature Communications. 2018;9:4610. doi:10.1038/s41467-018-06916-5.

用途：DEMETER2 / RNAi endpoint 背景。

## 可选引用

16. Rood JE, Hupalowska A, Regev A. Toward a foundation model of causal cell and tissue biology with a perturbation cell and tissue atlas. Cell. 2024.

用途：foundation model / perturbation atlas broader framing。

17. Szałata A, et al. Transformers in single-cell omics: a review and new perspectives. Nature Methods. 2024.

用途：foundation model review；只有 Background 需要时引用。

## 待人工核对

- 是否正式引用 PerturbArena / systematic comparison preprint。
- Genome Biology 要求的 reference style 是否使用 article title。
