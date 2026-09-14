# WTShiftBench reproducibility guide — v1.2.0

This is the English source view for [v1.2.0](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.2.0), released on 15 September 2026 at commit `ca6b0ee1562de9e20f12bec432283c55b0e64bca`. Text translation changes source/container hashes but not scientific values, matrix axes, seeds, or checkpoint tensors. Each workflow retains its relative execution paths within its specified package root; do not import the legacy root implementation. Later documentation updates do not move the release tag.

## 1. Download and verify

[manifests/archive_assets.json](manifests/archive_assets.json) lists the three matrix/training/verification ZIPs, download URLs, sizes, SHA256 values, and extraction roots. The release also provides its source ZIP; `release_manifest.json` lists all four assets.

Extract the matrix and training ZIPs into separate new directories without changing their internal paths:

- Matrix execution root: `WTShiftBench_v1.2.0_matrices/`.
- Training execution root: `WTShiftBench_v1.2.0_cellot_training/`.

Do not run from the parent directory, where Pixi could discover an unrelated environment.

This is a browsable code-and-small-table view, not a complete matrix download. `archive_manifest.json` describes the current matrix ZIP, not files necessarily present in this source view. `manifests/file_index.tsv` describes the source view itself. Execute full scoring inside the downloaded matrix package.

## 2. Recompute statistics from frozen matrices

Run these commands from the **extracted matrix package root**, containing `recompute.py`, `pixi.toml`, and `archive_manifest.json`:

```sh
pixi run --frozen --environment core python recompute.py --verify-only
pixi run --frozen --environment core python recompute.py --output recomputed
pixi run --frozen --environment core python recompute_auxiliary.py
```

The complete run recomputes point estimates and the registered CI/P/q statistics for 87 outputs, then compares them with frozen expected tables. `--points-only` is a faster point-estimate check, not full inference verification.

Optional groups are `--group m3`, `--group m4`, `--group m5`, `--group cellot_training_seeds`, `--group other_training_seeds`, and `--group replogle_feature_seeds`.

The auxiliary entry point rebuilds four cutoff-sensitivity tables from archived target-level scores and gene-effect sensitivity in eight contexts from extracted 25Q3 values. It does not reprocess or re-verify every complete upstream DepMap CSV.

Continuous-statistic tolerances are 1e-10 for HCC and 1e-6 for serialized Replogle float32 matrices. P/q values and sample counts use stricter tolerances. The frozen implementation defines each comparison.

## 3. CellOT checkpoint replay and staged training

Run from the **extracted training package root**, containing `run_cellot.py`, staged inputs, and the complete vendor directory:

```sh
pixi run --frozen --environment cellot python run_cellot.py --mode replay --seed 124 --context HCC1143 --output replay_check
pixi run --frozen --environment cellot python run_cellot.py --seed 123 --context HCC38 --target ARID1A --output retrained_check
```

The source-tree `training/cellot/` directory provides browsable entry points, environment files, and licensing, not a standalone training archive. CellOT is initialized from scratch and requires no external pretrained CellOT weights.

Historical local verification covers 470 checkpoint replays and seed-123 staged retraining of one ARID1A target in each HCC context. This is not 470 independently validated retraining runs or complete raw-single-cell-to-model reproduction. The original submitted checkpoint's training seed remains unknown; seed 123 does not recover it.

## 4. Source-table plotting and lightweight tests

These commands run from **this source directory**, `reproducibility/v1.2.0/`:

```sh
pixi run --frozen --environment core python build_figures.py --output outputs/figures
pixi run --frozen --environment core python -m pytest tests -q
```

Plotting reads the 46 frozen CSV/TSV tables in `presentation/Results/` and scientific configurations. It does not require a manuscript or reviewer responses. Function hashes and the D40 path mapping are recorded in `presentation/plot_source_provenance.json`.

The existing entry point produces programmatically arranged composite figures and source manifests, not separate files for every panel. Authors may perform final assembly, typography, and whitespace adjustments privately. Numerical sources and plotting code remain public, but pixel-identical reconstruction of a final manual layout is not promised.

## 5. Objects, runs, and provenance

- [Output/axis registry](manifests/outputs.tsv): 87 outputs with formal, seed-sensitivity, and diagnostic roles; generated references identify their code and seeds.
- [Run registry](provenance/run_registry.tsv): training seeds and feature seeds are separate; original configurations remain authoritative.
- [DepMap provenance](provenance/depmap_provenance.tsv): current 25Q3 inputs are distinct from historical 23Q4 numerical matches.
- [Numerical source index](presentation/INDEX.tsv): 46 tables with hashes and original analysis paths.
- [Data dictionary](docs/data_dictionary.md) and [provenance guide](provenance/README.md).

Historical records may describe information as unavailable at the time; those statements do not supersede current definitions. Their English translations preserve dates and scientific meaning. Translation provenance records original and derivative hashes, and original unmodified records remain private.

## 6. Verification and archive status

[Local verification of this English derivative](verification/local/english_publication_20260915.json) passed on 15 September 2026: 87 outputs/373 full-inference comparisons, four cutoff-sensitivity tables, and eight gene-effect contexts. All 46 numerical source tables retain their numbers, order, and dimensions, and all 470 checkpoint files retain their original bytes. The public-root and current-source tests passed. This does not replace fresh public-download verification.

[Historical public-download verification](../../../docs/verification/v1.2.1/github_release_verification.json) passed on 14 September 2026 for the original packages: 87 outputs/373 full-inference comparisons, four cutoff-sensitivity tables, and eight gene-effect contexts. That run used downloaded packages and a new frozen Pixi prefix; it did not retrain models or replay checkpoints. It does not verify this English derivative's public download.

[Fresh public-download verification](https://github.com/Chen-Rongchen/WTShiftBench/releases/download/v1.2.0/public_download_verification.json) passed for all four current ZIPs, 87 outputs/373 full-inference comparisons, four cutoff-sensitivity tables, and eight gene-effect contexts. The maximum difference was 6.084249104532091e-9, within the original item-specific tolerances. Commands, the loaded scoring module, package versions, UTC timestamps, hashes, and individual comparisons are recorded. This was matrix-to-statistic recomputation, not model retraining or checkpoint replay.

A new version-specific data DOI remains pending. Earlier source-only DOI records are listed in [data availability](../../../DATA_AVAILABILITY.md), not reused for this new distribution. `verification/local/` contains translated historical local receipts and the separately dated English-derivative check, each with its stated scope. The release manifest and subsequent public-verification receipt identify the actual commit, downloads, hashes, and computations verified for this distribution. Pre-verification status fields in the immutable source ZIP describe its packaging time, not later verification; the tag and original ZIPs have not been moved or replaced.
