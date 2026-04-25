# Extended Data Figure Redesign Plan v1

## 文档定位

本文档记录主图 Figure 1-5 全部定版后，Extended Data Figure 1-11 的收束计划。原主文 Figure 5 已下放为 Extended Data Fig. 11；原 Figure 6 已前移为主文 Figure 5。

原则：Extended Data 不是"低优先级主图"，而是"主图支持的完整细节层"。收束目标是消除冗余、合并重复信息、整合从主图下放的内容，而不是再压缩一次叙事。

## 主图下放内容汇总

| 下放来源 | 下放内容 | 接收 Extended Data |
|---|---|---|
| Fig. 4 旧 d-h | sweep bars / shift-excess / linear-control detail / coverage audit | ED Fig. 5（已冻结为 6 panel，见 `figure4_redesign_freeze.md` §Gate 1）|
| 原 Fig. 5 旧 b/c/d/f/g | composition bar / bootstrap ranking / annotation scatter / family counts / shift-minus-dependency ranking | ED Fig. 6 |
| 原 Fig. 5 当前 2-panel axis adjudication | axis explanatory scatter / axis adjudication profile | ED Fig. 11 |
| 当前 Fig. 5（原 Fig. 6）旧 a/b/c | covariate audit overview / covariate-aware tiering / barcode-gem-group boundary | ED Fig. 9 |
| 当前 Fig. 5（原 Fig. 6）旧 d/e/f | K562 temporal overview / stratification / A0/A1/B tiering | ED Fig. 7 |
| 当前 Fig. 5（原 Fig. 6）旧 g | endpoint hierarchy full detail / CRISPR vs RNAi comparison | ED Fig. 8 |

---

## Extended Data Figure 收束计划

### ED Fig. 1. Dataset and endpoint admission

**当前**：8 panel（a-h）

**问题**：大量 panel 是低信息量的 summary table/bar（d, g），或与其他 ED 重复（e 与 ED8e 重叠）。

**建议收束**：

| New panel | 内容 | 来源 |
|---|---|---|
| ED1 a | HCC38/HCC1143 primary bridge admission（scatter + rho） | 旧 a |
| ED1 b | K562 cell counts + cell accounting（合并旧 b+f） | 旧 b + f |
| ED1 c | DEMETER2 RNAi conversion summary | 旧 c |
| ED1 d | Endpoint hierarchy：primary / sensitivity / supplementary（合并旧 d+e） | 旧 d + e |
| ED1 e | Boundary card：K562 和 discovery 不是 primary co-pillars | 旧 h |

**删除**：旧 g（Primary endpoint summary，与 a+d 重复）。

**目标 panel 数**：5

---

### ED Fig. 2. Full target-level joint grid

**当前**：8 panel（a-h）

**问题**：e/f 是零计数类别（Q2/Q3 transcriptomic-excess / dependency-excess），已在 Fig 1e 中显式标注为零；h 是 grid summary table，与 c+d 重复。

**建议收束**：

| New panel | 内容 | 来源 |
|---|---|---|
| ED2 a | HCC38 full target-level shift-dependency grid | 旧 a |
| ED2 b | HCC1143 full target-level shift-dependency grid | 旧 b |
| ED2 c | Grid composition：category counts + Q1 anchor list + zero-count 显式标注（合并旧 c+d+e+f） | 旧 c + d + e + f |
| ED2 d | Target-level evidence-tier composition | 旧 g |

**删除**：旧 h（summary table，与 c 重复）。

**目标 panel 数**：4

---

### ED Fig. 3. Anchor sensitivity and claim tiering

**当前**：8 panel（a-h）

**问题**：c（cutoff-sensitive objects）已在 Fig 2c 中以 bar 形式呈现；f（evidence-tier composition）与 Fig 2f 的 claim matrix 重复；e+g+h 都是 claim-tier wording 的不同切面。

**建议收束**：

| New panel | 内容 | 来源 |
|---|---|---|
| ED3 a | Full target-level anchor distribution | 旧 a |
| ED3 b | Shared recurrent anchors | 旧 b |
| ED3 c | Control subsampling intervals for primary bridge metric | 旧 d |
| ED3 d | Covariate-aware anchor wording + downgrade rationale + allowed/disallowed claims（合并旧 e+g+h） | 旧 e + g + h |

**删除**：旧 c（Fig 2c 已覆盖），旧 f（Fig 2f 已覆盖）。

**目标 panel 数**：4

---

### ED Fig. 4. Full HCC38/HCC1143 model recovery detail

**当前**：8 panel（a-h）

**问题**：大量 per-cell-line 和 top-20 overlap detail 可以合并。

