# Stage 2 Replogle 2022 RPE1 Day 7 准入合同 v1

## 1. 文档定位

这份文档只冻结一件事：

**`Replogle 2022 RPE1 day 7` 作为 cross-cell-context short-horizon anchor 的准入规则。**

它是 `Replogle 2022 K562 GWPS day 8` 的并行候选，测试的是：A0/A1 architecture form 是否能从 K562 泛化到 RPE1 细胞背景。RPE1 是视网膜色素上皮细胞系，与 K562 的生物学背景不同，是跨细胞背景的 architecture form 泛化测试。

## 2. 与现有 Replogle 合同的关系

现有合同线：

- `Replogle 2022 K562 GWPS day 8` + DepMap CRISPR → `stage2_replogle_gwps_day8_admission_contract_v1.md`（primary external generalization anchor）
- `Replogle 2022 RPE1 day 7` + DepMap CRISPR → 本文档（cross-cell-context anchor）
- `Replogle 7d CRISPRi` + DepMap RNAi/shRNA → `stage2_replogle_rnai_expansion_admission_contract_v1.md`

三条线的区别：

| 维度 | K562 GWPS day 8 | RPE1 day 7 | K562 7d CRISPRi + RNAi |
|------|------------------|-------------|------------------------|
| 细胞系 | K562 | RPE1 | 待确认 |
| 时间点 | day 8 | day 7 | day 7 |
| 目标库 | genome-wide (~9866) | 待确认 | 待确认 |
| DepMap endpoint | CRISPR DepMap | CRISPR DepMap | RNAi/shRNA |
| 扰动模态 | CRISPRi | CRISPRi | CRISPRi |
| 定位 | primary short-horizon anchor | cross-cell-context anchor | modality-compatible expansion |
| 状态 | metadata-confirmed freeze | 合同制定中 | 待执行 |

## 3. 本地数据状态

### 3.1 本地已有数据

**状态**: AVAILABLE LOCALLY（2026-04-14 确认）

```
路径: data/raw/stage1a/replogle_2022_rpe1.h5ad
shape: (247914, 8749)
obs.cell_line: RPE1
obs.perturbation_type: CRISPR（原文献为 CRISPRi）
obs.nperts: 1 = 236429 cells; 0 = 11485 controls
unique target genes: 2394
```

### 3.2 待确认项（Paper-level metadata）

1. **Paper identity**: Replogle et al. 2022 Cell — "Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq"
2. **Library composition**: 2394 genes — 需确认是 genome-wide 还是 essential-prefiltered（不同于 K562 GWPS 的 9866，也不同于 K562 essential 的 2058）
3. **Duration**: day 7（待与原始数据 metadata 确认）
4. **DepMap model ID for RPE1**: 需查找 ACH-000xxx（DepMap 中 RPE1 的 model ID）

**状态**: PRE-ADMISSION（本地数据已就绪，paper-level metadata 待确认）

## 4. 数据身份冻结

### 4.1 实际数据特征

```
数据集: Replogle 2022 RPE1 day 7 CRISPRi Perturb-seq
细胞系: RPE1（视网膜色素上皮）
扰动类型: CRISPRi（dCas9-KRAB）
持续时间: day 7 after transduction
目标库: 待确认（可能是 genome-wide 或 essential-prefiltered）
```

### 4.2 待确认 DepMap Model ID

RPE1 的 DepMap model ID 预计为 `ACH-000xxx` 格式，具体 ID 需通过 DepMap 数据库确认。

### 4.3 数据集标签冻结（待完成）

正式标签（在 metadata 确认后）：

- `Replogle 2022 RPE1 day 7`
- `CRISPRi`
- `cross-cell-context short-horizon anchor`

## 5. 与当前目标空间的关系

### 5.1 RPE1 vs K562 GWPS

```
RPE1 day 7 (待确认) vs K562 GWPS day 8 (9866 genes)
重叠: 取决于 RPE1 library composition
```

解读: RPE1 是跨细胞背景测试，与 K562 的生物学背景不同（血癌细胞 vs 上皮细胞）。如果 RPE1 使用 genome-wide library，则可以直接与 K562 GWPS 比较 architecture form 的跨背景稳定性。

### 5.2 RPE1 vs GSE90063 K562 13d/7d

```
RPE1 day 7 vs GSE90063 K562 13d/7d
差异: 细胞背景不同 + library composition 不同
```

解读: GSE90063 是 K562 TF pool（14 genes），RPE1 是独立细胞系，两者均作为跨背景测试但 RPE1 更接近 formal generalization 测试。

## 6. What This Dataset CAN and CANNOT Answer

### 6.1 CAN Answer

