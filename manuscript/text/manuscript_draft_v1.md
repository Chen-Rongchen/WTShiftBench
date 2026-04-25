# Genome Biology manuscript draft v1

## Article type

Research

## Title page

### Title

A truth-anchored framework and resource for evaluating transcriptomic perturbation models against cancer dependency endpoints

### Authors

[Author names to be inserted]

### Affiliations

[Institutional addresses to be inserted]

### Corresponding author

[Corresponding author name and email to be inserted]

## Abstract

### Background

A central challenge in perturbation-model evaluation is that expression reconstruction does not by itself define the phenotype-relevant object a model should recover, potentially conflating transcriptional fit with phenotype-relevant structure.

### Results

We built a truth-first, architecture-aware framework and resource that freezes a phenotype-aligned benchmark object before model comparison. Real perturbation transcriptomic shifts were aligned with CRISPR DepMap dependency to define a fixed truth bridge, and model predictions were then adjudicated against this frozen architecture. In the breast-cancer cell-line contexts HCC38 and HCC1143, the bridge was supported by recurrent target-level anchors and bounded axis-level evidence rather than by a single global correlation. Architecture-aware adjudication decomposed recovery into backbone recovery, shift-excess identification and structure-versus-context separation, revealing a structured trade-off rather than a single leaderboard result: the shared-mean baseline was strongest for canonical backbone recovery, whereas GEARS retained stronger structure-versus-context separation. K562 temporal analyses supported bounded external recurrence of architecture form, whereas RNAi DEMETER2 provided a weaker cross-platform sensitivity endpoint than CRISPR DepMap.

### Conclusions

This resource provides a reproducible framework for phenotype-aligned perturbation-model adjudication and can support future extension across cell-line contexts, endpoints and entrants while preserving explicit claim boundaries.

## Keywords

Perturb-seq; functional genomics; cancer dependency; DepMap; single-cell transcriptomics; perturbation modeling; benchmarking; GEARS; foundation models; reproducibility

## Background

Perturbation-model benchmarks need a phenotype-relevant recovery object, not only a prediction score. Single-cell perturbation profiling has made it possible to observe how genetic perturbations reshape transcriptomic state at scale [1-3]. These datasets have supported graph neural networks, single-cell foundation models and embedding-based decoders that aim to predict expression responses to perturbation [4-7]. Such models are commonly assessed by expression-level reconstruction accuracy or local agreement with observed transcriptional shifts. These metrics are necessary but incomplete: they do not directly test whether a model recovers transcriptomic structures that are relevant to downstream cellular phenotypes such as fitness, dependency or liability, and may therefore mis-rank models when transcriptional fit and phenotype-relevant structure diverge.

The first design problem is therefore object definition. A perturbation response can contain a shared backbone that is recurrent across cell contexts and context-specific deviations that are only partially captured by global expression-level summaries. Within this structure, interpretable axes of variation may emerge, but these need not be equally aligned with dependency. A model may recover one component while missing another. Conversely, a simple baseline may perform strongly on the dominant shared component when the evaluated object is dominated by shared structure. Without defining a frozen, phenotype-relevant benchmark truth object before model comparison, model leaderboards risk conflating expression reconstruction, endpoint alignment and content-level interpretation.

Prior perturbation-prediction benchmarks have already shown that expression-level recovery by deep learning or foundation-model entrants can be matched or exceeded by simple baselines [8-11]. These studies provide essential context for interpreting model-side results, but they ask a different question from the one addressed here in that they do not first freeze a phenotype-relevant benchmark object. They evaluate transcriptome prediction accuracy, whereas the present benchmark first freezes a phenotype-relevant truth object by aligning perturbation transcriptomic shifts to CRISPR DepMap dependency. Model recovery is then decomposed into backbone recovery, shift-excess identification and structure-versus-context separation. The resulting claim is not that complex models fail in a unidirectional sense, but that current entrants recover different parts of a frozen fitness-bridge architecture.

Cancer dependency resources provide an opportunity to make this evaluation more direct with respect to phenotype-relevant fitness readouts. CRISPR DepMap captures gene-level fitness effects across cancer cell lines and can be aligned with perturbation transcriptomic shifts [12]. RNAi DEMETER2 provides a related but weaker cross-platform sensitivity readout [13]. However, these endpoints are not interchangeable. Bridge claims therefore require explicit endpoint hierarchy and claim governance, such that evidence layers remain separated from causal or mechanistic overinterpretation.

