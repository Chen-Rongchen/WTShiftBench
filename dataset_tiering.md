# Stage 1A 数据集分层

## 1. official formal

这一层保持不变，不改协议主线，不因新增候选重写既有结论。

- `replogle_2022_k562_essential`
- `replogle_2022_rpe1`
- `tian_2019_day7neuron`

要求：

- 继续作为当前 formal 主锚点
- 继续由 formal registry 与 formal freeze 默认消费
- 当前已存在的 trial run、baseline、null、truth 与 scoring 结论继续有效

## 2. next formal-admission batch

这一层只做 admission audit，不提前升格。

- `tian_2019_ipsc`
- `tian_2021_crispri`
- `replogle_2022_k562_gwps`
- `dixit_2016_raw`

统一审计问题：

1. 是否能定义清晰的 perturbation identity
2. control 语义是否清晰
3. 是否能限制到 single-guide / single-target 主线
4. support floor `>= 5` 后剩余多少 eligible perturbations
5. 是否能构建 perturbation-level pseudobulk delta truth
6. 是否适合进入 official formal

当前裁决：

- `tian_2019_ipsc`：`admit`
- `tian_2021_crispri`：`admit`
- `replogle_2022_k562_gwps`：`admit`
- `dixit_2016_raw`：`reject`

说明：

- `tian_2019_ipsc` 与 `tian_2021_crispri` 都已在 raw audit 层证明 control / single-target / support floor 可以闭合，适合进入下一批 formal 准入决策。
- `replogle_2022_k562_gwps` 已完成本地 raw audit：`gene == non-targeting` 可稳定定义 control，按 gene-level target 聚合后有 `9863` 个 perturbations 满足 support floor `>= 5`，因此建议进入下一批 formal 准入通过名单。
- `dixit_2016_raw` 作为整包 raw 资源覆盖多 screen / 多 context，不适合作为一个单一 official formal 数据集直接并入；若后续拆成单一 screen 子数据集，可再重新送审。

## 3. side formal / annex

- `norman_2019_raw`

要求：

- 单独审计
- 明确标记为 activation / combinatorial side track
- 不得直接并入 current official formal
- 只评估是否值得建立独立 annex

当前裁决：

- `norman_2019_raw`：`annex_admit`

说明：

- Norman 的主要信息增益在 activation 与 combinatorial 结构，不应被包装成当前 single-target official formal 的一部分。
- 其 single-target 子集可用于技术闭环，但这不改变它应留在 side track 的制度定位。
- 当前本地 raw 已复核通过：文件为 `111445 x 33694`，可由 `guide_ids` 切出 `57831` 个 single-target cells 与 `41759` 个 combinatorial cells；其中 single-target support floor `>= 5` 后保留 `105` 个 eligible targets。

## 4. 来源口径

- `replogle_2022_k562_essential`、`replogle_2022_rpe1`、`tian_2019_day7neuron`：继续使用当前已审查来源。
- `tian_2019_ipsc`：保留 Zenodo `TianKampmann2019_iPSC.h5ad` 作为受审来源，不采用 pertpy 稳定版源码中的可疑 `iPad` URL。
- `tian_2021_crispri`：继续使用 pertpy 官方 loader 对应来源。
- `replogle_2022_k562_gwps`：采用 pertpy 官方 `replogle_2022_k562_gwps()` 对应来源。
- `dixit_2016_raw`：采用 pertpy 官方 `dixit_2016_raw()` 对应来源。
- `norman_2019_raw`：采用 pertpy 官方 `norman_2019_raw()` 对应来源 `https://figshare.com/ndownloader/files/34002548`，不再复用旧的 processed `norman_2019` 资源，也不再保留当前错误下载件。

## 5. 派生 formalization 候选

这一层不改原始 raw 数据集的 `3 + 4 + 1` 分层，只记录“从原始数据集中切出的、更接近 current formal 主线的问题定义”的派生子集。

- `norman_2019_raw__single_target`
- `dixit_2016_raw__control_context`

当前裁决：

- `norman_2019_raw__single_target`：`admit_as_derived_candidate`
- `dixit_2016_raw__control_context`：`admit_as_derived_candidate`

说明：

- `norman_2019_raw__single_target` 是从 Norman raw 中切出的单扰动子集。它保留 `11855` 个 controls、`57553` 个 perturbed cells、`104` 个 support floor `>= 5` 的 eligible targets。合理的制度定位是：原始 `norman_2019_raw` 继续留在 annex，而这个派生子集可单独送入 next formal-admission candidate 轨道。
- `dixit_2016_raw__control_context` 是从 Dixit raw 中切出的 `condition == Control 且 MOI == 1` 子集。它保留 `3770` 个 control-like cells、`26716` 个 perturbed cells、`244` 个 support floor `>= 5` 的 eligible targets。合理的制度定位是：原始 `dixit_2016_raw` 整包继续 `reject`，但该派生子集可作为单独候选再审。
