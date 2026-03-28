from __future__ import annotations

import importlib
import json
import os
import sys
from typing import Any


def snapshot(label: str) -> dict[str, Any]:
    import torch

    payload = {
        "label": label,
        "sys_executable": sys.executable,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "nvidia_visible_devices": os.environ.get("NVIDIA_VISIBLE_DEVICES"),
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "torch_cuda_is_available": bool(torch.cuda.is_available()),
        "torch_cuda_device_count": int(torch.cuda.device_count()),
    }
    print(json.dumps(payload, ensure_ascii=True), flush=True)
    return payload


def import_and_probe(module_name: str) -> None:
    importlib.import_module(module_name)
    snapshot(f"after_import:{module_name}")


def main() -> None:
    snapshot("initial")
    for module_name in [
        "argparse",
        "pickle",
        "random",
        "pathlib",
        "anndata",
        "numpy",
        "pandas",
        "scipy.sparse",
        "torch_geometric.data",
        "gears",
        "gears.inference",
        "gears.utils",
        "scripts.stage1a.adapters.common.runtime",
        "scripts.stage1a.benchmark_invariant.catalog",
        "scripts.stage1a.benchmark_invariant.prediction_eval_common",
    ]:
        import_and_probe(module_name)


if __name__ == "__main__":
    main()
