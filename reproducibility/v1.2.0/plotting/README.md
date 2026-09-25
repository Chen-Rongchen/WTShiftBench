# Frozen-table plotting

`../build_figures.py` is the current entry point. Run it from the versioned directory or use the repository-root `reproduce_figures.sh`. The code reads packaged tables, never private manuscript files or hand-edited SVGs. The 33 display extracts retain their original bytes and source identifiers; `../presentation/final/sources.json` records their provenance and SHA256. Existing public tables D01, D08 and D16 supply formal summaries and inference. Original source keys such as `Linear low-rank` are retained internally and displayed as **Chargram low-rank**, distinct from Replogle **Chargram ridge**.

| Figure | Scientific panel map |
| --- | --- |
| 1 | A evaluation concerns; B endpoint categories; C context roles |
| 2 | A corrected association; B shift estimators; C count associations; D conditional association; E additional contexts |
| 3 | A HCC profiles; B diagnostic references; C descriptive model-level correlations; D centering sensitivity; E training seeds |
| 4 | A Replogle profiles; B reconstruction versus alignment/identity; C feature seeds; D post hoc cutoff selection |
| S1 | A datasets and roles; B eligibility and target/gene axes |
| S2 | A raw-response summaries; B endpoint representation; C raw-anchor influence; D gene-subset sensitivity |
| S3 | A coverage; B target expression; C baseline expression; D technical distributions; E control-reference repeats; F depth-specific cohorts; G fixed cohort |
| S4 | A–F six external association contexts, 3 rows by 2 columns |
| S5 | A target ordering; B category separation; C signed direction |
| S6 | A 2 contexts by 3 geometry diagnostics; B 10 pairwise-cosine ECDFs |
| S7 | A 21 outputs by 5 cutoff pairs; B category counts in full and scoring cohorts |

## Interpretation and plotting conventions

- Figure 1A is a schematic, not empirical target data. Frozen categories do not imply preregistration before all data inspection.
- Figure 2B averages sampled shift for each target before calculating a target-level correlation. S3F/G calculate a correlation in each subsampling repeat before reporting the median and empirical 2.5–97.5% range of correlations. These are different aggregations; the replicate ranges are not target-bootstrap confidence intervals. Numeric labels in S3F/G are target counts. S3E retains all 24 repeats. Target-gene RNA expression is not an estimate of perturbation efficiency.
- Figure 3C is a descriptive within-context correlation matrix over nine outputs, shown as its lower triangle and diagonal. It does not establish mutually independent metrics. Identity uses frozen target-label Mantel inference with 10,000 permutations and BH adjustment across the 18 formal HCC identity tests; repeated rounded q values need not indicate identical unadjusted P values. Training seeds 123–125 are shown for CPA, GEARS and scGen and 123–127 for CellOT. Each point is one run; vertical offsets encode ordering, not uncertainty. CellOT seed 123 is formal, not chosen here by performance.
- Figure 4A/B use formal feature seed 42; C shows additional feature-preparation seeds 123–125 for both ridge implementations. They are not pretraining replicates. Identity has no new CI. The two ridge nRMSE summaries are descriptively close, not established statistically equivalent.
- S1 counts retain the source-specific processing stages: input matrix barcodes for HCC and processed datasets for the other contexts. These counts are not a claim that every dataset underwent an identical processing stage; the plotted source overview and original preprocessing records define the corresponding objects.
- S2 concerns raw-response association sensitivity. Removing raw anchors is a descriptive influence check and does not redefine frozen categories or prove continuous full-range ordering. It does not constitute the same sensitivity analysis of corrected categories.
- S4 uses the same y limits and ticks for dependency probability in every panel; x limits vary. The two K562 TF contexts have n=10 and are additional association analyses, not model-audit qualifications.
- S5A/B percentiles are within each output. Targets in A are ordered by dependency probability from low to high. Black **vertical ticks** in C denote frozen median signed cosine for each implementation and context.
- S6A leading-mode energy share and effective rank are complementary spectral summaries of each predicted response matrix, not independent evidence streams. S6B includes the shared-mean diagnostic reference in addition to the nine numbered formal implementations. ECDFs show cumulative proportions over 1,081 distinct pairs of 47 valid targets; pairs share targets and are not independent inferential units. No data jitter is used to separate model-number labels.
- S7 `Replogle` means K562 essential CRISPRi day 6. Cell entries in B report anchors / low-information target counts. A combination is evaluable only with at least two scored anchors and two scored low-information targets. The outlined 25/75 pair is the frozen formal choice. Predictions remain unchanged as cutoff definitions and evaluation categories change. This is design sensitivity, not optimization of out-of-sample predictive performance. Figure 4D shows all 21 increases, including seven zero values; uncertainty intervals were not computed for these increases.

## Scope of reproduction

Plotting regenerates scientific panels from frozen display tables. It does not rerun upstream cell sampling or model training. Matrix scoring and its inference remain the separate commands in the main reproducibility guide. The original source DOI and historical download receipts retain their original snapshots; the current source archive is identified by the release manifest and its commit/hash. The already published six-file Zenodo core data record is unchanged.
