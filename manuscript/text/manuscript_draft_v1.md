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

Expression-level prediction accuracy does not by itself define the phenotype-relevant object a perturbation model should recover, and prior benchmarks have shown that simple baselines can match or exceed deep-learning entrants on expression reconstruction [8-11]. This creates a design problem: without a pre-defined phenotype-aligned truth object, model comparison risks conflating transcriptional fit with fitness-relevant structure.

### Results

We present a truth-first, architecture-aware framework for perturbation-model evaluation in cancer functional genomics. The framework defines a phenotype-aligned recovery object before model comparison by aligning perturbation transcriptomic shifts to CRISPR DepMap dependency endpoints, decomposes model recovery into three architecture-aware dimensions (backbone recovery, shift-excess identification, and structure-versus-context separation), and governs all claims through pre-specified category rules, covariate-aware evidence tiering, finite-budget rebuttal tests, and explicit claim-boundary language (A0/A1/B). We demonstrate the framework in the breast-cancer cell-line contexts HCC38 and HCC1143. The perturbation-to-dependency bridge was structurally supported above permutation null (aligned Spearman rho = 0.726 and 0.779, empirical p = 0.001) and was organized by recurrent target-level anchors (PFDN5 primary but qualified; PMF1, PRPF6, ZNF131 supporting-only after covariate-aware tiering) rather than by a single global correlation. Architecture-aware adjudication revealed an asymmetric recovery pattern: the shared-mean baseline achieved the strongest canonical backbone recovery (0.807 versus 0.660 for GEARS), whereas GEARS retained stronger structure-versus-context separation (0.428 versus 0.353). This pattern persisted under finite-budget GEARS hyperparameter sweeps, embedding-based linear controls and coverage audits. Temporal analysis in K562 revealed a noteworthy stratification: the 7-day panel had stronger rank alignment with dependency (0.733 versus 0.515 at 13 days), whereas the 13-day panel had larger mean perturbation shift. A larger-scale CRISPRi screen (Replogle et al. 2022, 1,882 targets) confirmed that the perturbation-fitness bridge correlation is not a small-n artifact confined to the modest target counts in the primary HCC demonstration (rho = 0.402, 95% CI 0.363–0.439, p = 0.001; Extended Data Fig. 3b). Bridge strength was lower than in the primary KO contexts (rho = 0.40 versus 0.73–0.78), consistent with the direction expected from the CRISPRi-to-CRISPR-KO modality difference, although cell-line and library-design contributions cannot be isolated. CRISPR DepMap consistently exceeded RNAi DEMETER2 as a bridge endpoint across all four tested contexts. An exploratory pathway-response polarity analysis further showed that anchor genes (PFDN5, PRPF6) can maintain strong fitness-dependency linkage while their downstream pathway execution programs diverge across cell-line contexts, suggesting that fitness anchoring and transcriptional response wiring can be partially dissociable properties.

### Conclusions

This framework provides a reproducible, bounded methodology for phenotype-aligned perturbation-model adjudication. Each framework element—truth object definition, architecture decomposition, pre-specified category rules, anchor tiering with covariate governance, finite-budget rebuttal tests, and claim-boundary tiering—is defined independently of the HCC38/HCC1143 demonstration and is designed to be applicable to future cell-line contexts, endpoints and entrants while preserving explicit claim boundaries.

## Keywords

Perturb-seq; functional genomics; cancer dependency; DepMap; single-cell transcriptomics; perturbation modeling; benchmarking; GEARS; foundation models; reproducibility

## Background

Perturbation-model evaluation requires a phenotype-relevant recovery object, not only a prediction score. Single-cell perturbation profiling has made it possible to observe how genetic perturbations reshape transcriptomic state at scale [1-3]. These datasets have supported graph neural networks, single-cell foundation models and embedding-based decoders that aim to predict expression responses to perturbation [4-7]. Such models are commonly assessed by expression-level reconstruction accuracy. These metrics are necessary but incomplete: they do not directly test whether a model recovers transcriptomic structures that are relevant to downstream cellular phenotypes such as fitness or dependency. Prior benchmarks have already shown that expression-level recovery by deep-learning or foundation-model entrants can be matched or exceeded by simple baselines [8-11], consistent with the possibility that expression reconstruction and phenotype-relevant structure can diverge.

The first design problem is therefore object definition. We propose that a perturbation response can be conceptually decomposed into a shared canonical backbone that is recurrent across cell contexts, context-specific deviations, and shift-excess components that carry perturbation signal beyond the backbone (this decomposition serves as the architecture hypothesis of the framework and is tested empirically below). Critically, these components need not be equally aligned with dependency. A simple baseline may perform strongly on the dominant shared-backbone component, while a complex model may add signal in separation or deviation dimensions without recovering the backbone itself. Without defining a frozen, phenotype-relevant truth object before model comparison, leaderboard-style evaluation can conflate expression reconstruction, endpoint alignment and biological interpretation.

