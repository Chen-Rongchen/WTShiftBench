# WTShiftBench v1.0.0

This release provides the Cell Genomics submission-oriented WTShiftBench resource bundle.

## Scope

WTShiftBench is a cancer-dependency-anchored benchmark resource for auditing endpoint-aligned recovery by transcriptomic perturbation models. The resource fixes a DepMap-aligned endpoint-recovery object before model scoring, converts model outputs into a common target-by-gene generated-shift contract, and audits endpoint alignment, common-response dominance and target-identity preservation.

## Included

- Active main figure source data and panel outputs for Figure 1-4.
- Active Extended Data source data and panel outputs for Extended Data Figure 1-6.
- Resource registries for dataset eligibility, evidence layers, endpoint categories, model entrants, metric definitions and claim boundaries.
- Figure source-data manifest and artifact hash manifest.
- Supplementary Table 1-10 files and Key Resources Table.
- Reproducibility scripts and figure-build entry points.
- Graphical overview SVG.

## Claim boundary

This release supports endpoint-aligned perturbation-model recovery audit and bridge-form boundary analysis. It does not claim direct DepMap prediction, causal fitness inference, broad cross-dataset model generalization or universal model ranking.

## Primary manuscript-facing files

- `manuscript/manuscript.docx`
- `manuscript/text/cover_letter_v1.md`
- `manuscript/claim_audit_sentence_by_sentence.md`
- `manuscript/additional_files/key_resources_table.tsv`
- `manuscript/additional_files/supplementary_tables/`
- `resource_registry/figure_source_data_manifest.tsv`
- `resource_registry/artifact_hash_manifest.tsv`

## Reproduction entry points

- `reproduce_figures.sh`
- `scripts/pipeline/build_resource_registry.py`
- `scripts/manuscript/streamline_manuscript_and_claim_audit.py`

## Notes

Large raw and processed single-cell objects are not committed to the repository. Dataset accessions and resource roles are documented in the dataset registry and README.
