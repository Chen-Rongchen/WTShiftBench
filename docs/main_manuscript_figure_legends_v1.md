# 主文 Figure Legends v1

## Figure 1. A truth-anchored benchmark defines a pre-specified perturbation-fitness recovery object in HCC38 and HCC1143

**a,** Study workflow and frozen recovery object. A truth-first workflow (perturbation truth → DepMap CRISPR dependency endpoint → frozen bridge object → model recovery adjudication → qualified claim boundary) defines the target-level recovery object before entrant scoring. The adjudicated entrant set includes the shared-mean baseline, GEARS, foundation-model entrants, linear controls, null references and rebuttal checks. The object is unpacked below into three pre-specified components: the truth signal (absolute mean perturbation shift), the alignment endpoint (CRISPR dependency) and the category rule (pre-specified 25/75 joint grid).

**b,** Pre-specified 25/75 category rule. Targets were classified on a pre-specified joint grid using the 25th and 75th quantiles of transcriptomic perturbation shift and CRISPR dependency, with corner-defined categories (Q1 anchor, Q2 transcriptomic excess, Q3 dependency excess, Q4 low information) and a retained middle band.

**c,** HCC38 target-level joint grid, with n, aligned Spearman rho and Q1 anchor count shown in the panel.

**d,** HCC1143 target-level joint grid, with n, aligned Spearman rho and Q1 anchor count shown in the panel.

**e,** Grid composition across the two primary contexts. Q2 transcriptomic-excess and Q3 dependency-excess targets were not observed in either primary context and are retained as zero-count categories in the composition summary.

**f,** Bridge strength summary. Visual elements are: (i) point, the observed aligned Spearman rho between absolute mean perturbation shift and CRISPR DepMap dependency on target-level pairs, with n = 47 (HCC38) and n = 48 (HCC1143); (ii) vertical error bar, the Fisher z-transform 95% confidence interval of the point estimate, computed in closed form from n and the observed rho and describing sampling uncertainty of the point itself, not a bootstrap; (iii) gray band, the 95% envelope of an empirical permutation null obtained by shuffling the target-to-DepMap pairing within each context 1000 times under a fixed seed, describing the range of aligned Spearman rho expected under the rho = 0 null hypothesis of no target-level alignment. The point estimate, the point-level CI and the null envelope are distinct quantities and are plotted together only to show that the observed bridge strength lies well outside the permutation null envelope in both primary contexts (empirical two-sided p = 0.001 for each context), consistent with a structured perturbation-fitness bridge rather than random association. The bridge is interpreted as a structured target-level recovery object with pre-specified categories, not as fully deconfounded causal proof.

## Figure 2. Shared anchors form a tiered target-level bridge rather than clean primary objects

**a,** Shared canonical anchor ranking across HCC38 and HCC1143.

**b,** Anchor recurrence across the two HCC cell lines.

**c,** Cutoff stability of recurrent anchors. PFDN5, PMF1, PRPF6 and ZNF131 retain stable shared-anchor status under the current cutoff sensitivity analysis.

**d,** Representative anchor-level contrast between PFDN5 and supporting anchors.

**e,** Cutoff-sensitive supporting objects, including ENY2, NPM1, RPS3, RUVBL2 and ZBTB17.

**f,** Evidence-tier composition after structural and covariate-aware tiering.

**g,** Anchor claim matrix. PFDN5 remains `primary_but_qualified`, whereas PMF1, PRPF6 and ZNF131 are retained as `supporting_only`.

**h,** Anchor-level claim boundary. Shared anchors support the bridge, but no individual anchor is allowed to prove a fully deconfounded bridge.

## Figure 3. Model recovery is metric-dependent and reveals a backbone-separation trade-off

**a,** Three adjudication metrics separate recovery modes across entrants. Absolute scores for backbone recovery, shift-excess identification and structure-versus-context separation, shown for the shared-mean baseline, the formal GEARS recipe, foundation-model entrants (Geneformer, scGPT), linear controls and the null reference.

**b,** Baseline leads backbone recovery, whereas GEARS leads context separation. Paired-dot contrast limited to the shared-mean baseline and the formal GEARS recipe on the two headline metrics.

**c,** Entrants occupy a backbone-separation trade-off space. Backbone recovery versus structure-versus-context separation across all entrants; baseline and GEARS are highlighted, Geneformer and scGPT are labelled, and GEARS sweep variants, linear controls and the null reference appear as a family-grouped supporting cloud. A lightly shaded upper-right reference region is included as an illustrative visual aid indicating the empty high-backbone/high-separation corner; the region is not a decision threshold and is not used for scoring or adjudication.

**d,** The same qualitative ordering is preserved in HCC38 and HCC1143. Per-context paired-dot comparison of the shared-mean baseline and the formal GEARS recipe on backbone recovery.

Prespecified GEARS sweep variants and their stop-rule adjudication (backbone versus shift-excess trade-off) are reported in Extended Data Fig. 5. shared_mean_baseline remains the backbone primary reference, whereas GEARS is retained as an architecture trade-off diagnosis rather than an overall HCC primary winner.

## Figure 4. Recipe and embedding controls do not close the backbone gap

**a,** GEARS backbone sweep. No finite-budget sweep candidate closes the backbone recovery gap to the shared-mean baseline.

**b,** Sweep trade-off between backbone recovery and structure-versus-context separation.

**c,** Shift-excess performance across GEARS sweep candidates.

**d,** Frozen stop-rule schematic for the GEARS sweep.

**e,** Linear-control schematic comparing low-rank, scGPT-ridge and Geneformer-ridge controls.

**f,** Linear-control ranking. Geneformer-ridge exceeds the other linear controls but does not exceed the shared-mean baseline in backbone recovery.

**g,** Coverage audit for embedding-based controls. Target coverage is complete and therefore does not explain the backbone gap.

**h,** Interpretation boundary. The observed gap is treated as a task-structure or direction-level mismatch rather than a missing small recipe.

## Figure 5. Covariate, temporal and endpoint analyses define the final claim boundary

**a,** Boundary architecture. Three independent layers jointly define the final claim scope. **b,** Covariate boundary. Mean Total Variation Distance across five covariate axes in HCC38 and HCC1143. **c,** Temporal and endpoint hierarchy boundary. K562 7d/13d temporal comparison is shown alongside CRISPR versus RNAi endpoint hierarchy across four contexts. **d,** Final claim boundary. CRISPR DepMap dependency is the primary readout; K562 temporal panel is supplementary evidence; RNAi DEMETER2 is a weaker cross-platform sensitivity endpoint; fully deconfounded architecture, content-level replication, RNAi primary readout and mechanism-level recovery remain unclaimed.