Prior perturbation-prediction benchmarks [8-11] provide essential context for interpreting model-side results, but they address a different question: they evaluate transcriptome prediction accuracy, whereas the present framework first freezes a phenotype-relevant truth object by aligning perturbation transcriptomic shifts to CRISPR DepMap dependency, and only then adjudicates model recovery. The resulting claim is not that complex models fail in a unidirectional sense, but that current entrants recover different components of a frozen fitness-bridge architecture, and that the framework identifies which components are recovered, missed or only partially supported.

Cancer dependency resources provide an opportunity to anchor this evaluation in phenotype-relevant fitness readouts. CRISPR DepMap captures gene-level fitness effects across cancer cell lines [12]. RNAi DEMETER2 provides a related but distinct cross-platform readout [13]; as we show below, it is consistently weaker than CRISPR DepMap as a bridge endpoint in the tested contexts. These endpoints are not interchangeable, and the framework therefore requires explicit endpoint hierarchy and claim governance, ensuring that evidence layers remain separated from causal or mechanistic overinterpretation.

We therefore constructed a truth-first, architecture-aware framework for perturbation transcriptome model evaluation in cancer functional genomics. The framework consists of seven elements: (i) phenotype-aligned truth object definition via perturbation-to-dependency bridge construction with pre-specified category rules; (ii) architecture decomposition into backbone, shift-excess and structure-versus-context dimensions; (iii) target-level anchor identification with covariate-aware evidence tiering; (iv) model recovery adjudication against the frozen architecture; (v) finite-budget rebuttal tests with pre-specified stop rules; (vi) claim-boundary tiering (A0/A1/B) for external evidence; and (vii) endpoint hierarchy with explicit primary/sensitivity/supplementary designation. Here we demonstrate this framework in the breast-cancer cell-line contexts HCC38 and HCC1143, with supplementary temporal evidence from K562. The study asks a narrow but important question: which components of a phenotype-relevant perturbation architecture are recovered by current transcriptome models, and which claims remain unsupported?

## Results

### Framework element 1: Truth object definition via a pre-specified perturbation-to-dependency bridge

The first framework element requires that the recovery object be defined independently of model predictions, using pre-specified rules. For each HCC38/HCC1143 breast-cancer context, transcriptomic truth was summarized by the absolute mean perturbation shift (`real_shift_mean_abs`), chosen as a full-transcriptome perturbation-magnitude summary that does not privilege any gene subset. This truth metric was aligned with CRISPR DepMap dependency such that larger aligned values represented stronger dependency. Targets were assigned to pre-specified joint shift-dependency categories using the 25th and 75th rank percentiles as symmetric cutoffs, defining high-shift/high-dependency anchors (Q1), transcriptomic-excess targets, dependency-excess targets, low-information targets and a retained middle band (Fig. 1a,d; Extended Data Fig. 1). The 25/75 symmetric percentile rule was chosen for simplicity and reproducibility; sensitivity to this choice was assessed by cutoff-sensitivity analysis and metric-robustness controls (Extended Data Fig. 2; Methods).

Both breast-cancer cell-line contexts contained a high-shift/high-dependency anchor set. HCC38 contained 9 Q1 anchors and HCC1143 contained 10 Q1 anchors, with aligned Spearman rho values of 0.726 (95% CI 0.554-0.838) and 0.779 (95% CI 0.636-0.871), respectively; both observed values lay well outside the permutation-null envelope (empirical p = 0.001 for each context; Fig. 1b,c,e,f). The resulting bridge was therefore treated as a structured target-level recovery object whose categories, source data and interpretation boundary were fixed before model comparison. The bridge is interpreted as structurally above permutation null; it is not interpreted as fully deconfounded causal proof.

### Framework element 2: Anchor tiering with covariate-aware evidence governance

The second framework element requires that target-level claims be governed by explicit tiering rules that separate structural recurrence from unqualified causal interpretation. We identified targets recurrently occupying the high-shift/high-dependency region across both HCC38 and HCC1143. PFDN5, PMF1, PRPF6 and ZNF131 formed the most stable shared anchor set, retaining shared-anchor status under cutoff sensitivity analysis (Fig. 2a-c).

However, structural recurrence alone does not justify unqualified primary wording. Covariate-aware tiering—assessing each anchor against barcode gem group, UMI-signal, detected-gene and total-signal axes using total variation distance (TVD)—revealed that PFDN5 was covariate-clean (TVD <= 0.25 across all 10 audited covariate-context cells), whereas PMF1, PRPF6 and ZNF131 each exceeded the TVD imbalance threshold on UMI-related axes (Fig. 2e). Accordingly, PFDN5 was retained as a primary but qualified anchor; PMF1, PRPF6 and ZNF131 were retained as supporting-only anchors. ENY2, NPM1, RPS3, RUVBL2 and ZBTB17 were retained as supporting but cutoff-sensitive objects, indicating weaker structural stability (Fig. 2c,f). This tiering procedure implements a core framework principle: recurrent anchors support the existence of a structured perturbation-fitness bridge, but target-level wording remains capped by covariate stability and governance constraints (Fig. 2d,e). No individual anchor is interpreted as fully deconfounded causal evidence.

### Framework element 3: Architecture-aware model adjudication reveals an asymmetric recovery pattern

