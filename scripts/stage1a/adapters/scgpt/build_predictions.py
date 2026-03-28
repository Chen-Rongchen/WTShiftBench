from __future__ import annotations

import argparse
import json
import random

import anndata as ad
import numpy as np
import pandas as pd
import torch

from scripts.stage1a.adapters.common.runtime import (
    PROJECT_ROOT,
    coalesce_arg,
    compute_train_target_deltas,
    cosine_kernel_predict,
    load_frozen_prediction_space,
    load_run_config,
    resolve_path,
    resolve_torch_device,
)
from scripts.stage1a.benchmark_invariant.catalog import get_formal_dataset_contract
from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    json_dump,
    resolve_project_relative,
    write_matrix,
)


DEFAULT_RAW_PREDICTION_ROOT = PROJECT_ROOT / "data/predictions/stage1a_scgpt_raw"
DEFAULT_MODEL_ROOT = PROJECT_ROOT / "models/pretrained/scgpt_human"
DEFAULT_MODEL_ID = "scgpt_embedding_kernel_formal"
MIN_HELDOUT_COVERAGE = 0.8


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="构造 Stage 1A formal dataset 的 scGPT embedding-kernel predicted_shift.tsv.gz。"
    )
    parser.add_argument("--run-config")
    parser.add_argument("--dataset-id")
    parser.add_argument("--model-id")
    parser.add_argument("--formal-h5ad-path")
    parser.add_argument("--prediction-path")
    parser.add_argument("--metadata-path")
    parser.add_argument("--checkpoint-dir")
    parser.add_argument(
        "--device",
        help="计算设备：cuda / cpu / auto（默认 auto：有 GPU 则用 CUDA）",
    )
    parser.add_argument("--seed", type=int)
    parser.add_argument("--top-k", type=int)
    return parser


def set_random_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def require_file(path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} 不存在: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"{label} 不是文件: {path}")


