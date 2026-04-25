# 主文稿投稿草案 v1

## Title

Truth-first architecture-aware benchmarking reveals a backbone-separation trade-off in transcriptomic perturbation model recovery

## Abstract

Perturbation-response models are often evaluated by expression-level prediction accuracy, but such metrics do not directly test whether a model recovers transcriptomic structures that are relevant to cellular fitness or dependency. We developed a truth-first, architecture-aware benchmark in which the evaluated object is defined before model comparison: real perturbation transcriptomic shifts are aligned to DepMap dependency endpoints to form a frozen fitness-relevant bridge architecture, and models are then assessed for recovery of this object. In the HCC38 and HCC1143 breast-cancer cell-line contexts, the truth-DepMap bridge was not a loose correlation phenomenon, but a tiered object supported by target-level anchors and limited axis-level evidence. PFDN5 remained a primary but qualified anchor, whereas PMF1, PRPF6 and ZNF131 were retained only as supporting anchors after covariate-aware claim tiering. Model-side adjudication showed that a shared-mean baseline recovered the canonical backbone more strongly than the formal GEARS recipe (0.807 versus 0.660), whereas GEARS showed stronger structure-versus-context separation (0.428 versus 0.353). A finite GEARS backbone sweep and embedding-based linear controls did not close this gap, supporting an architecture trade-off rather than model recovery. A GSE90063 K562 7d/13d temporal panel provided supplementary support for recurrence of the backbone-plus-shift-excess architecture form, but not content-level replication. Across HCC38, HCC1143, K562 7d and K562 13d, CRISPR DepMap endpoints consistently retained stronger bridge signals than RNAi DEMETER2 endpoints, establishing CRISPR as the primary bridge readout and RNAi as a weaker cross-platform sensitivity endpoint. These results define a limitation-bounded benchmark: fitness-relevant transcriptomic bridge architectures can be constructed, decomposed and partially replicated, but current entrants do not yet stably recover the frozen architecture beyond a strong backbone baseline.

## Introduction

Large-scale perturbation transcriptomic datasets have motivated a growing class of virtual perturbation models, including graph neural networks, single-cell foundation models and embedding-based decoders. These models are typically evaluated by how well they predict observed gene expression after perturbation. Expression-level accuracy is useful, but it does not fully answer whether a model recovers the specific transcriptomic structures that matter for downstream cellular phenotypes such as viability, dependency or fitness.

This distinction is important because a perturbation response can contain several separable components. Some signal may reflect a shared canonical backbone that is common across contexts. Other signal may reflect context-specific deviations, shift-excess responses or axis-level structures that are not captured by a single global expression metric. A model can therefore look useful in one component while failing in another. Conversely, a simple baseline can be strong if the benchmark target is dominated by shared backbone structure.

We therefore constructed a truth-first benchmark. Instead of ranking models first and interpreting the highest-scoring entrant afterward, we first defined the object to be recovered. In the HCC38 and HCC1143 breast-cancer cell-line contexts, real perturbation transcriptomic shifts were aligned to DepMap CRISPR dependency endpoints, producing a truth-DepMap bridge. This bridge was decomposed into target-level joint-priority grids, shared anchors, axis-level explanatory structures, covariate boundaries and endpoint hierarchy. Only after this truth object was fixed did we evaluate model recovery.

The model-side adjudication was also architecture-aware. Rather than collapsing performance into a single score, we used three recovery dimensions: canonical backbone recovery, shift-excess identification and structure-versus-context separation. This design allowed us to distinguish a model that recovers the shared backbone from one that is better at separating context-specific or deviation-related structure.

Our main finding is not that a particular complex model wins. Instead, current entrants expose a backbone-separation trade-off. A shared-mean baseline remains the strongest primary reference for canonical backbone recovery, whereas GEARS shows a relative advantage in structure-versus-context separation. Foundation-model entrants and linear controls do not reverse this conclusion. Additional K562 temporal and RNAi endpoint analyses further define the boundary of the claim: the architecture form has supplementary recurrence, and CRISPR is the stronger primary bridge endpoint, but the current evidence does not establish broad content-level replication or model recovery.

## Results

### A truth-first benchmark defines a structured fitness bridge

We first asked whether the object to be recovered could be defined independently of model predictions. In the HCC38/HCC1143 primary breast-cancer cell-line analysis, we aligned real perturbation transcriptomic shifts to DepMap CRISPR dependency endpoints using `real_shift_mean_abs` as the primary transcriptomic truth metric and aligned dependency strength as the fitness-relevant endpoint. Targets were assigned to a joint-priority grid by stratifying both transcriptomic shift and dependency strength into high, middle and low bins. This defined Q1 anchors with high transcriptomic shift and high dependency strength, transcriptomic-excess and dependency-excess quadrants, and a middle band that was retained rather than forced into binary calls (Fig. 1a-c).

