from __future__ import annotations

import pickle
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from torch_geometric.data import DataLoader
from gears.utils import create_cell_graph_dataset_for_prediction


def write_gene_set(cache_dir: Path, perturbation_genes: list[str]) -> Path:
    path = Path(cache_dir) / "gene_set.pkl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(sorted(set(map(str, perturbation_genes))), handle)
    return path


def write_fake_gene2go(cache_dir: Path, perturbation_genes: list[str]) -> Path:
    path = Path(cache_dir) / "gene2go.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = ["gene\tgo"]
    rows.extend(f"{gene}\tGO:0000000" for gene in sorted(set(map(str, perturbation_genes))))
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def build_split_file(
    split_path: Path,
    train_conditions: list[str],
    seed: int,
    train_val_fraction: float,
) -> dict[str, list[str]]:
    rng = np.random.default_rng(seed)
    conditions = sorted(set(map(str, train_conditions)))
    non_ctrl = [condition for condition in conditions if condition != "ctrl"]
    rng.shuffle(non_ctrl)
    n_val = max(1, int(round(len(non_ctrl) * (1.0 - float(train_val_fraction))))) if len(non_ctrl) > 1 else 0
    val = sorted(non_ctrl[:n_val])
    train = sorted(["ctrl", *non_ctrl[n_val:]])
    payload = {"train": train, "val": val, "test": []}
    split_path.parent.mkdir(parents=True, exist_ok=True)
    with split_path.open("wb") as handle:
        pickle.dump(payload, handle)
    return payload


def _sample_indices(indices: np.ndarray, max_count: int | None, rng: np.random.Generator) -> np.ndarray:
    if max_count is None or int(max_count) <= 0 or len(indices) <= int(max_count):
        return indices
    return np.sort(rng.choice(indices, size=int(max_count), replace=False))


def build_gears_input_adata(
    *,
    formal_adata: ad.AnnData,
    heldout_targets: set[str],
    rng: np.random.Generator,
    max_control_cells: int | None,
    max_cells_per_train_condition: int | None,
    cell_type_label: str,
) -> tuple[ad.AnnData, list[str]]:
    obs = formal_adata.obs.copy()
    obs["target_gene"] = obs["target_gene"].astype(str)
    obs["is_control"] = obs["is_control"].astype(bool)
    keep_indices: list[np.ndarray] = []
    control_idx = np.flatnonzero(obs["is_control"].to_numpy())
    keep_indices.append(_sample_indices(control_idx, max_control_cells, rng))
    train_targets = []
    for target, group in obs.loc[~obs["is_control"]].groupby("target_gene", sort=True):
        if str(target) in heldout_targets:
            continue
        idx = group.index
        positions = np.asarray([formal_adata.obs_names.get_loc(name) for name in idx], dtype=int)
        keep_indices.append(_sample_indices(positions, max_cells_per_train_condition, rng))
        train_targets.append(str(target))
    selected = np.concatenate(keep_indices)
    train = formal_adata[selected].copy()
    train.obs["condition"] = np.where(train.obs["is_control"].astype(bool), "ctrl", train.obs["target_gene"].astype(str))
    train.obs["perturbation"] = train.obs["condition"].astype(str)
    train.obs["cell_type"] = cell_type_label
    train.obs["cov_drug_dose_name"] = train.obs["condition"].astype(str)
    train.var["gene_name"] = train.var.index.astype(str)
    train.var["gene_id"] = train.var.index.astype(str)
    return train, sorted(train_targets)


def build_identity_graph(n_vars: int) -> tuple[torch.Tensor, torch.Tensor]:
    nodes = torch.arange(int(n_vars), dtype=torch.long)
    edge_index = torch.vstack([nodes, nodes])
    edge_weight = torch.ones(int(n_vars), dtype=torch.float32)
    return edge_index, edge_weight


def build_local_perturbation_graph(
    *,
    control_matrix,
    control_gene_names: list[str],
    perturbation_genes: list[str],
    k: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    # GEARS uses this graph in perturbation-node space, not transcriptome-gene
    # column space. Keep a conservative identity graph over the perturbation
    # names to avoid leaking an unsupported external graph assumption.
    return build_identity_graph(len(perturbation_genes))


def _mean_control(pert_data) -> np.ndarray:
    adata = pert_data.adata
    condition = adata.obs["condition"].astype(str)
    mask = condition.eq("ctrl").to_numpy()
    x = adata.X[mask]
    mean = x.mean(axis=0)
    if sparse.issparse(mean):
        mean = mean.A1
    return np.asarray(mean).ravel().astype(np.float64)


def _mean_control_from_model(gears_model) -> np.ndarray:
    if hasattr(gears_model, "ctrl_expression"):
        value = gears_model.ctrl_expression.detach().cpu().numpy()
        return np.asarray(value).ravel().astype(np.float64)
    if hasattr(gears_model, "adata"):
        adata = gears_model.adata
        condition = adata.obs["condition"].astype(str)
        mask = condition.eq("ctrl").to_numpy()
        mean = adata.X[mask].mean(axis=0)
        if sparse.issparse(mean):
            mean = mean.A1
        return np.asarray(mean).ravel().astype(np.float64)
    raise AttributeError("GEARS model does not expose ctrl_expression or adata for fallback prediction.")


def predict_transcriptomes(
    *,
    gears_model,
    target_order: list[str],
    num_samples: int,
    device: str,
) -> dict[str, np.ndarray]:
    predictions: dict[str, np.ndarray] = {}
    model = gears_model.best_model.to(device)
    model.eval()
    ctrl_adata = gears_model.adata[gears_model.adata.obs["condition"].astype(str).eq("ctrl")].copy()
    if int(num_samples) > 0 and ctrl_adata.n_obs > int(num_samples):
        ctrl_adata = ctrl_adata[: int(num_samples)].copy()
    for target in target_order:
        cell_graphs = create_cell_graph_dataset_for_prediction(
            [str(target)],
            ctrl_adata,
            gears_model.pert_list,
            device,
        )
        loader = DataLoader(cell_graphs, batch_size=min(16, max(1, len(cell_graphs))), shuffle=False)
        chunks = []
        with torch.no_grad():
            for batch in loader:
                batch.to(device)
                chunks.append(model(batch).detach().cpu().numpy())
        if not chunks:
            raise ValueError(f"GEARS prediction produced no batches for {target}")
        vector = np.vstack(chunks).mean(axis=0)
        predictions[str(target)] = vector.ravel().astype(np.float64)
    expected = getattr(gears_model, "num_genes", None)
    bad_shapes = {target: vector.shape for target, vector in predictions.items() if expected is not None and vector.shape[0] != expected}
    if bad_shapes:
        raise ValueError(f"GEARS prediction vector shapes do not match num_genes={expected}: {bad_shapes}")
    return predictions
