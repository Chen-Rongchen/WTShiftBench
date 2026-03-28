#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np

from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT, get_formal_dataset_contract
from scripts.stage1a.benchmark_invariant.prediction_eval_common import json_dump, load_main_aligned_truth_entry, read_matrix


DEFAULT_CONFIG = PROJECT_ROOT / "configs/entrants/stage1a_inner_split_3datasets_seed101.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="物化 Stage 1A outer split 与 inner validation split。")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="split 配置 JSON 路径。",
    )
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON object。")
    return payload


def ensure_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} 必须是非空列表。")
    return value


def build_target_level_split_manifest(
    dataset_id: str,
    split_seed: int,
    *,
    heldout_fraction: float,
) -> dict[str, Any]:
    split_dir = PROJECT_ROOT / "artifacts" / "splits" / dataset_id / f"seed{split_seed}"
    train_path = split_dir / "train_targets.txt"
    heldout_path = split_dir / "heldout_targets.txt"
    manifest_path = split_dir / "manifest.json"
    if train_path.exists() and heldout_path.exists():
        train_targets = tuple(line.strip() for line in train_path.read_text(encoding="utf-8").splitlines() if line.strip())
        heldout_targets = tuple(
            line.strip() for line in heldout_path.read_text(encoding="utf-8").splitlines() if line.strip()
        )
        return {
            "dataset_id": dataset_id,
            "split_seed": split_seed,
            "train_targets": train_targets,
            "heldout_targets": heldout_targets,
            "manifest_path": manifest_path,
            "split_dir": split_dir,
        }

    truth = read_matrix(load_main_aligned_truth_entry(dataset_id).path)
    truth_targets = set(truth.index.astype(str).tolist())
    formal_adata = ad.read_h5ad(get_formal_dataset_contract(dataset_id).path)
    try:
        obs = formal_adata.obs.copy()
        obs["is_control"] = obs["is_control"].astype(bool)
        obs["target_gene"] = obs["target_gene"].astype("string").fillna("")
        candidate_targets = sorted(
            target
            for target in obs.loc[~obs["is_control"], "target_gene"].dropna().astype(str).unique().tolist()
            if target and target in truth_targets
        )
    finally:
        del formal_adata

    if len(candidate_targets) < 2:
        raise ValueError(f"{dataset_id} 可切分的 target 数量不足: {len(candidate_targets)}")

    rng = np.random.default_rng(split_seed)
    shuffled = list(np.asarray(candidate_targets, dtype=object)[rng.permutation(len(candidate_targets))])
    heldout_count = max(1, int(round(len(candidate_targets) * heldout_fraction)))
    heldout_count = min(heldout_count, len(candidate_targets) - 1)
    heldout_targets = tuple(sorted(str(target) for target in shuffled[:heldout_count]))
    train_targets = tuple(sorted(str(target) for target in shuffled[heldout_count:]))

    split_dir.mkdir(parents=True, exist_ok=True)
    train_path.write_text("\n".join(train_targets) + "\n", encoding="utf-8")
    heldout_path.write_text("\n".join(heldout_targets) + "\n", encoding="utf-8")
    json_dump(
        {
            "dataset_id": dataset_id,
            "split_seed": split_seed,
            "split_type": "target_level",
            "heldout_fraction": heldout_fraction,
            "candidate_target_count": len(candidate_targets),
            "train_target_count": len(train_targets),
            "heldout_target_count": len(heldout_targets),
        },
        manifest_path,
    )
    return {
        "dataset_id": dataset_id,
        "split_seed": split_seed,
        "train_targets": train_targets,
        "heldout_targets": heldout_targets,
        "manifest_path": manifest_path,
        "split_dir": split_dir,
    }


