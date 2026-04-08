# Stage 2 Truth-Driven Bridge v1

## 目标

先验证 `HCC38` 与 `HCC1143` 的真实 14d genetic perturbation transcriptomic truth，是否能桥接到同 cell line 的 `DepMap gene effect / gene dependency`。

这一版只做 truth-side bridge，不引入任何 entrant predicted shift。

## 方法定位与措辞边界

- 本文所说的「合理」，均指 **对 Stage 2 truth-driven bridge 任务合理**：在定义 **target-level、可冻结、可审计的 bridge object**，而非追求泛用场景下的「最佳单细胞全流程」或「最复杂 normalization」。
- **Pooled intergenic control（v1 边界语）**：v1 使用 pooled intergenic controls 作为统一参照，以保证 target-level truth 定义简洁一致；该定义默认 target 与 control 间 **不存在主导性的技术构成偏差**，后续将通过 **matched / stratified control** 等敏感性分析评估其稳健性。

## 默认入口

- 主线配置（肝癌两条线）：`configs/stage2/truth_driven_bridge_hcc38_hcc1143_v1.json`
- **与主线相同 filters/metrics**、且并入 **Dixit**（h5ad）的配置：`configs/stage2/truth_driven_bridge_hcc38_hcc1143_dixit_v1.json` — 产出写入 **同一** `data/processed/stage2_truth_driven_bridge` 与 `reports/stage2_truth_driven_bridge`，并多出 `dixit_2016_raw__control_context` 子目录；跨线一致性为 **逐对** inner join（三数据集时共三对）。
- CLI：`scripts/build_stage2_truth_driven_bridge.py --config <上述 JSON>`
- `pixi`：`build-stage2-truth-driven-bridge`（主线） / `build-stage2-truth-driven-bridge-with-dixit`（含 Dixit）
- supplementary `dixit`（K562 / `ACH-000551`）配置：`configs/stage2/truth_driven_bridge_dixit_k562_supplement.json`；formal-like 自 `data/raw/stage1a/candidates/dixit_2016_raw.h5ad` 经 `scripts/build_stage1a_candidate_formalization.py`（`dixit_context` + `subset_condition: Control`）写出，含 **NO_SITE / non-gene** 等对照（`is_control`）与单扰动细胞；**勿与 HCC 主线并列作主结论**，仅 supplement。

## 关键实现约定

- 主键固定为 `cell_line × target_gene`
- 只使用 `num_features == 1` 的单扰动细胞
- `intergenic_chr_*` 固定作为同 cell line control proxy
- `HCC38` 与 `HCC1143` 先各自独立汇总，再做跨 cell line 一致性
- `gene effect` 与 `gene dependency` 并列输出，不预设单一主轴
- 当前实现同时支持两类 truth 源：
  - `mtx_protospacer`
  - `h5ad_obs`

## 主要输出

- `data/processed/stage2_truth_driven_bridge/<cell_line>/target_level_bridge_table.tsv.gz`
- `data/processed/stage2_truth_driven_bridge/combined_target_level_bridge_table.tsv.gz`
- `reports/stage2_truth_driven_bridge/<cell_line>/bridge_audit.tsv`
- `reports/stage2_truth_driven_bridge/<cell_line>/correlation_summary.tsv`
- `reports/stage2_truth_driven_bridge/<cell_line>/group_comparison_summary.tsv`
- `reports/stage2_truth_driven_bridge/cross_cell_line_consistency_summary.tsv`
- `reports/stage2_truth_driven_bridge/stage2_truth_driven_bridge_report.md`

## 指标说明

**证据等级（写结果时勿四指标平行陈列，避免证据强度被误读为相同）**

| 等级 | 指标 | 角色 |
|------|------|------|
| 主支柱 | `real_shift_L2`、`real_shift_mean_abs` | 转录位移强度的直接、稳健摘要 |
| 补充支柱 | `real_Edistance` | 分布层面 complement（不只看均值） |
| 敏感性 / 辅助 | `real_DEG_burden` | 依赖阈值，宜作敏感性或补充，**不当主桥主证据** |

**定义**

- `real_shift_L2`：target mean shift 的 L2 范数
- `real_shift_mean_abs`：target mean shift 的逐基因绝对值均值
- `real_Edistance`：target cells 与 control cells 在 log-normalized expression SVD embedding 上的 energy distance
- `real_DEG_burden`：满足表达下限且 `abs(delta)` 超过阈值的基因数

## mtx_protospacer 路径：矩阵方向与归一化（一次性约定）

在 `mtx_protospacer` 路径中，原始矩阵为 **feature × cell**；经 gene filtering 与 barcode 对齐后 **转置为 cell × gene**，后续 **library normalization 沿细胞维（行）** 施加；target / control 的 **逐基因均值** 沿 **基因维** 以 **跨细胞** 方式计算（即对行集合取 `mean(axis=0)` 得到基因向量，再作差得到 `delta`）。`h5ad_obs` 路径中 `adata.X` 与 obs 行对齐，同为 **cell × gene**，归一化与均值约定一致。

