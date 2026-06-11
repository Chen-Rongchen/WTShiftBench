from __future__ import annotations

from pathlib import Path

import torch


def resolve_geneformer_checkpoint_dir(checkpoint_root: Path) -> Path:
    checkpoint_root = Path(checkpoint_root)
    if (checkpoint_root / "pytorch_model.bin").exists():
        return checkpoint_root
    candidates = sorted(checkpoint_root.glob("**/pytorch_model.bin"))
    if not candidates:
        raise FileNotFoundError(f"No pytorch_model.bin found under {checkpoint_root}")
    return candidates[0].parent


def load_geneformer_word_embedding_weight(checkpoint_dir: Path) -> torch.Tensor:
    checkpoint_dir = Path(checkpoint_dir)
    state = torch.load(checkpoint_dir / "pytorch_model.bin", map_location="cpu")
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    candidate_keys = [
        "bert.embeddings.word_embeddings.weight",
        "embeddings.word_embeddings.weight",
        "geneformer.embeddings.word_embeddings.weight",
    ]
    for key in candidate_keys:
        if key in state:
            return state[key].detach().float().cpu()
    for key, value in state.items():
        if key.endswith("word_embeddings.weight"):
            return value.detach().float().cpu()
    raise KeyError(f"Could not find Geneformer word embedding weight in {checkpoint_dir / 'pytorch_model.bin'}")
