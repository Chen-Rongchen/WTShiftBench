from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "configs/entrants/supplement_entrants.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="统一运行当前 supplement entrant 池。")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH), help="supplement entrant registry 路径。")
    parser.add_argument(
        "--entrant-id",
        action="append",
        default=[],
        help="只运行指定 supplement entrant，可重复传入。",
    )
    parser.add_argument("--skip-build", action="store_true", help="透传给 entrant runner，只做 ingest/evaluate/render。")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_registry(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("entrants", [])
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path} 缺少非空 entrants 列表。")
    return rows


def run_command(command: list[str], *, dry_run: bool) -> None:
    print(" ".join(command))
    if dry_run:
        return
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    args = build_parser().parse_args()
    registry = load_registry(resolve_path(args.registry))
    selected = {item for item in args.entrant_id if item}

    for entry in registry:
        entrant_id = str(entry["entrant_id"])
        if selected and entrant_id not in selected:
            continue
        command = [
            sys.executable,
            "-m",
            str(entry["runner_module"]),
            "--batch-config",
            str(entry["batch_config"]),
        ]
        if args.skip_build:
            command.append("--skip-build")
        run_command(command, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

