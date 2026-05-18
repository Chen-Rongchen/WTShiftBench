# Data Availability

All raw data used in WTShiftBench come from public Perturb-seq /
single-cell repositories. The repository ships only:

- per-panel **source data** under `figures/Figure_*/panels/*_source_data.tsv`
  and `figures/Extended_Data_Figure_*/panels/*_source_data.tsv`,
- small precomputed **intermediate tables** under
  `reports/truth_driven_bridge/`, `reports/real_hcc_smoke/`,
  `reports/pathway_response/`, etc., that the figure-build scripts read,
- and a few **derived prediction tables** under `data/predictions/`,
  `data/reference/`, `data/covariates/`.

Raw and processed `h5ad` objects (≈ 14 GB total) are **not** stored in git;
they must be re-downloaded and re-preprocessed before running the
public figure wrappers under `figure_build/`.

## Datasets used in WTShiftBench

| Dataset identifier | Public source | Local target | Used in figures |
| --- | --- | --- | --- |
| HCC38 / HCC1143 (breast cancer) | GEO **GSE241115** | `data/raw/...` then `data/processed/hcc_gears_formal/HCC{38,1143}.h5ad` | Fig 2-4, ED Fig 1-2 |
| Dixit 2016 K562 TF pool, 7 day | GEO **GSE90063** | `data/processed/gse90063/dixit_2016_k562_tf_7d_gse90063.h5ad` | ED Fig 1, ED Fig 3 |
| Dixit 2016 K562 TF pool, 13 day | GEO **GSE90063** | `data/processed/gse90063/dixit_2016_k562_tf_13d_gse90063.h5ad` | ED Fig 1, ED Fig 3 |
| Replogle 2022 K562 essential Perturb-seq | figshare 20029387 (published with [Replogle et al., *Cell* 2022](https://doi.org/10.1016/j.cell.2022.05.013)) | `data/raw/replogle_2022_k562_essential.h5ad` then `data/processed/replogle_k562_essential/essential_processed.h5ad` | ED Fig 1, ED Fig 3 |

DepMap / RNAi DEMETER2 dependency tables (used for the truth-fitness bridge)
are obtained from [depmap.org](https://depmap.org/portal/download/) (DepMap
Public 23Q4 release) and the DEMETER2 v6 RNAi screen.

## Step-by-step reproduction

### 1. Download raw data

```bash
# (a) Replogle 2022 K562 essential — via pertpy (preferred) or figshare fallback
python scripts/download/replogle_k562_essential.py

# (b) GSE241115 (HCC38 / HCC1143) and GSE90063 (Dixit 2016 K562) — via the
#     bundled GEO supplementary fetcher, or by hand from
#     https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE241115
#     https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE90063
python scripts/download/geo_supplementary.py --accession GSE241115
python scripts/download/geo_supplementary.py --accession GSE90063
```

### 2. Preprocess into the layout expected by the figure scripts

```bash
python scripts/preprocess/replogle_k562_essential.py
python scripts/materialize/hcc_gears_formal_h5ad.py
python scripts/materialize/gse90063_k562_h5ad.py
```

After these complete, `bash reproduce_figures.sh` can regenerate the public
figure bundle under `figure_build/output/` and sync the GitHub display snapshot
under `figures/`.

## Code availability

This repository is the canonical source for the analysis and figure-build
code. A versioned, citable public snapshot has been archived at Zenodo under DOI
[10.5281/zenodo.20098897](https://doi.org/10.5281/zenodo.20098897), with
GitHub release tag [`v1.0`](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.0).