The third framework element requires that model recovery be adjudicated against the frozen architecture across multiple pre-specified dimensions, rather than by a single aggregate score. After freezing the truth object and anchor tiers, we evaluated recovery by the shared-mean baseline, GEARS, scGPT, Geneformer, low-rank linear controls and pretrained-embedding ridge controls. Models were scored across three dimensions: canonical backbone recovery (rank-percentile recovery of the expected axis among backbone-labeled targets), shift-excess identification (pairwise superiority probability of expected-axis magnitude for shift-excess versus backbone targets), and structure-versus-context separation (ratio of expected-axis magnitude to total magnitude across all axes) (Fig. 3a,b; Methods).

The shared-mean baseline achieved the strongest backbone recovery score (0.807), exceeding the pre-specified formal GEARS recipe (0.660). GEARS instead showed stronger structure-versus-context separation (0.428 versus 0.353 for the baseline). Shift-excess identification was tied at 0.333 for both the baseline and the formal GEARS recipe. Under the pre-specified definition (pairwise superiority probability with ties counted as 0.5, chance expectation = 0.5; Methods), this value falls below the chance level and indicates that neither entrant has recovered the shift-excess component beyond the background expectation under the current architecture definition (Fig. 3a,c). The pattern is therefore an asymmetric recovery profile rather than a single winner: the baseline recovers the dominant shared backbone more strongly, whereas GEARS adds signal in the separation dimension, but neither entrant recovers the full architecture.

Foundation-model entrants and embedding-based controls did not reverse this pattern. Geneformer retained more recoverable structure than scGPT in this setting, and Geneformer-ridge exceeded the other linear controls, but neither displaced the shared-mean baseline as the backbone reference (Fig. 3). Current entrants therefore recovered different but incomplete components of the frozen architecture. The term "asymmetric recovery pattern" is used throughout rather than "trade-off" because the present evidence demonstrates differential recovery across dimensions without establishing that the dimensions are mutually constraining within a single model.

### Framework element 4: Finite-budget rebuttal tests with pre-specified stop rules

The fourth framework element is the use of pre-specified rebuttal tests, rather than open-ended optimization, to assess whether a result is sensitive to local recipe variation. We applied a finite-budget neighborhood sweep to test whether GEARS backbone recovery could be improved by small recipe changes. The sweep varied epochs (20, 30, 40), learning rate (0.0005, 0.001, 0.002) and weight decay (1e-6, 1e-5) under a nearest-to-base selection rule, yielding six materialized or re-used candidates. The truth object, adjudication space and scoring system were held fixed throughout.

No sweep candidate closed the backbone gap to the shared-mean baseline. The best sweep candidate scored 0.643 for backbone recovery, below both the baseline (0.807) and the formal GEARS recipe (0.660) (Fig. 4a,b). Some candidates modestly improved shift-excess identification or separation, but these gains did not translate into backbone superiority. Under the pre-specified stop rule, GEARS was retained as an architecture-level diagnosis rather than promoted as the HCC38/HCC1143 primary winner (Fig. 4a-c). Linear-control analyses gave the same message: low-rank and pretrained-embedding ridge controls achieved complete target coverage but did not exceed the shared-mean baseline in backbone recovery (Fig. 4b,c). The persistence of the gap after finite-budget sweeps, linear controls and coverage audits is consistent with the interpretation that the backbone-recovery gap reflects a systematic structure in the prediction-target relationship under the present architecture definition; it does not exclude untested model-side factors, and this bounded interpretation is stated in the Fig. 4 caption.

### Framework element 5: Descriptive axis-level and pathway-response context

The fifth framework element provides descriptive biological context without elevating axis-level or pathway-level summaries to mechanistic claims. The bridge was summarized at the axis level to display how annotated biological axes distribute across transcriptomic shift and dependency signal (Extended Data Fig. 4). Transcription/chromatin showed the strongest transcriptomic-shift association (shift R2 = 0.092) with near-zero dependency R2 and target support from ENY2 and TADA3. Other axes—including chromatin remodeling, TGF-beta/BMP signaling, ER stress/UPR, RNA processing/spliceosome, ribosome biogenesis/nucleolar and ribosomal/translation—showed heterogeneous profiles with varying enrichment support, per-target consistency and bootstrap stability (Extended Data Fig. 4). Axis-level evidence is used here for biological contextualization, not to establish a new mechanistic hierarchy. The R2 values are modest (all below 0.1), consistent with the interpretation that the axis layer provides informative but partial descriptive context.

An exploratory pathway-response polarity analysis revealed a biologically noteworthy dissociation. PFDN5 and PRPF6 were strongly dependency-linked in both HCC38 and HCC1143, yet their Hallmark pathway-level response patterns showed low sign agreement across the two cell lines (Extended Data Fig. 5). This observation suggests that fitness anchoring (dependency linkage) and transcriptional response wiring (pathway execution) can be partially dissociable properties: a gene perturbation can converge on similar fitness consequences across contexts while engaging different downstream transcriptional programs. This finding is treated as framework-generated exploratory context rather than as a portable pathway mechanism. It illustrates a broader capability of the framework: by separating truth-object definition from model scoring, the architecture can also surface context-dependent response features that are not directly assessed by expression-only benchmarks.

