# Manuscript hardening plan v1

## 文档定位

本文档记录当前从 **strong editorial draft** 推进到 **Genome Biology submission-ready manuscript** 的最后一轮文字与投稿风险治理。

本轮不新增分析，不重开 truth object，不新增 entrant，不改变 frozen claim boundary。目标是把已经完成的 evidence package 以更可审计、更少歧义、更符合 Genome Biology resource/framework 文章身份的方式写出来。

## 当前判断

稿件主线已经逻辑闭环：

- Fig. 1 定义 phenotype-relevant benchmark truth object。
- Fig. 2 管理 shared anchor 证据层级。
- Fig. 3 用三指标裁决 model recovery，而不是做单一 leaderboard。
- Fig. 4 排除 recipe、embedding coverage 和 linear control 这类简单反驳。
- Fig. 5 给出 qualified axis-level interpretation。
- Fig. 6 用 covariate、K562 temporal panel 和 RNAi endpoint sensitivity 收住最终 claim ceiling。

但当前稿件仍应视为 strong editorial draft，而不是最终 submission-ready 版本。剩余风险集中在四类：

1. 对象身份与缩写风险。
2. Genome Biology submission blocker。
3. Introduction / Results 对 framework/resource 的主语强度不足。
4. Methods 仍需推进到公式、阈值和判定规则级别。

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
- Fig. 5：biological interpretation is tiered, asymmetric and partial。
- Fig. 6：external sensitivity analyses define the admissible claim ceiling。

每节最后一句继续保留边界句，防止局部结果被读成 overclaim。

## 第五优先级：Methods 推进到 operational definition 级

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

1. 先修 HCC38/HCC1143 身份与缩写风险。
2. 补齐 submission blocker 清单和占位位置。
3. 重写 Abstract / Introduction 前半段，使 framework/resource 成为第一主语。
4. 重写每个 Results 小节首句和末句。
5. 扩 Methods 到 operational definition 级。
6. 最后再统一图题、panel title、Discussion 和 cover letter。

## 当前不做

- 不新增正式分析。
- 不重训 GEARS。
- 不新增 entrant family。
- 不升级 K562 或 RNAi endpoint 地位。
- 不扩 Stage 3 discovery。
- 不重画整套图版，除非文字修订要求图中文字同步。
