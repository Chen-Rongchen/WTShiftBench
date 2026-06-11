# Active figure panels

This directory contains only publication-facing, editable SVG panels and their
panel-level source tables. Assembled figures, raster exports and captions are
not part of the public repository.

| Figure | Active panels | Builder |
| --- | --- | --- |
| Figure 1 | a-c | Publication-designed SVG panels retained as provided |
| Figure 2 | a-e | `scripts/figures/build_figure2.py` |
| Figure 3 | a-f | `scripts/figures/build_figure3.py` |
| Figure 4 | a-c | `scripts/figures/build_figure4.py` |
| Extended Data Figure 1 | a-c | `scripts/figures/build_extended_data_figure1.py` |
| Extended Data Figure 2 | a-f | `scripts/figures/build_extended_data_figure2.py` |
| Extended Data Figure 3 | a, containing six small multiples | `scripts/figures/build_extended_data_figure3.py` |
| Extended Data Figure 4 | a-b | `scripts/figures/build_extended_data_figure4.py` |
| Extended Data Figure 5 | a-c | `scripts/figures/build_extended_data_figure5.py` |
| Extended Data Figure 6 | a-d | `scripts/figures/build_extended_data_figure6.py` |

Run all active builders from the repository root:

```bash
pixi run --environment core build-figures
```

Canonical source-data paths and hashes are recorded in
`source_data/figure_source_data_manifest.tsv`.
