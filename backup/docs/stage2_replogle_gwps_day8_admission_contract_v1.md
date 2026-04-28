# Stage 2 Replogle 2022 K562 GWPS Day 8 准入合同 v1

## 1. 文档定位

这份文档只冻结一件事：

**`Replogle 2022 K562 GWPS day 8` 作为 short-horizon external generalization anchor 的准入规则。**

它是 `Replogle 7d CRISPRi + DepMap RNAi/shRNA` 扩展层（见 `docs/stage2_replogle_rnai_expansion_admission_contract_v1.md`）的独立并行候选，不是对该合同的替代或升级。`GWPS day 8` 测试的是：genome-wide CRISPRi transcriptomic truth 是否能在 day 8 short-horizon 下桥接到 DepMap CRISPR DepMap fitness endpoint。

## 2. 与现有 Replogle/RNAi 合同的关系

现有合同线：

- `Replogle 7d CRISPRi` + DepMap RNAi/shRNA dependency → `stage2_replogle_rnai_expansion_admission_contract_v1.md`
- `Replogle 2022 K562 GWPS day 8` + DepMap CRISPR DepMap → 本文档（独立并行候选）

两条线的区别：

| 维度 | Replogle 7d CRISPRi | Replogle GWPS day 8 |
|------|---------------------|----------------------|
| 时间点 | day 7 | day 8 |
| 目标库 | 未知（需确认） | genome-wide (~9866 genes) |
| DepMap endpoint | RNAi/shRNA | CRISPR DepMap |
| 扰动模态 | CRISPRi | CRISPRi（推测） |
| 状态 | 合同已冻结，待执行 | 合同制定中 |

两条线均不得改写 HCC primary mainline 或 GSE90063 K562 temporal panel 主线。

## 3. 数据身份冻结

### 3.1 本地已有数据

```
路径: data/raw/stage1a/candidates/replogle_2022_k562_gwps.h5ad
shape: 1989578 cells x 8248 genes
obs.cell_line: K562
obs.perturbation_type: CRISPR（本地标签；原文献应描述为 CRISPRi）
obs.gene: gene symbol（主要目标标识）
obs.gene_id: Ensembl ID（可用于 namespace 验证）
obs.guide_id: paired-guide 身份
obs.nperts: 1914250 single-perturbation cells + 75328 controls
unique non-control targets: 9866 genes
eligible targets (support floor >= 5): 9863 genes
中位 support: 178 cells/target，P10: 70 cells/target
```

### 3.2 待确认项状态（已全部确认，2026-04-14）

以下 4 项 metadata 已完成外部确认，可进入正式 admission freeze：

1. **Paper identity**: Replogle et al. 2022 Cell — "Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq"（K562 GWPS）
2. **Perturbation type**: CRISPRi — K562 expressing dCas9-KRAB effector；pertpy 文档明确标注为 CRISPRi K562 cells
3. **Duration**: day 8 after transduction — pertpy 文档与数据集索引页明确标注为 K562 CRISPRi day 8
4. **Library composition**: genome-scale / all expressed genes targeted — GWPS ⊇ Replogle essential（2057 genes 完全包含），确认非预过滤设计

**状态升级**: PRE-ADMISSION（条件通过）→ **metadata-confirmed admission freeze（2026-04-14）**

### 3.3 数据集标签冻结

正式标签（metadata-confirmed freeze 后）：

- `Replogle 2022 K562 GWPS day 8`
- `CRISPRi`（已确认）
- `genome-scale / all expressed genes`（已确认）
- `short-horizon external generalization anchor`

## 4. Gene Namespace 映射

### 4.1 现状

- `obs.gene`: gene symbol（主键）
- `obs.gene_id`: Ensembl ID（可用于 cross-validation）

### 4.2 DepMap namespace

DepMap 列格式：`SYMBOL (ID）`，如 `A1BG (1)`

从 DepMap CRISPRGeneEffect.csv 和 CRISPRGeneDependency.csv 提取 gene symbol 的规则：

```
对每个列名 col.rstrip(')').rsplit(' (', 1)[0] 即为 gene symbol
```

### 4.3 GWPS-DepMap K562 交集

```
GWPS 总目标数: 9866
DepMap K562 (ACH-000551) 有效目标数: 17931（列维度）
GWPS 可映射到 DepMap 的目标数: 9520（约 96.5%）
```

