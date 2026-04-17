# Genome Biology figure legends v1

## Fig. 1. A truth-anchored HCC benchmark defines the perturbation-fitness recovery object

**a,** Benchmark workflow. Real perturbation transcriptomic shifts are aligned to CRISPR DepMap dependency endpoints to define a frozen phenotype-relevant bridge before model evaluation. **b,** Primary HCC benchmark contexts and endpoint definitions. HCC38 and HCC1143 are evaluated using absolute mean transcriptomic shift and aligned CRISPR dependency. **c,** Joint shift-dependency grid used to define anchor, excess, low-information and middle-band target categories. **d,** HCC38 target-level joint grid. **e,** HCC1143 target-level joint grid. **f,** Grid composition across HCC contexts, including 9 Q1 anchors in HCC38 and 10 Q1 anchors in HCC1143. **g,** CRISPR truth-DepMap bridge strength across HCC38 and HCC1143. **h,** Claim boundary for the benchmark object. The bridge is retained as a structured functional-genomic recovery object, not as fully deconfounded causal proof.

## Fig. 2. Shared anchor tiering separates recurrent bridge support from target proof

**a,** Shared canonical anchor ranking across HCC38 and HCC1143. **b,** Anchor recurrence across the two HCC benchmark contexts. **c,** Cutoff stability of recurrent anchors. PFDN5, PMF1, PRPF6 and ZNF131 retain stable shared-anchor status under the current sensitivity analysis. **d,** Representative contrast between PFDN5 and supporting anchors. **e,** Cutoff-sensitive supporting objects, including ENY2, NPM1, RPS3, RUVBL2 and ZBTB17. **f,** Evidence-tier composition after structural and covariate-aware governance. **g,** Anchor claim matrix. PFDN5 remains primary but qualified, whereas PMF1, PRPF6 and ZNF131 are retained as supporting-only evidence. **h,** Anchor-level claim boundary. Shared anchors support the perturbation-fitness bridge, but no individual anchor is sufficient to prove a fully deconfounded bridge.

## Fig. 3. Model recovery reveals a backbone-separation trade-off

**a,** HCC formal model comparison by backbone recovery score. **b,** Three-dimensional recovery summary including backbone recovery, shift-excess identification and structure-versus-context separation. **c,** Headline comparison between the shared-mean baseline and formal GEARS recipe. The baseline has stronger backbone recovery, whereas GEARS has stronger structure-versus-context separation. **d,** Backbone recovery versus structure-versus-context separation across entrants. **e,** Per-context comparison between the baseline and GEARS. **f,** Shift-excess recovery across model entrants. **g,** Model-family grouping across baseline, GEARS, foundation-model and linear-control entrants. **h,** Model-side claim boundary. GEARS is interpreted as an architecture trade-off diagnosis, not as the HCC primary winner.

## Fig. 4. Recipe and embedding controls do not close the backbone recovery gap

**a,** GEARS backbone sweep. No finite-budget sweep candidate closes the backbone recovery gap to the shared-mean baseline. **b,** Sweep trade-off between backbone recovery and structure-versus-context separation. **c,** Shift-excess performance across GEARS sweep candidates. **d,** Frozen stop-rule schematic for GEARS adjudication. **e,** Linear-control schematic comparing low-rank, scGPT-ridge and Geneformer-ridge controls. **f,** Linear-control ranking. Geneformer-ridge exceeds the other linear controls but does not exceed the shared-mean baseline in backbone recovery. **g,** Coverage audit for embedding-based controls. Target coverage is complete and therefore does not explain the backbone gap. **h,** Interpretation boundary. The observed gap is treated as a task-structure or direction-level mismatch rather than a missing small recipe.

## Fig. 5. Axis-level decomposition provides qualified biological interpretation

**a,** Axis-level explanatory balance comparing dependency R2 with transcriptomic shift R2. **b,** Formal and preliminary axis-call composition. Transcription/chromatin is the only formal positive axis in the current evidence set. **c,** Bootstrap stability of representative axis calls. **d,** Annotation support across representative axes, summarized by enrichment hits, database support and structure support. **e,** Transcription/chromatin focus. This axis is transcriptomic-heavy, with shift R2 = 0.092, dependency R2 near zero and targets ENY2 and TADA3. **f,** Partial support by broader axis family. Annotation-backed axes remain partially supported rather than fully established. **g,** Preliminary and mixed axes ranked by shift-minus-dependency explanatory balance. **h,** Axis claim boundary. Transcription/chromatin is retained as primary but qualified; the manuscript does not claim a fully deconfounded shared explanatory architecture.

## Fig. 6. Covariate, temporal and endpoint analyses define the final benchmark boundary

