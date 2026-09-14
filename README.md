# WTShiftBench

WTShiftBench (whole-transcriptome shift benchmark) audits external dependency ordering, response direction, anchor separation, between-target structure, and homogenization in perturbation-model outputs. These properties are interpreted separately, not combined into a universal leaderboard. Endpoint ordering alone does not establish faithful transcriptional recovery.

## Current release: v1.2.2 — English documentation

Use the [English reproducibility guide](reproducibility/v1.2.1/README.md). [GitHub Release v1.2.2](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.2.2) is the English documentation/source release. It retains the frozen **v1.2.1 scientific assets and execution paths**: the three matrix/training/local-verification ZIPs are byte-identical to their previously verified versions. Only the source ZIP and distribution documentation are updated. The release manifest identifies the exact new source commit and all asset hashes.

On 14 September 2026, the original publicly downloaded scientific assets passed full recomputation of 87 outputs and all 373 comparison checks. [10.5281/zenodo.22735108](https://doi.org/10.5281/zenodo.22735108) preserves the **earlier v1.2.1 source snapshot**, not this English source release or the matrix/training archives. Their persistent data archive remains pending. English-release download checks are reported separately from the completed scientific recomputation.

- Code, configurations, numerical source tables, and axis indexes: `reproducibility/v1.2.1/`.
- Matrix and five-seed CellOT training ZIPs: [asset manifest](reproducibility/v1.2.1/manifests/archive_assets.json). Large ZIPs are release assets, not ordinary Git files.
- Sources and usage conditions: [data availability](DATA_AVAILABILITY.md) and [third-party notices](docs/THIRD_PARTY_NOTICES.md).
- Technical changes: [changelog](docs/CHANGELOG.md).
- [Public-download verification](docs/verification/v1.2.1/github_release_verification.json): four ZIPs passed size/SHA256/ZIP checks; 371 matrix-package members, 87 outputs/373 comparisons, four cutoff-sensitivity tables, and gene-effect sensitivity in eight contexts passed verification. All 1,767 training-package manifest members passed integrity checks. This run did not replay checkpoints or retrain models. Earlier incomplete-download reports remain in Git history.

## Scoring and training are different paths

**Scoring requires no retraining.** Download and verify the matrix ZIP, preserve its internal structure, and run `recompute.py` with Pixi from the extracted package root. Statistics are computed from observed/predicted matrices and then compared against `expected/`. Do not combine source-browsing files with legacy code or another environment.

**CellOT replay and training use the training ZIP.** Seed 123 is the formal entrant; seeds 124–127 remain separate sensitivity runs. The five-seed results do not establish that the positive seed-123 ordering is a stable cross-seed capability. Historical local verification covered 470 checkpoint replays and staged retraining of two ARID1A targets, not 470 independent retraining validations.

## Evaluation scope

HCC model scoring uses a common **47-gene** space. This is not synonymous with 47 perturbation targets and does not establish whole-transcriptome recovery. Held-out and in-sample outputs retain their registered settings.

Replogle scoring covers **1,882 targets × 1,024 genes**; the three specified entrants use target-response-held-out leave-one-out evaluation. The WTShiftBench name does not expand these feature spaces.

Both the current dependency-probability endpoint and gene-effect sensitivity use DepMap Public 25Q3. Historical HepG2/Jurkat gene-effect values match 23Q4; this provenance is retained separately, not used as the current sensitivity input.

## Historical versions

`reproducibility/v1.2.0/` and existing tags remain historical records. The v1.2.1 Git tag and its Zenodo source record are retained even when its GitHub Release page and attachments are retired; current asset links use v1.2.2. Root-level `src/`, `scripts/`, `configs/`, `pixi.toml`, and plotting commands are legacy/development paths, not the current analysis entry point.

[Existing SVG figures](figures/README.md) remain at their original paths as historical assets, not current results. Do not mix historical panels into the revised analysis. Earlier statements that seed 123 was supplementary, homogenization intervals were unavailable, or gene-effect provenance was unresolved describe earlier versions.

## Public and private materials

Public materials include analysis/plotting code, configurations, environments, seeds, endpoint/category tables, numerical source tables, and scientific provenance. Complete matrices and training assets are distributed separately.

Manuscripts, reviewer responses, final submission workbooks, manually assembled publication figures, layout projects, and internal editing logs remain private. Their numerical CSV/TSV sources and plotting code remain public. Public computation does not require private submission files and does not promise pixel-identical reproduction of final manual layouts.

Current reading guides are in English. Frozen machine-readable provenance and archived execution logs may retain original-language annotations; documentation translation does not silently rewrite those records.
