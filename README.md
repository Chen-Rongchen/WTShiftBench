# WTShiftBench

Code, intermediate tables, and figure artefacts for the manuscript

> **Truth-anchored evaluation of perturbation-response models: a fitness-bridge
> benchmark on cancer cell lines and K562 Perturb-seq panels**
> *Submitted to Genome Biology, 2026.*

WTShiftBench is a **truth-first** virtual perturbation benchmark. Rather than
scoring models on aggregate transcriptomic similarity, it (i) defines
structured **bridge architecture objects** that connect single-cell
perturbation truth to cellular-fitness / gene-dependency endpoints
(DepMap / RNAi), (ii) measures whether published perturbation-response models
recover those bridge objects, and (iii) reports separation, anchor tiering,
and covariate / endpoint sensitivity rather than a single leaderboard number.

The repository contains everything needed to regenerate every figure in the
manuscript from public Perturb-seq inputs.

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

# 5. regenerate every figure
bash reproduce_figures.sh
```

A docker image with the figure-reproduction subset is also provided:

```bash
docker build -t wtshiftbench:latest .
docker run --rm -it -v $(pwd)/data:/app/data -v $(pwd)/reports:/app/reports wtshiftbench:latest
```

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
│   ├── manuscript/             Figure-build scripts (one per figure)
│   └── utils/                  Environment probes, conversions
├── figures/                    Per-panel build artefacts (Fig 1-5, ED Fig 1-5)
│   ├── Figure_1/panels/        PNG / PDF / source_data.tsv per panel
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
├── reproduce_figures.sh        End-to-end figure regeneration driver
├── DATA_AVAILABILITY.md        Public dataset accession + download instructions
└── LICENSE                     MIT
```

---

## Reproducing the manuscript figures

After the [Quick start](#quick-start) preprocessing has finished:

| Figure                              | Command                                                          |
| ----------------------------------- | ---------------------------------------------------------------- |
| Figure 1 (truth object)             | `python scripts/manuscript/build_figure1_truth_object.py`        |
| Figure 2 (anchor tiering)           | `python scripts/manuscript/build_figure2_anchor_tiering.py`      |
| Figure 3 (model trade-off)          | `python scripts/manuscript/build_figure3_model_tradeoff.py`      |
| Figure 4 (sweep controls)           | `python scripts/manuscript/build_figure4_sweep_controls.py`      |
| Figure 5 (boundary)                 | `python scripts/manuscript/build_figure6_boundary.py`            |
| Extended Data Figures 1-5           | `python scripts/manuscript/build_extended_data_figure*.py`       |
| Sensitivity / robustness panels     | `python scripts/manuscript/build_sensitivity_*.py`               |

Or simply `bash reproduce_figures.sh` to run them in sequence. Reference panel
artefacts produced by these scripts are cached under `figures/` in the repo so
that reviewers can match expected outputs without rerunning the full pipeline.

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
| Geneformer                  | Install from the official Hugging Face repository: `pip install git+https://huggingface.co/ctheodoris/Geneformer` (pin to the commit recorded in `pixi.toml`). |
| `lm_g_scgpt_ridge`          | Linear control on top of scGPT gene embeddings (this work).           |
| `lm_g_geneformer_ridge`     | Linear control on top of Geneformer gene embeddings (this work).      |
| `lm_train_lowrank`          | Low-rank linear control trained directly on perturbation data.        |

---

## Citing

```bibtex
@article{chen_wtshiftbench_2026,
    author  = {Chen, Rongchen and ...},
    title   = {Truth-anchored evaluation of perturbation-response models},
    journal = {Genome Biology},
    year    = {2026},
    note    = {Submitted}
}
```

A Zenodo DOI for this repository will be added here once the manuscript is
accepted.

---

## License

MIT — see [LICENSE](LICENSE).
