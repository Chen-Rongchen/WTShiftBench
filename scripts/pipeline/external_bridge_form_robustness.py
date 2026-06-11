from __future__ import annotations

import argparse
import gzip
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports/external_bridge_form_robustness"

BRIDGE_TABLES = (
    {
        "dataset_id": "gse241115_hcc38_hcc1143",
        "context": "HCC38 day 14",
        "cell_line": "HCC38",
        "evidence_layer": "primary_model_audit",
        "source_path": "data/processed/truth_driven_bridge/HCC38/target_level_bridge_table.tsv.gz",
        "claim_role": "primary endpoint-recovery context",
    },
    {
        "dataset_id": "gse241115_hcc38_hcc1143",
        "context": "HCC1143 day 14",
        "cell_line": "HCC1143",
        "evidence_layer": "primary_model_audit",
        "source_path": "data/processed/truth_driven_bridge/HCC1143/target_level_bridge_table.tsv.gz",
        "claim_role": "primary endpoint-recovery context",
    },
    {
        "dataset_id": "gse90063_dixit_k562_temporal",
        "context": "K562 TF day 7",
        "cell_line": "K562",
        "evidence_layer": "external_bridge_form_boundary",
        "source_path": "data/processed/truth_driven_bridge_gse90063_7d/combined_target_level_bridge_table.tsv.gz",
        "claim_role": "temporal-boundary evidence",
    },
    {
        "dataset_id": "gse90063_dixit_k562_temporal",
        "context": "K562 TF day 13",
        "cell_line": "K562",
        "evidence_layer": "external_bridge_form_boundary",
        "source_path": "data/processed/truth_driven_bridge_gse90063_13d/combined_target_level_bridge_table.tsv.gz",
        "claim_role": "temporal-boundary evidence",
    },
    {
        "dataset_id": "replogle_k562_essential_day6",
        "context": "K562 essential CRISPRi day 6",
        "cell_line": "K562",
        "evidence_layer": "external_bridge_form_boundary",
        "source_path": "data/processed/truth_driven_bridge_replogle_k562_essential_day7/combined_target_level_bridge_table.tsv.gz",
        "claim_role": "large-scale CRISPRi bridge-form evidence",
    },
    {
        "dataset_id": "replogle_k562_gwps_day8",
        "context": "K562 genome-scale CRISPRi day 8",
        "cell_line": "K562",
        "evidence_layer": "external_bridge_form_boundary",
        "source_path": "data/processed/truth_driven_bridge_replogle_k562_gwps_day8/combined_target_level_bridge_table.tsv.gz",
        "claim_role": "large-scale CRISPRi scale-boundary evidence",
    },
    {
        "dataset_id": "gse264667_hepg2_day7",
        "context": "HepG2 day 7",
        "cell_line": "HepG2",
        "evidence_layer": "candidate_secondary_endpoint_extension",
        "source_path": "reports/gse264667_endpoint_extension/gse264667_hepg2_day7/target_level_bridge_table.tsv.gz",
        "claim_role": "secondary cancer-line endpoint-extension evidence",
    },
    {
        "dataset_id": "gse264667_jurkat_day7",
        "context": "Jurkat day 7",
        "cell_line": "Jurkat",
        "evidence_layer": "candidate_secondary_endpoint_extension",
        "source_path": "reports/gse264667_endpoint_extension/gse264667_jurkat_day7/target_level_bridge_table.tsv.gz",
        "claim_role": "secondary lineage-boundary endpoint-extension evidence",
    },
)

CANDIDATE_DATASETS = (
    {
        "dataset_id": "gse264667_hepg2_day7",
        "context": "HepG2 day 7",
        "cell_line": "HepG2",
        "evidence_layer": "candidate_secondary_endpoint_extension",
        "source_path": "data/raw/gse264667/series/GSE264667_hepg2_raw_singlecell_01.h5ad",
        "claim_role": "candidate cancer-line endpoint-extension pending target mapping",
    },
    {
        "dataset_id": "gse264667_jurkat_day7",
        "context": "Jurkat day 7",
        "cell_line": "Jurkat",
        "evidence_layer": "candidate_secondary_endpoint_extension",
        "source_path": "data/raw/gse264667/series/GSE264667_jurkat_raw_singlecell_01.h5ad",
        "claim_role": "candidate lineage-boundary endpoint-extension pending target mapping",
    },
)

