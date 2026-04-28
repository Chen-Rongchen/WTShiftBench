# Reserve Figure: PCA Centroid-Arrow Displacement Visualization

## Status

**Frozen reserve figure spec; ready for P2 MVP execution; not part of the submission package unless later editorial review finds a suitable integration slot.**

This is a geometric-intuition panel, not an adjudication-evidence panel. It answers only one question: "Do perturbations produce visible geometric displacement in low-dimensional expression space?" It does not adjudicate bridge existence, model superiority, or causal deconfounding.

---

## P0: Technical Path Verification (Completed 2026-04-26)

### File Paths

| Context | Path | Shape (cells × genes) |
|---|---|---|
| K562 7d | `./data/processed/stage2_gse90063/dixit_2016_k562_tf_7d_gse90063.h5ad` | 28,034 × 23,111 |
| K562 13d | `./data/processed/stage2_gse90063/dixit_2016_k562_tf_13d_gse90063.h5ad` | 15,849 × 21,713 |
| HCC38 | `./data/processed/stage2_hcc_gears_formal/HCC38.h5ad` | 14,175 × 36,601 |
| HCC1143 | `./data/processed/stage2_hcc_gears_formal/HCC1143.h5ad` | 11,405 × 36,601 |

### Obs Fields

All four files contain:
- `is_control` (bool): stable control/perturbation marking
- `target_gene` (string): target gene name, consistent with main-analysis tables
- `num_features` (int): number of guides per cell

All K562 cells are single-guide (`num_features == 1`).

### Expression Layer / Normalization State

| Context | X State | Action Required |
|---|---|---|
| HCC38, HCC1143 | Log-normalized (max ~6.8, no values > 100). Likely `normalize_total(1e4)` + `log1p`. | Use directly. |
| K562 7d, K562 13d | Raw UMI counts (median total ~19K / ~12K, max 1,945 / 736). | **Must apply `sc.pp.normalize_total(target_sum=1e4)` + `sc.pp.log1p()` before PCA.** |

**Cross-context note:** HCC and K562 use different preprocessing states. This is acceptable because each context uses its own PCA basis (HCC38 separate, HCC1143 separate, K562 7d/13d shared). Internal consistency within each basis matters more than cross-context uniformity.

### K562 Preprocessing Lock (Script-Level Rule)

For K562 7d and 13d, raw count matrices are first restricted to the shared gene intersection, followed by library-size normalization to 10,000 counts per cell and log1p transformation. The shared K562 PCA basis is then fitted on the pooled normalized/log-transformed cells from 7d and 13d. Because the 7d/13d cell-count ratio is 0.565 (>1/3), no balanced subsampling is used for PCA fitting.

**Enforcement:** This rule must be hard-coded in the generation script. K562 raw counts must never reach PCA without passing through `normalize_total(target_sum=1e4)` + `log1p()`.

### K562 Shared PCA Basis: Cell Count & Gene Overlap

- **Cell count ratio:** min(15,849, 28,034) / max = 0.565 > 1/3
  - **Decision:** No balanced subsampling needed. Fit shared PCA on pooled 7d + 13d cells directly.
- **Gene overlap:** 23,111 (7d) vs 21,713 (13d). Intersection required before PCA fitting.
  - **Decision:** Use gene-name intersection; project each time point onto the shared basis independently.

---

## P1: Frozen Rules (Execute Before Drawing)

### A. Minimum Cell Count Thresholds

Per target, per context:
- Perturbed cells ≥ 20
- Matched control cells ≥ 50

If a target falls below threshold in a context, omit it from that panel's arrows (do not lower the threshold for visualization).

If the main-analysis pipeline enforces stricter thresholds, adopt the stricter rule.

### B. Highlighted Target Selection Rule (Frozen)

**HCC38 / HCC1143:**
- Rank all qualifying targets by absolute mean perturbation shift.
- Label the top 2 targets by this ranking.
- Retain **PFDN5** as a benchmark-relevant anchor if it passes the cell-count threshold, regardless of rank.
- **Hard cap:** 3 labeled targets per panel maximum.

**K562 7d / 13d:**
- Consider only targets present in **both** 7d and 13d with sufficient cells.
- Rank by average absolute mean perturbation shift across the two time points.
- Label the top 3 targets from this unified ranking in **both** panels.
- This fixed set enables direct temporal comparison of the same perturbations.

