#!/usr/bin/env python3
"""验证 core 环境的主链路依赖。"""

from __future__ import annotations

import importlib
import sys


REQUIRED_MODULES = [
    "numpy",
    "pandas",
    "scipy",
    "yaml",
    "rich",
    "typer",
    "anndata",
]


def module_version(module_name: str) -> str:
    module = importlib.import_module(module_name)
    return getattr(module, "__version__", "unknown")


def main() -> int:
    failed: list[str] = []

    print("=== Core Environment Check ===")
    print(f"Python: {sys.version.split()[0]}")
    print()

    for module_name in REQUIRED_MODULES:
        try:
            version = module_version(module_name)
        except Exception as exc:
            failed.append(module_name)
            print(f"✗ {module_name}: {exc}")
            continue
        print(f"✓ {module_name}: {version}")

    print()
    if failed:
        print("Result: FAILED")
        print("缺失或不可用模块:", ", ".join(failed))
        return 1

    print("Result: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
