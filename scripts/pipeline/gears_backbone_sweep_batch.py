from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "reports/gears_backbone_sweep/candidate_manifest.tsv"
DEFAULT_REPORT_ROOT = PROJECT_ROOT / "reports/gears_backbone_sweep/batch_run"
CELL_LINES = ["HCC38", "HCC1143"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="顺序执行 GEARS backbone sweep 候选。")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH), help="候选 manifest TSV 路径。")
    parser.add_argument("--report-root", default=str(DEFAULT_REPORT_ROOT), help="批处理报告输出目录。")
    parser.add_argument("--start-rank", type=int, default=2, help="起始 candidate_rank。默认跳过与 base 等价的 rank1。")
    parser.add_argument("--end-rank", type=int, default=6, help="结束 candidate_rank。")
    parser.add_argument("--skip-existing", action="store_true", help="若原始预测已存在则跳过训练。")
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def run_command(command: list[str], *, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=PROJECT_ROOT, env=env, check=True)


def export_one_cell_line(model_id: str, cell_line: str, env: dict[str, str]) -> None:
    raw_prediction = (
        PROJECT_ROOT / "data/predictions/gears_raw" / model_id / cell_line / "predicted_shift.tsv.gz"
    )
    command = [
        env.get("PYTHON_BIN", "python"),
        "scripts/pipeline/hcc_prediction_export.py",
        "--cell-line",
        cell_line,
        "--model-id",
        model_id,
        "--model-version",
        "v1",
        "--object-role",
        "entrant",
        "--input-prediction-path",
        str(raw_prediction.relative_to(PROJECT_ROOT)),
        "--source-kind",
        "gears_hcc_backbone_sweep",
    ]
    run_command(command, env=env)


def append_status(
    rows: list[dict[str, object]],
    *,
    candidate_rank: int,
    model_id: str,
    variant_id: str,
    phase: str,
    status: str,
    message: str = "",
) -> None:
    rows.append(
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "candidate_rank": candidate_rank,
            "model_id": model_id,
            "variant_id": variant_id,
            "phase": phase,
            "status": status,
            "message": message,
        }
    )


def main() -> None:
    args = build_parser().parse_args()
    manifest_path = resolve_path(args.manifest)
    report_root = resolve_path(args.report_root)
    report_root.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["MPLCONFIGDIR"] = "/tmp/matplotlib_gears_sweep"
    env["PYTHON_BIN"] = env.get("PYTHON_BIN", "python")

    manifest = pd.read_csv(manifest_path, sep="\t")
    selected = manifest.loc[
        (manifest["candidate_rank"] >= int(args.start_rank)) & (manifest["candidate_rank"] <= int(args.end_rank))
    ].copy()

    status_rows: list[dict[str, object]] = []
    for row in selected.itertuples(index=False):
        model_id = str(row.model_id)
        variant_id = str(row.variant_id)
        config_path = resolve_path(str(row.config_path))
        candidate_rank = int(row.candidate_rank)
        raw_hcc38 = PROJECT_ROOT / "data/predictions/gears_raw" / model_id / "HCC38" / "predicted_shift.tsv.gz"
        raw_hcc1143 = PROJECT_ROOT / "data/predictions/gears_raw" / model_id / "HCC1143" / "predicted_shift.tsv.gz"
        try:
            if args.skip_existing and raw_hcc38.exists() and raw_hcc1143.exists():
                append_status(
                    status_rows,
                    candidate_rank=candidate_rank,
                    model_id=model_id,
                    variant_id=variant_id,
                    phase="train",
                    status="skipped_existing",
                    message="raw predictions already exist",
                )
            else:
                append_status(
                    status_rows,
                    candidate_rank=candidate_rank,
                    model_id=model_id,
                    variant_id=variant_id,
                    phase="train",
                    status="started",
                    message=str(config_path.relative_to(PROJECT_ROOT)),
                )
                run_command(
                    [
                        "pixi",
                        "run",
                        "--environment",
                        "gears",
                        "python",
                        "scripts/pipeline/gears_hcc_predictions.py",
                        "--config",
                        str(config_path.relative_to(PROJECT_ROOT)),
                    ],
                    env=env,
                )
                append_status(
                    status_rows,
                    candidate_rank=candidate_rank,
                    model_id=model_id,
                    variant_id=variant_id,
                    phase="train",
                    status="completed",
                )

            for cell_line in CELL_LINES:
                append_status(
                    status_rows,
                    candidate_rank=candidate_rank,
                    model_id=model_id,
                    variant_id=variant_id,
                    phase=f"export_{cell_line}",
                    status="started",
                )
                export_one_cell_line(model_id, cell_line, env)
                append_status(
                    status_rows,
                    candidate_rank=candidate_rank,
                    model_id=model_id,
                    variant_id=variant_id,
                    phase=f"export_{cell_line}",
                    status="completed",
                )

            append_status(
                status_rows,
                candidate_rank=candidate_rank,
                model_id=model_id,
                variant_id=variant_id,
                phase="smoke",
                status="started",
            )
            run_command([env["PYTHON_BIN"], "scripts/pipeline/real_hcc_smoke.py"], env=env)
            append_status(
                status_rows,
                candidate_rank=candidate_rank,
                model_id=model_id,
                variant_id=variant_id,
                phase="smoke",
                status="completed",
            )
        except subprocess.CalledProcessError as exc:
            append_status(
                status_rows,
                candidate_rank=candidate_rank,
                model_id=model_id,
                variant_id=variant_id,
                phase="error",
                status="failed",
                message=f"returncode={exc.returncode}",
            )
            pd.DataFrame(status_rows).to_csv(report_root / "batch_status.tsv", sep="\t", index=False)
            (report_root / "batch_status.json").write_text(
                json.dumps(status_rows, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            raise
        pd.DataFrame(status_rows).to_csv(report_root / "batch_status.tsv", sep="\t", index=False)
        (report_root / "batch_status.json").write_text(
            json.dumps(status_rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
