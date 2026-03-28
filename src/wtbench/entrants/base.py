from __future__ import annotations

import argparse
import json
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
import torch
import yaml
from scipy import sparse

from scripts.stage1a.benchmark_invariant.catalog import PROJECT_ROOT, get_formal_dataset_contract
from scripts.stage1a.benchmark_invariant.prediction_eval_common import (
    evaluate_prediction_frame,
    json_dump,
    load_main_aligned_truth_entry,
    read_matrix,
)


@dataclass(frozen=True)
class EntrantSpec:
    entrant_name: str
    entrant_taxonomy: str
    model_provenance: dict[str, Any]
    checkpoint_identity: dict[str, Any]
    preprocessing_identity: dict[str, Any]
    adapter_recipe: dict[str, Any]
    predicted_shift_export_recipe: dict[str, Any]
    trainable_components: dict[str, Any]
    runtime_config: dict[str, Any]


@dataclass(frozen=True)
class SplitManifest:
    dataset_id: str
    split_seed: int
    train_targets: tuple[str, ...]
    heldout_targets: tuple[str, ...]
    split_dir: Path
    train_path: Path
    heldout_path: Path
    manifest_path: Path


@dataclass(frozen=True)
class InnerSplitManifest:
    dataset_id: str
    outer_split_seed: int
    inner_seed: int
    inner_val_fraction: float
    inner_train_targets: tuple[str, ...]
    inner_val_targets: tuple[str, ...]
    split_dir: Path
    inner_train_path: Path
    inner_val_path: Path
    manifest_path: Path


@dataclass(frozen=True)
class EntrantContext:
    config_path: Path
    raw_config: dict[str, Any]
    dataset_id: str
    split_seed: int
    output_dir: Path
    runtime_config: dict[str, Any]
    requested_device: str
    device: torch.device
    timestamp: str

    @property
    def entrant_name(self) -> str:
        return str(self.raw_config["entrant_name"])

    @property
    def dataset_contract(self):
        return get_formal_dataset_contract(self.dataset_id)


def ensure_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} 必须是键值映射。")
    return value


def resolve_project_path(path_value: str | Path | None) -> Path | None:
    if path_value is None:
        return None
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_mapping_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(text) if text.strip() else {}
    else:
        payload = yaml.safe_load(text) or {}
    return ensure_mapping(payload, str(path))


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    return load_mapping_config(path)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def mean_expression(matrix: Any) -> np.ndarray:
    if getattr(matrix, "shape", None) is not None and matrix.shape[0] == 0:
        raise ValueError("空细胞集合无法计算 pseudobulk。")
    if sparse.issparse(matrix):
        values = np.asarray(matrix.mean(axis=0)).ravel()
    else:
        values = np.asarray(matrix.mean(axis=0)).ravel()
    return values.astype(np.float64, copy=False)


def set_global_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def resolve_torch_device(device: str | None) -> torch.device:
    if device in {None, "", "auto"}:
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    resolved = torch.device(device)
    if resolved.type == "cuda" and not torch.cuda.is_available():
        raise ValueError(f"请求 device={device}，但当前环境不可用 CUDA。")
    return resolved


def load_output_gene_space(dataset_id: str) -> tuple[pd.DataFrame, list[str]]:
    truth_entry = load_main_aligned_truth_entry(dataset_id)
    truth = read_matrix(truth_entry.path)
    return truth, list(truth.columns)


