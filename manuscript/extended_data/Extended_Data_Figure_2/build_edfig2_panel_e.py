#!/usr/bin/env python3
"""Delegate to ``scripts/manuscript/build_edfig2_panel_e.py`` (single source of truth)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    script = ROOT / "scripts/manuscript/build_edfig2_panel_e.py"
    subprocess.run([sys.executable, str(script), *sys.argv[1:]], cwd=str(ROOT), check=True)


if __name__ == "__main__":
    main()
