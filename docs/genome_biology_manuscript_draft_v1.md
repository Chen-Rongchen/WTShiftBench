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

Perturbation transcriptome models are usually evaluated by expression reconstruction, but this does not establish recovery of phenotype-relevant biology.

### Results

We built a truth-anchored framework and resource that aligns perturbation transcriptomic shifts with cancer dependency endpoints before model comparison. In HCC38 and HCC1143, the benchmark retained a structured CRISPR fitness bridge with qualified target anchors and partial axis-level interpretation. Architecture-aware adjudication decomposed recovery into backbone recovery, shift-excess identification and structure-versus-context separation, revealing a backbone-vs-separation trade-off rather than a single leaderboard result. K562 temporal and RNAi analyses supported bounded external and endpoint sensitivity.

### Conclusions

This resource provides a reproducible framework for extending phenotype-aligned perturbation-model adjudication to future contexts, endpoints and entrants while preserving explicit claim boundaries.

## Keywords

Perturb-seq; functional genomics; cancer dependency; DepMap; single-cell transcriptomics; perturbation modeling; benchmarking; GEARS; foundation models; reproducibility

## Background

Single-cell perturbation profiling has made it possible to observe how genetic perturbations reshape transcriptomic state at scale. These datasets have supported graph neural networks, single-cell foundation models and embedding-based decoders that aim to predict expression responses to perturbation. Such models are often assessed by expression-level reconstruction accuracy or local agreement with observed transcriptional shifts. These metrics are necessary but incomplete: they do not directly test whether a model recovers transcriptomic structures that are relevant to downstream cellular phenotypes such as fitness, dependency or liability.

This distinction is important for functional genomics. A perturbation response can contain a shared backbone that is recurrent across cell contexts, context-specific deviations, and biological axes that are only partially aligned with dependency. A model may recover one component while missing another. Conversely, a simple baseline can perform strongly when the evaluated object is dominated by shared structure. Without defining the phenotype-relevant truth object before model comparison, model leaderboards risk conflating expression reconstruction, endpoint alignment and biological interpretation.

Prior perturbation-prediction benchmarks have already shown that expression-level recovery by deep learning or foundation-model entrants can be matched or exceeded by simple baselines. These studies provide essential context for interpreting model-side results, but they ask a different question from the one addressed here. They evaluate transcriptome prediction accuracy, whereas the present benchmark first freezes a phenotype-relevant truth object by aligning perturbation transcriptomic shifts to cancer dependency endpoints. Model recovery is then decomposed into backbone recovery, shift-excess identification and structure-versus-context separation. The resulting claim is not that complex models fail in a unidirectional sense, but that current entrants occupy different parts of a frozen fitness-bridge architecture.

Cancer dependency resources provide an opportunity to make this evaluation more direct. CRISPR DepMap endpoints capture gene-level fitness effects across cancer cell lines and can be aligned with perturbation transcriptomic shifts. RNAi DEMETER2 endpoints provide a related but noisier cross-platform sensitivity readout. However, these endpoints are not interchangeable, and bridge claims require governance: target anchors, covariate boundaries and external recurrence must be separated from causal or mechanistic overinterpretation.

We therefore built a truth-anchored benchmark for perturbation transcriptome models in cancer functional genomics. In HCC38 and HCC1143, real perturbation transcriptomic shifts were aligned to CRISPR DepMap dependency endpoints to define a frozen truth bridge before model evaluation. The bridge was decomposed into target-level grids, shared anchors, axis-level interpretation, covariate boundaries and endpoint hierarchy. Model predictions from GEARS, single-cell foundation-model entrants and linear controls were then evaluated against this frozen architecture. The study asks a narrow but important question: which components of a phenotype-relevant perturbation architecture are recovered by current transcriptome models, and which claims remain unsupported?

## Results

### A truth-anchored HCC benchmark defines the phenotype-relevant recovery object

