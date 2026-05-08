from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from scipy.stats import hypergeom


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/axis_enrichment_template_v1.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 Stage 2 axis-level enrichment。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="axis enrichment 配置 JSON 路径。")
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload


def load_gmt(path: Path) -> dict[str, set[str]]:
    terms: dict[str, set[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 3:
            continue
        term = parts[0].strip()
        genes = {item.strip() for item in parts[2:] if item.strip()}
        if genes:
            terms[term] = genes
    return terms


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    n = len(p_values)
    if n == 0:
        return []
    order = sorted(range(n), key=lambda idx: p_values[idx])
    adjusted = [1.0] * n
    running = 1.0
    for rank, idx in enumerate(reversed(order), start=1):
        original_idx = idx
        p_value = p_values[original_idx]
        factor = n / (n - rank + 1)
        running = min(running, p_value * factor)
        adjusted[original_idx] = min(1.0, running)
    return adjusted


def build_axis_gene_sets(signature: pd.DataFrame, top_n: int) -> dict[str, set[str]]:
    gene_sets: dict[str, set[str]] = {}
    for axis_id, frame in signature.groupby("axis_id", sort=True):
        top = frame.sort_values(["rank", "axis_score"], ascending=[True, False]).head(top_n)
        gene_sets[str(axis_id)] = set(top["gene"].astype(str))
    return gene_sets


def run_ora(
    *,
    axis_id: str,
    axis_genes: set[str],
    universe: set[str],
    database: str,
    terms: dict[str, set[str]],
    min_genes_per_term: int,
    max_genes_per_term: int,
    min_overlap: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    M = len(universe)
    N = len(axis_genes)
    for term, term_genes in terms.items():
        filtered = term_genes & universe
        K = len(filtered)
        if K < min_genes_per_term or K > max_genes_per_term:
            continue
        overlap_genes = axis_genes & filtered
        x = len(overlap_genes)
        if x < min_overlap:
            continue
        p_value = float(hypergeom.sf(x - 1, M, K, N))
        rows.append(
            {
                "axis_id": axis_id,
                "database": database,
                "term": term,
                "NES_or_effect": float(x / N) if N else 0.0,
                "FDR": p_value,
                "leading_edge_size": x,
                "overlap_gene_count": x,
                "term_gene_count_in_universe": K,
                "axis_gene_count": N,
                "overlap_genes": "; ".join(sorted(overlap_genes)),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    adjusted = benjamini_hochberg(frame["FDR"].astype(float).tolist())
    frame["FDR"] = adjusted
    return frame.sort_values(["FDR", "leading_edge_size", "term"]).reset_index(drop=True)


def main() -> None:
    args = build_parser().parse_args()
    config = load_json(resolve_path(args.config))
    signature_path = resolve_path(str(config["input"]["axis_gene_signature_path"]))
    output_path = resolve_path(str(config["output"]["table_path"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    signature = pd.read_csv(signature_path, sep="\t")
    if signature.empty:
        pd.DataFrame(columns=["axis_id", "database", "term", "NES_or_effect", "FDR", "leading_edge_size"]).to_csv(
            output_path, sep="\t", index=False
        )
        print(json.dumps({"status": "empty_signature", "output_path": str(output_path.relative_to(PROJECT_ROOT))}, ensure_ascii=False))
        return

    top_n = int(config["analysis"]["top_n_per_axis"])
    axis_gene_sets = build_axis_gene_sets(signature, top_n=top_n)
    universe = set(signature["gene"].astype(str))
    min_genes_per_term = int(config["analysis"]["min_genes_per_term"])
    max_genes_per_term = int(config["analysis"]["max_genes_per_term"])
    min_overlap = int(config["analysis"]["min_overlap"])

    rows: list[pd.DataFrame] = []
    for collection in config["gene_sets"]["collections"]:
        database = str(collection["database"])
        gmt_path = resolve_path(str(collection["gmt_path"]))
        if not gmt_path.exists():
            raise FileNotFoundError(f"缺少 gene set GMT：{gmt_path}")
        terms = load_gmt(gmt_path)
        for axis_id, axis_genes in axis_gene_sets.items():
            rows.append(
                run_ora(
                    axis_id=axis_id,
                    axis_genes=axis_genes,
                    universe=universe,
                    database=database,
                    terms=terms,
                    min_genes_per_term=min_genes_per_term,
                    max_genes_per_term=max_genes_per_term,
                    min_overlap=min_overlap,
                )
            )
    result = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if result.empty:
        result = pd.DataFrame(
            columns=[
                "axis_id",
                "database",
                "term",
                "NES_or_effect",
                "FDR",
                "leading_edge_size",
                "overlap_gene_count",
                "term_gene_count_in_universe",
                "axis_gene_count",
                "overlap_genes",
            ]
        )
    result.to_csv(output_path, sep="\t", index=False)
    print(
        json.dumps(
            {
                "status": "completed",
                "output_path": str(output_path.relative_to(PROJECT_ROOT)),
                "n_rows": int(len(result)),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
