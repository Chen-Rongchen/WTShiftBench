#!/usr/bin/env python3
"""Build Figure_4 panel c."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
TEST = ROOT / "manuscript/build_scripts/test_output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_figure4_sweep_controls.py"), "--panels-only"], cwd=ROOT, check=True, env=env)
dst = TEST / "Figure_4" / "panels"
dst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_figures_v2/fig4_sweep_controls/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure4_panelc{ext}"
    if s.exists(): shutil.copy2(s, dst / f"Figure_4_panel_c{ext}")
print(f"  Figure_4 panel c -> {dst}")