Both breast-cancer cell-line contexts contained a clear Q1 anchor component. HCC1143 contained 10 Q1 anchors, representing 20.8% of bridgeable targets, while HCC38 contained 9 Q1 anchors, representing 19.1% of bridgeable targets (Fig. 1d-f). This distribution indicates that the bridge is not merely a single global correlation. Instead, it has target-level structure in which a subset of perturbations jointly occupy high transcriptomic-impact and high-dependency regions. The global truth-DepMap bridge was therefore retained at the structural level, while explicitly not interpreted as fully deconfounded causal evidence (Fig. 1g,h).

### Shared anchors support the bridge but require tiered claim strength

We next examined which target-level objects supported the bridge across HCC38 and HCC1143. PFDN5, PMF1, PRPF6 and ZNF131 formed the most stable shared anchor set. These targets recurrently occupied the high-shift/high-dependency region across both breast-cancer cell-line contexts and retained shared-anchor status under cutoff sensitivity analysis (Fig. 2a-c).

However, structural stability did not justify unqualified primary wording. After covariate-aware tiering, PFDN5 remained the only primary but qualified anchor. PMF1, PRPF6 and ZNF131 retained their structural anchor identity but were downgraded to supporting-only evidence. Additional objects, including ENY2, NPM1, RPS3, RUVBL2 and ZBTB17, remained informative but cutoff-sensitive and were therefore treated as supporting but sensitive (Fig. 2d-f).

The resulting target-level evidence tier separates two ideas that are often conflated: an anchor can be structurally stable without being fully deconfounded. The allowed claim is that shared anchors support a structured truth-DepMap bridge. The disallowed claim is that any single anchor, or the anchor set as a whole, proves a fully deconfounded bridge (Fig. 2g,h).

### Current entrants reveal a backbone-separation trade-off

Having fixed the truth object, we evaluated model recovery in HCC38 and HCC1143. The formal comparison included a shared-mean baseline, GEARS, scGPT, Geneformer, low-rank linear controls and pretrained-embedding ridge controls. Model recovery was evaluated using canonical backbone recovery, shift-excess identification and structure-versus-context separation (Fig. 3a,b).

The shared-mean baseline achieved the strongest backbone recovery score (0.807), exceeding the formal GEARS recipe (0.660). In contrast, GEARS exceeded the baseline in structure-versus-context separation (0.428 versus 0.353). This pattern was not a symmetric model-versus-baseline split; it showed a directional trade-off. The baseline better recovered the shared canonical backbone, whereas GEARS was more separation- or deviation-biased (Fig. 3c,d).

Foundation-model entrants and embedding-based controls did not reverse this conclusion. Geneformer performed more strongly than scGPT within the foundation-model family, and the Geneformer-ridge control retained more signal than the scGPT-ridge control, but neither displaced the shared-mean baseline as the backbone primary reference. These results indicate that the main failure mode is not merely absence of complex features or pretrained embeddings. Current entrants recover only part of the frozen architecture and do not establish model recovery beyond the baseline (Fig. 3e-h).

### Recipe and embedding controls do not close the backbone gap

We then tested whether the GEARS result reflected a missing recipe rather than a structural limitation. A finite backbone sweep varied only predefined recipe dimensions, including epoch/checkpoint, learning rate and weight decay. No sweep candidate approached the shared-mean baseline in backbone recovery. The best sweep candidate for backbone recovery scored 0.643, below both the formal GEARS recipe and the shared-mean baseline. Several candidates increased structure-versus-context separation or shift-excess identification, but these gains did not translate into backbone superiority (Fig. 4a-c).

The sweep therefore met the frozen stop rule: if limited recipe variation does not close the backbone gap, GEARS should not be advanced as the HCC38/HCC1143 primary winner. Instead, its role is to diagnose an architecture trade-off. This interpretation is strengthened by linear controls. Low-rank and pretrained-embedding ridge models tested whether simpler decoders or frozen embeddings could recover the backbone direction. These controls achieved complete target coverage, but still did not exceed the shared-mean baseline in backbone recovery (Fig. 4b,c; Extended Data Fig. 5).

Together, the sweep and control analyses make the simplest counterargument less plausible. The gap is not well explained by a missing small recipe, incomplete target coverage or failure to include pretrained target embeddings. The pattern is consistent with a direction-level or task-structure mismatch: the dominant shared backbone is already captured strongly by the baseline, while complex entrants add signal primarily in separation or deviation-related components; the bounded wording is now stated in the Fig. 4 caption rather than as a separate panel.

### Axis-level interpretation is informative but remains partial

