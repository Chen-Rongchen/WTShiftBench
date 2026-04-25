# Extended Data Fig. 5 Redesign — Pre-Redraw Freeze Spec v1

**状态**：2026-04-23 起草，与 `manuscript/figures/Figure_4/figure4_redesign_freeze.md` 配套签字后进入阶段 B。

**用途**：在 Figure 4 收束为 4 panel 主图的同时，把 ED Fig. 5 作为其承接容器一次性冻结，避免"主图干净了、ED 重新膨胀"的二次返工。ED5 不再作为独立叙事图，它的唯一职责是为 Figure 4 的 rebuttal 结论提供可审计的支持层。

**上游依赖**：`figure4_redesign_freeze.md` §0 的 L1–L4 锁定语言；本文件任何 caption 必须与之同频，不得新增 headline 叙事。

**Anchor commit（figure-side）**：沿用 Figure 4 freeze 的 `5a9bc6507755a2ebc1f860b7d56e8541c5f6db54`。

---

## 0. Locked boundaries（本节内容不得再改）

**B1. ED5 最终标题**

> Extended Data Fig. 5. Finite-budget GEARS neighborhood sweep, linear-control design and coverage audit supporting Fig. 4.

**B2. ED5 panel 数量硬上限**

6 panel，不上浮。若后续发现需要 7 panel，必须先回本 freeze spec 修订；不允许通过代码侧"再塞一个小图"绕过。

**B3. ED5 的叙事边界**

ED5 不得承载任何 Figure 4 之外的 headline 叙事。它的三条 claim slot 只有：

- 本次 rebuttal test 的 finite-sweep 展开事实（sweep backbone / shift-excess）
- linear-control 的 design + coverage 实施说明
- figure-stage 产出的 reproducibility / provenance boundary

**B4. 与 Figure 4 主图的交叉引用方向**

Figure 4 主图 caption 中显式 cross-reference ED5（已写入 Figure 4 freeze §3）；ED5 caption 中反向写一句 "see Fig. 4 for the main-figure adjudication"。不允许在 ED5 中重复 Figure 4 的 headline 句。

---

## 1. Panel inventory（6 panel，硬冻结）

| Panel | Short id | 承接自旧 Fig 4 / 旧 ED5 |
|---|---|---|
| a | sweep backbone bar | 旧 Fig 4 panel a + 旧 ED5 c/e |
| b | shift-excess across sweep | 旧 Fig 4 panel c |
| c | recipe grid matrix | 旧 ED5 a + g |
| d | linear-control schematic | 旧 Fig 4 panel e |
| e | coverage audit matrix | 旧 Fig 4 panel g |
| f | reproducibility card | 旧 ED5 b + f + h |

---

## 2. Panel spec（每 panel 同步锁 4 件事：purpose / source / script / caption boundary）

---

### Panel a — Sweep backbone bar

**Panel purpose（回答哪条 reviewer question）**：
> 在 pre-specified finite sweep 中，每一个 sweep candidate 相对 shared-mean baseline 与 GEARS formal 的 backbone recovery 分数到底是多少？

**Panel content**：水平 bar chart，x 轴 `backbone_recovery_score`（0–1），y 轴 7 个对象自上而下按 backbone 降序：`shared_mean_baseline` → `gears_hcc_formal_v1` → Sweep A/B/C/D/E。配色沿用 Figure 3 对象 identity（黑 / 深蓝 / 淡蓝）。每条 bar 右端直接标数值（0.807 / 0.660 / 0.643 / 0.627 / 0.613 / 0.530 / 0.493）。

**Source data mapping**：
- Primary：`reports/stage2_real_hcc_smoke/model_comparison.tsv`（筛 `shared_mean_baseline` + `gears_hcc_formal_v1` + 5 个 sweep variant_id）
- Provenance manifest：`reports/stage2_gears_backbone_sweep/candidate_manifest.tsv`

