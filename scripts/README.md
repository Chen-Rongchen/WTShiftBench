# scripts/

Command-line entry points for WTShiftBench. Scripts are grouped by purpose:

| Subdirectory | Purpose | Examples |
| --- | --- | --- |
| `download/` | Fetch raw public datasets | `replogle_k562_essential.py`, `geo_supplementary.py` |
| `preprocess/` | Convert raw `h5ad` files to the layout expected by the truth-bridge pipeline | `replogle_k562_essential.py`, `frangieh_2021_melanoma.py`, `replogle_rpe1.py`, `replogle_gwps_k562.py` |
| `materialize/` | Build derived tables / signatures used downstream | `covariates.py`, `gse90063_k562_h5ad.py`, `hcc_gears_formal_h5ad.py`, `per_target_signature.py`, `axis_per_target_signature.py`, `gears_backbone_sweep.py` |
| `pipeline/` | Per-model and per-analysis runners (training, scoring, sensitivity, validation) | `gears_hcc_predictions.py`, `scgpt_hcc_predictions.py`, `geneformer_hcc_predictions.py`, `truth_bridge_decomposition.py`, `truth_bridge_sensitivity.py`, `closure_pipeline.py`, `validate_closure_artifacts.py`, … |
| `manuscript/` | Build figure panels for the manuscript | `build_figure{1..4}_*.py`, `build_figure6_boundary.py`, `build_extended_data_figure*.py`, `build_sensitivity_*.py` |
| `utils/` | Environment probes and ad-hoc converters | `cuda_env_probe.py`, `convert_rnai_demeter2_to_depmap_endpoints.py`, `convert_scp542_rds.R` |

## Conventions

- Each runner takes either a `--config <path-to-config.json>` flag or no arguments, and writes outputs under `reports/` (cached intermediates) or `data/predictions/` (model outputs).
- Configs live under `configs/`; a script never hard-codes any value that a future user would want to override.
- The CLI registry under `configs/runtime/wtbench_cli_v1.json` exposes a small set of high-level commands via `python -m wtbench`.

## Running figure regeneration

For a one-shot rerun of every main and Extended Data figure:

```bash
bash reproduce_figures.sh
```

For a single panel:

```bash
PYTHONPATH=src python scripts/manuscript/build_figure1_truth_object.py
```

See `DATA_AVAILABILITY.md` and the top-level `README.md` for the full
end-to-end reproduction recipe.
