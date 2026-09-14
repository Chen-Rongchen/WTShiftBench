# WTShiftBench

WTShiftBench (whole-transcriptome shift benchmark) audits external dependency ordering, response direction, anchor separation, between-target structure, and homogenization in perturbation-model outputs. These properties are interpreted separately, not combined into a universal leaderboard. Endpoint ordering alone does not establish faithful transcriptional recovery.

## Current release candidate: v1.2.0 — English public assets

Use the [reproducibility guide](reproducibility/v1.2.0/README.md) and the planned [GitHub Release v1.2.0](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.2.0). Public documentation, code comments, runtime messages, and textual metadata are in English. Translated files and ZIPs have new hashes; scientific numerical values, matrix axes, seeds, and checkpoint tensors are unchanged. The release manifest will identify the exact source commit and all asset hashes.

This English derivative passed [local verification](reproducibility/v1.2.0/verification/local/english_publication_20260915.json) on 15 September 2026: 87 outputs and 373 full-inference comparisons, four cutoff-sensitivity tables, and gene-effect sensitivity in eight contexts. All 470 checkpoint files retain their original bytes; this check did not retrain models or replay checkpoints. Publication and fresh public-download verification remain pending until recorded explicitly. The original assets' public-download receipts are historical evidence, not proof of a new download.

A new version-specific archive DOI remains pending. Earlier source-only DOIs are preserved historical records and must not be cited as this package's complete matrix/training archive; see [data availability](DATA_AVAILABILITY.md).

- Code, configurations, numerical source tables, and axis indexes: `reproducibility/v1.2.0/`.
- Matrix and five-seed CellOT training ZIPs: [asset manifest](reproducibility/v1.2.0/manifests/archive_assets.json). Large ZIPs are release assets, not ordinary Git files.
- Sources and usage conditions: [data availability](DATA_AVAILABILITY.md) and [third-party notices](docs/THIRD_PARTY_NOTICES.md).
- Technical changes: [changelog](docs/CHANGELOG.md).
- [Historical public-download verification](docs/verification/v1.2.1/github_release_verification.json): original-package scoring, four cutoff-sensitivity tables, and gene-effect sensitivity in eight contexts passed. That run did not replay checkpoints or retrain models. Its timestamps and original hashes identify the historical assets.

## Scoring and training are different paths

**Scoring requires no retraining.** Download and verify the matrix ZIP, preserve its internal structure, and run `recompute.py` with Pixi from the extracted package root. Statistics are computed from observed/predicted matrices and then compared against `expected/`. Do not combine source-browsing files with legacy code or another environment.

**CellOT replay and training use the training ZIP.** Seed 123 is the formal entrant; seeds 124–127 remain separate sensitivity runs. The five-seed results do not establish that the positive seed-123 ordering is a stable cross-seed capability. Historical local verification covered 470 checkpoint replays and staged retraining of two ARID1A targets, not 470 independent retraining validations.

## Evaluation scope

HCC model scoring uses a common **47-gene** space. This is not synonymous with 47 perturbation targets and does not establish whole-transcriptome recovery. Held-out and in-sample outputs retain their registered settings.

Replogle scoring covers **1,882 targets × 1,024 genes**; the three specified entrants use target-response-held-out leave-one-out evaluation. The WTShiftBench name does not expand these feature spaces.

Both the current dependency-probability endpoint and gene-effect sensitivity use DepMap Public 25Q3. Historical HepG2/Jurkat gene-effect values match 23Q4; this provenance is retained separately, not used as the current sensitivity input.

## Historical versions

At the author's request, the current publication label is v1.2.0 after removal of earlier v1.2.x GitHub release pages and tags. The label has been used before: identify this distribution by its date, exact commit, and hashes, not the label alone. Scientific history and original archive hashes are retained in provenance; Git history and previous Zenodo records are not rewritten. `reproducibility/v1.2.0/` now contains the current source view. Root-level `src/`, `scripts/`, `configs/`, `pixi.toml`, and plotting commands remain legacy/development paths, not the current analysis entry point.

[Existing SVG figures](figures/README.md) remain at their original paths as historical assets, not current results. Do not mix historical panels into the revised analysis. Earlier statements that seed 123 was supplementary, homogenization intervals were unavailable, or gene-effect provenance was unresolved describe earlier versions.

## Public and private materials

Public materials include analysis/plotting code, configurations, environments, seeds, endpoint/category tables, numerical source tables, and scientific provenance. Complete matrices and training assets are distributed separately.

Manuscripts, reviewer responses, final submission workbooks, manually assembled publication figures, layout projects, and internal editing logs remain private. Their numerical CSV/TSV sources and plotting code remain public. Public computation does not require private submission files and does not promise pixel-identical reproduction of final manual layouts.

Public textual material is English. Translated historical records retain their original dates, conclusions, and source hashes; translation does not retrospectively change what was known or verified. Original unmodified records are retained privately.