def compute_target_shift_matrix(
    formal_adata: ad.AnnData,
    output_genes: list[str],
    target_order: list[str] | tuple[str, ...],
) -> np.ndarray:
    obs = formal_adata.obs.copy()
    obs["is_control"] = obs["is_control"].astype(bool)
    obs["target_gene"] = obs["target_gene"].astype("string").fillna("")
    gene_index = pd.Index(formal_adata.var.index.astype(str))
    gene_positions = gene_index.get_indexer(output_genes)
    if (gene_positions < 0).any():
        missing = [output_genes[i] for i, pos in enumerate(gene_positions) if pos < 0][:10]
        raise ValueError(f"formal source 缺少输出基因: {missing}")
    control_values = mean_expression(formal_adata.X[obs["is_control"].to_numpy()])
    rows: list[np.ndarray] = []
    for target in target_order:
        target_mask = (~obs["is_control"]).to_numpy() & obs["target_gene"].eq(target).fillna(False).to_numpy(dtype=bool)
        if not target_mask.any():
            raise ValueError(f"formal source 中缺少 target={target} 的 perturbation cells。")
        target_values = mean_expression(formal_adata.X[target_mask])
        rows.append((target_values - control_values)[gene_positions])
    return np.asarray(rows, dtype=np.float32)


def build_target_level_split_manifest(
    dataset_id: str,
    split_seed: int,
    *,
    heldout_fraction: float = 0.2,
) -> SplitManifest:
    split_dir = PROJECT_ROOT / "artifacts" / "splits" / dataset_id / f"seed{split_seed}"
    train_path = split_dir / "train_targets.txt"
    heldout_path = split_dir / "heldout_targets.txt"
    manifest_path = split_dir / "manifest.json"
    if train_path.exists() and heldout_path.exists():
        train_targets = tuple(
            line.strip() for line in train_path.read_text(encoding="utf-8").splitlines() if line.strip()
        )
        heldout_targets = tuple(
            line.strip() for line in heldout_path.read_text(encoding="utf-8").splitlines() if line.strip()
        )
        return SplitManifest(
            dataset_id=dataset_id,
            split_seed=split_seed,
            train_targets=train_targets,
            heldout_targets=heldout_targets,
            split_dir=split_dir,
            train_path=train_path,
            heldout_path=heldout_path,
            manifest_path=manifest_path,
        )

    truth, _ = load_output_gene_space(dataset_id)
    truth_targets = set(truth.index.astype(str).tolist())
    formal_adata = ad.read_h5ad(get_formal_dataset_contract(dataset_id).path)
    try:
        obs = formal_adata.obs.copy()
        obs["is_control"] = obs["is_control"].astype(bool)
        obs["target_gene"] = obs["target_gene"].astype("string").fillna("")
        candidate_targets = sorted(
            target
            for target in obs.loc[~obs["is_control"], "target_gene"].dropna().astype(str).unique().tolist()
            if target and target in truth_targets
        )
    finally:
        del formal_adata
    if len(candidate_targets) < 2:
        raise ValueError(f"{dataset_id} 可切分的 target 数量不足: {len(candidate_targets)}")

    rng = np.random.default_rng(split_seed)
    shuffled = list(np.asarray(candidate_targets, dtype=object)[rng.permutation(len(candidate_targets))])
    heldout_count = max(1, int(round(len(candidate_targets) * heldout_fraction)))
    heldout_count = min(heldout_count, len(candidate_targets) - 1)
    heldout_targets = tuple(sorted(str(target) for target in shuffled[:heldout_count]))
    train_targets = tuple(sorted(str(target) for target in shuffled[heldout_count:]))

    split_dir.mkdir(parents=True, exist_ok=True)
    train_path.write_text("\n".join(train_targets) + "\n", encoding="utf-8")
    heldout_path.write_text("\n".join(heldout_targets) + "\n", encoding="utf-8")
    json_dump(
        {
            "dataset_id": dataset_id,
            "split_seed": split_seed,
            "split_type": "target_level",
            "heldout_fraction": heldout_fraction,
            "candidate_target_count": len(candidate_targets),
            "train_target_count": len(train_targets),
            "heldout_target_count": len(heldout_targets),
        },
        manifest_path,
    )
    return SplitManifest(
        dataset_id=dataset_id,
        split_seed=split_seed,
        train_targets=train_targets,
        heldout_targets=heldout_targets,
        split_dir=split_dir,
        train_path=train_path,
        heldout_path=heldout_path,
        manifest_path=manifest_path,
    )