**Script entry**：
- `scripts/manuscript/build_extended_data_figure5.py`
- → `src/wtbench/manuscript/extended_data_remaining.py : main_edfig5`（当前 ED5 入口已在此模块）

**Caption boundary**：
- 能说：no sweep candidate reaches the shared-mean baseline backbone score; no sweep candidate exceeds the GEARS formal backbone score under the pre-specified neighborhood.
- 不能说：sweep narrows the backbone gap（事实上未 narrow，见 Figure 4 Gate 4）；sweep 是 open-ended search；sweep 的最高分已"接近"baseline。
- 推荐 panel title：**a, GEARS finite-sweep backbone recovery**.

---

### Panel b — Shift-excess across sweep

**Panel purpose**：
> GEARS sweep candidates 在 backbone 之外的第二指标（shift-excess identification）上是否表现出可解释的 trade-off？

**Panel content**：水平 bar chart（与 a 同坐标系、同对象顺序、同配色），x 轴 `shift_excess_identification_score`（0–1）。同样 7 个对象。数值：0.333 / 0.333 / 0.833 / 0.500 / 0.917 / 0.917 / 0.667。允许在 panel 内加一条浅灰 reference line 标 baseline 值 0.333，便于读者对齐。

**Source data mapping**：
- 同 Panel a：`reports/stage2_real_hcc_smoke/model_comparison.tsv` 的 `shift_excess_identification_score` 列。

**Script entry**：同 a。

**Caption boundary**：
- 能说：several sweep candidates raise shift-excess identification relative to baseline and to GEARS formal; this rise co-occurs with lower backbone recovery in Panel a; shift-excess is an auxiliary metric, not a primary adjudication layer.
- 不能说：shift-excess 证明 GEARS 在任何"更合理的指标"下胜出；shift-excess 升高等价于 architecture 改进；shift-excess 是 independent orthogonal validation。
- 推荐 panel title：**b, Shift-excess rises while backbone recovery remains below baseline**.

---

### Panel c — Recipe grid matrix

**Panel purpose**：
> Pre-specified neighborhood 的 3×3×2 recipe grid 中，实际被 sweep 选中执行的 6 个点（base + 5 nearest neighbours）落在哪里？

**Panel content**：一张小的 matrix heatmap-style schematic，展示 `epochs ∈ {20,30,40}` × `lr ∈ {5e-4, 1e-3, 2e-3}` 的 9 格 grid（对 wd 两个值做两层 stacked matrix 或两张并列小矩阵），每格标注：
- `base` 标记在 `epochs=30, lr=1e-3, wd=1e-6`
- `A` 标记在 `epochs=30, lr=2e-3, wd=1e-6`
- `B/C/D/E` 各自对应 `candidate_manifest.tsv` 中的 variant_id
- 未被选中的格子用浅灰留空 + 小字 "not in nearest-6"

**Source data mapping**：
- Primary：`reports/stage2_gears_backbone_sweep/candidate_manifest.tsv`
- Grid 定义：`configs/stage2/gears_hcc_backbone_sweep_v1.json`（`allowed_recipe_axes` + `selection.max_candidates` + `selection.strategy`）

**Script entry**：同 a。

**Caption boundary**：
- 能说：the 3 × 3 × 2 pre-registered neighborhood, the `nearest_to_base` selection rule with `max_candidates = 6`, and the six executed variant_id.
- 不能说：grid 覆盖了所有"合理"的 GEARS 调参空间；未执行的 grid 点"可能胜出"；grid 设计可在 revision 中扩展。
- 推荐 panel title：**c, Pre-registered recipe grid and executed neighborhood**.

---

### Panel d — Linear-control design schematic

**Panel purpose**：
> Figure 4c 三个 linear controls 的具体实现（embedding source、readout、target coverage promise）是什么？

