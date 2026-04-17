# Revision-round admission readiness v1

## 状态

完成日期：2026-04-17。

用途：B16 revision round 弹药预装。本文档只确认 admission / feasibility 状态，不运行正式 bridge，不进入第一版正文。

## 总结

| 候选 | 当前状态 | 可作为 revision 弹药吗 | 第一版是否纳入 |
|---|---|---:|---:|
| Frangieh 2021 melanoma + TIL co-culture | exploratory boundary only；无 DepMap endpoint | 有限可用，只能作为 non-DepMap boundary / exploratory architecture-form probe | 否 |
| Replogle 2022 K562 GWPS day 8 + DepMap CRISPR | metadata-confirmed admission freeze | 可用，若 reviewer 要求更大 external panel，这是最强候选 | 否 |
| Replogle 7d CRISPRi + DepMap RNAi/shRNA | 本地 Replogle 可用，但 RNAi/shRNA endpoint matrix 缺失 | 条件可用；需先补 DepMap RNAi/shRNA 数据 | 否 |
| Replogle K562 essential day 7 + DepMap CRISPR | local data available but pre-admission pending external metadata confirmation | 可作为 sensitivity / failure-decomposition panel 候选 | 否 |

## Frangieh 2021 melanoma

入口：`docs/stage2_frangieh_2021_melanoma_admission_contract_v1.md`

当前判断：

- 本地 legacy `dixit_2016_raw.h5ad` 已确认更接近 Frangieh 2021 melanoma + TIL co-culture Perturb-CITE-seq。
- 该对象不匹配 GSE90063 K562 TF-pool，不再作为 Dixit evidence。
- Frangieh melanoma cell lines 当前无可用 DepMap CRISPR endpoint mapping。

允许作为 revision 弹药：

- exploratory / boundary test
- non-DepMap-matched architecture-form probe
- framework limitation in tumor-immune complex context

禁止作为 revision 弹药：

- formal bridge validation
- matched endpoint replication
- external generalization anchor
- HCC content-level replication

结论：Frangieh 可以保留为 reviewer 要求“解释 legacy object / non-DepMap boundary”时的备份材料，但不适合作为第一优先 external validation response。

## Replogle 2022 K562 GWPS day 8

入口：`docs/stage2_replogle_gwps_day8_admission_contract_v1.md`

当前判断：

- 本地数据存在：`data/raw/stage1a/candidates/replogle_2022_k562_gwps.h5ad`
- cell line：K562
- perturbation：CRISPRi 已外部确认
- duration：day 8 已外部确认
- library：genome-wide / all expressed genes，约 9866 targets
- DepMap K562 model ID：ACH-000551
- 可映射 DepMap CRISPR targets：约 9520
- 状态：metadata-confirmed admission freeze

允许作为 revision 弹药：

- 若 reviewer 要求 larger external target panel，可优先考虑。
- 只能写成 K562 genome-wide CRISPRi day 8 short-horizon external panel。
- 可测试 architecture form / bridge form，但不能写成 HCC content-level replication。

禁止作为 revision 弹药：

- matched endpoint claim
- HCC content-level anchors replicated
- external model-side generalization proved
- K562 GWPS as primary closure

结论：Replogle GWPS day 8 是当前最强的 revision-round external panel 候选，但第一版不运行，以免扩大主线范围。

## Replogle 7d CRISPRi + DepMap RNAi/shRNA

入口：`docs/stage2_replogle_rnai_expansion_admission_contract_v1.md`

当前判断：

- 本地 Replogle K562 GWPS object 可用。
- 但当前只确认本地存在 `depmap/CRISPRGeneDependency.csv`，尚未确认 DEMETER2 / RNAi / shRNA matrix。
- RNAi/shRNA endpoint 必须由用户提供或下载后，才能进入正式 admission。

允许作为 revision 弹药：

- reviewer 要求 cross-platform endpoint sensitivity 时可考虑。
- 只能写成 RNAi/shRNA-family dependency compatibility layer。

禁止作为 revision 弹药：

- siRNA matched endpoint
- CRISPRi matched endpoint
- primary endpoint replacement
- external model-side generalization proved

结论：条件可用，但缺 endpoint 文件；不是第一优先 revision 弹药。

## Replogle K562 essential day 7

入口：`docs/stage2_replogle_k562_essential_day7_admission_contract_v1.md`

当前判断：

- 本地数据存在：`data/raw/stage1a/replogle_2022_k562_essential.h5ad`
- cell line：K562
- target set：约 2058 essential-prefiltered targets
- 当前状态：pre-admission，仍需外部确认 paper identity、accession、library composition、DepMap model ID。

允许作为 revision 弹药：

- essential-bias sensitivity / failure-decomposition panel
- baseline/entrant trade-off sensitivity under essential-prefiltered library

禁止作为 revision 弹药：

- replacement for GWPS day 8
- primary external generalization anchor
- essential gene list as ground truth
- matched endpoint

结论：可作为 sensitivity panel 候选，但需先完成 metadata confirmation。

## 推荐 revision 响应顺序

若 reviewer 要求新增外部证据：

1. 优先评估 Replogle 2022 K562 GWPS day 8 + DepMap CRISPR。
2. 若 reviewer 明确要求 endpoint-platform sensitivity，再评估 Replogle 7d / RNAi-shRNA compatibility。
3. 若 reviewer 要求 library-bias sensitivity，再评估 K562 essential day 7。
4. Frangieh 只用于 legacy clarification 或 non-DepMap boundary illustration，不作为 formal validation。

## 第一版边界

第一版投稿不新增上述正式分析。所有候选只作为 revision-ready backlog，不改写 HCC primary、GSE90063 supplementary temporal panel、endpoint hierarchy 或 current entrant set。
