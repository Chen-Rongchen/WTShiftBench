from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLAN = PROJECT_ROOT / "configs/hcc_model_execution_plan_v1.json"
DEFAULT_LOG = PROJECT_ROOT / "reports/model_endpoint_recovery/model_queue_run_log.tsv"


def export_pair_commands(model_id: str, raw_root: str, source_kind: str, model_version: str = "v1") -> list[str]:
    return [
        (
            "pixi run python scripts/pipeline/hcc_prediction_export.py "
            f"--cell-line HCC38 --model-id {model_id} --model-version {model_version} --object-role entrant "
            f"--input-prediction-path {raw_root}/{model_id}/HCC38/predicted_shift.tsv.gz --source-kind {source_kind}"
        ),
        (
            "pixi run python scripts/pipeline/hcc_prediction_export.py "
            f"--cell-line HCC1143 --model-id {model_id} --model-version {model_version} --object-role entrant "
            f"--input-prediction-path {raw_root}/{model_id}/HCC1143/predicted_shift.tsv.gz --source-kind {source_kind}"
        ),
    ]


def audit_hash_commands(model_id: str) -> list[str]:
    return [
        f"pixi run audit-hcc-model-after-run --model-id {model_id}",
        f"pixi run python scripts/pipeline/hash_hcc_model_artifacts.py --model-id {model_id}",
    ]


def scorer_ready_required_paths(model_id: str) -> list[str]:
    return [
        f"data/predictions/hcc_scorer_ready/{model_id}/HCC38/predicted_shift.tsv.gz",
        f"data/predictions/hcc_scorer_ready/{model_id}/HCC1143/predicted_shift.tsv.gz",
    ]


