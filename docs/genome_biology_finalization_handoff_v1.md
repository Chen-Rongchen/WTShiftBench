# Genome Biology finalization handoff v1

## 状态

更新日期：2026-04-20。

本文档只记录 A/B/C reviewer-risk reduction 完成后的投稿收口事项。它不新增分析任务，也不改变 frozen claim boundary。

当前投稿前单入口工作区已经整理完成：

- `manuscript/README.md`
- `manuscript/file_index.txt`

该目录包含 610 个文件，约 22 MB；主图、Extended Data、panel a-h、source data、manifest、Additional files 和 audit 文档均已集中到一个工作区。整理提交为 `b335d2c Organize Genome Biology manuscript workspace`。

## 当前已冻结

- 主投期刊：Genome Biology。
- 文章身份：framework / resource / benchmark Research article。
- 主标题：`A truth-anchored framework and resource for evaluating transcriptomic perturbation models against cancer dependency endpoints`
- 主叙事：phenotype-aligned truth object + architecture-aware adjudication + reproducibility package。
- 模型侧结论：backbone-vs-separation trade-off，而不是 simple baseline wins headline。
- 证据边界：HCC primary evidence limited to HCC38 / HCC1143；K562 only supplementary architecture-form；RNAi DEMETER2 only cross-platform sensitivity endpoint。

## 已完成并版本化

当前 reviewer-risk reduction 版本：

- commit：`174c809 Prepare Genome Biology submission readiness docs`
- manuscript workspace commit：`b335d2c Organize Genome Biology manuscript workspace`

完成项：

- A1-A12：投稿前必须项全部完成。
- B13-B16：强烈建议项全部完成。
- C17：最小 community adjudication kit 完成并跑通。

核心入口：

- `manuscript/README.md`
- `manuscript/text/manuscript_draft_v1.md`
- `manuscript/text/figure_legends_v1.md`
- `manuscript/source_data_manifests/submission_package_manifest.json`
- `docs/manuscript_hardening_plan_v1.md`
- `docs/genome_biology_submission_execution_plan_v1.md`
- `manuscript/source_data_manifests/MANUSCRIPT_REPRODUCIBILITY.md`
- `docs/genome_biology_submission_checklist_v1.md`
- `docs/submission_readiness_checklist_v1.md`
- `docs/top10_anticipated_reviewer_questions_v1.md`
- `docs/community_adjudication_kit_v1.md`
- `docs/genome_biology_figure_text_audit_v1.md`
- `docs/genome_biology_final_wording_audit_v1.md`
- `docs/genome_biology_word_count_v1.md`
- `docs/genome_biology_preprint_role_audit_v1.md`
- `docs/genome_biology_submission_final_index_v1.md`

## 下一步只做投稿格式收口

### 0. Manuscript hardening

当前稿件应视为 strong editorial draft，而不是最终 submission-ready 版本。下一轮先按 `docs/manuscript_hardening_plan_v1.md` 执行：

- 修正 HCC38/HCC1143 是乳腺癌细胞系这一身份表述，移除 `HCC = hepatocellular carcinoma` 和单独 `HCC context` 的投稿文本用法。
- 把文章主语固定为 framework/resource，而不是 model leaderboard。
- 补齐 public repository / archive DOI / declarations 等 submission blocker。
- 将 Methods 扩到 operational definition 级，包括 shift、dependency alignment、grid bin、三指标、baseline、tiering、bootstrap 和 permutation null。
- 降档两处 interpretation-level overclaim：GEARS gap 解释和 baseline/canonical-backbone 解释。

### 1. 作者与 declarations

需要人工补齐：

- 作者姓名。
- 作者单位。
- 通讯作者姓名与邮箱。
- Funding。
- Competing interests。
- Authors' contributions。
- Acknowledgements。
- Public repository / archive DOI。
- AI use statement 是否保留与最终措辞。

当前占位位置：

- `docs/genome_biology_manuscript_draft_v1.md`

### 2. References

需要整理为 Genome Biology 格式。

当前整理队列：

- `docs/genome_biology_reference_formatting_queue_v1.md`

当前状态：

- 正式 References 草案已插入 `docs/genome_biology_manuscript_draft_v1.md`。
- 正文 Background 已加入编号引用。
- 两个非必要 preprint 已从正式 References 草案中移除。
- 仍需作者确认是否恢复任何 preprint 引用。

必查 reference 组：

- perturbation baseline / benchmark prior art。
- scPerturb / perturbation dataset resource。
- scGPT / Geneformer / scFoundation 等模型背景。
- GEARS 原始方法。
- DepMap / DEMETER2 / Replogle / GSE90063 相关数据来源。
- 本文复现、source-data 或 manifest 需要引用的软件包。

注意：

- Ahlmann-Eltze / Huber / Anders 应按 Nature Methods 2025 记录，不写 2024。
- preprint 如 PerturbArena / systematic comparison 类工作必须标注 preprint status。

### 3. Additional files

当前说明文档：

- `docs/genome_biology_additional_files_v1.md`

当前上传 staging 目录：

- `manuscript/additional_files/`

建议编号：

- Additional file 1：`manuscript/additional_files/Additional_file_1_supplementary_tables_v1.xlsx`
- Additional file 2：`manuscript/additional_files/Additional_file_2_submission_package_manifest.json`
- Additional file 3：`manuscript/additional_files/Additional_file_3_submission_package_file_manifest.tsv`

需要最终确认：

- Genome Biology 是否接受当前 `xlsx + json + tsv` 组合。
- Additional files 文件名是否需要重命名为期刊系统要求的 `Additional file 1` 样式。
- source data 是否作为 figure source data 单独上传，还是作为 Additional file 汇总上传。

当前文件大小：

- `supplementary_tables_v1.xlsx`：约 103 KB。
- `submission_package_manifest.json`：约 215 KB。
- `submission_package_file_manifest.tsv`：约 112 KB。

三者均低于 BMC Additional file 20 MB 单文件上限。

当前状态：

- Submission package 已在 Nature Methods 风格重绘后重建。
- Additional files staging 目录已刷新。
- `docs/genome_biology_additional_files_v1.md` 已更新最新 SHA256。

### 4. 图文一致性

最终人工检查：

- 正文中 Fig. 1-5 引用顺序。
- Extended Data Fig. 1-11 引用顺序。
- Figure legends 与 panel source data 一致。
- 数字是否与 source data 一致，尤其是 backbone 0.807 / GEARS 0.660 / separation 0.428 vs 0.353。
- `K562`、`RNAi DEMETER2`、`barcode_gem_group`、`GEARS sweep` 的 wording 不越界。

### 5. 不再做

第一版投稿前不做：

- 不重训 GEARS。
- 不新增 entrant family。
- 不把 K562 升级为 co-primary。
- 不把 RNAi DEMETER2 写成 matched primary endpoint。
- 不新增 Frangieh / Replogle 正式分析。
- 不扩 Stage 3 discovery。
- 不重开 HCC truth contract。

## 提交前最后检查命令

```bash
git status --short
PYTHONPATH=src python -m compileall scripts/manuscript/run_architecture_adjudication.py
PYTHONPATH=src python scripts/manuscript/run_architecture_adjudication.py --config configs/manuscript/architecture_adjudication_example_v1.json
```

若需要重建完整投稿包，再运行：

```bash
pixi run --environment core python scripts/manuscript/build_all_main_figures.py
pixi run --environment core python scripts/manuscript/build_all_extended_data_figures.py
pixi run --environment core python scripts/manuscript/build_supplementary_table_index.py
pixi run --environment core python scripts/manuscript/build_submission_package.py
```
