# Stage 1A 数据集分层

当前收口为两层：

- `formal`：进入正式主榜与 formal freeze 的主线数据集
- `supplement`：允许进入统一运行矩阵与补充审查的数据集

另外，未筛选原始整包数据仍可保留在 `supplement`，但其 `usage` 必须是 `backup_only`；体量过大的 supplement 数据集也可标为 `deferred`，两者都不进入默认统一评测矩阵。

## 1. formal

- `replogle_2022_k562_essential`
- `replogle_2022_rpe1`
- `tian_2019_day7neuron`

要求：

- 继续作为当前 formal 主锚点
- 继续由 formal registry 与 formal freeze 默认消费
- 当前 trial run、baseline、null、truth 与 scoring 结论继续有效

## 2. supplement

### 2.1 可运行 supplement

这些数据集已经具备进入统一运行矩阵的条件，可以做 entrant 对比、baseline 对比和补充审查。

- `tian_2019_ipsc`
- `tian_2021_crispri`
- `norman_2019_raw__single_target`
- `dixit_2016_raw__control_context`

说明：

- `tian_2019_ipsc` 与 `tian_2021_crispri` 已在 raw audit 层证明 control、single-target 与 truth build 可以闭合，当前作为 runnable supplement 使用。
- `norman_2019_raw__single_target` 是从 `norman_2019_raw` 中切出的 single-target 子集，已落盘 formal-like 子集，可直接作为 runnable supplement。
- `dixit_2016_raw__control_context` 是从 `dixit_2016_raw` 中切出的 `Control + MOI==1` 子集，已落盘 formal-like 子集，可直接作为 runnable supplement。

### 2.2 deferred supplement

这些数据集在制度上仍属于 supplement，但当前轮次默认不进入统一运行矩阵。

- `replogle_2022_k562_gwps`

说明：

- `replogle_2022_k562_gwps` 已完成 raw audit：`gene == non-targeting` 可稳定定义 control，按 gene-level target 聚合后有 `9863` 个 perturbations 满足 support floor `>= 5`。
- 但由于当前 `cells` 规模过大，默认跑模成本明显高于其他 supplement 数据集，因此当前先标记为 `deferred`。

### 2.3 backup-only supplement

这些数据集保留 raw 回溯、再切分和审计价值，但不再进入统一评测矩阵。

- `norman_2019_raw`
- `dixit_2016_raw`

说明：

- `norman_2019_raw` 的主要价值在 activation / combinatorial side track。它保留为备份与 annex 参考，不直接参与当前 single-target 主线跑模。
- `dixit_2016_raw` 作为整包 raw 资源横跨多个 context，不适合作为单一 benchmark object；原始整包仅保留备份作用，真正进入评测的是派生子集 `dixit_2016_raw__control_context`。

## 3. 来源口径

- `replogle_2022_k562_essential`、`replogle_2022_rpe1`、`tian_2019_day7neuron`：继续使用当前已审查来源。
- `tian_2019_ipsc`：保留 Zenodo `TianKampmann2019_iPSC.h5ad` 作为受审来源，不采用 pertpy 稳定版源码中的可疑 `iPad` URL。
- `tian_2021_crispri`：继续使用 pertpy 官方 loader 对应来源。
- `replogle_2022_k562_gwps`：采用 pertpy 官方 `replogle_2022_k562_gwps()` 对应来源。
- `dixit_2016_raw`：采用 pertpy 官方 `dixit_2016_raw()` 对应来源。
- `norman_2019_raw`：采用 pertpy 官方 `norman_2019_raw()` 对应来源 `https://figshare.com/ndownloader/files/34002548`。

## 4. 机器可读口径

当前两层治理的机器可读入口是：

- `configs/stage1a/dataset_governance.json`
- `admission_matrix.tsv`

其中：

- `tier` 只允许 `formal` 或 `supplement`
- `usage=mainline` 表示正式主线
- `usage=runnable` 表示 supplement 中可直接进入统一运行矩阵的数据集
- `usage=deferred` 表示 supplement 中暂时搁置、不进入默认运行矩阵的数据集
- `usage=backup_only` 表示仅保留为原始备份，不进入统一运行矩阵
