from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

import pandas as pd

from scripts.pipeline.category_response_pathway import (
    GMT_FILES,
    PROJECT_ROOT,
    DEFAULT_RSCRIPT_BIN,
    bh_fdr,
    run_fgsea,
)


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports/category_response_pathway/contrasts"
SIGNATURES = PROJECT_ROOT / "reports/category_response_pathway/category_response_signatures.tsv.gz"
SUMMARY = PROJECT_ROOT / "reports/category_response_pathway/category_response_summary.tsv"

CONTRASTS = (
    {
        "contrast_id": "Q1_anchor_vs_Q4_low_information",
        "positive_category": "Q1_anchor",
        "negative_category": "Q4_low_information",
        "claim_role": "anchor response-program contrast against low-information targets",
    },
    {
        "contrast_id": "Q1_anchor_vs_middle",
        "positive_category": "Q1_anchor",
        "negative_category": "middle",
        "claim_role": "anchor response-program contrast against retained middle band",
    },
)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_contrast_signatures(signatures: pd.DataFrame, summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    qc = []
    for context, csign in signatures.groupby("context"):
        available = set(csign["endpoint_category"].astype(str))
        for contrast in CONTRASTS:
            pos = contrast["positive_category"]
            neg = contrast["negative_category"]
            include = pos in available and neg in available
            if not include:
                qc.append(
                    {
                        "context": context,
                        **contrast,
                        "included": False,
                        "reason": f"missing category: {pos if pos not in available else neg}",
                    }
                )
                continue
            pos_df = csign.loc[csign["endpoint_category"].eq(pos), ["gene", "category_signed_shift", "n_targets", "targets"]]
            neg_df = csign.loc[csign["endpoint_category"].eq(neg), ["gene", "category_signed_shift", "n_targets", "targets"]]
            merged = pos_df.merge(neg_df, on="gene", suffixes=("_positive", "_negative"), how="inner")
            merged["contrast_score"] = merged["category_signed_shift_positive"] - merged["category_signed_shift_negative"]
            merged["context"] = context
            merged["contrast_id"] = contrast["contrast_id"]
            merged["positive_category"] = pos
            merged["negative_category"] = neg
            merged["claim_role"] = contrast["claim_role"]
            merged["ranking_method"] = "mean_signed_shift_positive_category_minus_negative_category"
            merged["claim_boundary"] = (
                "exploratory response-program contrast; not a causal mechanism or target-membership enrichment claim"
            )
            rows.append(merged)
            qc.append(
                {
                    "context": context,
                    **contrast,
                    "included": True,
                    "reason": "",
                    "n_genes": int(merged["gene"].nunique()),
                    "n_targets_positive": int(summary.loc[
                        summary["context"].eq(context) & summary["endpoint_category"].eq(pos), "n_targets"
                    ].iloc[0]),
                    "n_targets_negative": int(summary.loc[
                        summary["context"].eq(context) & summary["endpoint_category"].eq(neg), "n_targets"
                    ].iloc[0]),
                }
            )
    contrast_signatures = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    return contrast_signatures, pd.DataFrame(qc)


def run_contrast_gsea(
    contrast_signatures: pd.DataFrame,
    *,
    output_dir: Path,
    rscript_bin: str,
    eps: float,
    n_perm_simple: int,
    seed: int,
) -> list[Path]:
    output_paths = []
    for collection, gmt_path in GMT_FILES.items():
        frames = []
        for i, ((context, contrast_id), group) in enumerate(
            contrast_signatures.groupby(["context", "contrast_id"], sort=True)
        ):
            ranking = group.set_index("gene")["contrast_score"].astype(float).sort_values(ascending=False)
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
            meta = group.iloc[0]
            result["context"] = context
            result["contrast_id"] = contrast_id
            result["positive_category"] = meta["positive_category"]
            result["negative_category"] = meta["negative_category"]
            result["collection"] = collection
            result["ranking_method"] = meta["ranking_method"]
            result["claim_boundary"] = meta["claim_boundary"]
            frames.append(result)
        out = output_dir / f"category_response_contrast_gsea_{collection}.tsv"
        if frames:
            frame = pd.concat(frames, ignore_index=True)
            if "pval" in frame:
                frame["padj_within_context_contrast"] = frame.groupby(["context", "contrast_id"])["pval"].transform(bh_fdr)
            frame.to_csv(out, sep="\t", index=False)
        else:
            pd.DataFrame().to_csv(out, sep="\t", index=False)
        output_paths.append(out)
    return output_paths


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
    parser = argparse.ArgumentParser(description="Run response-level endpoint-category contrast GSEA.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--rscript-bin", default=DEFAULT_RSCRIPT_BIN)
    parser.add_argument("--eps", type=float, default=1e-10)
    parser.add_argument("--n-perm-simple", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=8921)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    signatures = pd.read_csv(SIGNATURES, sep="\t")
    summary = pd.read_csv(SUMMARY, sep="\t")
    contrast_signatures, qc = build_contrast_signatures(signatures, summary)

    paths = []
    sig_path = output_dir / "category_response_contrast_signatures.tsv.gz"
    contrast_signatures.to_csv(sig_path, sep="\t", index=False, compression="gzip")
    paths.append(sig_path)
    qc_path = output_dir / "category_response_contrast_qc.tsv"
    qc.to_csv(qc_path, sep="\t", index=False)
    paths.append(qc_path)
    paths.extend(
        run_contrast_gsea(
            contrast_signatures,
            output_dir=output_dir,
            rscript_bin=args.rscript_bin,
            eps=args.eps,
            n_perm_simple=args.n_perm_simple,
            seed=args.seed,
        )
    )
    hallmark = output_dir / "category_response_contrast_gsea_hallmark.tsv"
    if hallmark.exists():
        registry_copy = PROJECT_ROOT / "resource_registry/category_response_contrast_gsea_hallmark.tsv"
        registry_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(hallmark, registry_copy)
        paths.append(registry_copy)
    write_manifest(output_dir, paths)
    print(f"category response contrast GSEA outputs: {output_dir}")


if __name__ == "__main__":
    main()
