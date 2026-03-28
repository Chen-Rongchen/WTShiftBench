#!/usr/bin/env python3
"""GPU sanity check for the current WTKO workspace."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="检查宿主层与 pixi gears 环境里的 GPU/CUDA 可见性是否稳定。"
    )
    parser.add_argument("--probe-runs", type=int, default=5)
    parser.add_argument("--launcher-attempts", type=int, default=3)
    parser.add_argument("--launcher-sleep-seconds", type=float, default=1.0)
    return parser


def run_command(command: list[str]) -> tuple[int, str]:
    print(f"$ {shlex.join(command)}")
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if output.strip():
        print(output.rstrip())
    else:
        print("<no output>")
    return result.returncode, output


def extract_probe_payload(output: str) -> dict[str, object] | None:
    for line in reversed(output.splitlines()):
        candidate = line.strip()
        if not candidate.startswith("{"):
            continue
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and "torch_cuda_is_available" in payload:
            return payload
    return None


def host_device_nodes() -> list[str]:
    return sorted(str(path) for path in Path("/dev").glob("nvidia*"))


def main() -> int:
    args = build_parser().parse_args()
    failed: list[str] = []

    print("=== GPU Sanity Check ===")
    print(f"Project root: {PROJECT_ROOT}")
    print()

    print("== Host driver ==")
    nvidia_smi_rc, _ = run_command(["nvidia-smi", "-L"])
    if nvidia_smi_rc != 0:
        failed.append("host:nvidia-smi")

    nodes = host_device_nodes()
    print("$ python -c 'glob /dev/nvidia*'")
    if nodes:
        for node in nodes:
            print(node)
    else:
        print("<no /dev/nvidia*>")
        failed.append("host:/dev/nvidia*")
    print()

    print("== Pixi gears probe ==")
    successful_probes = 0
    for idx in range(1, args.probe_runs + 1):
        label = f"gpu_sanity_probe_{idx}"
        rc, output = run_command(
            [
                "pixi",
                "run",
                "--environment",
                "gears",
                "python",
                "scripts/probe_cuda_env.py",
                "--label",
                label,
            ]
        )
        payload = extract_probe_payload(output)
        probe_ok = (
            rc == 0
            and payload is not None
            and bool(payload.get("torch_cuda_is_available"))
            and int(payload.get("torch_cuda_device_count", 0)) > 0
        )
        if probe_ok:
            successful_probes += 1
        print(f"[probe {idx}/{args.probe_runs}] stable_cuda={probe_ok}")
        print()

    if successful_probes != args.probe_runs:
        failed.append(f"pixi-gears-probe:{successful_probes}/{args.probe_runs}")

    print("== GEARS launcher ==")
    launcher_rc, _ = run_command(
        [
            "python",
            "scripts/stage1a/adapters/gears/launch_build_predictions.py",
            "--max-attempts",
            str(args.launcher_attempts),
            "--sleep-seconds",
            str(args.launcher_sleep_seconds),
            "--",
            "--help",
        ]
    )
    if launcher_rc != 0:
        failed.append("gears-launcher")
    print()

    print("== Summary ==")
    print(f"host_nvidia_smi_ok={nvidia_smi_rc == 0}")
    print(f"host_device_nodes_ok={bool(nodes)}")
    print(f"pixi_gears_probe_successes={successful_probes}/{args.probe_runs}")
    print(f"gears_launcher_ok={launcher_rc == 0}")

    if failed:
        print("result=FAILED")
        print("failed_checks=" + ", ".join(failed))
        return 1

    print("result=PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
