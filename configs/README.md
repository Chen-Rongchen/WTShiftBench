# configs 目录说明

## 1. 当前职责

`configs/` 保存当前 truth-first 主线的 machine-readable 入口配置。近端维护对象集中在：

- `configs/stage2/*.json`：Stage 2 truth bridge、covariate audit、model recovery adjudication、Dixit supplementary replication 与 axis validation。
- `configs/stage2/checkpoint_registry_v1.yaml`：Stage 2 仍需读取的 scGPT / Geneformer checkpoint registry。
- `configs/stage2/feature_registry_v1.json`：Stage 2 linear control 使用的 target-side feature registry。
- `configs/runtime/wtbench_cli_v1.json`：`python -m wtbench` / `pixi run --environment core wtbench` 使用的动态命令注册表。
- `configs/runtime/wtbench_cli.schema.json`：统一 CLI 注册表的结构说明。
- `configs/manuscript/*.json`：论文图、Extended Data、supplementary tables 与 submission package 生成配置。

旧 `configs/stage1a/`、旧 `configs/entrants/` 与 Stage 1A formal/split/prediction contract 配置已从当前工作树清理。原始数据保留在 `data/raw`；不再使用的处理后数据与旧预测缓存已删除。

## 2. Stage 2 关键配置

- `stage2/truth_driven_bridge_hcc38_hcc1143_v1.json`：HCC 主线 truth-driven bridge 配置。
- `stage2/rnai_demeter2_conversion_v1.json`：DEMETER2 RNAi 分数转 DepMap endpoint 宽表的转换配置。
- `stage2/truth_driven_bridge_dixit_k562_supplement.json`：Dixit/K562 supplementary truth bridge 的默认配置，当前固定指向 `GSE90063 K562 TF pool 13d-only`。
- `stage2/truth_driven_bridge_dixit_k562_tf_{13d,7d}_gse90063_v1.json`：GSE90063 分时间点的显式冻结配置；其中 `13d` 为 primary formal supplementary bridge test，`7d` 为 temporal sensitivity / early-bridge probe。
- `stage2/truth_driven_bridge_dixit_k562_tf_7d_gse90063_rnai_demeter2_v1.json`：GSE90063 K562 7d CRISPR KO truth 接 DEMETER2 RNAi endpoint 的 temporal sensitivity 对照配置。
- `stage2/truth_driven_bridge_dixit_k562_tf_13d_gse90063_rnai_demeter2_v1.json`：GSE90063 K562 13d CRISPR KO truth 接 DEMETER2 RNAi endpoint 的 cross-platform sensitivity 对照配置。
- `stage2/k562_rnai_endpoint_consistency_v1.json`：GSE90063 K562 7d/13d 的 CRISPR DepMap vs DEMETER2 RNAi endpoint consistency 汇总配置。
- `stage2/truth_driven_bridge_dixit_k562_legacy_v1.json`：历史 Dixit lineage 的 historical-only truth bridge 配置。
- `stage2/gse90063_k562_tf_{13d,7d}_materialization_v1.json`：GSE90063 K562 TF pool 物化配置（原始 mtx/csv -> h5ad）。
- `stage2/truth_driven_bridge_dixit_k562_tf_{13d,7d}_gse90063_v1.json`：GSE90063 13d/7d 分时间点 truth bridge 配置。
- `stage2/dixit_axis_compression_v1.json`：Dixit supplementary axis compression 的默认配置，当前固定指向 `GSE90063 K562 TF pool 13d-only`。
- `stage2/dixit_k562_tf_{13d,7d}_structure_replication_gse90063_v1.json`：GSE90063 13d/7d 分时间点 axis compression / claim tier 配置。
- `stage2/dixit_k562_temporal_panel_gse90063_v1.json`：GSE90063 K562 13d/7d temporal panel 汇总配置；只组织同一外部 context 下的 temporal comparison，不改变 `13d` / `7d` 的主张层级。
- `stage2/dixit_axis_compression_legacy_v1.json` 与 `stage2/dixit_k562_structure_replication_legacy_v1.json`：历史 Dixit lineage 的 historical-only axis compression 配置。
- `stage2/hcc_prediction_contract_v1.json`：真实 HCC 预测 contract。
- `stage2/gears_hcc_formal_v1.json`：GEARS HCC formal recipe。
- `stage2/scgpt_hcc_formal_v1.json`：scGPT HCC formal recipe。
- `stage2/geneformer_hcc_formal_v1.json`：Geneformer HCC formal recipe。
- `stage2/lm_train_lowrank_hcc_formal_v1.json`：symbol chargram linear low-rank control。
- `stage2/lm_g_scgpt_ridge_hcc_formal_v1.json`：scGPT embedding ridge control。
- `stage2/lm_g_geneformer_ridge_hcc_formal_v1.json`：Geneformer embedding ridge control。
- `stage2/truth_bridge_covariate_audit_v1.json`：HCC covariate audit 配置。
- `stage2/truth_bridge_sensitivity_hcc_full_v1.json`：HCC formal closure 默认 sensitivity 配置，含 5 条 covariate 轴。
- `stage2/stage2_closure_pipeline_v1.json`：Stage 2 closure pipeline 总配置，串联 covariates 物化、sensitivity 与 covariate audit。
- `stage2/closure_artifact_validation_v1.json`：Stage 2 closure 关键 TSV / 文档边界的轻量校验配置。
- `stage2/axis_validation_summary_v1.json`：axis validation summary 配置。

