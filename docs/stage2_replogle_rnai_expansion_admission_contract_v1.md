# Stage 2 Replogle/RNAi 扩展准入合同 v1

## 1. 文档定位

这份文档只冻结一件事：

**`Replogle 7d CRISPRi` 与 DepMap RNAi/shRNA dependency 的扩展层准入规则。**

它不是 HCC primary closure，也不是对 `GSE90063 K562 13d/7d temporal panel` 的替代。它的作用是在正式主文写作和作图前，给 short-horizon / modality-compatible external expansion 预先定义边界，避免后续扩数据时重开主线主张。

## 2. 当前主张层级

当前固定采用四层：

- `HCC primary mainline`
  `HCC38 / HCC1143` truth-first fitness-bridge architecture
- `GSE90063 K562 supplementary temporal panel`
  `13d` 是 primary formal supplementary bridge test；`7d` 是 temporal sensitivity / early-bridge probe
- `Replogle/RNAi external expansion candidate`
  `Replogle 7d CRISPRi` 接 DepMap RNAi/shRNA dependency，只能作为 short-horizon / modality-compatible external expansion
- `not admitted`
  无法确认 cell line、target overlap、perturbation modality 或 endpoint 身份的对象

`Replogle/RNAi` 扩展层不得改写已经冻结的 HCC primary mainline，也不得把 GSE90063 temporal panel 降级为未完成探索项。

## 3. Endpoint 术语冻结

DepMap 侧优先查找并使用：

- `DEMETER2 RNAi dependency`
- Project Achilles RNAi / shRNA dependency
- Project DRIVE RNAi / shRNA dependency

正式写法只能是：

- `RNAi/shRNA-derived dependency endpoint`
- `RNAi-family dependency compatibility layer`
- `modality-compatible external dependency readout`

禁止写法：

- `siRNA matched endpoint`
- `CRISPRi matched DepMap endpoint`
- `strictly matched knockdown endpoint`
- `external model-side generalization proved`

原因：DepMap 侧更明确存在的是 RNAi / shRNA dependency 资源；它与 CRISPRi 同属 knockdown-family compatibility，但不是严格 matched 的 Replogle CRISPRi endpoint。

## 4. 下载前准入检查

在下载或物化大数据前，必须先完成最小 metadata check：

1. `Replogle 7d CRISPRi` 的 cell line 身份明确，并能映射到 DepMap cell line id
2. DepMap RNAi/shRNA endpoint 中存在对应 cell line 或可辩护的近邻 mapping
3. Replogle perturbation target 与 RNAi/shRNA dependency gene symbol 可统一到同一 gene namespace
4. 目标基因与当前 HCC / GSE90063 主线的 overlap 可统计，不默认要求高 overlap
5. 能区分 `CRISPRi transcriptomic truth` 与 `RNAi/shRNA dependency endpoint` 的 modality difference
6. 能形成独立报告，不覆盖 HCC 或 GSE90063 已冻结产物

若第 1-3 条不满足，不下载大数据；先停在 `not admitted`。

## 4.1 当前本地预检查

当前仓库已经存在 Replogle 侧输入：

- `data/raw/stage1a/candidates/replogle_2022_k562_gwps.h5ad`
- shape = `1989578 x 8248`
- `obs.cell_line = K562`
- `obs.gene / obs.gene_id / obs.guide_id` 可用
- `obs.nperts` 显示 `1914250` 个 single-perturbation cells 与 `75328` 个 controls
- 既有准入说明显示：`9866` 个非 control target gene，support floor `>=5` 后保留 `9863` 个 eligible perturbations

需要保留的边界：

- 本地 `obs.perturbation_type` 标为 `CRISPR`，因此正式写作前仍需回到 Replogle 数据说明确认该对象在本项目里是否应写成 `CRISPRi`、`CRISPR` 或更保守的 `Replogle perturbation transcriptomic truth`
- 当前本地只发现 `depmap/CRISPRGeneDependency.csv`，尚未发现 `DEMETER2 / RNAi / shRNA` dependency matrix
- 因此下一步若推进 RNAi-family endpoint，需要用户提供或下载 DepMap DEMETER2 / RNAi dependency matrix 与对应 metadata

