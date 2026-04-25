# Figure 2 Redesign Freeze Spec v1

**状态**：2026-04-24 当前版本冻结  
**结论**：Figure 2 的叙事结构、颜色语义、panel 顺序与 claim-tier 可视化逻辑在本文档中冻结；后续仅允许按本规范落地，不再开放式试错。  
**Anchor commit**：`503fd0d536e5fb4c91e712deab4bd7d5df12914f`

---

## 0. 冻结对象

本文件冻结以下对象的**目标视觉状态**与**语义映射规则**：

- `manuscript/figures/Figure_2/Figure_2.png`
- `manuscript/figures/Figure_2/Figure_2.pdf`
- `src/wtbench/manuscript/figure2_anchor_tiering.py`
- `scripts/manuscript/build_figure2_anchor_tiering.py`

注意：

- 当前 `manuscript/figures/Figure_2/Figure_2.png` / `Figure_2.pdf` 即为本 freeze 对应的最终版本。
- 本 freeze 同时锁定 Figure 2 的最终配色、层级、版式与标号位置。
- Figure 2 自此进入与 Figure 1 对称的 submission QA-only 状态。

---

## 1. Locked Boundaries

### B1. Figure 2 总体叙事边界

Figure 2 只回答一个核心问题：

> Shared anchors recur and support the bridge, but they must be tiered by stability and covariate cleanliness rather than described as clean primary objects.

不允许在本图中扩展以下 headline：

- fully deconfounded causal proof
- all shared anchors are equivalent primary objects
- covariate exposure is visually downplayed or erased
- beyond-anchor mechanistic closure

### B2. Panel 数量冻结

Figure 2 固定为 `a–f` 六个 panel，不增减，不拆分为 `g/h`。

若后续需要展示 claim boundary、tier composition 或额外 adjudication，只能在现有 `f` 图叙事边界内完成，不新增 panel。

### B3. 当前版面骨架冻结

最终布局冻结为：

- 第一行：`a | b`
- 第二行：`c | d`
- 第三行：`e | f`

其中：

- `a` 宽于 `b`
- `c` 宽于 `d`
- `e` 为较宽矩阵 panel
- `f` 为右侧放大的表格型 adjudication panel

### B4. Figure 1 继承关系冻结

Figure 2 的颜色语言必须继承 `Figure 1` 已冻结的 Okabe-Ito 语义，不允许重新定义主色含义。

跨图继承原则：

- Figure 1 建立的“绿色 = primary / anchor / HCC1143 / clean-positive”在 Figure 2 中继续有效
- Figure 1 建立的“橙色 = HCC38 / contrast”在 Figure 2 中扩展为“contrast / exposed / warning”
- Figure 1 建立的“蓝色 = threshold / reference”在 Figure 2 中扩展为“shift / cutoff / reference”
- Figure 1 建立的“灰色 = non-anchor / neutral / background”在 Figure 2 中继续有效

---

## 2. 全局视觉规范（冻结）

### 2.1 语义分层冻结

Figure 2 必须把颜色语义分为四层，禁止混用：

#### 身份语义

- `#009E73`：primary / anchor / stable / HCC1143 / clean
- `#D55E00`：HCC38 / contrast

#### 状态语义

- `#009E73`：clean / supported
- `#D55E00`：exposed / sensitive / warning

#### 参考语义

- `#56B4E9`：shift / threshold / reference / cutoff

#### 背景语义

- `#8E8E8E`：supporting / non-anchor / neutral text emphasis
- `#BDBDBD`：mid-gray bars / separators / secondary outlines
- `#F5F5F5`：table header / soft background / de-emphasized fill
- `#E8F5E9`：very light green identity wash，仅用于 primary row 的弱强调
- `#FFF3E0`：very light orange exposure wash，仅用于 exposed warning 的弱强调
- `#000000`：正文与主轴

### 2.2 禁用颜色

以下颜色或语义组合在 Figure 2 freeze 后不得使用：

- 金色 / 土黄作为主 tier 语义
- 绿色同时表示“anchor 身份”和“高风险暴露”
- 橙色表示“主要支持证据”或“clean”
- 任何与 Figure 1 主色语言无对应关系的新强调色

### 2.3 字体与文字下限

