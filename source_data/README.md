# Figure source data

This directory provides the publication-facing index for figure source data.
Canonical source tables are stored next to each active figure panel under
`../figures/` and indexed by
`../resource_registry/figure_source_data_manifest.tsv`.

The public repository includes editable SVG panels and panel-level source
tables. It intentionally excludes assembled figures, manuscript files,
PNG/PDF exports and model-prediction intermediates.

## Main locations

- `../figures/Figure_*/panels/*_source_data.tsv`: panel-level source data for
  main figures.
- `../figures/Extended_Data_Figure_*/panels/*_source_data.tsv`: panel-level
  source data for Extended Data figures.
- `../resource_registry/figure_source_data_manifest.tsv`: source-data manifest
  binding figure panels to files and hashes.

## Refresh

```bash
pixi install
./reproduce_figures.sh
pixi run --environment core validate-release
```

The rebuild retains the publication-designed Figure 1 SVG panels and
regenerates the remaining active panels through the Pixi `core` environment.