def command_plan() -> list[dict[str, object]]:
    gears_sweep = [
        "gears_hcc_formal_v1_e20_lr1e-03_wd1e-06",
        "gears_hcc_formal_v1_e30_lr5e-04_wd1e-06",
        "gears_hcc_formal_v1_e30_lr1e-03_wd1e-05",
        "gears_hcc_formal_v1_e30_lr2e-03_wd1e-06",
        "gears_hcc_formal_v1_e40_lr1e-03_wd1e-06",
    ]
    steps: list[dict[str, object]] = [
        {
            "name": "builtin_null_shared_export",
            "model_id": "builtin_controls",
            "commands": [
                "pixi run python scripts/pipeline/hcc_prediction_export.py --cell-line HCC38 --model-id null_model --model-version v1 --object-role null",
                "pixi run python scripts/pipeline/hcc_prediction_export.py --cell-line HCC1143 --model-id null_model --model-version v1 --object-role null",
                "pixi run python scripts/pipeline/hcc_prediction_export.py --cell-line HCC38 --model-id shared_mean_baseline --model-version v1 --object-role baseline",
                "pixi run python scripts/pipeline/hcc_prediction_export.py --cell-line HCC1143 --model-id shared_mean_baseline --model-version v1 --object-role baseline",
                *audit_hash_commands("null_model"),
                *audit_hash_commands("shared_mean_baseline"),
            ],
        },
        {
            "name": "gears_hcc_formal_generate",
            "model_id": "gears_hcc_formal_v1",
            "commands": [
                "pixi run --environment gears python scripts/pipeline/gears_hcc_predictions.py --config configs/gears_hcc_formal_v1.json",
                *export_pair_commands("gears_hcc_formal_v1", "data/predictions/gears_raw", "gears_generated_shift"),
                *audit_hash_commands("gears_hcc_formal_v1"),
            ],
        },
        {
            "name": "scgpt_hcc_formal_generate",
            "model_id": "scgpt_hcc_formal_v1",
            "required_paths": [
                "models/pretrained/scgpt_human/vocab.json",
                "models/pretrained/scgpt_human/best_model.pt",
            ],
            "fallback_required_paths": scorer_ready_required_paths("scgpt_hcc_formal_v1"),
            "fallback_commands": audit_hash_commands("scgpt_hcc_formal_v1"),
            "commands": [
                "pixi run --environment scgpt python scripts/pipeline/scgpt_hcc_predictions.py --config configs/scgpt_hcc_formal_v1.json",
                *export_pair_commands("scgpt_hcc_formal_v1", "data/predictions/scgpt_raw", "scgpt_embedding_kernel_shift"),
                *audit_hash_commands("scgpt_hcc_formal_v1"),
            ],
        },
        {
            "name": "geneformer_hcc_formal_generate",
            "model_id": "geneformer_hcc_formal_v1",
            "required_paths": [
                "models/pretrained/geneformer_gf_12l_95m_i4096",
            ],
            "fallback_required_paths": scorer_ready_required_paths("geneformer_hcc_formal_v1"),
            "fallback_commands": audit_hash_commands("geneformer_hcc_formal_v1"),
            "commands": [
                "pixi run --environment geneformer python scripts/pipeline/geneformer_hcc_predictions.py --config configs/geneformer_hcc_formal_v1.json",
                *export_pair_commands("geneformer_hcc_formal_v1", "data/predictions/geneformer_raw", "geneformer_embedding_kernel_shift"),
                *audit_hash_commands("geneformer_hcc_formal_v1"),
            ],
        },
        {
            "name": "lm_train_lowrank_hcc_generate",
            "model_id": "lm_train_lowrank_hcc_formal_v1",
            "commands": [
                "pixi run python scripts/pipeline/lm_train_lowrank_hcc_predictions.py --config configs/lm_train_lowrank_hcc_formal_v1.json",
                *export_pair_commands("lm_train_lowrank_hcc_formal_v1", "data/predictions/lm_train_lowrank_raw", "linear_lowrank_shift"),
                *audit_hash_commands("lm_train_lowrank_hcc_formal_v1"),
            ],
        },
        {
            "name": "lm_g_scgpt_ridge_hcc_generate",
            "model_id": "lm_g_scgpt_ridge_hcc_formal_v1",
            "required_paths": [
                "models/pretrained/scgpt_human/vocab.json",
                "models/pretrained/scgpt_human/best_model.pt",
            ],
            "fallback_required_paths": scorer_ready_required_paths("lm_g_scgpt_ridge_hcc_formal_v1"),
            "fallback_commands": audit_hash_commands("lm_g_scgpt_ridge_hcc_formal_v1"),
            "commands": [
                "pixi run --environment scgpt python scripts/pipeline/lm_g_scgpt_ridge_hcc_predictions.py --config configs/lm_g_scgpt_ridge_hcc_formal_v1.json",
                *export_pair_commands("lm_g_scgpt_ridge_hcc_formal_v1", "data/predictions/lm_g_scgpt_ridge_raw", "linear_ridge_scgpt_embedding_shift"),
                *audit_hash_commands("lm_g_scgpt_ridge_hcc_formal_v1"),
            ],
        },
        {
            "name": "lm_g_geneformer_ridge_hcc_generate",
            "model_id": "lm_g_geneformer_ridge_hcc_formal_v1",
            "required_paths": [
                "models/pretrained/geneformer_gf_12l_95m_i4096",
            ],
            "fallback_required_paths": scorer_ready_required_paths("lm_g_geneformer_ridge_hcc_formal_v1"),
            "fallback_commands": audit_hash_commands("lm_g_geneformer_ridge_hcc_formal_v1"),
            "commands": [
                "pixi run --environment geneformer python scripts/pipeline/lm_g_geneformer_ridge_hcc_predictions.py --config configs/lm_g_geneformer_ridge_hcc_formal_v1.json",
                *export_pair_commands("lm_g_geneformer_ridge_hcc_formal_v1", "data/predictions/lm_g_geneformer_ridge_raw", "linear_ridge_geneformer_embedding_shift"),
                *audit_hash_commands("lm_g_geneformer_ridge_hcc_formal_v1"),
            ],
        },
        {
            "name": "cpa_hcc38_train",
            "model_id": "cpa_v0.8.8",
            "commands": [
                "pixi run --environment cpa python scripts/models/cpa/run_cpa_full_materialization.py --cell-line HCC38 --max-epochs 400 --early-stopping-patience 15 --seed 1"
            ],
        },
        {
            "name": "cpa_hcc1143_train",
            "model_id": "cpa_v0.8.8",
            "commands": [
                "pixi run --environment cpa python scripts/models/cpa/run_cpa_full_materialization.py --cell-line HCC1143 --max-epochs 400 --early-stopping-patience 15 --seed 1"
            ],
        },
        {
            "name": "cpa_export_audit",
            "model_id": "cpa_v0.8.8",
            "commands": [
                "pixi run export-cpa-hcc38-full",
                "pixi run export-cpa-hcc1143-full",
                *audit_hash_commands("cpa_v0.8.8"),
            ],
        },
        {
            "name": "scgen_hcc38_full",
            "model_id": "scgen_hcc_formal_v1",
            "commands": [
                "pixi run --environment scgen python scripts/models/scgen/run_scgen_hcc_smoke.py --cell-line HCC38 --max-targets 0 --max-epochs 100"
            ],
        },
        {
            "name": "scgen_hcc1143_full",
            "model_id": "scgen_hcc_formal_v1",
            "commands": [
                "pixi run --environment scgen python scripts/models/scgen/run_scgen_hcc_smoke.py --cell-line HCC1143 --max-targets 0 --max-epochs 100"
            ],
        },
        {
            "name": "scgen_export_audit",
            "model_id": "scgen_hcc_formal_v1",
            "commands": [
                "pixi run export-scgen-hcc38-full",
                "pixi run export-scgen-hcc1143-full",
                *audit_hash_commands("scgen_hcc_formal_v1"),
            ],
        },
        {
            "name": "cellot_hcc38_stage_train_export",
            "model_id": "cellot_hcc_formal_v1",
            "commands": [
                "pixi run prepare-cellot-hcc38-full",
                "pixi run --environment cellot python scripts/models/cellot/run_cellot_hcc_staged.py --cell-line HCC38",
                "pixi run --environment cellot python scripts/models/cellot/export_cellot_hcc_predicted_shift.py --cell-line HCC38",
            ],
        },
        {
            "name": "cellot_hcc1143_stage_train_export",
            "model_id": "cellot_hcc_formal_v1",
            "commands": [
                "pixi run prepare-cellot-hcc1143-full",
                "pixi run --environment cellot python scripts/models/cellot/run_cellot_hcc_staged.py --cell-line HCC1143",
                "pixi run --environment cellot python scripts/models/cellot/export_cellot_hcc_predicted_shift.py --cell-line HCC1143",
            ],
        },
        {
            "name": "cellot_export_contract_audit",
            "model_id": "cellot_hcc_formal_v1",
            "commands": [
                "pixi run export-cellot-hcc38-full",
                "pixi run export-cellot-hcc1143-full",
                *audit_hash_commands("cellot_hcc_formal_v1"),
            ],
        },
    ]
    for model_id in gears_sweep:
        steps.append(
            {
                "name": f"{model_id}_generate",
                "model_id": model_id,
                "commands": [
                    f"pixi run --environment gears python scripts/pipeline/gears_hcc_predictions.py --config configs/generated/gears_hcc_backbone_sweep_v1/{model_id.replace('gears_hcc_formal_v1_', '')}.json",
                    *export_pair_commands(model_id, "data/predictions/gears_raw", "gears_generated_shift"),
                    *audit_hash_commands(model_id),
                ],
            }
        )
    steps.append(
        {
            "name": "final_all_model_endpoint_recovery",
            "model_id": "all_models",
            "commands": [
                "pixi run run-model-endpoint-recovery",
                "pixi run python scripts/pipeline/hash_hcc_model_artifacts.py --model-id null_model",
                "pixi run python scripts/pipeline/hash_hcc_model_artifacts.py --model-id shared_mean_baseline",
            ],
        }
    )
    return steps


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the HCC model queue sequentially with audit after each model.")
    parser.add_argument("--from-step", default=None, help="Start at this step name.")
    parser.add_argument("--only-step", action="append", help="Run only named step(s). Repeatable.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--log-path", default=str(DEFAULT_LOG))
    return parser


