"""Build WTShiftBench resource-governance registry tables.

The registry is intentionally small and auditable. It records benchmark
contexts, endpoint hierarchy, dataset and model eligibility, metric definitions,
claim boundaries, and figure source-data files without rerunning model training
or figure generation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable


DEFAULT_CONFIG = Path("configs/resource_registry_v1.json")

TABLE_SPECS: dict[str, tuple[str, list[str]]] = {
    "dataset_eligibility_registry": (
        "dataset_eligibility_registry.tsv",
        [
            "dataset",
            "context",
            "cell_line",
            "perturbation_modality",
            "readout_day",
            "endpoint_mappability",
            "target_type",
            "benchmark_role",
            "claim_ceiling",
            "inclusion_rationale",
        ],
    ),
    "benchmark_contexts": (
        "benchmark_contexts.tsv",
        [
            "context",
            "cell_line",
            "readout_day",
            "perturbation_modality",
            "role",
            "endpoint",
            "claim_ceiling",
        ],
    ),
    "endpoint_registry": (
        "endpoint_registry.tsv",
        ["endpoint", "role", "interpretation", "forbidden_claim"],
    ),
    "temporal_compatibility_audit": (
        "temporal_compatibility_audit.tsv",
        ["context", "readout_class", "benchmark_role", "temporal_claim", "forbidden_claim"],
    ),
    "metric_definition_registry": (
        "metric_definition_registry.tsv",
        [
            "metric_name",
            "input_table",
            "output_table",
            "formula_or_definition",
            "chance_baseline",
            "claim_boundary",
        ],
    ),
    "claim_boundary_registry": (
        "claim_boundary_registry.tsv",
        ["allowed_phrase", "not_allowed"],
    ),
    "model_entrant_registry": (
        "model_entrant_registry.tsv",
        [
            "model_name",
            "model_family",
            "perturbation_type_supported",
            "input_required",
            "output_type",
            "target_coverage",
            "endpoint_compatible_output",
            "included_role",
            "reason_included",
            "reason_excluded",
            "claim_ceiling",
        ],
    ),
    "model_inclusion_exclusion_audit": (
        "model_inclusion_exclusion_audit.tsv",
        ["model_or_category", "include_now", "rationale", "claim_ceiling"],
    ),
    "model_eligibility_audits": (
        "model_eligibility_audits.tsv",
        [
            "model_name",
            "priority",
            "candidate_role",
            "required_output",
            "must_preserve_truth_object",
            "custom_metric_allowed",
            "decision_rule",
            "local_audit_result",
            "audit_evidence",
        ],
    ),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_tsv(path: Path, rows: Iterable[dict[str, object]], columns: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            missing = [column for column in columns if column not in row]
            if missing:
                raise ValueError(f"{path}: row is missing required columns {missing}: {row}")
            writer.writerow({column: row.get(column, "") for column in columns})
            row_count += 1
    return row_count


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_figure_source_data_manifest(root: Path, outdir: Path) -> int:
    columns = ["path", "figure_group", "bytes", "sha256"]
    rows: list[dict[str, object]] = []
    for source_path in sorted((root / "figures").glob("**/*_source_data.tsv")):
        rel = source_path.relative_to(root)
        parts = rel.parts
        figure_group = parts[1] if len(parts) > 1 else ""
        rows.append(
            {
                "path": str(rel),
                "figure_group": figure_group,
                "bytes": source_path.stat().st_size,
                "sha256": sha256_file(source_path),
            }
        )
    return write_tsv(outdir / "figure_source_data_manifest.tsv", rows, columns)


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def build_exclusion_future_extension_registry(outdir: Path) -> int:
    source = read_tsv(outdir / "dataset_eligibility_registry.tsv")
    rows = []
    for row in source:
        role = row.get("benchmark_role", "")
        if "excluded" in role or "future" in role or "registry_candidate" in role:
            rows.append(
                {
                    "dataset": row.get("dataset", ""),
                    "context": row.get("context", ""),
                    "perturbation_modality": row.get("perturbation_modality", ""),
                    "registry_status": role,
                    "reason": row.get("inclusion_rationale", ""),
                    "future_module_condition": row.get("claim_ceiling", ""),
                }
            )
    return write_tsv(
        outdir / "exclusion_future_extension_registry.tsv",
        rows,
        ["dataset", "context", "perturbation_modality", "registry_status", "reason", "future_module_condition"],
    )


def build_endpoint_category_grid(root: Path, outdir: Path) -> int:
    rows: list[dict[str, object]] = []
    hcc = read_tsv(root / "reports/truth_bridge_decomposition/target_level_joint_grid.tsv")
    for row in hcc:
        if row.get("cell_line") in {"HCC38", "HCC1143"}:
            rows.append(
                {
                    "context": f"{row.get('cell_line')} day 14",
                    "cell_line": row.get("cell_line", ""),
                    "target_gene": row.get("target_gene", ""),
                    "shift_percentile": row.get("shift_quantile", ""),
                    "dependency_percentile": row.get("depmap_quantile", ""),
                    "endpoint_category": row.get("joint_grid", ""),
                    "evidence_role": "primary_model_audit",
                    "category_interpretation": "operational endpoint-aligned recovery annotation; not a causal truth label or direct fitness readout",
                }
            )
    gse = read_tsv(root / "reports/gse264667_endpoint_extension/category_grid/gse264667_endpoint_category_grid.tsv")
    for row in gse:
        rows.append(
            {
                "context": row.get("context", ""),
                "cell_line": row.get("cell_line", ""),
                "target_gene": row.get("target_gene", ""),
                "shift_percentile": row.get("shift_quantile", ""),
                "dependency_percentile": row.get("depmap_quantile", ""),
                "endpoint_category": row.get("endpoint_category", row.get("joint_grid", "")),
                "evidence_role": "secondary_endpoint_extension",
                "category_interpretation": "operational endpoint-aligned recovery annotation; not primary model-audit evidence",
            }
        )
    return write_tsv(
        outdir / "endpoint_category_grid.tsv",
        rows,
        [
            "context",
            "cell_line",
            "target_gene",
            "shift_percentile",
            "dependency_percentile",
            "endpoint_category",
            "evidence_role",
            "category_interpretation",
        ],
    )


def build_model_output_contract_audit(root: Path, outdir: Path) -> int:
    registry = read_tsv(outdir / "model_entrant_registry.tsv")
    metrics = read_tsv(root / "reports/model_endpoint_recovery/source_data/model_endpoint_recovery_metrics.tsv")
    scored = {(row.get("model_id", ""), row.get("cell_line", "")) for row in metrics}
    rows = []
    for row in registry:
        name = row.get("model_name", "")
        model_id = name
        for cell_line in ["HCC38", "HCC1143"]:
            matched = any(mid.startswith(model_id) or model_id.lower() in mid.lower() for mid, cell in scored if cell == cell_line)
            rows.append(
                {
                    "model_name": name,
                    "cell_line": cell_line,
                    "included_role": row.get("included_role", ""),
                    "predicted_shift_contract": "available" if matched else "not_scored_or_reference",
                    "metadata_required": "yes",
                    "endpoint_used_for_training": "no",
                    "endpoint_used_for_selection": "no for primary claims",
                    "claim_ceiling": row.get("claim_ceiling", ""),
                }
            )
    return write_tsv(
        outdir / "model_output_contract_audit.tsv",
        rows,
        [
            "model_name",
            "cell_line",
            "included_role",
            "predicted_shift_contract",
            "metadata_required",
            "endpoint_used_for_training",
            "endpoint_used_for_selection",
            "claim_ceiling",
        ],
    )


def build_artifact_hash_manifest(root: Path, outdir: Path) -> int:
    candidates = [
        outdir / "figure_source_data_manifest.tsv",
        outdir / "observed_shift_depmap_bridge_summary.tsv",
        outdir / "gse264667_endpoint_category_grid.tsv",
        outdir / "category_response_contrast_gsea_hallmark.tsv",
        root / "reports/model_endpoint_recovery/closure_artifact_hashes.tsv",
        root / "reports/external_bridge_form_robustness/artifact_hashes.tsv",
        root / "reports/category_response_pathway/contrasts/artifact_hashes.tsv",
    ]
    rows = []
    for path in candidates:
        if path.exists():
            rel = path.relative_to(root) if path.is_relative_to(root) else path
            rows.append({"artifact": path.stem, "path": str(rel), "sha256": sha256_file(path)})
    return write_tsv(outdir / "artifact_hash_manifest.tsv", rows, ["artifact", "path", "sha256"])


def build_registry(config_path: Path, *, root: Path) -> dict[str, int]:
    config = read_json(config_path)
    outdir = root / config.get("output_dir", "resource_registry")
    outdir.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    for key, (filename, columns) in TABLE_SPECS.items():
        rows = config.get(key, [])
        counts[filename] = write_tsv(outdir / filename, rows, columns)

    counts["figure_source_data_manifest.tsv"] = build_figure_source_data_manifest(root, outdir)
    counts["exclusion_future_extension_registry.tsv"] = build_exclusion_future_extension_registry(outdir)
    counts["endpoint_category_grid.tsv"] = build_endpoint_category_grid(root, outdir)
    counts["model_output_contract_audit.tsv"] = build_model_output_contract_audit(root, outdir)
    counts["artifact_hash_manifest.tsv"] = build_artifact_hash_manifest(root, outdir)

    metadata = {
        "config": str(config_path.relative_to(root) if config_path.is_relative_to(root) else config_path),
        "output_dir": str(outdir.relative_to(root) if outdir.is_relative_to(root) else outdir),
        "tables": counts,
        "note": "Registry tables define benchmark resource governance and do not rerun model training.",
    }
    (outdir / "resource_registry_manifest.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return counts


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build WTShiftBench resource registry TSV files.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)

    root = repo_root()
    config_path = args.config if args.config.is_absolute() else root / args.config
    counts = build_registry(config_path, root=root)
    for filename, count in counts.items():
        print(f"{filename}\t{count}")


if __name__ == "__main__":
    main()