### Framework element 6: Temporal architecture and endpoint hierarchy

The sixth framework element examines whether the architecture form recurs outside the primary demonstration contexts and establishes an explicit endpoint hierarchy. We assessed external recurrence using the GSE90063 K562 7d/13d temporal panel under the pre-specified A0/A1/B evidence-tiering scheme (Methods). Both time points supported recurrence of a backbone-plus-shift-excess architecture form, satisfying the A0 (architecture-form confirmation) tier (Fig. 5c; Extended Data Fig. 3).

A notable temporal stratification emerged: the 7-day panel showed stronger rank alignment with CRISPR DepMap dependency (aligned Spearman rho = 0.733), whereas the 13-day panel had a weaker rank bridge (0.515) despite exhibiting significantly larger mean perturbation shift (Fig. 5c; Extended Data Fig. 3). This dissociation—larger perturbation magnitude at the later time point co-occurring with weaker dependency-aligned rank structure—indicates temporal stratification rather than monotonic improvement. It suggests that early perturbation responses may be more tightly coupled to fitness-relevant architecture, while later time points show larger perturbation magnitude but weaker dependency-aligned rank organization. Under A0/A1/B tiering, K562 supports A0 architecture-form recurrence and A1 bounded bridge-form support, but does not reach content-level replication (B tier) because the target set (10 TFs versus 47-48 genome-wide targets), macro-class composition and bridgeable target count differ from the HCC38/HCC1143 primary demonstration (Fig. 5d).

We further tested whether the perturbation-to-dependency bridge correlation could be detected at a larger scale using a publicly available CRISPRi screen targeting 2,057 common essential genes in K562 at day 7 (Replogle et al. 2022) [2]. On the 1,882 targets with matched DepMap CRISPR dependency, the bridge remained clearly detectable (aligned Spearman rho = 0.402, 95% CI 0.363–0.439, empirical p = 0.001; Extended Data Fig. 3b). This result confirms that the perturbation-fitness bridge correlation is not a small-n artifact confined to the modest target counts (n = 47–48) in the primary HCC demonstration. Bridge strength was lower than in the primary KO contexts (rho = 0.40 versus 0.73–0.78), consistent with the direction expected from the CRISPRi-to-CRISPR-KO modality difference, although cell-line context and library composition differences cannot be isolated from the modality effect.

CRISPR DepMap and RNAi DEMETER2 endpoints were compared across all four contexts (HCC38, HCC1143, K562 7d, K562 13d). CRISPR bridge Spearman exceeded RNAi in every context without exception: 0.726 versus 0.276 (HCC38), 0.779 versus 0.384 (HCC1143), 0.733 versus 0.333 (K562 7d), and 0.515 versus 0.300 (K562 13d) (Fig. 5c). This consistent directionality across four perturbation contexts spanning two cell lineages (breast, leukemia), two datasets, and two perturbation platforms establishes a clear endpoint hierarchy for perturbation-model benchmarking: CRISPR DepMap is the primary bridge readout, while RNAi DEMETER2 provides a cross-platform sensitivity endpoint but cannot replace the primary readout (Fig. 5d).

### Framework element 7: Covariate governance and claim boundaries

The seventh framework element requires that claims be bounded by explicit covariate governance. We performed a multi-axis covariate audit covering barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes (Fig. 5a,b). The audit retained the bridge-form claim but prevented fully deconfounded wording. Barcode gem group illustrates this boundary: HCC38 maps to aggregated GEM groups aggrMH001-3 and HCC1143 maps to aggrMH004-6, but individual MH001-MH006 run labels are not resolved in the available metadata. Barcode gem group is therefore a design-proxy covariate rather than a fully resolved run-level batch covariate (Fig. 5c; Methods). Residual UMI-related imbalance persisted for several anchors after rank residualization, motivating the covariate-aware tiering applied in framework element 2. Design-proxy rank residualization did not overturn the bridge or primary anchor structure, but residual design or batch confounding cannot be fully excluded. This governance structure ensures that claim language reflects evidence quality rather than aspiration, a principle that applies to any future application of the framework.

## Discussion

This study presents a truth-first, architecture-aware framework for evaluating perturbation transcriptome models against cancer dependency endpoints. The framework's defining principle is that the phenotype-relevant recovery object must be defined and frozen before model comparison, separating three questions that are often conflated in benchmark studies: whether a perturbation-to-dependency bridge exists, which targets and axes provide qualified evidence for that bridge, and which components of the frozen architecture current models recover.

The framework comprises seven elements, each defined independently of the HCC38/HCC1143 demonstration context:

