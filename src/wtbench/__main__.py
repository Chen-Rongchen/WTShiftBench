from __future__ import annotations

import argparse
import json
from pathlib import Path

from wtbench import __version__
from wtbench.runtime import (
    build_runtime_commands,
    load_cli_registry,
    render_jsonable,
    resolve_command_config,
    resolve_project_path,
    run_registered_command,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wtbench",
        description="Unified WT Benchmark entry point; uses Pixi by default without requiring Docker images.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="CLI registry JSON; alternatively set WTBENCH_CLI_REGISTRY.",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("version", help="Print project version.")
    sub.add_parser("list", help="List runnable registry commands.")

    run = sub.add_parser("run", help="Run a registered command.")
    run.add_argument("command", help="Command name from configs/runtime/wtbench_cli_v1.json.")
    run.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Override the registered default configuration; resolve relative paths from the project root.",
    )
    run.add_argument(
        "--json",
        action="store_true",
        help="Output returned values as JSON for pipeline consumption.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.action == "version":
        print(__version__)
        return

    registry = load_cli_registry(resolve_project_path(args.registry) if args.registry else None)
    commands = build_runtime_commands(registry)

    if args.action == "list":
        for name, command in sorted(commands.items()):
            config = command.default_config if command.default_config is not None else "<required>"
            env = command.config_env or "-"
            print(f"{name}\tconfig={config}\tenv={env}\t{command.description}")
        return

    if args.command not in commands:
        available = ", ".join(sorted(commands))
        raise SystemExit(f"Unknown command: {args.command}. Available: {available}")

    command = commands[args.command]
    config_path = resolve_command_config(command, args.config)
    result = run_registered_command(command, config_path)

    if args.json:
        print(json.dumps(render_jsonable(result), ensure_ascii=False, indent=2))
        return

    print(f"Completed: {args.command}")
    print(f"- config: {config_path}")
    rendered = render_jsonable(result)
    if isinstance(rendered, dict):
        for key, value in rendered.items():
            print(f"- {key}: {value}")
    else:
        print(f"- result: {rendered}")


if __name__ == "__main__":
    main()
