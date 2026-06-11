#!/usr/bin/env bash
# Rebuild the active WTShiftBench panel bundle.
#
# Figure 1 panels are publication-designed SVG assets and are retained as
# provided. All other active panels are regenerated through the Pixi core
# environment. Composite figures and manuscript files are not synchronized
# into the public release.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/wtshiftbench-matplotlib}"
mkdir -p "$MPLCONFIGDIR"

run_python() {
    echo
    echo "==> $*"
    pixi run --environment core python "$@"
}

echo "==> Retaining publication-designed Figure 1 panels"
for panel in a b c; do
    test -f "figures/Figure_1/panels/Figure_1_panel_${panel}.svg"
done

# Main figure panels. These builders write canonical panel outputs under
# manuscript/figures; only SVG and panel source data are copied publicly.
run_python scripts/manuscript/build_figure2_anchor_tiering.py --panels-only
run_python scripts/manuscript/build_figure3_model_endpoint_recovery.py --panels-only
run_python scripts/manuscript/build_figure4_sweep_controls.py --panels-only

for figure in 2 3 4; do
    mkdir -p "figures/Figure_${figure}/panels"
    cp "manuscript/figures/Figure_${figure}/panels/"*.svg \
       "figures/Figure_${figure}/panels/"
    cp "manuscript/figures/Figure_${figure}/panels/"*_source_data.tsv \
       "figures/Figure_${figure}/panels/"
done

# Extended Data panels.
run_python scripts/manuscript/build_extended_data_figure1.py --panels-only
run_python scripts/manuscript/build_extended_data_figure2_active.py
run_python scripts/manuscript/build_extended_data_figure3_raw_bridge_small_multiples.py
run_python scripts/manuscript/build_extended_data_figure4_active.py
run_python scripts/manuscript/build_extended_data_figure5_output_geometry.py
run_python scripts/manuscript/build_extended_data_figure6_response_programs.py --panels-only

# Replace internal category IDs in publication-facing panel tables before
# hashes are calculated.
run_python scripts/release/normalize_public_labels.py figures

# Refresh the active supplementary-table registry. The registry builder applies
# the same publication-label normalization before calculating file hashes.
run_python scripts/pipeline/build_resource_registry.py \
    --config configs/resource_registry_v1.json
cp benchmark/registry/figure_source_data_manifest.tsv \
   source_data/figure_source_data_manifest.tsv

echo
echo "Done. Active editable SVG panels are available under figures/."
