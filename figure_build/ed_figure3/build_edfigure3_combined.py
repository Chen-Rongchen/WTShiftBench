#!/usr/bin/env python3
"""Build Extended_Data_Figure_3 combined raw external-bridge small multiples."""
import subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run(
    [sys.executable, str(ROOT / "scripts/manuscript/build_extended_data_figure3_raw_bridge_small_multiples.py")],
    cwd=ROOT,
    check=True,
    env=env,
)

print(f"  Extended_Data_Figure_3 all panels + combined -> {TEST}")
