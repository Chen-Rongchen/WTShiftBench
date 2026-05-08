# Pathway-response exploratory layer

This directory contains exploratory pathway-level summaries computed from target-versus-matched-control perturbation rankings.

These analyses are intended as a bounded biological landing layer. They are **not** used to define the benchmark truth object, endpoint hierarchy, model-adjudication criteria, or mechanism-level claims.

## Primary analysis

Pre-ranked fgsea over MSigDB Hallmark gene sets, computed with the
R Bioconductor package `fgsea` (Korotkevich et al., Nat Methods 2021)
using its adaptive multilevel permutation test.

For each context and perturbation target, genes were ranked by:
```
rank_gene = mean_log_expr_perturbed - mean_log_expr_matched_control
```

Then pre-ranked fgsea was applied using Hallmark gene sets with:
- minSize = 10
- maxSize = 500
- eps = 1e-10 (multilevel boundary; pval can resolve down to ~1e-10)
- nPermSimple = 10000 (initial permutation count for the pre-test)
- set.seed(42) (bit-identical reproducibility under fixed seed)

The R wrapper (`src/wtbench/pathway_response/run_fgsea.R`) is invoked from
the Python entrypoint via subprocess so that ranking generation stays in
Python while the statistical computation uses the canonical, peer-reviewed
fgsea implementation.

## Data sources

| Context | Cell line | Source | Preprocessing |
|---------|-----------|--------|---------------|
| HCC38 | Breast cancer (HCC38) | GSE241115 | Pre-log-normalized (1e4 + log1p) |
| HCC1143 | Breast cancer (HCC1143) | GSE241115 | Pre-log-normalized (1e4 + log1p) |
| K562_7d | Leukemia (K562) | GSE90063 | Raw counts -> normalize_total(1e4) -> log1p |
| K562_13d | Leukemia (K562) | GSE90063 | Raw counts -> normalize_total(1e4) -> log1p |

## Gene-set source

MSigDB Hallmark collection (h.all.symbols.gmt), obtained from BiocSet R package.

## Display panel

Displayed pathways were selected from a pre-specified perturbation-response panel covering:
- Cell death / stress
- Proliferation / cell cycle
- Proteostasis / stress
- Metabolic state
- State remodeling
- Inflammatory / interferon (optional)

## Target selection

Targets displayed in figures were selected using:
- Tier 1: Benchmark-relevant anchor targets (PFDN5, PMF1, PRPF6, ZNF131) if available
- Tier 2: Top targets by NES variance (proxy for perturbation shift)
- Tier 3: Cross-context recurrent targets

Selection was done by pre-specified rules, not by the appearance of pathway enrichment results.

## Output files

- `fgsea_hallmark_*.tsv`: Full fgsea results per context
- `target_inclusion_qc_*.tsv`: Target inclusion criteria and QC
- `selected_targets_for_display.tsv`: Selected targets for visualization
- `selected_response_gene_set_panel.tsv`: Selected pathways for visualization
- `pathway_response_nes_heatmap.png`: NES heatmap (primary display)
- `qc/`: Provenance and method logs

## Interpretation boundary

Allowed language:
- "pathway-level perturbation response summary"
- "exploratory response-level enrichment"
- "bounded biological landing layer"
- "target-versus-control pathway summaries"

Avoid:
- "mechanism discovered"
- "pathway causally mediates the benchmark signal"
- "validated pathway"
- "closed biological mechanism"
- "model recovered pathway biology"

Main claim boundary:
> Pathway enrichment was used as an exploratory response-level summary and was not used to define the benchmark truth object or model-adjudication criteria.
