# Genome Biology figure legends v1

## Fig. 1. A truth-anchored benchmark defines a pre-specified perturbation-fitness recovery object in HCC38 and HCC1143

**a,** Study workflow and frozen recovery object. A truth-first workflow (perturbation truth → DepMap CRISPR dependency endpoint → frozen bridge object → model recovery adjudication → qualified claim boundary) defines the target-level recovery object before entrant scoring. The adjudicated entrant set includes the shared-mean baseline, GEARS, foundation-model entrants, linear controls, null references and rebuttal checks. The object is unpacked below into three pre-specified components: the truth signal (absolute mean perturbation shift), the alignment endpoint (CRISPR dependency) and the category rule (pre-specified 25/75 joint grid). **b,** Pre-specified 25/75 category rule. Targets were classified on a pre-specified joint grid using the 25th and 75th quantiles of transcriptomic perturbation shift and CRISPR dependency, with corner-defined categories and a retained middle band. **c,** HCC38 target-level joint grid, with n, aligned Spearman rho and Q1 anchor count shown in the panel. **d,** HCC1143 target-level joint grid, with n, aligned Spearman rho and Q1 anchor count shown in the panel. **e,** Grid composition across the two primary contexts. Q2 transcriptomic-excess and Q3 dependency-excess targets were not observed in either primary context and are retained as zero-count categories in the composition summary. **f,** Bridge strength summary. Visual elements are: (i) point, the observed aligned Spearman rho between absolute mean perturbation shift and CRISPR DepMap dependency on target-level pairs, with n = 47 (HCC38) and n = 48 (HCC1143); (ii) vertical error bar, the Fisher z-transform 95% confidence interval of the point estimate, computed in closed form from n and the observed rho and describing sampling uncertainty of the point itself, not a bootstrap; (iii) gray band, the 95% envelope of an empirical permutation null obtained by shuffling the target-to-DepMap pairing within each context 1000 times under a fixed seed, describing the range of aligned Spearman rho expected under the rho = 0 null hypothesis of no target-level alignment. The point estimate, the point-level CI and the null envelope are distinct quantities and are plotted together only to show that the observed bridge strength lies well outside the permutation null envelope in both primary contexts (empirical two-sided p = 0.001 for each context), consistent with a structured perturbation-fitness bridge rather than random association. The bridge is interpreted as a structured target-level recovery object with pre-specified categories, not as fully deconfounded causal proof.

## Fig. 2. Shared anchor tiering separates recurrent bridge support from target proof

**a,** Shared canonical anchor ranking across HCC38 and HCC1143. **b,** Anchor recurrence across the two HCC38/HCC1143 breast-cancer contexts. **c,** Cutoff stability of recurrent anchors. PFDN5, PMF1, PRPF6 and ZNF131 retain stable shared-anchor status under the current sensitivity analysis. **d,** Representative contrast between PFDN5 and supporting anchors. **e,** Cutoff-sensitive supporting objects, including ENY2, NPM1, RPS3, RUVBL2 and ZBTB17. **f,** Evidence-tier composition after structural and covariate-aware governance. **g,** Anchor claim matrix. PFDN5 remains primary but qualified, whereas PMF1, PRPF6 and ZNF131 are retained as supporting-only evidence. **h,** Anchor-level claim boundary. Shared anchors support the perturbation-fitness bridge, but no individual anchor is sufficient to prove a fully deconfounded bridge.

## Fig. 3. Model recovery is metric-dependent and reveals a backbone-separation trade-off

**a,** Three adjudication metrics (backbone recovery, shift-excess identification, structure-versus-context separation) separate recovery modes across the shared-mean baseline, the formal GEARS recipe, foundation-model entrants (Geneformer, scGPT), linear controls and the null reference. **b,** Baseline leads backbone recovery, whereas GEARS leads context separation; paired-dot contrast limited to the two formal entrants on the two headline metrics. **c,** Entrants occupy a backbone-separation trade-off space; baseline and GEARS are highlighted, Geneformer and scGPT are labelled, and GEARS sweep variants, linear controls and the null reference appear as a family-grouped supporting cloud. A lightly shaded upper-right reference region is included as an illustrative visual aid indicating the empty high-backbone/high-separation corner; the region is not a decision threshold and is not used for scoring or adjudication. **d,** The same qualitative ordering is preserved in HCC38 and HCC1143 under per-context paired-dot comparison between baseline and GEARS on backbone recovery. Prespecified GEARS sweep variants and the stop-rule adjudication are reported in Extended Data Fig. 5; shared_mean_baseline remains the backbone primary reference, whereas GEARS is retained as an architecture trade-off diagnosis rather than an overall HCC38/HCC1143 primary winner.

## Fig. 4. Recipe and embedding controls do not close the backbone recovery gap

**a,** GEARS backbone sweep. No finite-budget sweep candidate closes the backbone recovery gap to the shared-mean baseline. **b,** Sweep trade-off between backbone recovery and structure-versus-context separation. **c,** Shift-excess performance across GEARS sweep candidates. **d,** Frozen stop-rule schematic for GEARS adjudication. **e,** Linear-control schematic comparing low-rank, scGPT-ridge and Geneformer-ridge controls. **f,** Linear-control ranking. Geneformer-ridge exceeds the other linear controls but does not exceed the shared-mean baseline in backbone recovery. **g,** Coverage audit for embedding-based controls. Target coverage is complete and therefore does not explain the backbone gap. **h,** Interpretation boundary. The observed gap is treated as a task-structure or direction-level mismatch rather than a missing small recipe.

## Fig. 5. Covariate, temporal and endpoint analyses define the final benchmark boundary

