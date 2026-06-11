# configs/

Machine-readable recipes used by every entry point under `scripts/` and
`src/wtbench/`.

## Layout

| Group | Contents |
| --- | --- |
| `configs/*.json` | Truth-driven bridge recipes, model formal-evaluation recipes (GEARS / scGPT / Geneformer / linear controls), Dixit supplementary configurations, sensitivity / covariate-audit configurations, axis-validation summaries, and closure-pipeline / artifact-validation configs. |
| `configs/manuscript/` | Figure / Extended-Data / supplementary-table generation configurations. |
| `configs/runtime/` | The dynamic CLI registry (`wtbench_cli_v1.json`) that backs `python -m wtbench`, and its JSON schema. |
| `configs/generated/` | Auto-generated configs produced by sweep batchers (e.g. GEARS backbone hyper-parameter sweep). |
| `configs/feature_registry_v1.json` | Target-side feature registry shared by the linear controls. |
| `configs/checkpoint_registry_v1.yaml` | scGPT / Geneformer checkpoint registry consumed by the model runners. |
| `configs/resource_registry_v1.json` | Source records for generated benchmark resource registry TSVs. |
| `configs/model_score_calibration_controls_v1.json` | Model score-calibration inputs and null-control definitions. |
| `configs/candidate_model_eligibility_v1.json` | Eligibility audit inputs for CPA, CellOT, scGen, and scDisInFact candidate model families. |
| `configs/cpa_hcc_input_preparation_v1.json` | Metadata preparation recipe for CPA-ready HCC AnnData inputs. |

## Conventions

- New recipes go under the appropriate top-level group as JSON.
- Cross-dataset / cross-cell-line parameters live in `configs/**/*.json`;
  scripts only load and execute them.
- New runners should be registered in `configs/runtime/wtbench_cli_v1.json`
  rather than being hard-coded.  Registry callables must be `module:function`
  strings whose target accepts `(config_path: Path)`.
- Supplementary roles must not be promoted into primary-mainline configs.
- For the Dixit / K562 lineage, the canonical default is `13d` (primary
  formal supplementary bridge test) and `7d` is reserved as a temporal
  sensitivity / early-bridge probe.

## Example: regenerating an HCC sensitivity sweep

```bash
PYTHONPATH=src python scripts/pipeline/truth_bridge_sensitivity.py \
    --config configs/truth_bridge_sensitivity_hcc_full_v1.json
```

or via the unified CLI:

```bash
python -m wtbench run truth_bridge_sensitivity_hcc_full
```

(see `wtbench list` for the current command catalogue).
