from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "configs/figure5_finite_budget_sensitivity_v1.json"
CELL_LINES = ("HCC38", "HCC1143")


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_tsv(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, sep="\t", index=False)


def run_command(command: list[str], log_path: Path, *, dry_run: bool) -> int | None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("ab") as handle:
        handle.write(("\n[" + datetime.now(timezone.utc).isoformat() + "] " + " ".join(command) + "\n").encode())
        handle.flush()
        if dry_run:
            return None
        completed = subprocess.run(command, cwd=PROJECT_ROOT, stdout=handle, stderr=subprocess.STDOUT, check=False)
        return int(completed.returncode)


def scorer_ready_path(model_id: str, cell_line: str) -> Path:
    return PROJECT_ROOT / "data/predictions/hcc_scorer_ready" / model_id / cell_line / "predicted_shift.tsv.gz"


def export_prediction(model_id: str, cell_line: str, raw_path: Path, source_kind: str, log_path: Path, *, dry_run: bool) -> int | None:
    if scorer_ready_path(model_id, cell_line).exists():
        return 0
    command = [
        "pixi",
        "run",
        "python",
        "scripts/pipeline/hcc_prediction_export.py",
        "--cell-line",
        cell_line,
        "--model-id",
        model_id,
        "--model-version",
        "finite_budget_v1",
        "--object-role",
        "entrant",
        "--input-prediction-path",
        str(raw_path.relative_to(PROJECT_ROOT)),
        "--source-kind",
        source_kind,
    ]
    return run_command(command, log_path, dry_run=dry_run)


def audit_and_hash(model_id: str, output_root: Path, *, dry_run: bool) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    audit_log = output_root / "logs" / model_id / "audit.log"
    commands = [
        [
            "pixi",
            "run",
            "python",
            "scripts/pipeline/audit_hcc_model_after_run.py",
            "--model-id",
            model_id,
        ],
        [
            "pixi",
            "run",
            "python",
            "scripts/pipeline/hash_hcc_model_artifacts.py",
            "--model-id",
            model_id,
        ],
    ]
    for command in commands:
        code = run_command(command, audit_log, dry_run=dry_run)
        rows.append({"model_id": model_id, "stage": command[3], "returncode": code, "log_path": str(audit_log.relative_to(PROJECT_ROOT))})
        if code not in (0, None):
            break
    return rows


def run_scgen(entry: dict, cfg: dict, output_root: Path, *, dry_run: bool) -> list[dict[str, object]]:
    model_id = str(entry["model_id"])
    params = dict(entry["params"])
    raw_root = resolve(cfg["raw_output_root"]) / model_id
    rows: list[dict[str, object]] = []
    for cell_line in cfg.get("cell_lines", CELL_LINES):
        raw_path = raw_root / cell_line / "predicted_shift.tsv.gz"
        log_path = output_root / "logs" / model_id / f"{cell_line}.log"
        if not raw_path.exists():
            command = [
                "pixi",
                "run",
                "--environment",
                "scgen",
                "python",
                "scripts/models/scgen/run_scgen_hcc_smoke.py",
                "--cell-line",
                cell_line,
                "--outdir",
                str(raw_root.relative_to(PROJECT_ROOT)),
                "--max-targets",
                "0",
                "--max-epochs",
                str(params["max_epochs"]),
                "--batch-size",
                str(params["batch_size"]),
                "--early-stopping-patience",
                str(params["early_stopping_patience"]),
                "--seed",
                str(params["seed"]),
            ]
            code = run_command(command, log_path, dry_run=dry_run)
        else:
            code = 0
        rows.append({"model_id": model_id, "cell_line": cell_line, "stage": "train_predict", "returncode": code, "raw_path": str(raw_path.relative_to(PROJECT_ROOT)), "log_path": str(log_path.relative_to(PROJECT_ROOT))})
        if code not in (0, None):
            return rows
        export_code = export_prediction(model_id, cell_line, raw_path, str(entry["source_kind"]), log_path, dry_run=dry_run)
        rows.append({"model_id": model_id, "cell_line": cell_line, "stage": "export", "returncode": export_code, "raw_path": str(raw_path.relative_to(PROJECT_ROOT)), "log_path": str(log_path.relative_to(PROJECT_ROOT))})
        if export_code not in (0, None):
            return rows
    rows.extend(audit_and_hash(model_id, output_root, dry_run=dry_run))
    return rows


