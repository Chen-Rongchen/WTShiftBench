# WT Benchmark 长期协议蓝图

## 1. 文档定位

这份文档定义长期制度，不等同于当前实现状态，也不是近期执行清单。

它回答三类问题：

- WT Benchmark 长期要评什么
- Stage 1A / Stage 1B / Stage 2 / Stage 3 的正式制度边界是什么
- 输出契约、资格治理、聚合规则与 claim discipline 应如何冻结

当前仓库近期开发顺序看 `plan.md`；当前真实可运行事实看 `README.md`。

## 2. 研究定位与非目标

### 2.1 项目定位

本项目不开发新的扰动预测模型，而是构建一个面向黑盒 prediction engine 的制度化评测框架。

`GEARS`、`scGPT`、`Geneformer` 以及其他 entrant 都被视为 prediction engine。benchmark 统一约束的是：

- entrant 身份与 recipe 是否可审计
- 输出是否满足统一 contract
- 在正式 truth 上是否具有可比较、可复现的预测能力

本框架长期回答三个核心问题：

1. `Stage 1`：模型在分子层面是否真的能预测 perturbation 后的 transcriptomic shift
2. `Stage 2`：模型输出的 shift 是否与长期 dependency / gene effect 存在真实、非随机、可审计的 bridge
3. `Stage 3`：在严格 clean gate 与假阳性治理下，能否识别 phenotype shifter candidates

### 2.2 非目标

本项目明确不做以下事情：

- 不训练新的 `WT -> KO` 生成模型
- 不在 `Stage 1` 使用 `DepMap` 信息反向调参或反向构造最优评估空间
- 不做 pred-real 联合 integration 或联合 batch correction
- 不允许在看到结果后回调 primary thresholds 以挽救主结论
- 不允许在看到四条 formal lanes 的结果后，事后挑选“最好看”的单 lane 挽救正式结论
- 不允许把 `exploratory_admissible` 或 `blocked` 结果包装成 formal downstream claim
- 不允许把 `Stage 3` candidate 直接上升为 causal driver、validated mechanism 或 therapeutic target

## 3. 总体叙事

长期主叙事是：

- `Benchmarking`：先证明模型“算得准”
- `Bridge`：再证明模型输出“有功能意义”
- `Discovery`：最后在严格制度约束下做 candidate discovery

这是一个 `Benchmarking -> Bridge -> Discovery` 的闭环，而不是单纯做 pooled leaderboard。

## 4. 全局制度与核心原则

### 4.1 正式评估对象

正式评估对象始终是 `predicted_shift vs real_shift`，而不是 raw expression。

### 4.2 主评分尺度

长期主评分尺度统一为 `log-normalized pseudobulk delta space`。

要求：

- 主分析单位为 `perturbation-level pseudobulk delta`
- `Stage 1` 与 `Stage 2` 共用同一类 delta constitution，而不是要求同一 gene universe
- 主分析默认不做 gene-wise scaling
- standardized delta 只允许作为 sensitivity 分析

本节定义的是长期 `canonical scoring space`，而非对当前仓库任一实现版本的事实描述。若某一实现版本仍处于过渡态，其与本节之间的差异应由独立的 implementation report / audit report 记录与解释，而不得反向改写本节的长期制度定义。

### 4.2A Stage 1A 双层边界

对当前 `Stage 1A`，长期必须显式区分两层：

#### benchmark-invariant layer

与具体模型无关，负责：

- truth
- evaluation eligibility
- baselines / nulls
- ingest
- evaluate
- render
- pass skeleton

#### model-specific adapter layer

与具体模型有关，负责：

- 从同一 biological / formal source 派生模型原生输入
- 执行模型推理
- 将模型输出转换成统一 benchmark contract：`predicted_shift`

固定边界应表达为：

```text
formal source shared
-> model-native adapter
-> model prediction
-> predicted_shift contract
-> benchmark-invariant scoring
```

制度含义：

- 共享的是 formal source，不是“所有模型必须吃同一种输入矩阵”
- 统一的是 `predicted_shift` contract，不是模型输入形态
- 任何真实模型接入都应先经过 adapter，再进入公共 scoring

### 4.2B Harmonized Resource Layer 优先于 Entrant Benchmarking

长期制度中，`benchmark-invariant layer` 不应直接从“原始候选数据集”跳到 entrant benchmarking，而应先建设 `harmonized resource layer`，再进入 `dataset admission layer`，最后才进入 `entrant benchmarking layer`。

固定顺序应表达为：

```text
raw / processed candidate resources
-> harmonized resource layer
-> dataset admission layer
-> entrant benchmarking layer
```

三层职责固定如下：

