# WTShiftBench v1.2.1 reproducibility guide

The frozen analysis is distributed through [GitHub Release v1.2.1](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.2.1), whose source commit is `63a00cedcf4960ede5f1b21066cc94a8469cec6c`. Documentation updates do not move that tag or replace its ZIPs. Execute each workflow from its specified package root; do not import the legacy root implementation.

## 1. Download and verify

[manifests/archive_assets.json](manifests/archive_assets.json) lists the three matrix/training/verification ZIPs, download URLs, sizes, SHA256 values, and extraction roots. The release also provides its source ZIP; `release_manifest.json` lists all four assets.

Extract the matrix and training ZIPs into separate new directories without changing their internal paths:

- Matrix execution root: `WTShiftBench_v1.2.1_matrices/`.
- Training execution root: `WTShiftBench_v1.2.1_cellot_training/`.

Do not run from the parent directory, where Pixi could discover an unrelated environment.

This source tree is a browsable code-and-small-table view, not a complete matrix download. Its `archive_manifest.json` is the original matrix ZIP's member manifest, not a claim that all matrix members are present here. Execute full scoring inside the downloaded matrix package.

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

These commands run from **this source directory**, `reproducibility/v1.2.1/`:

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

Historical records may describe information as unavailable at the time. Those statements do not supersede the current definitions. Frozen machine-readable records and ZIPs may retain original-language annotations; these English guides explain their use without changing their evidence.

## 6. Verification and archive status

[Public-download verification](../../../docs/verification/v1.2.1/github_release_verification.json) passed on 14 September 2026: all four ZIPs, 371 matrix-package members, 87 outputs/373 full-inference comparisons, four cutoff-sensitivity tables, and eight gene-effect contexts. The run used the actual downloaded package and a new frozen Pixi prefix; it did not retrain models or replay checkpoints.

The code-version DOI is [10.5281/zenodo.22735108](https://doi.org/10.5281/zenodo.22735108). Its verified source snapshot does not include the matrix/training assets, whose Zenodo data record remains pending. `verification/local/` retains historical local checks and is not relabeled as a public-download run.
