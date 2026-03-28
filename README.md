# WTKO

环境管理使用 `pixi`。

## 项目一句话

**WT Benchmark**：用统一、可审计的 black-box 框架评估各 entrant 是否产出可信的 `predicted_shift`。当前最近一批工作的重点是按 blueprint 收口 `Stage 1A` 的 `3 datasets × split_seed 101` 主线，并保留 1 个辅助数据集用于鲁棒性审计。

## 当前真实状态

| 状态 | 内容 |
|---|---|
| 已具备 | `core` / `gears` / `scgpt` / `geneformer` 四套 Pixi 环境 |
| 已具备 | benchmark-invariant 的 contract validation / ingest / alignment 主线 |
| 已具备 | 本地 checkpoint：`models/pretrained/scgpt_human` |
| 已具备 | 本地 checkpoint：`models/pretrained/geneformer_gf_12l_95m_i4096` |
| 已具备 | 三个 smoke yaml、runtime defaults、checkpoint registry |
| 进行中 | `Stage 1A` 的 dataset-local / four-lane / cross-lane formal 收口 |
| 已具备 | 三模型 × 三数据集 × seed101 的 formal adapter / ingest / evaluate 主线配置 |
| 待重跑 | 新第三主线 `tian_2019_day7neuron` 与辅助位 `tian_2021_crispri` 的产物审计与重建 |
| 暂不进行 | formal multi-dataset × multi-seed adjudication（`3 datasets × 5 seeds`） |

## 当前收口范围

- 正式主线使用 `replogle_2022_k562_essential / replogle_2022_rpe1 / tian_2019_day7neuron`
- 辅助数据集使用 `tian_2021_crispri`，默认不进入 formal 主流程
- `tian_2019_ipsc` 与 `replogle_2022_k562_gwps` 不属于当前默认主线
- 本轮固定 `split_seed: 101`
- 正式评分按 `dataset-local + four-lane + cross-lane summary`
- `common intersection` 仅保留 supplementary / audit 用途
- train-side 终点选择统一采用 target-level inner validation：`inner_seed=11`、`inner_val_fraction=0.2`
- outer heldout 只用于最终正式评估，不参与 epoch / checkpoint 选型
- 三个 entrant 的外层训练上限字段统一命名为 `max_epochs`
- 当前 single-seed 收口版统一采用 `max_epochs=30`
- `GEARS` 在内部把 `max_epochs` 映射到官方训练接口 `epochs`
- `scGPT / Geneformer` 的 `max_epochs` 属于本项目 adapter 训练层，不是官方 backbone 原生参数名
- 设备策略统一为 `gpu_if_available_else_cpu`：GPU 可用时默认且优先使用 GPU，只在 CUDA 不可用时回退 CPU

## 关键文件

- 蓝图：`docs/protocol_blueprint.md`
- 当前计划：`plan.md`
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
- 当前 `linear_delta_baseline` 的仓库实现仅保留 `legacy` 版本，不作为 canonical linear baseline formal 结论依据
- `scripts/run_stage1a_smoke_matrix.py` 当前用于 entrant smoke / inner-validation 批量回归，不等同于 formal `3 datasets × 5 seeds` adjudication 主线

## 数据集来源校验

- 当前主线 / 辅助位统一以 `pertpy.data.*` loader 名为准：
  - `pertpy.data.replogle_2022_rpe1()`
  - `pertpy.data.replogle_2022_k562_essential()`
  - `pertpy.data.tian_2019_day7neuron()`
  - `pertpy.data.tian_2021_crispri()`
- 该口径已按 pertpy 官方 datasets 文档与 `_datasets` 源码页核对；仓库配置中的 loader 名、文件名与下载 URL 应与官方实现一致

## Registry 层状态（已弃用）

`configs/entrants/registry.yaml` 与 `src/wtbench/entrants/registry.py` 已被**显式弃用**。

原因：
- `registry.yaml` 中 `adapter_class` 与实际类名不一致（`GEARSEntrantAdapter` → `GEARSEntrant` 等）
- `registry.yaml` 中 `default_config_path` 指向不存在的文件
- `registry.py` 曾引用 `base.py` 中不存在的 `DEFAULT_ENTRANT_REGISTRY_PATH`
- `scripts/run_stage1a_entrant.py` 引用了 `base.py` 中不存在的函数（`build_output_paths` 等）

**当前支持的入口**：使用 `scripts/smoke_stage1a_*.py` 直连 entrant class，不依赖 registry 层。
