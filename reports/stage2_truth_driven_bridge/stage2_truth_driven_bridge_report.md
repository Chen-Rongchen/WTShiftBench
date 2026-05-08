# Stage 2 Truth-Driven Bridge v1

## 摘要

- 本报告只覆盖 truth-side bridge，不包含任何 entrant predicted shift。
- `DepMap gene effect` 与 `gene dependency` 并列输出；主报告严格按 dataset role 与 evidence tier 分层。
- 主结论只允许 primary datasets 的 primary truth metrics；supplementary datasets 与非 primary metrics 不进入主结论。

## 主结论

### HCC38
- single-feature cells: `14485`；control cells: `1666`；可分析 targets: `48`。
- DepMap 双端点同时 join 成功率：`97.9%`。
- 单扰动判定：`verified_via_num_features_eq_1`（evidence=`num_features`）。
- `real_shift_mean_abs` vs `depmap_gene_dependency` 的 aligned Spearman = `0.726`（n=`47`）。
- `real_shift_L2` vs `depmap_gene_dependency` 的 aligned Spearman = `0.702`（n=`47`）。
- `real_shift_mean_abs` vs `depmap_gene_effect` 的 aligned Spearman = `0.725`（n=`47`）。
- `real_shift_L2` vs `depmap_gene_effect` 的 aligned Spearman = `0.702`（n=`47`）。

### HCC1143
- single-feature cells: `11636`；control cells: `1325`；可分析 targets: `49`。
- DepMap 双端点同时 join 成功率：`98.0%`。
- 单扰动判定：`verified_via_num_features_eq_1`（evidence=`num_features`）。
- `real_shift_mean_abs` vs `depmap_gene_dependency` 的 aligned Spearman = `0.779`（n=`48`）。
- `real_shift_L2` vs `depmap_gene_dependency` 的 aligned Spearman = `0.761`（n=`48`）。
- `real_shift_mean_abs` vs `depmap_gene_effect` 的 aligned Spearman = `0.781`（n=`48`）。
- `real_shift_L2` vs `depmap_gene_effect` 的 aligned Spearman = `0.763`（n=`48`）。

## 补充证据

### HCC38
- `real_Edistance`（supplementary）vs `depmap_gene_dependency` 的 aligned Spearman = `0.629`（n=`47`）。
- `real_Edistance`（supplementary）vs `depmap_gene_effect` 的 aligned Spearman = `0.629`（n=`47`）。
- `real_DEG_burden`（auxiliary）vs `depmap_gene_dependency` 的 aligned Spearman = `0.551`（n=`47`）。
- `real_DEG_burden`（auxiliary）vs `depmap_gene_effect` 的 aligned Spearman = `0.551`（n=`47`）。

### HCC1143
- `real_Edistance`（supplementary）vs `depmap_gene_dependency` 的 aligned Spearman = `0.741`（n=`48`）。
- `real_Edistance`（supplementary）vs `depmap_gene_effect` 的 aligned Spearman = `0.743`（n=`48`）。
- `real_DEG_burden`（auxiliary）vs `depmap_gene_dependency` 的 aligned Spearman = `0.714`（n=`48`）。
- `real_DEG_burden`（auxiliary）vs `depmap_gene_effect` 的 aligned Spearman = `0.716`（n=`48`）。

## 分组比较

### HCC38
- `real_shift_L2` 分层后，`depmap_gene_effect` 的 aligned_effect_direction = `0.705`（high=`16`，low=`16`）。
- `real_shift_mean_abs` 分层后，`depmap_gene_effect` 的 aligned_effect_direction = `0.705`（high=`16`，low=`16`）。
- `real_Edistance` 分层后，`depmap_gene_effect` 的 aligned_effect_direction = `0.592`（high=`16`，low=`16`）。
- `real_shift_L2` 分层后，`depmap_gene_dependency` 的 aligned_effect_direction = `0.562`（high=`16`，low=`16`）。
- `real_shift_mean_abs` 分层后，`depmap_gene_dependency` 的 aligned_effect_direction = `0.562`（high=`16`，low=`16`）。
- `real_Edistance` 分层后，`depmap_gene_dependency` 的 aligned_effect_direction = `0.420`（high=`16`，low=`16`）。
- `real_DEG_burden` 分层后，`depmap_gene_effect` 的 aligned_effect_direction = `0.279`（high=`29`，low=`18`）。
- `real_DEG_burden` 分层后，`depmap_gene_dependency` 的 aligned_effect_direction = `0.080`（high=`29`，low=`18`）。

### HCC1143
- `real_shift_L2` 分层后，`depmap_gene_effect` 的 aligned_effect_direction = `0.939`（high=`16`，low=`16`）。
- `real_shift_mean_abs` 分层后，`depmap_gene_effect` 的 aligned_effect_direction = `0.929`（high=`16`，low=`16`）。
- `real_shift_L2` 分层后，`depmap_gene_dependency` 的 aligned_effect_direction = `0.842`（high=`16`，low=`16`）。
- `real_shift_mean_abs` 分层后，`depmap_gene_dependency` 的 aligned_effect_direction = `0.841`（high=`16`，low=`16`）。
- `real_Edistance` 分层后，`depmap_gene_effect` 的 aligned_effect_direction = `0.563`（high=`16`，low=`16`）。
- `real_Edistance` 分层后，`depmap_gene_dependency` 的 aligned_effect_direction = `0.521`（high=`16`，low=`16`）。
- `real_DEG_burden` 分层后，`depmap_gene_effect` 的 aligned_effect_direction = `0.430`（high=`15`，low=`17`）。
- `real_DEG_burden` 分层后，`depmap_gene_dependency` 的 aligned_effect_direction = `0.296`（high=`15`，low=`17`）。

## 跨 Cell Line 一致性

- `real_shift_mean_abs` 在 `HCC1143 vs HCC38` 上的 Spearman = `0.859`，centered sign concordance = `0.833`。
- `real_shift_L2` 在 `HCC1143 vs HCC38` 上的 Spearman = `0.843`，centered sign concordance = `0.875`。
- `real_DEG_burden` 在 `HCC1143 vs HCC38` 上的 Spearman = `0.775`，centered sign concordance = `0.708`。
- `real_Edistance` 在 `HCC1143 vs HCC38` 上的 Spearman = `0.766`，centered sign concordance = `0.750`。
- `depmap_gene_dependency` 在 `HCC1143 vs HCC38` 上的 Spearman = `0.739`，centered sign concordance = `0.787`。
- `depmap_gene_effect` 在 `HCC1143 vs HCC38` 上的 Spearman = `0.739`，centered sign concordance = `0.787`。

## 附录

- `aligned` 方向按 endpoint 区分：`gene effect` 为更负，`gene dependency` 为更高。
- `real_DEG_burden` 在 v1 中按 `abs(log1p-normalized delta) >= threshold` 且表达达到 floor 的基因数定义。
- `real_Edistance` 在 v1 中基于同 cell line 单扰动细胞的 log-normalized expression SVD embedding 计算。
