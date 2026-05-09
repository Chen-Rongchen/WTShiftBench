#!/usr/bin/env python3
"""Build Extended_Data_Figure_1 panel k."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_extended_data_figure1.py"), "--panels-only"], cwd=ROOT, check=True, env=env)
dst = TEST / "Extended_Data_Figure_1" / "panels"
dst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_extended_data_v1/edfig1_dataset_familiarization/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig1_panelk{ext}"
    if s.exists(): shutil.copy2(s, dst / f"Extended_Data_Figure_1_panel_k{ext}")
print(f"  Extended_Data_Figure_1 panel k -> {dst}")
