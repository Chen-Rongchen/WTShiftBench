# WTShiftBench

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20098897.svg)](https://doi.org/10.5281/zenodo.20098897)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Public code and figure-reproduction bundle for:

> **Truth-anchored evaluation of perturbation-response models: a fitness-bridge
> benchmark on cancer cell lines and K562 Perturb-seq panels**
> *Submitted to Genome Biology, 2026.*

WTShiftBench is a truth-first benchmark for virtual perturbation models. It
defines bridge architecture objects linking single-cell perturbation responses
to cellular-fitness and gene-dependency endpoints, then asks whether model
predictions recover those structures. The repository is organized for external
reviewers and readers: figure panels, per-panel source data, cached
intermediate tables, and the scripts used to rebuild the public figure bundle
are included here; large raw and processed single-cell objects are downloaded
separately from public sources.

## What Is Included

- `figures/`: GitHub-browsable snapshot of the submitted figure panels and
  source-data TSVs for Figure 1-5 and Extended Data Figure 1-5.
- `figure_build/`: canonical public wrappers for regenerating the figure bundle.
  Fresh outputs are written to `figure_build/output/`.
- `src/wtbench/`: Python package with truth-bridge, scoring, model-comparison,
  and figure-rendering code.
- `scripts/`: download, preprocessing, materialization, model, and low-level
  manuscript figure-rendering entry points.
- `reports/` and selected `data/` subdirectories: small cached tables and
  derived outputs needed by the public figure scripts.

Raw and processed `h5ad` files are not committed because of size. See
[`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md) for dataset accessions and
download/preprocessing instructions.

All public commands are intended to run from the repository root and use
relative paths. The figure driver sets `PYTHONPATH` automatically; single
wrapper examples show the required environment explicitly.

---

## Quick start

```bash
# 1. clone
git clone https://github.com/Chen-Rongchen/WTShiftBench.git
cd WTShiftBench

# 2a. environment via conda (lightweight, figure reproduction only)
conda env create -f environment.yml
conda activate wtshiftbench
pip install -e .

# 2b. or environment via pixi (full model stack: GEARS / scGPT / Geneformer)
pixi install
pixi shell

# 3. fetch raw data (~14 GB on disk; see DATA_AVAILABILITY.md for details)
python scripts/download/replogle_k562_essential.py
python scripts/download/geo_supplementary.py --accession GSE241115
python scripts/download/geo_supplementary.py --accession GSE90063

# 4. preprocess to the layout expected by the figure scripts
python scripts/preprocess/replogle_k562_essential.py
python scripts/materialize/hcc_gears_formal_h5ad.py
python scripts/materialize/gse90063_k562_h5ad.py

# 5. regenerate figure_build/output/ and sync figures/
bash reproduce_figures.sh
```

A `Dockerfile` is provided for building a local figure-reproduction image. No
prebuilt container registry image is required for the submission bundle:

```bash
docker build -t wtshiftbench:latest .
docker run --rm -it \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/figure_build/output:/app/figure_build/output \
  -v $(pwd)/figures:/app/figures \
  wtshiftbench:latest
```

Inside the container, run `bash reproduce_figures.sh` after the public datasets
have been mounted or downloaded into `data/`.

---

## Repository layout

```
WTShiftBench/
├── src/wtbench/                Python package (truth-bridge / scoring / figure)
│   ├── truth_bridge.py
│   ├── bridge_decomposition.py
│   ├── truth_sensitivity.py
│   ├── hcc_prediction_export.py
│   ├── model_expression_scorer.py
│   ├── model_structure_scorer.py
│   ├── baselines/
│   ├── pathway_response/
│   └── manuscript/
├── scripts/
│   ├── download/               GEO / figshare downloaders (2)
│   ├── preprocess/             Raw → processed h5ad (4)
│   ├── materialize/            Build derived tables / signatures (6)
│   ├── pipeline/               Per-model and per-analysis runners (~45)
│   ├── manuscript/             Low-level renderers called by figure_build/
│   └── utils/                  Environment probes, conversions
├── figure_build/               Canonical public figure-build wrappers + outputs
│   ├── figure1/ … figure5/     Main-figure build wrappers
│   ├── ed_figure1/ … ed_figure5/ Extended Data build wrappers
│   └── output/                 Regenerated PNG/source-data bundle
├── figures/                    GitHub display snapshot copied from figure_build/output
│   ├── Figure_1/panels/        PNG / source_data.tsv per panel
│   └── ...
├── reports/                    Cached intermediate tables read by figure scripts
├── data/
│   ├── predictions/            Derived model predictions (this work)
│   ├── reference/              Reference annotation tables
│   ├── covariates/             Per-cell-line covariate matrices
│   └── (raw/, processed/, …)   Not tracked - see DATA_AVAILABILITY.md
├── configs/                    YAML / JSON configs for pipelines and figures
├── tests/                      Unit / smoke tests
├── pixi.toml / environment.yml Reproducible environments
├── Dockerfile                  Containerised figure-reproduction environment
├── reproduce_figures.sh        Regenerate figure_build/output and sync figures/
├── DATA_AVAILABILITY.md        Public dataset accession + download instructions
└── LICENSE                     MIT
```

---

## Reproducing Figures

The submitted figure snapshot is already committed under `figures/`. To rebuild
the public bundle after downloading/preprocessing the public datasets, run:

```bash
bash reproduce_figures.sh
```

The driver runs the canonical wrappers under `figure_build/`, writes fresh
artefacts to `figure_build/output/`, and then syncs that output to `figures/`
for GitHub browsing.

To rebuild one figure, run the corresponding wrapper directly, for example:

```bash
PYTHONPATH=src:scripts:. python figure_build/figure1/build_figure1_truth_object.py
PYTHONPATH=src:scripts:. python figure_build/ed_figure2/build_edfigure2_metric_robustness.py
```

The underlying plotting functions live in `src/wtbench/manuscript/`; the
low-level scripts in `scripts/manuscript/` are kept because the public
`figure_build/` wrappers call them.

---

## Data availability

All raw data are public. See [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md) for
GEO accessions, figshare URLs, and per-figure dataset → file mappings.

Briefly:

- **GEO GSE241115** — HCC38 / HCC1143 single-cell perturbation atlas (Fig 2-4, ED Fig 1-2)
- **GEO GSE90063** — Dixit 2016 K562 TF-pool Perturb-seq, 7 day and 13 day (ED Fig 1, 3)
- **figshare 20029387** — Replogle 2022 K562 essential Perturb-seq (ED Fig 1, 3)
- **DepMap 23Q4 + DEMETER2 v6** — fitness / dependency endpoints (truth-bridge construction)

---

## Models evaluated

The model stack (`pixi.toml` provides feature-pinned environments):

| Model                       | Source                                                                |
| --------------------------- | --------------------------------------------------------------------- |
| GEARS                       | `cell-gears==0.1.2` (PyPI). Trained per cell line.                    |
| scGPT                       | Pretrained checkpoint from the official release.                      |
| Geneformer                  | Install from the official Hugging Face repository: `pip install git+https://huggingface.co/ctheodoris/Geneformer`, or use the `geneformer` pixi environment. |
| `lm_g_scgpt_ridge`          | Linear control on top of scGPT gene embeddings (this work).           |
| `lm_g_geneformer_ridge`     | Linear control on top of Geneformer gene embeddings (this work).      |
| `lm_train_lowrank`          | Low-rank linear control trained directly on perturbation data.        |

---

## Citing

If you use WTShiftBench, please cite both the manuscript and this code release:

**Manuscript:**

```bibtex
@article{chen_wtshiftbench_2026,
    author  = {Chen, Rongchen and ...},
    title   = {Truth-anchored evaluation of perturbation-response models},
    journal = {Genome Biology},
    year    = {2026},
    note    = {Submitted}
}
```

**Code (Zenodo, archived snapshot of `v1.0.1`):**

```bibtex
@software{chen_wtshiftbench_zenodo_2026,
    author    = {Chen, Rongchen},
    title     = {{WTShiftBench: Truth-anchored evaluation of perturbation-response models}},
    year      = {2026},
    publisher = {Zenodo},
    version   = {v1.0.1},
    doi       = {10.5281/zenodo.20098897},
    url       = {https://doi.org/10.5281/zenodo.20098897}
}
```

DOI: [10.5281/zenodo.20098897](https://doi.org/10.5281/zenodo.20098897)

---

## License

MIT — see [LICENSE](LICENSE).
