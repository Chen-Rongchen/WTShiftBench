from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_CONFIG = Path("configs/manuscript/main_figures_v2.json")
EXPECTED_PANEL_COUNTS = {
    "figure1": 6,
    "figure2": 6,
    "figure3": 4,
    "figure4": 3,
    "figure5": 2,
    "figure6": 4,
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def run_figure(root: Path, figure: dict, panels_only: bool) -> None:
    script = root / figure["script"]
    cmd = [sys.executable, str(script)]
    if panels_only:
        cmd.append("--panels-only")
    subprocess.run(cmd, cwd=root, check=True)


def verify_outputs(root: Path, figures: list[dict]) -> None:
    for figure in figures:
        out = root / figure["output_dir"]
        panels = out / "panels"
        figure_num = figure["figure_id"].replace("figure", "")
        counts = {
            "panel_png": len(list(panels.glob("*_panel*.png"))),
            "panel_pdf": len(list(panels.glob("*_panel*.pdf"))),
            "panel_source": len(list(panels.glob("*_panel*_source_data.tsv"))),
            "panel_manifest": len(list(panels.glob("*_panel*_manifest.json"))),
            "figure_png": len(list(out.glob(f"figure{figure_num}.png"))),
            "figure_pdf": len(list(out.glob(f"figure{figure_num}.pdf"))),
            "figure_source": len(list(out.glob(f"figure{figure_num}_source_data.tsv"))),
            "figure_manifest": len(list(out.glob(f"figure{figure_num}_panel_manifest.json"))),
        }
        expected_panel_count = EXPECTED_PANEL_COUNTS[figure["figure_id"]]
        expected = {
            "panel_png": expected_panel_count,
            "panel_pdf": expected_panel_count,
            "panel_source": expected_panel_count,
            "panel_manifest": expected_panel_count,
            "figure_png": 1,
            "figure_pdf": 1,
            "figure_source": 1,
            "figure_manifest": 1,
        }
        if counts != expected:
            raise RuntimeError(f"{figure['figure_id']} output check failed: {counts}")
        print(f"{figure['figure_id']}\t{figure['name']}\tok")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build all main manuscript figures from the configured panel scripts.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--panels-only", action="store_true")
    parser.add_argument("--skip-verify", action="store_true")
    args = parser.parse_args(argv)

    root = repo_root()
    config = load_config(root / args.config)
    figures = config["figures"]
    for figure in figures:
        print(f"building {figure['figure_id']}: {figure['name']}")
        run_figure(root, figure, args.panels_only)
    if not args.skip_verify and not args.panels_only:
        verify_outputs(root, figures)


if __name__ == "__main__":
    main()
