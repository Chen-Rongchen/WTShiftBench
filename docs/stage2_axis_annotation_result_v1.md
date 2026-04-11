# Stage 2 功能轴注释结果 v1

## 1. 文档定位

这份文档不是再定义功能轴，也不是重新发现 axis。

它只做一件事：

**把当前已经完成的 frozen structure、axis enrichment 与 per-target consistency 结果，压成可直接写入主文档的结果段落。**

当前结果口径保持保守：

- 不反向改写 frozen `axis membership`
- 不自动把 `partially_supported_axis` 升级成更强结论
- 只报告当前相对更稳与当前仍混杂的 axis

## 2. 当前总体结论

当前 Stage 2 frozen axis 已经完成第一轮 `annotation + validation` 闭环。

就证据形态而言：

- 结构证据来自已经冻结的 truth-driven bridge / master atlas
- 注释证据来自 axis-level enrichment
- 一致性证据来自 per-target pathway consistency audit

当前最合适的总体表述是：

**多数 frozen axis 已经获得部分支持，但支持强度不均匀；现阶段更适合把它们写成 `partially supported axes`，而不是 fully established functional axes。**

更准确地说，当前 axis 框架的价值不在于证明一个已经完全闭合的模块架构，而在于完成了第一轮 `annotation`、`validation` 与 `evidence tiering`：哪些 axis 可以进入 formal 或 primary 层级，哪些仅能作为 supporting evidence，哪些仍应停留在 preliminary status，现已具备清晰边界。

## 3. 当前相对更稳的 axis

### 3.1 RNA processing / spliceosome

- frozen 结构支持较强
- axis-level enrichment 指向 `Reactome::Metabolism Of RNA`
- 当前命名与 frozen axis 一致

当前可写法：

`RNA processing / spliceosome` 是当前证据较稳的一条 axis，但 enrichment 命中数量仍有限，因此更适合写成“方向正确的部分支持”，而不是“证据已完全封顶”。

### 3.2 transcription / chromatin

- frozen 结构支持较强
- enrichment 命中 `Chromatin Modifying Enzymes`、`HATs Acetylate Histones`
- 与 axis 成员的既有 biology 基本一致

当前可写法：

`transcription / chromatin` 是 `gene expression machinery` 内当前较稳的一条轴，已经获得了和染色质调控一致的 annotation 支持。

### 3.3 chromatin remodeling

- frozen 结构支持较强
- enrichment 指向 `Chromatin Organization / Chromatin Remodeling`
- consistency 已出现弱复现，但 recurrent term 还不够机制特异

当前可写法：

`chromatin remodeling` 已获得结构与注释的双重支持，但 consistency 仍偏弱，因此目前更适合保留为部分支持的机制轴。

### 3.4 TGF-beta / BMP signaling

- enrichment 命中 `Signaling By TGFB Family Members`
- consistency 也复现了 `Cellular Response to Transforming Growth Factor Beta Stimulus`

当前可写法：

`TGF-beta / BMP signaling` 是当前 signaling 相关 axis 里相对更整齐的一条，annotation 与 consistency 方向基本一致。

### 3.5 ribosome biogenesis / nucleolar 与 ribosomal / translation

- 两条轴都获得了较高的 enrichment 命中数
- 当前命名与 frozen 结构基本一致

当前可写法：

这两条轴在 annotation 层已经有较稳定支持，但仍需保留一个边界：它们可能部分混入更广义的 growth / proteostasis / essentiality 程序，因此当前不宜过度机制化。

### 3.6 ER stress / UPR

- enrichment 命中 `MSigDB Hallmark::Unfolded Protein Response`
- 当前命名与 frozen axis 一致

当前可写法：

`ER stress / UPR` 已获得较清楚的注释支持，但仍应与 generic stress / collapse-like response 保持区分。

## 4. 当前仍偏混杂的 axis

### 4.1 transcription regulation

- frozen 结构存在
- 但当前 enrichment 没有形成稳定、收敛的机制主题
- consistency recurrence 虽高，但高频 term 偏泛化：
  - receptor tyrosine kinase signaling
  - neutrophil degranulation
  - proliferation / apoptosis / migration 相关主题

当前可写法：

`transcription regulation` 更像一条真实存在但机制仍偏混杂的轴；现阶段不宜给出更强、更细的功能命名。

### 4.2 cell cycle / replication

- annotation hit 数不少
- 但 consistency 尚未形成足够集中的 recurrent program

当前可写法：

`cell cycle / replication` 可以保留 frozen 名称，但当前还不足以把它写成更细的、稳定的 cell-cycle 子程序轴。

### 4.3 JAK-STAT signaling

- annotation 有信号
- consistency 尚未给出足够集中的 pathway core

当前可写法：

`JAK-STAT signaling` 目前更适合作为部分支持的 signaling axis，而不是已经完全坐实的功能轴。

## 5. 当前应保持保守的 axis

以下轴目前不应被写成更强机制结论：

- `NF-kB / copper signaling`
- `proteostasis / chaperone`
- `metabolism / transcription`
- `synaptic / signaling`

原因不是“完全没有信号”，而是当前 annotation 与 consistency 还不足以支撑更强的命名与断言。

## 6. 当前推荐写法

在主文档里，当前最稳的写法是：

1. 先说明 frozen axis 已完成第一轮 `annotation + per-target consistency` 闭环。
2. 再说明若干 axis 获得了较稳的部分支持：
   - `RNA processing / spliceosome`
   - `transcription / chromatin`
   - `chromatin remodeling`
   - `TGF-beta / BMP signaling`
   - `ribosome biogenesis / nucleolar`
   - `ribosomal / translation`
   - `ER stress / UPR`
3. 最后明确说明整体仍应保持 `partially supported axis` 口径。

同时建议补一句主张边界：

当前结果支持的是“少数 axis 获得方向一致且层级清晰的支持”，而不是“多数 axis 已完成同等级、同稳健性的正式闭环”。

## 7. 一句话收口

当前 Stage 2 的 frozen axis 已经从结构发现推进到了第一轮注释与验证；其中若干 axis 获得了较稳的部分支持，但整体上仍应保持保守表述，不宜提前升级为 fully established functional axes。
