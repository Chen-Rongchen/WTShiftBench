# 主文投稿稿 v2

## Title

Truth-first architecture-aware benchmarking reveals a backbone-separation trade-off in transcriptomic perturbation model recovery

## Abstract

Perturbation-response models are commonly evaluated by expression-level prediction accuracy, but such metrics do not directly test whether a model recovers transcriptomic structures linked to cellular fitness. We developed a truth-first, architecture-aware benchmark in which the object to be recovered is defined before model comparison. Real perturbation transcriptomic shifts were aligned to DepMap dependency endpoints to form a frozen truth-DepMap bridge, and model predictions were then assessed for recovery of this bridge architecture. In HCC38 and HCC1143, the bridge was supported by target-level anchors and bounded axis-level evidence rather than by a single global correlation. PFDN5 remained a primary but qualified anchor, whereas PMF1, PRPF6 and ZNF131 were retained as supporting anchors after covariate-aware tiering. Model adjudication showed that a shared-mean baseline recovered the canonical backbone more strongly than the formal GEARS recipe (0.807 versus 0.660), whereas GEARS showed stronger structure-versus-context separation (0.428 versus 0.353). A finite GEARS sweep and embedding-based linear controls did not close the backbone gap. K562 7d/13d temporal analysis provided supplementary architecture-form support but not content-level replication. Across HCC38, HCC1143, K562 7d and K562 13d, CRISPR DepMap endpoints retained stronger bridge signals than RNAi DEMETER2 endpoints. These results define a limitation-bounded benchmark: fitness-relevant transcriptomic bridge architectures can be defined, decomposed and audited, but current entrants do not stably recover the frozen architecture beyond a strong backbone baseline.

## Introduction

Large-scale perturbation transcriptomic datasets have enabled virtual perturbation models based on graph neural networks, single-cell foundation models and embedding-based decoders. These models are usually scored by their ability to predict observed expression after perturbation. Expression-level accuracy is useful, but it does not determine whether a model recovers the transcriptomic structures that align with downstream cellular phenotypes such as viability, dependency or fitness.

This distinction matters because perturbation responses contain separable components. Some signal can reflect a shared canonical backbone across contexts. Other signal can reflect context deviations, shift-excess responses or biological axes that are not captured by a single global prediction metric. A simple baseline can therefore perform strongly when the benchmark object is dominated by shared backbone structure, whereas a complex model can add signal in separation or deviation dimensions without recovering the backbone itself.

We therefore constructed a truth-first benchmark. In HCC38 and HCC1143, real perturbation transcriptomic shifts were aligned to DepMap CRISPR dependency endpoints, producing a truth-DepMap bridge. This bridge was decomposed into joint-priority grids, target-level anchors, axis-level interpretation, covariate boundaries and endpoint hierarchy before model comparison. Model predictions were then evaluated against the frozen architecture using three recovery dimensions: canonical backbone recovery, shift-excess identification and structure-versus-context separation.

This design revealed a backbone-separation trade-off. The shared-mean baseline remained the strongest primary reference for canonical backbone recovery, whereas GEARS showed a relative advantage in structure-versus-context separation. Foundation-model entrants and linear controls did not reverse this conclusion. K562 temporal and RNAi endpoint analyses further constrained the claim: architecture form recurred at a supplementary level, and CRISPR remained the stronger primary bridge endpoint, but the current evidence did not establish broad content-level replication or model recovery.

## Results

### A truth-first benchmark defines a structured fitness bridge

We first defined the recovery object independently of model predictions. In HCC38 and HCC1143, transcriptomic truth was summarized by `real_shift_mean_abs` and aligned to CRISPR DepMap dependency. Targets were stratified into high, middle and low bins for transcriptomic shift and dependency strength, defining Q1 anchors, transcriptomic-excess targets, dependency-excess targets, low-information targets and a retained middle band (Fig. 1a-c; Extended Data Fig. 1,2).

