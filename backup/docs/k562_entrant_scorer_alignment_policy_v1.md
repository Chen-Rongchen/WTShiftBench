# K562 Entrant Scorer Alignment Policy v1

## 1. 文档定位

这份文档解决一个问题：

**K562 7d/13d entrant evaluation 中，各 entrant 的 prediction gene ID space 不同（ENSG vs symbol，genome-wide vs atlas-space），scorer 应如何在这种异质性下执行可比评分。**

本文件不引入新结果，只冻结 scorer 的执行规则。

## 2. K562 h5ad 的 gene ID 空间

- K562 h5ad var index 格式：`ENSG_ID + "_" + HGNC_symbol`（如 `ENSG00000000003_TP53`）
- 13d unique genes: 21,713（ENSG-level）
- 7d unique genes: 23,111（ENSG-level）
- Union: 24,000 unique ENSG IDs
- Truth delta matrix 使用 ENSG IDs 作为列标识（从 ENSG_symbol 格式提取 ENSG 前缀）

## 3. 各 entrant 的 prediction gene ID space

| Entrant | Prediction gene ID type | Prediction universe | Aligned scoring universe |
|---------|------------------------|--------------------|--------------------------|
| GEARS base | hgnc_symbol | 45 atlas gene symbols | 45-gene K562-atlas intersection |
| scGPT | hgnc_symbol | ~18,700 genome-wide symbols | Entrant-specific intersection with truth space |
| Geneformer | hgnc_symbol | ~20,600 genome-wide symbols | Entrant-specific intersection with truth space |
| lm_train_lowrank | hgnc_symbol (chargram-derived) | ~23,000 genome-wide symbols | Entrant-specific intersection with truth space |
| lm_g_scgpt_ridge | hgnc_symbol | ~18,700 genome-wide (scGPT embedding) | Entrant-specific intersection with truth space |
| lm_g_geneformer_ridge | hgnc_symbol | ~20,600 genome-wide (Geneformer embedding) | Entrant-specific intersection with truth space |

**关键约束**：Truth delta matrix 列标识为 ENSG IDs；所有 entrant 的 prediction 列标识为 HGNC symbols。Scorer 必须先将 symbol 映射到 ENSG，再与 truth 对齐。

## 4. Scorer 标准对齐顺序（冻结版）

给定一个 entrant 的 raw prediction file 和对应的 truth delta file， scorer 应执行以下步骤：

### Step 1：识别 entrant 的 gene ID type

- 若列名以 `ENSG` 开头或包含数字+字母组合的 ENSG 格式 → 视为 ENSG ID
- 否则默认视为 hgnc_symbol

### Step 2：通过冻结映射表转到 ENSG

- 映射表路径：`configs/stage2/gene_id_mapping_k562_v1.tsv`
- 映射表结构：`ensembl_gene_id | hgnc_symbol | in_k562_13d | in_k562_7d`
- 行为规则：
  - 若 entrant 列为 ENSG ID：直接使用（跳过映射）
  - 若 entrant 列为 hgnc_symbol：
    1. 查 `hgnc_symbol` 列
    2. 若 symbol 在映射表中唯一 → 取其对应 `ensembl_gene_id`
    3. 若 symbol 在映射表中不唯一（重码）→ 保留所有匹配行，scorer 使用所有匹配行共同覆盖的 ENSG 交集
    4. 若 symbol 不在映射表中 → 该列不进入 scoring
  - 13 个含下划线的 symbol（如 `RP11-34P13.7`）按标准 symbol 处理

### Step 3：与 truth 做 intersection

- Truth matrix 列 = ENSG IDs
- Entrant 已映射列 = ENSG IDs
- 取交集：`common_ensgs = set(truth_cols) ∩ set(entrant_mapped_cols)`
- 仅在 `common_ensgs` 上计算 per-target Spearman correlation

### Step 4：Entrant-specific aligned scoring universe

- **GEARS**：在 45 个 K562∩Atlas gene symbols 上评分（这是 GEARS 的全部 output space）
- **Embedding-based entrants**：在 entrant 实际输出且可映射到 truth space 的基因上评分
- **禁止**的行为：
  - 禁止将各 entrant 强行扩充到"共同全集"（如统一限定到 45 个基因）
  - 禁止把 GEARS 的 45-gene atlas-space 输出与 scGPT 的 ~18K genome-wide 输出写成"同一 universe 下的比较"
  - 禁止在未显式声明的情况下将不同 entrant 的 Spearman 值并置比较

## 5. Entrant-specific scoring universe 记录