**a,** Covariate audit overview across barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes. **b,** Covariate-aware anchor tiering. PFDN5 remains primary but qualified; PMF1, PRPF6 and ZNF131 are supporting-only. **c,** Barcode gem group boundary. HCC38 maps to aggrMH001-3 and HCC1143 maps to aggrMH004-6, but individual MH001-MH006 run labels are not resolved. **d,** K562 temporal panel overview for GSE90063 7d and 13d. **e,** Temporal stratification. The 7d panel shows stronger rank alignment, whereas 13d shows larger mean shift. **f,** A0/A1/B supplementary tiering for K562 evidence. The temporal panel supports architecture-form confirmation and bridge-form support, but not content-level replication. **g,** Endpoint hierarchy across HCC38, HCC1143, K562 7d and K562 13d. CRISPR DepMap endpoints retain stronger bridge Spearman than RNAi DEMETER2 endpoints in every context. **h,** Final claim boundary. CRISPR is the primary bridge readout, RNAi is a weaker sensitivity endpoint, K562 is supplementary and discovery remains gated.

## Extended Data Fig. 1. Dataset and endpoint admission

**a,** HCC38 and HCC1143 primary bridge admission using aligned transcriptomic shift versus CRISPR DepMap dependency. **b,** GSE90063 K562 7d and 13d kept-cell counts after single-guide filtering. **c,** DEMETER2 RNAi conversion summary. **d,** Admission status for the global bridge, K562 temporal panel and RNAi expansion candidate. **e,** Endpoint hierarchy separating primary, sensitivity and supplementary evidence. **f,** K562 cell accounting across matrix cells, kept cells and unassigned cells. **g,** Primary HCC endpoint strength. **h,** Boundary showing that K562 and discovery layers are not primary co-pillars.

## Extended Data Fig. 2. Full target-level joint grid

**a,** HCC38 full target-level shift-dependency grid. **b,** HCC1143 full target-level shift-dependency grid. **c,** Grid category counts across HCC38 and HCC1143. **d,** All Q1 anchors observed across the HCC grids. **e,** Transcriptomic-excess targets under the current formal grid. **f,** Dependency-excess targets under the current formal grid. **g,** Target-level evidence-tier composition. **h,** Grid summary table by cell line and category.

## Extended Data Fig. 3. Anchor sensitivity and claim tiering

**a,** Full target-level anchor distribution. **b,** Shared canonical anchors. **c,** Cutoff-sensitive supporting objects. **d,** Control subsampling intervals for the primary bridge metric. **e,** Covariate-aware anchor wording. **f,** Evidence-tier composition. **g,** Anchor downgrade rationale. **h,** Allowed and disallowed anchor claims.

## Extended Data Fig. 4. Full HCC model recovery detail

**a,** Full HCC model backbone recovery ranking. **b,** Per-cell-line backbone recovery. **c,** Per-cell-line shift-excess identification. **d,** Per-cell-line structure-versus-context separation. **e,** Baseline top-20 overlap. **f,** GEARS top-20 overlap. **g,** Foundation-model top-20 overlap. **h,** Null-model top-20 overlap.

## Extended Data Fig. 5. GEARS sweep and stop rule

**a,** GEARS sweep candidate manifest. **b,** Batch status summary for sweep execution. **c,** Sweep candidate backbone recovery scores. **d,** Sweep candidate structure-versus-context separation scores. **e,** Baseline versus sweep-candidate trade-off. **f,** Stop-rule adjudication. **g,** Recipe dimensions varied in the finite sweep. **h,** GEARS training exemption boundary for figure generation.

## Extended Data Fig. 6. Full axis annotation and bootstrap support

**a,** Full axis explanatory balance. **b,** Representative bootstrap axis-call stability. **c,** Axis families in validation summary. **d,** Top axes by enrichment hits. **e,** Enrichment database coverage. **f,** Formal and preliminary axis-call composition. **g,** Top annotation terms. **h,** Axis claim boundary.

## Extended Data Fig. 7. K562 temporal evidence detail

**a,** K562 7d bridge summary. **b,** K562 13d bridge summary. **c,** Temporal stratification of rank bridge and mean shift. **d,** Temporal structure calls. **e,** K562 7d evidence tiers. **f,** K562 13d evidence tiers. **g,** Temporal panel call. **h,** A0/A1/B tier distribution.

## Extended Data Fig. 8. CRISPR versus RNAi endpoint detail

**a,** HCC CRISPR and RNAi truth-endpoint bridge strengths. **b,** K562 CRISPR and RNAi truth-endpoint bridge strengths. **c,** CRISPR-RNAi endpoint agreement. **d,** DEMETER2 conversion summary. **e,** Endpoint hierarchy across HCC and K562 contexts. **f,** RNAi sensitivity boundary. **g,** CRISPR-RNAi bridge gap. **h,** Endpoint claim boundary.

## Extended Data Fig. 9. Covariate audit details and wording boundary

**a,** Covariate audit axes. **b,** Covariate balance by cell line. **c,** Barcode-gem-group design-proxy boundary. **d,** High-imbalance target counts. **e,** Covariate-audit impact on anchor wording. **f,** Covariate status in the final claim matrix. **g,** Allowed wording. **h,** Disallowed wording.

## Extended Data Fig. 10. Reproducibility and claim governance

**a,** Main figure manifest overview. **b,** Supplementary table group overview. **c,** Hash coverage by file type. **d,** Final claim-matrix evidence-tier overview. **e,** Key allowed wording tiers. **f,** Configured rebuild entrypoints. **g,** Explicitly enumerated disallowed wording. **h,** Figure-stage rerun boundary.
