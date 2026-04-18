# Genome Biology preprint role audit v1

## 状态

更新日期：2026-04-18。

用途：判断正式 References 是否需要保留 preprint。结论是第一版 Genome Biology 投稿正文中不保留非必要 preprint；相关工作可保留在内部 prior-art / rebuttal 准备文档中。

## 审计原则

每条 preprint 按三个问题判断：

- 是否承担主论证功能。
- 删除后是否破坏主论证闭环。
- 是否有正式发表文献可替代其背景功能。

## Li et al. systematic comparison preprint

角色：

- perturbation prediction landscape / systematic comparison 背景。
- 不承担本文核心 differentiation。

判断：

- 删除后不影响主论证闭环。
- Ahlmann-Eltze 2025、Wong 2025、Wei et al. 2026 和 Genome Biology 2025 foundation-model benchmark 已足以支撑 prior-art positioning。

处理：

- 从正式 References 草案中移除。
- 保留在 `docs/prior_art_literature_scan_v1.md` 和 `docs/genome_biology_reference_formatting_queue_v1.md` 作为可选 prior-art / rebuttal 弹药。

## Dempster et al. Project Achilles preprint

角色：

- DepMap / Project Achilles 背景。
- 不承担本文 CRISPR endpoint 的唯一依据。

判断：

- 删除后不影响主论证闭环。
- Meyers et al. 2017 可支撑 CRISPR-Cas9 dependency screen correction / CERES 背景。
- 正式数据来源、accession 与 repository / DOI 将在 Availability of data and materials 中补齐，适合承载 dataset provenance，而不是依赖 preprint 背景文献。

处理：

- 从正式 References 草案中移除。
- 保留在内部 reference queue 作为可选背景，不进入第一版正文，除非作者明确要求。

## 当前正式正文 References

当前 `docs/genome_biology_manuscript_draft_v1.md` 正文保留 13 条正式或正式期刊文献：

- Perturb-seq / scPerturb resources。
- GEARS / scGPT / Geneformer / scFoundation model background。
- Ahlmann-Eltze / Wong / Wei / Genome Biology 2025 prior-art positioning。
- CERES / DepMap CRISPR correction。
- DEMETER2 RNAi endpoint。

## 剩余人工确认

- 如果作者希望最大化 literature coverage，可以在 revision 或 rebuttal 中重新引用 Li et al.。
- 如果投稿系统要求 dataset citation 与 public repository 同步，应以最终 archive DOI / accession 为主。
