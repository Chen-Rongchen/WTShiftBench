# `barcode_gem_group` 映射 closure note

## 1. 这份说明只回答什么

这份说明只回答一个问题：

**当前能否把 `barcode_gem_group = 1/2/3` 唯一映射到 `MH001...MH006` 的单个 run？**

结论先写在前面：

- 能确认 `-1/-2/-3` 是两个聚合样本内部的三个 gem group
- 能确认 `HCC38` 对应 `aggrMH001-3`，`HCC1143` 对应 `aggrMH004-6`
- 但基于当前仓库内与 GEO 已公开产物，**不能**把 `-1/-2/-3` 唯一钉死到单个 `MH001`、`MH002`、`MH003` 或 `MH004`、`MH005`、`MH006`

因此，当前正式口径应固定为：

**`barcode_gem_group` 是 design-proxy axis，而不是已确认到单个 `MH00x` 的 run-level label。**

## 2. 已确认的事实

### 2.1 聚合样本命名已明确给出两组 run family

当前主线配置与 GEO 文件名一致：

- `HCC38` 使用 `GSM7716951_*_HCC38_aggrMH001-3.*`
- `HCC1143` 使用 `GSM7716952_*_HCC1143_aggrMH004-6.*`

这一步只支持下面两条结论：

- `HCC38` 来自 `MH001/002/003` 这一组聚合样本
- `HCC1143` 来自 `MH004/005/006` 这一组聚合样本

### 2.2 条形码尾缀确实包含三个 gem group

当前 `barcodes.tsv.gz` 中可见三个尾缀层级：

- `HCC38`：`-1 = 9712`、`-2 = 11411`、`-3 = 10424`
- `HCC1143`：`-1 = 8573`、`-2 = 7283`、`-3 = 8643`

在 covariate 物化后的 single-feature 子集中，三组也都保留：

- `HCC38`：`1 = 4524`、`2 = 5302`、`3 = 4659`
- `HCC1143`：`1 = 4079`、`2 = 3500`、`3 = 4057`

因此，`barcode_gem_group` 作为三层 design-proxy stratifier 是真实存在的，不是分析侧伪造变量。

## 3. 当前不能确认的部分

当前缺的不是 `-1/-2/-3` 是否存在，而是：

- `HCC38` 中 `-1/-2/-3` 是否分别等于 `MH001/MH002/MH003`
- `HCC1143` 中 `-1/-2/-3` 是否分别等于 `MH004/MH005/MH006`
- 以及这套对应关系是否有作者公开元数据可直接引用

当前本地证据链不足以完成这一步，原因很直接：

- `GSE241115_RAW.tar` 里只公开了 `aggrMH001-3` 与 `aggrMH004-6` 两个聚合产物
- GEO sample 页面也只列出这两个 aggregated processed files
- 仓库内没有单独的 `MH001...MH006` run-level matrix / barcode / metadata 文件
- 当前公开产物中也没有把 gem group 编号和单个 `MH00x` 显式对照的表

## 4. 为什么这里应停止继续追查

如果没有新的 run-level metadata，继续在当前仓库内追查只会把“合理猜测”误写成“已确认映射”。

最接近事实、同时又可防守的写法是：

- `barcode_gem_group` 捕捉到的是聚合样本内部的三层 gem group / design-layer aggregation 结构
- 它比 protospacer / transcriptome quantile 轴更接近实验设计层
- 但它仍只是 proxy，不是已解析到单个 `MH00x` 的 fully resolved design covariate

## 5. 当前正式收口

从当前版本起，这条线按以下口径冻结：

1. 不再把 “继续追查 `-1/-2/-3 -> MH00x`” 作为默认下一步
2. 主文档统一写成 `barcode_gem_group = design-proxy axis`
3. 允许写：
   - `HCC38` 对应 `aggrMH001-3`
   - `HCC1143` 对应 `aggrMH004-6`
   - `barcode_gem_group` 是聚合样本内部的 gem group 分层
4. 不允许写：
   - `-1 = MH001`
   - `-2 = MH002`
   - `-3 = MH003`
   - 或 `HCC1143` 上对应的任何单个 `MH004/005/006` 唯一映射
5. 若未来拿到作者级 run sheet、Cell Ranger aggregation manifest 或单 run 原始文件，再重新打开这条线

## 6. 一句话结论

`barcode_gem_group` 已足以作为正式 design-proxy axis 进入 claim boundary；但在当前公开元数据上限下，它不能升级成单个 `MH00x` 已确认的 run-level 标签。
