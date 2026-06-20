# WTShiftBench

Code and source-data repository for:

> **WTShiftBench: a problem-solving benchmark protocol for endpoint-aligned
> auditing of transcriptomic perturbation model outputs**

Article type: Problem solving protocol.

WTShiftBench evaluates whether model-generated perturbation shifts recover a
fixed endpoint-aligned recovery object anchored to DepMap Public 25Q3 CRISPR
dependency. The audit separates endpoint recovery, target-identity preservation
and output homogenization while keeping claim boundaries explicit. It is not a
direct DepMap predictor, a drug-efficacy model, a cell-death mechanism assay or
a universal model-ranking leaderboard.

## Repository contents

- `benchmark/`: benchmark definition and governed dataset, endpoint, metric and
  model registries.
- `figures/`: editable SVG panels and panel-level source data for Figures 1-4
  and Extended Data Figures 1-6.
- `source_data/`: publication-facing figure source-data index.
- `src/wtbench/`: reusable scoring and figure-generation code.
- `scripts/figures/`: stable entry points for active figure panels.
- `scripts/`: data acquisition, preprocessing, model adapters and analyses.
- `configs/`: frozen, repository-relative analysis and model configurations.
- `reproduce_figures.sh`: public figure and source-data rebuild entry point.

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
pixi run --environment core check-env
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

The active manuscript-aligned figure set is Figures 1-4 and Extended Data
Figures 1-6. The repository provides editable figure panels, panel-level
source-data tables, governed registries, artifact hashes and reproducibility
manifests for this bundle.

Build the active registries:

```bash
pixi run --environment core build-registry
```

Validate the public release bundle:

```bash
pixi run --environment core validate-release
```

Regenerate public figure panels after acquiring the required datasets:

```bash
pixi run --environment core build-figures
```

Detailed benchmark definitions and scoring boundaries are documented in
[`benchmark/README.md`](benchmark/README.md).

The figure-to-script and figure-to-source-data mappings are indexed in
[`source_data/figure_source_data_manifest.tsv`](source_data/figure_source_data_manifest.tsv).
All repository paths are relative to the repository root.

## Verification

```bash
pixi run --environment core test
pixi run --environment core validate-release
```

The release validator rejects manuscripts, assembled figures, raster exports,
prediction intermediates and machine-specific absolute paths.

## Citation

Use the metadata in [`CITATION.cff`](CITATION.cff) and cite the versioned
GitHub release corresponding to the analysis snapshot. A version-specific
Zenodo DOI should be cited once the manuscript-aligned archival release has
been deposited.

## License

Released under the [MIT License](LICENSE).
