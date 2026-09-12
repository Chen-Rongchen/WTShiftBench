# 当前CellOT的可移植训练与checkpoint回放

五seed候选包包含两个context的固定staged细胞/47-gene轴/原配置、CellOT源码522d2b9、Pixi锁、seed123–127共470个best checkpoint及对应预测。以实际training_archive_manifest.json为准；旧三seed候选只有282个checkpoint，不能冒充五seed归档。无外部预训练权重；网络随机初始化。原配置中的两条绝对数据路径运行时重定位，其余超参数不改。

从包根目录运行一个target的从头训练检查：

```sh
pixi run --frozen --environment cellot python run_cellot.py --seed 123 --context HCC38 --target ARID1A --output retrained_check
```

省略`--target`会执行该context全部47个target；HCC1143同理。当前测试范围以实际verification.json记录为准，不能由一个target的通过冒称整个470项移植重训都通过。

回放已保存的checkpoint而不训练：

```sh
pixi run --frozen --environment cellot python run_cellot.py --mode replay --seed 124 --context HCC1143 --output replay_check
```

入口先核对包内文件hash，每项独立设置Python/NumPy/PyTorch seed与单线程确定性CPU执行；完成后与同seed/target的已冻结预测比较（最大绝对误差≤1e-10）。已有输出目录拒绝覆盖，可指定新目录复跑。只加载此归档的本项目checkpoint；不应用于不可信权重。

123为当前正式seed，124–127为敏感性；五seed的endpoint相关出现明显变化，所有结果均保留，不择优、不平均预测。126/127在前三seed结果已知后应作者要求登记扩展，不倒写为最初一次性预设五seed。此包从staged细胞开始，不冒称从原始FASTQ/MTX完成全部预处理，也不恢复原投稿CellOT未记录的训练seed。历史checkpoint仍保留在原项目，当前五seed包的470个权重均为修订训练。
