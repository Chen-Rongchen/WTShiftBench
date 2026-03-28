# Stage 1A Entrant Readiness Summary

| entrant | taxonomy | checkpoint_status | smoke_dataset | split_seed | trainable_components | predicted_shift_path_defined | current_status | main_blocker |
|---|---|---|---|---:|---|---|---|---|
| GEARS | `native_perturbation_model` | `not_applicable` | `replogle_2022_k562_essential` | 101 | `native_parameters_on_train_split` | `yes` | `pipeline_proven_under_audit` | `space/export audit` |
| scGPT | `foundation_model_plus_adapter` | `resolved_local` | `replogle_2022_k562_essential` | 101 | `adapter_head_only` | `yes` | `environment_ready_recipe_not_frozen` | `checkpoint + adapter + export recipe freeze` |
| Geneformer | `foundation_model_plus_adapter` | `resolved_local` | `replogle_2022_k562_essential` | 101 | `adapter_head_only` | `yes` | `environment_ready_recipe_not_frozen` | `checkpoint + workflow type + export recipe freeze` |

1. `GEARS`：当前最接近 formal entrant，但优先任务仍是 `space/export audit`。
2. `GEARS`：`2026-03-28` 已完成三套 formal 数据的 batch 跑通；该进展证明工程链路稳定性提升，但不自动关闭 `space/export audit`，也不自动构成 formal adjudication。
3. `scGPT`：本轮基于本地 `scgpt_human` 建立首个 target-feature + adapter smoke 路径。
4. `Geneformer`：本轮基于本地 `geneformer_gf_12l_95m_i4096` 建立首个 `embedding_plus_adapter` smoke 路径。
