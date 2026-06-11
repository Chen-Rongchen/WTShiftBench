# Model Endpoint-Recovery Interpretation

## Purpose and Claim Ceiling

WTShiftBench does not evaluate perturbation models as direct DepMap predictors.
Each model output is converted into a `target_gene x gene` model-generated
perturbation-shift matrix, and WTShiftBench audits whether those shifts
preserve fixed DepMap-aligned endpoint-relevant structure.

The model-layer question is:

> Does the model-generated perturbation shift preserve DepMap-aligned and
> target-relevant structure, or does it collapse into a shared/common/stress-like
> response?

Allowed claim:

> Predicted-shift-derived features contain varying degrees of DepMap-aligned
> endpoint-recovery information under a within-context, target-observed regime.

Do not claim:

- the model directly predicts DepMap dependency,
- the model predicts essentiality,
- the model predicts viability or causal fitness loss,
- the model generalizes to unseen targets under the current audit,
- the model provides causal dependency inference.

## Evaluation Regime

| Entrant or reference | Training context | Evaluation context | Target status | Pair status | Endpoint supervision | Claim ceiling |
| --- | --- | --- | --- | --- | --- | --- |
| scGen | HCC38 and HCC1143 separately | same context | target-observed | pair-observed | endpoint-not-supervised | within-context endpoint-recovery audit |
| CPA | HCC38 and HCC1143 separately | same context | target-observed | pair-observed | endpoint-not-supervised | within-context endpoint-recovery audit |
| GEARS formal | HCC38 and HCC1143 separately | same context | target-observed | pair-observed | endpoint-not-supervised | finite-budget endpoint-recovery audit |
| GEARS sweep | HCC38 and HCC1143 separately | same context | target-observed | pair-observed | endpoint-not-supervised for audit; endpoint-selected best is not primary | sensitivity / upper-bound diagnostic only |
| scGPT / Geneformer | HCC38 and HCC1143 separately | same context | target-observed | pair-observed | endpoint-not-supervised for scorer-ready outputs | secondary candidate / artifact-limited sensitivity |
| shared-mean baseline | derived diagnostic reference | same context | not a predictive model | not a predictive model | not applicable | shared-architecture diagnostic reference |
| observed-shift oracle | truth-side reference | same context | truth-side observed | not a predictive model | not applicable | reference ceiling, not a model entrant |

This is a within-context, target-observed, pair-observed,
endpoint-not-supervised recovery audit. It is not an unseen-target,
cross-cell-line, or direct DepMap prediction benchmark.

## Output Contract

All model entrants and diagnostic references are reduced to the same scorer
contract:

- rows: evaluated perturbation targets,
- columns: frozen scorer genes / axis-member genes,
- values: model-generated perturbation shift,
- summary fields: total shift magnitude, axis-aligned magnitude, endpoint
  category, common-response metrics, target-identity preservation, and
  endpoint-recovery p/q values.

The primary outputs are:

- `reports/model_endpoint_recovery/model_summary.tsv`,
- `reports/model_endpoint_recovery/target_summary.tsv`,
- `reports/model_endpoint_recovery/category_summary.tsv`,
- `reports/model_endpoint_recovery/target_identity_summary.tsv`,
- `reports/model_endpoint_recovery/common_response_quadrant.tsv`,
- `reports/model_endpoint_recovery/residual_endpoint_recovery.tsv`,
- `reports/model_endpoint_recovery/gears_selection_registry.tsv`.

## Shared-Mean Reference

Total-shift DepMap correlation is not estimated for the shared-mean reference
because its target-level total magnitude is constant by construction within
each cell line. Therefore:

```text
Spearman(predicted_shift_mean_abs, dependency_strength)
```

has no target-level rank variation for `shared_mean_baseline`.

This is not a failed computation and not a negative result. It means the
shared-mean reference is not interpretable for total-magnitude endpoint-rank
alignment. It is used for axis/category, common-response, and target-collapse
diagnostics.

Operational rule:

- compare scGen and other entrants against shared mean for axis/category/common
  diagnostics,
- do not claim that scGen exceeds or fails to exceed shared mean on total-shift
  rank recovery,
- report the explicit status `non_estimable_constant_score` for shared-mean
  total-shift fields.

## GEARS Selection Rule

Only the pre-specified `gears_hcc_formal_v1` configuration is used for the main
GEARS model comparison.

Finite-budget sweep configurations are reported only as sensitivity or
upper-bound diagnostics. They must not be promoted to primary evidence by
selecting the run with the best endpoint-recovery score.

Selection governance is frozen in:

```text
reports/model_endpoint_recovery/gears_selection_registry.tsv
```

Required interpretation:

- `gears_hcc_formal_v1`: primary formal GEARS result,
- `gears_hcc_formal_v1_*`: finite-budget sensitivity only,
- endpoint-selected best settings: diagnostic upper-bound only if discussed.

## P and Q Value Families

Nominal p values and FDR-adjusted q values are reported within declared metric
families rather than as one pooled omnibus correction.