We next asked whether the truth object could be interpreted at the biological-axis level. Axis-level analysis decomposed the bridge into transcriptomic and dependency explanatory strengths. The strongest qualified formal axis was transcription/chromatin, which showed transcriptomic-heavy behavior with shift R2 = 0.092, dependency R2 = 0.000 and targets ENY2 and TADA3 (Extended Data Fig. 11).

Additional axes showed partial support, including chromatin remodeling, TGF-beta/BMP signaling, ER stress/UPR, RNA processing/spliceosome, ribosome biogenesis/nucleolar and ribosomal/translation axes. These axes were supported by varying combinations of enrichment evidence, database support, per-target consistency and bootstrap stability. However, support was uneven, and many axes remained preliminary or mixed rather than formal primary evidence (Extended Data Fig. 11).

The axis layer therefore provides interpretation, not closure. The allowed wording is that transcription/chromatin is a primary but qualified axis and that broader axes are partially supported. The disallowed wording is that the project has established a fully closed shared explanatory architecture.

### Covariate, temporal and endpoint analyses define the final boundary

To evaluate whether the bridge claims were robust to available design and quality covariates, we performed a multi-axis covariate audit. The audit included barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes. This analysis retained the global bridge claim but prevented fully deconfounded wording (Fig. 5a,b).

The barcode gem group analysis illustrates the resulting boundary. Current metadata support writing barcode gem group as a design-proxy axis: HCC38 maps to aggrMH001-3 and HCC1143 maps to aggrMH004-6. The evidence does not resolve individual MH001-MH006 run labels, and the bridge cannot be described as fully deconfounded at the run level (Fig. 5c).

We also examined external architecture recurrence using the GSE90063 K562 7d/13d temporal panel. Both time points supported a backbone-plus-shift-excess architecture form. The 7d panel showed stronger rank alignment, whereas 13d showed larger mean shift, indicating temporal stratification rather than a monotonic later-timepoint improvement. Under the A0/A1/B tiering system, K562 supports architecture-form confirmation and bridge-form support, but not content-level replication or a primary co-pillar conclusion (Fig. 5c,d).

Finally, we compared CRISPR DepMap and RNAi DEMETER2 dependency endpoints across HCC38, HCC1143, K562 7d and K562 13d. CRISPR bridge Spearman was consistently stronger than RNAi: 0.726 versus 0.276 in HCC38, 0.779 versus 0.384 in HCC1143, 0.733 versus 0.333 in K562 7d and 0.515 versus 0.300 in K562 13d. CRISPR-RNAi endpoint agreement was lower in the HCC38/HCC1143 contexts than in K562, indicating context-dependent cross-platform robustness. Thus, CRISPR DepMap is the formal primary bridge readout, whereas RNAi DEMETER2 is a weaker cross-platform sensitivity endpoint (Fig. 5c,d).

## Discussion

This study reframes perturbation-model benchmarking around a prior truth object rather than a posterior leaderboard. By defining a fitness-relevant transcriptomic bridge before model comparison, the benchmark asks whether models recover a structured architecture that connects perturbation response to dependency. This framing revealed a robust but bounded result: the truth-DepMap bridge is structurally retained, but current entrants do not stably recover the frozen architecture beyond a strong shared-backbone baseline.

The model-side result is most naturally interpreted as a backbone-separation trade-off. The shared-mean baseline is not a weak placeholder; in this task, it captures a dominant shared canonical backbone. GEARS contributes a different kind of structure, showing stronger separation of structure and context, but this advantage does not become superior backbone recovery. Foundation-model entrants and embedding-based linear controls also fail to overturn the baseline reference. This does not imply that complex perturbation models have no value. It indicates that their current advantages are not aligned with the strongest backbone component of this frozen fitness-bridge architecture.

The truth-side result is similarly bounded. PFDN5, PMF1, PRPF6 and ZNF131 are meaningful shared anchors because they jointly occupy high transcriptomic-impact and high-dependency regions and remain stable under cutoff sensitivity. Yet the covariate audit prevents these objects from being written as clean, fully deconfounded primary anchors. This distinction is central to the manuscript: structural stability supports the bridge, but it does not eliminate design or quality-related uncertainty.

The external and endpoint analyses further constrain interpretation. K562 provides supplementary evidence that the architecture form can recur outside the HCC38/HCC1143 primary breast-cancer cell-line contexts, but it does not establish content-level replication because the target set, macro-class composition and bridgeable target count differ from the HCC38/HCC1143 benchmark object. RNAi DEMETER2 provides a useful sensitivity endpoint, but it is consistently weaker than matched CRISPR DepMap endpoints and cannot replace the primary bridge readout.

