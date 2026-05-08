#!/usr/bin/env python3
"""Build Extended_Data_Figure_6 combined — all panels + composite."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
TEST = ROOT / "manuscript/build_scripts/test_output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_extended_data_figure_robustness.py")], cwd=ROOT, check=True, env=env)
pdst = TEST / "Extended_Data_Figure_6" / "panels"
pdst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_extended_data_v1/edfig_robustness/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig_robustness_panela{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_6_panel_a{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig_robustness_panelb{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_6_panel_b{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig_robustness_panelc{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_6_panel_c{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig_robustness_paneld{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_6_panel_d{ext}")

# Combined figure
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = ROOT / f"reports/manuscript_extended_data_v1/edfig_robustness/edfig_robustness{ext}"
    if s.exists(): shutil.copy2(s, TEST / "Extended_Data_Figure_6" / f"Extended_Data_Figure_6{ext}")

print(f"  Extended_Data_Figure_6 all panels + combined -> {TEST}")
