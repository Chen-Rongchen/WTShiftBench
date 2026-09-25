# Data availability

The frozen core data archive is published at [10.5281/zenodo.22768933](https://doi.org/10.5281/zenodo.22768933). The [v1.2.0 GitHub release](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.2.0) also provides the analysis assets and the separate CellOT training package. Its [historical release manifest](https://github.com/Chen-Rongchen/WTShiftBench/releases/download/v1.2.0/release-manifest.json) identifies the original source commit, file sizes, and SHA256 checksums. Follow the [reproducibility guide](reproducibility/v1.2.0/README.md) to run the analysis.

The Zenodo data record contains exactly six files: the matrix ZIP, local-verification ZIP, historical GitHub download receipt, README, core manifest, and SHA256SUMS. Its 87-output scoring scope includes 21 formal outputs and the frozen sensitivity/diagnostic outputs. It does not include checkpoints, large training inputs, or a complete raw-data-to-training archive for every model.

## Packages

- **Matrices:** observed and predicted matrices, target/gene axes, endpoint/category tables, configurations, scoring code, and reference results for 87 outputs. Includes the reported training-seed and feature-seed checks.
- **CellOT training:** staged inputs, execution code, and 470 checkpoints across seeds 123–127 and two contexts.
- **Source:** the code snapshot corresponding to the release.
- **Local verification:** records of the supported scoring, checkpoint-replay, and staged-training checks.

The [public-download verification record](https://github.com/Chen-Rongchen/WTShiftBench/releases/download/v1.2.0/public-download-verification.json) documents historical GitHub matrix-to-statistic recomputation of 87 outputs and 373 comparisons, completed on 14 September 2026 UTC. It is separate from training validation and is not a Zenodo fresh-download receipt. Publication of the data DOI does not itself establish that scoring has been rerun from Zenodo downloads; that verification remains separate and will not overwrite the historical receipt.

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

- **Core frozen-output data:** [10.5281/zenodo.22768933](https://doi.org/10.5281/zenodo.22768933).
- **Original source-code snapshot:** [10.5281/zenodo.22755330](https://doi.org/10.5281/zenodo.22755330). This is a separate software object; it does not archive the new commit history or the full matrix/training assets.
- **Training assets:** the separate versioned GitHub CellOT package, not this core data DOI.

The original release/source commit is `ca6b0ee1562de9e20f12bec432283c55b0e64bca`. After correcting author/committer attribution, the content-identical `v1.2.0` tag points to `1b9c1d34f388f5f2595dafce2e03986ee7d01d32`. All historical trees, messages, timestamps and parent relationships are retained; the [complete commit map](reproducibility/v1.2.0/provenance/author_commit_map_20260925.tsv) records both identities and their shared tree IDs. Original source ZIPs, release checksums and verification receipts retain their original bytes and commit identifiers. GitHub-generated source downloads use the corrected tag; they must not be confused with the historical uploaded source ZIP identified by its own SHA256. The new documentation commit on `main` changes only metadata and provenance navigation, not scientific or plotting code.

The deposited core manifest records its assembly-time DOI state (reserved; publication pending). That historical statement is preserved after publication rather than edited to simulate a later verification. MIT applies only to WTShiftBench-authored code; third-party and derived materials retain their source-specific terms. The author confirmed redistribution of the six-file core archive under those terms on 25 September 2026.

Earlier source-only records, [10.5281/zenodo.22753462](https://doi.org/10.5281/zenodo.22753462) and [10.5281/zenodo.22735108](https://doi.org/10.5281/zenodo.22735108), do not contain the current matrix/training packages. Their relationship to this release is described in the [provenance guide](reproducibility/v1.2.0/provenance/README.md#distribution-history).
