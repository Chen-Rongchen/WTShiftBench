# Reserve Figure: Dataset Familiarization Overview (Version A)

## Status

**Frozen. Reserve candidate only. Not part of the submission package unless later editorial review finds a suitable integration slot.**

This figure is a descriptive dataset-overview panel, not an evidence or adjudication panel. It does not define truth objects, support benchmark adjudication, prove temporal stratification, or validate perturbation efficacy.

---

## Purpose

Provide a single visual entry point that tells the reader:
1. Which benchmark contexts were used and their roles (primary vs supplementary temporal)
2. How perturbation-level mean expression profiles distribute in low-dimensional space
3. The magnitude of whole-transcriptome perturbation displacement across targets

---

## Structure (Frozen)

| Panel | Title | Content |
|---|---|---|
| a | Benchmark contexts | 4-tile strip: HCC38 / HCC1143 / K562 7d / K562 13d with role, cell count, target count, control count, gene count |
| b–e | UMAP of perturbation-level mean profiles | Each point = one target mean expression vector; red star = control mean. Four independent embeddings (one per context). |
| f–i | Target-level perturbation-shift magnitude | Horizontal dot plots: absolute mean whole-transcriptome perturbation shift, ranked. |

---

## Key Design Decisions (Locked)

1. **No target-gene expression change.** The panel c of this figure uses `absolute mean perturbation shift` (whole-transcriptome), not `target-gene expression change` (single-gene). This avoids the "why does target transcript increase after CRISPRi" interpretability trap.
2. **Perturbation-level mean profiles, not single-cell UMAP.** Each UMAP point represents one target's mean expression vector. This aligns with the benchmark truth-side object and avoids depth/density confounding.
3. **Independent embeddings per context.** HCC38, HCC1143, K562 7d, and K562 13d each have their own UMAP basis. No global joint embedding. This prevents cross-context manifold comparison.
4. **K562 preprocessing lock:** `gene intersection` → `normalize_total(target_sum=1e4)` → `log1p` before any downstream computation.

---

## Output

```
reports/extended_data_candidates/dataset_familiarization_v2/
├── ed_candidate_dataset_familiarization_v2.png
├── ed_candidate_dataset_familiarization_v2.pdf
├── ed_candidate_dataset_familiarization_v2_caption.md
├── ed_candidate_v2_umap_source_data.tsv
├── ed_candidate_v2_shift_magnitude_source_data.tsv
└── qc/
    ├── context_metadata.tsv
    ├── umap_panel_info.tsv
    └── provenance.json
```

---

## Frozen Caption

```
Extended Data Figure Candidate. Descriptive overview of benchmark input datasets across primary and supplementary contexts.

a, Benchmark contexts. Primary HCC38 and HCC1143 contexts and the supplementary K562 7d and 13d temporal contexts used in the benchmark are summarized with their corresponding cell and perturbation counts.

b–e, UMAP of perturbation-level mean profiles. Each point represents the mean expression profile of one perturbation target (green) or the matched control aggregate (red star) within the indicated context. Embeddings are shown independently for each context and are intended for descriptive visualization only.

f–i, Target-level perturbation-shift magnitude. For each perturbation target, the displayed value summarizes the absolute mean whole-transcriptome perturbation shift relative to matched controls within the indicated context. Targets are ranked to provide a descriptive overview of transcriptomic perturbation magnitude.

Claim boundary. These panels are provided as descriptive visualization of the input datasets and do not replace the pre-specified perturbation-shift metric and endpoint definitions used for benchmark adjudication.
```

---

## Editorial Gate

- **Preferred:** Keep as reserve. Do not add to submission package.
- **If inclusion desired:** Only if a suitable panel slot opens during Extended Data finalization (e.g., replacing a low-value schematic or redundant table).
- **Never:** Create as a new standalone Extended Data Figure if the 49-panel budget is frozen.

---

## Checklist

- [x] Script frozen: `scripts/manuscript/build_ed_candidate_dataset_familiarization_v2.py`
- [x] Figure generated and reviewed
- [x] Source data exported
- [x] QC files exported
- [x] Caption frozen
- [x] No target-gene expression change (avoided efficacy trap)
- [x] Independent UMAP embeddings per context
- [x] K562 preprocessing: gene intersection + normalize_total(1e4) + log1p
- [x] Claim boundary sentence included in caption
