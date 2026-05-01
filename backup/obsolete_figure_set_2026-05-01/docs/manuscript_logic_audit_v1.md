# WTKO 手稿逻辑审查报告 v1

**审查日期**: 2026-04-28
**审查范围**: 主文正文 (Abstract, Background, Results, Discussion, Conclusions, Methods) + 图注 (Fig. 1-5 + Extended Data Fig. 1-11)
**审查维度**: 逐句事实分类 + 逻辑断点识别 + 数据/代码/映射一致性

---

## 分类图例

| 标记 | 含义 |
|------|------|
| **F** | 事实 (Fact) — 可验证的客观陈述 |
| **CF** | 引用事实 (Cited Fact) — 有文献支撑的事实 |
| **I** | 推断 (Inference) — 从事实出发的逻辑推论 |
| **V** | 价值判断 (Value Judgment) — 主观评估/修辞选择 |
| **UC** | 未证断言 (Unsubstantiated Claim) — 需要证据但未提供 |
| ⚠️ | 逻辑断点位置 |

---

# Part 1: 正文逐句审查

## 1. ABSTRACT

### Background

**S1**: "A central challenge in perturbation-model evaluation is that expression reconstruction does not by itself define the phenotype-relevant object a model should recover, potentially conflating transcriptional fit with phenotype-relevant structure."

| V + I | ⚠️ 缺少引用支撑。"central challenge" 声称需引用具体文献指出此问题（如 Ahlmann-Eltze 2025, Kedzierska 2025）。

### Results

**S2**: "We built a truth-first, architecture-aware framework and resource that freezes a phenotype-aligned benchmark object before model comparison."
| F | 方法事实。无断点。

**S3**: "Real perturbation transcriptomic shifts were aligned with CRISPR DepMap dependency to define a fixed truth bridge, and model predictions were then adjudicated against this frozen architecture."
| F | 方法事实。无断点。

**S4**: "In the breast-cancer cell-line contexts HCC38 and HCC1143, the bridge was summarized by recurrent target-level anchors and descriptive axis-level context rather than by a single global correlation."
| F + V | ⚠️ "rather than by a single global correlation" 隐含 strawman——未说明谁在这样做。

**S5**: "Architecture-aware adjudication decomposed recovery into backbone recovery, shift-excess identification and structure-versus-context separation, revealing a structured trade-off rather than a single leaderboard result: the shared-mean baseline was strongest for canonical backbone recovery, whereas GEARS retained stronger structure-versus-context separation."
| F + I | ⚠️ "trade-off" 的因果性未建立。观察到 baseline 在 backbone 更强而 GEARS 在 separation 更强，这是"差异"（difference），不必然构成"权衡"（trade-off）。Trade-off 暗示在同一模型内两个维度互斥，但这未被证明。

**S6**: "K562 temporal analyses supported bounded external recurrence of architecture form, whereas RNAi DEMETER2 provided a weaker cross-platform sensitivity endpoint than CRISPR DepMap."
| F | 有数据支撑。无断点。

### Conclusions

**S7**: "This resource provides a reproducible framework for phenotype-aligned perturbation-model adjudication and can support future extension across cell-line contexts, endpoints and entrants while preserving explicit claim boundaries."
| V + I | ⚠️ 可扩展性未证明——当前仅在 2 个 breast-cancer line + 1 个 K562 line 上测试。"can support future extension" 应改为 "is designed to support" 或 "provides a template for"。

---

## 2. BACKGROUND

**S1**: "Perturbation-model benchmarks need a phenotype-relevant recovery object, not only a prediction score."
| UC | ⚠️ **核心前提未被支撑**——全文的 normative 前提在此处作为断言出现，应至少引用 1-2 篇文献（[8-11] 在后面才出现）。

**S2**: "Single-cell perturbation profiling has made it possible to observe how genetic perturbations reshape transcriptomic state at scale [1-3]."
| CF | 有引用支撑。无断点。

**S3**: "These datasets have supported graph neural networks, single-cell foundation models and embedding-based decoders that aim to predict expression responses to perturbation [4-7]."
| CF | 有引用支撑。无断点。

