#!/usr/bin/env python3
"""Build Extended_Data_Figure_2 combined — all panels + composite."""
import shutil, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "figure_build/output"
env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_extended_data_figure13.py")], cwd=ROOT, check=True, env=env)
pdst = TEST / "Extended_Data_Figure_2" / "panels"
pdst.mkdir(parents=True, exist_ok=True)
composite_out = ROOT / "manuscript/build_scripts/output/Extended_Data_Figure_2"
composite_pdst = composite_out / "panels"
composite_pdst.mkdir(parents=True, exist_ok=True)
src = ROOT / "reports/manuscript_extended_data_v1/edfig13_metric_robustness/panels"
for letter in ("a", "b", "c", "d"):
    for ext in [".png", ".pdf", "_source_data.tsv"]:
        s = src / f"edfig13_panel{letter}{ext}"
        if s.exists():
            dst_name = f"Extended_Data_Figure_2_panel_{letter}{ext}"
            shutil.copy2(s, pdst / dst_name)
            shutil.copy2(s, composite_pdst / dst_name)

# Combined figure
for ext in [".png", ".pdf", "_source_data.tsv"]:
    s = ROOT / f"reports/manuscript_extended_data_v1/edfig13_metric_robustness/edfig13{ext}"
    if s.exists():
        shutil.copy2(s, TEST / "Extended_Data_Figure_2" / f"Extended_Data_Figure_2{ext}")
# Panel e (separate script) and composite
panel_e_tmp = TEST / "Extended_Data_Figure_2" / "_panel_e_tmp"
if panel_e_tmp.exists():
    shutil.rmtree(panel_e_tmp)
panel_e_tmp.mkdir(parents=True, exist_ok=True)
subprocess.run(
    [sys.executable, str(ROOT / "scripts/manuscript/build_edfig2_panel_e.py"), "--output-dir", str(panel_e_tmp)],
    cwd=ROOT,
    check=True,
    env=env,
)
for src_name, dst_name in {
    "panel_e.png": "Extended_Data_Figure_2_panel_e.png",
    "panel_e.pdf": "Extended_Data_Figure_2_panel_e.pdf",
    "Extended_Data_Figure_2_panel_e_source_data.tsv": "Extended_Data_Figure_2_panel_e_source_data.tsv",
}.items():
    s = panel_e_tmp / src_name
    if s.exists():
        shutil.copy2(s, pdst / dst_name)
        shutil.copy2(s, composite_pdst / dst_name)
shutil.rmtree(panel_e_tmp)
subprocess.run([sys.executable, str(ROOT / "scripts/manuscript/build_edfig2_composite.py")], cwd=ROOT, check=True, env=env)
composite_png = composite_out / "Extended_Data_Figure_2.png"
if composite_png.exists():
    shutil.copy2(composite_png, TEST / "Extended_Data_Figure_2" / "Extended_Data_Figure_2.png")
composite_pdf = composite_out / "Extended_Data_Figure_2.pdf"
if composite_pdf.exists():
    shutil.copy2(composite_pdf, TEST / "Extended_Data_Figure_2" / "Extended_Data_Figure_2.pdf")

print(f"  Extended_Data_Figure_2 all panels + combined -> {TEST}")