We first defined the benchmark object independently of model predictions. For each HCC context, transcriptomic truth was summarized by the absolute mean perturbation shift and aligned with CRISPR DepMap dependency so that larger aligned values represented stronger dependency. Targets were assigned to joint shift-dependency categories, including high-shift/high-dependency anchors, transcriptomic-excess targets, dependency-excess targets, low-information targets and a retained middle band (Fig. 1a-c; Extended Data Fig. 1,2).

Both HCC cell lines contained a high-shift/high-dependency anchor component. HCC38 contained 9 Q1 anchors and HCC1143 contained 10 Q1 anchors (Fig. 1d-f; Extended Data Fig. 2). The resulting bridge was not treated as a single global correlation. Instead, it was retained as a structured target-level recovery object whose categories, source data and claim boundaries were fixed before any model comparison (Fig. 1g,h).

### Shared anchor analysis separates recurrent structure from unqualified target claims

We next asked which target-level objects were recurrent across HCC38 and HCC1143. PFDN5, PMF1, PRPF6 and ZNF131 formed the most stable shared anchor set, repeatedly occupying the high-shift/high-dependency region and retaining shared-anchor status under cutoff sensitivity analysis (Fig. 2a-c; Extended Data Fig. 3).

However, recurrent structure did not justify unqualified target-level claims. After covariate-aware tiering, PFDN5 remained a primary but qualified anchor, whereas PMF1, PRPF6 and ZNF131 were retained as supporting-only anchors. ENY2, NPM1, RPS3, RUVBL2 and ZBTB17 were retained as supporting but cutoff-sensitive objects (Fig. 2d-g; Extended Data Fig. 3). This tiering separates bridge support from target proof: shared anchors support the existence of a structured perturbation-fitness bridge, but no individual anchor is interpreted as fully deconfounded causal evidence (Fig. 2h).

### Model comparisons reveal a backbone-separation trade-off

After freezing the truth object, we evaluated recovery by the shared-mean baseline, GEARS, scGPT, Geneformer, low-rank linear controls and pretrained-embedding ridge controls. Models were scored across three dimensions: canonical backbone recovery, shift-excess identification and structure-versus-context separation (Fig. 3a,b; Extended Data Fig. 4).

The shared-mean baseline achieved the strongest backbone recovery score, 0.807, exceeding the formal GEARS recipe, 0.660. GEARS instead showed stronger structure-versus-context separation, 0.428 compared with 0.353 for the baseline (Fig. 3c,d). The difference was therefore not a simple model failure or success. It was a trade-off: the baseline recovered the dominant shared backbone more strongly, whereas GEARS contributed more separation- or deviation-biased signal.

Foundation-model entrants and embedding-based controls did not overturn this result. Geneformer retained more signal than scGPT in this setting, and Geneformer-ridge exceeded other linear controls, but neither displaced the shared-mean baseline as the backbone reference (Fig. 3e-h; Extended Data Fig. 4). Current model entrants therefore recovered only part of the frozen perturbation-fitness architecture.

### GEARS recipe sweeps and embedding controls do not close the backbone gap

We then tested whether GEARS underperformance on backbone recovery reflected a missing small local recipe. A predefined finite-budget neighborhood sweep varied epochs, learning rate and weight decay using a nearest-to-base selection rule. Six candidate recipes were materialized or re-used, including the base recipe and five one-axis variants. No sweep candidate closed the backbone gap to the shared-mean baseline. The best sweep candidate scored 0.643 for backbone recovery, below both the baseline and the formal GEARS recipe (Fig. 4a-c; Extended Data Fig. 5).

Some sweep candidates improved shift-excess identification or structure-versus-context separation, but these gains did not become backbone superiority. The stop rule therefore retained GEARS as an architecture trade-off diagnosis rather than an HCC primary winner (Fig. 4d,h). Linear-control analyses led to the same interpretation. Low-rank and pretrained-embedding ridge controls achieved complete target coverage but did not exceed the shared-mean baseline in backbone recovery (Fig. 4e-g). The observed gap is most parsimoniously interpreted as a task-structure or direction-level mismatch rather than a missing small recipe or target-coverage artifact.

