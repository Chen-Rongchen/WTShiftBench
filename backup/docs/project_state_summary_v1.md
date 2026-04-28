# 项目阶段状态摘要 v1

## 1. 当前项目处于什么阶段

当前项目已经不再处在“分析还没收住”的阶段，而是进入了：

**主张治理稳定化阶段。**

更准确地说：

- 写作收口主线：叙事主线已稳定，但 manuscript-wide synchronization 尚未完成
- 方法学闭环主线：仍未 fully closed
- `global / structural bridge claim` 已可保留
- `object-level strongest claims` 已完成正式分级与必要降级
- `discovery` 已被成功压回 `gated_downstream_layer`
- 后续若想继续推进 full closure，主要瓶颈不再是分析框架不足，而是可用实验设计元数据的上限

工程状态也已经同步收口：旧 Stage 1A smoke / freeze / scoring 顶层流程、旧 entrant registry、旧处理后数据和旧 Stage 1A 测试已从当前工作树清理。`scripts/stage1a/` 只保留 Stage 2 入口仍直接复用的 adapter / feature helper；`configs/stage2/` 现在承载当前 registry 与 recipe，`configs/stage1a/` 与 `configs/entrants/` 不再是当前入口。

## 2. 当前最稳的项目状态标签

当前最稳的一句话状态是：

**当前项目已进入“主张治理稳定化”阶段：叙事主线已稳定，但 manuscript-wide synchronization 尚未完成；全局 bridge 主张可保留，对象级最强主张已完成正式分级与降级治理；后续闭环的主要瓶颈不再是分析框架不足，而是实验设计元数据的可用性上限。**

## 3. 当前已经完成到位的

- `bridge exists`：保住
- `GEARS trade-off diagnosis`：保住
- `scGPT` entrant-qualified HCC smoke：已完成第一轮接入与裁决
- `Geneformer` entrant-qualified HCC smoke：已完成第一轮接入与裁决
- `lm_train_lowrank` linear control：已完成第一轮接入与裁决
- `lm_G_scgpt_ridge` linear control：已完成第一轮接入与裁决
- `lm_G_geneformer_ridge` linear control：已完成第一轮接入与裁决
- anchor strongest wording：完成正式降级治理
- `PFDN5 = primary_but_qualified`：固定
- `PMF1 / PRPF6 / ZNF131 = supporting_only`：固定
- `transcription / chromatin = primary_axis_but_qualified`：固定
- `claim matrix`：已成形，并已接回主文稿与 boundary 文档
- discovery：已明确 `gated`
- `Dixit/K562`：已固定为 `GSE90063 K562 13d/7d temporal panel`；`13d` provides formal supplementary external support for architecture form, with bridge-form support remaining supporting / partial-support；`7d` is a temporal sensitivity / early-bridge probe；bridge content is not eligible
- `K562 RNAi endpoint sensitivity`：DEMETER2 RNAi 只作为 `GSE90063 K562 7d/13d CRISPR KO truth` 的 cross-platform sensitivity endpoint；`CRISPR DepMap` 仍是 matched primary endpoint，RNAi 不替代主线，也不提供等价 primary evidence
- foundation-model entrant family：已形成 `Geneformer > scGPT`
- 第一层 linear controls：已形成 `lm_g_geneformer_ridge > lm_train_lowrank > lm_g_scgpt_ridge`
- 禁写边界：`model recovery proved` / `Stage 2 complete` / `Stage 3 complete` 已固定

## 4. 当前还没有 fully closed 的

- `covariate closure` 仍不是最终闭环
- `sensitivity full closure` 仍不是最终闭环
- `final claim matrix -> manuscript wording` 仍需持续同步到所有入口文档
- discovery 仍未进入 formal deliverable
- 这不是因为缺少分析框架
- 而是因为缺少更深层实验设计元数据来继续做 deconfounding

需要补充的是，sensitivity 线当前已不再停留在“formal interval 不可引用”的阶段。`control subsampling` 已完成 `24/24` 配置重复数并达到 `formal_interval_citable = true`；因此 sensitivity 当前剩余的主缺口，已主要收缩到 covariate closure 仍未 fully closed 这一点。

当前混杂线已经从“单轴提示性审计”推进到“多轴、配置驱动、可汇总输出”的状态：`barcode_gem_group`、`num_umis_quantile_bin`、`num_umis_over_threshold_bin`、`transcriptome_total_signal_quantile_bin` 与 `transcriptome_detected_genes_quantile_bin` 都已经进入正式 covariate audit 入口。但这一步解决的是**把风险显式量化并纳入边界治理**，不是把混杂风险宣布为 fully closed。

更准确地说，当前状态应写成：五条 covariate 轴已落盘、风险已治理进边界；其中 `barcode_gem_group` 已固定为 design-proxy axis，但主张层面仍不能写成 `fully deconfounded`。

这两件事必须分开理解：

- 前者是“方法没做到”
- 后者是“证据天花板到了”

当前项目更接近后者。

因此，本阶段应明确接受四条现实边界：

- 接受 `design-proxy` 是当前最终口径，不再等待升级
- 接受 covariate 线当前不会到 `fully clean`
- 接受论文必须带着这条 limitation 写
- 接受“是否开始写论文”的门槛应改成文稿与边界是否稳定，而不是数据是否完美

与此同时，model-side entrant 状态也已经从“只有 `GEARS` 进入正式 HCC 裁决”推进到“`GEARS + scGPT + Geneformer + 三条 linear controls` 已进入同一份 HCC comparison”。当前新增 entrant / control 并没有推翻主结论，只是把 entrant family 的第一轮位置明确出来：`Geneformer` 强于 `scGPT`，`lm_g_geneformer_ridge` 能保住一部分 backbone，但当前没有任何对象改写 `shared_mean_baseline` 仍是 backbone primary reference 这一点。

