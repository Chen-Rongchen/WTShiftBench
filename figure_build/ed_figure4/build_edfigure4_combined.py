#!/usr/bin/env python3
"""Build Extended_Data_Figure_4 combined — all panels + composite."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_extended_data_figure10_axis_explanatory.py")], cwd=ROOT, check=True, env=env)
pdst = TEST / "Extended_Data_Figure_4" / "panels"
pdst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_extended_data_v1/edfig10_axis_explanatory_space/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig10_panela{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_4_panel_a{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig10_panelb{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_4_panel_b{ext}")

# Combined figure
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = ROOT / f"reports/manuscript_extended_data_v1/edfig10_axis_explanatory_space/edfig10{ext}"
    if s.exists(): shutil.copy2(s, TEST / "Extended_Data_Figure_4" / f"Extended_Data_Figure_4{ext}")

print(f"  Extended_Data_Figure_4 all panels + combined -> {TEST}")
