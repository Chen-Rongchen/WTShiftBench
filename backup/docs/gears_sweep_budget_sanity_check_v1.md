# GEARS sweep budget sanity check v1

## 状态

完成日期：2026-04-17。

用途：支撑 Methods / Supplementary 中关于 GEARS sweep 的透明化措辞，避免把有限预算 sweep 写成 exhaustive search。

## 输入产物

- Sweep 配置：`configs/stage2/gears_hcc_backbone_sweep_v1.json`
- 候选 manifest：`reports/stage2_gears_backbone_sweep/candidate_manifest.tsv`
- 候选说明：`reports/stage2_gears_backbone_sweep/candidate_manifest.md`
- batch 状态：`reports/stage2_gears_backbone_sweep/batch_run/batch_status.tsv`
- 最终裁决：`reports/stage2_gears_backbone_sweep/final_adjudication.md`

## 实际 sweep budget

该 sweep 是 predefined finite-budget sweep，不是 exhaustive hyperparameter search。

配置层允许轴：

- `epochs`: 20, 30, 40
- `lr`: 0.0005, 0.001, 0.002
- `weight_decay`: 0.000001, 0.00001
- `materialization_export_sanity`: default_only

候选选择规则：

- strategy = `nearest_to_base`
- max_candidates = 6
- 优先保留与 base recipe 距离最近的候选，先比较单轴变化，再比较多轴联动。

实际物化候选：

| rank | variant | epochs | lr | weight_decay | change_count |
|---|---:|---:|---:|---:|---:|
| 1 | `e30_lr1e-03_wd1e-06` | 30 | 0.001 | 0.000001 | 0 |
| 2 | `e30_lr1e-03_wd1e-05` | 30 | 0.001 | 0.00001 | 1 |
| 3 | `e30_lr5e-04_wd1e-06` | 30 | 0.0005 | 0.000001 | 1 |
| 4 | `e30_lr2e-03_wd1e-06` | 30 | 0.002 | 0.000001 | 1 |
| 5 | `e20_lr1e-03_wd1e-06` | 20 | 0.001 | 0.000001 | 1 |
| 6 | `e40_lr1e-03_wd1e-06` | 40 | 0.001 | 0.000001 | 1 |

其中 rank 1 是 base recipe；rank 2-6 是有限预算邻域候选。

## 运行状态

`reports/stage2_gears_backbone_sweep/batch_run/batch_status.tsv` 显示 rank 2-6 均完成 export 和 smoke；rank 3-6 有本轮 train completed 记录，rank 2 使用已有 raw predictions 并完成 export / smoke。

## 结果摘要

来自 `reports/stage2_gears_backbone_sweep/final_adjudication.md`：

- `shared_mean_baseline`
  - `backbone_recovery_score = 0.8067`
  - `structure_vs_context_separation_score = 0.3526`
- `gears_hcc_formal_v1`
  - `backbone_recovery_score = 0.6600`
  - `structure_vs_context_separation_score = 0.4284`
- sweep 最优 backbone 候选：`gears_hcc_formal_v1_e30_lr2e-03_wd1e-06`
  - `backbone_recovery_score = 0.6433`
  - `structure_vs_context_separation_score = 0.4485`

没有候选接近或追平 `shared_mean_baseline` 的 backbone recovery；没有候选超过正式 GEARS recipe 的 backbone recovery。

## 推荐 manuscript 措辞

允许写：

> We performed a predefined finite-budget GEARS neighborhood sweep over epochs, learning rate and weight decay. Six candidate recipes were materialized or re-used according to a nearest-to-base selection rule, including the base recipe and five one-axis variants. The sweep was not intended as an exhaustive hyperparameter search. It tested whether a small local recipe change could close the frozen backbone-recovery gap under the pre-specified stop rule.

允许写：

> No candidate closed the backbone-recovery gap to the shared-mean reference, and no candidate exceeded the formal GEARS recipe for backbone recovery. The stop rule therefore retained GEARS as a separation-biased entrant rather than promoting it to the HCC primary backbone winner.

禁止写：

- exhaustive sweep
- comprehensive hyperparameter optimization
- GEARS has been fully optimized
- GEARS cannot perform better under any training setup

## 结论

Methods 中应采用 `predefined finite-budget neighborhood sweep` 口径，而不是 `broad` 或 `exhaustive` 口径。该 sweep 足以支撑当前 stop-rule adjudication，但不能支撑对 GEARS 全部可能 recipes 的全局最优声明。
