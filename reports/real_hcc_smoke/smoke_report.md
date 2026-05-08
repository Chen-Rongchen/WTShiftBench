# Stage 2 Real HCC Smoke

## 定位

- 本报告只覆盖真实 HCC 输入桥的 smoke adjudication。
- 当前检查 `null_model`、`shared_mean_baseline` 与所有已冻结 entrant 是否成功导出、通过 contract、并可进入 scorer。
- 这仍是 smoke adjudication，不直接上升为 architecture recovery 正式结论。

## 状态

- A/B/C 三层在本报告中固定映射到：`A=canonical_backbone`，`B=shift_excess`，`C=context_deviation`。
- `cosine`、`L2`、`top-20 overlap` 只作为辅助裁决层，用于解释为什么赢/输，不替代 architecture-level 主裁决。

### null_model / HCC38
- export_status = `contract_validated`。
- backbone recovery = `0.500`；shift-excess identification = `0.500`；structure-vs-context separation = `0.000`。
- 辅助数值层（全 targets）：cosine = `0.000`；L2 = `0.388`；top-20 overlap = `0.463`。
- A 层 `canonical_backbone`：cosine = `0.000`；L2 = `0.514`；top-20 overlap = `0.483`。
- B 层 `shift_excess`：cosine = `0.000`；L2 = `0.819`；top-20 overlap = `0.450`。
- C 层 `context_deviation`：cosine = `0.000`；L2 = `0.358`；top-20 overlap = `0.460`。

### null_model / HCC1143
- export_status = `contract_validated`。
- backbone recovery = `0.500`；shift-excess identification = `0.500`；structure-vs-context separation = `0.000`。
- 辅助数值层（全 targets）：cosine = `0.000`；L2 = `0.440`；top-20 overlap = `0.455`。
- A 层 `canonical_backbone`：cosine = `0.000`；L2 = `0.640`；top-20 overlap = `0.508`。
- B 层 `shift_excess`：cosine = `0.000`；L2 = `0.553`；top-20 overlap = `0.450`。
- C 层 `context_deviation`：cosine = `0.000`；L2 = `0.407`；top-20 overlap = `0.448`。

### shared_mean_baseline / HCC38
- export_status = `contract_validated`。
- backbone recovery = `0.773`；shift-excess identification = `0.500`；structure-vs-context separation = `0.357`。
- 辅助数值层（全 targets）：cosine = `0.163`；L2 = `0.448`；top-20 overlap = `0.572`。
- A 层 `canonical_backbone`：cosine = `0.408`；L2 = `0.473`；top-20 overlap = `0.592`。
- B 层 `shift_excess`：cosine = `-0.143`；L2 = `0.885`；top-20 overlap = `0.500`。
- C 层 `context_deviation`：cosine = `0.133`；L2 = `0.433`；top-20 overlap = `0.571`。

### shared_mean_baseline / HCC1143
- export_status = `contract_validated`。
- backbone recovery = `0.840`；shift-excess identification = `0.167`；structure-vs-context separation = `0.348`。
- 辅助数值层（全 targets）：cosine = `0.153`；L2 = `0.528`；top-20 overlap = `0.567`。
- A 层 `canonical_backbone`：cosine = `0.409`；L2 = `0.590`；top-20 overlap = `0.633`。
- B 层 `shift_excess`：cosine = `-0.077`；L2 = `0.656`；top-20 overlap = `0.550`。
- C 层 `context_deviation`：cosine = `0.121`；L2 = `0.516`；top-20 overlap = `0.557`。

### gears_hcc_formal_v1 / HCC38
- export_status = `contract_validated`。
- backbone recovery = `0.600`；shift-excess identification = `0.167`；structure-vs-context separation = `0.426`。
- 辅助数值层（全 targets）：cosine = `0.145`；L2 = `0.580`；top-20 overlap = `0.535`。
- A 层 `canonical_backbone`：cosine = `0.179`；L2 = `0.637`；top-20 overlap = `0.583`。
- B 层 `shift_excess`：cosine = `0.216`；L2 = `0.878`；top-20 overlap = `0.550`。
- C 层 `context_deviation`：cosine = `0.138`；L2 = `0.564`；top-20 overlap = `0.528`。

