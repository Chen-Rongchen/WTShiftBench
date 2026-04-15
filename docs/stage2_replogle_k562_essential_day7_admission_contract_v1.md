# Stage 2 Replogle 2022 K562 Essential Day 7 准入合同 v1

## 1. 文档定位

这份文档只冻结一件事：

**`Replogle 2022 K562 essential day 7` 作为 essential-bias sensitivity / failure-decomposition panel 的准入规则。**

它是 `Replogle 2022 K562 GWPS day 8` 的 essential-prefiltered 版本，测试的是：在 essential-bias target library 下，framework 还能工作到什么程度；baseline/entrant trade-off 会不会变化。

**重要区分**: 本数据集 NOT a replacement for GWPS day 8。它们回答不同的问题：
- GWPS day 8 = formal short-horizon external generalization (genome-wide)
- K562 essential day 7 = essential-bias sensitivity / failure-decomposition panel

## 2. 与现有 Replogle 合同的关系

现有合同线：

- `Replogle 2022 K562 GWPS day 8` + DepMap CRISPR → `stage2_replogle_gwps_day8_admission_contract_v1.md`（primary external generalization anchor）
- `Replogle 2022 K562 essential day 7` + DepMap CRISPR → 本文档（essential-bias sensitivity panel）
- `Replogle 7d CRISPRi` + DepMap RNAi/shRNA → `stage2_replogle_rnai_expansion_admission_contract_v1.md`

三条线的区别：

| 维度 | K562 GWPS day 8 | K562 essential day 7 | K562 7d CRISPRi + RNAi |
|------|-----------------|----------------------|------------------------|
| 时间点 | day 8 | day 7 | day 7 |
| 目标库 | genome-wide (~9866) | essential-prefiltered (~2057) | 待确认 |
| DepMap endpoint | CRISPR DepMap | CRISPR DepMap | RNAi/shRNA |
| 扰动模态 | CRISPRi | CRISPRi | CRISPRi |
| 定位 | primary anchor | sensitivity panel | expansion |
| 状态 | metadata-confirmed freeze | 合同制定中 | 待执行 |

## 3. 本地数据状态

### 3.1 本地已有数据

**状态**: AVAILABLE LOCALLY（2026-04-14 确认）

```
路径: data/raw/stage1a/replogle_2022_k562_essential.h5ad
shape: (310385, 8563)
obs.cell_line: K562
obs.perturbation_type: CRISPR（原文献为 CRISPRi）
obs.nperts: 1 = 299694 cells; 0 = 10691 controls
unique target genes: 2058
```

与 GWPS 的关系：GWPS (9866) ⊇ Essential (2058)，Essential 是 GWPS 的预过滤子集（约 2058 个 20Q1 Cancer Dependency Map common essential genes）。

### 3.2 待确认项状态（Pending - 需要外部确认）

以下 4 项 metadata 需要外部确认：

1. **Paper identity**: Replogle et al. 2022 Cell — "Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq"
2. **GEO accession**: 待确认（同一篇 Cell 2022 论文的数据子集）
3. **Library composition**: ~2057 common essential genes（20Q1 Cancer Dependency Map 预过滤）
4. **DepMap model ID**: ACH-000551（与 K562 GWPS 相同）

**状态**: PRE-ADMISSION（待外部确认 + 数据下载）

## 4. 数据身份冻结（待完成）

### 4.1 预期数据特征

```
数据集: Replogle 2022 K562 essential day 7 CRISPRi Perturb-seq
细胞系: K562
扰动类型: CRISPRi（dCas9-KRAB）
持续时间: day 7 after transduction
目标库: ~2057 common essential genes（20Q1 Cancer Dependency Map 预过滤）
目标基因来源: 20Q1 Cancer Dependency Map common essential gene list
```

### 4.2 关键数字（预期）

```
Essential targets: ~2057 genes
与 GWPS 重叠: 2057（Essential 完全包含在 GWPS 中）
DepMap K562 (ACH-000551) 有效目标数: ~17931
Essential 可映射到 DepMap 的目标数: ~2057（全部）
```

### 4.3 DepMap Endpoint 身份

`K562 essential day 7` 的正确配对 endpoint 是：

- **CRISPR DepMap fitness/dependency**（`CRISPRGeneEffect.csv` / `CRISPRGeneDependency.csv`）
- NOT RNAi/shRNA（那是 `Replogle 7d CRISPRi` 合同线的 endpoint）

原因：K562 essential 是 CRISPRi 扰动的 transcriptomic truth，应配对到 CRISPR 家族的 DepMap endpoint。

## 5. 与当前目标空间的重叠

### 5.1 Essential vs GWPS

```
Essential (2057 genes) vs GWPS (9866 genes)
重叠: 2057（Essential 完全包含在 GWPS 中）
```

解读: Essential 数据集是 GWPS 的预过滤子集（约 2057 个 common essential genes）。这说明 GWPS 确实是 genome-wide 覆盖，而 Essential 是针对 common essential genes 的预过滤。

### 5.2 Essential vs GSE90063 K562 13d

```
Essential (2057 genes) vs GSE90063 K562 13d (14 TF targets)
重叠: 取决于有多少 TF 落在 essential gene list 中
```

解读: Essential 是 essential-prefiltered library，TF pool 是 transcription factor prefiltered subset；两者设计逻辑不同。

## 6. What This Dataset CAN and CANNOT Answer

### 6.1 CAN Answer