def build_inner_target_level_split_manifest(
    split_manifest: SplitManifest,
    *,
    inner_seed: int = 11,
    inner_val_fraction: float = 0.2,
) -> InnerSplitManifest:
    split_dir = split_manifest.split_dir / f"inner_seed{inner_seed}"
    inner_train_path = split_dir / "inner_train_targets.txt"
    inner_val_path = split_dir / "inner_val_targets.txt"
    manifest_path = split_dir / "inner_manifest.json"
    if inner_train_path.exists() and inner_val_path.exists():
        inner_train_targets = tuple(
            line.strip() for line in inner_train_path.read_text(encoding="utf-8").splitlines() if line.strip()
        )
        inner_val_targets = tuple(
            line.strip() for line in inner_val_path.read_text(encoding="utf-8").splitlines() if line.strip()
        )
        return InnerSplitManifest(
            dataset_id=split_manifest.dataset_id,
            outer_split_seed=split_manifest.split_seed,
            inner_seed=inner_seed,
            inner_val_fraction=inner_val_fraction,
            inner_train_targets=inner_train_targets,
            inner_val_targets=inner_val_targets,
            split_dir=split_dir,
            inner_train_path=inner_train_path,
            inner_val_path=inner_val_path,
            manifest_path=manifest_path,
        )

    outer_train_targets = list(split_manifest.train_targets)
    if len(outer_train_targets) < 2:
        raise ValueError("outer_train_targets 数量不足，无法构造 inner train/val split。")
    rng = np.random.default_rng(inner_seed)
    shuffled = list(np.asarray(outer_train_targets, dtype=object)[rng.permutation(len(outer_train_targets))])
    inner_val_count = max(1, int(round(len(shuffled) * inner_val_fraction)))
    inner_val_count = min(inner_val_count, len(shuffled) - 1)
    inner_val_targets = tuple(sorted(str(target) for target in shuffled[:inner_val_count]))
    inner_train_targets = tuple(sorted(str(target) for target in shuffled[inner_val_count:]))

    split_dir.mkdir(parents=True, exist_ok=True)
    inner_train_path.write_text("\n".join(inner_train_targets) + "\n", encoding="utf-8")
    inner_val_path.write_text("\n".join(inner_val_targets) + "\n", encoding="utf-8")
    json_dump(
        {
            "dataset_id": split_manifest.dataset_id,
            "outer_split_seed": split_manifest.split_seed,
            "split_type": "target_level_inner_validation",
            "inner_seed": inner_seed,
            "inner_val_fraction": inner_val_fraction,
            "outer_train_target_count": len(outer_train_targets),
            "inner_train_target_count": len(inner_train_targets),
            "inner_val_target_count": len(inner_val_targets),
        },
        manifest_path,
    )
    return InnerSplitManifest(
        dataset_id=split_manifest.dataset_id,
        outer_split_seed=split_manifest.split_seed,
        inner_seed=inner_seed,
        inner_val_fraction=inner_val_fraction,
        inner_train_targets=inner_train_targets,
        inner_val_targets=inner_val_targets,
        split_dir=split_dir,
        inner_train_path=inner_train_path,
        inner_val_path=inner_val_path,
        manifest_path=manifest_path,
    )


class AdapterHead(torch.nn.Module):
    def __init__(self, input_dim: int, output_dim: int, hidden_dim: int = 0) -> None:
        super().__init__()
        if hidden_dim > 0:
            self.layers = torch.nn.Sequential(
                torch.nn.Linear(input_dim, hidden_dim),
                torch.nn.GELU(),
                torch.nn.Linear(hidden_dim, output_dim),
            )
        else:
            self.layers = torch.nn.Linear(input_dim, output_dim)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.layers(features)