**Panel content**：三栏并列 schematic，一栏一个 control，每栏自上而下三行：
- 顶行：reader-facing 名字（Low-rank linear decoder / Geneformer-ridge control / scGPT-ridge control）
- 中行：embedding source（train-derived low-rank structure / frozen Geneformer target embedding / frozen scGPT target embedding）
- 底行：readout（linear low-rank decoder / ridge regression / ridge regression）

代码名（`lm_train_lowrank_hcc_formal_v1` 等）仅出现在 source data TSV 与 manifest，不出现在 panel 图面。

**Source data mapping**：
- Control configs：`configs/stage2/lm_train_lowrank_hcc_formal_v1.json`、`configs/stage2/lm_g_geneformer_ridge_hcc_formal_v1.json`、`configs/stage2/lm_g_scgpt_ridge_hcc_formal_v1.json`
- Recipe freeze 文档：`docs/stage2_lm_train_lowrank_hcc_recipe_freeze_v1.md` + 同级 `stage2_lm_g_*` recipe freeze（如存在）

**Script entry**：同 a。

**Caption boundary**：
- 能说：how each control defines its embedding source and its linear readout; that all three are evaluated under the identical scoring pipeline as GEARS and the shared-mean baseline.
- 不能说：这三个 controls 是 exhaustive；linear controls 足以 falsify GEARS；任何 linear decoder 的额外扩展"会关掉 gap"。
- 推荐 panel title：**d, Linear embedding controls: design summary**.

---

### Panel e — Coverage audit matrix

**Panel purpose**：
> 三个 linear controls 在两个 primary context（HCC38 / HCC1143）上是否都达到 full target coverage（47/47），以排除"gap 由 coverage 缺失解释"这一 reviewer 反驳？

**Panel content**：3 行（controls）× 2 列（HCC38 / HCC1143）的小 audit matrix，每格填 `47/47` 并用同一浅绿底色（或统一浅色，不用语义红绿），矩阵下方一行小字注 "full target coverage (47/47) in both primary contexts."

不做柱状图（旧 ED5 h 的等高柱完全删除，信息量不值主图-级 bar）。

**Source data mapping**：
- `reports/stage2_lm_train_lowrank_hcc_recipe/{HCC38,HCC1143}/coverage_audit.json`
- `reports/stage2_lm_g_geneformer_ridge_hcc_recipe/{HCC38,HCC1143}/coverage_audit.json`
- `reports/stage2_lm_g_scgpt_ridge_hcc_recipe/{HCC38,HCC1143}/coverage_audit.json`

**Script entry**：同 a。

**Caption boundary**：
- 能说：full target coverage was retained by all three linear controls in both primary contexts; therefore the backbone gap cannot be attributed to missing targets or to truncated vocabulary under the present rebuttal design.
- 不能说：full coverage 排除所有 "representation-level" 解释；coverage 是 sufficient check；coverage audit 证明 embedding 无关。
- 推荐 panel title：**e, Full target coverage in both primary contexts (47/47)**.

---

### Panel f — Reproducibility card

**Panel purpose**：
> 本轮 figure-stage 没有重训任何模型；所有 sweep runs 的 batch status、stop rule 触发与 artefact hash 的 provenance boundary 是什么？

**Panel content**：单 panel 白底细边框 card，分三段：

1. **Batch status summary**（小字列表）：`5 sweep variants + 1 formal base = 6 runs completed, 0 failed`；来源 `reports/stage2_gears_backbone_sweep/batch_run/batch_status.tsv`。
2. **Stop rule outcome**：直接引用 sweep config JSON 的 `"stop_rule"` 字段文本 + 一行结论 "triggered; no further GEARS optimization pursued."
3. **Figure-stage boundary**：`GEARS training is not rerun during figure production; figure panels recompose frozen Stage 2 adjudication artefacts only.`（与 Figure 4 `claim_boundary` 同步。）

