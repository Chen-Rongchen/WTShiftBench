# Final Claim Matrix

## 文档定位

这份表不是新结果报告。

它只做一件事：

**把当前项目里哪些对象还能写、能写多强、哪些绝对不能写，统一压成一张 claim governance 表。**

## 当前使用原则

- 以后主文稿、README、summary、supplementary 的对象级口径，都应优先从 [`final_claim_matrix.tsv`](/home/data/gz0705/WTKO/reports/truth_driven_bridge/sensitivity/final_claim_matrix.tsv) 取值
- 若对象不在表中，不默认升级措辞
- 若后续有新 covariate 元数据，先更新这张表，再改主文稿表述

当前还需要额外固定一条同步纪律：

- 新版 `covariate_balance` 正式重跑若只是在边界上“坐实风险仍未关闭”，而没有改变对象级 tier，就不改写这张表的 tier，只继续同步相关 manuscript wording
- 对 `barcode_gem_group` 这条轴，默认沿用 `design-proxy axis` 口径；在没有新的 HCC run-level metadata 前，不再继续追写单个 `MH00x` 映射

## 当前最关键的三条

- `global_truth_depmap_bridge`
  - 当前可保留为 `retainable_global_claim`
- `barcode_gem_group_design_proxy`
  - 当前只可保留为方法学边界层的 `design-proxy axis`
- `PFDN5`
  - 当前可保留为 `primary_but_qualified`
- `PMF1 / PRPF6 / ZNF131`
  - 当前只保留为 `supporting_only`

## K562 13d/7d 补充说明（三层 tiering）

Dixit/K562 的 formal tiering 统一为三层，拒绝层不应混用：

| 对象 | Tier | 地位 |
|------|------|------|
| `Dixit_K562_supplementary` | A0 architecture form | **confirmed** |
| `Dixit_architecture_replication` | A1 bridge form | **supporting / partial-support** |
| `Dixit_K562_supplementary` | B 层 content | **not eligible** |

全部禁止表述：
- 禁止：写成 `formal primary co-pillar`
- 禁止：写成 `external validation confirmed`
- 禁止：写成 `replication confirmed`（单独使用）
- 禁止：写成 `content-level replication established`

正式固定短语：
- `formal supplementary external evidence`
- `supplementary-level architecture-form / bridge-form support`
- `A0 confirmed / A1 supporting / B not eligible`

temporal panel 固定短语：

- `7d` 和 `13d` 均确认 `backbone_plus_shift_excess`，支持同一外部 K562 context 下 architecture form 的时间稳定性。
- `7d` rank alignment 更强，而 `13d` mean shift 更大，支持 bridge readout 的 temporal stratification，而不是 later timepoint 单调更强。
- K562 与 HCC 的 macro class 仍为 `CONTEXT_SPECIFIC`，因此该 panel 支持的是 form-level recurrence，不支持 content-level convergence 或 external model-side generalization proved。

### Shift interpretation boundary

`shared trend / overall displacement` 与 `shift-excess` 必须分开书写。前者对应 backbone / shared mean trend 可解释的整体位移，后者只指超出该 backbone 后仍保留的过度偏移成分。当前允许写 GEARS 在部分 setting 中更偏向 separation / shift-excess signal；不允许写成整体 shift recovery proved，也不允许把 shift 混成单一层。

对应表内对象为 `shift_interpretation_band`（wording boundary，非新增实验对象）。

## Replogle/RNAi 扩展层

`Replogle 7d CRISPRi + DepMap RNAi/shRNA dependency` 只能作为 short-horizon / modality-compatible external expansion candidate。正式进入分析前必须先完成 `docs/replogle_rnai_expansion_admission_contract_v1.md` 中的 cell line mapping、gene namespace、target overlap 与 endpoint 身份检查。

允许写法：

- `RNAi/shRNA-derived dependency endpoint`
- `modality-compatible external dependency readout`
- `short-horizon external expansion layer`

禁止写法：

- `siRNA matched endpoint`
- `CRISPRi matched DepMap endpoint`
- `primary closure`
- `external model-side generalization proved`

当前最新版 covariate audit 已补齐 `summary.tsv`、combined TSV 与 per-axis TSV，并把审计轴扩展到一条 `barcode_gem_group` 设计层代理轴、两条 protospacer 轴加两条 transcriptome 轴；但在五条已落盘 covariate 轴下，`PFDN5 / PMF1 / PRPF6 / ZNF131` 的对象级 tier 仍未发生变化。因此，这张表当前更新的重点不是 tier 改写，而是继续确认这些 wording 仍与正式边界一致。

## 一句话收口

当前项目已经从“有没有信号”推进到“每条信号允许写多强”的治理阶段；这张 claim matrix 是当前统一口径的主入口。
