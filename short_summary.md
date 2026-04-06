# 为什么改成 formal / supplement

因为当前真正需要解决的，不是给数据集堆更多中间标签，而是回答两个问题：

- 哪些数据集已经足够稳定，能进入正式主榜
- 哪些数据集已经可跑、可审、可比，但还不该和正式主榜混写

因此当前最简洁的治理方式是：

- `formal` 只保留 3 个主线锚点
- 其余可用数据统一放进 `supplement`
- 未筛选原始整包也放在 `supplement`，但只保留 `backup_only` 身份

这意味着：

- `norman_2019_raw__single_target`
- `dixit_2016_raw__control_context`

都不再被描述成“还差一步才能用”的对象，而是明确作为可运行的 `supplement` 数据集使用。

同时：

- `norman_2019_raw`
- `dixit_2016_raw`

继续保留为原始备份与回溯来源，不再进入统一评测矩阵。
