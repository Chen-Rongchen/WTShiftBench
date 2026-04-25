# Figure 4 Redesign Freeze Spec v1

**状态**：2026-04-25 冻结。当前 3-panel 投稿版结构已确认正确，代码可复现。

**核心问题**：The backbone recovery gap remains after prespecified local rebuttal tests.

---

## 0. Locked language

**Title**：
> Fig. 4. The backbone recovery gap remains after prespecified local rebuttal tests.

**Key quantitative anchors**：
- Shared-mean baseline backbone = 0.807
- GEARS formal backbone = 0.660
- Best rebuttal candidate (Sweep A) backbone = 0.643
- Residual gap Δ = 0.164

**Claim boundary**：
> A finite-budget GEARS neighborhood sweep (6 prespecified candidates) and embedding-based linear controls do not close the backbone recovery gap to the shared-mean baseline. GEARS training is not rerun during figure production; figure panels recompose frozen Stage 2 adjudication artefacts only.

---

## 1. Panel inventory（3 panel，硬冻结）

| Panel | Content | Purpose |
|---|---|---|
| a | Pre-specified finite-budget GEARS candidates table | 展示 sweep design：formal recipe + 5 sweep candidates (A-E) |
| b | Prespecified rebuttal trade-off subset | Backbone recovery × structure/context separation，有限 rebuttal 子集同度量同 pipeline |
| c | Per-context delta backbone plot | HCC38 / HCC1143 双栏对比，无 candidate 闭合 backbone gap |

---

## 2. Panel specs

### Panel a — Candidate table
- 列：Candidate, Epoch, LR, WD, Role
- 行：GEARS formal (reference) + A(best) + B + C + D + E
- 无 panel letter，标题左对齐

### Panel b — Trade-off map
- x = backbone_recovery_score, y = structure_vs_context_separation_score
- 共享坐标语法与 Fig 3c
- Baseline (black, large), GEARS formal (blue, large), sweep A-E (light blue, small), linear controls (gray, diamond)
- Baseline backbone 虚线标注 + gap bracket
- 该 panel 是 rebuttal subset，而不是对 Fig 3c 的全模型重画；解释边界写入 caption，不再单列 panel d
- 标题冻结为：`Prespecified rebuttal candidates do not close the backbone gap`

### Panel c — Delta plot
- HCC38 / HCC1143 双 facet
- x = Δ backbone recovery vs baseline
- 5 个 comparator：GEARS formal / Best sweep / scGPT-ridge / Geneformer-ridge / Low-rank decoder
- 零线虚线参考
- 不再保留独立 interpretation-boundary panel；bounded wording 移入 figure caption

---

## 3. Data anchors

| Source | File | SHA256 |
|---|---|---|
| Model comparison | `reports/stage2_real_hcc_smoke/model_comparison.tsv` | 790934f7... |
| Smoke summary | `reports/stage2_real_hcc_smoke/smoke_summary.tsv` | 2a7cd0c6... |
| Sweep manifest | `reports/stage2_gears_backbone_sweep/candidate_manifest.tsv` | e30c87b3... |
| Coverage audits | 6 JSON files (HCC38/HCC1143 × 3 controls) | various |

---

## 4. 视觉 identity

- `shared_mean_baseline`：`#333333`
- `gears_hcc_formal_v1`：`#0072B2`
- GEARS sweep A-E：`#85C1E9`
- linear controls：`#8E8E8E`
- baseline boundary / zero-line：`#56B4E9`
- shaded region：`#FAFAFA`

---

## 5. 语言治理

**必用**：
- prespecified local rebuttal test
- finite-budget neighborhood sweep
- does not close the backbone gap
- GEARS training is not rerun

**禁止**：
- tuning failure / hidden recipe winner
- coverage explains the gap
- 代码名 `lm_*` / `gears_hcc_formal_v1_e*` 出现在图面

---

## 6. 代码可复现性

- Script：`scripts/manuscript/build_figure4_sweep_controls.py`
- Entry：`pixi run --environment core python scripts/manuscript/build_figure4_sweep_controls.py`
- Output：`reports/manuscript_figures_v2/fig4_sweep_controls/`
- 已验证：2026-04-25 成功复现，输出与投稿目录一致
