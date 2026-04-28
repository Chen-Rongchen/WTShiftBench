# 模型对 baseline 后续推进拆解 v1

## 1. 文档定位

这份文档只回答一个问题：

**在 `docs/model_vs_baseline_deeper_explanation_note_v1.md` 已经固定解释边界之后，下一步若继续推进，具体应该做什么？**

它不重复已有 explanation layer，也不把 plausible biological interpretation 提前升级成主结论。

它只做三件事：

- 把后续推进固定成两个更小的问题
- 给出这两个问题各自对应的验证目标
- 固定下次进来时的默认 stop rule，避免重新回到空泛争论

## 2. 一句话工作口径

下一步若继续推进，不再泛泛问“模型为什么打不过 baseline”，而是只问：

1. `baseline winner` 是否主要由 shared backbone objective 决定
2. entrant 的额外能力是否稳定落在 `separation / deviation` 而不是 backbone 上

这两个问题必须按非对称 trade-off 来理解：`shared_mean_baseline` 是 backbone primary reference，`GEARS` 是 deviation / separation-biased entrant；`shift-excess` 指超出 shared backbone 可解释部分的过度偏移，不等于 shared trend / overall displacement。

只有这两个问题更清楚后，biology-facing interpretation 才值得继续往前推进。

## 3. 先固定解释边界

在继续任何验证前，先固定一条纪律：

- 方法学解释：当前已经有 defendable explanation layer
- 生物学解释：当前仍主要是 plausible interpretation

因此下次进来时，先不要问“biology 到底是什么 root cause”，而要先问：

- 当前还缺哪一种方法学验证
- 缺口补上后，是否真的足以推动 biology-facing interpretation 前移

默认先读：

