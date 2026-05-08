#!/usr/bin/env python3
"""Build Extended_Data_Figure_5 combined — all panels + composite."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
TEST = ROOT / "manuscript/build_scripts/test_output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_extended_data_figure9_biological_landing.py")], cwd=ROOT, check=True, env=env)
pdst = TEST / "Extended_Data_Figure_5" / "panels"
pdst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_extended_data_v1/edfig9_biological_landing/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig9_panela{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_5_panel_a{ext}")

# Combined figure
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = ROOT / f"reports/manuscript_extended_data_v1/edfig9_biological_landing/edfig9{ext}"
    if s.exists(): shutil.copy2(s, TEST / "Extended_Data_Figure_5" / f"Extended_Data_Figure_5{ext}")

print(f"  Extended_Data_Figure_5 all panels + combined -> {TEST}")