We therefore built a truth-first, architecture-aware benchmark and resource for perturbation transcriptome models in cancer functional genomics. In the breast-cancer cell-line contexts HCC38 and HCC1143, real perturbation transcriptomic shifts were aligned to CRISPR DepMap dependency to define a frozen benchmark truth bridge before model evaluation. This bridge was organized into a structured target-level recovery object, with recurrent anchors and qualified axis-level interpretation, and was further bounded by covariate governance and endpoint hierarchy. Model predictions from GEARS, single-cell foundation-model entrants and linear controls were then evaluated against this frozen architecture. The study asks a narrow but important question: which components of a phenotype-relevant perturbation architecture are recovered by current transcriptome models, and which claims remain unsupported?

## Results

### A truth-anchored HCC38/HCC1143 breast-cancer benchmark defines the phenotype-relevant recovery object

We first defined the benchmark object independently of model predictions. For each HCC38/HCC1143 breast-cancer context, transcriptomic truth was summarized by the absolute mean perturbation shift and aligned with CRISPR DepMap dependency so that larger aligned values represented stronger dependency. Targets were assigned to pre-specified joint shift-dependency categories, including high-shift/high-dependency anchors, transcriptomic-excess targets, dependency-excess targets, low-information targets and a retained middle band (Fig. 1a,d; Extended Data Fig. 1,2).

Both breast-cancer cell-line contexts contained a high-shift/high-dependency anchor set. HCC38 contained 9 Q1 anchors and HCC1143 contained 10 Q1 anchors, with aligned Spearman rho values of 0.726 and 0.779, respectively (Fig. 1b,c,e; Extended Data Fig. 2). The resulting bridge was not treated as a single global correlation, but as a structured target-level recovery object whose categories, source data and interpretation boundary were fixed before model comparison.

### Shared anchor analysis separates recurrent structure from unqualified target claims

We next asked which target-level objects were recurrent across HCC38 and HCC1143. PFDN5, PMF1, PRPF6 and ZNF131 formed the most stable shared anchor set, repeatedly occupying the high-shift/high-dependency region and retaining shared-anchor status under cutoff sensitivity analysis (Fig. 2a-c; Extended Data Fig. 3).

However, recurrent structure alone did not justify unqualified target-level claims. After covariate-aware tiering, PFDN5 remained a primary but qualified anchor, whereas PMF1, PRPF6 and ZNF131 were retained as supporting-only anchors. ENY2, NPM1, RPS3, RUVBL2 and ZBTB17 were retained as supporting but cutoff-sensitive objects, indicating weaker structural stability than the core shared-anchor set (Fig. 2c; Extended Data Fig. 3). This tiering separates bridge support from target proof: shared anchors support the existence of a structured perturbation-fitness bridge, but no individual anchor is interpreted as fully deconfounded causal evidence (Fig. 2d,e).

### Model comparisons reveal a backbone-separation trade-off

After freezing the benchmark truth object, we evaluated recovery by the shared-mean baseline, GEARS, scGPT, Geneformer, low-rank linear controls and pretrained-embedding ridge controls. Models were scored across three dimensions: canonical backbone recovery, shift-excess identification and structure-versus-context separation (Fig. 3a,b; Extended Data Fig. 4).

The shared-mean baseline achieved the strongest backbone recovery score, 0.807, exceeding the prespecified formal GEARS recipe, 0.660. GEARS instead showed stronger structure-versus-context separation, 0.428 compared with 0.353 for the baseline. Shift-excess identification did not distinguish the formal baseline-GEARS comparison, with both scoring 0.333 (Fig. 3c,d). The difference was therefore not a simple model failure or success. It was a trade-off: under the present benchmark definition, the baseline recovered the dominant shared backbone more strongly, whereas GEARS retained stronger separation- or deviation-biased recovery.

Foundation-model entrants and embedding-based controls did not overturn this trade-off. Geneformer retained more recoverable structure than scGPT in this setting, and Geneformer-ridge exceeded other linear controls, but neither displaced the shared-mean baseline as the backbone reference (Fig. 3e-h; Extended Data Fig. 4). Current entrants therefore recovered different but incomplete components of the frozen perturbation-fitness architecture.

