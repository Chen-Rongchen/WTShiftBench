# Current and historical provenance

Formal CellOT uses seed 123 in both HCC contexts; seeds 124–127 are training-seed sensitivity runs. Recipe registration, formal adoption, and later seed expansion occurred at different times. Consult the frozen amendments and selection chronology. Post-result adoption must not be described as prespecified before the original submission. Seed 123 is not claimed to be the best seed, and predictions are not averaged.

`run_registry.tsv` indexes 87 scoring outputs; it does not replace the original training registry. Unknown/unrecorded values must not be filled with zero. CPA/GEARS CLI seeds, split seeds, and actual initialization seeds can differ; see `reports/revision/finalization_v2/m4/model_training_evaluation_registry.tsv` and the execution configurations. Replogle feature seeds do not represent retraining of the pretrained foundation model.

`depmap_provenance.tsv` distinguishes current Public 25Q3 inputs from historical numerical matches. Unresolved-status statements in old recovery records describe that earlier state. Current gene-effect inputs are specified in `reports/revision/finalization_v2/depmap/`. Historical HepG2/Jurkat values and missingness match 23Q4; those records remain separate from current scoring inputs.

This directory preserves scientific sources, runs, and selection chronology, not private reviewer correspondence or author discussions. Machine paths in historical logs describe recorded runs and are not runtime dependencies. Original analysis-worktree commits document provenance together with file hashes; the public release commit is recorded separately in the release manifest.

Historical machine-readable records retain their original bytes, including original-language annotations. This English guide provides context without retrospectively rewriting the record.
