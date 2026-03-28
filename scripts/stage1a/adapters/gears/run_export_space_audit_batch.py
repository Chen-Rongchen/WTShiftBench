from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_BATCH_CONFIG = ROOT / "configs/stage1a/adapters/formal/gears_stage1a_formal.batch.yaml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="批量执行 GEARS export-space audit。")
    parser.add_argument("--batch-config", default=str(DEFAULT_BATCH_CONFIG))
    parser.add_argument("--audit-root")
    return parser


def load_run_config_paths(batch_yaml: Path) -> list[str]:
    payload = yaml.safe_load(batch_yaml.read_text(encoding="utf-8")) or {}
    paths = payload.get("run_configs")
    if not isinstance(paths, list) or not paths:
        raise ValueError(f"{batch_yaml} 缺少非空 run_configs")
    return [str(path) for path in paths]


def run(command: list[str]) -> None:
    print("==", " ".join(command), "==", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    args = build_parser().parse_args()
    batch_config = Path(args.batch_config)
    if not batch_config.is_absolute():
        batch_config = ROOT / batch_config
    for run_config in load_run_config_paths(batch_config):
        command = [
            "pixi",
            "run",
            "--environment",
            "gears",
            "python",
            "scripts/stage1a/adapters/gears/export_space_audit.py",
            "--run-config",
            run_config,
        ]
        if args.audit_root:
            command.extend(["--audit-root", args.audit_root])
        run(command)


if __name__ == "__main__":
    main()
