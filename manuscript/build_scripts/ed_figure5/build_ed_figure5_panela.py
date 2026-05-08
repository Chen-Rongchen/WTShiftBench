#!/usr/bin/env python3
"""Build Extended_Data_Figure_5 panel a."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
TEST = ROOT / "manuscript/build_scripts/test_output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_extended_data_figure9_biological_landing.py"), "--panels-only"], cwd=ROOT, check=True, env=env)
dst = TEST / "Extended_Data_Figure_5" / "panels"
dst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_extended_data_v1/edfig9_biological_landing/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig9_panela{ext}"
    if s.exists(): shutil.copy2(s, dst / f"Extended_Data_Figure_5_panel_a{ext}")
print(f"  Extended_Data_Figure_5 panel a -> {dst}")
