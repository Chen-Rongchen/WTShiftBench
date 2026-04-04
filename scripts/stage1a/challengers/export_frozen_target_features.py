from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path

import anndata as ad
import pandas as pd
import torch

from scripts.stage1a.benchmark_invariant.catalog import load_formal_dataset_contracts
from scripts.stage1a.challengers.common import (
    DEFAULT_FEATURE_REGISTRY_PATH,
    load_feature_registry,
    resolve_path,
)


DEFAULT_SCGPT_CHECKPOINT_DIR = Path("models/pretrained/scgpt_human")
DEFAULT_GENEFORMER_CHECKPOINT_DIR = Path("models/pretrained/geneformer_gf_12l_95m_i4096")
DEFAULT_GENEFORMER_ASSET_DIR = Path("models/pretrained/geneformer_assets/geneformer")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="导出并冻结当前 Stage 1A challenger 允许使用的 target-side features。")
    parser.add_argument(
        "--feature-registry",
        default=str(DEFAULT_FEATURE_REGISTRY_PATH),
        help="feature registry JSON 路径。",
    )
    return parser


def collect_current_smoke_targets() -> list[str]:
    targets: set[str] = set()
    for contract in load_formal_dataset_contracts(include_auxiliary=True):
        adata = ad.read_h5ad(contract.path)
        try:
            obs = adata.obs.loc[:, ["is_control", "target_gene"]].copy()
            obs["is_control"] = obs["is_control"].astype(bool)
            obs["target_gene"] = obs["target_gene"].astype("string").fillna("")
            dataset_targets = {
                str(target)
                for target in obs.loc[~obs["is_control"], "target_gene"].tolist()
                if str(target).strip()
            }
            targets.update(dataset_targets)
        finally:
            del adata
    if not targets:
        raise ValueError("当前 smoke target 集合为空。")
    return sorted(targets)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_feature_matrix(frame: pd.DataFrame, output_path: Path) -> None:
    ensure_parent(output_path)
    frame.to_csv(output_path, sep="\t", compression="gzip", index=True, index_label="target_gene")


def write_summary(payload: dict[str, object], output_path: Path) -> None:
    ensure_parent(output_path)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_geneformer_checkpoint_dir(path: Path) -> Path:
    if (path / "model.safetensors").is_file() or (path / "pytorch_model.bin").is_file():
        return path
    nested = path / "gf-12L-95M-i4096"
    if (nested / "model.safetensors").is_file() or (nested / "pytorch_model.bin").is_file():
        return nested
    raise FileNotFoundError(f"Geneformer checkpoint 未找到: {path}")


def load_geneformer_word_embedding_weight(checkpoint_dir: Path) -> torch.Tensor:
    key = "bert.embeddings.word_embeddings.weight"
    bin_path = checkpoint_dir / "pytorch_model.bin"
    safe_path = checkpoint_dir / "model.safetensors"
    if bin_path.is_file():
        state = torch.load(bin_path, map_location="cpu")
        if key not in state:
            raise KeyError(f"Geneformer checkpoint 缺少 {key}")
        return state[key].detach().float()
    if safe_path.is_file():
        from safetensors.torch import load_file

        state = load_file(str(safe_path))
        if key not in state:
            raise KeyError(f"Geneformer checkpoint 缺少 {key}")
        return state[key].detach().float()
    raise FileNotFoundError(f"Geneformer checkpoint 需要 pytorch_model.bin 或 model.safetensors: {checkpoint_dir}")


def export_scgpt_features(targets: list[str], output_path: Path) -> dict[str, object]:
    checkpoint_dir = resolve_path(DEFAULT_SCGPT_CHECKPOINT_DIR)
    vocab_path = checkpoint_dir / "vocab.json"
    checkpoint_path = checkpoint_dir / "best_model.pt"
    vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
    state = torch.load(checkpoint_path, map_location="cpu")
    emb = state["encoder.embedding.weight"].detach().cpu().numpy()

    rows: list[list[float]] = []
    kept_targets: list[str] = []
    missing_targets: list[str] = []
    for target in targets:
        token_id = vocab.get(target)
        if token_id is None:
            missing_targets.append(target)
            continue
        kept_targets.append(target)
        rows.append(emb[int(token_id)].astype(float).tolist())

    if not kept_targets:
        raise ValueError("scGPT 当前 smoke targets 无可导出 embedding。")
    frame = pd.DataFrame(rows, index=kept_targets)
    frame.index.name = "target_gene"
    frame.columns = [f"feat_{idx:04d}" for idx in range(frame.shape[1])]
    write_feature_matrix(frame, output_path)
    return {
        "feature_id": "scgpt_gene_embedding_human",
        "n_targets_total": len(targets),
        "n_targets_exported": len(kept_targets),
        "coverage_on_current_smoke": float(len(kept_targets) / len(targets)),
        "missing_targets_sample": missing_targets[:20],
        "embedding_dim": int(frame.shape[1]),
        "source_checkpoint_dir": str(DEFAULT_SCGPT_CHECKPOINT_DIR),
    }