1. **Truth object definition**: Pre-specified joint shift-dependency categories (25/75 percentile grid) with the full-transcriptome mean absolute shift as the primary truth metric, aligned to a phenotype-relevant endpoint before model scoring.
2. **Architecture decomposition**: Three-dimensional recovery adjudication (backbone, shift-excess, structure-versus-context) that separates components a model may differentially recover.
3. **Anchor tiering with covariate governance**: Rule-based evidence tiering (primary-qualified, supporting-only, cutoff-sensitive) using structural recurrence, cutoff stability and covariate TVD, capping target-level wording below fully deconfounded causal claims.
4. **Finite-budget rebuttal tests**: Pre-specified neighborhood sweeps with explicit stop rules that prevent post hoc winner-picking.
5. **Descriptive axis/pathway context**: Biological annotation layers used for contextualization rather than mechanistic claims.
6. **A0/A1/B claim-boundary tiering**: Explicit evidence-tier assignments for external/supplementary data, distinguishing architecture-form recurrence from content-level replication.
7. **Endpoint hierarchy**: Primary (CRISPR DepMap), sensitivity (RNAi DEMETER2) and supplementary (K562 temporal) designations based on comparative bridge strength.

Each element is a methodological component that can be re-applied to new cell-line contexts, dependency endpoints or model entrants without requiring modification of the framework logic.

The model-side demonstration in HCC38 and HCC1143 revealed an asymmetric recovery pattern. The shared-mean baseline—constructed as a frozen canonical-backbone reference from truth-architecture component means, without using DepMap values, RNAi endpoints or model-side scoring—achieved the strongest backbone recovery (0.807 versus 0.660 for GEARS). GEARS showed stronger structure-versus-context separation (0.428 versus 0.353). This does not imply that complex perturbation models have no value. Rather, it specifies that, under the present architecture definition, the dominant recoverable component is the cross-context canonical backbone, and current complex entrants are better aligned with separation- or deviation-related dimensions that carry less weight in the backbone-dominated scoring space. The term "asymmetric recovery pattern" is used deliberately rather than "trade-off" to reflect that the two dimensions describe different model behaviors without a demonstrated within-model negative constraint.

The truth-side demonstration is also deliberately bounded. PFDN5, PMF1, PRPF6 and ZNF131 occupy recurrent high-shift/high-dependency positions and are stable under cutoff sensitivity. Covariate-aware TVD tiering further separates PFDN5 (covariate-clean across all audited axes) from PMF1, PRPF6 and ZNF131 (UMI-exposed), illustrating in this case that structural recurrence and covariate robustness are distinct evidence dimensions. No target is interpreted as fully deconfounded causal proof.

Three supplementary findings deserve emphasis. First, the K562 temporal analysis revealed that perturbation magnitude increases from 7 to 13 days, but the dependency-aligned rank structure weakens rather than strengthens. This temporal stratification—stronger rank bridge at the earlier time point despite smaller perturbation magnitude—suggests that the fitness-relevant architecture may be most accessible in early perturbation responses, consistent with the interpretation that early perturbation responses carry more fitness-relevant information before transcriptional programs undergo time-dependent changes. Second, the pathway-response polarity analysis (Extended Data Fig. 5) showed that PFDN5 and PRPF6 maintain strong fitness-dependency linkage across HCC38 and HCC1143 while their downstream Hallmark pathway execution patterns diverge. This observation, based on two anchor genes and two cell-line contexts, illustrates that fitness anchoring and transcriptional response wiring can be partially dissociable properties, reinforcing the framework's core premise that expression reconstruction and phenotype relevance are partially independent dimensions that require separate adjudication. Third, the Replogle K562 essential CRISPRi screen (1,882 matched targets) confirmed that the perturbation-fitness bridge correlation persists at scale (rho = 0.402, 95% CI 0.363–0.439, p = 0.001), with bridge strength attenuated in the direction expected from the CRISPRi-to-CRISPR-KO modality difference (rho = 0.40 versus 0.73–0.78 for the primary KO contexts). This large-n result addresses the concern that the bridge correlation observed in the primary HCC demonstration (n = 47–48) could be a small-sample artifact.

Several limitations follow from the framework's design. First, the primary demonstration uses two breast-cancer cell-line contexts (HCC38 and HCC1143) with 47-48 matched targets per context. The joint grid stratification and anchor tiering operate on small target counts (9-10 Q1 anchors; 4 shared anchors). We therefore confirmed the architecture form at scale using an independent CRISPRi dataset with 1,882 matched targets (Replogle et al. 2022, Extended Data Fig. 3b), which retained the Q1 anchor quadrant (202 targets) and confirmed that the bridge correlation persists above null at scale. The framework is designed such that scale limitations are acknowledged explicitly in the claim language. Second, the truth metric (`real_shift_mean_abs`) equally weights all genes in the perturbation response, and while Extended Data Fig. 2 shows that alternative metrics (L2 magnitude, DEG burden, top-k summaries) produce consistent results, no single scalar summary can capture all phenotype-relevant dimensions of a transcriptomic perturbation. Third, barcode gem group is a design-proxy covariate rather than a fully resolved run-level batch variable; residual confounding cannot be excluded. Fourth, the K562 temporal panel supports architecture-form recurrence (A0) and bounded bridge-form support (A1) but not content-level replication (B) because of differences in target-set composition and bridgeable target count. Fifth, RNAi DEMETER2 is retained only as a cross-platform sensitivity endpoint. The GEARS sweep was a finite neighborhood test of three hyperparameters (epochs, learning rate, weight decay) and does not exhaust all possible model configurations; however, it was sufficient for the pre-specified stop rule. The framework does not prove biological mechanism recovery by any model. Instead, it provides a reproducible adjudication methodology that makes claim boundaries explicit and prevents overinterpretation.

