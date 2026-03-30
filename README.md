# WTKO

环境管理使用 `pixi`。

## 项目一句话

**WT Benchmark**：用统一、可审计的 black-box 框架评估各 entrant 是否产出可信的 `predicted_shift`。当前最近一批工作的重点是先冻结 `benchmark-invariant layer`，再在冻结边界上推进 `Stage 1A` entrant benchmarking 与解释边界审计。

## 当前真实状态

| 状态 | 内容 |
|---|---|
| 已具备 | `core` / `gears` / `scgpt` / `geneformer` 四套 Pixi 环境 |
| 已具备 | benchmark-invariant 的 contract validation / ingest / alignment 主线 |
| 已具备 | 本地 checkpoint：`models/pretrained/scgpt_human` |
| 已具备 | 本地 checkpoint：`models/pretrained/geneformer_gf_12l_95m_i4096` |
| 已具备 | 三个 smoke yaml、runtime defaults、checkpoint registry |
| 已具备 | `tian_2021_crispri` 原始文件下载完成并完成 raw audit |
| 已具备 | 4 个 Stage 1A 数据集的 raw audit 产物 |
| 已具备 | 三模型 × 三数据集 × seed101 的 formal adapter / ingest / evaluate 主线配置 |
| 已完成 | `Stage 1A` 的 harmonized resource layer / dataset admission layer 收口 |
| 已完成 | `tian_2019_day7neuron` 的 formal filtering 与 formal 统计回填 |
| 已完成 | `tian_2021_crispri` 的 target mapping closure 审计与 formal filtering |
| 已完成 | `Stage 1A` admission manifest 与 formal freeze gating |
| 已完成 | `1 seed × 3 entrants × 3 datasets` 的 formal trial run（预测、对齐、评分、pass skeleton） |
| 暂不进行 | formal multi-dataset × multi-seed adjudication（`3 datasets × 5 seeds`） |

## 当前收口范围

- 当前固定顺序：`harmonized resource layer -> dataset admission layer -> entrant benchmarking layer`
- 正式主线使用 `replogle_2022_k562_essential / replogle_2022_rpe1 / tian_2019_day7neuron`
- 辅助数据集使用 `tian_2021_crispri`，默认不进入 formal 主流程
- `tian_2019_ipsc` 与 `replogle_2022_k562_gwps` 不属于当前默认主线
- 本轮固定 `split_seed: 101`
- `signal adequacy` 与 `model fidelity` 明确分离：adequacy diagnostics 不替代 `predicted_shift` formal scoring
- `support floor` 具有 admission 语义，至少显式追踪 `cells per perturbation`、`cells per control`、`UMI depth`
- formal freeze 只消费 `admission_decision=pass` 的主线数据集
- 正式评分按 `dataset-local + four-lane + cross-lane summary`
- `common intersection` 仅保留 supplementary / audit 用途
- 当前 trial run 固定 `model/adaptor seed: 123`，与 formal split seed `101` 分离
- `GEARS` 是当前唯一训练型 entrant；其试运行配置当前为 `epochs=30`、`lr=1e-3`、`weight_decay=1e-6`、`train_val_fraction=0.8`、`device=auto`
- `scGPT / Geneformer` 当前接入方式是 `embedding + cosine kernel regression` adapter，不走训练型 inner validation 主线
- 设备策略统一为 `gpu_if_available_else_cpu`：GPU 可用时默认且优先使用 GPU，只在 CUDA 不可用时回退 CPU

## 当前数据集状态

- `replogle_2022_k562_essential`：已在 formal 主线中
- `replogle_2022_rpe1`：已在 formal 主线中
- `tian_2019_day7neuron`：已完成 formal filtering，admission=`pass`
- `tian_2021_crispri`：已完成 formal filtering，admission=`auxiliary_pass`

其中：

- `tian_2019_day7neuron` 当前 raw 统计为 `182790 x 33752`，formal 统计为 `85290 x 33752`，`n_controls=15580`，`n_perturbed=69710`，`n_unique_targets=26`
- `replogle_2022_rpe1` 当前 formal 统计为 `247914 x 8749`；有 458 行 source `gene_id` 为空，但 formal 主键仍可稳定落在 `target_gene`
- `tian_2021_crispri` 当前 raw 统计为 `32300 x 33538`，`n_controls=437`，`n_perturbed=31863`，`n_unique_targets=184`
- `tian_2021_crispri` 的 3 个旧符号 token 已完成 target mapping closure：`ATP5C1 -> ATP5F1C`、`ATP5H -> ATP5PD`、`TMEM55A -> PIP4P2`
- `tian_2021_crispri` 当前 formal 统计为 `32300 x 33538`，`n_controls=437`，`n_perturbed=31863`，`n_unique_targets=184`

当前 admission manifest 冻结结果：

- `replogle_2022_k562_essential`：`pass`
- `replogle_2022_rpe1`：`pass`
- `tian_2019_day7neuron`：`pass`
- `tian_2021_crispri`：`auxiliary_pass`

当前 formal freeze 仅冻结 3 个 mainline `pass` 数据集：

- `replogle_2022_k562_essential`
- `replogle_2022_rpe1`
- `tian_2019_day7neuron`

## 当前 trial run 状态

本轮已完成 `1 seed × 3 entrants × 3 datasets` 的 formal 试运行：

- entrants：`gears_stage1a_formal`、`scgpt_embedding_kernel_formal`、`geneformer_embedding_kernel_formal`
- datasets：`replogle_2022_k562_essential`、`replogle_2022_rpe1`、`tian_2019_day7neuron`
- split seed：`101`
- model/adaptor seed：`123`