**MVP strategy:** Start with 2 labeled targets per panel. Only expand to 3 if readability review shows no label overlap and no visual crowding.

**Why frozen:** Prevents cherry-picking targets that "look good" in PCA. Selection must be rank-driven.

### C. PC–Depth Correlation Audit

For each PCA basis, record:
- `cor(PC1, log10 nCount)`
- `cor(PC2, log10 nCount)`
- `cor(PC1, nFeature)`
- `cor(PC2, nFeature)`

Store these values in:
- `reports/extended_data_candidates/pca_displacement/qc/pca_depth_correlation.tsv`

**Decision rule:**
- If any |r| > 0.5, add the following sentence to the figure caption:
  > "PC axes showed partial correlation with sequencing-depth-related covariates; these panels are therefore used only as low-dimensional geometric visualization."
- Do **not** switch to PC3/PC4 or perform residual PCA. That would over-engineer an intuition panel.

### D. Claim Boundary (Caption Mandatory)

The following sentence **must** appear verbatim in the caption:

> "These panels provide geometric intuition for perturbation displacement and do not replace the pre-specified perturbation-shift metric used for benchmark adjudication."

---

## P2: Execution Steps (Strict Order)

The script must follow this exact sequence to prevent implicit inconsistencies.

**Steps 1–4: HCC contexts**

1. Load HCC38 and HCC1143 h5ad files.
2. Confirm HCC matrices are already log-normalized (assert `X.max() < 20`).
3. Fit context-specific PCA for HCC38.
4. Fit context-specific PCA for HCC1143.

**Steps 5–11: K562 shared basis**

5. Load K562 7d and 13d h5ad files.
6. Intersect genes by gene name across 7d and 13d.
7. Subset both K562 matrices to the shared gene intersection.
8. Apply `sc.pp.normalize_total(target_sum=1e4)` + `sc.pp.log1p()` per cell. (Normalization can be done separately or after concatenation; the key constraint is per-cell, not on raw counts.)
9. Pool 7d + 13d cells.
10. Fit shared K562 PCA basis on the pooled normalized/log-transformed cells.
11. Project both time points independently into the shared basis.

**Steps 12–15: Centroids, selection, audit, export**

12. Compute centroid arrows using **all** eligible cells (perturbed ≥ 20, control ≥ 50). Subsampling applies only to PCA basis fitting when required; centroid computation always uses the full qualified cell set.
13. Select highlighted targets by the frozen P1-B rules.
14. Compute PC–depth correlations (P1-C).
15. Export figure + source data + caption + QC files.

### Gene Intersection Provenance

Before pooling K562 7d and 13d, record:
- `n_genes_7d_raw`
- `n_genes_13d_raw`
- `n_genes_intersection`

Write these values into `qc/pca_basis_provenance.json` so the shared PCA feature space is auditable.

### Step 4: Visualize

Each panel (a–d):
- Very light gray background: all cells or 2D density contour.
- Light gray arrows: all qualifying perturbations.
- Highlighted arrows: 2 targets per panel in MVP; expand to 3 only if readability review passes.
- Labels: only on highlighted targets.
- Control centroid: open circle.
- Perturbation centroid: filled circle.
- Panel labels: a (HCC38), b (HCC1143), c (K562 7d), d (K562 13d).

### Step 5: Output

Directory: `reports/extended_data_candidates/pca_displacement/`

```
extended_data_pca_displacement.png          # 2×2 combined figure
extended_data_pca_displacement_source_data.tsv    # merged source data
extended_data_pca_displacement_caption.md   # frozen caption + claim boundary
qc/
  pca_depth_correlation.tsv                 # P1-C audit
  target_cell_counts.tsv                    # per-target cell counts per context
  k562_cell_counts_7d_13d.tsv               # total counts (balanced-sampling gate)
  pca_basis_provenance.json                 # basis construction metadata (includes gene intersection counts)
```

---

## Frozen Caption