## Conclusions

We present a truth-first, architecture-aware framework for evaluating perturbation transcriptome models against cancer dependency endpoints. The framework's seven elements—truth object definition, architecture decomposition, covariate-aware anchor tiering, architecture-aware model adjudication, finite-budget rebuttal tests, claim-boundary tiering, and endpoint hierarchy—are defined independently of any specific cell-line context. In the HCC38 and HCC1143 breast-cancer demonstration, a structured perturbation-to-CRISPR-DepMap bridge was defined and audited before model comparison. Current entrants exhibited an asymmetric recovery pattern: the shared-mean baseline was the primary backbone reference, GEARS showed stronger structure-versus-context separation, and neither foundation-model entrants nor embedding-based controls reversed this pattern. Supplementary analyses confirmed the architecture form at scale (1,882-target CRISPRi screen), revealed temporal stratification of the fitness-relevant architecture (stronger rank alignment at earlier time points), and identified a dissociation between fitness anchoring and pathway-level response wiring. The framework and accompanying source-data manifests with SHA256-hashed reproducibility artifacts provide a bounded, phenotype-aligned resource that is designed to be extendable to future cell-line contexts, endpoints and entrants while preserving explicit claim boundaries.

## Methods

### Study aim, design and setting

The aim was to construct and demonstrate a phenotype-relevant evaluation framework for perturbation transcriptome models in cancer functional genomics. The design was retrospective and computational. The framework was defined independently of any specific cell-line context; HCC38 and HCC1143 breast-cancer cell lines served as the primary demonstration contexts. Real perturbation transcriptomic shifts were aligned with CRISPR DepMap dependency to define a frozen truth object. Model predictions were evaluated only after that object and its claim boundaries were fixed.

### Datasets and endpoint alignment

HCC38 and HCC1143 breast-cancer cell lines were used as the primary demonstration contexts. Transcriptomic truth was summarized at the perturbation-target level using absolute mean perturbation shift. For each context, single-cell expression was library-size normalized to a target sum of 10,000 and log1p transformed. For target \(p\), the perturbation shift vector was the difference between the mean log-normalized expression vector of cells assigned to \(p\) and the mean vector of matched control cells. The absolute mean perturbation shift, stored as `real_shift_mean_abs`, was the mean of the absolute values of this vector across gene-expression features. This quantity was used as a truth-side perturbation magnitude summary, not as a model expression-reconstruction score. Alternative truth metrics (L2 magnitude, DEG burden, top-k shift summaries) were evaluated in Extended Data Fig. 2 as robustness checks; the primary metric was chosen for its simplicity—it equally weights all genes and avoids gene-subset selection—and its empirical stability under control subsampling.

Primary bridge analyses used CRISPR DepMap dependency as the matched fitness endpoint. The CRISPR DepMap gene dependency variable (aligned such that larger values represent stronger dependency; sign convention harmonized as `depmap_gene_dependency` with alignment direction +1.0, in contrast to `depmap_gene_effect` which has alignment direction -1.0 and was used in sensitivity analyses only) was used for target ranking, binning and bridge construction. Direction alignment standardized interpretation only; it did not alter endpoint identity or render CRISPR DepMap and RNAi DEMETER2 interchangeable.

RNAi DEMETER2 was used only as a weaker cross-platform sensitivity endpoint, as established by the endpoint hierarchy analysis (Fig. 5c). The GSE90063 K562 7d/13d temporal panel was used as supplementary external architecture-form evidence. An earlier legacy object distributed under a `dixit_2016_raw` filename did not match the GSE90063 K562 TF-pool description (the legacy object contained gene symbols inconsistent with the validated TF-pool composition) and was excluded before analysis. All Dixit/K562 evidence in this study was derived de novo from GSE90063 7d and 13d data.

### Framework element 1: Truth-DepMap bridge construction

For each HCC38/HCC1143 breast-cancer context, targets with matched perturbation truth and DepMap dependency were ranked separately by `real_shift_mean_abs` and aligned `depmap_gene_dependency`. Within each context, rank percentiles at or below 0.25 were assigned to the low bin, rank percentiles at or above 0.75 were assigned to the high bin, and the remaining targets were assigned to the middle bin. Joint categories were then assigned from the two-dimensional grid: high-shift/high-dependency targets were Q1 anchors; high-shift/low-dependency targets were transcriptomic-excess targets; low-shift/high-dependency targets were dependency-excess targets; low-shift/low-dependency targets were low-information targets; all other observed combinations were retained as the middle band. The 25/75 symmetric percentile rule was chosen for simplicity, symmetry and ease of reproduction; sensitivity to the cutoff choice was assessed via cutoff-sensitivity analysis (Extended Data Fig. 2). The middle band was retained as part of the benchmark object rather than discarded. The target grid, Q1 anchor counts and category composition were frozen before model comparison, and the categories were used as architecture-structure labels rather than target-proof or causal labels.

