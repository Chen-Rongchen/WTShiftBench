#!/usr/bin/env python3
"""从「已完成 formal-filter-stage1a」起：formal freeze → truth → 三模型 adapter（按 *.batch.yaml）→ 批量 scoring。"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def log_env_cuda(env: str) -> None:
    """各子进程独立环境，启动 adapter 前打印该 env 下 PyTorch 是否可用 CUDA。"""
    code = (
        "import torch; c=torch.cuda.is_available(); "
        "print('cuda=' + str(c) + (', device=' + repr(torch.cuda.get_device_name(0)) if c else ''))"
    )
    r = subprocess.run(
        ["pixi", "run", "--environment", env, "python", "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    out = (r.stdout or "").strip() or (r.stderr or "").strip()
    print(f"[{env}] torch: {out}", flush=True)

ADAPTER_BATCHES: list[tuple[str, str, Path]] = [
    (
        "gears",
        "default",
        ROOT / "configs/stage1a/adapters/formal/gears_stage1a_formal.batch.yaml",
    ),
    (
        "scgpt",
        "scgpt",
        ROOT / "configs/stage1a/adapters/formal/scgpt_embedding_kernel_formal.batch.yaml",
    ),
    (
        "geneformer",
        "geneformer",
        ROOT / "configs/stage1a/adapters/formal/geneformer_embedding_kernel_formal.batch.yaml",
    ),
]

BUILD_COMMANDS = {
    "gears": ["python", "scripts/stage1a/adapters/gears/launch_build_predictions.py"],
    "scgpt": ["python", "-m", "scripts.stage1a.adapters.scgpt.build_predictions"],
    "geneformer": ["python", "-m", "scripts.stage1a.adapters.geneformer.build_predictions"],
}

SCORING_BATCH = "configs/stage1a/runs/batch_scoring_three_models_formal.yaml"


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="从 formal freeze 开始执行三模型 Stage 1A 预测与批量 scoring。"
    )


def run(cmd: list[str]) -> None:
    print("==", " ".join(cmd), "==", flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def load_run_config_paths(batch_yaml: Path) -> list[str]:
    payload = yaml.safe_load(batch_yaml.read_text(encoding="utf-8")) or {}
    paths = payload.get("run_configs")
    if not isinstance(paths, list) or not paths:
        raise ValueError(f"{batch_yaml} 缺少非空 run_configs")
    return [str(p) for p in paths]


def main() -> None:
    build_parser().parse_args()
    run(["pixi", "run", "run-stage1a-formal-freeze-mainline"])
    run(["pixi", "run", "run-stage1a-truth-space-mainline"])

    seen_env: set[str] = set()
    for name, env, batch_path in ADAPTER_BATCHES:
        probe_env = "gears" if name == "gears" else env
        if probe_env not in seen_env:
            log_env_cuda(probe_env)
            seen_env.add(probe_env)
        for rc in load_run_config_paths(batch_path):
            rc_path = ROOT / rc
            if not rc_path.is_file():
                raise FileNotFoundError(rc_path)
            run(
                [
                    "pixi",
                    "run",
                    "--environment",
                    env,
                    *BUILD_COMMANDS[name],
                    "--run-config",
                    rc,
                ]
            )

    run(
        [
            "pixi",
            "run",
            "run-stage1a-batch-scoring-pipeline",
            "--",
            "--batch-config",
            SCORING_BATCH,
        ]
    )
    print("完成：三模型 × 三数据集预测与 batch scoring 已跑完。", flush=True)


if __name__ == "__main__":
    main()