def run_cpa(entry: dict, cfg: dict, output_root: Path, *, dry_run: bool) -> list[dict[str, object]]:
    model_id = str(entry["model_id"])
    params = dict(entry["params"])
    raw_root = resolve(cfg["raw_output_root"]) / model_id
    rows: list[dict[str, object]] = []
    for cell_line in cfg.get("cell_lines", CELL_LINES):
        raw_path = raw_root / f"predicted_shift_{cell_line}.tsv.gz"
        log_path = output_root / "logs" / model_id / f"{cell_line}.log"
        if not raw_path.exists():
            command = [
                "pixi",
                "run",
                "--environment",
                "cpa",
                "python",
                "scripts/models/cpa/run_cpa_full_materialization.py",
                "--cell-line",
                cell_line,
                "--outdir",
                str(raw_root.relative_to(PROJECT_ROOT)),
                "--max-epochs",
                str(params["max_epochs"]),
                "--early-stopping-patience",
                str(params["early_stopping_patience"]),
                "--batch-size",
                str(params["batch_size"]),
                "--n-latent",
                str(params["n_latent"]),
                "--seed",
                str(params["seed"]),
            ]
            code = run_command(command, log_path, dry_run=dry_run)
        else:
            code = 0
        rows.append({"model_id": model_id, "cell_line": cell_line, "stage": "train_predict", "returncode": code, "raw_path": str(raw_path.relative_to(PROJECT_ROOT)), "log_path": str(log_path.relative_to(PROJECT_ROOT))})
        if code not in (0, None):
            return rows
        export_code = export_prediction(model_id, cell_line, raw_path, str(entry["source_kind"]), log_path, dry_run=dry_run)
        rows.append({"model_id": model_id, "cell_line": cell_line, "stage": "export", "returncode": export_code, "raw_path": str(raw_path.relative_to(PROJECT_ROOT)), "log_path": str(log_path.relative_to(PROJECT_ROOT))})
        if export_code not in (0, None):
            return rows
    rows.extend(audit_and_hash(model_id, output_root, dry_run=dry_run))
    return rows


def run_cellot(entry: dict, cfg: dict, output_root: Path, *, dry_run: bool) -> list[dict[str, object]]:
    model_id = str(entry["model_id"])
    params = dict(entry["params"])
    staging_root = resolve(cfg["raw_output_root"]) / f"{model_id}_staging"
    raw_root = resolve(cfg["raw_output_root"]) / f"{model_id}_raw"
    rows: list[dict[str, object]] = []
    for cell_line in cfg.get("cell_lines", CELL_LINES):
        raw_path = raw_root / cell_line / "predicted_shift.tsv.gz"
        log_path = output_root / "logs" / model_id / f"{cell_line}.log"
        if not raw_path.exists():
            commands = [
                [
                    "pixi",
                    "run",
                    "python",
                    "scripts/models/cellot/prepare_cellot_hcc_smoke.py",
                    "--cell-line",
                    cell_line,
                    "--outdir",
                    str(staging_root.relative_to(PROJECT_ROOT)),
                    "--max-targets",
                    str(params["max_targets"]),
                    "--max-control-cells",
                    str(params["max_control_cells"]),
                    "--max-target-cells",
                    str(params["max_target_cells"]),
                    "--gene-space",
                    str(params["gene_space"]),
                    "--seed",
                    str(params["seed"]),
                    "--n-iters",
                    str(params["n_iters"]),
                ],
                [
                    "pixi",
                    "run",
                    "--environment",
                    "cellot",
                    "python",
                    "scripts/models/cellot/run_cellot_hcc_staged.py",
                    "--cell-line",
                    cell_line,
                    "--staging-root",
                    str(staging_root.relative_to(PROJECT_ROOT)),
                ],
                [
                    "pixi",
                    "run",
                    "--environment",
                    "cellot",
                    "python",
                    "scripts/models/cellot/export_cellot_hcc_predicted_shift.py",
                    "--cell-line",
                    cell_line,
                    "--staging-root",
                    str(staging_root.relative_to(PROJECT_ROOT)),
                    "--outdir",
                    str(raw_root.relative_to(PROJECT_ROOT)),
                ],
            ]
            code = 0
            for command in commands:
                code = run_command(command, log_path, dry_run=dry_run)
                if code not in (0, None):
                    break
        else:
            code = 0
        rows.append({"model_id": model_id, "cell_line": cell_line, "stage": "train_predict", "returncode": code, "raw_path": str(raw_path.relative_to(PROJECT_ROOT)), "log_path": str(log_path.relative_to(PROJECT_ROOT))})
        if code not in (0, None):
            return rows
        export_code = export_prediction(model_id, cell_line, raw_path, str(entry["source_kind"]), log_path, dry_run=dry_run)
        rows.append({"model_id": model_id, "cell_line": cell_line, "stage": "export", "returncode": export_code, "raw_path": str(raw_path.relative_to(PROJECT_ROOT)), "log_path": str(log_path.relative_to(PROJECT_ROOT))})
        if export_code not in (0, None):
            return rows
    rows.extend(audit_and_hash(model_id, output_root, dry_run=dry_run))
    return rows