Several limitations follow directly from these boundaries. First, available experimental design metadata limit covariate closure; barcode gem group can be treated as a design proxy, but not as a fully resolved run-level covariate. Second, axis-level interpretation remains partial. Transcription/chromatin is the strongest qualified formal axis, whereas most other axes remain supporting or preliminary. Third, the K562 temporal panel has limited bridgeable target counts and should be read as supplementary architecture-form support. Fourth, the current benchmark does not prove biological mechanism recovery by any model. It provides a structured adjudication framework and shows where current entrants succeed or fail within it.

Overall, the benchmark establishes a defensible claim: fitness-relevant transcriptomic bridge architectures can be defined, decomposed and audited, but current perturbation-response entrants show only partial recovery and remain bounded by a backbone-separation trade-off.

## Methods Overview

### Truth-DepMap bridge construction

For each HCC38/HCC1143 breast-cancer cell-line context, perturbation-level transcriptomic truth was summarized using `real_shift_mean_abs`. DepMap dependency endpoints were direction-aligned so that larger values represented stronger dependency or liability. Targets were stratified by transcriptomic shift and aligned dependency strength into high, middle and low bins, defining Q1 anchors, transcriptomic-excess targets, dependency-excess targets, low-information targets and middle-band targets.

### Anchor tiering

Shared anchors were defined by recurrent high-shift/high-dependency behavior across HCC38 and HCC1143, followed by cutoff sensitivity analysis. Anchor claim strength was assigned using structural recurrence, cutoff stability and covariate-aware claim governance. PFDN5 was retained as primary but qualified; PMF1, PRPF6 and ZNF131 were retained as supporting-only anchors.

### Model recovery adjudication

Model predictions were evaluated against the frozen truth architecture using three primary metrics: backbone recovery, shift-excess identification and structure-versus-context separation. Entrants included GEARS, scGPT, Geneformer, low-rank linear controls and pretrained-embedding ridge controls. A shared-mean baseline and a null model served as references.

### GEARS sweep and controls

The GEARS sweep varied only predefined recipe parameters and was evaluated under the same frozen scoring system. Linear controls tested whether low-rank structure or pretrained target embeddings could recover the backbone direction. The stop rule required stopping model-winner escalation if no finite-budget recipe closed the backbone gap to the shared-mean baseline.

### Axis-level analysis

Axis-level explanatory strength was computed separately for transcriptomic shift and dependency. Formal axis interpretation required sufficient target count and was evaluated with enrichment support, per-target consistency and bootstrap stability. Axis evidence was used for interpretation and tiering, not as a replacement for target-level bridge evidence.

### Covariate audit

Covariate audit included barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes. Barcode gem group was treated as a design-proxy axis rather than a fully resolved run-level covariate. Covariate audit governed wording strength and did not claim complete deconfounding.

### K562 temporal panel

The GSE90063 K562 7d/13d temporal panel was used as supplementary external evidence. The 13d panel was treated as the primary formal supplementary bridge test and the 7d panel as a temporal sensitivity or early-bridge probe. Evidence was assigned to A0 architecture-form confirmation, A1 bridge-form support or B content-level not eligible tiers.

### Endpoint hierarchy

CRISPR DepMap and RNAi DEMETER2 endpoints were compared across HCC38, HCC1143, K562 7d and K562 13d. Bridge Spearman values and CRISPR-RNAi endpoint agreement were used to establish endpoint hierarchy. CRISPR DepMap was retained as the primary bridge readout; RNAi DEMETER2 was retained as a weaker cross-platform sensitivity endpoint.

## Figure Plan

The complete figure plan is fixed in:

- `docs/manuscript_complete_figure_plan_v1.md`

All figure panels will be generated as reproducible panel-level artifacts. Each panel will have its own PNG, PDF, source-data table and manifest recording input files, SHA256 hashes, output hashes, script path and claim boundary. Whole-figure assemblies will also record combined source-data hashes, output hashes and git status. GEARS training is exempt from rerunning during figure production because of runtime cost; GEARS-related figures will instead cite frozen prediction, scoring and sweep artifacts with recorded hashes.

The planned main figures are:

1. Fig. 1: truth-first bridge object.
2. Fig. 2: shared anchor tiering.
3. Fig. 3: model recovery trade-off.
4. Fig. 4: sweep and embedding controls.
5. Fig. 5: covariate, temporal and endpoint boundary.
6. Extended Data Fig. 11: axis-level partial interpretation.

The manuscript is compressed to five main figures by moving axis-level interpretation to Extended Data and retaining the boundary figure in the main text.

## Claim Boundaries

The manuscript must not claim:

- model recovery proved;
- GEARS overall winner;
- fully deconfounded anchors;
- fully established shared explanatory architecture;
- K562 primary co-pillar;
- content-level replication confirmed;
- broad cross-context validation;
- RNAi primary evidence;
- external model-side generalization proved;
- discovery as a current formal primary deliverable.
