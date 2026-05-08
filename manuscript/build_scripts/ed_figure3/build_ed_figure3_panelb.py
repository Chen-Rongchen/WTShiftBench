#!/usr/bin/env python3
"""Build Extended_Data_Figure_3 panel b."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
TEST = ROOT / "manuscript/build_scripts/test_output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_extended_data_figure3_v2.py"), "--panels-only"], cwd=ROOT, check=True, env=env)
dst = TEST / "Extended_Data_Figure_3" / "panels"
dst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_extended_data_v1/edfig3_k562_temporal_and_replogle/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig3_panelb{ext}"
    if s.exists(): shutil.copy2(s, dst / f"Extended_Data_Figure_3_panel_b{ext}")
print(f"  Extended_Data_Figure_3 panel b -> {dst}")
