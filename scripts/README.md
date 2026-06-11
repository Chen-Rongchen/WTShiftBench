# scripts/

Command-line entry points for WTShiftBench. Scripts are grouped by purpose:

| Subdirectory | Purpose | Examples |
| --- | --- | --- |
| `figures/` | Stable builders for active main and Extended Data panels | `build_figure2.py`, `build_extended_data_figure5.py` |
| `download/` | Fetch raw public datasets | `replogle_k562_essential.py`, `geo_supplementary.py` |
| `preprocess/` | Convert raw `h5ad` files to the layout expected by the truth-bridge pipeline | `replogle_k562_essential.py`, `frangieh_2021_melanoma.py`, `replogle_rpe1.py`, `replogle_gwps_k562.py` |
| `materialize/` | Build derived tables / signatures used downstream | `covariates.py`, `gse90063_k562_h5ad.py`, `hcc_gears_formal_h5ad.py`, `per_target_signature.py`, `axis_per_target_signature.py`, `gears_backbone_sweep.py` |
| `pipeline/` | Per-model and per-analysis runners (training, scoring, sensitivity, validation, registry building) | `build_resource_registry.py`, `gears_hcc_predictions.py`, `scgpt_hcc_predictions.py`, `geneformer_hcc_predictions.py`, `truth_bridge_decomposition.py`, `truth_bridge_sensitivity.py`, `closure_pipeline.py`, `validate_closure_artifacts.py`, … |
| `utils/` | Environment probes and ad-hoc converters | `cuda_env_probe.py`, `convert_rnai_demeter2_to_depmap_endpoints.py`, `convert_scp542_rds.R` |

## Conventions

- Each runner takes either a `--config <path-to-config.json>` flag or no arguments, and writes outputs under `reports/` (cached intermediates) or `data/predictions/` (model outputs).
- Configs live under `configs/`; a script never hard-codes any value that a future user would want to override.
- The CLI registry under `configs/runtime/wtbench_cli_v1.json` exposes a small set of high-level commands via `python -m wtbench`.

## Running public figure regeneration

For a one-shot rerun of the public main and Extended Data figure bundle:

```bash
pixi run --environment core build-figures
```

For a single public figure:

```bash
pixi run --environment core python scripts/figures/build_figure3.py --panels-only
```

See `DATA_AVAILABILITY.md` and the top-level `README.md` for the full
end-to-end reproduction recipe.

## Building the resource registry

The benchmark-governance tables can be generated without rerunning models:

```bash
python scripts/pipeline/build_resource_registry.py --config configs/resource_registry_v1.json
```

or via Pixi:

```bash
pixi run --environment core build-registry
```

## Running model score-calibration controls

The model-layer null and diagnostic controls can be run from scorer-ready
prediction matrices:

```bash
python scripts/pipeline/model_score_calibration_controls.py --config configs/model_score_calibration_controls_v1.json
```

or via Pixi:

```bash
pixi run --environment core run-model-score-calibration
```

## Preparing CPA HCC inputs

CPA input metadata can be prepared in dry-run mode first:

```bash
python scripts/pipeline/prepare_cpa_hcc_inputs.py --config configs/cpa_hcc_input_preparation_v1.json
```

Materialize CPA-ready H5AD files only when needed:

```bash
python scripts/pipeline/prepare_cpa_hcc_inputs.py --config configs/cpa_hcc_input_preparation_v1.json --write-h5ad
```