1. [`docs/project_state_summary_v1.md`](/home/data/gz0705/WTKO/docs/project_state_summary_v1.md)
2. [`docs/final_claim_boundary_and_discovery_gating_note_v1.md`](/home/data/gz0705/WTKO/docs/final_claim_boundary_and_discovery_gating_note_v1.md)
3. [`docs/why_models_do_not_stably_beat_baseline_v1.md`](/home/data/gz0705/WTKO/docs/why_models_do_not_stably_beat_baseline_v1.md)
4. [`docs/model_vs_baseline_deeper_explanation_note_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_deeper_explanation_note_v1.md)
5. [`docs/model_vs_baseline_next_step_breakdown_v1.md`](/home/data/gz0705/WTKO/docs/model_vs_baseline_next_step_breakdown_v1.md)

## 4. 问题一：`baseline winner` 是否主要由 shared backbone objective 决定

### 4.1 这个问题真正要验证什么

这里要验证的不是“baseline 强不强”，而是：

- 当前 primary adjudication 是否本质上最奖励 `shared canonical backbone`
- baseline 的胜出是否主要来自它对这部分 shared backbone 的天然贴合
- entrant 若想赢，是否必须先保住 backbone，再谈额外结构能力

### 4.2 当前最小可防守验证目标

这一问下一步只需要补到下面这个层级：

- 继续确认 backbone gap 是否主要表现为 `direction mismatch`
- 继续确认 baseline 的优势是否稳定集中在 backbone，而非来自偶然的单一指标波动
- 继续确认不同 entrant 是否都面临“只要强化额外结构能力，就更难保住 backbone”的同向约束

只要这三点更清楚，就足以支撑：

**baseline winner 更像由 shared backbone objective 主导。**

### 4.3 达到什么程度就够

这一问的 stop rule 不是证明唯一 root cause，而是做到：

- 可以更稳地说“主裁决确实偏向 backbone winner”
- 可以更稳地说“baseline 胜出不是接入失败的假象”
- 不需要再靠新增 entrant 来重复同一结论

如果这三点已经满足，就不要继续无限扩验证。

## 5. 问题二：entrant 的额外能力是否稳定落在 `separation / deviation` 而不是 backbone 上

### 5.1 这个问题真正要验证什么

这里要验证的不是“entrant 有没有价值”，而是：

- entrant 的增益是否稳定体现在 `structure/context separation`
- entrant 的增益是否稳定体现在 `deviation / shift-excess`
- 这些增益是否没有同步转化为 backbone superiority

### 5.2 当前最小可防守验证目标

这一问下一步只需要补到下面这个层级：

- 继续确认 separation gain 与 backbone loss 是否构成稳定 `trade-off frontier`
- 继续确认不同 entrant family 是否共享这一模式，而不是只在 `GEARS` 上偶然出现
- 继续确认 foundation-model entrant 与 linear controls 的位置差异，主要体现在“保留多少 backbone”与“是否拥有额外 separation/deviation 能力”，而不是出现 hidden winner

只要这三点更清楚，就足以支撑：

**entrant 的额外能力主要落在 backbone 之外。**

### 5.3 达到什么程度就够

这一问的 stop rule 同样不是解释所有模型，而是做到：

- 可以更稳地说 entrant 学到的是另一类结构，而不是“什么都没学到”
- 可以更稳地说 entrant 的优势方向与当前 backbone winner 方向不完全一致
- 不需要再把 biology-facing interpretation 提前抬成主结论

如果这三点已经满足，就应停止继续把“模型为什么没赢”写成开放式问题。

## 6. 两个问题做完后，biology-facing interpretation 才能往前走

如果前面两问还不够清楚，biology-facing interpretation 只能继续保留为：

- lower-confidence
- biological-facing
- plausible

只有在前两问都更稳后，才值得继续追问：

- 当前 frozen backbone 在 biology 上更像哪些 shared programs
- entrant 学到的 deviation 在 biology 上是否更接近 context-specific rewiring
- 哪些 foundation-model prior 只是 gene semantic prior，而不是 perturbation backbone prior

但即便推进到这里，也仍然不等于：

- 已证明唯一 biological mechanism
- 已证明只要改 objective 就一定能赢 baseline

## 7. 推荐执行顺序

如果下一轮只做方法学收口，按这个顺序：

1. 先固定解释边界
2. 先做问题一的验证
3. 再做问题二的验证
4. 最后才决定 biology-facing interpretation 是否值得前推

原因很简单：

- 问题一回答“主裁决到底在奖励什么”
- 问题二回答“entrant 额外学到的到底落在哪里”
- 只有这两层都更清楚，biology-facing 解释才不会重新变成空话

## 8. 当前明确不该做什么

- 不要重新把问题写回“模型为什么不行”这种泛问题
- 不要在没有新证据的前提下把 biology-facing interpretation 升成主结论
- 不要为了回答这两个问题而无边界继续扩 entrant
- 不要回头重做 truth object
- 不要把辅助指标升级成新的 primary adjudication

## 9. 推荐落点

如果要把这份文档压成一句执行口径，最稳的版本是：

**后续推进的默认主线，不是继续空谈“模型为什么打不过 baseline”，而是先把 `baseline winner 是否由 backbone objective 决定` 与 `entrant gain 是否主要落在 separation / deviation` 这两个更小的问题收紧到可防守层级。**

## 10. 可直接进入主文的写法

如果需要把这条后续推进口径压成 manuscript-ready wording，更稳的版本是：

> 在当前解释边界下，后续工作不再将“复杂模型为何未稳定胜过 `shared_mean_baseline`”保留为开放式泛问题，而是优先收紧为两个方法学问题：其一，当前 `baseline winner` 是否主要由 shared backbone objective 决定；其二，entrant 的额外能力是否稳定落在 `structure/context separation` 与 deviation-related structure，而非更强的 backbone recovery 上。在这两个问题进一步澄清之前，biology-facing interpretation 仍应保留为 plausible layer，而不升级为主结论。

如果需要更短的 Results-style 版本，可写成：

> 后续对 baseline-vs-model gap 的推进应优先聚焦于两个方法学问题，即 `baseline winner` 是否主要由 shared backbone objective 决定，以及 entrant gain 是否主要落在 `separation / deviation` 而非 backbone；在此之前，biology-facing explanation 仍只应保留为 plausible interpretation。

## 11. 一句话收口

下一步真正要做的，不是再找一个更大的解释，而是把 `backbone winner` 与 `entrant extra capability` 这两个问题分别钉死。