### gears_hcc_formal_v1 / HCC1143
- export_status = `contract_validated`。
- backbone recovery = `0.720`；shift-excess identification = `0.500`；structure-vs-context separation = `0.431`。
- 辅助数值层（全 targets）：cosine = `0.119`；L2 = `0.674`；top-20 overlap = `0.483`。
- A 层 `canonical_backbone`：cosine = `0.134`；L2 = `0.754`；top-20 overlap = `0.492`。
- B 层 `shift_excess`：cosine = `0.079`；L2 = `0.693`；top-20 overlap = `0.650`。
- C 层 `context_deviation`：cosine = `0.117`；L2 = `0.662`；top-20 overlap = `0.478`。

### gears_hcc_formal_v1_e20_lr1e-03_wd1e-06 / HCC38
- export_status = `contract_validated`。
- backbone recovery = `0.593`；shift-excess identification = `0.500`；structure-vs-context separation = `0.461`。
- 辅助数值层（全 targets）：cosine = `0.164`；L2 = `0.647`；top-20 overlap = `0.501`。
- A 层 `canonical_backbone`：cosine = `0.104`；L2 = `0.726`；top-20 overlap = `0.517`。
- B 层 `shift_excess`：cosine = `-0.006`；L2 = `0.923`；top-20 overlap = `0.450`。
- C 层 `context_deviation`：cosine = `0.177`；L2 = `0.628`；top-20 overlap = `0.500`。

### gears_hcc_formal_v1_e20_lr1e-03_wd1e-06 / HCC1143
- export_status = `contract_validated`。
- backbone recovery = `0.660`；shift-excess identification = `0.500`；structure-vs-context separation = `0.457`。
- 辅助数值层（全 targets）：cosine = `0.237`；L2 = `0.618`；top-20 overlap = `0.514`。
- A 层 `canonical_backbone`：cosine = `0.306`；L2 = `0.703`；top-20 overlap = `0.575`。
- B 层 `shift_excess`：cosine = `0.211`；L2 = `0.784`；top-20 overlap = `0.650`。
- C 层 `context_deviation`：cosine = `0.227`；L2 = `0.601`；top-20 overlap = `0.501`。

### gears_hcc_formal_v1_e30_lr1e-03_wd1e-05 / HCC38
- export_status = `contract_validated`。
- backbone recovery = `0.540`；shift-excess identification = `0.833`；structure-vs-context separation = `0.420`。
- 辅助数值层（全 targets）：cosine = `0.145`；L2 = `0.526`；top-20 overlap = `0.506`。
- A 层 `canonical_backbone`：cosine = `0.226`；L2 = `0.560`；top-20 overlap = `0.517`。
- B 层 `shift_excess`：cosine = `-0.221`；L2 = `0.930`；top-20 overlap = `0.550`。
- C 层 `context_deviation`：cosine = `0.142`；L2 = `0.511`；top-20 overlap = `0.504`。

### gears_hcc_formal_v1_e30_lr1e-03_wd1e-05 / HCC1143
- export_status = `contract_validated`。
- backbone recovery = `0.687`；shift-excess identification = `1.000`；structure-vs-context separation = `0.436`。
- 辅助数值层（全 targets）：cosine = `0.106`；L2 = `0.666`；top-20 overlap = `0.528`。
- A 层 `canonical_backbone`：cosine = `0.213`；L2 = `0.724`；top-20 overlap = `0.592`。
- B 层 `shift_excess`：cosine = `0.269`；L2 = `0.873`；top-20 overlap = `0.550`。
- C 层 `context_deviation`：cosine = `0.086`；L2 = `0.652`；top-20 overlap = `0.518`。