Both HCC contexts contained a Q1 anchor component. HCC38 contained 9 Q1 anchors and HCC1143 contained 10 Q1 anchors (Fig. 1d-f; Extended Data Fig. 2). The bridge was therefore not treated as a loose global correlation. It was retained as a structured truth object with target-level organization, while explicitly not interpreted as fully deconfounded causal proof (Fig. 1g,h).

### Shared anchors support the bridge but require tiered claim strength

We next examined target-level evidence shared across HCC38 and HCC1143. PFDN5, PMF1, PRPF6 and ZNF131 formed the most stable shared anchor set, recurrently occupying the high-shift/high-dependency region and retaining shared-anchor status under cutoff sensitivity analysis (Fig. 2a-c; Extended Data Fig. 3).

However, structural stability did not justify unqualified primary wording. After covariate-aware tiering, PFDN5 remained primary but qualified, whereas PMF1, PRPF6 and ZNF131 were downgraded to supporting-only evidence. ENY2, NPM1, RPS3, RUVBL2 and ZBTB17 were retained as supporting but cutoff-sensitive objects (Fig. 2d-g; Extended Data Fig. 3). The target-level evidence tier therefore separates structural recurrence from full deconfounding: shared anchors support the bridge, but no single anchor proves it (Fig. 2h).

### Current entrants reveal a backbone-separation trade-off

After freezing the truth object, we evaluated model recovery in HCC38 and HCC1143. The formal comparison included a shared-mean baseline, GEARS, scGPT, Geneformer, low-rank linear controls and pretrained-embedding ridge controls. Models were evaluated by backbone recovery, shift-excess identification and structure-versus-context separation (Fig. 3a,b; Extended Data Fig. 4).

The shared-mean baseline achieved the strongest backbone recovery score (0.807), exceeding formal GEARS (0.660). GEARS instead exceeded the baseline in structure-versus-context separation (0.428 versus 0.353). This was a directional trade-off: the baseline recovered the canonical backbone more strongly, whereas GEARS added more separation- or deviation-biased signal (Fig. 3c,d).

Foundation-model entrants and embedding-based controls did not overturn this result. Geneformer retained more signal than scGPT in this setting, and Geneformer-ridge exceeded the other linear controls, but neither displaced the shared-mean baseline as the backbone reference (Fig. 3e-h; Extended Data Fig. 4). Current entrants therefore recovered only part of the frozen architecture and did not establish model recovery beyond the baseline.

### Recipe and embedding controls do not close the backbone gap

We then tested whether the GEARS result reflected a missing small recipe. A finite sweep varied predefined recipe dimensions, including epoch/checkpoint, learning rate and weight decay. No sweep candidate closed the backbone gap to the shared-mean baseline. The best sweep candidate scored 0.643 for backbone recovery, below the baseline and below the formal GEARS recipe. Some candidates improved shift-excess identification or separation, but these gains did not become backbone superiority (Fig. 4a-c; Extended Data Fig. 5).

The sweep therefore met the stop rule: GEARS should be interpreted as an architecture trade-off diagnosis rather than as the HCC primary winner. Linear controls gave the same message. Low-rank and pretrained-embedding ridge models achieved complete target coverage but still did not exceed the shared-mean baseline in backbone recovery (Fig. 4d-g). The simplest interpretation is a task-structure mismatch, not a missing small recipe or missing target coverage (Fig. 4h).

### Axis-level interpretation is informative but remains partial

Axis-level analysis tested whether the bridge could be interpreted biologically. The strongest qualified formal axis was transcription/chromatin, which showed transcriptomic-heavy behavior with shift R2 = 0.092, dependency R2 near 0 and targets ENY2 and TADA3 (Fig. 5a,b,e; Extended Data Fig. 6).