- 字体：`Arial / Helvetica / sans-serif fallback`
- 正文可见文字：`>= 7.5 pt`
- 坐标轴标签：`8 pt`
- 图内数值：`7.5 pt`
- 仅脚注性说明允许 `7 pt`
- PDF 导出保留 editable text，不转曲

### 2.4 线宽下限

- 主轴：`0.8 pt`
- 普通边框 / 误差线 / 分隔线：`1.0 pt`
- TVD 高亮框：`2.0 pt`
- 全图任何线条不得 `< 0.5 pt`

### 2.5 网格与背景

- `a/c/d/e` 原则上删除浅灰背景网格
- 如保留参考线，只允许极弱单向参考线，不得形成视觉主层
- 表格或矩阵底色只承担结构分组功能，不承担主叙事

---

## 3. Panel Freeze

### Panel a — Shared-canonical anchor ranking

锁定点：

- panel 标题保持为 `Shared-canonical candidates occupy high joint ranks`
- `PFDN5` 行使用 `#009E73` 低透明度背景带，作为 primary anchor 身份提示
- shift 点使用 `#56B4E9`，空心或浅填充均可，但必须读作参考维度
- dependency 点使用 `#009E73`
- shift 与 dependency 之间的连接线为中性灰，不参与主语义竞争
- cutoff range 线统一为 `#BDBDBD`
- legend 固定在右下空白区，不得遮挡右侧点与标签

不得再改：

- 不得把 shift 与 dependency 都画成灰色系
- 不得把 cutoff range 重新做成视觉主层
- 不得让 `PFDN5` 的高亮强于数据点本身

### Panel b — Stable anchor recurrence matrix

锁定点：

- panel 标题保持为 `Stable anchors recur across both HCC contexts`
- 左列 `HCC1143` 使用 `#009E73`
- 右列 `HCC38` 使用 `#D55E00`
- 单元格数值文字为白色粗体，确保在深色填充上可读
- `PFDN5` 行标签使用 `#009E73` 加粗
- 底部说明文字降级为辅助层，使用深灰而非主色

不得再改：

- 不得再用绿色深浅区分两个 cell line
- 不得让读者重新学习 `HCC38 / HCC1143` 的颜色映射

### Panel c — Stability fraction across stable and sensitive anchors

锁定点：

- panel 标题保持为 `Stability fraction separates stable from sensitive anchors`
- stable anchors 条统一使用 `#009E73`
- cutoff-sensitive supporting 条统一使用 `#BDBDBD` 或 `#8E8E8E`
- 误差线 / whisker 使用深灰，带清晰端帽
- `PFDN5` 标签使用 `#009E73` 加粗
- legend 固定在右下角空白区

不得再改：

- 不得恢复土黄 / 金黄作为 sensitive supporting 的主色
- 不得让 supporting 对象与 stable anchor 共享同一主色层级

### Panel d — Final stable anchor shift/dependency

锁定点：

- panel 标题保持为 `Final stable anchors retain high shift and dependency ranks`
- shift 条统一使用 `#56B4E9`
- dependency 条统一使用 `#009E73`
- 数值标注为黑色粗体，位置统一
- `PFDN5` 标签使用 `#009E73` 加粗
- legend 保持在图内右上或顶部空白处，不遮挡数值

不得再改：

- 不得用双灰条去表达 shift / dependency 两个维度
- 不得让维度颜色与 Figure 1 的阈值/shift 语义断裂

### Panel e — Per-anchor covariate TVD matrix

锁定点：

- panel 标题保持为 `Per-anchor covariate TVD (threshold: TVD > 0.25)`
- `TVD > 0.25` 的高亮框使用 `#D55E00`，线宽 `2.0 pt`
- 可选使用 `#FFF3E0` 极浅橙填充，但填充强度不得压过数值阅读
- `PFDN5` 行标签使用 `#009E73` 加粗
- 其他行标签保持黑色
- `HCC38` 分组标题使用 `#D55E00` 加粗
- `HCC1143` 分组标题使用 `#009E73` 加粗
- HCC38 与 HCC1143 之间的垂直分隔线必须清晰可见
- x 轴标签可旋转或两行排布，但不得重叠

语义解释冻结为：

- 绿色表示 anchor 身份
- 橙色表示 covariate exposure / warning 状态

不得再改：

- 不得把 `TVD > 0.25` 高亮框画成绿色
- 不得让绿色在本 panel 中表示“混杂暴露”
- 不得使用金色边框作为主阈值高亮

### Panel f — Anchor claim matrix

