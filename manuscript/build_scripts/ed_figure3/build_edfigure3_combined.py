#!/usr/bin/env python3
"""Build Extended_Data_Figure_3 combined — all panels + composite."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
TEST = ROOT / "manuscript/build_scripts/test_output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_extended_data_figure3_v2.py")], cwd=ROOT, check=True, env=env)
pdst = TEST / "Extended_Data_Figure_3" / "panels"
pdst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_extended_data_v1/edfig3_k562_temporal_and_replogle/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig3_panela{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_3_panel_a{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig3_panelb{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_3_panel_b{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig3_panelc{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_3_panel_c{ext}")

# Combined figure
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = ROOT / f"reports/manuscript_extended_data_v1/edfig3_k562_temporal_and_replogle/edfig3{ext}"
    if s.exists(): shutil.copy2(s, TEST / "Extended_Data_Figure_3" / f"Extended_Data_Figure_3{ext}")

print(f"  Extended_Data_Figure_3 all panels + combined -> {TEST}")
