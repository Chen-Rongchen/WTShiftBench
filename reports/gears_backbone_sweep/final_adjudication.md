# GEARS HCC Backbone Sweep 最终裁决

## 结论

- 这一轮有限预算 `GEARS backbone sweep` 已全部完成。
- 当前结果不支持继续把 `GEARS` 推为 `HCC primary winner`。
- 本轮 sweep 的更合理收口是：`architecture trade-off diagnosis`。

## stop rule 裁决

项目中预先冻结的 stop rule 是：

> 如果一轮有限预算 sweep 后，`canonical_backbone recovery` 仍不能接近或追平 `shared_mean_baseline`，且任何改进都以明显损失 `structure/context separation` 为代价，则停止继续把 `GEARS` 推为 HCC primary winner，并将当前结果收口为 architecture trade-off diagnosis。

本轮结果满足该 stop rule。

## 关键结果

- `shared_mean_baseline`
  - `backbone_recovery_score = 0.8067`
  - `structure_vs_context_separation_score = 0.3526`
- `gears_hcc_formal_v1`
  - `backbone_recovery_score = 0.6600`
  - `structure_vs_context_separation_score = 0.4284`
- sweep 最优 backbone 候选：`gears_hcc_formal_v1_e30_lr2e-03_wd1e-06`
  - `backbone_recovery_score = 0.6433`
  - `structure_vs_context_separation_score = 0.4485`
- 最后一个候选：`gears_hcc_formal_v1_e40_lr1e-03_wd1e-06`
  - `backbone_recovery_score = 0.4933`
  - `structure_vs_context_separation_score = 0.4684`

## 判定理由

- 没有任何候选接近或追平 `shared_mean_baseline = 0.8067`。
- 没有任何候选超过当前正式 `GEARS = 0.6600` 的 backbone recovery。
- 多个候选继续提高了 `structure_vs_context separation` 或 `shift_excess identification`，但这没有转化为 backbone 补强。
- 因此当前最稳定的解释不是“还差一个小 recipe 就能赢”，而是 `GEARS` 在 HCC primary 任务上表现出较稳定的 `backbone vs separation` 架构 trade-off。

## 本轮 sweep 覆盖范围

- 只允许小范围 recipe 变化：
  - `epoch / checkpoint`
  - `learning rate`
  - `weight decay`
- 未引入：
  - 新模型结构
  - 新 entrant
  - 新 truth object
  - 新评分体系

## 已完成候选

- `gears_hcc_formal_v1_e30_lr1e-03_wd1e-05`
- `gears_hcc_formal_v1_e30_lr5e-04_wd1e-06`
- `gears_hcc_formal_v1_e30_lr2e-03_wd1e-06`
- `gears_hcc_formal_v1_e20_lr1e-03_wd1e-06`
- `gears_hcc_formal_v1_e40_lr1e-03_wd1e-06`

## 后续建议

- 将 `GEARS` 在当前 HCC primary 线路上的定位固定为：
  - 可运行 entrant
  - 可恢复部分 `structure/context separation`
  - 不作为当前 `canonical_backbone recovery` 的主胜出者
- 后续若继续分析，应转到：
  - `architecture trade-off` 的机制解释
  - frozen axis 的 annotation / validation

## 参考产物

- `reports/real_hcc_smoke/model_comparison.tsv`
- `reports/gears_backbone_sweep/batch_run/batch_status.tsv`
- `reports/real_hcc_smoke/backbone_diagnosis.md`
