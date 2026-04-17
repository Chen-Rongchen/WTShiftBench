# Top-10 anticipated reviewer questions v1

## 状态

完成日期：2026-04-17。

用途：内部 rebuttal rehearsal，不作为正文提交。若进入 major revision，可从本文件抽取 response-to-reviewers 初稿。

## 1. Why only two HCC cell lines?

The primary HCC evidence is intentionally limited to HCC38 and HCC1143 because the benchmark first freezes a truth object with matched perturbation transcriptomic and cancer dependency readouts, rather than aggregating heterogeneous contexts post hoc. We do not claim broad biological generalization from two cell lines. The manuscript frames HCC as the primary demonstration of a phenotype-aligned truth object and architecture-aware adjudication, with K562 retained only as supplementary architecture-form evidence.

The claim boundary is therefore framework/resource first, bridge content second. Target-level anchors are tiered and qualified; PFDN5 is primary but qualified, while PMF1, PRPF6 and ZNF131 are supporting-only.

## 2. Is the shared-mean baseline winning because of metric artifact or leakage?

The shared-mean baseline is a frozen-architecture backbone reference, not a deployable predictive model. It is constructed from the canonical-backbone transcriptomic component and does not use DepMap dependency values, RNAi endpoints or model-side scoring outcomes to generate target-specific predictions. Its role is to test whether the recovery object contains a dominant shared-backbone component.

The result is not uniformly favorable to the baseline: GEARS shows stronger structure-versus-context separation, and sweep candidates can improve separation or shift-excess without closing the backbone gap. The metric diagnostic also shows that the three architecture-aware metrics are partially coupled but non-identical. A three-metric permutation null is planned as an additional first-submission robustness analysis.

## 3. Was GEARS sufficiently trained or swept?

GEARS was evaluated under a predefined finite-budget neighborhood sweep, not an exhaustive hyperparameter optimization. The sweep varied epochs, learning rate and weight decay, selected six nearest-to-base candidate recipes, and used a pre-specified stop rule. No candidate closed the backbone gap to the shared-mean reference, and no candidate exceeded the formal GEARS recipe for backbone recovery.

We therefore do not claim that every possible GEARS recipe has been ruled out. The claim is narrower: under a bounded, pre-specified local sweep, GEARS remains a separation-biased entrant rather than becoming the HCC primary backbone winner.

## 4. How is this different from Ahlmann-Eltze et al. and other baseline-vs-deep-model benchmarks?

Prior perturbation-prediction benchmarks evaluated expression-level reconstruction or post-perturbation transcriptome prediction and showed that simple baselines can match or exceed deep learning entrants. This manuscript does not claim novelty for the generic observation that baselines can be strong.

The difference is the evaluated object and adjudication structure. We first freeze a phenotype-relevant fitness bridge by aligning perturbation transcriptomic shifts to cancer dependency endpoints. Model recovery is then decomposed into backbone recovery, shift-excess identification and structure-versus-context separation. The result is an architecture-aware trade-off diagnosis, not a single expression-prediction leaderboard.

## 5. Why is K562 architecture-form only?

The K562 temporal panel differs from the HCC primary benchmark in target set, macro-class composition, timepoint structure and bridgeable target count. It can test whether a backbone-plus-shift-excess form recurs under an external K562 context, but it cannot establish content-level replication of HCC anchors.

For this reason, K562 is tiered as supplementary architecture-form support. It is not a primary co-pillar, not content-level convergence, and not proof of external model-side generalization.

## 6. What does shift-excess measure beyond ordinary residual?

Shift-excess is the part of the perturbation response that exceeds what is explained by the canonical shared backbone. It is not synonymous with total displacement, global expression error or ordinary residual in a generic regression sense. In this benchmark, it is an architecture role defined after freezing the truth object.

The metric asks whether a model identifies targets whose transcriptomic displacement is larger or more context-specific than expected from the shared backbone. This is why a model can improve shift-excess identification without winning backbone recovery.

## 7. Why is PFDN5 primary_but_qualified rather than fully primary?

PFDN5 is the strongest shared anchor under the current evidence tiering because it remains recurrent across HCC38 and HCC1143 and survives cutoff/covariate-aware governance better than the other shared anchors. However, the metadata do not fully resolve run-level batch structure, and the shared-anchor set remains small.

Therefore, PFDN5 supports the bridge content layer but does not become an unqualified causal or fully deconfounded target claim. The wording `primary_but_qualified` preserves this distinction.

## 8. Is axis R2 = 0.092 enough for a primary axis?

The transcription/chromatin axis is not used as a strong mechanistic claim. It is retained as `primary_axis_but_qualified` because it is the strongest formal axis under the predefined evidence rules, not because its R2 alone proves a dominant biological mechanism.

Axis-level evidence is explicitly secondary to the architecture-level truth object and target tiering. It provides interpretation, not closure.

## 9. How do you handle barcode_gem_group confounding?

`barcode_gem_group` is treated as a design-proxy covariate because the available metadata resolve HCC38 to aggrMH001-3 and HCC1143 to aggrMH004-6, but do not map each barcode suffix to a single MH001-MH006 run. The manuscript therefore does not claim full deconfounding.

The covariate audit prevents overclaiming rather than removing the limitation. A one-shot design-proxy residualization check is planned to test whether the primary anchor structure is overturned, but even a stable result will not be written as full run-level batch control.

## 10. Why retain RNAi DEMETER2 if it is weaker than CRISPR DepMap?

RNAi DEMETER2 is retained as a cross-platform sensitivity endpoint, not as a matched primary endpoint. Across HCC38, HCC1143, K562 7d and K562 13d, CRISPR DepMap bridge signal is stronger than RNAi. This supports the endpoint hierarchy rather than weakening it.

The manuscript uses RNAi to show that the primary bridge readout should remain CRISPR DepMap. RNAi does not replace CRISPR and does not provide equivalent primary evidence.

## Revision-ready expansion notes

If reviewers request additional evidence scope:

- Frangieh 2021 can be considered as architecture-form-only external evidence after admission confirmation.
- Replogle 2022 K562 CRISPRi can be considered as a larger modality-compatible external panel after admission confirmation.
- If an additional entrant is explicitly requested, add at most one entrant under expedited admission and label it as reviewer-requested sensitivity, not core benchmark expansion.
