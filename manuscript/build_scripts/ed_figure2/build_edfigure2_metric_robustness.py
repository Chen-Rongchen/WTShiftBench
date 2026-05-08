#!/usr/bin/env python3
"""Build Extended_Data_Figure_2 combined — all panels + composite."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
TEST = ROOT / "manuscript/build_scripts/test_output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_extended_data_figure13.py")], cwd=ROOT, check=True, env=env)
pdst = TEST / "Extended_Data_Figure_2" / "panels"
pdst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_extended_data_v1/edfig13_metric_robustness/panels"
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig13_panela{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_2_panel_a{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig13_panelb{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_2_panel_b{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig13_panelc{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_2_panel_c{ext}")
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = src / f"edfig13_paneld{ext}"
    if s.exists(): shutil.copy2(s, pdst / f"Extended_Data_Figure_2_panel_d{ext}")

# Combined figure
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = ROOT / f"reports/manuscript_extended_data_v1/edfig13_metric_robustness/edfig13{ext}"
    if s.exists():
        shutil.copy2(s, TEST / "Extended_Data_Figure_2" / f"Extended_Data_Figure_2{ext}")
# Panel e (separate script) and composite
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_edfig2_panel_e.py")], cwd=ROOT, check=True, env=env)
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_edfig2_composite.py")], cwd=ROOT, check=True, env=env)
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s2 = ROOT / f"manuscript/extended_data/Extended_Data_Figure_2/panels/Extended_Data_Figure_2_panel_e{ext}"
    if s2.exists():
        shutil.copy2(s2, pdst / f"Extended_Data_Figure_2_panel_e{ext}")
for ext in [".png", ".pdf"]:
    sc = ROOT / f"manuscript/extended_data/Extended_Data_Figure_2/Extended_Data_Figure_2{ext}"
    if sc.exists():
        shutil.copy2(sc, TEST / "Extended_Data_Figure_2" / f"Extended_Data_Figure_2{ext}")

print(f"  Extended_Data_Figure_2 all panels + combined -> {TEST}")