**Source data mapping**：
- `reports/stage2_gears_backbone_sweep/batch_run/batch_status.tsv`
- `configs/stage2/gears_hcc_backbone_sweep_v1.json`（`stop_rule` 字段）
- `reports/stage2_gears_backbone_sweep/final_adjudication.md`

**Script entry**：同 a。

**Caption boundary**：
- 能说：sweep execution state, stop-rule trigger, and the figure-stage provenance boundary.
- 不能说：该 boundary card 等价于 full pre-registration；stop rule 可在 revision 中重新定义。
- 推荐 panel title：**f, Reproducibility and stop-rule boundary**.

---

## 3. ED5 整体 caption 草稿（冻结）

**Extended Data Fig. 5. Finite-budget GEARS neighborhood sweep, linear-control design and coverage audit supporting Fig. 4.**

**a**, GEARS finite-sweep backbone recovery. Backbone recovery scores for the shared-mean baseline, GEARS formal and five pre-registered sweep candidates (A–E), drawn from the identical HCC primary adjudication pipeline (`reports/stage2_real_hcc_smoke/model_comparison.tsv`). No sweep candidate reaches the shared-mean baseline or exceeds GEARS formal.

**b**, Shift-excess across the sweep. Several sweep candidates raise shift-excess identification above the baseline and GEARS formal, while their backbone recovery remains below baseline in panel a. Shift-excess is an auxiliary metric, not a primary adjudication layer.

**c**, Pre-registered recipe grid and executed neighborhood. The 3 × 3 × 2 recipe grid over epochs, learning rate and weight decay, with the six executed variants (base + nearest five) marked; selection rule `nearest_to_base`, `max_candidates = 6` (`configs/stage2/gears_hcc_backbone_sweep_v1.json`).

**d**, Linear embedding controls: design summary. Embedding source and linear readout for Low-rank linear decoder, Geneformer-ridge control and scGPT-ridge control; all three are evaluated under the identical scoring pipeline as GEARS and the shared-mean baseline.

**e**, Full target coverage in both primary contexts (47/47). Target-coverage audit for the three linear controls across HCC38 and HCC1143; the backbone gap is therefore not attributable to missing targets under the present rebuttal design.

**f**, Reproducibility and stop-rule boundary. Sweep batch execution state, the pre-registered stop rule and its trigger, and the figure-stage provenance boundary. GEARS training is not rerun during figure production; all panels recompose frozen Stage 2 adjudication artefacts only.

See Fig. 4 for the main-figure adjudication.

---

## 4. Panel-to-artefact 矩阵（一张表对齐所有 panel）

| Panel | Purpose slot | Source file(s) | Script entry | Caption boundary 号 |
|---|---|---|---|---|
| a | Sweep backbone fact | `reports/stage2_real_hcc_smoke/model_comparison.tsv` | `scripts/manuscript/build_extended_data_figure5.py` → `extended_data_remaining.main_edfig5` | a §2a |
| b | Shift-excess trade-off | `reports/stage2_real_hcc_smoke/model_comparison.tsv` | 同 a | b §2b |
| c | Recipe grid design | `configs/stage2/gears_hcc_backbone_sweep_v1.json` + `reports/stage2_gears_backbone_sweep/candidate_manifest.tsv` | 同 a | c §2c |
| d | Linear-control design | `configs/stage2/lm_*_hcc_formal_v1.json` + `docs/stage2_lm_*_hcc_recipe_freeze_v1.md` | 同 a | d §2d |
| e | Coverage audit | `reports/stage2_lm_*_hcc_recipe/{HCC38,HCC1143}/coverage_audit.json` | 同 a | e §2e |
| f | Reproducibility boundary | `reports/stage2_gears_backbone_sweep/batch_run/batch_status.tsv` + sweep config `stop_rule` + `final_adjudication.md` | 同 a | f §2f |

---

## 5. 视觉 identity（沿用 Figure 3/4）

