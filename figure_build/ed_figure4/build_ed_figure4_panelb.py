#!/usr/bin/env python3
"""Build Extended_Data_Figure_4 panel b."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_extended_data_figure10_axis_explanatory.py"), "--panels-only"], cwd=ROOT, check=True, env=env)
dst = TEST / "Extended_Data_Figure_4" / "panels"
dst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_extended_data_v1/edfig10_axis_explanatory_space/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig10_panelb{ext}"
    if s.exists(): shutil.copy2(s, dst / f"Extended_Data_Figure_4_panel_b{ext}")
print(f"  Extended_Data_Figure_4 panel b -> {dst}")
