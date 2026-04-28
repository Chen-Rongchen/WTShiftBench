# 主文投稿稿 v2

## Title

A truth-anchored framework and resource for evaluating transcriptomic perturbation models against cancer dependency endpoints

## Abstract

A central problem in perturbation-model evaluation is that expression-level prediction accuracy does not by itself define the phenotype-relevant object a model should recover. We developed a truth-first, architecture-aware framework and resource that first freezes a phenotype-aligned truth object and only then adjudicates model recovery. Real perturbation transcriptomic shifts were aligned to DepMap dependency endpoints to define a truth-DepMap bridge, and model predictions were assessed against this fixed architecture using backbone recovery, shift-excess identification and structure-versus-context separation. In the HCC38 and HCC1143 breast-cancer cell-line contexts, the bridge was supported by target-level anchors and bounded axis-level evidence rather than by a single global correlation. PFDN5 remained a primary but qualified anchor, whereas PMF1, PRPF6 and ZNF131 were retained as supporting anchors after covariate-aware tiering. Architecture-aware adjudication revealed a backbone-vs-separation trade-off: a shared-mean reference recovered the canonical backbone more strongly than the formal GEARS recipe (0.807 versus 0.660), whereas GEARS showed stronger structure-versus-context separation (0.428 versus 0.353). A finite GEARS sweep and embedding-based linear controls did not close the backbone gap. K562 7d/13d temporal analysis provided supplementary architecture-form support but not content-level replication. Across HCC38, HCC1143, K562 7d and K562 13d, CRISPR DepMap endpoints retained stronger bridge signals than RNAi DEMETER2 endpoints. This resource provides a reproducible framework for extending phenotype-aligned perturbation-model adjudication to future cell-line contexts, endpoints and entrants while preserving explicit claim boundaries.

## Introduction

Perturbation-model benchmarks need a phenotype-relevant recovery object, not only a prediction score. Large-scale perturbation transcriptomic datasets have enabled virtual perturbation models based on graph neural networks, single-cell foundation models and embedding-based decoders. These models are usually scored by their ability to predict observed expression after perturbation. Expression-level accuracy is useful, but it does not determine whether a model recovers the transcriptomic structures that align with downstream cellular phenotypes such as viability, dependency or fitness.

The first design problem is therefore object definition. A perturbation response can contain a shared canonical backbone across contexts, context deviations, shift-excess responses and biological axes that are only partially aligned with dependency. A simple baseline can perform strongly when the benchmark object is dominated by shared backbone structure, whereas a complex model can add signal in separation or deviation dimensions without recovering the backbone itself. Without freezing the benchmark truth object before model comparison, a leaderboard can conflate expression reconstruction, endpoint alignment and biological interpretation.

Prior perturbation-prediction benchmarks have already shown that expression-level recovery by deep learning or foundation-model entrants can be matched or exceeded by simple baselines. These studies provide essential context for interpreting model-side results, but they ask a different question from the one addressed here. They evaluate transcriptome prediction accuracy, whereas the present benchmark first freezes a phenotype-relevant truth object by aligning perturbation transcriptomic shifts to cancer dependency endpoints. Model recovery is then decomposed into backbone recovery, shift-excess identification and structure-versus-context separation. The resulting claim is not that complex models fail in a unidirectional sense, but that current entrants occupy different parts of a frozen fitness-bridge architecture.

We therefore constructed a truth-first benchmark and resource. In the HCC38 and HCC1143 breast-cancer cell-line contexts, real perturbation transcriptomic shifts were aligned to DepMap CRISPR dependency endpoints to produce a truth-DepMap bridge. This bridge was decomposed into joint-priority grids, target-level anchors, axis-level interpretation, covariate boundaries and endpoint hierarchy before model comparison. Model predictions were then evaluated against the frozen architecture using three recovery dimensions: canonical backbone recovery, shift-excess identification and structure-versus-context separation.

This design revealed a backbone-separation trade-off. The shared-mean baseline remained the strongest primary reference for canonical backbone recovery, whereas GEARS showed a relative advantage in structure-versus-context separation. Foundation-model entrants and linear controls did not reverse this conclusion. K562 temporal and RNAi endpoint analyses further constrained the claim: architecture form recurred at a supplementary level, and CRISPR remained the stronger primary bridge endpoint, but the current evidence did not establish broad content-level replication or model recovery.

