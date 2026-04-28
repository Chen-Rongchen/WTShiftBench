# Figure 3 Redesign Freeze Spec v1

**状态**：2026-04-24 冻结  
**结论**：Figure 3 的内容逻辑已收束为 `a → b → c`（**不再包含**原 main-figure 的 per-context panel；相应读数不再作为当前 Extended Data 固定承接层单独保留）；本 freeze 将语义修正、视觉收敛和版面压缩触发条件正式锁定，后续仅允许按本文档执行，不再做开放式视觉漂移。  
**Anchor commit**：`392579c9bfdf0f06bf3c7dc4026fd1c7965b4cee`

---

## 0. 冻结对象

本文件冻结以下产物的 redesign 原则与提交前检查标准：

- `manuscript/figures/Figure_3/Figure_3.png`
- `manuscript/figures/Figure_3/Figure_3.pdf`
- `manuscript/figures/Figure_3/Figure_3_panel_manifest.json`
- `manuscript/figures/Figure_3/panels/Figure_3_panel_a_manifest.json`
- `manuscript/figures/Figure_3/panels/Figure_3_panel_b_manifest.json`
- `manuscript/figures/Figure_3/panels/Figure_3_panel_c_manifest.json`
- `src/wtbench/manuscript/figure3_model_tradeoff.py`
- `scripts/manuscript/build_figure3_model_tradeoff.py`

本 freeze 的含义是：

Figure 3 不再被视为“单图润色对象”，而被视为 `Figure 1–3` 之间颜色语义、叙事层级和 claim boundary 的对齐节点。后续修改必须服务于三个固定目标：

- 修正内容与视觉不匹配
- 建立与 `Figure 1/2` 的低成本语义迁移
- 在不损害可读性的前提下控制投稿版面高度

---

## 1. Locked Boundaries

### B1. Figure 3 核心叙事边界

Figure 3 只回答一个核心问题：

> Model recovery is metric-dependent, and the observed baseline-versus-GEARS difference is a structured backbone-separation trade-off rather than a simple winner-take-all model ranking.

不允许在本图中扩展额外 headline，例如：

- GEARS 已证明恢复真实 biology
- backbone recovery 已等同于模型 closure
- foundation entrants 已推翻 shared-mean baseline
- 任一模型已“解决” recovery problem

### B2. Panel 数量与顺序冻结

Figure 3 固定为 `a–c` 三个 panel，不增减，不重排叙事顺序。

固定递进关系为：

- `a`：全量 metrics 总览
- `b`：headline baseline versus GEARS 核心对比
- `c`：backbone-separation trade-off 空间

跨 context 的 per-cell-line backbone 读数与配对展示 **不放在主图**；当前投稿版不再为这部分单独保留固定 Extended Data 承接图。

### B3. Claim boundary 冻结

当前 claim boundary 冻结为：

> GEARS is an architecture trade-off diagnosis; shared_mean_baseline is the backbone primary reference; do not claim model recovery proved.

这一定义高于局部作图偏好。凡是会削弱 `baseline = backbone reference` 或误导读者把 `GEARS` 读成“被证实的更优恢复器”的视觉处理，均禁止进入最终图。

### B4. 当前版面骨架冻结

最终布局冻结为：

- 第一行：`a | b`
- 第二行：`c`（全宽）

允许的后续版面动作仅限：

- 面板间距轻微收紧
- `c` 内部坐标范围和图例位置微调
- 投稿尺寸约束触发时的纵向压缩

不允许：

- 改成全新拼版语法
- 改变 `a → b → c` 的阅读路径
- 为了压缩高度而牺牲字号、图例可读性或数据区呼吸空间

---

## 2. 全局视觉规范（冻结）

### 2.1 跨图语义继承

Figure 3 必须继承 `Figure 1/2` 已建立的颜色语义，不允许重新发明颜色语言。