- `harmonized resource layer`：统一来源登记、schema 映射、字段命名、provenance、processed/raw level 标注与基础可读性审计
- `dataset admission layer`：判断数据是否具备进入 formal benchmark 的最低统计支持与元数据闭环
- `entrant benchmarking layer`：仅对 admission 通过的数据运行 truth build、predicted-shift scoring 与 entrant adjudication

长期原则：

- `signal adequacy` 与 `model fidelity` 必须分离
- `E-test`、`E-distance` 或其他 distributional diagnostics 只能用于 adequacy / diagnosability，不替代 `predicted_shift vs real_shift` formal scoring
- formal benchmark 的主问题始终是模型 fidelity，而不是“该数据集是否看起来有信号”
- 若数据集在 admission 层未闭合，则不得把 entrant score 解释为模型成败

`support floor` 必须具备统计语义，而不能只是经验门槛。至少应显式追踪：

- `cells per perturbation`
- `cells per control`
- `UMI depth`

必要时可增加：

- `detected genes per cell`
- `usable pseudobulk replicates`
- `perturbation prevalence / support distribution`

这些支持度指标的职责是定义 admission / hold / exclude，而不是在 entrant 结果出来后事后救场。

### 4.2C Dataset Admission 的前置元数据治理

`dataset admission` 的本质是元数据治理，而不是“文件能读就算可评”。

在进入 formal benchmark 前，长期应前置审计并冻结至少以下维度：

- `single-target vs multi-target`
- `MOI`
- `control definition`
- `barcode assignment reliability`
- `processed/raw level`
- `target mapping closure`

制度含义：

- admission 决策必须先于 truth build、formal filtering 与 entrant benchmarking
- 若上述维度存在关键歧义，数据集应进入 `hold` 或 `auxiliary-only`，而不是带病进入 formal 主裁决
- metadata audit 结论属于 `benchmark-invariant layer` 的公共治理资产，不得为某个 entrant 单独改写

### 4.2D `scPerturb` 的制度角色

`scPerturb` 或其他 dataset hub 的长期角色，是 `harmonized resource layer` 与预审计层的输入来源，而不是 formal benchmark protocol 本身。

正式条文：

- `scPerturb` 可作为候选数据资源目录、下载入口、初始 schema 参考与 provenance 起点
- `scPerturb` 不等同于本项目的 formal dataset registry
- `scPerturb` 的处理口径、字段命名或预处理层级，不得直接上升为本项目的 formal benchmark protocol
- 任何来自 `scPerturb` 的资源，仍须经过本项目自己的 harmonization、admission audit 与 contract freezing

### 4.3 Stage 1A Four-Lane Formal Adjudication

`Stage 1A` adopts a four-lane formal adjudication design, in which `full_gene`, `top500`, `top1000`, and `top2000` lanes are evaluated in parallel under a pre-registered rule. Admission is determined by cross-lane stability rather than by post hoc selection of the best-performing lane.

制度含义：

- 四条 lanes 共同构成 `formal Stage 1A lane set`
- 四条 lanes 不是主轨与补充轨的层级关系
- 四条 lanes 不是可事后互相替代的救场轨道
- `Stage 1A` 的正式裁决必须同时参考 lane-wise outputs 与 cross-lane stability

#### 4.3.1 Lane set

四条正式赛道定义如下：

1. `full_gene_lane`
   - 使用 dataset-local all evaluable genes
   - 表征最广义输出空间下的整体 perturbation fidelity
2. `top500_lane`
   - 使用 control condition mean expression 排序后的前 500 genes
   - 表征最强 readout / 高信号 readout 下的预测能力
3. `top1000_lane`
   - 使用 control condition mean expression 排序后的前 1000 genes
   - 表征与 literature 更常见 readout 宽度可比的预测能力
4. `top2000_lane`
   - 使用 control condition mean expression 排序后的前 2000 genes
   - 表征从窄 readout 向较宽 readout 扩展时的保持能力

正式条文：

- `full_gene_lane`、`top500_lane`、`top1000_lane`、`top2000_lane` 全部属于 `formal Stage 1A lane set`
- lane 之间不存在主从等级；四条 lanes 全部为正式赛道
- lane 之间也不存在事后替代关系；任何 entrant version 都不得在看到结果后指定某一 lane 作为“真正主结论”

#### 4.3.2 Gene subset rule

`top500_lane`、`top1000_lane`、`top2000_lane` 的 gene ranking 规则固定为：

- 在每个 dataset 内
- 从 current evaluable genes 中
- 按 `control condition` 的 `mean expression` 做 descending 排序
- 取前 `N` 个 genes

硬规则：

- 不得按 observed differential expression 选 gene
- 不得以 HVG 或其他事后波动性口径替代
- 不得在看到模型结果后修改 `N`、ranking rule 或 tie-breaking rule

#### 4.3.3 Shared output contract

四条 lanes 使用同一个 entrant `predicted_shift` contract。

