#!/usr/bin/env python3
"""Build the active Extended Data Fig. 4 panels.

The active ED Fig. 4 contains statistical calibration and finite-budget
sensitivity panels. Older axis-explanatory assets are intentionally not copied
here because they no longer match the manuscript figure plan.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/manuscript/build_extended_data_figure4_active.py"),
        ],
        cwd=ROOT,
        check=True,
        env=env,
    )


if __name__ == "__main__":
    main()