REGISTRY_ONLY_DATASETS = (
    {
        "dataset_id": "gse200201_molm13_mswi_snf",
        "context": "MOLM13 mSWI/SNF Perturb-seq",
        "evidence_layer": "candidate_secondary_endpoint_extension",
        "current_status": "registry_candidate_pending_single_target_and_combinatorial_audit",
        "claim_boundary": "candidate hematologic cancer endpoint-extension only if single-target mapping is sufficient",
    },
    {
        "dataset_id": "gse90546_adamson_k562_upr",
        "context": "Adamson K562 UPR Perturb-seq",
        "evidence_layer": "narrow_pathway_boundary_candidate",
        "current_status": "registry_candidate_pending_pathway_boundary_audit",
        "claim_boundary": "stress-axis/pathway-boundary candidate; not primary endpoint recovery or model generalization",
    },
    {
        "dataset_id": "replogle_rpe1_essential_day7",
        "context": "RPE1 essential CRISPRi day 7",
        "evidence_layer": "excluded_future_registry",
        "current_status": "excluded_non_cancer_boundary",
        "claim_boundary": "non-cancer context; not a baseline cancer-dependency endpoint analysis",
    },
    {
        "dataset_id": "norman_k562_crispra",
        "context": "Norman K562 CRISPRa",
        "evidence_layer": "excluded_future_registry",
        "current_status": "excluded_gain_of_function_direction_mismatch",
        "claim_boundary": "activation perturbation does not match loss-of-function DepMap dependency endpoint",
    },
    {
        "dataset_id": "gasperini_k562_enhancer_crispri",
        "context": "Gasperini K562 enhancer CRISPRi",
        "evidence_layer": "excluded_future_registry",
        "current_status": "future_regulatory_extension",
        "claim_boundary": "regulatory-element perturbation is not direct gene-level DepMap dependency mapping",
    },
    {
        "dataset_id": "thp1_stimulated_perturbseq",
        "context": "THP-1 stimulated Perturb-seq",
        "evidence_layer": "excluded_future_registry",
        "current_status": "excluded_stimulus_confounded_boundary",
        "claim_boundary": "stimulus context changes baseline dependency endpoint interpretation",
    },
    {
        "dataset_id": "frangieh_melanoma_til_perturb_citeseq",
        "context": "Frangieh melanoma/TIL Perturb-CITE-seq",
        "evidence_layer": "excluded_future_registry",
        "current_status": "future_non_depmap_immune_endpoint_extension",
        "claim_boundary": "immune co-culture endpoint is not baseline DepMap dependency",
    },
)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_bridge(path: Path) -> pd.DataFrame:
    with gzip.open(path, "rt") as handle:
        return pd.read_csv(handle, sep="\t")


def empirical_p(observed: float, null: np.ndarray) -> float:
    if not np.isfinite(observed) or null.size == 0:
        return np.nan
    return (float(np.sum(np.abs(null) >= abs(observed))) + 1.0) / (float(null.size) + 1.0)


def bootstrap_ci(x: np.ndarray, y: np.ndarray, method: str, rng: np.random.Generator, n_bootstrap: int) -> tuple[float, float]:
    if len(x) < 4:
        return np.nan, np.nan
    values = []
    n = len(x)
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        xb = x[idx]
        yb = y[idx]
        if np.unique(xb).size < 2 or np.unique(yb).size < 2:
            continue
        if method == "spearman":
            values.append(stats.spearmanr(xb, yb).statistic)
        else:
            values.append(stats.pearsonr(xb, yb).statistic)
    if not values:
        return np.nan, np.nan
    return tuple(np.quantile(values, [0.025, 0.975]))