def fit_adapter_head(
    *,
    train_features: np.ndarray,
    train_targets: np.ndarray,
    val_features: np.ndarray | None,
    val_targets: np.ndarray | None,
    runtime_config: dict[str, Any],
    device: torch.device,
    seed: int,
    train_target_names: list[str] | None = None,
    val_target_names: list[str] | None = None,
) -> tuple[AdapterHead, dict[str, Any]]:
    if train_features.shape[0] != train_targets.shape[0]:
        raise ValueError("adapter 训练特征与目标行数不一致。")
    if train_features.shape[0] == 0:
        raise ValueError("adapter 训练样本为空。")

    set_global_seed(seed)
    hidden_dim = int(runtime_config.get("adapter_hidden_dim", 0))
    learning_rate = float(runtime_config["learning_rate"])
    weight_decay = float(runtime_config["weight_decay"])
    batch_size = max(1, int(runtime_config["batch_size"]))
    max_epochs = max(1, int(runtime_config["max_epochs"]))
    early_stopping_enabled = bool(runtime_config.get("early_stopping_enabled", True))
    early_stopping_patience = max(1, int(runtime_config.get("early_stopping_patience", 3)))
    optimizer_name = str(runtime_config["optimizer"]).lower()
    metric_tie_tolerance = float(runtime_config.get("inner_metric_tie_tolerance", 1.0e-4))
    selection_topk = int(runtime_config.get("selection_topk", 50))

    n_samples = int(train_features.shape[0])
    if train_target_names is None:
        train_target_names = [f"train_target_{idx}" for idx in range(n_samples)]
    if len(train_target_names) != n_samples:
        raise ValueError("train_target_names 与训练样本数不一致。")
    train_indices = np.arange(n_samples, dtype=int)
    val_indices = np.arange(0, dtype=int)
    if val_target_names:
        val_indices = np.arange(len(val_target_names), dtype=int)

    feature_tensor = torch.as_tensor(train_features, dtype=torch.float32, device=device)
    target_tensor = torch.as_tensor(train_targets, dtype=torch.float32, device=device)
    model = AdapterHead(
        input_dim=int(train_features.shape[1]),
        output_dim=int(train_targets.shape[1]),
        hidden_dim=hidden_dim,
    ).to(device)

    if optimizer_name == "adamw":
        optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    elif optimizer_name == "adam":
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    else:
        raise ValueError(f"不支持的 optimizer={runtime_config['optimizer']}")

    best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    best_epoch = 0
    best_selection_score = {
        "pearson_mean": float("-inf"),
        "top50_jaccard_mean": float("-inf"),
        "rmse_mean": float("inf"),
    }
    patience_left = early_stopping_patience
    history: list[dict[str, float]] = []
    epoch_grid_rows: list[dict[str, object]] = []
    val_feature_tensor = None
    val_target_tensor = None
    if val_features is not None and val_targets is not None and val_target_names:
        val_feature_tensor = torch.as_tensor(val_features, dtype=torch.float32, device=device)
        val_target_tensor = torch.as_tensor(val_targets, dtype=torch.float32, device=device)

    def should_replace_best(candidate: dict[str, float], incumbent: dict[str, float], tolerance: float) -> bool:
        if candidate["pearson_mean"] > incumbent["pearson_mean"] + tolerance:
            return True
        if abs(candidate["pearson_mean"] - incumbent["pearson_mean"]) <= tolerance:
            if candidate["top50_jaccard_mean"] > incumbent["top50_jaccard_mean"] + tolerance:
                return True
            if abs(candidate["top50_jaccard_mean"] - incumbent["top50_jaccard_mean"]) <= tolerance:
                if candidate["rmse_mean"] < incumbent["rmse_mean"] - tolerance:
                    return True
        return False

    for epoch in range(1, max_epochs + 1):
        model.train()
        epoch_losses: list[float] = []
        for start in range(0, len(train_indices), batch_size):
            batch_index = train_indices[start : start + batch_size]
            batch_features = feature_tensor[batch_index]
            batch_targets = target_tensor[batch_index]
            optimizer.zero_grad(set_to_none=True)
            prediction = model(batch_features)
            loss = torch.nn.functional.mse_loss(prediction, batch_targets)
            loss.backward()
            optimizer.step()
            epoch_losses.append(float(loss.detach().cpu().item()))

        train_loss = float(np.mean(epoch_losses)) if epoch_losses else 0.0
        val_loss = train_loss
        val_metrics = {
            "pearson_mean": float("nan"),
            "top50_jaccard_mean": float("nan"),
            "rmse_mean": float("nan"),
        }
        if val_feature_tensor is not None and val_target_tensor is not None:
            model.eval()
            with torch.no_grad():
                prediction = model(val_feature_tensor)
                val_loss = float(torch.nn.functional.mse_loss(prediction, val_target_tensor).detach().cpu().item())
            val_prediction_frame = pd.DataFrame(
                prediction.detach().cpu().numpy().astype(np.float32, copy=False),
                index=list(val_target_names),
            )
            val_truth_frame = pd.DataFrame(
                val_target_tensor.detach().cpu().numpy().astype(np.float32, copy=False),
                index=list(val_target_names),
            )
            val_prediction_frame.columns = [f"g{idx}" for idx in range(val_prediction_frame.shape[1])]
            val_truth_frame.columns = list(val_prediction_frame.columns)
            _, aggregate_scores = evaluate_prediction_frame(
                prediction=val_prediction_frame,
                truth=val_truth_frame,
                topk_values=[selection_topk],
            )
            val_metrics = {
                "pearson_mean": float(aggregate_scores["pearson_mean"]),
                "top50_jaccard_mean": float(aggregate_scores[f"top{selection_topk}_jaccard_mean"]),
                "rmse_mean": float(aggregate_scores["rmse_mean"]),
            }
        history.append(
            {
                "epoch": float(epoch),
                "train_loss": train_loss,
                "val_loss": val_loss,
                **val_metrics,
            }
        )
        epoch_grid_rows.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                **val_metrics,
            }
        )
        if val_target_names:
            is_better = should_replace_best(val_metrics, best_selection_score, metric_tie_tolerance)
        else:
            is_better = val_loss < float(best_selection_score["rmse_mean"])
        if is_better:
            if val_target_names:
                best_selection_score = dict(val_metrics)
            else:
                best_selection_score = {
                    "pearson_mean": float("-inf"),
                    "top50_jaccard_mean": float("-inf"),
                    "rmse_mean": float(val_loss),
                }
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            best_epoch = epoch
            patience_left = early_stopping_patience
        elif early_stopping_enabled and val_target_names:
            patience_left -= 1
            if patience_left <= 0:
                break

    model.load_state_dict(best_state)
    return model, {
        "hidden_dim": hidden_dim,
        "optimizer": optimizer_name,
        "learning_rate": learning_rate,
        "weight_decay": weight_decay,
        "batch_size": batch_size,
        "max_epochs": max_epochs,
        "epochs_ran": len(history),
        "early_stopping_enabled": early_stopping_enabled and bool(val_target_names),
        "early_stopping_patience": early_stopping_patience,
        "train_sample_count": int(len(train_indices)),
        "validation_sample_count": int(len(val_indices)),
        "best_epoch": int(best_epoch or len(history)),
        "selection_topk": selection_topk,
        "metric_tie_tolerance": metric_tie_tolerance,
        "best_validation_metrics": best_selection_score,
        "training_history_tail": history[-5:],
        "epoch_grid_rows": epoch_grid_rows,
    }


