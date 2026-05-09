#!/usr/bin/env python3
"""Build Figure_4 combined — all panels + composite."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_figure4_sweep_controls.py")], cwd=ROOT, check=True, env=env)
pdst = TEST / "Figure_4" / "panels"
pdst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_figures_v2/fig4_sweep_controls/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure4_panela{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Figure_4_panel_a{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure4_panelb{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Figure_4_panel_b{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure4_panelc{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Figure_4_panel_c{ext}")

# Combined figure
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = ROOT / f"reports/manuscript_figures_v2/fig4_sweep_controls/figure4{ext}"
    if s.exists(): shutil.copy2(s, TEST / "Figure_4" / f"Figure_4{ext}")

print(f"  Figure_4 all panels + combined -> {TEST}")
