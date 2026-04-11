# Stage 2 sensitivity full closure note v1

## 1. 文档定位

这份文档只回答一个问题：

**当前 sensitivity 哪些已经足够关闭，哪些仍是实质风险，哪些只能降级写成 limitation？**

它不重跑结果，也不把 partial snapshot 误写成 full closure。

## 2. 当前总体判断

当前 sensitivity 不是“完全没做”，而是“主支柱材料已经基本齐备，但 full closure 仍未完成”。

更准确地说：

- `cutoff sensitivity`
- `bootstrap stability`
- `control subsampling`

这三条线已经足够支持一版正式的 sensitivity 收口；与此同时：

- `formal interval claim` 已完成配置重复数并达到可引用状态
- `covariate balance closure` 仍未完成

因此，现阶段更稳的写法不是“robustness 已全面建立”，而是：

**主支柱信号已获得保守稳健性支持，formal interval 已可引用，但 sensitivity full closure 仍保留由 covariate closure 带来的剩余方法学缺口。**

这里需要额外固定一条边界：当前 sensitivity 的主要未闭环项，不应再被叙述成“分析框架还不够”，而应被叙述成“formal interval claim 已可引用，但 covariate closure 仍受可用元数据上限约束”。

也就是说，当前 sensitivity 的 formal interval 已经 fully citable，但 sensitivity full closure 仍不能被写成 fully closed。

## 3. 哪些 sensitivity 已经足够关闭

### 3.1 target anchor cutoff sensitivity

当前 `anchor_cutoff_sensitivity` 与 `evidence_tier_summary` 已经足够支持如下保守结论：

- `PFDN5`
- `PMF1`
- `PRPF6`
- `ZNF131`

这四个对象可以继续保留为当前最稳的 shared anchors。

更重要的是，这一步已经把 anchor 主张从“单次 cutoff 偶然命中”收成了“跨 cutoff 仍保持 anchor 身份”的保守写法。

因此：

- anchor 主支柱已足够关闭
- cutoff-sensitive 对象仍应明确降级为 `supporting_but_sensitive`

### 3.2 axis bootstrap stability

当前 `axis_bootstrap_stability.tsv` 已经足够支持两条边界：

- `transcription / chromatin` 是当前唯一稳的 formal positive axis
- 多数其余 axis 即使 bootstrap 下稳定，也仍只是 `preliminary` 或 `mixed_or_low_signal`

这条线的价值不在于“证明很多 axis 都成立”，而在于：

- 它支持“formal axis evidence 仍然有限”
- 它支持“多数 axis 不能升级成 stronger claim”

因此，这条 sensitivity 已经足够关闭为一条主张边界。

### 3.3 control subsampling

当前 `control_subsample_summary.tsv` 显示：

- `real_shift_L2`
- `real_shift_mean_abs`
- `real_shift_top20_mean`
- `real_Edistance`

在 `HCC38 / HCC1143` 上都保持较强、较稳定的 aligned correlation。

同时，`control_subsample_rank_stability.tsv` 显示：

- 多数 shift-based truth metric 与 baseline 的 target rank 一致性很高

因此，当前更稳的写法是：

- shift-based truth signal 对 control subsampling 整体较稳
- 它足够支持当前 bridge 主支柱不是 control 随机抽样假象

## 4. 哪些 sensitivity 仍是实质风险

### 4.1 DEG burden threshold sensitivity

`deg_threshold_sweep.tsv` 已经表明：

- `DEG burden` 与 aligned gene effect 的相关性对阈值更敏感
- 尤其在 `HCC38` 上，阈值变化会带来更明显波动

因此，`DEG burden` 当前不适合作为与 shift-based truth 同等级的主支柱。

更稳的定位应是：

- 作为 supporting / auxiliary metric 保留
- 不作为 formal bridge 成立与否的唯一支柱

### 4.2 covariate balance

当前脚本和底层实现已经支持 `covariate_balance` 审计，且第一轮正式产物已经生成。

因此，这条线当前仍是剩余方法学风险，而不是已关闭事项。

当前不能写：

- covariate risk excluded
- covariate balance established

当前只能写：

