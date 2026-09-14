# Historical public figures

This directory preserves previously published SVG panels and source tables at their original paths. These are historical assets and **do not represent the current formal results** or the author's final manually assembled publication figures. English layer identifiers do not change panel geometry or scientific content.

Use the [v1.2.0 reproducibility guide](../reproducibility/v1.2.0/README.md) for current analyses, numerical source tables, and plotting. The panels and legacy commands below are not the current Figure 1–4 / S1–S7 entry point.

| Historical figure | Retained panels | Historical generator |
|---|---|---|
| Figure 1 | a–c | Original design SVGs |
| Figure 2 | a–e | `scripts/figures/build_figure2.py` |
| Figure 3 | a–f | `scripts/figures/build_figure3.py` |
| Figure 4 | a–c | `scripts/figures/build_figure4.py` |
| Extended Data Figure 1 | a–c | `scripts/figures/build_extended_data_figure1.py` |
| Extended Data Figure 2 | a–f | `scripts/figures/build_extended_data_figure2.py` |
| Extended Data Figure 3 | a, containing six subplots | `scripts/figures/build_extended_data_figure3.py` |
| Extended Data Figure 4 | a–b | `scripts/figures/build_extended_data_figure4.py` |
| Extended Data Figure 5 | a–c | `scripts/figures/build_extended_data_figure5.py` |
| Extended Data Figure 6 | a–d | `scripts/figures/build_extended_data_figure6.py` |

Only when examining historical figures, use the old root environment and this historical command; it is not the current plotting command:

```sh
pixi run --environment core build-figures
```

Historical source paths and hashes are in `source_data/figure_source_data_manifest.tsv`. Current numerical sources and plotting mappings are in `reproducibility/v1.2.0/presentation/`. Do not mix these sets.
