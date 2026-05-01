# Manuscript hardening plan v1

## 文档定位

本文档记录当前从 **strong editorial draft** 推进到 **Genome Biology submission-ready manuscript** 的最后一轮文字与投稿风险治理。

本轮不新增分析，不重开 truth object，不新增 entrant，不改变 frozen claim boundary。目标是把已经完成的 evidence package 以更可审计、更少歧义、更符合 Genome Biology resource/framework 文章身份的方式写出来。

## 当前判断

稿件主线已经逻辑闭环，并且本轮 boundary / grammar audit 已经落入当前主稿：

- Fig. 1 定义 phenotype-relevant benchmark truth object。
- Fig. 2 管理 shared anchor 证据层级。
- Fig. 3 用三指标裁决 model recovery，而不是做单一 leaderboard。
- Fig. 4 排除 recipe、embedding coverage 和 linear control 这类简单反驳。
- Fig. 5 用 covariate、K562 temporal panel 和 RNAi endpoint sensitivity 收住最终 claim ceiling。
- Extended Data Fig. 11 给出 qualified axis-level interpretation。

当前正文与图注不再是待 hardening 草稿，而是投稿前文字 source of truth。剩余工作已经从 claim grammar 转入两类：

1. Genome Biology submission blocker。
2. 按当前正文和图注重新用代码绘制图版。

当前图像文件仍是上一轮生成产物，不视为最终视觉版。

## 第一优先级：修正 HCC38/HCC1143 身份风险

HCC38 和 HCC1143 是人源乳腺癌细胞系。`HCC` 不能定义为 hepatocellular carcinoma，也不应在正文中单独作为肿瘤类型缩写使用。

允许写法：

- `HCC38 and HCC1143 breast-cancer cell-line contexts`
- `the two primary breast-cancer contexts`
- `the HCC38/HCC1143 benchmark contexts`
- `the HCC38/HCC1143 breast-cancer benchmark`

不推荐写法：

- `HCC context`
- `HCC benchmark`
- `HCC primary evidence`
- `HCC = hepatocellular carcinoma`

内部工程文档中历史形成的 `HCC` shorthand 可以保留为路线记录，但投稿文本、图注、缩写表和最终上传材料必须避免误读。

## 第二优先级：补齐 submission blocker

这些不是科学缺口，但正式投稿前必须补齐：

- 作者姓名。
- 作者单位。
- 通讯作者姓名和邮箱。
- Funding。
- Competing interests。
- Authors' contributions。
- Acknowledgements。
- Public repository URL。
- Archive DOI。
- Data availability。
- Code availability。
- 数据 accession / source-data statement。
- AI use statement 最终确认。

当前最关键 blocker 是 public repository / archive DOI。内部路径只能用于 reproducibility package 的本地索引，不能替代公开仓库或归档 DOI。

## 第三优先级：把卖点固定为 framework/resource

稿件不能卖成：

> 我们比较几个模型，发现 baseline 比 GEARS 强。

正式卖点应固定为：

> 我们先定义 phenotype-aligned benchmark truth object，再用 architecture-aware adjudication 框架评估模型恢复哪些结构，并通过 claim governance 与 reproducibility package 管理可写边界。

模型比较是 framework 的 demonstration，不是文章身份本身。

Introduction 的 root-cause 句式应从：

> existing perturbation model benchmarks are incomplete

推进到：

> existing benchmarks often compare models before operationally freezing a phenotype-aligned truth object.

## 第四优先级：重写 Results 每节首尾

每个 Results 小节需要承担一个明确闭环功能：

- Fig. 1：object definition before adjudication。
- Fig. 2：recurrent structure does not license unqualified target claims。
- Fig. 3：architecture-aware metrics decompose entrants rather than form a single leaderboard。
- Fig. 4：alternative technical explanations were stress-tested but did not close the backbone gap。
- Fig. 5：external sensitivity analyses define the admissible claim ceiling。
- Extended Data Fig. 11：biological interpretation is tiered, asymmetric and partial。

每节最后一句继续保留边界句，防止局部结果被读成 overclaim。

## 第五优先级：Methods 推进到 operational definition 级

状态：已完成并落入 `manuscript/text/manuscript_draft_v1.md`。本节保留为审计记录。

Methods 至少需要明确以下对象的可复现定义：

- absolute mean perturbation shift。
- DepMap dependency alignment 方向处理。
- high / middle / low bin 阈值或规则。
- Q1 anchor 定义。
- shared anchor 定义。
- backbone recovery score。
- shift-excess identification。
- structure-versus-context separation。
- shared-mean baseline 构造方式。
- permutation null。
- cutoff sensitivity。
- axis-level R2。
- bootstrap stability。
- evidence tier 判定规则。

目标是让 benchmark object 成为 operational object，而不是 verbal construct。

## 第六优先级：两处 overclaim 降档

状态：已完成并落入 Results、Discussion、Figure legends。以下保留为审计记录。

### GEARS gap 解释

过强版本：

> The observed gap is most parsimoniously interpreted as a task-structure or direction-level mismatch.

推荐版本：

> The persistence of the gap after finite-budget recipe sweeps, linear controls and coverage audits is consistent with a task-structure or direction-level mismatch, although it does not exclude other untested model-side factors.

### baseline / backbone 解释

过强版本：

> the dominant component of the HCC benchmark truth object is a cross-context canonical backbone.

推荐版本：

> the results support the interpretation that a cross-context canonical backbone is the dominant recoverable component of the HCC38/HCC1143 benchmark truth object under the present benchmark definition.

## 执行顺序

已完成：

1. HCC38/HCC1143 身份与缩写风险已在当前主稿中收口。
2. Abstract / Background / Results / Methods / Discussion / Conclusions 已完成 grammar 同步。
3. Figure 1-5 与 Extended Data Fig. 1-11 图注已完成 boundary 同步。
4. Methods 已推进到 operational definition 级。

剩余执行顺序：

1. 按 `docs/manuscript_figure_redesign_plan_v1.md` 重画 Figure 1-5 与 Extended Data Fig. 1-11。
2. 作者人工补齐 author metadata、funding、competing interests、contributions、acknowledgements。
3. 补齐 public repository / archive DOI 与公开 Data / Code availability。
4. 最终导出投稿版 PDF/Word、图版文件和 Additional files。

## 当前不做

- 不新增正式分析。
- 不重训 GEARS。
- 不新增 entrant family。
- 不升级 K562 或 RNAi endpoint 地位。
- 不扩 Stage 3 discovery。
- 不在图版重画阶段新增分析或改变 source data。
- 不把图版重画与 claim boundary 修改混在一起。
