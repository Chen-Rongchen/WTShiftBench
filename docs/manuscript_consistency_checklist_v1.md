# WTShiftBench Manuscript Consistency Checklist v1

This checklist freezes the manuscript-facing interpretation after the model
endpoint-recovery and external bridge-form updates. Its purpose is to keep
Results, Methods, figure legends, source data, and README wording aligned during
later edits.

## Claim Ceiling

Primary manuscript claim:

- WTShiftBench audits whether model-generated perturbation shifts recover a
  fixed DepMap-aligned endpoint-recovery object.

Allowed wording:

- endpoint-recovery audit
- DepMap-aligned perturbation structure
- model-generated perturbation shifts
- within-context, target-observed, pair-observed, endpoint-not-supervised
- recovery-object portability and boundary evidence
- common-response or stress-like collapse

Disallowed wording:

- direct DepMap predictor
- broad model generalization across unseen datasets
- unseen-target generalization, unless a separate held-out split is explicitly
  introduced
- essentiality, viability, or causal fitness prediction
- mechanism discovery from endpoint categories
- model leaderboard as the primary goal

## Dataset Evidence Layers

| Layer | Contexts | Supported claim | Do not claim |
| --- | --- | --- | --- |
| Primary model-audit | HCC38 day 14, HCC1143 day 14 | formal endpoint-recovery audit of model outputs | broad model generalization |
| External bridge-form boundary | K562 temporal 7d/13d, Replogle K562 essential/GWPS | bridge-form detectability and temporal/modality/scale boundaries | cross-dataset model superiority |
| Secondary endpoint extension | GSE264667 HepG2 day 7, Jurkat day 7 | endpoint-object portability after target-level shift and DepMap matching | primary model-audit evidence |
| Candidate secondary extension | MOLM13 mSWI/SNF | registry candidate pending single-target/combinatorial audit | completed endpoint bridge |
| Narrow pathway boundary | Adamson K562 UPR | stress-axis/pathway-boundary candidate | primary endpoint recovery |
| Excluded/future extension | RPE1, CRISPRa, enhancer, stimulation, co-culture contexts | eligibility governance and future modules | current DepMap LOF endpoint evidence |

Current completed external bridge summary:

| Context | Matched targets | Spearman rho | Empirical p | Interpretation |
| --- | ---: | ---: | ---: | --- |
| HCC38 day 14 | 47 | 0.726 | 0.001 | primary bridge/model-audit context |
| HCC1143 day 14 | 48 | 0.779 | 0.001 | primary bridge/model-audit context |
| K562 TF day 7 | 10 | 0.733 | 0.028 | temporal-boundary evidence |
| K562 TF day 13 | 10 | 0.515 | 0.149 | positive direction, weaker temporal support |
| Replogle K562 essential day 6 | 1,882 | 0.402 | 0.001 | large-scale CRISPRi bridge-form evidence |
| Replogle K562 GWPS day 8 | 9,261 | 0.252 | 0.001 | genome-scale weak-but-detectable bridge |
| GSE264667 HepG2 day 7 | 1,000 | 0.493 | 0.001 | secondary cancer-line endpoint extension |
| GSE264667 Jurkat day 7 | 1,687 | 0.311 | 0.001 | secondary lineage-boundary endpoint extension |

Source tables:

```text
reports/external_bridge_form_robustness/observed_shift_depmap_bridge_summary.tsv
reports/external_bridge_form_robustness/dataset_evidence_layers.tsv
reports/gse264667_endpoint_extension/category_grid/gse264667_endpoint_category_grid.tsv
reports/gse264667_endpoint_extension/category_grid/gse264667_endpoint_category_composition.tsv
reports/resource_governance_strengthening/dataset_governance_decision_table.tsv
resource_registry/observed_shift_depmap_bridge_summary.tsv
resource_registry/dataset_evidence_layers.tsv
resource_registry/gse264667_endpoint_category_grid.tsv
resource_registry/gse264667_endpoint_category_composition.tsv
resource_registry/dataset_governance_decision_table.tsv
```

Secondary GSE264667 category-grid summary:

| Context | Q1 anchors | Q4 low-info | Middle | Q2 shift-excess | Q3 dependency-excess | Claim boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| HepG2 day 7 | 133 / 1,000 | 107 / 1,000 | 720 / 1,000 | 14 / 1,000 | 26 / 1,000 | endpoint-object portability only |
| Jurkat day 7 | 185 / 1,687 | 150 / 1,687 | 1,236 / 1,687 | 54 / 1,687 | 62 / 1,687 | endpoint-object portability only |

