# SCP542 Basal Program Explanation Layer — Frozen Boundaries

## Data Availability

SCP542 Reference Layer Coverage:
  - HCC38_BREAST: 5648 genes × 30 NMF programs — AVAILABLE
  - HCC1143_BREAST: NOT in SCP542
  - BT549_BREAST (TNBC proxy): 5459 genes × 30 NMF programs — AVAILABLE
  - K562: NOT in SCP542 (different lineage/cancer type)

Data type: Per-cell-line NMF (gene × program loadings, W matrix)
           + cell-level program activation (H × cell matrix)
           + 800 global program gene sets (nmf_programs_sig_ccle)

HCC38 W matrix gene overlap with 47-gene atlas: 28/47 (60%)
Missing genes: BMPR1A, CDKN2A, ERC1, ETV3, HLX, KLF3, MAML3,
               MYBL1, NCOA1, PEX14, RORC, SMAD1, TAB3, THRA, TMF1,
               ZBTB17, ZBTB20, ZBTB5, ZNF566

## Positive Findings (What SCP542 Supports)

Supported by SCP542 analysis (positive claims):

1. "backbone 轴在 basal 空间中处于高可塑状态"
   → 所有 backbone 轴都跨 17-30 个程序分布
   → 这解释了为什么这些轴在扰动后表现为"强位移"：
     它们本来就嵌入在高可变的 basal 程序维度中

2. "Type A（state-rewriting）锚定在 chromatin/spliceosome 命运程序"
   → ENY2/TADA3/PRPF6/NPM1/ARID1A 在 basal HCC38 中就集中于
     chromatin/spliceosome 程序（8.1/7.6/9.9）
   → 这支持"state-rewriting"功能定位

3. "Type B（transition）与 signaling/cell-cycle 程序绑定"
   → LAMTOR5/VEZF1 basal loading 集中在 signaling 程序（6.5/8.2）
   → 这支持"过渡状态"功能定位

4. "TNBC 内部 basal state 存在异质性"
   → HCC38 vs BT549 loading correlation ≈ 0
   → 这为 line-skewed 提供了 basal heterogeneity 来源证据

5. "basal placement 是 distributed 而非 focal"
   → 这是所有轴的共同特征，支持"broad programmatic effect"模型

## Evaluations Performed

Q1 (Axis Basal Loading in HCC38 NMF):
  All 26 fine axes show broad distribution across 17-30 programs.
  No axis is anchored to a single "master program".
  Peak loadings are distributed, supporting "high basal plasticity" not
  "single anchor program" claim.

  Highest basal loadings:
    - JAK-STAT signaling (STAT3): 0.060 peak loading, 30/30 programs active
    - RNA processing/spliceosome (PRPF6): 0.060 peak loading, 30/30 programs
    - ER stress/UPR (XBP1): 0.050 peak loading, 30/30 programs
    → These are broad, distributed axes even in unperturbed basal state.

Q2 (Type A vs Type B Basal Placement):
  Type A genes (ENY2/TADA3/PRPF6/NPM1/ARID1A):
    Peak at programs 8.1, 7.6, 9.9 → chromatin/spliceosome lineage programs
    NOT matching any single SCP542 global program gene set exactly
  Type B genes (LAMTOR5/VEZF1):
    Peak at programs 6.5, 8.2 → signaling/cell-cycle programs
    NOT matching any single SCP542 global program gene set exactly

  → Type A and B systematically separate in basal program space,
    but neither maps to a discrete SCP542 global program.

Q3 (Line-skewed Basal Heterogeneity):
  PFDN5 (proteostasis/chaperone): skew=2.18, 17/30 programs active
  PA2G4 (growth/proliferation): skew=2.71, 12/30 programs active
  → Broad distribution supports "context-dependent basal heterogeneity"
    NOT "single fixed module"

Cross-line (HCC38 vs BT549 TNBC proxy):
  Loading correlation: mean=-0.056, median=-0.091
  → Weak/no correlation even within TNBC suggests basal state heterogeneity
    is a genuine feature, not artifact.

## Negative Claims (What SCP542 Does NOT Support)

Explicitly NOT supported by SCP542 analysis:

1. "某 backbone 轴锚定到单一 SCP542 全局程序"
   → 所有轴都broad分布，没有单点锚定。不存在"program X = our backbone"

2. "HCC1143 的 basal state 已被解释"
   → HCC1143 不在 SCP542，BT549 只是 proxy，不代表 HCC1143

3. "Type A/B 在 SCP542 中有精确匹配"
   → Type A peak at 8.1/7.6/9.9，Type B peak at 6.5/8.2
   → 分散在多个程序，没有一对一的 SCP542 global program 匹配

4. "K562 的结构复现有 SCP542 解释"
   → K562 完全不在 SCP542，N/A

5. "SCP542 解释了为什么 line-skewed 发生"
   → SCP542 只提供了 basal heterogeneity 的存在性证据（broad distribution）
   → 但不能直接解释"为什么同一基因在HCC38和HCC1143效果不同"

## Claim Boundary Summary

| Claim | SCP542 Status |
|-------|--------------|
| Backbone = high basal plasticity (distributed) | ✅ Supported |
| Type A = chromatin/spliceosome lineage programs | ✅ Supported |
| Type B = signaling/cell-cycle programs | ✅ Supported |
| Line-skewed = basal heterogeneity exists | ✅ Supported |
| Backbone = single anchor SCP542 program | ❌ Not supported |
| Type A/B = exact SCP542 global program match | ❌ Not supported |
| HCC1143 basal state explained | ❌ Not in SCP542 |
| K562 structure explained | ❌ Not in SCP542 |

## Evaluability Table

| Fine Axis | SCP542 Evaluable | Role Note |
|---|---|---|
| transcription / chromatin | Yes | broad/distributed placement — NOT 'single anchor program' |
| chromatin remodeling | Yes | broad/distributed placement — NOT 'single anchor program' |
| RNA processing / spliceosome | Yes | broad/distributed placement — NOT 'single anchor program' |
| ribosomal / translation | Yes | broad/distributed placement — NOT 'single anchor program' |

---
Generated: 2026-04-09
Script: scripts/pipeline/freeze_scp542_explanation_boundaries.py
