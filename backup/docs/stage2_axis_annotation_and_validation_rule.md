# Stage 2 功能轴的发现、注释与验证规则

## 1. 文档定位

这份文档只回答一个方法学问题：

**功能轴应该如何被定义、命名与验证。**

当前明确约束是：

- `GSEA / pathway enrichment` 适合做 `axis annotation` 与 `axis validation`
- **不适合**单独充当 `axis discovery` 或 `axis definition` 的主证据

如果只保留一句话，当前推荐顺序是：

**先发现 axis，再用 GSEA 解释 axis，再用 per-target pathway consistency 验证 axis。**

## 2. 先区分两个问题

### 2.1 结构问题

要先回答：

**这些 targets 是否真的落在同一条功能轴上？**

这是结构发现问题，不是通路命名问题。

主证据应优先来自：

- target 在 real shift 空间里是否形成稳定聚类、连续轴或共同 loading
- target 在 dependency / gene effect / bridge grid 上是否落在相近区域
- shared response / excess / context deviation 分解后，是否存在稳定共同结构
- 这种结构是否在跨 cell line / context 中至少部分复现

只有先证明：

**它们在数据几何和 truth-driven bridge 结构上确实是同一类对象**

后面才值得问：

**这类对象的生物学名字是什么？**

### 2.2 解释问题

第二个问题是：

**这条轴在生物学上更像什么程序、复合体或 pathway 主题？**

这里 `GSEA / pathway enrichment` 很有用，但它回答的是解释问题，不是定义问题。

## 3. 为什么不能用 GSEA 单独定义 axis

`target KO -> pathway enrichment` 不是充分证据，因为同一个 enrichment 可能来自：

- target 本身属于该 pathway
- target 不属于该 pathway，但扰动后引发该 pathway 的二级响应
- 更泛化的 stress / growth arrest / transcriptional collapse
- pathway gene set 彼此高度重叠带来的表面一致性

因此：

**“敲掉 A 后 spliceosome pathway 变了” 不等于 “A 一定属于 spliceosome axis”。**

这只能增加后验置信度，不能单独定义 axis。

## 4. 当前推荐的三层证据

### 4.1 第一层：结构发现（主证据）

功能轴存在与否，主要靠结构证据。

推荐对象：

- target-target 相似性（基于 real shift）
- target 在 dependency-shift grid 上的共同位置
- shared / excess / context-deviation 分解
- clustering / factorization / PCA / NMF / graph community / consensus clustering

这一层负责回答：

**axis 是否存在。**

### 4.2 第二层：轴注释（核心解释证据）

在 axis 已经被定义后，再问它在生物学上是什么。

更稳的做法不是先逐 target 跑 GSEA，而是先做 axis-level enrichment。

优先方法：

1. 对 axis loading genes 做 enrichment
2. 对 axis member targets 的 shared real-shift signature 做 enrichment

推荐知识库：

- MSigDB Hallmark
- Reactome
- GO BP
- KEGG / Canonical pathways
- CORUM
- TF target / footprint（如 DoRothEA、PROGENy）

这一层负责回答：

**axis 应该如何命名。**

### 4.3 第三层：轴内一致性验证（辅助验证）

在 axis 已经被定义并命名后，再看单个 target 是否大体朝共同 pathway 方向变化。

推荐对象：

- per-target fgsea
- pathway sign consistency
- top pathway recurrence
- leading-edge overlap

这一层负责回答：

**axis 内部是否足够一致。**

它是 coherence audit，不是 discovery 本身。

## 5. GSEA 在当前项目里最有价值的三个用途

### 5.1 给 axis 命名

如果某条 axis 的 shared signature 或 loading genes 反复指向：

- `RNA splicing`
- `mRNA processing`
- `spliceosomal complex`

那就可以较稳地命名为：

`RNA processing / spliceosome-associated axis`

### 5.2 帮助区分 backbone 与 deviation

如果 canonical backbone 的多个 axis 主要打到：

- ribosome biogenesis
- transcription machinery
- RNA processing
- proteostasis / translation

而 deviation / line-skewed 轴更偏向：

- stress
- MAPK / NFkB
- cell cycle context-specific program
- lineage/state-specific response

那么 pathway enrichment 可作为 backbone 与 deviation 的解释支撑。

### 5.3 识别 generic collapse

若某条 axis 的 shared response 主要是：

- apoptosis
- p53 / stress response
- global suppression of translation / transcription

则要警惕它更像：

`generic essentiality / collapse axis`

而不是机制更清楚的功能轴。

## 6. 只做 GSEA 时最容易犯的错误

- 把 downstream consequence 误当 upstream identity
- 把 generic essentiality 误当功能特异性
- 被 pathway set 重叠放大“伪重复证据”
- 在单 perturbation 噪声较大时，把单 target enrichment 误当稳定轴结构

因此项目内应默认：

**axis-level shared signature enrichment > single-target GSEA**

## 7. 当前项目的正式规则

### 7.1 功能轴的发现

主要靠：

- target-level bridge structure
- shift similarity / clustering / factorization
- shared vs line-skewed vs excess decomposition
- cross-context replication

### 7.2 功能轴的生物学注释

主要靠：

- axis loading gene enrichment
- shared axis signature enrichment
- external knowledge base（GO / Reactome / CORUM / co-essentiality）

### 7.3 功能轴的内部一致性验证

辅助靠：

- per-target fgsea
- pathway direction consistency
- top pathway recurrence
- leading-edge overlap

## 8. 最小执行顺序

如果现在就要把这套规则落到分析流程，最小顺序应是：

1. 冻结每条 axis 的成员 targets
2. 为每条 axis 构建 shared real-shift signature 或 gene ranking
3. 对 axis signature 做 enrichment
4. 再对 axis 内单个 target 做 fgsea 一致性审计
5. 只有在结构、注释、一致性与外部知识同时支持时，才把它正式写成“功能轴”

## 9. 当前一句话结论

项目里确实需要看扰动后的 pathway 变化；但它的角色应是：

**在结构发现之后，对功能轴做注释与一致性验证，而不是单独用来定义功能轴。**