def main() -> None:
    args = build_parser().parse_args()
    run_config = load_run_config(args.run_config)

    dataset_id = str(coalesce_arg(args.dataset_id, run_config, "dataset_id", "replogle_2022_k562_essential"))
    dataset_contract = get_formal_dataset_contract(dataset_id)
    model_id = str(
        coalesce_arg(
            args.model_id,
            run_config,
            "model_id",
            DEFAULT_MODEL_ID,
        )
    )
    formal_h5ad_path = resolve_path(
        coalesce_arg(
            args.formal_h5ad_path,
            run_config,
            "formal_h5ad_path",
            dataset_contract.path,
        )
    )
    prediction_path = resolve_path(
        coalesce_arg(
            args.prediction_path,
            run_config,
            "prediction_path",
            DEFAULT_RAW_PREDICTION_ROOT / model_id / dataset_id / "predicted_shift.tsv.gz",
        )
    )
    metadata_path = resolve_path(
        coalesce_arg(
            args.metadata_path,
            run_config,
            "metadata_path",
            prediction_path.with_name("adapter_metadata.json"),
        )
    )
    checkpoint_dir = resolve_path(
        coalesce_arg(args.checkpoint_dir, run_config, "checkpoint_dir", DEFAULT_MODEL_ROOT)
    )
    device = resolve_torch_device(str(coalesce_arg(args.device, run_config, "device", "auto")))
    seed = int(coalesce_arg(args.seed, run_config, "seed", 123))
    top_k = int(coalesce_arg(args.top_k, run_config, "top_k", 4))
    set_random_seed(seed)

    heldout_target_order, common_genes = load_frozen_prediction_space(dataset_id)
    heldout_targets = set(heldout_target_order)

    formal_adata = ad.read_h5ad(formal_h5ad_path)
    try:
        train_targets, train_deltas = compute_train_target_deltas(formal_adata, common_genes, heldout_targets)
    finally:
        del formal_adata

    vocab_path = checkpoint_dir / "vocab.json"
    checkpoint_path = checkpoint_dir / "best_model.pt"
    require_file(vocab_path, "scGPT vocab")
    require_file(checkpoint_path, "scGPT checkpoint")
    vocab = json.loads(vocab_path.read_text())
    state = torch.load(checkpoint_path, map_location="cpu")
    if "encoder.embedding.weight" not in state:
        raise KeyError("scGPT checkpoint 缺少 encoder.embedding.weight")
    emb_weight = state["encoder.embedding.weight"].detach().float()
    n_vocab = int(emb_weight.shape[0])
    compute_device = device if device.type == "cuda" else None

    mapped_train_targets = []
    train_mask = []
    for target in train_targets:
        token_id = vocab.get(target)
        is_mapped = token_id is not None
        if is_mapped and not 0 <= int(token_id) < n_vocab:
            raise ValueError(f"scGPT vocab index 越界: target={target}, token_id={token_id}")
        train_mask.append(is_mapped)
        if is_mapped:
            mapped_train_targets.append(target)
    if not mapped_train_targets:
        raise ValueError("scGPT vocab 无法映射任何 train targets。")

    train_deltas = train_deltas[pd.Series(train_mask, dtype=bool).to_numpy()]
    train_token_ids = [int(vocab[target]) for target in mapped_train_targets]
    fallback_delta = train_deltas.mean(axis=0)
    top_k = min(top_k, len(mapped_train_targets))

    if compute_device is not None:
        emb_gpu = emb_weight.to(compute_device)
        train_embeddings_t = emb_gpu[train_token_ids]
        train_deltas_t = torch.as_tensor(train_deltas, dtype=torch.float64, device=compute_device)
    else:
        embedding_np = emb_weight.numpy()
        train_embeddings_np = embedding_np[train_token_ids]

    predicted_rows = []
    mapped_heldout = 0
    for target in heldout_target_order:
        token_id = vocab.get(target)
        if token_id is None:
            predicted_rows.append(fallback_delta)
            continue
        if not 0 <= int(token_id) < n_vocab:
            raise ValueError(f"scGPT vocab index 越界: target={target}, token_id={token_id}")
        mapped_heldout += 1
        tid = int(token_id)
        if compute_device is not None:
            predicted_rows.append(
                cosine_kernel_predict(
                    emb_gpu[tid],
                    train_embeddings_t,
                    train_deltas_t,
                    top_k=top_k,
                    compute_device=device,
                )
            )
        else:
            predicted_rows.append(
                cosine_kernel_predict(
                    query_embedding=embedding_np[tid],
                    ref_embeddings=train_embeddings_np,
                    ref_values=train_deltas,
                    top_k=top_k,
                )
            )
    heldout_coverage = float(mapped_heldout / len(heldout_target_order))
    if heldout_coverage < MIN_HELDOUT_COVERAGE:
        raise ValueError(
            "scGPT heldout target vocab coverage 过低，当前 embedding-kernel adapter "
            f"会退化为均值 delta baseline: coverage={heldout_coverage:.4f}, "
            f"threshold={MIN_HELDOUT_COVERAGE:.4f}"
        )

    predicted_shift = pd.DataFrame(predicted_rows, index=heldout_target_order, columns=common_genes)
    predicted_shift.index.name = "target_gene"
    write_matrix(predicted_shift, prediction_path)
    json_dump(
        {
            "adapter_name": "scgpt_embedding_kernel",
            "adapter_method": "scGPT embedding + cosine kernel regression + mean delta fallback",
            "claim_scope": "不是 scGPT native perturbation prediction model。",
            "dataset_id": dataset_id,
            "model_id": model_id,
            "cell_type": dataset_contract.cell_line,
            "prediction_path": resolve_project_relative(prediction_path),
            "seed": seed,
            "top_k": top_k,
            "heldout_targets_total": len(heldout_target_order),
            "heldout_targets_mapped": mapped_heldout,
            "heldout_vocab_coverage": heldout_coverage,
            "heldout_vocab_coverage_threshold": MIN_HELDOUT_COVERAGE,
            "train_targets_total": len(train_targets),
            "train_targets_mapped": len(mapped_train_targets),
            "device": str(device),
        },
        metadata_path,
    )

    print(f"已写出: {resolve_project_relative(prediction_path)}")
    print(f"已写出: {resolve_project_relative(metadata_path)}")
    print(f"device: {device}")
    print(f"seed: {seed}")
    print(f"dataset_id: {dataset_id}")
    print(f"cell_type: {dataset_contract.cell_line}")
    print("adapter_method: scGPT embedding + cosine kernel regression")
    print(f"train_targets_total: {len(train_targets)}")
    print(f"train_targets_mapped_to_scgpt_vocab: {len(mapped_train_targets)}")
    print(f"heldout_targets_total: {len(heldout_target_order)}")
    print(f"heldout_targets_mapped_to_scgpt_vocab: {mapped_heldout}")


if __name__ == "__main__":
    main()