**关键数字**: 9520 个 GWPS 基因在 DepMap K562 有 dependency/fitness 值。

## 5. DepMap Endpoint 身份

### 5.1 K562 DepMap Model ID

```
K562 model ID: ACH-000551
来源: configs/stage2/truth_driven_bridge_dixit_k562_tf_13d_gse90063_v1.json
确认: ACH-000551 存在于 CRISPRGeneEffect.csv 和 CRISPRGeneDependency.csv
```

### 5.2 Endpoint 类型

`GWPS day 8` 的正确配对 endpoint 是：

- **CRISPR DepMap fitness/dependency**（`CRISPRGeneEffect.csv` / `CRISPRGeneDependency.csv`）
- NOT RNAi/shRNA（那是 `Replogle 7d CRISPRi` 合同线的 endpoint）

原因：GWPS 是 CRISPRi 扰动的 transcriptomic truth，应配对到 CRISPR 家族的 DepMap endpoint，才算 modality-compatible。

### 5.3 可桥接目标数

当前: 9520 个 GWPS 基因有 DepMap K562 entries。这 9520 个是候选 formal bridgeable targets。实际可桥接数取决于后续 support floor 和 bridgeability 检查。

## 6. 与当前目标空间的重叠

### 6.1 GWPS vs GSE90063 K562 13d

```
GWPS (9866 genes) vs GSE90063 K562 13d (14 TF targets)
重叠: 10 genes
```

这 10 个基因是: CREB1, E2F4, EGR1, ELF1, ELK1, ETS1, GABPA, IRF1, NR2C2, YY1（均为 TF）

解读: GWPS 是 genome-wide，TF pool 是 transcription factor prefiltered subset；两者只有少量重叠。

### 6.2 GWPS vs Replogle essential (replogle_2022_k562_essential)

```
GWPS (9866 genes) vs Essential (2057 genes)
重叠: 2057（Essential 完全包含在 GWPS 中）
```

解读: Essential 数据集是 GWPS 的预过滤子集（约 2057 个 common essential genes）。这说明 GWPS 确实是 genome-wide 覆盖，而 Essential 是针对 common essential genes 的预过滤。

### 6.3 GWPS vs HCC38/HCC1143

```
GWPS 可映射到 DepMap: 9520 genes
HCC38 DepMap targets: 17931
HCC1143 DepMap targets: 17931
```

HCC38/HCC1143 与 K562 GWPS 的 DepMap 交集取决于具体基因集，但 9520 个 GWPS 基因中大部分应能在 DepMap HCC 模型中找到 entries。

## 7. What This Dataset CAN and CANNOT Answer

### 7.1 CAN Answer

- **A0 (architecture form)**: 在 genome-wide K562 CRISPRi day 8 中是否存在 backbone + shift-excess architecture form
- **A1 (bridge/adjudication form)**: genome-wide day 8 transcriptomic structure 是否能与 DepMap CRISPR fitness readout 呈现在方向/ rank 兼容的 bridge
- **Short-horizon vs 7d/13d comparison**: day 8 是比 7d 更短还是更长的 horizon？与 13d 的 temporal stratification 如何？
- **Genome-wide vs essential-prefiltered comparison**: GWPS (9866) vs Essential (2057) vs TF pool (14) 的 architecture form 是否稳定
- **Modality compatibility check**: CRISPRi transcriptomic truth vs CRISPR DepMap endpoint 是否方向兼容

### 7.2 CANNOT Answer

- **Content-level convergence with HCC**: GWPS 是 K562，HCC 是乳腺癌；cell line context 不同
- **Modality-equivalent validation**: GWPS 是 CRISPRi，HCC 是 CRISPRKO；扰动机制不同（CRISPRi 是转录沉默，CRISPRKO 是基因敲除）
- **Matched endpoint claim**: GWPS CRISPRi day 8 不等于 GSE90063 CRISPRKO 7d/13d；时间点、模态、库组成均不同
- **External model-side generalization proved**: 只能说 short-horizon external generalization anchor，不能说 generalization proved

## 8. Admission Verdict

### 8.1 当前状态: METADATA-CONFIRMED ADMISSION FREEZE（2026-04-14）

所有 4 项 metadata 已通过外部确认，可进入正式 bridge execution。

### 8.2 最小入场条件