def summarize_bridge(spec: dict[str, str], n_perm: int, n_bootstrap: int, seed: int) -> dict[str, object]:
    path = PROJECT_ROOT / spec["source_path"]
    df = read_bridge(path)
    data = df.loc[df["depmap_join_status"].eq("both"), ["target_gene", "real_shift_mean_abs", "depmap_gene_dependency"]].copy()
    data["real_shift_mean_abs"] = pd.to_numeric(data["real_shift_mean_abs"], errors="coerce")
    data["depmap_gene_dependency"] = pd.to_numeric(data["depmap_gene_dependency"], errors="coerce")
    data = data.dropna().drop_duplicates("target_gene")
    x = data["real_shift_mean_abs"].to_numpy(float)
    y = data["depmap_gene_dependency"].to_numpy(float)
    rng = np.random.default_rng(seed)

    if len(data) >= 3 and np.unique(x).size > 1 and np.unique(y).size > 1:
        spearman = float(stats.spearmanr(x, y).statistic)
        pearson = float(stats.pearsonr(x, y).statistic)
        null_s = np.empty(n_perm, dtype=float)
        null_p = np.empty(n_perm, dtype=float)
        for i in range(n_perm):
            yp = rng.permutation(y)
            null_s[i] = stats.spearmanr(x, yp).statistic
            null_p[i] = stats.pearsonr(x, yp).statistic
        spearman_ci = bootstrap_ci(x, y, "spearman", rng, n_bootstrap)
        pearson_ci = bootstrap_ci(x, y, "pearson", rng, n_bootstrap)
        status = "estimated"
    else:
        spearman = pearson = np.nan
        null_s = null_p = np.array([], dtype=float)
        spearman_ci = pearson_ci = (np.nan, np.nan)
        status = "not_estimable"

    return {
        **{k: spec[k] for k in ("dataset_id", "context", "cell_line", "evidence_layer", "claim_role")},
        "source_path": spec["source_path"],
        "source_sha256": sha256_file(path),
        "n_targets_total": int(df["target_gene"].nunique()),
        "n_targets_matched_depmap": int(len(data)),
        "dependency_strength_variable": "depmap_gene_dependency",
        "shift_metric": "real_shift_mean_abs",
        "spearman_rho": spearman,
        "spearman_permutation_pvalue": empirical_p(spearman, null_s),
        "spearman_bootstrap_ci_low": spearman_ci[0],
        "spearman_bootstrap_ci_high": spearman_ci[1],
        "pearson_r": pearson,
        "pearson_permutation_pvalue": empirical_p(pearson, null_p),
        "pearson_bootstrap_ci_low": pearson_ci[0],
        "pearson_bootstrap_ci_high": pearson_ci[1],
        "n_permutations": n_perm,
        "n_bootstrap": n_bootstrap,
        "status": status,
        "supported_claim": "bridge-form detectability or boundary evidence; not model generalization",
    }