**a,** Boundary architecture. Three independent layers jointly define the final claim scope. **b,** Covariate boundary. Mean Total Variation Distance across five covariate axes in HCC38 and HCC1143. **c,** Temporal and endpoint hierarchy boundary. K562 7d/13d temporal comparison is shown alongside CRISPR versus RNAi endpoint hierarchy across four contexts. **d,** Final claim boundary. CRISPR DepMap dependency is the primary readout; K562 temporal panel is supplementary evidence; RNAi DEMETER2 is a weaker cross-platform sensitivity endpoint; fully deconfounded architecture, content-level replication, RNAi primary readout and mechanism-level recovery remain unclaimed.

## Extended Data Fig. 1. Dataset and endpoint admission

**a,** HCC38 and HCC1143 breast-cancer primary bridge admission using aligned transcriptomic shift versus CRISPR DepMap dependency. **b,** GSE90063 K562 7d and 13d kept-cell counts after single-guide filtering. **c,** DEMETER2 RNAi conversion summary. **d,** Admission status for the global bridge, K562 temporal panel and RNAi expansion candidate. **e,** Endpoint hierarchy separating primary, sensitivity and supplementary evidence. **f,** K562 cell accounting across matrix cells, kept cells and unassigned cells. **g,** Primary HCC38/HCC1143 endpoint strength. **h,** Boundary showing that K562 and discovery layers are not primary co-pillars.

## Extended Data Fig. 2. Full target-level joint grid

**a,** HCC38 full target-level shift-dependency grid. **b,** HCC1143 full target-level shift-dependency grid. **c,** Grid category counts across HCC38 and HCC1143. **d,** All Q1 anchors observed across the HCC38/HCC1143 grids. **e,** Transcriptomic-excess targets under the current formal grid. **f,** Dependency-excess targets under the current formal grid. **g,** Target-level evidence-tier composition. **h,** Grid summary table by cell line and category.

## Extended Data Fig. 3. Anchor sensitivity and claim tiering

**a,** Full target-level anchor distribution. **b,** Shared canonical anchors. **c,** Cutoff-sensitive supporting objects. **d,** Control subsampling intervals for the primary bridge metric. **e,** Covariate-aware anchor wording. **f,** Evidence-tier composition. **g,** Anchor downgrade rationale. **h,** Allowed and disallowed anchor claims.

## Extended Data Fig. 4. Full HCC38/HCC1143 model recovery detail

**a,** Full HCC38/HCC1143 model backbone recovery ranking. **b,** Per-cell-line backbone recovery. **c,** Per-cell-line shift-excess identification. **d,** Per-cell-line structure-versus-context separation. **e,** Baseline top-20 overlap. **f,** GEARS top-20 overlap. **g,** Foundation-model top-20 overlap. **h,** Null-model top-20 overlap.

## Extended Data Fig. 5. GEARS sweep and stop rule

**a,** GEARS sweep candidate manifest. **b,** Batch status summary for sweep execution. **c,** Sweep candidate backbone recovery scores. **d,** Sweep candidate structure-versus-context separation scores. **e,** Baseline versus sweep-candidate trade-off. **f,** Stop-rule adjudication. **g,** Recipe dimensions varied in the finite sweep. **h,** GEARS training exemption boundary for figure generation.

## Extended Data Fig. 6. Full axis annotation and bootstrap support

**a,** Full axis explanatory balance. **b,** Representative bootstrap axis-call stability. **c,** Axis families in validation summary. **d,** Top axes by enrichment hits. **e,** Enrichment database coverage. **f,** Formal and preliminary axis-call composition. **g,** Top annotation terms. **h,** Axis claim boundary.

## Extended Data Fig. 7. K562 temporal evidence detail

**a,** K562 7d bridge summary. **b,** K562 13d bridge summary. **c,** Temporal stratification of rank bridge and mean shift. **d,** Temporal structure calls. **e,** K562 7d evidence tiers. **f,** K562 13d evidence tiers. **g,** Temporal panel call. **h,** A0/A1/B tier distribution.

## Extended Data Fig. 8. CRISPR versus RNAi endpoint detail

**a,** HCC38/HCC1143 CRISPR and RNAi truth-endpoint bridge strengths. **b,** K562 CRISPR and RNAi truth-endpoint bridge strengths. **c,** CRISPR-RNAi endpoint agreement. **d,** DEMETER2 conversion summary. **e,** Endpoint hierarchy across HCC38/HCC1143 and K562 contexts. **f,** RNAi sensitivity boundary. **g,** CRISPR-RNAi bridge gap. **h,** Endpoint claim boundary.

## Extended Data Fig. 9. Covariate audit details and wording boundary

**a,** Covariate audit axes. **b,** Covariate balance by cell line. **c,** Barcode-gem-group design-proxy boundary. **d,** High-imbalance target counts. **e,** Covariate-audit impact on anchor wording. **f,** Covariate status in the final claim matrix. **g,** Allowed wording. **h,** Disallowed wording.

## Extended Data Fig. 10. Reproducibility and claim governance

**a,** Main figure manifest overview. **b,** Supplementary table group overview. **c,** Hash coverage by file type. **d,** Final claim-matrix evidence-tier overview. **e,** Key allowed wording tiers. **f,** Configured rebuild entrypoints. **g,** Explicitly enumerated disallowed wording. **h,** Figure-stage rerun boundary.

## Extended Data Fig. 11. Axis-level adjudication supports only a qualified transcription/chromatin interpretation

**a,** Axis-level explanatory space comparing dependency signal with transcriptomic shift signal; the pale diagonal denotes equal explanatory signal, and RNA processing/spliceosome is annotated as PRPF6-only to mark the breadth boundary. **b,** Axis adjudication profile across shift signal, dependency signal, bootstrap stability and annotation/database support; target breadth is shown in each row label, and structure support is retained in the supplementary adjudication profile.
