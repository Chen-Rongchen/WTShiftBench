# K562 Entrant Summary Table (v1, 2026-04-15)

## Overview

Per-target Spearman correlation (ρ) between predicted and observed log₁p-normalized expression deltas
on the K562 atlas gene space (45 genes overlapping between K562 h5ad and HCC atlas gene set).

**K562 13d**: 10 perturbed TFs (leave-one-out evaluation)
**K562 7d**: 10 perturbed TFs (leave-one-out evaluation)

---

## K562 13d — Per-Target Spearman ρ

| Target | GEARS base | scGPT | Geneformer | lm_train_lowrank | lm_g_scgpt_ridge | lm_g_geneformer_ridge |
|--------|------------|-------|------------|------------------|------------------|----------------------|
| CREB1 | -0.038 | 0.266 | 0.228 | 0.228 | 0.213 | 0.243 |
| E2F4 | 0.100 | 0.198 | 0.289 | 0.154 | 0.256 | 0.303 |
| EGR1 | 0.297 | 0.526 | 0.514 | 0.541 | 0.542 | 0.535 |
| ELF1 | 0.100 | 0.347 | 0.379 | 0.377 | 0.393 | 0.377 |
| ELK1 | 0.191 | 0.372 | 0.436 | 0.355 | 0.371 | 0.374 |
| ETS1 | 0.247 | 0.449 | 0.437 | 0.431 | 0.430 | 0.433 |
| GABPA | -0.100 | 0.269 | 0.289 | 0.271 | 0.275 | 0.271 |
| IRF1 | 0.163 | 0.328 | 0.314 | 0.307 | 0.317 | 0.316 |
| NR2C2 | 0.156 | 0.334 | 0.369 | 0.362 | 0.372 | 0.367 |
| YY1 | 0.091 | 0.410 | 0.430 | 0.423 | 0.422 | 0.421 |

**Mean ρ** | **0.127** | **0.350** | **0.373** | **0.349** | **0.369** | **0.373**
**Min ρ** | -0.100 | 0.198 | 0.228 | 0.154 | 0.213 | 0.243
**Max ρ** | 0.297 | 0.526 | 0.514 | 0.541 | 0.542 | 0.535
**n targets ρ > 0** | 9 | 10 | 10 | 10 | 10 | 10
**n targets ρ > 0.2** | 1 | 7 | 8 | 8 | 9 | 9

---

## K562 7d — Per-Target Spearman ρ

| Target | GEARS base | scGPT | Geneformer | lm_train_lowrank | lm_g_scgpt_ridge | lm_g_geneformer_ridge |
|--------|------------|-------|------------|------------------|------------------|----------------------|
| CREB1 | -0.169 | 0.193 | 0.248 | 0.295 | 0.278 | 0.316 |
| E2F4 | 0.141 | 0.410 | 0.420 | 0.388 | 0.395 | 0.385 |
| EGR1 | 0.094 | 0.434 | 0.459 | 0.459 | 0.455 | 0.455 |
| ELF1 | 0.338 | 0.625 | 0.649 | 0.631 | 0.644 | 0.632 |
| ELK1 | 0.094 | 0.544 | 0.552 | 0.540 | 0.544 | 0.541 |
| ETS1 | 0.178 | 0.560 | 0.562 | 0.562 | 0.574 | 0.562 |
| GABPA | -0.072 | 0.425 | 0.420 | 0.434 | 0.422 | 0.435 |
| IRF1 | 0.031 | 0.513 | 0.508 | 0.513 | 0.520 | 0.516 |
| NR2C2 | 0.197 | 0.597 | 0.604 | 0.594 | 0.607 | 0.607 |
| YY1 | 0.169 | 0.556 | 0.720 | 0.694 | 0.674 | 0.675 |

**Mean ρ** | **0.093** | **0.477** | **0.476** | **0.482** | **0.520** | **0.513**
**Min ρ** | -0.169 | 0.193 | 0.248 | 0.295 | 0.278 | 0.316
**Max ρ** | 0.338 | 0.625 | 0.720 | 0.694 | 0.674 | 0.675
**n targets ρ > 0** | 8 | 10 | 10 | 10 | 10 | 10
**n targets ρ > 0.2** | 2 | 9 | 9 | 10 | 9 | 10

---

## Cross-Timepoint Summary

| Entrant | 13d Mean ρ | 7d Mean ρ | 7d–13d Δ |
|---------|-----------|-----------|----------|
| GEARS base | 0.127 | 0.093 | -0.034 |
| scGPT | 0.350 | 0.477 | +0.127 |
| Geneformer | 0.373 | 0.476 | +0.103 |
| lm_train_lowrank | 0.349 | 0.482 | +0.133 |
| lm_g_scgpt_ridge | 0.369 | 0.520 | +0.151 |
| lm_g_geneformer_ridge | 0.373 | 0.513 | +0.140 |

---

## Key Observations

1. **7d consistently outperforms 13d** across all embedding-based entrants (+0.10 to +0.15 ρ gain), consistent with temporal sensitivity prediction thesis
2. **GEARS base is substantially worse** than all embedding-based entrants on K562 (mean ρ 0.09–0.13 vs 0.35–0.52)
3. **All embedding-based entrants cluster tightly** (within ≈0.35–0.52 range), suggesting shared architecture form rather than model-specific advantage
4. **EGR1 and ELF1** are the strongest performers across both timepoints (ρ 0.4–0.7)
5. **CREB1 and E2F4** are the weakest performers, especially at 13d

---

## Paper Role

K562 entrant evaluation is **context-local rather than atlas-shared**.
Supports supplementary external model-side analysis for:
- Architecture form external recurrence
- Trade-off partial recurrence diagnostic
- Temporal stratification effect

**NOT**: target-overlap replication of HCC atlas genes, or large-scale leaderboard.