### GEARS recipe sweeps and embedding controls do not close the backbone gap

We then tested whether GEARS underperformance on backbone recovery reflected a missing small local recipe. A prespecified finite-budget neighborhood sweep varied epochs, learning rate and weight decay using a nearest-to-base selection rule. Six candidate recipes were materialized or re-used, including the base recipe and five one-parameter local variants. No sweep candidate closed the backbone gap to the shared-mean baseline. The best sweep candidate scored 0.643 for backbone recovery, below both the baseline and the formal GEARS recipe (Fig. 4a,b; Extended Data Fig. 5).

Some sweep candidates modestly improved shift-excess identification or structure-versus-context separation, but these gains did not become backbone superiority. The prespecified stop rule therefore retained GEARS as an architecture trade-off diagnosis rather than the HCC38/HCC1143 primary winner (Fig. 4a-c; Extended Data Fig. 5). Linear-control analyses led to the same trade-off interpretation. Low-rank and pretrained-embedding ridge controls achieved complete target coverage but did not exceed the shared-mean baseline in backbone recovery (Fig. 4b,c; Extended Data Fig. 5). The persistence of the gap after finite-budget recipe sweeps, linear controls and coverage audits is consistent with a task-structure or direction-level mismatch under the present benchmark definition, although it does not exclude other untested model-side factors; this bounded interpretation is stated in the Fig. 4 caption rather than as a separate panel.

### Axis-level decomposition provides qualified biological interpretation

We next decomposed the bridge at the axis level to test whether the target-level architecture had interpretable biological structure. The strongest qualified interpretive axis was transcription/chromatin. This axis showed transcriptomic-heavy behavior, with shift R2 = 0.092, dependency R2 near zero, and target support from ENY2 and TADA3 (Extended Data Fig. 11).

Other axes showed partial and non-uniform support, including chromatin remodeling, TGF-beta/BMP signaling, ER stress/UPR, RNA processing/spliceosome, ribosome biogenesis/nucleolar and ribosomal/translation axes. These axes showed heterogeneous support across enrichment evidence, database support, per-target consistency and bootstrap stability (Extended Data Fig. 11). Axis-level evidence therefore supports biological interpretation but not closure. Transcription/chromatin can be written as a primary but qualified interpretive axis, while the broader axis-level explanatory scaffold remains partial.

### Covariate, temporal and endpoint analyses define the claim boundary

We performed a covariate audit covering barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes. The audit retained the bridge-form claim but prevented fully deconfounded wording (Fig. 5a,b; Extended Data Fig. 9). Barcode gem group illustrates this boundary: HCC38 maps to aggrMH001-3 and HCC1143 maps to aggrMH004-6, but individual MH001-MH006 run labels are not resolved (Fig. 5c; Extended Data Fig. 9).

External recurrence was assessed using the GSE90063 K562 temporal panel. Both 7-day and 13-day panels supported recurrence of a backbone-plus-shift-excess architecture form. The 7-day panel had stronger rank alignment, whereas the 13-day panel had larger mean shift, supporting temporal stratification rather than monotonic improvement at the later time point (Fig. 5c; Extended Data Fig. 7). Under A0/A1/B tiering, the K562 panel supports architecture-form recurrence and bounded bridge-form support, but not content-level replication or a primary co-pillar conclusion (Fig. 5d; Extended Data Fig. 7).

Finally, CRISPR DepMap and RNAi DEMETER2 endpoints were compared across HCC38, HCC1143, K562 7d and K562 13d. CRISPR DepMap bridge Spearman exceeded RNAi DEMETER2 bridge Spearman in every context: 0.726 versus 0.276 in HCC38, 0.779 versus 0.384 in HCC1143, 0.733 versus 0.333 in K562 7d and 0.515 versus 0.300 in K562 13d (Fig. 5c; Extended Data Fig. 8). CRISPR DepMap was therefore retained as the primary bridge readout, whereas RNAi DEMETER2 was retained as a weaker cross-platform sensitivity endpoint (Fig. 5d).

## Discussion

This study presents a truth-anchored benchmark for evaluating perturbation transcriptome models against CRISPR DepMap-anchored cancer dependency readouts. The central design choice is to define the phenotype-relevant recovery object before model comparison. This separates three questions that are often conflated: whether a perturbation-to-dependency bridge exists, which targets and axes provide qualified support for that bridge, and whether model predictions recover the frozen architecture.