正式条文：

- entrant 不应为不同 lanes 导出不同版本的 prediction
- 四条 lanes 的差异仅允许体现在 scoring gene subset
- lane distinction 不得扩展为 lane-specific prediction contract、lane-specific adapter recipe 或 lane-specific export rule

#### 4.3.4 Lane-wise dataset-local governance

`Stage 1A` 的四条 formal lanes 全部是 `dataset-local`。

对每个 formal dataset：

- truth 在该 dataset 内的 dataset-native comparable space 中构建
- evaluable output genes 在该 dataset 内定义，不由跨数据集共同交集先验决定
- 每个 entrant 在每条 lane 内分别与 dataset-local baselines / nulls 比较
- 若 entrant coverage 不同，则 formal cross-entrant comparison 仅限于该 dataset、该 lane 内的 all-entrant-comparable subset

因此：

- `Stage 1A` 不再以单一 leaderboard 作为制度中心，而是以 `lane-wise formal outputs + adjudication summary` 作为正式记录
- cross-dataset common gene intersection 若保留，只能作为 implementation-level sensitivity output 或 audit reference
- common intersection 不得决定 formal adjudication
- common intersection 不得决定 target eligibility
- common intersection 不得决定 target feature lookup space

#### 4.3A Stage 1A Canonical Baseline and Null Family

`Stage 1A` 的 canonical reference family 固定由 `baseline layer` 与 `null layer` 组成。

`baseline layer` 包括：

- `zero_shift_null`
- `mean_shift_baseline`
- `linear_delta_baseline`

`null layer` 包括：

- `label_shuffle`
- `random_pairing`

正式条文：

- 四条 formal lanes 内的 entrant 裁决，必须相对同一 canonical baseline/null family 解释
- 上述 baseline/null family 属于 `benchmark-invariant layer`，不得因 entrant taxonomy、dataset 或 lane 而被事后改写
- implementation 层可以增加 `audit-only` 或 `sensitivity-only` 的补充分析，但不得替代上述 canonical family 作为 `formal adjudication reference`

#### 4.3A.1 `linear_delta_baseline` 的制度定义

`linear_delta_baseline` 是 `Stage 1A` 中高于 `mean_shift_baseline`、但仍保持简单、可审计、可复现的 supervised simple baseline。它的目的不是模拟某一 entrant 的建模范式，而是为 held-out target prediction 提供一个 deterministic linear reference。

构建规则：

- 在每个 `dataset × split × lane` 内独立构建
- 仅使用该 split 的 `training targets` 拟合，不得使用 `held-out targets` 的 truth
- 输入为该 dataset 的 `dataset-specific target lookup space` 中、对 target 可合法取得的 `target-side features`
- 输出为该 lane output space 中的 `perturbation-level predicted_shift`
- 训练目标为 `training targets` 的 `lane-local real_shift`
- 对 held-out targets 应应用同一已拟合线性映射，得到 held-out `predicted_shift`

硬约束：

- 不得使用 `DepMap`、`Stage 1B` / `Stage 2` / `Stage 3` truth、或其他外部 phenotype 信息
- 不得跨 dataset pooled fit
- 不得为不同 entrant 或不同 lane 事后改写 baseline 定义
- 不得在看到 held-out 结果后回调特征集、正则化强度或其他主超参数
- 不得把当前某一实现版本的具体 estimator 反向上升为 blueprint 的长期 canonical definition

说明：

- blueprint 在此冻结的是制度定义：`simple, deterministic, train-target-only, linear map from target-side features to lane-local shift`
- 具体 estimator class、feature encoding、regularization registry 与 hyperparameter manifest 属于 `runtime spec / implementation registry`，不在 blueprint 中以当前某一实现版本替代长期 canonical definition
- 当前实现若采用 `ridge-like linear map`、`elasticnet linear map`、`low-rank linear map` 或其他 deterministic linear instantiation，应由独立的 implementation report / runtime spec 记录，而不得反向改写本节

### 4.4 Cross-Lane Stability as the Admission Basis

`Stage 1A` 的正式裁决不是由单一 lane 的最好成绩决定，而是由 entrant 在四条 formal lanes 上的 `cross-lane stability` 决定。

正式裁决至少应纳入以下稳定性维度：

1. `n_lanes_signal_adequate`
   - 四条 lanes 中有多少条达到最低 signal adequacy
2. `n_lanes_null_superior`
   - 四条 lanes 中有多少条显著优于 null family
3. `n_lanes_baseline_competitive`
   - 四条 lanes 中有多少条达到最低 simple-baseline competitiveness
4. `lane_performance_consistency`
   - 各 lanes 表现是否呈现合理、一致、可解释的 readout-width 退化或保持模式
