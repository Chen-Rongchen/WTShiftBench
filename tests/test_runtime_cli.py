from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import wtbench
from wtbench.runtime import (
    build_runtime_commands,
    load_callable,
    load_cli_registry,
    resolve_command_config,
    run_registered_command,
)


def echo_config_path(config_path: Path) -> dict[str, str]:
    return {"config_path": str(config_path)}


class RuntimeCliTests(unittest.TestCase):
    def test_package_version_matches_pixi_workspace_version(self) -> None:
        text = Path("pixi.toml").read_text(encoding="utf-8")
        match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
        self.assertIsNotNone(match)
        self.assertEqual(wtbench.__version__, match.group(1))

    def test_default_registry_references_existing_configs_and_callables(self) -> None:
        commands = build_runtime_commands(load_cli_registry())
        self.assertGreaterEqual(len(commands), 10)
        for command in commands.values():
            self.assertIsNotNone(command.default_config)
            self.assertTrue(command.default_config.exists(), command.default_config)
            self.assertTrue(callable(load_callable(command.callable_path)))

    def test_registry_schema_document_exists(self) -> None:
        schema_path = Path("configs/runtime/wtbench_cli.schema.json")
        self.assertTrue(schema_path.exists())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["title"], "WTBench CLI registry")

    def test_registry_builds_dynamic_commands(self) -> None:
        registry = {
            "commands": {
                "demo": {
                    "callable": "tests.test_runtime_cli:echo_config_path",
                    "description": "demo command",
                    "default_config": "configs/demo.json",
                    "config_env": "WTBENCH_DEMO_CONFIG",
                }
            }
        }
        commands = build_runtime_commands(registry)
        self.assertIn("demo", commands)
        self.assertEqual(commands["demo"].description, "demo command")
        self.assertTrue(str(commands["demo"].default_config).endswith("configs/demo.json"))

    def test_config_resolution_prefers_cli_override(self) -> None:
        command = build_runtime_commands(
            {
                "commands": {
                    "demo": {
                        "callable": "tests.test_runtime_cli:echo_config_path",
                        "default_config": "configs/default.json",
                        "config_env": "WTBENCH_DEMO_CONFIG",
                    }
                }
            }
        )["demo"]
        config = resolve_command_config(command, Path("configs/override.json"))
        self.assertTrue(str(config).endswith("configs/override.json"))

    def test_config_resolution_uses_environment_override(self) -> None:
        command = build_runtime_commands(
            {
                "commands": {
                    "demo": {
                        "callable": "tests.test_runtime_cli:echo_config_path",
                        "default_config": "configs/default.json",
                        "config_env": "WTBENCH_DEMO_CONFIG",
                    }
                }
            }
        )["demo"]
        with patch.dict("os.environ", {"WTBENCH_DEMO_CONFIG": "configs/from_env.json"}):
            config = resolve_command_config(command)
        self.assertTrue(str(config).endswith("configs/from_env.json"))

    def test_load_registry_and_run_callable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            registry_path = root / "registry.json"
            config_path = root / "config.json"
            config_path.write_text("{}", encoding="utf-8")
            registry_path.write_text(
                json.dumps(
                    {
                        "commands": {
                            "demo": {
                                "callable": "tests.test_runtime_cli:echo_config_path",
                                "default_config": str(config_path),
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            registry = load_cli_registry(registry_path)
            command = build_runtime_commands(registry)["demo"]
            result = run_registered_command(command, resolve_command_config(command))
            self.assertEqual(result["config_path"], str(config_path))


if __name__ == "__main__":
    unittest.main()
