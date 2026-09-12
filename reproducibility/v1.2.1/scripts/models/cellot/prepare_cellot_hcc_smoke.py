#!/usr/bin/env python3
"""Stage per-target HCC smoke inputs for official CellOT training.

CellOT trains one transport map for a source -> target condition pair. This
script does not train the model; it writes compact per-target AnnData files,
CellOT-style YAML configs, and runnable command files so GPU/CPU training can
be launched after the CPA full materialization jobs finish.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AXIS_MEMBERSHIP_PATH = (
    PROJECT_ROOT / "reports/truth_driven_bridge/master_atlas/shared_target_axis_membership.tsv"
)
DEFAULT_INPUT_ROOT = PROJECT_ROOT / "data/processed/cpa_hcc_formal"
DEFAULT_OUTDIR = PROJECT_ROOT / "reports/model_eligibility/cellot_hcc_smoke"


def project_relative(path: Path) -> str:
    resolved = path.resolve()
    return str(resolved.relative_to(PROJECT_ROOT)) if resolved.is_relative_to(PROJECT_ROOT) else str(resolved)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def axis_targets(path: Path) -> list[str]:
    frame = pd.read_csv(path, sep="\t")
    return frame["target_gene"].astype(str).drop_duplicates().sort_values().tolist()


def dense_or_sparse_copy(x):
    if sparse.issparse(x):
        return x.copy()
    return np.asarray(x).copy()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare CellOT HCC smoke staging files.")
    parser.add_argument("--cell-line", required=True, choices=["HCC38", "HCC1143"])
    parser.add_argument("--input-root", default=str(DEFAULT_INPUT_ROOT))
    parser.add_argument("--axis-membership-path", default=str(DEFAULT_AXIS_MEMBERSHIP_PATH))
    parser.add_argument("--outdir", default=str(DEFAULT_OUTDIR))
    parser.add_argument("--max-targets", type=int, default=3)
    parser.add_argument("--max-control-cells", type=int, default=512)
    parser.add_argument("--max-target-cells", type=int, default=512)
    parser.add_argument("--gene-space", choices=["axis", "full"], default="axis")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--n-iters", type=int, default=1000)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rng = np.random.default_rng(args.seed)

    input_path = Path(args.input_root) / f"{args.cell_line}.h5ad"
    adata = ad.read_h5ad(input_path)
    adata.var_names_make_unique()

    required_obs = {"cpa_perturbation"}
    missing_obs = sorted(required_obs - set(adata.obs.columns))
    if missing_obs:
        raise ValueError(f"{input_path} missing obs columns: {missing_obs}")

    target_order = axis_targets(Path(args.axis_membership_path))
    if args.gene_space == "axis":
        missing_genes = [gene for gene in target_order if gene not in set(adata.var_names.astype(str))]
        if missing_genes:
            raise ValueError(f"{args.cell_line} missing axis genes: {missing_genes}")
        gene_positions = pd.Series(np.arange(adata.n_vars), index=adata.var_names.astype(str)).loc[target_order].to_numpy()
        adata = adata[:, gene_positions].copy()
    present = set(adata.obs["cpa_perturbation"].astype(str))
    targets = [target for target in target_order if target in present]
    if args.max_targets > 0:
        targets = targets[: args.max_targets]

    control_idx = np.flatnonzero(adata.obs["cpa_perturbation"].astype(str).eq("control").to_numpy())
    if len(control_idx) == 0:
        raise ValueError(f"{args.cell_line} has no control cells.")

    outroot = Path(args.outdir) / args.cell_line
    staged: list[dict[str, object]] = []

    for target in targets:
        target_idx = np.flatnonzero(adata.obs["cpa_perturbation"].astype(str).eq(target).to_numpy())
        if len(target_idx) == 0:
            continue
        selected_control = rng.choice(control_idx, size=min(args.max_control_cells, len(control_idx)), replace=False)
        selected_target = rng.choice(target_idx, size=min(args.max_target_cells, len(target_idx)), replace=False)
        selected = np.concatenate([selected_control, selected_target])

        staged_adata = ad.AnnData(
            X=dense_or_sparse_copy(adata.X[selected]),
            obs=adata.obs.iloc[selected].copy(),
            var=adata.var.copy(),
        )
        staged_adata.obs["cellot_condition"] = np.where(
            staged_adata.obs["cpa_perturbation"].astype(str).eq("control"),
            "control",
            target,
        )
        staged_adata.obs["cellot_context"] = args.cell_line

        target_dir = outroot / target
        h5ad_path = target_dir / "input.h5ad"
        features_path = target_dir / "features.txt"
        task_config_path = target_dir / "task.yaml"
        model_config_path = target_dir / "model.yaml"
        command_path = target_dir / "run_cellot_train.sh"

        target_dir.mkdir(parents=True, exist_ok=True)
        staged_adata.write_h5ad(h5ad_path, compression="gzip")
        write_text(features_path, "\n".join(staged_adata.var_names.astype(str).tolist()) + "\n")

        write_text(
            task_config_path,
            "\n".join(
                [
                    "data:",
                    f"  path: {h5ad_path}",
                    f"  features: {features_path}",
                    "  condition: cellot_condition",
                    "  source: control",
                    f"  target: {target}",
                    "  type: cell",
                    "dataloader:",
                    "  batch_size: 256",
                    "  shuffle: true",
                    "datasplit:",
                    "  groupby: cellot_condition",
                    "  name: train_test",
                    "  test_size: 0.2",
                    "",
                ]
            ),
        )
        write_text(
            model_config_path,
            "\n".join(
                [
                    "model:",
                    "  name: cellot",
                    "  hidden_units: [64, 64, 64, 64]",
                    "  latent_dim: 50",
                    "  softplus_W_kernels: false",
                    "  kernel_init_fxn:",
                    "    b: 0.1",
                    "    name: uniform",
                    "  g:",
                    "    fnorm_penalty: 1",
                    "    kernel_init_fxn:",
                    "      b: 0.1",
                    "      name: uniform",
                    "optim:",
                    "  optimizer: Adam",
                    "  lr: 0.0001",
                    "  beta1: 0.5",
                    "  beta2: 0.9",
                    "  weight_decay: 0",
                    "training:",
                    f"  n_iters: {args.n_iters}",
                    "  n_inner_iters: 10",
                    "  cache_freq: 1000",
                    "  eval_freq: 250",
                    "  logs_freq: 50",
                    "",
                ]
            ),
        )
        write_text(
            command_path,
            "\n".join(
                [
                    "#!/usr/bin/env bash",
                    "set -euo pipefail",
                    "# Requires the CellOT source checkout installed by pixi task pip-install-cellot.",
                    "python /tmp/wtko_cellot_install/scripts/train.py \\",
                    f"  --outdir {target_dir / 'model-cellot'} \\",
                    f"  --config {task_config_path} \\",
                    f"  --config {model_config_path} \\",
                    f"  --config.data.target {target}",
                    "",
                ]
            ),
        )
        staged.append(
            {
                "cell_line": args.cell_line,
                "target_gene": target,
                "n_control_cells": int(len(selected_control)),
                "n_target_cells": int(len(selected_target)),
                "h5ad_path": project_relative(h5ad_path),
                "task_config_path": project_relative(task_config_path),
                "model_config_path": project_relative(model_config_path),
                "command_path": project_relative(command_path),
            }
        )

    manifest = {
        "stage": "cellot_hcc_smoke_staging",
        "cell_line": args.cell_line,
        "input_path": project_relative(input_path),
        "n_staged_targets": len(staged),
        "max_control_cells": args.max_control_cells,
        "max_target_cells": args.max_target_cells,
        "gene_space": args.gene_space,
        "n_genes": int(adata.n_vars),
        "n_iters": args.n_iters,
        "staged_targets": staged,
    }
    manifest_path = outroot / "staging_manifest.json"
    write_text(manifest_path, json.dumps(manifest, indent=2) + "\n")
    print(f"staged CellOT smoke inputs: {manifest_path}")


if __name__ == "__main__":
    main()
