#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STAGING_ROOT = PROJECT_ROOT / "reports/model_eligibility/cellot_hcc_smoke"


def project_relative(path: Path) -> str:
    resolved = path.resolve()
    return str(resolved.relative_to(PROJECT_ROOT)) if resolved.is_relative_to(PROJECT_ROOT) else str(resolved)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run staged CellOT HCC per-target training jobs sequentially.")
    parser.add_argument("--cell-line", required=True, choices=["HCC38", "HCC1143"])
    parser.add_argument("--staging-root", default=str(DEFAULT_STAGING_ROOT))
    parser.add_argument("--max-targets", type=int, default=0, help="0 means all staged targets.")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def checkpoint_path_for_command(command_path: Path) -> Path:
    return command_path.parent / "model-cellot" / "cache" / "model.pt"


def write_run_report(rows: list[dict[str, object]], run_report: Path) -> None:
    run_report.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(run_report, sep="\t", index=False)


def main() -> None:
    args = build_parser().parse_args()
    manifest_path = Path(args.staging_root) / args.cell_line / "staging_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing CellOT staging manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    staged = list(manifest.get("staged_targets", []))
    if args.max_targets > 0:
        staged = staged[: args.max_targets]
    rows: list[dict[str, object]] = []
    run_report = Path(args.staging_root) / args.cell_line / "cellot_train_run_report.tsv"
    for item in staged:
        target = str(item["target_gene"])
        command_path = PROJECT_ROOT / str(item["command_path"])
        if not command_path.exists():
            raise FileNotFoundError(f"Missing CellOT command for {target}: {command_path}")
        command = ["bash", str(command_path)]
        checkpoint_path = checkpoint_path_for_command(command_path)
        log_path = command_path.parent / "cellot_train.log"
        row = {
            "cell_line": args.cell_line,
            "target_gene": target,
            "command_path": project_relative(command_path),
            "checkpoint_path": project_relative(checkpoint_path),
            "log_path": project_relative(log_path),
            "dry_run": bool(args.dry_run),
            "started_utc": datetime.now(timezone.utc).isoformat(),
        }
        if args.dry_run:
            row["returncode"] = None
            row["status"] = "dry_run"
        elif checkpoint_path.exists():
            row["returncode"] = 0
            row["status"] = "skipped_existing_model"
        else:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("ab") as log_handle:
                header = (
                    f"\n[{datetime.now(timezone.utc).isoformat()}] "
                    f"Running {' '.join(command)}\n"
                )
                log_handle.write(header.encode("utf-8"))
                log_handle.flush()
                completed = subprocess.run(
                    command,
                    cwd=PROJECT_ROOT,
                    check=False,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                )
            row["returncode"] = int(completed.returncode)
            row["status"] = "completed" if completed.returncode == 0 else "failed"
            if completed.returncode != 0:
                rows.append(row)
                write_run_report(rows, run_report)
                break
        rows.append(row)
        write_run_report(rows, run_report)
    print(f"CellOT run report: {run_report}")
    failures = [row for row in rows if row.get("status") == "failed"]
    if failures:
        raise SystemExit(f"CellOT training failed at target {failures[0]['target_gene']}")


if __name__ == "__main__":
    main()
