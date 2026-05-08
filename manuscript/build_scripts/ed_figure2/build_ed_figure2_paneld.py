#!/usr/bin/env python3
"""Build Extended_Data_Figure_2 panel d."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
TEST = ROOT / "manuscript/build_scripts/test_output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_extended_data_figure13.py"), "--panels-only"], cwd=ROOT, check=True, env=env)
dst = TEST / "Extended_Data_Figure_2" / "panels"
dst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_extended_data_v1/edfig13_metric_robustness/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig13_paneld{ext}"
    if s.exists(): shutil.copy2(s, dst / f"Extended_Data_Figure_2_panel_d{ext}")
print(f"  Extended_Data_Figure_2 panel d -> {dst}")