| Entrant | Timepoint | Scored gene count | Scoring universe description |
|---------|-----------|------------------|--------------------------|
| GEARS base | 13d | 45 | Full GEARS output space = K562-atlas intersection |
| GEARS base | 7d | 45 | Full GEARS output space = K562-atlas intersection |
| scGPT | 13d | ~45 (in vocab & in atlas) | Entrant genome-wide ∩ atlas space |
| scGPT | 7d | ~45 (in vocab & in atlas) | Entrant genome-wide ∩ atlas space |
| Geneformer | 13d | ~45 (in vocab & in atlas) | Entrant genome-wide ∩ atlas space |
| Geneformer | 7d | ~45 (in vocab & in atlas) | Entrant genome-wide ∩ atlas space |
| lm_train_lowrank | 13d | ~45 (mapped & in atlas) | Entrant genome-wide ∩ atlas space |
| lm_train_lowrank | 7d | ~45 (mapped & in atlas) | Entrant genome-wide ∩ atlas space |
| lm_g_scgpt_ridge | 13d | ~45 (in vocab & in atlas) | Entrant genome-wide ∩ atlas space |
| lm_g_scgpt_ridge | 7d | ~45 (in vocab & in atlas) | Entrant genome-wide ∩ atlas space |
| lm_g_geneformer_ridge | 13d | ~45 (in vocab & in atlas) | Entrant genome-wide ∩ atlas space |
| lm_g_geneformer_ridge | 7d | ~45 (in vocab & in atlas) | Entrant genome-wide ∩ atlas space |

## 6. 如何解释可比性

K562 entrant evaluation 的 entrants 分属两类 scoring universe：

### GEARS：Atlas-space entrant

- 输出固定为 45 个 atlas gene symbols（K562 h5ad 与 HCC atlas 的交集）
- 45 个基因是 GEARS 的完整 output space，不是截断结果
- 可与 HCC GEARS 在相同 atlas gene space 上做 architecture-form 比较
- 但不可与 genome-wide entrants 在"同一基因集"上做公平比较

### Embedding-based entrants：Genome-wide entrants

- 输出为 genome-wide symbols，可映射到 ~20K+ 基因
- 在实际可对齐且与 atlas 重叠的基因子集上评分
- 它们的"有利基因"可能比 GEARS 更多，但这是因为 prediction universe 更大
- 可相互比较（均在 atlas 基因子集上），但与 GEARS 的比较只限于 architecture-form/pattern 层面，不在 raw Spearman 数值层面

### 正式禁止并置表述

以下表述在正式文稿中**禁止使用**：

- "GEARS (ρ̄=0.13) 低于 scGPT (ρ̄=0.48)" 在"相同基因集"意义上 — 错误，两者的 scoring universe 不同
- "在相同 45 个基因上，embedding-based entrants 优于 GEARS" — 错误，embedding-based entrants 的评分 universe 不严格等于 45

### 合规表述示例

- "在 GEARS 的完整 output space（45 个 atlas 基因）上，GEARS base 的 mean Spearman 为 0.13（13d）和 0.09（7d）"
- "在 embedding-based entrants 可对齐且与 atlas 重叠的基因子集上，scGPT 的 mean Spearman 为 0.48（7d）"
- "两类 entrants 的评分 universe 不同（GEARS = atlas-space 完整输出；embedding-based = genome-wide 的 atlas 子集），因此 raw Spearman 数值不具严格可比性，但 temporal pattern（7d > 13d）在两类 entrants 中均可见"

## 7. Truth 主空间定义

- **Truth delta matrix 的主 ID 空间：ENSG IDs**
- Truth matrix 由 K562 h5ad 的 ENSG_symbol 格式 var index 构建
- Truth 列名 = ENSG ID（从 ENSG_symbol 提取）
- Truth 行标识 = target_gene（symbol）

## 8. 下一步建议

若后续需要在 K562 entrants 之间进行更严格的可比性分析，建议：

1. 为 embedding-based entrants 额外计算一次"限定在 GEARS 45-gene output space 上的 Spearman"
2. 在 Supplementary 中明确标注这是 entrant-specific aligned universe vs GEARS full output space 的区别
3. 在 Results 写作时区分：architecture-form 比较（可用 GEARS 45-gene atlas space）vs genome-wide entrants 的评分（在自己可对齐 universe 内）

## 9. 一句话收口

K562 scorer 的核心规则是：各 entrant 在自己可对齐的基因宇宙内评分；GEARS 的 45-gene atlas-space 是完整 output space，embedding-based entrants 的评分 universe 是其全基因组输出的 atlas 子集；二者不做伪公平比较，只在 temporal pattern、architecture-form 和 per-target profile 层面做跨-universe 讨论。