5. `absence_of_lane_specific_contract_failure`
   - 是否存在某一 lane 明显异常崩坏，提示 contract / export / scoring mismatch

说明：

- 上述维度的具体阈值应由预注册规则单独冻结
- blueprint 在此冻结的是裁决原则：Admission basis = `cross-lane stability`, not `single-lane best score`

解释边界：

- `cross-lane stability` 指 entrant 在不同 readout width 下呈现非病理性、可解释、不过度崩坏的 performance pattern；其含义不是要求四条 lanes 数值近似相等
- 允许从 `top500 -> top1000 -> top2000 -> full_gene` 出现可解释的性能退化
- 不允许出现提示 contract / export / scoring mismatch 的 lane-specific 异常崩塌

### 4.5 Stage 1A Adjudication Outcomes

`Stage 1A` 的正式裁决结果固定分为三档：

#### 4.5.1 `stable_formal_admissible`

定义：

- entrant 在四条 formal lanes 中表现出足够的跨 lane 稳定性
- 至少满足预注册的 lane-count / null superiority / signal adequacy / baseline competitiveness 要求
- 不存在重大 contract violation、space mismatch、governance violation 或解释边界失效

可进入：

- `Freeze`
- `Stage 1B formal validation`
- `Stage 2 formal bridge`
- `Stage 3 formal discovery`

#### 4.5.2 `exploratory_admissible`

定义：

- entrant 未达到 `stable_formal_admissible` 门槛
- 但在部分 lanes 中显示出稳定的非随机信号
- 不属于明显 invalid entrant，也不属于应立即阻断的 governance failure

可进入：

- `Stage 1B exploratory analysis`
- `Stage 2 exploratory bridge`

不得进入：

- `Freeze`
- `formal leaderboard`
- `formal pass skeleton`
- `Stage 2 formal claim`
- `Stage 3 formal discovery claim`

#### 4.5.3 `blocked`

定义：

- contract 不合法，或存在重大 space mismatch / governance violation
- 或四条 lanes 普遍接近 null，缺乏稳定、非随机、可解释的预测信号

处理：

- 不进入 downstream analytical mainline
- 仅保留在修复、诊断、adapter 调整与审计流程中

### 4.6 Entrant Taxonomy and Interpretation Boundary

`Entrant taxonomy` 用于界定 entrant identity、output contract 的解释边界，以及横向比较时允许成立的 claim 类型；其作用不是重写 `Stage 1A` 的统一 `predicted_shift` contract，而是防止不同 entrant 身份被错误压平成同一类主张。

正式分类如下：

- `Native perturbation model entrant`：模型原生面向 perturbation response / post-perturbation expression prediction；`GEARS` 的目标身份属于此类
- `Foundation model embedding + adapter entrant`：以预训练 embedding 为主干，经固定 `adapter / regression / retrieval` 机制导出 `predicted_shift`；当前 `scGPT` 接入方式属于此类，当前不应表述为 native `scGPT` perturbation prediction model
- `Embedding / in-silico perturbation + adapter entrant`：基于 embedding impact 或 `in-silico perturbation` 信号，经 adapter 导出 `predicted_shift`；当前 `Geneformer` 接入方式属于此类，当前不应表述为 native `Geneformer` expression prediction model

硬规则：

- 不同 entrant taxonomy 的结果不得被简化为“一句话总排名”
- 不同 taxonomy 仍不得被压平成同一类机制性 claim
- 所有 taxonomy 均进入同一个 `four-lane formal adjudication system`
- 横向解释时必须同时披露 entrant taxonomy 与 lane-wise performance pattern

**Note on current GEARS adapter status**

当前 `GEARS` adapter 的 `predicted_shift` 导出空间与 canonical scoring space 之间存在 suspected `LOG-RAW` space mismatch under audit。在完成 space audit 并确认修复前，当前 `GEARS` version 不应用于 `stable_formal_admissible` 的正式裁决解释；其 lane-wise results 至多可用于审计、诊断与 `exploratory` status 讨论。该状态不改变 `GEARS` 作为 `native perturbation model entrant` 的目标身份，但改变当前 version 的解释边界。

### 4.7 Entrant eligibility 与 evaluation eligibility

`Entrant eligibility` 与 `evaluation eligibility` 必须分离。

#### entrant eligibility

判断某 entrant 是否能在某 dataset 上合法、可复现、contract-compliantly 产出预测。

它关心的是：

- entrant recipe 是否冻结且可审计
- adapter 是否能在该 dataset 上运行
- 是否能导出 contract-compliant `predicted_shift`
- provenance / validator / output artifact 是否完整

#### evaluation eligibility

判断在该 dataset 内，哪些 perturbations、targets、output rows 可用于 eligible entrants 之间的公平比较。

它关心的是：

