# Figure 1 Redesign Freeze Spec v1

**状态**：2026-04-24 冻结  
**结论**：用户确认当前 `Figure_1` 版本可先冻结，后续仅允许 submission QA 级修正，不再做开放式视觉重构。  
**Anchor commit**：`392579c9bfdf0f06bf3c7dc4026fd1c7965b4cee`

---

## 0. 冻结对象

本文件冻结以下产物的当前视觉与布局状态：

- `manuscript/figures/Figure_1/Figure_1.png`
- `manuscript/figures/Figure_1/Figure_1.pdf`
- `src/wtbench/manuscript/figure1_truth_object_v2.py`
- `scripts/manuscript/build_figure1_truth_object.py`

本 freeze 的含义是：  
Figure 1 的 panel 结构、色彩语义、主要标注逻辑、legend 位置与 panel 相对布局已经锁定；除非是投稿合规检查触发的必要修复，否则不再继续做主观审美迭代。

---

## 1. Locked Boundaries

### B1. Figure 1 总体叙事边界

Figure 1 只回答一个核心问题：

> A truth-anchored benchmark defines a pre-specified perturbation-fitness recovery object, and the observed bridge is visualized as a structured target-level object in HCC38 and HCC1143.

不允许在本图中扩展额外 headline，例如：

- fully deconfounded causal proof
- target-level mechanistic closure
- beyond-object biological claims

### B2. Panel 数量冻结

Figure 1 固定为 `a–f` 六个 panel，不增减，不重排叙事顺序。

### B3. 当前版面骨架冻结

最终布局冻结为：

- 第一行：`a | b`
- 第二行：`c | d`
- 第三行：`e | f`

其中：

- `e` 与 `f` 保持同一行
- `f` 为接近正方形 panel
- `f` legend 固定在图外右侧

### B4. 字母标号相对关系冻结

当前字母标号关系冻结为：

- `a / c / e` 作为同组左边界对齐基准
- `b / f` 明确比该基准更向左
- `d` 相对 `c` 略向右收

后续如无强理由，不再继续微调 panel 字母位置。

---

## 2. 全局视觉规范（冻结）

### 2.1 色彩语义映射

全图固定使用 Okabe-Ito 语义映射：

- `#009E73`：Q1 anchors / HCC1143 / frozen bridge / 核心阳性
- `#D55E00`：HCC38
- `#56B4E9`：25/75 阈值线与参考系
- `#8E8E8E`：非 Q1 / 中性点 / 次要信息
- `#F5F5F5`：流程框 / 表头 / Q4 / 退底浅背景
- `#E8E8E8`：null band
- `#BDBDBD`：分隔 / 中灰条带 / 边框层
- `#000000`：文字与主轴语义

### 2.2 字体与文字下限

- 字体：`Arial / Helvetica / sans-serif fallback`
- 正文可见文字：`>= 7.5 pt`
- 仅脚注性说明允许 `7 pt`
- PDF 导出保留 editable text，不转曲

### 2.3 线宽下限

- 全图任何线条不得 `< 0.5 pt`
- 主轴、误差条、关键引线优先使用 `0.75–1.0 pt`

---

## 3. Panel Freeze

### Panel a — Truth-first recovery object

锁定点：

- 5 个流程框使用浅灰背景
- `frozen bridge object` 为唯一绿色焦点
- 箭头深灰，`unpacked` 为绿色斜体
- 下方表格保留三列结构，不再重排

不得再改：

- 不再增加额外步骤框
- 不再改变 `a` 图内部表格内容层级

### Panel b — Pre-specified 25/75 rule

锁定点：

- 无背景网格，仅保留 `0.25 / 0.75` 蓝色虚线
- `Q1–Q4` 与说明文字位于各自象限中心
- `Q1` 保留绿色小方块色标
- `CRISPR dependency quantile` 为纵坐标标签
- `shift quantile` 为底部横坐标标签

不得再改：

- 不再恢复 Q1 底色
- 不再把四象限说明挪出对应象限中心

### Panel c / d — Target-level joint grid

锁定点：

- 非 Q1：灰色空心圆
- Q1：绿色实心圆
- 仅保留蓝色阈值虚线，无背景网格
- legend 放左上统计块区域
- 基因引线为降级暖橙注释层
- 基因名保持在各自 panel 边界内

补充冻结：

- `c` 与 `d` 之间当前间距冻结
- `d` 字母标号相对 `c` 略向右

### Panel e — Grid composition across primary contexts

锁定点：

- 与 `f` 同排
- 条带整体相对上一版压缩约 `10%`
- 条带整体更靠近左侧 `HCC38 / HCC1143` 标签
- 图内删除 “Pre-specified but empty: Q2...” 重复说明
- 条带文字全部黑色

不得再改：

- 不再恢复底部重复说明
- 不再把 `e` 单独拆到下一行

### Panel f — Bridge strength

锁定点：

- panel 接近正方形
- `HCC38` 为橙色点与误差条
- `HCC1143` 为绿色点与误差条
- null 作为浅灰背景带
- legend 固定在图外右侧
- legend 中仅写 `Null envelope`，不再重复写 `rho=0`

不得再改：

- 不再把 legend 放回绘图区
- 不再让 legend 遮挡 `HCC1143`

---

## 4. Submission QA Only（允许的后续改动）

freeze 后仅允许以下类型修改：

- PDF 文件大小、裁剪、边距、RGB、字体嵌入检查
- 导出设置导致的字体或线宽修复
- 期刊 production spec 要求的尺寸微调
- 明确的排版 bug 修复

不允许的后续改动：

- 再次开放式调整 panel 布局
- 再次修改主色语义
- 再次移动 legend 或整体重排
- 基于“也许更好看”的持续微调

---

## 5. Build / Refresh Path

重建命令冻结为：

```bash
PYTHONPATH="/home/data/gz0705/WTKO/src" python "scripts/manuscript/build_figure1_truth_object.py"
```

重建输出目录：

- `reports/manuscript_figures_v2/fig1_truth_object/`

投稿目录同步目标：

- `manuscript/figures/Figure_1/Figure_1.png`
- `manuscript/figures/Figure_1/Figure_1.pdf`

---

## 6. Freeze Verdict

当前 Figure 1 版本通过以下冻结标准：

- panel 结构稳定
- 色彩语义稳定
- 关键可读性问题已解决
- `f` 图数据点与 legend 冲突已解决
- `c` 图基因名越界问题已解决
- `e` 图重复说明已删除

**结论**：Figure 1 当前版本可进入 freeze 状态。后续仅做 submission QA，不再做开放式重画。