- `#009E73`：高性能 / 稳定 / HCC1143 / primary positive
- `#D55E00`：HCC38 / exposed contrast
- `#56B4E9`：阈值线 / baseline=1.0 参考线 / shift-like reference
- `#0072B2`：GEARS formal（仅 Figure 3 使用，表示实体方法而非阈值）
- `#333333`：shared-mean baseline / 文字 / 主轴 reference
- `#8E8E8E`：foundation entrants / 次要 supporting layer
- `#BDBDBD`：null / controls cloud / 分隔线 / 中性辅助层
- `#F5F5F5`：浅背景 / null 行锚定 / 退底层
- `#FAFAFA`：仅用于示意性 shaded region

### 2.2 文字与线宽下限

- 字体：`Arial / Helvetica / sans-serif fallback`
- 主文字、轴标签、数值标签：`>= 7.5 pt`
- 仅脚注性说明允许 `7 pt`
- 全图线宽不得 `< 0.5 pt`
- 关键引导线、误差条、虚线参考线优先 `0.75 pt`

### 2.3 三层执行原则

Figure 3 的 redesign 固定遵循以下顺序：

1. **先修正语义**：先纠正颜色映射、说明缺失和 reader-facing 标签错误。
2. **再做最小必要视觉收敛**：只做能强化主次层级、但不会改变 claim boundary 的视觉微调。
3. **最后才考虑压缩版面**：只有在实测高度和可读性同时触发风险时，才允许做纵向压缩。

---

## 3. 强制修改（必须完成）

### M1. Panel d — HCC context 颜色归位

必须执行：

- `HCC38` 全部数据点、连接线、误差条统一为 `#D55E00`
- `HCC1143` 全部数据点、连接线、误差条统一为 `#009E73`
- `baseline = 1.0` 参考虚线统一为 `#56B4E9`

原因：

这是与 `Figure 1/2` 建立零成本语义迁移的第一优先级，不可协商。

### M2. Panel b / c — GEARS 脱离阈值蓝

必须执行：

- `GEARS formal` 在 `b` 和 `c` 中统一改为 `#0072B2`
- 不得继续使用 `#56B4E9` 表示 GEARS 实体方法

原因：

`#56B4E9` 在全文已经承担“阈值 / 参考线”语义；若 GEARS 继续占用该色，会造成实体方法与参考系统混淆。

### M3. Panel c — supporting cloud 自我说明

必须同时执行图内与图注两层说明：

- 图内加极简脚注：`light gray cloud = GEARS sweeps, linear controls & null`
- 图注补充：`The null reference (separation = 0.00) lies below the displayed y-axis range.`

原因：

图内解决“这团灰点是什么”，图注解决“为什么看不到 null”。两层缺一不可。

### M4. Panel b — y 轴标签去代码化

必须执行：

- `backbone_recovery` 改为 `Backbone recovery`
- `structure/context_separation` 改为 `Structure / context separation`

不允许把 reader-facing 轴标签继续保留为代码变量风格。

### M5. Panel a — null 行视觉锚定

必须执行以下至少一项：

- `null` 行整行填充 `#F5F5F5`
- 或 `null` 行加上下细分隔线（`#BDBDBD`, `0.75 pt`）

目标：

让 `null` 明确作为参照系被读到，而不是继续埋入 LM controls 背景中。

---

## 4. 保守修改（按最小必要原则执行）

### C1. Panel a — 热图强调层

默认策略冻结为：

- 保留整体中性矩阵观感
- 仅对 `>= 0.8` 的格值加 `#009E73` 边框（约 `2 pt`）

暂不推荐：

- 把整张热图改成强主导的全绿 sequential heatmap

原因：

`a` 图的角色是“指标矩阵”，不是“类别归属图”；绿色应作为强调层，而不是统治整张图。

### C2. Panel c — shaded region 去判定化

默认策略冻结为：

- 右上示意区域使用 `#FAFAFA`
- 透明度约 `15%`
- 无边框

