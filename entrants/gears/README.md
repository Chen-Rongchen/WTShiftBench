# GEARS entrant recipe

## 当前定位

本目录记录 `gears_k562_smoke_v1` 的冻结边界。它不是“更强 GEARS 训练策略”，而是把当前仓库里已经跑通的最小 GEARS submission 正式化为可审计、可复现、可输出 `predicted_shift` 的 entrant recipe。

## recipe 身份

- `entrant_id`: `gears`
- `entrant_version`: `gears_k562_smoke_v1`
- 数据集范围：`replogle_2022_k562_essential`
- split seed：`101`
- training seed：`123`
- 输出：`data/predictions/stage1a_gears_raw/gears_k562_smoke_v1/replogle_2022_k562_essential/`

## 输入与输出

- 输入源：`data/processed/stage1a/formal_filtered/replogle_2022_k562_essential.h5ad`
- GEARS 输入准备：保留单细胞 AnnData 输入，并按当前 helper 构造 perturbation graph 与 custom split。
- 模型输出：先得到 perturbation-level predicted expression。
- contract 导出：在 adapter 内减去共享 control pseudobulk，得到 `predicted_shift.tsv.gz`。

## provenance 最少字段

`provenance.json` 会记录：数据集、split seed、control 定义、graph prior 来源、输入空间、checkpoint/weights 身份、adapter 身份、代码版本与运行环境。

## 兼容性说明

旧的 `scripts/build_stage1a_gears_k562_predictions.py` 仍可保留作为历史入口；新的正式入口统一切到 `scripts/run_stage1a_entrant.py`。
