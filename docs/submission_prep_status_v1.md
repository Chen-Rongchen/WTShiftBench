# Submission Prep Status v1

## 状态：figure redesign and submission packaging phase

**Phase label（2026-04-21 更新）：figure redesign and submission packaging phase — analysis closure 完成，infrastructure closure 完成，claim boundary 冻结，manuscript grammar / legends / Discussion-Conclusions 已同步；当前主要差距是 Genome Biology 级别的图版成熟度、公开资源、Additional files 和 submission metadata。**

## 当前执行口径更新（2026-04-21）

本轮 manuscript boundary / grammar audit 已完成。当前唯一正文 source of truth 为：

- `manuscript/text/manuscript_draft_v1.md`
- `manuscript/text/figure_legends_v1.md`

当前状态：

- Abstract、Background、Results、Methods、Discussion、Conclusions 已围绕同一套 benchmark grammar 同步。
- Figure 1-5 与 Extended Data Fig. 1-11 图注已完成 claim-boundary 同步。
- `docs/` 下早期 manuscript draft 文件保留为历史草稿，不再作为当前投稿稿同步源。
- 现有 `manuscript/figures/` 与 `manuscript/extended_data/` 图像文件为上一轮生成产物，后续需要按当前正文和图注重新用代码绘制。

下一阶段不是新增分析，而是 figure redesign / regenerated artifacts：更新绘图代码、图中文字、panel 布局和导出文件，同时保持 source data、claim boundary 和 endpoint hierarchy 不变。

## Genome Biology 对标后的差距判断（2026-04-21）

已阅读 `Genome Biology/` 下两篇近期参考论文：

- `s13059-026-04070-6_reference.pdf`
- `s13059-026-04063-5_reference.pdf`

对标结论：

- 当前稿件更接近 benchmark/resource paper，尤其接近 `s13059-026-04063-5_reference.pdf` 的问题类型。
- 科学主线和 claim boundary 已基本过线；不建议为第一版投稿新增分析。
- 当前最大差距是图版成熟度：现有图像仍偏内部分析报告，需要重画成数据优先、层级清楚、panel 问题单一的 Genome Biology / Nature Methods 风格图。
- 第二类差距是投稿完整度：public repository / archive DOI、Additional files 编号与说明、Data / Code availability、declarations 和作者元信息仍需补齐。
- 科学覆盖面上，HCC38/HCC1143 两个 primary contexts 比参考 benchmark paper 更窄；这一点已通过 K562 / RNAi boundary language 限制，不应通过新增主张补偿。

## 当前已就绪

| 层级 | 状态 |
|------|------|
| Analysis closure | 基本完成 |
| Infrastructure closure | 完成 |
| Claim boundary | 冻结 |
| Wording audit | Clean |
| 四敏感位置终审 | Clean |
| Abstract / Background / Results / Methods / Discussion / Conclusions | 同构，无 wording drift |
| Figure 1-5 legends | Clean |
| Extended Data Fig. 1-11 legends | Clean |
| Current figure image design | 待按当前图注重新绘制 |
| Genome Biology reference comparison | 完成第一轮差距判断 |
| Figure 1 redraw prototype | 已重构为 5-panel data-forward prototype，生成至 `reports/manuscript_figures_v2/fig1_truth_object/`，尚未替换投稿目录 |
| Figure 2 redraw | 下一步 |

## 四敏感位置终审结论

1. **Abstract 首句**："能否恢复"问句，无 overclaim ✅
2. **Figure 标题 × 4**：全部带限制性修饰语（partially / rather than / limitation-bounded）✅
3. **Abstract 结尾否定句**：三个"不支持"直接锁定 claim matrix 禁止边界 ✅
4. **Discussion 结尾**："不声称" + "只陈述"主动划界，与 Fig. 2 叙事一致 ✅

## 仍需人工判断的事项

以下事项需要人工判断，不能自动完成：

1. **Paper title**：当前可先保留宽口径标题，最后 polish 时再决定是否收紧到 CRISPR DepMap-anchor wording
2. **Author list**：未包含，需按实际贡献填写
3. **References**：draft 中未引用，需在正式写作时补入
4. **Supplementary table / figure numbering**：需与正文图表编号体系对齐
5. **Figure cross-references**：draft 中未插入 "(Fig. X)" 引用，需在正式稿中补入
6. **Figure visual design**：当前图像需要按已收口正文和图注重新绘制，不能仅沿用上一轮视觉版。
7. **Public repository / archive DOI**：需要作者确认公开位置和归档策略。

## 投稿 skeleton

### 1. Title 候选

以下题目只作为编辑候选，不改变 claim boundary：

1. Truth-first evaluation reveals architecture trade-offs in virtual perturbation models
2. Fitness-bridge architecture exposes limited recovery by current perturbation models
3. Architecture-aware perturbation benchmarking identifies a transcriptomic bridge to cellular fitness

