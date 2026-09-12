from __future__ import annotations

from pathlib import Path

import torch


CHECKPOINT_FILENAMES = ("model.safetensors", "pytorch_model.bin")


def resolve_geneformer_checkpoint_dir(checkpoint_root: Path) -> Path:
    checkpoint_root = Path(checkpoint_root)
    for filename in CHECKPOINT_FILENAMES:
        if (checkpoint_root / filename).is_file():
            return checkpoint_root
    candidates = sorted(
        {
            path.parent
            for filename in CHECKPOINT_FILENAMES
            for path in checkpoint_root.glob(f"**/{filename}")
        }
    )
    if not candidates:
        expected = " or ".join(CHECKPOINT_FILENAMES)
        raise FileNotFoundError(f"No {expected} found under {checkpoint_root}")
    return candidates[0]


def resolve_geneformer_checkpoint_file(checkpoint_dir: Path) -> Path:
    checkpoint_dir = Path(checkpoint_dir)
    for filename in CHECKPOINT_FILENAMES:
        candidate = checkpoint_dir / filename
        if candidate.is_file():
            return candidate
    expected = " or ".join(CHECKPOINT_FILENAMES)
    raise FileNotFoundError(f"No {expected} found in {checkpoint_dir}")


def load_geneformer_word_embedding_weight(checkpoint_dir: Path) -> torch.Tensor:
    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_file = resolve_geneformer_checkpoint_file(checkpoint_dir)
    if checkpoint_file.suffix == ".safetensors":
        from safetensors.torch import load_file

        state = load_file(str(checkpoint_file), device="cpu")
    else:
        try:
            state = torch.load(checkpoint_file, map_location="cpu", weights_only=True)
        except TypeError:
            # PyTorch < 2.0 does not expose the safer weights_only argument.
            state = torch.load(checkpoint_file, map_location="cpu")
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
    raise KeyError(f"Could not find Geneformer word embedding weight in {checkpoint_file}")
