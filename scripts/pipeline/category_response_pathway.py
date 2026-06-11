from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse, stats


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports/category_response_pathway"
R_FGSEA_SCRIPT = PROJECT_ROOT / "src/wtbench/pathway_response/run_fgsea.R"
DEFAULT_RSCRIPT_BIN = "/opt/R/4.3.2/bin/Rscript"

CONTEXTS = {
    "HCC38": PROJECT_ROOT / "data/processed/hcc_gears_formal/HCC38.h5ad",
    "HCC1143": PROJECT_ROOT / "data/processed/hcc_gears_formal/HCC1143.h5ad",
}

GMT_FILES = {
    "hallmark": PROJECT_ROOT / "data/reference/gene_sets/axis_annotation/msigdb_hallmark.gmt",
    "reactome": PROJECT_ROOT / "data/reference/gene_sets/axis_annotation/reactome.gmt",
    "gobp": PROJECT_ROOT / "data/reference/gene_sets/axis_annotation/go_bp.gmt",
}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bh_fdr(pvalues: pd.Series) -> pd.Series:
    p = pd.to_numeric(pvalues, errors="coerce").to_numpy(float)
    out = np.full(len(p), np.nan)
    valid = np.isfinite(p)
    if valid.sum() == 0:
        return pd.Series(out, index=pvalues.index)
    pv = p[valid]
    order = np.argsort(pv)
    ranked = pv[order]
    adjusted = np.empty_like(ranked)
    prev = 1.0
    m = len(ranked)
    for i in range(m - 1, -1, -1):
        value = min(prev, ranked[i] * m / (i + 1))
        adjusted[i] = value
        prev = value
    valid_indices = np.flatnonzero(valid)
    out[valid_indices[order]] = np.minimum(adjusted, 1.0)
    return pd.Series(out, index=pvalues.index)


def read_gmt(path: Path) -> dict[str, set[str]]:
    gene_sets: dict[str, set[str]] = {}
    with path.open() as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            gene_sets[parts[0]] = set(g for g in parts[2:] if g)
    return gene_sets


def extract_gene_symbols(var: pd.DataFrame) -> list[str]:
    if "gene_name" in var.columns:
        return var["gene_name"].astype(str).tolist()
    return var.index.astype(str).tolist()


def load_category_grid() -> pd.DataFrame:
    path = PROJECT_ROOT / "reports/truth_bridge_decomposition/target_level_joint_grid.tsv"
    grid = pd.read_csv(path, sep="\t")
    grid = grid.loc[grid["cell_line"].isin(CONTEXTS)].copy()
    grid["endpoint_category"] = grid["joint_grid"].astype(str)
    return grid


def load_context_matrix(context: str) -> tuple[sparse.csr_matrix, pd.DataFrame, list[str]]:
    adata = ad.read_h5ad(CONTEXTS[context])
    X = adata.X.tocsr() if sparse.issparse(adata.X) else sparse.csr_matrix(np.asarray(adata.X))
    obs = adata.obs.copy()
    genes = extract_gene_symbols(adata.var.copy())
    return X, obs, genes


