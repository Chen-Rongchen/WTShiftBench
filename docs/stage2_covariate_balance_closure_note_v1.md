# Stage 2 covariate balance closure note v1

## 1. 文档定位

这份文档只回答一个问题：

**当前混杂风险应如何收口，下一步到底要审什么，审完后哪些主张能保留，哪些必须降级？**

它不假装当前已经完成 covariate closure。

## 2. 当前总体判断

当前 `covariate balance closure` 仍是剩余的主要方法学风险。

但要注意，这条线不是“没有实现入口”，而是：

- 底层审计函数已经存在
- CLI 已支持输出
- 第一轮正式审计已完成
- 当前已覆盖 `barcode_gem_group`、`num_umis_quantile_bin`、`num_umis_over_threshold_bin`、`transcriptome_total_signal_quantile_bin` 与 `transcriptome_detected_genes_quantile_bin` 五条 covariate 轴

因此，当前更准确的状态是：

**混杂审计已形成五条已落盘 covariate 轴的正式产物，但 full closure 仍未完成。**

当前这条线最近一步已经进一步收口为：

- `barcode_gem_group` 的 design-layer 含义已完成追查
- 现可正式确认 `HCC38 -> aggrMH001-3`、`HCC1143 -> aggrMH004-6`
- 但仍不能把 `-1/-2/-3` 唯一写成单个 `MH00x`
- 因此这条轴从现在起固定写成 `design-proxy axis`，不再继续上推成已确认 run label

当前更关键的补充是：这条线的主要瓶颈已不再是“没有分析框架”，而是“更深层实验设计元数据的可用性上限”。

在主张层面，这还只能支持“风险已被治理进正式边界”，不能支持“对象已经 fully deconfounded”。

## 3. 现有实现入口

当前已经具备的入口包括：

- [`src/wtbench/stage2_truth_sensitivity.py`](/home/data/gz0705/WTKO/src/wtbench/stage2_truth_sensitivity.py)
  - `audit_covariate_balance(...)`
  - `run_covariate_audit_if_configured(...)`
- [`scripts/run_stage2_truth_bridge_sensitivity.py`](/home/data/gz0705/WTKO/scripts/run_stage2_truth_bridge_sensitivity.py)
  - 若配置存在 `covariates`，会输出 `covariate_balance/*.tsv`
- [`configs/stage2/truth_bridge_sensitivity_covariate_template_v1.json`](/home/data/gz0705/WTKO/configs/stage2/truth_bridge_sensitivity_covariate_template_v1.json)
  - 作为下一步执行模板
- [`configs/stage2/hcc_covariates_v1.json`](/home/data/gz0705/WTKO/configs/stage2/hcc_covariates_v1.json)
  - 物化 `HCC38 / HCC1143` covariates TSV 的正式配置
- [`scripts/materialize_stage2_covariates.py`](/home/data/gz0705/WTKO/scripts/materialize_stage2_covariates.py)
  - 从 `protospacer_calls` 与主线同源的 `matrix/barcodes/features` 物化 protospacer / transcriptome covariates
- [`configs/stage2/truth_bridge_covariate_audit_v1.json`](/home/data/gz0705/WTKO/configs/stage2/truth_bridge_covariate_audit_v1.json)
- [`scripts/run_stage2_covariate_audit.py`](/home/data/gz0705/WTKO/scripts/run_stage2_covariate_audit.py)
- [`reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.md)
  - 当前 `num_umis_quantile_bin` 审计摘要
- [`reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv)
  - 当前新版多轴 covariate audit 的正式汇总表
