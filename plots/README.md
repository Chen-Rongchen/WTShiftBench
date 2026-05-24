# Plot outputs

WTShiftBench keeps plotting code and source data in Git, while large rendered
figure binaries are treated as reproducible outputs.

## Current local output layout

- `../figure_build/output/`: regenerated plot bundle.
- `../figures/`: GitHub-browsable figure/source-data snapshot.
- `../manuscript/figures/`: local manuscript assembly copy.

## Rebuild

```bash
bash reproduce_figures.sh
```

The driver rebuilds Fig. 1-5 and Extended Data Fig. 1-7. It also refreshes the
local `figures/` snapshot. For GitHub commits, prefer staging code, source-data
TSVs and manifests rather than composite PNG/PDF outputs.

## Style guardrails

- Data plots carry the main evidence.
- Compact matrices/tables carry governance, registry and reproducibility.
- Cards and flow diagrams are avoided except where a compact schematic is
  unavoidable.
