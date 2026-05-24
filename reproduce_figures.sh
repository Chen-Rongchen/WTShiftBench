#!/usr/bin/env bash
# Driver for regenerating the public manuscript figure bundle from the
# cached intermediates checked into the repository.
#
# Prerequisite: an environment satisfying environment.yml or pixi.toml,
# with this repository's `src/` on PYTHONPATH (set automatically below).
#
# Steps that require raw h5ad files will fail until those public datasets have
# been downloaded and preprocessed; see DATA_AVAILABILITY.md.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/src:$ROOT/scripts:$ROOT${PYTHONPATH+:$PYTHONPATH}"

FAILED_STEPS=()

run() {
    echo
    echo "==> $*"
    if ! python "$@"; then
        echo "    ERROR: figure step failed. Check the traceback above and DATA_AVAILABILITY.md for required inputs."
        FAILED_STEPS+=("$*")
    fi
}

# Main figures
run figure_build/figure1/build_figure1_truth_object.py
run figure_build/figure2/build_figure2_anchor_tiering.py
run figure_build/figure3/build_figure3_model_tradeoff.py
run figure_build/figure4/build_figure4_sweep_controls.py
run figure_build/figure5/build_figure5_boundary.py

# Extended Data figures
run scripts/manuscript/build_extended_data_resource_bundle.py

if [[ "${#FAILED_STEPS[@]}" -ne 0 ]]; then
    echo
    echo "One or more figure steps failed:"
    printf '  - %s\n' "${FAILED_STEPS[@]}"
    echo "Existing figures/ snapshot was left unchanged."
    exit 1
fi

rm -rf figures
cp -a figure_build/output figures

echo
echo "Done. Fresh artefacts are written under figure_build/output/."
echo "    Repo root figures/ has been synced from figure_build/output/ for GitHub browsing."
