# Submission Prep Status v1

## 状态：pre-submission editorial convergence ready

**Phase label（2026-04-15 冻结）：pre-submission editorial convergence ready — analysis closure 基本完成，infrastructure closure 完成，claim boundary 冻结，wording audit clean，四敏感位置终审 clean，remaining work = 编辑性压缩与投稿准备。**

## 当前执行口径更新（2026-04-21）

本轮 manuscript boundary / grammar audit 已完成。当前唯一正文 source of truth 为：

- `manuscript/text/manuscript_draft_v1.md`
- `manuscript/text/figure_legends_v1.md`

当前状态：

- Abstract、Background、Results、Methods、Discussion、Conclusions 已围绕同一套 benchmark grammar 同步。
- Figure 1-6 与 Extended Data Fig. 1-10 图注已完成 claim-boundary 同步。
- `docs/` 下早期 manuscript draft 文件保留为历史草稿，不再作为当前投稿稿同步源。
- 现有 `manuscript/figures/` 与 `manuscript/extended_data/` 图像文件为上一轮生成产物，后续需要按当前正文和图注重新用代码绘制。

下一阶段不是新增分析，而是 figure redesign / regenerated artifacts：更新绘图代码、图中文字、panel 布局和导出文件，同时保持 source data、claim boundary 和 endpoint hierarchy 不变。

## 当前已就绪

| 层级 | 状态 |
|------|------|
| Analysis closure | 基本完成 |
| Infrastructure closure | 完成 |
| Claim boundary | 冻结 |
| Wording audit | Clean |
| 四敏感位置终审 | Clean |
| Abstract / Background / Results / Methods / Discussion / Conclusions | 同构，无 wording drift |
| Figure 1-6 legends | Clean |
| Extended Data Fig. 1-10 legends | Clean |
| Current figure image design | 待按当前图注重新绘制 |

## 四敏感位置终审结论

1. **Abstract 首句**："能否恢复"问句，无 overclaim ✅
2. **Figure 标题 × 4**：全部带限制性修饰语（partially / rather than / limitation-bounded）✅
3. **Abstract 结尾否定句**：三个"不支持"直接锁定 claim matrix 禁止边界 ✅
4. **Discussion 结尾**："不声称" + "只陈述"主动划界，与 Fig. 2 叙事一致 ✅

## 仍需人工判断的事项

以下事项需要人工判断，不能自动完成：

1. **Paper title**：尚未确定，需根据论文主卖点拟定
2. **Author list**：未包含，需按实际贡献填写
3. **References**：draft 中未引用，需在正式写作时补入
4. **Supplementary table / figure numbering**：需与正文图表编号体系对齐
5. **Figure cross-references**：draft 中未插入 "(Fig. X)" 引用，需在正式稿中补入
6. **Figure visual design**：当前图像需要按已收口正文和图注重新绘制，不能仅沿用上一轮视觉版。

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

## 禁止再做的动作

- 不新增分析结果
- 不引入新 claim
- 不改动 claim matrix 已冻结的 allowed/disallowed wording
- 不把 supplementary 对象升格为主线
- 不添加超越 architecture-level 的 mechanism recovery 表述
