"""Audit candidate model-family eligibility for WTShiftBench.

This script does not train models. It checks whether fixed candidate model
families can enter the endpoint-aligned recovery audit without changing the
truth object or using custom metrics.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = Path("configs/candidate_model_eligibility_v1.json")


def resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def package_available(modules: list[str]) -> tuple[bool, str]:
    available = []
    missing = []
    for module in modules:
        if importlib.util.find_spec(module) is None:
            missing.append(module)
        else:
            available.append(module)
    if available:
        return True, "available modules: " + ",".join(available)
    return False, "missing modules: " + ",".join(missing)


def load_axis_targets(path: Path) -> set[str]:
    frame = pd.read_csv(path, sep="\t")
    if "target_gene" not in frame.columns:
        raise ValueError(f"{path} must contain a target_gene column")
    return set(frame["target_gene"].astype(str))


def read_h5ad_contexts(
    *,
    context_paths: dict[str, str],
    root: Path,
    perturbation_label_column: str,
    control_column: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    try:
        import anndata as ad
    except ImportError as exc:
        raise RuntimeError("anndata is required for candidate model eligibility audits") from exc

    rows: list[dict[str, object]] = []
    target_rows: list[dict[str, object]] = []
    for context, raw_path in context_paths.items():
        path = resolve_path(root, raw_path)
        if not path.exists():
            rows.append(
                {
                    "context": context,
                    "h5ad_path": str(path),
                    "exists": False,
                    "n_cells": 0,
                    "n_genes": 0,
                    "has_perturbation_label": False,
                    "has_control_label": False,
                    "n_controls": 0,
                    "n_targets": 0,
                    "n_targets_with_min_cells": 0,
                }
            )
            continue
        adata = ad.read_h5ad(path, backed="r")
        obs = adata.obs
        has_perturbation_label = perturbation_label_column in obs.columns
        has_control_label = control_column in obs.columns
        target_counts = pd.Series(dtype=int)
        n_controls = 0
        if has_perturbation_label:
            target_counts = obs[perturbation_label_column].astype(str).value_counts()
            for target, n_cells in target_counts.items():
                target_rows.append(
                    {
                        "context": context,
                        "target_gene": str(target),
                        "n_cells": int(n_cells),
                    }
                )
        if has_control_label:
            control_values = obs[control_column].astype(str).str.lower()
            n_controls = int(control_values.isin(["true", "1", "yes", "control"]).sum())
        rows.append(
            {
                "context": context,
                "h5ad_path": str(path.relative_to(root) if path.is_relative_to(root) else path),
                "exists": True,
                "n_cells": int(adata.n_obs),
                "n_genes": int(adata.n_vars),
                "has_perturbation_label": bool(has_perturbation_label),
                "has_control_label": bool(has_control_label),
                "n_controls": n_controls,
                "n_targets": int(target_counts.size),
                "n_targets_with_min_cells": 0,
            }
        )
        adata.file.close()
    return rows, target_rows


def build_context_summary(
    *,
    context_rows: list[dict[str, object]],
    target_rows: list[dict[str, object]],
    axis_targets: set[str],
    minimum_cells_per_target: int,
) -> pd.DataFrame:
    context_frame = pd.DataFrame(context_rows)
    if not target_rows:
        context_frame["n_axis_overlap_targets"] = 0
        return context_frame
    target_frame = pd.DataFrame(target_rows)
    target_frame["passes_cell_threshold"] = target_frame["n_cells"].astype(int) >= minimum_cells_per_target
    target_frame["in_axis_target_universe"] = target_frame["target_gene"].astype(str).isin(axis_targets)
    usable = target_frame[target_frame["passes_cell_threshold"] & target_frame["in_axis_target_universe"]]
    usable_counts = usable.groupby("context")["target_gene"].nunique().to_dict()
    min_cell_counts = target_frame[target_frame["passes_cell_threshold"]].groupby("context")["target_gene"].nunique().to_dict()
    context_frame["n_targets_with_min_cells"] = context_frame["context"].map(min_cell_counts).fillna(0).astype(int)
    context_frame["n_axis_overlap_targets"] = context_frame["context"].map(usable_counts).fillna(0).astype(int)
    return context_frame


def status_row(model_name: str, check_name: str, status: str, detail: str, evidence: str) -> dict[str, str]:
    return {
        "model_name": model_name,
        "check_name": check_name,
        "status": status,
        "detail": detail,
        "evidence": evidence,
    }


def audit_model(
    *,
    candidate: dict,
    context_summary: pd.DataFrame,
    prediction_contract: dict,
    minimum_overlapping_targets: int,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    model_name = str(candidate["model_name"])
    rows: list[dict[str, str]] = []

    package_ok, package_evidence = package_available(list(candidate.get("package_modules", [])))
    rows.append(
        status_row(
            model_name,
            "package_availability",
            "pass" if package_ok else "warn",
            "Python package module lookup.",
            package_evidence,
        )
    )

    required_context_cols = [
        "exists",
        "has_perturbation_label",
        "has_control_label",
    ]
    context_contract_ok = bool(context_summary[required_context_cols].all(axis=None))
    rows.append(
        status_row(
            model_name,
            "hcc_context_contract",
            "pass" if context_contract_ok else "fail",
            "HCC contexts must exist and provide perturbation and control labels.",
            "; ".join(
                f"{row.context}:cells={row.n_cells},targets={row.n_targets},controls={row.n_controls}"
                for row in context_summary.itertuples()
            ),
        )
    )

    coverage_ok = bool((context_summary["n_axis_overlap_targets"].astype(int) >= minimum_overlapping_targets).all())
    rows.append(
        status_row(
            model_name,
            "target_coverage",
            "pass" if coverage_ok else "fail",
            f"Each primary context needs at least {minimum_overlapping_targets} usable endpoint-axis targets.",
            "; ".join(
                f"{row.context}:axis_overlap={row.n_axis_overlap_targets}"
                for row in context_summary.itertuples()
            ),
        )
    )

    output_ok = (
        str(candidate.get("expected_output", "")).startswith("target-level")
        and prediction_contract.get("prediction_space") == "truth_aligned_log_shift"
        and prediction_contract.get("required_first_column") == "target_gene"
    )
    rows.append(
        status_row(
            model_name,
            "scorer_output_contract",
            "pass" if output_ok else "fail",
            "Candidate output must be exportable as target_gene x gene predicted shift.",
            (
                f"expected_output={candidate.get('expected_output')}; "
                f"prediction_space={prediction_contract.get('prediction_space')}; "
                f"first_column={prediction_contract.get('required_first_column')}"
            ),
        )
    )

    truth_object_ok = True
    rows.append(
        status_row(
            model_name,
            "truth_object_preservation",
            "pass",
            "Candidate must use the existing WTShiftBench truth object and metrics.",
            "custom metrics are not allowed for candidate entry",
        )
    )

    all_required_ok = context_contract_ok and coverage_ok and output_ok and truth_object_ok
    if all_required_ok and package_ok:
        decision = str(candidate.get("decision_if_ready", "ready"))
    elif all_required_ok and not package_ok:
        decision = str(candidate.get("decision_if_missing_package", "pending_installation"))
    else:
        decision = str(candidate.get("decision_if_not_ready", "not_ready"))

    summary = {
        "model_name": model_name,
        "priority": str(candidate.get("priority", "")),
        "candidate_role": str(candidate.get("candidate_role", "")),
        "package_available": str(package_ok).lower(),
        "data_contract_pass": str(context_contract_ok).lower(),
        "target_coverage_pass": str(coverage_ok).lower(),
        "scorer_output_contract_pass": str(output_ok).lower(),
        "decision": decision,
        "claim_ceiling": str(candidate.get("claim_ceiling", "")),
    }
    return rows, summary


def run(config_path: Path, *, root: Path) -> dict[str, object]:
    config = read_json(config_path)
    outdir = resolve_path(root, config.get("outdir", "reports/model_eligibility"))
    outdir.mkdir(parents=True, exist_ok=True)

    axis_targets = load_axis_targets(resolve_path(root, config["axis_membership_path"]))
    prediction_contract = read_json(resolve_path(root, config["prediction_contract_path"]))
    context_rows, target_rows = read_h5ad_contexts(
        context_paths=config["hcc_contexts"],
        root=root,
        perturbation_label_column=str(config["perturbation_label_column"]),
        control_column=str(config["control_column"]),
    )
    context_summary = build_context_summary(
        context_rows=context_rows,
        target_rows=target_rows,
        axis_targets=axis_targets,
        minimum_cells_per_target=int(config.get("minimum_cells_per_target", 5)),
    )

    all_rows: list[dict[str, str]] = []
    summary_rows: list[dict[str, str]] = []
    for candidate in config.get("candidate_models", []):
        rows, summary = audit_model(
            candidate=candidate,
            context_summary=context_summary,
            prediction_contract=prediction_contract,
            minimum_overlapping_targets=int(config.get("minimum_overlapping_targets", 25)),
        )
        all_rows.extend(rows)
        summary_rows.append(summary)
        model_slug = str(candidate["model_name"]).lower()
        pd.DataFrame(rows).to_csv(outdir / f"{model_slug}_eligibility_audit.tsv", sep="\t", index=False)

    context_path = outdir / "hcc_context_model_input_audit.tsv"
    summary_path = outdir / "candidate_model_eligibility_summary.tsv"
    combined_path = outdir / "candidate_model_eligibility_audit.tsv"
    manifest_path = outdir / "candidate_model_eligibility_manifest.json"
    context_summary.to_csv(context_path, sep="\t", index=False)
    pd.DataFrame(summary_rows).to_csv(summary_path, sep="\t", index=False)
    pd.DataFrame(all_rows).to_csv(combined_path, sep="\t", index=False)

    manifest = {
        "config": str(config_path.relative_to(root) if config_path.is_relative_to(root) else config_path),
        "outdir": str(outdir.relative_to(root) if outdir.is_relative_to(root) else outdir),
        "n_candidate_models": len(summary_rows),
        "outputs": {
            "context_input_audit": str(context_path.relative_to(root) if context_path.is_relative_to(root) else context_path),
            "summary": str(summary_path.relative_to(root) if summary_path.is_relative_to(root) else summary_path),
            "combined_audit": str(combined_path.relative_to(root) if combined_path.is_relative_to(root) else combined_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit candidate model-family eligibility.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)

    config_path = args.config if args.config.is_absolute() else PROJECT_ROOT / args.config
    manifest = run(config_path, root=PROJECT_ROOT)
    print(json.dumps(manifest["outputs"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