**S4**: "Such models are commonly assessed by expression-level reconstruction accuracy or local agreement with observed transcriptional shifts."
| F | 行业常识。无断点。

**S5**: "These metrics are necessary but incomplete: they do not directly test whether a model recovers transcriptomic structures that are relevant to downstream cellular phenotypes such as fitness, dependency or liability, and may therefore mis-rank models when transcriptional fit and phenotype-relevant structure diverge."
| I + UC | ⚠️ "may mis-rank models" 缺少具体实例。如果引用 [8-11] 可以提供此证据，应在此处提前出现。

**S8**: "The first design problem is therefore object definition."
| V | 立场声明。可接受。

**S9**: "A perturbation response can contain a shared backbone that is recurrent across cell contexts and context-specific deviations that are only partially captured by global expression-level summaries."
| I | ⚠️ **概念先行于证据**：shared backbone / deviation 的二分在此作为已知事实陈述，但实际上是本研究的概念框架。应标记为假设或框架设计。

**S10**: "Within this structure, interpretable axes of variation may emerge, but these need not be equally aligned with dependency."
| I | 合理推断。

**S11**: "A model may recover one component while missing another. Conversely, a simple baseline may perform strongly on the dominant shared component when the evaluated object is dominated by shared structure."
| I | 概念性推断。合理。

**S12**: "Without defining a frozen, phenotype-relevant benchmark truth object before model comparison, model leaderboards risk conflating expression reconstruction, endpoint alignment and content-level interpretation."
| UC + V | ⚠️ 对现有 leaderboard 做法的批评缺乏具体引用。建议改为 "risk conflating" → "may conflate"，或引用具体 benchmark 实例。

**S13**: "Prior perturbation-prediction benchmarks have already shown that expression-level recovery by deep learning or foundation-model entrants can be matched or exceeded by simple baselines [8-11]."
| CF | 有引用支撑。

**S14**: "These studies provide essential context for interpreting model-side results, but they ask a different question from the one addressed here in that they do not first freeze a phenotype-relevant benchmark object."
| I + V | ⚠️ 区分点的准确性需确认——特别是 [8] Ahlmann-Eltze 2025 是否确实没有 phenotype-relevant 维度？

**S15**: "They evaluate transcriptome prediction accuracy, whereas the present benchmark first freezes a phenotype-relevant truth object by aligning perturbation transcriptomic shifts to CRISPR DepMap dependency."
| F | 方法描述。

**S16**: "Model recovery is then decomposed into backbone recovery, shift-excess identification and structure-versus-context separation."
| F | 方法描述。

**S17**: "The resulting claim is not that complex models fail in a unidirectional sense, but that current entrants recover different parts of a frozen fitness-bridge architecture."
| V | 结果框架。合理。

**S18**: "Cancer dependency resources provide an opportunity to make this evaluation more direct with respect to phenotype-relevant fitness readouts."
| V | 前提声明。合理但未被引用支撑。

**S19**: "CRISPR DepMap captures gene-level fitness effects across cancer cell lines and can be aligned with perturbation transcriptomic shifts [12]."
| CF | 引用 [12] (Meyers 2017)。

**S20**: "RNAi DEMETER2 provides a related but weaker cross-platform sensitivity readout [13]."
| CF + V | ⚠️ "weaker" 的引用支撑——[13] (McFarland 2018) 是 DEMETER2 方法论文，可能不直接涉及与 CRISPR 对比。应在 Results 中用数据证明。

**S21**: "However, these endpoints are not interchangeable. Bridge claims therefore require explicit endpoint hierarchy and claim governance, such that evidence layers remain separated from causal or mechanistic overinterpretation."
| I + V | 前提论证。合理。

**S22** (最后一段): 目标陈述。与 Abstract 重复。无新增断点。

---

## 3. RESULTS

### 3.1 A truth-anchored HCC38/HCC1143 benchmark defines the phenotype-relevant recovery object

**S1**: "We first defined the benchmark object independently of model predictions." | F | 无断点。

**S2**: "For each HCC38/HCC1143 breast-cancer context, transcriptomic truth was summarized by the absolute mean perturbation shift and aligned with CRISPR DepMap dependency so that larger aligned values represented stronger dependency." | F | 无断点。