### Axis-level decomposition provides qualified biological interpretation

We next decomposed the bridge at the axis level to test whether the target-level architecture had interpretable biological structure. The strongest qualified formal axis was transcription/chromatin. This axis showed transcriptomic-heavy behavior, with shift R2 = 0.092, dependency R2 near zero, and target support from ENY2 and TADA3 (Fig. 5a,b,e; Extended Data Fig. 6).

Other axes showed partial support, including chromatin remodeling, TGF-beta/BMP signaling, ER stress/UPR, RNA processing/spliceosome, ribosome biogenesis/nucleolar and ribosomal/translation axes. These axes varied in enrichment support, database support, per-target consistency and bootstrap stability (Fig. 5c-g; Extended Data Fig. 6). Axis-level evidence therefore supports biological interpretation but not closure. Transcription/chromatin can be written as a primary but qualified axis, while the broader explanatory architecture remains partial (Fig. 5h).

### Covariate, temporal and endpoint analyses define the claim boundary

We performed a covariate audit covering barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes. The audit retained the bridge claim but prevented fully deconfounded wording (Fig. 6a,b; Extended Data Fig. 9). Barcode gem group illustrates this boundary: HCC38 maps to aggrMH001-3 and HCC1143 maps to aggrMH004-6, but individual MH001-MH006 run labels are not resolved (Fig. 6c; Extended Data Fig. 9).

External recurrence was assessed using the GSE90063 K562 temporal panel. Both 7-day and 13-day panels supported a backbone-plus-shift-excess architecture form. The 7-day panel had stronger rank alignment, whereas the 13-day panel had larger mean shift, indicating temporal stratification rather than monotonic improvement at the later time point (Fig. 6d,e; Extended Data Fig. 7). Under A0/A1/B tiering, the K562 panel supports architecture-form confirmation and bridge-form support, but not content-level replication or a primary co-pillar conclusion (Fig. 6f; Extended Data Fig. 7).

Finally, CRISPR DepMap and RNAi DEMETER2 endpoints were compared across HCC38, HCC1143, K562 7d and K562 13d. CRISPR bridge Spearman exceeded RNAi in every context: 0.726 versus 0.276 in HCC38, 0.779 versus 0.384 in HCC1143, 0.733 versus 0.333 in K562 7d and 0.515 versus 0.300 in K562 13d (Fig. 6g; Extended Data Fig. 8). CRISPR DepMap was therefore retained as the primary bridge readout, whereas RNAi DEMETER2 was retained as a weaker cross-platform sensitivity endpoint (Fig. 6h).

## Discussion

This study presents a truth-anchored benchmark for evaluating perturbation transcriptome models against cancer fitness phenotypes. The central design choice is to define the phenotype-relevant recovery object before model comparison. This separates three questions that are often conflated: whether a perturbation-fitness bridge exists, which targets and axes support that bridge, and whether model predictions recover the frozen architecture.

The model-side result is a backbone-separation trade-off. The shared-mean baseline captures the dominant canonical backbone more strongly than the formal GEARS recipe, while GEARS shows stronger structure-versus-context separation. Foundation-model entrants and embedding-based controls do not reverse this ordering. This does not mean that complex perturbation models are uninformative. Rather, it specifies that their current advantages are misaligned with the strongest component of this HCC fitness-bridge benchmark.

The strength of the shared-mean baseline is informative rather than artifactual. The baseline was used as a frozen-architecture backbone reference rather than as a deployable predictive model: it was constructed from the canonical-backbone transcriptomic component and did not use DepMap dependency values, RNAi endpoints or model-side scoring outcomes to generate target-specific predictions. Control subsampling showed stable truth-DepMap bridge estimates in both HCC contexts, and embedding-based controls achieved complete target coverage without closing the backbone gap. Thus, the baseline result indicates that the dominant component of the HCC truth object is a cross-context canonical backbone. GEARS and Geneformer retain signal in separation or shift-excess dimensions, but this signal does not displace the baseline for primary backbone recovery.

