#!/usr/bin/env python3
"""Build Figure_1 panel c."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_figure1_truth_object.py"), "--panels-only"], cwd=ROOT, check=True, env=env)
dst = TEST / "Figure_1" / "panels"
dst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_figures_v2/fig1_truth_object/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure1_panele{ext}"
    if s.exists(): shutil.copy2(s, dst / f"Figure_1_panel_c{ext}")
print(f"  Figure_1 panel c -> {dst}")