本轮已落地产物：

- 9 份 dataset-level score summary：`reports/stage1a/model_eval/*/*/dataset_score_summary.json`
- 9 份 lane-level summary：`reports/stage1a/model_eval_lanes/*/*/lane_summary.tsv`
- 9 份 aligned predictions：`data/predictions/stage1a_main_aligned/*/*/predicted_shift_aligned.tsv.gz`
- 3 份 entrant-level pass skeleton：
  - `reports/stage1a/model_eval/gears_stage1a_formal/stage1a_pass_skeleton_official_leaderboard.tsv`
  - `reports/stage1a/model_eval/scgpt_embedding_kernel_formal/stage1a_pass_skeleton_official_leaderboard.tsv`
  - `reports/stage1a/model_eval/geneformer_embedding_kernel_formal/stage1a_pass_skeleton_official_leaderboard.tsv`

说明：

- 这次运行是 single-seed trial run，不等同于正式 `3 datasets × 5 seeds` adjudication
- 当前结果可用于 runtime 审计、lane-wise 诊断与解释边界核查，不自动等同于 entrant version 已获得 formal downstream admission

## 关键文件

- 蓝图：`docs/protocol_blueprint.md`
- 当前计划：`plan.md`
- admission manifest：`reports/stage1a/admission/stage1a_admission_manifest.tsv`
- formal freeze manifest：`reports/stage1a/freeze/freeze_manifest.json`
- smoke 卡片与 runtime spec：`docs/entrants/`
- smoke 配置：`configs/entrants/*.yaml`
- checkpoint registry：`configs/entrants/checkpoint_registry.yaml`
- entrant 代码：`src/wtbench/entrants/`
- smoke 脚本：`scripts/smoke_stage1a_*.py`

## 推荐命令

先检查环境：

```bash
pixi run check-envs
```

GEARS smoke：

```bash
pixi run --environment gears python scripts/smoke_stage1a_gears.py
```

GEARS formal adapter：

```bash
python scripts/stage1a/adapters/gears/launch_build_predictions.py --run-config <path/to/run-config.yaml>
```

scGPT smoke：

```bash
pixi run --environment scgpt python scripts/smoke_stage1a_scgpt.py
```

Geneformer smoke：

```bash
pixi run --environment geneformer python scripts/smoke_stage1a_geneformer.py
```

三模型 × 三数据集 × 五个 seeds 的 smoke matrix：

```bash
python scripts/run_stage1a_smoke_matrix.py
```

## 输出边界

- smoke 运行只证明 entrant identity、runtime spec、split governance、`predicted_shift` export 与 benchmark hooks 已接通
- smoke 结果不构成 formal Stage 1A adjudication 结论
- 正式记录以 `lane-wise outputs + cross-lane summary` 为中心，而不是单一 leaderboard
- `E-test` / `E-distance` 等 adequacy diagnostics 只用于资源层 / admission 层诊断，不替代 formal predicted-shift scoring
- 当前 `linear_delta_baseline` 的仓库实现仅保留 `legacy` 版本，不作为 canonical linear baseline formal 结论依据
- `scripts/run_stage1a_smoke_matrix.py` 当前用于 entrant smoke / inner-validation 批量回归，不等同于 formal `3 datasets × 5 seeds` adjudication 主线

## 数据集来源校验

- 当前主线 / 辅助位统一以 `pertpy.data.*` loader 名为准：
  - `pertpy.data.replogle_2022_rpe1()`
  - `pertpy.data.replogle_2022_k562_essential()`
  - `pertpy.data.tian_2019_day7neuron()`
  - `pertpy.data.tian_2021_crispri()`
- 该口径已按 pertpy 官方 datasets 文档与 `_datasets` 源码页核对；仓库配置中的 loader 名、文件名与下载 URL 应与官方实现一致
- `scPerturb` 或其他 dataset hub 只作为候选资源入口与预审计输入，不等同于本项目 formal benchmark protocol

## 下一步

按当前优先级：

1. 审查 9 份 `dataset_score_summary.json` 与 9 份 `lane_summary.tsv`，形成单 seed trial run 的解释报告
2. 对 `GEARS` 继续做 prediction space / LOG-RAW mismatch 审计，确认当前 version 的解释边界
3. 明确 `scGPT / Geneformer` 当前 adapter taxonomy 与可声明范围，避免把 adapter 结果误写成 backbone 原生 perturbation 能力
4. 在解释边界稳定后，再决定是否推进 formal `3 datasets × 5 seeds` adjudication
5. 视需要决定是否把 `tian_2021_crispri` 纳入 supplementary / auxiliary benchmarking

## Registry 层状态（已弃用）

`configs/entrants/registry.yaml` 与 `src/wtbench/entrants/registry.py` 已被**显式弃用**。

原因：
- `registry.yaml` 中 `adapter_class` 与实际类名不一致（`GEARSEntrantAdapter` → `GEARSEntrant` 等）
- `registry.yaml` 中 `default_config_path` 指向不存在的文件
- `registry.py` 曾引用 `base.py` 中不存在的 `DEFAULT_ENTRANT_REGISTRY_PATH`
- `scripts/run_stage1a_entrant.py` 引用了 `base.py` 中不存在的函数（`build_output_paths` 等）

**当前支持的入口**：使用 `scripts/smoke_stage1a_*.py` 直连 entrant class，不依赖 registry 层。