The model-side result is a backbone-separation trade-off. The shared-mean baseline captures the dominant shared-backbone component more strongly than the formal GEARS recipe, while GEARS shows stronger structure-versus-context separation. Foundation-model entrants and embedding-based controls do not reverse this ordering. This does not mean that complex perturbation models are uninformative. Rather, it specifies that their current advantages are misaligned with the dominant shared-backbone component of the present HCC38/HCC1143 fitness-bridge benchmark.

The strength of the shared-mean baseline is informative rather than artifactual. The baseline was used as a frozen-architecture backbone reference rather than as a deployable predictive model: it was constructed from the canonical-backbone transcriptomic component and did not use DepMap dependency values, RNAi endpoints or model-side scoring outcomes to generate target-specific predictions. Control subsampling showed stable truth-DepMap bridge estimates in both HCC38/HCC1143 contexts, and embedding-based controls achieved complete target coverage without closing the backbone gap. Thus, the results support the interpretation that, under the present benchmark definition, the cross-context canonical backbone is the most consistently recoverable component of the HCC38/HCC1143 truth object. GEARS and Geneformer retain recoverable structure in separation- or shift-excess-related dimensions, but this recovery does not displace the baseline for primary backbone recovery.

The truth-side result is also deliberately bounded. Shared anchors such as PFDN5, PMF1, PRPF6 and ZNF131 support the bridge structurally because they occupy recurrent high-shift/high-dependency regions and remain stable under cutoff sensitivity. However, covariate-aware tiering prevents these anchors from being written as clean, fully deconfounded primary target proofs. Similarly, transcription/chromatin is the strongest qualified interpretive axis, but axis-level interpretation remains partial.

External and endpoint analyses further constrain the claim. K562 temporal data support bounded recurrence of the architecture form outside the HCC38/HCC1143 primary breast-cancer contexts, but do not provide content-level replication because the target set, macro-class composition and bridgeable target count differ from the HCC38/HCC1143 benchmark. RNAi DEMETER2 provides useful cross-platform sensitivity evidence, but is consistently weaker than CRISPR DepMap and cannot replace it as the primary endpoint.

Several limitations follow directly from these boundaries. First, the primary evidence is based on two breast-cancer cell lines, HCC38 and HCC1143, and a limited shared-anchor set, so bridge content is treated as qualified rather than as broad biological generalization. Second, barcode gem group is available as a design-proxy axis but not as fully resolved run-level metadata; design-proxy rank residualization did not overturn the bridge or primary anchor structure, but residual design or batch confounding cannot be fully excluded. Third, the K562 temporal panel supports architecture-form recurrence but not content-level replication because the target set, macro-class composition and bridgeable target count differ from the HCC38/HCC1143 benchmark. Fourth, RNAi DEMETER2 is retained only as a cross-platform sensitivity endpoint and is not a matched primary endpoint. The GEARS sweep was a finite neighborhood test and did not exhaust all possible model recipes, although it was sufficient for the prespecified stop rule. GEARS training was not rerun during figure production; frozen predictions and scoring artifacts were used for reproducibility. The benchmark does not prove mechanism recovery by any model. Instead, it provides a reproducible adjudication framework for assessing which components of a functional-genomic perturbation architecture are recovered, missed or only partially supported.

## Conclusions

Perturbation transcriptome models should be evaluated against phenotype-relevant truth objects, not only expression reconstruction metrics. In the breast-cancer cell-line contexts HCC38 and HCC1143, a structured perturbation-to-CRISPR-DepMap bridge can be defined and audited before model comparison. Current entrants recover different but incomplete parts of this architecture: the shared-mean baseline is strongest for canonical backbone recovery, whereas GEARS retains stronger structure-versus-context separation. Anchor and axis analyses provide qualified content- and interpretation-level support, whereas temporal and endpoint analyses define the outer claim boundary. The resulting benchmark and accompanying source-data manifests provide a bounded, phenotype-aligned resource for functional-genomic evaluation of future perturbation models.

## Methods

### Study aim, design and setting

