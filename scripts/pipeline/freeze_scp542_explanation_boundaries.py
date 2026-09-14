#!/usr/bin/env python3
"""
Stage 2 — Freeze SCP542 Explanation Layer Boundaries

Documents what SCP542 calibration supports and does not support
regarding the HCC truth architecture.

NOT a new discovery script — boundary documentation only.

Run: pixi run python scripts/pipeline/freeze_scp542_explanation_boundaries.py
"""

from pathlib import Path

import pandas as pd

SCP542_DIR = Path("data/baselines/scp542")
ATLAS_DIR  = Path("reports/truth_driven_bridge/master_atlas")
CONTRACT_DIR = ATLAS_DIR.parent / "truth_architecture_contract"
SCP542_CAL_DIR = ATLAS_DIR.parent / "scp542_calibration"
OUT_DIR    = SCP542_CAL_DIR

# ── What SCP542 is ─────────────────────────────────────────────────────────
SCP542_COVERAGE = """
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
"""

# ── What SCP542 evaluated ──────────────────────────────────────────────────
SCP542_EVALUATION = """
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
"""

# ── What SCP542 DOES NOT support ───────────────────────────────────────────
SCP542_NEGATIVE_CLAIMS = """
Explicitly NOT supported by SCP542 analysis:

1. "A backbone axis is anchored to one SCP542 global program"
   All axes are broadly distributed, without a single anchor; no program X equals our backbone.

2. "The HCC1143 basal state has been explained"
   HCC1143 is absent from SCP542; BT549 is a proxy, not HCC1143.

3. "Type A/B exactly match SCP542 programs"
   → Type A peak at 8.1/7.6/9.9，Type B peak at 6.5/8.2
   They span multiple programs, without one-to-one SCP542 global-program matches.

4. "SCP542 explains K562 structural replication"
   K562 is absent from SCP542; not applicable.

5. "SCP542 explains why line-skewing occurs"
   SCP542 only provides evidence of basal heterogeneity through broad distributions.
   It does not directly explain why the same gene has different effects in HCC38/HCC1143.
"""

# ── What SCP542 DOES support ────────────────────────────────────────────────
SCP542_POSITIVE_CLAIMS = """
Supported by SCP542 analysis (positive claims):

1. "Backbone axes occupy highly plastic basal states"
   All backbone axes span17-30 programs.
   This is offered as an explanation for strong perturbational displacement:
     they are already embedded in highly variable basal-program dimensions.

2. "Type A(state-rewriting) anchors to chromatin/spliceosome fate programs"
   ENY2/TADA3/PRPF6/NPM1/ARID1A concentrate in basal HCC38
     chromatin/spliceosome programs(8.1/7.6/9.9).
   This supports the state-rewriting functional interpretation.

3. "Type B(transition) associates with signaling/cell-cycle programs"
   LAMTOR5/VEZF1 basal loadings concentrate in signaling programs(6.5/8.2).
   This supports a transition-state functional interpretation.

4. "Basal states vary within TNBC"
   → HCC38 vs BT549 loading correlation ≈ 0
   This provides evidence of basal heterogeneity underlying line-skewing.

5. "Basal placement is distributed rather than focal"
   All axes share this property, supporting a broad programmatic-effect model.
"""


def _make_evaluability_table():
    contract_path = CONTRACT_DIR / "truth_architecture_contract.tsv"
    if not contract_path.exists():
        return "(contract not yet generated)"
    df = pd.read_csv(contract_path, sep="\t")
    bb = df[df["architecture_role"] == "canonical_backbone"][["fine_axis", "scp542_evaluable", "scp542_role_note"]]
    lines = ["| Fine Axis | SCP542 Evaluable | Role Note |",
             "|---|---|---|"]
    for _, r in bb.iterrows():
        ev = "Yes" if r["scp542_evaluable"] else "No"
        note = str(r.get("scp542_role_note", "N/A"))
        lines.append(f"| {r['fine_axis']} | {ev} | {note} |")
    return "\n".join(lines)


# ── Generate frozen boundary document ──────────────────────────────────────
doc = f"""# SCP542 Basal Program Explanation Layer — Frozen Boundaries

## Data Availability

{SCP542_COVERAGE.strip()}

## Positive Findings (What SCP542 Supports)

{SCP542_POSITIVE_CLAIMS.strip()}

## Evaluations Performed

{SCP542_EVALUATION.strip()}

## Negative Claims (What SCP542 Does NOT Support)

{SCP542_NEGATIVE_CLAIMS.strip()}

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

{_make_evaluability_table()}

---
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d')}
Script: scripts/pipeline/freeze_scp542_explanation_boundaries.py
"""


doc_path = OUT_DIR / "scp542_explanation_boundaries.md"
with open(doc_path, "w") as f:
    f.write(doc)

print(f"Frozen SCP542 boundaries → {doc_path}")
print(doc)
