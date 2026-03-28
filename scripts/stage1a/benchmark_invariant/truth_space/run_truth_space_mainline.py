from __future__ import annotations

import subprocess
import sys

from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT


MAINLINE_MODULES = [
    "scripts.build_stage1a_pseudobulk_delta_truth",
    "scripts.freeze_stage1a_truth",
    "scripts.build_stage1a_evaluation_space",
    "scripts.build_stage1a_main_aligned_baselines_nulls",
]


def run_module(module_name: str) -> None:
    command = [sys.executable, "-m", module_name]
    print(f"开始执行: {' '.join(command)}")
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    for module_name in MAINLINE_MODULES:
        run_module(module_name)
    print("Stage 1A truth/evaluation-space benchmark-invariant 主线已完成。")


if __name__ == "__main__":
    main()
