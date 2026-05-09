#!/usr/bin/env python3
"""Build Figure_2 combined — all panels + composite."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_figure2_anchor_tiering.py")], cwd=ROOT, check=True, env=env)
pdst = TEST / "Figure_2" / "panels"
pdst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_figures_v2/fig2_anchor_tiering/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure2_panela{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Figure_2_panel_a{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure2_panelb{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Figure_2_panel_b{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure2_panelc{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Figure_2_panel_c{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure2_paneld{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Figure_2_panel_d{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure2_panele{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Figure_2_panel_e{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure2_panelf{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Figure_2_panel_f{ext}")

# Combined figure
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = ROOT / f"reports/manuscript_figures_v2/fig2_anchor_tiering/figure2{ext}"
    if s.exists(): shutil.copy2(s, TEST / "Figure_2" / f"Figure_2{ext}")

print(f"  Figure_2 all panels + combined -> {TEST}")
