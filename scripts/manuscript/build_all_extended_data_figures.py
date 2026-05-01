from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_CONFIG = Path("configs/manuscript/extended_data_figures_v1.json")
EXPECTED_PANEL_COUNTS = {
    "extended_data_figure1": 9,
    "extended_data_figure2": 4,
    "extended_data_figure3": 2,
    "extended_data_figure4": 2,
    "extended_data_figure5": 1,
}


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


def figure_number(figure_id: str) -> int:
    return int(figure_id.rsplit("figure", 1)[1])


def sync_to_manuscript(root: Path, figure: dict) -> None:
    num = figure_number(figure["figure_id"])
    src = root / figure["output_dir"]
    dst = root / "manuscript" / "extended_data" / f"Extended_Data_Figure_{num}"
    dst.mkdir(parents=True, exist_ok=True)
    panel_dst = dst / "panels"
    panel_dst.mkdir(exist_ok=True)

    for path in panel_dst.glob(f"Extended_Data_Figure_{num}_panel_*"):
        path.unlink()
    for suffix in (".png", ".pdf", "_source_data.tsv", "_panel_manifest.json"):
        path = dst / f"Extended_Data_Figure_{num}{suffix}"
        if path.exists():
            path.unlink()

    stem = figure.get("source_stem", f"edfig{num}")
    shutil.copy2(src / f"{stem}.png", dst / f"Extended_Data_Figure_{num}.png")
    shutil.copy2(src / f"{stem}.pdf", dst / f"Extended_Data_Figure_{num}.pdf")
    shutil.copy2(src / f"{stem}_source_data.tsv", dst / f"Extended_Data_Figure_{num}_source_data.tsv")
    shutil.copy2(src / f"{stem}_panel_manifest.json", dst / f"Extended_Data_Figure_{num}_panel_manifest.json")
    for panel_file in sorted((src / "panels").glob(f"{stem}_panel*")):
        rest = panel_file.name.removeprefix(f"{stem}_panel")
        letter, suffix = rest[0], rest[1:]
        shutil.copy2(panel_file, panel_dst / f"Extended_Data_Figure_{num}_panel_{letter}{suffix}")


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
        if not args.panels_only:
            sync_to_manuscript(root, figure)
    if not args.skip_verify and not args.panels_only:
        verify_outputs(root, figures)


if __name__ == "__main__":
    main()