### gears_hcc_formal_v1_e30_lr2e-03_wd1e-06 / HCC38
- export_status = `contract_validated`。
- backbone recovery = `0.580`；shift-excess identification = `1.000`；structure-vs-context separation = `0.423`。
- 辅助数值层（全 targets）：cosine = `0.121`；L2 = `0.548`；top-20 overlap = `0.503`。
- A 层 `canonical_backbone`：cosine = `0.059`；L2 = `0.654`；top-20 overlap = `0.575`。
- B 层 `shift_excess`：cosine = `0.238`；L2 = `0.827`；top-20 overlap = `0.550`。
- C 层 `context_deviation`：cosine = `0.128`；L2 = `0.526`；top-20 overlap = `0.491`。

### gears_hcc_formal_v1_e30_lr2e-03_wd1e-06 / HCC1143
- export_status = `contract_validated`。
- backbone recovery = `0.707`；shift-excess identification = `0.667`；structure-vs-context separation = `0.474`。
- 辅助数值层（全 targets）：cosine = `0.214`；L2 = `0.592`；top-20 overlap = `0.526`。
- A 层 `canonical_backbone`：cosine = `0.339`；L2 = `0.679`；top-20 overlap = `0.550`。
- B 层 `shift_excess`：cosine = `0.470`；L2 = `0.559`；top-20 overlap = `0.550`。
- C 层 `context_deviation`：cosine = `0.189`；L2 = `0.579`；top-20 overlap = `0.521`。

### gears_hcc_formal_v1_e30_lr5e-04_wd1e-06 / HCC38
- export_status = `contract_validated`。
- backbone recovery = `0.533`；shift-excess identification = `1.000`；structure-vs-context separation = `0.429`。
- 辅助数值层（全 targets）：cosine = `0.185`；L2 = `0.575`；top-20 overlap = `0.531`。
- A 层 `canonical_backbone`：cosine = `0.165`；L2 = `0.654`；top-20 overlap = `0.525`。
- B 层 `shift_excess`：cosine = `0.698`；L2 = `0.610`；top-20 overlap = `0.500`。
- C 层 `context_deviation`：cosine = `0.175`；L2 = `0.562`；top-20 overlap = `0.532`。

### gears_hcc_formal_v1_e30_lr5e-04_wd1e-06 / HCC1143
- export_status = `contract_validated`。
- backbone recovery = `0.527`；shift-excess identification = `0.833`；structure-vs-context separation = `0.463`。
- 辅助数值层（全 targets）：cosine = `0.214`；L2 = `0.644`；top-20 overlap = `0.524`。
- A 层 `canonical_backbone`：cosine = `0.272`；L2 = `0.720`；top-20 overlap = `0.625`。
- B 层 `shift_excess`：cosine = `0.325`；L2 = `0.905`；top-20 overlap = `0.500`。
- C 层 `context_deviation`：cosine = `0.203`；L2 = `0.626`；top-20 overlap = `0.510`。

### gears_hcc_formal_v1_e40_lr1e-03_wd1e-06 / HCC38
- export_status = `contract_validated`。
- backbone recovery = `0.387`；shift-excess identification = `0.833`；structure-vs-context separation = `0.490`。
- 辅助数值层（全 targets）：cosine = `0.157`；L2 = `0.561`；top-20 overlap = `0.484`。
- A 层 `canonical_backbone`：cosine = `0.104`；L2 = `0.627`；top-20 overlap = `0.483`。
- B 层 `shift_excess`：cosine = `0.267`；L2 = `0.853`；top-20 overlap = `0.450`。
- C 层 `context_deviation`：cosine = `0.163`；L2 = `0.543`；top-20 overlap = `0.485`。

