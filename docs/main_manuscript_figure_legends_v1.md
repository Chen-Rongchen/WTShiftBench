# 主文 Figure Legends v1

## Figure 1. A truth-first benchmark defines the fitness-relevant transcriptomic bridge object

**a,** Truth-first benchmark workflow. Real perturbation transcriptomic shifts are first aligned to DepMap dependency endpoints to define a frozen bridge object. Model predictions are evaluated only after this truth object is fixed.

**b,** HCC dataset and endpoint overview. HCC38 and HCC1143 are evaluated using `real_shift_mean_abs` as the transcriptomic truth metric and CRISPR DepMap dependency as the primary fitness-relevant endpoint.

**c,** Joint-priority grid definition. Targets are stratified by transcriptomic shift and dependency strength to define Q1 anchors, transcriptomic-excess objects, dependency-excess objects, low-information objects and a retained middle band.

**d,** HCC38 target-level joint grid.

**e,** HCC1143 target-level joint grid.

**f,** Grid composition across HCC contexts. HCC38 contains 9 Q1 anchors and HCC1143 contains 10 Q1 anchors.

**g,** CRISPR truth-DepMap bridge strength across HCC38 and HCC1143.

**h,** Claim boundary for Fig. 1. The bridge is retained as a structured truth object, but it is not interpreted as fully deconfounded causal proof.

## Figure 2. Shared anchors form a tiered target-level bridge rather than clean primary objects

**a,** Shared canonical anchor ranking across HCC38 and HCC1143.

**b,** Anchor recurrence across the two HCC cell lines.

**c,** Cutoff stability of recurrent anchors. PFDN5, PMF1, PRPF6 and ZNF131 retain stable shared-anchor status under the current cutoff sensitivity analysis.

**d,** Representative anchor-level contrast between PFDN5 and supporting anchors.

**e,** Cutoff-sensitive supporting objects, including ENY2, NPM1, RPS3, RUVBL2 and ZBTB17.

**f,** Evidence-tier composition after structural and covariate-aware tiering.

**g,** Anchor claim matrix. PFDN5 remains `primary_but_qualified`, whereas PMF1, PRPF6 and ZNF131 are retained as `supporting_only`.

**h,** Anchor-level claim boundary. Shared anchors support the bridge, but no individual anchor is allowed to prove a fully deconfounded bridge.

## Figure 3. Current entrants do not outperform the backbone baseline but reveal a recovery trade-off

**a,** HCC formal model comparison by backbone recovery score.

**b,** Three-dimensional recovery summary: backbone recovery, shift-excess identification and structure-versus-context separation.

**c,** Headline comparison between the shared-mean baseline and formal GEARS recipe. The baseline has stronger backbone recovery, whereas GEARS has stronger structure-versus-context separation.

**d,** Backbone recovery versus structure-versus-context separation.

**e,** Per-context recovery comparison between the baseline and GEARS.

**f,** Shift-excess recovery across model entrants.

**g,** Model-family grouping across baseline, GEARS, foundation-model and linear-control entrants.

**h,** Model-side claim boundary. GEARS is interpreted as an architecture trade-off diagnosis, not as the HCC primary winner.

## Figure 4. Recipe and embedding controls do not close the backbone gap

**a,** GEARS backbone sweep. No finite-budget sweep candidate closes the backbone recovery gap to the shared-mean baseline.

**b,** Sweep trade-off between backbone recovery and structure-versus-context separation.

**c,** Shift-excess performance across GEARS sweep candidates.

**d,** Frozen stop-rule schematic for the GEARS sweep.

**e,** Linear-control schematic comparing low-rank, scGPT-ridge and Geneformer-ridge controls.

**f,** Linear-control ranking. Geneformer-ridge exceeds the other linear controls but does not exceed the shared-mean baseline in backbone recovery.

**g,** Coverage audit for embedding-based controls. Target coverage is complete and therefore does not explain the backbone gap.

**h,** Interpretation boundary. The observed gap is treated as a task-structure or direction-level mismatch rather than a missing small recipe.

## Figure 5. Axis-level interpretation is partial and claim-bounded

**a,** Axis-level explanatory balance, comparing dependency R2 with transcriptomic shift R2.

**b,** Formal and preliminary axis-call composition. Transcription/chromatin is the only formal positive axis in the current evidence set.

**c,** Bootstrap stability of representative axis calls, including unstable, stable and transcription/chromatin examples.

**d,** Annotation support across representative axes, summarized by enrichment hits, database support and structure support.

**e,** Transcription/chromatin focus. This axis is transcriptomic-heavy, with shift R2 = 0.092, dependency R2 = 0.000 and targets ENY2 and TADA3.

**f,** Partial support by broader axis family. Annotation-backed axes remain partially supported rather than fully established.

**g,** Preliminary and mixed axes ranked by shift-minus-dependency explanatory balance.

**h,** Axis claim boundary. Transcription/chromatin is retained as `primary_axis_but_qualified`; the manuscript must not claim a fully deconfounded shared explanatory architecture.

## Figure 6. Covariate, temporal and endpoint analyses define the final claim boundary

**a,** Covariate audit overview across barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes.

**b,** Covariate-aware anchor tiering. PFDN5 remains primary but qualified; PMF1, PRPF6 and ZNF131 are supporting-only.

**c,** Barcode gem group boundary. HCC38 maps to aggrMH001-3 and HCC1143 maps to aggrMH004-6, but individual MH001-MH006 run labels are not resolved.

**d,** K562 temporal panel overview for GSE90063 7d and 13d.

**e,** Temporal stratification. The 7d panel shows stronger rank alignment, whereas 13d shows larger mean shift.

**f,** A0/A1/B supplementary tiering for K562 evidence. The temporal panel supports architecture-form recurrence and bridge-form support, but not content-level replication.

**g,** Endpoint hierarchy across HCC38, HCC1143, K562 7d and K562 13d. CRISPR DepMap endpoints retain stronger bridge Spearman than RNAi DEMETER2 endpoints in every context.

**h,** Final claim boundary. CRISPR is the primary bridge readout, RNAi is a weaker sensitivity endpoint, K562 is supplementary and discovery remains gated.
