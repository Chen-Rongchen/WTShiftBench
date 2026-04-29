# Manuscript submission workspace

## 一句话入口

当前最新主稿只看这里：

- 正文：`manuscript/text/manuscript_draft_v1.md`
- 图注：`manuscript/text/figure_legends_v1.md`

这两个文件是当前投稿前唯一正文 source of truth。

## 当前阶段

**Extended Data Fig. 1-5 全部定版**（2026-04-30，commit `8c6d0a0`）。

剩余投稿事项：
- 作者姓名、单位、通讯邮箱
- Funding、competing interests、author contributions、acknowledgements
- Public repository / archive DOI
- Additional files 编号最终确认

## 原则

- 不新增分析、不改变 source data、不改变 claim boundary
- 原始 source data 和 manifest 仍以 `reports/` 中的冻结产物为准

## ED Figure 面板结构

| Figure | Panels | 构建脚本 |
|--------|--------|---------|
| ED Fig 1 | a (table), b (5 UMAPs), c (5 arrows) | `scripts/manuscript/build_edfig1_composite.py` |
| ED Fig 2 | a (top-n), b (heatmap), c (endpoint gap), d (subsampling), e (self-expression scatter) | `scripts/manuscript/build_edfig2_panel_e.py --reference` → `scripts/manuscript/build_edfig2_composite.py` |
| ED Fig 3 | a (K562 temporal), b (Replogle scatter) | `scripts/manuscript/fix_edfig3_panelb_square.py` |
| ED Fig 4 | a (axis signal space), b (R² ranking) | `scripts/manuscript/build_extended_data_figure10_axis_explanatory.py` |
| ED Fig 5 | a (pathway heatmap) | `scripts/manuscript/build_extended_data_figure9_biological_landing.py` |

## 一键重画全部 Extended Data Figures

```bash
# ED Fig 3 — K562 temporal + Replogle large-scale
pixi run --environment core python scripts/manuscript/fix_edfig3_panelb_square.py

# ED Fig 1 — Dataset familiarization (PIL composite from existing panel PNGs)
pixi run --environment core python scripts/manuscript/build_edfig1_composite.py

# ED Fig 2 — Metric robustness + self-expression scatter
pixi run --environment core python scripts/manuscript/build_edfig2_panel_e.py --reference
pixi run --environment core python scripts/manuscript/build_edfig2_composite.py

# ED Fig 4 — Axis explanatory space
pixi run --environment core python scripts/manuscript/build_extended_data_figure10_axis_explanatory.py
cp reports/manuscript_extended_data_v1/edfig10_axis_explanatory_space/edfig10.png \
   manuscript/extended_data/Extended_Data_Figure_4/Extended_Data_Figure_4.png

# ED Fig 5 — Pathway polarity heatmap
pixi run --environment core python scripts/manuscript/build_extended_data_figure9_biological_landing.py
cp reports/manuscript_extended_data_v1/edfig9_biological_landing/edfig9.png \
   manuscript/extended_data/Extended_Data_Figure_5/Extended_Data_Figure_5.png
```

## Panel Letter 统一规范

所有 ED 图 panel letter 统一为：
- **matplotlib**：`fontsize=8.5`、`fontweight="bold"`、位置 `x=-0.08`
- **PIL**：`FONT_SIZE=34`、`DejaVuSans-Bold`、位置 `(32, 12-18)`

## 面板结构明细

### ED Fig 1 — Dataset familiarization and endpoint inputs

PIL composite 拼接，依赖 `manuscript/extended_data/Extended_Data_Figure_1/panels/` 下的 a-k panel PNG。

- **a**：Dataset overview table
- **b**：5 UMAPs (HCC38, HCC1143, K562 7d, K562 13d, Replogle K562 essential)
- **c**：5 target-gene expression change arrows

### ED Fig 2 — Metric robustness audit

Panel a-d 由 `build_extended_data_figure13.py` 生成。Panel e 由 `build_edfig2_panel_e.py --reference` 独立生成。PIL composite 拼接为 5-panel 整图。

- **a**：Top-n gene-subset sensitivity
- **b**：Metric × CRISPR endpoint heatmap
- **c**：Endpoint sensitivity (CRISPR vs RNAi gap)
- **d**：Control-subsampling robustness
- **e**：Whole-transcriptome shift vs target-gene self-expression scatter (YlOrRd colormap, gene labels below with arrows)

### ED Fig 3 — K562 temporal + large-scale bridge confirmation

独立脚本 `fix_edfig3_panelb_square.py` 生成 panel a+b，PIL 拼接。

- **a**：K562 temporal bridge-magnitude dissociation (7d vs 13d)
- **b**：Replogle K562 essential joint grid scatter (square axes, 5-color quadrants)

### ED Fig 4 — Descriptive axis-level signal space

- **a**：Axis-level signal space (dependency R² vs shift R²)
- **b**：Paired axis R² ranking (Shift/Dependency markers in legend)

### ED Fig 5 — Exploratory pathway-response polarity heatmap

- **a**：Pathway NES heatmap (Hallmark gene sets) with Spearman rho and sign-agreement side strips

## 不再作为当前稿的文件

`docs/` 下的早期 manuscript draft 文件只作为历史草稿或路线记录。

## 投稿前仍需作者补齐

- 作者姓名、单位、通讯邮箱
- Funding、competing interests、author contributions、acknowledgements
- Public repository 链接、数据 accession、代码 archive DOI
- Additional files 最终编号
