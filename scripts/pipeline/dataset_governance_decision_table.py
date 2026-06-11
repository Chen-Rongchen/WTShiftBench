from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports/resource_governance_strengthening"
EVIDENCE_LAYERS = PROJECT_ROOT / "reports/external_bridge_form_robustness/dataset_evidence_layers.tsv"
BRIDGE_SUMMARY = PROJECT_ROOT / "reports/external_bridge_form_robustness/observed_shift_depmap_bridge_summary.tsv"
CANDIDATE_ELIGIBILITY = PROJECT_ROOT / "reports/external_bridge_form_robustness/candidate_endpoint_extension_eligibility.tsv"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decision_for(row: pd.Series) -> tuple[str, str, str, str]:
    layer = row["evidence_layer"]
    status = row["current_status"]
    if layer == "primary_model_audit":
        return (
            "include_primary_model_audit",
            "formal endpoint-recovery model audit",
            "primary bridge and model-audit claim",
            "do not expand into broad model-generalization language",
        )
    if layer == "external_bridge_form_boundary":
        return (
            "include_external_bridge_boundary",
            "observed bridge-form / temporal / modality / scale boundary",
            "recovery-object external validity and boundary evidence",
            "do not use as model-generalization evidence",
        )
    if layer == "candidate_secondary_endpoint_extension" and status == "bridge_form_summary_completed":
        return (
            "include_secondary_endpoint_extension",
            "secondary endpoint-object portability evidence",
            "additional cancer-line or lineage bridge-form evidence",
            "do not use as primary model-audit evidence without same output contract",
        )
    if layer == "candidate_secondary_endpoint_extension":
        return (
            "registry_candidate",
            "candidate secondary endpoint-extension",
            "eligibility governance only",
            "complete single-target/control/DepMap mapping audit before endpoint claims",
        )
    if layer == "narrow_pathway_boundary_candidate":
        return (
            "registry_pathway_boundary_candidate",
            "narrow stress/pathway boundary candidate",
            "future stress-axis interpretability module",
            "do not use as broad endpoint-recovery or model-generalization evidence",
        )
    return (
        "excluded_or_future_extension",
        "excluded/future module",
        "governance and scope definition",
        "requires a separate endpoint module before inclusion",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build dataset eligibility and evidence-layer decision table.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    layers = pd.read_csv(EVIDENCE_LAYERS, sep="\t")
    bridge = pd.read_csv(BRIDGE_SUMMARY, sep="\t")
    bridge_cols = [
        "dataset_id",
        "context",
        "n_targets_matched_depmap",
        "spearman_rho",
        "spearman_bootstrap_ci_low",
        "spearman_bootstrap_ci_high",
        "spearman_permutation_pvalue",
        "status",
    ]
    table = layers.merge(bridge[bridge_cols], on=["dataset_id", "context"], how="left", suffixes=("", "_bridge"))
    if CANDIDATE_ELIGIBILITY.exists():
        elig = pd.read_csv(CANDIDATE_ELIGIBILITY, sep="\t")
        elig_cols = [
            "dataset_id",
            "context",
            "source_exists",
            "n_obs",
            "n_vars",
            "n_gene_labels_ge_50_cells",
            "n_control_cells_non_targeting",
        ]
        table = table.merge(elig[elig_cols], on=["dataset_id", "context"], how="left")
    decisions = table.apply(decision_for, axis=1, result_type="expand")
    decisions.columns = ["decision", "resource_role", "supported_claim", "not_used_to_claim"]
    table = pd.concat([table, decisions], axis=1)
    table["claim_boundary_frozen"] = True
    table["manuscript_layer_label"] = table["evidence_layer"].map(
        {
            "primary_model_audit": "Primary model-audit layer",
            "external_bridge_form_boundary": "External bridge-form / boundary layer",
            "candidate_secondary_endpoint_extension": "Secondary endpoint-extension / candidate layer",
            "narrow_pathway_boundary_candidate": "Narrow pathway-boundary candidate layer",
            "excluded_future_registry": "Excluded / future-extension registry",
        }
    )
    table = table.sort_values(["decision", "dataset_id", "context"]).reset_index(drop=True)

    out_path = output_dir / "dataset_governance_decision_table.tsv"
    table.to_csv(out_path, sep="\t", index=False)
    registry_copy = PROJECT_ROOT / "resource_registry/dataset_governance_decision_table.tsv"
    registry_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_path, registry_copy)
    manifest = pd.DataFrame(
        [
            {
                "artifact": out_path.stem,
                "path": str(out_path.relative_to(PROJECT_ROOT)),
                "size_bytes": int(out_path.stat().st_size),
                "sha256": sha256_file(out_path),
            },
            {
                "artifact": registry_copy.stem,
                "path": str(registry_copy.relative_to(PROJECT_ROOT)),
                "size_bytes": int(registry_copy.stat().st_size),
                "sha256": sha256_file(registry_copy),
            },
        ]
    )
    manifest.to_csv(output_dir / "artifact_hashes.tsv", sep="\t", index=False)
    print(f"dataset governance decision table outputs: {output_dir}")


if __name__ == "__main__":
    main()
