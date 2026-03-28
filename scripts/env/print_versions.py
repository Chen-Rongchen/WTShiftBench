#!/usr/bin/env python3
"""打印当前环境的 Python、平台、关键依赖与 GPU 状态。"""

from __future__ import annotations

import importlib
from importlib import metadata
import platform
import sys
from typing import Optional


PACKAGE_MAP = {
    "numpy": ("numpy", None),
    "pandas": ("pandas", None),
    "scipy": ("scipy", None),
    "pyyaml": ("yaml", "PyYAML"),
    "rich": ("rich", None),
    "typer": ("typer", None),
    "anndata": ("anndata", None),
    "torch": ("torch", "torch"),
    "pytorch-lightning": ("pytorch_lightning", "pytorch-lightning"),
    "torch-geometric": ("torch_geometric", "torch-geometric"),
    "cell-gears": ("gears", "cell-gears"),
    "transformers": ("transformers", None),
    "datasets": ("datasets", None),
    "accelerate": ("accelerate", None),
    "scgpt": ("scgpt", None),
    "geneformer": ("geneformer", "geneformer"),
}


def get_package_version(package_name: str) -> str:
    """尝试获取包的版本号，如果未安装返回 `not installed`。"""
    module_name, distribution_name = PACKAGE_MAP.get(package_name, (package_name, None))

    try:
        module = importlib.import_module(module_name)
    except Exception:
        return "not installed"

    version = getattr(module, "__version__", None)
    if version:
        return version

    try:
        return metadata.version(distribution_name or package_name)
    except Exception:
        return "installed (version unknown)"


def print_gpu_info():
    """打印 GPU 信息。"""
    try:
        import torch
        if torch.cuda.is_available():
            print("GPU Information:")
            print(f"  ✓ CUDA available: {torch.cuda.is_available()}")
            print(f"  ✓ GPU count: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"    - GPU {i}: {torch.cuda.get_device_name(i)}")
            if torch.version.cuda:
                print(f"  ✓ CUDA version: {torch.version.cuda}")
            print()
        else:
            print("GPU Information:")
            print("  ✗ CUDA not available")
            print()
    except ImportError:
        print("GPU Information:")
        print("  ✗ PyTorch not available")
        print()


def print_versions(environment: Optional[str] = None):
    """打印版本信息。"""
    if environment:
        print(f"=== {environment.upper()} Environment Version Report ===")
    else:
        print("=== Version Report ===")
    print()

    print(f"Python: {sys.version.split()[0]}")
    print()

    print("Platform:")
    print(f"  System: {platform.system()}")
    print(f"  Release: {platform.release()}")
    print(f"  Machine: {platform.machine()}")
    print(f"  Processor: {platform.processor()}")
    print()

    common_packages = ["numpy", "pandas", "scipy", "pyyaml", "rich", "typer", "anndata"]
    env_specific = {
        "core": [],
        "gears": ["torch", "pytorch-lightning", "torch-geometric", "cell-gears"],
        "scgpt": ["torch", "transformers", "datasets", "accelerate", "scgpt"],
        "geneformer": ["torch", "transformers", "datasets", "accelerate", "geneformer"],
    }

    if environment and environment in env_specific:
        display_packages = common_packages + env_specific[environment]
    else:
        display_packages = common_packages + sorted({pkg for packages in env_specific.values() for pkg in packages})

    print("Package Versions:")
    for pkg in display_packages:
        version = get_package_version(pkg)
        status = "✓" if version != "not installed" else "✗"
        print(f"  {status} {pkg}: {version}")

    print()
    if get_package_version("torch") != "not installed":
        print_gpu_info()

    print("=" * 50)


def main():
    environment = None
    if len(sys.argv) > 1:
        environment = sys.argv[1].lower()

    print_versions(environment)


if __name__ == "__main__":
    main()
