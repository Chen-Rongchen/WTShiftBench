from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "reports/category_response_pathway"
COLLECTION_FILES = {
    "hallmark": OUTPUT_DIR / "category_response_gsea_hallmark.tsv",
    "reactome": OUTPUT_DIR / "category_response_gsea_reactome.tsv",
    "gobp": OUTPUT_DIR / "category_response_gsea_gobp.tsv",
}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def top_terms(frame: pd.DataFrame, n: int = 3) -> str:
    sig = frame.loc[frame["padj"].le(0.10)].copy()
    if sig.empty:
        sig = frame.copy()
    sig = sig.sort_values(["padj", "pval", "pathway"], na_position="last").head(n)
    terms = []
    for row in sig.itertuples(index=False):
        terms.append(f"{row.pathway} ({row.direction}, NES={float(row.NES):.3g}, q={float(row.padj):.3g})")
    return "; ".join(terms)


def build_summary() -> Path:
    rows = []
    for collection, path in COLLECTION_FILES.items():
        gsea = pd.read_csv(path, sep="\t")
        for (context, category), group in gsea.groupby(["context", "endpoint_category"], sort=True):
            rows.append(
                {
                    "context": context,
                    "endpoint_category": category,
                    "collection": collection,
                    "n_targets": int(group["n_targets"].max()),
                    "n_pathways_tested": int(group["pathway"].nunique()),
                    "n_padj_lt_0_10": int(group["padj"].le(0.10).sum()),
                    "n_padj_lt_0_05": int(group["padj"].le(0.05).sum()),
                    "top_terms": top_terms(group),
                    "primary_interpretation": (
                        "response-program annotation only; endpoint categories are frozen truth-side labels"
                    ),
                    "not_allowed_interpretation": (
                        "do not infer that category target genes mechanistically cause the enriched pathway"
                    ),
                }
            )
    out_path = OUTPUT_DIR / "category_response_gsea_summary.tsv"
    pd.DataFrame(rows).sort_values(["collection", "context", "endpoint_category"]).to_csv(
        out_path, sep="\t", index=False
    )
    return out_path


def update_manifest(summary_path: Path) -> None:
    manifest_path = OUTPUT_DIR / "source_manifest.tsv"
    manifest = pd.read_csv(manifest_path, sep="\t")
    row = {
        "artifact": summary_path.stem,
        "path": str(summary_path.relative_to(PROJECT_ROOT)),
        "size_bytes": int(summary_path.stat().st_size),
        "sha256": sha256_file(summary_path),
    }
    manifest = manifest.loc[manifest["artifact"].ne(summary_path.stem)].copy()
    manifest = pd.concat([manifest, pd.DataFrame([row])], ignore_index=True)
    manifest.to_csv(manifest_path, sep="\t", index=False)


def main() -> None:
    summary_path = build_summary()
    update_manifest(summary_path)
    print(f"wrote {summary_path}")


if __name__ == "__main__":
    main()
