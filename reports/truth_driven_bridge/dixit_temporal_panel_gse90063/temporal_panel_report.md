# GSE90063 K562 13d/7d temporal panel

## 定位

`13d` 是 primary formal supplementary bridge test；`7d` 是 temporal sensitivity / early-bridge probe。该 panel 只回答同一 K562 TF pool 外部 context 下，早期与后期接同一 DepMap endpoint 时 bridge / architecture 轮廓如何变化；它不支持 primary closure 或 external model-side generalization proved。

## 项目对象层 target 口径

在当前项目对象层与现行 admission/bridgeability 规则下，`7d` 与 `13d` 目前各有 10 个正式 bridgeable targets 进入 DepMap 对接；这一数字不应与原始实验设计中的 target / guide 数直接等同。

正式 bridgeable targets：`CREB1 / E2F4 / EGR1 / ELF1 / ELK1 / ETS1 / GABPA / IRF1 / NR2C2 / YY1`。

## Primary temporal readout

- `13d`：`real_shift_mean_abs` vs `depmap_gene_dependency` aligned Spearman = `0.515`；mean shift = `0.004383`；n targets = `10`。
- `7d`：`real_shift_mean_abs` vs `depmap_gene_dependency` aligned Spearman = `0.733`；mean shift = `0.003099`；n targets = `10`。

## Panel call

- rank bridge call: `rank_bridge_not_stronger_at_13d`
- mean shift call: `mean_shift_stronger_at_13d`

## Architecture form

- `7d` `canonical backbone present`: `True` (`CONFIRMED`)
- `7d` `shift-excess present`: `True` (`CONFIRMED`)
- `7d` `architecture class`: `backbone_plus_shift_excess` (`CONFIRMED`)
- `13d` `canonical backbone present`: `True` (`CONFIRMED`)
- `13d` `shift-excess present`: `True` (`CONFIRMED`)
- `13d` `architecture class`: `backbone_plus_shift_excess` (`CONFIRMED`)

## 产物

- `temporal_bridge_summary.tsv`
- `temporal_target_delta.tsv`
- `temporal_structure_summary.tsv`
- `temporal_panel_calls.tsv`
