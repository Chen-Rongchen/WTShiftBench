# Stage 2 功能轴分析最小模板

## 1. 文档定位

这份文档不是再解释“为什么不能直接用 GSEA 定义 axis”，而是把已有规则压成一个**最小可执行模板**。

适用场景：

- 已经有冻结好的 axis members / axis object
- 准备开始做 axis-level annotation
- 准备补 axis-level consistency audit

如果只保留一句话，执行顺序固定为：

**冻结 axis -> 构建 shared signature -> 做 axis enrichment -> 做 per-target consistency audit -> 汇总命名与证据等级。**

## 2. 入口对象

分析开始前，至少要先固定三类对象：

### 2.1 axis members

每条 axis 必须先有固定成员列表，例如：

- `canonical_backbone_axis_1`
- `canonical_backbone_axis_2`
- `shift_excess_axis_1`
- `line_skewed_axis_1`

最小字段建议：

- `axis_id`
- `axis_family`
- `target_gene`
- `membership_weight`
- `cell_line_scope`
- `evidence_tier`

### 2.2 gene-level axis signature

每条 axis 至少要有一种可排序的 gene-level signature：

- shared real-shift mean
- factor loading ranking
- positive / negative loading genes

最小字段建议：

- `axis_id`
- `gene`
- `score`
- `direction`

### 2.3 per-target signatures

后续做一致性验证时，需要 axis 内每个 target 的单独 gene ranking 或 perturbation signature。

最小字段建议：

- `axis_id`
- `target_gene`
- `gene`
- `score`

## 3. Step 1：先冻结 axis members

这一步回答：

**到底在分析哪一条 axis。**

最小要求：

- axis 成员在分析前冻结，不在 enrichment 后倒推改成员
- 如果 axis 有 primary / supplementary 之分，要先写清
- 如果 axis 只在某个 cell line 成立，要明确 `cell_line_scope`

最小产物建议：

- `reports/.../axis_membership.tsv`

## 4. Step 2：构建 axis shared signature

这一步回答：

**这条 axis 共同推动了哪些 gene-level 变化。**

推荐做法二选一：

### 方法 A：axis member targets 的 shared real-shift

例如：

- axis 内 targets 的平均 delta
- axis 内 targets 的 shared component

### 方法 B：factor / loading 导出的 gene ranking

例如：

- axis loading 分数
- 正负向 loading genes 排名

最小产物建议：

- `reports/.../axis_gene_signature.tsv`

最小字段：

- `axis_id`
- `gene`
- `axis_score`
- `rank`

## 5. Step 3：做 axis-level enrichment

这一步回答：

**这条 axis 在生物学上最像什么。**

优先知识库：

- `MSigDB Hallmark`
- `Reactome`
- `GO BP`
- `CORUM`

可选扩展：

- `KEGG / Canonical pathways`
- `TF target`
- `footprint / PROGENy`

最小产物建议：

- `reports/.../axis_enrichment.tsv`

最小字段：

- `axis_id`
- `database`
- `term`
- `NES_or_effect`
- `FDR`
- `leading_edge_size`

### 命名规则

axis 命名不应来自单个 term，而应来自：

- 多个 top terms 是否收敛到同一主题
- CORUM / pathway / TF evidence 是否相互支持
- 是否与 axis members 的已知 biology 一致

推荐输出：

- `axis_label`
- `axis_annotation_note`

## 6. Step 4：做 per-target consistency audit

这一步回答：

**axis 内单个 target 是否大体朝共同 pathway 方向变化。**

推荐检查：

- pathway sign consistency
- top pathway recurrence
- leading-edge overlap

最小产物建议：

- `reports/.../axis_target_consistency.tsv`

最小字段：

- `axis_id`
- `target_gene`
- `database`
- `term`
- `NES_or_effect`
- `sign`
- `leading_edge_size`

进一步汇总建议：

- `pathway_sign_consistency`
- `top_pathway_recurrence`
- `mean_leading_edge_overlap`

## 7. Step 5：做最终综合判定

只有当下面几类证据同时存在时，才较稳地把它写成功能轴：

- 结构上聚在一起
- dependency / shift 上有共同位置
- shared signature 指向一致 pathway 主题
- 单 target pathway 响应大体一致
- 外部知识支持这些成员 targets 在机制上相关

推荐最终输出一个汇总表：

- `axis_id`
- `axis_label`
- `structure_support`
- `annotation_support`
- `consistency_support`
- `external_knowledge_support`
- `final_call`

其中 `final_call` 建议限制为：

- `supported_functional_axis`
- `supported_but_generic_collapse_axis`
- `partially_supported_axis`
- `insufficient_support`

## 8. 最小产物清单

如果只做最小版本，最后至少应有这四张表：

1. `axis_membership.tsv`
2. `axis_gene_signature.tsv`
3. `axis_enrichment.tsv`
4. `axis_target_consistency.tsv`

再加一份面向结论层的：

5. `axis_summary.tsv`

## 9. 写作边界

写结果时必须坚持：

- 不把单 target GSEA 当作 axis existence 的主证据
- 不把 generic stress / collapse 直接命名成功能特异性 axis
- 不把高冗余 pathway term 的重复出现误写成“多重独立证据”
- 不在 enrichment 之后反向修改 axis members

## 10. 推荐一句话模板

如果要把结果写成一句短结论，推荐格式是：

`该 axis 先由 target-level bridge structure 与 shared shift geometry 定义，再由 axis-level enrichment 命名，并经 per-target pathway consistency audit 验证其内部一致性。`