### gears_hcc_formal_v1_e40_lr1e-03_wd1e-06 / HCC1143
- export_status = `contract_validated`。
- backbone recovery = `0.600`；shift-excess identification = `0.500`；structure-vs-context separation = `0.447`。
- 辅助数值层（全 targets）：cosine = `0.255`；L2 = `0.590`；top-20 overlap = `0.535`。
- A 层 `canonical_backbone`：cosine = `0.311`；L2 = `0.728`；top-20 overlap = `0.567`。
- B 层 `shift_excess`：cosine = `0.356`；L2 = `0.745`；top-20 overlap = `0.600`。
- C 层 `context_deviation`：cosine = `0.244`；L2 = `0.565`；top-20 overlap = `0.529`。

### geneformer_hcc_formal_v1 / HCC38
- export_status = `contract_validated`。
- backbone recovery = `0.493`；shift-excess identification = `0.833`；structure-vs-context separation = `0.423`。
- 辅助数值层（全 targets）：cosine = `0.146`；L2 = `0.402`；top-20 overlap = `0.556`。
- A 层 `canonical_backbone`：cosine = `0.148`；L2 = `0.517`；top-20 overlap = `0.567`。
- B 层 `shift_excess`：cosine = `-0.195`；L2 = `0.851`；top-20 overlap = `0.500`。
- C 层 `context_deviation`：cosine = `0.155`；L2 = `0.373`；top-20 overlap = `0.556`。

### geneformer_hcc_formal_v1 / HCC1143
- export_status = `contract_validated`。
- backbone recovery = `0.573`；shift-excess identification = `0.667`；structure-vs-context separation = `0.380`。
- 辅助数值层（全 targets）：cosine = `0.115`；L2 = `0.462`；top-20 overlap = `0.574`。
- A 层 `canonical_backbone`：cosine = `0.204`；L2 = `0.633`；top-20 overlap = `0.600`。
- B 层 `shift_excess`：cosine = `-0.344`；L2 = `0.595`；top-20 overlap = `0.500`。
- C 层 `context_deviation`：cosine = `0.113`；L2 = `0.433`；top-20 overlap = `0.573`。

### lm_g_geneformer_ridge_hcc_formal_v1 / HCC38
- export_status = `contract_validated`。
- backbone recovery = `0.533`；shift-excess identification = `0.333`；structure-vs-context separation = `0.320`。
- 辅助数值层（全 targets）：cosine = `0.051`；L2 = `0.730`；top-20 overlap = `0.580`。
- A 层 `canonical_backbone`：cosine = `0.089`；L2 = `0.672`；top-20 overlap = `0.575`。
- B 层 `shift_excess`：cosine = `-0.009`；L2 = `0.950`；top-20 overlap = `0.600`。
- C 层 `context_deviation`：cosine = `0.047`；L2 = `0.733`；top-20 overlap = `0.580`。

### lm_g_geneformer_ridge_hcc_formal_v1 / HCC1143
- export_status = `contract_validated`。
- backbone recovery = `0.720`；shift-excess identification = `0.000`；structure-vs-context separation = `0.332`。
- 辅助数值层（全 targets）：cosine = `0.101`；L2 = `0.773`；top-20 overlap = `0.584`。
- A 层 `canonical_backbone`：cosine = `0.222`；L2 = `0.712`；top-20 overlap = `0.617`。
- B 层 `shift_excess`：cosine = `0.199`；L2 = `0.742`；top-20 overlap = `0.650`。
- C 层 `context_deviation`：cosine = `0.081`；L2 = `0.783`；top-20 overlap = `0.577`。

### lm_g_scgpt_ridge_hcc_formal_v1 / HCC38
- export_status = `contract_validated`。
- backbone recovery = `0.500`；shift-excess identification = `0.000`；structure-vs-context separation = `0.253`。
- 辅助数值层（全 targets）：cosine = `0.042`；L2 = `0.756`；top-20 overlap = `0.582`。
- A 层 `canonical_backbone`：cosine = `0.078`；L2 = `0.838`；top-20 overlap = `0.600`。
- B 层 `shift_excess`：cosine = `0.005`；L2 = `0.971`；top-20 overlap = `0.700`。
- C 层 `context_deviation`：cosine = `0.037`；L2 = `0.738`；top-20 overlap = `0.576`。

