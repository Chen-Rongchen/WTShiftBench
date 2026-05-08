from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/dixit_axis_compression_v1.json"


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_recipe(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="按配置运行 Dixit supplementary axis compression；默认配置固定为 GSE90063 K562 13d-only。"
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    return parser


def run_from_config(config_path: Path) -> dict[str, Path]:
    recipe = load_recipe(resolve_path(config_path))
    input_paths = dict(recipe["input_paths"])
    output_cfg = dict(recipe["output"])
    metrics = dict(recipe["metrics"])
    report_root = resolve_path(str(output_cfg["report_root"]))

    env = os.environ.copy()
    env["WTKO_DIXIT_BRIDGE_TABLE"] = str(resolve_path(str(input_paths["bridge_table"])))
    env["WTKO_DIXIT_HCC_ATLAS"] = str(resolve_path(str(input_paths["hcc_atlas"])))
    env["WTKO_DIXIT_HCC_AXIS_SUM"] = str(resolve_path(str(input_paths["hcc_axis_summary_macro"])))
    env["WTKO_DIXIT_HCC_FINE_SUM"] = str(resolve_path(str(input_paths["hcc_axis_summary_fine"])))
    env["WTKO_DIXIT_OUT_DIR"] = str(report_root)
    env["WTKO_DIXIT_PRIMARY_X"] = str(metrics["primary_x"])
    env["WTKO_DIXIT_PRIMARY_Y"] = str(metrics["primary_y"])

    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "stage2_dixit_axis_compression.py")]
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT), env=env)
    return {"report_root": report_root}


def main() -> None:
    args = build_parser().parse_args()
    run_from_config(Path(args.config))


if __name__ == "__main__":
    main()