- [`reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/barcode_gem_group_mapping_note.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/barcode_gem_group_mapping_note.md)
  - `barcode_gem_group` 与 `aggrMH00x` 关系的正式收口说明
- [`reports/stage2_truth_driven_bridge/sensitivity/covariate_balance_threshold_ratio/`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/covariate_balance_threshold_ratio)
  - 第二条 `num_umis_over_threshold_bin / threshold_ratio` 审计结果

当前审计逻辑很明确：

- 按 target vs control 比较指定分层变量的分布
- 报告每个 target 的 `total_variation_distance`
- 同一 cell line 现已支持一次配置多个 `strat_columns`，输出 combined TSV、按轴拆分 TSV 与统一 summary

因此，这条线当前不再缺实现，而是要判断第一轮审计结果足以保留哪些主张、又不足以关闭哪些风险。

目前这条入口已经按新版配置完成了一次正式重跑，`covariate_balance/` 目录下现已同时具备 combined TSV、per-axis TSV、`summary.tsv` 与 `summary.md`。

## 4. 当前不能写什么

即使已有第一轮审计输出，当前仍不能写：

- covariate imbalance excluded
- major confounding ruled out
- all structure claims robust to covariate balance

这些表述现在都过强。

## 5. 第一轮审计当前说明了什么

当前新版五轴审计结果显示：

- `barcode_gem_group` 已可作为一条更接近实验设计 aggregation 结构的代理轴进入正式审计
- 这条轴目前只能被确认到 `aggrMH001-3 / aggrMH004-6` 级别，不能唯一展开到单个 `MH001...MH006`
- `HCC38 / HCC1143` 上这条轴的 `mean_tvd` 分别约为 `0.0529 / 0.0554`
- `HCC38` 上更轻的 transcriptome 轴为 `transcriptome_detected_genes_quantile_bin`，`mean_tvd = 0.0576`
- `HCC1143` 上更轻的 transcriptome 轴为 `transcriptome_detected_genes_quantile_bin`，`mean_tvd = 0.0764`
- 两个 cell line 上最重的总体轴仍来自 protospacer 侧，分别是 `num_umis_quantile_bin` 的 `0.1088 / 0.1332`
- stable shared anchors 中，`PMF1`、`PRPF6`、`ZNF131` 在至少一个 cell line 上都表现出不可忽略的分布差异
- 新增 transcriptome 轴虽然整体更轻，但没有把关键 stable anchors 洗成 fully deconfounded objects
- 新增 `barcode_gem_group` 轴同样没有触发对象级 tier 改写；例如 `HCC38` 上 `PRPF6` 约为 `0.1527`，`HCC1143` 上 `PMF1` 约为 `0.1456`
- 在 `HCC1143` 上，`PMF1` 在 `transcriptome_detected_genes_quantile_bin` 的 `total_variation_distance` 约为 `0.2555`，说明新增轴并未统一朝“更干净”方向推进

因此，这轮审计支持的不是“confounding 已排除”，而是：

- 第一轮混杂风险已经被显式量化
- `barcode_gem_group` 已足以进入正式边界，但应固定写成 `design-proxy axis`
- 某些主支柱对象需要保留更强的方法学谨慎
- `structural stability` 与 `covariate cleanliness` 必须分开写
- 当前降级治理已经可以进入 claim boundary，但仍不足以写成 fully deconfounded closure
- 五条 covariate 轴已落盘、风险已治理进边界，但 covariate closure 本身仍未 fully closed

## 6. 当前最稳的过渡写法

在混杂 closure 完成之前，当前更稳的写法应是：

- 当前主要结构信号来自 truth-side decomposition、bootstrap stability 与 model-side adjudication 的共同支持
- 但 covariate balance 审计尚未形成 fully closed 的正式 closure
- `barcode_gem_group` 当前应被理解为聚合样本内部的 gem-group 分层代理，而不是已解析到单个 `MH00x` 的 design label
- 当前剩余缺口主要受实验设计元数据上限约束，而不是分析框架缺位
- 因此，涉及更细 context deviation 或更弱 axis 的主张，仍需保留方法学谨慎边界

换句话说：

- 主支柱结论可保留
- 次级对象与更细机制化解释应更保守

## 7. 下一步正式执行清单

### 7.1 准备更丰富的 covariates 输入

当前 protospacer / transcriptome 两侧的基础分层已经跑通。下一步若还要继续推进，应优先补更贴近实验设计批次结构的 covariates TSV，至少包含：

- `cell_barcode`
- 一个用于分层审计的 `strat_column`

推荐先从最直接、最可能造成 target/control 分布偏移的变量开始。

但对于当前 HCC 主线，需要同步一条 stop rule：

- 在没有新的 run-level metadata 前，不再继续把 `barcode_gem_group` 追写成单个 `MH00x`
- 默认直接沿用 `design-proxy axis` 这一定稿口径

### 7.2 配置与物化入口

当前已具备两层入口：

- [`configs/stage2/truth_bridge_sensitivity_covariate_template_v1.json`](/home/data/gz0705/WTKO/configs/stage2/truth_bridge_sensitivity_covariate_template_v1.json)
- [`configs/stage2/hcc_covariates_v1.json`](/home/data/gz0705/WTKO/configs/stage2/hcc_covariates_v1.json)
- [`configs/stage2/truth_bridge_covariate_audit_v1.json`](/home/data/gz0705/WTKO/configs/stage2/truth_bridge_covariate_audit_v1.json)

### 7.3 运行并生成正式产物

先物化 covariates：

- [`scripts/materialize_stage2_covariates.py`](/home/data/gz0705/WTKO/scripts/materialize_stage2_covariates.py)

再运行：

- [`scripts/run_stage2_covariate_audit.py`](/home/data/gz0705/WTKO/scripts/run_stage2_covariate_audit.py)

目标产物：

- `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/HCC38_target_control_balance.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/HCC1143_target_control_balance.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/HCC38_num_umis_quantile_bin_target_control_balance.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/HCC38_num_umis_over_threshold_bin_target_control_balance.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/HCC38_transcriptome_total_signal_quantile_bin_target_control_balance.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/HCC38_transcriptome_detected_genes_quantile_bin_target_control_balance.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv`
- `reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.md`

### 7.4 审计后做三分法裁决

每条主张都应被归到三类之一：

- 审计后仍稳，可保留
- 存在一定风险，只能降级
- 混杂风险过高，暂不进入正式主张

## 8. 推荐裁决原则

当前建议按以下原则收口：

- stable shared anchors 若在后续更完整的 covariate audit 后仍无明显 target-specific imbalance，可继续保留为主支柱
- 在当前五条 covariate 轴与 design-proxy 边界下，`PFDN5` 可暂时保留为相对更轻风险对象
- `PMF1`、`PRPF6`、`ZNF131` 当前更适合降级为 `supporting_but_covariate_exposed`
- `transcription / chromatin` 若 formal positive axis 的支持不依赖明显分层偏移，可继续保留为 formal positive axis
- 更弱的 axis、context-specific deviation 与 discovery-like 对象，若混杂风险明显，应优先降级而不是硬保留

## 9. 渐进披露

默认先看：

1. [`src/wtbench/stage2_truth_sensitivity.py`](/home/data/gz0705/WTKO/src/wtbench/stage2_truth_sensitivity.py)
2. [`scripts/run_stage2_truth_bridge_sensitivity.py`](/home/data/gz0705/WTKO/scripts/run_stage2_truth_bridge_sensitivity.py)
3. [`reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.md)
4. [`configs/stage2/truth_bridge_covariate_audit_v1.json`](/home/data/gz0705/WTKO/configs/stage2/truth_bridge_covariate_audit_v1.json)
5. [`reports/stage2_truth_driven_bridge/sensitivity/anchor_covariate_screen.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/anchor_covariate_screen.md)
6. [`reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/barcode_gem_group_mapping_note.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/barcode_gem_group_mapping_note.md)

若要继续写作，再看：

- [`docs/stage2_sensitivity_full_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_sensitivity_full_closure_note_v1.md)
- [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)

## 10. 一句话收口

当前混杂 closure 的关键，不是再发明新方法，而是把第一轮 covariate audit 结果纳入正式边界，并在元数据上限明确存在的前提下，把 `barcode_gem_group` 固定收口为 `design-proxy axis`，再重新划定哪些主张仍稳、哪些必须降级。