**S3**: "Targets were assigned to pre-specified joint shift-dependency categories, including high-shift/high-dependency anchors, transcriptomic-excess targets, dependency-excess targets, low-information targets and a retained middle band (Fig. 1a,d; Extended Data Fig. 1-2)." | F | 无断点。

**S4**: "Both breast-cancer cell-line contexts contained a high-shift/high-dependency anchor set." | F | 无断点。

**S5**: "HCC38 contained 9 Q1 anchors and HCC1143 contained 10 Q1 anchors, with aligned Spearman rho values of 0.726 and 0.779, respectively (Fig. 1b,c,e)." | F | 无断点。

**S6**: "The resulting bridge was not treated as a single global correlation, but as a structured target-level recovery object whose categories, source data and interpretation boundary were fixed before model comparison." | F + V | ⚠️ 暗示"单一全局相关性"是不足的做法（strawman）。

### 3.2 Shared anchor analysis separates recurrent structure from unqualified target claims

**S1**: "We next asked which target-level objects were recurrent across HCC38 and HCC1143." | F | 无断点。

**S2**: "PFDN5, PMF1, PRPF6 and ZNF131 formed the most stable shared anchor set, repeatedly occupying the high-shift/high-dependency region and retaining shared-anchor status under cutoff sensitivity analysis (Fig. 2a-c)." | F | 无断点。

**S3**: "However, recurrent structure alone did not justify unqualified target-level claims." | V | 方法论立场。合理。

**S4**: "After covariate-aware tiering, PFDN5 remained a primary but qualified anchor, whereas PMF1, PRPF6 and ZNF131 were retained as supporting-only anchors." | F | 有 Fig. 2 支撑。

**S5**: "ENY2, NPM1, RPS3, RUVBL2 and ZBTB17 were retained as supporting but cutoff-sensitive objects, indicating weaker structural stability than the core shared-anchor set (Fig. 2c)." | F + I | 合理。

**S6**: "This tiering separates bridge support from target proof: shared anchors support the existence of a structured perturbation-fitness bridge, but no individual anchor is interpreted as fully deconfounded causal evidence (Fig. 2d,e)." | I | ⚠️ "causal" 一词的边界——什么条件下才能提供 causal 证据？本体论边界未定义。

### 3.3 Model comparisons reveal a backbone-separation trade-off

**S1-S2**: 方法事实。无断点。

**S3**: "The shared-mean baseline achieved the strongest backbone recovery score, 0.807, exceeding the prespecified formal GEARS recipe, 0.660." | F | 无断点。

**S4**: "GEARS instead showed stronger structure-versus-context separation, 0.428 compared with 0.353 for the baseline." | F | 无断点。

**S5**: "Shift-excess identification did not distinguish the formal baseline-GEARS comparison, with both scoring 0.333 (Fig. 3c)." | F | ⚠️ 0.333 在两个模型上完全相同的含义未解释。如果这是随机猜测水平的值，需要明确说明。

**S6**: "The difference was therefore not a simple model failure or success. It was a trade-off: under the present benchmark definition, the baseline recovered the dominant shared backbone more strongly, whereas GEARS retained stronger separation- or deviation-biased recovery." | I + V | ⚠️ **核心逻辑断点**。"trade-off" 需要两个维度间的负相关证据。当前只有跨模型差异，不构成 trade-off。建议改为 "asymmetric recovery pattern" 或 "complementary recovery profile"。

**S7**: "Foundation-model entrants and embedding-based controls did not overturn this trade-off." | F | "did not overturn" 暗示推翻是期望，带有方向性偏见。建议改为 "showed the same pattern"。

**S8**: "Geneformer retained more recoverable structure than scGPT in this setting, and Geneformer-ridge exceeded other linear controls, but neither displaced the shared-mean baseline as the backbone reference (Fig. 3)." | F | 无断点。

**S9**: "Current entrants therefore recovered different but incomplete components of the frozen perturbation-fitness architecture." | I | ⚠️ "incomplete" 的参照系未定义。什么构成 "complete" recovery？如果 backbone + separation + shift-excess 都是 1.0？这实质上是否可能？

### 3.4 GEARS recipe sweeps and embedding controls do not close the backbone gap

