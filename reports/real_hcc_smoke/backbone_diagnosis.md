# GEARS Backbone 诊断摘要

## 定位

- 这是 GEARS 正式 recipe sweep 前的最小诊断中间产物。
- 它只服务于 `canonical_backbone recovery` 的失败分解，不引入新 truth object、entrant 或评分体系。
- `failure_mode_call` 固定限制为：`direction / amplitude / tradeoff / mixed`。

## 诊断口径

- `direction`：backbone cosine 明显落后，但 top-20 overlap 没有同步明显变差，优先怀疑方向没有学到。
- `amplitude`：backbone L2 明显落后，但 cosine 没有同步明显变差，优先怀疑幅度校准。
- `tradeoff`：backbone recovery 落后，同时 separation 明显更强，按 backbone-vs-separation trade-off 处理。
- `mixed`：不能被单一 failure mode 干净解释。

## 结果

### gears_hcc_formal_v1 / HCC38
- backbone: recovery = `0.600`；cosine = `0.179`；L2 = `0.637`；top-20 = `0.583`。
- baseline: recovery = `0.773`；cosine = `0.408`；L2 = `0.473`；top-20 = `0.592`。
- separation: entrant = `0.426`；baseline = `0.357`。
- failure_mode_call = `mixed`。

### gears_hcc_formal_v1 / HCC1143
- backbone: recovery = `0.720`；cosine = `0.134`；L2 = `0.754`；top-20 = `0.492`。
- baseline: recovery = `0.840`；cosine = `0.409`；L2 = `0.590`；top-20 = `0.633`。
- separation: entrant = `0.431`；baseline = `0.348`。
- failure_mode_call = `tradeoff`。

### gears_hcc_formal_v1_e20_lr1e-03_wd1e-06 / HCC38
- backbone: recovery = `0.593`；cosine = `0.104`；L2 = `0.726`；top-20 = `0.517`。
- baseline: recovery = `0.773`；cosine = `0.408`；L2 = `0.473`；top-20 = `0.592`。
- separation: entrant = `0.461`；baseline = `0.357`。
- failure_mode_call = `mixed`。

### gears_hcc_formal_v1_e20_lr1e-03_wd1e-06 / HCC1143
- backbone: recovery = `0.660`；cosine = `0.306`；L2 = `0.703`；top-20 = `0.575`。
- baseline: recovery = `0.840`；cosine = `0.409`；L2 = `0.590`；top-20 = `0.633`。
- separation: entrant = `0.457`；baseline = `0.348`。
- failure_mode_call = `mixed`。

### gears_hcc_formal_v1_e30_lr1e-03_wd1e-05 / HCC38
- backbone: recovery = `0.540`；cosine = `0.226`；L2 = `0.560`；top-20 = `0.517`。
- baseline: recovery = `0.773`；cosine = `0.408`；L2 = `0.473`；top-20 = `0.592`。
- separation: entrant = `0.420`；baseline = `0.357`。
- failure_mode_call = `mixed`。

### gears_hcc_formal_v1_e30_lr1e-03_wd1e-05 / HCC1143
- backbone: recovery = `0.687`；cosine = `0.213`；L2 = `0.724`；top-20 = `0.592`。
- baseline: recovery = `0.840`；cosine = `0.409`；L2 = `0.590`；top-20 = `0.633`。
- separation: entrant = `0.436`；baseline = `0.348`。
- failure_mode_call = `mixed`。

### gears_hcc_formal_v1_e30_lr2e-03_wd1e-06 / HCC38
- backbone: recovery = `0.580`；cosine = `0.059`；L2 = `0.654`；top-20 = `0.575`。
- baseline: recovery = `0.773`；cosine = `0.408`；L2 = `0.473`；top-20 = `0.592`。
- separation: entrant = `0.423`；baseline = `0.357`。
- failure_mode_call = `mixed`。

### gears_hcc_formal_v1_e30_lr2e-03_wd1e-06 / HCC1143
- backbone: recovery = `0.707`；cosine = `0.339`；L2 = `0.679`；top-20 = `0.550`。
- baseline: recovery = `0.840`；cosine = `0.409`；L2 = `0.590`；top-20 = `0.633`。
- separation: entrant = `0.474`；baseline = `0.348`。
- failure_mode_call = `tradeoff`。

### gears_hcc_formal_v1_e30_lr5e-04_wd1e-06 / HCC38
- backbone: recovery = `0.533`；cosine = `0.165`；L2 = `0.654`；top-20 = `0.525`。
- baseline: recovery = `0.773`；cosine = `0.408`；L2 = `0.473`；top-20 = `0.592`。
- separation: entrant = `0.429`；baseline = `0.357`。
- failure_mode_call = `mixed`。

### gears_hcc_formal_v1_e30_lr5e-04_wd1e-06 / HCC1143
- backbone: recovery = `0.527`；cosine = `0.272`；L2 = `0.720`；top-20 = `0.625`。
- baseline: recovery = `0.840`；cosine = `0.409`；L2 = `0.590`；top-20 = `0.633`。
- separation: entrant = `0.463`；baseline = `0.348`。
- failure_mode_call = `mixed`。