The aim was to build and apply a phenotype-relevant benchmark for perturbation transcriptome model evaluation in cancer functional genomics. The design was retrospective and computational. Real perturbation transcriptomic shifts in the breast-cancer cell-line contexts HCC38 and HCC1143 were aligned with CRISPR DepMap dependency to define a frozen benchmark truth object. Model predictions were evaluated only after that object and its claim boundaries were fixed.

### Datasets and endpoint alignment

HCC38 and HCC1143 breast-cancer cell lines were used as the primary benchmark contexts. Transcriptomic truth was summarized at the perturbation-target level using absolute mean perturbation shift. For each context, single-cell expression was library-size normalized to a target sum of 10,000 and log1p transformed. For target \(p\), the perturbation shift vector was the difference between the mean log-normalized expression vector of cells assigned to \(p\) and the mean vector of matched control cells. The absolute mean perturbation shift, stored as `real_shift_mean_abs`, was the mean of the absolute values of this vector across gene-expression features. This quantity was used as a truth-side perturbation magnitude summary, not as a model expression-reconstruction score.

Primary bridge analyses used CRISPR DepMap dependency as the matched fitness endpoint. To maintain a consistent larger-is-stronger semantic convention across bridge summaries, targets with larger aligned values were interpreted as showing stronger dependency or liability. In the primary bridge layer, this alignment was applied to the prespecified CRISPR DepMap dependency variable used for target ranking, binning and bridge construction. In gene-effect sensitivity analyses, sign orientation was harmonized by applying the prespecified sign flip used in the frozen pipeline so that larger values again represented stronger dependency-like sensitivity. Direction alignment standardized interpretation only; it did not create a new endpoint, alter endpoint identity or render CRISPR DepMap and RNAi DEMETER2 interchangeable.

RNAi DEMETER2 was used only as a weaker cross-platform sensitivity endpoint. The GSE90063 K562 7d/13d temporal panel was used as supplementary external architecture-form evidence. An earlier legacy object distributed under a `dixit_2016_raw` filename did not match the GSE90063 K562 TF-pool description and was excluded before analysis. All Dixit/K562 evidence in this study was derived de novo from GSE90063 7d and 13d data.

### Truth-DepMap bridge construction

For each HCC38/HCC1143 breast-cancer context, targets with matched perturbation truth and DepMap dependency were ranked separately by `real_shift_mean_abs` and aligned `depmap_gene_dependency`. Within each context, rank percentiles at or below 0.25 were assigned to the low bin, rank percentiles at or above 0.75 were assigned to the high bin, and the remaining targets were assigned to the middle bin. Joint categories were then assigned from the two-dimensional grid: high-shift/high-dependency targets were Q1 anchors; high-shift/low-dependency targets were transcriptomic-excess targets; low-shift/high-dependency targets were dependency-excess targets; low-shift/low-dependency targets were low-information targets; all other observed combinations were retained as the middle band. The middle band was retained as part of the benchmark object rather than discarded as noise. The target grid, Q1 anchor counts and category composition were frozen before model comparison, and the categories were used as benchmark-structure labels rather than target-proof or causal labels.

The headline bridge strength (Fig. 1f) was reported in two separate components. First, for each primary context the point estimate was the aligned Spearman rho between `real_shift_mean_abs` and `depmap_gene_dependency` on the matched target-level pairs (n = 47 for HCC38, n = 48 for HCC1143). Sampling uncertainty of the point estimate was summarized by a closed-form Fisher z-transform 95% confidence interval computed from \(z = \mathrm{arctanh}(\rho)\) with standard error \(1/\sqrt{n-3}\), back-transformed by \(\tanh\); this quantity, stored in the panel source data as `ci_method = fisher_z_transform`, describes the precision of the point itself and is not a bootstrap. Second, the null reference envelope was obtained by permuting the target-to-DepMap pairing within each context 1000 times under a fixed random seed, recomputing the aligned Spearman rho on each permutation, and reporting the 2.5% and 97.5% quantiles of the resulting null distribution together with the empirical two-sided p value (p = 0.001 in each context). The point-level CI and the null envelope are distinct quantities and are reported together only to show that the observed bridge strength lies outside the rho = 0 permutation envelope. This pre-specified definition of bridge strength was used only to establish that the recovery object is structured above the permutation null; it was not used as a model adjudication metric.

### Anchor tiering and sensitivity analysis

