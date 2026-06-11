#!/usr/bin/env python3
"""Build Figure_3 combined — endpoint-recovery audit panels + composite."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_figure3_model_endpoint_recovery.py")], cwd=ROOT, check=True, env=env)
pdst = TEST / "Figure_3" / "panels"
pdst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_figures_v2/fig3_model_endpoint_recovery/panels"
for panel in ["a", "b", "c", "d", "e", "f"]:
    for ext in [".png", ".pdf", ".svg", "_source_data.tsv"]:
        s = src / f"figure3_panel{panel}{ext}"
        if s.exists(): shutil.copy2(s, pdst / f"Figure_3_panel_{panel}{ext}")

# Combined figure
for ext in [".png", ".pdf", ".svg", "_source_data.tsv"]:
    s = ROOT / f"reports/manuscript_figures_v2/fig3_model_endpoint_recovery/figure3{ext}"
    if s.exists(): shutil.copy2(s, TEST / "Figure_3" / f"Figure_3{ext}")

print(f"  Figure_3 all panels + combined -> {TEST}")