- covariate audit 已完成第一轮量化
- 但 full closure 仍待完成
- sensitivity full closure 目前仍不能单独推出 `robustness fully established`
- formal interval 已可引用，但 full closure 仍被 covariate 未闭环卡住

更准确地说，当前新版五轴审计已经提示：部分 stable shared anchors 仍存在不可忽略的 target-control 分布差异，因此混杂线现在应被写成“已有正式审计，但尚未关闭”，而不是“尚未开始”。

当前这条边界现在还有一个更具体的落点：新版 `covariate_balance` 目录下已经补齐 `summary.tsv`、`summary.md`、combined TSV 与按轴拆分 TSV，并且新增了 `barcode_gem_group` 这条更接近实验设计 aggregation 结构的代理轴，以及 transcriptome 总信号与检测基因数两条分层轴。因此“covariate 审计已形成正式产物”现在不再只是原则性表述，而是已被新版正式输出落实。

从最新 summary 看，新增 transcriptome 轴的总体 `mean_tvd` 低于 protospacer `num_umis` 轴，但它们并没有触发对象级 tier 改写；例如 `HCC1143` 的 `PMF1` 在 `transcriptome_detected_genes_quantile_bin` 上仍达到约 `0.2555`。因此，当前可写成“边界更实”，不能写成“混杂已洗净”。

## 5. 哪些只能降级写成 limitation

### 5.1 formal interval claim

[`reports/stage2_truth_driven_bridge/sensitivity/sensitivity_report.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/sensitivity_report.md)
当前标注为：

- `configured_replicates = 24`
- `completed_replicates = 24`
- `formal_interval_citable = true`

因此，当前这条线已经完成从“partial snapshot”到“formal interval citable”的推进，支持：

- 正式引用 control subsampling 的区间/分位数结果
- 将 control subsampling 从 supporting stability 升级为可引用的 sensitivity 支柱

但它仍不等于 full formal closure，因为 covariate 线尚未 fully closed。

## 6. 推荐写法

当前最稳的 sensitivity 收口可写成：

当前 sensitivity 分析表明，truth bridge 的主支柱信号已获得一版保守稳健性支持。具体而言，stable shared anchors 在 cutoff sensitivity 下保持较高稳定性，`transcription / chromatin` 作为唯一 formal positive axis 在 bootstrap 审计下保持稳定，而多数其他 axis 仍应停留在 preliminary 或 mixed-signal 层级。与此同时，shift-based truth metrics 对 control subsampling 整体较稳，且当前已达到配置重复数，使 formal interval 结果可以正式引用，说明当前主 bridge 信号并非 control 随机抽样的偶然结果。需要同时强调的是，`DEG burden` 对阈值更敏感，因此更适合作为 supporting metric；此外，covariate balance 审计当前仍未完全关闭，其剩余缺口还受实验设计元数据上限约束，因而 sensitivity full closure 仍应保留剩余方法学风险与明确 limitation。

## 7. 渐进披露

默认先看：

1. [`reports/stage2_truth_driven_bridge/sensitivity/sensitivity_report.md`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/sensitivity_report.md)
2. [`reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_bridge_decomposition/evidence_tier_summary.tsv)
3. [`reports/stage2_truth_bridge_decomposition/axis_bootstrap_stability.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_bridge_decomposition/axis_bootstrap_stability.tsv)
4. [`reports/stage2_truth_driven_bridge/sensitivity/control_subsample_summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/control_subsample_summary.tsv)
5. [`reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/covariate_balance/summary.tsv)

若要继续执行，再看：

- [`docs/stage2_covariate_balance_closure_note_v1.md`](/home/data/gz0705/WTKO/docs/stage2_covariate_balance_closure_note_v1.md)
- [`configs/stage2/truth_bridge_sensitivity_covariate_template_v1.json`](/home/data/gz0705/WTKO/configs/stage2/truth_bridge_sensitivity_covariate_template_v1.json)

## 8. 一句话收口

当前 sensitivity 已足够支持“主支柱保守稳健、formal interval 可引用、但 full closure 仍受 covariate 线限制”这一版本的正式写法；它还不能被收口成 fully closed。