**S1-S3**: 方法事实。无断点。

**S4**: "No sweep candidate closed the backbone gap to the shared-mean baseline. The best sweep candidate scored 0.643 for backbone recovery, below both the baseline and the formal GEARS recipe (Fig. 4a,b)." | F | ⚠️ Sweep 设计限制——仅搜索 epochs, lr, weight_decay 的 3×3×2 邻域。是否有文献支持这些是 GEARS 最关键的参数？如果其他参数（hidden dimension, number of layers）更重要，sweep 覆盖范围不足。

**S5-S6**: 定量结果 + 推断。合理。

**S7**: "Linear-control analyses led to the same trade-off interpretation..." | F | 无断点。

**S8**: "The persistence of the gap after finite-budget recipe sweeps, linear controls and coverage audits is consistent with a task-structure or direction-level mismatch under the present benchmark definition, although it does not exclude other untested model-side factors..." | I | ⚠️ "task-structure or direction-level mismatch" 是重要推断，但未进一步阐述具体含义。Reviewer 会追问。

### 3.5 Axis-level decomposition provides descriptive biological context

**S1-S2**: 方法事实。 | ⚠️ **图号不一致**：manuscript_draft_v1.md 引用 Extended Data Fig. 4，submission_draft_v2.md 引用 Extended Data Fig. 11。两版本 Extended Data 图号完全不同，需统一确认。

**S3**: "For example, transcription/chromatin shows transcriptomic-heavy behavior, with shift R2 = 0.092, dependency R2 near zero, and target support from ENY2 and TADA3..." | F | ⚠️ R2 = 0.092 极低（解释不到 10% 方差），却被标记为 "strongest qualified formal axis"。需说明为何低 R2 仍有信息量。

**S4-S8**: 描述性结果 + 自我限定。合理。

### 3.6 Covariate, temporal and endpoint analyses define the claim boundary

**S1-S2**: 方法事实。

**S3**: "Barcode gem group illustrates this boundary: HCC38 maps to aggrMH001-3 and HCC1143 maps to aggrMH004-6, but individual MH001-MH006 run labels are not resolved (Fig. 5c)." | F | ⚠️ "aggrMH001-3" 命名来源需说明——是原始数据变量名还是自定义聚合标签？

**S4-S6**: 结果 + 推断。 | ⚠️ 图号引用不一致（manuscript_draft_v1 引用 EDFig3, submission_draft_v2 引用 EDFig7）。

**S7**: "Under A0/A1/B tiering, the K562 panel supports architecture-form recurrence and bounded bridge-form support..." | F + V | ⚠️ A0/A1/B tiering 框架是本研究自定义的，Results 中未充分解释其含义。

**S8-S10**: 定量结果 + 推断。合理。

---

## 4. DISCUSSION

**S2**: "The central design choice is to define the phenotype-relevant recovery object before model comparison. This separates three questions that are often conflated..." | V + I | ⚠️ "often conflated" 缺乏引用支持。

**S6**: "The strength of the shared-mean baseline is informative rather than artifactual." | UC | ⚠️ **"not artifactual" 的证明不完整**——baseline 由 canonical_backbone 的 truth 向量构造，而 backbone recovery 评分也可能受此构造方式影响。存在循环论证风险（见跨章节断点 C）。

**S3-S14**: 总体与 Results 重复。自我限定较好。

**Limitations paragraph (S15-S19)**: 总体写得好。| ⚠️ 缺少一个 limitation：truth 度量选择（`real_shift_mean_abs`）本身的局限性讨论，虽 Extended Data Fig. 2 做了 metric 比较，但 Discussion 未提及。

---

## 5. CONCLUSIONS

**S1**: "Perturbation transcriptome models should be evaluated against phenotype-relevant truth objects, not only expression reconstruction metrics." | V | 规范性 "should" 主张。受限于当前证据范围。

**S2-S5**: 结果总结 + 前瞻声明。合理。"bounded" 是恰当的自我修饰。

---

## 6. METHODS — 关键断点

