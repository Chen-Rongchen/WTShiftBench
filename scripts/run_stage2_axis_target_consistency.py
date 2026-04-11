from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from scipy.stats import hypergeom


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/stage2/axis_target_consistency_template_v1.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 Stage 2 per-target pathway consistency audit。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="axis target consistency 配置 JSON 路径。")
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


def build_target_gene_sets(signature: pd.DataFrame, top_n: int) -> dict[tuple[str, str], pd.DataFrame]:
    gene_sets: dict[tuple[str, str], pd.DataFrame] = {}
    grouped = signature.groupby(["axis_id", "target_gene"], sort=True)
    for key, frame in grouped:
        top = frame.sort_values(["score"], ascending=[False]).head(top_n)
        gene_sets[(str(key[0]), str(key[1]))] = top.reset_index(drop=True)
    return gene_sets


def update_top_target_gene_sets(
    top_frames: dict[tuple[str, str], pd.DataFrame],
    chunk: pd.DataFrame,
    top_n: int,
) -> dict[tuple[str, str], pd.DataFrame]:
    for key, frame in chunk.groupby(["axis_id", "target_gene"], sort=False):
        existing = top_frames.get((str(key[0]), str(key[1])))
        candidate = frame.copy()
        if existing is not None and not existing.empty:
            candidate = pd.concat([existing, candidate], ignore_index=True)
        top_frames[(str(key[0]), str(key[1]))] = (
            candidate.sort_values(["score"], ascending=[False]).head(top_n).reset_index(drop=True)
        )
    return top_frames


def run_ora(
    *,
    axis_id: str,
    target_gene: str,
    target_frame: pd.DataFrame,
    universe: set[str],
    database: str,
    terms: dict[str, set[str]],
    min_genes_per_term: int,
    max_genes_per_term: int,
    min_overlap: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    target_genes = set(target_frame["gene"].astype(str))
    M = len(universe)
    N = len(target_genes)
    for term, term_genes in terms.items():
        filtered = term_genes & universe
        K = len(filtered)
        if K < min_genes_per_term or K > max_genes_per_term:
            continue
        overlap_genes = target_genes & filtered
        x = len(overlap_genes)
        if x < min_overlap:
            continue
        effect = float(x / N) if N else 0.0
        overlap_frame = target_frame.loc[target_frame["gene"].astype(str).isin(overlap_genes)].copy()
        if "signed_score" in overlap_frame.columns and not overlap_frame["signed_score"].empty:
            signed_mean = float(overlap_frame["signed_score"].mean())
            sign = "positive" if signed_mean >= 0 else "negative"
        else:
            sign = "positive"
        p_value = float(hypergeom.sf(x - 1, M, K, N))
        rows.append(
            {
                "axis_id": axis_id,
                "target_gene": target_gene,
                "database": database,
                "term": term,
                "NES_or_effect": effect,
                "sign": sign,
                "leading_edge_size": x,
                "raw_p_value": p_value,
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values(["raw_p_value", "leading_edge_size", "term"], ascending=[True, False, True]).reset_index(drop=True)


def main() -> None:
    args = build_parser().parse_args()
    config = load_json(resolve_path(args.config))

    signature_path = resolve_path(str(config["input"]["per_target_signature_path"]))
    if not signature_path.exists():
        raise FileNotFoundError(
            f"缺少 per_target_signature 输入：{signature_path}。"
            "当前不允许脚本内部伪造 per-target signature；请先物化真实对象后再运行 consistency audit。"
        )

    output_path = resolve_path(str(config["output"]["table_path"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    candidate_columns = ["axis_id", "target_gene", "gene", "score", "signed_score"]
    top_n = int(config["analysis"]["top_n_per_target"])
    min_genes_per_term = int(config["analysis"]["min_genes_per_term"])
    max_genes_per_term = int(config["analysis"]["max_genes_per_term"])
    min_overlap = int(config["analysis"]["min_overlap"])

    top_frames: dict[tuple[str, str], pd.DataFrame] = {}
    universe: set[str] = set()
    required_columns = {"axis_id", "target_gene", "gene", "score"}
    chunk_reader = pd.read_csv(
        signature_path,
        sep="\t",
        usecols=lambda col: col in candidate_columns,
        compression=None,
        chunksize=250000,
    )
    seen_columns: set[str] | None = None
    for chunk in chunk_reader:
        if seen_columns is None:
            seen_columns = set(chunk.columns)
            missing_columns = sorted(required_columns - seen_columns)
            if missing_columns:
                raise ValueError(f"per_target_signature 缺少字段：{missing_columns}")
        universe.update(chunk["gene"].astype(str))
        top_frames = update_top_target_gene_sets(top_frames, chunk, top_n=top_n)

    if seen_columns is None:
        raise ValueError("per_target_signature 为空。")

    rows: list[pd.DataFrame] = []

    for collection in config["gene_sets"]["collections"]:
        database = str(collection["database"])
        gmt_path = resolve_path(str(collection["gmt_path"]))
        if not gmt_path.exists():
            raise FileNotFoundError(f"缺少 gene set GMT：{gmt_path}")
        terms = load_gmt(gmt_path)
        for (axis_id, target_gene), target_frame in top_frames.items():
            rows.append(
                run_ora(
                    axis_id=axis_id,
                    target_gene=target_gene,
                    target_frame=target_frame,
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
                "target_gene",
                "database",
                "term",
                "NES_or_effect",
                "sign",
                "leading_edge_size",
            ]
        )
    else:
        result = result.loc[
            :,
            [
                "axis_id",
                "target_gene",
                "database",
                "term",
                "NES_or_effect",
                "sign",
                "leading_edge_size",
            ],
        ]

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