- **A0 (architecture form)**: RPE1 CRISPRi day 7 中是否存在与 K562 相似的 backbone + shift-excess architecture form
- **A1 (bridge/adjudication form)**: architecture form 是否能在不同细胞背景（RPE1 vs K562）间泛化
- **Cross-cell-context stability**: genome-wide library 设计在 RPE1 中是否产生与 K562 相似的 transcriptomic structure
- **Essential-bias vs genome-wide comparison**: 如果 RPE1 数据同时包含两种 library，可以测试 essential-prefiltered vs genome-wide 的 architecture form 差异

### 6.2 CANNOT Answer

- **Content-level convergence with HCC**: RPE1 是独立细胞系，不代表 HCC breast cancer context
- **Matched endpoint claim**: RPE1 day 7 不等于 GSE90063 K562 7d/13d；细胞背景、library 组成均不同
- **External model-side generalization proved**: 只能说 cross-cell-context architecture form stability，不能说 generalization proved
- **Primary closure**: RPE1 是 secondary anchor，K562 GWPS day 8 才是 primary external generalization anchor

## 7. Admission Verdict

### 7.1 当前状态: PRE-ADMISSION（待外部 metadata 确认）

需要先完成以下 4 项外部确认才能进入 admission freeze：

1. 确认 Replogle 2022 Cell 论文包含 RPE1 day 7 CRISPRi 数据
2. 确认 RPE1 day 7 的 GEO accession 或数据下载入口
3. 确认 RPE1 day 7 的 target library composition
4. 确认 RPE1 的 DepMap model ID (ACH-000xxx)

### 7.2 最小入场条件

在下载大数据或运行正式 bridge 前，必须先确认：

1. Cell line 与 DepMap RPE1 model ID 映射明确
2. Gene namespace 可统一到 gene symbol
3. 目标基因与 DepMap CRISPR entries 可桥接
4. 能区分 RPE1 CRISPRi truth vs CRISPR DepMap endpoint 的 modality difference
5. 能形成独立报告，不覆盖 HCC 或 K562 GWPS 已冻结产物

### 7.3 合同冻结先决条件

若第 1-5 条全部满足，冻结本合同并进入正式 bridge execution；若任一不满足，写成 tested boundary 而非 admission。

## 8. 允许写法 vs 禁止写法

### 8.1 允许写法

- `Replogle 2022 RPE1 day 7`
- `cross-cell-context short-horizon anchor (RPE1 vs K562)`
- `A0 (architecture form) test in RPE1 CRISPRi day 7 context`
- `A1 (bridge/adjudication form) test: cross-cell-context architecture form stability`
- `architecture form generalization across cell backgrounds (RPE1 vs K562)`
- `CRISPRi transcriptomic truth -> CRISPR DepMap endpoint`

### 8.2 禁止写法

- `RPE1 as primary external generalization anchor`
- `cross-cell-context validation proved`
- `matched endpoint`
- `HCC-level replication in RPE1`
- `external model-side generalization proved`
- `RPE1 as replacement for K562 GWPS`

### 8.3 核心区分

**RPE1 day 7 + DepMap CRISPR** 是:
- cross-cell-context anchor（测试 architecture form 是否跨细胞背景泛化）
- day 7 duration
- 待确认 library composition
- secondary to K562 GWPS day 8

**不是**:
- primary external generalization anchor
- replacement for K562 GWPS
- content-level replication
- matched endpoint validation

## 9. 推荐 Paper Wording

### 9.1 引入语（Allowed）

"We further tested whether the observed architecture form generalizes across cell backgrounds using a CRISPRi screen in RPE1 cells (Replogle et al. 2022, day 7)."

### 9.2 结果陈述（Allowed）

"The RPE1 day 7 screen tested cross-cell-context architecture form stability, showing [result] compared to K562 GWPS day 8."

### 9.3 禁止写法示例

- "We validated our findings in RPE1 as a matched cell line"
- "RPE1 confirms K562-level architecture replication"
- "Cross-cell-context generalization was proved"

## 10. 与 K562 GWPS day 8 的关系

RPE1 day 7 与 K562 GWPS day 8 回答不同的问题：

| 维度 | K562 GWPS day 8 | RPE1 day 7 |
|------|-----------------|-------------|
| 主要问题 | genome-wide short-horizon architecture form 是否成立 | architecture form 是否跨细胞背景泛化 |
| 定位 | primary external generalization anchor | cross-cell-context secondary anchor |
| library | genome-wide (~9866) | 待确认 |
| 时间点 | day 8 | day 7 |

两者可以并行报告，但必须在论文中明确区分各自的主张层级。

## 11. 一句话收口

`Replogle 2022 RPE1 day 7` 可以作为 cross-cell-context short-horizon anchor 进入框架，但必须先确认 paper identity、target library composition 和 DepMap model ID；它只能写成 architecture form 跨细胞背景泛化的 secondary support，不能写成 primary closure、matched endpoint 或 external model-side generalization proved。