| # | 断点 | 描述 | 建议 |
|---|------|------|------|
| M1 | 25/75 分位数选择 | 为何选择 25/75 分位数定义 anchor？ | 引用 Extended Data Fig. 2 的 cutoff sensitivity；陈述选择理由 |
| M2 | `real_shift_mean_abs` 作为唯一 primary truth metric | 所有基因等权平均，可能被高表达基因或噪声主导 | Extended Data Fig. 2 已有比较，Methods 应简要提及 |
| M3 | 方向对齐操作未显式写出 | "larger aligned values represented stronger dependency"——CRISPR dependency 原始值为负（越负越 essential），翻转逻辑需显式写出 | 写出符号翻转公式 |
| M4 | `canonical_backbone` 标签的循环定义 | Backbone recovery 评分依赖 `canonical_backbone` 标签；baseline 也从 canonical_backbone 成分构造 | 显式描述标注方法；论证 baseline 构造与评分的独立性（见跨章节断点 C） |
| M5 | Stop rule 对 GEARS 的公平性 | Backbone recovery 是否是合理的唯一评判标准？ | 当前 wording 已做 bounded 处理；但需确认 stop rule 不排除 GEARS 在其他维度的价值 |
| M6 | GSE90063 legacy object 排除 | "dixit_2016_raw" 不匹配的具体表现未说明 | 提供更多细节（不匹配表现、来源） |

---

## 7. FIGURE LEGENDS — 关键断点

### Fig. 1

**Fig. 1f**: "empirical two-sided p = 0.001 for each context"
| ⚠️ p 值精度——如果 observed rho 在 1000 次 permutation 中严格最大，p 应为 "< 0.001"（保守估计 p = 1/1001）。写成 "p = 0.001" 暗示至少 1 个 permuted rho >= observed。

### Fig. 2

**Panel e**: "TVD > 0.25 (hard imbalance cutoff)"
| ⚠️ TVD 阈值 0.25 的来源未说明。是文献标准还是自定义？需要引用或解释。

### Fig. 3

**Panel c**: "lightly shaded upper-right region is shown only as an illustrative visual aid... not a decision threshold"
| 自我限定好。但阴影区域边界如何确定？Reviewer 可能追问。

### Fig. 4

"GEARS training is not rerun during figure production"
| ⚠️ Reproducibility 声明需可验证支撑。是否有 hash 记录或 frozen artifacts 路径？需在 source data manifest 中提供。

### Fig. 5

**Panel b**: SMAD5 和 ZNF131 的 "endpoint dropouts"
| ⚠️ Dropout 原因未解释（基因不在 panel 中？数据质量问题？）。

---

# Part 2: 跨章节系统性问题

## 断点 A: "Backbone-separation trade-off" 的因果性未澄清（最严重）

**出现位置**: Abstract, Results §3, Discussion

这是全文最核心的 claim。当前证据：
- Baseline backbone = 0.807, GEARS backbone = 0.660
- Baseline separation = 0.353, GEARS separation = 0.428

两件事同时成立 → "差异"（difference）。称之为 "trade-off" 需要额外条件：
- (a) 两个维度间存在负相关（同一模型内提升 backbone 会降低 separation）
- (b) 没有模型在两个维度上都做到最好

当前仅支持 (b)，不支持 (a)。(a) 需要 sweep 内 backbone 和 separation 的负相关分析。

**建议**:
1. 将 "trade-off" 替换为 "asymmetric recovery pattern" 或 "complementary recovery profile"
2. 或：补充 GEARS sweep candidates 中 backbone vs separation 的 scatter plot，展示两点间的负相关模式

## 断点 B: 图号在两个手稿版本间不一致

| 主题 | manuscript_draft_v1.md | submission_draft_v2.md |
|------|----------------------|----------------------|
| Axis analysis | EDFig 4 | EDFig 11 |
| K562 temporal | EDFig 3 | EDFig 7 |
| Pathway polarity | EDFig 5 | 无 |

**建议**: 确认最终版本的 Extended Data 图号方案并统一全文引用。

## 断点 C: `canonical_backbone` 标签的定义循环（重要）

**机制**: 
1. Truth 架构合约中，`canonical_backbone` = fraction_Q1 >= 0.5 的轴
2. `shared_mean_baseline` = canonical_backbone 目标的平均 shift 向量
3. Backbone recovery score = backbone 目标上 predicted shift 对 expected axis 的 rank-percentile recovery

