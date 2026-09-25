#!/usr/bin/env bash
# Render the current four main and seven supplementary figures from frozen tables.
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"
exec pixi run --frozen --environment core python reproducibility/v1.2.0/build_figures.py "$@"
