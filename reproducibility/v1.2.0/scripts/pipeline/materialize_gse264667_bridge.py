from __future__ import annotations

import argparse
import gzip
import hashlib
import shutil
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import stats

from wtbench.truth_bridge import clean_depmap_gene_columns


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports/gse264667_endpoint_extension"
DEP_EFFECT = PROJECT_ROOT / "depmap/CRISPRGeneEffect.csv"
DEP_DEPENDENCY = PROJECT_ROOT / "depmap/CRISPRGeneDependency.csv"

CONTEXTS = (
    {
        "dataset_id": "gse264667_hepg2_day7",
        "context": "HepG2 day 7",
        "cell_line": "HepG2",
        "depmap_model_id": "ACH-000739",
        "source_path": "data/raw/gse264667/series/GSE264667_hepg2_raw_singlecell_01.h5ad",
        "evidence_layer": "candidate_secondary_endpoint_extension",
        "claim_role": "secondary cancer-line endpoint-extension evidence",
        "depmap_id_source": "DepMap/Harmonizome cell-line mapping; verified row exists in local CRISPRGeneEffect.csv",
    },
    {
        "dataset_id": "gse264667_jurkat_day7",
        "context": "Jurkat day 7",
        "cell_line": "Jurkat",
        "depmap_model_id": "ACH-000995",
        "source_path": "data/raw/gse264667/series/GSE264667_jurkat_raw_singlecell_01.h5ad",
        "evidence_layer": "candidate_secondary_endpoint_extension",
        "claim_role": "secondary lineage-boundary endpoint-extension evidence",
        "depmap_id_source": "DepMap/Jurkat mapping; verified row exists in local CRISPRGeneEffect.csv",
    },
)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_depmap_row(path: Path, model_id: str) -> pd.Series:
    frame = pd.read_csv(path)
    frame.columns = clean_depmap_gene_columns(pd.Index(frame.columns))
    frame = frame.rename(columns={"ModelID": "depmap_model_id"})
    row = frame.loc[frame["depmap_model_id"].astype(str).eq(model_id)]
    if row.empty:
        raise ValueError(f"{model_id} not found in {path}")
    return row.iloc[0].drop(labels=["depmap_model_id"], errors="ignore")


def top_k_mean_abs(values: np.ndarray, k: int) -> float:
    if values.size == 0:
        return np.nan
    k = min(k, values.size)
    return float(np.partition(np.abs(values), -k)[-k:].mean())


def materialize_context(
    spec: dict[str, str],
    *,
    output_dir: Path,
    min_target_cells: int,
    min_control_cells: int,
    chunk_size: int,
    target_sum: float,
) -> tuple[Path, pd.DataFrame]:
    path = PROJECT_ROOT / spec["source_path"]
    adata = ad.read_h5ad(path, backed="r")
    try:
        obs = adata.obs.copy()
        if "gene" not in obs.columns:
            raise ValueError(f"{path} missing obs['gene']")
        genes = adata.var["gene_name"].astype(str).tolist() if "gene_name" in adata.var else adata.var.index.astype(str).tolist()
        labels = obs["gene"].astype(str)
        counts = labels.value_counts()
        control_label = "non-targeting"
        n_control = int(counts.get(control_label, 0))
        if n_control < min_control_cells:
            raise ValueError(f"{spec['context']} has {n_control} controls < {min_control_cells}")
        target_labels = sorted(
            label for label, n in counts.items()
            if label != control_label and int(n) >= min_target_cells
        )
        group_labels = [control_label] + target_labels
        group_index = {label: i for i, label in enumerate(group_labels)}
        codes = labels.map(group_index).fillna(-1).astype(int).to_numpy()

        sums = np.zeros((len(group_labels), adata.n_vars), dtype=np.float64)
        group_counts = np.zeros(len(group_labels), dtype=np.int64)
        for start in range(0, adata.n_obs, chunk_size):
            stop = min(start + chunk_size, adata.n_obs)
            chunk_codes = codes[start:stop]
            keep = chunk_codes >= 0
            if not np.any(keep):
                continue
            x = np.asarray(adata.X[start:stop], dtype=np.float32)
            x = x[keep]
            chunk_codes = chunk_codes[keep]
            totals = x.sum(axis=1)
            nonzero = totals > 0
            if not np.any(nonzero):
                continue
            x = x[nonzero]
            chunk_codes = chunk_codes[nonzero]
            totals = totals[nonzero]
            x = np.log1p(x / totals[:, None] * target_sum)
            for code in np.unique(chunk_codes):
                mask = chunk_codes == code
                sums[code] += x[mask].sum(axis=0, dtype=np.float64)
                group_counts[code] += int(mask.sum())

        effect = load_depmap_row(DEP_EFFECT, spec["depmap_model_id"])
        dependency = load_depmap_row(DEP_DEPENDENCY, spec["depmap_model_id"])
        control_mean = sums[0] / max(group_counts[0], 1)
        rows = []
        for label in target_labels:
            code = group_index[label]
            if group_counts[code] < min_target_cells:
                continue
            target_mean = sums[code] / max(group_counts[code], 1)
            delta = target_mean - control_mean
            dep_effect = pd.to_numeric(pd.Series([effect.get(label, np.nan)]), errors="coerce").iloc[0]
            dep_dependency = pd.to_numeric(pd.Series([dependency.get(label, np.nan)]), errors="coerce").iloc[0]
            rows.append(
                {
                    "dataset_id": spec["dataset_id"],
                    "context": spec["context"],
                    "cell_line": spec["cell_line"],
                    "depmap_model_id": spec["depmap_model_id"],
                    "depmap_id_source": spec["depmap_id_source"],
                    "target_gene": label,
                    "n_cells_target": int(group_counts[code]),
                    "n_cells_control": int(group_counts[0]),
                    "truth_source_cell_count": int(adata.n_obs),
                    "gene_universe_size": int(adata.n_vars),
                    "normalization": f"log1p(raw_counts_per_cell_total * {target_sum:g})",
                    "min_target_cells": int(min_target_cells),
                    "real_shift_L2": float(np.linalg.norm(delta)),
                    "real_shift_mean_abs": float(np.abs(delta).mean()),
                    "real_shift_top20_mean": top_k_mean_abs(delta, 20),
                    "real_shift_top50_mean": top_k_mean_abs(delta, 50),
                    "real_shift_top100_mean": top_k_mean_abs(delta, 100),
                    "depmap_gene_effect": float(dep_effect) if pd.notna(dep_effect) else np.nan,
                    "depmap_gene_dependency": float(dep_dependency) if pd.notna(dep_dependency) else np.nan,
                    "depmap_effect_found": bool(pd.notna(dep_effect)),
                    "depmap_dependency_found": bool(pd.notna(dep_dependency)),
                    "depmap_join_status": "both" if pd.notna(dep_effect) and pd.notna(dep_dependency) else "missing",
                }
            )
        table = pd.DataFrame(rows)
        out_path = output_dir / spec["dataset_id"] / "target_level_bridge_table.tsv.gz"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(out_path, sep="\t", index=False, compression="gzip")
        qc = pd.DataFrame(
            {
                "context": [spec["context"]],
                "n_obs": [adata.n_obs],
                "n_vars": [adata.n_vars],
                "n_controls": [int(group_counts[0])],
                "n_candidate_targets_before_min_cell_filter": [int((counts.drop(labels=[control_label], errors="ignore") > 0).sum())],
                "n_targets_passing_min_cell_filter": [len(target_labels)],
                "n_targets_output": [int(table["target_gene"].nunique())],
                "n_targets_with_both_depmap": [int(table["depmap_join_status"].eq("both").sum())],
                "min_target_cells": [min_target_cells],
                "min_control_cells": [min_control_cells],
                "chunk_size": [chunk_size],
                "source_path": [spec["source_path"]],
                "source_sha256": [sha256_file(path)],
                "output_path": [str(out_path.relative_to(PROJECT_ROOT))],
                "output_sha256": [sha256_file(out_path)],
            }
        )
        qc.to_csv(output_dir / spec["dataset_id"] / "materialization_qc.tsv", sep="\t", index=False)
        return out_path, table
    finally:
        adata.file.close()