如果 backbone recovery 的 expected axis 也是从 truth 数据导出的，而 baseline 恰好又是该 truth 的均值，则 baseline 在 backbone recovery 上的优势可能部分来自构造循环。

**代码验证** (`scripts/stage2_freeze_truth_architecture_contract.py`, line 59-60):
```python
if q1_38 >= 0.5 and q1_1143 >= 0.5:
    return "canonical_backbone"
```

Baseline 构造 (`src/wtbench/stage2_hcc_prediction_export.py`, line 197-227):
- 取 canonical_backbone 目标的 mean shift vector
- 对**所有目标**（含非 backbone 目标）预测该均值

**建议**:
1. 显式描述 canonical_backbone 的标注方法
2. 论证 baseline 的 backbone recovery 评分不是简单的自洽（self-consistency）
3. 考虑用 permutation 测试：随机分配 backbone 标签，看 baseline 的优势是否消失

## 断点 D: "Truth-first" 框架的隐含假设未被审视

| 假设 | 内容 | 风险 |
|------|------|------|
| Truth 度量的充分性 | `real_shift_mean_abs` + CRISPR DepMap 充分捕获 phenotype-relevant 信息 | 其他 phenotype 维度（如 drug response, metastasis）被排除 |
| Truth 度量的排他性 | 时间动态、细胞类型异质性等可忽略 | 扰动的时间依赖性可能是 phenotype 的重要维度 |
| Truth 度量的不变性 | 跨上下文的 bridge 结构足够稳定 | n = 47-48 的小样本下稳定性有限 |

**建议**: 在 Discussion limitations 中增加一段，讨论 truth 度量选择的本体论假设。

## 断点 E: 样本量与统计效力

- HCC38: n = 47
- HCC1143: n = 48
- Q1 anchors: 仅 9-10 个
- Multi-way stratification (joint grid + covariate tiering) 在小样本下行为未讨论

Fisher z-transform CI 提供了点估计精度，但 anchor tiering 在小 n 下的行为（如 TVD 估计的不确定性）未讨论。

**建议**: 在 Methods 或 Discussion 中增加样本量限制的讨论。

---

# Part 3: 数据 / 代码 / 映射审查

## 审查范围

- 代码: `src/wtbench/manuscript/` (20 个 .py 文件) + `scripts/manuscript/` (28 个 .py 文件)
- 配置: `configs/manuscript/` (6 个 JSON)
- 源数据: `reports/manuscript_figures_v2/` + `reports/manuscript_extended_data_v1/`
- 核心变量: `real_shift_mean_abs`, `depmap_gene_dependency`, `canonical_backbone`, `barcode_gem_group`, `shared_mean_baseline`
- K562 数据: GSE90063 的处理管线
- GEARS sweep: 配置与 stop rule

## 发现的问题

### 1. 图号映射不一致（代码层面）

`configs/manuscript/extended_data_figures_v1.json` 中存在以下映射：

| 配置 key | script 文件 | script 中的 FIGURE_ID | 不一致？ |
|----------|------------|----------------------|---------|
| `extended_data_figure2` | `build_extended_data_figure13.py` | `extended_data_figure13` | **是** |
| `extended_data_figure3` | `build_extended_data_figure8.py` | `extended_data_figure8` | **是** |
| `extended_data_figure4` | edfig10 目录 | edfig10 | **是** |
| `extended_data_figure5` | edfig9 目录 | edfig9 | **是** |

这些映射意味着 publication 中的 Extended Data 图号与代码内部 FIGURE_ID 不一致。虽然可能是重编号的结果（脚本先写、后来重排），但这会造成维护困难。**如果 rebuild 时需要追溯，容易出错**。

### 2. 遗留备份文件

`src/wtbench/manuscript/figure3_model_tradeoff.py.backup` — 应在 freeze 前清理。

### 3. Stop rule 无程序化执行

GEARS sweep 的 stop rule 仅作为 JSON 配置中的注释字符串存在（`configs/stage2/gears_hcc_backbone_sweep_v1.json`），没有自动检查。实际执行依赖手动判断。**这不影响结果正确性**，但如果 reviewer 要求证明 stop rule 是 prespecified（而非 post hoc），仅有 JSON comment 可能不够。建议将 stop rule 记录在带时间戳的 freeze 文件中。

