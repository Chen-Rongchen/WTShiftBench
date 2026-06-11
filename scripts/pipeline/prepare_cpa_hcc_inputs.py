"""Prepare HCC AnnData metadata for a CPA sensitivity entrant.

The script is conservative by default: it audits and writes manifests, but does
not duplicate H5AD files unless --write-h5ad is supplied.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = Path("configs/cpa_hcc_input_preparation_v1.json")


def resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def bool_series(values: pd.Series) -> pd.Series:
    return values.astype(str).str.lower().isin(["true", "1", "yes", "control"])


def prepare_context(
    *,
    context: str,
    input_path: Path,
    output_path: Path,
    config: dict,
    write_h5ad: bool,
) -> dict[str, object]:
    import anndata as ad

    adata = ad.read_h5ad(input_path)
    obs = adata.obs.copy()
    perturbation_col = str(config["perturbation_label_column"])
    control_col = str(config["control_column"])
    cpa_cols = config["cpa_obs_columns"]
    if perturbation_col not in obs.columns:
        raise ValueError(f"{input_path} missing perturbation label column: {perturbation_col}")
    if control_col not in obs.columns:
        raise ValueError(f"{input_path} missing control column: {control_col}")

    is_control = bool_series(obs[control_col])
    perturbation = obs[perturbation_col].astype(str).copy()
    perturbation.loc[is_control] = str(config.get("control_perturbation_label", "control"))

    adata.obs[str(cpa_cols["perturbation"])] = perturbation.astype(str).values
    adata.obs[str(cpa_cols["dosage"])] = str(config.get("default_dosage", "1.0"))
    adata.obs[str(cpa_cols["context"])] = context
    adata.obs[str(cpa_cols["batch"])] = context
    adata.obs[str(cpa_cols["is_control"])] = is_control.astype(bool).values
    adata.uns["wtshiftbench_cpa_input_preparation"] = {
        "source_path": str(input_path.relative_to(PROJECT_ROOT) if input_path.is_relative_to(PROJECT_ROOT) else input_path),
        "context": context,
        "perturbation_column": str(cpa_cols["perturbation"]),
        "dosage_column": str(cpa_cols["dosage"]),
        "context_column": str(cpa_cols["context"]),
        "batch_column": str(cpa_cols["batch"]),
        "write_h5ad": bool(write_h5ad),
    }

    if write_h5ad:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        adata.write_h5ad(output_path)

    target_counts = adata.obs[str(cpa_cols["perturbation"])].astype(str).value_counts()
    return {
        "context": context,
        "input_path": str(input_path.relative_to(PROJECT_ROOT) if input_path.is_relative_to(PROJECT_ROOT) else input_path),
        "output_path": str(output_path.relative_to(PROJECT_ROOT) if output_path.is_relative_to(PROJECT_ROOT) else output_path),
        "written": bool(write_h5ad),
        "n_cells": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "n_control_cells": int(is_control.sum()),
        "n_perturbation_labels": int(target_counts.size),
        "min_cells_per_label": int(target_counts.min()),
        "median_cells_per_label": float(target_counts.median()),
        "perturbation_column": str(cpa_cols["perturbation"]),
        "dosage_column": str(cpa_cols["dosage"]),
        "context_column": str(cpa_cols["context"]),
        "batch_column": str(cpa_cols["batch"]),
    }


def run(config_path: Path, *, root: Path, write_h5ad: bool) -> dict[str, object]:
    config = read_json(config_path)
    outdir = resolve_path(root, config["outdir"])
    manifest_dir = resolve_path(root, config["manifest_dir"])
    manifest_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    for context, raw_path in config["contexts"].items():
        input_path = resolve_path(root, raw_path)
        output_path = outdir / f"{context}.h5ad"
        summaries.append(
            prepare_context(
                context=context,
                input_path=input_path,
                output_path=output_path,
                config=config,
                write_h5ad=write_h5ad,
            )
        )

    summary_path = manifest_dir / "cpa_hcc_input_preparation_summary.tsv"
    manifest_path = manifest_dir / "cpa_hcc_input_preparation_manifest.json"
    pd.DataFrame(summaries).to_csv(summary_path, sep="\t", index=False)
    manifest = {
        "config": str(config_path.relative_to(root) if config_path.is_relative_to(root) else config_path),
        "write_h5ad": bool(write_h5ad),
        "n_contexts": len(summaries),
        "outputs": {
            "summary": str(summary_path.relative_to(root) if summary_path.is_relative_to(root) else summary_path),
            "h5ad_outdir": str(outdir.relative_to(root) if outdir.is_relative_to(root) else outdir),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Prepare HCC metadata for CPA input.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--write-h5ad", action="store_true", help="Materialize CPA-ready H5AD files.")
    args = parser.parse_args(argv)

    config_path = args.config if args.config.is_absolute() else PROJECT_ROOT / args.config
    manifest = run(config_path, root=PROJECT_ROOT, write_h5ad=args.write_h5ad)
    print(json.dumps(manifest["outputs"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
