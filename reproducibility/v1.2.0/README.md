# Reproducing WTShiftBench

This directory contains the code and numerical source tables for [v1.2.0](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.2.0). Install [Pixi](https://pixi.sh) before running the commands below.

## Download

Download the matrix package for scoring. The CellOT training package is only needed for checkpoint replay or training. File URLs, SHA256 checksums, and extraction directories are listed in the [asset manifest](manifests/archive_assets.json).

To check a downloaded ZIP, compare the output of `sha256sum filename.zip` with its manifest entry. Extract each package separately and keep its internal paths unchanged.

Release filenames use hyphens without dates. ZIP contents and extraction directories are unchanged; the [release manifest](https://github.com/Chen-Rongchen/WTShiftBench/releases/download/v1.2.0/release-manifest.json) maps filenames retained in historical records to the current downloads.

## Recompute scores

Run inside the extracted `WTShiftBench_v1.2.0_matrices/` directory:

```sh
pixi run --frozen --environment core python recompute.py --verify-only
pixi run --frozen --environment core python recompute.py --output recomputed
pixi run --frozen --environment core python recompute_auxiliary.py
```

The first command checks the package manifest. The second computes endpoint correlation, signed cosine, anchor AUC, identity, homogenization, and registered CI/P/q statistics for 87 outputs. Results are written to `recomputed/` and compared with `expected/`. The third recomputes four cutoff-sensitivity tables and gene-effect sensitivity in eight contexts.

For a faster point-estimate check, add `--points-only`. To run a subset, use `--group m3`, `m4`, `m5`, `cellot_training_seeds`, `other_training_seeds`, or `replogle_feature_seeds`.

Run scoring from the downloaded package, not this browsable source directory: the package includes the matrices, axes, code, and environment needed together.

## CellOT replay and training

Run inside the extracted `WTShiftBench_v1.2.0_cellot_training/` directory:

```sh
pixi run --frozen --environment cellot python run_cellot.py --mode replay --seed 124 --context HCC1143 --output replay_check
pixi run --frozen --environment cellot python run_cellot.py --seed 123 --context HCC38 --target ARID1A --output retrained_check
```

The first command replays saved checkpoints; the second trains from staged inputs. CellOT starts from scratch and needs no external pretrained weights. The package contains seeds 123–127 for both HCC contexts.

## Plotting and tests

Run from this repository's `reproducibility/v1.2.0/` directory:

```sh
pixi run --frozen --environment core python build_figures.py --output outputs/figures
pixi run --frozen --environment core python -m pytest tests -q
```

Plotting uses the 46 CSV/TSV source tables in `presentation/Results/` and writes programmatically arranged figures and source manifests. Final manual layout adjustments are separate.

## Data and model definitions

- HCC scoring uses a common 47-gene space. In-sample and target-held-out settings are recorded per output; they are not a single matched training design.
- Replogle K562 essential day 6 uses 1,882 targets and 1,024 genes, with three target-response-held-out entrants.
- CellOT seed 123 supplies the formal output; seeds 124–127 are separate sensitivity runs. Endpoint correlations change sign across seeds. Registration and adoption dates are retained in the [provenance guide](provenance/README.md).
- Dependency probability and current gene-effect sensitivity use DepMap Public 25Q3. Historical HepG2/Jurkat gene-effect matches to 23Q4 are recorded separately.

Details: [output and axis registry](manifests/outputs.tsv), [run registry](provenance/run_registry.tsv), [DepMap sources](provenance/depmap_provenance.tsv), [source-table index](presentation/INDEX.tsv), and [data dictionary](docs/data_dictionary.md).

## Verification

The [public-download check](https://github.com/Chen-Rongchen/WTShiftBench/releases/download/v1.2.0/public-download-verification.json) passed archive integrity, 87-output/373-comparison full scoring, four cutoff tables, and eight gene-effect contexts. It records commands, environments, hashes, and numerical tolerances. This check did not retrain models or replay checkpoints.

Separate [local records](verification/local/) cover 470 checkpoint replays and staged retraining of one ARID1A target in each HCC context, not all models' raw-data-to-training pipelines.

See [data availability](../../DATA_AVAILABILITY.md) for archive and DOI status.
