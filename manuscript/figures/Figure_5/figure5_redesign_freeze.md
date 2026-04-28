# Figure 5 Redesign — Final Reconstruction Lock

**状态**：2026-04-25 锁定。Figure 5 不再继续开放结构讨论，后续只按边界条件执行重画。 

**当前 Figure 5 身份**：原 Figure 6 前移为主文 Figure 5，作为最终 claim-boundary 图。

**原 Figure 5 身份**：axis-level interpretation 现作为 biological landing layer 并入 Extended Data Fig. 4；不再单独保留 axis adjudication figure。

---

## Locked Boundaries

**Title**

> Fig. 5. Boundary audits define the benchmark's bounded claim scope.

**Core principle**

This figure is not a summary slide and not an additional discovery figure. It is a graphical claim-boundary figure.

The figure must convert existing audit results into visual evidence, with minimal text and no card-like explanatory blocks.

**Narrative order (left → right)**

1. **a** — HCC38 / HCC1143 covariate boundary (primary benchmark core).  
2. **b** — Cross-context **endpoint hierarchy** (first unified readout placing HCC and K562 together).  
3. **c** — **K562 temporal** boundary (7d/13d zoom-in; supplementary, after K562 is already introduced in b).

**Panel count**

3 panel（a-c）进入主 Figure 5 composite；原 boundary gate flow 另存为 overview 素材，供后续 Figure 1a / study overview 重排复用。

**Visual center**

`b` endpoint hierarchy 是新版 Figure 5 的主视觉中心（置中、最宽列）；boundary gate flow 不进入主图，只作为 overview 素材另存。

**Output location**

- 投稿主图：`manuscript/figures/Figure_5/Figure_5.{png,pdf}`
- Panel 输出：`manuscript/figures/Figure_5/panels/Figure_5_panel_{a..c}.{png,pdf}`
- Overview 素材：`manuscript/figures/Figure_5/overview_assets/boundary_gate_flow_overview.{png,pdf}`
- 开发输出：`reports/manuscript_figures_v2/fig6_boundary/figure6.{png,pdf}`

**Cross-references**

- Axis-level explanatory space is now part of Extended Data Fig. 4.
- Temporal details remain Extended Data Fig. 3.
- Endpoint hierarchy is carried by Fig. 5 and no longer has a separate Extended Data figure.

---

## Figure Identity

The benchmark scope is not asserted by narrative; it is bounded by three audit layers and finalized in the caption-level claim boundary.

Internal production rule:

- `a` 讲 residual exposure
- `b` 讲 endpoint hierarchy（跨 context 统一 readout）
- `c` 讲 K562 metric dependence / temporal boundary

---

## Panel Inventory

| Panel | Short id | Role | Locked task |
|---|---|---|---|
| a | Covariate boundary heatmap | Residual exposure | Separate axis-level mean imbalance from target-level residual exposure. |
| b | Endpoint hierarchy | Main visual evidence | Show CRISPR > RNAi within every context; HCC and K562 under the same readout. |
| c | Temporal boundary | Metric dependence (K562) | Show that K562 7d/13d evidence is metric-dependent and boundary-setting. |

---

## Panel Specs

### Overview asset — Boundary gate flow

**Role**  
Navigation only. This asset is not part of the final Figure 5 composite.

**Must show**

- Covariate boundary
- Temporal boundary
- Endpoint hierarchy
- Bounded claim scope

**Design**

- Use a thin gate-flow strip.
- Keep labels short.
- Treat the panel as a map for the rest of the figure.

**Do not**

- Add paragraph text.
- Explain claim logic here.
- Let this panel dominate the figure.
- Write full “blocks xxx wording” sentences inside the panel.

**Internal rule**  
The gate flow only tells the reader what boundaries exist. It is reserved for later Figure 1a / overview assembly.

### Panel a — Covariate boundary heatmap

**Role**  
Show residual covariate exposure.

**Source fields**

- `mean_tvd`
- `n_targets_tvd_gt_0.25`

**Visual encoding**

- Cell shading = `mean_tvd`
- Dot / glyph / number = `n_targets_tvd_gt_0.25`
- Do not introduce a third primary encoding in the main panel

**Axis order**

Sorting must serve interpretation, not naming.

Recommended order:

1. `barcode_gem_group`
2. `transcriptome_detected_genes_quantile_bin`
3. `transcriptome_total_signal_quantile_bin`
4. `num_umis_over_threshold_bin`
5. `num_umis_quantile_bin`

UMI-related axes must remain visually clustered.

**Critical logic**

Mean TVD does not exceed the hard imbalance threshold, but target-level residual UMI-related exposure prevents fully deconfounded wording.

**Do not**

- Add an “Impact on wording” text column.
- Imply mean TVD itself triggered the hard threshold.
- Use this panel to block the bridge claim entirely.
- Sort rows alphabetically or blindly inherit raw source-data order.