def export_geneformer_features(targets: list[str], output_path: Path) -> dict[str, object]:
    checkpoint_root = resolve_path(DEFAULT_GENEFORMER_CHECKPOINT_DIR)
    asset_root = resolve_path(DEFAULT_GENEFORMER_ASSET_DIR)
    checkpoint_dir = resolve_geneformer_checkpoint_dir(checkpoint_root)
    token_dict = pd.read_pickle(asset_root / "token_dictionary_gc104M.pkl")
    gene_name_to_ensembl = pd.read_pickle(asset_root / "gene_name_id_dict_gc104M.pkl")
    emb = load_geneformer_word_embedding_weight(checkpoint_dir).cpu().numpy()

    rows: list[list[float]] = []
    kept_targets: list[str] = []
    missing_targets: list[str] = []
    for target in targets:
        ensembl_id = gene_name_to_ensembl.get(target)
        token_id = token_dict.get(ensembl_id) if ensembl_id is not None else None
        if token_id is None:
            missing_targets.append(target)
            continue
        kept_targets.append(target)
        rows.append(emb[int(token_id)].astype(float).tolist())

    if not kept_targets:
        raise ValueError("Geneformer 当前 smoke targets 无可导出 embedding。")
    frame = pd.DataFrame(rows, index=kept_targets)
    frame.index.name = "target_gene"
    frame.columns = [f"feat_{idx:04d}" for idx in range(frame.shape[1])]
    write_feature_matrix(frame, output_path)
    return {
        "feature_id": "geneformer_gene_embedding_gc104m",
        "n_targets_total": len(targets),
        "n_targets_exported": len(kept_targets),
        "coverage_on_current_smoke": float(len(kept_targets) / len(targets)),
        "missing_targets_sample": missing_targets[:20],
        "embedding_dim": int(frame.shape[1]),
        "source_checkpoint_dir": str(DEFAULT_GENEFORMER_CHECKPOINT_DIR),
        "source_asset_root": str(DEFAULT_GENEFORMER_ASSET_DIR),
    }


def hashed_chargram_vector(target: str, dim: int) -> list[float]:
    normalized = f"^{target.lower()}$"
    grams = [normalized[idx : idx + 3] for idx in range(max(1, len(normalized) - 2))]
    vector = [0.0] * dim
    for gram in grams:
        digest = hashlib.sha256(gram.encode("utf-8")).digest()
        position = int.from_bytes(digest[:4], byteorder="little", signed=False) % dim
        vector[position] += 1.0
    norm = sum(value * value for value in vector) ** 0.5
    if norm > 0.0:
        vector = [value / norm for value in vector]
    return vector


def export_symbol_chargram_features(targets: list[str], output_path: Path, dim: int = 256) -> dict[str, object]:
    rows = [hashed_chargram_vector(target, dim) for target in targets]
    frame = pd.DataFrame(rows, index=targets)
    frame.index.name = "target_gene"
    frame.columns = [f"feat_{idx:04d}" for idx in range(frame.shape[1])]
    write_feature_matrix(frame, output_path)
    return {
        "feature_id": "gene_symbol_chargram_v1",
        "n_targets_total": len(targets),
        "n_targets_exported": len(targets),
        "coverage_on_current_smoke": 1.0,
        "missing_targets_sample": [],
        "embedding_dim": int(frame.shape[1]),
        "source_rule": "lowercase target_gene with boundary markers, hashed trigram bag, L2 normalized",
    }


def main() -> None:
    args = build_parser().parse_args()
    registry = load_feature_registry(resolve_path(args.feature_registry))
    targets = collect_current_smoke_targets()

    summaries: list[dict[str, object]] = []
    for entry in registry:
        if entry.feature_id == "scgpt_gene_embedding_human":
            summary = export_scgpt_features(targets, entry.source_path)
        elif entry.feature_id == "geneformer_gene_embedding_gc104m":
            summary = export_geneformer_features(targets, entry.source_path)
        elif entry.feature_id == "gene_symbol_chargram_v1":
            summary = export_symbol_chargram_features(targets, entry.source_path)
        else:
            raise ValueError(f"当前 exporter 未实现 feature_id={entry.feature_id}")
        summary_path = entry.source_path.with_name(f"{entry.source_path.stem}_summary.json")
        write_summary(summary, summary_path)
        summaries.append(summary)
        print(f"已写出: {entry.source_path}")
        print(f"已写出: {summary_path}")

    manifest_path = resolve_path("reports/stage1a/challengers/feature_export_manifest.json")
    write_summary(
        {
            "stage": "stage1a_challenger_feature_export",
            "n_current_smoke_targets": len(targets),
            "targets_sample": targets[:20],
            "features": summaries,
        },
        manifest_path,
    )
    print(f"已写出: {manifest_path}")


if __name__ == "__main__":
    main()