The truth-side result is also deliberately bounded. Shared anchors such as PFDN5, PMF1, PRPF6 and ZNF131 support the bridge because they occupy recurrent high-shift/high-dependency regions and remain stable under cutoff sensitivity. However, covariate-aware tiering prevents these anchors from being written as clean, fully deconfounded primary target proofs. Similarly, transcription/chromatin is the strongest qualified axis, but axis-level interpretation remains partial.

External and endpoint analyses further constrain the claim. K562 temporal data support recurrence of the architecture form outside the HCC primary context, but do not provide content-level replication because the target set, macro-class composition and bridgeable target count differ from the HCC benchmark. RNAi DEMETER2 provides useful cross-platform sensitivity evidence, but is consistently weaker than CRISPR DepMap and cannot replace it as the primary endpoint.

Several limitations follow directly from these boundaries. First, the primary evidence is based on two HCC cell lines and a limited shared-anchor set, so bridge content is treated as qualified rather than as broad biological generalization. Second, barcode gem group is available as a design-proxy axis but not as fully resolved run-level metadata; design-proxy rank residualization did not overturn the bridge or primary anchor structure, but residual design or batch confounding cannot be fully excluded. Third, the K562 temporal panel supports architecture-form recurrence but not content-level replication because the target set, macro-class composition and bridgeable target count differ from the HCC benchmark. Fourth, RNAi DEMETER2 is retained only as a cross-platform sensitivity endpoint and is not a matched primary endpoint. The GEARS sweep was a finite neighborhood test and did not exhaust all possible model recipes, although it was sufficient for the predefined stop rule. GEARS training was not rerun during figure production; frozen predictions and scoring artifacts were used for reproducibility. The benchmark does not prove mechanism recovery by any model. Instead, it provides a reproducible adjudication framework for assessing which components of a functional-genomic perturbation architecture are recovered, missed or only partially supported.

## Conclusions

Perturbation transcriptome models should be evaluated against phenotype-relevant truth objects, not only expression reconstruction metrics. In HCC38 and HCC1143, a structured CRISPR fitness bridge can be defined and audited before model comparison. Current entrants recover different parts of this architecture: the shared-mean baseline is strongest for canonical backbone recovery, whereas GEARS contributes stronger structure-versus-context separation. Anchor, axis, temporal and endpoint analyses define a reproducible but bounded claim space. The resulting benchmark and accompanying source-data manifests provide a resource for functional-genomic evaluation of future perturbation models.

## Methods

### Study aim, design and setting

The aim was to build and apply a phenotype-relevant benchmark for perturbation transcriptome model evaluation in cancer functional genomics. The design was retrospective and computational. Real perturbation transcriptomic shifts in HCC38 and HCC1143 were aligned with cancer dependency endpoints to define a frozen truth object. Model predictions were evaluated only after that truth object and its claim boundaries were fixed.

### Datasets and endpoint alignment

HCC38 and HCC1143 were used as the primary benchmark contexts. Transcriptomic truth was summarized at the perturbation-target level using absolute mean expression shift. CRISPR DepMap dependency was used as the primary fitness endpoint and direction-aligned so that larger values represented stronger dependency or liability. RNAi DEMETER2 endpoints were used as weaker sensitivity readouts. The GSE90063 K562 7d/13d temporal panel was used as supplementary external architecture-form evidence. An earlier legacy object distributed under a `dixit_2016_raw` filename did not match the GSE90063 K562 TF-pool description and was excluded before analysis. All Dixit/K562 evidence in this study was derived de novo from GSE90063 7d and 13d data.

### Truth-DepMap bridge construction

For each HCC context, targets were stratified by transcriptomic shift and aligned CRISPR dependency into high, middle and low bins. Joint categories defined Q1 anchors, transcriptomic-excess targets, dependency-excess targets, low-information targets and retained middle-band targets. The target grid, Q1 anchor counts and category composition were frozen before model comparison.

### Anchor tiering and sensitivity analysis