## Model-Layer Roles

| Entrant/reference | Manuscript role | Claim ceiling |
| --- | --- | --- |
| scGen | strongest current positive entrant | within-context target-observed endpoint-recovery profile |
| CPA | boundary/negative entrant | HCC1143 common/stress-like response collapse |
| GEARS formal | modest formal entrant | pre-specified finite-budget model audit |
| GEARS sweep | sensitivity only | upper-bound/recipe-sensitivity diagnostic |
| scGPT/Geneformer and embedding-ridge controls | secondary/sensitivity entrants | artifact- and output-contract-limited comparison |
| shared_mean | diagnostic reference | shared perturbation architecture reference, not deployable model |
| observed-shift oracle | observed-data reference ceiling | not a predictive model entrant |

Required model-layer checks:

- scGen positive wording must require endpoint alignment plus target-identity
  preservation, not large generated shifts alone.
- CPA HCC1143 wording should emphasize common/stress-like or target-collapsed
  generated response.
- GEARS sweep settings must not be promoted by endpoint-score selection.
- shared_mean total-shift rho must be marked non-estimable when target-level
  total magnitude is constant by construction.
- Figure 3 scatter small multiples should show the six formal or representative
  entrants only: scGen, CPA, GEARS formal, CellOT, scGPT, and Geneformer.
  Linear controls, ridge controls, shared_mean, and null remain in the full
  profile, common-response, and target-identity panels.

## Figure And Source-Data Mapping

| Figure | Role | Source-data location |
| --- | --- | --- |
| Figure 1 | endpoint-recovery resource contract | `figures/Figure_1/Figure_1_source_data.tsv` |
| Figure 2 | primary HCC endpoint-recovery object | `figures/Figure_2/Figure_2_source_data.tsv` |
| Figure 3 | model endpoint-recovery audit | `figures/Figure_3/Figure_3_source_data.tsv` |
| Figure 4 | external bridge-form robustness and boundaries | `figures/Figure_4/Figure_4_source_data.tsv` |
| Figure 5 | response-program annotation and governance | `figures/Figure_5/Figure_5_source_data.tsv` |
| Extended Data Figure 1 | dataset inventory and perturbation-readout QC | `figures/Extended_Data_Figure_1/` |
| Extended Data Figure 2 | primary HCC endpoint-object robustness | `figures/Extended_Data_Figure_2/Extended_Data_Figure_2_source_data.tsv` |
| Extended Data Figure 3 | raw external bridge-form evidence and endpoint-extension eligibility | `figures/Extended_Data_Figure_3/Extended_Data_Figure_3_source_data.tsv` |
| Extended Data Figure 4 | model registry, output-contract status and reproducibility closure | `figures/Extended_Data_Figure_4/Extended_Data_Figure_4_source_data.tsv` |
| Extended Data Figure 5 | null calibration, FDR and model sensitivity | `figures/Extended_Data_Figure_5/Extended_Data_Figure_5_source_data.tsv` |
| Extended Data Figure 6 | common-response and target-identity diagnostics | `figures/Extended_Data_Figure_6/Extended_Data_Figure_6_source_data.tsv` |
| Extended Data Figure 7 | response-level pathway-enrichment details and gene-set provenance | `figures/Extended_Data_Figure_7/Extended_Data_Figure_7_source_data.tsv` |

The source-data registry must include Figure 3 and Extended Data Figure 7:

```text
resource_registry/figure_source_data_manifest.tsv
```

Current checks:

- Figure 3 panel a-e source data are present in `figures/Figure_3/panels/`.
- Extended Data Figure 7 panel a-c source data are present in
  `figures/Extended_Data_Figure_7/panels/`.
- Figure 3 and Extended Data Figure 7 hashes are registered in
  `resource_registry/figure_source_data_manifest.tsv`.

## Extended Data Figure Contract

Final Extended Data titles:

1. Dataset inventory and perturbation-readout quality control.
2. Robustness of the primary HCC endpoint-recovery object.
3. Raw external bridge-form evidence and endpoint-extension eligibility.
4. Model registry, output-contract status and reproducibility closure.
5. Null calibration, multiple-testing control and model-sensitivity analyses.
6. Common-response and target-identity diagnostics for model-generated shifts.
7. Response-level pathway-enrichment details and gene-set provenance.

Required boundaries:

- ED1 is descriptive input QC only; do not include endpoint or model claims.
- ED2 protects the primary HCC endpoint object; panels a-c are bridge
  robustness and panels d-f are category/anchor/covariate governance.