仅当导出后该区域仍被误读为强定义区时，才允许考虑极淡 hatch。  
默认不使用 hatch。

### C3. Panel c — 主次点大小层级

默认层级冻结为：

- `shared mean baseline`：`9 pt`，最大 reference anchor
- `GEARS formal`：`7 pt`，第二主角
- `Geneformer / scGPT`：`5 pt` 左右，降级为 foundation supporting entrants
- `GEARS sweeps / linear controls / null`：`3–4 pt`，组成真正的 supporting cloud

目的不是美学变化，而是把叙事稳定为：

`reference anchor` vs `best entrant` vs `supporting background`

### C4. Panel c — foundation entrants 降级为 supporting 层

默认策略冻结为：

- `Geneformer / scGPT` 使用 `#8E8E8E`
- 不再与 GEARS 或 baseline 共享高饱和视觉权重

原因：

本 panel 的主语是 trade-off 关系，而不是 foundation-model leaderboard。

### C5. Panel d — 图例位置原则

默认策略：

- 图例优先留在右下角
- 作为“读完图后确认身份”的次级阅读位置

仅当其与最右侧数据点、误差条或数值标注发生真实拥挤时，才允许移至右上角。  
不允许出于预防性焦虑提前改位。

---

## 5. Panel Freeze

### Panel a — Three adjudication metrics

锁定点：

- 保留三指标矩阵作为 Figure 3 的全量总览入口
- 高值仅做局部绿色强调，不把整图改成“绿色成绩单”
- `null` 必须拥有独立视觉锚定
- 数值文字遵循对比度优先原则：高值可白字加粗，低值黑字

不得再改：

- 不再把 `null` 与普通 controls 处理成完全同层
- 不再恢复代码化 reader-facing 标签

### Panel b — Baseline versus GEARS paired-dot

锁定点：

- `shared mean baseline` 为 `#333333`
- `GEARS formal` 为 `#0072B2`
- 连接线为 `#BDBDBD`
- y 轴标签使用自然语言，不使用下划线变量名

不得再改：

- 不再让 GEARS 与阈值参考线共用颜色
- 不再把 baseline 与 GEARS 视觉上画成并列无主次的双主角

### Panel c — Backbone-separation trade-off

锁定点：

- `shared mean baseline` 是最大 reference anchor
- `GEARS formal` 是第二主角，不与 baseline 等权
- `Geneformer / scGPT` 降级为 supporting entrants
- `light gray cloud` 必须自我说明
- 右上 shaded region 仅为 illustrative visual aid，不是 decision threshold
- 去除强背景网格，仅保留极淡参考线

不得再改：

- 不再把 shaded region 画成“合格区”
- 不再让 foundation entrants 与 GEARS / baseline 争夺第一层视觉权重

### Panel d — Per-context paired-dot

锁定点：

- `HCC38` 固定橙色，`HCC1143` 固定绿色
- `baseline = 1.0` 参考虚线固定为 `#56B4E9`
- 数值标注保持黑色
- 图例默认右下角，必要时才改位

不得再改：

- 不再交换 HCC 颜色语义
- 不再让图例遮挡右侧高值点或误差条

---

## 6. 版面压缩触发条件（冻结）

### 6.1 决策规则

Figure 3 不采用“为了压缩而压缩”的策略。  
是否压缩，固定按以下三维标准共同判断：

- 总高度
- 字号是否仍安全（主文字 `>= 7.5 pt`，脚注 `>= 7 pt`）
- panel 呼吸空间、图例与脚注是否开始挤占数据区

### 6.2 操作阈值

- `<= 240 mm`：默认不压缩
- `240–250 mm`：只允许轻微收紧 `a/b` 与 `c` 的间距
- `> 250 mm`：若同时出现拥挤征象，允许执行压缩

### 6.3 允许的压缩顺序

若必须压缩，仅允许优先执行：

1. 收紧 `c` 图显示范围与空白占比
2. 小幅压缩第一行与第二行之间的纵向留白