**建议收束**：

| New panel | 内容 | 来源 |
|---|---|---|
| ED4 a | Full backbone recovery ranking across all entrants | 旧 a |
| ED4 b | Per-cell-line multi-metric comparison（backbone / shift-excess / separation，合并旧 b+c+d） | 旧 b + c + d |
| ED4 c | Top-20 overlap comparison across baseline / GEARS / foundation / null（合并旧 e+f+g+h） | 旧 e + f + g + h |

**目标 panel 数**：3

---

### ED Fig. 5. GEARS finite-budget sweep and prespecified stop rule

**当前**：8 panel（a-h）

**状态**：已在 `figure4_redesign_freeze.md` §Gate 1 中冻结为 6 panel，本计划直接采纳该冻结方案：

| New panel | 内容 | 来源 |
|---|---|---|
| ED5 a | GEARS finite-sweep backbone bar（baseline + formal + Sweep A-E） | 合并旧 c + e |
| ED5 b | Shift-excess across sweep（同 6 个对象） | 旧 Fig 4 c |
| ED5 c | Recipe grid summary：3×3×2 neighborhood 的 6 点 coverage matrix | 合并旧 a + g |
| ED5 d | Linear-control design schematic（reader-facing 名字） | 旧 Fig 4 e |
| ED5 e | Linear-control target coverage audit（47/47 matrix，两 context） | 旧 Fig 4 g |
| ED5 f | Reproducibility boundary card：batch status + stop-rule + figure boundary | 合并旧 b + f + h |

**目标 panel 数**：6（已冻结，不动）

---

### ED Fig. 6. Full axis annotation and bootstrap support

**当前**：8 panel（a-h）

**新增任务**：保留原 Fig. 5 下放的 full axis annotation / bootstrap support 内容（旧 b/c/d/f/g：composition bar / bootstrap ranking / annotation scatter / family counts / shift-minus-dependency ranking）。当前精简 2-panel axis adjudication 另存为 ED Fig. 11，不覆盖 ED6。

**建议收束**：

| New panel | 内容 | 来源 |
|---|---|---|
| ED6 a | Full axis explanatory balance（含 shift-minus-dependency ranking） | 旧 a + g |
| ED6 b | Representative bootstrap axis-call stability（完整 ranking） | 旧 b + c |
| ED6 c | Annotation support detail：enrichment hits + database coverage + top terms（合并旧 d+e+g） | 旧 d + e + g |
| ED6 d | Qualified and preliminary axis-call composition bar（从 Fig 5 下放） | 旧 Fig 5 b |
| ED6 e | Axis claim boundary card（完整版，含 Fig 5 未展示的限制证据） | 旧 h |

**删除**：旧 f（composition bar 单独保留为 d，但位置调整）。

**目标 panel 数**：5

---

### ED Fig. 7. K562 temporal evidence detail

**当前**：8 panel（a-h）

**新增任务**：接收 Fig 6 下放内容（旧 d/e/f：temporal overview / stratification / A0/A1/B tiering）。

**建议收束**：

| New panel | 内容 | 来源 |
|---|---|---|
| ED7 a | K562 7d supplementary bridge summary | 旧 a |
| ED7 b | K562 13d supplementary bridge summary | 旧 b |
| ED7 c | Temporal stratification：rank bridge + mean shift（7d vs 13d 同图） | 旧 c + Fig 6 旧 e |
| ED7 d | Evidence-tier comparison（7d vs 13d A0/A1/B，合并旧 e+f+h） | 旧 e + f + h |
| ED7 e | Supplementary temporal panel call | 旧 g |

**删除**：旧 d（temporal structure calls，细节层，可由 c 覆盖）。

**目标 panel 数**：5

---

### ED Fig. 8. CRISPR versus RNAi endpoint detail

**当前**：8 panel（a-h）

**新增任务**：接收 Fig 6 下放内容（旧 g：endpoint hierarchy full detail）。

**建议收束**：

| New panel | 内容 | 来源 |
|---|---|---|
| ED8 a | HCC38/HCC1143 CRISPR and RNAi truth-endpoint bridge summaries | 旧 a |
| ED8 b | K562 CRISPR and RNAi truth-endpoint bridge summaries | 旧 b |
| ED8 c | CRISPR-RNAi endpoint agreement | 旧 c |
| ED8 d | RNAi cross-platform sensitivity boundary | 旧 f |
| ED8 e | CRISPR-RNAi bridge gap across contexts | 旧 g |
| ED8 f | Endpoint claim boundary + DEMETER2 conversion（合并旧 d+h） | 旧 d + h |

