# WTShiftBench

Code and source-data repository for:

> **WTShiftBench, a cancer-dependency-anchored benchmark resource for
> auditing endpoint-aligned recovery by transcriptomic perturbation models**

WTShiftBench evaluates whether model-generated perturbation shifts recover a
fixed, cancer-dependency-aligned endpoint structure. The audit separates
endpoint recovery, target-identity preservation and output homogenization. It
is not a direct DepMap predictor or a broad model-generalization leaderboard.

## Repository contents

- `benchmark/`: benchmark definition and governed dataset, endpoint, metric and
  model registries.
- `figures/`: editable SVG panels and panel-level source data for Figures 1-4
  and Extended Data Figures 1-6.
- `source_data/`: publication-facing figure source-data index.
- `src/wtbench/`: reusable scoring and figure-generation code.
- `scripts/`: data preparation, model adapters and analysis entry points.
- `configs/`: frozen analysis and model-run configurations.

Large raw single-cell objects, model-training intermediates, manuscripts,
assembled figures and raster exports are not included. Dataset accessions and
preparation notes are listed in
[`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md).

## Environment

The repository uses [Pixi](https://pixi.sh/) for reproducible environments.

```bash
git clone https://github.com/Chen-Rongchen/WTShiftBench.git
cd WTShiftBench

pixi install --environment core
pixi run --environment core env-check-core
```

Model-specific environments are isolated:

```bash
pixi install --environment gears
pixi install --environment scgpt
pixi install --environment geneformer
pixi install --environment cpa
pixi install --environment scgen
pixi install --environment cellot
```

## Reproduction

Build the active registries:

```bash
pixi run --environment core build-resource-registry
```

Validate the public release bundle:

```bash
pixi run --environment core validate-release
```

Regenerate public figure panels after acquiring the required datasets:

```bash
./reproduce_figures.sh
```

Detailed benchmark definitions and scoring boundaries are documented in
[`benchmark/README.md`](benchmark/README.md).

## Citation

The manuscript citation and permanent Zenodo DOI will be added after archival
release. Until then, cite this repository and the corresponding GitHub release.

## License

Released under the [MIT License](LICENSE).