- 该 dataset 内哪些 truth 行合法可评
- 哪些输出基因属于该 dataset 的 formal lane output space
- 多 entrant 并列时的 all-entrant-comparable subset 是什么

正式条文：

- entrant 无法在某 dataset 上生成 contract-compliant predictions 时，应记为 `dataset-ineligible`
- benchmark 不得通过强行施加全局 gene-space harmonization 来“挽救”一个本来 dataset-ineligible 的 entrant
- evaluation eligibility 不得反向改写 entrant recipe

### 4.8 Target lookup space governance

`Target feature lookup space` 不得与 formal output scoring space 混为一体。

正式要求：

- formal output scoring 可以使用 dataset-specific、truth-aligned 的 evaluable output space
- target feature lookup 可以使用更大的 dataset-specific full feature space / lookup space
- 当全局交集会移除原本可合法评测的 perturbation targets 时，必须执行这一解耦

制度含义：

- output scoring space 服务于公平评分
- target lookup space 服务于 entrant 在该 dataset 内对目标的可覆盖性
- 二者职责不同，不得由同一个“共同基因交集”同时承担

### 4.9 聚合规则

正式裁决采用 `dataset-first, lane-aware, then aggregated`。

规则如下：

- 先计算 `dataset × split × lane` 结果
- 再做 entrant-level aggregation across datasets、splits 与 lanes
- 任何 pooled cross-dataset gene-universe score 都不得覆盖 dataset-level fairness checks
- implementation-level sensitivity rerun 不能上升为 formal adjudication
- 任何 downstream formal admission 都必须以 adjudication outcome 而不是单 lane 最佳值为依据

### 4.10 协议层、运行层、产物层分离

长期必须严格区分三层：

- `protocol/schema layer`
- `runtime config layer`
- `generated artifact layer`

含义：

- 协议层定义制度、字段、阈值和输出契约
- 运行层定义某次运行如何执行
- 产物层定义某次运行实际落盘的 manifest、summary、表格与日志

任何实现都不应把制度文件直接当运行配置使用。
当前 blueprint 中关于 `four-lane formal adjudication`、entrant taxonomy 与 `GEARS` explanation boundary 的条文，属于制度定义已建立；是否已在实现层完成端到端验证，应以独立的 implementation report / audit report 为准，而不由 blueprint 本身宣称。

对 `Stage 1A` 进一步要求：

- protocol / runtime / artifact 三层分离之外，还要显式区分 `benchmark-invariant` 与 `adapter`
- adapter 可以有模型专属输入空间、模型专属权重路径、模型专属中间缓存
- benchmark-invariant 层不得反向依赖某个模型的输入假设或训练实现

## 5. 数据资产与角色分工

### 5.1 Stage 1A formal 数据池

`Stage 1A formal benchmark-entry` 层当前主线采用三套单扰动数据：

- `replogle_2022_k562_essential`
- `replogle_2022_rpe1`
- `tian_2019_day7neuron`

说明：

- `Norman` 不进入 `Stage 1A formal`
- `adamson_2016_upr_perturb_seq` 不进入 `Stage 1A formal`
- `tian_2021_crispri` 当前只作为辅助鲁棒性数据集，默认不进入 formal 主裁决
- `replogle_2022_k562_gwps` 当前不升格为主线
- 正式分析不依赖模型仓库自带数据版本
- 正式数据可由 `pertpy`、`scPerturb` 或其他公开资源进入候选池，但只有经本项目 harmonized resource layer 与 admission audit 收口后的版本，才能进入 formal registry

### 5.1A Stage 1A 目标划分与 split governance

本节只约束 target 划分与复现性，不决定 gene space 治理。

实现锚点仍以：

- `configs/stage1a_split_governance.yaml`
- `scripts/stage1a_split_plan_b.py`
- `analyze_stage1a_pseudobulk_eligibility`
- `build_stage1a_pseudobulk_delta_truth`

为准。

长期规则：

- eligible targets 先按 minimum-support floor 进入候选集
- split governance 只负责 train / held-out target 划分
- split governance 不得与 formal output gene-space 治理混写
- split governance 不得被 common gene intersection 反向决定

对 `minimum-support floor` 的长期解释进一步固定为：

- 它是 admission 语义，不是事后调分语义
- 至少应联合追踪 `cells per perturbation`、`cells per control` 与 `UMI depth`
- 若支持度不足，应先在 admission 层 `hold / exclude`，而不是继续进入 entrant formal scoring
- adequacy diagnostics 可以支持这一决策，但不得替代 `predicted_shift` formal score 本身

当前预注册参数仍包括：

- `support >= 5`
- split seeds `[101, 202, 303, 404, 505]`
- truth freeze 默认 seed `101`

### 5.2 Stage 1B / Stage 2 / Stage 3 主线数据

#### HCC38 与 HCC1143