**删除**：旧 e（endpoint hierarchy，已在 Fig 6c 中展示）。

**目标 panel 数**：6

---

### ED Fig. 9. Covariate audit details and wording boundary

**当前**：8 panel（a-h），但注意：per-anchor covariate TVD matrix 已提升至 Fig 2e。

**新增任务**：接收 Fig 6 下放内容（旧 a/b/c：covariate audit overview / covariate-aware tiering / barcode-gem-group boundary）。

**建议收束**：

| New panel | 内容 | 来源 |
|---|---|---|
| ED9 a | Covariate audit axes overview（含 barcode-gem-group design-proxy） | 旧 a + c + Fig 6 旧 c |
| ED9 b | Covariate balance by cell line（含 TVD summary，不含 per-anchor matrix） | 旧 b + Fig 6 旧 a |
| ED9 c | High-imbalance target counts + covariate impact on anchor wording（合并旧 d+e） | 旧 d + e |
| ED9 d | Allowed and disallowed wording boundary（合并旧 g+h） | 旧 g + h |
| ED9 e | Covariate-aware anchor tiering（从 Fig 6 下放） | Fig 6 旧 b |

**删除**：旧 f（covariate status in claim matrix，与 Fig 2f 重复）。

**目标 panel 数**：5

---

### ED Fig. 10. Reproducibility and claim governance

**当前**：8 panel（a-h）

**问题**：b+c 都是文件/包级别 overview，可以合并；f+h 都是 reproducibility boundary。

**建议收束**：

| New panel | 内容 | 来源 |
|---|---|---|
| ED10 a | Main figure manifest overview | 旧 a |
| ED10 b | Submission package overview：tables + hash coverage（合并旧 b+c） | 旧 b + c |
| ED10 c | Final claim-matrix evidence-tier overview | 旧 d |
| ED10 d | Key allowed wording tiers | 旧 e |
| ED10 e | Explicitly enumerated disallowed wording | 旧 g |
| ED10 f | Reproducibility boundary：rebuild entrypoints + figure-stage rerun boundary（合并旧 f+h） | 旧 f + h |

**目标 panel 数**：6

---

### ED Fig. 11. Axis-level adjudication profile

**当前**：2 panel（a-b），由原主文 Fig. 5 下放。

**功能**：支撑 transcription/chromatin 只能作为 qualified interpretive axis，不在主文中形成强生物学机制主张。

**目标 panel 数**：2（保持当前紧凑版本）

---

## 收束前后对比

| ED Figure | 当前 panel 数 | 目标 panel 数 | 变化 |
|---|---|---|---|
| ED1 | 8 | 5 | -3 |
| ED2 | 8 | 4 | -4 |
| ED3 | 8 | 4 | -4 |
| ED4 | 8 | 3 | -5 |
| ED5 | 8 | 6 | -2（已冻结） |
| ED6 | 8 | 5 | -3 |
| ED7 | 8 | 5 | -3 |
| ED8 | 8 | 6 | -2 |
| ED9 | 8 | 5 | -3 |
| ED10 | 8 | 6 | -2 |
| ED11 | 2 | 2 | 新增下放图 |
| **总计** | **82** | **51** | **-31** |

---

## 执行顺序建议

由于 Extended Data 的 redraw 不涉及 claim boundary 变更，只涉及 panel 合并和重组，执行顺序可以按依赖关系安排：

1. **ED Fig. 5**：已冻结，最先执行（因其被 Fig 4 cross-reference）
2. **ED Fig. 6**：保留 full axis annotation / bootstrap support，其次执行
3. **ED Fig. 11**：承接原 Fig. 5 当前 2-panel axis adjudication
4. **ED Fig. 9**：接收当前 Fig. 5（原 Fig. 6）下放内容，与 ED7/8 可并行
5. **ED Fig. 7**：接收当前 Fig. 5（原 Fig. 6）下放内容
6. **ED Fig. 8**：接收当前 Fig. 5（原 Fig. 6）下放内容
7. **ED Fig. 1-4, 10**：独立，可任意顺序

## 配色策略

Extended Data 沿用主图已冻结的 `src/wtbench/manuscript/_palette.py` sage-olive-sand 色系，不新建颜色系统。主图配色冻结在主图全部 redraw 完成后统一 pass 一次（当前阶段主图已全部完成，可直接沿用）。

## 不变原则

- 不新增分析
- 不改变 source data
- 不改变 claim boundary
- 所有保留 panel 仍保留 manifest JSON + source data TSV
- 所有合并 panel 的 source data 需包含合并前各子 panel 的数据来源