## 3. Manuscript / submission package 配置

- `manuscript/main_figures_v2.json`：当前主文 Fig. 1-Fig. 5 的生成配置。
- `manuscript/extended_data_figures_v1.json`：当前 Extended Data Fig. 1-Fig. 5 的生成配置。
- `manuscript/supplementary_tables_v1.json`：supplementary table group 与冻结来源文件索引配置。
- `manuscript/submission_package_v1.json`：Genome Biology submission package manifest 与 Supplementary Tables workbook 生成配置。

## 4. 维护原则

- 新 recipe 优先使用 JSON。
- 少数现有代码已经固定读取 YAML 的 registry 可以保留 YAML，但只用于 registry，不再扩展成长参数表。
- 跨数据集批量运行参数写入 `configs/**/*.json`，脚本只负责加载、物化和执行。
- 新增主链路 CLI 时优先注册到 `configs/runtime/wtbench_cli_v1.json`，不要在统一入口里硬编码长命令表。
- 注册表中的 callable 必须是 `module:function` 格式，且函数签名保持 `function(config_path: Path)`。
- 不把 supplementary dataset role 写成 primary mainline。
- `Dixit/K562` 的泛名默认配置固定指向 `13d`，不再默认指向 legacy lineage。
- `Dixit/K562` temporal panel 配置必须保持 `13d = primary formal supplementary bridge test`、`7d = temporal sensitivity / early-bridge probe`。
- 不把 discovery 提前写成当前配置层的 primary deliverable。
- 不把 enrichment 单独写成 axis discovery 的主证据；axis analysis 配置默认只服务 annotation 与 validation。

## 5. 与 pixi 的对应关系

当前推荐把下面几份配置视为 `pixi run --environment core` 的默认执行入口：

- `stage2/stage2_closure_pipeline_v1.json`：对应 `run-stage2-closure-pipeline`
- `stage2/rnai_demeter2_conversion_v1.json`：对应 `convert-rnai-demeter2-depmap-endpoints`
- `stage2/truth_driven_bridge_dixit_k562_tf_7d_gse90063_rnai_demeter2_v1.json`：对应 `build-stage2-truth-driven-bridge-k562-7d-rnai-demeter2`
- `stage2/truth_driven_bridge_dixit_k562_tf_13d_gse90063_rnai_demeter2_v1.json`：对应 `build-stage2-truth-driven-bridge-k562-13d-rnai-demeter2`
- `stage2/k562_rnai_endpoint_consistency_v1.json`：对应 `run-stage2-k562-rnai-endpoint-consistency`
- `stage2/truth_bridge_sensitivity_hcc_full_v1.json`：对应 `run-stage2-truth-bridge-sensitivity-hcc-full`
- `stage2/truth_bridge_covariate_audit_v1.json`：对应 `run-stage2-covariate-audit`
- `stage2/truth_driven_bridge_dixit_k562_supplement.json`：对应 `build-stage2-truth-driven-bridge-dixit-supplement`
- `stage2/dixit_axis_compression_v1.json`：对应 `run-stage2-dixit-axis-compression`
- `stage2/dixit_k562_temporal_panel_gse90063_v1.json`：对应 `run-stage2-dixit-temporal-panel`
- `stage2/closure_artifact_validation_v1.json`：对应 `validate-stage2-closure-artifacts`
- `manuscript/figure1_truth_object_v1.json`：对应 `render-manuscript-figure1`
- `manuscript/main_figures_v2.json`：对应 `python scripts/manuscript/build_all_main_figures.py`
- `manuscript/extended_data_figures_v1.json`：对应 `python scripts/manuscript/build_all_extended_data_figures.py`
- `manuscript/supplementary_tables_v1.json`：对应 `python scripts/manuscript/build_supplementary_table_index.py`
- `manuscript/submission_package_v1.json`：对应 `python scripts/manuscript/build_submission_package.py`