二者为 human cell line 下的 external time-aligned 主柱，作为 `Stage 1B` 与 `Stage 2/3` 的 dual pillars：

- 承载真实 14d perturbation transcriptome
- 与 `DepMap` 在 `cell line x gene` 层面配对
- 作为 dual-pillar integration 的 primary evidence

#### Additional long-timescale datasets

`GSE222378`（mouse，约 14d）可作为 `Stage 1B` 的 additional support，用于补充时间尺度相关鲁棒性证据；其不替代 human external validation pillar，也不作为 human `Stage 2 formal bridge admission` 的主依据。

#### SCP542

`SCP542` 不作为 `Stage 2 truth`，而作为：

- WT-like baseline / input reference
- predicted shift 起点参考
- expression gate 的外部参考
- replication / generalization 背景

#### DepMap

`DepMap` 作为 macro-truth：

- 提供长期 dependency / gene effect readout
- 用于 `Stage 2 bridge` 与 `Stage 3 low-dependency` 维度

## 6. Stage 1：Micro-Truth

### 6.0 Stage 1A adjudication → Freeze → Stage 1B（制度协议）

`Freeze` 只发生在 `Stage 1A adjudication outcome = stable_formal_admissible` 之后、`Stage 1B formal validation` 开始之前。

核心含义：

- `Stage 1A` 是 fidelity gate，不是训练层
- 进入 `Stage 1A` 的对象须已具备 `predicted_shift` 输出能力
- `Stage 1B` 消费 `stable_formal_admissible` 的 frozen entrant version，或消费 `exploratory_admissible` 的 entrant version 做非正式后续分析，而不是重新定义 entrant recipe
- 关键改动（权重、adapter、主预处理、导出规则、主阈值等）构成新版本，须重新走 `Stage 1A -> Freeze -> Stage 1B`

正式说明：`Freeze` 的对象是 entrant `recipe / version identity`，而不是某个单一 dataset、单一 split、单次运行中的“最佳结果”或单一 lane 的“最好成绩”。同一 entrant version 可以在不同 datasets、splits 与 lanes 上产生不同 run artifacts；这些 artifacts 构成该 version 的审计证据包，而不构成多个可供择优挑选的 frozen entrants。

version-level adjudication 进一步要求：

- `Formal Stage 1A` 的 `3 datasets × 5 split seeds` 构成同一 entrant version 的 `audit evidence package`
- 上述 evidence package 服务于同一个 entrant version-level adjudication outcome，而不是 15 个可供择优挑选的冻结候选
- 任何 downstream formal admission 都针对 `entrant version-level adjudication outcome`，而不是针对单次 run、单个 dataset、单个 seed 或单条 lane 的最佳结果

正式准入规则：

- 只有 `stable_formal_admissible` entrant versions 可以进入 `Freeze`、`Stage 1B formal validation`、`Stage 2 formal bridge` 与 `Stage 3 formal discovery`
- `exploratory_admissible` entrant versions 可以继续进入 `Stage 1B exploratory analysis` 与 `Stage 2 exploratory bridge`，但不得进入 `Freeze` 或生成 formal downstream claim
- `blocked` entrant versions 不进入 downstream analytical stages

完整可执行条文见 `docs/protocols/stage1a_freeze_stage1b.md`。

### 6.1 Stage 1A 总目标

`Stage 1` 是模型前门准入层，用于验证 `predicted_shift vs real_shift` 的分子层准确性。

### 6.2 Stage 1A formal output contract 与 adapter governance

`Stage 1A` 的统一 contract 仍是 `predicted_shift`。

要求：

- `formal source shared` 可以是 formal-filtered 单细胞 `h5ad`，也可以是同一 formal source 上的其他 adapter-native 派生表示
- 不得把“所有模型必须直接吃同一个单细胞矩阵”上升为制度默认
- 不要求所有 entrant 共享统一输入 gene universe
- 只要最终输出满足 `predicted_shift` contract，就可以进入统一评分

#### Model provenance / entrant acquisition

- `Stage 1A` 不是训练层；benchmark 不负责把模型训练出来
- entrant 必须已具备按统一契约产出 `predicted_shift` 的能力
- 该能力可以来自原生 perturbation model training、pretrained foundation model + task adapter、或固定 black-box workflow
- entrant 须提交并落盘：model provenance、checkpoint / weights identity、adapter recipe、preprocessing identity、predicted_shift export recipe

#### Entrant readiness cards（`docs/entrants/`）与协议术语引用