## 5. 最小数据请求

如果需要下载，优先只请求最小集合：

- Replogle 7d CRISPRi 的 perturbation transcriptomic object 或已物化 h5ad
- DepMap DEMETER2 / RNAi dependency matrix
- DepMap RNAi cell line metadata
- DepMap RNAi gene metadata

不在第一轮下载：

- 全量多组学协变量
- 与 cell line / gene mapping 无关的原始中间文件
- 新 entrant 的大型预测输出

下载动作由用户执行；本仓库先维护配置、准入合同和检查脚本入口。

## 6. Positive / partial / negative 判据

### 6.1 Positive

只有同时满足以下条件，才可写成 `supporting external expansion`：

- cell line 与 gene namespace 可明确映射
- formal bridgeable target 数达到预冻结最小阈值
- `CRISPRi transcriptomic truth` 与 `RNAi/shRNA dependency endpoint` 在 rank / direction 层呈现方向兼容
- 结果不依赖单个 target 才成立
- 写作中保留 modality-compatible，而不是 matched endpoint

允许写法：

`Replogle 7d CRISPRi` 可作为 truth-dependency bridge 的 short-horizon、RNAi/shRNA-compatible external expansion layer，但不建立 matched endpoint replication。

### 6.2 Partial

以下情况写成 `partial / boundary-supporting expansion`：

- cell line 与 endpoint 可映射，但 formal bridgeable target 数偏低
- rank / direction 层有趋势，但不稳定或对少数 target 敏感
- architecture form 可见，但 dependency bridge 弱
- modality difference 解释了部分不一致

### 6.3 Negative

以下情况写成 `not supported in tested setting`：

- cell line 或 gene namespace 无法可靠映射
- formal bridgeable target 数不足
- RNAi/shRNA dependency 与 CRISPRi transcriptomic truth 无方向兼容
- 结果完全由单个 target 驱动

Negative 结果不能事后降级成“只是 exploratory 所以不报告”；应按 tested setting 的边界写入 supplementary / limitation。

## 7. Entrant 接入边界

现有 entrant 可以接入 Replogle/RNAi 扩展层，但必须满足两个条件：

1. 先完成 truth-side Replogle/RNAi bridge admission
2. 只接入已经在 HCC 主线出现过的 entrant family

当前允许候选：

- `GEARS`
- `scGPT`
- `Geneformer`
- `lm_train_lowrank`
- `lm_G_scgpt_ridge`
- `lm_G_geneformer_ridge`

禁止：

- 在 Replogle/RNAi truth-side admission 之前扩新 entrant
- 把 Replogle/RNAi entrant 结果写成 HCC model recovery proved
- 用单一 global Pearson 替代 architecture-level adjudication

## 8. 与当前主线的关系

`Replogle/RNAi` 扩展层只回答：

**short-horizon CRISPRi transcriptomic truth 是否能与 RNAi/shRNA-family dependency readout 呈现 modality-compatible bridge。**

它不回答：

- HCC primary bridge 是否成立
- GSE90063 temporal panel 是否成立
- 模型是否已经完成 external generalization
- 具体 HCC content-level anchors 是否跨 context 复现

## 9. 渐进披露

默认先看：

1. `plan.md`
2. `docs/stage2_dixit_admission_contract_v1.md`
3. `reports/stage2_truth_driven_bridge/dixit_temporal_panel_gse90063/temporal_panel_report.md`
4. `reports/stage2_truth_driven_bridge/sensitivity/final_claim_matrix.tsv`

若进入 Replogle/RNAi 扩展，再新增：

1. 本文档
2. Replogle metadata check 报告
3. DepMap RNAi/shRNA endpoint metadata check 报告
4. Replogle/RNAi bridge summary

## 10. 一句话收口

`Replogle 7d CRISPRi + DepMap RNAi/shRNA dependency` 可以作为正式写论文和作图前的 external expansion layer，但必须先完成准入检查；它只能写成 short-horizon / modality-compatible support 或 boundary，不写成 siRNA matched endpoint、primary closure 或 external model-side generalization proved。
