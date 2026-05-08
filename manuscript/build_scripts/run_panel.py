#!/usr/bin/env python3
"""Generic panel builder: run original build script, copy target panel to test_output."""
import shutil, subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "manuscript/build_scripts/test_output"

def build_panel(build_script: str, reports_panel_dir: str,
                src_stem: str, dst_stem: str, panel_id: str, dst_subdir: str):
    """Run build script with --panels-only, then copy target panel."""
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    subprocess.run(
        [sys.executable, str(ROOT / build_script), "--panels-only"],
        cwd=ROOT, check=True, env=env,
    )
    dst = TEST / dst_subdir / "panels"
    dst.mkdir(parents=True, exist_ok=True)
    src = ROOT / reports_panel_dir
    for ext in [".png", ".pdf", "_source_data.tsv"]:
        s = src / f"{src_stem}_panel{panel_id}{ext}"
        if s.exists():
            shutil.copy2(s, dst / f"{dst_stem}_panel_{panel_id}{ext}")
    print(f"  {dst_stem} panel {panel_id} -> {dst}")