- 仓库内 `docs/entrants/*_stage1a_card.md` 为 **Stage 1A entrant readiness card**，用于在 formal 编排之前书面化：entrant 身份、provenance、可训练组件、`predicted_shift` 导出契约与阻断项；与「单次运行结果」或「多数据集多 seed 执行计划」解耦。
- **entrant card 不负责二次定义协议术语**；若需引用对照、差分或与 baseline 的关系，应仅表述为与 **本蓝图** 中已冻结条文一致。
- 若未来本蓝图 **重命名** 某一协议术语，entrant card 层仅保留「与协议一致」的引用层级，**不在 entrant card 内固化旧称作为独立定义**。

#### Protocol term: `shared control pseudobulk`

`shared control pseudobulk` 指：在 **同一 formal dataset / 可比条件** 下，为与 **perturbation-level** 表达或 delta 对齐而采用的 **协议约定的对照侧 pseudobulk 聚合**（具体构建、与 truth 及 `predicted_shift` export 的对齐方式由实现与 runtime spec 记录）。在需要 **control/reference subtraction** 以导出 `predicted_shift` 的 entrant recipe 中，对照侧须与该术语一致；**术语解释以本蓝图为准**，`docs/entrants/` 中的 card **仅引用、不展开替代定义**。

#### Foundation entrant checkpoint provenance（冻结规则）

对使用 **外部预训练权重** 的 entrant（例如 `scGPT`、`Geneformer`），冻结 **entrant version** 时须落盘 **可审计 provenance**，**至少**包含：

- `checkpoint_vendor_type`：`huggingface` \| `official_release` \| `internal_mirror`
- `checkpoint_vendor_uri`：**唯一** URI、仓库地址、发布页地址，或内部镜像的**唯一路径**
- `checkpoint_version_tag`：版本号、release tag、revision、commit hash 或其他可唯一标识的版本标签
- `checkpoint_artifact_identity`：具体 checkpoint 文件名、snapshot id、目录路径；必要时补 **hash**

若 `checkpoint_vendor_type = internal_mirror`，须尽量补充 **上游 provenance**：`upstream_vendor_uri`、`upstream_version_tag`。**不得**将内部镜像写成无上游可追溯的黑箱来源。

不允许仅以「官方 checkpoint」「预训练模型」「本地镜像」等不可审计表述替代上述字段。

#### 覆盖度制度

prediction coverage 必须明确区分：

- `entrant eligibility`
- `evaluation eligibility`
- `official dataset-level comparable subset`
- `adjudication outcome boundary`

允许：

- 对 contract-compliant predictions 在 dataset 内做 alignment 与 subset scoring

不允许：

- coverage 不足或 lane-specific contract 失效的结果直接进入 `stable_formal_admissible` 裁决
- 用跨数据集共同交集把一个 dataset-ineligible entrant 伪装成可比 entrant

#### Stage 1A 主要输出

- dataset-local predictions
- dataset-local truths
- dataset-local baseline/null matrices
- `dataset × split × lane` score tables
- lane-wise metrics tables
- cross-lane stability summaries
- adjudication outcome summaries

#### 当前实现状态声明

根据 Blueprint 4.3.4，Stage 1A 的 truth 和 evaluation space 均为 dataset-local：
- `main_aligned` = 每个数据集各自的全部 evaluable genes
- 当前主线第三数据集已切换为 `tian_2019_day7neuron`；其确切 evaluable gene 规模以重跑后的 registry / audit 产物为准
- 不存在跨数据集共同交集决定 evaluation space 的机制

### 6.3 Stage 1B：external dataset-local validation and exploratory analysis layer

`Stage 1B` 对不同 adjudication outcome 采用严格分流：

- `stable_formal_admissible` entrant version 进入 `Stage 1B formal validation`
- `exploratory_admissible` entrant version 仅进入 `Stage 1B exploratory analysis`

二者都必须消费同一 entrant version identity，而不得借 `Stage 1B` 重新定义 entrant recipe。

正式条文：

- `Stage 1B` 默认消费已经在 `Stage 1A` 后冻结的 entrant version identity
- `Stage 1B` 不承担模型 / adapter / 主预处理 / 输出契约继续开发职责
- `Stage 1B` 的 formal / exploratory 分流继承 `Stage 1A adjudication outcome`，而不是在 `Stage 1B` 重新定义 entrant recipe
- 若在 `Stage 1B` 期间发生关键 recipe 改动，则视为新 entrant version，需重新走 `Stage 1A -> Freeze -> Stage 1B`
- `Stage 1B` 不要求与 `Stage 1A` 完全同一 gene universe
- `Stage 1B` 不要求与 `Stage 1A` 完全同一 output space
- 允许在 `Stage 1B` 数据集上建立 dataset-local truth 与 dataset-local scoring space

前提条件必须同时满足：

- entrant recipe/version identity 不变
- exported output contract 不变
- prediction 与 truth 在 `Stage 1B` dataset-local comparable output space 内同尺度可比

比较原则：

