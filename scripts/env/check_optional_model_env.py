#!/usr/bin/env python3
"""Check optional candidate model environments.

The optional entrants are not required for the primary benchmark. This checker
only verifies importability and key package versions so installation failures
can be separated from model-eligibility decisions.
"""

from __future__ import annotations

import argparse
import importlib
from importlib import metadata
import sys


CHECKS: dict[str, list[tuple[str, str | None]]] = {
    "cellot": [
        ("torch", None),
        ("numpy", None),
        ("pandas", None),
        ("anndata", None),
        ("cellot", None),
    ],
    "scgen": [
        ("torch", None),
        ("numpy", None),
        ("anndata", None),
        ("scanpy", None),
        ("scgen", None),
    ],
    "scdisinfact": [
        ("torch", None),
        ("numpy", None),
        ("pandas", None),
        ("anndata", None),
        ("scDisInFact", None),
    ],
}


def module_version(module_name: str, distribution_name: str | None = None) -> str:
    module = importlib.import_module(module_name)
    if distribution_name:
        return metadata.version(distribution_name)
    return getattr(module, "__version__", "unknown")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check optional model environment imports.")
    parser.add_argument("model", choices=sorted(CHECKS), help="Optional model environment to check")
    args = parser.parse_args()

    failed: list[str] = []
    print(f"=== {args.model} Optional Model Environment Check ===")
    print(f"Python: {sys.version.split()[0]}")
    print()

    for module_name, dist_name in CHECKS[args.model]:
        try:
            version = module_version(module_name, dist_name)
        except Exception as exc:
            failed.append(module_name)
            print(f"✗ {module_name}: {exc}")
            continue
        print(f"✓ {module_name}: {version}")

    try:
        import torch

        print()
        print(f"torch.version.cuda: {torch.version.cuda}")
        print(f"torch.cuda.is_available(): {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")
    except Exception as exc:
        failed.append("torch.cuda_metadata")
        print(f"✗ torch metadata check failed: {exc}")

    print()
    if failed:
        print("Result: FAILED")
        print("failed:", ", ".join(failed))
        return 1
    print("Result: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