- ED3 contains raw external bridge evidence. HepG2 day 7 and Jurkat day 7 are
  completed secondary endpoint-extension contexts (n=1,000, rho=0.493,
  p=0.001; n=1,687, rho=0.311, p=0.001), not primary model-audit contexts and
  not cross-dataset model-generalization evidence.
- ED4 is compact registry/contract/reproducibility visualization; complete
  tables remain source-data or supplementary tables.
- ED5 q values must be computed and described within pre-specified metric
  families. GEARS sweep is sensitivity/upper-bound evidence only.
- ED6 must answer whether model-generated shifts preserve endpoint-relevant
  and target-specific structure or collapse into shared/common/stress-like
  responses.
- ED7 uses response-level GSEA as annotation. Target-set ORA, if retained, is
  descriptive-only because endpoint-category target counts are small.

Extended Data panel audit checklist columns:

```text
figure_id
panel_id
current_status
reuse_or_redraw
source_data_file
script_file
claim_supported
claim_not_supported
needs_caption_change
needs_source_manifest_update
hash_updated
```

## Pathway-Layer Rules

Primary pathway layer:

- response-level category GSEA using aggregated signed observed-shift vectors.
- response-level contrast GSEA for Q1 anchor versus Q4 low-information and
  Q1 anchor versus retained middle.

Secondary pathway layer:

- target-set ORA only as descriptive category-membership annotation.

Current frozen HCC endpoint categories:

- present: Q1 anchor, Q4 low-information, middle
- absent: Q2/Q3 categories

Required wording:

- Response-level enrichment annotates transcriptomic programs associated with
  endpoint categories.
- Contrast GSEA annotates signed response-program differences between frozen
  endpoint categories.
- It does not define endpoint categories, tune model scoring, or establish
  causal mechanisms for target membership.

Current contrast-GSEA source tables:

```text
reports/category_response_pathway/contrasts/category_response_contrast_signatures.tsv.gz
reports/category_response_pathway/contrasts/category_response_contrast_qc.tsv
reports/category_response_pathway/contrasts/category_response_contrast_gsea_hallmark.tsv
reports/category_response_pathway/contrasts/category_response_contrast_gsea_reactome.tsv
reports/category_response_pathway/contrasts/category_response_contrast_gsea_gobp.tsv
resource_registry/category_response_contrast_gsea_hallmark.tsv
```

References to retain for this layer:

- GSEA original method.
- MSigDB Hallmark collection.

## Reference Checklist

Required reference families:

- Perturb-seq/K562 temporal: Dixit et al.
- Replogle K562 CRISPRi: Replogle et al.
- benchmark landscape: scPerturb and other perturbation-model benchmarks.
- model entrants: GEARS, scGPT, Geneformer, scFoundation, scGen, CPA.
- endpoints: CRISPR DepMap and DEMETER2.
- pathway analysis: GSEA and MSigDB Hallmark.

Do not cite CPA/scGen as evidence that WTShiftBench tested their original broad
out-of-distribution claims. They are evaluated only as entrants under the
WTShiftBench output contract.

## Manuscript Consistency Checks

Before freezing a new manuscript revision:

1. Run the manuscript updater:

```bash
pixi run python scripts/manuscript/update_manuscript_model_endpoint_recovery.py
```

2. Confirm no stale HepG2/Jurkat pending wording remains:

```bash
rg -n "target-level bridge materialization pending|raw eligible; bridge pending|not treated as completed|HepG2/Jurkat raw H5AD files passed an initial candidate audit" \
  README.md docs/benchmark_resource_strengthening_plan_v1.md scripts/manuscript/update_manuscript_model_endpoint_recovery.py
```

3. Confirm no duplicate Extended Data Figure 6/7 legends remain in
   `manuscript/manuscript.docx`.

4. Rebuild source-data registry after figure edits:

```bash
pixi run build-resource-registry
```

5. Confirm Figure 3 and Extended Data Figure 7 source hashes are present:

```bash
rg -n "Figure_3|Extended_Data_Figure_7" resource_registry/figure_source_data_manifest.tsv
```

6. Compile modified Python entry points:

```bash
python -m py_compile \
  src/wtbench/manuscript/figure3_model_endpoint_recovery.py \
  src/wtbench/manuscript/edfigure7_external_pathway.py \
  scripts/pipeline/materialize_gse264667_bridge.py \
  scripts/pipeline/external_bridge_form_robustness.py \
  scripts/pipeline/category_response_pathway.py \
  scripts/pipeline/summarize_category_response_pathway.py \
  scripts/manuscript/update_manuscript_model_endpoint_recovery.py
```
