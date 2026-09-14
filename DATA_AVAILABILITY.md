# Data and reproducibility assets

The frozen analysis uses scientific assets v1.2.1; the English documentation/source release is **v1.2.2**. See the [guide](reproducibility/v1.2.1/README.md) and [asset manifest](reproducibility/v1.2.1/manifests/archive_assets.json) for download URLs, sizes, SHA256 values, and extraction roots. [GitHub Release v1.2.2](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.2.2) distributes the new source ZIP and the three unchanged scientific ZIPs. Their original names and internal execution paths are retained deliberately.

[10.5281/zenodo.22735108](https://doi.org/10.5281/zenodo.22735108) is the **original v1.2.1 source DOI**, corresponding to commit `63a00cedcf4960ede5f1b21066cc94a8469cec6c`. It is not the English v1.2.2 source DOI and does not contain the matrix/training attachments. Their data archive and version DOI remain pending; a code DOI is not a substitute. See the current release page for separately verified source-archive updates.

On 14 September 2026, publicly downloaded files passed full score recomputation in a new extraction directory and frozen Pixi environment: 87 outputs/373 comparisons, four cutoff-sensitivity tables, and gene-effect sensitivity in eight contexts. See the [verification record](docs/verification/v1.2.1/github_release_verification.json). This run did not retrain models, replay 470 checkpoints, or repeat all raw-cell processing.

## Sources and current use

| Object | Source | Use |
|---|---|---|
| HCC38 / HCC1143 | GEO GSE241115 | Registered preprocessing and frozen endpoints; common 47-gene scoring space |
| Replogle K562 essential | figshare 20029387 | Day 6; 1,882 targets × 1,024 genes; day7 is retained only in a legacy identifier mapping |
| K562 TF | GEO GSE90063 | Registered external-context checks at days 7 and 13 |
| HepG2 / Jurkat | GEO GSE264667 | External-context sensitivity; frozen eligibility rules |
| Dependency probability | DepMap Public 25Q3 CRISPRGeneDependency.csv | Primary endpoint; higher values indicate greater dependency |
| Gene effect | DepMap Public 25Q3 CRISPRGeneEffect.csv | Current sensitivity across contexts; more negative values indicate greater dependency |

The [DepMap registry](reproducibility/v1.2.1/provenance/depmap_provenance.tsv) distinguishes ModelIDs, official-file hashes, and extracted-table hashes. Historical HepG2/Jurkat values and missingness match 23Q4; numerical matching does not recover the original download log. Unavailable exact internal Chronos builds are not inferred.

## Contents and limits

The matrix ZIP contains 87 registered outputs, observed matrices and axes, frozen endpoints/categories, statistical configurations, scoring code, expected comparison tables, and provenance. `expected/` supplies comparison references, not predictions or precomputed answers to the scoring computation.

The CellOT training ZIP contains 470 checkpoints across seeds 123–127 and two contexts, staged inputs, and execution code. Reported seed-check predictions for other models are included in matrix scoring; this does not establish that all models' raw-data processing, pretraining, and checkpoints have been archived.

Numerical source tables, plotting code, and figure-source mappings are public. Manuscripts, responses, final submission workbooks, and manually assembled publication figures are not default public attachments. Existing SVGs are [historical figures](figures/README.md), not current results.

Complete raw h5ad objects, official DepMap tables, and upstream pretrained weights are not redistributed by default. See [third-party notices](docs/THIRD_PARTY_NOTICES.md). Redistribution permissions must be assessed for the actual assets; the project code license does not automatically license upstream data or weights.
