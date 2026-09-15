# Current and historical provenance

Formal CellOT uses seed 123 in both HCC contexts; seeds 124–127 are training-seed sensitivity runs. Recipe registration, formal adoption, and later seed expansion occurred at different times. Consult the frozen amendments and selection chronology. Post-result adoption must not be described as prespecified before the original submission. Seed 123 is not claimed to be the best seed, and predictions are not averaged.

`run_registry.tsv` indexes 87 scoring outputs; it does not replace the original training registry. Unknown/unrecorded values must not be filled with zero. CPA/GEARS CLI seeds, split seeds, and actual initialization seeds can differ; see `reports/revision/finalization_v2/m4/model_training_evaluation_registry.tsv` and the execution configurations. Replogle feature seeds do not represent retraining of the pretrained foundation model.

`depmap_provenance.tsv` distinguishes current Public 25Q3 inputs from historical numerical matches. Unresolved-status statements in old recovery records describe that earlier state. Current gene-effect inputs are specified in `reports/revision/finalization_v2/depmap/`. Historical HepG2/Jurkat values and missingness match 23Q4; those records remain separate from current scoring inputs.

This directory preserves scientific sources, runs, and selection chronology, not private reviewer correspondence or author discussions. Machine paths in historical logs describe recorded runs and are not runtime dependencies. Original analysis-worktree commits document provenance together with file hashes; the public release commit is recorded separately in the release manifest.

Public historical records are English derivatives with original dates, conclusions, and source hashes retained. Translation provenance maps original and current hashes; original unmodified records are retained privately. Translation does not establish a new execution, recover an unknown seed, or retroactively make a result-informed decision preregistered.

## Distribution history

Commit descriptions on `main` were shortened without changing the original commits' file trees. The [commit map](commit_map.tsv) relates previous identifiers to their equivalents on the current branch. Published tags and existing archive files retain their original identifiers and hashes.

The current v1.2.0 distribution was published on 15 September 2026 at commit `ca6b0ee1562de9e20f12bec432283c55b0e64bca`. The version label was previously used for a different distribution; the exact commit and [release manifest](https://github.com/Chen-Rongchen/WTShiftBench/releases/download/v1.2.0/release-manifest.json) distinguish them.

- The 10 September distribution contained 57 model/reference outputs and 199 full-inference comparisons.
- The 12–13 September distribution, labelled v1.2.1, included the current formal CellOT adoption, five-seed CellOT checks, other model/feature-seed checks, 25Q3 gene-effect sensitivity, and homogenization intervals. Its source commit was `63a00cedcf4960ede5f1b21066cc94a8469cec6c`.
- The 14 September distribution, labelled v1.2.2, updated documentation while retaining the numerical assets. Its source commit was `942108f06f738a4b54783c9d3ef412e9943ef5de`.
- The 15 September distribution uses v1.2.0 and updated textual metadata with new file hashes. Numerical results, axes, seeds, and checkpoint tensors were preserved. Earlier release pages/tags were removed, while Git history and existing source-only DOI records remain.

The [historical public-download receipt](../../../docs/verification/v1.2.1/github_release_verification.json) describes the earlier packages. The [current receipt](https://github.com/Chen-Rongchen/WTShiftBench/releases/download/v1.2.0/public-download-verification.json) verifies the current package contents. Historical and current checks are separate executions. Packaging-time status in source snapshots is not a record of later verification.

External filenames were subsequently shortened without changing ZIPs or verification-record bytes. The release manifest maps original filenames to current downloads; SHA256 values identify the same contents. Source snapshots and original receipts retain their recorded names and URLs. This naming update did not rerun scoring or training.
