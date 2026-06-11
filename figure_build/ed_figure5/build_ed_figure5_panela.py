#!/usr/bin/env python3
"""Build active Extended Data Figure 5 axis-free diagnostic panels."""
import subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run(
    [
        sys.executable,
        str(ROOT / "scripts/manuscript/build_extended_data_figure5_output_geometry.py"),
    ],
    cwd=ROOT,
    check=True,
    env=env,
)
print(f"  Extended_Data_Figure_5 panels a–f -> {TEST / 'Extended_Data_Figure_5/panels'}")