### gears_hcc_formal_v1_e40_lr1e-03_wd1e-06 / HCC38
- backbone: recovery = `0.387`；cosine = `0.104`；L2 = `0.627`；top-20 = `0.483`。
- baseline: recovery = `0.773`；cosine = `0.408`；L2 = `0.473`；top-20 = `0.592`。
- separation: entrant = `0.490`；baseline = `0.357`。
- failure_mode_call = `tradeoff`。

### gears_hcc_formal_v1_e40_lr1e-03_wd1e-06 / HCC1143
- backbone: recovery = `0.600`；cosine = `0.311`；L2 = `0.728`；top-20 = `0.567`。
- baseline: recovery = `0.840`；cosine = `0.409`；L2 = `0.590`；top-20 = `0.633`。
- separation: entrant = `0.447`；baseline = `0.348`。
- failure_mode_call = `mixed`。

### geneformer_hcc_formal_v1 / HCC38
- backbone: recovery = `0.493`；cosine = `0.148`；L2 = `0.517`；top-20 = `0.567`。
- baseline: recovery = `0.773`；cosine = `0.408`；L2 = `0.473`；top-20 = `0.592`。
- separation: entrant = `0.423`；baseline = `0.357`。
- failure_mode_call = `mixed`。

### geneformer_hcc_formal_v1 / HCC1143
- backbone: recovery = `0.573`；cosine = `0.204`；L2 = `0.633`；top-20 = `0.600`。
- baseline: recovery = `0.840`；cosine = `0.409`；L2 = `0.590`；top-20 = `0.633`。
- separation: entrant = `0.380`；baseline = `0.348`。
- failure_mode_call = `direction`。

### lm_g_geneformer_ridge_hcc_formal_v1 / HCC38
- backbone: recovery = `0.533`；cosine = `0.089`；L2 = `0.672`；top-20 = `0.575`。
- baseline: recovery = `0.773`；cosine = `0.408`；L2 = `0.473`；top-20 = `0.592`。
- separation: entrant = `0.320`；baseline = `0.357`。
- failure_mode_call = `direction`。

### lm_g_geneformer_ridge_hcc_formal_v1 / HCC1143
- backbone: recovery = `0.720`；cosine = `0.222`；L2 = `0.712`；top-20 = `0.617`。
- baseline: recovery = `0.840`；cosine = `0.409`；L2 = `0.590`；top-20 = `0.633`。
- separation: entrant = `0.332`；baseline = `0.348`。
- failure_mode_call = `direction`。

### lm_g_scgpt_ridge_hcc_formal_v1 / HCC38
- backbone: recovery = `0.500`；cosine = `0.078`；L2 = `0.838`；top-20 = `0.600`。
- baseline: recovery = `0.773`；cosine = `0.408`；L2 = `0.473`；top-20 = `0.592`。
- separation: entrant = `0.253`；baseline = `0.357`。
- failure_mode_call = `direction`。

### lm_g_scgpt_ridge_hcc_formal_v1 / HCC1143
- backbone: recovery = `0.433`；cosine = `0.088`；L2 = `0.983`；top-20 = `0.625`。
- baseline: recovery = `0.840`；cosine = `0.409`；L2 = `0.590`；top-20 = `0.633`。
- separation: entrant = `0.265`；baseline = `0.348`。
- failure_mode_call = `direction`。

### lm_train_lowrank_hcc_formal_v1 / HCC38
- backbone: recovery = `0.560`；cosine = `0.096`；L2 = `0.716`；top-20 = `0.575`。
- baseline: recovery = `0.773`；cosine = `0.408`；L2 = `0.473`；top-20 = `0.592`。
- separation: entrant = `0.278`；baseline = `0.357`。
- failure_mode_call = `direction`。

### lm_train_lowrank_hcc_formal_v1 / HCC1143
- backbone: recovery = `0.513`；cosine = `0.193`；L2 = `0.831`；top-20 = `0.642`。
- baseline: recovery = `0.840`；cosine = `0.409`；L2 = `0.590`；top-20 = `0.633`。
- separation: entrant = `0.294`；baseline = `0.348`。
- failure_mode_call = `direction`。

### scgpt_hcc_formal_v1 / HCC38
- backbone: recovery = `0.427`；cosine = `0.085`；L2 = `0.593`；top-20 = `0.542`。
- baseline: recovery = `0.773`；cosine = `0.408`；L2 = `0.473`；top-20 = `0.592`。
- separation: entrant = `0.308`；baseline = `0.357`。
- failure_mode_call = `direction`。

### scgpt_hcc_formal_v1 / HCC1143
- backbone: recovery = `0.467`；cosine = `0.137`；L2 = `0.705`；top-20 = `0.633`。
- baseline: recovery = `0.840`；cosine = `0.409`；L2 = `0.590`；top-20 = `0.633`。
- separation: entrant = `0.281`；baseline = `0.348`。
- failure_mode_call = `direction`。
