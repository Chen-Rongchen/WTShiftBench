# Public technical changelog

## [1.2.2] — 2026-09-14

- Provide English project, data, reproduction, training, provenance, and citation guides.
- Preserve frozen matrices, expected results, scoring implementations, environments, and historical execution records. Original archive bytes are unchanged.
- Refresh the source-view documentation checksums and language regression checks. The archived matrix manifest still describes the original matrix ZIP, not a newly translated data package.
- Use v1.2.2 for the English source/documentation release and download mirrors; retain scientific assets v1.2.1 and their already validated execution paths. No models, statistics, seeds, or numerical results change.
- All four replacement ZIPs passed anonymous download, SHA256 and ZIP-integrity checks. Retired the earlier v1.2.1 GitHub Release page/attachments afterwards; its Git tag, Git history and Zenodo source record remain preserved. Original scientific recomputation receipts retain their historical URLs and timestamps.
- The new source record is `10.5281/zenodo.22753462`; like the earlier source DOI, it does not contain the matrix/training ZIPs. Persistent data archiving remains a separate step. Post-release documentation does not move the v1.2.2 tag or replace its source ZIP.

## [1.2.1] — 2026-09-12

### Public-download verification — 2026-09-14

- Downloaded all four release ZIPs from public URLs and verified sizes, SHA256 values, and ZIP integrity.
- A new extraction directory and frozen Pixi environment passed 371-member integrity checks, 87-output/373-comparison full inference verification, four cutoff-sensitivity table checks, and eight-context gene-effect sensitivity recomputation. Maximum continuous-statistic difference was approximately 6.1e-9; original tolerances were retained.
- Verified all 1,767 training-package manifest members. This run did not repeat the historical 470 checkpoint replays or two staged retraining checks.
- Verified code-version DOI `10.5281/zenodo.22735108`: its downloaded source matches all 987 files in the fixed GitHub source snapshot. The Zenodo record contains only source code; matrix/training data archiving remains pending.
- Public verification records replace machine paths with placeholders; original evidence remains private. Earlier incomplete-download statements below describe their original dates, not current status.

### Release and distribution scope — 2026-09-13

- Published GitHub Release v1.2.1 at `63a00cedcf4960ede5f1b21066cc94a8469cec6c`, with source, matrix, CellOT training, and local-verification ZIPs plus three description/manifest files.
- All seven assets matched server-side sizes and hashes. Initial anonymous source/local-verification downloads passed; initial matrix/training downloads were incomplete because of timeouts/TLS failures. Later verification is recorded above.
- Retained existing SVGs and paths as historical assets. Final publication figures, manual layout projects, final submission workbooks, manuscripts, responses, and internal editing logs were not uploaded as default attachments.
- Retained numerical source tables, plotting code, scientific provenance, and technical change notes. Programmatically arranged figures are distinguished from final manual layouts; pixel-identical reproduction of the latter is not promised.
- Documentation commits update guidance without moving the frozen tag, replacing release ZIPs, or changing scientific results.

### Public source and CI

- Added the versioned source entry point and passed 17 lightweight tests in GitHub CI.
- Adapted the legacy root public-file validator to check versioned manifests precisely, rather than permitting arbitrary documentation or private material.
- Preserved private-file exclusion and exact-hash exceptions for specified historical JSON records containing machine paths; runtime code/configurations remain restricted.
- Retained scientific configurations, selection chronology, and third-party version identifiers. Public documentation uses scientific release identifiers rather than private submission-iteration labels.

### Scientific assets

- Adopted the registered seed-123 CellOT execution as formal, retaining all seeds 123–127 separately and reporting cross-seed sign changes without best-seed selection or prediction averaging.
- Included three-seed scGen/CPA/GEARS checks and Replogle feature-seed checks, distinguishing training randomness from randomized dimensionality reduction.
- Standardized current gene-effect sensitivity to Public 25Q3 while retaining evidence that historical HepG2/Jurkat values match 23Q4.
- Updated the formal HCC BH family and cutoff sensitivity; added target-delete-one jackknife intervals for homogenization and excess. Retained 46 frozen numerical source tables.
- Added complete scoring dependencies, 87-output/axis registries, and public-source plotting without changing the validated matrix/training ZIP bytes.

## [1.2.0] — 2026-09-10

- Added frozen endpoint/category tables, HCC/Replogle observed and predicted target-by-gene matrices, and explicit axes.
- Added standalone matrix scoring, Pixi locks, statistical seeds, and training/historical provenance. Matrix-to-score reproducibility does not establish recovery of every historical training trajectory.
- Pre-release verification passed 199 full-inference comparisons for 57 model/reference outputs. Maximum differences were approximately 3.6e-15 in HCC and 6.1e-9 after Replogle float32 serialization; P/q and sample-count tolerances were not relaxed.
- Confirmed the WT name without expanding the common HCC 47-gene scoring space or changing predictions and frozen labels. Earlier versions were retained.
- Published only public reproducibility materials, excluding private manuscripts, responses, and development history. Public-download verification and DOI scope were separate from local checks.