```
Extended Data Fig. X (Reserve). Low-dimensional geometric visualization of perturbation displacement across primary and supplementary contexts.

a,b, Primary HCC contexts (HCC38 and HCC1143). c,d, Supplementary temporal K562 panel (7d and 13d). Within each panel, low-dimensional coordinates are shown for the indicated context, and each arrow connects the centroid of matched control cells to the centroid of perturbed cells for one target. Light gray arrows show all displayed perturbations, whereas labeled arrows highlight a small set of representative targets selected by pre-specified perturbation-shift ranking and, in the HCC panels, anchored to benchmark-relevant exemplars where appropriate. HCC38 and HCC1143 were visualized in context-specific PCA bases, whereas K562 7d and 13d were projected into a shared K562 PCA basis fitted on the pooled set of both time points. These panels provide geometric intuition for perturbation displacement and do not replace the pre-specified perturbation-shift metric used for benchmark adjudication.
```

*(If PC–depth correlation |r| > 0.5, append: "PC axes showed partial correlation with sequencing-depth-related covariates; these panels are therefore used only as low-dimensional geometric visualization.")*

---

## Editorial Gate

This figure is **optional**. Inclusion rules:

1. **Preferred:** Keep as reserve. Do not add to submission package.
2. **If inclusion desired:** Do not create a new Extended Data Figure. Instead:
   - **Option A:** Merge K562 7d/13d panels into an existing K562 temporal Extended Data figure.
   - **Option B:** Replace a low-value illustrative/redundant panel in an existing Extended Data figure.
3. **Never:** Add as a standalone new Extended Data Figure if the 49-panel budget is frozen.

---

## Checklist Summary

- [x] P0-1: K562 7d/13d h5ad paths confirmed
- [x] P0-2: HCC38/HCC1143 h5ad paths confirmed
- [x] P0-3: `is_control` / `target_gene` fields present in all files
- [x] P0-4: K562 cell-count ratio checked (0.565 > 1/3, no balanced subsampling needed)
- [x] P0-5: K562 gene overlap noted (23,111 vs 21,713, intersection required)
- [x] P0-6: Expression layer state identified (HCC = log-normalized; K562 = raw counts)
- [ ] P1-A: Target/control minimum cell-count thresholds applied at draw time
- [ ] P1-B: Highlighted-target selection rule frozen and executed
- [ ] P1-C: PC–depth correlation computed and recorded
- [ ] P1-D: Caption claim-boundary sentence included
- [ ] P2-1: K562 normalization (`normalize_total(1e4)` + `log1p`) applied
- [ ] P2-2: PCA bases built per rules
- [ ] P2-3: Centroids computed with full cell sets
- [ ] P2-4: Figure drawn with manuscript style
- [ ] P2-5: Source data and QC outputs written

---

## P2-MVP Execution Scope

Target output (MVP, 2 labels per panel):

1. `extended_data_pca_displacement.png` — 2×2 centroid-arrow PCA figure
2. `extended_data_pca_displacement_source_data.tsv`
3. `qc/pca_depth_correlation.tsv`
4. `qc/target_cell_counts.tsv`
5. `qc/k562_cell_counts_7d_13d.tsv`
6. `qc/pca_basis_provenance.json`
7. `extended_data_pca_displacement_caption.md`

### First-Round Review Criteria (MVP Pass/Fail)

Before expanding from 2 to 3 labels per panel, confirm all four:

1. **K562 7d/13d shared PCA visual comparability:** The two panels must use the same PC basis, and the displacement patterns should be visually interpretable without axis relabeling.
2. **HCC38/HCC1143 panel independence:** Each panel must be clearly readable on its own; there must be no visual suggestion that HCC38 and HCC1143 share a PCA space or are directly comparable across panels.
3. **Label clarity and non-crowding:** The 2 highlighted targets per panel must be legible without overlapping arrows, labels, or centroids. If 2 labels already crowd the panel, do not expand to 3.
4. **PC depth-dominance check:** PC1/PC2 must not be obviously dominated by `nCount` or `nFeature`. If `pca_depth_correlation.tsv` shows |r| > 0.5, the figure is still acceptable as intuition, but the caption must include the depth-correlation downgrade sentence.

**Decision rule:** If all four criteria pass, optionally expand to 3 labels per panel. If any criterion fails, maintain 2 labels and record the limiting factor in `qc/mvp_review_notes.txt`.