Target-level anchor wording was governed by a rule-based tiering procedure rather than by post hoc narrative interpretation. For each candidate anchor, the evidence inputs considered were: structural recurrence across the primary HCC38 and HCC1143 contexts, defined by recurrent occupancy of the high-shift/high-dependency region under the prespecified joint shift-dependency assignment; cutoff sensitivity, assessed by whether shared-anchor status was retained under the prespecified cutoff sensitivity analyses; stability under control subsampling where applicable; and covariate-aware governance, based on the covariate audit and its implications for wording strength.

These evidence inputs were used to assign wording tiers rather than to rank biological importance. Targets that showed recurrent high-shift/high-dependency behavior with stronger structural stability but remained subject to residual covariate or design-proxy limitations were retained as primary but qualified anchors. Targets that supported the bridge structure but lacked sufficient stability or admissibility for stronger wording were retained as supporting-only anchors. Targets that showed supporting evidence but whose status depended materially on cutoff choice were retained as supporting but cutoff-sensitive objects. No target-level tier was interpreted as fully deconfounded causal proof.

This tiering procedure separates bridge support from target proof. Recurrent anchors support the existence of a structured perturbation-fitness bridge, but target-level wording remains capped by stability and governance constraints. Accordingly, target tiers should be interpreted as claim-strength assignments within the present benchmark, not as definitive biological truth rankings.

### Model recovery adjudication

Model predictions were evaluated against the frozen truth architecture using three dimensions: canonical backbone recovery, shift-excess identification and structure-versus-context separation. Predictions were first projected onto the frozen target-axis architecture: for each target and each fine axis, the projected axis magnitude was the mean absolute predicted shift across genes assigned to that axis. Canonical backbone recovery was the mean rank-percentile recovery of the expected axis among targets whose expected axis was labeled `canonical_backbone` in the truth architecture contract. Shift-excess identification was the pairwise superiority probability that expected-axis projected magnitude for `shift_excess` targets exceeded expected-axis projected magnitude for `canonical_backbone` targets, with ties counted as 0.5. Structure-versus-context separation was the mean, across targets, of the expected-axis magnitude divided by the sum of expected-axis magnitude and mean off-axis magnitude. All three scores were oriented so that larger values indicated stronger recovery of that component.

Entrants included GEARS, scGPT, Geneformer, low-rank linear controls and pretrained-embedding ridge controls. A shared-mean baseline and a null model served as references. The `shared_mean_baseline` was constructed within each primary HCC context by averaging the truth-aligned log-shift vectors of targets assigned to the `canonical_backbone` component and assigning that same mean vector to every frozen target. The null model assigned a zero shift vector to every target. The shared-mean baseline therefore served as a frozen canonical-backbone reference, not as a deployable perturbation model and not as a dependency-informed predictor. The primary model-side claim was based on joint interpretation of the three recovery dimensions against the frozen HCC38/HCC1143 architecture rather than expression prediction alone.

### GEARS finite-budget sweep and prespecified stop rule

The GEARS recipe audit was a prespecified finite-budget neighborhood sweep around the frozen formal GEARS recipe rather than an exhaustive hyperparameter search. The parent configuration allowed variation only in epochs (20, 30 or 40), learning rate (0.0005, 0.001 or 0.002) and weight decay (0.000001 or 0.00001), with `materialization_export_sanity` fixed to `default_only`. Under the prespecified nearest-to-base selection rule, candidate recipes were restricted to the base recipe and the nearest eligible one-parameter local variants within this neighborhood, yielding six materialized or re-used candidates in total. The truth object, model architecture, adjudication space and scoring system were held fixed throughout the sweep.

The sweep was designed as a local rebuttal test of whether the backbone-recovery gap could be closed by small recipe changes. The prespecified stop rule was that GEARS would not be promoted to the HCC38/HCC1143 primary winner unless a finite-budget candidate closed the backbone-recovery gap to the `shared_mean_baseline`. Because no candidate satisfied this criterion, GEARS was retained as an architecture trade-off diagnosis rather than as the HCC38/HCC1143 primary winner. GEARS training was not rerun during figure production; frozen predictions, scoring tables and sweep artifacts were reused and recorded with hashes for reproducibility.

### Linear and foundation-model controls

