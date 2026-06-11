from __future__ import annotations

import argparse
import gzip
import hashlib
import shutil
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports/gse264667_endpoint_extension/category_grid"

INPUTS = (
    {
        "dataset_id": "gse264667_hepg2_day7",
        "context": "HepG2 day 7",
        "cell_line": "HepG2",
        "source_path": "reports/gse264667_endpoint_extension/gse264667_hepg2_day7/target_level_bridge_table.tsv.gz",
        "evidence_layer": "candidate_secondary_endpoint_extension",
        "claim_role": "secondary cancer-line endpoint-extension category grid",
    },
    {
        "dataset_id": "gse264667_jurkat_day7",
        "context": "Jurkat day 7",
        "cell_line": "Jurkat",
        "source_path": "reports/gse264667_endpoint_extension/gse264667_jurkat_day7/target_level_bridge_table.tsv.gz",
        "evidence_layer": "candidate_secondary_endpoint_extension",
        "claim_role": "secondary lineage-boundary endpoint-extension category grid",
    },
)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_table(path: Path) -> pd.DataFrame:
    with gzip.open(path, "rt") as handle:
        return pd.read_csv(handle, sep="\t")


def rank_quantile(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    return numeric.rank(method="average", pct=True)


def assign_category(shift_q: float, dep_q: float) -> tuple[str, str]:
    if not np.isfinite(shift_q) or not np.isfinite(dep_q):
        return "not_mapped", "not_scored"
    if shift_q >= 0.75 and dep_q >= 0.75:
        return "Q1_anchor", "high_shift_high_dependency"
    if shift_q >= 0.75 and dep_q <= 0.25:
        return "Q2_shift_excess", "high_shift_low_dependency"
    if shift_q <= 0.25 and dep_q >= 0.75:
        return "Q3_dependency_excess", "low_shift_high_dependency"
    if shift_q <= 0.25 and dep_q <= 0.25:
        return "Q4_low_information", "low_shift_low_dependency"
    return "middle", "retained_middle_band"


def build_context_grid(spec: dict[str, str]) -> pd.DataFrame:
    path = PROJECT_ROOT / spec["source_path"]
    table = read_table(path)
    scored = table.loc[table["depmap_join_status"].eq("both")].copy()
    scored["real_shift_mean_abs"] = pd.to_numeric(scored["real_shift_mean_abs"], errors="coerce")
    scored["depmap_gene_dependency"] = pd.to_numeric(scored["depmap_gene_dependency"], errors="coerce")
    scored = scored.dropna(subset=["real_shift_mean_abs", "depmap_gene_dependency"]).drop_duplicates("target_gene")
    scored["shift_quantile"] = rank_quantile(scored["real_shift_mean_abs"])
    scored["dependency_quantile"] = rank_quantile(scored["depmap_gene_dependency"])
    assigned = [assign_category(s, d) for s, d in zip(scored["shift_quantile"], scored["dependency_quantile"])]
    scored["endpoint_category"] = [a[0] for a in assigned]
    scored["category_rule"] = [a[1] for a in assigned]
    scored["shift_threshold_rule"] = "rank_quantile_25_75_within_context"
    scored["dependency_threshold_rule"] = "rank_quantile_25_75_within_context"
    scored["dependency_strength_variable"] = "depmap_gene_dependency"
    scored["evidence_layer"] = spec["evidence_layer"]
    scored["claim_role"] = spec["claim_role"]
    scored["claim_boundary"] = (
        "secondary endpoint-extension category grid; not a model-audit context and not model generalization"
    )
    keep = [
        "dataset_id",
        "context",
        "cell_line",
        "evidence_layer",
        "claim_role",
        "target_gene",
        "n_cells_target",
        "n_cells_control",
        "real_shift_mean_abs",
        "depmap_gene_dependency",
        "shift_quantile",
        "dependency_quantile",
        "endpoint_category",
        "category_rule",
        "shift_threshold_rule",
        "dependency_threshold_rule",
        "dependency_strength_variable",
        "claim_boundary",
    ]
    return scored[keep].sort_values(["context", "endpoint_category", "target_gene"]).reset_index(drop=True)


def write_manifest(output_dir: Path, paths: list[Path]) -> None:
    rows = []
    for path in paths:
        if path.exists():
            rows.append(
                {
                    "artifact": path.stem,
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "size_bytes": int(path.stat().st_size),
                    "sha256": sha256_file(path),
                }
            )
    pd.DataFrame(rows).to_csv(output_dir / "artifact_hashes.tsv", sep="\t", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build GSE264667 HepG2/Jurkat endpoint-category grids.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    grids = [build_context_grid(spec) for spec in INPUTS]
    target_grid = pd.concat(grids, ignore_index=True)
    composition = (
        target_grid.groupby(["dataset_id", "context", "cell_line", "evidence_layer", "endpoint_category"], as_index=False)
        .agg(
            n_targets=("target_gene", "nunique"),
            median_shift_quantile=("shift_quantile", "median"),
            median_dependency_quantile=("dependency_quantile", "median"),
            targets=("target_gene", lambda s: ";".join(sorted(set(s))[:200])),
        )
    )
    totals = target_grid.groupby(["dataset_id", "context"], as_index=False).agg(n_targets_context=("target_gene", "nunique"))
    composition = composition.merge(totals, on=["dataset_id", "context"], how="left")
    composition["fraction_targets"] = composition["n_targets"] / composition["n_targets_context"]
    composition["claim_boundary"] = (
        "category composition supports endpoint-object portability only; not model generalization"
    )

    paths = []
    target_path = output_dir / "gse264667_endpoint_category_grid.tsv"
    target_grid.to_csv(target_path, sep="\t", index=False)
    paths.append(target_path)
    comp_path = output_dir / "gse264667_endpoint_category_composition.tsv"
    composition.to_csv(comp_path, sep="\t", index=False)
    paths.append(comp_path)

    registry_dir = PROJECT_ROOT / "resource_registry"
    registry_dir.mkdir(parents=True, exist_ok=True)
    reg_grid = registry_dir / "gse264667_endpoint_category_grid.tsv"
    reg_comp = registry_dir / "gse264667_endpoint_category_composition.tsv"
    shutil.copy2(target_path, reg_grid)
    shutil.copy2(comp_path, reg_comp)
    paths.extend([reg_grid, reg_comp])
    write_manifest(output_dir, paths)
    print(f"gse264667 endpoint category grid outputs: {output_dir}")


if __name__ == "__main__":
    main()
