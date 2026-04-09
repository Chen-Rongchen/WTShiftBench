# Stage 2 Truth Bridge Decomposition Result v1

## 结果主段落

我们将 `truth–DepMap bridge` 分解为两个递进层面进行刻画。首先，在 `target-level joint-priority grid` 中，我们分别将 transcriptomic real shift 与 aligned DepMap dependency 划分为 `high / middle / low` 三段，仅将四个角点定义为正式 `Q1-Q4`，而将任何一侧落入 `middle` 的 target 保留在 `middle band`。在这一更保守的定义下，`HCC38` 与 `HCC1143` 中均可识别出一组稳定的 `Q1` canonical bridge anchors，说明部分 target 同时具有较高的 transcriptomic impact 与较高的 cellular dependency；相对地，`Q2/Q3` 更适合作为 deviation structure，用于区分 transcriptomic-excess 与 dependency-excess targets，而不是被视为噪音。

进一步地，在 `axis-level shared explanatory structure` 中，我们将 target 压缩到 frozen functional axes，并分别评估各 axis 对 transcriptomic side 与 DepMap side 的解释强度。为避免将单基因现象过度上升为模块级结论，这里要求 `n_targets >= 2` 的 axis 才进入 formal call。按此口径，当前结果支持一类更保守的 shared explanatory structure，同时也显示部分 axis 更偏向 transcriptomic-heavy 或 dependency-heavy。换言之，这条 bridge 并不是由单一整体相关性支撑，而是由少数 shared anchors 与有限的 shared / skewed functional structure 共同构成。

## 图注草稿

### 图 1

`Target-level joint-priority grid of the truth–DepMap bridge.`

横轴为 aligned DepMap strength，纵轴为 real shift。两侧分别按分位数划分为 `high / middle / low`，仅四个 corner cells 被定义为 `Q1-Q4`；任一侧落入 `middle` 的 target 保留在 `middle band`。`Q1` 表示 canonical bridge anchors，`Q2/Q3` 表示 transcriptomic-excess 或 dependency-excess deviation structure，`Q4` 表示 low-information background。

推荐对应图：

- `reports/stage2_truth_bridge_decomposition/HCC38_target_level_joint_grid.png`
- `reports/stage2_truth_bridge_decomposition/HCC1143_target_level_joint_grid.png`

### 图 2

`Axis-level shared explanatory structure of the truth–DepMap bridge.`

每个点代表一个 frozen axis。横轴与纵轴分别表示该 axis 对 DepMap side 与 transcriptomic side 的 explanatory `R²`。只有 `n_targets >= 2` 的 axis 才进入 formal call；因此图中 formal shared/skewed axes 表示更接近模块级的结构证据，而单 target axes 即使有明显信号，也仅记为 preliminary。

推荐对应图：

- `reports/stage2_truth_bridge_decomposition/axis_level_shared_explanatory_structure.png`

## 当前写作边界

- 这里支持的是 transcriptomic impact 与 cellular dependency 在 target / axis 上的结构性共定位。
- 这里不支持因果性表述，例如“transcriptomic shift 导致 dependency”或“dependency 导致 transcriptomic shift”。
- 当前 formal axis call 受 `n_targets >= 2` 约束；单 target axis 只能写成 preliminary signal，不应提升为正式 shared backbone 结论。

## 渐进披露

如果主文只保留最短结果链，建议按以下顺序引用：

1. `reports/stage2_truth_bridge_decomposition/bridge_decomposition_report.md`
2. `reports/stage2_truth_bridge_decomposition/shared_canonical_anchor_summary.tsv`
3. `reports/stage2_truth_bridge_decomposition/axis_level_shared_explanatory_summary.tsv`

