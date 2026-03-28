from __future__ import annotations

from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
import torch

from wtbench.entrants.base import (
    BaseEntrant,
    EntrantSpec,
    InnerSplitManifest,
    SplitManifest,
    compute_target_shift_matrix,
    fit_adapter_head,
    load_output_gene_space,
    predict_with_adapter_head,
    resolve_project_path,
)
from wtbench.entrants.checkpoints import build_checkpoint_manifest, load_resolved_checkpoint_path
from wtbench.entrants.export import format_predicted_shift


def resolve_geneformer_checkpoint_dir(path: Any) -> Any:
    if (path / "model.safetensors").is_file() or (path / "pytorch_model.bin").is_file():
        return path
    nested = path / "gf-12L-95M-i4096"
    if (nested / "model.safetensors").is_file() or (nested / "pytorch_model.bin").is_file():
        return nested
    raise FileNotFoundError(
        "Geneformer checkpoint 未找到：在下列位置之一需要 model.safetensors 或 pytorch_model.bin："
        f"\n  {path}\n  {nested}"
    )


def load_geneformer_word_embedding_weight(checkpoint_dir):
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
    raise FileNotFoundError(
        f"Geneformer checkpoint 需要 pytorch_model.bin 或 model.safetensors: {checkpoint_dir}"
    )


