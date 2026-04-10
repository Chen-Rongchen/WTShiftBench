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
- 当前已覆盖 `num_umis_quantile_bin` 与 `num_umis_over_threshold_bin` 两条 covariate 轴

因此，当前更准确的状态是：

**混杂审计已形成两条已落盘 covariate 轴的正式产物，但 full closure 仍未完成。**

当前更关键的补充是：这条线的主要瓶颈已不再是“没有分析框架”，而是“更深层实验设计元数据的可用性上限”。

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
  - 从 `protospacer_calls` 物化 `num_umis_quantile_bin`
- [`configs/stage2/truth_bridge_covariate_audit_v1.json`](/home/data/gz0705/WTKO/configs/stage2/truth_bridge_covariate_audit_v1.json)
- [`scripts/run_stage2_covariate_audit.py`](/home/data/gz0705/WTKO/scripts/run_stage2_covariate_audit.py)
- [`reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.md)
  - 当前 `num_umis_quantile_bin` 审计摘要
- [`reports/stage2_truth_driven_bridge/sensitivity/covariate_balance_threshold_ratio/`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/covariate_balance_threshold_ratio)
  - 第二条 `num_umis_over_threshold_bin / threshold_ratio` 审计结果

当前审计逻辑很明确：

- 按 target vs control 比较指定分层变量的分布
- 报告每个 target 的 `total_variation_distance`
- 同一 cell line 现已支持一次配置多个 `strat_columns`，输出 combined TSV、按轴拆分 TSV 与统一 summary

因此，这条线当前不再缺实现，而是要判断第一轮审计结果足以保留哪些主张、又不足以关闭哪些风险。

## 4. 当前不能写什么

即使已有第一轮审计输出，当前仍不能写：

- covariate imbalance excluded
- major confounding ruled out
- all structure claims robust to covariate balance

这些表述现在都过强。

## 5. 第一轮审计当前说明了什么

第一轮按 `num_umis_quantile_bin` 的审计结果显示：

- `HCC38` 的 target-level `total_variation_distance` 均值约为 `0.1088`
- `HCC1143` 的 target-level `total_variation_distance` 均值约为 `0.1332`
- stable shared anchors 中，`PMF1`、`PRPF6`、`ZNF131` 在至少一个 cell line 上都表现出不可忽略的分布差异
- 第二条 `threshold_ratio` 审计轴虽然让整体 imbalance 略有下降，但没有把关键 stable anchors 洗成 fully deconfounded objects

因此，这轮审计支持的不是“confounding 已排除”，而是：

- 第一轮混杂风险已经被显式量化
- 某些主支柱对象需要保留更强的方法学谨慎
- `structural stability` 与 `covariate cleanliness` 必须分开写
- 当前降级治理已经可以进入 claim boundary，但仍不足以写成 fully deconfounded closure

## 6. 当前最稳的过渡写法

在混杂 closure 完成之前，当前更稳的写法应是：

- 当前主要结构信号来自 truth-side decomposition、bootstrap stability 与 model-side adjudication 的共同支持
- 但 covariate balance 审计尚未形成正式 closure
- 当前剩余缺口主要受实验设计元数据上限约束，而不是分析框架缺位
- 因此，涉及更细 context deviation 或更弱 axis 的主张，仍需保留方法学谨慎边界

换句话说：

- 主支柱结论可保留
- 次级对象与更细机制化解释应更保守

## 7. 下一步正式执行清单

### 7.1 准备更丰富的 covariates 输入

当前 `num_umis` 分层已经跑通。下一步应继续补充更接近实验设计的 covariates TSV，至少包含：

- `cell_barcode`
- 一个用于分层审计的 `strat_column`

推荐先从最直接、最可能造成 target/control 分布偏移的变量开始。

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
- 在当前两条 covariate 轴下，`PFDN5` 可暂时保留为相对更轻风险对象
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

若要继续写作，再看：

- [`docs/stage2_sensitivity_full_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_sensitivity_full_closure_note_v1.md)
- [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)

## 10. 一句话收口

当前混杂 closure 的关键，不是再发明新方法，而是把第一轮 covariate audit 结果纳入正式边界，并在元数据上限明确存在的前提下，继续补更贴近实验设计的 covariate 轴，重新划定哪些主张仍稳、哪些必须降级。