**Internal rule**  
`a` separates axis-level mean imbalance from target-level residual exposure. The row order is part of the explanation.

### Panel b — Endpoint hierarchy

**Role**  
Main visual evidence panel; first time HCC and K562 share a unified bridge-Spearman readout in this figure.

**Source fields**

- `spearman` by `context` and `platform_pair`
- `n_shared_targets` as small label

**Locked anchor values**

- HCC38: CRISPR `0.726` vs RNAi `0.276`
- HCC1143: CRISPR `0.779` vs RNAi `0.384`
- K562 7d: CRISPR `0.733` vs RNAi `0.333`
- K562 13d: CRISPR `0.515` vs RNAi `0.300`

**Preferred visual**

Paired dot / dumbbell plot.

**Reason**

The main message is within-context hierarchy: CRISPR consistently exceeds RNAi.

**Design**

- y-axis: contexts
- x-axis: bridge Spearman rho
- green point: CRISPR DepMap
- gray point: RNAi DEMETER2
- thin connector line within each context
- short, light annotation: `CRISPR > RNAi in all contexts`

**Readability constraints**

- Lines and points must stay light
- Context labels must remain fully legible
- The annotation must not overpower the data

**Fallback**

If the dumbbell layout becomes visually crowded or less legible, fall back to a plainer paired-point or paired-bar form.

**Do not**

- Compress this panel too much.
- Hide it as a small inset.
- Prioritize novelty over clarity.

**Internal rule**  
`b` is the strongest data panel in Figure 5. Its form serves “hierarchy at first glance,” not visual innovation.

### Panel c — Temporal boundary

**Role**  
Show metric dependence across K562 7d / 13d (supplementary zoom after `b` introduces K562).

**Source fields**

- `aligned_spearman`
- `mean_truth_metric`
- optional footer source: `temporal_target_delta.tsv`

**Core message**

K562 7d has stronger rank-bridge alignment, whereas K562 13d has larger perturbation-shift magnitude.

**Interpretation**

Supports temporal stratification / architecture-form recurrence, not content-level replication.

**Design**

- Main plot: `aligned_spearman` for 7d vs 13d
- Inset: `mean_truth_metric`
- Optional very thin delta strip: target-level `13d - 7d` shift

**Decision rule**

Export both with and without the delta strip. Keep the delta strip only if it does not reduce first-glance readability.

**Do not**

- Turn this panel into a metric dashboard.
- Put both mean and median in the formal inset.
- Let the delta strip become a third full plotting grammar.
- Frame this panel as K562 validation or content-level replication.

**Internal rule**  
`c` shows metric dependence, not K562 validation. The inset keeps only one main metric, with `mean_truth_metric` preferred.

## Caption Lock

**Title line**

> Fig. 5. Boundary audits define the benchmark's bounded claim scope.

**Core legend sentences that must be preserved**

> a, Covariate boundary across HCC38 and HCC1143. Cell shading shows mean target-control Total Variation Distance, whereas glyphs indicate the number of targets exceeding the TVD > 0.25 threshold. Mean TVD did not exceed the hard imbalance threshold, but residual UMI-related target-level exposure constrained fully deconfounded wording.

> b, Endpoint hierarchy across contexts. CRISPR DepMap bridge Spearman exceeded RNAi DEMETER2 bridge Spearman in all four contexts, supporting CRISPR DepMap dependency as the primary endpoint and RNAi DEMETER2 as a weaker cross-platform sensitivity endpoint.

> c, Temporal boundary in the K562 supplementary panel. K562 7d showed stronger rank-bridge alignment, whereas K562 13d showed larger perturbation-shift magnitude, supporting temporal stratification rather than content-level replication.

**Wording boundary that must remain enforced**

- no fully deconfounded wording
- no K562 content-level replication
- no RNAi primary endpoint
- no mechanism-level recovery

---

## Execution Order

1. Lock layout: `a-c` three-panel evidence structure (covariate → endpoint → K562 temporal).
2. Give `b` (endpoint) enough visual width and centrality.
3. Replace all placeholder values in `a/b/c` with source data.
4. Draw `a` as mean TVD + target-level threshold-hit heatmap.
5. Draw `c` in two versions: with and without delta strip.
6. Draw `b` as paired dumbbell, unless readability forces fallback.
7. Save the boundary gate flow separately as overview material for later Figure 1a assembly.
8. Re-check the caption against the locked claim boundary.

---

## Final Internal Execution Rules

1. `a` 讲 residual exposure
2. `b` 讲 endpoint hierarchy
3. `c` 讲 K562 metric dependence / temporal boundary
4. gate flow 只作为 overview 素材另存
5. `a` 的排序服务解释，不服务命名
6. `c` 的 inset 只保留一个主指标
7. `b` 的形式服从清晰，不服从装饰
8. claim scope 放在 caption，不再作为独立 panel
