# WTShiftBench benchmark

WTShiftBench defines a fixed endpoint-recovery object before model comparison.
Each entrant provides a target-by-gene predicted perturbation-shift matrix and
is evaluated under the same context-specific target contract.

## Evaluation axes

The active model audit reports:

- total-shift endpoint alignment;
- response-aligned endpoint recovery;
- endpoint-anchor versus low-information separation;
- target-identity preservation;
- output homogenization, quantified as mean off-diagonal cosine similarity
  between predicted target-level shift vectors.

Output homogenization is a warning diagnostic, not a performance metric.
Target-identity preservation compares predicted and observed target-target
similarity geometry. Full definitions are in
[`metric_definition_registry.tsv`](registry/metric_definition_registry.tsv).

## Evidence layers

- **Primary model audit:** HCC38 and HCC1143.
- **Secondary endpoint extension:** HepG2 and Jurkat.
- **Temporal boundary:** K562 TF day 7 and day 13.
- **Scale/target-universe boundary:** Replogle K562 essential and genome-wide
  CRISPRi.

External contexts test bridge-form detectability and attenuation. They do not
establish direct DepMap prediction or broad cross-dataset model generalization.

## Model entrants

The active audit includes formal perturbation-response entrants, repurposed
foundation-model entrants, linear controls and diagnostic references. Entrant
status and allowed interpretations are recorded in:

- [`model_entrant_registry.tsv`](registry/model_entrant_registry.tsv)
- [`model_output_contract_audit.tsv`](registry/model_output_contract_audit.tsv)
- [`claim_boundary_registry.tsv`](registry/claim_boundary_registry.tsv)

Finite-budget runs define sensitivity envelopes and do not replace formal
entries in the primary audit.

## Rebuild

Run from the repository root:

```bash
pixi install --environment core
pixi run --environment core build-resource-registry
pixi run --environment core validate-release
./reproduce_figures.sh
```

Large input objects are acquired separately; see
[`DATA_AVAILABILITY.md`](../DATA_AVAILABILITY.md).
