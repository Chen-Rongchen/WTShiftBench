# Genome Biology 投稿执行计划 v1

## 状态

本计划是当前 Genome Biology 第一版投稿前的执行清单。目标不是扩大 biological discovery，而是降低 reviewer 风险、提高 resource 可审计性，并为 revision round 预装弹药。

执行原则：

- 主叙事固定为 `phenotype-aligned benchmark framework + reproducible resource + architecture-aware adjudication`。
- `baseline beats deep models` 只能作为 backbone-vs-separation trade-off 的一个实例，不作为 headline。
- 第一版投稿不新增 entrant family，不把 K562 升为 co-primary，不重训 GEARS，不扩 Stage 3 discovery。
- 所有新增分析只服务于 artifact 排除、metric sanity check、covariate 边界和 reviewer-proofing。

## A. 投稿前必须完成

### A1. 重写 Title / Abstract / Cover letter framing

状态：完成。

目标：

- Title 明确包含 framework/resource 身份。
- Abstract 前半强调 truth object 与三指标 architecture-aware adjudication。
- Abstract 结果句写成 backbone-vs-separation trade-off。
- shared-mean baseline 只作为 trade-off 中 backbone recovery 的 reference，不作为全文 headline。
- Cover letter 第一段强调 phenotype-aligned adjudication framework，不写成 "deep models fail"。

当前推荐 title：

`A truth-anchored framework and resource for evaluating transcriptomic perturbation models against cancer dependency endpoints`

### A2. prior-art literature scan

状态：完成。

记录文档：`docs/prior_art_literature_scan_v1.md`

目标：

- 系统检查 2024-2026 年 perturbation prediction、single-cell foundation model、benchmark/resource 相关文献。
- 输出一个小表：文献、任务、endpoint、模型、baseline 处理、与本文差异。
- 写作前确认没有遗漏关键 prior art。

最低覆盖：

- Ahlmann-Eltze / Huber / Anders，Nature Methods 2025。
- Wong，Bioinformatics 2025。
- Wei / Wang / Gao 等，Nature Methods 2026。
- Peidli 等 scPerturb，Nature Methods 2024。
- Genome Biology 2025 zero-shot single-cell foundation model benchmark。
- scGPT、Geneformer、scFoundation 原始模型及其 benchmark claims。
- PertBench / PertEval / systematic perturbation prediction benchmark 类工作。
- Replogle 2022 与 dependency / genotype-phenotype landscape 相关工作。

### A3. prior-art positioning 段落

状态：完成。

目标：

- 在 Introduction 或 Discussion 前半主动区分本文与 expression-level perturbation prediction benchmark。
- 明确本文评估对象是 phenotype-relevant fitness bridge，而不是 expression reconstruction。
- 明确本文输出是 architecture-aware trade-off diagnosis，而不是单一 leaderboard 或 unidirectional model failure claim。

### A4. GEARS sweep budget sanity check

状态：完成。

记录文档：`docs/gears_sweep_budget_sanity_check_v1.md`

目标：

- 内部确认实际 sweep config 总数、超参维度、grid 粒度、selection criterion、stop-rule 记录。
- 根据实际规模决定措辞：
  - 若配置数量和维度足够：写成 finite but broad hyperparameter sweep。
  - 若配置数量偏少：写成 predefined finite-budget sweep with explicit stop rule。

### A5. GEARS sweep / stop-rule 透明化写作

状态：完成。

同步位置：

- `docs/main_manuscript_submission_draft_v2.md`
- `docs/genome_biology_manuscript_draft_v1.md`

目标：

- Methods 或 Supplementary 写清 frozen predictions、scoring tables、sweep artifacts 的使用边界。
- 不重训 GEARS。
- 不写 exhaustive search，除非 A4 证明确实可支撑。

### A6. metric orthogonality quick check

状态：完成。

记录目录：`reports/manuscript_metric_diagnostic_v1/`

目标：

- 先计算三指标两两相关性，不急于出图。
- 三个 pair：
  - `backbone_recovery_score` vs `shift_excess_identification_score`
  - `backbone_recovery_score` vs `structure_vs_context_separation_score`
  - `shift_excess_identification_score` vs `structure_vs_context_separation_score`
- 点定义为 entrant x context 或现有 scoring table 中最稳定的同构单位。

决策规则：

- 若相关性大致低到中等：放 Extended Data，支撑三指标分解。
- 若存在中高相关：放 Supplementary，并写成 partially coupled but non-identical signals。
- 若存在高度相关：Methods / Discussion 主动承认 metric coupling，不硬卖 orthogonality。

### A7. metric diagnostic 最终呈现

状态：完成。

呈现口径：Supplementary diagnostic；写成 partially coupled but non-identical architecture signals，不写成 formal proof of orthogonality。

记录报告：`reports/manuscript_metric_diagnostic_v1/metric_diagnostic_report.md`

目标：

- 根据 A6 决定 Extended Data 还是 Supplementary。
- 图中报告 Pearson、Spearman 和 exact n。
- 若样本量小，明确写成 diagnostic，不写成 formal proof of orthogonality。

### A8. shared_mean_baseline leakage / artifact appendix

状态：完成。

记录文档：`docs/shared_mean_baseline_artifact_appendix_v1.md`