def build_inner_target_level_split_manifest(
    outer_split: dict[str, Any],
    *,
    inner_seed: int,
    inner_val_fraction: float,
) -> dict[str, Any]:
    split_dir = Path(outer_split["split_dir"]) / f"inner_seed{inner_seed}"
    inner_train_path = split_dir / "inner_train_targets.txt"
    inner_val_path = split_dir / "inner_val_targets.txt"
    manifest_path = split_dir / "inner_manifest.json"
    if inner_train_path.exists() and inner_val_path.exists():
        inner_train_targets = tuple(
            line.strip() for line in inner_train_path.read_text(encoding="utf-8").splitlines() if line.strip()
        )
        inner_val_targets = tuple(
            line.strip() for line in inner_val_path.read_text(encoding="utf-8").splitlines() if line.strip()
        )
        return {
            "inner_train_targets": inner_train_targets,
            "inner_val_targets": inner_val_targets,
            "manifest_path": manifest_path,
        }

    outer_train_targets = list(outer_split["train_targets"])
    if len(outer_train_targets) < 2:
        raise ValueError("outer_train_targets 数量不足，无法构造 inner train/val split。")
    rng = np.random.default_rng(inner_seed)
    shuffled = list(np.asarray(outer_train_targets, dtype=object)[rng.permutation(len(outer_train_targets))])
    inner_val_count = max(1, int(round(len(shuffled) * inner_val_fraction)))
    inner_val_count = min(inner_val_count, len(shuffled) - 1)
    inner_val_targets = tuple(sorted(str(target) for target in shuffled[:inner_val_count]))
    inner_train_targets = tuple(sorted(str(target) for target in shuffled[inner_val_count:]))

    split_dir.mkdir(parents=True, exist_ok=True)
    inner_train_path.write_text("\n".join(inner_train_targets) + "\n", encoding="utf-8")
    inner_val_path.write_text("\n".join(inner_val_targets) + "\n", encoding="utf-8")
    json_dump(
        {
            "dataset_id": outer_split["dataset_id"],
            "outer_split_seed": outer_split["split_seed"],
            "split_type": "target_level_inner_validation",
            "inner_seed": inner_seed,
            "inner_val_fraction": inner_val_fraction,
            "outer_train_target_count": len(outer_train_targets),
            "inner_train_target_count": len(inner_train_targets),
            "inner_val_target_count": len(inner_val_targets),
        },
        manifest_path,
    )
    return {
        "inner_train_targets": inner_train_targets,
        "inner_val_targets": inner_val_targets,
        "manifest_path": manifest_path,
    }


def main() -> None:
    args = build_parser().parse_args()
    payload = load_json(resolve_path(args.config))
    dataset_ids = [str(value) for value in ensure_list(payload.get("datasets"), "datasets")]
    split_seeds = [int(value) for value in ensure_list(payload.get("split_seeds"), "split_seeds")]
    heldout_fraction = float(payload.get("heldout_fraction", 0.2))
    inner_seed = int(payload.get("inner_seed", 11))
    inner_val_fraction = float(payload.get("inner_val_fraction", 0.2))

    for dataset_id in dataset_ids:
        for split_seed in split_seeds:
            outer_split = build_target_level_split_manifest(
                dataset_id,
                split_seed,
                heldout_fraction=heldout_fraction,
            )
            inner_split = build_inner_target_level_split_manifest(
                outer_split,
                inner_seed=inner_seed,
                inner_val_fraction=inner_val_fraction,
            )
            print(f"dataset_id={dataset_id}")
            print(f"split_seed={split_seed}")
            print(f"outer_train_targets={len(outer_split['train_targets'])}")
            print(f"outer_heldout_targets={len(outer_split['heldout_targets'])}")
            print(f"inner_train_targets={len(inner_split['inner_train_targets'])}")
            print(f"inner_val_targets={len(inner_split['inner_val_targets'])}")
            print(f"outer_manifest_path={outer_split['manifest_path']}")
            print(f"inner_manifest_path={inner_split['manifest_path']}")


if __name__ == "__main__":
    main()
