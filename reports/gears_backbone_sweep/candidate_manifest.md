# GEARS Backbone Sweep 候选

## 定位

- 这是 GEARS HCC primary mainline 的有限预算 backbone sweep 候选物化清单。
- 这里只物化 recipe，不扩模型、不扩 truth object、不引入新评分体系。
- 当前诊断摘要：`HCC38=mixed, HCC1143=tradeoff`。

## 候选选择策略

- strategy = `nearest_to_base`
- max_candidates = `6`
- 选择原则：优先保留与 base recipe 距离最近的候选，先比较单轴变化，再比较多轴联动。

## 候选列表

- rank `1`：`e30_lr1e-03_wd1e-06`，epochs = `30`，lr = `0.001`，weight_decay = `1e-06`，change_count = `0`。
- rank `2`：`e30_lr1e-03_wd1e-05`，epochs = `30`，lr = `0.001`，weight_decay = `1e-05`，change_count = `1`。
- rank `3`：`e30_lr5e-04_wd1e-06`，epochs = `30`，lr = `0.0005`，weight_decay = `1e-06`，change_count = `1`。
- rank `4`：`e30_lr2e-03_wd1e-06`，epochs = `30`，lr = `0.002`，weight_decay = `1e-06`，change_count = `1`。
- rank `5`：`e20_lr1e-03_wd1e-06`，epochs = `20`，lr = `0.001`，weight_decay = `1e-06`，change_count = `1`。
- rank `6`：`e40_lr1e-03_wd1e-06`，epochs = `40`，lr = `0.001`，weight_decay = `1e-06`，change_count = `1`。

## Stop Rule

- 如果一轮有限 sweep 后，canonical_backbone recovery 仍不能接近或追平 shared_mean_baseline，且任何改进都以明显损失 structure/context separation 为代价，则停止继续把 GEARS 推为 HCC primary winner，并将当前结果收口为 architecture trade-off diagnosis。
