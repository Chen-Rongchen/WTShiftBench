# Figure source data

This directory is the publication-facing index for figure source data. The
canonical source tables are kept next to each figure panel under `../figures/`
and are indexed by `../resource_registry/figure_source_data_manifest.tsv`.

The repository intentionally does not require committing regenerated composite
PNG/PDF figures. Figures can be rebuilt from the checked-in code and source
tables.

## Main locations

- `../figures/Figure_*/Figure_*_source_data.tsv`: combined source data for each
  main figure.
- `../figures/Figure_*/panels/*_source_data.tsv`: panel-level source data for
  main figures.
- `../figures/Extended_Data_Figure_*/Extended_Data_Figure_*_source_data.tsv`:
  combined source data for each Extended Data figure.
- `../figures/Extended_Data_Figure_*/panels/*_source_data.tsv`: panel-level
  source data for Extended Data figures.
- `../resource_registry/figure_source_data_manifest.tsv`: source-data manifest
  binding figure panels to files and hashes.

## Refresh

```bash
pixi run python scripts/manuscript/build_extended_data_resource_bundle.py
pixi run build-resource-registry
```

After refreshing, stage source-data TSVs and registry/manifests, but do not
stage regenerated PNG/PDF files unless preparing a release archive outside Git.
