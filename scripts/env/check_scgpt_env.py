#!/usr/bin/env python3
"""Verify the scGPT environment requires GPU PyTorch and importable scgpt."""

from __future__ import annotations

import importlib
import sys


def module_version(module_name: str) -> str:
    module = importlib.import_module(module_name)
    return getattr(module, "__version__", "unknown")


def main() -> int:
    failed: list[str] = []

    print("=== scGPT Environment Check ===")
    print(f"Python: {sys.version.split()[0]}")
    print()

    for module_name in ["torch", "transformers", "datasets", "accelerate", "scgpt"]:
        try:
            version = module_version(module_name)
        except Exception as exc:
            failed.append(module_name)
            print(f"✗ {module_name}: {exc}")
            continue
        print(f"✓ {module_name}: {version}")

    try:
        import torch

        cuda_available = torch.cuda.is_available()
        print()
        print(f"torch.version.cuda: {torch.version.cuda}")
        print(f"torch.cuda.is_available(): {cuda_available}")
        if cuda_available:
            print(f"GPU: {torch.cuda.get_device_name(0)}")
        else:
            failed.append("torch.cuda")
            print("GPU PyTorch required, but CUDA is unavailable.")
    except Exception as exc:
        failed.append("torch.cuda")
        print(f"torch.cuda check failed: {exc}")

    print()
    if failed:
        print("Result: FAILED")
        print("Failed checks:", ", ".join(failed))
        return 1

    print("Result: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