def predict_with_adapter_head(
    *,
    model: AdapterHead,
    features: np.ndarray,
    device: torch.device,
    batch_size: int,
) -> np.ndarray:
    if features.shape[0] == 0:
        output_dim = model.layers[-1].out_features if isinstance(model.layers, torch.nn.Sequential) else model.layers.out_features
        return np.zeros((0, output_dim), dtype=np.float32)
    tensor = torch.as_tensor(features, dtype=torch.float32, device=device)
    rows: list[np.ndarray] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, tensor.shape[0], max(1, batch_size)):
            batch = tensor[start : start + max(1, batch_size)]
            rows.append(model(batch).detach().cpu().numpy())
    return np.concatenate(rows, axis=0).astype(np.float32, copy=False)


def merge_runtime_config(raw_config: dict[str, Any]) -> dict[str, Any]:
    runtime: dict[str, Any] = {}
    runtime_ref = raw_config.get("runtime_defaults_ref")
    if runtime_ref:
        runtime.update(load_yaml_mapping(resolve_project_path(runtime_ref)))
    runtime_overrides = raw_config.get("runtime", {})
    if runtime_overrides:
        runtime.update(ensure_mapping(runtime_overrides, "runtime"))
    runtime.setdefault("device_policy", "gpu_if_available_else_cpu")
    runtime["device"] = raw_config.get("device", runtime.get("device", "auto"))
    return runtime


