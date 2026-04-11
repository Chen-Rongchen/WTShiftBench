# Stage 1A / 1B failure decomposition note v1

## 1. 文档定位

这份文档只回答一个问题：

**在 truth-first 主线下，`Stage 1A / 1B` 现在到底承担什么角色？**

它不重写旧 `Stage 1A` 的 formal benchmark 制度，也不重写 `Stage 1B` 的 freeze / validation 协议；当前仓库已清理旧执行流，只保留其在主文叙事中的 failure decomposition 解释角色。

这份 note 只补“解释层”：

- `Stage 1A` 不再只是 leaderboard
- `Stage 1B` 不再只是 long-horizon stress test
- 二者应被统一解释为 frozen truth architecture 下的 `failure decomposition track`

## 2. 当前最稳的总体定位

在当前项目主线中，`Stage 1A / 1B` 的作用不是和 `Stage 2` 竞争主结论，而是为 `Stage 2` 的 architecture adjudication 提供失败类型解释层。

更稳的说法是：

- `Stage 1A`：short-horizon failure decomposition
- `Stage 1B`：long-horizon / temporal failure decomposition

因此，`Stage 1A / 1B` 当前最重要的产出不应再被理解为“谁排第一”，而应被理解为：

**模型究竟丢掉了哪一种结构，失败发生在什么层级，以及这种失败是否会在更长时间尺度上进一步恶化。**

## 3. Stage 1A 的新角色

`Stage 1A` 仍然保留 short-horizon formal benchmark 的制度身份，但在 truth-first 口径下，它更重要的解释任务是：

- 模型是否连短期 backbone 都无法稳定恢复
- 模型是否能拟合 shared mean trend，却丢掉 `shift-excess`
- 模型是否把 context-specific deviation 平均化抹平
- 模型 failure 是随机波动，还是具有稳定的结构偏差

因此，`Stage 1A` 当前最适合被理解为：

**short-horizon structure-aware failure gate。**

它回答的不是抽象的“预测准不准”，而是：

1. backbone 有没有丢
2. shift-excess 有没有被抹平
3. structure 和 context 有没有被混在一起
4. 这些问题在 formal held-out / multi-split 下是否稳定存在

## 4. Stage 1B 的新角色

`Stage 1B` 仍然保留 external time-aligned validation / stress layer 的制度身份，但在当前主线里，它更重要的解释任务是：

- short-horizon 中已出现的 failure mode，到了 long horizon 是否进一步放大
- 模型是否出现 `temporal structure degradation`
- backbone、shift-excess、context specificity 之间，哪一部分在 14d external truth 中最先失稳

因此，`Stage 1B` 当前最适合被理解为：

**temporal failure decomposition layer。**

它不是再做一轮 leaderboard，而是用更长时间尺度判断：

- failure 是局部数值退化
- 还是 architecture-level structure degradation

## 5. Stage 1A / 1B 与 Stage 2 的关系

`Stage 2` 负责回答：

> 模型能否恢复 frozen truth architecture？

而 `Stage 1A / 1B` 负责回答：

> 如果不能恢复，失败究竟发生在哪里？

更具体地说：

- `Stage 2` 给出 architecture-level adjudication
- `Stage 1A` 给出 short-horizon failure typing
- `Stage 1B` 给出 long-horizon / temporal failure typing

因此三者不是替代关系，而是：

1. `Stage 2` 先定义主裁决问题
2. `Stage 1A / 1B` 再解释 failure mode

这也是为什么当前不能把 `Stage 1A / 1B` 写成废弃层，也不能把它们继续只写成 leaderboard / stress test。

## 6. 当前最推荐的正式写法

如果要把 `Stage 1A / 1B` 写成主文档中的一段，最稳的说法是：

在 truth-first 主线下，`Stage 1A / 1B` 不再只是 benchmark leaderboard 与时间外推 stress test，而应被重新解释为 frozen truth architecture 下的 failure decomposition track。其中，`Stage 1A` 负责 short-horizon failure decomposition，重点区分模型丢掉的是 backbone、shift-excess 还是 context specificity；`Stage 1B` 则负责 long-horizon / temporal failure decomposition，用于判断这些结构性 failure mode 是否会在 external time-aligned truth 中进一步放大为 temporal structure degradation。因而，`Stage 1A / 1B` 当前最重要的价值，不是提供一组脱离结构语义的排名，而是为 `Stage 2` 的 architecture adjudication 提供结构化失败解释层。

## 7. 主张边界

当前这条线应避免以下写法：

- 把 `Stage 1A` 再写回“只服务 leaderboard”
- 把 `Stage 1B` 再写回“只服务 stress test”
- 把 `Stage 1A / 1B` 写成与 `Stage 2` 并列争夺 primary biological conclusion 的层
- 把单次分数波动直接升级成结构性 failure claim

当前更稳的边界是：

- `Stage 1A / 1B` 是解释层，不是 truth-side 发现层
- 它们解释的是 model failure，不是新 truth object
- 它们服务的是 architecture-aware adjudication，而不是脱离结构语义的排名展示

## 8. 渐进披露

默认先看：

1. [`plan.md`](/home/data/gz0705/WTKO/plan.md)
2. [`docs/protocol_blueprint.md`](/home/data/gz0705/WTKO/docs/protocol_blueprint.md)
3. [`docs/main_manuscript_results_draft_v1.md`](/home/data/gz0705/WTKO/docs/main_manuscript_results_draft_v1.md)

若要进执行层，再看：

- [`scripts/README.md`](/home/data/gz0705/WTKO/scripts/README.md)
- [`configs/README.md`](/home/data/gz0705/WTKO/configs/README.md)
