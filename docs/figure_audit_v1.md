# Figure Audit v1

Date: 2026-05-20

This audit reviews the current public figure bundle as a Cell Genomics-oriented
benchmark-resource package. It is a figure-production guardrail, not a change
to the frozen scoring object, model registry, dataset evidence layers, or claim
ceiling.

## Global Figure Rules

- Keep the visual grammar restrained: white background, low-ink axes, muted
  green / blue / orange / gray, direct numeric annotations, and source-data
  traceability for every panel.
- Use a Nature Methods-style benchmark palette inspired by Ahlmann-Eltze,
  Huber and Anders (2025): Okabe-Ito compatible colors, few hues per panel,
  gray baselines, and muted diverging heat maps rather than saturated red/blue
  blocks.
- Do not make a visual leaderboard. Model panels should show endpoint-recovery
  profiles, common-response diagnostics, and target-identity preservation.
- Keep model-generalization language out of figures that use only the
  HCC38/HCC1143 model-audit contexts.
- Keep external datasets in the bridge-form / boundary / endpoint-extension
  layer unless they have the same model-output contract and endpoint scoring.
- Panel letters must be visible in combined figures and must match manuscript
  legends.

## Main Figures

| Figure | Current role | Audit status | Action taken / next guardrail |
|---|---|---|---|
| Figure 1 | Endpoint-recovery resource contract | Rebuilt as a contract map, not a workflow/card figure. | Uses endpoint plane, dataset evidence-layer map, model-output contract table, and claim-boundary matrix. |
| Figure 2 | Primary HCC endpoint-recovery object | Rebuilt from the old anchor-focused figure into the primary HCC evidence figure. | Uses HCC38/HCC1143 observed shift-DepMap scatters, endpoint-category composition, endpoint-label permutation calibration, and compact anchor claim tiering. |
| Figure 3 | Full model endpoint-recovery audit | Rebuilt to include native perturbation-response entrants, foundation/repurposed entrants, linear controls, and diagnostic references. | Keep as an audit-profile figure, not a leaderboard; rows are grouped by model role rather than performance rank. Scatter small multiples are restricted to scGen, CPA, GEARS formal, CellOT, scGPT and Geneformer; controls, shared_mean and null stay in summary panels. |
| Figure 4 | External bridge-form robustness and boundaries | Rebuilt from the old GEARS sensitivity figure into the external bridge evidence layer. | Uses rho+CI forest plot, evidence-layer governance, GSE264667 HepG2/Jurkat category composition, and boundary interpretation. |
| Figure 5 | Response-program annotation and governance | Rebuilt from boundary-only governance into response-level GSEA plus resource governance. | GSEA is response-signature enrichment, not target-set mechanism discovery; governance/source-data panels carry claim boundaries and reproducibility. |

## Extended Data Figures

| Figure | Current role | Audit status | Guardrail |
|---|---|---|---|
| Extended Data Fig. 1 | Dataset inventory and perturbation-readout QC | Keep as three evidence blocks, not 11 independent claims. | Dataset inventory, embedding/familiarization, and target-expression readout only; no endpoint or model conclusions. |
| Extended Data Fig. 2 | Robustness of the primary HCC endpoint-recovery object | Primary support for Figure 2. | Panels a-c cover bridge robustness; panels d-f cover category, anchor-influence and covariate governance. |
| Extended Data Fig. 3 | Raw external bridge-form evidence and endpoint-extension eligibility | Primary support for Figure 4 raw evidence. | Include K562 temporal, Replogle essential/GWPS, and GSE264667 HepG2/Jurkat raw scatter or category grids. HepG2/Jurkat are completed secondary endpoint-extension evidence, not primary model-audit contexts. |
| Extended Data Fig. 4 | Model registry, output-contract status and reproducibility closure | Resource-transparency support for Figures 1 and 3. | Use compact matrices rather than table screenshots; full registries remain supplementary/source-data tables. |
| Extended Data Fig. 5 | Null calibration, multiple-testing control and model-sensitivity analyses | Statistical support for Figure 3. | Report q values within pre-specified metric families; GEARS sweep remains sensitivity/upper-bound diagnostic, not endpoint-selected primary evidence. |
| Extended Data Fig. 6 | Common-response and target-identity diagnostics for model-generated shifts | Artifact/recovery support for Figure 3. | Separate endpoint-relevant recovery from shared/common/stress-like collapse; include CPA HCC1143 boundary diagnosis and scGen/shared_mean/CPA contrasts. |
| Extended Data Fig. 7 | Response-level pathway-enrichment details and gene-set provenance | Support for Figure 5. | Response-level GSEA only for primary interpretation; target-set ORA, if retained, is descriptive-only or supplementary-table material. |

### Extended Data Panel Contract

