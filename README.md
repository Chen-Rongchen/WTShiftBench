# WTShiftBench

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Public code and figure-reproduction bundle for:

> **WTShiftBench, a cancer-dependency-anchored benchmark resource for
> auditing endpoint-aligned recovery by transcriptomic perturbation models**

WTShiftBench (Whole-Transcriptome Shift Benchmark) is a
cancer-dependency-anchored benchmark resource for virtual perturbation models.
It fixes a cancer-dependency-aligned perturbation recovery object before model
scoring, then audits whether model-generated shifts recover that structure or
collapse into shared/common responses. The repository is organized as a public
code and figure-reproduction bundle: figure panels, per-panel source data,
cached intermediate tables, and the scripts used to rebuild the public figure
bundle are included here; large raw and processed single-cell objects are
downloaded separately from public sources.

## What Is Included

- `figures/`: GitHub-browsable snapshot of the public figure panels and
  source-data TSVs for active Figure 1–4 and Extended Data Figure 1–6,
  including the model endpoint-recovery, external bridge and pathway panels.
- `benchmark/`: publication-facing entry point for the benchmark/resource
  layer, with pointers to governed contexts, model entrants and claim ceilings.
- `source_data/`: publication-facing index for figure source-data files and the
  source-data manifest, matching the layout expected for a paper reproduction
  repository.
- `plots/`: publication-facing notes for rendered plot outputs and figure-style
  guardrails. Composite PNG/PDF figures are reproducible outputs and do not need
  to be staged for ordinary GitHub code/source-data updates.
- `figure_build/`: canonical public wrappers for regenerating the figure bundle.
  Fresh outputs are written to `figure_build/output/`.
- `resource_registry/`: generated governance tables for benchmark contexts,
  endpoint hierarchy, dataset eligibility, model entrant eligibility, metric
  definitions, claim boundaries, and figure source-data files.
- `src/wtbench/`: Python package with truth-bridge, scoring, model-comparison,
  and figure-rendering code.
- `scripts/`: download, preprocessing, materialization, model, and low-level
  manuscript figure-rendering entry points.
- `reports/` and selected `data/` subdirectories: small cached tables and
  derived outputs needed by the public figure scripts.