## Results

### A truth-first benchmark defines a structured fitness bridge

We first defined the recovery object independently of model predictions. In HCC38 and HCC1143, transcriptomic truth was summarized by `real_shift_mean_abs` and aligned to CRISPR DepMap dependency. Targets were stratified into high, middle and low bins for transcriptomic shift and dependency strength, defining Q1 anchors, transcriptomic-excess targets, dependency-excess targets, low-information targets and a retained middle band (Fig. 1a-c; Extended Data Fig. 1,2).

Both breast-cancer cell-line contexts contained a Q1 anchor component. HCC38 contained 9 Q1 anchors and HCC1143 contained 10 Q1 anchors (Fig. 1d-f; Extended Data Fig. 2). The bridge was therefore not treated as a loose global correlation. It was retained as a structured truth object with target-level organization, while explicitly not interpreted as fully deconfounded causal proof (Fig. 1g,h).

### Shared anchors support the bridge but require tiered claim strength

We next examined target-level evidence shared across HCC38 and HCC1143. PFDN5, PMF1, PRPF6 and ZNF131 formed the most stable shared anchor set, recurrently occupying the high-shift/high-dependency region and retaining shared-anchor status under cutoff sensitivity analysis (Fig. 2a-c; Extended Data Fig. 2).

However, structural stability did not justify unqualified primary wording. After covariate-aware tiering, PFDN5 remained primary but qualified, whereas PMF1, PRPF6 and ZNF131 were downgraded to supporting-only evidence. ENY2, NPM1, RPS3, RUVBL2 and ZBTB17 were retained as supporting but cutoff-sensitive objects (Fig. 2d-g; Extended Data Fig. 2). The target-level evidence tier therefore separates structural recurrence from full deconfounding: shared anchors support the bridge, but no single anchor proves it (Fig. 2h).

### Current entrants reveal a backbone-separation trade-off

After freezing the truth object, we evaluated model recovery in HCC38 and HCC1143. The formal comparison included a shared-mean baseline, GEARS, scGPT, Geneformer, low-rank linear controls and pretrained-embedding ridge controls. Models were evaluated by backbone recovery, shift-excess identification and structure-versus-context separation (Fig. 3a,b).

The shared-mean baseline achieved the strongest backbone recovery score (0.807), exceeding formal GEARS (0.660). GEARS instead exceeded the baseline in structure-versus-context separation (0.428 versus 0.353). This was a directional trade-off: the baseline recovered the canonical backbone more strongly, whereas GEARS added more separation- or deviation-biased signal (Fig. 3c,d).

Foundation-model entrants and embedding-based controls did not overturn this result. Geneformer retained more signal than scGPT in this setting, and Geneformer-ridge exceeded the other linear controls, but neither displaced the shared-mean baseline as the backbone reference (Fig. 3e-h). Current entrants therefore recovered only part of the frozen architecture and did not establish model recovery beyond the baseline.

### Recipe and embedding controls do not close the backbone gap

We then tested whether the GEARS result reflected a missing small local recipe. A predefined finite-budget neighborhood sweep varied epochs, learning rate and weight decay using a nearest-to-base selection rule. Six candidate recipes were materialized or re-used, including the base recipe and five one-axis variants. No sweep candidate closed the backbone gap to the shared-mean baseline. The best sweep candidate scored 0.643 for backbone recovery, below the baseline and below the formal GEARS recipe. Some candidates improved shift-excess identification or separation, but these gains did not become backbone superiority (Fig. 4a-c).

The sweep therefore met the stop rule: GEARS should be interpreted as an architecture trade-off diagnosis rather than as the HCC38/HCC1143 primary winner. Linear controls gave the same message. Low-rank and pretrained-embedding ridge models achieved complete target coverage but still did not exceed the shared-mean baseline in backbone recovery (Fig. 4b,c). These controls make an untested small recipe or missing target coverage less likely as the sole explanation for the backbone gap; the bounded interpretation is stated in the Fig. 4 caption rather than as a separate panel.

### Axis-level interpretation is informative but remains partial

