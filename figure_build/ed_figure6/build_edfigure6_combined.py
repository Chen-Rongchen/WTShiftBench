#!/usr/bin/env python3
"""Build Extended_Data_Figure_6 panels — response-program detail and robustness."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run(
    [sys.executable, str(ROOT / "scripts/manuscript/build_extended_data_figure6_response_programs.py"), "--panels-only"],
    cwd=ROOT,
    check=True,
    env=env,
)
print(f"  Extended_Data_Figure_6 response-program panels -> {TEST}")
