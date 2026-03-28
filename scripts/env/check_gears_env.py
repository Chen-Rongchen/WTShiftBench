#!/usr/bin/env python3
"""验证 GEARS 环境，要求 GPU PyTorch 与 `gears` 可导入。"""

from __future__ import annotations

import importlib
from importlib import metadata
import sys


def import_and_version(module_name: str, distribution_name: str | None = None) -> str:
    importlib.import_module(module_name)
    if distribution_name is not None:
        return metadata.version(distribution_name)
    module = sys.modules[module_name]
    return getattr(module, "__version__", "unknown")


def main() -> int:
    failed: list[str] = []

    print("=== GEARS Environment Check ===")
    print(f"Python: {sys.version.split()[0]}")
    print()

    required = [
        ("torch", None),
        ("pytorch_lightning", "pytorch-lightning"),
        ("torch_geometric", "torch-geometric"),
        ("gears", "cell-gears"),
    ]

    for module_name, dist_name in required:
        try:
            version = import_and_version(module_name, dist_name)
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
            print("✗ 需要 GPU 版 PyTorch，但当前 CUDA 不可用。")
    except Exception as exc:
        failed.append("torch.cuda")
        print(f"✗ torch.cuda 检查失败: {exc}")

    print()
    if failed:
        print("Result: FAILED")
        print("失败项:", ", ".join(failed))
        return 1

    print("Result: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