Low-rank linear controls and pretrained-embedding ridge controls were used to test whether backbone recovery was limited by target coverage or by a missing embedding-level representation. Coverage audits were performed for embedding-based controls. Geneformer-ridge, scGPT-ridge and low-rank controls were compared under the same frozen recovery metrics as GEARS and the shared-mean baseline.

### Axis-level analysis

Axis-level explanatory strength was computed separately for transcriptomic shift and dependency. Axis interpretation used enrichment evidence, database support, per-target consistency and bootstrap stability. Axis-level evidence was used for interpretation and claim tiering, not as a replacement for target-level bridge evidence.

### Covariate audit

The covariate audit included barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes. Barcode gem group was treated as a design-proxy axis rather than a fully resolved run-level covariate. Covariate evidence governed wording strength and prevented fully deconfounded target claims.

### K562 temporal panel analysis

The GSE90063 K562 7d/13d temporal panel was evaluated as supplementary evidence using a prespecified three-level evidence scheme: A0, A1 and B. This tiering was designed to distinguish architecture-form recurrence, bridge-form support and content-level admissibility.

A0, architecture-form recurrence, was assigned when the K562 panel supported recurrence of the benchmark architecture form, operationalized here as recurrence of the backbone-plus-shift-excess structure under the frozen truth-side framework. A0 addresses whether the architectural form observed in the primary HCC38/HCC1143 contexts is detectable in the supplementary K562 context; it does not require shared target identity or content-level convergence.

A1, bounded bridge-form support, was assigned when the K562 panel further showed support for a bridge-form relationship to the matched primary endpoint framework, while remaining weaker or more limited than the HCC38/HCC1143 primary evidence. A1 therefore supports the claim that the recurrent architecture form remains bridge-relevant in the supplementary context, but does not establish symmetric external validation or co-primary status.

B, content-level not eligible, was assigned when the supplementary K562 evidence was not admissible for content-level replication claims. This applied when target-set composition, macro-class composition, bridgeable target count or related context differences prevented direct elevation of K562 results into shared target-level or axis-level replication claims. Under this rule, K562 could support architecture-form recurrence and bounded bridge-form support while remaining ineligible for content-level convergence or primary co-pillar interpretation.

Within this framework, the 13-day panel was treated as the formal supplementary K562 bridge test and the 7-day panel as a temporal sensitivity or early-bridge probe. Differences between 7-day and 13-day readouts were interpreted as temporal stratification within the supplementary context rather than as monotonic strengthening at the later time point.

### Endpoint hierarchy

CRISPR DepMap and RNAi DEMETER2 endpoints were compared across HCC38, HCC1143, K562 7d and K562 13d. Bridge Spearman values and CRISPR-RNAi endpoint agreement were used to assign endpoint hierarchy. CRISPR DepMap was retained as the primary bridge readout. RNAi DEMETER2 was retained as a weaker cross-platform sensitivity endpoint.

### Reproducibility and software

All main and Extended Data figures were generated as panel-level artifacts. Each panel has PNG, PDF, source-data TSV and manifest JSON outputs. Each manifest records input files, SHA256 hashes, output hashes, script path, generation time, git status and claim boundary. Whole-figure assemblies have combined source-data tables and figure-level manifests. The main figure package can be rebuilt with:

```bash
pixi run --environment core python scripts/manuscript/build_all_main_figures.py
pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py
pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py
pixi run --environment core python scripts/manuscript/build_submission_package.py
```

### Use of artificial intelligence tools

Draft organization, wording review and editorial checklist preparation were assisted by a large language model. All analyses, generated files, data interpretation and final manuscript wording were reviewed and remain the responsibility of the authors. No large language model is listed as an author.

## Abbreviations

CRISPR: clustered regularly interspaced short palindromic repeats; DEMETER2: gene-level RNA interference dependency correction model; DepMap: Cancer Dependency Map; GEARS: graph-enhanced gene activation and repression simulator; HCC38/HCC1143: breast-cancer cell-line contexts used as the primary benchmark contexts; RNAi: RNA interference; TSV: tab-separated values; UMI: unique molecular identifier.

## Declarations

### Ethics approval and consent to participate

Not applicable. This study used existing cell-line and publicly available or previously generated functional-genomic datasets and did not involve new human participant recruitment, human tissue collection or animal experiments.

### Consent for publication

Not applicable.

### Availability of data and materials