The headline bridge strength (Fig. 1f) was reported in two separate components. First, for each primary context the point estimate was the aligned Spearman rho between `real_shift_mean_abs` and `depmap_gene_dependency` on the matched target-level pairs (n = 47 for HCC38, n = 48 for HCC1143). Sampling uncertainty of the point estimate was summarized by a closed-form Fisher z-transform 95% confidence interval computed from \(z = \mathrm{arctanh}(\rho)\) with standard error \(1/\sqrt{n-3}\), back-transformed by \(\tanh\); this quantity, stored in the panel source data as `ci_method = fisher_z_transform`, describes the precision of the point itself and is not a bootstrap. Second, the null reference envelope was obtained by permuting the target-to-DepMap pairing within each context 1000 times under a fixed random seed, recomputing the aligned Spearman rho on each permutation, and reporting the 2.5% and 97.5% quantiles of the resulting null distribution together with the empirical two-sided p value (observed rho exceeded all 1000 permuted values in both contexts, yielding p = 0.001 under the conservative p = 1/(N_perm + 1) convention). The point-level CI and the null envelope are distinct quantities and are reported together only to show that the observed bridge strength lies outside the rho = 0 permutation envelope. This pre-specified definition of bridge strength was used only to establish that the recovery object is structured above the permutation null; it was not used as a model adjudication metric.

### Framework element 2: Anchor tiering and sensitivity analysis

Target-level anchor wording was governed by a rule-based tiering procedure rather than by post hoc narrative interpretation. For each candidate anchor, the evidence inputs considered were: structural recurrence across the primary HCC38 and HCC1143 contexts, defined by recurrent occupancy of the high-shift/high-dependency region under the pre-specified joint shift-dependency assignment; cutoff sensitivity, assessed by whether shared-anchor status was retained under the pre-specified cutoff sensitivity analyses; stability under control subsampling where applicable; and covariate-aware governance, based on total variation distance (TVD) across five covariate axes (barcode gem group, UMI-threshold bin, UMI-quantile bin, detected-genes quantile bin, total-signal quantile bin) in both HCC contexts. The TVD imbalance threshold was set at 0.25; this value was chosen pre-specification as a conservative threshold corresponding to a quarter of the probability mass being displaced between the target and control distributions for a given covariate stratification.

These evidence inputs were used to assign wording tiers rather than to rank biological importance. Targets that showed recurrent high-shift/high-dependency behavior with stronger structural stability and TVD <= 0.25 across all audited cells but remained subject to residual design-proxy limitations were retained as primary but qualified anchors. Targets that supported the bridge structure but showed TVD > 0.25 on one or more covariate axes were retained as supporting-only anchors. Targets that showed supporting evidence but whose status depended materially on cutoff choice were retained as supporting but cutoff-sensitive objects. No target-level tier was interpreted as fully deconfounded causal proof. This tiering procedure separates bridge support from target proof and ensures that claim language reflects evidence quality.

### Framework element 3: Model recovery adjudication

Model predictions were evaluated against the frozen truth architecture using three dimensions: canonical backbone recovery, shift-excess identification and structure-versus-context separation. Predictions were first projected onto the frozen target-axis architecture: for each target and each fine axis, the projected axis magnitude was the mean absolute predicted shift across genes assigned to that axis. Canonical backbone recovery was the mean rank-percentile recovery of the expected axis among targets whose expected axis was labeled `canonical_backbone` in the truth architecture contract. The `canonical_backbone` label was assigned to axes where the fraction of member targets in the Q1 quadrant reached at least 0.5 in both HCC38 and HCC1143 (a structural property of the truth data, computed before model comparison). The shared-mean baseline was constructed as the mean truth-aligned log-shift vector across all canonical_backbone-labeled targets; it was assigned to every frozen target regardless of that target's architecture label. Because backbone recovery scoring uses the expected-axis rank percentile (not the predicted shift value directly) and is evaluated across all backbone-labeled targets, baseline construction and scoring operate on related but non-identical target subsets and use distinct mathematical operations (mean vector construction versus rank-percentile recovery). Control subsampling confirmed stable truth-DepMap bridge estimates independent of baseline construction.

Shift-excess identification was the pairwise superiority probability that expected-axis projected magnitude for `shift_excess` targets exceeded expected-axis projected magnitude for `canonical_backbone` targets, with ties counted as 0.5 (chance level = 0.5). Structure-versus-context separation was the mean, across targets, of the expected-axis magnitude divided by the sum of expected-axis magnitude and mean off-axis magnitude. All three scores were oriented so that larger values indicated stronger recovery of that component.

Entrants included GEARS, scGPT, Geneformer, low-rank linear controls and pretrained-embedding ridge controls. A shared-mean baseline and a null model served as references. The `shared_mean_baseline` was constructed within each primary HCC context by averaging the truth-aligned log-shift vectors of targets assigned to the `canonical_backbone` component and assigning that same mean vector to every frozen target. The null model assigned a zero shift vector to every target. The shared-mean baseline served as a frozen canonical-backbone reference, not as a deployable perturbation model and not as a dependency-informed predictor. The primary model-side claim was based on joint interpretation of the three recovery dimensions against the frozen HCC38/HCC1143 architecture rather than expression prediction alone.