### 4. `barcode_gem_group` 的提取逻辑

从 cell barcode 中通过 regex `-(\d+)$` 提取最后一个数字段。这对应于 10x Genomics 的 GEM group。但需确认：
- 原始数据中 barcode 格式是否一致（是否所有批次用相同格式）
- aggr 后的 barcode 是否保留了原始的 GEM group 后缀

### 5. K562 vs HCC 的 bridge 对象差异

K562 bridge 仅使用 10 个 TF targets（GSE90063 的 TF-pool 设计），而 HCC 使用 47-48 个（全基因组扰动）。正文已承认 K562 不提供 content-level replication。但需进一步明确：
- K562 的 10-TF 集合与 HCC 的 bridge 目标是否有重叠？
- 重叠基因在 K562 中的行为是否与 HCC 中一致？

### 6. 关键变量的方向对齐

`depmap_gene_dependency` 的 alignment direction = +1.0（higher = more dependent），而 `depmap_gene_effect` = -1.0（more negative = stronger effect）。正文说 "targets with larger aligned values were interpreted as showing stronger dependency"。需确认：
- 所有下游分析（Spearman rho, joint grid 分箱）使用的是对齐后的值
- 图 1f 展示的 Spearman rho 是 alignment 后的

---

# Part 4: 总体评估与修复优先级

## 按严重程度排序

| 优先级 | 问题 | 位置 | 修复成本 |
|--------|------|------|---------|
| **P0** | "trade-off" 因果性未建立 → 改为 "asymmetric recovery pattern" | Abstract, Results, Discussion | 低（措辞替换） |
| **P0** | 图号两版本不一致 → 统一确认 | 全文 | 中（需核对所有引用） |
| **P1** | `canonical_backbone` 标签的循环论证风险 → 增加 independence 论证 | Methods, Discussion | 中（需补充分析或论证） |
| **P1** | Background 核心前提缺乏引用支撑 → 提前引用 [8-11] | Background S1 | 低 |
| **P1** | "weaker" RNAi 的引用支撑不足 → 用 Results 数据支撑 | Background S20 | 低（已有 Results 数据） |
| **P2** | 代码图号映射不一致 → 同步 FIGURE_ID 与 publication 图号 | configs, scripts | 中 |
| **P2** | 0.333 shift-excess 值含义未解释 → 补充说明 | Results §3 | 低 |
| **P2** | R2 = 0.092 作为 "strongest axis" 的合理性 → 补充上下文 | Results §5 | 低 |
| **P2** | TVD 阈值 0.25 的来源 → 引用或解释 | Fig. 2 legend | 低 |
| **P3** | p = 0.001 精确性 → 确认 permutation 结果 | Fig. 1 legend | 低 |
| **P3** | 多个 strawman 措辞 → 添加引用或软化措辞 | 全文 | 低 |
| **P3** | 样本量限制讨论不足 → Discussion 补充 | Discussion | 低 |
| **P3** | 遗留 .backup 文件 → 清理 | src/ | 极低 |

## 修复建议汇总

1. **措辞层面（最低成本，最高影响）**:
   - "backbone-separation trade-off" → "asymmetric recovery pattern" 或 "complementary recovery profile"
   - "often conflated" → "can be conflated" 或提供引用
   - "central challenge" → "an important challenge" + 引用
   - p = 0.001 → 确认实际 permuted rho 分布后修正

2. **分析层面（中等成本）**:
   - 补充 GEARS sweep 中 backbone vs separation 的 scatter（用于支持或弱化 trade-off 措辞）
   - 补充 canonical_backbone labeling 与 baseline scoring 的独立性论证
   - 统一 Extended Data 图号方案

3. **文档层面（低中成本）**:
   - 清理备份文件
   - 同步代码 FIGURE_ID 与 publication 图号
   - 记录 stop rule prespecification 的时间戳
   - 补充 barcode_gem_group 提取逻辑的文档注释

---

# Part 5: Genome Biology 投稿可行性评估

## 优势 (Strengths)