class GeneformerEntrant(BaseEntrant):
    def __init__(self, context) -> None:
        super().__init__(
            EntrantSpec(
                entrant_name=context.entrant_name,
                entrant_taxonomy="foundation_model_plus_adapter",
                model_provenance={"backbone": "geneformer_gf_12l_95m_i4096", "backbone_freeze": True},
                checkpoint_identity={"registry_key": context.raw_config["checkpoint_key"]},
                preprocessing_identity={
                    "tokenizer": "token_dictionary_gc104M.pkl",
                    "gene_mapping": "gene_name_id_dict_gc104M.pkl",
                    "model_native_feature_preparation": "target-side embedding lookup",
                },
                adapter_recipe={"type": "embedding_plus_adapter", "architecture": "linear"},
                predicted_shift_export_recipe={
                    "native_output": "target-side gene embedding",
                    "projection_export_step": "adapter head -> output gene space",
                    "control_subtraction_position": "fixed in train-target real_shift",
                    "export": "predicted_shift",
                },
                trainable_components={"adapter_head": "trainable", "backbone": "frozen"},
                runtime_config=context.runtime_config,
            ),
            context,
        )
        self._embedding_weight: torch.Tensor | None = None
        self._token_dict: dict[Any, Any] = {}
        self._gene_name_to_ensembl: dict[str, str] = {}

    def load_checkpoint_or_initialize(self) -> None:
        registry_path = resolve_project_path(self.context.raw_config["checkpoint_registry_ref"])
        if registry_path is None:
            raise ValueError("checkpoint_registry_ref 不能为空。")
        entry, checkpoint_root = load_resolved_checkpoint_path(
            registry_path,
            str(self.context.raw_config["checkpoint_key"]),
        )
        checkpoint_dir = resolve_geneformer_checkpoint_dir(checkpoint_root)
        asset_root = resolve_project_path(self.context.runtime_config["asset_root"])
        if asset_root is None:
            raise ValueError("Geneformer asset_root 不能为空。")
        token_dict_path = asset_root / "token_dictionary_gc104M.pkl"
        gene_name_to_ensembl_path = asset_root / "gene_name_id_dict_gc104M.pkl"
        if not token_dict_path.is_file():
            raise FileNotFoundError(f"Geneformer token_dictionary 不存在: {token_dict_path}")
        if not gene_name_to_ensembl_path.is_file():
            raise FileNotFoundError(f"Geneformer gene mapping 不存在: {gene_name_to_ensembl_path}")
        self._embedding_weight = load_geneformer_word_embedding_weight(checkpoint_dir)
        self._token_dict = pd.read_pickle(token_dict_path)
        self._gene_name_to_ensembl = pd.read_pickle(gene_name_to_ensembl_path)
        self._checkpoint_manifest = build_checkpoint_manifest(
            registry_path=registry_path,
            checkpoint_key=str(self.context.raw_config["checkpoint_key"]),
            resolved_path=checkpoint_dir,
            entry=entry,
        )
        self._checkpoint_manifest.update(
            {
                "checkpoint_root": str(checkpoint_root),
                "token_dictionary_path": str(token_dict_path),
                "gene_name_mapping_path": str(gene_name_to_ensembl_path),
                "embedding_shape": list(self._embedding_weight.shape),
                "workflow_type": "embedding_plus_adapter",
                "model_load_device": str(self.context.device),
            }
        )

    def prepare_model_native_inputs(
        self,
        split_manifest: SplitManifest,
        inner_split_manifest: InnerSplitManifest,
    ) -> dict[str, Any]:
        if self._embedding_weight is None:
            raise RuntimeError("Geneformer checkpoint 尚未加载。")
        formal_adata = ad.read_h5ad(self.context.dataset_contract.path)
        _, output_genes = load_output_gene_space(self.context.dataset_id)
        train_shift = compute_target_shift_matrix(formal_adata, output_genes, list(split_manifest.train_targets))
        fallback_shift = train_shift.mean(axis=0).astype(np.float32, copy=False)
        vocab_size = int(self._embedding_weight.shape[0])

        mapped_train_targets: list[str] = []
        mapped_train_indices: list[int] = []
        train_token_ids: list[int] = []
        unmapped_train_targets: list[str] = []
        for idx, target in enumerate(split_manifest.train_targets):
            ensembl_id = self._gene_name_to_ensembl.get(target)
            token_id = self._token_dict.get(ensembl_id) if ensembl_id is not None else None
            if token_id is None:
                unmapped_train_targets.append(target)
                continue
            if not 0 <= int(token_id) < vocab_size:
                raise ValueError(f"Geneformer token id 越界: target={target}, token_id={token_id}")
            mapped_train_targets.append(target)
            mapped_train_indices.append(idx)
            train_token_ids.append(int(token_id))
        if not mapped_train_targets:
            raise ValueError("Geneformer train split 中没有可映射的 targets。")

        heldout_token_ids: list[int | None] = []
        mapped_heldout_targets: list[str] = []
        unmapped_heldout_targets: list[str] = []
        for target in split_manifest.heldout_targets:
            ensembl_id = self._gene_name_to_ensembl.get(target)
            token_id = self._token_dict.get(ensembl_id) if ensembl_id is not None else None
            if token_id is None:
                heldout_token_ids.append(None)
                unmapped_heldout_targets.append(target)
                continue
            if not 0 <= int(token_id) < vocab_size:
                raise ValueError(f"Geneformer token id 越界: target={target}, token_id={token_id}")
            heldout_token_ids.append(int(token_id))
            mapped_heldout_targets.append(target)

        train_features = self._embedding_weight[train_token_ids].detach().cpu().numpy().astype(np.float32, copy=False)
        train_targets = train_shift[np.asarray(mapped_train_indices, dtype=int)]
        inner_train_set = set(inner_split_manifest.inner_train_targets)
        inner_val_set = set(inner_split_manifest.inner_val_targets)
        inner_train_positions = [idx for idx, target in enumerate(mapped_train_targets) if target in inner_train_set]
        inner_val_positions = [idx for idx, target in enumerate(mapped_train_targets) if target in inner_val_set]
        if not inner_train_positions or not inner_val_positions:
            raise ValueError("Geneformer inner split 无法同时覆盖 inner_train 与 inner_val。")
        inner_train_features = train_features[np.asarray(inner_train_positions, dtype=int)]
        inner_train_shift = train_targets[np.asarray(inner_train_positions, dtype=int)]
        inner_val_features = train_features[np.asarray(inner_val_positions, dtype=int)]
        inner_val_shift = train_targets[np.asarray(inner_val_positions, dtype=int)]
        inner_train_targets = [mapped_train_targets[idx] for idx in inner_train_positions]
        inner_val_targets = [mapped_train_targets[idx] for idx in inner_val_positions]
        mapped_heldout_positions = [idx for idx, token_id in enumerate(heldout_token_ids) if token_id is not None]
        mapped_heldout_features = (
            self._embedding_weight[[int(heldout_token_ids[idx]) for idx in mapped_heldout_positions]]
            .detach()
            .cpu()
            .numpy()
            .astype(np.float32, copy=False)
            if mapped_heldout_positions
            else np.zeros((0, train_features.shape[1]), dtype=np.float32)
        )

        heldout_coverage = float(len(mapped_heldout_targets) / max(1, len(split_manifest.heldout_targets)))
        train_coverage = float(len(mapped_train_targets) / max(1, len(split_manifest.train_targets)))
        self._feature_manifest = {
            "feature_type": "target_side_gene_embedding",
            "workflow_type": "embedding_plus_adapter",
            "train_targets_total": len(split_manifest.train_targets),
            "train_targets_mapped": len(mapped_train_targets),
            "train_tokenizer_coverage": train_coverage,
            "train_targets_unmapped_sample": unmapped_train_targets[:20],
            "heldout_targets_total": len(split_manifest.heldout_targets),
            "heldout_targets_mapped": len(mapped_heldout_targets),
            "heldout_tokenizer_coverage": heldout_coverage,
            "heldout_targets_unmapped_sample": unmapped_heldout_targets[:20],
            "output_gene_count": len(output_genes),
            "fallback_policy_for_unmapped_heldout": "mean_train_real_shift",
        }
        return {
            "output_genes": output_genes,
            "train_features": train_features,
            "train_shift": train_targets,
            "heldout_features": mapped_heldout_features,
            "heldout_positions": mapped_heldout_positions,
            "heldout_targets": list(split_manifest.heldout_targets),
            "fallback_shift": fallback_shift,
            "inner_train_features": inner_train_features,
            "inner_train_shift": inner_train_shift,
            "inner_train_targets": inner_train_targets,
            "inner_val_features": inner_val_features,
            "inner_val_shift": inner_val_shift,
            "inner_val_targets": inner_val_targets,
        }

    def fit_on_train_split(self, prepared_inputs: dict[str, Any]) -> dict[str, Any]:
        model, training_manifest = fit_adapter_head(
            train_features=prepared_inputs["inner_train_features"],
            train_targets=prepared_inputs["inner_train_shift"],
            val_features=prepared_inputs["inner_val_features"],
            val_targets=prepared_inputs["inner_val_shift"],
            runtime_config=self.context.runtime_config,
            device=self.context.device,
            seed=int(self.context.runtime_config.get("training_seed", self.context.split_seed)),
            train_target_names=prepared_inputs["inner_train_targets"],
            val_target_names=prepared_inputs["inner_val_targets"],
        )
        self._feature_manifest["adapter_training"] = training_manifest
        return {
            "adapter_head": model,
            "selected_epoch": int(training_manifest["best_epoch"]),
            "selected_checkpoint_label": "best_inner_val_epoch",
            "inner_val_epoch_grid_rows": training_manifest["epoch_grid_rows"],
        }

    def predict_for_heldout_targets(
        self,
        prepared_inputs: dict[str, Any],
        fitted_state: dict[str, Any],
    ) -> pd.DataFrame:
        heldout_targets = prepared_inputs["heldout_targets"]
        prediction = np.repeat(
            prepared_inputs["fallback_shift"][None, :],
            repeats=len(heldout_targets),
            axis=0,
        ).astype(np.float32, copy=False)
        if prepared_inputs["heldout_features"].shape[0] > 0:
            mapped_prediction = predict_with_adapter_head(
                model=fitted_state["adapter_head"],
                features=prepared_inputs["heldout_features"],
                device=self.context.device,
                batch_size=int(self.context.runtime_config["batch_size"]),
            )
            prediction[np.asarray(prepared_inputs["heldout_positions"], dtype=int)] = mapped_prediction
        return format_predicted_shift(
            target_order=heldout_targets,
            gene_names=prepared_inputs["output_genes"],
            values=prediction,
        )
