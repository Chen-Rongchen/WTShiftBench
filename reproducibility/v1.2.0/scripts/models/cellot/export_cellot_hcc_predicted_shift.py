#!/usr/bin/env python3
from __future__ import annotations

import argparse
import functools
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STAGING_ROOT = PROJECT_ROOT / "reports/model_eligibility/cellot_hcc_smoke"
DEFAULT_OUTDIR = PROJECT_ROOT / "reports/model_eligibility/cellot_hcc_predictions"


def project_relative(path: Path) -> str:
    resolved = path.resolve()
    return str(resolved.relative_to(PROJECT_ROOT)) if resolved.is_relative_to(PROJECT_ROOT) else str(resolved)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export staged CellOT HCC models to raw predicted_shift matrix.")
    parser.add_argument("--cell-line", required=True, choices=["HCC38", "HCC1143"])
    parser.add_argument("--staging-root", default=str(DEFAULT_STAGING_ROOT))
    parser.add_argument("--outdir", default=str(DEFAULT_OUTDIR))
    parser.add_argument("--cellot-source", default="/tmp/wtko_cellot_install")
    parser.add_argument("--max-targets", type=int, default=0, help="0 means all staged targets.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    cellot_source = Path(args.cellot_source)
    if not cellot_source.exists():
        raise FileNotFoundError(f"CellOT source checkout not found: {cellot_source}")
    sys.path.insert(0, str(cellot_source))

    import torch

    # CellOT checkpoints are created locally by the immediately preceding queue
    # step. Upstream CellOT calls torch.load without weights_only, which breaks
    # under PyTorch 2.6 where the default changed to True.
    torch.load = functools.partial(torch.load, weights_only=False)

    from cellot.utils.evaluate import load_conditions

    manifest_path = Path(args.staging_root) / args.cell_line / "staging_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing CellOT staging manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    staged = list(manifest.get("staged_targets", []))
    if args.max_targets > 0:
        staged = staged[: args.max_targets]

    rows: list[dict[str, object]] = []
    exported: list[dict[str, object]] = []
    for item in staged:
        target = str(item["target_gene"])
        target_dir = PROJECT_ROOT / str(item["command_path"])
        target_dir = target_dir.parent / "model-cellot"
        checkpoint = target_dir / "cache" / "model.pt"
        if not checkpoint.exists():
            raise FileNotFoundError(f"Missing trained CellOT checkpoint for {target}: {checkpoint}")
        control, _treated, imputed = load_conditions(target_dir, where="data_space", setting="iid")
        shift = imputed.to_df().mean(axis=0) - control.mean(axis=0)
        rows.append({"target_gene": target, **{str(gene): float(value) for gene, value in shift.items()}})
        exported.append(
            {
                "target_gene": target,
                "checkpoint": project_relative(checkpoint),
                "n_control_eval_cells": int(control.shape[0]),
                "n_imputed_cells": int(imputed.n_obs),
                "n_genes": int(len(shift)),
            }
        )

    outdir = Path(args.outdir) / args.cell_line
    outdir.mkdir(parents=True, exist_ok=True)
    prediction_path = outdir / "predicted_shift.tsv.gz"
    pd.DataFrame(rows).to_csv(prediction_path, sep="\t", index=False, compression="gzip")
    report = {
        "stage": "cellot_hcc_predicted_shift_export",
        "cell_line": args.cell_line,
        "prediction_path": project_relative(prediction_path),
        "n_targets": len(rows),
        "exported_targets": exported,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    report_path = outdir / "export_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"CellOT raw predicted_shift: {prediction_path}")
    print(f"CellOT export report: {report_path}")


if __name__ == "__main__":
    main()