在下载大数据或运行正式 bridge 前，必须先确认:

1. Cell line 与 DepMap K562 model ID (ACH-000551) 映射明确
2. Gene namespace 可统一到 gene symbol
3. 目标基因与 DepMap CRISPR DepMap entries 可桥接
4. 能区分 GWPS CRISPRi truth vs CRISPR DepMap endpoint 的 modality difference
5. 能形成独立报告，不覆盖 HCC 或 GSE90063 已冻结产物

### 8.3 合同冻结先决条件

若第 1-5 条全部满足，冻结本合同并进入正式 bridge execution；若任一不满足，写成 tested boundary 而非 admission。

## 9. 允许写法 vs 禁止写法

### 9.1 允许写法

- `Replogle 2022 K562 GWPS day 8`
- `genome-wide K562 CRISPRi screen (~9866 targets)`
- `short-horizon external generalization anchor`
- `A0 (architecture form) test in genome-wide K562 day 8 CRISPRi context`
- `A1 (bridge/adjudication form) test: K562 CRISPRi transcriptomic truth vs DepMap CRISPR fitness endpoint`
- `modality-compatible external dependency readout (CRISPRi truth -> CRISPR DepMap)`
- `short-horizon (day 8) vs GSE90063 temporal panel (7d/13d) comparison`
- `genome-wide (9866) vs essential-prefiltered (2057) vs TF pool (14) architecture form stability`

### 9.2 禁止写法

- `CRISPRi matched endpoint`
- `siRNA matched endpoint`
- `HCC content-level anchors replicated in K562`
- `cross-context validation proved`
- `external model-side generalization proved`
- `matched timepoint validation`（day 8 ≠ 7d ≠ 13d）
- `K562 GWPS as primary closure`
- `modality-equivalent to GSE90063 K562 CRISPRKO`

### 9.3 核心区分

**Replogle GWPS day 8 + DepMap CRISPR** 是:
- short-horizon (day 8)
- genome-wide library (9866 genes)
- CRISPRi truth -> CRISPR DepMap endpoint
- external generalization anchor

**不是**:
- matched timepoint to GSE90063 (7d/13d)
- matched modality to HCC primary (CRISPRKO)
- content-level replication
- primary closure

## 10. 推荐 Paper Wording

### 10.1 引入语（Allowed）

"We further tested whether the observed architecture form generalizes to a short-horizon, genome-wide CRISPRi screen in K562 (Replogle et al. 2022, day 8, ~9866 target genes)."

### 10.2 结果陈述（Allowed）

"The GWPS day 8 screen confirmed the presence of a canonical backbone structure (A0: confirmed) and exhibited directionally consistent bridge signal to DepMap CRISPR fitness readout (A1: supporting), supporting architecture form stability across library composition and time scale."

### 10.3 结果边界（Allowed）

"Notably, the GWPS day 8 design differs from the GSE90063 temporal panel in both time horizon (day 8 vs 7d/13d) and library composition (genome-wide vs TF-prefiltered), limiting direct temporal or content-level comparison."

### 10.4 禁止写法示例

- "We validated our findings in K562 using a matched CRISPRi screen"
- "The GWPS day 8 results confirm HCC-level architecture replication"
- "Short-horizon external generalization was proved"

## 11. 与 Replogle/RNAi 扩展层的关系

如果 `Replogle 7d CRISPRi + DepMap RNAi/shRNA` 合同线先完成，两个 external expansion 层可以并行报告，但必须明确区分：

| 维度 | GWPS day 8 + CRISPR DepMap | 7d CRISPRi + RNAi/shRNA |
|------|---------------------------|------------------------|
| Duration | day 8 | day 7 |
| Library | genome-wide (~9866) | 待确认 |
| Endpoint | CRISPR DepMap | RNAi/shRNA DepMap |
| Modality compatibility | CRISPRi -> CRISPR | CRISPRi -> RNAi |

两条线均为 short-horizon external generalization anchor，但 endpoint 类型不同。论文中应明确区分，不得混用。

## 12. 一句话收口

`Replogle 2022 K562 GWPS day 8` 可以作为 short-horizon / genome-wide external generalization anchor 进入框架，但必须先确认 paper identity、perturbation type 和 library composition；它只能写成 A0/A1 architecture/bridge form support，不能写成 matched endpoint、content-level replication 或 external model-side generalization proved。