def selected_steps(steps: list[dict[str, object]], from_step: str | None, only_step: list[str] | None) -> list[dict[str, object]]:
    if only_step:
        allowed = set(only_step)
        return [step for step in steps if step["name"] in allowed]
    if from_step is None:
        return steps
    names = [str(step["name"]) for step in steps]
    if from_step not in names:
        raise ValueError(f"Unknown --from-step {from_step}. Available: {', '.join(names)}")
    return steps[names.index(from_step) :]


def main() -> None:
    args = build_parser().parse_args()
    steps = selected_steps(command_plan(), args.from_step, args.only_step)
    log_rows: list[dict[str, object]] = []
    for step in steps:
        missing_required = [
            str(PROJECT_ROOT / str(path))
            for path in step.get("required_paths", [])
            if not (PROJECT_ROOT / str(path)).exists()
        ]
        if missing_required:
            missing_fallback = [
                str(PROJECT_ROOT / str(path))
                for path in step.get("fallback_required_paths", [])
                if not (PROJECT_ROOT / str(path)).exists()
            ]
            row = {
                "step_name": step["name"],
                "model_id": step["model_id"],
                "command": "",
                "dry_run": bool(args.dry_run),
                "started_utc": datetime.now(timezone.utc).isoformat(),
                "returncode": None,
                "status": "blocked_missing_required_artifact",
                "missing_required": ";".join(missing_required),
            }
            if step.get("fallback_commands") and not missing_fallback:
                row["status"] = "reusing_existing_outputs_missing_required_artifact"
                print(
                    f"[queue] {step['name']}: missing required artifact(s), reusing existing scorer-ready outputs: {row['missing_required']}",
                    flush=True,
                )
                log_rows.append(row)
                for command in step["fallback_commands"]:
                    fallback_row = {
                        "step_name": step["name"],
                        "model_id": step["model_id"],
                        "command": command,
                        "dry_run": bool(args.dry_run),
                        "started_utc": datetime.now(timezone.utc).isoformat(),
                        "missing_required": row["missing_required"],
                    }
                    print(f"[queue] {step['name']}: {command}", flush=True)
                    if args.dry_run:
                        fallback_row["returncode"] = None
                        fallback_row["status"] = "dry_run_reuse_existing_outputs"
                    else:
                        completed = subprocess.run(shlex.split(str(command)), cwd=PROJECT_ROOT, check=False)
                        fallback_row["returncode"] = int(completed.returncode)
                        fallback_row["status"] = "completed_reuse_existing_outputs" if completed.returncode == 0 else "failed"
                        if completed.returncode != 0:
                            log_rows.append(fallback_row)
                            break
                    log_rows.append(fallback_row)
                if log_rows and log_rows[-1].get("status") == "failed":
                    break
                continue
            if missing_fallback:
                row["missing_fallback"] = ";".join(missing_fallback)
            print(f"[queue] {step['name']}: blocked, missing required artifact(s): {row['missing_required']}", flush=True)
            log_rows.append(row)
            continue
        for command in step["commands"]:
            row = {
                "step_name": step["name"],
                "model_id": step["model_id"],
                "command": command,
                "dry_run": bool(args.dry_run),
                "started_utc": datetime.now(timezone.utc).isoformat(),
            }
            print(f"[queue] {step['name']}: {command}", flush=True)
            if args.dry_run:
                row["returncode"] = None
                row["status"] = "dry_run"
            else:
                completed = subprocess.run(shlex.split(str(command)), cwd=PROJECT_ROOT, check=False)
                row["returncode"] = int(completed.returncode)
                row["status"] = "completed" if completed.returncode == 0 else "failed"
                if completed.returncode != 0:
                    log_rows.append(row)
                    break
            log_rows.append(row)
        if log_rows and log_rows[-1].get("status") == "failed":
            break
    log_path = Path(args.log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    import pandas as pd

    pd.DataFrame(log_rows).to_csv(log_path, sep="\t", index=False)
    print(json.dumps({"log_path": str(log_path), "n_commands": len(log_rows)}, indent=2))
    if log_rows and log_rows[-1].get("status") == "failed":
        raise SystemExit(f"Queue stopped at failed step {log_rows[-1]['step_name']}")


if __name__ == "__main__":
    main()
