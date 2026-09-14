# Portable CellOT training and checkpoint replay

The five-seed training archive includes staged cells and the common 47-gene axis for both HCC contexts, original configurations, CellOT source at 522d2b9, the Pixi lock, 470 saved best checkpoints across seeds 123–127, and corresponding predictions. `training_archive_manifest.json` defines the actual members. The historical three-seed candidate contained only 282 checkpoints.

No external pretrained weights are required: networks start from random initialization. The entry point relocates two original absolute data paths while retaining the remaining hyperparameters.

## Train one target from staged inputs

Run from the **training ZIP root**:

```sh
pixi run --frozen --environment cellot python run_cellot.py --seed 123 --context HCC38 --target ARID1A --output retrained_check
```

Omitting `--target` executes all 47 targets in that context. HCC1143 uses the same interface. Verification of one target does not establish successful independent retraining of all 470 fits.

## Replay saved checkpoints without training

```sh
pixi run --frozen --environment cellot python run_cellot.py --mode replay --seed 124 --context HCC1143 --output replay_check
```

The entry point first verifies archive-member hashes, sets Python/NumPy/PyTorch seeds separately for each fit, and uses single-thread deterministic CPU execution. Outputs are compared with frozen predictions for the same seed and target, with maximum absolute error at most 1e-10. Existing output directories are not overwritten; use a new directory for another run. Load only the project checkpoints from this archive, not untrusted weights.

## Interpretation and verified scope

Seed 123 is formal; seeds 124–127 are sensitivity runs. Endpoint correlations vary substantially across seeds. All runs are retained without selecting the best result or averaging predictions. Seeds 126/127 were registered after results for the first three seeds were known; all five were not prespecified in one initial registration.

The workflow begins with staged cells, not raw FASTQ/MTX preprocessing. It does not recover the unrecorded training seed of the original submission checkpoint. Historical checkpoints remain in the original project; all 470 weights in this five-seed archive are revision-time training runs.

Historical local verification covers 470 checkpoint replays and two seed-123 ARID1A staged retraining checks, one per context. The later public-download scoring verification did not repeat those training or replay checks.

This guide describes the English training-package derivative. Public text is translated and member/ZIP hashes are updated, while staged numerical inputs, hyperparameters, seeds, and all checkpoint tensors are retained. Translation provenance preserves original hashes and historical verification scope; it is not a new training or replay validation.