| Figure | Panel | Task | Claim supported | Claim not supported |
|---|---|---|---|---|
| ED1 | a | Dataset inventory matrix | Input data transparency | Endpoint bridge or model performance |
| ED1 | b | Perturbation-level embedding/PCA/UMAP | Dataset familiarization | Biological mechanism |
| ED1 | c | Target-expression / perturbation-readout QC | Perturbation labels have expression-level readout | Complete guide-level efficacy proof |
| ED2 | a | Alternative shift metrics | Primary bridge not driven by one scalar metric | New optimized endpoint metric |
| ED2 | b | CRISPR versus RNAi endpoint sensitivity | CRISPR DepMap is the primary endpoint; RNAi is sensitivity | RNAi equivalence |
| ED2 | c | Control subsampling robustness | Bridge is not driven by one control-cell draw | Full deconfounding |
| ED2 | d | Anchor-influence jackknife | Bridge is not a single-anchor artifact | Anchor causal proof |
| ED2 | e | Category cutoff sensitivity | Frozen categories are not a fragile threshold artifact | Post hoc threshold tuning |
| ED2 | f | Covariate TVD audit | Claim boundary for target-level anchors | Fully deconfounded causality |
| ED3 | a | K562 day 7 raw bridge scatter | Temporal-boundary raw evidence | Model generalization |
| ED3 | b | K562 day 13 raw bridge scatter | Direction retained but weaker temporal support | Time-invariant bridge |
| ED3 | c | Replogle essential raw bridge scatter | Large-scale CRISPRi bridge detectability | KO-context equivalence |
| ED3 | d | Replogle GWPS raw bridge scatter | Genome-scale weak-but-detectable bridge | Strong universal bridge |
| ED3 | e | HepG2 raw scatter/category grid | Secondary cancer-line endpoint extension | Primary model-audit evidence |
| ED3 | f | Jurkat raw scatter/category grid | Secondary lineage-boundary endpoint extension | Primary model-audit evidence |
| ED3 | g | External permutation/null summary | Bridge-form calibration beyond primary contexts | Cross-dataset model superiority |
| ED4 | a | Model entrant registry | Formal/control/reference roles | Performance ranking |
| ED4 | b | Training/evaluation regime matrix | Within-context target-observed claim ceiling | Unseen-target generalization |
| ED4 | c | Output-contract availability | Common scorer contract | Identical original-model objectives |
| ED4 | d | Inclusion/exclusion audit | Claim-governed model inclusion | Arbitrary model omission |
| ED4 | e | Artifact hash manifest | Reproducibility closure | Biological conclusion |
| ED4 | f | Figure/source-data manifest | Source-data traceability | New evidence |
| ED5 | a | Total-shift endpoint permutation null | Total rho calibration | Direct DepMap prediction |
| ED5 | b | Axis-aligned endpoint permutation null | Axis rho calibration | Mechanism proof |
| ED5 | c | Anchor-vs-low-info AUC null | Category separation calibration | Category causality |
| ED5 | d | FDR/q-value by metric family | Multiple-testing control | Global omnibus winner |
| ED5 | e | GEARS formal versus sweep | Hyperparameter sensitivity | Endpoint-selected primary model |
| ED5 | f | Target-label/model-output shuffle | Target/output-structure specificity | Causal fitness prediction |
| ED5 | g | Observed-shift oracle | Truth-side ceiling | Predictive model entrant |
| ED6 | a | Common-response metric heatmap | Common/stress dominance audit | Standalone biology |
| ED6 | b | Observed target-target similarity | Target-identity reference structure | Model result |
| ED6 | c | Predicted target-target similarity matrices | Target collapse versus specificity | Model generalization |
| ED6 | d | Target-identity preservation summary | Quantified target-specific recovery | Direct endpoint prediction |
| ED6 | e | HCC1143 CPA observed/predicted axis heatmap | CPA boundary/common-response diagnosis | Universal CPA failure |
| ED6 | f | scGen/shared_mean/CPA comparison | Distinguish model-specific, shared and common responses | Leaderboard ranking |
| ED6 | g | Alternative common-response score sensitivity | Robustness of collapse diagnosis | Single definitive stress mechanism |
| ED7 | a | Response-signature construction QC | GSEA input provenance | Target-set mechanism |
| ED7 | b | Full Hallmark NES heatmap | Primary response-program annotation | Mechanism discovery |
| ED7 | c | Reactome sensitivity | Gene-set collection sensitivity | Hallmark replacement |
| ED7 | d | GO BP sensitivity | Fine-grained process annotation | Causal mechanism |
| ED7 | e | Anchor versus low-information details | Main response contrast support | Category causality |
| ED7 | f | Anchor versus middle details | Retained-band contrast support | New category definition |
| ED7 | g | Descriptive target-set ORA, optional | Category membership annotation only | Mechanistic enrichment claim |
| ED7 | h | Gene-set/source-data version manifest | Reproducibility | Biological evidence |

## Current Production Checks

- Rebuilt Figure 1, Figure 2, Figure 4, and Figure 5 after panel-letter fixes.
- Rebuilt Figure 3, Figure 4, Figure 5, Extended Data Figure 3, Extended Data
  Figure 5, Extended Data Figure 6 and Extended Data Figure 7 after the
  Nature Methods-style palette pass.
- Synced rebuilt figures into `figure_build/output/` and `figures/`.
- Synced Extended Data Figure 6 into `figures/` so the public figure snapshot
  matches the model-audit manuscript bundle.
- Refreshed `resource_registry/figure_source_data_manifest.tsv`.
- Verified modified drawing modules compile with `python -m py_compile`.

## Remaining Visual Priorities

1. Figure legends and Results text must be updated to the new Figure 1-5
   architecture; older GEARS/backbone-centered wording is no longer aligned
   with the current figure sequence.
2. Keep Figure 3 as an endpoint-recovery audit profile, not a visual model
   leaderboard. Additional GEARS sweep details belong in Extended Data.
3. Avoid duplicating the same bridge-form conclusion across ED3, ED7, and the
   new Figure 4. Figure 4 is now the preferred main-text external bridge-form
   summary because it includes GSE264667 HepG2/Jurkat.
4. Before submission, verify that `manuscript/figures/`, `figures/`, and
   `figure_build/output/` contain the same intended public versions.
