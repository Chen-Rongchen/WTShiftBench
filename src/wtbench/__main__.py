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
        description="WT Benchmark 统一运行入口。默认使用 pixi 环境，不依赖 Docker 镜像。",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="CLI 注册表 JSON。也可用 WTBENCH_CLI_REGISTRY 指定。",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("version", help="打印项目版本。")
    sub.add_parser("list", help="列出注册表中的可运行命令。")

    run = sub.add_parser("run", help="运行一个注册命令。")
    run.add_argument("command", help="命令名，来自 configs/runtime/wtbench_cli_v1.json。")
    run.add_argument(
        "--config",
        type=Path,
        default=None,
        help="覆盖注册表默认配置；相对路径按项目根目录解析。",
    )
    run.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 输出返回值，便于流水线读取。",
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
        raise SystemExit(f"未知命令: {args.command}。可用命令: {available}")

    command = commands[args.command]
    config_path = resolve_command_config(command, args.config)
    result = run_registered_command(command, config_path)

    if args.json:
        print(json.dumps(render_jsonable(result), ensure_ascii=False, indent=2))
        return

    print(f"完成: {args.command}")
    print(f"- config: {config_path}")
    rendered = render_jsonable(result)
    if isinstance(rendered, dict):
        for key, value in rendered.items():
            print(f"- {key}: {value}")
    else:
        print(f"- result: {rendered}")


if __name__ == "__main__":
    main()
