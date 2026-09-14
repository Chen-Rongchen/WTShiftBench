# Historical Stage 2 axis-annotation gene sets

This directory stores local GMT resources used by the historical Stage 2 axis-enrichment workflow. It is not the current v1.2.1 scoring entry point.

The recorded workflow accepts local GMT files only; `scripts/pipeline/axis_enrichment.py` does not download them at runtime and fails when `gmt_path` is absent.

| File | Recorded source |
|---|---|
| `msigdb_hallmark.gmt` | Enrichr / MSigDB_Hallmark_2020 |
| `reactome.gmt` | Enrichr / Reactome_2022 |
| `go_bp.gmt` | Enrichr / GO_Biological_Process_2025 |
| `corum.gmt` | Enrichr / CORUM |

During the recorded run, the official Reactome `ReactomePathways.gmt.zip` endpoint returned HTTP 504, so the accessible Enrichr source was used. This historical substitution is retained for provenance.

Associated historical paths are `configs/axis_enrichment_template_v1.json` and `scripts/pipeline/axis_enrichment.py`; the recorded output is `reports/axis_analysis/axis_enrichment.tsv`. These paths describe the original workflow, not a promise that the current public matrix package executes this separate analysis.

The original note proposed adding a versioned source manifest for tighter database freezing; this English translation does not claim that such additional provenance work has since been completed.