Additional axes showed partial support, including chromatin remodeling, TGF-beta/BMP signaling, ER stress/UPR, RNA processing/spliceosome, ribosome biogenesis/nucleolar and ribosomal/translation axes. These axes varied in enrichment support, database support, per-target consistency and bootstrap stability (Fig. 5c-g; Extended Data Fig. 6). Thus, the axis layer provides interpretation rather than closure. Transcription/chromatin can be written as a primary but qualified axis, while the broader explanatory architecture remains partial (Fig. 5h).

### Covariate, temporal and endpoint analyses define the final boundary

We performed a multi-axis covariate audit covering barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes. The audit retained the bridge claim but prevented fully deconfounded wording (Fig. 6a,b; Extended Data Fig. 9). Barcode gem group illustrates this boundary: HCC38 maps to aggrMH001-3 and HCC1143 maps to aggrMH004-6, but individual MH001-MH006 run labels are not resolved (Fig. 6c; Extended Data Fig. 9).

We next examined external recurrence using the GSE90063 K562 7d/13d temporal panel. Both time points supported a backbone-plus-shift-excess architecture form. The 7d panel had stronger rank alignment, whereas 13d had larger mean shift, indicating temporal stratification rather than monotonic later-timepoint improvement (Fig. 6d,e; Extended Data Fig. 7). Under A0/A1/B tiering, K562 supports architecture-form confirmation and bridge-form support, but not content-level replication or a primary co-pillar conclusion (Fig. 6f; Extended Data Fig. 7).

Finally, CRISPR DepMap and RNAi DEMETER2 endpoints were compared across HCC38, HCC1143, K562 7d and K562 13d. CRISPR bridge Spearman exceeded RNAi in every context: 0.726 versus 0.276 in HCC38, 0.779 versus 0.384 in HCC1143, 0.733 versus 0.333 in K562 7d and 0.515 versus 0.300 in K562 13d (Fig. 6g; Extended Data Fig. 8). CRISPR DepMap was therefore retained as the primary bridge readout, whereas RNAi DEMETER2 was retained as a weaker cross-platform sensitivity endpoint (Fig. 6h).

## Discussion

This study reframes perturbation-model benchmarking around a prior truth object rather than a posterior leaderboard. By defining a fitness-relevant transcriptomic bridge before model comparison, the benchmark asks whether models recover a structured architecture connecting perturbation response to dependency. The resulting claim is robust but bounded: the bridge is structurally retained, but current entrants do not stably recover the frozen architecture beyond a strong shared-backbone baseline.

The model-side result is a backbone-separation trade-off. The shared-mean baseline captures the dominant canonical backbone. GEARS contributes stronger structure-versus-context separation, but that advantage does not translate into superior backbone recovery. Foundation-model entrants and embedding-based controls also fail to overturn the baseline reference. This does not imply that complex perturbation models have no value; it specifies where their current advantages are misaligned with the strongest component of this frozen fitness-bridge architecture.

The truth-side result is also bounded. PFDN5, PMF1, PRPF6 and ZNF131 are meaningful shared anchors because they jointly occupy high transcriptomic-impact and high-dependency regions and remain stable under cutoff sensitivity. Yet covariate-aware governance prevents these objects from being written as clean, fully deconfounded primary anchors. Structural stability supports the bridge; it does not remove design or quality-related uncertainty.

External and endpoint analyses further constrain interpretation. K562 supports recurrence of the architecture form outside the HCC primary context, but does not establish content-level replication because the target set, macro-class composition and bridgeable target count differ from HCC. RNAi DEMETER2 provides a useful cross-platform sensitivity endpoint, but is consistently weaker than matched CRISPR DepMap endpoints and cannot replace the primary readout.

Several limitations follow directly from these boundaries. Available metadata do not resolve barcode gem group to individual MH001-MH006 runs. Axis-level interpretation remains partial, with transcription/chromatin as the strongest qualified formal axis. The K562 temporal panel has limited bridgeable target counts and should be read as supplementary architecture-form support. Finally, the benchmark does not prove biological mechanism recovery by any model; it provides a structured adjudication framework for where current entrants succeed or fail.

