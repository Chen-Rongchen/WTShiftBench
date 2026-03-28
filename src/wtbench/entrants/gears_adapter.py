from __future__ import annotations

from typing import Any
from copy import deepcopy

import anndata as ad
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from gears import GEARS, PertData
from torch.optim.lr_scheduler import StepLR
from gears.inference import evaluate, compute_metrics
from gears.utils import loss_fct, uncertainty_loss_fct

from scripts.stage1a.adapters.gears.build_predictions import (
    build_gears_input_adata,
    build_identity_graph,
    build_local_perturbation_graph,
    build_split_file,
    predict_transcriptomes,
    write_fake_gene2go,
    write_gene_set,
)
from scripts.stage1a.benchmark_invariant.prediction_eval_common import evaluate_prediction_frame
from wtbench.entrants.base import (
    BaseEntrant,
    EntrantSpec,
    InnerSplitManifest,
    SplitManifest,
    load_output_gene_space,
    mean_expression,
    resolve_project_path,
    set_global_seed,
)
from wtbench.entrants.export import format_predicted_shift


class GEARSEntrant(BaseEntrant):
    def __init__(self, context) -> None:
        super().__init__(
            EntrantSpec(
                entrant_name=context.entrant_name,
                entrant_taxonomy="native_perturbation_model",
                model_provenance={"foundation_checkpoint_dependency": "none"},
                checkpoint_identity={"type": "run_initialized_weights"},
                preprocessing_identity={"shared_control_pseudobulk": "与协议一致"},
                adapter_recipe={"type": "native_gears_training"},
                predicted_shift_export_recipe={
                    "model_output": "predicted_expression",
                    "aggregation": "perturbation_level",
                    "control_subtraction": "shared control pseudobulk",
                    "export": "predicted_shift",
                },
                trainable_components={"native_parameters": "trainable_on_train_split"},
                runtime_config=context.runtime_config,
            ),
            context,
        )

    def load_checkpoint_or_initialize(self) -> None:
        self._checkpoint_manifest = {
            "entrant_name": self.context.entrant_name,
            "checkpoint_type": "none",
            "status": "initialized_from_train_split",
        }

    def prepare_model_native_inputs(
        self,
        split_manifest: SplitManifest,
        inner_split_manifest: InnerSplitManifest,
    ) -> dict[str, Any]:
        runtime = self.context.runtime_config
        formal_adata = ad.read_h5ad(self.context.dataset_contract.path)
        truth, output_genes = load_output_gene_space(self.context.dataset_id)
        heldout_targets = set(split_manifest.heldout_targets)
        set_global_seed(int(runtime.get("training_seed", self.context.split_seed)))
        rng = np.random.default_rng(int(runtime.get("training_seed", self.context.split_seed)))

        obs = formal_adata.obs.copy()
        obs["is_control"] = obs["is_control"].astype(bool)
        obs["target_gene"] = obs["target_gene"].astype("string").fillna("")
        perturbation_genes = sorted(obs.loc[~obs["is_control"], "target_gene"].dropna().astype(str).unique().tolist())
        control_gene_names = formal_adata.var.index.astype(str).tolist()
        gene_index = pd.Index(control_gene_names)
        output_gene_positions = gene_index.get_indexer(output_genes)
        if (output_gene_positions < 0).any():
            missing = [output_genes[i] for i, pos in enumerate(output_gene_positions) if pos < 0][:10]
            raise ValueError(f"GEARS formal source 缺少输出基因: {missing}")
        control_values = mean_expression(formal_adata.X[obs["is_control"].to_numpy()])[output_gene_positions]
        inner_val_truth_rows: list[np.ndarray] = []
        for target in inner_split_manifest.inner_val_targets:
            target_mask = (~obs["is_control"]).to_numpy() & obs["target_gene"].eq(target).fillna(False).to_numpy(dtype=bool)
            target_values = mean_expression(formal_adata.X[target_mask])
            inner_val_truth_rows.append((target_values - control_values).astype(np.float32, copy=False))
        inner_val_truth = pd.DataFrame(
            np.asarray(inner_val_truth_rows, dtype=np.float32),
            index=list(inner_split_manifest.inner_val_targets),
            columns=output_genes,
        )

        train_adata, train_targets = build_gears_input_adata(
            formal_adata=formal_adata,
            heldout_targets=heldout_targets,
            rng=rng,
            max_control_cells=runtime.get("max_control_cells", 2048),
            max_cells_per_train_condition=runtime.get("max_cells_per_train_condition"),
            cell_type_label=self.context.dataset_contract.cell_line,
        )
        self._feature_manifest = {
            "feature_type": "gears_native_training_input",
            "output_gene_count": len(output_genes),
            "train_target_count": len(train_targets),
            "heldout_target_count": len(split_manifest.heldout_targets),
            "inner_train_target_count": len(inner_split_manifest.inner_train_targets),
            "inner_val_target_count": len(inner_split_manifest.inner_val_targets),
            "truth_target_count": int(truth.shape[0]),
            "space_audit_status": "pending",
        }
        return {
            "train_adata": train_adata,
            "train_targets": train_targets,
            "inner_train_targets": list(inner_split_manifest.inner_train_targets),
            "inner_val_targets": list(inner_split_manifest.inner_val_targets),
            "heldout_targets": list(split_manifest.heldout_targets),
            "perturbation_genes": perturbation_genes,
            "output_genes": output_genes,
            "control_values": control_values,
            "control_gene_names": control_gene_names,
            "inner_val_truth": inner_val_truth,
        }

    def fit_on_train_split(self, prepared_inputs: dict[str, Any]) -> dict[str, Any]:
        runtime = self.context.runtime_config
        gears_cache_dir = resolve_project_path(runtime.get("gears_cache_dir", "artifacts/gears_cache/stage1a_smoke"))
        if gears_cache_dir is None:
            raise ValueError("GEARS cache dir 不能为空。")
        gears_cache_dir.mkdir(parents=True, exist_ok=True)

        write_fake_gene2go(gears_cache_dir, prepared_inputs["perturbation_genes"])
        gene_set_path = write_gene_set(gears_cache_dir, prepared_inputs["perturbation_genes"])
        split_path = gears_cache_dir / "custom_split.pkl"
        train_conditions = sorted(prepared_inputs["train_adata"].obs["condition"].astype(str).unique().tolist())
        explicit_val_conditions = [f"{target}+ctrl" for target in prepared_inputs["inner_val_targets"]]
        split_payload = build_split_file(
            split_path,
            train_conditions,
            int(runtime.get("training_seed", self.context.split_seed)),
            float(runtime.get("train_val_fraction", 0.875)),
            val_conditions=explicit_val_conditions,
        )

        pert_data = PertData(str(gears_cache_dir), gene_set_path=str(gene_set_path), default_pert_graph=False)
        pert_data.new_data_process(
            dataset_name=f"{self.context.dataset_id}_{self.context.entrant_name}",
            adata=prepared_inputs["train_adata"],
            skip_calc_de=False,
        )
        pert_data.prepare_split(split="custom", split_dict_path=str(split_path))
        effective_batch_size = min(int(runtime["batch_size"]), max(1, prepared_inputs["train_adata"].n_obs))
        pert_data.get_dataloader(batch_size=effective_batch_size, test_batch_size=effective_batch_size)
        pert_data.dataloader.pop("test_loader", None)

        perturbation_edge_index, perturbation_edge_weight = build_local_perturbation_graph(
            control_matrix=prepared_inputs["train_adata"].X[
                prepared_inputs["train_adata"].obs["condition"].astype(str).eq("ctrl").to_numpy()
            ],
            control_gene_names=prepared_inputs["train_adata"].var["gene_name"].astype(str).tolist(),
            perturbation_genes=pert_data.pert_names.astype(str).tolist(),
            k=int(runtime.get("perturbation_graph_k", 8)),
        )
        gene_edge_index, gene_edge_weight = build_identity_graph(prepared_inputs["train_adata"].n_vars)

        model = GEARS(pert_data, device=str(self.context.device), weight_bias_track=False)
        model.model_initialize(
            G_go=perturbation_edge_index,
            G_go_weight=perturbation_edge_weight,
            G_coexpress=gene_edge_index,
            G_coexpress_weight=gene_edge_weight,
        )
        model.model = model.model.to(str(self.context.device))
        optimizer = optim.Adam(
            model.model.parameters(),
            lr=float(runtime["learning_rate"]),
            weight_decay=float(runtime["weight_decay"]),
        )
        scheduler = StepLR(optimizer, step_size=1, gamma=0.5)
        train_loader = pert_data.dataloader["train_loader"]
        val_loader = pert_data.dataloader["val_loader"]
        max_epochs = int(runtime["max_epochs"])
        early_stopping_enabled = bool(runtime.get("early_stopping_enabled", True))
        early_stopping_patience = int(runtime.get("early_stopping_patience", 5))
        metric_tie_tolerance = float(runtime.get("inner_metric_tie_tolerance", 1.0e-4))
        prediction_num_samples = int(runtime.get("prediction_num_samples", 64))
        best_model = deepcopy(model.model)
        best_epoch = 0
        best_metrics = {
            "pearson_mean": float("-inf"),
            "top50_jaccard_mean": float("-inf"),
            "rmse_mean": float("inf"),
        }
        patience_left = early_stopping_patience
        epoch_grid_rows: list[dict[str, object]] = []

        def should_replace_best(candidate: dict[str, float], incumbent: dict[str, float]) -> bool:
            if candidate["pearson_mean"] > incumbent["pearson_mean"] + metric_tie_tolerance:
                return True
            if abs(candidate["pearson_mean"] - incumbent["pearson_mean"]) <= metric_tie_tolerance:
                if candidate["top50_jaccard_mean"] > incumbent["top50_jaccard_mean"] + metric_tie_tolerance:
                    return True
                if abs(candidate["top50_jaccard_mean"] - incumbent["top50_jaccard_mean"]) <= metric_tie_tolerance:
                    if candidate["rmse_mean"] < incumbent["rmse_mean"] - metric_tie_tolerance:
                        return True
            return False

        for epoch in range(1, max_epochs + 1):
            model.model.train()
            train_losses: list[float] = []
            for batch in train_loader:
                batch.to(str(self.context.device))
                optimizer.zero_grad()
                y = batch.y
                if model.config["uncertainty"]:
                    pred, logvar = model.model(batch)
                    loss = uncertainty_loss_fct(
                        pred,
                        logvar,
                        y,
                        batch.pert,
                        reg=model.config["uncertainty_reg"],
                        ctrl=model.ctrl_expression,
                        dict_filter=model.dict_filter,
                        direction_lambda=model.config["direction_lambda"],
                    )
                else:
                    pred = model.model(batch)
                    loss = loss_fct(
                        pred,
                        y,
                        batch.pert,
                        ctrl=model.ctrl_expression,
                        dict_filter=model.dict_filter,
                        direction_lambda=model.config["direction_lambda"],
                    )
                loss.backward()
                nn.utils.clip_grad_value_(model.model.parameters(), clip_value=1.0)
                optimizer.step()
                train_losses.append(float(loss.detach().cpu().item()))
            scheduler.step()

            train_res = evaluate(train_loader, model.model, model.config["uncertainty"], str(self.context.device))
            val_res = evaluate(val_loader, model.model, model.config["uncertainty"], str(self.context.device))
            train_metrics, _ = compute_metrics(train_res)
            val_metrics_lib, _ = compute_metrics(val_res)

            model.best_model = model.model
            inner_val_prediction = predict_transcriptomes(
                gears_model=model,
                target_order=prepared_inputs["inner_val_targets"],
                num_samples=prediction_num_samples,
                device=str(self.context.device),
            )
            gene_index = pd.Index(prepared_inputs["control_gene_names"])
            output_positions = gene_index.get_indexer(prepared_inputs["output_genes"])
            predicted_rows: list[np.ndarray] = []
            for target in prepared_inputs["inner_val_targets"]:
                predicted_expression = inner_val_prediction[target].astype(np.float64, copy=False)
                predicted_rows.append(
                    (predicted_expression[output_positions] - prepared_inputs["control_values"]).astype(np.float32)
                )
            inner_val_prediction_frame = pd.DataFrame(
                np.asarray(predicted_rows, dtype=np.float32),
                index=prepared_inputs["inner_val_targets"],
                columns=prepared_inputs["output_genes"],
            )
            _, selection_aggregates = evaluate_prediction_frame(
                prediction=inner_val_prediction_frame,
                truth=prepared_inputs["inner_val_truth"],
                topk_values=[int(runtime.get("selection_topk", 50))],
            )
            selection_metrics = {
                "pearson_mean": float(selection_aggregates["pearson_mean"]),
                "top50_jaccard_mean": float(selection_aggregates["top50_jaccard_mean"]),
                "rmse_mean": float(selection_aggregates["rmse_mean"]),
            }
            epoch_grid_rows.append(
                {
                    "epoch": epoch,
                    "train_loss": float(np.mean(train_losses)) if train_losses else 0.0,
                    "val_loss": float(val_metrics_lib["mse_de"]),
                    **selection_metrics,
                }
            )
            if should_replace_best(selection_metrics, best_metrics):
                best_metrics = dict(selection_metrics)
                best_epoch = epoch
                best_model = deepcopy(model.model)
                patience_left = early_stopping_patience
            elif early_stopping_enabled:
                patience_left -= 1
                if patience_left <= 0:
                    break

        model.best_model = best_model
        return {
            "model": model,
            "split_payload": split_payload,
            "effective_batch_size": effective_batch_size,
            "selected_epoch": int(best_epoch) if best_epoch else None,
            "selected_checkpoint_label": "gears_best_model_on_inner_val",
            "inner_val_epoch_grid_rows": epoch_grid_rows,
        }

    def predict_for_heldout_targets(
        self,
        prepared_inputs: dict[str, Any],
        fitted_state: dict[str, Any],
    ) -> pd.DataFrame:
        runtime = self.context.runtime_config
        transcriptome_predictions = predict_transcriptomes(
            gears_model=fitted_state["model"],
            target_order=prepared_inputs["heldout_targets"],
            num_samples=int(runtime.get("prediction_num_samples", 64)),
            device=str(self.context.device),
        )
        gene_index = pd.Index(prepared_inputs["control_gene_names"])
        output_positions = gene_index.get_indexer(prepared_inputs["output_genes"])
        rows: list[np.ndarray] = []
        for target in prepared_inputs["heldout_targets"]:
            predicted_expression = transcriptome_predictions[target].astype(np.float64, copy=False)
            rows.append((predicted_expression[output_positions] - prepared_inputs["control_values"]).astype(np.float32))
        self._feature_manifest["prediction_num_samples"] = int(runtime.get("prediction_num_samples", 64))
        self._feature_manifest["space_export_consistency"] = "pending_audit"
        return format_predicted_shift(
            target_order=prepared_inputs["heldout_targets"],
            gene_names=prepared_inputs["output_genes"],
            values=np.asarray(rows, dtype=np.float32),
        )