def compute_target_shift_vectors(context: str, min_target_cells: int, min_control_cells: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    X, obs, genes = load_context_matrix(context)
    if "is_control" not in obs or "target_gene" not in obs:
        raise ValueError(f"{context} h5ad must contain obs columns is_control and target_gene")
    control_mask = obs["is_control"].astype(bool).to_numpy()
    n_control = int(control_mask.sum())
    if n_control < min_control_cells:
        raise ValueError(f"{context} has only {n_control} control cells")
    control_mean = np.asarray(X[control_mask].mean(axis=0)).ravel()

    rows = []
    qc = []
    for target in sorted(obs.loc[~obs["is_control"].astype(bool), "target_gene"].astype(str).unique()):
        target_mask = (~obs["is_control"].astype(bool).to_numpy()) & (obs["target_gene"].astype(str).to_numpy() == target)
        n_target = int(target_mask.sum())
        include = n_target >= min_target_cells
        reason = "" if include else f"n_target={n_target} < {min_target_cells}"
        qc.append(
            {
                "context": context,
                "target_gene": target,
                "n_target_cells": n_target,
                "n_control_cells": n_control,
                "included": include,
                "exclusion_reason": reason,
            }
        )
        if not include:
            continue
        target_mean = np.asarray(X[target_mask].mean(axis=0)).ravel()
        shift = target_mean - control_mean
        rows.extend(
            {
                "context": context,
                "target_gene": target,
                "gene": gene,
                "signed_shift": float(value),
            }
            for gene, value in zip(genes, shift)
        )
    return pd.DataFrame(rows), pd.DataFrame(qc)


def aggregate_category_signatures(target_shifts: pd.DataFrame, grid: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged = target_shifts.merge(
        grid[["cell_line", "target_gene", "endpoint_category", "grid_role"]],
        left_on=["context", "target_gene"],
        right_on=["cell_line", "target_gene"],
        how="inner",
    )
    signatures = (
        merged.groupby(["context", "endpoint_category", "grid_role", "gene"], as_index=False)
        .agg(
            category_signed_shift=("signed_shift", "mean"),
            category_abs_mean_shift=("signed_shift", lambda s: float(np.mean(np.abs(s)))),
            n_targets=("target_gene", "nunique"),
            targets=("target_gene", lambda s: ";".join(sorted(set(s)))),
        )
    )
    category_summary = (
        signatures[["context", "endpoint_category", "grid_role", "n_targets", "targets"]]
        .drop_duplicates()
        .sort_values(["context", "endpoint_category"])
    )
    return signatures, category_summary


def run_fgsea(
    ranking: pd.Series,
    gmt_path: Path,
    *,
    rscript_bin: str,
    seed: int,
    eps: float,
    n_perm_simple: int,
    min_size: int,
    max_size: int,
) -> pd.DataFrame:
    if not Path(rscript_bin).exists() and shutil.which(rscript_bin) is None:
        raise FileNotFoundError(f"Rscript binary not found: {rscript_bin}")
    if not R_FGSEA_SCRIPT.exists():
        raise FileNotFoundError(f"R fgsea wrapper missing: {R_FGSEA_SCRIPT}")
    with tempfile.TemporaryDirectory(prefix="category_fgsea_") as tmpdir:
        tmp_in = Path(tmpdir) / "ranking.tsv"
        tmp_out = Path(tmpdir) / "fgsea.tsv"
        ranking.rename_axis("gene").reset_index(name="score").to_csv(tmp_in, sep="\t", index=False)
        cmd = [
            rscript_bin,
            str(R_FGSEA_SCRIPT),
            "--ranking-tsv",
            str(tmp_in),
            "--gmt",
            str(gmt_path),
            "--output-tsv",
            str(tmp_out),
            "--min-size",
            str(min_size),
            "--max-size",
            str(max_size),
            "--eps",
            str(eps),
            "--n-perm-simple",
            str(n_perm_simple),
            "--seed",
            str(seed),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout)
            sys.stderr.write(proc.stderr)
            raise RuntimeError(f"fgsea failed: {' '.join(cmd)}")
        return pd.read_csv(tmp_out, sep="\t")


def run_category_gsea(
    signatures: pd.DataFrame,
    category_summary: pd.DataFrame,
    output_dir: Path,
    rscript_bin: str,
    eps: float,
    n_perm_simple: int,
    seed: int,
) -> list[Path]:
    output_paths: list[Path] = []
    for collection, gmt_path in GMT_FILES.items():
        frames = []
        for i, ((context, category), group) in enumerate(signatures.groupby(["context", "endpoint_category"])):
            n_targets = int(
                category_summary.loc[
                    (category_summary["context"].eq(context))
                    & (category_summary["endpoint_category"].eq(category)),
                    "n_targets",
                ].iloc[0]
            )
            if n_targets < 2:
                continue
            ranking = (
                group.set_index("gene")["category_signed_shift"]
                .astype(float)
                .sort_values(ascending=False)
            )
            result = run_fgsea(
                ranking,
                gmt_path,
                rscript_bin=rscript_bin,
                seed=seed + i,
                eps=eps,
                n_perm_simple=n_perm_simple,
                min_size=10,
                max_size=500,
            )
            result["context"] = context
            result["endpoint_category"] = category
            result["n_targets"] = n_targets
            result["collection"] = collection
            result["ranking_method"] = "mean_signed_observed_shift_across_category_targets"
            result["claim_boundary"] = "exploratory response-program annotation; not causal mechanism"
            frames.append(result)
        out_path = output_dir / f"category_response_gsea_{collection}.tsv"
        if frames:
            pd.concat(frames, ignore_index=True).to_csv(out_path, sep="\t", index=False)
        else:
            pd.DataFrame().to_csv(out_path, sep="\t", index=False)
        output_paths.append(out_path)
    return output_paths


def run_target_set_ora(grid: pd.DataFrame, output_dir: Path) -> Path:
    rows = []
    for collection, gmt_path in GMT_FILES.items():
        gene_sets = read_gmt(gmt_path)
        for context, cgrid in grid.groupby("cell_line"):
            universe = set(cgrid["target_gene"].astype(str))
            m = len(universe)
            for category, subset in cgrid.groupby("endpoint_category"):
                category_targets = set(subset["target_gene"].astype(str))
                n = len(category_targets)
                if n == 0:
                    continue
                for pathway, genes in gene_sets.items():
                    pathway_targets = universe & genes
                    k = len(category_targets & genes)
                    if k == 0 or len(pathway_targets) == 0:
                        continue
                    pvalue = float(stats.hypergeom.sf(k - 1, m, len(pathway_targets), n))
                    rows.append(
                        {
                            "context": context,
                            "endpoint_category": category,
                            "collection": collection,
                            "pathway": pathway,
                            "n_category_targets": n,
                            "n_universe_targets": m,
                            "n_pathway_targets_in_universe": len(pathway_targets),
                            "n_overlap": k,
                            "overlap_targets": ";".join(sorted(category_targets & genes)),
                            "pvalue": pvalue,
                            "claim_boundary": "descriptive target-membership annotation only",
                        }
                    )
    ora = pd.DataFrame(rows)
    if not ora.empty:
        ora["padj"] = ora.groupby(["context", "endpoint_category", "collection"])["pvalue"].transform(bh_fdr)
    out_path = output_dir / "target_set_ora_descriptive.tsv"
    ora.to_csv(out_path, sep="\t", index=False)
    return out_path


def write_manifest(output_dir: Path, paths: list[Path]) -> None:
    rows = []
    for path in paths:
        if not path.exists():
            continue
        rows.append(
            {
                "artifact": path.stem,
                "path": str(path.relative_to(PROJECT_ROOT)),
                "size_bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
            }
        )
    pd.DataFrame(rows).to_csv(output_dir / "source_manifest.tsv", sep="\t", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Endpoint-category response-level pathway enrichment.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--rscript-bin", default=DEFAULT_RSCRIPT_BIN)
    parser.add_argument("--eps", type=float, default=1e-10)
    parser.add_argument("--n-perm-simple", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=4207)
    parser.add_argument("--min-target-cells", type=int, default=20)
    parser.add_argument("--min-control-cells", type=int, default=50)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    grid = load_category_grid()
    shift_frames = []
    qc_frames = []
    for context in CONTEXTS:
        shifts, qc = compute_target_shift_vectors(context, args.min_target_cells, args.min_control_cells)
        shift_frames.append(shifts)
        qc_frames.append(qc)
    target_shifts = pd.concat(shift_frames, ignore_index=True)
    target_qc = pd.concat(qc_frames, ignore_index=True)
    signatures, category_summary = aggregate_category_signatures(target_shifts, grid)

    outputs = []
    p = output_dir / "target_shift_vectors.tsv.gz"
    target_shifts.to_csv(p, sep="\t", index=False, compression="gzip")
    outputs.append(p)
    p = output_dir / "target_inclusion_qc.tsv"
    target_qc.to_csv(p, sep="\t", index=False)
    outputs.append(p)
    p = output_dir / "category_response_signatures.tsv.gz"
    signatures.to_csv(p, sep="\t", index=False, compression="gzip")
    outputs.append(p)
    p = output_dir / "category_response_summary.tsv"
    category_summary.to_csv(p, sep="\t", index=False)
    outputs.append(p)
    outputs.extend(
        run_category_gsea(
            signatures,
            category_summary,
            output_dir,
            rscript_bin=args.rscript_bin,
            eps=args.eps,
            n_perm_simple=args.n_perm_simple,
            seed=args.seed,
        )
    )
    outputs.append(run_target_set_ora(grid, output_dir))
    write_manifest(output_dir, outputs)
    print(f"category response pathway outputs: {output_dir}")


if __name__ == "__main__":
    main()
