#!/usr/bin/env python3
"""Build helper: run a build script and copy outputs to test_output."""
import shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "manuscript/build_scripts/test_output"


def run_script(script: str, panels_only: bool = True) -> None:
    cmd = [sys.executable, str(ROOT / script)]
    if panels_only:
        cmd.append("--panels-only")
    subprocess.run(cmd, cwd=ROOT, check=True, env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")})


def copy_panels(src_dir: str, dst_dir: str, file_map: dict[str, str]) -> None:
    """Copy panel files from reports src_dir to test_output dst_dir, renaming per file_map."""
    src = ROOT / src_dir
    dst = TEST / dst_dir
    dst.mkdir(parents=True, exist_ok=True)
    for old_name, new_name in file_map.items():
        for ext in [".png", ".pdf", "_source_data.tsv"]:
            s = src / f"{old_name}{ext}"
            if s.exists():
                shutil.copy2(s, dst / f"{new_name}{ext}")
        # also copy manifest
        s = src / f"{old_name}_manifest.json"
        if s.exists():
            shutil.copy2(s, dst / f"{new_name}_manifest.json")


def copy_combined(src_path: str, dst_name: str) -> None:
    """Copy combined figure from reports to test_output."""
    src = ROOT / src_path
    dst_dir = TEST / dst_name
    dst_dir.mkdir(parents=True, exist_ok=True)
    for ext in [".png", ".pdf"]:
        s = Path(str(src) + ext)
        if s.exists():
            shutil.copy2(s, dst_dir / f"{dst_name}{ext}")
