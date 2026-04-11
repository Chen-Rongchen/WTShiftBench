from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_recipe(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按配置运行 Dixit supplementary axis compression。")
    parser.add_argument("--config", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    recipe = load_recipe(resolve_path(args.config))
    input_paths = dict(recipe["input_paths"])
    output_cfg = dict(recipe["output"])
    metrics = dict(recipe["metrics"])

    env = os.environ.copy()
    env["WTKO_DIXIT_BRIDGE_TABLE"] = str(resolve_path(str(input_paths["bridge_table"])))
    env["WTKO_DIXIT_HCC_ATLAS"] = str(resolve_path(str(input_paths["hcc_atlas"])))
    env["WTKO_DIXIT_HCC_AXIS_SUM"] = str(resolve_path(str(input_paths["hcc_axis_summary_macro"])))
    env["WTKO_DIXIT_HCC_FINE_SUM"] = str(resolve_path(str(input_paths["hcc_axis_summary_fine"])))
    env["WTKO_DIXIT_OUT_DIR"] = str(resolve_path(str(output_cfg["report_root"])))
    env["WTKO_DIXIT_PRIMARY_X"] = str(metrics["primary_x"])
    env["WTKO_DIXIT_PRIMARY_Y"] = str(metrics["primary_y"])

    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "stage2_dixit_axis_compression.py")]
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT), env=env)


if __name__ == "__main__":
    main()