- `shared_mean_baseline`：`#2B2B2B`
- `gears_hcc_formal_v1`：`#4C78A8`
- GEARS sweep A–E：`#8DB7D6`
- linear controls：`#A6A6A6`
- reference lines / grid empty cells：`#D0D0D0`

Panel c 的 grid matrix 与 Panel e 的 coverage matrix 统一用浅色系填充，不用语义红绿。最终配色 pass 等 6 主图 + 10 ED 全部 redraw 完成后统一冻结。

---

## 6. 语言治理（ED5 专属追加）

**禁止**：
- 在 ED5 任何 panel / caption 中复写 Figure 4 的 L1 title 或 L4 boundary 句；
- 在 ED5 中引入任何非本文件 §1 inventory 的 panel（即使是"为了读者好"）；
- 在 panel d 中出现代码名 `lm_train_lowrank_hcc_formal_v1` 等（只允许出现在 source data TSV / manifest）；
- 在 panel e 中把 coverage audit 叫作 "sufficient check" 或 "complete audit"；统一用 "target coverage audit"。

**必用**：
- `pre-specified neighborhood` / `pre-registered recipe grid` / `nearest-to-base selection`
- `finite-budget sweep`
- `auxiliary metric, not a primary adjudication layer`（panel b）
- `under the present rebuttal design`（panel e）
- `figure-stage provenance boundary`（panel f）

---

## 7. 实施依赖与执行顺序

**阶段 A（本 freeze spec 与 Figure 4 freeze 一同签字）**：
- 本文件与 `figure4_redesign_freeze.md` 构成 Figure 4 / ED5 redraw 的双文件冻结。签字后进入阶段 B。

**阶段 B（代码重画）**：
1. 修改 `src/wtbench/manuscript/figure4_sweep_controls.py`：收束为 4 panel。
2. 修改 `src/wtbench/manuscript/extended_data_remaining.py : main_edfig5`：收束为本文件 §1 的 6 panel。
3. 重跑 prototype：
   - `pixi run --environment core python scripts/manuscript/build_figure4_sweep_controls.py`
   - `pixi run --environment core python scripts/manuscript/build_extended_data_figure5.py`
4. 产出位置：
   - 主图 prototype：`reports/manuscript_figures_v2/fig4_sweep_controls/`
   - ED5 prototype：`reports/manuscript_extended_data_v1/edfig5_gears_sweep/`
5. 人工审过再覆盖投稿目录：
   - `manuscript/figures/Figure_4/`（PDF/PNG/panel manifest/source data）
   - `manuscript/extended_data/Extended_Data_Figure_5/`（同上）
6. 同步 legend 与正文：
   - `manuscript/text/figure_legends_v1.md`（Fig. 4 + ED Fig. 5）
   - `manuscript/text/manuscript_draft_v1.md`（cross-reference）
7. 重建 submission manifest：
   - `pixi run --environment core python scripts/manuscript/build_submission_package.py`
8. 更新 `plan.md` 的 Phase label 与本轮执行记录。

**阶段 C（审图确认）**：人工目视 prototype → 覆盖投稿目录 → 同步 legend → 更新 plan。

---

## 8. Go / No-Go 表

| Gate | 状态 | 备注 |
|---|---|---|
| ED5 ≤ 6 panel | ✅ 已冻结（§1） | 硬上限 |
| 每 panel 的 purpose / source / script / caption boundary 四锁 | ✅ 已逐条列（§2） | |
| 与 Figure 4 locked language 同频 | ✅ §0 B3/B4 保证 | 不得复写 L1–L4 |
| 代码入口确认 | ✅ `extended_data_remaining.main_edfig5` | 需在阶段 B 内部重构该函数 |
| 数据锚全部已存在 | ✅ model_comparison.tsv / candidate_manifest.tsv / batch_status.tsv / sweep config / coverage audits | 无需新跑分析 |

**五项全 PASS。与 Figure 4 freeze 一同签字后进入阶段 B。**