Shared anchors were defined by recurrent high-shift/high-dependency behavior across HCC38 and HCC1143. Cutoff sensitivity and control subsampling were used to evaluate stability of anchor calls and bridge estimates. Anchor wording was assigned using structural recurrence, cutoff stability and covariate-aware governance. PFDN5 was retained as primary but qualified. PMF1, PRPF6 and ZNF131 were retained as supporting-only anchors.

### Model recovery adjudication

Model predictions were evaluated against the frozen truth architecture using three dimensions: canonical backbone recovery, shift-excess identification and structure-versus-context separation. Entrants included GEARS, scGPT, Geneformer, low-rank linear controls and pretrained-embedding ridge controls. A shared-mean baseline and a null model served as references. The primary model-side claim was based on recovery of the frozen HCC architecture rather than expression prediction alone.

### GEARS sweep and stop rule

The GEARS sweep was a predefined finite-budget neighborhood sweep rather than an exhaustive hyperparameter search. The parent configuration allowed variation in epochs (20, 30 or 40), learning rate (0.0005, 0.001 or 0.002) and weight decay (0.000001 or 0.00001), with `materialization_export_sanity` fixed to `default_only`. A nearest-to-base selection rule materialized or re-used six candidate recipes, including the base recipe and five one-axis variants. The sweep did not change model architecture, truth object or scoring system. The stop rule required GEARS not to be promoted as the HCC primary winner unless a finite-budget recipe closed the backbone recovery gap to the shared-mean baseline. GEARS training was not rerun during manuscript figure generation. Frozen predictions, scoring tables and sweep artifacts were used and recorded with hashes.

### Linear and foundation-model controls

Low-rank linear controls and pretrained-embedding ridge controls were used to test whether backbone recovery was limited by target coverage or by a missing embedding-level representation. Coverage audits were performed for embedding-based controls. Geneformer-ridge, scGPT-ridge and low-rank controls were compared under the same frozen recovery metrics as GEARS and the shared-mean baseline.

### Axis-level analysis

Axis-level explanatory strength was computed separately for transcriptomic shift and dependency. Axis interpretation used enrichment evidence, database support, per-target consistency and bootstrap stability. Axis-level evidence was used for interpretation and claim tiering, not as a replacement for target-level bridge evidence.

### Covariate audit

The covariate audit included barcode gem group, protospacer-related axes, UMI/transcriptome signal axes and detected-gene axes. Barcode gem group was treated as a design-proxy axis rather than a fully resolved run-level covariate. Covariate evidence governed wording strength and prevented fully deconfounded target claims.

### K562 temporal panel analysis

The GSE90063 K562 7d/13d temporal panel was evaluated as supplementary evidence. The 13-day panel was treated as the primary formal supplementary bridge test and the 7-day panel as a temporal sensitivity or early-bridge probe. Evidence was assigned to A0 architecture-form confirmation, A1 bridge-form support or B content-level-not-eligible tiers.

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

[To be confirmed by the authors before submission.] Drafting and project organization were assisted by a large language model. All analyses, data interpretation, generated files and final manuscript wording require author review and approval. No large language model is listed as an author.

## Abbreviations

CRISPR: clustered regularly interspaced short palindromic repeats; DEMETER2: gene-level RNA interference dependency correction model; DepMap: Cancer Dependency Map; GEARS: graph-enhanced gene activation and repression simulator; HCC: hepatocellular carcinoma context in this benchmark; RNAi: RNA interference; TSV: tab-separated values; UMI: unique molecular identifier.

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

[Formal reference list to be inserted before submission. Current formatting queue: `docs/genome_biology_reference_formatting_queue_v1.md`.]

## Additional files

Additional file 1: `.xlsx`; Supplementary Tables workbook. This workbook contains the frozen supplementary tables supporting the main and Extended Data figures.

Additional file 2: `.json`; Submission package manifest. This manifest records the submission package file inventory and hashes.

Additional file 3: `.tsv`; Submission package file manifest. This table provides a reviewer-readable index of the files included in the submission package.