- 使用 `HCC38` 与 `HCC1143` 两个 pillar 并行
- baseline 采用同 dataset / 同 cell line / 同 timepoint 的 in-dataset NT/control
- predicted shift 与 real shift 必须在同一 cell line、同一 perturbation、同一 endpoint、同一 dataset-local comparable output space 上比较
- 两个 pillar 必须分开输出，不得提前混合

### 6.4 Truth-building QC

长期要求：

- nominal perturbation 不自动等于 effective perturbation
- 进入正式 truth 前必须经过 efficacy QC

证据族至少包括：

1. target-centric evidence
2. transcriptome-level evidence
3. replicate consistency evidence
4. perturbation assignment evidence

### 6.5 制度已定后的实现层后果

以下内容不是近期任务清单，而是由本蓝图已定义制度直接推出的实现层后果。其是否已在当前仓库版本完成，应由独立 implementation / audit 文档说明。

1. truth build 在实现层应落实为 dataset-specific formal lane output spaces
2. target lookup 在实现层应落实为 dataset-specific full lookup space
3. compare layer 在实现层应落实为每个 dataset 内生成 all-entrant-comparable subset
4. aggregation layer 在实现层应落实为 dataset-first / split-first 汇总
5. common intersection 在实现层只应保留为 sensitivity rerun / audit output

这些后果属于 governance refactor 在实现层的结果性要求，而不是 blueprint 对近期开发顺序的单独下发。

## 7. Stage 2：Macro-Truth / Bridge

`Stage 2` 评估的是：预测到的 shift 是否能桥接到外部 phenotype truth，而不是重新定义 `Stage 1A` 的 gene-space 主制度。

主线条文应遵循：

- 只有 `Stage 1A adjudication outcome = stable_formal_admissible` 的 entrant version，才可进入 `Stage 2 formal bridge`
- `Stage 1A adjudication outcome = exploratory_admissible` 的 entrant version，可进入 `Stage 2 exploratory bridge`
- `blocked` entrant version 不进入 `Stage 2`
- `exploratory_admissible` entrant 不得产生 formal bridge claim

解释边界：

- 若 `Stage 1` fidelity 未立住，则 `Stage 2` 与 `DepMap` 的结果只能作为 `exploratory / diagnostic evidence`，不得解释为 formal biological utility 或 formal bridge validity

`Stage 2` 当前处于“主制度方向已确定、细化条文待继续冻结”的状态；后续应重点补强 bridge admission criteria、dual-pillar aggregation rule 与 threshold governance，但这些扩展不改变本节已定义的主制度方向。

## 8. Stage 3：Candidate Discovery

`Stage 3` 只在前两层满足正式准入后进入正式执行。

进入前提至少包括：

- `Stage 1A adjudication outcome = stable_formal_admissible`
- `Stage 2` 达到预注册桥接门槛
- entrant version 已冻结
- expression gate / stress filter / false-positive dictionary / threshold registry 已注册执行
- dual-pillar combined ranking 采用预注册规则

补充条文：

- `exploratory_admissible` entrant 不得进入 `Stage 3 formal discovery`
- `Stage 2 exploratory bridge` 不得外推为 `Stage 3 formal discovery claim`

本层不重新定义 `Stage 1A` / `Stage 1B` 的 gene-space 治理。
`Stage 3` 当前处于“执行前提与 claim discipline 已冻结、排序细则与 registry 细化待继续完善”的状态；后续扩展应集中于 ranking governance、threshold registry 与 false-positive adjudication，而不回改前述准入前提。

## 9. Stage 1A Formal Outputs and Downstream Separation

### 9.1 Formal lane-wise outputs

`Stage 1A` 的正式结果记录应采用 `lane-wise governance`。

正式要求：

- 每条 lane 都应有自己的正式结果记录
- 结果记录至少包括 lane-wise metrics、baseline/null comparison、dataset coverage 与 lane-specific audit note
- lane-wise output 是 formal record 的组成部分，而不是可供事后择优引用的候选池

### 9.2 Adjudication summary

最终正式 summary 应固定包含：

- lane-wise metrics table
- cross-lane stability summary
- adjudication outcome summary

制度含义：

- 最终 summary 的主键是 entrant version，而不是 entrant version 在某一单 lane 上的最佳分数
- 正式结论必须同时披露 lane-wise performance pattern 与最终 adjudication outcome

### 9.3 Formal vs exploratory downstream separation

正式下游输出必须遵守以下边界：

- `stable_formal_admissible` 可进入 formal downstream outputs
- `exploratory_admissible` 只能进入 exploratory downstream outputs
- `blocked` 不产生 downstream outputs

进一步要求：

- `formal downstream claim` 不得以 `exploratory_admissible` 或 `blocked` entrant 为证据主体
- exploratory output 可以用于诊断、假设生成与后续 adapter 改进，但不得被渲染成 formal pass