def write_manifest_tables(cfg: dict, output_root: Path) -> None:
    rows = []
    for family, model_id in dict(cfg["formal_model_ids"]).items():
        rows.append({"model_family": family, "model_id": model_id, "run_type": "formal", "params_json": "{}"})
    for model_id in cfg.get("existing_gears_sensitivity_model_ids", []):
        rows.append({"model_family": "GEARS", "model_id": model_id, "run_type": "finite_budget_existing", "params_json": "{}"})
    for entry in cfg["sensitivity_runs"]:
        rows.append(
            {
                "model_family": entry["model_family"],
                "model_id": entry["model_id"],
                "run_type": entry["run_type"],
                "params_json": json.dumps(entry["params"], sort_keys=True),
            }
        )
    write_tsv(rows, output_root / "finite_budget_manifest.tsv")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Fig. 3f finite-budget model sensitivity jobs.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--model-family", action="append", choices=["scGen", "CPA", "CellOT"])
    parser.add_argument("--model-id", action="append")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    cfg = load_json(resolve(args.config))
    output_root = resolve(cfg["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    write_manifest_tables(cfg, output_root)
    allowed_families = set(args.model_family or [])
    allowed_ids = set(args.model_id or [])

    rows: list[dict[str, object]] = []
    runners = {"scGen": run_scgen, "CPA": run_cpa, "CellOT": run_cellot}
    for entry in cfg["sensitivity_runs"]:
        family = str(entry["model_family"])
        model_id = str(entry["model_id"])
        if allowed_families and family not in allowed_families:
            continue
        if allowed_ids and model_id not in allowed_ids:
            continue
        if family not in runners:
            continue
        started = datetime.now(timezone.utc).isoformat()
        model_rows = runners[family](entry, cfg, output_root, dry_run=args.dry_run)
        for row in model_rows:
            row["model_family"] = family
            row["started_utc"] = started
            row["finished_utc"] = datetime.now(timezone.utc).isoformat()
            row["dry_run"] = bool(args.dry_run)
        rows.extend(model_rows)
        write_tsv(rows, output_root / "finite_budget_run_log.tsv")
        if any(row.get("returncode") not in (0, None) for row in model_rows):
            break
    write_tsv(rows, output_root / "finite_budget_run_log.tsv")
    print(f"Fig. 3f finite-budget manifest: {output_root / 'finite_budget_manifest.tsv'}")
    print(f"Fig. 3f finite-budget run log: {output_root / 'finite_budget_run_log.tsv'}")


if __name__ == "__main__":
    main()