## Methods

### Truth-DepMap bridge construction

For each HCC context, perturbation-level transcriptomic truth was summarized using `real_shift_mean_abs`. DepMap dependency endpoints were direction-aligned so that larger aligned values represented stronger dependency or liability. Targets were stratified by transcriptomic shift and aligned dependency strength into high, middle and low bins. This produced Q1 anchors, transcriptomic-excess targets, dependency-excess targets, low-information targets and middle-band targets. Full target-level grids and summaries were retained as source data for Fig. 1 and Extended Data Fig. 2.

### Anchor tiering and sensitivity

Shared anchors were defined by recurrent high-shift/high-dependency behavior across HCC38 and HCC1143. Cutoff sensitivity and control subsampling were used to assess whether anchor calls and global bridge estimates were stable. Anchor claim strength was assigned using structural recurrence, cutoff stability and covariate-aware governance. PFDN5 was retained as primary but qualified; PMF1, PRPF6 and ZNF131 were retained as supporting-only anchors.

### Model recovery adjudication

Model predictions were evaluated against the frozen truth architecture using backbone recovery, shift-excess identification and structure-versus-context separation. Entrants included GEARS, scGPT, Geneformer, low-rank linear controls and pretrained-embedding ridge controls. A shared-mean baseline and a null model served as references. Per-cell-line and model-level summaries were retained for Extended Data Fig. 4.

### GEARS sweep and controls

The GEARS sweep varied only predefined recipe parameters and was evaluated under the same frozen scoring system. The stop rule required that GEARS not be promoted as the HCC primary winner unless a finite-budget recipe closed the backbone gap to the shared-mean baseline. GEARS training was not rerun during figure production; frozen predictions, scoring tables and sweep artifacts were used with recorded hashes.

### Axis-level analysis

Axis-level explanatory strength was computed separately for transcriptomic shift and dependency. Formal axis interpretation required sufficient support and was evaluated using enrichment evidence, database support, per-target consistency and bootstrap stability. Axis evidence was used for interpretation and tiering, not as a replacement for target-level bridge evidence.

### Covariate audit

Covariate audit included barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes. Barcode gem group was treated as a design-proxy axis rather than a fully resolved run-level covariate. Covariate audit governed wording strength and did not claim complete deconfounding.

### K562 temporal panel

The GSE90063 K562 7d/13d temporal panel was used as supplementary external evidence. The 13d panel was treated as the primary formal supplementary bridge test and the 7d panel as a temporal sensitivity or early-bridge probe. Evidence was assigned to A0 architecture-form confirmation, A1 bridge-form support or B content-level not eligible tiers.

### Endpoint hierarchy

CRISPR DepMap and RNAi DEMETER2 endpoints were compared across HCC38, HCC1143, K562 7d and K562 13d. Bridge Spearman values and CRISPR-RNAi endpoint agreement were used to establish endpoint hierarchy. CRISPR DepMap was retained as the primary bridge readout; RNAi DEMETER2 was retained as a weaker cross-platform sensitivity endpoint.

### Reproducibility and source data

All main figures and Extended Data figures were generated as panel-level artifacts. Each panel has a PNG, PDF, source-data table and manifest recording input files, SHA256 hashes, output hashes, script path and claim boundary. Whole-figure assemblies have combined source-data tables and figure-level manifests. The manuscript figure package can be rebuilt with:

```bash
pixi run --environment core python scripts/manuscript/build_all_main_figures.py
pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py
pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py
```

## Data Availability

Figure source data are available under `reports/manuscript_figures_v2/` and `reports/manuscript_extended_data_v1/`. Supplementary table indexes and file hashes are available under `reports/manuscript_supplementary_tables_v1/`.

## Code Availability

Figure-generation code is available under `src/wtbench/manuscript/` and `scripts/manuscript/`. Figure configuration files are available under `configs/manuscript/`.
