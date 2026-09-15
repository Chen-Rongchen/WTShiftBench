# Data availability

Download the analysis assets from [v1.2.0](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.2.0). The [release manifest](https://github.com/Chen-Rongchen/WTShiftBench/releases/download/v1.2.0/release-manifest.json) identifies the source commit, file sizes, and SHA256 checksums. Follow the [reproducibility guide](reproducibility/v1.2.0/README.md) to run the analysis.

## Packages

- **Matrices:** observed and predicted matrices, target/gene axes, endpoint/category tables, configurations, scoring code, and reference results for 87 outputs. Includes the reported training-seed and feature-seed checks.
- **CellOT training:** staged inputs, execution code, and 470 checkpoints across seeds 123–127 and two contexts.
- **Source:** the code snapshot corresponding to the release.
- **Local verification:** records of the supported scoring, checkpoint-replay, and staged-training checks.

The [public-download verification record](https://github.com/Chen-Rongchen/WTShiftBench/releases/download/v1.2.0/public-download-verification.json) documents successful matrix-to-statistic recomputation. It is separate from training validation.

## Original data

| Object | Source | Use |
|---|---|---|
| HCC38 / HCC1143 | GEO GSE241115 | Frozen endpoints and common 47-gene model-scoring space |
| Replogle K562 essential | figshare 20029387 | Day 6; 1,882 targets × 1,024 genes |
| K562 TF | GEO GSE90063 | External-context checks at days 7 and 13 |
| HepG2 / Jurkat | GEO GSE264667 | External-context sensitivity |
| Dependency probability | DepMap Public 25Q3 CRISPRGeneDependency.csv | Primary endpoint; higher values indicate greater dependency |
| Gene effect | DepMap Public 25Q3 CRISPRGeneEffect.csv | Sensitivity; more negative values indicate greater dependency |

The [DepMap registry](reproducibility/v1.2.0/provenance/depmap_provenance.tsv) records ModelIDs, official-file hashes, and extracted-table hashes. Historical HepG2/Jurkat values and missingness match 23Q4; they are not current sensitivity inputs. The original download log and exact internal Chronos build were not recovered. The Replogle `day7` legacy identifier is mapped to the day-6 dataset in the source records.

Complete raw single-cell objects, official DepMap tables, and upstream pretrained weights are not redistributed by default. See [third-party notices](docs/THIRD_PARTY_NOTICES.md) for sources and usage conditions. The MIT code license does not cover all upstream data or weights.

## Archive citation

The current release corresponds to commit `ca6b0ee1562de9e20f12bec432283c55b0e64bca`. Its version-specific data DOI is pending; use the release manifest to identify the current files.

Earlier source-only records, [10.5281/zenodo.22753462](https://doi.org/10.5281/zenodo.22753462) and [10.5281/zenodo.22735108](https://doi.org/10.5281/zenodo.22735108), do not contain the current matrix/training packages. Their relationship to this release is described in the [provenance guide](reproducibility/v1.2.0/provenance/README.md#distribution-history).