建议标题：

`Why the shared-mean baseline is a strong but non-leaking backbone reference`

需要回答：

- shared_mean_baseline 使用了什么信息。
- 它没有使用什么 truth object / endpoint 信息。
- 为什么 truth object 可能包含 shared-structure-dominated 成分。
- baseline backbone 优势不等于 deep models useless，也不等于全指标胜利。

### A9. dixit legacy 澄清

状态：完成。

建议写入 Methods Datasets 段：

`An earlier legacy object distributed under a dixit_2016_raw filename did not match the GSE90063 K562 TF-pool description and was excluded before analysis. All Dixit/K562 evidence in this study was derived de novo from GSE90063 7d and 13d data.`

### A10. Discussion Limitations 四条重写

状态：完成。

必须正面写：

- primary evidence 只来自两个 HCC cell line，shared anchors 有限。
- `barcode_gem_group` 只能作为 design-proxy covariate，不能替代 run-level batch metadata。
- K562 只支持 architecture-form，不支持 content-level replication。
- RNAi DEMETER2 是 cross-platform sensitivity endpoint，不是 matched primary endpoint。

### A11. MANUSCRIPT_REPRODUCIBILITY.md 单入口整理

状态：完成。

入口文档：`MANUSCRIPT_REPRODUCIBILITY.md`

目标：

- 在仓库顶层提供 reviewer-readable 复现入口。
- 连接主图、Extended Data、source data、manifest、frozen claim matrix、scoring tables、configs、legacy exclusion、pixi 重跑命令。
- 可作为 Availability of data and materials 段的引用锚点。

### A12. Top-10 anticipated reviewer questions

状态：完成。

记录文档：`docs/top10_anticipated_reviewer_questions_v1.md`

目标：

- 写一份内部 response rehearsal 文档，不进正文。
- 每个问题准备 1-2 段回答。
- 覆盖 evidence scope、baseline artifact、GEARS sweep、prior art、K562 边界、shift-excess、PFDN5 tier、axis R2、barcode_gem_group、RNAi endpoint。

## B. 强烈建议完成

### B13. 三指标 permutation null

状态：完成。

记录目录：`reports/manuscript_permutation_null_v1/`

说明：target-to-axis permutation 对所有模型完成；因 `shared_mean_baseline` 对 target label permutation 近似不敏感，额外完成 baseline gene-label permutation null。

目标：

- 对 backbone / shift-excess / separation 三指标都做 permutation null。
- 同一套 permutation schema，同一套 entrant/context 单元。
- 输出 observed vs null distribution，并报告 empirical percentile 或 p-value。

### B14. barcode_gem_group design-proxy residualization check

状态：完成。

记录目录：`reports/manuscript_covariate_residualization_v1/`

结论口径：design-proxy rank residualization did not overturn the bridge or primary anchor structure, but HCC1143 shared-anchor residualized Q1 status remained partial and run-level confounding cannot be excluded.

目标：

- 用 `barcode_gem_group` 作为 design-proxy covariate 做 one-shot residualization。
- 重新评估 primary anchor structure 是否被 overturn。
- 只允许写：design-proxy residualization did not overturn the primary anchor structure。
- 仍然禁止写 fully deconfounded。

### B15. relaxed cutoff sensitivity for shared anchors

状态：完成。

记录目录：`reports/manuscript_relaxed_cutoff_sensitivity_v1/`

结论口径：frozen primary shared-anchor set 仍为 4 个；放宽到 2/3 cutoff pairs 为 7 个，放宽到 1/3 cutoff pairs 为 9 个。新增对象只作为 robustness，不提升 claim tier。

目标：

- 保持 frozen Q1 / shared-anchor primary boundary。
- 展示 cutoff 放宽一档、两档后 shared anchor set 数量和核心结构。
- 新增 anchors 只作为 robustness，不提升 claim tier。

### B16. revision round 弹药预装

状态：完成。

记录文档：`docs/revision_round_admission_readiness_v1.md`

目标：

- Frangieh 2021：确认 architecture-form-only admission / feasibility note ready。
- Replogle 2022 K562 CRISPRi：确认 admission contract、cell line mapping、gene namespace、DepMap endpoint mapping 状态。
- 不跑正式分析，不进第一版正文。

## C. 有余力再做

### C17. 最小 community adjudication kit

状态：完成。

实现入口：

- `scripts/manuscript/run_architecture_adjudication.py`
- `configs/manuscript/architecture_adjudication_example_v1.json`
- `docs/community_adjudication_kit_v1.md`

目标：

- 5-7 天硬截止。
- 若能干净完成，提供最小 CLI、example config、toy input / frozen sample、三指标输出和 manifest。
- 若无法在截止内闭环，留到 revision。

## D. 第一版不要做

- 不重训 GEARS。
- 不把 K562 升为 co-primary。
- 不新增 entrant family。
- 不扩 Stage 3 discovery。
- 不强行解决 run-level metadata。
- 不无限扩 axis。
- 不新增 Frangieh / Replogle 正式分析，除非 revision 明确要求。

Revision round 边界：

- 若 reviewer 明确点名要求新增 entrant，可考虑加 1 个 entrant，但必须走 expedited admission，并写成 reviewer-requested sensitivity，而不是 core benchmark expansion。