def load_smoke_context(config_path: str | Path) -> EntrantContext:
    path = Path(config_path)
    raw_config = load_yaml_mapping(path)
    runtime_config = merge_runtime_config(raw_config)
    requested_device = str(raw_config.get("device", runtime_config.get("device", "auto")))
    device = resolve_torch_device(requested_device)
    output_dir = resolve_project_path(raw_config["output_dir"])
    if output_dir is None:
        raise ValueError("output_dir 不能为空。")
    return EntrantContext(
        config_path=path,
        raw_config=raw_config,
        dataset_id=str(raw_config["dataset_id"]),
        split_seed=int(raw_config["split_seed"]),
        output_dir=output_dir,
        runtime_config=runtime_config,
        requested_device=requested_device,
        device=device,
        timestamp=utc_timestamp(),
    )


def write_json(output_path: Path, payload: dict[str, Any]) -> None:
    json_dump(payload, output_path)


def print_runtime_banner(context: EntrantContext) -> None:
    runtime = context.runtime_config
    print(f"entrant={context.entrant_name}")
    print(f"dataset_id={context.dataset_id}")
    print(f"split_seed={context.split_seed}")
    print(f"device_type={context.device.type}")
    print(f"model_load_device={context.device}")
    print(f"batch_size={runtime.get('batch_size')}")
    print(f"max_epochs={runtime.get('max_epochs')}")
    print(f"early_stopping_enabled={runtime.get('early_stopping_enabled')}")


def add_smoke_config_argument(parser: argparse.ArgumentParser, default_path: str) -> argparse.ArgumentParser:
    parser.add_argument("--config", default=default_path, help="smoke yaml 配置路径。")
    return parser