当前更稳的 title 方向是第 1 个：强调 truth-first evaluation 与 architecture trade-off，不提前承诺 model recovery。

### 2. Author / affiliation 占位

| 字段 | 状态 | 备注 |
|------|------|------|
| Corresponding author | 待人工填写 | 需要真实姓名、邮箱与单位 |
| Author list | 待人工填写 | 需按实际贡献排序 |
| Affiliations | 待人工填写 | 不从仓库内容推断 |
| Contributions | 待人工填写 | 建议按 conceptualization / data curation / software / analysis / writing 分项 |
| Competing interests | 待人工确认 | 若无，正式稿写 `The authors declare no competing interests.` |

### 3. 正文图编号草案

| 编号 | 图题定位 | 对应 blueprint |
|------|----------|----------------|
| Fig. 1 | truth-DepMap bridge 的结构化 truth object | `truth object exists` |
| Fig. 2 | entrant recovery limited / architecture trade-off | `entrant recovery is limited / trade-off bounded` |
| Fig. 3 | axis interpretation partial / tiered | `axis interpretation is partial` |
| Fig. 4 | covariate + supplementary boundary / endpoint hierarchy | `boundary is explicit` |

正文引用建议：

- Result 1 引 `Fig. 2`
- Result 2 引 `Fig. 1`
- Result 3 引 `Fig. 3`
- Result 4 和 Result 5 引 `Fig. 4`
- Result 6 保持正文解释层，不抢主图 headline

### 4. Supplementary 编号草案

| 编号 | 内容 |
|------|------|
| Supplementary Fig. 1 | fuller entrant comparison |
| Supplementary Fig. 2 | GEARS sweep candidates |
| Supplementary Fig. 3 | anchor cutoff sensitivity |
| Supplementary Fig. 4 | control subsampling / formal interval |
| Supplementary Fig. 5 | full axis enrichment / consistency detail |
| Supplementary Fig. 6 | GSE90063 K562 13d/7d temporal panel details |
| Supplementary Fig. 7 | CRISPR DepMap vs RNAi DEMETER2 endpoint hierarchy details |
| Supplementary Fig. 8 | per-axis / per-target covariate detail |
| Supplementary Table 1 | final claim matrix |
| Supplementary Table 2 | anchor claim tiering |
| Supplementary Table 3 | HCC entrant comparison |
| Supplementary Table 4 | axis validation summary |
| Supplementary Table 5 | covariate balance summary |
| Supplementary Table 6 | Dixit/K562 supplementary tiering |
| Supplementary Table 7 | K562 entrant summary |

### 5. References 待补清单

正式稿至少需要补入以下类别引用：

- DepMap / CRISPR dependency datasets
- DEMETER2 / RNAi dependency processing
- GEARS
- scGPT
- Geneformer
- GSE241115 / HCC Perturb-seq source
- GSE90063 / Dixit K562 TF perturbation source
- Replogle CRISPRi datasets（若在 discussion 或 future work 中保留）
- Perturbation / virtual cell benchmarking 相关方法文献

### 6. Data / code availability 草案

当前可写成：

本研究使用的公开输入数据、配置化分析入口与主要中间产物路径在仓库中逐项列出。所有 Stage 2 主线运行入口位于 `scripts/`，可调参数位于 `configs/stage2/`，核心实现位于 `src/wtbench/`。关键 claim boundary 由 `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv` 与 `configs/stage2/closure_artifact_validation_v1.json` 共同约束。

正式投稿前仍需补充：

- 代码仓库 URL / DOI
- 数据下载 URL / accession 列表
- 大文件或未纳入 git 的产物存放位置
- 环境复现说明是否以 `pixi` 为主

## 投稿前编辑检查清单

- [x] Paper title 候选拟定
- [ ] Paper title 最终确认
- [ ] Author list 与 affiliation 填写
- [ ] Abstract 末尾否定句保留
- [ ] Discussion 结尾主动划界句保留
- [ ] Figure 标题限制性修饰语保留（partially / rather than / limitation-bounded）
- [x] 各 figure legend 与正文 claim 强度一致性规则补入 blueprint
- [ ] References 补入
- [x] Supplementary table / figure 编号草案补入
- [x] 正文图表交叉引用草案补入
- [ ] 句式风格统一（中英文语气一致）
- [x] 冗长句压缩（尤其是 Result Summary 段）
- [ ] Figure 1-5 按当前 manuscript grammar 重画
- [ ] Extended Data Fig. 1-11 按当前 figure legends 重画
- [ ] Figure 1 5-panel prototype 人工确认后替换投稿目录
- [ ] Figure 2 anchor tiering 重画
- [ ] Public GitHub / Zenodo DOI / Data availability 最终确认

## 禁止再做的动作

- 不新增分析结果
- 不引入新 claim
- 不改动 claim matrix 已冻结的 allowed/disallowed wording
- 不把 supplementary 对象升格为主线
- 不添加超越 architecture-level 的 mechanism recovery 表述
