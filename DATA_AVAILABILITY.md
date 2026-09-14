# Data and reproducibility assets

The current English publication is **v1.2.0**, released on 15 September 2026 at commit `ca6b0ee1562de9e20f12bec432283c55b0e64bca`. See the [guide](reproducibility/v1.2.0/README.md), [asset manifest](reproducibility/v1.2.0/manifests/archive_assets.json), and [GitHub Release v1.2.0](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.2.0). Text translation changes source/container hashes but preserves numerical results, matrix axes, seeds, and checkpoint tensors. Relative execution paths within each package are retained. [Fresh public-download verification](https://github.com/Chen-Rongchen/WTShiftBench/releases/download/v1.2.0/public_download_verification.json) passed all four ZIP hashes, 87-output/373-comparison full inference, four cutoff-sensitivity tables, and gene-effect sensitivity in eight contexts. No original tolerances were relaxed, and no model retraining or checkpoint replay was performed in this check.

A new code/data version DOI remains pending. Preserved historical source-only records [10.5281/zenodo.22753462](https://doi.org/10.5281/zenodo.22753462) and [10.5281/zenodo.22735108](https://doi.org/10.5281/zenodo.22735108) correspond to commits `942108f06f738a4b54783c9d3ef412e9943ef5de` and `63a00cedcf4960ede5f1b21066cc94a8469cec6c`, respectively. They neither identify this English derivative nor contain the complete matrix/training assets.

Earlier v1.2.x GitHub release pages and tags were removed by the author, who requested the v1.2.0 label for this distribution. Git history and earlier Zenodo records remain. Cite the exact new commit and archive hashes, not the reused version label or an old DOI alone.

On 14 September 2026, the original publicly downloaded files passed 87-output/373-comparison full scoring, four cutoff-sensitivity tables, and eight-context gene-effect sensitivity in a new directory and frozen Pixi environment. The [historical receipt](docs/verification/v1.2.1/github_release_verification.json) retains that scope: no retraining, checkpoint replay, or complete raw-cell reprocessing. Fresh verification of the current English derivative is recorded separately; publication/public-download status must not be inferred from the old receipt.

## Sources and current use

| Object | Source | Use |
|---|---|---|
| HCC38 / HCC1143 | GEO GSE241115 | Registered preprocessing and frozen endpoints; common 47-gene scoring space |
| Replogle K562 essential | figshare 20029387 | Day 6; 1,882 targets × 1,024 genes; day7 is retained only in a legacy identifier mapping |
| K562 TF | GEO GSE90063 | Registered external-context checks at days 7 and 13 |
| HepG2 / Jurkat | GEO GSE264667 | External-context sensitivity; frozen eligibility rules |
| Dependency probability | DepMap Public 25Q3 CRISPRGeneDependency.csv | Primary endpoint; higher values indicate greater dependency |
| Gene effect | DepMap Public 25Q3 CRISPRGeneEffect.csv | Current sensitivity across contexts; more negative values indicate greater dependency |

The [DepMap registry](reproducibility/v1.2.0/provenance/depmap_provenance.tsv) distinguishes ModelIDs, official-file hashes, and extracted-table hashes. Historical HepG2/Jurkat values and missingness match 23Q4; numerical matching does not recover the original download log. Unavailable exact internal Chronos builds are not inferred.

## Contents and limits

The matrix ZIP contains 87 registered outputs, observed matrices and axes, frozen endpoints/categories, statistical configurations, scoring code, expected comparison tables, and provenance. `expected/` supplies comparison references, not predictions or precomputed answers to the scoring computation.

The CellOT training ZIP contains 470 checkpoints across seeds 123–127 and two contexts, staged inputs, and execution code. Reported seed-check predictions for other models are included in matrix scoring; this does not establish that all models' raw-data processing, pretraining, and checkpoints have been archived.

Numerical source tables, plotting code, and figure-source mappings are public. Manuscripts, responses, final submission workbooks, and manually assembled publication figures are not default public attachments. Existing SVGs are [historical figures](figures/README.md), not current results.

Complete raw h5ad objects, official DepMap tables, and upstream pretrained weights are not redistributed by default. See [third-party notices](docs/THIRD_PARTY_NOTICES.md). Redistribution permissions must be assessed for the actual assets; the project code license does not automatically license upstream data or weights.
