# Stage 2 Frangieh 2021 Melanoma Admission Contract v1

## 1. Document Scope

**`Frangieh 2021 melanoma + TIL co-culture`** as tumor-immune complex exploratory / boundary test.

This contract replaces the legacy `dixit_2016_raw.h5ad` identity with the correct dataset name.
The file at `data/raw/stage1a/candidates/dixit_2016_raw.h5ad` is confirmed to be Frangieh et al. 2021 melanoma + TIL co-culture Perturb-CITE-seq data (not Norman 2019, not Dixit 2016).

## 2. Data Identity

### 2.1 Local File

```
Path: data/raw/stage1a/candidates/dixit_2016_raw.h5ad
Processed: data/processed/stage2_frangieh_2021_melanoma/frangieh_2021_processed.h5ad
Shape: (218331, 23712) cells × genes
obs.condition: Control / IFNγ / Co-culture
obs.MOI: 0-19 (multiplicity of infection)
obs.sgRNA: 818 unique guides → 250 unique extracted genes
```

### 2.2 Dataset Role

**NOT ELIGIBLE as formal bridge anchor** — melanoma cell lines (A375, Hs 294T, A101D, etc.) are not present in DepMap CRISPR gene effect or dependency datasets.

### 2.3 Paper Identity (Likely)

Frangieh et al. 2021 — likely "Multiplexed single-cell profiling of post-transcriptional regulators enables genetic dissection of complex immune programs" or similar. Requires external confirmation of exact publication.

## 3. Gene Namespace

- `sgRNA` column format: `GENENAME_number` (e.g., `IFNGR2_2`)
- Gene extraction: `rsplit('_', 1)[0]` → gene symbol
- 250 unique extracted genes
- DepMap mapping: melanoma lines NOT in DepMap CRISPR → **no bridge endpoint available**

## 4. DepMap Endpoint Check

### 4.1 Melanoma in DepMap CRISPR

Checked cell lines: A375 (ACH-000219), Hs 294T (ACH-000014), A101D (ACH-000008), WM-115 (ACH-000304), Hs 852.T (ACH-000274)

**Result: NONE of these melanoma lines are present in DepMap CRISPRGeneEffect.csv or CRISPRGeneDependency.csv**

### 4.2 Verdict

**NO DepMap endpoint available for this dataset.** It cannot serve as a formal external bridge/generalization anchor. It can only be used as an exploratory dataset to test whether A0 architecture form is present in a tumor-immune complex context, without bridge quantification.

## 5. What This Dataset CAN and CANNOT Answer

### 5.1 CAN Answer (Exploratory)

- A0: Does a canonical backbone-like structure exist in melanoma + TIL co-culture transcriptomics?
- Tumor-immune context: Does perturbation-induced transcriptomic structure look different in immune-evasion / IFNγ stimulation context?
- Preliminary evidence: architecture form in a more complex, biologically realistic tumor setting
- Boundary: framework limitation in non-DepMap-matched cell lines

### 5.2 CANNOT Answer

- A1: bridge to DepMap dependency (no endpoint)
- Formal external generalization anchor
- A0/A1 confirmed in formal sense
- Matched endpoint validation
- Any bridge-form quantitative claim

## 6. Admission Verdict

**NOT ELIGIBLE AS FORMAL BRIDGE** — no DepMap endpoint exists for melanoma.

**STATUS: EXPLORATORY ONLY** (2026-04-14)

Role: tumor-immune complex exploratory / boundary-defining dataset
Claim tier: Preliminary / exploratory (no A0/A1 formal support)
Use case: demonstrate framework can interrogate architecture form in complex tumor-immune context; does NOT provide formal validation

## 7. Relationship to Other Datasets

| Dataset | Role | DepMap Endpoint | Claim Tier |
|---------|------|-----------------|------------|
| HCC38/HCC1143 | Primary mainline | ✅ CRISPR DepMap | Formal A0/A1 |
| K562 7d/13d GSE90063 | Temporal panel | ✅ CRISPR DepMap | Formal A0/A1 |
| Replogle K562 GWPS day 8 | Short-horizon anchor | ✅ CRISPR DepMap | Formal A0/A1 |
| Replogle K562 essential | Sensitivity panel | ✅ CRISPR DepMap | A0/A1 supporting |
| **Frangieh 2021 melanoma** | **Exploratory boundary test** | **❌ No endpoint** | **Preliminary only** |

## 8. Allowed vs Disallowed Wording

### 8.1 Allowed

- "exploratory analysis in melanoma + TIL co-culture"
- "preliminary evidence for architecture form in tumor-immune complex context"
- "transcriptomic structure in IFNγ-stimulated / co-culture conditions"
- "boundary test: framework in non-DepMap-matched cell context"
- "A0 architecture form: preliminary, requires formal validation"

### 8.2 Disallowed

- "formal A0/A1 confirmed"
- "bridge to DepMap dependency"
- "external validation"
- "matched endpoint"
- "generalization anchor"
- Any quantitative bridge claim

## 9. One-Sentence Summary

Frangieh 2021 melanoma + TIL co-culture provides exploratory evidence for architecture form in a tumor-immune complex context, but lacks a DepMap endpoint and can only support preliminary/qualitative interpretation, not formal bridge claims.
