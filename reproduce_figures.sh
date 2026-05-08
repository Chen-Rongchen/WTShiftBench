#!/usr/bin/env bash
# One-shot driver to regenerate the manuscript figures from the cached
# intermediates checked into the repository.
#
# Prerequisite: an environment satisfying environment.yml or pixi.toml,
# with this repository's `src/` on PYTHONPATH (see below).
#
# Steps that require the raw h5ad files (e.g. extended_data_figure3 axis
# panels that read data/processed/.../*.h5ad) will be skipped automatically;
# follow DATA_AVAILABILITY.md to fetch and preprocess them first.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/src:$ROOT/scripts:$ROOT${PYTHONPATH+:$PYTHONPATH}"

run() {
    echo
    echo "==> $*"
    if ! python "$@"; then
        echo "    (skipped: prerequisites missing — see DATA_AVAILABILITY.md)"
    fi
}

# Main figures
run scripts/manuscript/build_figure1_truth_object.py
run scripts/manuscript/build_figure2_anchor_tiering.py
run scripts/manuscript/build_figure3_model_tradeoff.py
run scripts/manuscript/build_figure4_sweep_controls.py
run scripts/manuscript/build_figure6_boundary.py

# Extended Data figures
run scripts/manuscript/build_extended_data_figure1.py
run scripts/manuscript/build_extended_data_figure3_v2.py
run scripts/manuscript/build_extended_data_figure9_biological_landing.py
run scripts/manuscript/build_extended_data_figure10_axis_explanatory.py
run scripts/manuscript/build_extended_data_figure13.py
run scripts/manuscript/build_extended_data_figure_robustness.py

echo
echo "Done. Outputs:"
echo "  manuscript/figures/Figure_*/"
echo "  manuscript/extended_data/Extended_Data_Figure_*/"
