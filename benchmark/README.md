# WTShiftBench benchmark layer

This directory is the publication-facing entry point for the benchmark/resource
component of WTShiftBench. It mirrors the role of a `benchmark/` folder in a
paper reproduction repository: define the evaluation object, list the governed
contexts, and point to the scripts that regenerate the scored tables.

WTShiftBench is not a direct DepMap predictor and is not a model leaderboard.
It audits whether target-by-gene perturbation-shift outputs recover a fixed
DepMap-aligned endpoint-recovery object.

## Core registries

- `../resource_registry/benchmark_contexts.tsv`: contexts used by the resource.
- `../resource_registry/dataset_eligibility_registry.tsv`: dataset inclusion
  and boundary status.
- `../resource_registry/dataset_evidence_layers.tsv`: primary, external
  bridge-form, secondary endpoint-extension, and excluded/future layers.
- `../resource_registry/model_entrant_registry.tsv`: model and reference
  entrants with claim ceilings.
- `../resource_registry/model_inclusion_exclusion_audit.tsv`: model-family
  inclusion/exclusion logic.
- `../resource_registry/metric_definition_registry.tsv`: endpoint-recovery,
  common-response and target-identity metric definitions.
- `../resource_registry/claim_boundary_registry.tsv`: supported and disallowed
  claims.

## Rebuild commands

From the repository root:

```bash
pixi run build-resource-registry
pixi run python scripts/manuscript/build_extended_data_resource_bundle.py
bash reproduce_figures.sh
```

Large raw single-cell objects are not stored in Git. Dataset acquisition and
preprocessing instructions are tracked in `../DATA_AVAILABILITY.md`.

## Claim boundary

The primary model-audit layer is restricted to HCC38 and HCC1143 because those
contexts have matched endpoint mapping and complete model-output contracts.
K562 temporal, Replogle K562 CRISPRi, and GSE264667 HepG2/Jurkat are used to
test bridge-form detectability, temporal/modality/scale boundaries, and
secondary endpoint-extension. They are not used as evidence of cross-dataset
model generalization.