def audit_candidate_h5ad(spec: dict[str, str]) -> dict[str, object]:
    import anndata as ad

    path = PROJECT_ROOT / spec["source_path"]
    if not path.exists():
        return {
            **spec,
            "source_exists": False,
            "file_size_bytes": 0,
            "n_obs": np.nan,
            "n_vars": np.nan,
            "obs_columns": "",
            "candidate_target_columns": "",
            "candidate_control_columns": "",
            "status": "missing_source",
            "next_step": "download or materialize source h5ad",
        }
    adata = ad.read_h5ad(path, backed="r")
    obs_cols = list(adata.obs.columns)
    target_cols = [c for c in obs_cols if any(token in c.lower() for token in ("gene", "target", "perturb", "guide", "sgrna"))]
    control_cols = [c for c in obs_cols if any(token in c.lower() for token in ("control", "ntc", "non", "safe"))]
    gene_counts = adata.obs["gene"].astype(str).value_counts() if "gene" in adata.obs else pd.Series(dtype=int)
    n_control_cells = int(gene_counts.get("non-targeting", 0))
    n_gene_labels = int(max(gene_counts.index.nunique() - (1 if "non-targeting" in gene_counts.index else 0), 0))
    n_gene_labels_ge_20_cells = int((gene_counts.drop(labels=["non-targeting"], errors="ignore") >= 20).sum())
    n_gene_labels_ge_50_cells = int((gene_counts.drop(labels=["non-targeting"], errors="ignore") >= 50).sum())
    materialized = PROJECT_ROOT / "reports/gse264667_endpoint_extension" / spec["dataset_id"] / "target_level_bridge_table.tsv.gz"
    if materialized.exists():
        status = "raw_h5ad_available_target_level_bridge_completed"
        next_step = "use as secondary endpoint-extension bridge evidence; do not use as model-generalization evidence"
    else:
        status = "raw_h5ad_available_pending_target_mapping"
        next_step = "materialize target-level observed shifts, map targets to cell-line-specific DepMap, then run bridge-form audit"
    return {
        **spec,
        "source_exists": True,
        "file_size_bytes": int(path.stat().st_size),
        "source_sha256": sha256_file(path),
        "n_obs": int(adata.n_obs),
        "n_vars": int(adata.n_vars),
        "obs_columns": ";".join(obs_cols[:80]),
        "candidate_target_columns": ";".join(target_cols),
        "candidate_control_columns": ";".join(control_cols),
        "n_gene_labels_excluding_non_targeting": n_gene_labels,
        "n_control_cells_non_targeting": n_control_cells,
        "n_gene_labels_ge_20_cells": n_gene_labels_ge_20_cells,
        "n_gene_labels_ge_50_cells": n_gene_labels_ge_50_cells,
        "status": status,
        "next_step": next_step,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build external bridge-form robustness summaries.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--n-permutations", type=int, default=1000)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=1729)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = [
        summarize_bridge(spec, args.n_permutations, args.n_bootstrap, args.seed + i)
        for i, spec in enumerate(BRIDGE_TABLES)
    ]
    summary = pd.DataFrame(rows)
    summary.to_csv(out / "observed_shift_depmap_bridge_summary.tsv", sep="\t", index=False)

    candidates = pd.DataFrame([audit_candidate_h5ad(spec) for spec in CANDIDATE_DATASETS])
    candidates.to_csv(out / "candidate_endpoint_extension_eligibility.tsv", sep="\t", index=False)

    layer_rows = []
    for spec in BRIDGE_TABLES:
        layer_rows.append(
            {
                "dataset_id": spec["dataset_id"],
                "context": spec["context"],
                "evidence_layer": spec["evidence_layer"],
                "current_status": "bridge_form_summary_completed",
                "claim_boundary": "observed shift-DepMap bridge evidence; not model generalization",
            }
        )
    completed_dataset_ids = {spec["dataset_id"] for spec in BRIDGE_TABLES}
    for spec in CANDIDATE_DATASETS:
        if spec["dataset_id"] in completed_dataset_ids:
            continue
        layer_rows.append(
            {
                "dataset_id": spec["dataset_id"],
                "context": spec["context"],
                "evidence_layer": spec["evidence_layer"],
                "current_status": "raw_data_available_pending_eligibility_and_bridge_materialization",
                "claim_boundary": "candidate endpoint-extension only until target-level bridge table is complete",
            }
        )
    layer_rows.extend(REGISTRY_ONLY_DATASETS)
    pd.DataFrame(layer_rows).to_csv(out / "dataset_evidence_layers.tsv", sep="\t", index=False)
    hash_rows = []
    for relative in (
        "observed_shift_depmap_bridge_summary.tsv",
        "candidate_endpoint_extension_eligibility.tsv",
        "dataset_evidence_layers.tsv",
    ):
        path = out / relative
        hash_rows.append(
            {
                "artifact": Path(relative).stem,
                "path": str(path.relative_to(PROJECT_ROOT)),
                "size_bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
            }
        )
    pd.DataFrame(hash_rows).to_csv(out / "artifact_hashes.tsv", sep="\t", index=False)
    print(f"external bridge-form robustness outputs: {out}")


if __name__ == "__main__":
    main()