## 敏感性分析（已实现）

- 配置：`configs/stage2/truth_bridge_sensitivity_v1.json`
- CLI：`scripts/run_stage2_truth_bridge_sensitivity.py`
- `pixi` 任务：`run-stage2-truth-bridge-sensitivity`

**内容**

1. **Control 无放回子抽样**：默认 `subsample_size = min(500, n_control)`（可在配置中覆盖），重复 `n_replicates` 次；每次重算 truth 与 DepMap 相关，汇总 `spearman_aligned` 的均值与分位数；并对各 truth 指标输出 **与全量 control 基线的秩相关**（`spearman_rank_vs_baseline`）。
2. **DEG 阈值扫描**：对 `deg_abs_log1p_delta_threshold` 列表重算 `real_DEG_burden` 与 `depmap_gene_effect` 的 aligned Spearman（不改变 shift / E-distance）。
3. **可选协变量审计**：在配置中按 `cell_line` 提供 `covariates`（TSV：`cell_barcode` + 分层列），输出各 target 与 control 在该分层上的 **total variation distance**；无外部 metadata 时可为空。

**输出目录**：`reports/stage2_truth_driven_bridge/sensitivity/`（`control_subsample_*.tsv`、`deg_threshold_sweep.tsv`、可选 `covariate_balance/`）。

**性能**：每个 cell line 只做 **一次** `prepare_bridge_inputs`（含 SVD）；总耗时仍随 `n_replicates` 与 target 数近似线性增长，完整配置可能需数十分钟量级，属预期。

### 敏感性结果的判读边界（写作时必守）

1. **重复次数与不确定性表述**  
   `n_replicates` 很少（例如仅 **2**）时，只支持定性结论：**在 limited subsampling replicates 下未见明显不稳**；**不足以**支撑严格的 **95% 区间**或很正式的 **分位数/不确定性量化**。若 supplement 需要可引用的区间表，应使用配置中 **`n_replicates` 跑满（例如 24）** 后的 `control_subsample_summary.tsv`。

2. **Control 子抽样在方法学上回答什么、不回答什么**  
   子抽样检验的是：在 **同一 pooled intergenic control 池** 内，随机改变 control 子集规模/组成时，bridge 指标与排序是否稳健。它 **不等于** 已排除 **batch / lane / capture** 等系统性构成偏差——若整池 control 与某些 target 在技术协变量上 **整体不匹配**，子抽样仍从该池抽取，**不一定能发现**该问题。  
   因此 **covariate balance（协变量分层审计）仍是剩余风险**，需通过 **独立提供的 covariates TSV** 单独审；未审计前 **不应写成「batch 问题已关闭」**。

3. **DEG 阈值扫描与 cherry-picking**  
   若出现 **阈值非单调**（例如 HCC38 上），提示 **按阈值挑最强相关** 有 cherry-picking 风险。写作须坚持：**bridge 主表所用阈值在分析前已由主线配置固定**；扫描结果仅用于说明敏感性，**不得**改口成「选用表现最好的阈值」。更稳妥的表述示例：  
   *在 HCC38 中，`real_DEG_burden` 与 DepMap 的桥接强度对阈值较敏感，故该指标仅作辅助分析，不用于定义主桥接结论。*

### 项目层面判断（可压缩进讨论/附录导语）

当前敏感性分析表明：Stage 2 **主桥接信号**对 pooled control 的 **随机子抽样**具有 **较高稳健性**，尤其是 **shift-based truth** 与 **E-distance** 在 target **排序**层面几乎不受影响；相比之下，**DEG burden** 对 control 子抽样与 **阈值设定**更敏感，**支持**其作为 **辅助而非主支柱** 的预设定位。现阶段 **剩余的主要方法学风险**不在于「主桥接是否成立」，而在于 **pooled control 与 target 的技术构成偏差**尚未通过 **协变量分层审计**被正式关闭。

### 后续工作（优先序）

1. 以 **`n_replicates` 跑满（如 24）** 完成 control subsampling，为 supplement 提供 **可正式引用** 的区间/分位数版本。  
2. 补齐 **batch/lane 等 covariates TSV**，运行 `covariates` 审计，将 **构成偏差**从「剩余风险」推进 **可报告**。

主线仍以 v1 提取为准；若需 **按 batch 的 stratified control mean** 等更重方案，可在同一输出目录下扩展脚本，而不改默认 bridge 表定义。

## 渐进披露

默认先看：

1. `stage2_truth_driven_bridge_report.md`
2. 每个 cell line 的 `correlation_summary.tsv`
3. `cross_cell_line_consistency_summary.tsv`

需要更细时，再下钻到 `target_level_bridge_table.tsv.gz` 与各类 audit 表。
