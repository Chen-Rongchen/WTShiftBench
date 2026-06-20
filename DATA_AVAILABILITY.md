# Data availability and reproduction

WTShiftBench uses public perturbation and dependency resources. Large raw
single-cell objects and model-prediction intermediates are intentionally not
stored in Git. The repository contains:

- editable SVG panels and panel-level source tables under `figures/`;
- governed benchmark registries under `benchmark/registry/`;
- compact reference gene sets under `data/reference/`;
- primary-context covariate tables under `data/covariates/`.

All paths below are relative to the repository root.

## Public datasets

| Context | Public source | Role |
| --- | --- | --- |
| HCC38 and HCC1143, day 14 | GEO [GSE241115](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE241115) | Primary endpoint object and model audit |
| K562 TF perturbations, days 7 and 13 | GEO [GSE90063](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE90063) | Temporal-boundary evidence |
| K562 essential CRISPRi, day 6 | Replogle et al. figshare [20029387](https://plus.figshare.com/articles/dataset/20029387) | Scale and modality boundary |
| K562 genome-wide CRISPRi, day 8 | Replogle et al. 2022 public Perturb-seq release | Target-universe boundary |
| HepG2 and Jurkat, day 7 | GEO [GSE264667](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE264667) | Secondary endpoint extension |

DepMap Public 25Q3 CRISPR dependency and gene-effect tables are obtained from
the [DepMap data portal](https://depmap.org/portal/download/). The frozen endpoint
release and interpretation boundaries are recorded in
`benchmark/registry/endpoint_registry.tsv`.

## Environment

```bash
pixi install --environment core
pixi run --environment core check-env
```

Model-specific environments are installed only when their predictions must be
regenerated:

```bash
pixi install --environment gears
pixi install --environment scgpt
pixi install --environment geneformer
pixi install --environment cpa
pixi install --environment scgen
pixi install --environment cellot
```

## Data acquisition

The acquisition registry is `configs/dataset_acquisition_registry_v1.json`.
It records expected repository-relative destinations and dataset roles.

```bash
# Generate an auditable acquisition plan.
pixi run --environment core plan-data

# GEO supplementary files.
pixi run --environment core download-gse90063
pixi run --environment core download-gse264667

# Replogle essential CRISPRi object.
pixi run --environment core python scripts/download/replogle_k562_essential.py
```

GSE241115 and Replogle genome-wide files can be downloaded from their public
records and placed at the repository-relative locations recorded in
`configs/dataset_acquisition_registry_v1.json`. Raw-file redistribution terms
remain governed by the original repositories.

## Analysis and figures

After the required raw data, DepMap tables and model outputs have been
materialized:

```bash
pixi run --environment gears materialize-edfig1
pixi run --environment core build-registry
pixi run --environment core build-figures
pixi run --environment core test
pixi run --environment core validate-release
```

`build-figures` regenerates active panel-level SVG and source-data files under
`figures/`. It does not publish manuscripts, assembled figures, raster exports
or prediction intermediates.

The exact figure-to-source mapping and hashes are provided in:

- `source_data/figure_source_data_manifest.tsv`;
- `benchmark/registry/figure_source_data_manifest.tsv`;
- `benchmark/registry/artifact_hash_manifest.tsv`.

## Versioned archive

Use the manuscript-aligned GitHub release for the code and source-data snapshot.
A version-specific Zenodo archival DOI should be cited only after the final
public record is deposited and verified. Do not reuse an older archive DOI for a
new manuscript-aligned release.
