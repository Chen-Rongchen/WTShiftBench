# Nature Methods 2025 figure style note v1

## 状态

更新日期：2026-04-18。

参考对象：

- `s41592-025-02772-6.pdf`
- `https://github.com/const-ae/linear_perturbation_prediction-Paper`

本文档只记录可迁移的图版风格规则，不复制参考论文的图像、数据或版式内容。

## 可迁移规则

### 页面与组合图

- 白色背景。
- 多 panel figure 使用紧凑网格，panel 间距小于当前初稿的大空白布局。
- 不在图内部堆叠过多解释性文字；解释放到 legend 或正文。
- panel label 使用小写 `a`、`b`、`c`，黑色加粗，字号略大于轴文字但不抢主图。

### 坐标轴

- 去掉 top / right spines。
- left / bottom spines 保留细线。
- ticks 短、细、低对比度。
- grid 只作辅助，使用很浅的灰色；不要让 grid 成为视觉主元素。

### 颜色

- 主体使用灰度和低饱和颜色。
- baseline 使用近黑色。
- 模型或条件用少数稳定强调色区分：
  - GEARS：低饱和蓝。
  - sweep：浅蓝。
  - foundation / embedding：低饱和绿。
  - linear / null：灰色。
  - boundary / warning：低饱和红。
- 散点优先用浅灰或中灰；只有关键对象使用强调色。

### 文字

- panel title 左对齐，短句，不写成完整结论句。
- 轴标签保留必要信息，避免长句。
- legend 无边框。
- 字号层级：
  - axis tick：约 6 pt。
  - axis label：约 7 pt。
  - panel title：约 7.5-8 pt。
  - panel label：约 8.5-9 pt。

## 已落地位置

统一样式层：

- `src/wtbench/manuscript/manuscript_style.py`

已调整：

- `COLORS`
- `apply_manuscript_style()`
- `clean_axes()`
- `add_panel_label()`

## 边界

- 本次只迁移通用视觉 grammar。
- 不改变任何 source data、score、claim boundary 或 figure panel 语义。
- 不复制参考论文的原图或数据。
