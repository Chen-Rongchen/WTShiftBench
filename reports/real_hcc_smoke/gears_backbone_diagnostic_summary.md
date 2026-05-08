# GEARS Backbone 诊断摘要

## 定位

- 这是 GEARS HCC primary mainline 在正式 recipe sweep 前的最小失败分解产物。
- 它只服务于 `canonical_backbone recovery` 诊断，不引入新 entrant、新 truth object 或新评分体系。
- sweep 必须基于这里的 `failure_mode_call` 才能启动。

## 当前诊断

### HCC38
- GEARS backbone：recovery = `0.600`；cosine = `0.179`；L2 = `0.637`；top-20 = `0.583`。
- reference backbone：recovery = `0.773`；cosine = `0.408`；L2 = `0.473`；top-20 = `0.592`。
- `failure_mode_call = mixed`；`direction_issue = true`；`amplitude_issue = true`；`tradeoff_signal = false`。

### HCC1143
- GEARS backbone：recovery = `0.720`；cosine = `0.134`；L2 = `0.754`；top-20 = `0.492`。
- reference backbone：recovery = `0.840`；cosine = `0.409`；L2 = `0.590`；top-20 = `0.633`。
- `failure_mode_call = tradeoff`；`direction_issue = true`；`amplitude_issue = true`；`tradeoff_signal = true`。

## Sweep 边界

- 允许变化：
- `epoch_or_checkpoint_selection`
- `learning_rate_small_grid`
- `weight_decay_small_grid`
- `hcc_specific_materialization_or_export_sanity`

- 禁止变化：
- `model_architecture`
- `new_entrant`
- `new_truth_object`
- `new_scoring_system`

## Stop Rule

- 如果一轮有限 sweep 后，`canonical_backbone recovery` 仍不能接近或追平 `shared_mean_baseline`，且任何改进都以明显损失 `structure/context separation` 为代价，则停止继续把 `GEARS` 推为 HCC primary winner，并将当前结果收口为 architecture trade-off diagnosis。
