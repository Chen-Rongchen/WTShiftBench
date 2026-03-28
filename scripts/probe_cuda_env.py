from __future__ import annotations

import argparse

from scripts.cuda_env_probe import emit_cuda_env_probe


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="打印当前进程的 CUDA 环境探针。")
    parser.add_argument("--label", default="probe_cuda_env.py")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    emit_cuda_env_probe(args.label)


if __name__ == "__main__":
    main()