锁定点：

- panel 标题保持为 `Anchor claim matrix`
- `PFDN5` 作为 `primary_but_qualified`，用 `#009E73` 表示
- `PMF1 / PRPF6 / ZNF131` 作为 `supporting_only`，以灰色系表示，不再用金黄作为主类别色
- `clean` 使用 `#009E73`
- `exposed` 使用 `#D55E00`
- 表头底色使用 `#F5F5F5`
- 表格边框与横向分隔线使用浅灰，不得喧宾夺主

允许的弱强调：

- `PFDN5` 行文字使用绿色加粗
- 或对 `PFDN5` 行使用极浅绿背景带

不得再改：

- 不得让 `supporting_only` 比 `primary_but_qualified` 更显眼
- 不得让 `clean / exposed` 颜色与 `e` 图的 TVD 暴露逻辑相冲突
- 不得出现行内容被裁切、遮挡或截断的排版 bug

---

## 4. 颜色继承表（冻结）

| 语义角色 | Figure 1 用法 | Figure 2 继承用法 | Hex |
| --- | --- | --- | --- |
| Primary anchor / Q1 / stable / HCC1143 / clean | Q1 anchors, frozen bridge | PFDN5, stable anchors, HCC1143, clean | `#009E73` |
| HCC38 / contrast / exposed / warning | HCC38 points | HCC38 column, exposed TVD boxes, warning state | `#D55E00` |
| Transcriptomic shift / threshold / reference | 0.25 / 0.75 threshold lines | shift dimension, cutoff range, claim boundary reference | `#56B4E9` |
| Supporting / non-anchor / neutral | other targets, null layers | supporting-only rows, neutral bars, separators | `#8E8E8E` / `#BDBDBD` |
| Soft backgrounds | null band / panel wash | table header, weak row wash, neutral base | `#F5F5F5` / `#E8F5E9` / `#FFF3E0` |
| Text / axes | global text | global text | `#000000` |

---

## 5. Submission QA Only（允许的后续改动）

freeze 后，仅允许以下类型修改：

- PDF 文件大小、裁切、边距、RGB、字体嵌入检查
- 导出设置导致的字体、线宽、透明度修复
- 期刊 production spec 要求的尺寸微调
- 明确的标签碰撞、裁切、越界、截断 bug 修复

不允许的后续改动：

- 再次开放式调整 Figure 2 主色语义
- 恢复 amber/gold 作为 supporting tier 主色
- 再次把 `TVD > 0.25` 改回绿色或金色强调
- 再次新增 panel 或重排 `a–f`
- 基于“也许更好看”的持续微调

---

## 6. Build / Refresh Path

重建命令冻结为：

```bash
PYTHONPATH="/home/data/gz0705/WTKO/src" python "scripts/manuscript/build_figure2_anchor_tiering.py"
```

重建输出目录：

- `reports/manuscript_figures_v2/fig2_anchor_tiering/`

投稿目录同步目标：

- `manuscript/figures/Figure_2/Figure_2.png`
- `manuscript/figures/Figure_2/Figure_2.pdf`

---

## 7. 跨图一致性验收标准

Figure 1 与 Figure 2 并置时，读者应零成本迁移以下颜色语义：

- 看到绿色：`primary / anchor / stable / clean / HCC1143`
- 看到橙色：`HCC38 / contrast / exposed / sensitive / warning`
- 看到蓝色：`shift / threshold / reference / cutoff`
- 看到灰色：`supporting / non-anchor / neutral / background`

一票否决条件：

- 绿色同时表示“被支持的身份”与“高风险暴露状态”
- 橙色同时表示“warning”与“clean”
- supporting tier 的颜色层级压过 primary tier
- panel `f` 仍存在裁切或表格信息不完整

---

## 8. Freeze Verdict

当前 Figure 2 的最终结论不是“每个 panel 自己独立好看”，而是：

1. Figure 2 必须从 Figure 1 继承同一套颜色语言。
2. Figure 2 必须把“身份语义”与“状态语义”明确分层。
3. Figure 2 必须把 `PFDN5` 与 supporting anchors 的 claim tier 差异稳定地可视化。
4. Figure 2 必须把 covariate exposure 作为橙色 warning 层，而不是绿色阳性层。

**结论**：Figure 2 按本规范冻结；后续仅执行落地重建与 submission QA，不再进行开放式重画。