- **A0 (architecture form)**: 在 essential-prefiltered K562 CRISPRi day 7 中是否存在 backbone + shift-excess architecture form
- **A1 (bridge/adjudication form)**: essential-bias library 是否仍能与 DepMap CRISPR fitness readout 呈现方向兼容的 bridge
- **Essential-bias sensitivity**: essential gene set 中的 bridge signal 是否比 genome-wide 更强或更弱
- **Baseline/entrant trade-off**: essential-prefiltered library 下，baseline/entrant trade-off 是否变化
- **GWPS vs Essential comparison**: genome-wide vs essential-prefiltered 的 architecture form 是否稳定

### 6.2 CANNOT Answer

- **Primary external generalization**: GWPS day 8 才是 formal primary anchor；essential day 7 是 sensitivity panel
- **Content-level convergence with HCC**: K562 essential 是 K562，与 HCC breast cancer context 不同
- **Essential gene list as anchor**: essential-bias 只是一种 library 设计，不代表生物学 ground truth
- **External model-side generalization proved**: 只能说 essential-bias sensitivity / failure-decomposition
- **Matched endpoint claim**: K562 essential day 7 ≠ GWPS day 8；library 组成、时间点均不同

## 7. Admission Verdict

### 7.1 当前状态: PRE-ADMISSION（待外部 metadata 确认 + 数据下载）

需要先完成以下步骤才能进入 admission freeze：

1. 确认 Replogle 2022 Cell 论文中 K562 essential day 7 的 GEO accession
2. 下载 `replogle_2022_k562_essential.h5ad` 到本地
3. 验证 target count (~2057) 和 library composition
4. 确认 DepMap K562 model ID (ACH-000551)

### 7.2 最小入场条件

在下载大数据或运行正式 bridge 前，必须先确认：

1. Cell line 与 DepMap K562 model ID (ACH-000551) 映射明确
2. Gene namespace 可统一到 gene symbol
3. Essential targets 与 DepMap CRISPR entries 可桥接
4. 能区分 Essential CRISPRi truth vs CRISPR DepMap endpoint 的 modality difference
5. 能形成独立报告，不覆盖 GWPS day 8 已冻结产物

### 7.3 合同冻结先决条件

若第 1-5 条全部满足，冻结本合同并进入正式 bridge execution；若任一不满足，写成 tested boundary 而非 admission。

## 8. 允许写法 vs 禁止写法

### 8.1 允许写法

- `Replogle 2022 K562 essential day 7`
- `essential-prefiltered K562 CRISPRi screen (~2057 targets)`
- `essential-bias sensitivity / failure-decomposition panel`
- `A0 (architecture form) test in essential-prefiltered K562 day 7 CRISPRi context`
- `A1 (bridge/adjudication form) test: essential-bias library vs DepMap CRISPR fitness endpoint`
- `essential-bias sensitivity: baseline/entrant trade-off check under essential-prefiltered library`
- `genome-wide (9866) vs essential-prefiltered (2057) architecture form stability comparison`

### 8.2 禁止写法

- `K562 essential as replacement for GWPS day 8`
- `essential day 7 as primary external generalization anchor`
- `essential-prefiltered library as ground truth`
- `cross-context validation proved`
- `matched endpoint`
- `external model-side generalization proved`
- `essential gene set as primary closure`

### 8.3 核心区分

**K562 essential day 7 + DepMap CRISPR** 是:
- essential-bias sensitivity / failure-decomposition panel
- day 7 duration
- essential-prefiltered library (~2057 genes)
- NOT a replacement for GWPS day 8

**不是**:
- primary external generalization anchor
- matched endpoint to GWPS
- essential gene list as ground truth
- replacement for GWPS day 8

## 9. 推荐 Paper Wording

### 9.1 引入语（Allowed）

"We further tested whether the framework remains robust under essential-bias library design using a CRISPRi screen targeting ~2057 common essential genes in K562 cells (Replogle et al. 2022, day 7)."

### 9.2 结果陈述（Allowed）

"The essential-prefiltered day 7 screen tested baseline/entrant trade-off sensitivity under essential-bias library composition, showing [result] compared to genome-wide GWPS day 8."

### 9.3 结果边界（Allowed）

"Notably, the essential day 7 design differs from GWPS day 8 in both library composition (essential-prefiltered vs genome-wide) and time horizon (day 7 vs day 8), and serves as a sensitivity panel rather than a formal generalization anchor."

### 9.4 禁止写法示例

- "We validated our findings using a K562 essential screen"
- "Essential day 7 confirms GWPS-level architecture"
- "Essential-bias library provides ground truth validation"

## 10. 与 GWPS day 8 的关系

| 维度 | GWPS day 8 | Essential day 7 |
|------|-----------|-----------------|
| 主要问题 | genome-wide short-horizon architecture form 是否成立 | essential-bias library 下 framework 还能工作到什么程度 |
| 定位 | primary external generalization anchor | sensitivity / failure-decomposition panel |
| library | genome-wide (~9866) | essential-prefiltered (~2057) |
| 时间点 | day 8 | day 7 |
| DepMap 可桥接目标 | ~9520 | ~2057（全部） |
| 主张层级 | primary anchor | secondary sensitivity panel |

两者回答不同问题，essential day 7 不能替代 GWPS day 8 作为 primary anchor。

## 11. 一句话收口

`Replogle 2022 K562 essential day 7` 可以作为 essential-bias sensitivity / failure-decomposition panel 进入框架，但必须先确认 paper identity、library composition 和完成数据下载；它只能写成 essential-bias library 下的 sensitivity / trade-off boundary，不能写成 primary closure、matched endpoint 或 GWPS replacement。
