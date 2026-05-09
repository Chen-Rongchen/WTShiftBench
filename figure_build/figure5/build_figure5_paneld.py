#!/usr/bin/env python3
"""Build Figure_5 panel d."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_figure6_boundary.py"), "--panels-only"], cwd=ROOT, check=True, env=env)
dst = TEST / "Figure_5" / "panels"
dst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_figures_v2/fig6_boundary/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure6_paneld{ext}"
    if s.exists(): shutil.copy2(s, dst / f"Figure_5_panel_d{ext}")
print(f"  Figure_5 panel d -> {dst}")
