# Figure 5 Redesign — Final Claim Boundary Freeze Spec

**状态**：2026-04-25 更新。当前投稿结构采用 5 张主图。

**当前 Figure 5 身份**：原 Figure 6 前移为主文 Figure 5，作为最终 claim boundary 图。

**原 Figure 5 身份**：axis-level interpretation 已下放为 Extended Data Fig. 11；原 Extended Data Fig. 6 保持 full axis annotation / bootstrap support，不被覆盖。

---

## Locked Boundaries

**Figure 5 title**

> Covariate, temporal and endpoint boundaries define the final benchmark scope.

**Panel count**

4 panel（a-d），对应当前 `src/wtbench/manuscript/figure6_boundary.py` 的 boundary 图输出。

**Output location**

- 投稿主图：`manuscript/figures/Figure_5/Figure_5.{png,pdf}`
- Panel 输出：`manuscript/figures/Figure_5/panels/Figure_5_panel_{a..d}.{png,pdf}`
- 开发输出：`reports/manuscript_figures_v2/fig6_boundary/figure6.{png,pdf}`

**Old output cleanup**

`manuscript/figures/Figure_6/` 已从投稿主图目录移除，避免出现第六张主图。

---

## Panel Inventory

| Panel | Short id | Purpose |
|---|---|---|
| a | Boundary architecture | Define the three boundary layers that jointly cap the final claim. |
| b | Covariate boundary | Show covariate imbalance evidence that blocks fully deconfounded wording. |
| c | Temporal and endpoint hierarchy boundary | Combine K562 temporal stratification with CRISPR-vs-RNAi endpoint hierarchy. |
| d | Final claim boundary | State allowed and disallowed claims in one ledger. |

---

## Cross-References

- Axis-level adjudication is now Extended Data Fig. 11.
- Full axis annotation and bootstrap support remain Extended Data Fig. 6.
- Temporal details remain Extended Data Fig. 7.
- Endpoint details remain Extended Data Fig. 8.
- Covariate audit details remain Extended Data Fig. 9.

---

## Wording Boundary

Allowed:

- CRISPR DepMap dependency is the primary bridge readout for the HCC38/HCC1143 benchmark contexts.
- K562 temporal evidence supports architecture-form recurrence but not content-level replication.
- RNAi DEMETER2 is a weaker cross-platform sensitivity endpoint.

Not allowed:

- Fully deconfounded architecture.
- Content-level replication in K562.
- RNAi as primary readout.
- Mechanism-level recovery.
