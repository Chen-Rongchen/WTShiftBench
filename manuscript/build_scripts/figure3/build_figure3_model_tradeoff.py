#!/usr/bin/env python3
"""Build Figure_3 combined — all panels + composite."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
TEST = ROOT / "manuscript/build_scripts/test_output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_figure3_model_tradeoff.py")], cwd=ROOT, check=True, env=env)
pdst = TEST / "Figure_3" / "panels"
pdst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_figures_v2/fig3_model_tradeoff/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure3_panela{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Figure_3_panel_a{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure3_panelb{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Figure_3_panel_b{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure3_panelc{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Figure_3_panel_c{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"figure3_paneld{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Figure_3_panel_d{ext}")

# Combined figure
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = ROOT / f"reports/manuscript_figures_v2/fig3_model_tradeoff/figure3{ext}"
    if s.exists(): shutil.copy2(s, TEST / "Figure_3" / f"Figure_3{ext}")

print(f"  Figure_3 all panels + combined -> {TEST}")