Raw and processed `h5ad` files are not committed because of size. See
[`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md) for dataset accessions and
download/preprocessing instructions.

## Benchmark Resource Scope

WTShiftBench is intended to fill a benchmark-object gap rather than a
model-development gap. It defines, before model comparison, the
endpoint-aligned perturbation structure that transcriptomic perturbation models
are expected to recover. Existing expression-response benchmarks ask whether a
model predicts perturbation profiles or generalizes across datasets; WTShiftBench
adds a fixed recovery object aligned to external cancer-dependency endpoints.

The current public bundle organizes perturbation datasets into four evidence
layers plus an excluded/future-extension registry. HCC38 and HCC1143 day-14
CROP-seq contexts are the primary model-audit contexts. K562 temporal and
Replogle K562 day-6/8 CRISPRi datasets provide external bridge-form and
temporal/modality/scale-boundary evidence. GSE264667 HepG2/Jurkat day-7 are
completed secondary endpoint-extension contexts, while MOLM13 remains a
candidate secondary cancer-line endpoint-extension context pending
dataset-specific target-mapping and endpoint audits. Adamson K562 UPR is a
narrow pathway/stress-axis boundary candidate. RPE1, CRISPRa, regulatory-
element, stimulation, and co-culture datasets are retained only as excluded or
future-extension registry entries unless a separate endpoint module is defined.

External bridge-form robustness is summarized in
`reports/external_bridge_form_robustness/` and mirrored into
`resource_registry/`. These summaries test whether observed perturbation-shift
magnitude remains aligned with DepMap dependency beyond the primary HCC
contexts. They are not model-generalization tests. GSE264667 HepG2/Jurkat raw
H5AD files passed eligibility checks and now have target-level observed-shift
bridge summaries and endpoint-category grids as secondary endpoint-extension
evidence. Dataset inclusion decisions and claim ceilings are also summarized in
`reports/resource_governance_strengthening/dataset_governance_decision_table.tsv`
and mirrored to `resource_registry/dataset_governance_decision_table.tsv`.

The model panel is likewise intended as a representative entrant audit rather
than an exhaustive perturbation-model leaderboard. Entrants are interpreted
under a unified target-by-gene predicted-shift output contract. In the current
HCC38/HCC1143 model-audit layer, scGen is the strongest positive entrant, CPA is
a boundary/negative entrant, GEARS formal is a modest perturbation-specific
entrant, GEARS sweep settings are sensitivity-only, and shared-mean is a
diagnostic reference rather than a deployable model. CellOT remains a deferred
candidate, and scDisInFact remains registry-only unless the benchmark expands
toward a condition/batch disentanglement question.

## Applying WTShiftBench to a New Dataset

Required inputs:

1. Perturbation expression matrix or target-level shift table.
2. Control-cell definition and perturbation-to-target assignment.
3. External endpoint table, such as DepMap CRISPR dependency.
4. Optional model-predicted perturbation profiles for entrant scoring.

Core outputs:

1. Endpoint-aligned target categories and anchor tiers.
2. Model endpoint-recovery scores and common-response diagnostics.
3. Covariate, endpoint, and temporal compatibility audit reports.
4. Claim-boundary records describing allowed and disallowed interpretations.

Current missing parts are tracked in
[`docs/benchmark_resource_strengthening_plan_v1.md`](docs/benchmark_resource_strengthening_plan_v1.md).
Manuscript-facing claim, figure, and source-data consistency checks are tracked
in [`docs/manuscript_consistency_checklist_v1.md`](docs/manuscript_consistency_checklist_v1.md).
Current figure-production guardrails and the all-figure audit are tracked in
[`docs/figure_audit_v1.md`](docs/figure_audit_v1.md).
The key active items are:

- keep HepG2/Jurkat interpreted as secondary endpoint-extension evidence, not
  as primary model-audit or model-generalization evidence,
- keep Replogle essential/GWPS as large-scale CRISPRi bridge-form and
  modality/scale-boundary evidence, not model-generalization evidence,
- keep active Extended Data Figure 1–6 source data, pathway summaries, and
  manuscript wording synchronized during any later figure edits,
- keep endpoint-category target-gene ORA, if used, as descriptive annotation only.

Pathway analyses should prioritize response-level GSEA over target-set
over-representation. The primary question is whether endpoint categories have
distinct transcriptomic response programs, not whether the small category target
gene lists themselves are mechanistically enriched. In the current HCC38/HCC1143
frozen endpoint grid, response-level GSEA is available for endpoint anchors,
low-information, and middle-band categories; shift-excess and dependency-excess
categories are not reported because they are absent from the frozen HCC grid.
Response-level contrast GSEA is also available for endpoint anchors versus
low-information and endpoint anchors versus retained middle-band targets in
`reports/category_response_pathway/contrasts/`.

All public commands are intended to run from the repository root and use
relative paths. The figure driver sets `PYTHONPATH` automatically; single
wrapper examples show the required environment explicitly.

---

## Requirements

The lightweight resource-registry and figure-reproduction paths run in the
`core` environment. Model production environments are separated because GEARS,
scGPT, and Geneformer have different GPU and package requirements.

- Linux x86_64.
- Conda or Pixi for environment management.
- Public raw datasets listed in [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md)
  for full figure regeneration.
- Optional GPU environments for model-output regeneration.

---

## Installation

```bash
# 1. clone
git clone https://github.com/Chen-Rongchen/WTShiftBench.git
cd WTShiftBench

# 2a. environment via conda
conda env create -f environment.yml
conda activate wtshiftbench
pip install -e .

# 2b. or environment via pixi
pixi install --environment core
pixi run --environment core env-check-core
```

Install model-specific environments only when regenerating model predictions:

```bash
pixi install --environment gears
pixi install --environment scgpt
pixi install --environment geneformer
```

---

## Running WTShiftBench

Build the resource registry:

```bash
pixi run build-resource-registry
```

Regenerate the resource-strengthening evidence layer:

```bash
pixi run run-external-bridge-form-robustness
pixi run build-gse264667-category-grid
pixi run run-category-response-contrast-gsea
pixi run build-dataset-governance-table
pixi run build-resource-registry
```

Run model score-calibration controls:

```bash
pixi run run-model-score-calibration
```

Audit the fixed candidate model-family extension set:

```bash
pixi run audit-candidate-models
```

Prepare CPA HCC input metadata in dry-run mode:

```bash
pixi run prepare-cpa-hcc-inputs
```

Regenerate the public figure bundle after downloading and preprocessing the
public datasets:

```bash
bash reproduce_figures.sh
```

Minimal end-to-end data preparation for public figure regeneration:

```bash
# 1. fetch raw data (~14 GB on disk; see DATA_AVAILABILITY.md for details)
python scripts/download/replogle_k562_essential.py
python scripts/download/geo_supplementary.py --accession GSE241115
python scripts/download/geo_supplementary.py --accession GSE90063

# 2. preprocess to the layout expected by the figure scripts
python scripts/preprocess/replogle_k562_essential.py
python scripts/materialize/hcc_gears_formal_h5ad.py
python scripts/materialize/gse90063_k562_h5ad.py

# 3. regenerate figure_build/output/ and sync figures/
bash reproduce_figures.sh
```

A single public figure wrapper can also be run directly:

```bash
PYTHONPATH=src:scripts:. python figure_build/figure1/build_figure1_truth_object.py
```

---

## Inputs and Outputs

Primary inputs:

- public perturbation-expression datasets listed in
  [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md),
- external dependency endpoints,
- model prediction tables under `data/predictions/` or regenerated by model
  runners,
- configuration recipes under `configs/`.

Primary outputs:

- `resource_registry/*.tsv`: benchmark governance tables,
- `reports/model_score_calibration_v1/`: model score-calibration controls,
- `reports/model_eligibility/`: candidate model-family eligibility audits,
- `figures/**/panels/*_source_data.tsv`: per-panel source data,
- `figure_build/output/`: regenerated public figure bundle,
- `reports/`: cached intermediate tables and scoring outputs.

---

## Quick start

```bash
# fetch raw data
python scripts/download/replogle_k562_essential.py
python scripts/download/geo_supplementary.py --accession GSE241115
python scripts/download/geo_supplementary.py --accession GSE90063

# preprocess
python scripts/preprocess/replogle_k562_essential.py
python scripts/materialize/hcc_gears_formal_h5ad.py
python scripts/materialize/gse90063_k562_h5ad.py

# build resource registry and figures
python scripts/pipeline/build_resource_registry.py --config configs/resource_registry_v1.json
python scripts/pipeline/model_score_calibration_controls.py --config configs/model_score_calibration_controls_v1.json
bash reproduce_figures.sh
```

A `Dockerfile` is provided for building a local figure-reproduction image. No
prebuilt container registry image is required for the public reproduction
bundle:

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
│   ├── myfig/                  Manual Fig. 1 assembly from figures/myfig/
│   ├── figure2/ … figure4/     Main-figure build wrappers
│   ├── ed_figure1/ … ed_figure7/ Extended Data support wrappers
│   └── output/                 Regenerated PNG/source-data bundle
├── figures/                    GitHub display snapshot copied from figure_build/output
│   ├── Figure_1/panels/        PNG / source_data.tsv per panel
│   └── ...
├── benchmark/                  Publication-facing benchmark/resource entry point
├── source_data/                Figure source-data index and manifest
├── plots/                      Plot-output and style guardrail notes
├── resource_registry/          Generated benchmark resource governance TSVs
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

The public figure snapshot is already committed under `figures/`. To rebuild
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

- **GEO GSE241115** — HCC38 / HCC1143 single-cell perturbation atlas (Fig 2–4, ED Fig 1–2)
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

If you use WTShiftBench, please cite the repository below. A Zenodo DOI and
manuscript or preprint citation can be added when available.

**Code repository:**

```bibtex
@software{chen_wtshiftbench_2026,
    author    = {Chen, Rongchen},
    title     = {{WTShiftBench, a cancer-dependency-anchored benchmark resource for auditing endpoint-aligned recovery by transcriptomic perturbation models}},
    year      = {2026},
    url       = {https://github.com/Chen-Rongchen/WTShiftBench},
    note      = {Zenodo DOI pending}
}
```

Zenodo DOI: pending.

---

## License

MIT — see [LICENSE](LICENSE).
