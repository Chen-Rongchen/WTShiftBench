from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
GEARS_ENV = "gears"
PROBE_SCRIPT = "scripts/probe_cuda_env.py"
TARGET_SCRIPT = "scripts/stage1a/adapters/gears/export_space_audit.py"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="通过独立 probe + 重试稳定启动 GEARS export_space_audit。"
    )
    parser.add_argument("--max-attempts", type=int, default=8)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    return parser


def run_and_tee(command: list[str]) -> tuple[int, str]:
    print(f"[gears-audit-launch] exec: {' '.join(command)}", flush=True)
    process = subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    chunks: list[str] = []
    for line in process.stdout:
        print(line, end="")
        chunks.append(line)
    return process.wait(), "".join(chunks)


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


def probe_has_cuda(output: str) -> bool:
    payload = extract_probe_payload(output)
    if payload is None:
        return False
    return bool(payload.get("torch_cuda_is_available")) and int(payload.get("torch_cuda_device_count", 0)) > 0


def is_cuda_visibility_failure(output: str) -> bool:
    markers = [
        "Can't initialize NVML",
        '"torch_cuda_is_available": false',
        "请求 device=cuda，但当前环境不可用 CUDA。",
    ]
    return any(marker in output for marker in markers)


def main() -> int:
    parser = build_parser()
    args, forwarded = parser.parse_known_args()
    if forwarded[:1] == ["--"]:
        forwarded = forwarded[1:]
    if args.max_attempts < 1:
        raise ValueError("--max-attempts 必须 >= 1")
    if not forwarded:
        forwarded = ["--help"]

    probe_command = [
        "pixi",
        "run",
        "--environment",
        GEARS_ENV,
        "python",
        PROBE_SCRIPT,
        "--label",
        "launch_export_space_audit:probe",
    ]
    target_command = [
        "pixi",
        "run",
        "--environment",
        GEARS_ENV,
        "python",
        TARGET_SCRIPT,
        *forwarded,
    ]

    for attempt in range(1, args.max_attempts + 1):
        print(
            f"[gears-audit-launch] attempt {attempt}/{args.max_attempts}: probing CUDA visibility",
            flush=True,
        )
        probe_rc, probe_output = run_and_tee(probe_command)
        if probe_rc == 0 and probe_has_cuda(probe_output):
            print(f"[gears-audit-launch] attempt {attempt}: CUDA visible, launching target", flush=True)
            target_rc, target_output = run_and_tee(target_command)
            if target_rc == 0:
                return 0
            if is_cuda_visibility_failure(target_output) and attempt < args.max_attempts:
                print(
                    f"[gears-audit-launch] attempt {attempt}: target lost CUDA visibility, retrying after {args.sleep_seconds}s",
                    flush=True,
                )
                time.sleep(args.sleep_seconds)
                continue
            return target_rc

        if attempt < args.max_attempts:
            print(
                f"[gears-audit-launch] attempt {attempt}: probe did not see CUDA, retrying after {args.sleep_seconds}s",
                flush=True,
            )
            time.sleep(args.sleep_seconds)

    print(
        f"[gears-audit-launch] exhausted {args.max_attempts} attempts without a stable CUDA-visible GEARS process",
        flush=True,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