The datasets supporting the conclusions of this article are included within the article and its additional files. Main figure source data are provided under `reports/manuscript_figures_v2/`; Extended Data source data are provided under `reports/manuscript_extended_data_v1/`; supplementary table indexes and file hashes are provided under `reports/manuscript_supplementary_tables_v1/`; and the submission package manifest is provided under `reports/manuscript_submission_package_v1/`. Public repository links, accession identifiers and archived DOI links will be inserted before submission.

### Competing interests

[To be completed by the authors.]

### Funding

[To be completed by the authors.]

### Authors' contributions

[To be completed by the authors.]

### Acknowledgements

[To be completed by the authors.]

### Authors' information

Not applicable.

## References

1. Dixit A, Parnas O, Li B, Chen J, Fulco CP, Jerby-Arnon L, et al. Perturb-Seq: dissecting molecular circuits with scalable single-cell RNA profiling of pooled genetic screens. Cell. 2016;167:1853-1866.e17. doi:10.1016/j.cell.2016.11.038.

2. Replogle JM, Saunders RA, Pogson AN, Hussmann JA, Lenail A, Guna A, et al. Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq. Cell. 2022;185:2559-2575.e28. doi:10.1016/j.cell.2022.05.013.

3. Peidli S, Green TD, Shen C, Gross T, Min J, Buettner F, et al. scPerturb: harmonized single-cell perturbation data. Nat Methods. 2024;21:531-540. doi:10.1038/s41592-023-02144-y.

4. Roohani Y, Huang K, Leskovec J. Predicting transcriptional outcomes of novel multigene perturbations with GEARS. Nat Biotechnol. 2024;42:927-935. doi:10.1038/s41587-023-01905-6.

5. Cui H, Wang C, Maan H, Pang K, Luo F, Duan N, et al. scGPT: toward building a foundation model for single-cell multi-omics using generative AI. Nat Methods. 2024;21:1470-1480. doi:10.1038/s41592-024-02201-0.

6. Theodoris CV, Xiao L, Chopra A, Chaffin MD, Al Sayed ZR, Hill MC, et al. Transfer learning enables predictions in network biology. Nature. 2023;618:616-624. doi:10.1038/s41586-023-06139-9.

7. Hao M, Gong J, Zeng X, Liu C, Guo Y, Cheng X, et al. Large-scale foundation model on single-cell transcriptomics. Nat Methods. 2024;21:1481-1491. doi:10.1038/s41592-024-02305-7.

8. Ahlmann-Eltze C, Huber W, Anders S. Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear baselines. Nat Methods. 2025;22:1657-1661. doi:10.1038/s41592-025-02772-6.

9. Wong DR. Simple controls exceed best deep learning algorithms and reveal foundation model effectiveness for predicting genetic perturbations. Bioinformatics. 2025;41:btaf317. doi:10.1093/bioinformatics/btaf317.

10. Wei Z, Wang Y, Gao Y, Wang S, et al. Benchmarking algorithms for generalizable single-cell perturbation response prediction. Nat Methods. 2026;23:451-464. doi:10.1038/s41592-025-02980-0.

11. Kedzierska KZ, Crawford L, Amini AP, Lu AX, et al. Zero-shot evaluation reveals limitations of single-cell foundation models. Genome Biol. 2025;26:101. doi:10.1186/s13059-025-03574-x.

12. Meyers RM, Bryan JG, McFarland JM, Weir BA, Sizemore AE, Xu H, et al. Computational correction of copy-number effect improves specificity of CRISPR-Cas9 essentiality screens in cancer cells. Nat Genet. 2017;49:1779-1784. doi:10.1038/ng.3984.

13. McFarland JM, Ho ZV, Kugener G, Dempster JM, Montgomery PG, Bryan JG, et al. Improved estimation of cancer dependencies from large-scale RNAi screens using model-based normalization and data integration. Nat Commun. 2018;9:4610. doi:10.1038/s41467-018-06916-5.

## Additional files

Additional file 1: `.xlsx`; Supplementary Tables workbook. This workbook contains the frozen supplementary tables supporting the main and Extended Data figures.

Additional file 2: `.json`; Submission package manifest. This manifest records the submission package file inventory and hashes.

Additional file 3: `.tsv`; Submission package file manifest. This table provides a reviewer-readable index of the files included in the submission package.