Axis-level analysis tested whether the bridge could be interpreted biologically. The strongest qualified formal axis was transcription/chromatin, which showed transcriptomic-heavy behavior with shift R2 = 0.092, dependency R2 near 0 and targets ENY2 and TADA3 (Extended Data Fig. 4).

Additional axes showed partial support, including chromatin remodeling, TGF-beta/BMP signaling, ER stress/UPR, RNA processing/spliceosome, ribosome biogenesis/nucleolar and ribosomal/translation axes. These axes varied in enrichment support, database support, per-target consistency and bootstrap stability (Extended Data Fig. 4). Thus, the axis layer provides interpretation rather than closure. Transcription/chromatin can be written as a primary but qualified axis, while the broader explanatory architecture remains partial.

### Covariate, temporal and endpoint analyses define the final boundary

We performed a multi-axis covariate audit covering barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes. The audit retained the bridge claim but prevented fully deconfounded wording (Fig. 5a,b). Barcode gem group illustrates this boundary: HCC38 maps to aggrMH001-3 and HCC1143 maps to aggrMH004-6, but individual MH001-MH006 run labels are not resolved (Fig. 5c).

We next examined external recurrence using the GSE90063 K562 7d/13d temporal panel. Both time points supported a backbone-plus-shift-excess architecture form. The 7d panel had stronger rank alignment, whereas 13d had larger mean shift, indicating temporal stratification rather than monotonic later-timepoint improvement (Fig. 5c; Extended Data Fig. 3). Under A0/A1/B tiering, K562 supports architecture-form confirmation and bridge-form support, but not content-level replication or a primary co-pillar conclusion (Fig. 5d; Extended Data Fig. 3).

Finally, CRISPR DepMap and RNAi DEMETER2 endpoints were compared across HCC38, HCC1143, K562 7d and K562 13d. CRISPR bridge Spearman exceeded RNAi in every context: 0.726 versus 0.276 in HCC38, 0.779 versus 0.384 in HCC1143, 0.733 versus 0.333 in K562 7d and 0.515 versus 0.300 in K562 13d (Fig. 5c; Extended Data Fig. 2). CRISPR DepMap was therefore retained as the primary bridge readout, whereas RNAi DEMETER2 was retained as a weaker cross-platform sensitivity endpoint (Fig. 5d).

## Discussion

This study reframes perturbation-model benchmarking around a prior truth object rather than a posterior leaderboard. By defining a fitness-relevant transcriptomic bridge before model comparison, the benchmark asks whether models recover a structured architecture connecting perturbation response to dependency. The resulting claim is robust but bounded: the bridge is structurally retained, but current entrants do not stably recover the frozen architecture beyond a strong shared-backbone baseline.

The model-side result is a backbone-separation trade-off. The shared-mean baseline captures the dominant canonical backbone. This baseline is a frozen-architecture backbone reference rather than a deployable predictive model: it is constructed from the canonical-backbone transcriptomic component and does not use DepMap dependency values, RNAi endpoints or model-side scoring outcomes to generate target-specific predictions. GEARS contributes stronger structure-versus-context separation, but that advantage does not translate into superior backbone recovery. Foundation-model entrants and embedding-based controls also fail to overturn the baseline reference. This does not imply that complex perturbation models have no value; it specifies where their current advantages are misaligned with the strongest component of this frozen fitness-bridge architecture.

The truth-side result is also bounded. PFDN5, PMF1, PRPF6 and ZNF131 are meaningful shared anchors because they jointly occupy high transcriptomic-impact and high-dependency regions and remain stable under cutoff sensitivity. Yet covariate-aware governance prevents these objects from being written as clean, fully deconfounded primary anchors. Structural stability supports the bridge; it does not remove design or quality-related uncertainty.

External and endpoint analyses further constrain interpretation. K562 supports recurrence of the architecture form outside the HCC38/HCC1143 primary breast-cancer cell-line contexts, but does not establish content-level replication because the target set, macro-class composition and bridgeable target count differ from the HCC38/HCC1143 benchmark object. RNAi DEMETER2 provides a useful cross-platform sensitivity endpoint, but is consistently weaker than matched CRISPR DepMap endpoints and cannot replace the primary readout.