不允许优先执行：

- drastic layout change
- 降低字号
- 把脚注、图例硬塞进数据最密处

---

## 7. Caption / Legend 同步要求

Figure 3 完成 redesign 后，caption 必须同步以下边界：

- 明确 `shared-mean baseline` 是 backbone primary reference
- 明确 GEARS 代表的是 trade-off diagnosis，而非“总体胜出”
- 明确 `light gray cloud` 的组成
- 明确 `null` 位于 `panel c` 可视 y 轴范围之外
- 不得把右上 shaded region 写成 decision rule、pass region 或 scoring threshold

若 caption 与 panel 实际编码冲突，优先修正文案，不允许用“读者应自行理解”代替同步。

---

## 8. Submission QA Only（允许的后续改动）

freeze 后仅允许以下类型修改：

- PDF 裁剪、边距、RGB、字体嵌入、文件大小优化
- 导出导致的字号、线宽、透明度修复
- 期刊生产规范触发的尺寸微调
- 图例遮挡、脚注越界、数值重叠等明确排版 bug 修复

不允许的后续改动：

- 再次开放式修改 Figure 3 主色语义
- 再次改变 `a → b → c` 叙事顺序
- 基于“也许更好看”继续做无上限细调
- 在没有实测高度证据时主动压缩版面

---

## 9. Build / Refresh Path

重建命令冻结为：

```bash
PYTHONPATH="/home/data/gz0705/WTKO/src" python "scripts/manuscript/build_figure3_model_tradeoff.py"
```

重建输出目录：

- `reports/manuscript_figures_v2/fig3_model_tradeoff/`

投稿目录同步目标：

- `manuscript/figures/Figure_3/Figure_3.png`
- `manuscript/figures/Figure_3/Figure_3.pdf`

---

## 10. Figure 3 专用检查清单

### 强制项

- [ ] `3b/3c` 中 `GEARS = #0072B2`
- [ ] `3c` 图内已加 `light gray cloud = GEARS sweeps, linear controls & null`
- [ ] `3c` 图注已说明 `null` 位于显示 y 轴范围之外
- [ ] `3b` y 轴标签已去下划线
- [ ] `3a` `null` 行已有视觉锚定
- [ ] 需要 per-cell-line HCC 色与配对读数时，确认该层不再作为当前投稿版固定 Extended Data 图保留

### 保守项

- [ ] `3a` 高值格采用局部绿框，而非整图全绿
- [ ] `3c` shaded region 已降为极淡实色、无边框
- [ ] `3c` 中 baseline 与 GEARS 的点大小层级已拉开
- [ ] `3c` 中 foundation entrants 已降级为灰色 supporting 层

### 投稿合规项

- [ ] 全图主文字 `>= 7.5 pt`
- [ ] 脚注 `>= 7 pt`
- [ ] 全图线宽 `>= 0.5 pt`
- [ ] `3c` 无强背景网格
- [ ] 若总高度 `> 250 mm`，压缩动作已按 §6 顺序执行

---

## 11. Freeze Verdict

当前 Figure 3 的 redesign 冻结标准如下：

- 内容逻辑已稳定为 `全量 metrics → 核心对比 → trade-off 空间`；**跨 context 验证**不再作为当前投稿版固定 Extended Data 图单独给出
- 与 `Figure 1/2` 的颜色语义已明确可继承
- 误导风险最高的三处已锁定为第一优先级修正：
  - per-cell-line 读数不回流主图（防与 3c pooled 误读混叠；见 ED4）
  - `3b/3c` GEARS 脱离阈值蓝
  - `3c` supporting cloud 自我说明
- 视觉收敛策略已固定为最小必要原则
- 版面压缩已从“审美偏好”改为“实测触发”

**结论**：Figure 3 现进入 freeze 状态。后续只允许按本规范执行落地与 submission QA，不再做开放式重画。
