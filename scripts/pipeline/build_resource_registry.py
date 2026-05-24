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
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", extrasaction="ignore")
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


def build_registry(config_path: Path, *, root: Path) -> dict[str, int]:
    config = read_json(config_path)
    outdir = root / config.get("output_dir", "resource_registry")
    outdir.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    for key, (filename, columns) in TABLE_SPECS.items():
        rows = config.get(key, [])
        counts[filename] = write_tsv(outdir / filename, rows, columns)

    counts["figure_source_data_manifest.tsv"] = build_figure_source_data_manifest(root, outdir)

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
