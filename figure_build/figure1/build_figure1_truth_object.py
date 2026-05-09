#!/usr/bin/env python3
"""Build Figure_1 combined — all panels + composite."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_figure1_truth_object.py")], cwd=ROOT, check=True, env=env)
pdst = TEST / "Figure_1" / "panels"
pdst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_figures_v2/fig1_truth_object/panels"
# Map code-generated panels cdef → abcd (panels a,b are hand-drawn overview)
PANEL_MAP = {"c": "a", "d": "b", "e": "c", "f": "d"}
for src_panel, dst_panel in PANEL_MAP.items():
    for ext in [".png", ".pdf", "_source_data.tsv"]:
        s = src / f"figure1_panel{src_panel}{ext}"
        if s.exists(): shutil.copy2(s, pdst / f"Figure_1_panel_{dst_panel}{ext}")

# Combined figure
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = ROOT / f"reports/manuscript_figures_v2/fig1_truth_object/figure1{ext}"
    if s.exists(): shutil.copy2(s, TEST / "Figure_1" / f"Figure_1{ext}")

print(f"  Figure_1 all panels + combined -> {TEST}")
