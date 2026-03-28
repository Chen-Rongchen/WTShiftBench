from __future__ import annotations

import json
import os
import sys
from typing import Any

import torch


def collect_cuda_env_probe(label: str) -> dict[str, Any]:
    return {
        "label": label,
        "sys_executable": sys.executable,
        "sys_argv0": sys.argv[0] if sys.argv else None,
        "sys_path0": sys.path[0] if sys.path else None,
        "cwd": os.getcwd(),
        "module_name": __name__,
        "package_name": __package__,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "nvidia_visible_devices": os.environ.get("NVIDIA_VISIBLE_DEVICES"),
        "path": os.environ.get("PATH"),
        "ld_library_path": os.environ.get("LD_LIBRARY_PATH"),
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "torch_cuda_is_available": bool(torch.cuda.is_available()),
        "torch_cuda_device_count": int(torch.cuda.device_count()),
    }


def emit_cuda_env_probe(label: str) -> dict[str, Any]:
    payload = collect_cuda_env_probe(label)
    print(json.dumps(payload, ensure_ascii=True), flush=True)
    return payload