Several limitations follow directly from these boundaries. First, the primary evidence is based on two breast-cancer cell-line contexts, HCC38 and HCC1143, and a limited shared-anchor set, so bridge content is treated as qualified rather than as broad biological generalization. Second, available metadata do not resolve barcode gem group to individual MH001-MH006 runs; `barcode_gem_group` is therefore a design-proxy covariate, not a fully resolved run-level batch covariate. Design-proxy rank residualization did not overturn the bridge or primary anchor structure, but residual design or batch confounding cannot be fully excluded. Third, the K562 temporal panel supports architecture-form recurrence but not content-level replication because the target set, macro-class composition and bridgeable target count differ from the HCC38/HCC1143 benchmark object. Fourth, RNAi DEMETER2 is retained only as a cross-platform sensitivity endpoint and is not a matched primary endpoint. Axis-level interpretation remains partial, with transcription/chromatin as the strongest qualified formal axis. Finally, the benchmark does not prove biological mechanism recovery by any model; it provides a structured adjudication framework for assessing which components of the frozen architecture are recovered, missed or only partially supported.

## Methods

### Truth-DepMap bridge construction

For each HCC38/HCC1143 breast-cancer cell-line context, perturbation-level transcriptomic truth was summarized using `real_shift_mean_abs`. DepMap dependency endpoints were direction-aligned so that larger aligned values represented stronger dependency or liability. Targets were stratified by transcriptomic shift and aligned dependency strength into high, middle and low bins. This produced Q1 anchors, transcriptomic-excess targets, dependency-excess targets, low-information targets and middle-band targets. Full target-level grids and summaries were retained as source data for Fig. 1 and Extended Data Fig. 2.

### Anchor tiering and sensitivity

Shared anchors were defined by recurrent high-shift/high-dependency behavior across HCC38 and HCC1143. Cutoff sensitivity and control subsampling were used to assess whether anchor calls and global bridge estimates were stable. Anchor claim strength was assigned using structural recurrence, cutoff stability and covariate-aware governance. PFDN5 was retained as primary but qualified; PMF1, PRPF6 and ZNF131 were retained as supporting-only anchors.

### Model recovery adjudication

Model predictions were evaluated against the frozen truth architecture using backbone recovery, shift-excess identification and structure-versus-context separation. Entrants included GEARS, scGPT, Geneformer, low-rank linear controls and pretrained-embedding ridge controls. A shared-mean baseline and a null model served as references. Per-cell-line and model-level summaries were retained for Fig. 3.

### GEARS sweep and controls

The GEARS sweep was a predefined finite-budget neighborhood sweep rather than an exhaustive hyperparameter search. The parent configuration allowed variation in epochs (20, 30 or 40), learning rate (0.0005, 0.001 or 0.002) and weight decay (0.000001 or 0.00001), with `materialization_export_sanity` fixed to `default_only`. A nearest-to-base selection rule materialized or re-used six candidate recipes, including the base recipe and five one-axis variants. All candidates were evaluated under the same frozen scoring system. The stop rule required that GEARS not be promoted as the HCC38/HCC1143 primary winner unless a finite-budget recipe closed the backbone gap to the shared-mean baseline. GEARS training was not rerun during figure production; frozen predictions, scoring tables and sweep artifacts were used with recorded hashes.

### Axis-level analysis

Axis-level explanatory strength was computed separately for transcriptomic shift and dependency. Formal axis interpretation required sufficient support and was evaluated using enrichment evidence, database support, per-target consistency and bootstrap stability. Axis evidence was used for interpretation and tiering, not as a replacement for target-level bridge evidence.

### Covariate audit

Covariate audit included barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes. Barcode gem group was treated as a design-proxy axis rather than a fully resolved run-level covariate. Covariate audit governed wording strength and did not claim complete deconfounding.

### K562 temporal panel

The GSE90063 K562 7d/13d temporal panel was used as supplementary external evidence. An earlier legacy object distributed under a `dixit_2016_raw` filename did not match the GSE90063 K562 TF-pool description and was excluded before analysis. All Dixit/K562 evidence in this study was derived de novo from GSE90063 7d and 13d data. The 13d panel was treated as the primary formal supplementary bridge test and the 7d panel as a temporal sensitivity or early-bridge probe. Evidence was assigned to A0 architecture-form confirmation, A1 bridge-form support or B content-level not eligible tiers.

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