baseline-vs-GEARS 的 trade-off 必须写成非对称。当前不是“GEARS 和 baseline 各赢一半”，而是：`shared_mean_baseline` 更像 shared backbone winner，且这个优势更稳定、更主导；`GEARS` 更像 deviation / separation-biased entrant，它的相对强项主要落在 `structure_vs_context_separation`，并在部分对象上更接近 `shift-excess`。这里的 `shift-excess` 指超出 backbone 可解释部分的过度偏移或 context-specific deviation，不等于 shared trend / overall displacement。

`GSE90063 K562 13d-only` 的 model-side 最小审计进一步支持 `partial recurrence / partial-support`：`shared_mean_baseline` 再次在 backbone recovery 上占优，而 `GEARS` 仍在 structure-vs-context separation 上更强；但 `shift-excess` 分量未复现。因此，backbone vs separation trade-off recurrence 可写成 `supporting / partial-confirmed`，full three-component recurrence 与 external model-side generalization 均不能写成 established。

这也意味着，后续如果继续推进“为什么模型打不过 baseline”，默认不该再以泛问题形式展开，而应先拆成两个更小的问题：

- `baseline winner` 是否主要由 shared backbone objective 决定
- entrant 的额外能力是否稳定落在 `separation / deviation` 而不是 backbone 上

在这两个问题更清楚之前，biology-facing explanation 仍应停留在 plausible interpretation 层。

## 5. 当前最稳的三层边界

### 5.1 全局层

当前证据支持 `truth–DepMap bridge` 在整体与结构层面上成立，且该结论在现有 covariate audit 下仍可保留。

### 5.2 对象层

当前 covariate audit 表明 anchor-level strongest wording 需要收紧。现阶段仅 `PFDN5` 可保留为 `primary_but_qualified`；`PMF1`、`PRPF6` 与 `ZNF131` 虽保持结构稳定的 anchor 身份，但目前仅能作为 `supporting_only`，而不足以被表述为 fully deconfounded primary anchors。与此同时，`transcription / chromatin` 当前最多只能写成 `primary_axis_but_qualified`。

### 5.3 方法学边界层

现有 covariate closure 受限于仓库中可用的实验设计元数据范围。若无新增元数据源，后续最合理的推进方向应是完成 `claim matrix`、`evidence tier synchronization` 与 manuscript-ready wording，而非无停止规则地继续扩展 covariate 审计轴。当前更准确的口径应是：**混杂风险已完成第一轮多轴治理，但仍受元数据上限约束；其中 `barcode_gem_group` 只能写成 design-proxy axis，而不是单个 `MH00x` 已确认的 run-level covariate。**

`Dixit/K562` 在这一边界下也应固定写成：`GSE90063 K562 13d/7d temporal panel` 支持 architecture form 的时间稳定性与 bridge readout 的 temporal stratification；`13d` 是 primary formal supplementary bridge test，`7d` 是 temporal sensitivity / early-bridge probe，bridge content is not eligible。因此这些结果不支持 `13d` 全面强于 `7d`、`model generalization proved`，也不支持与 HCC 对称的 primary conclusion、shared mainline architecture content、content-level convergence 或 broad cross-context validation。

DEMETER2 RNAi endpoint sensitivity 只能在这一层之后阅读：它用于检查 `7d/13d CRISPR KO truth` 接到 RNAi-derived dependency endpoint 时是否保留方向兼容或 endpoint robustness。它不能改变已冻结的 CRISPR DepMap 主线，也不能把 RNAi 写成 matched endpoint、primary closure 或等价 primary evidence。

### 5.4 指标治理层级

state summary 单独阅读时也必须保留指标层级：

- 主裁决三指标：`backbone_recovery_score`、`shift_excess_identification_score`、`structure_vs_context_separation_score`。这三者共同定义 model recovery adjudication，回答模型是否恢复 frozen architecture。
- 补充四模块：`Spearman(E, ΔT)`、`E-distance`、essentiality stratification、stress-removed sensitivity。它们用于解释 bridge form、state displacement、非线性分层与 stress 稳健性，不替代主裁决三指标。
- 禁止把 scalar association 或 stratification 写成 model recovery adjudication 的同级证据；它们是 supplementary explanation / audit layer。
- 禁止把 `shift` 写成单层概念；shared trend / overall displacement 与 `shift-excess` 分属不同层级，后者才是 GEARS 相对强项更可能出现的位置。

## 6. 当前最该守住的四条纪律

- 不把 `primary_but_qualified` 偷偷写成 `primary`
- 不把 `supporting_only` 借叙事语气抬升
- 不把 `retainable_global_claim` 延伸成 `recovery proved`
- 不把 `gated_downstream_layer` 提前写成主 deliverable

## 7. 当前统一口径源

本文件只做阶段性状态裁决，不承担仓库入口或执行清单职责。仓库入口看 `README.md`；近端执行顺序看 `plan.md`；最终 wording 边界以 `final_claim_matrix.tsv` 和 boundary 文档为准。

当前 state-summary 层只固定三类口径源：

1. [`reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`](/home/data/gz0705/WTKO/reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv)
2. [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)
3. [`docs/main_manuscript_results_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_results_draft_v1.md)

## 8. 一句话收口

当前主线已经不是“缺结果”，而是“结果边界已经被治理清楚；叙事主线已稳定，但 manuscript-wide synchronization 尚未完成；剩下要做的是把 claim matrix 同步成 manuscript-ready wording，并承认再往上能不能闭环，取决于未来是否拿得到更高质量实验设计元数据”。
