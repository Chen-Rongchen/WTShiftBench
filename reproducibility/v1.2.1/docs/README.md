# Frozen v1.2.1 matrix archive: scope and execution

This English guide describes the unchanged v1.2.1 matrix archive mirrored in GitHub Release v1.2.2. Its original embedded README was written while the assets were candidates; historical candidate-status text is not the current publication status. For current downloads, source/data DOI distinctions, and public verification, use the [main reproducibility guide](../README.md).

The package covers 87 scoring outputs. The separate five-seed CellOT training archive contains 470 checkpoints. Package manifests define the actual members. Historical local verification and later public-download verification are distinct records.

## Scientific scope

- The registered sampling-corrected object and Public 25Q3 dependency-probability endpoint are unchanged.
- Formal CellOT uses seed 123 in both contexts. Seeds 124–127 measure training-seed sensitivity under the registered recipe; predictions are neither selected by best result nor averaged.
- Additional checks contain 18 scGen/CPA/GEARS training-seed outputs and six Replogle randomized-feature outputs. They do not replace the original formal outputs. Feature-seed checks do not retrain pretrained foundation models.
- The formal 18-output HCC BH family, metric comparisons, and cutoff analysis were updated for the revised formal entrant set.
- Current gene-effect sensitivity consistently uses 25Q3; historical HepG2/Jurkat matches to 23Q4 remain documented separately.
- Homogenization and paired excess use target-delete-one jackknife intervals, re-centering after each deletion where applicable. These intervals do not cover training-seed variation or cell-level measurement uncertainty.

## Run from the extracted matrix package root

```sh
pixi run --frozen --environment core python recompute.py --verify-only
pixi run --frozen --environment core python recompute.py --output recomputed
pixi run --frozen --environment core python recompute_auxiliary.py
```

Optional groups: `m3`, `m4`, `m5`, `cellot_training_seeds`, `other_training_seeds`, and `replogle_feature_seeds`, selected using `--group`. Full execution recomputes point estimates, registered bootstrap/permutation/BH inference, and homogenization intervals. `--points-only` is not full-inference verification.

HCC matrix axes must match exactly; continuous-statistic tolerance is 1e-10. Replogle matrices are serialized as float32 with continuous-statistic tolerance 1e-6. P/q values and sample counts retain stricter checks. Frozen inputs are verified by SHA256 before scoring.

## Verification boundaries

The auxiliary entry point rebuilds four cutoff-sensitivity tables from archived target-level scores and eight-context gene-effect rho/CI/P/q from extracted 25Q3 values. It does not replace provenance verification of complete upstream CSVs.

The separate CellOT training archive supports staged training and checkpoint replay without external pretrained CellOT weights. Including some training scripts in the matrix archive does not make it a complete training package for every model.

On 12 September 2026, local verification passed all 470 checkpoint replays (maximum prediction error 3.55e-15) and one seed-123 ARID1A staged retraining check per HCC context. These are not 470 independently validated retraining runs. On 14 September, the actual public matrix download passed full scoring and auxiliary verification; that run did not repeat the training checks.

Historical scoring tables remain in historical paths. Current references are specified by `expected/` and `reports/revision/finalization_v2/`; do not mix old tables with new predictions. Data-archive DOI completion remains separate from the existing code DOI.
