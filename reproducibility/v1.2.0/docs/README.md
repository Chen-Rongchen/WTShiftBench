# WTShiftBench v1.2.0 公开复现归档

WT已由作者确认代表whole-transcriptome；HCC模型评分仍限定于共同47基因空间，不因此扩展为全转录组覆盖。本次归档冻结既有分析，不新增模型、指标或显著性门槛。

## 可复算范围

提供HCC两个context的实测矩阵、9个正式模型及零输出/共享均值矩阵、Replogle K562 day 6的1,882×1,024实测矩阵与3个target-held-out预测矩阵，以及两组CellOT seed123补充预测。TSV首列为target、首行为gene；NPZ内含values、targets、genes三个数组。HCC诊断对照从同包实测矩阵和固定seed再生；Replogle四种诊断参照同样由原函数生成。

endpoint/category表保留A003定义及负值；HCC1143完整endpoint有48targets，共同评分为47targets，交集后不重定标签。配置、可用随机seed、模型训练设定、评分代码、冻结结果和来源hash一并提供。所有包内文件由archive_manifest.json校验。

本包承诺“冻结矩阵→五维评分、常规重构摘要及原已提供的CI/P/q”的复算，不承诺“原始细胞→所有历史训练”的精确重现。M1/M2/M6结果及来源配置一并保留；原始细胞抽样和模型训练不是下面命令执行的路径。历史CellOT训练seed未知，123只属于独立新增执行；Chronos精确历史build及两列legacy gene-effect来源仍有明确缺口。Identity没有CI，homogenization为描述性参照；不新增这些推断。

## 执行

在归档根目录使用随包原始Pixi清单与lock：

```sh
pixi install --environment core --locked
pixi run --environment core python recompute.py --verify-only
pixi run --environment core python recompute.py --output /tmp/wtshiftbench_recomputed
```

完整复算包括原始bootstrap和Mantel置换次数，可能需要较长时间。可先用`--points-only --group m5`检查点估计；这不代替完整推断。`--group m3`、`m4`、`m5`、`cellot_seed123`可分别执行。输出写入指定目录，不覆盖冻结结果；comparison.tsv逐项比较，verification.json记录模式、差异和实际加载的随包代码路径。对NA、不变向量和缺失target沿用冻结实现。

Replogle保存的NPZ为float32，原评分采用float64内存矩阵；不声称位级一致。连续评分使用绝对误差1e-6核验，HCC使用1e-10；P/q及计数不因该精度差异放宽。实际下载验证结果另行登记，未验证前不将本说明视为验证成功证明。

## 文件说明与边界

- `reports/revision/`：M1–M6冻结的endpoint、categories、结果、统计设置及历史run manifests。
- `data/predictions/`与`matrices/`：可公开的聚合target×gene矩阵，不包含原始单细胞个体条目或模型权重。
- `configs/`：冻结的参数、种子和checkpoint登记；部分历史路径指向完整开发仓库，只有本README列出的recompute.py是本包独立入口。
- `src/wtbench/`：原评分函数及其导入依赖，未改科学计算定义。
- `provenance/`：恢复核验、训练与输出回放记录；历史文件hash是来源证据，不表示所引用全部大文件都在本包。
- `expected/`：原冻结context结果作为比较基准，不作为复算分数输入。

保留原MIT代码许可。衍生矩阵来自原公开研究数据，使用时须同时引用相应原始数据集与DepMap；不将MIT许可解释为替代上游数据条款。本归档不包含投稿主稿、回复信或本地私有Git历史。独立修订DOI仅在实际发布且下载核验后登记。