### lm_g_scgpt_ridge_hcc_formal_v1 / HCC1143
- export_status = `contract_validated`。
- backbone recovery = `0.433`；shift-excess identification = `0.333`；structure-vs-context separation = `0.265`。
- 辅助数值层（全 targets）：cosine = `0.017`；L2 = `0.844`；top-20 overlap = `0.584`。
- A 层 `canonical_backbone`：cosine = `0.088`；L2 = `0.983`；top-20 overlap = `0.625`。
- B 层 `shift_excess`：cosine = `-0.069`；L2 = `0.818`；top-20 overlap = `0.600`。
- C 层 `context_deviation`：cosine = `0.009`；L2 = `0.824`；top-20 overlap = `0.578`。

### lm_train_lowrank_hcc_formal_v1 / HCC38
- export_status = `contract_validated`。
- backbone recovery = `0.560`；shift-excess identification = `0.667`；structure-vs-context separation = `0.278`。
- 辅助数值层（全 targets）：cosine = `0.058`；L2 = `0.669`；top-20 overlap = `0.565`。
- A 层 `canonical_backbone`：cosine = `0.096`；L2 = `0.716`；top-20 overlap = `0.575`。
- B 层 `shift_excess`：cosine = `-0.111`；L2 = `0.931`；top-20 overlap = `0.500`。
- C 层 `context_deviation`：cosine = `0.057`；L2 = `0.655`；top-20 overlap = `0.565`。

### lm_train_lowrank_hcc_formal_v1 / HCC1143
- export_status = `contract_validated`。
- backbone recovery = `0.513`；shift-excess identification = `0.500`；structure-vs-context separation = `0.294`。
- 辅助数值层（全 targets）：cosine = `0.034`；L2 = `0.745`；top-20 overlap = `0.585`。
- A 层 `canonical_backbone`：cosine = `0.193`；L2 = `0.831`；top-20 overlap = `0.642`。
- B 层 `shift_excess`：cosine = `-0.107`；L2 = `0.723`；top-20 overlap = `0.700`。
- C 层 `context_deviation`：cosine = `0.014`；L2 = `0.733`；top-20 overlap = `0.574`。

### scgpt_hcc_formal_v1 / HCC38
- export_status = `contract_validated`。
- backbone recovery = `0.427`；shift-excess identification = `0.500`；structure-vs-context separation = `0.308`。
- 辅助数值层（全 targets）：cosine = `0.089`；L2 = `0.466`；top-20 overlap = `0.540`。
- A 层 `canonical_backbone`：cosine = `0.085`；L2 = `0.593`；top-20 overlap = `0.542`。
- B 层 `shift_excess`：cosine = `0.001`；L2 = `0.879`；top-20 overlap = `0.650`。
- C 层 `context_deviation`：cosine = `0.091`；L2 = `0.436`；top-20 overlap = `0.537`。

### scgpt_hcc_formal_v1 / HCC1143
- export_status = `contract_validated`。
- backbone recovery = `0.467`；shift-excess identification = `0.167`；structure-vs-context separation = `0.281`。
- 辅助数值层（全 targets）：cosine = `0.153`；L2 = `0.519`；top-20 overlap = `0.582`。
- A 层 `canonical_backbone`：cosine = `0.137`；L2 = `0.705`；top-20 overlap = `0.633`。
- B 层 `shift_excess`：cosine = `0.257`；L2 = `0.622`；top-20 overlap = `0.650`。
- C 层 `context_deviation`：cosine = `0.153`；L2 = `0.489`；top-20 overlap = `0.573`。