### Framework element 4: GEARS finite-budget sweep and pre-specified stop rule

The GEARS recipe audit was a pre-specified finite-budget neighborhood sweep around the frozen formal GEARS recipe rather than an exhaustive hyperparameter search. The parent configuration allowed variation only in epochs (20, 30 or 40), learning rate (0.0005, 0.001 or 0.002) and weight decay (0.000001 or 0.00001), with `materialization_export_sanity` fixed to `default_only`. Under the pre-specified nearest-to-base selection rule, candidate recipes were restricted to the base recipe and the nearest eligible one-parameter local variants within this neighborhood, yielding six materialized or re-used candidates in total. The truth object, model architecture, adjudication space and scoring system were held fixed throughout the sweep. The sweep was designed as a local rebuttal test of whether the backbone-recovery gap could be closed by small recipe changes. The pre-specified stop rule was that GEARS would not be promoted to the HCC38/HCC1143 primary winner unless a finite-budget candidate closed the backbone-recovery gap to the `shared_mean_baseline`. Because no candidate satisfied this criterion, GEARS was retained as an architecture-level diagnosis. GEARS training was not rerun during figure production; frozen predictions, scoring tables and sweep artifacts were reused and recorded with SHA256 hashes for reproducibility (see source data manifests).

### Framework element 5: Linear and foundation-model controls

Low-rank linear controls and pretrained-embedding ridge controls were used to test whether backbone recovery was limited by target coverage or by a missing embedding-level representation. Coverage audits were performed for embedding-based controls. Geneformer-ridge, scGPT-ridge and low-rank controls were compared under the same frozen recovery metrics as GEARS and the shared-mean baseline.

### Framework element 6: Axis-level analysis and pathway-response exploration

Axis-level explanatory strength was computed separately for transcriptomic shift (R2 from linear model of per-target shift magnitude against axis membership) and dependency (R2 from linear model of per-target dependency against axis membership). Axis interpretation used enrichment evidence, database support, per-target consistency and bootstrap stability. Axis-level evidence was used for interpretation and claim tiering, not as a replacement for target-level bridge evidence. Pathway enrichment (Hallmark gene sets, FDR < 0.10) was computed for selected anchor and high-variance response targets across HCC38, HCC1143, K562 7d and K562 13d. Cross-context pathway polarity was summarized by Spearman correlation and sign-agreement fraction of pathway normalized enrichment scores. Pathway-level results were treated as exploratory context for response wiring; they were not used to define the truth object or to adjust model adjudication.

### Framework element 7: Covariate audit

The covariate audit included barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes. Barcode gem group was extracted from cell barcodes by the regex `-(\d+)$`, capturing the trailing numeric GEM group identifier from 10x Genomics chemistry, and aggregated as `aggrMH001-3` (HCC38) and `aggrMH004-6` (HCC1143). Barcode gem group was treated as a design-proxy axis rather than a fully resolved run-level covariate because individual MH001-MH006 run labels are not resolved in the available metadata; the aggregation reflects the mapping of GEM groups to cell-line contexts in the experimental design. Covariate evidence governed wording strength and prevented fully deconfounded target claims.

### K562 temporal panel analysis

The GSE90063 K562 7d/13d temporal panel was evaluated as supplementary evidence using a pre-specified three-level evidence scheme: A0, A1 and B. This tiering distinguishes architecture-form recurrence, bridge-form support and content-level admissibility.

A0 (architecture-form recurrence) was assigned when the K562 panel supported recurrence of the benchmark architecture form, operationalized as recurrence of the backbone-plus-shift-excess structure under the frozen truth-side framework. A0 addresses whether the architectural form observed in the primary HCC38/HCC1143 contexts is detectable in the supplementary K562 context; it does not require shared target identity or content-level convergence.

A1 (bounded bridge-form support) was assigned when the K562 panel further showed support for a bridge-form relationship to the matched primary endpoint framework, while remaining weaker or more limited than the HCC38/HCC1143 primary evidence. A1 supports the claim that the recurrent architecture form remains bridge-relevant in the supplementary context, but does not establish symmetric external validation or co-primary status.

B (content-level not eligible) was assigned when supplementary evidence was not admissible for content-level replication claims. This applied when target-set composition, macro-class composition, bridgeable target count or related context differences prevented direct elevation of K562 results into shared target-level or axis-level replication claims.

Within this framework, the 13-day panel was treated as the formal supplementary K562 bridge test and the 7-day panel as a temporal sensitivity or early-bridge probe. Differences between 7-day and 13-day readouts were interpreted as temporal stratification within the supplementary context.

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

CRISPR: clustered regularly interspaced short palindromic repeats; DEMETER2: gene-level RNA interference dependency correction model; DepMap: Cancer Dependency Map; GEARS: graph-enhanced gene activation and repression simulator; HCC38/HCC1143: breast-cancer cell-line contexts used as the primary demonstration contexts; RNAi: RNA interference; TSV: tab-separated values; TVD: total variation distance; UMI: unique molecular identifier.

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