class BaseEntrant(ABC):
    def __init__(self, spec: EntrantSpec, context: EntrantContext) -> None:
        self.spec = spec
        self.context = context
        self._checkpoint_manifest: dict[str, Any] = {}
        self._feature_manifest: dict[str, Any] = {}

    @abstractmethod
    def load_checkpoint_or_initialize(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def prepare_model_native_inputs(
        self,
        split_manifest: SplitManifest,
        inner_split_manifest: InnerSplitManifest,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def fit_on_train_split(self, prepared_inputs: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def predict_for_heldout_targets(
        self,
        prepared_inputs: dict[str, Any],
        fitted_state: dict[str, Any],
    ) -> pd.DataFrame:
        raise NotImplementedError

    def export_predicted_shift(self, predicted_shift: pd.DataFrame) -> Path:
        from wtbench.entrants.export import export_predicted_shift

        return export_predicted_shift(output_dir=self.context.output_dir, predicted_shift=predicted_shift)

    def get_checkpoint_manifest(self) -> dict[str, Any]:
        return self._checkpoint_manifest

    def get_feature_manifest(self) -> dict[str, Any]:
        return self._feature_manifest

    def run_smoke(self, split_manifest: SplitManifest) -> dict[str, Any]:
        inner_split_manifest = build_inner_target_level_split_manifest(
            split_manifest,
            inner_seed=int(self.context.runtime_config.get("inner_seed", 11)),
            inner_val_fraction=float(self.context.runtime_config.get("inner_val_fraction", 0.2)),
        )
        self.load_checkpoint_or_initialize()
        prepared = self.prepare_model_native_inputs(split_manifest, inner_split_manifest)
        fitted_state = self.fit_on_train_split(prepared)
        predicted_shift = self.predict_for_heldout_targets(prepared, fitted_state)
        prediction_path = self.export_predicted_shift(predicted_shift)
        inner_val_epoch_grid_path = self.context.output_dir / "inner_val_epoch_grid.tsv"
        selected_recipe_path = self.context.output_dir / "selected_recipe.json"
        run_summary = {
            "entrant_name": self.context.entrant_name,
            "dataset_id": self.context.dataset_id,
            "split_seed": self.context.split_seed,
            "device": str(self.context.device),
            "prediction_path": str(prediction_path),
            "train_target_count": len(split_manifest.train_targets),
            "heldout_target_count": len(split_manifest.heldout_targets),
            "inner_train_target_count": len(inner_split_manifest.inner_train_targets),
            "inner_val_target_count": len(inner_split_manifest.inner_val_targets),
            "runtime_config": self.spec.runtime_config,
            "timestamp": self.context.timestamp,
            "checkpoint_manifest_path": str(self.context.output_dir / "checkpoint_manifest.json"),
            "feature_manifest_path": str(self.context.output_dir / "feature_manifest.json"),
            "inner_val_epoch_grid_path": str(inner_val_epoch_grid_path),
            "selected_recipe_path": str(selected_recipe_path),
        }
        self.context.output_dir.mkdir(parents=True, exist_ok=True)
        epoch_grid = pd.DataFrame(fitted_state.get("inner_val_epoch_grid_rows", []))
        if epoch_grid.empty:
            epoch_grid = pd.DataFrame(
                columns=["epoch", "train_loss", "val_loss", "pearson_mean", "top50_jaccard_mean", "rmse_mean"]
            )
        epoch_grid.to_csv(inner_val_epoch_grid_path, sep="\t", index=False)
        selected_recipe = {
            "dataset_id": self.context.dataset_id,
            "entrant_name": self.context.entrant_name,
            "outer_split_seed": self.context.split_seed,
            "outer_heldout_usage": "final_evaluation_only",
            "inner_seed": inner_split_manifest.inner_seed,
            "inner_val_fraction": inner_split_manifest.inner_val_fraction,
            "inner_split_type": "target_level",
            "inner_train_target_count": len(inner_split_manifest.inner_train_targets),
            "inner_val_target_count": len(inner_split_manifest.inner_val_targets),
            "selection_rule": {
                "priority": ["pearson_mean_high", "top50_jaccard_mean_high", "rmse_mean_low"],
                "tie_tolerance": float(self.context.runtime_config.get("inner_metric_tie_tolerance", 1.0e-4)),
                "topk": int(self.context.runtime_config.get("selection_topk", 50)),
            },
            "selected_epoch": fitted_state.get("selected_epoch"),
            "selected_checkpoint_label": fitted_state.get("selected_checkpoint_label", "best_epoch_state"),
            "inner_split_manifest_path": str(inner_split_manifest.manifest_path),
        }
        write_json(self.context.output_dir / "checkpoint_manifest.json", self.get_checkpoint_manifest())
        write_json(self.context.output_dir / "feature_manifest.json", self.get_feature_manifest())
        write_json(self.context.output_dir / "run_summary.json", run_summary)
        write_json(selected_recipe_path, selected_recipe)
        return {
            "prediction_path": prediction_path,
            "run_summary": run_summary,
            "checkpoint_manifest": self.get_checkpoint_manifest(),
            "feature_manifest": self.get_feature_manifest(),
        }