| FDR family | Included tests | Source |
| --- | --- | --- |
| total endpoint alignment | total shift versus DepMap p values | `model_summary.tsv` |
| axis-aligned endpoint alignment | axis-aligned shift versus DepMap and endpoint permutation p values | `model_summary.tsv` |
| target identity | target-label permutation p values | `target_identity_summary.tsv` |
| residual endpoint recovery | residual total and residual axis p values | `residual_endpoint_recovery.tsv` |

The source-data declaration is:

```text
reports/model_endpoint_recovery/source_data/model_endpoint_recovery_pq_values.tsv
```

Reporting rule:

- report nominal p and family-wise q,
- if q is not significant, describe the signal as nominal or suggestive,
- do not use nominal p alone as strong evidence.

## Entrant Roles and Main Interpretation

### scGen

scGen is the most consistent current positive entrant under the current
within-context, target-observed audit.

Key evidence:

- HCC38 total-shift endpoint alignment: rho = 0.487, q = 0.00555.
- HCC38 axis-aligned endpoint permutation: q = 0.0225.
- HCC38 target-identity preservation: rho = 0.431, target-label permutation
  q = 0.0140.
- HCC1143 total-shift endpoint alignment: rho = 0.520, q = 0.00250.
- HCC1143 target-identity preservation: rho = 0.327, target-label permutation
  q = 0.0140.
- HCC1143 axis-aligned endpoint permutation is weaker after correction
  (q = 0.105), so the HCC1143 axis-specific claim should be written as
  suggestive rather than definitive.

Interpretation:

> scGen combines endpoint-aligned recovery with target-identity preservation,
> which makes it the strongest current positive entrant. The claim remains
> bounded to within-context, target-observed recovery and is not direct DepMap
> prediction.

### CPA

CPA is a boundary / negative case, especially in HCC1143.

Key evidence:

- HCC1143 total endpoint alignment is negative (rho = -0.160, q = 0.492).
- HCC1143 axis-aligned endpoint alignment is negative (rho = -0.186).
- HCC1143 target-identity preservation is not supported (rho = 0.006,
  target-label permutation q = 0.606).
- HCC1143 common-response quadrant is `low_recovery/high_common`.

Interpretation:

> CPA HCC1143 exposes common/stress-like or target-collapsed generated response
> behavior rather than endpoint-relevant recovery.

HCC38 CPA has some axis-level signal but does not support a consistent positive
endpoint-recovery claim.

### GEARS

GEARS formal is a modest / partial recovery case.

Key evidence:

- Formal HCC38 total rho = 0.227, q = 0.399.
- Formal HCC38 axis rho = 0.205, endpoint permutation q = 0.225.
- Formal HCC38 target-identity preservation is nominal by target-label
  permutation but not strong after family correction (q = 0.224).
- Formal HCC1143 shows weak endpoint and target-identity support.

Interpretation:

> GEARS shows partial recovery signals under some finite-budget settings, but
> the formal configuration does not support a strong primary endpoint-recovery
> claim. Sweep configurations remain sensitivity evidence.

### scGPT / Geneformer

scGPT and Geneformer remain secondary / artifact-limited candidates unless all
pretrained artifacts and scorer-ready outputs are fully reproducible from the
same output contract.

Interpretation:

> These models can be shown as secondary candidates or sensitivity entrants,
> but should not drive the main model-layer claim unless artifact provenance is
> tightened.

### Shared-Mean Baseline

The shared-mean baseline is a diagnostic reference, not a deployable model or a
leaderboard competitor.

It is used to distinguish:

- model-specific endpoint recovery,
- recurrent shared perturbation architecture,
- common-response or target-collapse behavior.

Because its total magnitude is constant by construction, it is not evaluated
for total-shift rank alignment.

## Figure-Ready Outputs

Recommended model-layer figure panels:

| Panel | Source data | Purpose |
| --- | --- | --- |
| Total shift versus DepMap small multiples | `source_data/model_endpoint_recovery_metrics.tsv` | total endpoint alignment |
| Axis-aligned shift versus DepMap small multiples | `source_data/model_endpoint_recovery_metrics.tsv` | structure-aware endpoint alignment |
| Endpoint-category distributions | `source_data/model_endpoint_category_summary.tsv` | frozen category separation |
| Common-response quadrant | `source_data/model_common_response_metrics.tsv` | endpoint recovery versus common response |
| Target-identity preservation | `source_data/model_target_identity_preservation.tsv` | target-specific structure preservation |
| GEARS selection governance | `source_data/model_registry.tsv` | formal versus sweep claim boundary |

Source-data manifest:

```text
reports/model_endpoint_recovery/source_data/figure_panel_source_manifest.tsv
```

Hash manifest:

```text
reports/model_endpoint_recovery/closure_artifact_hashes.tsv
```

## Manuscript-Ready Summary

WTShiftBench distinguishes endpoint-recovery profiles across perturbation
models. Under a within-context, target-observed regime, scGen currently shows
the most consistent endpoint-aligned and target-specific recovery. CPA,
especially in HCC1143, exposes common/stress-like response collapse. GEARS
shows partial but hyperparameter-sensitive recovery, with sweep runs treated as
sensitivity rather than primary evidence. The shared-mean reference defines the
shared-architecture diagnostic needed to separate model-specific recovery from
recurrent common structure.
