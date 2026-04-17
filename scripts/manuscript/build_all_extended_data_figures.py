from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_CONFIG = Path("configs/manuscript/extended_data_figures_v1.json")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def run_figure(root: Path, figure: dict, panels_only: bool) -> None:
    cmd = [sys.executable, str(root / figure["script"])]
    if panels_only:
        cmd.append("--panels-only")
    subprocess.run(cmd, cwd=root, check=True)


def verify_outputs(root: Path, figures: list[dict]) -> None:
    for figure in figures:
        out = root / figure["output_dir"]
        panels = out / "panels"
        counts = {
            "panel_png": len(list(panels.glob("*.png"))),
            "panel_pdf": len(list(panels.glob("*.pdf"))),
            "panel_source": len(list(panels.glob("*_source_data.tsv"))),
            "panel_manifest": len(list(panels.glob("*_manifest.json"))),
            "figure_png": len(list(out.glob("*.png"))),
            "figure_pdf": len(list(out.glob("*.pdf"))),
            "figure_source": len(list(out.glob("*_source_data.tsv"))),
            "figure_manifest": len(list(out.glob("*_panel_manifest.json"))),
        }
        expected = {
            "panel_png": 8,
            "panel_pdf": 8,
            "panel_source": 8,
            "panel_manifest": 8,
            "figure_png": 1,
            "figure_pdf": 1,
            "figure_source": 1,
            "figure_manifest": 1,
        }
        if counts != expected:
            raise RuntimeError(f"{figure['figure_id']} output check failed: {counts}")
        print(f"{figure['figure_id']}\t{figure['name']}\tok")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build configured Extended Data figures.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--panels-only", action="store_true")
    parser.add_argument("--skip-verify", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    figures = load_config(root / args.config)["figures"]
    for figure in figures:
        print(f"building {figure['figure_id']}: {figure['name']}")
        run_figure(root, figure, args.panels_only)
    if not args.skip_verify and not args.panels_only:
        verify_outputs(root, figures)


if __name__ == "__main__":
    main()
