from __future__ import annotations

import subprocess
import sys

from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT


MAINLINE_MODULES = [
    "scripts.render_stage1a_formal_registry",
    "scripts.analyze_stage1a_pseudobulk_eligibility",
    "scripts.build_stage1a_admission_manifest",
    "scripts.freeze_stage1a_formal_inputs",
]


def run_module(module_name: str) -> None:
    command = [sys.executable, "-m", module_name]
    print(f"开始执行: {' '.join(command)}")
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    for module_name in MAINLINE_MODULES:
        run_module(module_name)
    print("Stage 1A formal freeze benchmark-invariant 主线已完成。")


if __name__ == "__main__":
    main()
