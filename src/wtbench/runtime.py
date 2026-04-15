from __future__ import annotations

import importlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CLI_REGISTRY_PATH = PROJECT_ROOT / "configs/runtime/wtbench_cli_v1.json"
CLI_REGISTRY_ENV = "WTBENCH_CLI_REGISTRY"


@dataclass(frozen=True)
class RuntimeCommand:
    name: str
    callable_path: str
    description: str
    default_config: Path | None
    config_env: str | None


def resolve_project_path(path: str | Path) -> Path:
    value = Path(path)
    if value.is_absolute():
        return value
    return PROJECT_ROOT / value


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_cli_registry(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = resolve_project_path(os.environ.get(CLI_REGISTRY_ENV, DEFAULT_CLI_REGISTRY_PATH))
    payload = load_json(path)
    validate_cli_registry(payload, path=path)
    return payload


def validate_cli_registry(payload: dict[str, Any], *, path: Path) -> None:
    if "commands" not in payload:
        raise ValueError(f"{path} 缺少 commands。")
    if not isinstance(payload["commands"], dict) or not payload["commands"]:
        raise ValueError(f"{path} 的 commands 必须是非空 JSON 对象。")
    for name, item in payload["commands"].items():
        if not isinstance(item, dict):
            raise ValueError(f"{path} 命令 {name} 必须是 JSON 对象。")
        missing = sorted({"callable", "default_config"} - set(item))
        if missing:
            raise ValueError(f"{path} 命令 {name} 缺少字段: {missing}")
        if ":" not in str(item["callable"]):
            raise ValueError(f"{path} 命令 {name} callable 必须采用 module:function 格式。")
        if item.get("config_env") is not None and not str(item["config_env"]).startswith("WTBENCH_"):
            raise ValueError(f"{path} 命令 {name} config_env 必须以 WTBENCH_ 开头。")


def build_runtime_commands(registry: dict[str, Any]) -> dict[str, RuntimeCommand]:
    commands: dict[str, RuntimeCommand] = {}
    for name, item in registry["commands"].items():
        default_config = item.get("default_config")
        commands[str(name)] = RuntimeCommand(
            name=str(name),
            callable_path=str(item["callable"]),
            description=str(item.get("description", "")),
            default_config=resolve_project_path(default_config) if default_config else None,
            config_env=str(item["config_env"]) if item.get("config_env") else None,
        )
    return commands


def resolve_command_config(command: RuntimeCommand, override: Path | None = None) -> Path:
    if override is not None:
        return resolve_project_path(override)
    if command.config_env:
        env_value = os.environ.get(command.config_env)
        if env_value:
            return resolve_project_path(env_value)
    if command.default_config is not None:
        return command.default_config
    raise ValueError(f"{command.name} 未配置 default_config，必须通过 --config 指定。")


def load_callable(callable_path: str) -> Callable[..., Any]:
    if ":" not in callable_path:
        raise ValueError(f"callable 必须采用 module:function 格式: {callable_path}")
    module_name, function_name = callable_path.split(":", 1)
    module = importlib.import_module(module_name)
    fn = getattr(module, function_name)
    if not callable(fn):
        raise TypeError(f"{callable_path} 不是可调用对象。")
    return fn


def render_jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): render_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [render_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [render_jsonable(v) for v in value]
    return value


def run_registered_command(command: RuntimeCommand, config_path: Path) -> Any:
    fn = load_callable(command.callable_path)
    return fn(config_path)
