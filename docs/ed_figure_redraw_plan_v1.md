# Extended Data Figure Redraw — Execution Plan

## Status: COMPLETE (2026-04-30, commit `8c6d0a0`)

## Overview

Redrew all 5 Extended Data figures to match `manuscript/text/figure_legends_v1.md`.
Unified panel letter formatting across all figures.
No new analyses — only re-layout and visual adjustments.

## ED Fig 1: Dataset familiarization

**Script**: `scripts/manuscript/build_edfig1_composite.py`
**Method**: PIL composite from 11 individual panel PNGs (panels a-k in manuscript directory)
**Panels**: a (table), b (5 UMAPs with Replogle), c (5 target-gene arrow plots)
**Changes**: Added panel letters a-c, high-res UMAP/arrow scaling

## ED Fig 2: Metric robustness + self-expression

**Scripts**: 
- `scripts/manuscript/build_edfig2_panel_e.py --reference` — generates panel e (self-expression scatter)
- `scripts/manuscript/build_edfig2_composite.py` — PIL composite of 5 panels
**Panels**: a (top-n sensitivity), b (heatmap), c (endpoint gap), d (subsampling), e (self-expression)
**Changes**: 
- Panel e: YlOrRd shift colormap, gene labels below with vertical arrows pointing up
- Only 3 genes labeled (PFDN5, PRPF6, ZNF131)
- Rho stats placed between scatter plots
- Figure legends updated to 5-panel a-e
- Panel letters a-e via PIL

## ED Fig 3: K562 temporal + Replogle

**Script**: `scripts/manuscript/fix_edfig3_panelb_square.py`
**Panels**: a (temporal stratification), b (Replogle joint grid)
**Changes**:
- Panel b: square axes (`set_box_aspect(1)`), 5 distinct quadrant colors
- Rho/CI/p + quadrant counts placed outside right, no borders
- Legend moved to bottom-right
- Panel letters via PIL for pixel-perfect alignment (fontsize=8.5 unified)
- Height compressed ~30% via matplotlib figsize reduction
- Panel b title spacing via PIL top padding

## ED Fig 4: Axis-level signal space

**Script**: `scripts/manuscript/build_extended_data_figure10_axis_explanatory.py`
**Changes**:
- Shift R² / Dependency R² markers merged into profile legend
- Panel letter a unified to x=-0.08

## ED Fig 5: Pathway polarity heatmap

**Script**: `scripts/manuscript/build_extended_data_figure9_biological_landing.py`
**Changes**:
- Removed "Same target / partner context / all Hallmark" grey annotation
- Panel letter a unified to x=-0.08

## Panel Letter Unification

| Figure | Method | Font | Position |
|--------|--------|------|----------|
| ED Fig 1 | PIL | 34px DejaVuSans-Bold | (32, 12-18) |
| ED Fig 2 | PIL | 34px DejaVuSans-Bold | (32, 12-18) |
| ED Fig 3 | PIL | 34px DejaVuSans-Bold | (32, 12-16) |
| ED Fig 4 | matplotlib | 8.5pt bold | x=-0.08 |
| ED Fig 5 | matplotlib | 8.5pt bold | x=-0.08 |

## Manuscript Text Changes

- `figure_legends_v1.md`: ED Fig 2 updated from 3-panel (a-c) to 5-panel (a-e)
- `manuscript_draft_v1.md`: Logic audit fixes (boundary qualifiers, "not a small-n artifact", etc.)

## Reproduction

See `manuscript/README.md` for the complete set of build commands.
All scripts output to `manuscript/extended_data/Extended_Data_Figure_N/`.