1. **新颖的 benchmark 设计范式**：truth-first/architecture-aware 的方法论框架在领域内有一定独特性，不是又一个 expression prediction leaderboard
2. **方法学的严谨性**：pre-specified categories, frozen architecture, stop rule, covariate governance — 这些设计元素体现了一定的 rigor
3. **Reproducibility 基础设施好**：panel-level manifest, SHA256 hashes, source data TSV — 这些在投稿时是加分项
4. **诚实的自我限定**：全文反复强调 claim boundary，"qualified"、"bounded"、"supplementary" 等修饰词使用恰当
5. **已有外部文献支持核心论点**：[8-11] 可以为"简单 baseline 可以匹敌复杂模型"的论证提供独立背书
6. **对领域有建设性的批评**：不是单纯说"模型不好"，而是提供诊断框架（哪个组件被恢复、哪个没有）

## 劣势 (Weaknesses)

1. **样本量小 (n=47-48)**：仅有 2 个 breast-cancer cell line contexts，总共不到 50 个 targets。对于声称构建 "resource" 的工作，这个规模偏小
2. **Primary finding 不够强**："baseline 在 backbone 上好，GEARS 在 separation 上好" — 这是一个温和的发现，不是突破性结果。Reviewer 可能问：so what?
3. **缺乏独立验证**：K562 只有 10 个 TF targets 且 bridge 更弱 (rho ~0.5)，不能真正提供 external validation
4. **核心概念 "trade-off" 逻辑脆弱**（见断点 A）
5. **Truth 度量的选择有任意性**：为什么 `real_shift_mean_abs` 是 "phenotype-relevant" 的？这个 bridge 构造方式虽然合理，但不是唯一可能
6. **没有正面的生物学发现**：PFDN5 作为 anchor 是"已知的基因在已知的 cell line 中有已知的表型效应"，缺乏新的生物学 insight
7. **GEARS sweep 覆盖有限**：3 个参数的局部搜索不足以充分排除 GEARS 的潜力

## 竞争环境

- Genome Biology 发表过 Kedzierska et al. 2025 ("Zero-shot evaluation reveals limitations of single-cell foundation models")，说明该刊对 benchmark/critique 类文章有接受度
- 但 GB 通常期望更高的生物学发现含量，纯方法/benchmark 文章的接受门槛较高
- Ahlmann-Eltze et al. 2025 在 Nature Methods 发表了类似性质的 baseline-vs-DL 比较，如果他们的工作被视为更权威的版本，可能会挤压本文的发表空间

## 发表策略建议

### Option A: 以当前内容投稿 Genome Biology（风险较高）

- 需要先修复 P0-P1 级别的逻辑断点
- 在 cover letter 中强调：(1) truth-first 范式的方法学创新，(2) reproducibility 基础设施，(3) 对领域 leaderboard 文化的建设性批评
- 预期 reviewer 会追问的问题已在 Part 2 中断点中列出，需提前准备回应
- 估计接受概率：30-40%

### Option B: 先投 Nature Methods 或 Genome Biology，被拒后转 Bioinformatics 或 GigaScience

- Bioinformatics 对 benchmark 类文章接受度更高
- GigaScience 对 data resource + reproducible pipeline 有偏好
- 如果被 GB 拒，可以带着 reviewer 反馈改善后转投

### Option C: 增加生物学发现含量后投稿

- 如果能在更多 cell line contexts 上验证 bridge（增加 n），或在 anchor 基因的生物学功能上做更深入的挖掘（如 PFDN5 在 HCC38 vs HCC1143 中的不同行为机制），文章的生物学吸引力会显著提升
- 但根据 project stage 标签，分析 closure 已完成，不建议新增分析

### 我的建议

**可以尝试投稿 Genome Biology，但需在投稿前完成 P0 和 P1 修复**。同时准备一个 backup plan（如 Bioinformatics 或 GigaScience）。Cover letter 需要精心撰写，强调方法学创新和 reproducibility 基础设施，而非仅凭生物学发现。

核心卖点应该是："这是一个有原则的（principled）、可复现的（reproducible）、自带 claim boundary 的 benchmark 框架，而不是又一个 leaderboard。"

---

*审查人: Claude Code | 日期: 2026-04-28 | 文档版本: v1*
