# WTShiftBench

WTShiftBench (whole-transcriptome shift benchmark) evaluates how perturbation-model outputs preserve dependency-associated ordering, response direction, anchor separation, between-target structure, and homogenization.

## Reproduce the analysis

The frozen core dataset is archived at [Zenodo DOI 10.5281/zenodo.22768933](https://doi.org/10.5281/zenodo.22768933). It contains the six-file matrix/scoring archive, not the separate training package. The original source-code snapshot has a distinct DOI, [10.5281/zenodo.22755330](https://doi.org/10.5281/zenodo.22755330).

Download the [matrix package](https://github.com/Chen-Rongchen/WTShiftBench/releases/download/v1.2.0/WTShiftBench-v1.2.0-matrices.zip) from [v1.2.0](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.2.0). Extract it, install [Pixi](https://pixi.sh), and run these commands inside `WTShiftBench_v1.2.0_matrices/`:

```sh
pixi run --frozen --environment core python recompute.py --verify-only
pixi run --frozen --environment core python recompute.py --output recomputed
pixi run --frozen --environment core python recompute_auxiliary.py
```

These commands verify the extracted files, recompute scores and statistical inference from the matrices, and compare the results with the reference tables. Model retraining is not required.

The [reproducibility guide](reproducibility/v1.2.0/README.md) includes archive checksums, output locations, plotting, and optional CellOT checkpoint replay and training.

## Repository contents

The current analysis is in [`reproducibility/v1.2.0/`](reproducibility/v1.2.0/):

- `src/wtbench/`: scoring and statistical methods.
- `configs/` and `pixi.lock`: analysis settings and software environment.
- `presentation/Results/`: numerical source tables.
- `build_figures.py`: figures generated from the source tables.
- `provenance/`: datasets, model runs, and seeds.

HCC scoring uses 47 genes; Replogle K562 scoring uses 1,882 targets and 1,024 genes. Dataset and training settings are described in the guide.

Root-level analysis scripts and [Existing SVG figures](figures/README.md) belong to earlier versions. Use the versioned directory above for the current analysis.

## Data and license

See [data availability](DATA_AVAILABILITY.md) for data sources and downloads, [third-party notices](docs/THIRD_PARTY_NOTICES.md) for usage conditions, and [LICENSE](LICENSE) for the MIT code license.

The finalized `v1.2.0` source archive includes the current four-main/seven-supplementary plotting implementation and its frozen display tables. Run `bash reproduce_figures.sh` from the repository root. The original matrix/training assets and historical verification receipts are unchanged; no separate figure or patch archive is required. Manual publication typography is outside pixel-exact reproduction scope.

Historical attribution was corrected to Rongchen Chen without changing historical file trees; see the [commit map](reproducibility/v1.2.0/provenance/author_commit_map_20260925.tsv). The finalized source commit is identified by the release manifest. It is not the older source DOI snapshot, and does not replace or modify either published Zenodo record.
