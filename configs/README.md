# configs 目录说明

## 1. 当前职责

`configs/` 保存当前 truth-first 主线的 machine-readable 入口配置。近端维护对象集中在：

- `configs/stage2/*.json`：Stage 2 truth bridge、covariate audit、model recovery adjudication、Dixit supplementary replication 与 axis validation。
- `configs/stage2/checkpoint_registry_v1.yaml`：Stage 2 仍需读取的 scGPT / Geneformer checkpoint registry。
- `configs/stage2/feature_registry_v1.json`：Stage 2 linear control 使用的 target-side feature registry。
- `configs/manuscript/*.json`：论文图生成配置。

旧 `configs/stage1a/`、旧 `configs/entrants/` 与 Stage 1A formal/split/prediction contract 配置已从当前工作树清理。原始数据保留在 `data/raw`；不再使用的处理后数据与旧预测缓存已删除。

## 2. Stage 2 关键配置

- `stage2/truth_driven_bridge_hcc38_hcc1143_v1.json`：HCC 主线 truth-driven bridge 配置。
- `stage2/truth_driven_bridge_dixit_k562_supplement.json`：Dixit/K562 supplementary external structure replication 配置。
- `stage2/hcc_prediction_contract_v1.json`：真实 HCC 预测 contract。
- `stage2/gears_hcc_formal_v1.json`：GEARS HCC formal recipe。
- `stage2/scgpt_hcc_formal_v1.json`：scGPT HCC formal recipe。
- `stage2/geneformer_hcc_formal_v1.json`：Geneformer HCC formal recipe。
- `stage2/lm_train_lowrank_hcc_formal_v1.json`：symbol chargram linear low-rank control。
- `stage2/lm_g_scgpt_ridge_hcc_formal_v1.json`：scGPT embedding ridge control。
- `stage2/lm_g_geneformer_ridge_hcc_formal_v1.json`：Geneformer embedding ridge control。
- `stage2/truth_bridge_covariate_audit_v1.json`：HCC covariate audit 配置。
- `stage2/axis_validation_summary_v1.json`：axis validation summary 配置。

## 3. 维护原则

- 新 recipe 优先使用 JSON。
- 少数现有代码已经固定读取 YAML 的 registry 可以保留 YAML，但只用于 registry，不再扩展成长参数表。
- 跨数据集批量运行参数写入 `configs/**/*.json`，脚本只负责加载、物化和执行。
- 不把 supplementary dataset role 写成 primary mainline。
- 不把 discovery 提前写成当前配置层的 primary deliverable。
- 不把 enrichment 单独写成 axis discovery 的主证据；axis analysis 配置默认只服务 annotation 与 validation。
