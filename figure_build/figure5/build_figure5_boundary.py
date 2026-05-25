#!/usr/bin/env python3
"""Build Figure_5 combined — all panels + composite."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_figure6_boundary.py")], cwd=ROOT, check=True, env=env)
pdst = TEST / "Figure_5" / "panels"
pdst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_figures_v2/fig6_boundary/panels"
src = ROOT / "reports/manuscript_figures_v2/fig5_response_governance/panels"
for panel in ["a", "b", "c", "d"]:
    for ext in [".png", ".pdf", "_source_data.tsv"]:
        s = src / f"figure5_panel{panel}{ext}"
        if s.exists(): shutil.copy2(s, pdst / f"Figure_5_panel_{panel}{ext}")

# Combined figure
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = ROOT / f"reports/manuscript_figures_v2/fig5_response_governance/figure5{ext}"
    if s.exists(): shutil.copy2(s, TEST / "Figure_5" / f"Figure_5{ext}")

print(f"  Figure_5 all panels + combined -> {TEST}")