def empirical_p(observed: float, null: np.ndarray) -> float:
    if not np.isfinite(observed) or null.size == 0:
        return np.nan
    return (float(np.sum(np.abs(null) >= abs(observed))) + 1.0) / (float(null.size) + 1.0)


def bootstrap_ci(x: np.ndarray, y: np.ndarray, method: str, rng: np.random.Generator, n_bootstrap: int) -> tuple[float, float]:
    if len(x) < 4:
        return np.nan, np.nan
    values = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, len(x), len(x))
        xb = x[idx]
        yb = y[idx]
        if np.unique(xb).size < 2 or np.unique(yb).size < 2:
            continue
        values.append(stats.spearmanr(xb, yb).statistic if method == "spearman" else stats.pearsonr(xb, yb).statistic)
    if not values:
        return np.nan, np.nan
    return tuple(np.quantile(values, [0.025, 0.975]))


def summarize_context(spec: dict[str, str], path: Path, table: pd.DataFrame, n_perm: int, n_bootstrap: int, seed: int) -> dict[str, object]:
    data = table.loc[table["depmap_join_status"].eq("both"), ["target_gene", "real_shift_mean_abs", "depmap_gene_dependency"]].copy()
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
        null_s = null_p = np.array([])
        spearman_ci = pearson_ci = (np.nan, np.nan)
        status = "not_estimable"
    return {
        "dataset_id": spec["dataset_id"],
        "context": spec["context"],
        "cell_line": spec["cell_line"],
        "evidence_layer": spec["evidence_layer"],
        "claim_role": spec["claim_role"],
        "source_path": str(path.relative_to(PROJECT_ROOT)),
        "source_sha256": sha256_file(path),
        "n_targets_total": int(table["target_gene"].nunique()),
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
        "supported_claim": "secondary endpoint-extension bridge-form evidence; not model generalization",
    }


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
    parser = argparse.ArgumentParser(description="Materialize GSE264667 HepG2/Jurkat target-level bridge tables.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--min-target-cells", type=int, default=50)
    parser.add_argument("--min-control-cells", type=int, default=500)
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--target-sum", type=float, default=10000.0)
    parser.add_argument("--n-perm", type=int, default=1000)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=264667)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    summaries = []
    for i, spec in enumerate(CONTEXTS):
        path, table = materialize_context(
            spec,
            output_dir=output_dir,
            min_target_cells=args.min_target_cells,
            min_control_cells=args.min_control_cells,
            chunk_size=args.chunk_size,
            target_sum=args.target_sum,
        )
        paths.append(path)
        qc_path = output_dir / spec["dataset_id"] / "materialization_qc.tsv"
        paths.append(qc_path)
        summaries.append(summarize_context(spec, path, table, args.n_perm, args.n_bootstrap, args.seed + i))
    summary_path = output_dir / "observed_shift_depmap_bridge_summary.tsv"
    pd.DataFrame(summaries).to_csv(summary_path, sep="\t", index=False)
    paths.append(summary_path)

    registry_copy = PROJECT_ROOT / "resource_registry/gse264667_observed_shift_depmap_bridge_summary.tsv"
    registry_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(summary_path, registry_copy)
    paths.append(registry_copy)
    write_manifest(output_dir, paths)
    print(f"wrote {summary_path}")


if __name__ == "__main__":
    main()
